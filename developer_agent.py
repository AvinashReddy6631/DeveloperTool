import os
import re
import time
import base64
import json
import difflib

from dotenv import load_dotenv
from openai import OpenAI
import httpx


load_dotenv()


# ============================================================
# CONFIGURATION & CONSTANTS
# ============================================================

# Maximum characters allowed per individual analysis group.
MAX_GROUP_CHARS = int(os.getenv("MAX_GROUP_CHARS", "5000"))

# Maximum groups to analyze (can be configured via env var)
MAX_ANALYSIS_GROUPS = int(os.getenv("MAX_ANALYSIS_GROUPS", "8"))

# Maximum tokens for LLM output (configured via env var)
DEVELOPER_MAX_TOKENS = int(os.getenv("DEVELOPER_MAX_TOKENS", "400"))

# Delay between group requests to prevent triggering rate limits.
BATCH_DELAY_SECONDS = float(os.getenv("DEVELOPER_AGENT_BATCH_DELAY", "1.5"))

# Request timeout and retry settings
LLM_REQUEST_TIMEOUT = float(os.getenv("DEVELOPER_AGENT_TIMEOUT", "45.0"))
MAX_RETRIES = int(os.getenv("DEVELOPER_AGENT_MAX_RETRIES", "3"))


# ============================================================
# GITHUB HELPERS
# ============================================================

GITHUB_API = "https://api.github.com"


def _extract_github_target(query):
    """
    Detect whether the query contains a GitHub repository or profile.

    Returns:
        ("repo", owner, repo)
        ("user", username, None)
        (None, None, None)
    """

    q = str(query).strip()

    # Full GitHub repository URL
    repo_match = re.search(
        r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)",
        q,
        flags=re.IGNORECASE,
    )

    if repo_match:
        owner = repo_match.group(1)
        repo = repo_match.group(2)
        
        # Strip trailing punctuation
        repo = re.sub(r"[\.,;:'\"\)\]>]+$", "", repo)
        repo = re.sub(r"\.git$", "", repo, flags=re.IGNORECASE)

        # Ignore obvious non-repository GitHub URLs
        if repo.lower() not in {
            "issues",
            "pulls",
            "settings",
            "followers",
            "following",
            "repositories",
        }:
            return "repo", owner, repo

    # GitHub profile URL
    user_match = re.search(
        r"github\.com/([A-Za-z0-9_.-]+)",
        q,
        flags=re.IGNORECASE,
    )

    if user_match:
        username = user_match.group(1)
        username = re.sub(r"[\.,;:'\"\)\]>]+$", "", username)

        if username.lower() not in {
            "login",
            "signup",
            "settings",
            "features",
            "pricing",
            "explore",
            "marketplace",
        }:
            return "user", username, None

    return None, None, None


def _extract_github_repo(query):
    """
    Backward-compatible helper.
    """

    target_type, owner, repo = _extract_github_target(query)

    if target_type == "repo":
        return owner, repo

    return None, None


def _extract_github_repo_url(text):
    """
    Robustly extracts a clean GitHub repository URL from arbitrary text.
    Handles punctuation, brackets, and natural language formatting.
    """
    target_type, owner, repo = _extract_github_target(text)
    if target_type == "repo":
        return f"https://github.com/{owner}/{repo}"
    return None


def _extract_requested_files(query):
    """
    Extract specific files requested in the query.
    """
    files = []
    for word in str(query).split():
        w = word.strip(' ,;.:"\'?!()[]{}')
        if "github.com" in w.lower() or "http" in w.lower():
            continue
        # Check if it looks like a file path or extension
        if "/" in w or re.search(r'\.[a-zA-Z0-9]{1,5}$', w):
            if re.search(r'\.(py|js|jsx|ts|tsx|json|md|txt|yml|yaml|toml|ini|html|css|sh|c|cpp|h|go|rs|java|php)$', w.lower()) or w.lower() in ["dockerfile", "makefile", "package.json"]:
                files.append(w)
    return files


def _github_headers():
    """
    GitHub API headers.

    GITHUB_TOKEN is optional.
    """

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "DevGitHub-AI",
    }

    token = os.getenv("GITHUB_TOKEN")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def _github_get(path, params=None):
    """
    Safe GET request to GitHub API.
    """

    try:
        with httpx.Client(
            timeout=15.0,
            follow_redirects=True,
        ) as client:

            response = client.get(
                f"{GITHUB_API}{path}",
                headers=_github_headers(),
                params=params,
            )

        if response.status_code == 200:
            return response.json(), None

        if response.status_code == 404:
            return None, "GitHub returned HTTP 404 (Not Found). The resource URL might be invalid, does not exist, or is private without a valid GITHUB_TOKEN."

        if response.status_code == 401:
            return None, "GitHub returned HTTP 401 (Unauthorized). Authentication failed. Your GITHUB_TOKEN may be invalid, expired, or lack necessary scopes."

        if response.status_code == 403:
            return None, "GitHub returned HTTP 403 (Forbidden). API access was denied, likely due to GitHub API rate limits."
            
        if response.status_code == 429:
            return None, "GitHub returned HTTP 429 (Too Many Requests). Rate limit exceeded. Please try again later."

        return (
            None,
            f"GitHub API returned unexpected HTTP {response.status_code}.",
        )

    except httpx.RequestError as exc:
        return None, f"GitHub network request failed: {exc}"
    except Exception as exc:
        return None, f"GitHub request failed: {exc}"


# ============================================================
# GITHUB USER REPOSITORIES (FEATURE)
# ============================================================

def get_github_user_repositories(github_user_url):
    """
    Fetch all public repositories for a given GitHub user profile URL or username.
    Returns structured repository data tailored for frontend repository cards.
    """
    q = str(github_user_url).strip()
    
    # Handle direct username or full URL
    if "github.com/" in q:
        match = re.search(r"github\.com/([A-Za-z0-9_.-]+)", q, flags=re.IGNORECASE)
        if not match:
            raise ValueError(f"Invalid GitHub user URL: {github_user_url}")
        username = match.group(1)
    else:
        username = q

    username = re.sub(r"[\.,;:'\"\)\]>]+$", "", username)
    
    ignored_usernames = {
        "login", "signup", "settings", "features", "pricing", 
        "explore", "marketplace", "topics", "collections", "trending"
    }
    if not username or username.lower() in ignored_usernames:
        raise ValueError(f"Invalid or reserved GitHub username: {username}")

    all_repos = []
    page = 1
    per_page = 100

    while True:
        data, error = _github_get(
            f"/users/{username}/repos",
            params={"type": "owner", "sort": "updated", "per_page": per_page, "page": page}
        )
        if error:
            if page == 1:
                if "404" in error:
                    raise RuntimeError(f"GitHub user '{username}' not found.")
                raise RuntimeError(f"Could not fetch repositories for user '{username}': {error}")
            break
        
        if not isinstance(data, list) or not data:
            break

        for repo in data:
            all_repos.append({
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description"),
                "html_url": repo.get("html_url"),
                "clone_url": repo.get("clone_url"),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "open_issues": repo.get("open_issues_count", 0),
                "updated_at": repo.get("updated_at"),
                "created_at": repo.get("created_at"),
                "default_branch": repo.get("default_branch", "main"),
                "private": repo.get("private", False),
                "archived": repo.get("archived", False),
            })

        if len(data) < per_page:
            break
        page += 1

    return {
        "status": "success",
        "username": username,
        "repositories": all_repos
    }


