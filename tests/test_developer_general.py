import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from developer_agent import developer_agent
from orchestrator import local_route


def test_binary_search_is_developer_route():
    assert local_route("Explain binary search.") == "DEVELOPER"


def test_linked_list_is_developer_route():
    assert local_route("How do I reverse a linked list?") == "DEVELOPER"


def test_python_vs_c_is_developer_route():
    assert local_route("What is the difference between Python and C?") == "DEVELOPER"


def test_hyderabad_weather_is_weather_route():
    assert local_route("What is the weather in Hyderabad?") == "WEATHER"


def test_github_analyze_is_developer_route():
    assert local_route(
        "Analyze https://github.com/pallets/flask. Find real issues."
    ) == "DEVELOPER"


def test_developer_agent_answers_non_repo_questions():
    result = developer_agent("What is MCP?", test_mode=True)
    assert result["status"] == "success"
    assert result["agent"] == "developer_agent"
    assert result["answer"]
    assert "did not produce a final report" not in result["answer"]
