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
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# OPENROUTER
# ============================================================

def get_request_llm(api_key=None):
    """Return an OpenRouter client for this request.

    When api_key is provided, it is used only for the current
    request. Otherwise the project-level OPENROUTER_API_KEY is used.
    """
    selected_key = api_key or os.getenv("OPENROUTER_API_KEY")

    if not selected_key:
        raise RuntimeError(
            "No OpenRouter API key is configured."
        )

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=selected_key
    )


# Backward-compatible default client for existing code/tests.
llm = get_request_llm()


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
MAX_TOOL_CALLS = 10


# ============================================================
# CONVERT MCP TO OPENROUTER TOOLS
# ============================================================

def convert_tools(mcp_tools):

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
# COMPANY AGENT PROMPT
# ============================================================

COMPANY_AGENT_PROMPT = """
You are a specialized Company Analysis Agent.

Your responsibility is to answer questions about:

- Companies
- Company information
- Employees belonging to a company
- Company statistics
- Company workforce
- Roles within a company
- Company-level analysis

Use MCP tools whenever company or employee database
information is required.

For a complete analysis of one specific company,
prefer the get_company_statistics MCP tool.

Never invent company or employee information.

Do not assume information that is not present
in the database.

Use the minimum number of MCP tools necessary
to answer the user's question.

Return clear and concise answers.

If the database does not contain the requested
information, clearly say that the information is unavailable.

IMPORTANT:

The MCP database is the source of truth.

Never invent a company, employee, role, salary,
or statistic that is not returned by MCP.
"""


# ============================================================
# COMPANY EXTRACTION
# ============================================================

def extract_company_from_query(query):

    query = query.strip()

    patterns = [
        r"\btell me about\s+([A-Za-z][A-Za-z0-9&.\- ]*?)(?:\?|$)",
        # Give me a complete analysis of Google.
        r"\bof\s+([A-Za-z][A-Za-z0-9&.\- ]*?)(?:\?|$)",

        # Analyze Tesla.
        r"\banalyze\s+([A-Za-z][A-Za-z0-9&.\- ]*?)(?:\?|$)",

        # Show me employees working at Tesla.
        r"\bat\s+([A-Za-z][A-Za-z0-9&.\- ]*?)(?:\?|$)",

        # employees at Google
        r"\bat\s+([A-Za-z][A-Za-z0-9&.\- ]*?)(?:\s+(?:employees|employee|roles|role|workforce|salary|statistics))",

        # employees working in Google
        r"\bin\s+([A-Za-z][A-Za-z0-9&.\- ]*?)(?:\?|$)",

        # company Google
        r"\bcompany\s+([A-Za-z][A-Za-z0-9&.\- ]*?)(?:\?|$)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            query,
            re.IGNORECASE
        )

        if match:

            company = match.group(1).strip()

            # Remove punctuation
            company = company.rstrip(
                ".,!?;:"
            ).strip()

            # Remove trailing common words
            company = re.sub(
                r"\s+(?:employees|employee|roles|role|"
                r"workforce|salary|statistics|analysis|"
                r"information|overview)$",
                "",
                company,
                flags=re.IGNORECASE
            ).strip()

            company = company.rstrip(
                ".,!?;:"
            ).strip()

            if company:
                return company

    return None


# ============================================================
# COMPANY ANALYSIS INTENT
# ============================================================

def is_company_analysis_query(query):

    q = query.lower()

    patterns = [
        "complete analysis",
        "company analysis",
        "analyze ",
        "analysis of",
        "company statistics",
        "company overview",
        "company information",
        "tell me about",
    "information about",
    ]

    return any(
        pattern in q
        for pattern in patterns
    )


# ============================================================
# EMPLOYEE QUERY
# ============================================================

def is_employee_query(query):

    q = query.lower()

    patterns = [
        "employees at",
        "employees working at",
        "employees working in",
        "show me employees",
        "who works at",
        "who work at",
        "list employees",
        "workforce",
    ]

    return any(
        pattern in q
        for pattern in patterns
    )


# ============================================================
# ROLES QUERY
# ============================================================

def is_roles_query(query):

    q = query.lower()

    patterns = [
        "what roles exist",
        "which roles",
        "what roles are",
        "roles at",
        "roles within",
        "roles in",
    ]

    return any(
        pattern in q
        for pattern in patterns
    )


# ============================================================
# PARSE STATISTICS
# ============================================================

def parse_statistics(text):

    data = {}

    for line in text.splitlines():

        if ":" not in line:
            continue

        key, value = line.split(
            ":",
            1
        )

        data[key.strip()] = value.strip()

    return data


# ============================================================
# CHECK NO DATA
# ============================================================

