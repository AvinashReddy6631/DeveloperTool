import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT ACTUAL ORCHESTRATOR FUNCTIONS
# ============================================================

from orchestrator import (
    local_route,
    extract_companies,
)


# ============================================================
# TEST DATA
# ============================================================

SALARY_QUERIES = [

    "Who is the highest paid employee at Google?",

    "Who earns the most at Google?",

    "What is the salary information for Google?",

    "Who is the highest paid employee at Tesla?",

]


COMPANY_QUERIES = [

    "Give me a complete analysis of Google.",

    "Show me employees working at Google.",

    "What roles exist at Google?",

    "Give me a complete analysis of Tesla.",

]


BOTH_QUERIES = [

    "Analyze Google and tell me who earns the most and what roles exist.",

    "Analyze Tesla and tell me who earns the most and what roles exist.",

]


# ============================================================
# EXPECTED ROUTING
# ============================================================

EXPECTED_SALARY = "SALARY"

EXPECTED_COMPANY = "COMPANY"

EXPECTED_BOTH = "BOTH"


# ============================================================
# ROUTING EVALUATION
# ============================================================

def evaluate_routing(
    name,
    queries,
    expected
):

    print(
        "\n"
        + "=" * 60
    )

    print(
        f"{name} ROUTING EVALUATION"
    )

    print(
        "=" * 60
    )

    total = len(queries)

    passed = 0

    failed = 0

    for query in queries:

        try:

            decision = local_route(
                query
            )

        except Exception as e:

            print(
                "\n❌ ERROR"
            )

            print(
                "Query:",
                query
            )

            print(
                "Error:",
                e
            )

            failed += 1

            continue

        if decision == expected:

            print(
                "\n✅ PASS"
            )

            print(
                "Query:",
                query
            )

            print(
                "Expected:",
                expected
            )

            print(
                "Actual:",
                decision
            )

            passed += 1

        else:

            print(
                "\n❌ FAIL"
            )

            print(
                "Query:",
                query
            )

            print(
                "Expected:",
                expected
            )

            print(
                "Actual:",
                decision
            )

            failed += 1

    accuracy = (
        passed / total * 100
        if total
        else 0
    )

    print(
        "\n"
        + "-" * 60
    )

    print(
        "Total:",
        total
    )

    print(
        "Passed:",
        passed
    )

    print(
        "Failed:",
        failed
    )

    print(
        "Accuracy:",
        f"{accuracy:.2f}%"
    )

    return {
        "name": name,
        "total": total,
        "passed": passed,
        "failed": failed,
        "accuracy": accuracy,
    }


# ============================================================
# COMPANY EXTRACTION EVALUATION
# ============================================================

def evaluate_company_extraction():

    print(
        "\n"
        + "=" * 60
    )

    print(
        "COMPANY EXTRACTION EVALUATION"
    )

    print(
        "=" * 60
    )

    test_cases = [

        (
            "Who is the highest paid employee at Google?",
            ["Google"]
        ),

        (
            "Give me a complete analysis of Google.",
            ["Google"]
        ),

        (
            "What roles exist at Tesla?",
            ["Tesla"]
        ),

        (
            "Who earns the most at Tesla?",
            ["Tesla"]
        ),

        (
            "Show me employees working at Google.",
            ["Google"]
        ),

        (
            "Analyze Google and tell me who earns the most and what roles exist.",
            ["Google"]
        ),

        (
            "Analyze Tesla and tell me who earns the most and what roles exist.",
            ["Tesla"]
        ),

    ]

    total = len(test_cases)

    passed = 0

    failed = 0

    for query, expected in test_cases:

        try:

            actual = extract_companies(
                query
            )

        except Exception as e:

            print(
                "\n❌ ERROR"
            )

            print(
                "Query:",
                query
            )

            print(
                "Error:",
                e
            )

            failed += 1

            continue

        if actual == expected:

            print(
                "\n✅ PASS"
            )

            print(
                "Query:",
                query
            )

            print(
                "Expected:",
                expected
            )

            print(
                "Actual:",
                actual
            )

            passed += 1

        else:

            print(
                "\n❌ FAIL"
            )

            print(
                "Query:",
                query
            )

            print(
                "Expected:",
                expected
            )

            print(
                "Actual:",
                actual
            )

            failed += 1

    accuracy = (
        passed / total * 100
        if total
        else 0
    )

    print(
        "\n"
        + "-" * 60
    )

    print(
        "Total:",
        total
    )

    print(
        "Passed:",
        passed
    )

    print(
        "Failed:",
        failed
    )

    print(
        "Accuracy:",
        f"{accuracy:.2f}%"
    )

    return {
        "name": "Company Extraction",
        "total": total,
        "passed": passed,
        "failed": failed,
        "accuracy": accuracy,
    }


# ============================================================
# MAIN EVALUATION
# ============================================================

def main():

    results = []

    # ========================================================
    # SALARY ROUTING
    # ========================================================

    results.append(
        evaluate_routing(
            "SALARY",
            SALARY_QUERIES,
            EXPECTED_SALARY
        )
    )

    # ========================================================
    # COMPANY ROUTING
    # ========================================================

    results.append(
        evaluate_routing(
            "COMPANY",
            COMPANY_QUERIES,
            EXPECTED_COMPANY
        )
    )

    # ========================================================
    # BOTH ROUTING
    # ========================================================

    results.append(
        evaluate_routing(
            "BOTH",
            BOTH_QUERIES,
            EXPECTED_BOTH
        )
    )

    # ========================================================
    # COMPANY EXTRACTION
    # ========================================================

    results.append(
        evaluate_company_extraction()
    )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    total_tests = sum(
        result["total"]
        for result in results
    )

    total_passed = sum(
        result["passed"]
        for result in results
    )

    total_failed = sum(
        result["failed"]
        for result in results
    )

    overall_accuracy = (
        total_passed
        / total_tests
        * 100
        if total_tests
        else 0
    )

    print(
        "\n\n"
        + "=" * 60
    )

    print(
        "        MCP ORCHESTRATOR EVALUATION"
    )

    print(
        "=" * 60
    )

    for result in results:

        print(
            f"\n{result['name']}"
        )

        print(
            "Total:",
            result["total"]
        )

        print(
            "Passed:",
            result["passed"]
        )

        print(
            "Failed:",
            result["failed"]
        )

        print(
            "Accuracy:",
            f"{result['accuracy']:.2f}%"
        )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "OVERALL RESULTS"
    )

    print(
        "=" * 60
    )

    print(
        "Total Tests:",
        total_tests
    )

    print(
        "Passed:",
        total_passed
    )

    print(
        "Failed:",
        total_failed
    )

    print(
        "Overall Accuracy:",
        f"{overall_accuracy:.2f}%"
    )

    print(
        "=" * 60
    )

    if (
        total_failed == 0
        and overall_accuracy == 100
    ):

        print(
            "✅ ORCHESTRATOR EVALUATION PASSED"
        )

    else:

        print(
            "⚠️ ORCHESTRATOR NEEDS IMPROVEMENT"
        )

    print(
        "=" * 60
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()