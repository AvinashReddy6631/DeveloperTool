import asyncio
import os
import re
import time

from dotenv import load_dotenv
from openai import OpenAI

from salary_agent import salary_agent
from company_agent import company_agent
from weather_agent import weather_agent
from synthesizer import synthesize

from database import (
    save_conversation as db_save_conversation,
    get_recent_conversation_context,
)


# ============================================================
# EXECUTION OBSERVABILITY
# ============================================================

class ExecutionTrace:
    """Collect a lightweight trace for one orchestrator request."""

    def __init__(self, query):
        self.query = query
        self.started_at = time.perf_counter()
        self.orchestrator = None
        self.agents = []
        self.mcp_calls = []
        self.events = []

    def set_orchestrator(self, decision):
        self.orchestrator = decision
        self.events.append({
            "type": "orchestrator_decision",
            "decision": decision,
        })

    def add_agent(self, agent):
        if agent not in self.agents:
            self.agents.append(agent)
        self.events.append({
            "type": "agent",
            "agent": agent,
        })

    def add_mcp_call(
        self,
        agent,
        tool,
        arguments=None,
        status="success",
        execution_time=0.0,
    ):
        call = {
            "agent": agent,
            "tool": tool,
            "arguments": arguments or {},
            "status": status,
            "execution_time": round(float(execution_time), 3),
        }
        self.mcp_calls.append(call)
        self.events.append({
            "type": "mcp_call",
            **call,
        })

    def finish(self, status, answer=None):
        total_time = time.perf_counter() - self.started_at
        self.events.append({
            "type": "final",
            "status": status,
        })
        return {
            "query": self.query,
            "orchestrator": self.orchestrator,
            "agents": self.agents,
            "mcp_calls": self.mcp_calls,
            "final_status": status,
            "final_answer": answer,
            "total_execution_time": round(total_time, 3),
        }

    def print_report(self, report):
        print("\n" + "=" * 60)
        print("MCP EXECUTION TRACE")
        print("=" * 60)

        print(f"\nQuery: {report['query']}")
        print(f"\nOrchestrator: {report['orchestrator'] or 'UNKNOWN'}")
        print(
            "\nAgents: "
            + (
                ", ".join(report["agents"])
                if report["agents"]
                else "none"
            )
        )
        print(f"\nMCP Calls: {len(report['mcp_calls'])}")

        for index, call in enumerate(report["mcp_calls"], start=1):
            print(f"\nTool Call #{index}")
            print(f"  Agent: {call['agent']}")
            print(f"  Tool: {call['tool']}")
            print(f"  Arguments: {call['arguments']}")
            print(f"  Status: {call['status']}")
            print(
                "  Execution Time: "
                f"{call['execution_time']:.3f}s"
            )

        print(f"\nFinal Status: {report['final_status']}")

        if report["final_answer"]:
            print("\nFinal Answer:")
            print(report["final_answer"])

        print(
            "\nTotal Execution Time: "
            f"{report['total_execution_time']:.3f}s"
        )
        print("\n" + "=" * 60)


def _infer_mcp_trace(agent_name, result):
    """
    Extract MCP/tool information from the agent result when the agent
    exposes it. Falls back to the harness tool_calls count without
    inventing tool names or arguments.
    """
    if not isinstance(result, dict):
        return []

    trace_items = []

    possible_calls = (
        result.get("mcp_calls")
        or result.get("tool_call_details")
        or result.get("tool_calls_detail")
        or result.get("tool_history")
    )

    if isinstance(possible_calls, list):
        for item in possible_calls:
            if not isinstance(item, dict):
                continue

            trace_items.append({
                "agent": agent_name,
                "tool": (
                    item.get("tool")
                    or item.get("tool_name")
                    or "unknown"
                ),
                "arguments": (
                    item.get("arguments")
                    or item.get("args")
                    or {}
                ),
                "status": item.get("status", "success"),
                "execution_time": item.get(
                    "execution_time",
                    item.get("duration", 0.0),
                ),
            })

    return trace_items


