import asyncio
import json
import os
import re
import time

from dotenv import load_dotenv
from openai import OpenAI

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from harness import AgentHarness


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# OPENROUTER
# ============================================================

llm = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def get_request_llm(api_key=None):
    """
    Return the OpenRouter client for this request.

    Without a user key, keep the existing project-level key.
    With a user key, use that key only for this request.
    """
    if api_key and api_key.strip():
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key.strip()
        )

    return llm


# ============================================================
# MCP SERVER
# ============================================================

server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
    env=os.environ.copy(),
)


# ============================================================
# AGENT CONFIGURATION
# ============================================================

MAX_ITERATIONS = 5


# ============================================================
# CONVERT MCP TO OPENROUTER TOOLS
# ============================================================

def convert_tools(mcp_tools):
    """
    Convert MCP tools into OpenAI/OpenRouter tool format.
    """

    tools = []

    for tool in mcp_tools:

        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
            }
        )

    return tools


# ============================================================
# SALARY AGENT PROMPT
# ============================================================

SALARY_AGENT_PROMPT = """
You are a specialized Salary Analysis Agent.

Your responsibility is to answer questions about:

- Employee salaries
- Highest-paid employees
- Lowest-paid employees
- Salary comparisons
- Salary thresholds
- Company salary statistics
- Highest-paid employee at a company

Use MCP tools whenever employee or company
database information is required.

Never invent salary information.

For company-specific salary questions, use
the appropriate MCP tool.

Do not assume a currency unless the database
explicitly provides one.

Use the minimum number of MCP tools necessary
to answer the user's question.

Return clear and concise answers.

If the database does not contain the requested
information, clearly say that the information
is unavailable.

IMPORTANT:

The MCP database is the source of truth.

Never invent a company, employee, salary,
role, or statistic that is not returned
by the MCP database.
"""


# ============================================================
# CLEAN COMPANY NAME
# ============================================================

def clean_company_name(company):
    """
    Clean punctuation and common trailing words
    from an extracted company name.
    """

    if not company:
        return None

    company = company.strip()

    # Remove trailing punctuation
    company = re.sub(
        r"[.,!?;:]+$",
        "",
        company
    ).strip()

    # Remove possessive suffix
    company = re.sub(
        r"['’]s$",
        "",
        company,
        flags=re.IGNORECASE
    ).strip()

    # Remove common trailing words
    company = re.sub(
        r"\s+(?:salary|salaries|employee|employees|"
        r"role|roles|information|details|structure|"
        r"analysis|statistics|stats)$",
        "",
        company,
        flags=re.IGNORECASE
    ).strip()

    return company if company else None


# ============================================================
# EXTRACT COMPANY NAME
# ============================================================

def extract_company_from_query(query):
    """
    Extract one company name from a salary query.

    Examples:

    Who is the highest paid employee at Google?
        -> Google

    What is the salary information for Google?
        -> Google

    What is the salary information for Google.?
        -> Google

    Give me salary details for Tesla.
        -> Tesla
    """

    if not query:
        return None

    query = query.strip()

    patterns = [

        # at Google
        r"\bat\s+([A-Za-z][A-Za-z0-9&.\- ]+?)(?:\?|$)",

        # at Google salary
        r"\bat\s+([A-Za-z][A-Za-z0-9&.\- ]+?)(?:\s+"
        r"(?:salary|salaries|employee|employees|role|roles|"
        r"information|details|structure|analysis|statistics|stats))",

        # of Google
        r"\bof\s+([A-Za-z][A-Za-z0-9&.\- ]+?)(?:\?|$)",

        # for Google
        r"\bfor\s+([A-Za-z][A-Za-z0-9&.\- ]+?)(?:\?|$)",

        # Google's salary
        r"\b([A-Za-z][A-Za-z0-9&.\- ]+?)['’]s\s+"
        r"(?:salary|salaries|pay|compensation|earnings)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            query,
            re.IGNORECASE
        )

        if match:

            company = match.group(1)

            company = clean_company_name(
                company
            )

            if company:
                return company

    return None


