import os
import sys
import uuid

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient

from api import app
from auth import ensure_auth_tables
from quota import ensure_quota_tables, get_usage, refund_usage


def _client():
    ensure_auth_tables()
    ensure_quota_tables()
    return TestClient(app)


def _register(client, email):
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _auth_headers(payload):
    return {"Authorization": f"Bearer {payload['token']}"}


def _usage(client, headers):
    response = client.get("/usage", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["usage"]


def _agent_result(agent, status, error=None, answer=None):
    return {
        "status": status,
        "agent": agent,
        "answer": answer,
        "error": error,
        "error_code": None,
        "execution_trace": None,
    }


def _patch_orchestrate(monkeypatch, result=None, error=None):
    async def fake_orchestrate(query, session_id, api_key=None):
        if error is not None:
            raise error
        return result

    monkeypatch.setattr("api.orchestrate", fake_orchestrate)


def test_successful_developer_request_consumes_one_quota(monkeypatch):
    client = _client()
    user = _register(client, f"dev-ok-{uuid.uuid4().hex[:10]}@example.com")
    headers = _auth_headers(user)
    _patch_orchestrate(
        monkeypatch,
        _agent_result(
            "developer_agent",
            "success",
            answer="Python is dynamically typed; C is statically typed.",
        ),
    )

    response = client.post(
        "/query",
        json={"query": "What is the difference between Python and C?"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["agent"] == "developer_agent"
    assert data["usage"]["ai_used"] == 1
    assert data["usage"]["ai_remaining"] == 2
    assert _usage(client, headers)["ai_used"] == 1


def test_failed_developer_request_refunds_quota(monkeypatch):
    client = _client()
    user = _register(client, f"dev-fail-{uuid.uuid4().hex[:10]}@example.com")
    headers = _auth_headers(user)
    _patch_orchestrate(
        monkeypatch,
        _agent_result(
            "developer_agent",
            "error",
            error="Developer agent failed to produce a final report.",
        ),
    )

    response = client.post(
        "/query",
        json={"query": "What is the difference between Python and C?"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "error"
    assert data["agent"] == "developer_agent"
    assert data["error"] == "Developer agent failed to produce a final report."
    assert data["usage"]["ai_used"] == 0
    assert data["usage"]["ai_remaining"] == 3
    assert _usage(client, headers)["ai_used"] == 0


def test_failed_weather_request_refunds_quota(monkeypatch):
    client = _client()
    user = _register(client, f"wx-{uuid.uuid4().hex[:10]}@example.com")
    headers = _auth_headers(user)
    provider_error = (
        "OpenWeather authentication failed. "
        "Please check your OPENWEATHER_API_KEY."
    )
    _patch_orchestrate(
        monkeypatch,
        _agent_result("weather_agent", "error", error=provider_error),
    )

    response = client.post(
        "/query",
        json={"query": "What is the weather in Hyderabad?"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "error"
    assert data["agent"] == "weather_agent"
    assert data["error"] == provider_error
    assert data["usage"]["ai_used"] == 0
    assert _usage(client, headers)["ai_used"] == 0


def test_failed_salary_request_refunds_quota(monkeypatch):
    client = _client()
    user = _register(client, f"sal-{uuid.uuid4().hex[:10]}@example.com")
    headers = _auth_headers(user)
    _patch_orchestrate(
        monkeypatch,
        _agent_result(
            "salary_agent",
            "error",
            error="Salary lookup failed for the requested company.",
        ),
    )

    response = client.post(
        "/query",
        json={"query": "Who is the highest paid employee at Google?"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "error"
    assert data["agent"] == "salary_agent"
    assert data["usage"]["ai_used"] == 0
    assert _usage(client, headers)["ai_used"] == 0


def test_failed_github_request_refunds_quota(monkeypatch):
    client = _client()
    user = _register(client, f"gh-{uuid.uuid4().hex[:10]}@example.com")
    headers = _auth_headers(user)
    _patch_orchestrate(
        monkeypatch,
        _agent_result(
            "developer_agent",
            "partial",
            error="GitHub API returned HTTP 403 while reading the repository.",
        ),
    )

    response = client.post(
        "/query",
        json={
            "query": (
                "Analyze https://github.com/pallets/flask. Find real issues, "
                "explain the architecture, and analyze the repository based only "
                "on supplied repository evidence."
            )
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "partial"
    assert data["agent"] == "developer_agent"
    assert "GitHub API returned HTTP 403" in data["error"]
    assert data["usage"]["ai_used"] == 0
    assert _usage(client, headers)["ai_used"] == 0


def test_unexpected_exception_refunds_quota(monkeypatch):
    client = _client()
    user = _register(client, f"exc-{uuid.uuid4().hex[:10]}@example.com")
    headers = _auth_headers(user)
    _patch_orchestrate(
        monkeypatch,
        error=RuntimeError("unexpected orchestrator crash"),
    )

    response = client.post(
        "/query",
        json={"query": "What is the weather in Hyderabad?"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "error"
    assert data["error"] == "unexpected orchestrator crash"
    assert data["usage"]["ai_used"] == 0
    assert _usage(client, headers)["ai_used"] == 0


def test_refund_happens_exactly_once(monkeypatch):
    client = _client()
    user = _register(client, f"once-{uuid.uuid4().hex[:10]}@example.com")
    headers = _auth_headers(user)
    calls = []
    real_refund = refund_usage

    def tracked_refund(user_id, consume_repo):
        calls.append((user_id, consume_repo))
        return real_refund(user_id, consume_repo)

    monkeypatch.setattr("api.refund_usage", tracked_refund)
    _patch_orchestrate(
        monkeypatch,
        _agent_result(
            "weather_agent",
            "error",
            error="OpenWeather request failed with HTTP 401.",
        ),
    )

    response = client.post(
        "/query",
        json={"query": "What is the weather in Hyderabad?"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "error"
    assert len(calls) == 1
    assert _usage(client, headers)["ai_used"] == 0

    leftover = refund_usage(user["user"]["id"], False)
    assert leftover["ai_used"] == 0


def test_quota_is_isolated_per_account(monkeypatch):
    client = _client()
    user_a = _register(client, f"a-{uuid.uuid4().hex[:10]}@example.com")
    user_b = _register(client, f"b-{uuid.uuid4().hex[:10]}@example.com")

    headers_a = _auth_headers(user_a)
    headers_b = _auth_headers(user_b)

    assert user_a["usage"]["ai_remaining"] == 3
    assert user_a["usage"]["repo_remaining"] == 1
    assert user_b["usage"]["ai_remaining"] == 3

    _patch_orchestrate(
        monkeypatch,
        _agent_result(
            "salary_agent",
            "success",
            answer="Priya is the highest paid employee at Google.",
        ),
    )

    first = client.post(
        "/query",
        json={"query": "Who is the highest paid employee at Google?"},
        headers=headers_a,
    )
    assert first.status_code == 200
    data = first.json()
    assert data["status"] == "success"
    assert data["usage"]["ai_remaining"] == 2

    me_a = client.get("/auth/me", headers=headers_a).json()
    me_b = client.get("/auth/me", headers=headers_b).json()
    assert me_a["usage"]["ai_remaining"] == 2
    assert me_b["usage"]["ai_remaining"] == 3
    assert me_b["usage"]["repo_remaining"] == 1
    assert _usage(client, headers_b)["ai_used"] == 0
