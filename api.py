import time
import uuid
import re
import httpx

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import get_connection
from orchestrator import orchestrate
from config import APP_HOST, APP_PORT


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="MCP Agent Orchestrator API",
    description=(
        "Production-style API for the MCP multi-agent "
        "orchestration system."
    ),
    version="1.1.0"
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://mcp-orchestrator-bay.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class QueryRequest(BaseModel):

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User query for the MCP orchestrator."
    )

    session_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description=(
            "Optional conversation session identifier. "
            "Requests without one use the legacy default session."
        )
    )

class GitHubProfileRequest(BaseModel):

    profile_url: str = Field(
        ...,
        min_length=1,
        description="GitHub profile URL or username to discover repositories."
    )

class GitHubRepoOverviewRequest(BaseModel):

    repository_url: str = Field(
        ...,
        min_length=1,
        description="GitHub repository URL to get overview for."
    )


# ============================================================
# RESPONSE MODEL
# ============================================================

class QueryResponse(BaseModel):

    request_id: str

    status: str

    answer: str | None = None

    execution_time: float

    error: str | None = None

    execution_trace: dict | None = None


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():

    return {
        "service": "MCP Agent Orchestrator",
        "status": "running",
        "version": "1.1.0"
    }


# ============================================================
# HEALTH ENDPOINT
# ============================================================

@app.get("/health")
async def health():

    try:

        connection = get_connection()
        connection.close()

        return {
            "status": "healthy",
            "service": "MCP Agent Orchestrator",
            "database": "connected"
        }

    except Exception:

        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "MCP Agent Orchestrator",
                "database": "disconnected"
            }
        )


# ============================================================
# GITHUB REPOSITORY DISCOVERY ENDPOINT
# ============================================================

@app.post("/github/repositories")
async def discover_repositories(request: GitHubProfileRequest):

    url_val = request.profile_url.strip()
    
    # Extract the username. Allows raw usernames or full https://github.com/username URLs
    match = re.search(r"(?:github\.com/)?([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})/?$", url_val)
    
    if not match:
        raise HTTPException(
            status_code=400, 
            detail="Invalid GitHub profile URL or username."
        )
        
    username = match.group(1)
    
    api_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=headers, timeout=15.0)
            
            # Handle specific GitHub API Errors
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="GitHub user not found.")
            
            if response.status_code == 403 and "rate limit" in response.text.lower():
                raise HTTPException(status_code=429, detail="GitHub API rate limit exceeded. Please try again later.")
                
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"GitHub API failure: {response.status_code}")
            
            repos = response.json()
            
            if not isinstance(repos, list):
                raise HTTPException(status_code=502, detail="Invalid response format from GitHub API.")
            
            if not repos:
                return {"status": "success", "repositories": []}
            
            # Extract and return only safe, relevant metadata
            result = []
            for repo in repos:
                result.append({
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "url": repo.get("html_url"),
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "visibility": repo.get("visibility", "public"),
                    "default_branch": repo.get("default_branch"),
                    "updated_at": repo.get("updated_at")
                })
                
            return {"status": "success", "repositories": result}
            
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503, 
            detail="Network failure while contacting GitHub API."
        )


# ============================================================
# GITHUB REPOSITORY OVERVIEW ENDPOINT
# ============================================================