# ============================================================
# EXTRACT MULTIPLE COMPANIES
# ============================================================

def extract_companies_from_query(query):
    """
    Extract multiple companies for salary comparison.

    Examples:

    Compare Google and Tesla salaries.
        -> ["Google", "Tesla"]

    Google vs Tesla salary
        -> ["Google", "Tesla"]
    """

    if not query:
        return []

    query = query.strip()

    companies = []

    # Pattern: Google and Tesla
    match = re.search(
        r"\b([A-Za-z][A-Za-z0-9&.\- ]+?)"
        r"\s+(?:and|vs\.?|versus)\s+"
        r"([A-Za-z][A-Za-z0-9&.\- ]+)",
        query,
        re.IGNORECASE
    )

    if match:

        first = clean_company_name(
            match.group(1)
        )

        second = clean_company_name(
            match.group(2)
        )

        # Remove words that may have been captured
        for company in [first, second]:

            if not company:
                continue

            cleaned = re.sub(
                r"^(?:compare|salary|salaries)\s+",
                "",
                company,
                flags=re.IGNORECASE
            ).strip()

            cleaned = clean_company_name(
                cleaned
            )

            if cleaned and cleaned not in companies:
                companies.append(cleaned)

    # If two were not found, try the normal extractor
    if len(companies) < 2:

        company = extract_company_from_query(
            query
        )

        if company and company not in companies:
            companies.append(company)

    return companies


# ============================================================
# DETECT HIGHEST-PAID QUERY
# ============================================================

def is_highest_paid_query(query):

    if not query:
        return False

    query = query.lower()

    patterns = [

        "highest paid employee",
        "highest-paid employee",
        "highest paid",
        "highest-paid",
        "earns the most",
        "earns most",
        "most paid",
        "top paid employee",
        "top-paid employee",
        "highest salary",
        "highest earner",
        "highest earning",
        "who makes the most",
        "who gets paid the most",
        "who is paid the most",
        "who earns the most",
        "who makes most",
    ]

    return any(
        pattern in query
        for pattern in patterns
    )


# ============================================================
# DETECT GENERAL SALARY INFORMATION QUERY
# ============================================================

def is_salary_information_query(query):

    if not query:
        return False

    query = query.lower()

    salary_terms = [
        "salary",
        "salaries",
        "pay",
        "pays",
        "paid",
        "compensation",
        "earnings",
        "earning",
        "salary structure",
        "salary information",
        "salary details",
    ]

    information_terms = [
        "information",
        "details",
        "structure",
        "statistics",
        "stats",
        "overview",
        "breakdown",
        "what are",
        "tell me",
        "show me",
        "give me",
        "what does",
        "complete salary analysis",
        "salary analysis",
    ]

    has_salary_term = any(
        term in query
        for term in salary_terms
    )

    has_information_term = any(
        term in query
        for term in information_terms
    )

    return (
        has_salary_term
        and has_information_term
    )


# ============================================================
# DETECT SALARY COMPARISON
# ============================================================

def is_salary_comparison(query):

    if not query:
        return False

    query = query.lower()

    comparison_words = [
        "compare",
        "comparison",
        "versus",
        "vs",
        "which company pays more",
        "who pays more",
    ]

    has_comparison = any(
        word in query
        for word in comparison_words
    )

    has_salary = any(
        word in query
        for word in [
            "salary",
            "salaries",
            "paid",
            "earns",
            "pay",
        ]
    )

    return (
        has_comparison
        and has_salary
    )


# ============================================================
# MCP RESULT TEXT
# ============================================================

def get_mcp_text(result):
    """
    Safely extract text from an MCP result.
    """

    if not result:
        return None

    if not getattr(result, "content", None):
        return None

    first_content = result.content[0]

    if hasattr(first_content, "text"):
        return first_content.text

    return str(first_content)


# ============================================================
# FORMAT COMPANY STATISTICS
# ============================================================

