import os
import sys

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORTS
# ============================================================

from harness import AgentHarness


# ============================================================
# HELPER
# ============================================================

def create_harness(agent="test_agent"):

    harness = AgentHarness(
        agent_name=agent,
        max_iterations=5,
        max_tool_calls=3,
        timeout_seconds=60
    )

    harness.start()

    return harness


# ============================================================
# TEST 1
# MCP SERVER / TOOL ERROR
# ============================================================

def test_mcp_tool_error():

    harness = create_harness()

    harness.record_tool_call(
        agent="test_agent",
        tool="get_company_statistics",
        arguments={
            "company": "Google"
        },
        result="MCP server unavailable",
        status="error",
        execution_time=0.10
    )

    result = harness.error(
        "MCP tool execution failed."
    )

    assert result["status"] == "error"

    assert result["answer"] is None

    assert result["error"] == (
        "MCP tool execution failed."
    )

    assert len(result["mcp_calls"]) == 1

    call = result["mcp_calls"][0]

    assert call["tool"] == (
        "get_company_statistics"
    )

    assert call["status"] == "error"


# ============================================================
# TEST 2
# INVALID MCP RESULT
# ============================================================

def test_invalid_mcp_result():

    harness = create_harness()

    harness.record_tool_call(
        agent="test_agent",
        tool="get_company_statistics",
        arguments={
            "company": "Google"
        },
        result=None,
        status="success",
        execution_time=0.10
    )

    result = harness.success(
        "No valid MCP data was returned."
    )

    assert result["status"] == "success"

    assert len(result["mcp_calls"]) == 1

    call = result["mcp_calls"][0]

    assert call["result"] is None

    assert call["status"] == "success"


# ============================================================
# TEST 3
# MCP TIMEOUT ERROR
# ============================================================

def test_mcp_timeout():

    harness = create_harness()

    harness.record_tool_call(
        agent="test_agent",
        tool="get_company_statistics",
        arguments={
            "company": "Google"
        },
        result="Tool execution timed out.",
        status="error",
        execution_time=60
    )

    result = harness.error(
        "MCP tool timeout."
    )

    assert result["status"] == "error"

    assert "timeout" in (
        result["error"].lower()
    )

    assert len(result["mcp_calls"]) == 1

    assert result["mcp_calls"][0]["status"] == (
        "error"
    )


# ============================================================
# TEST 4
# TOOL CALL LIMIT
# ============================================================

def test_mcp_tool_call_limit():

    harness = create_harness()

    harness.check_tool_call_limit()
    harness.check_tool_call_limit()
    harness.check_tool_call_limit()

    try:

        harness.check_tool_call_limit()

        assert False, (
            "Expected tool call limit error."
        )

    except RuntimeError as error:

        assert "Maximum tool calls exceeded" in str(
            error
        )


# ============================================================
# TEST 5
# ITERATION LIMIT
# ============================================================

def test_agent_iteration_limit():

    harness = AgentHarness(
        agent_name="test_agent",
        max_iterations=2,
        max_tool_calls=10,
        timeout_seconds=60
    )

    harness.start()

    harness.next_iteration()
    harness.next_iteration()

    try:

        harness.next_iteration()

        assert False, (
            "Expected iteration limit error."
        )

    except RuntimeError as error:

        assert "Maximum iterations exceeded" in str(
            error
        )


# ============================================================
# TEST 6
# AGENT TIMEOUT
# ============================================================

def test_agent_timeout():

    harness = AgentHarness(
        agent_name="test_agent",
        max_iterations=5,
        max_tool_calls=10,
        timeout_seconds=0
    )

    harness.start()

    try:

        harness.check_timeout()

        assert False, (
            "Expected timeout error."
        )

    except TimeoutError as error:

        assert "Agent execution exceeded" in str(
            error
        )


# ============================================================
# TEST 7
# MCP SUCCESS AFTER PREVIOUS FAILURE
# ============================================================

def test_mcp_recovery_after_failure():

    harness = create_harness()

    # First MCP call fails.

    harness.record_tool_call(
        agent="test_agent",
        tool="get_company_statistics",
        arguments={
            "company": "Google"
        },
        result="Temporary MCP failure",
        status="error",
        execution_time=0.10
    )

    # Second MCP call succeeds.

    harness.record_tool_call(
        agent="test_agent",
        tool="get_company_statistics",
        arguments={
            "company": "Google"
        },
        result={
            "employees": 2
        },
        status="success",
        execution_time=0.10
    )

    result = harness.success(
        "Google has 2 employees."
    )

    assert result["status"] == "success"

    assert len(result["mcp_calls"]) == 2

    assert result["mcp_calls"][0]["status"] == (
        "error"
    )

    assert result["mcp_calls"][1]["status"] == (
        "success"
    )

    assert result["mcp_calls"][1]["result"] == {
        "employees": 2
    }


# ============================================================
# TEST 8
# PARTIAL MCP DATA
# ============================================================

def test_partial_mcp_data():

    harness = create_harness()

    harness.record_tool_call(
        agent="test_agent",
        tool="get_company_statistics",
        arguments={
            "company": "Google"
        },
        result={
            "employees": 2
        },
        status="success",
        execution_time=0.10
    )

    result = harness.success(
        "Google has 2 employees."
    )

    assert result["status"] == "success"

    assert result["mcp_calls"][0]["result"] == {
        "employees": 2
    }


# ============================================================
# TEST 9
# MULTIPLE MCP CALLS
# ============================================================