def analyze_github_user_repository(github_user_url, repo_identifier=0, query=None):
    """
    Product Workflow:
    1. Fetches repositories for the GitHub user URL.
    2. Selects ONE repository by index (int) or name (str).
    3. Passes the selected repository URL to analyze_github_repository_code().
    4. Returns the complete analysis result including repository metadata.
    """
    res = get_github_user_repositories(github_user_url)
    repos = res.get("repositories", [])
    if not repos:
        raise ValueError(f"No repositories found for GitHub user URL: {github_user_url}")
    
    selected_repo = None
    if isinstance(repo_identifier, int):
        if repo_identifier < 0 or repo_identifier >= len(repos):
            raise IndexError(f"Repository index {repo_identifier} out of range (0-{len(repos)-1})")
        selected_repo = repos[repo_identifier]
    elif isinstance(repo_identifier, str):
        match = next(
            (r for r in repos if r["name"].lower() == repo_identifier.lower() or r["full_name"].lower() == repo_identifier.lower()), 
            None
        )
        if not match:
            raise ValueError(f"Repository '{repo_identifier}' not found in user repositories.")
        selected_repo = match
    else:
        selected_repo = repos[0]

    repo_url = selected_repo["html_url"]
    
    # Run the existing analysis pipeline
    analysis_result = analyze_github_repository_code(repo_url, query=query)
    
    # Attach frontend-ready context
    analysis_result["selected_user_repository"] = selected_repo
    analysis_result["user_repositories_list"] = repos
    
    return analysis_result


# ============================================================
# GITHUB REPOSITORY CONTEXT
# ============================================================

def _get_github_repo_context(owner, repo):
    """
    Get high-level repository information.
    """

    data, error = _github_get(
        f"/repos/{owner}/{repo}"
    )

    if error:
        return (
            f"GitHub repository context could not be loaded "
            f"for {owner}/{repo}. {error}"
        )

    if not data:
        return None

    sections = [
        f"""
GitHub Repository Context
-------------------------
Repository: {data.get('full_name', f'{owner}/{repo}')}
Description: {data.get('description') or 'No description provided.'}
Default branch: {data.get('default_branch') or 'unknown'}
Stars: {data.get('stargazers_count', 0)}
Forks: {data.get('forks_count', 0)}
Open issues: {data.get('open_issues_count', 0)}
Primary language: {data.get('language') or 'unknown'}
License: {(data.get('license') or {}).get('spdx_id', 'not specified')}
Archived: {data.get('archived', False)}
Created: {data.get('created_at', 'unknown')}
Last updated: {data.get('updated_at', 'unknown')}
Repository URL: {data.get('html_url', '')}
"""
    ]

    # Languages
    languages, _ = _github_get(
        f"/repos/{owner}/{repo}/languages"
    )

    if isinstance(languages, dict) and languages:
        sections.append(
            "\nLanguages:\n" +
            ", ".join(languages.keys())
        )

    # Topics
    topics = data.get("topics", [])

    if topics:
        sections.append(
            "\nTopics:\n" +
            ", ".join(topics)
        )

    # Recent commits
    commits, _ = _github_get(
        f"/repos/{owner}/{repo}/commits",
        params={"per_page": 10},
    )

    if isinstance(commits, list) and commits:

        commit_lines = []

        for commit in commits:
            message = (
                commit.get("commit", {})
                .get("message", "")
                .split("\n")[0]
            )

            sha = commit.get("sha", "")[:7]

            if message:
                commit_lines.append(
                    f"- {sha}: {message}"
                )

        if commit_lines:
            sections.append(
                "\nRecent Commits:\n" +
                "\n".join(commit_lines)
            )

    # Open pull requests
    pulls, _ = _github_get(
        f"/repos/{owner}/{repo}/pulls",
        params={
            "state": "open",
            "per_page": 10,
        },
    )

    if isinstance(pulls, list):

        pull_lines = [
            f"- #{pull.get('number')}: {pull.get('title', '')}"
            for pull in pulls
        ]

        if pull_lines:
            sections.append(
                "\nSample Open Pull Requests:\n" +
                "\n".join(pull_lines)
            )

    return "\n".join(sections)


# ============================================================
# GITHUB USER CONTEXT
# ============================================================

def _get_github_user_context(username):
    """
    Get GitHub profile and public repository information.
    """

    data, error = _github_get(
        f"/users/{username}"
    )

    if error:
        return (
            f"GitHub profile context could not be loaded "
            f"for {username}. {error}"
        )

    if not data:
        return None

    sections = [
        f"""
GitHub Profile Context
----------------------
Username: {data.get('login', username)}
Name: {data.get('name') or 'Not provided'}
Bio: {data.get('bio') or 'No bio provided.'}
Company: {data.get('company') or 'Not provided'}
Location: {data.get('location') or 'Not provided'}
Public repositories: {data.get('public_repos', 0)}
Public gists: {data.get('public_gists', 0)}
Followers: {data.get('followers', 0)}
Following: {data.get('following', 0)}
Profile URL: {data.get('html_url', '')}
"""
    ]

    repos, _ = _github_get(
        f"/users/{username}/repos",
        params={
            "type": "owner",
            "sort": "updated",
            "per_page": 30,
        },
    )

    if isinstance(repos, list):

        repo_lines = []

        for repo in repos:

            repo_lines.append(
                f"- {repo.get('full_name', repo.get('name', ''))} | "
                f"language={repo.get('language') or 'unknown'} | "
                f"stars={repo.get('stargazers_count', 0)} | "
                f"forks={repo.get('forks_count', 0)} | "
                f"description="
                f"{repo.get('description') or 'No description'}"
            )

        if repo_lines:
            sections.append(
                "\nPublic Repositories:\n" +
                "\n".join(repo_lines)
            )

    return "\n".join(sections)