@app.post("/github/repository/overview")
async def get_repository_overview(request: GitHubRepoOverviewRequest):
    url_val = request.repository_url.strip()
    
    match = re.search(r"github\.com/([^/]+)/([^/?#\s]+)", url_val)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL.")
        
    owner, repo_name = match.groups()
    repo_name = repo_name.replace(".git", "")
    
    api_base = f"https://api.github.com/repos/{owner}/{repo_name}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    try:
        async with httpx.AsyncClient() as client:
            # 1. Fetch Repo info
            repo_resp = await client.get(api_base, headers=headers, timeout=15.0)
            if repo_resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Repository not found.")
            if repo_resp.status_code == 403 and "rate limit" in repo_resp.text.lower():
                raise HTTPException(status_code=429, detail="GitHub API rate limit exceeded.")
            if repo_resp.status_code != 200:
                raise HTTPException(status_code=repo_resp.status_code, detail=f"GitHub API failure: {repo_resp.status_code}")
                
            repo_data = repo_resp.json()
            default_branch = repo_data.get("default_branch", "main")
            
            # 2. Fetch Languages
            langs_resp = await client.get(f"{api_base}/languages", headers=headers, timeout=15.0)
            langs_data = langs_resp.json() if langs_resp.status_code == 200 else {}
            languages = list(langs_data.keys()) if langs_data else ["Not detected from supplied repository evidence."]
            
            # 3. Fetch Tree (Recursive) to detect evidence
            tree_resp = await client.get(f"{api_base}/git/trees/{default_branch}?recursive=1", headers=headers, timeout=15.0)
            tree_data = tree_resp.json() if tree_resp.status_code == 200 else {}
            paths = [item.get("path", "") for item in tree_data.get("tree", [])]
            
            # Evidence detection helpers
            def find_paths(keywords):
                return [p for p in paths if any(k.lower() in p.lower() for k in keywords)]

            frameworks = []
            if find_paths(["fastapi"]): frameworks.append("FastAPI")
            if find_paths(["react", "next"]): frameworks.append("React/Next.js")
            if find_paths(["flask"]): frameworks.append("Flask")
            if find_paths(["django"]): frameworks.append("Django")
            if find_paths(["spring"]): frameworks.append("Spring")
            if find_paths(["express"]): frameworks.append("Express.js")
            if find_paths(["vue"]): frameworks.append("Vue.js")
            if not frameworks: frameworks = ["Not detected from supplied repository evidence."]

            deps = []
            if find_paths(["requirements.txt"]): deps.append("requirements.txt (Python)")
            if find_paths(["package.json"]): deps.append("package.json (Node)")
            if find_paths(["pom.xml"]): deps.append("pom.xml (Java)")
            if find_paths(["gemfile"]): deps.append("Gemfile (Ruby)")
            if find_paths(["build.gradle"]): deps.append("build.gradle (Java/Kotlin)")
            if find_paths(["pyproject.toml"]): deps.append("pyproject.toml (Python)")
            if not deps: deps = ["Not detected from supplied repository evidence."]

            entry = find_paths(["main.py", "server.py", "app.py", "index.js", "app.jsx", "app.tsx", "manage.py", "run.py"])
            entry = list(set([p.split('/')[-1] for p in entry]))
            if not entry: entry = ["Not detected from supplied repository evidence."]

            apis = find_paths(["api.py", "routes", "controllers", "endpoints"])
            apis = list(set([p.split('/')[-1] for p in apis if p.endswith(('.py', '.js', '.ts', '.java', '.go'))]))
            if not apis: apis = ["Not detected from supplied repository evidence."]

            mcp = find_paths(["mcp", "orchestrator", "agent"])
            mcp = list(set([p.split('/')[-1] for p in mcp if p.endswith(('.py', '.js', '.ts', '.jsx', '.tsx'))]))
            if not mcp: mcp = ["Not detected from supplied repository evidence."]

            config = find_paths(["config.py", ".env", "tsconfig.json", "docker-compose", "settings.py", "vite.config", "webpack.config"])
            config = list(set([p.split('/')[-1] for p in config]))
            if not config: config = ["Not detected from supplied repository evidence."]

            testing = find_paths(["test", "spec", "pytest", "jest"])
            test_summary = ["Testing files/directories detected"] if testing else ["Not detected from supplied repository evidence."]

            deployment = []
            if find_paths([".github/workflows"]): deployment.append("GitHub Actions")
            if find_paths(["Dockerfile"]): deployment.append("Docker")
            if find_paths(["Jenkinsfile"]): deployment.append("Jenkins")
            if find_paths(["heroku"]): deployment.append("Heroku")
            if find_paths(["vercel.json"]): deployment.append("Vercel")
            if not deployment: deployment = ["Not detected from supplied repository evidence."]

            arch_summary = "Standard Repository Structure"
            has_frontend = find_paths(["frontend", "client", "ui", "web"])
            has_backend = find_paths(["backend", "api", "server"])
            
            if has_frontend and has_backend:
                arch_summary = "Client-Server / Full-Stack Architecture"
            elif find_paths(["mcp", "agent", "llm"]):
                arch_summary = "Agentic / AI Architecture"
            elif has_frontend and not has_backend:
                arch_summary = "Frontend Architecture"
            elif has_backend and not has_frontend:
                arch_summary = "Backend / API Architecture"

            top_structure = [p for p in paths if '/' not in p][:10]
            if not top_structure: top_structure = ["Not detected from supplied repository evidence."]

            return {
                "status": "success",
                "repository": {
                    "name": repo_data.get("name"),
                    "description": repo_data.get("description")
                },
                "architecture": {"summary": arch_summary},
                "structure": top_structure,
                "languages": languages,
                "frameworks": frameworks,
                "dependencies": deps,
                "entry_points": entry[:10],
                "apis": apis[:10],
                "mcp_components": mcp[:10],
                "configuration": config[:10],
                "testing": test_summary,
                "deployment": deployment
            }
            
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503, 
            detail="Network failure while contacting GitHub API."
        )