def format_company_statistics(
    company,
    text
):
    """
    Convert MCP company statistics into
    a clean salary analysis.
    """

    if not text:
        return (
            f"No salary information is available "
            f"for **{company}** in the current database."
        )

    lines = text.splitlines()

    data = {}

    for line in lines:

        if ":" not in line:
            continue

        key, value = line.split(
            ":",
            1
        )

        data[key.strip()] = value.strip()

    return (
        f"**{company} Salary Analysis**\n\n"
        f"- **Employees:** "
        f"{data.get('Employees', 'Unavailable')}\n"
        f"- **Average Salary:** "
        f"{data.get('Average Salary', 'Unavailable')}\n"
        f"- **Highest Salary:** "
        f"{data.get('Highest Salary', 'Unavailable')}\n"
        f"- **Lowest Salary:** "
        f"{data.get('Lowest Salary', 'Unavailable')}\n"
        f"- **Highest-Paid Employee:** "
        f"{data.get('Highest Paid Employee', 'Unavailable')}\n"
        f"- **Highest-Paid Role:** "
        f"{data.get('Highest Paid Role', 'Unavailable')}\n"
        f"- **Roles:** "
        f"{data.get('Roles', 'Unavailable')}"
    )


# ============================================================
# NO DATA DETECTION
# ============================================================

def mcp_has_no_data(text):

    if not text:
        return True

    no_data_patterns = [
        "not found",
        "no employees",
        "no data",
        "not available",
        "does not exist",
        "no records",
    ]

    return any(
        pattern in text.lower()
        for pattern in no_data_patterns
    )


# ============================================================
# RECORD MCP CALL
# ============================================================

def record_mcp_call(
    harness,
    tool_name,
    arguments,
    result,
    status,
    execution_time
):
    """
    Centralized MCP tracing.

    IMPORTANT:
    This records the ACTUAL MCP call after it
    has completed.
    """

    harness.record_tool_call(
        tool=tool_name,
        arguments=arguments,
        result=result,
        status=status,
        execution_time=execution_time,
    )


# ============================================================
# DIRECT HIGHEST-PAID ROUTING
# ============================================================

async def direct_highest_paid(
    session,
    company,
    harness
):

    print(
        "\n⚡ Deterministic Salary Router"
    )

    print(
        "→ Intent: HIGHEST_PAID_EMPLOYEE"
    )

    print(
        "→ Company:",
        company
    )

    print(
        "→ MCP Tool: get_company_statistics"
    )

    arguments = {
        "company": company
    }

    # --------------------------------------------------------
    # ACTUAL MCP CALL
    # --------------------------------------------------------

    tool_start = time.perf_counter()

    try:

        result = await session.call_tool(
            "get_company_statistics",
            arguments=arguments
        )

        tool_execution_time = round(
            time.perf_counter() - tool_start,
            3
        )

        tool_result = get_mcp_text(
            result
        )

        record_mcp_call(
            harness=harness,
            tool_name="get_company_statistics",
            arguments=arguments,
            result=tool_result,
            status="success",
            execution_time=tool_execution_time,
        )

    except Exception as e:

        tool_execution_time = round(
            time.perf_counter() - tool_start,
            3
        )

        record_mcp_call(
            harness=harness,
            tool_name="get_company_statistics",
            arguments=arguments,
            result=None,
            status="error",
            execution_time=tool_execution_time,
        )

        return None, (
            f"MCP tool error: {str(e)}"
        )

    # --------------------------------------------------------
    # EMPTY RESULT
    # --------------------------------------------------------

    if not tool_result:

        return None, (
            "MCP tool returned no result."
        )

    print(
        "\nMCP Result:"
    )

    print(
        tool_result
    )

    # --------------------------------------------------------
    # NO DATA
    # --------------------------------------------------------

    if mcp_has_no_data(
        tool_result
    ):

        return (
            f"No salary information is available "
            f"for **{company}** in the current database.",
            None
        )

    # --------------------------------------------------------
    # PARSE RESULT
    # --------------------------------------------------------

    data = {}

    for line in tool_result.splitlines():

        if ":" not in line:
            continue

        key, value = line.split(
            ":",
            1
        )

        data[key.strip()] = value.strip()

    employee = data.get(
        "Highest Paid Employee"
    )

    salary = data.get(
        "Highest Salary"
    )

    role = data.get(
        "Highest Paid Role"
    )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    if (
        not employee
        or not salary
        or employee.lower()
        in [
            "none",
            "null",
            "n/a",
            "unavailable",
        ]
    ):

        return (
            f"No salary information is available "
            f"for **{company}** in the current database.",
            None
        )

    # --------------------------------------------------------
    # BUILD ANSWER
    # --------------------------------------------------------

    answer = (
    f"The highest-paid employee at "
    f"**{company}** is **{employee}**, "
    f"earning **{salary}** "
)

    if role:
        answer += (
            f"as a **{role}**."
        )
    else:
        answer += "."

    return answer, None


