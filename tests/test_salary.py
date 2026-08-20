import sys
from pathlib import Path
import asyncio

# Add the MCP project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from salary_agent import salary_agent


def test_highest_paid_employee():

    result = asyncio.run(
        salary_agent(
            "Who is the highest paid employee at Google?"
        )
    )

    assert result["status"] == "success"
    assert result["answer"] is not None
    assert "Priya" in result["answer"]
    assert "85000" in result["answer"]
    assert result["tool_calls"] >= 1


def test_unknown_company():

    result = asyncio.run(
        salary_agent(
            "Who is the highest paid employee at Tesla?"
        )
    )

    assert result["status"] == "success"
    assert "No salary information" in result["answer"]
    assert result["tool_calls"] >= 1