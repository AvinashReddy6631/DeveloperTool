import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import developer_agent
from developer_agent import (
    MAX_ANALYSIS_GROUPS,
    analyze_github_repository_code,
    developer_agent as run_developer_agent,
)


QUERY = (
    "Analyze this GitHub repository: https://github.com/pallets/flask. "
    "Explain its architecture, identify real issues, and provide "
    "recommendations based only on the repository evidence."
)


def _valid_llm_json(title="Example issue"):
    return json.dumps({
        "category": "Backend, API & Orchestration",
        "findings": [{
            "category": "BUG",
            "title": title,
            "severity": "P3",
            "confidence": "VERIFIED",
            "file": "src/app.py",
            "line_start": 1,
            "line_end": 2,
            "evidence": "def main():",
            "problem": "Example problem supported by the supplied file.",
            "impact": "Limited to this evidence.",
            "recommendation": "Keep the evidence-backed behavior.",
            "finding_type": "bug",
        }],
        "positive_findings": [{
            "file": "src/app.py",
            "line_start": 1,
            "line_end": 2,
            "evidence": "def main():",
            "explanation": "A clear entry function is present.",
        }],
        "gaps": [],
    })


def _repo_metadata():
    return {
        "owner": "pallets",
        "name": "flask",
        "full_name": "pallets/flask",
        "branch": "main",
        "language": "Python",
        "stars": 72143,
        "forks": 16954,
        "open_issues": 3,
        "license": "BSD-3-Clause",
        "archived": False,
        "url": "https://github.com/pallets/flask",
        "description": "The Python micro framework for building web applications.",
    }


def _selected_files():
    return [{
        "path": "src/app.py",
        "content": "def main():\n    return 1\n",
        "raw_content": "def main():\n    return 1\n",
        "truncated": False,
        "category": "CORE_BACKEND",
    }]


def _group(group_id, category):
    return {
        "group_id": group_id,
        "category": category,
        "files": ["src/app.py"],
        "content": (
            "===== FILE: src/app.py =====\n"
            "001 | def main():\n"
            "002 |     return 1\n"
            "===== END FILE =====\n"
        ),
    }


def _repo_context(group_count=2):
    groups = [
        _group(i + 1, name)
        for i, name in enumerate(
            [
                "Repository & Configuration",
                "Backend, API & Orchestration",
                "Authentication & Security",
                "Testing",
            ][:group_count]
        )
    ]
    return {
        "repository": _repo_metadata(),
        "selected_files": _selected_files(),
        "analysis_groups": groups,
        "analysis_metadata": {
            "retrieved_files": 1,
            "useful_files": 1,
            "analysis_groups": len(groups),
        },
    }


def _patch_repo(monkeypatch, context, llm_side_effect):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(
        developer_agent,
        "analyze_github_repository_code",
        lambda *args, **kwargs: context,
    )
    monkeypatch.setattr(
        developer_agent,
        "_call_llm_with_retry",
        llm_side_effect,
    )


def test_successful_repository_analysis(monkeypatch):
    calls = []

    def fake_llm(*args, **kwargs):
        calls.append(kwargs.get("group_number") or len(calls) + 1)
        return _valid_llm_json("Successful finding"), None

    _patch_repo(monkeypatch, _repo_context(1), fake_llm)
    result = run_developer_agent(QUERY)

    assert result["status"] == "success"
    report = result["final_report"]
    assert report["status"] == "success"
    assert report["total_findings"] == 1
    assert report["findings"][0]["file"] == "src/app.py"
    assert report["repository_metadata"]["full_name"] == "pallets/flask"
    assert "findings" in report
    assert "positive_findings" in report
    assert "gaps" in report
    assert "group_results" in report
    assert len(calls) == 1


def test_openrouter_402_is_a_clean_failure(monkeypatch):
    def fake_llm(*args, **kwargs):
        return None, (
            "FATAL_LIMIT_ERROR: OpenRouter credits/token budget are "
            "insufficient. Reduce prompt size/max_tokens, use a cheaper "
            "model, or add credits."
        )

    _patch_repo(monkeypatch, _repo_context(2), fake_llm)
    result = run_developer_agent(QUERY)

    assert result["status"] == "error"
    assert result["error"] and "FATAL_LIMIT_ERROR" in result["error"]
    assert result["failed_groups"] == 1
    assert result["group_results"][0]["status"] == "error"
    assert result["final_report"]["status"] == "error"
    assert result["final_report"]["repository_metadata"]["name"] == "flask"