# ============================================================
# GLOBAL API ERROR HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):

    request_id = str(uuid.uuid4())

    print()
    print("=" * 60)
    print("API UNHANDLED ERROR")
    print("=" * 60)

    print(
        "Request ID:",
        request_id
    )

    print(
        "Path:",
        request.url.path
    )

    print(
        "Error:",
        str(exc)
    )

    print("=" * 60)

    return JSONResponse(
        status_code=500,
        content={
            "request_id": request_id,
            "status": "error",
            "answer": None,
            "execution_time": 0,
            "error": "Internal server error."
        }
    )


# ============================================================
# QUERY ENDPOINT
# ============================================================

@app.post(
    "/query",
    response_model=QueryResponse
)
async def query_agent(
    request: QueryRequest,
    http_request: Request
):

    start_time = time.perf_counter()

    request_id = str(uuid.uuid4())

    query = request.query.strip()

    # Preserve backward compatibility for existing clients/tests.
    # The frontend will provide a real session_id for isolated memory.
    session_id = (
        request.session_id.strip()
        if request.session_id
        else "default"
    )

    # Optional BYOK support:
    # If the frontend sends X-OpenRouter-Key, the orchestrator
    # can use that key for this request. If omitted, existing
    # behavior continues using the server-configured key.
    user_openrouter_key = http_request.headers.get("X-OpenRouter-Key")
    
    if user_openrouter_key:
        print("BYOK RECEIVED: YES")
    else:
        print("BYOK RECEIVED: NO")

    # --------------------------------------------------------
    # EMPTY QUERY
    # --------------------------------------------------------

    if not query:

        raise HTTPException(
            status_code=400,
            detail={
                "request_id": request_id,
                "error": "Query cannot be empty."
            }
        )

    # --------------------------------------------------------
    # REQUEST LOG
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("MCP API REQUEST")
    print("=" * 60)

    print(
        "Request ID:",
        request_id
    )

    print(
        "Query:",
        query
    )

    print(
        "Session ID:",
        session_id
    )

    print("=" * 60)

    try:

        # ----------------------------------------------------
        # ORCHESTRATOR
        # ----------------------------------------------------

        result = await orchestrate(
            query,
            session_id,
            api_key=user_openrouter_key
        )

        # ----------------------------------------------------
        # EXECUTION TIME
        # ----------------------------------------------------

        execution_time = round(
            time.perf_counter() - start_time,
            3
        )

        # ----------------------------------------------------
        # INVALID RESULT
        # ----------------------------------------------------

        if not isinstance(
            result,
            dict
        ):

            return QueryResponse(
                request_id=request_id,
                status="error",
                answer=None,
                execution_time=execution_time,
                error=(
                    "Orchestrator returned "
                    "an invalid result."
                ),
                execution_trace=None
            )

        # ----------------------------------------------------
        # RESULT VALUES
        # ----------------------------------------------------

        status = result.get(
            "status",
            "error"
        )

        answer = result.get(
            "answer"
        )

        error = result.get(
            "error"
        )

        # FIX:
        # Always define execution_trace before the response.
        execution_trace = result.get(
            "execution_trace"
        )
        # --------------------------------------------------------
        # FRIENDLY OPENROUTER RATE-LIMIT MESSAGE
        # --------------------------------------------------------

        if status == "error" and error:

            error_text = str(error)

            if (
                "429" in error_text
                or "Rate limit exceeded" in error_text
                or "free-models-per-day" in error_text
            ):

                error = (
                    "AI request limit reached. "
                    "The free AI model limit has been reached for today. "
                    "Your MCP system is working correctly. "
                    "Please wait for the limit to reset and try again."
        )

        # ----------------------------------------------------
        # STATUS VALIDATION
        # ----------------------------------------------------

        if status not in [
            "success",
            "error"
        ]:

            status = "error"

            if error is None:

                error = (
                    "Orchestrator returned "
                    "an invalid status."
                )

        # ----------------------------------------------------
        # RESPONSE LOG
        # ----------------------------------------------------

        print(
            "Request ID:",
            request_id
        )

        print(
            "Status:",
            status
        )

        print(
            "Execution Time:",
            f"{execution_time:.3f}s"
        )

        print(
            "MCP API REQUEST COMPLETED"
        )

        print("=" * 60)

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return QueryResponse(
            request_id=request_id,
            status=status,
            answer=answer,
            execution_time=execution_time,
            error=error,
            execution_trace=execution_trace
        )

    except Exception as exc:

        execution_time = round(
            time.perf_counter() - start_time,
            3
        )

        # ----------------------------------------------------
        # ORIGINAL ERROR
        # ----------------------------------------------------

        error_message = str(exc)

        # ----------------------------------------------------
        # FRIENDLY ERROR HANDLING
        # ----------------------------------------------------

        if (
            "429" in error_message
            or "Rate limit exceeded" in error_message
            or "free-models-per-day" in error_message
        ):

            error_message = (
                "The AI service has reached its current "
                "request limit. The MCP system is working "
                "correctly. Please try again later."
            )

        elif (
            "401" in error_message
            or "Invalid API key" in error_message
            or "authentication" in error_message.lower()
        ):

            error_message = (
                "The AI service authentication failed. "
                "Please check the API configuration."
            )

        elif "timeout" in error_message.lower():

            error_message = (
                "The AI service took too long to respond. "
                "Please try again."
            )

        # ----------------------------------------------------
        # FAILURE LOG
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("MCP API REQUEST FAILED")
        print("=" * 60)

        print(
            "Request ID:",
            request_id
        )

        print(
            "Original Error:",
            str(exc)
        )

        print(
            "User Error:",
            error_message
        )

        print(
            "Execution Time:",
            f"{execution_time:.3f}s"
        )

        print("=" * 60)

        # ----------------------------------------------------
        # FRIENDLY ERROR RESPONSE
        # ----------------------------------------------------

        return QueryResponse(
            request_id=request_id,
            status="error",
            answer=None,
            execution_time=execution_time,
            error=error_message,
            execution_trace=None
        )


# ============================================================
# LOCAL / PRODUCTION SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "api:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=False
    )