def test_multiple_mcp_calls():

    harness = create_harness()

    harness.record_tool_call(
        agent="test_agent",
        tool="get_company_statistics",
        arguments={
            "company": "Google"
        },
        result={
            "employees": 2
        },
        status="success",
        execution_time=0.10
    )

    harness.record_tool_call(
        agent="test_agent",
        tool="company_search",
        arguments={
            "query": "Google"
        },
        result={
            "matches": 2
        },
        status="success",
        execution_time=0.10
    )

    result = harness.success(
        "Google information retrieved."
    )

    assert result["status"] == "success"

    assert len(result["mcp_calls"]) == 2

    assert result["mcp_calls"][0]["tool"] == (
        "get_company_statistics"
    )

    assert result["mcp_calls"][1]["tool"] == (
        "company_search"
    )


# ============================================================
# TEST 10
# ERROR RESULT PRESERVES MCP TRACE
# ============================================================

def test_error_preserves_mcp_trace():

    harness = create_harness()

    harness.record_tool_call(
        agent="test_agent",
        tool="company_search",
        arguments={
            "query": "UnknownCompany"
        },
        result=(
            "No company found."
        ),
        status="error",
        execution_time=0.12
    )

    result = harness.error(
        "Company lookup failed."
    )

    assert result["status"] == "error"

    assert result["answer"] is None

    assert len(result["mcp_calls"]) == 1

    assert result["mcp_calls"][0]["tool"] == (
        "company_search"
    )

    assert result["mcp_calls"][0]["status"] == (
        "error"
    )


# ============================================================
# TEST 11
# DEBUG INFO AFTER MCP CALL
# ============================================================

def test_debug_info_contains_mcp_calls():

    harness = create_harness()

    harness.record_tool_call(
        agent="test_agent",
        tool="get_company_statistics",
        arguments={
            "company": "Google"
        },
        result={
            "employees": 2
        },
        status="success",
        execution_time=0.08
    )

    debug = harness.debug_info()

    assert "mcp_calls" in debug

    assert len(debug["mcp_calls"]) == 1

    assert debug["mcp_calls"][0]["tool"] == (
        "get_company_statistics"
    )


# ============================================================
# TEST 12
# RESULT VALIDATION WITH MCP TRACE
# ============================================================

def test_validation_preserves_mcp_trace():

    result = {
        "agent": "company_agent",
        "status": "success",
        "answer": "Google has 2 employees.",
        "tool_calls": 1,
        "iterations": 0,
        "execution_time": 0.9,
        "mcp_calls": [
            {
                "agent": "company_agent",
                "tool": "get_company_statistics",
                "arguments": {
                    "company": "Google"
                },
                "result": {
                    "employees": 2
                },
                "status": "success",
                "execution_time": 0.08
            }
        ],
        "error": None
    }

    validated = AgentHarness.validate_result(
        result,
        "company_agent"
    )

    assert validated["status"] == "success"

    assert len(
        validated["mcp_calls"]
    ) == 1

    assert validated["mcp_calls"][0]["tool"] == (
        "get_company_statistics"
    )


# ============================================================
# TEST 13
# AGENT ERROR WITHOUT MCP CALL
# ============================================================

def test_agent_error_without_mcp_call():

    harness = create_harness()

    result = harness.error(
        "Agent failed before MCP execution."
    )

    assert result["status"] == "error"

    assert result["answer"] is None

    assert result["tool_calls"] == 0

    assert result["mcp_calls"] == []


# ============================================================
# TEST 14
# SUCCESS AFTER MCP ERROR
# ============================================================

def test_success_after_mcp_error():

    harness = create_harness()

    harness.record_tool_call(
        agent="test_agent",
        tool="company_search",
        arguments={
            "query": "Google"
        },
        result="Temporary error",
        status="error",
        execution_time=0.10
    )

    harness.record_tool_call(
        agent="test_agent",
        tool="company_search",
        arguments={
            "query": "Google"
        },
        result="Google employee data",
        status="success",
        execution_time=0.10
    )

    result = harness.success(
        "Google data successfully retrieved."
    )

    assert result["status"] == "success"

    assert len(result["mcp_calls"]) == 2

    assert result["mcp_calls"][0]["status"] == (
        "error"
    )

    assert result["mcp_calls"][1]["status"] == (
        "success"
    )


# ============================================================
# TEST 15
# MCP TRACE ARGUMENTS
# ============================================================

def test_mcp_trace_arguments():

    harness = create_harness()

    harness.record_tool_call(
        agent="salary_agent",
        tool="get_company_statistics",
        arguments={
            "company": "Google"
        },
        result={
            "highest_salary": 85000
        },
        status="success",
        execution_time=0.08
    )

    result = harness.success(
        "Priya is the highest-paid employee."
    )

    call = result["mcp_calls"][0]

    assert call["agent"] == "salary_agent"

    assert call["tool"] == (
        "get_company_statistics"
    )

    assert call["arguments"] == {
        "company": "Google"
    }

    assert call["result"] == {
        "highest_salary": 85000
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    import pytest

    print()
    print("=" * 60)
    print("MCP RESILIENCE TESTS")
    print("=" * 60)
    print()

    exit_code = pytest.main(
        [
            __file__,
            "-v"
        ]
    )

    print()

    if exit_code == 0:

        print("=" * 60)
        print("✅ ALL MCP RESILIENCE TESTS PASSED")
        print("=" * 60)

    else:

        print("=" * 60)
        print("❌ MCP RESILIENCE TESTS FAILED")
        print("=" * 60)

    sys.exit(exit_code)