# ============================================================
# GENERAL GITHUB CONTEXT
# ============================================================

def _get_github_context(query):
    """
    Determine whether the query contains a GitHub repository
    or profile and return appropriate context.
    """

    target_type, owner, repo = _extract_github_target(query)

    if target_type == "repo":
        return _get_github_repo_context(
            owner,
            repo,
        )

    if target_type == "user":
        return _get_github_user_context(
            owner,
        )

    return None


# ============================================================
# GITHUB REPOSITORY CODE ANALYSIS
# ============================================================

def _github_get_tree(owner, repo, branch):
    """
    Get the complete Git tree recursively.
    """

    data, error = _github_get(
        f"/repos/{owner}/{repo}/git/trees/{branch}",
        params={"recursive": "1"},
    )

    if error:
        return [], error

    if not data:
        return [], "GitHub returned no tree data."
        
    if getattr(data, "get", None) and data.get("truncated"):
        pass

    tree = data.get("tree", [])

    return tree, None


def _github_get_file(owner, repo, path, branch):
    """
    Get a text file from a GitHub repository.
    """

    data, error = _github_get(
        f"/repos/{owner}/{repo}/contents/{path}",
        params={"ref": branch},
    )

    if error:
        return None, error

    if not data:
        return None, "No file data returned."

    if isinstance(data, list):
        return None, "Requested path is a directory."

    if data.get("type") != "file":
        return None, "Requested path is not a file."

    content = data.get("content")

    if not content:
        return None, "File has no readable content."

    try:
        decoded = base64.b64decode(
            content
        ).decode(
            "utf-8",
            errors="replace",
        )

        return decoded, None

    except Exception as exc:
        return None, f"Could not decode file: {exc}"


def _is_useful_code_file(path):
    """
    Decide whether a repository file is useful for AI code analysis.
    Excludes generated lock files and prioritizes source/config files.
    """

    lower = path.lower()
    filename = lower.split("/")[-1]

    # Exclude lock files as requested
    excluded_lock_files = {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "pipfile.lock",
    }
    if filename in excluded_lock_files:
        return False

    ignored_directories = (
        "node_modules/",
        ".git/",
        "dist/",
        "build/",
        ".next/",
        "coverage/",
        "__pycache__/",
        ".venv/",
        "venv/",
        "vendor/",
    )

    for directory in ignored_directories:
        if directory in lower:
            return False

    ignored_extensions = (
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".svg",
        ".mp4",
        ".mp3",
        ".zip",
        ".pdf",
        ".exe",
        ".dll",
        ".woff",
        ".woff2",
        ".ttf",
        ".lock",
    )

    if lower.endswith(ignored_extensions):
        return False

    useful_extensions = (
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".swift",
        ".kt",
        ".kts",
        ".cs",
        ".html",
        ".css",
        ".scss",
        ".sql",
        ".sh",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".ini",
        ".md",
        ".txt",
        ".env.example",
        ".dockerfile",
    )

    if filename in {
        "dockerfile",
        "makefile",
        "requirements.txt",
        "pyproject.toml",
        "package.json",
        "readme.md",
        "contributing.md",
        "docker-compose.yml",
        "docker-compose.yaml",
    }:
        return True

    return lower.endswith(useful_extensions)


def _score_code_file(path, query_intent="general"):
    """
    Score files and assign a category for PASS 1 Repository Inventory.
    Prioritizes Python, JS, JSX, TS, TSX, and core source files over README files.
    Returns: (score, category)
    """

    lower = path.lower()
    score = 0
    filename = lower.split("/")[-1]
    
    # 1. Classification
    category = "OTHER"
    if "mcp" in lower:
        category = "MCP"
    elif "agent" in lower:
        category = "AGENTS"
    elif lower.endswith((".jsx", ".tsx", ".css", ".scss", ".html", "tailwind.config.js")):
        category = "FRONTEND"
    elif "/tests/" in lower or lower.startswith("tests/") or "test_" in filename:
        category = "TESTS"
    elif filename in ["dockerfile", "compose.yaml", "docker-compose.yml", "docker-compose.yaml"]:
        category = "DOCKER"
    elif "/.github/workflows/" in lower or lower.startswith(".github/workflows/"):
        category = "CI_CD"
    elif "auth" in lower or "security" in lower or "jwt" in lower or "login" in lower:
        category = "AUTH"
    elif lower.endswith((".json", ".toml", ".txt", ".ini", ".yaml", ".yml", ".env.example", "config.py", "settings.py")):
        category = "CONFIG"
    elif "api" in lower or "server" in lower or "routes" in lower or "controllers" in lower:
        category = "API"
    elif "db" in lower or "database" in lower or "models" in lower or "schemas" in lower:
        category = "DATABASE"
    elif filename.endswith(".md"):
        category = "DOCUMENTATION"
    elif lower.endswith((".py", ".js", ".ts", ".go", ".rs", ".java", ".c", ".cpp")):
        category = "CORE_BACKEND"

    # 2. Priority Scoring (Prioritizing Python/JS/TS source files over README)
    important_names = {
        "pyproject.toml": 160,
        "requirements.txt": 155,
        "package.json": 155,
        "dockerfile": 150,
        "compose.yaml": 150,
        "docker-compose.yml": 150,
        "docker-compose.yaml": 150,
        "config.py": 145,
        "settings.py": 145,
        "api.py": 140,
        "server.py": 140,
        "app.py": 140,
        "main.py": 140,
        "readme.md": 90,
    }

    score += important_names.get(filename, 0)

    if lower.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
        score += 80

    if "src/" in lower:
        score += 30
    if "app/" in lower:
        score += 25
    if category == "API":
        score += 20
    if category == "AGENTS":
        score += 20
    if category == "AUTH":
        score += 20
    if category == "CORE_BACKEND":
        score += 15

    score -= lower.count("/") * 2
    return score, category


