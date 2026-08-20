import sys
from pathlib import Path
import asyncio
import statistics

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT AGENTS
# ============================================================

from salary_agent import salary_agent
from company_agent import company_agent


# ============================================================
# RUN AGENT EVALUATION
# ============================================================

async def evaluate_agent(
    agent_name,
    agent_function,
    queries
):

    results = []

    print(
        f"\n{'=' * 60}"
    )

    print(
        f"Evaluating: {agent_name}"
    )

    print(
        f"{'=' * 60}"
    )

    for query in queries:

        print(
            f"\nQuery: {query}"
        )

        try:

            result = await agent_function(
                query
            )

            results.append(result)

            print(
                "Status:",
                result.get("status")
            )

            print(
                "Tool calls:",
                result.get("tool_calls")
            )

            print(
                "Execution time:",
                result.get("execution_time"),
                "seconds"
            )

        except Exception as e:

            print(
                "ERROR:",
                e
            )

            results.append({
                "status": "error",
                "tool_calls": 0,
                "execution_time": 0,
                "error": str(e)
            })


    # ========================================================
    # CALCULATE METRICS
    # ========================================================

    total = len(results)

    successful = sum(
        1
        for result in results
        if result.get("status") == "success"
    )

    failed = total - successful

    success_rate = (
        successful / total * 100
        if total
        else 0
    )

    execution_times = [
        result.get("execution_time", 0)
        for result in results
        if result.get("execution_time") is not None
    ]

    tool_calls = [
        result.get("tool_calls", 0)
        for result in results
        if result.get("tool_calls") is not None
    ]

    average_latency = (
        statistics.mean(execution_times)
        if execution_times
        else 0
    )

    average_tool_calls = (
        statistics.mean(tool_calls)
        if tool_calls
        else 0
    )


    # ========================================================
    # REPORT
    # ========================================================

    print(
        f"\n{'-' * 60}"
    )

    print(
        f"{agent_name} Evaluation"
    )

    print(
        f"{'-' * 60}"
    )

    print(
        "Total Queries:      ",
        total
    )

    print(
        "Successful Queries:  ",
        successful
    )

    print(
        "Failed Queries:      ",
        failed
    )

    print(
        "Success Rate:        ",
        f"{success_rate:.2f}%"
    )

    print(
        "Average Latency:     ",
        f"{average_latency:.3f}s"
    )

    print(
        "Average Tool Calls:  ",
        f"{average_tool_calls:.2f}"
    )

    return {
        "agent": agent_name,
        "total_queries": total,
        "successful": successful,
        "failed": failed,
        "success_rate": success_rate,
        "average_latency": average_latency,
        "average_tool_calls": average_tool_calls
    }


# ============================================================
# MAIN EVALUATION
# ============================================================

async def main():

    # ========================================================
    # SALARY TEST QUERIES
    # ========================================================

    salary_queries = [

        "Who is the highest paid employee at Google?",

        "Who earns the most at Google?",

        "What is the salary information for Google?",

        "Who is the highest paid employee at Tesla?"
    ]


    # ========================================================
    # COMPANY TEST QUERIES
    # ========================================================

    company_queries = [

        "Give me a complete analysis of Google.",

        "Show me employees working at Google.",

        "What roles exist at Google?",

        "Give me a complete analysis of Tesla."
    ]


    # ========================================================
    # RUN EVALUATIONS
    # ========================================================

    salary_metrics = await evaluate_agent(
        "Salary Agent",
        salary_agent,
        salary_queries
    )

    company_metrics = await evaluate_agent(
        "Company Agent",
        company_agent,
        company_queries
    )


    # ========================================================
    # FINAL REPORT
    # ========================================================

    print(
        "\n\n"
        + "=" * 60
    )

    print(
        "           MCP AGENT EVALUATION REPORT"
    )

    print(
        "=" * 60
    )


    print(
        "\nSalary Agent"
    )

    print(
        "Success Rate:",
        f"{salary_metrics['success_rate']:.2f}%"
    )

    print(
        "Average Latency:",
        f"{salary_metrics['average_latency']:.3f}s"
    )

    print(
        "Average Tool Calls:",
        f"{salary_metrics['average_tool_calls']:.2f}"
    )


    print(
        "\nCompany Agent"
    )

    print(
        "Success Rate:",
        f"{company_metrics['success_rate']:.2f}%"
    )

    print(
        "Average Latency:",
        f"{company_metrics['average_latency']:.3f}s"
    )

    print(
        "Average Tool Calls:",
        f"{company_metrics['average_tool_calls']:.2f}"
    )


    print(
        "\n"
        + "=" * 60
    )

    print(
        "Evaluation completed."
    )

    print(
        "=" * 60
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )