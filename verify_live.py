"""Live production verification. Does not print secrets."""
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv()

BASE = os.getenv("VITE_API_URL") or "http://127.0.0.1:8000"


def configured(name):
    value = os.getenv(name)
    return bool(value and str(value).strip())


def request(method, path, body=None, token=None, extra=None):
    url = BASE + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra:
        headers.update(extra)
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"error": raw}
        return exc.code, payload


def signup(email, password):
    status, payload = request("POST", "/auth/register", {"email": email, "password": password})
    if status == 400:
        status, payload = request("POST", "/auth/login", {"email": email, "password": password})
    return status, payload


def main():
    print("=== ENV PRESENCE ===")
    print("OPENROUTER_API_KEY", "CONFIGURED" if configured("OPENROUTER_API_KEY") else "MISSING")
    print("OPENWEATHER_API_KEY", "CONFIGURED" if configured("OPENWEATHER_API_KEY") else "MISSING")
    print("GITHUB_TOKEN", "CONFIGURED" if configured("GITHUB_TOKEN") else "MISSING")
    print("DB_HOST", "CONFIGURED" if configured("DB_HOST") else "MISSING")
    print("DB_NAME", "CONFIGURED" if configured("DB_NAME") else "MISSING")
    print("DB_USER", "CONFIGURED" if configured("DB_USER") else "MISSING")
    print("DB_PASSWORD", "CONFIGURED" if configured("DB_PASSWORD") else "MISSING")

    print("=== HEALTH ===")
    status, health = request("GET", "/health")
    print("GET /health", status, health.get("status"), health.get("database"))

    password_a = "Qa-" + secrets.token_urlsafe(8)
    password_b = "Qa-" + secrets.token_urlsafe(8)
    email_a = "test-user-a@example.test"
    email_b = "test-user-b@example.test"

    print("=== AUTH ===")
    sa, a = signup(email_a, password_a)
    sb, b = signup(email_b, password_b)
    print("register/login A", sa, "user" in a, "token" in a)
    print("register/login B", sb, "user" in b, "token" in b)
    if sa >= 400:
        print("A detail", a)
        return
    if sb >= 400:
        print("B detail", b)
        return

    id_a = a["user"]["id"]
    id_b = b["user"]["id"]
    print("ids_differ", id_a != id_b)
    print("A usage", a.get("usage"))
    print("B usage", b.get("usage"))

    print("=== SPOOF ===")
    status, me = request("GET", "/auth/me", extra={"X-User-Id": id_b}, token=a["token"])
    print("A /auth/me with spoof header", status, me.get("user", {}).get("id") == id_a)

    status, usage_unauth = request("GET", "/usage")
    print("GET /usage no auth", status)

    print("=== QUOTA A SUCCESS ===")
    q1_status, q1 = request(
        "POST",
        "/query",
        {"query": "Who is the highest paid employee at Google?", "session_id": "qa-a"},
        token=a["token"],
    )
    print("A salary query", q1_status, q1.get("status"), q1.get("agent"), q1.get("usage"))
    print("A request_id", bool(q1.get("request_id")))

    status, me_a = request("GET", "/auth/me", token=a["token"])
    print("A reload usage", me_a.get("usage"))
    status, me_b = request("GET", "/auth/me", token=b["token"])
    print("B usage after A request", me_b.get("usage"))

    print("=== WEATHER ===")
    w_status, weather = request(
        "POST",
        "/query",
        {"query": "What is the weather in Hyderabad?", "session_id": "qa-a"},
        token=a["token"],
    )
    print(
        "weather",
        w_status,
        weather.get("status"),
        weather.get("agent"),
        weather.get("error_code"),
        "key_in_body",
        "OPENWEATHER" in json.dumps(weather).upper() and "API_KEY" in json.dumps(weather),
    )
    print("weather_error_present", bool(weather.get("error")))
    print("A usage after weather", weather.get("usage"))

    print("=== DEVELOPER Q ===")
    d_status, dev = request(
        "POST",
        "/query",
        {"query": "What is the difference between Python and C?", "session_id": "qa-a"},
        token=a["token"],
    )
    print(
        "python vs c",
        d_status,
        dev.get("status"),
        dev.get("agent"),
        "final report" in str(dev.get("error") or "").lower(),
        "answer_len",
        len(str(dev.get("answer") or "")),
    )

    print("=== GITHUB OVERVIEW ===")
    g_status, overview = request(
        "POST",
        "/github/repository/overview",
        {"repository_url": "https://github.com/pallets/flask"},
        token=a["token"],
    )
    print(
        "overview",
        g_status,
        overview.get("status"),
        "structure",
        bool(overview.get("structure")),
        "frameworks",
        overview.get("frameworks"),
    )

    print("=== REPO ANALYZE ===")
    r_status, repo = request(
        "POST",
        "/query",
        {
            "query": (
                "Analyze https://github.com/pallets/flask. Find real issues, "
                "explain the architecture, and analyze the repository based only "
                "on supplied repository evidence."
            ),
            "session_id": "qa-a",
        },
        token=a["token"],
    )
    print(
        "repo analyze",
        r_status,
        repo.get("status"),
        repo.get("agent"),
        repo.get("error_code"),
        "generic_final_report",
        str(repo.get("error") or "").find("did not produce a final report") >= 0,
        "usage",
        repo.get("usage"),
    )

    print("=== B ISOLATION ===")
    status, usage_b = request("GET", "/usage", token=b["token"])
    print("B GET /usage", status, usage_b.get("usage"))


if __name__ == "__main__":
    main()