def github_repository_code_context(
    url,
    requested_files=None,
    query=None,
):
    """
    Read-only repository analysis primitive.
    Implements complete repository tree fetching, useful-file selection,
    complete-file retrieval, and fine-grained analysis groups.
    """

    target_type, owner, repo = _extract_github_target(url)

    if target_type != "repo":
        raise ValueError(f"Expected a valid GitHub repository URL. Got: {url}")

    print(f"[DeveloperAgent] Fetching repository metadata for {owner}/{repo}...")
    repo_data, error = _github_get(f"/repos/{owner}/{repo}")

    if error:
        raise RuntimeError(error)

    if not repo_data:
        raise RuntimeError("GitHub repository was not found or is empty.")

    branch = repo_data.get("default_branch") or "main"

    print(f"[DeveloperAgent] Fetching complete repository tree for branch: {branch}...")
    tree, tree_error = _github_get_tree(owner, repo, branch)

    if tree_error:
        raise RuntimeError(tree_error)

    # Pass 1: Inventory
    files = [
        item for item in tree
        if item.get("type") == "blob" and _is_useful_code_file(item.get("path", ""))
    ]

    query_intent = "general"
    if query:
        q = str(query).lower()
        if "secur" in q or "vulnerab" in q: query_intent = "security"
        elif "architect" in q or "flow" in q or "structure" in q: query_intent = "architecture"
        elif "test" in q: query_intent = "testing"
        elif "databas" in q or "sql" in q or "model" in q: query_intent = "database"
        elif "perform" in q or "bottleneck" in q or "scalab" in q: query_intent = "performance"
        elif "front" in q or "ui " in q or "react" in q or "css" in q: query_intent = "frontend"

    # Pass 2: Priority Selection
    scored_files = []
    for item in files:
        path = item.get("path", "")
        score, category = _score_code_file(path, query_intent)
        item["_score"] = score
        item["_category"] = category
        scored_files.append(item)

    selected_paths = []
    missing_requested_paths = []

    if requested_files:
        useful_paths = {item.get("path") for item in files}
        for requested in requested_files:
            requested = str(requested).strip().lstrip("./")
            if requested in useful_paths:
                selected_paths.append(requested)
            else:
                missing_requested_paths.append(requested)
    else:
        ranked = sorted(scored_files, key=lambda x: x["_score"], reverse=True)
        max_files_to_fetch = min(40, len(ranked))
        selected_paths = [item.get("path") for item in ranked[:max_files_to_fetch]]

    # Pass 3: File Retrieval
    selected_files = []
    retrieved_paths = []
    truncated_files_count = 0
    file_categories = {}

    for item in scored_files:
        if item["path"] in selected_paths:
            file_categories[item["path"]] = item["_category"]

    for path in selected_paths:
        content, file_error = _github_get_file(
            owner,
            repo,
            path,
            branch,
        )

        if file_error:
            if "403" in file_error or "429" in file_error:
                break
            selected_files.append({
                "path": path,
                "content": "",
                "error": file_error,
                "truncated": False,
                "original_size": 0,
                "retrieved_size": 0,
                "category": file_categories.get(path, "OTHER"),
                "raw_content": ""
            })
            continue

        if content is None:
            content = ""

        original_size = len(content)
        truncated = False
        max_file_chars = 15000

        raw_content_backup = content

        if original_size > max_file_chars:
            content = content[:max_file_chars] + "\n\n[FILE TRUNCATED FOR ANALYSIS]"
            truncated = True
            truncated_files_count += 1

        retrieved_size = len(content)

        lines = content.split('\n')
        numbered_content = '\n'.join(f"{i:03d} | {line}" for i, line in enumerate(lines, 1))

        selected_files.append({
            "path": path,
            "content": numbered_content,
            "raw_content": raw_content_backup,
            "truncated": truncated,
            "original_size": original_size,
            "retrieved_size": retrieved_size,
            "category": file_categories.get(path, "OTHER")
        })
        retrieved_paths.append(path)

    # Coverage Metrics
    total_files = len(tree)
    useful_files_count = len(files)
    retrieved_files_count = len(retrieved_paths)
    coverage_percent = round((retrieved_files_count / max(1, useful_files_count)) * 100, 2)

    retrieved_set = set(retrieved_paths)
    not_retrieved_paths = [item.get("path") for item in files if item.get("path") not in retrieved_set]
    important_missing = [p for p in not_retrieved_paths if _score_code_file(p, query_intent)[0] >= 100]

    # Logical Analysis Groups Definition
    SUPER_GROUP_ORDER = [
        "Repository & Configuration",
        "Backend, API & Orchestration",
        "Frontend",
        "Authentication & Security",
        "Database & Data Layer",
        "Testing",
        "Dependencies, Build & Deployment",
        "Documentation"
    ]
    
    SUPER_GROUP_MAP = {
        "DOCUMENTATION": "Documentation",
        "CONFIG": "Repository & Configuration",
        "CORE_BACKEND": "Backend, API & Orchestration",
        "API": "Backend, API & Orchestration",
        "AGENTS": "Backend, API & Orchestration",
        "AUTH": "Authentication & Security",
        "DATABASE": "Database & Data Layer",
        "MCP": "Database & Data Layer",
        "TESTS": "Testing",
        "FRONTEND": "Frontend",
        "DOCKER": "Dependencies, Build & Deployment",
        "CI_CD": "Dependencies, Build & Deployment",
        "OTHER": "Repository & Configuration",
    }

    grouped_files = {k: [] for k in SUPER_GROUP_ORDER}
    for f in selected_files:
        if f.get("error") or not f.get("content"): 
            continue
        gname = SUPER_GROUP_MAP.get(f.get("category", "OTHER"), "Dependencies, Build & Deployment")
        if gname in grouped_files:
            grouped_files[gname].append(f)
        
    analysis_groups = []
    group_id_counter = 1
    
    for gname in SUPER_GROUP_ORDER:
        gfiles = grouped_files.get(gname, [])
        if not gfiles:
            continue
            
        parts_needed = []
        current_text = ""
        current_files = []
        
        for file_info in gfiles:
            file_text = f"\n===== FILE: {file_info['path']} =====\n{file_info['content']}\n===== END FILE =====\n"
            if len(current_text) + len(file_text) > MAX_GROUP_CHARS and current_text:
                parts_needed.append((current_files, current_text))
                current_text = file_text
                current_files = [file_info["path"]]
            else:
                current_text += file_text
                current_files.append(file_info["path"])
                
        if current_text:
            parts_needed.append((current_files, current_text))
            
        is_split = len(parts_needed) > 1
        
        for idx, (p_files, p_text) in enumerate(parts_needed):
            cat_name = f"{gname} (Part {idx+1})" if is_split else gname
            analysis_groups.append({
                "group_id": group_id_counter,
                "category": cat_name,
                "name": cat_name,
                "files": p_files,
                "content": p_text,
                "text": p_text,
                "file_count": len(p_files),
                "content_length": len(p_text)
            })
            group_id_counter += 1

    # Build legacy LLM-ready context
    context_parts = []
    context_parts.append(
        "===== REPOSITORY METADATA =====\n"
        f"Owner: {owner}\n"
        f"Repository: {repo}\n"
        f"Full Name: {repo_data.get('full_name', f'{owner}/{repo}')}\n"
        f"Branch: {branch}\n"
        f"Description: {repo_data.get('description') or 'Unavailable'}\n"
        f"Primary Language: {repo_data.get('language') or 'Unavailable'}\n"
        f"Stars: {repo_data.get('stargazers_count', 0)}\n"
        f"URL: {repo_data.get('html_url', url)}\n"
    )

    context_parts.append("\n===== FILE COVERAGE METADATA =====")
    context_parts.append(f"Total repository files: {total_files}")
    context_parts.append(f"Total useful code/config files: {useful_files_count}")
    context_parts.append(f"Retrieved files: {retrieved_files_count}")
    context_parts.append(f"Coverage: {coverage_percent}%")
    
    if missing_requested_paths:
        context_parts.append(f"\nREQUESTED FILES NOT FOUND:")
        for p in missing_requested_paths: context_parts.append(f" - {p}")

    context_parts.append(f"\nRETRIEVED FILES:")
    for file_obj in selected_files:
        if file_obj.get("path") in retrieved_set:
            trunc_mark = " [TRUNCATED]" if file_obj.get("truncated") else ""
            context_parts.append(f" - {file_obj['path']} ({file_obj['category']}){trunc_mark}")

    if important_missing:
        context_parts.append(f"\nIMPORTANT FILES NOT RETRIEVED:")
        for p in important_missing[:20]: context_parts.append(f" - {p}")

    context_parts.append("\n===== SELECTED FILE CONTENT =====")
    for g in analysis_groups:
        context_parts.append(g["content"])

    context = "\n".join(context_parts)
    context_truncated = False

    max_context_chars = 40000
    if len(context) > max_context_chars:
        context = context[:max_context_chars] + "\n\n[REPOSITORY CONTEXT TRUNCATED FOR LLM ANALYSIS]"
        context_truncated = True

    return {
        "repository": {
            "owner": owner,
            "name": repo,
            "full_name": repo_data.get("full_name", f"{owner}/{repo}"),
            "branch": branch,
            "description": repo_data.get("description"),
            "language": repo_data.get("language"),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "open_issues": repo_data.get("open_issues_count", 0),
            "license": ((repo_data.get("license") or {}).get("spdx_id")),
            "archived": repo_data.get("archived", False),
            "url": repo_data.get("html_url", url),
        },
        "tree": tree,
        "selected_files": selected_files,
        "context": context,
        "analysis_groups": analysis_groups,
        "analysis_batches": analysis_groups,
        "analysis_metadata": {
            "total_files": total_files,
            "useful_files": useful_files_count,
            "retrieved_files": retrieved_files_count,
            "coverage_percent": coverage_percent,
            "analysis_groups": len(analysis_groups),
            "truncated_files": truncated_files_count,
            "important_files_not_retrieved": important_missing,
            "not_retrieved_paths": not_retrieved_paths,
            "context_truncated": context_truncated
        }
    }