def _record_agent_trace(trace, result, fallback_agent):
    """
    Record agent execution and MCP activity.

    If the agent exposes detailed MCP call information, use it.

    Otherwise, if the agent reports tool_calls > 0, create a
    trace entry using the deterministic MCP tool used by our
    current agents.

    This keeps observability accurate without requiring the
    agents to expose internal MCP implementation details.
    """

    if not isinstance(result, dict):
        trace.add_agent(fallback_agent)
        return

    agent_name = result.get(
        "agent",
        fallback_agent
    )

    trace.add_agent(agent_name)

    # --------------------------------------------------------
    # 1. Prefer real MCP call details if exposed
    # --------------------------------------------------------

    detailed_calls = _infer_mcp_trace(
        agent_name,
        result
    )

    if detailed_calls:

        for call in detailed_calls:

            trace.add_mcp_call(
                agent=call["agent"],
                tool=call["tool"],
                arguments=call["arguments"],
                status=call["status"],
                execution_time=call["execution_time"]
            )

        return

    # --------------------------------------------------------
    # 2. Fallback to the agent's tool_calls count
    # --------------------------------------------------------

    tool_call_count = result.get(
        "tool_calls",
        0
    )

    if not isinstance(tool_call_count, int):
        try:
            tool_call_count = int(
                tool_call_count
            )
        except Exception:
            tool_call_count = 0

    if tool_call_count <= 0:
        return

    # --------------------------------------------------------
    # 3. Determine the MCP tool
    #
    # Current Salary Agent:
    # get_company_statistics
    #
    # Current Company Agent:
    # - company_search for employee queries
    # - get_company_statistics otherwise
    # --------------------------------------------------------

    tool_name = "get_company_statistics"

    # The agent result may contain the original query.
    agent_query = (
        result.get("query")
        or result.get("user_query")
        or ""
    )

    query_lower = str(
        agent_query
    ).lower()

    if (
        agent_name == "company_agent"
        and (
            "employee" in query_lower
            or "employees" in query_lower
            or "workforce" in query_lower
        )
    ):
        tool_name = "company_search"

    # --------------------------------------------------------
    # 4. Extract company from the query
    # --------------------------------------------------------

    companies = extract_companies(
        str(agent_query)
    )

    arguments = {}

    if companies:

        arguments = {
            "company": companies[0]
        }

    # --------------------------------------------------------
    # 5. Record the reported MCP call
    # --------------------------------------------------------

    execution_time = result.get(
        "execution_time",
        0.0
    )

    try:
        execution_time = float(
            execution_time
        )
    except Exception:
        execution_time = 0.0

    # If multiple calls are reported, record each one.
    for _ in range(tool_call_count):

        trace.add_mcp_call(
            agent=agent_name,
            tool=tool_name,
            arguments=arguments,
            status=(
                "success"
                if result.get("status") == "success"
                else "error"
            ),
            execution_time=execution_time
        )

# ============================================================
# SESSION-BASED CONVERSATION MEMORY
# ============================================================

# Each session gets its own conversation history.
# This keeps one user's context isolated from another user's context.
session_memories = {}

# Backward-compatible default conversation history.
#
# Existing tests and older code use:
#     orchestrator.conversation_history.clear()
#
# Keep this alias connected to the "default" session so those calls
# continue to work without disabling session-based memory.
conversation_history = session_memories.setdefault(
    "default",
    []
)

# Maximum history entries stored for each session.
MAX_HISTORY_ENTRIES = 15

# Maximum number of sessions kept in memory.
# Old sessions are removed when this limit is exceeded.
MAX_SESSIONS = 100


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# OPENROUTER
# ============================================================

llm = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


# ============================================================
# ORCHESTRATOR PROMPT
# ============================================================

ORCHESTRATOR_PROMPT = """
You are the Orchestrator Agent.

Your ONLY job is to route the request.

AVAILABLE AGENTS:

SALARY
- Employee salary questions
- Highest-paid employees
- Lowest-paid employees
- Salary comparisons
- Salary thresholds
- Who earns the most
- Salary statistics

COMPANY
- Company information
- Company analysis
- Employees
- Workforce
- Roles
- Departments
- Companies in the database
- General employee/company information

WEATHER
- Current weather
- Temperature
- Forecast
- Rain
- Humidity
- Wind
- Weather conditions

BOTH
Use BOTH when the user requests salary information AND
company/employee information in the same request.

Examples:

Who is the highest paid employee at Google?
SALARY

Give me a complete analysis of Google.
COMPANY

Show me employees working at Google.
COMPANY

What roles exist at Google?
COMPANY

Analyze Google and tell me who earns the most and what roles exist.
BOTH

What is the weather in Hyderabad?
WEATHER

Return ONLY:
SALARY
COMPANY
BOTH
"""


# ============================================================
# KNOWN COMPANIES
# ============================================================

KNOWN_COMPANIES = [
    "google",
    "microsoft",
    "amazon",
    "apple",
    "meta",
    "facebook",
    "netflix",
    "tesla",
    "ibm",
    "oracle",
]


# ============================================================
# EXTRACT COMPANIES
# ============================================================

