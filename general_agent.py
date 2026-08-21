import asyncio
import json
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from harness import AgentHarness


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# OPENROUTER
# ============================================================

llm = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


def get_request_llm(api_key=None):
    """
    Return the OpenRouter client for this request.

    Without a user key, use the project-level key.
    With a user key, use that key only for this request.

    The user key is never logged or persisted here.
    """
    if api_key and api_key.strip():
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key.strip()
        )

    return llm


# ============================================================
# AGENT CONFIGURATION
# ============================================================

MAX_ITERATIONS = 3


# ============================================================
# GENERAL AGENT PROMPT
# ============================================================

GENERAL_AGENT_PROMPT = """
You are the General Chat Agent of an MCP Orchestrator.

Your job is to answer general-purpose questions that do not
require the specialized Salary, Company, or Weather agents.

You can help with:
- General knowledge
- Programming concepts
- AI and machine learning concepts
- Python, JavaScript, Java, and other technical questions
- Explanations and comparisons
- Study and interview questions
- Project guidance
- General reasoning and everyday informational questions

Rules:
1. Give a clear, useful, and direct answer.
2. Do not pretend to have access to private databases or tools.
3. Do not invent facts when you are uncertain.
4. For technical explanations, use examples when helpful.
5. Keep the answer focused on the user's question.
6. You are not the Salary, Company, or Weather Agent.
7. Do not route the question to another agent.
8. Do not call MCP tools.
9. Return only the final natural-language answer.
"""


# ============================================================
# GENERAL AGENT
# ============================================================

async def general_agent(user_query, api_key=None):
    """
    Answer a general-purpose user question.

    Supports BYOK:
      general_agent(query)
        -> project OPENROUTER_API_KEY

      general_agent(query, api_key=user_key)
        -> user's OpenRouter key for this request only
    """

    start_time = time.perf_counter()

    harness = AgentHarness(
        agent_name="general_agent",
        max_iterations=MAX_ITERATIONS
    )

    harness.start()

    try:
        clean_query = (
            user_query.strip()
            if isinstance(user_query, str)
            else ""
        )

        if not clean_query:
            result = harness.error(
                "Query cannot be empty."
            )

            harness.print_summary(result)
            return result

        request_llm = get_request_llm(api_key)

        messages = [
            {
                "role": "system",
                "content": GENERAL_AGENT_PROMPT
            },
            {
                "role": "user",
                "content": clean_query
            }
        ]

        for iteration in range(MAX_ITERATIONS):

            harness.next_iteration()

            print(
                f"\n[General Agent] "
                f"Iteration {iteration + 1}"
            )

            try:
                response = (
                    request_llm.chat.completions.create(
                        model="openai/gpt-oss-20b:free",
                        max_tokens=700,
                        messages=messages
                    )
                )

            except Exception as exc:
                execution_time = round(
                    time.perf_counter() - start_time,
                    3
                )

                print(
                    "\n[General Agent] LLM ERROR:"
                )
                print(exc)

                result = harness.error(
                    f"LLM error: {str(exc)}"
                )

                # Preserve elapsed execution time in the result
                result["execution_time"] = execution_time
                result["mcp_calls"] = []

                harness.print_summary(result)
                return result

            if not response.choices:
                result = harness.error(
                    "LLM returned no choices."
                )

                result["mcp_calls"] = []
                harness.print_summary(result)
                return result

            message = response.choices[0].message

            if not message.content:
                result = harness.error(
                    "LLM returned an empty response."
                )

                result["mcp_calls"] = []
                harness.print_summary(result)
                return result

            answer = message.content.strip()

            if not answer:
                result = harness.error(
                    "LLM returned an empty response."
                )

                result["mcp_calls"] = []
                harness.print_summary(result)
                return result

            print("\nGeneral Agent:")
            print(answer)

            result = harness.success(answer)

            # General agent does not use MCP tools.
            result["mcp_calls"] = []

            execution_time = round(
                time.perf_counter() - start_time,
                3
            )
            result["execution_time"] = execution_time

            harness.print_summary(result)
            return result

        result = harness.error(
            f"Maximum agent iterations "
            f"({MAX_ITERATIONS}) reached."
        )

        result["mcp_calls"] = []
        harness.print_summary(result)
        return result

    except Exception as exc:
        print(
            "\n[General Agent] UNEXPECTED ERROR:"
        )
        print(exc)

        result = harness.error(str(exc))
        result["mcp_calls"] = []

        harness.print_summary(result)
        return result


# ============================================================
# COMMAND LINE TEST
# ============================================================

if __name__ == "__main__":

    query = input(
        "General Agent Query: "
    )

    result = asyncio.run(
        general_agent(query)
    )

    print(
        "\n================================"
    )

    print(
        "STRUCTURED AGENT RESULT"
    )

    print(
        "================================"
    )

    print(
        json.dumps(
            result,
            indent=2,
            default=str
        )
    )