def _limit_group_content(content, max_chars=5000):
    """
    Limits the supplied source code content for a group to max_chars (default 5000),
    preserving the beginning of each file and clearly marking truncation.
    """
    if not content:
        return content, False
    
    original_len = len(content)
    if original_len <= max_chars:
        return content, False

    truncated_content = content[:max_chars] + "\n\n[TRUNCATED: remaining source omitted because of token budget]"
    return truncated_content, True


# ============================================================
# PUBLIC GITHUB CODE FUNCTION
# ============================================================

def analyze_github_repository_code(
    url,
    requested_files=None,
    query=None,
):
    """
    Read-only repository analysis primitive.
    """
    return github_repository_code_context(
        url,
        requested_files=requested_files,
        query=query,
    )


# ============================================================
# SEVERITY & FINDING VALIDATION LAYER (P0-P3 STRICT SCHEMA)
# ============================================================

def normalize_severity(severity):
    """
    Normalizes or validates finding severity. P4 is strictly prohibited.
    Returns a valid severity (P0, P1, P2, P3) or None if invalid/P4.
    """
    if not severity:
        return "P3"
    sev_str = str(severity).strip().upper()
    if sev_str in ("P0", "CRITICAL", "BLOCKER"):
        return "P0"
    if sev_str in ("P1", "HIGH", "MAJOR"):
        return "P1"
    if sev_str in ("P2", "MEDIUM", "MODERATE"):
        return "P2"
    if sev_str in ("P3", "LOW", "MINOR"):
        return "P3"
    if sev_str in ("P4", "TRIVIAL", "INFO"):
        return None
    return "P3"


def validate_finding(finding, selected_files):
    """
    Validates a finding against retrieved repository files and enforces strict P0-P3 severity,
    confidence (VERIFIED/INFERRED), and required evidentiary fields.
    """
    if not isinstance(finding, dict):
        return None

    raw_sev = finding.get("severity", "P3")
    severity = normalize_severity(raw_sev)
    if severity is None:
        return None
    finding["severity"] = severity

    confidence = finding.get("confidence", "NOT_VERIFIED")
    if confidence not in ("VERIFIED", "INFERRED"):
        confidence = "INFERRED"
    finding["confidence"] = confidence

    file_path = finding.get("file", "")
    evidence = finding.get("evidence", "")
    
    target_file = None
    for sf in selected_files:
        if sf.get("path") == file_path or sf.get("path").endswith(file_path):
            target_file = sf
            break
            
    file_verified = target_file is not None
    if not file_verified or file_path in ("", "NOT VERIFIED", "None", None):
        finding["confidence"] = "NOT_VERIFIED"
        finding["file"] = "NOT VERIFIED"
        return None

    raw_content = target_file.get("raw_content", target_file.get("content", ""))
    evidence_clean = str(evidence).strip()
    
    evidence_verified = False
    if evidence_clean and evidence_clean not in ("Evidence not available", "N/A", ""):
        if evidence_clean in raw_content or any(line.strip() in raw_content for line in evidence_clean.split('\n') if len(line.strip()) > 5):
            evidence_verified = True

    if not evidence_verified:
        finding["confidence"] = "INFERRED"

    lines = raw_content.splitlines()
    total_lines = len(lines)
    try:
        line_start = int(finding.get("line_start", 1))
        line_end = int(finding.get("line_end", line_start))
    except (TypeError, ValueError):
        return None

    if not (1 <= line_start <= line_end <= max(1, total_lines)):
        return None

    finding["line_start"] = line_start
    finding["line_end"] = line_end

    return finding