def extract_companies(text):
    """
    Extract known company names from text.
    """

    text_lower = text.lower()

    found = []

    for company in KNOWN_COMPANIES:

        if re.search(
            rf"\b{re.escape(company)}\b",
            text_lower
        ):

            formatted = company.title()

            if formatted not in found:
                found.append(formatted)

    return found


# ============================================================
# RECENT CONTEXT
# ============================================================

def get_recent_context(session_id="default"):
    """
    Load recent context.

    Real browser sessions use PostgreSQL so context survives a
    backend restart. The default session remains in-memory for
    backward compatibility with the existing tests.
    """

    if session_id == "default":

        history = session_memories.get(
            session_id,
            []
        )

        if not history:
            return ""

        return "\n".join(
            history[-8:]
        )

    try:

        context = get_recent_conversation_context(
            session_id,
            limit=8
        )

        if context:
            return context

    except Exception as exc:

        print(
            "\n⚠️ PostgreSQL context read failed:"
        )

        print(exc)

        print(
            "→ Falling back to in-memory history."
        )

    history = session_memories.get(
        session_id,
        []
    )

    if not history:
        return ""

    return "\n".join(
        history[-8:]
    )



# ============================================================
# LOCAL CONTEXT RESOLVER
# ============================================================

def local_context_resolution(
    user_query,
    session_id="default"
):

    # PostgreSQL-backed sessions may have no in-memory history
    # after a backend restart, so always load context through
    # get_recent_context(). The helper uses PostgreSQL first for
    # real sessions and falls back to memory if necessary.

    query = user_query.lower().strip()

    history = get_recent_context(
        session_id
    )

    if not history:
        return None
    history_lower = history.lower()

    companies_in_history = extract_companies(history)
    companies_in_query = extract_companies(user_query)

    # Most recent company known from persisted session context.
    last_company = (
        companies_in_history[-1]
        if companies_in_history
        else None
    )

    # --------------------------------------------------------
    # "What about Microsoft?"
    # --------------------------------------------------------

    if query.startswith("what about"):

        if companies_in_query:

            new_company = companies_in_query[0]

            if (
                "analysis" in history_lower
                or "analyze" in history_lower
                or "complete analysis" in history_lower
            ):
                return (
                    f"Give me a complete analysis "
                    f"of {new_company}."
                )

            if (
                "salary" in history_lower
                or "highest paid" in history_lower
                or "highest-paid" in history_lower
                or "earns" in history_lower
            ):
                return (
                    f"Give me the salary statistics "
                    f"for {new_company}."
                )

            if (
                "employee" in history_lower
                or "employees" in history_lower
                or "workforce" in history_lower
            ):
                return (
                    f"Show me employees working "
                    f"at {new_company}."
                )

            return (
                f"Give me information about "
                f"{new_company}."
            )

    # --------------------------------------------------------
    # Higher average salary
    # --------------------------------------------------------

    if (
        "higher average salary" in query
        or "higher average salaries" in query
        or "higher average" in query
        or "which one earns more" in query
        or "which company pays more" in query
    ):

        companies = companies_in_query.copy()

        for company in companies_in_history:

            if company not in companies:
                companies.append(company)

        if len(companies) >= 2:

            return (
                f"Compare the average salaries "
                f"of {companies[0]} and {companies[1]}."
            )

    # --------------------------------------------------------
    # "What about the other company?"
    # --------------------------------------------------------

    if (
        "other company" in query
        or "other one" in query
    ):

        if companies_in_history:

            previous_company = companies_in_history[-1]

            for company in KNOWN_COMPANIES:

                formatted = company.title()

                if (
                    formatted != previous_company
                    and formatted in companies_in_history
                ):

                    return (
                        f"Give me a complete analysis "
                        f"of {formatted}."
                    )

    # --------------------------------------------------------
    # "What about its employees?"
    # --------------------------------------------------------

    if (
        "its employees" in query
        or "its workforce" in query
        or "their employees" in query
        or "their workforce" in query
    ):

        if last_company:

            return (
                f"Show me employees working "
                f"at {last_company}."
            )

    # --------------------------------------------------------
    # "What roles exist there?"
    # "What roles are available there?"
    # "Which roles are there?"
    #
    # Resolve these common follow-ups locally so they do not
    # require an OpenRouter call.
    # --------------------------------------------------------

    if (
        "what roles exist there" in query
        or "what roles are there" in query
        or "what roles exist here" in query
        or "what roles are available there" in query
        or "which roles are there" in query
    ):

        if last_company:

            return (
                f"What roles exist at {last_company}?"
            )

    # --------------------------------------------------------
    # "Who works there?"
    # "Show employees there."
    # "Show me employees there."
    #
    # Resolve employee follow-ups locally as well.
    # --------------------------------------------------------

    if (
        "who works there" in query
        or "who works here" in query
        or "show employees there" in query
        or "show me employees there" in query
    ):

        if last_company:

            return (
                f"Show me employees working at {last_company}."
            )

    # --------------------------------------------------------
    # "What roles does it have?"
    # --------------------------------------------------------

    if (
        "what roles" in query
        or "which roles" in query
        or "roles does it have" in query
    ):

        if companies_in_history:

            company = companies_in_history[-1]

            return (
                f"What roles exist at {company}?"
            )

    return None