# ============================================================
# DIRECT GENERAL SALARY INFORMATION
# ============================================================

async def direct_salary_information(
    session,
    company,
    harness
):

    print(
        "\n⚡ Deterministic Salary Router"
    )

    print(
        "→ Intent: SALARY_INFORMATION"
    )

    print(
        "→ Company:",
        company
    )

    print(
        "→ MCP Tool: get_company_statistics"
    )

    arguments = {
        "company": company
    }

    # --------------------------------------------------------
    # ACTUAL MCP CALL
    # --------------------------------------------------------

    tool_start = time.perf_counter()

    try:

        result = await session.call_tool(
            "get_company_statistics",
            arguments=arguments
        )

        tool_execution_time = round(
            time.perf_counter() - tool_start,
            3
        )

        tool_result = get_mcp_text(
            result
        )

        record_mcp_call(
            harness=harness,
            tool_name="get_company_statistics",
            arguments=arguments,
            result=tool_result,
            status="success",
            execution_time=tool_execution_time,
        )

    except Exception as e:

        tool_execution_time = round(
            time.perf_counter() - tool_start,
            3
        )

        record_mcp_call(
            harness=harness,
            tool_name="get_company_statistics",
            arguments=arguments,
            result=None,
            status="error",
            execution_time=tool_execution_time,
        )

        return None, (
            f"MCP tool error: {str(e)}"
        )

    # --------------------------------------------------------
    # EMPTY RESULT
    # --------------------------------------------------------

    if not tool_result:

        return None, (
            "MCP tool returned no result."
        )

    print(
        "\nMCP Result:"
    )

    print(
        tool_result
    )

    # --------------------------------------------------------
    # NO DATA
    # --------------------------------------------------------

    if mcp_has_no_data(
        tool_result
    ):

        return (
            f"No salary information is available "
            f"for **{company}** in the current database.",
            None
        )

    # --------------------------------------------------------
    # FORMAT ANSWER
    # --------------------------------------------------------

    answer = format_company_statistics(
        company,
        tool_result
    )

    return answer, None


# ============================================================
# DIRECT SALARY COMPARISON
# ============================================================