def validate_positive_finding(pos_finding, selected_files):
    """
    Validates positive findings requiring specific evidence and file path.
    """
    if not isinstance(pos_finding, dict):
        return None
    file_path = pos_finding.get("file", "")
    evidence = pos_finding.get("evidence", "")
    if not file_path or not evidence or evidence in ("N/A", ""):
        return None
    
    target_file = None
    for sf in selected_files:
        if sf.get("path") == file_path or sf.get("path").endswith(file_path):
            target_file = sf
            break
    if not target_file:
        return None
    return pos_finding


# ============================================================
# CODE FIX GENERATION & UNIFIED DIFF PATCH SYSTEM
# ============================================================

def generate_code_fix(repository_context, finding, api_key=None, test_mode=False):
    """
    Generates a minimal patch and unified diff for a validated finding using the repository context.
    Strictly validates file existence, line ranges, and evidence matching.
    """
    if not isinstance(finding, dict):
        return {"status": "error", "error": "Finding must be a dictionary."}

    file_path = finding.get("file") or finding.get("path")
    if not file_path or file_path in ("NOT VERIFIED", "", None):
        return {"status": "error", "error": "Invalid or unverified file path in finding."}

    file_content = None
    selected_files = []
    if isinstance(repository_context, dict):
        selected_files = repository_context.get("selected_files", [])
        for sf in selected_files:
            if sf.get("path") == file_path or sf.get("path").endswith(file_path):
                file_content = sf.get("raw_content", sf.get("content", ""))
                break
        if file_content is None and file_path in repository_context:
            file_content = repository_context[file_path]

    if file_content is None:
        return {"status": "error", "error": f"File '{file_path}' does not exist in repository context."}

    lines = file_content.splitlines()
    total_lines = len(lines)

    line_start = finding.get("line_start", 1)
    line_end = finding.get("line_end", line_start)

    try:
        line_start = int(line_start)
        line_end = int(line_end)
    except (TypeError, ValueError):
        return {"status": "insufficient_evidence", "error": "Invalid line_start or line_end format."}

    if not (1 <= line_start <= line_end <= max(1, total_lines)):
        return {"status": "insufficient_evidence", "error": f"Invalid line range: {line_start}-{line_end} for file with {total_lines} lines."}

    target_lines = lines[line_start - 1:line_end]
    original_code = "\n".join(target_lines)

    evidence = finding.get("evidence", "")
    if evidence and evidence not in ("Evidence not available", "N/A", ""):
        evidence_clean = str(evidence).strip()
        if evidence_clean and evidence_clean not in original_code and not any(l.strip() in original_code for l in evidence_clean.splitlines() if len(l.strip()) > 3):
            return {"status": "insufficient_evidence", "error": "Evidence does not match the specified line range in current file version."}

    if test_mode:
        proposed_code = original_code + "\n# Minimal fix applied"
    else:
        try:
            client = OpenAI(api_key=api_key or os.getenv("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1")
            model = os.getenv("OPENROUTER_MODEL", "openrouter/free")
            prompt = f"Generate a minimal code fix patch for file {file_path} between lines {line_start} and {line_end}.\nProblem: {finding.get('problem')}\nRecommendation: {finding.get('recommendation')}\nOriginal Code:\n{original_code}"
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "You are a precise code fixer. Return JSON with 'original_code', 'proposed_code', and 'explanation'."},
                          {"role": "user", "content": prompt}],
                max_tokens=DEVELOPER_MAX_TOKENS
            )
            content = response.choices[0].message.content
            parsed = json.loads(re.search(r'\{.*\}', content, re.DOTALL).group(0))
            proposed_code = parsed.get("proposed_code", original_code)
            explanation = parsed.get("explanation", "AI generated minimal patch.")
        except Exception as exc:
            return {"status": "error", "error": f"LLM fix generation failed: {exc}"}

    if test_mode:
        explanation = "Deterministic test mode patch generated successfully."

    diff_lines = list(difflib.unified_diff(
        original_code.splitlines(),
        proposed_code.splitlines(),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=""
    ))
    patch_str = "\n".join(diff_lines)

    return {
        "status": "success",
        "file": file_path,
        "line_start": line_start,
        "line_end": line_end,
        "original_code": original_code,
        "proposed_code": proposed_code,
        "patch": patch_str,
        "explanation": explanation,
        "minimal_change": True
    }


def generate_fix_for_finding(repository_url, finding, api_key=None, test_mode=False):
    """
    Retrieves repository context using existing mechanisms and generates a safe minimal code fix and diff.
    """
    try:
        if isinstance(repository_url, str) and "github.com" in repository_url:
            repo_context = analyze_github_repository_code(repository_url)
        elif isinstance(repository_url, dict):
            repo_context = repository_url
        else:
            repo_context = {}
    except Exception as exc:
        return {"status": "error", "error": f"Failed to retrieve repository context: {exc}"}

    return generate_code_fix(repo_context, finding, api_key=api_key, test_mode=test_mode)


# ============================================================
# FINAL REPORT AGGREGATION
# ============================================================

def build_final_report(group_results, repository_metadata=None):
    """
    Aggregates individual group analysis results into a final consolidated report,
    ensuring only valid P0-P3 severities and validated findings appear.
    Calculates final status correctly based on multi-group failures.
    """
    all_findings = []
    all_positive_findings = []
    all_gaps = []
    total_findings = 0
    failed_count = 0
    total_groups = len(group_results) if group_results else 0
    
    if isinstance(group_results, list):
        for grp in group_results:
            if grp.get("status") == "error":
                failed_count += 1
                for g in grp.get("gaps", []):
                    all_gaps.append(g)
                if grp.get("error"):
                    all_gaps.append(grp.get("error"))
                continue
            
            for f in grp.get("findings", []):
                sev = normalize_severity(f.get("severity"))
                if sev is not None:
                    f["severity"] = sev
                    all_findings.append(f)
                    total_findings += 1
                else:
                    all_gaps.append(f"Rejected finding due to invalid severity (P4/unknown): {f.get('title', '')}")

            for pf in grp.get("positive_findings", []):
                all_positive_findings.append(pf)

            for g in grp.get("gaps", []):
                all_gaps.append(g)

    if total_groups == 0:
        status = "error"
    elif failed_count == 0:
        status = "success"
    elif failed_count == total_groups:
        status = "error"
    else:
        status = "partial"

    return {
        "status": status,
        "total_findings": total_findings,
        "findings": all_findings,
        "positive_findings": all_positive_findings,
        "gaps": all_gaps,
        "group_results": group_results,
        "repository_metadata": repository_metadata or {}
    }


# ============================================================
# LLM HELPERS & SAFE WRAPPER
# ============================================================