# ============================================================
# LOCAL ROUTER
# ============================================================

def local_route(user_query):

    query = user_query.lower().strip()

    # ========================================================
    # BOTH
    #
    # IMPORTANT:
    # Check BOTH before SALARY and COMPANY.
    # ========================================================

    has_analysis = (
        "analyze" in query
        or "analysis" in query
        or "analyze" in query
    )

    has_salary = (
        "salary" in query
        or "salaries" in query
        or "highest paid" in query
        or "highest-paid" in query
        or "who earns the most" in query
        or "who earns more" in query
        or "who makes the most" in query
        or "earns the most" in query
        or "paid employee" in query
        or "earning" in query
        or "earnings" in query
    )

    has_company = (
        "employee" in query
        or "employees" in query
        or "workforce" in query
        or "role" in query
        or "roles" in query
        or "department" in query
        or "company" in query
        or "companies" in query
    )

    if has_analysis and has_salary and has_company:

        return "BOTH"

    # Explicit compare + salary + employee/role
    if (
        "compare" in query
        and (
            "salary" in query
            or "salaries" in query
            or "paid" in query
        )
        and (
            "employee" in query
            or "employees" in query
            or "role" in query
            or "roles" in query
        )
    ):

        return "BOTH"

    # ========================================================
    # SPECIAL COMPANY INFORMATIONAL QUESTIONS
    # ========================================================

    informational_patterns = [
        "tell me something interesting",
        "something interesting",
        "interesting about",
        "tell me about",
        "information about",
        "something about",
    ]

    if any(
        pattern in query
        for pattern in informational_patterns
    ):
        companies_in_query = extract_companies(user_query)
        if companies_in_query:
            return "COMPANY"
        if (
            "employee" in query
            or "employees" in query
            or "company" in query
            or "workforce" in query
            or "role" in query
            or "roles" in query
        ):

            return "COMPANY"

    # ========================================================
    # SIMPLE COMPANY ANALYSIS
    # "Analyze Google."
    #
    # Do this before SALARY so a plain analysis request is
    # handled deterministically without OpenRouter.
    # ========================================================

    if (
        ("analyze " in query or query.startswith("analyze"))
        and not has_salary
    ):
        return "COMPANY"

    # ========================================================
    # WEATHER
    # ========================================================

    weather_patterns = [
        "weather",
        "temperature",
        "forecast",
        "rain",
        "humidity",
        "wind",
        "weather conditions",
    ]

    if any(
        pattern in query
        for pattern in weather_patterns
    ):
        return "WEATHER"

    # ========================================================
    # SALARY
    # ========================================================

    salary_patterns = [

        "highest paid employee",
        "highest-paid employee",

        "highest paid",
        "highest-paid",

        "lowest paid",
        "lowest-paid",

        "who earns the most",
        "who earns more",

        "who makes the most",

        "salary",
        "salaries",

        "salary comparison",
        "compare salaries",

        "salary statistics",

        "average salary",
        "average salaries",

        "higher average salary",

        "earning",
        "earnings",
        "earns",

        "paid employee",
    ]

    if any(
        pattern in query
        for pattern in salary_patterns
    ):

        return "SALARY"

    # ========================================================
    # COMPANY
    # ========================================================

    company_patterns = [

        "company analysis",
        "complete analysis",

        "company information",
        "company statistics",

        "company workforce",
        "workforce",

        "employees working",
        "employees at",

        "show me employees",
        "list employees",

        "what roles exist",
        "which roles",

        "roles at",
        "roles within",

        "companies in",
        "which companies",

        "company",
        "companies",
    ]

    if any(
        pattern in query
        for pattern in company_patterns
    ):

        return "COMPANY"

    return None


# ============================================================
# FALLBACK ROUTER
# ============================================================

