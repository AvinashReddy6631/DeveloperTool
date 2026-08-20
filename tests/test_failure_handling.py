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
from synthesizer import deterministic_synthesis


# ============================================================
# TEST 1
# UNKNOWN COMPANY
# ============================================================

def test_unknown_company():

    result = {
        "agent": "salary_agent",
        "status": "success",
        "answer": (
            "No salary information is available "
            "for **Tesla** in the current database."
        ),
        "tool_calls": 1,
        "iterations": 0,
        "execution_time": 0.5,
        "mcp_calls": [
            {
                "agent": "salary_agent",
                "tool": "get_company_statistics",
                "arguments": {
                    "company": "Tesla"
                },
                "result": (
                    "No employees found "
                    "for company 'Tesla'."
                ),
                "status": "success",
                "execution_time": 0.08
            }
        ],
        "error": None
    }

    validated = AgentHarness.validate_result(
        result,
        "salary_agent"
    )

    assert validated["status"] == "success"
    assert validated["mcp_calls"][0]["status"] == "success"


# ============================================================
# TEST 2
# INVALID AGENT RESULT
# ============================================================

def test_invalid_agent_result():

    invalid_result = {
        "agent": "salary_agent",
        "status": "success"
    }

    validated = AgentHarness.validate_result(
        invalid_result,
        "salary_agent"
    )

    assert validated["status"] == "error"
    assert validated["answer"] is None
    assert "Missing field" in validated["error"]


# ============================================================
# TEST 3
# WRONG AGENT NAME
# ============================================================

def test_wrong_agent_name():

    result = {
        "agent": "company_agent",
        "status": "success",
        "answer": "Google has 2 employees.",
        "tool_calls": 1,
        "iterations": 0,
        "execution_time": 0.5,
        "mcp_calls": [],
        "error": None
    }

    validated = AgentHarness.validate_result(
        result,
        "salary_agent"
    )

    assert validated["status"] == "error"
    assert validated["answer"] is None
    assert "Unexpected agent name" in validated["error"]


# ============================================================
# TEST 4
# TOOL CALL LIMIT
# ============================================================

def test_tool_call_limit():

    harness = AgentHarness(
        "test_agent",
        max_tool_calls=2
    )

    harness.start()

    harness.check_tool_call_limit()
    harness.check_tool_call_limit()

    try:

        harness.check_tool_call_limit()

        assert False, (
            "Expected RuntimeError "
            "was not raised."
        )

    except RuntimeError as error:

        assert "Maximum tool calls exceeded" in str(error)


# ============================================================
# TEST 5
# ITERATION LIMIT
# ============================================================

def test_iteration_limit():

    harness = AgentHarness(
        "test_agent",
        max_iterations=2
    )

    harness.start()

    harness.next_iteration()
    harness.next_iteration()

    try:

        harness.next_iteration()

        assert False, (
            "Expected RuntimeError "
            "was not raised."
        )

    except RuntimeError as error:

        assert "Maximum iterations exceeded" in str(error)


# ============================================================
# TEST 6
# TIMEOUT
# ============================================================

def test_timeout():

    harness = AgentHarness(
        "test_agent",
        timeout_seconds=0
    )

    harness.start()

    try:

        harness.check_timeout()

        assert False, (
            "Expected TimeoutError "
            "was not raised."
        )

    except TimeoutError as error:

        assert "Agent execution exceeded" in str(error)


# ============================================================
# TEST 7
# MCP CALL RECORDING
# ============================================================

def test_mcp_call_recording():

    harness = AgentHarness(
        "test_agent"
    )

    harness.start()

    # record_tool_call() is responsible for
    # recording/counting the MCP call in the
    # current harness implementation.

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

    result = harness.success(
        "Google has 2 employees."
    )

    assert result["status"] == "success"

    assert result["tool_calls"] == 1

    assert len(
        result["mcp_calls"]
    ) == 1

    call = result["mcp_calls"][0]

    assert call["agent"] == "test_agent"

    assert call["tool"] == (
        "get_company_statistics"
    )

    assert call["arguments"]["company"] == (
        "Google"
    )

    assert call["status"] == "success"


# ============================================================
# TEST 8
# DETERMINISTIC SYNTHESIZER FALLBACK
# ============================================================