def _call_llm_with_retry(client, model, system_prompt, user_prompt, max_retries=3, test_mode=False, group_name="Group", max_tokens=None):
    if max_tokens is None:
        max_tokens = DEVELOPER_MAX_TOKENS

    if test_mode:
        return json.dumps({
            "category": group_name,
            "findings": [{
                "category": "SECURITY",
                "title": f"Mock Finding for {group_name}",
                "severity": "P3",
                "confidence": "VERIFIED",
                "file": "README.md",
                "line_start": 1,
                "line_end": 1,
                "evidence": "Mock evidence for test mode pipeline",
                "problem": "Mock problem description",
                "impact": "Mock impact assessment",
                "recommendation": "Mock fix recommendation",
                "finding_type": "vulnerability"
            }],
            "positive_findings": [{
                "file": "README.md",
                "line_start": 1,
                "line_end": 1,
                "evidence": "Mock positive evidence",
                "explanation": "Well structured documentation"
            }],
            "gaps": ["Runtime execution environment not supplied"]
        }), None

    attempt = 0
    current_max_tokens = max_tokens
    
    while attempt < max_retries:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=current_max_tokens,
                timeout=LLM_REQUEST_TIMEOUT
            )
            return response.choices[0].message.content, None
        except Exception as exc:
            error_msg = str(exc)
            
            # Non-retryable error check for HTTP 402 / 403 / insufficient credits / budget exhausted
            if "402" in error_msg or "403" in error_msg or "in_flight_budget_exhausted" in error_msg or "insufficient" in error_msg.lower() or "budget" in error_msg.lower():
                print(f"[DeveloperAgent ERROR] OpenRouter budget exhausted or non-retryable limit error; skipping retries. Details: {error_msg}")
                return None, "FATAL_LIMIT_ERROR: OpenRouter credits/token budget are insufficient. Reduce prompt size/max_tokens, use a cheaper model, or add credits."
            
            if "401" in error_msg:
                return None, f"OpenRouter API error 401 (Unauthorized): Invalid API key."

            if "429" in error_msg or "502" in error_msg or "503" in error_msg or "500" in error_msg or "timeout" in error_msg.lower():
                attempt += 1
                if attempt >= max_retries:
                    return None, error_msg
                wait_time = min(15 * (2 ** (attempt - 1)), 60)
                time.sleep(wait_time)
            else:
                return None, error_msg
                
    return None, "Max retries exceeded."


# ============================================================
# DEVELOPER AGENT
# ============================================================