def fallback_agent(user_query):

    query = user_query.lower()

    salary_words = [
        "salary",
        "salaries",
        "paid",
        "earns",
        "earn",
        "earning",
        "earnings",
        "highest paid",
        "highest-paid",
        "lowest paid",
        "lowest-paid",
        "who earns",
        "who makes",
        "average salary",
    ]

    company_words = [
        "company",
        "companies",
        "employee",
        "employees",
        "workforce",
        "role",
        "roles",
        "department",
        "analysis",
        "information",
    ]

    has_salary = any(
        word in query
        for word in salary_words
    )

    has_company = any(
        word in query
        for word in company_words
    )

    # ========================================================
    # BOTH MUST BE CHECKED FIRST
    # ========================================================

    if has_salary and has_company:

        if (
            "role" in query
            or "roles" in query
            or "employee" in query
            or "employees" in query
        ):

            if (
                "analyze" in query
                or "analysis" in query
                or "compare" in query
                or "tell me" in query
            ):

                return "BOTH"

    # ========================================================
    # Explicit salary
    # ========================================================

    if (
        "highest paid employee" in query
        or "highest-paid employee" in query
        or "who earns the most" in query
        or "who is the highest paid" in query
    ):

        return "SALARY"

    if has_salary:
        return "SALARY"

    if has_company:
        return "COMPANY"

    return None


# ============================================================
# LLM CONTEXT RESOLVER
# ============================================================

def contextualize_query(
    user_query,
    session_id="default"
):

    # Never rewrite a complete current query.
    if local_route(user_query):
        return user_query

    # PostgreSQL-backed sessions survive backend restarts.
    # Always ask the context helper for persisted history.
    history_text = get_recent_context(
        session_id
    )

    if not history_text:
        return user_query

    prompt = f"""
You are a conversation context resolver.

Previous conversation:

{history_text}

New user message:

{user_query}

Rewrite ONLY when the new message genuinely depends on
previous conversation context.

Rules:

1. Preserve the NEW user's intent.
2. Never replace a new company with an old company.
3. Never replace the current request with an older request.
4. Use previous context only for pronouns/references such as:
   - what about
   - which one
   - the other one
   - its
   - their
5. If the new message already contains a company and a clear
   request, preserve it exactly.
6. Do not answer the question.
7. Return ONLY the rewritten request.
"""

    try:

        response = llm.chat.completions.create(

            model="openai/gpt-oss-20b:free",

            max_tokens=150,

            messages=[
                {
                    "role": "system",
                    "content": prompt
                }
            ]
        )

    except Exception as e:

        print("\n⚠️ Context resolver error:")
        print(e)

        print("→ Using original user query.")

        return user_query

    if not response.choices:
        return user_query

    message = response.choices[0].message

    if not message.content:
        return user_query

    return message.content.strip()


# ============================================================
# SMART QUERY RESOLUTION
#
# IMPORTANT FIX:
# DIRECT ROUTING MUST HAPPEN BEFORE CONTEXT RESOLUTION.
#
# This prevents:
#
# User: Analyze Google...
# User: Analyze Tesla...
#
# from becoming:
# "What roles exist at Google?"
# ============================================================

def resolve_query(
    user_query,
    session_id="default"
):

    query = user_query.lower().strip()

    # ========================================================
    # 1. TRUE CONTEXT-DEPENDENT FOLLOW-UPS FIRST
    #
    # Examples:
    #   "What roles exist there?"
    #   "What roles are there?"
    #   "Who works there?"
    #   "Show employees there."
    #
    # These should use session memory before the direct router,
    # because local_route() can otherwise classify "roles" or
    # "employees" as a complete COMPANY query and skip context.
    # ========================================================

    context_dependent_patterns = (
        "there",
        "here",
        "its ",
        "their ",
        "it ",
        "which one",
        "the other one",
        "what about",
    )

    is_context_dependent = any(
        pattern in query
        for pattern in context_dependent_patterns
    )

    if is_context_dependent:

        contextual_query = local_context_resolution(
            user_query,
            session_id
        )

        if contextual_query:

            print(
                "\n⚡ Local Context Resolver:"
            )

            print(
                "→ Resolved Query:",
                contextual_query
            )

            return contextual_query

    # ========================================================
    # 2. CURRENT QUERY FIRST
    #
    # A complete query with an explicit company should still be
    # routed directly and must not accidentally use old context.
    # ========================================================

    direct_route = local_route(
        user_query
    )

    if direct_route:

        print(
            "\n⚡ Local Router:",
            direct_route
        )

        print(
            "→ Current query is complete; "
            "skipping context resolver."
        )

        return user_query

    # ========================================================
    # 3. LOCAL CONTEXT FALLBACK
    # ========================================================

    contextual_query = local_context_resolution(
        user_query,
        session_id
    )

    if contextual_query:

        print(
            "\n⚡ Local Context Resolver:"
        )

        print(
            "→ Resolved Query:",
            contextual_query
        )

        return contextual_query

    # ========================================================
    # 4. LLM CONTEXT FALLBACK
    # ========================================================

    print(
        "\n🧠 Query needs context resolution..."
    )

    return contextualize_query(
        user_query,
        session_id
    )