async def direct_salary_comparison(
    session,
    companies,
    harness
):

    print(
        "\n⚡ Deterministic Salary Router"
    )

    print(
        "→ Intent: SALARY_COMPARISON"
    )

    print(
        "→ Companies:",
        ", ".join(companies)
    )

    results = {}

    # --------------------------------------------------------
    # FETCH EACH COMPANY
    # --------------------------------------------------------

    for company in companies:

        print(
            f"\n→ Fetching statistics for "
            f"{company}"
        )

        arguments = {
            "company": company
        }

        tool_start = time.perf_counter()

        try:

            result = await session.call_tool(
                "get_company_statistics",
                arguments=arguments
            )

            tool_execution_time = round(
                time.perf_counter() - tool_start,
                3
            )

            tool_result = get_mcp_text(
                result
            )

            record_mcp_call(
                harness=harness,
                tool_name="get_company_statistics",
                arguments=arguments,
                result=tool_result,
                status="success",
                execution_time=tool_execution_time,
            )

        except Exception as e:

            tool_execution_time = round(
                time.perf_counter() - tool_start,
                3
            )

            record_mcp_call(
                harness=harness,
                tool_name="get_company_statistics",
                arguments=arguments,
                result=None,
                status="error",
                execution_time=tool_execution_time,
            )

            return None, (
                f"MCP error for {company}: "
                f"{str(e)}"
            )

        if not tool_result:

            return None, (
                f"No result returned for "
                f"{company}."
            )

        print(
            "\nMCP Result:"
        )

        print(
            tool_result
        )

        # ----------------------------------------------------
        # PARSE
        # ----------------------------------------------------

        data = {}

        for line in tool_result.splitlines():

            if ":" not in line:
                continue

            key, value = line.split(
                ":",
                1
            )

            data[key.strip()] = value.strip()

        # ----------------------------------------------------
        # HANDLE UNKNOWN COMPANY
        # ----------------------------------------------------

        if mcp_has_no_data(
            tool_result
        ):

            data = {
                "Employees": "Unavailable",
                "Average Salary": "Unavailable",
                "Highest Salary": "Unavailable",
                "Lowest Salary": "Unavailable",
                "Highest Paid Employee":
                    "Unavailable",
                "Highest Paid Role":
                    "Unavailable",
            }

        results[company] = data

    # ========================================================
    # BUILD COMPARISON
    # ========================================================

    output = (
        "**Salary Comparison**\n\n"
    )

    output += (
        "| Metric | "
        + " | ".join(companies)
        + " |\n"
    )

    output += (
        "|---|"
        + "---|" * len(companies)
        + "\n"
    )

    metrics = [

        (
            "Employees",
            "Employees"
        ),

        (
            "Average Salary",
            "Average Salary"
        ),

        (
            "Highest Salary",
            "Highest Salary"
        ),

        (
            "Lowest Salary",
            "Lowest Salary"
        ),

        (
            "Highest-Paid Employee",
            "Highest Paid Employee"
        ),

        (
            "Highest-Paid Role",
            "Highest Paid Role"
        ),

    ]

    for label, key in metrics:

        output += (
            f"| **{label}** | "
            + " | ".join(
                results[c].get(
                    key,
                    "Unavailable"
                )
                for c in companies
            )
            + " |\n"
        )

    # ========================================================
    # AVERAGE SALARY COMPARISON
    # ========================================================

    averages = {}

    for company in companies:

        raw = results[company].get(
            "Average Salary"
        )

        if not raw:
            continue

        try:

            numeric = float(
                raw.replace(",", "")
            )

            averages[company] = numeric

        except Exception:

            continue

    if len(averages) == len(companies):

        highest_company = max(
            averages,
            key=averages.get
        )

        highest_value = averages[
            highest_company
        ]

        output += (
            "\n**Key Takeaway**\n\n"
            f"**{highest_company}** has the "
            f"highest average salary at "
            f"**{highest_value:,.2f}**."
        )

    return output, None


# ============================================================
# SALARY AGENT
# ============================================================