def developer_agent(
    query,
    context=None,
    api_key=None,
    test_mode=False,
    max_groups=None,
    start_group=1,
):
    start_time = time.time()
    env_test_mode = os.getenv("LLM_TEST_MODE", "false").lower() in ("true", "1", "yes")
    is_test_mode = test_mode or env_test_mode

    if not api_key and not is_test_mode:
        api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key and not is_test_mode:
        return {
            "agent": "developer_agent",
            "status": "error",
            "error": "OPENROUTER_API_KEY is not configured.",
            "answer": "Developer Agent could not start because OPENROUTER_API_KEY is not configured.",
            "tool_calls": 0,
            "mcp_calls": 0,
            "execution_time": round(time.time() - start_time, 3),
        }

    github_context = None
    repository_code_context = None
    is_repo_analysis = False

    target_type, owner, repo = _extract_github_target(query)
    clean_repo_url = _extract_github_repo_url(query)

    if target_type == "repo" and clean_repo_url and any(
        word in str(query).lower() for word in [
            "analyze", "analyse", "code", "architecture", "structure",
            "implementation", "review", "repository", "repo", "security",
            "test", "performance", "problem", "flow", "explain", "find", 
            "what", "intelligence", "roadmap", "inspect"
        ]
    ):
        is_repo_analysis = True
        try:
            requested_files = _extract_requested_files(query)
            repository_code_context = analyze_github_repository_code(
                clean_repo_url,
                requested_files=requested_files if requested_files else None,
                query=query
            )
        except Exception as exc:
            return {
                "agent": "developer_agent",
                "status": "error",
                "error": str(exc),
                "answer": f"GitHub repository analysis failed: {exc}",
                "tool_calls": 0,
                "mcp_calls": 0,
                "execution_time": round(time.time() - start_time, 3),
            }

    client = None
    if not is_test_mode:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    model = os.getenv("OPENROUTER_MODEL", "openrouter/free")

    if is_repo_analysis and repository_code_context and repository_code_context.get("analysis_groups"):
        groups = repository_code_context["analysis_groups"]
        metadata = repository_code_context["analysis_metadata"]
        repo_data = repository_code_context["repository"]
        selected_files = repository_code_context.get("selected_files", [])
        
        if start_group < 1:
            return {"status": "error", "error": "start_group must be >= 1"}

        start_idx = max(0, start_group - 1)
        if start_idx >= len(groups):
            return {"status": "error", "error": f"start_group out of range. Total: {len(groups)}"}

        end_idx = (start_idx + max_groups) if max_groups is not None else len(groups)
        groups_to_process = groups[start_idx:end_idx]
        
        analysis_results = []
        failed_groups_count = 0
        llm_limit_hit = False
        fatal_error_msg = None
        consecutive_empty = 0

        group_system_prompt = (
            "You are an expert Repository Intelligence Code Reviewer. "
            "Analyze the supplied files, source code, and configuration within this group. "
            "Identify real code issues, security vulnerabilities, architectural flaws, bugs, or performance bottlenecks. "
            "STRICT RULES:\n"
            "1. ONLY allowed severities are P0, P1, P2, P3. NEVER generate P4.\n"
            "2. Confidence must be VERIFIED or INFERRED based strictly on supplied evidence.\n"
            "3. Never invent files, code, vulnerabilities, or behavior.\n"
            "4. If evidence is insufficient, do not create a finding; place the issue in gaps instead.\n"
            "5. Analysis is limited strictly to the supplied content below.\n"
            "Return strict JSON matching the exact schema:\n"
            "{\n"
            "  \"category\": \"...\",\n"
            "  \"findings\": [\n"
            "    {\n"
            "      \"category\": \"SECURITY|PERFORMANCE|ARCHITECTURE|BUG|MAINTAINABILITY\",\n"
            "      \"title\": \"...\",\n"
            "      \"severity\": \"P0|P1|P2|P3\",\n"
            "      \"confidence\": \"VERIFIED|INFERRED\",\n"
            "      \"file\": \"...\",\n"
            "      \"line_start\": 1,\n"
            "      \"line_end\": 1,\n"
            "      \"evidence\": \"...\",\n"
            "      \"problem\": \"...\",\n"
            "      \"impact\": \"...\",\n"
            "      \"recommendation\": \"...\",\n"
            "      \"finding_type\": \"vulnerability|antipattern|bug|gap\"\n"
            "    }\n"
            "  ],\n"
            "  \"positive_findings\": [\n"
            "    {\n"
            "      \"file\": \"...\",\n"
            "      \"line_start\": 1,\n"
            "      \"line_end\": 1,\n"
            "      \"evidence\": \"...\",\n"
            "      \"explanation\": \"...\"\n"
            "    }\n"
            "  ],\n"
            "  \"gaps\": []\n"
            "}"
        )

        for i, group in enumerate(groups_to_process):
            g_id = group.get("group_id", start_idx + i + 1)
            g_cat = group.get("category", "Unknown")
            g_files = group.get("files", [])
            
            raw_content = group.get("content", "")
            original_len = len(raw_content)
            limited_content, is_truncated = _limit_group_content(raw_content, max_chars=MAX_GROUP_CHARS)
            
            group_user_prompt = f"GROUP ID: {g_id}\nCATEGORY: {g_cat}\nFILES: {', '.join(g_files)}\n\nSUPPLIED REPOSITORY CONTENT:\n{limited_content}"
            
            print(
                f"[DeveloperAgent DEBUG]\n"
                f"Total Groups: {len(groups)}\n"
                f"Selected Groups: {len(groups_to_process)}\n"
                f"Current Group: {i+1}/{len(groups_to_process)}\n"
                f"Max Tokens: {DEVELOPER_MAX_TOKENS}\n"
                f"Original Chars: {original_len}\n"
                f"Sent Chars: {len(group_user_prompt)}\n"
                f"Truncated: {is_truncated}"
            )

            resp_text, err = _call_llm_with_retry(
                client, model, group_system_prompt, group_user_prompt, 
                test_mode=is_test_mode, group_name=g_cat, max_tokens=DEVELOPER_MAX_TOKENS
            )
            
            if err:
                print(f"[DeveloperAgent DEBUG] Group {g_id} FAILED: {err}")
                analysis_results.append({
                    "group_id": g_id, 
                    "category": g_cat, 
                    "findings": [], 
                    "positive_findings": [],
                    "gaps": [f"Group analysis unavailable because OpenRouter token/credit budget was insufficient. ({err})"], 
                    "status": "error",
                    "error": err
                })
                failed_groups_count += 1
                if "FATAL_LIMIT_ERROR" in err or "403" in err or "insufficient" in err.lower():
                    llm_limit_hit = True
                    fatal_error_msg = err
                    break  # Stop processing further groups immediately
            else:
                print(f"[DeveloperAgent DEBUG] Group {g_id} SUCCEEDED.")
                try:
                    parsed = json.loads(re.search(r'\{.*\}', resp_text, re.DOTALL).group(0))
                except Exception:
                    parsed = {"findings": [], "positive_findings": [], "gaps": []}
                
                validated_findings = []
                for f in parsed.get("findings", []):
                    vf = validate_finding(f, selected_files)
                    if vf:
                        validated_findings.append(vf)

                validated_pos = []
                for pf in parsed.get("positive_findings", []):
                    vpf = validate_positive_finding(pf, selected_files)
                    if vpf:
                        validated_pos.append(vpf)

                analysis_results.append({
                    "group_id": g_id,
                    "category": g_cat,
                    "findings": validated_findings,
                    "positive_findings": validated_pos,
                    "gaps": parsed.get("gaps", []),
                    "status": "success"
                })

                # Check for consecutive empty responses to determine optional early stop
                if not validated_findings and not validated_pos and not parsed.get("gaps", []):
                    consecutive_empty += 1
                else:
                    consecutive_empty = 0
                
                if consecutive_empty >= 3:
                    print("[DeveloperAgent DEBUG] Stopping early due to 3 consecutive empty group results.")
                    break

        report = build_final_report(analysis_results, repository_metadata=repo_data)

        return {
            "agent": "developer_agent",
            "status": report.get("status", "error"),
            "error": fatal_error_msg,
            "completed_groups": len(analysis_results) - failed_groups_count,
            "failed_groups": failed_groups_count,
            "group_results": analysis_results,
            "final_report": report,
            "answer": json.dumps(report, indent=2)
        }

    return {
    "agent": "developer_agent",
    "status": "error",
    "error": "Developer analysis did not produce a final report.",
    "completed_groups": 0,
    "failed_groups": 0,
    "group_results": [],
    "answer": "Developer analysis did not produce a final report."
}


# ============================================================
# GITHUB USER REPOSITORIES WORKFLOW (NEW FEATURE)
# ============================================================

def get_github_user_repositories(github_user_url):
    """
    Fetch all public repositories for a given GitHub user profile URL or username.
    Returns structured repository data tailored for frontend repository cards.
    """
    q = str(github_user_url).strip()
    
    if "github.com/" in q:
        match = re.search(r"github\.com/([A-Za-z0-9_.-]+)", q, flags=re.IGNORECASE)
        if not match:
            raise ValueError(f"Invalid GitHub user URL: {github_user_url}")
        username = match.group(1)
    else:
        username = q

    username = re.sub(r"[\.,;:'\"\)\]>]+$", "", username)
    
    ignored_usernames = {
        "login", "signup", "settings", "features", "pricing", 
        "explore", "marketplace", "topics", "collections", "trending"
    }
    if not username or username.lower() in ignored_usernames:
        raise ValueError(f"Invalid or reserved GitHub username: {username}")

    all_repos = []
    page = 1
    per_page = 100

    while True:
        data, error = _github_get(
            f"/users/{username}/repos",
            params={"type": "owner", "sort": "updated", "per_page": per_page, "page": page}
        )
        if error:
            if page == 1:
                if "404" in error:
                    raise RuntimeError(f"GitHub user '{username}' not found.")
                raise RuntimeError(f"Could not fetch repositories for user '{username}': {error}")
            break
        
        if not isinstance(data, list) or not data:
            break

        for repo in data:
            all_repos.append({
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description"),
                "html_url": repo.get("html_url"),
                "clone_url": repo.get("clone_url"),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "open_issues": repo.get("open_issues_count", 0),
                "updated_at": repo.get("updated_at"),
                "created_at": repo.get("created_at"),
                "default_branch": repo.get("default_branch", "main"),
                "private": repo.get("private", False),
                "archived": repo.get("archived", False),
            })

        if len(data) < per_page:
            break
        page += 1

    return {
        "status": "success",
        "username": username,
        "repositories": all_repos
    }