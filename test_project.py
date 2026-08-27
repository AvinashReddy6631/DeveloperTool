import os
import sys
import time
import traceback


# ============================================================
# MCP MULTI-AGENT PROJECT HEALTH TEST
# ============================================================

PASS = 0
FAIL = 0


def test(name, condition, details=""):
    global PASS, FAIL

    if condition:
        PASS += 1
        print(f"PASS  | {name}")
        if details:
            print(f"      {details}")
    else:
        FAIL += 1
        print(f"FAIL  | {name}")
        if details:
            print(f"      {details}")


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


print("\n")
print("=" * 60)
print("MCP MULTI-AGENT PROJECT HEALTH CHECK")
print("=" * 60)

started = time.perf_counter()


# ============================================================
# 1. ENVIRONMENT
# ============================================================

section("1. ENVIRONMENT")

test(
    "Python version",
    sys.version_info >= (3, 10),
    sys.version.split()[0]
)

test(
    "Virtual environment",
    sys.prefix != getattr(sys, "base_prefix", sys.prefix),
    "venv active" if sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    else "WARNING: virtual environment not detected"
)


# ============================================================
# 2. REQUIRED IMPORTS
# ============================================================

section("2. REQUIRED IMPORTS")

required_modules = [
    "dotenv",
    "openai",
    "mcp",
]

for module in required_modules:
    try:
        __import__(module)
        test(f"Import {module}", True)
    except Exception as e:
        test(f"Import {module}", False, str(e))


# ============================================================
# 3. PROJECT FILES
# ============================================================

section("3. PROJECT FILES")

required_files = [
    "orchestrator.py",
    "developer_agent.py",
    "salary_agent.py",
    "company_agent.py",
    "weather_agent.py",
]

for filename in required_files:
    exists = os.path.exists(filename)
    test(
        filename,
        exists,
        "found" if exists else "MISSING"
    )


# ============================================================
# 4. ORCHESTRATOR IMPORT
# ============================================================

section("4. ORCHESTRATOR")

try:
    from orchestrator import local_route

    test(
        "Import orchestrator",
        True
    )

except Exception as e:
    test(
        "Import orchestrator",
        False,
        str(e)
    )

    print("\nProject cannot continue because orchestrator.py")
    print("could not be imported.")

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"PASS: {PASS}")
    print(f"FAIL: {FAIL}")

    sys.exit(1)


# ============================================================
# 5. ROUTER TESTS
# ============================================================

section("5. ROUTER TESTS")

router_tests = [
    (
        "What is MCP?",
        "DEVELOPER",
    ),
    (
        "Why is my FastAPI server not running?",
        "DEVELOPER",
    ),
    (
        "Explain this Python error: ModuleNotFoundError: No module named fastapi",
        "DEVELOPER",
    ),
    (
        "Who is the highest paid employee at Google?",
        "SALARY",
    ),
    (
        "What is the weather in Hyderabad?",
        "WEATHER",
    ),
    (
        "Tell me something interesting about Google.",
        "COMPANY",
    ),
    (
        "Analyze Google.",
        "COMPANY",
    ),
    (
        "Which companies are in the database?",
        "COMPANY",
    ),
    (
        "List companies in the database",
        "COMPANY",
    ),
]

for query, expected in router_tests:

    try:
        actual = local_route(query)

        test(
            f"Route: {query}",
            actual == expected,
            f"Expected={expected} | Actual={actual}"
        )

    except Exception as e:
        test(
            f"Route: {query}",
            False,
            str(e)
        )


# ============================================================
# 6. DEVELOPER AGENT TEST
# ============================================================

section("6. DEVELOPER AGENT")

