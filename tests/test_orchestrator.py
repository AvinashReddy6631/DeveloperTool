import sys
from pathlib import Path

# Add MCP project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import orchestrator


def test_salary_routing():

    result = orchestrator.local_route(
        "Who is the highest paid employee at Google?"
    )

    assert result == "SALARY"


def test_company_routing():

    result = orchestrator.local_route(
        "Give me a complete analysis of Google."
    )

    assert result == "COMPANY"


def test_both_routing():

    result = orchestrator.local_route(
        "Analyze Google and tell me who earns the most "
        "and what roles exist."
    )

    assert result == "BOTH"


def test_tesla_both_routing():

    result = orchestrator.local_route(
        "Analyze Tesla and tell me who earns the most "
        "and what roles exist."
    )

    assert result == "BOTH"


def test_company_extraction_google():

    companies = orchestrator.extract_companies(
        "Analyze Google and tell me who earns the most "
        "and what roles exist."
    )

    assert companies == ["Google"]


def test_company_extraction_tesla():

    companies = orchestrator.extract_companies(
        "Analyze Tesla and tell me who earns the most "
        "and what roles exist."
    )

    assert companies == ["Tesla"]


def test_google_not_mixed_with_previous_query():

    query = (
        "Analyze Google and tell me who earns the most "
        "and what roles exist."
    )

    companies = orchestrator.extract_companies(query)

    assert "Google" in companies

    assert (
        "Google and tell me who earns the most "
        "and what roles exist"
        not in companies
    )


def test_tesla_not_mixed_with_google():

    query = (
        "Analyze Tesla and tell me who earns the most "
        "and what roles exist."
    )

    companies = orchestrator.extract_companies(query)

    assert "Tesla" in companies

    assert "Google" not in companies


def test_simple_analysis_does_not_need_llm():

    result = orchestrator.local_route(
        "Analyze Google."
    )

    assert result == "COMPANY"


def test_context_followup():

    orchestrator.conversation_history.clear()

    orchestrator.conversation_history.extend([
        "User: Analyze Google.",
        "Resolved: Analyze Google.",
        "Agent: COMPANY"
    ])

    resolved = orchestrator.local_context_resolution(
        "What about Tesla?"
    )

    assert resolved == (
        "Give me a complete analysis of Tesla."
    )

    orchestrator.conversation_history.clear()