def test_deterministic_synthesis():

    salary_result = (
        "The highest-paid employee at **Google** "
        "is **Priya**, earning **85000** "
        "as a **ML Engineer**."
    )

    company_result = (
        "**Google – Company Analysis**\n\n"
        "| Metric | Value |\n"
        "|---|---|\n"
        "| Employees | 2 |\n"
        "| Average Salary | 82500.00 |\n"
        "| Highest Salary | 85000 |\n"
        "| Lowest Salary | 80000 |"
    )

    answer = deterministic_synthesis(
        "Analyze Google",
        salary_result,
        company_result
    )

    assert answer is not None

    assert "Salary Information" in answer

    assert "Company Information" in answer

    assert "Priya" in answer

    assert "Google" in answer


# ============================================================
# TEST 9
# EMPTY SYNTHESIS RESULTS
# ============================================================

def test_empty_synthesis():

    answer = deterministic_synthesis(
        "Analyze Google",
        None,
        None
    )

    assert answer is not None

    assert (
        "could not find enough information"
        in answer.lower()
    )


# ============================================================
# TEST 10
# HARNESS SUCCESS RESULT
# ============================================================

def test_harness_success_result():

    harness = AgentHarness(
        "test_agent"
    )

    harness.start()

    result = harness.success(
        "Test completed successfully."
    )

    assert result["agent"] == "test_agent"

    assert result["status"] == "success"

    assert result["answer"] == (
        "Test completed successfully."
    )

    assert result["error"] is None

    assert result["mcp_calls"] == []


# ============================================================
# TEST 11
# HARNESS ERROR RESULT
# ============================================================

def test_harness_error_result():

    harness = AgentHarness(
        "test_agent"
    )

    harness.start()

    result = harness.error(
        "Simulated MCP failure."
    )

    assert result["agent"] == "test_agent"

    assert result["status"] == "error"

    assert result["answer"] is None

    assert result["error"] == (
        "Simulated MCP failure."
    )

    assert result["mcp_calls"] == []


# ============================================================
# TEST 12
# FAILED MCP CALL RECORDING
# ============================================================

def test_failed_mcp_call_recording():

    harness = AgentHarness(
        "test_agent"
    )

    harness.start()

    harness.record_tool_call(
        agent="test_agent",
        tool="get_company_statistics",
        arguments={
            "company": "UnknownCompany"
        },
        result=(
            "No employees found "
            "for company 'UnknownCompany'."
        ),
        status="error",
        execution_time=0.1
    )

    result = harness.error(
        "MCP tool failed."
    )

    assert result["status"] == "error"

    assert len(
        result["mcp_calls"]
    ) == 1

    assert result["tool_calls"] == 1

    call = result["mcp_calls"][0]

    assert call["tool"] == (
        "get_company_statistics"
    )

    assert call["status"] == "error"

    assert call["arguments"]["company"] == (
        "UnknownCompany"
    )


# ============================================================
# TEST 13
# DEBUG INFORMATION
# ============================================================

def test_debug_information():

    harness = AgentHarness(
        "test_agent",
        max_iterations=5,
        max_tool_calls=10,
        timeout_seconds=60
    )

    harness.start()

    harness.check_tool_call_limit()

    info = harness.debug_info()

    assert info["agent"] == "test_agent"

    assert info["max_iterations"] == 5

    assert info["max_tool_calls"] == 10

    assert info["timeout_seconds"] == 60

    assert info["tool_calls"] == 1

    assert "execution_time" in info

    assert "mcp_calls" in info


# ============================================================
# TEST 14
# VALID AGENT RESULT
# ============================================================

def test_valid_agent_result():

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

    assert validated["agent"] == "company_agent"

    assert validated["tool_calls"] == 1

    assert len(
        validated["mcp_calls"]
    ) == 1


# ============================================================
# TEST 15
# INVALID STATUS
# ============================================================

def test_invalid_status():

    result = {
        "agent": "salary_agent",
        "status": "unknown",
        "answer": "Something",
        "tool_calls": 0,
        "iterations": 0,
        "execution_time": 0,
        "mcp_calls": [],
        "error": None
    }

    validated = AgentHarness.validate_result(
        result,
        "salary_agent"
    )

    assert validated["status"] == "error"

    assert validated["answer"] is None

    assert validated["error"] == (
        "Invalid agent status."
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    import pytest

    print()
    print("=" * 60)
    print("MCP FAILURE HANDLING TESTS")
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
        print("✅ ALL FAILURE HANDLING TESTS PASSED")
        print("=" * 60)

    else:

        print("=" * 60)
        print("❌ FAILURE HANDLING TESTS FAILED")
        print("=" * 60)

    sys.exit(exit_code)