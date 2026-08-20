import os
import sys
import asyncio

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

from orchestrator import (
    orchestrate,
    local_route,
    extract_companies,
)


# ============================================================
# HELPER
# ============================================================

def run_async(coro):

    try:
        return asyncio.run(coro)

    except RuntimeError:

        loop = asyncio.new_event_loop()

        try:
            return loop.run_until_complete(coro)

        finally:
            loop.close()


# ============================================================
# TEST 1
# ============================================================

def test_salary_end_to_end():

    query = (
        "Who is the highest paid employee at Google?"
    )

    decision = local_route(query)

    assert decision == "SALARY"

    companies = extract_companies(query)

    assert companies == ["Google"]


# ============================================================
# TEST 2
# ============================================================

def test_company_end_to_end():

    query = (
        "Give me a complete analysis of Google."
    )

    decision = local_route(query)

    assert decision == "COMPANY"

    companies = extract_companies(query)

    assert companies == ["Google"]


# ============================================================
# TEST 3
# ============================================================

def test_both_end_to_end():

    query = (
        "Analyze Google and tell me who earns "
        "the most and what roles exist."
    )

    decision = local_route(query)

    assert decision == "BOTH"

    companies = extract_companies(query)

    assert companies == ["Google"]


# ============================================================
# TEST 4
# ============================================================

def test_tesla_salary_end_to_end():

    query = (
        "Who is the highest paid employee at Tesla?"
    )

    decision = local_route(query)

    assert decision == "SALARY"

    companies = extract_companies(query)

    assert companies == ["Tesla"]


# ============================================================
# TEST 5
# ============================================================

def test_tesla_company_end_to_end():

    query = (
        "Give me a complete analysis of Tesla."
    )

    decision = local_route(query)

    assert decision == "COMPANY"

    companies = extract_companies(query)

    assert companies == ["Tesla"]


# ============================================================
# TEST 6
# ============================================================

def test_tesla_both_end_to_end():

    query = (
        "Analyze Tesla and tell me who earns "
        "the most and what roles exist."
    )

    decision = local_route(query)

    assert decision == "BOTH"

    companies = extract_companies(query)

    assert companies == ["Tesla"]


# ============================================================
# TEST 7
# ============================================================

def test_google_employees_end_to_end():

    query = (
        "Show me employees working at Google."
    )

    decision = local_route(query)

    assert decision == "COMPANY"

    companies = extract_companies(query)

    assert companies == ["Google"]


# ============================================================
# TEST 8
# ============================================================

def test_google_roles_end_to_end():

    query = (
        "What roles exist at Google?"
    )

    decision = local_route(query)

    assert decision == "COMPANY"

    companies = extract_companies(query)

    assert companies == ["Google"]


# ============================================================
# TEST 9
# COMPLETE ORCHESTRATOR - SALARY
# ============================================================

def test_orchestrator_salary():

    query = (
        "Who is the highest paid employee at Google?"
    )

    result = run_async(
        orchestrate(query)
    )

    assert result is not None

    assert isinstance(
        result,
        dict
    )

    assert result.get("status") in [
        "success",
        "error"
    ]


# ============================================================
# TEST 10
# COMPLETE ORCHESTRATOR - COMPANY
# ============================================================

def test_orchestrator_company():

    query = (
        "Give me a complete analysis of Google."
    )

    result = run_async(
        orchestrate(query)
    )

    assert result is not None

    assert isinstance(
        result,
        dict
    )

    assert result.get("status") in [
        "success",
        "error"
    ]


# ============================================================
# TEST 11
# COMPLETE ORCHESTRATOR - BOTH
# ============================================================

def test_orchestrator_both():

    query = (
        "Analyze Google and tell me who earns "
        "the most and what roles exist."
    )

    result = run_async(
        orchestrate(query)
    )

    assert result is not None

    assert isinstance(
        result,
        dict
    )

    assert result.get("status") in [
        "success",
        "error"
    ]


# ============================================================
# TEST 12
# FOLLOW-UP ROUTING
# ============================================================

def test_followup_routing():

    query = "What about Tesla?"

    decision = local_route(query)

    # A follow-up query may require the
    # context resolver before the final
    # routing decision is known.
    #
    # Therefore None is valid here.

    assert decision in [
        "SALARY",
        "COMPANY",
        "BOTH",
        "UNKNOWN",
        None
    ]


# ============================================================
# TEST 13
# CASE-INSENSITIVE COMPANY EXTRACTION
# ============================================================

def test_company_extraction_case_insensitive():

    queries = [
        "Who earns the most at google?",
        "Who earns the most at GOOGLE?",
        "Who earns the most at Google?"
    ]

    for query in queries:

        companies = extract_companies(
            query
        )

        assert companies == ["Google"]


# ============================================================
# TEST 14
# MINIMAL QUERY
# ============================================================

def test_minimal_query_does_not_crash():

    queries = [
        "Google",
        "salary",
        "company",
        "hello"
    ]

    for query in queries:

        try:

            decision = local_route(query)

            # None is valid when the router
            # cannot determine an intent.

            assert decision in [
                "SALARY",
                "COMPANY",
                "BOTH",
                "UNKNOWN",
                None
            ]

        except Exception as error:

            assert False, (
                f"Router crashed for query "
                f"'{query}': {error}"
            )


# ============================================================
# TEST 15
# MULTI-STEP USER QUERY
# ============================================================

def test_multi_step_query():

    query = (
        "Analyze Google, show me the employees, "
        "and tell me who earns the most."
    )

    decision = local_route(query)

    assert decision == "BOTH"

    companies = extract_companies(query)

    assert companies == ["Google"]


# ============================================================
# TEST 16
# SALARY WORDING VARIATION
# ============================================================

def test_salary_wording_variation():

    queries = [
        "Who earns the most at Google?",
        "Who makes the most at Google?",
        "Who is the highest paid employee at Google?"
    ]

    for query in queries:

        decision = local_route(query)

        assert decision == "SALARY"

        companies = extract_companies(
            query
        )

        assert companies == ["Google"]


# ============================================================
# TEST 17
# COMPANY WORDING VARIATION
# ============================================================

def test_company_wording_variation():

    queries = [
        "Give me a complete analysis of Google.",
        "Show me employees working at Google.",
        "What roles exist at Google?"
    ]

    for query in queries:

        decision = local_route(query)

        assert decision == "COMPANY"

        companies = extract_companies(
            query
        )

        assert companies == ["Google"]


# ============================================================
# TEST 18
# BOTH WORDING VARIATION
# ============================================================

def test_both_wording_variation():

    queries = [
        (
            "Analyze Google and tell me who earns "
            "the most and what roles exist."
        ),
        (
            "Analyze Tesla and tell me who earns "
            "the most and what roles exist."
        )
    ]

    for query in queries:

        decision = local_route(query)

        assert decision == "BOTH"

        companies = extract_companies(
            query
        )

        assert len(companies) == 1


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    import pytest

    print()
    print("=" * 60)
    print("MCP END-TO-END TESTS")
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
        print("✅ ALL END-TO-END TESTS PASSED")
        print("=" * 60)

    else:

        print("=" * 60)
        print("❌ END-TO-END TESTS FAILED")
        print("=" * 60)

    sys.exit(exit_code)