try:

    from developer_agent import developer_agent

    result = developer_agent("What is MCP?")

    test(
        "Developer Agent returns result",
        isinstance(result, dict)
    )

    test(
        "Developer Agent status",
        result.get("status") == "success",
        f"status={result.get('status')}"
    )

    answer = str(result.get("answer", ""))

    test(
        "Developer Agent has answer",
        len(answer.strip()) > 20,
        f"{len(answer)} characters"
    )

    test(
        "Developer Agent does not return safety classification",
        "user safety: safe" not in answer.lower()
    )

    test(
        "Developer Agent does not return fake tool call",
        "<|tool_call_start|>" not in answer
    )

except Exception as e:

    test(
        "Developer Agent",
        False,
        str(e)
    )


# ============================================================
# 7. SALARY AGENT TEST
# ============================================================

section("7. SALARY AGENT")

try:

    import asyncio
    from salary_agent import salary_agent

    result = asyncio.run(
        salary_agent(
            "Who is the highest paid employee at Google?"
        )
    )

    test(
        "Salary Agent returns result",
        isinstance(result, dict)
    )

    test(
        "Salary Agent status",
        result.get("status") == "success",
        f"status={result.get('status')}"
    )

    answer = str(result.get("answer", ""))

    test(
        "Salary Agent has answer",
        len(answer.strip()) > 10
    )

    test(
        "Salary Agent used MCP",
        result.get("mcp_calls") or result.get("tool_calls"),
        f"MCP calls={result.get('mcp_calls')} | "
        f"Tool calls={result.get('tool_calls')}"
    )

except Exception as e:

    test(
        "Salary Agent",
        False,
        str(e)
    )


# ============================================================
# 8. COMPANY AGENT TEST
# ============================================================

section("8. COMPANY AGENT")

try:

    from company_agent import company_agent

    result = asyncio.run(
        company_agent("Analyze Google.")
    )

    test(
        "Company Agent returns result",
        isinstance(result, dict)
    )

    test(
        "Company Agent status",
        result.get("status") == "success",
        f"status={result.get('status')}"
    )

    answer = str(result.get("answer", ""))

    test(
        "Company Agent has answer",
        len(answer.strip()) > 10
    )

    test(
        "Company Agent used MCP",
        result.get("mcp_calls") or result.get("tool_calls"),
        f"MCP calls={result.get('mcp_calls')} | "
        f"Tool calls={result.get('tool_calls')}"
    )

except Exception as e:

    test(
        "Company Agent",
        False,
        str(e)
    )


# ============================================================
# 9. MCP CONNECTION TEST
# ============================================================

section("9. MCP CONNECTION")

try:

    from mcp import ClientSession

    test(
        "MCP SDK available",
        ClientSession is not None
    )

except Exception as e:

    test(
        "MCP SDK available",
        False,
        str(e)
    )


# ============================================================
# 10. ENVIRONMENT VARIABLES
# ============================================================

section("10. ENVIRONMENT VARIABLES")

try:
    from dotenv import load_dotenv

    load_dotenv()

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    weather_key = os.getenv("OPENWEATHER_API_KEY")

    test(
        "OPENROUTER_API_KEY configured",
        bool(openrouter_key),
        "configured" if openrouter_key else "missing"
    )

    if weather_key:
        test(
            "OPENWEATHER_API_KEY configured",
            True,
            "configured"
        )
    else:
        print(
            "INFO  | OPENWEATHER_API_KEY missing "
            "(weather can be fixed later)"
        )

except Exception as e:

    test(
        "Environment configuration",
        False,
        str(e)
    )


# ============================================================
# FINAL RESULT
# ============================================================

elapsed = time.perf_counter() - started

section("FINAL RESULT")

print(f"PASS: {PASS}")
print(f"FAIL: {FAIL}")
print(f"TIME: {elapsed:.2f}s")

print("\n" + "=" * 60)

if FAIL == 0:

    print("PROJECT HEALTH: ALL TESTS PASSED")
    print("=" * 60)
    print("\nYour current MCP project is healthy.")
    print("You can move to the next development stage.")

else:

    print("PROJECT HEALTH: ISSUES FOUND")
    print("=" * 60)
    print("\nFix the FAIL items above before moving forward.")

print()