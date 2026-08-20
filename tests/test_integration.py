import sys
from pathlib import Path
import asyncio

# Add MCP project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import orchestrator


def test_google_both_integration():

    # Clear previous conversation context
    orchestrator.conversation_history.clear()

    result = asyncio.run(
        orchestrator.orchestrate(
            "Analyze Google and tell me who earns the most "
            "and what roles exist."
        )
    )

    assert result["status"] == "success"

    assert result["answer"] is not None

    # Salary Agent result
    salary_result = result["agents"][0]

    # Company Agent result
    company_result = result["agents"][1]

    assert salary_result["status"] == "success"

    assert company_result["status"] == "success"

    # Verify salary information
    assert "Priya" in salary_result["answer"]

    assert "85000" in salary_result["answer"]

    assert "ML Engineer" in salary_result["answer"]

    # Verify company information
    assert "Google" in company_result["answer"]

    assert "AI Engineer" in company_result["answer"]

    assert "ML Engineer" in company_result["answer"]

    # Both agents must have used MCP
    assert salary_result["tool_calls"] >= 1

    assert company_result["tool_calls"] >= 1

    # Final answer must contain information from both agents
    assert "Priya" in result["answer"]

    assert "ML Engineer" in result["answer"]

    assert "AI Engineer" in result["answer"]

    # Clean up
    orchestrator.conversation_history.clear()


def test_tesla_both_integration():

    orchestrator.conversation_history.clear()

    result = asyncio.run(
        orchestrator.orchestrate(
            "Analyze Tesla and tell me who earns the most "
            "and what roles exist."
        )
    )

    assert result["status"] == "success"

    assert result["answer"] is not None

    salary_result = result["agents"][0]

    company_result = result["agents"][1]

    assert salary_result["status"] == "success"

    assert company_result["status"] == "success"

    # Tesla is not currently in the database
    assert (
        "No salary information"
        in salary_result["answer"]
    )

    assert (
        "No company information"
        in company_result["answer"]
    )

    assert salary_result["tool_calls"] >= 1

    assert company_result["tool_calls"] >= 1

    orchestrator.conversation_history.clear()