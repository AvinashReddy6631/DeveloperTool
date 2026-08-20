import os

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# OPENROUTER LLM
# ============================================================

API_KEY = os.getenv("OPENROUTER_API_KEY")

llm = None

if API_KEY:

    llm = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY
    )


# ============================================================
# DETERMINISTIC SYNTHESIS
# ============================================================

def deterministic_synthesis(
    user_query,
    salary_result,
    company_result
):
    """
    Creates a final answer without using an LLM.

    This is the safety fallback when:
    - OpenRouter is unavailable
    - API limit is reached
    - API key is missing
    - LLM returns an invalid response
    """

    parts = []

    if salary_result:

        parts.append(
            "### Salary Information\n\n"
            + salary_result.strip()
        )

    if company_result:

        parts.append(
            "### Company Information\n\n"
            + company_result.strip()
        )

    if not parts:

        return (
            "I could not find enough information "
            "to answer the question."
        )

    return "\n\n".join(parts)


# ============================================================
# LLM SYNTHESIS
# ============================================================

def synthesize(
    user_query,
    salary_result,
    company_result
):
    """
    Try to create a natural final response using the LLM.

    If the LLM is unavailable or rate-limited,
    return None so orchestrator.py can use its
    deterministic fallback.
    """

    # --------------------------------------------------------
    # No API key
    # --------------------------------------------------------

    if not API_KEY or llm is None:

        print(
            "\n⚠️ OpenRouter API key not available."
        )

        print(
            "→ Using deterministic synthesis."
        )

        return deterministic_synthesis(
            user_query,
            salary_result,
            company_result
        )

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = f"""
You are the Final Answer Synthesizer.

The user asked:

{user_query}

Salary Agent Result:

{salary_result}

Company Agent Result:

{company_result}

Create ONE final answer for the user.

Rules:

1. Combine the useful information from both results.
2. Answer exactly what the user asked.
3. Do not repeat information unnecessarily.
4. Do not invent any information.
5. Do not mention agents.
6. Do not mention orchestration.
7. Do not mention MCP.
8. Do not mention internal processing.
9. Use a table when it improves clarity.
10. Keep the answer clear and professional.
11. Only use information present in the supplied results.
"""

    # --------------------------------------------------------
    # LLM CALL
    # --------------------------------------------------------

    try:

        response = llm.chat.completions.create(

            model="openai/gpt-oss-20b:free",

            max_tokens=600,

            messages=[
                {
                    "role": "system",
                    "content": prompt
                }
            ]
        )

    except Exception as e:

        print(
            "\n⚠️ Synthesizer LLM unavailable."
        )

        print(
            f"Reason: {e}"
        )

        print(
            "→ Using deterministic synthesis fallback."
        )

        return deterministic_synthesis(
            user_query,
            salary_result,
            company_result
        )

    # --------------------------------------------------------
    # CHECK RESPONSE
    # --------------------------------------------------------

    if not response:

        print(
            "\n⚠️ Synthesizer returned no response."
        )

        print(
            "→ Using deterministic synthesis."
        )

        return deterministic_synthesis(
            user_query,
            salary_result,
            company_result
        )

    # --------------------------------------------------------
    # CHECK CHOICES
    # --------------------------------------------------------

    if not response.choices:

        print(
            "\n⚠️ Synthesizer returned no choices."
        )

        print(
            "→ Using deterministic synthesis."
        )

        return deterministic_synthesis(
            user_query,
            salary_result,
            company_result
        )

    # --------------------------------------------------------
    # GET MESSAGE
    # --------------------------------------------------------

    message = response.choices[0].message

    # --------------------------------------------------------
    # CHECK CONTENT
    # --------------------------------------------------------

    if not message.content:

        print(
            "\n⚠️ Synthesizer returned empty content."
        )

        print(
            "→ Using deterministic synthesis."
        )

        return deterministic_synthesis(
            user_query,
            salary_result,
            company_result
        )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    return message.content.strip()


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    salary = (
        "The highest-paid employee at **Google** "
        "is **Priya**, earning **85000** "
        "as a **ML Engineer**."
    )

    company = (
        "**Google – Company Analysis**\n\n"
        "| Metric | Value |\n"
        "|---|---|\n"
        "| Employees | 2 |\n"
        "| Average Salary | 82500.00 |\n"
        "| Highest Salary | 85000 |\n"
        "| Lowest Salary | 80000 |\n"
        "| Highest-Paid Employee | Priya |\n"
        "| Highest-Paid Role | ML Engineer |\n"
        "| Roles Represented | AI Engineer, ML Engineer |"
    )

    answer = synthesize(
        "Analyze Google and tell me who earns the most.",
        salary,
        company
    )

    print()
    print("=" * 60)
    print("SYNTHESIZER TEST")
    print("=" * 60)
    print()
    print(answer)