async def salary_agent(user_query, api_key=None):

    harness = AgentHarness(
        agent_name="salary_agent",
        max_iterations=MAX_ITERATIONS
    )

    harness.start()

    request_llm = get_request_llm(api_key)

    try:

        # ====================================================
        # CONNECT TO MCP
        # ====================================================

        async with stdio_client(
            server_params
        ) as (read, write):

            async with ClientSession(
                read,
                write
            ) as session:

                await session.initialize()

                print(
                    "\n[Salary Agent] MCP connected"
                )

                # =================================================
                # DISCOVER TOOLS
                # =================================================

                tools = await session.list_tools()

                openrouter_tools = convert_tools(
                    tools.tools
                )

                print(
                    "[Salary Agent] Tools discovered:",
                    len(tools.tools)
                )

                # =================================================
                # EXTRACT COMPANY
                # =================================================

                company = extract_company_from_query(
                    user_query
                )

                companies = extract_companies_from_query(
                    user_query
                )

                if company and company not in companies:
                    companies.insert(
                        0,
                        company
                    )

                # =================================================
                # SALARY COMPARISON
                # =================================================

                if (
                    is_salary_comparison(
                        user_query
                    )
                    and len(companies) >= 2
                ):

                    companies = companies[:2]

                    answer, error = (
                        await direct_salary_comparison(
                            session,
                            companies,
                            harness
                        )
                    )

                    if error:

                        result = harness.error(
                            error
                        )

                        harness.print_summary(
                            result
                        )

                        return result

                    print(
                        "\nSalary Agent:"
                    )

                    print(
                        answer
                    )

                    result = harness.success(
                        answer
                    )

                    harness.print_summary(
                        result
                    )

                    return result

                # =================================================
                # HIGHEST PAID
                # =================================================

                if (
                    is_highest_paid_query(
                        user_query
                    )
                    and len(companies) == 1
                ):

                    answer, error = (
                        await direct_highest_paid(
                            session,
                            companies[0],
                            harness
                        )
                    )

                    if error:

                        result = harness.error(
                            error
                        )

                        harness.print_summary(
                            result
                        )

                        return result

                    print(
                        "\nSalary Agent:"
                    )

                    print(
                        answer
                    )

                    result = harness.success(
                        answer
                    )

                    harness.print_summary(
                        result
                    )

                    return result

                # =================================================
                # GENERAL SALARY INFORMATION
                # =================================================

                if (
                    is_salary_information_query(
                        user_query
                    )
                    and len(companies) == 1
                    and not is_highest_paid_query(
                        user_query
                    )
                ):

                    answer, error = (
                        await direct_salary_information(
                            session,
                            companies[0],
                            harness
                        )
                    )

                    if error:

                        result = harness.error(
                            error
                        )

                        harness.print_summary(
                            result
                        )

                        return result

                    print(
                        "\nSalary Agent:"
                    )

                    print(
                        answer
                    )

                    result = harness.success(
                        answer
                    )

                    harness.print_summary(
                        result
                    )

                    return result

                # =================================================
                # LLM FALLBACK
                # =================================================

                print(
                    "\n🧠 Deterministic router "
                    "could not resolve query."
                )

                print(
                    "→ Falling back to Salary "
                    "Agent LLM..."
                )

                messages = [

                    {
                        "role": "system",
                        "content":
                            SALARY_AGENT_PROMPT
                    },

                    {
                        "role": "user",
                        "content":
                            user_query
                    }

                ]

                # =================================================
                # AGENT LOOP
                # =================================================

                for iteration in range(
                    MAX_ITERATIONS
                ):

                    harness.next_iteration()

                    print(
                        f"\n[Salary Agent] "
                        f"Iteration {iteration + 1}"
                    )

                    # ---------------------------------------------
                    # LLM CALL
                    # ---------------------------------------------

                    try:

                        response = (
                            request_llm.chat.completions.create(
                                model="openrouter/free",
                                max_tokens=500,
                                messages=messages,
                                tools=openrouter_tools,
                                tool_choice="auto"
                            )
                        )

                    except Exception as e:

                        print(
                            "\n[Salary Agent] "
                            "LLM ERROR:"
                        )

                        print(e)

                        return harness.error(
                            f"LLM error: {str(e)}"
                        )

                    if not response.choices:

                        return harness.error(
                            "LLM returned no choices."
                        )

                    message = (
                        response
                        .choices[0]
                        .message
                    )

                    # ---------------------------------------------
                    # EMPTY RESPONSE
                    # ---------------------------------------------

                    if (
                        not message.content
                        and not message.tool_calls
                    ):

                        return harness.error(
                            "LLM returned an empty response."
                        )

                    # ---------------------------------------------
                    # FINAL ANSWER
                    # ---------------------------------------------

                    if not message.tool_calls:

                        answer = (
                            message.content
                            or "No answer generated."
                        )

                        print(
                            "\nSalary Agent:"
                        )

                        print(
                            answer
                        )

                        result = harness.success(
                            answer
                        )

                        harness.print_summary(
                            result
                        )

                        return result

                    # ---------------------------------------------
                    # SAVE ASSISTANT MESSAGE
                    # ---------------------------------------------

                    messages.append(
                        message.model_dump(
                            exclude_none=True
                        )
                    )

                    # ---------------------------------------------
                    # EXECUTE MCP TOOLS
                    # ---------------------------------------------

                    for tool_call in (
                        message.tool_calls
                    ):

                        tool_name = (
                            tool_call
                            .function
                            .name
                        )

                        # -----------------------------------------
                        # PARSE ARGUMENTS
                        # -----------------------------------------

                        try:

                            arguments = json.loads(
                                tool_call
                                .function
                                .arguments
                            )

                        except json.JSONDecodeError as e:

                            return harness.error(
                                "Invalid tool arguments: "
                                f"{str(e)}"
                            )

                        print(
                            "\nSalary Agent Tool:"
                        )

                        print(
                            "Tool:",
                            tool_name
                        )

                        print(
                            "Arguments:",
                            arguments
                        )

                        # -----------------------------------------
                        # ACTUAL MCP CALL
                        # -----------------------------------------

                        tool_start = time.perf_counter()

                        try:

                            mcp_result = (
                                await session.call_tool(
                                    tool_name,
                                    arguments=arguments
                                )
                            )

                            tool_execution_time = round(
                                time.perf_counter()
                                - tool_start,
                                3
                            )

                            tool_result = get_mcp_text(
                                mcp_result
                            )

                            # -------------------------------------
                            # RECORD ACTUAL MCP CALL
                            # -------------------------------------

                            record_mcp_call(
                                harness=harness,
                                tool_name=tool_name,
                                arguments=arguments,
                                result=tool_result,
                                status="success",
                                execution_time=
                                    tool_execution_time,
                            )

                        except Exception as e:

                            tool_execution_time = round(
                                time.perf_counter()
                                - tool_start,
                                3
                            )

                            record_mcp_call(
                                harness=harness,
                                tool_name=tool_name,
                                arguments=arguments,
                                result=None,
                                status="error",
                                execution_time=
                                    tool_execution_time,
                            )

                            return harness.error(
                                f"MCP tool '{tool_name}' "
                                f"failed: {str(e)}"
                            )

                        # -----------------------------------------
                        # HANDLE EMPTY RESULT
                        # -----------------------------------------

                        if not tool_result:

                            tool_result = (
                                "The MCP tool returned "
                                "no usable result."
                            )

                        print(
                            "\nMCP Result:"
                        )

                        print(
                            tool_result
                        )

                        # -----------------------------------------
                        # SEND RESULT BACK TO LLM
                        # -----------------------------------------

                        messages.append(
                            {
                                "role": "tool",

                                "tool_call_id":
                                    tool_call.id,

                                "content":
                                    tool_result,
                            }
                        )

                # =================================================
                # MAX ITERATIONS
                # =================================================

                return harness.error(
                    "Maximum agent iterations "
                    f"({MAX_ITERATIONS}) reached."
                )

    # ============================================================
    # UNEXPECTED ERROR
    # ============================================================

    except Exception as e:

        print(
            "\n[Salary Agent] "
            "UNEXPECTED ERROR:"
        )

        print(e)

        return harness.error(
            str(e)
        )


# ============================================================
# COMMAND LINE TEST
# ============================================================

if __name__ == "__main__":

    query = input(
        "Salary Agent Query: "
    )

    result = asyncio.run(
        salary_agent(query)
    )

    print(
        "\n================================"
    )

    print(
        "STRUCTURED AGENT RESULT"
    )

    print(
        "================================"
    )

    print(
        json.dumps(
            result,
            indent=2,
            default=str
        )
    )