def is_no_data_result(text):

    no_data_patterns = [
        "not found",
        "no employees",
        "no data",
        "not available",
        "does not exist",
        "no records",
        "no company",
    ]

    text_lower = text.lower()

    return any(
        pattern in text_lower
        for pattern in no_data_patterns
    )


# ============================================================
# DIRECT COMPANY ANALYSIS
# ============================================================

async def direct_company_analysis(
    session,
    company,
    harness
):

    print(
        "\n⚡ Deterministic Company Router"
    )

    print(
        "→ Intent: COMPANY_ANALYSIS"
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

    start = time.perf_counter()

    try:

        result = await session.call_tool(
            "get_company_statistics",
            arguments=arguments
        )

    except Exception as e:

        execution_time = round(
            time.perf_counter() - start,
            3
        )

        harness.record_tool_call(
            agent="company_agent",
            tool="get_company_statistics",
            arguments=arguments,
            result=None,
            status="error",
            execution_time=execution_time
        )

        return None, (
            f"MCP error: {str(e)}"
        )

    execution_time = round(
        time.perf_counter() - start,
        3
    )

    if not result.content:

        harness.record_tool_call(
            agent="company_agent",
            tool="get_company_statistics",
            arguments=arguments,
            result=None,
            status="error",
            execution_time=execution_time
        )

        return None, (
            "MCP tool returned no result."
        )

    tool_result = result.content[0].text

    harness.record_tool_call(
        agent="company_agent",
        tool="get_company_statistics",
        arguments=arguments,
        result=tool_result,
        status="success",
        execution_time=execution_time
    )

    print(
        "\nMCP Result:"
    )

    print(
        tool_result
    )

    # ========================================================
    # NO COMPANY DATA
    # ========================================================

    if is_no_data_result(tool_result):

        return (
            f"No company information is "
            f"available for **{company}** "
            f"in the current database.",
            None
        )

    # ========================================================
    # PARSE RESULT
    # ========================================================

    data = parse_statistics(
        tool_result
    )

    answer = (

        f"**{company} – Company Analysis**\n\n"

        f"| Metric | Value |\n"
        f"|---|---|\n"

        f"| **Employees** | "
        f"{data.get('Employees', 'Unavailable')} |\n"

        f"| **Average Salary** | "
        f"{data.get('Average Salary', 'Unavailable')} |\n"

        f"| **Highest Salary** | "
        f"{data.get('Highest Salary', 'Unavailable')} |\n"

        f"| **Lowest Salary** | "
        f"{data.get('Lowest Salary', 'Unavailable')} |\n"

        f"| **Highest-Paid Employee** | "
        f"{data.get('Highest Paid Employee', 'Unavailable')} |\n"

        f"| **Highest-Paid Role** | "
        f"{data.get('Highest Paid Role', 'Unavailable')} |\n"

        f"| **Roles Represented** | "
        f"{data.get('Roles', 'Unavailable')} |"
    )

    return answer, None


# ============================================================
# DIRECT COMPANY EMPLOYEES
# ============================================================

async def direct_company_employees(
    session,
    company,
    harness
):

    print(
        "\n⚡ Deterministic Company Router"
    )

    print(
        "→ Intent: COMPANY_EMPLOYEES"
    )

    print(
        "→ Company:",
        company
    )

    print(
        "→ MCP Tool: company_search"
    )

    arguments = {
        "query": company
    }

    start = time.perf_counter()

    try:

        result = await session.call_tool(
            "company_search",
            arguments=arguments
        )

    except Exception as e:

        execution_time = round(
            time.perf_counter() - start,
            3
        )

        harness.record_tool_call(
            agent="company_agent",
            tool="company_search",
            arguments=arguments,
            result=None,
            status="error",
            execution_time=execution_time
        )

        return None, (
            f"MCP error: {str(e)}"
        )

    execution_time = round(
        time.perf_counter() - start,
        3
    )

    if not result.content:

        harness.record_tool_call(
            agent="company_agent",
            tool="company_search",
            arguments=arguments,
            result=None,
            status="error",
            execution_time=execution_time
        )

        return None, (
            "MCP tool returned no result."
        )

    tool_result = result.content[0].text

    harness.record_tool_call(
        agent="company_agent",
        tool="company_search",
        arguments=arguments,
        result=tool_result,
        status="success",
        execution_time=execution_time
    )

    print(
        "\nMCP Result:"
    )

    print(
        tool_result
    )

    # ========================================================
    # NO DATA
    # ========================================================

    if is_no_data_result(tool_result):

        return (
            f"No employees were found for "
            f"**{company}** in the current database.",
            None
        )

    # ========================================================
    # PARSE EMPLOYEES
    # ========================================================

    rows = []

    for line in tool_result.splitlines():

        if not line.strip():
            continue

        parts = [
            part.strip()
            for part in line.split(",")
        ]

        row = {}

        for part in parts:

            if ":" in part:

                key, value = part.split(
                    ":",
                    1
                )

                row[key.strip()] = (
                    value.strip()
                )

        if row:
            rows.append(row)

    if not rows:

        return (
            f"No employees were found for "
            f"**{company}** in the current database.",
            None
        )

    # ========================================================
    # BUILD TABLE
    # ========================================================

    answer = (
        f"**Employees at {company}**\n\n"
        "| ID | Name | Role | Salary |\n"
        "|---|---|---|---|\n"
    )

    for row in rows:

        answer += (
            f"| {row.get('ID', '-')} "
            f"| {row.get('Name', '-')} "
            f"| {row.get('Role', '-')} "
            f"| {row.get('Salary', '-')} |\n"
        )

    return answer, None


# ============================================================
# DIRECT COMPANY ROLES
# ============================================================

async def direct_company_roles(
    session,
    company,
    harness
):

    print(
        "\n⚡ Deterministic Company Router"
    )

    print(
        "→ Intent: COMPANY_ROLES"
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

    start = time.perf_counter()

    try:

        result = await session.call_tool(
            "get_company_statistics",
            arguments=arguments
        )

    except Exception as e:

        execution_time = round(
            time.perf_counter() - start,
            3
        )

        harness.record_tool_call(
            agent="company_agent",
            tool="get_company_statistics",
            arguments=arguments,
            result=None,
            status="error",
            execution_time=execution_time
        )

        return None, (
            f"MCP error: {str(e)}"
        )

    execution_time = round(
        time.perf_counter() - start,
        3
    )

    if not result.content:

        harness.record_tool_call(
            agent="company_agent",
            tool="get_company_statistics",
            arguments=arguments,
            result=None,
            status="error",
            execution_time=execution_time
        )

        return None, (
            "MCP tool returned no result."
        )

    tool_result = result.content[0].text

    harness.record_tool_call(
        agent="company_agent",
        tool="get_company_statistics",
        arguments=arguments,
        result=tool_result,
        status="success",
        execution_time=execution_time
    )

    print(
        "\nMCP Result:"
    )

    print(
        tool_result
    )

    # ========================================================
    # NO DATA
    # ========================================================

    if is_no_data_result(tool_result):

        return (
            f"No role information is "
            f"available for **{company}** "
            f"in the current database.",
            None
        )

    data = parse_statistics(
        tool_result
    )

    roles = data.get(
        "Roles",
        "Unavailable"
    )

    answer = (

        f"**Roles at {company}**\n\n"

        f"The roles represented in the "
        f"current database are: "
        f"**{roles}**."
    )

    return answer, None


# ============================================================
# COMPANY AGENT
# ============================================================

async def company_agent(
    user_query,
    api_key=None
):

    harness = AgentHarness(
        agent_name="company_agent",
        max_iterations=MAX_ITERATIONS,
        max_tool_calls=MAX_TOOL_CALLS
    )

    harness.start()

    request_llm = get_request_llm(api_key)

    try:

        # ====================================================
        # CONNECT MCP
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
                    "\n[Company Agent] MCP connected"
                )

                # =================================================
                # DISCOVER TOOLS
                # =================================================

                tools = await session.list_tools()

                openrouter_tools = convert_tools(
                    tools.tools
                )

                print(
                    "[Company Agent] "
                    "Tools discovered:",
                    len(tools.tools)
                )

                # =================================================
                # EXTRACT COMPANY
                # =================================================

                company = extract_company_from_query(
                    user_query
                )

                # =================================================
                # DETERMINISTIC ROUTING
                # =================================================

                if company:

                    # =============================================
                    # COMPANY ANALYSIS
                    # =============================================

                    if is_company_analysis_query(
                        user_query
                    ):

                        answer, error = (
                            await direct_company_analysis(
                                session,
                                company,
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
                            "\nCompany Agent:"
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

                    # =============================================
                    # EMPLOYEE QUERY
                    # =============================================

                    if is_employee_query(
                        user_query
                    ):

                        answer, error = (
                            await direct_company_employees(
                                session,
                                company,
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
                            "\nCompany Agent:"
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

                    # =============================================
                    # ROLE QUERY
                    # =============================================

                    if is_roles_query(
                        user_query
                    ):

                        answer, error = (
                            await direct_company_roles(
                                session,
                                company,
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
                            "\nCompany Agent:"
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
                    "→ Falling back to Company "
                    "Agent LLM..."
                )

                messages = [

                    {
                        "role": "system",
                        "content": COMPANY_AGENT_PROMPT
                    },

                    {
                        "role": "user",
                        "content": user_query
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
                        f"\n[Company Agent] "
                        f"Iteration {iteration + 1}"
                    )

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
                            "\n[Company Agent] "
                            "LLM ERROR:"
                        )

                        print(e)

                        result = harness.error(
                            f"LLM error: {str(e)}"
                        )

                        harness.print_summary(
                            result
                        )

                        return result

                    if not response.choices:

                        result = harness.error(
                            "LLM returned no choices."
                        )

                        harness.print_summary(
                            result
                        )

                        return result

                    message = (
                        response
                        .choices[0]
                        .message
                    )

                    # =================================================
                    # EMPTY RESPONSE
                    # =================================================

                    if (
                        not message.content
                        and not message.tool_calls
                    ):

                        result = harness.error(
                            "LLM returned an empty response."
                        )

                        harness.print_summary(
                            result
                        )

                        return result

                    # =================================================
                    # FINAL ANSWER
                    # =================================================

                    if not message.tool_calls:

                        answer = (
                            message.content
                            or "No answer generated."
                        )

                        print(
                            "\nCompany Agent:"
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
                    # SAVE ASSISTANT TOOL CALL
                    # =================================================

                    messages.append(
                        message.model_dump(
                            exclude_none=True
                        )
                    )

                    # =================================================
                    # EXECUTE MCP TOOLS
                    # =================================================

                    for tool_call in message.tool_calls:

                        # Safety limit
                        try:
                            harness.record_tool_call_limit = (
                                harness.record_tool_call
                            )
                        except Exception:
                            pass

                        tool_name = (
                            tool_call
                            .function
                            .name
                        )

                        # =============================================
                        # PARSE ARGUMENTS
                        # =============================================

                        try:

                            arguments = json.loads(
                                tool_call
                                .function
                                .arguments
                            )

                        except json.JSONDecodeError as e:

                            result = harness.error(
                                "Invalid tool arguments: "
                                f"{str(e)}"
                            )

                            harness.print_summary(
                                result
                            )

                            return result

                        print(
                            "\nCompany Agent Tool:"
                        )

                        print(
                            "Tool:",
                            tool_name
                        )

                        print(
                            "Arguments:",
                            arguments
                        )

                        # =============================================
                        # MCP CALL
                        # =============================================

                        start = time.perf_counter()

                        try:

                            mcp_result = (
                                await session.call_tool(
                                    tool_name,
                                    arguments=arguments
                                )
                            )

                        except Exception as e:

                            execution_time = round(
                                time.perf_counter() - start,
                                3
                            )

                            harness.record_tool_call(
                                agent="company_agent",
                                tool=tool_name,
                                arguments=arguments,
                                result=None,
                                status="error",
                                execution_time=execution_time
                            )

                            result = harness.error(
                                f"MCP tool '{tool_name}' "
                                f"failed: {str(e)}"
                            )

                            harness.print_summary(
                                result
                            )

                            return result

                        execution_time = round(
                            time.perf_counter() - start,
                            3
                        )

                        # =============================================
                        # EXTRACT MCP RESULT
                        # =============================================

                        if (
                            mcp_result.content
                            and hasattr(
                                mcp_result.content[0],
                                "text"
                            )
                        ):

                            tool_result = (
                                mcp_result
                                .content[0]
                                .text
                            )

                        else:

                            tool_result = (
                                "The MCP tool returned "
                                "no usable result."
                            )

                        # =============================================
                        # RECORD OBSERVABILITY
                        # =============================================

                        harness.record_tool_call(
                            agent="company_agent",
                            tool=tool_name,
                            arguments=arguments,
                            result=tool_result,
                            status="success",
                            execution_time=execution_time
                        )

                        print(
                            "\nMCP Result:"
                        )

                        print(
                            tool_result
                        )

                        # =============================================
                        # SEND RESULT BACK TO LLM
                        # =============================================

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id":
                                    tool_call.id,
                                "content":
                                    tool_result
                            }
                        )

                # =================================================
                # MAX ITERATIONS
                # =================================================

                result = harness.error(
                    "Maximum agent iterations "
                    f"({MAX_ITERATIONS}) reached."
                )

                harness.print_summary(
                    result
                )

                return result

    except Exception as e:

        print(
            "\n[Company Agent] "
            "UNEXPECTED ERROR:"
        )

        print(e)

        result = harness.error(
            str(e)
        )

        harness.print_summary(
            result
        )

        return result


# ============================================================
# TEST COMPANY AGENT
# ============================================================

if __name__ == "__main__":

    query = input(
        "Company Agent Query: "
    )

    result = asyncio.run(
        company_agent(query)
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