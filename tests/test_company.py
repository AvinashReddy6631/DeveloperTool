import sys
from pathlib import Path
import asyncio

# Add MCP project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from company_agent import company_agent


def test_company_analysis():

    result = asyncio.run(
        company_agent(
            "Give me a complete analysis of Google."
        )
    )

    assert result["status"] == "success"

    assert result["answer"] is not None

    assert "Google" in result["answer"]

    assert "Priya" in result["answer"]

    assert "ML Engineer" in result["answer"]

    assert result["tool_calls"] >= 1


def test_company_employees():

    result = asyncio.run(
        company_agent(
            "Show me employees working at Google."
        )
    )

    assert result["status"] == "success"

    assert result["answer"] is not None

    assert "Avinash" in result["answer"]

    assert "Priya" in result["answer"]

    assert "AI Engineer" in result["answer"]

    assert "ML Engineer" in result["answer"]

    assert result["tool_calls"] >= 1


def test_company_roles():

    result = asyncio.run(
        company_agent(
            "What roles exist at Google?"
        )
    )

    assert result["status"] == "success"

    assert result["answer"] is not None

    assert "AI Engineer" in result["answer"]

    assert "ML Engineer" in result["answer"]

    assert result["tool_calls"] >= 1


def test_unknown_company():

    result = asyncio.run(
        company_agent(
            "Give me a complete analysis of Tesla."
        )
    )

    assert result["status"] == "success"

    assert result["answer"] is not None

    assert (
        "No company information"
        in result["answer"]
    )

    assert result["tool_calls"] >= 1