def test_insufficient_token_budget_stops_further_groups(monkeypatch):
    calls = []

    def fake_llm(*args, **kwargs):
        calls.append(1)
        return None, "FATAL_LIMIT_ERROR: insufficient token budget"

    _patch_repo(monkeypatch, _repo_context(4), fake_llm)
    result = run_developer_agent(QUERY)

    assert len(calls) == 1
    assert result["status"] == "error"
    assert "insufficient" in result["error"].lower() or "FATAL_LIMIT_ERROR" in result["error"]
    assert result["completed_groups"] == 0


def test_partial_group_failure(monkeypatch):
    calls = []

    def fake_llm(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            return _valid_llm_json("First group finding"), None
        return None, "FATAL_LIMIT_ERROR: OpenRouter credits/token budget are insufficient."

    _patch_repo(monkeypatch, _repo_context(3), fake_llm)
    result = run_developer_agent(QUERY)

    assert result["status"] == "partial"
    assert result["error_code"] == "DEVELOPER_PARTIAL"
    assert result["completed_groups"] == 1
    assert result["failed_groups"] == 1
    assert result["group_results"][0]["status"] == "success"
    assert result["group_results"][1]["status"] == "error"
    assert result["final_report"]["status"] == "partial"
    assert result["final_report"]["total_findings"] == 1
    assert len(calls) == 2


def test_successful_multi_group_analysis(monkeypatch):
    calls = []

    def fake_llm(*args, **kwargs):
        calls.append(kwargs.get("group_number"))
        return _valid_llm_json(f"Finding {len(calls)}"), None

    _patch_repo(monkeypatch, _repo_context(3), fake_llm)
    result = run_developer_agent(QUERY)

    assert result["status"] == "success"
    assert len(calls) == 3
    assert result["completed_groups"] == 3
    assert result["failed_groups"] == 0
    assert result["final_report"]["total_findings"] == 3
    assert len(result["group_results"]) == 3


def test_repository_metadata_is_preserved(monkeypatch):
    def fake_llm(*args, **kwargs):
        return _valid_llm_json(), None

    _patch_repo(monkeypatch, _repo_context(1), fake_llm)
    result = run_developer_agent(QUERY)
    metadata = result["final_report"]["repository_metadata"]

    assert metadata["owner"] == "pallets"
    assert metadata["name"] == "flask"
    assert metadata["full_name"] == "pallets/flask"
    assert metadata["branch"] == "main"
    assert metadata["language"] == "Python"
    assert metadata["stars"] == 72143
    assert metadata["forks"] == 16954
    assert metadata["open_issues"] == 3
    assert metadata["license"] == "BSD-3-Clause"
    assert metadata["archived"] is False


def test_llm_calls_are_capped_even_when_more_groups_exist(monkeypatch):
    calls = []

    def fake_llm(*args, **kwargs):
        calls.append(1)
        return _valid_llm_json(), None

    context = _repo_context(4)
    context["analysis_groups"] = context["analysis_groups"] + [
        _group(5, "Documentation"),
        _group(6, "Frontend"),
    ]
    _patch_repo(monkeypatch, context, fake_llm)
    result = run_developer_agent(QUERY)

    assert len(calls) == MAX_ANALYSIS_GROUPS
    assert len(result["group_results"]) == MAX_ANALYSIS_GROUPS


def test_group_builder_does_not_duplicate_full_repo_context(monkeypatch):
    repo = {
        "default_branch": "main",
        "full_name": "acme/app",
        "language": "Python",
        "stargazers_count": 1,
        "forks_count": 0,
        "open_issues_count": 0,
        "license": {"spdx_id": "MIT"},
        "archived": False,
        "html_url": "https://github.com/acme/app",
        "description": "demo",
    }
    tree = [{"path": f"src/module_{index}.py", "type": "blob"} for index in range(20)]

    monkeypatch.setattr(
        developer_agent,
        "_github_get",
        lambda *args, **kwargs: (repo, None),
    )
    monkeypatch.setattr(
        developer_agent,
        "_github_get_tree",
        lambda *args, **kwargs: (tree, None),
    )
    monkeypatch.setattr(
        developer_agent,
        "_github_get_file",
        lambda *args, **kwargs: ("def main():\n    return 1\n", None),
    )

    packed = analyze_github_repository_code("https://github.com/acme/app")
    assert len(packed["analysis_groups"]) <= MAX_ANALYSIS_GROUPS
    assert packed["analysis_metadata"]["retrieved_files"] <= 12
    assert "def main():" not in packed["context"]
    file_markers_in_context = packed["context"].count("===== FILE:")
    assert file_markers_in_context == 0
    assert packed["analysis_groups"][0]["content"].count("===== FILE:") >= 1