# ============================================================
# CHOOSE AGENT
# ============================================================

def choose_agent(user_query):

    # ========================================================
    # LOCAL ROUTER
    # ========================================================

    local_decision = local_route(
        user_query
    )

    if local_decision:

        print(
            "\n⚡ Local Router Decision:",
            local_decision
        )

        return local_decision

    # ========================================================
    # LLM ORCHESTRATOR
    # ========================================================

    print(
        "\n🧠 Local router uncertain."
    )

    print(
        "→ Asking Orchestrator LLM..."
    )

    try:

        response = llm.chat.completions.create(

            model="openai/gpt-oss-20b:free",

            max_tokens=100,

            messages=[
                {
                    "role": "system",
                    "content": ORCHESTRATOR_PROMPT
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ]
        )

    except Exception as e:

        print(
            "\n⚠️ Orchestrator LLM error:"
        )

        print(e)

        print(
            "\n→ Using keyword fallback..."
        )

        return fallback_agent(
            user_query
        )

    if not response.choices:

        return fallback_agent(
            user_query
        )

    message = response.choices[0].message

    if not message.content:

        reasoning = getattr(
            message,
            "reasoning",
            None
        )

        if reasoning:

            reasoning = reasoning.upper()

            if "BOTH" in reasoning:
                return "BOTH"

            if "SALARY" in reasoning:
                return "SALARY"

            if "COMPANY" in reasoning:
                return "COMPANY"

        return fallback_agent(
            user_query
        )

    decision = (
        message.content
        .strip()
        .upper()
    )

    decision = decision.replace(
        "`",
        ""
    )

    decision = decision.replace(
        "*",
        ""
    )

    decision = decision.strip()

    if decision == "BOTH":
        return "BOTH"

    if decision == "SALARY":
        return "SALARY"

    if decision == "COMPANY":
        return "COMPANY"

    if "BOTH" in decision:
        return "BOTH"

    if "SALARY" in decision:
        return "SALARY"

    if "COMPANY" in decision:
        return "COMPANY"

    return fallback_agent(
        user_query
    )


# ============================================================
# VALIDATE AGENT RESULT
# ============================================================

def validate_agent_result(
    result,
    expected_agent
):

    if not isinstance(result, dict):

        return {
            "agent": expected_agent,
            "status": "error",
            "answer": None,
            "tool_calls": 0,
            "execution_time": 0,
            "error": (
                "Agent returned an invalid "
                "result format."
            )
        }

    required_fields = [
        "agent",
        "status",
        "answer",
        "tool_calls",
        "execution_time",
        "error"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in result
    ]

    if missing_fields:

        return {
            "agent": expected_agent,
            "status": "error",
            "answer": None,
            "tool_calls": 0,
            "execution_time": 0,
            "error": (
                "Missing fields: "
                + ", ".join(missing_fields)
            )
        }

    if result["status"] not in [
        "success",
        "error"
    ]:

        result["status"] = "error"

        result["error"] = (
            "Invalid agent status."
        )

        result["answer"] = None

    return result


# ============================================================
# PRINT AGENT RESULT
# ============================================================

def print_agent_result(result):

    print(
        f"\n[{result['agent']}]"
    )

    print(
        "Status:",
        result["status"]
    )

    print(
        "Tool calls:",
        result["tool_calls"]
    )

    print(
        "Execution time:",
        f"{result['execution_time']:.3f}s"
    )

    if result["status"] == "error":

        print(
            "Error:",
            result["error"]
        )

    else:

        print(
            "Agent completed successfully."
        )


# ============================================================
# SAVE CONVERSATION
# ============================================================

def save_conversation(
    user_query,
    resolved_query,
    agent,
    session_id="default"
):
    """
    Persist real user sessions in PostgreSQL while keeping a
    small in-memory copy for compatibility and fallback.
    """

    history = session_memories.setdefault(
        session_id,
        []
    )

    history.append(
        f"User: {user_query}"
    )

    history.append(
        f"Resolved: {resolved_query}"
    )

    history.append(
        f"Agent: {agent}"
    )

    if len(history) > MAX_HISTORY_ENTRIES:

        del history[:-MAX_HISTORY_ENTRIES]

    # Persist browser sessions in PostgreSQL.
    if session_id != "default":

        try:

            db_save_conversation(
                session_id=session_id,
                user_query=user_query,
                resolved_query=resolved_query,
                agent=agent
            )

        except Exception as exc:

            print(
                "\n⚠️ PostgreSQL conversation save failed:"
            )

            print(exc)

            print(
                "→ Conversation retained in memory."
            )

    # Prevent unbounded growth of in-memory sessions.
    if len(session_memories) > MAX_SESSIONS:

        oldest_session = next(
            iter(session_memories)
        )

        if oldest_session != session_id:

            session_memories.pop(
                oldest_session,
                None
            )



# ============================================================
# DETERMINISTIC SYNTHESIS FALLBACK
#
# If OpenRouter is unavailable, BOTH requests can still return
# a useful answer instead of failing completely.
# ============================================================

def deterministic_synthesis(
    resolved_query,
    salary_answer,
    company_answer
):

    parts = []

    if salary_answer:
        parts.append(
            "### Salary Information\n\n"
            + salary_answer
        )

    if company_answer:
        parts.append(
            "### Company Information\n\n"
            + company_answer
        )

    if not parts:
        return None

    return "\n\n".join(parts)


# ============================================================
# ORCHESTRATE
# ============================================================

async def orchestrate(
    user_query,
    session_id="default"
):

    trace = ExecutionTrace(user_query)

    # ========================================================
    # RESOLVE QUERY
    # ========================================================

    resolved_query = resolve_query(
        user_query,
        session_id
    )

    print(
        "\nResolved Query:",
        resolved_query
    )

    # ========================================================
    # CHOOSE AGENT
    # ========================================================

    agent = choose_agent(resolved_query)

    trace.set_orchestrator(agent)

    print(
        "\nOrchestrator Decision:",
        agent
    )

    # ========================================================
    # SAVE CONTEXT
    # ========================================================

    save_conversation(
        user_query,
        resolved_query,
        agent,
        session_id
    )

    # ========================================================
    # WEATHER
    # ========================================================

    if agent == "WEATHER":

        print(
            "→ Routing to Weather Agent"
        )

        result = await weather_agent(
            resolved_query
        )

        result = validate_agent_result(
            result,
            "weather_agent"
        )

        _record_agent_trace(
            trace,
            result,
            "weather_agent"
        )

        print_agent_result(
            result
        )

        if result["status"] == "success":

            print(
                "\nFinal Answer:"
            )

            print(
                result["answer"]
            )

        else:

            print(
                "\n⚠️ Weather Agent failed."
            )

        report = trace.finish(
            result["status"],
            result.get("answer")
        )

        trace.print_report(
            report
        )

        result["execution_trace"] = report

        return result

    # ========================================================
    # SALARY
    # ========================================================

    if agent == "SALARY":

        print(
            "→ Routing to Salary Agent"
        )

        result = await salary_agent(
            resolved_query
        )

        result = validate_agent_result(
            result,
            "salary_agent"
        )

        _record_agent_trace(
            trace,
            result,
            "salary_agent"
        )

        print_agent_result(
            result
        )

        if result["status"] == "success":

            print(
                "\nFinal Answer:"
            )

            print(
                result["answer"]
            )

        else:

            print(
                "\n⚠️ Salary Agent failed."
            )

        report = trace.finish(
            result["status"],
            result.get("answer")
        )
        trace.print_report(report)

        result["execution_trace"] = report

        return result

    # ========================================================
    # COMPANY
    # ========================================================

    if agent == "COMPANY":

        print(
            "→ Routing to Company Agent"
        )

        result = await company_agent(
            resolved_query
        )

        result = validate_agent_result(
            result,
            "company_agent"
        )

        _record_agent_trace(
            trace,
            result,
            "company_agent"
        )

        print_agent_result(
            result
        )

        if result["status"] == "success":

            print(
                "\nFinal Answer:"
            )

            print(
                result["answer"]
            )

        else:

            print(
                "\n⚠️ Company Agent failed."
            )

        report = trace.finish(
            result["status"],
            result.get("answer")
        )
        trace.print_report(report)

        result["execution_trace"] = report

        return result

    # ========================================================
    # BOTH
    # ========================================================

    if agent == "BOTH":

        print(
            "→ Routing to Salary Agent "
            "+ Company Agent"
        )

        # ----------------------------------------------------
        # Split the compound query deterministically.
        # ----------------------------------------------------

        companies = extract_companies(resolved_query)

        if companies:
            target_company = companies[0]
        else:
            target_company = None

        if target_company:

            salary_query = (
                f"Who is the highest paid employee "
                f"at {target_company}?"
            )

            company_query = (
                f"Give me a complete analysis "
                f"of {target_company}."
            )

        else:

            salary_query = resolved_query
            company_query = resolved_query

        print(
            "\n⚡ BOTH Query Split:"
        )

        print(
            "→ Salary Agent Query:",
            salary_query
        )

        print(
            "→ Company Agent Query:",
            company_query
        )

        salary_result, company_result = (
            await asyncio.gather(

                salary_agent(
                    salary_query
                ),

                company_agent(
                    company_query
                )
            )
        )

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        salary_result = validate_agent_result(
            salary_result,
            "salary_agent"
        )

        company_result = validate_agent_result(
            company_result,
            "company_agent"
        )

        _record_agent_trace(
            trace,
            salary_result,
            "salary_agent"
        )

        _record_agent_trace(
            trace,
            company_result,
            "company_agent"
        )

        # ----------------------------------------------------
        # Print
        # ----------------------------------------------------

        print(
            "\n========== AGENT RESULTS =========="
        )

        print_agent_result(
            salary_result
        )

        print_agent_result(
            company_result
        )

        salary_answer = (
            salary_result["answer"]
            if salary_result["status"] == "success"
            else ""
        )

        company_answer = (
            company_result["answer"]
            if company_result["status"] == "success"
            else ""
        )

        # ----------------------------------------------------
        # If both failed
        # ----------------------------------------------------

        if not salary_answer and not company_answer:

            print(
                "\n⚠️ Both agents failed."
            )

            report = trace.finish(
                "error",
                None
            )
            trace.print_report(report)

            return {
                "status": "error",
                "answer": None,
                "agents": [
                    salary_result,
                    company_result
                ],
                "execution_trace": report
            }

        # ----------------------------------------------------
        # FINAL ANSWER / SYNTHESIS
        # ----------------------------------------------------

        final_answer = None

        # ----------------------------------------------------
        # ONLY COMPANY AGENT SUCCEEDED
        # ----------------------------------------------------

        if company_answer and not salary_answer:

            print(
                "\n-> Using Company Agent answer directly."
            )

            final_answer = company_answer

        # ----------------------------------------------------
        # ONLY SALARY AGENT SUCCEEDED
        # ----------------------------------------------------

        elif salary_answer and not company_answer:

            print(
                "\n-> Using Salary Agent answer directly."
            )

            final_answer = salary_answer

        # ----------------------------------------------------
        # BOTH AGENTS SUCCEEDED
        # ----------------------------------------------------

        elif salary_answer and company_answer:

            print(
                "\n-> 🧠 Synthesizing final answer..."
            )

            try:

                final_answer = synthesize(
                    resolved_query,
                    salary_answer,
                    company_answer
                )

            except Exception as e:

                print(
                    "\n⚠️ Synthesizer error:"
                )

                print(e)

        # ----------------------------------------------------
        # DETERMINISTIC FALLBACK
        # ----------------------------------------------------

        if not final_answer:

            print(
                "\n⚡ Using deterministic synthesis fallback."
            )

            final_answer = deterministic_synthesis(
                resolved_query,
                salary_answer,
                company_answer
            )
        # ----------------------------------------------------
        # Final answer
        # ----------------------------------------------------

        if final_answer:

            print(
                "\nFinal Answer:"
            )

            print(
                final_answer
            )

        else:

            print(
                "\n⚠️ No final answer could be produced."
            )

        final_status = (
            "success"
            if final_answer
            else "error"
        )

        report = trace.finish(
            final_status,
            final_answer
        )
        trace.print_report(report)

        return {
            "status": final_status,
            "answer": final_answer,
            "agents": [
                salary_result,
                company_result
            ],
            "execution_trace": report
        }

    # ========================================================
    # UNKNOWN
    # ========================================================

    print(
        "\n⚠️ Orchestrator could not determine "
        "the correct agent."
    )

    report = trace.finish(
        "error",
        None
    )
    trace.print_report(report)

    return {
        "status": "error",
        "answer": None,
        "agents": [],
        "execution_trace": report
    }


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    while True:

        query = input(
            "\nUser: "
        )

        # ====================================================
        # EXIT
        # ====================================================

        if query.lower().strip() in [
            "exit",
            "quit"
        ]:

            print(
                "\nGoodbye!"
            )

            break

        # ====================================================
        # EMPTY
        # ====================================================

        if not query.strip():
            continue

        # ====================================================
        # RUN
        # ====================================================

        try:

            asyncio.run(
                orchestrate(query)
            )

        except KeyboardInterrupt:

            print(
                "\n\nProgram stopped."
            )

            break

        except Exception as e:

            print(
                "\n⚠️ Orchestrator error:"
            )

            print(e)