import os
import sys

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

from fastapi.testclient import TestClient

from api import app


# ============================================================
# TEST CLIENT
# ============================================================

client = TestClient(app)


# ============================================================
# TEST 1
# ROOT ENDPOINT
# ============================================================

def test_root():

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == (
        "MCP Agent Orchestrator"
    )

    assert data["status"] == "running"

    assert "version" in data


# ============================================================
# TEST 2
# HEALTH ENDPOINT
# ============================================================

def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"

    assert data["service"] == (
        "MCP Agent Orchestrator"
    )


# ============================================================
# TEST 3
# GOOGLE SALARY QUERY
# ============================================================

def test_google_salary_query():

    response = client.post(
        "/query",
        json={
            "query":
                "Who is the highest paid employee at Google?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"

    assert data["answer"] is not None

    assert "Priya" in data["answer"]

    assert "Google" in data["answer"]

    assert data["error"] is None


# ============================================================
# TEST 4
# GOOGLE COMPANY QUERY
# ============================================================

def test_google_company_query():

    response = client.post(
        "/query",
        json={
            "query":
                "Give me a complete analysis of Google."
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"

    assert data["answer"] is not None

    assert "Google" in data["answer"]

    assert data["error"] is None


# ============================================================
# TEST 5
# GOOGLE BOTH QUERY
# ============================================================

def test_google_both_query():

    response = client.post(
        "/query",
        json={
            "query": (
                "Analyze Google and tell me who "
                "earns the most and what roles exist."
            )
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"

    assert data["answer"] is not None

    assert "Google" in data["answer"]

    assert "Priya" in data["answer"]

    assert data["error"] is None


# ============================================================
# TEST 6
# GOOGLE EMPLOYEE QUERY
# ============================================================

def test_google_employee_query():

    response = client.post(
        "/query",
        json={
            "query":
                "Show me employees working at Google."
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"

    assert data["answer"] is not None

    assert "Google" in data["answer"]

    assert data["error"] is None


# ============================================================
# TEST 7
# GOOGLE ROLES QUERY
# ============================================================

def test_google_roles_query():

    response = client.post(
        "/query",
        json={
            "query":
                "What roles exist at Google?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"

    assert data["answer"] is not None

    assert "Google" in data["answer"]

    assert data["error"] is None


# ============================================================
# TEST 8
# TESLA QUERY
# ============================================================

def test_tesla_query():

    response = client.post(
        "/query",
        json={
            "query":
                "What is the salary information for Tesla?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"

    assert data["answer"] is not None

    assert "Tesla" in data["answer"]

    assert data["error"] is None


# ============================================================
# TEST 9
# REQUEST ID
# ============================================================

def test_request_id():

    response = client.post(
        "/query",
        json={
            "query":
                "Who is the highest paid employee at Google?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "request_id" in data

    assert data["request_id"] is not None

    assert isinstance(
        data["request_id"],
        str
    )

    assert len(
        data["request_id"]
    ) > 0


# ============================================================
# TEST 10
# REQUEST IDs SHOULD BE UNIQUE
# ============================================================

def test_request_ids_are_unique():

    response_1 = client.post(
        "/query",
        json={
            "query":
                "Who is the highest paid employee at Google?"
        }
    )

    response_2 = client.post(
        "/query",
        json={
            "query":
                "Who is the highest paid employee at Google?"
        }
    )

    assert response_1.status_code == 200

    assert response_2.status_code == 200

    id_1 = response_1.json()["request_id"]

    id_2 = response_2.json()["request_id"]

    assert id_1 != id_2


# ============================================================
# TEST 11
# EXECUTION TIME
# ============================================================

def test_execution_time():

    response = client.post(
        "/query",
        json={
            "query":
                "Who is the highest paid employee at Google?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "execution_time" in data

    assert isinstance(
        data["execution_time"],
        (int, float)
    )

    assert data["execution_time"] >= 0


# ============================================================
# TEST 12
# EMPTY QUERY
# ============================================================

def test_empty_query():

    response = client.post(
        "/query",
        json={
            "query": ""
        }
    )

    assert response.status_code == 422


# ============================================================
# TEST 13
# WHITESPACE QUERY
# ============================================================

def test_whitespace_query():
    
    response = client.post(
        "/query",
        json={
            "query": "   "
        }
    )

    assert response.status_code == 400

    data = response.json()

    assert "detail" in data

    assert data["detail"]["error"] == (
        "Query cannot be empty."
    )

    assert "request_id" in data["detail"]

# ============================================================
# TEST 14
# MISSING QUERY FIELD
# ============================================================

def test_missing_query():

    response = client.post(
        "/query",
        json={}
    )

    assert response.status_code == 422


# ============================================================
# TEST 15
# INVALID REQUEST TYPE
# ============================================================

def test_invalid_request_type():

    response = client.post(
        "/query",
        json={
            "query": 12345
        }
    )

    # Pydantic converts compatible values,
    # so the important check is that the API
    # does not crash.

    assert response.status_code in [
        200,
        422
    ]


# ============================================================
# TEST 16
# QUERY TOO LONG
# ============================================================

def test_query_too_long():

    long_query = "Google " * 400

    response = client.post(
        "/query",
        json={
            "query": long_query
        }
    )

    assert response.status_code == 422


# ============================================================
# TEST 17
# INVALID HTTP METHOD
# ============================================================

def test_invalid_method():

    response = client.get(
        "/query"
    )

    assert response.status_code == 405


# ============================================================
# TEST 18
# RESPONSE STRUCTURE
# ============================================================

def test_response_structure():

    response = client.post(
        "/query",
        json={
            "query":
                "Who is the highest paid employee at Google?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    required_fields = [
        "request_id",
        "status",
        "answer",
        "execution_time",
        "error"
    ]

    for field in required_fields:

        assert field in data


# ============================================================
# TEST 19
# RESPONSE STATUS
# ============================================================

def test_response_status():

    response = client.post(
        "/query",
        json={
            "query":
                "Who is the highest paid employee at Google?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] in [
        "success",
        "error"
    ]


# ============================================================
# TEST 20
# HEALTH DOES NOT REQUIRE QUERY
# ============================================================

def test_health_without_body():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json()["status"] == (
        "healthy"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    import pytest

    print()
    print("=" * 60)
    print("MCP API TESTS")
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
        print("✅ ALL API TESTS PASSED")
        print("=" * 60)

    else:

        print("=" * 60)
        print("❌ API TESTS FAILED")
        print("=" * 60)

    sys.exit(exit_code)