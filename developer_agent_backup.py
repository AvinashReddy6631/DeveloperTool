import os
import re
import time
import base64

from dotenv import load_dotenv
from openai import OpenAI
import httpx


load_dotenv()


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
        r"github\.com/([^/\s]+)/([^/\s#?\]\)]+)",
        q,
        flags=re.IGNORECASE,
    )

    if repo_match:
        owner = repo_match.group(1)
        repo = re.sub(r"\.git$", "", repo_match.group(2))

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
        r"github\.com/([^/\s?#]+)",
        q,
        flags=re.IGNORECASE,
    )

    if user_match:
        username = user_match.group(1)

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
            return None, "GitHub returned HTTP 404. The resource may not exist or may not be publicly accessible."

        if response.status_code == 401:
            return None, "GitHub authentication failed."

        if response.status_code == 403:
            return None, "GitHub API access was denied or rate-limited."

        return (
            None,
            f"GitHub API returned HTTP {response.status_code}.",
        )

    except Exception as exc:
        return None, f"GitHub request failed: {exc}"


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
    """

    lower = path.lower()

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

    filename = lower.split("/")[-1]

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


def _score_code_file(path):
    """
    Score files so important project files are selected first.
    """

    lower = path.lower()
    score = 0

    filename = lower.split("/")[-1]

    important_names = {
        "readme.md": 100,
        "package.json": 95,
        "pyproject.toml": 95,
        "requirements.txt": 90,
        "dockerfile": 90,
        "docker-compose.yml": 85,
        "docker-compose.yaml": 85,
        "main.py": 80,
        "app.py": 80,
        "server.py": 80,
        "index.py": 75,
        "index.js": 75,
        "index.ts": 75,
        "main.js": 75,
        "main.ts": 75,
    }

    score += important_names.get(
        filename,
        0,
    )

    if "src/" in lower:
        score += 30

    if "app/" in lower:
        score += 25

    if "server" in lower:
        score += 20

    if "api" in lower:
        score += 15

    if "agent" in lower:
        score += 15

    if "test" in lower:
        score += 5

    if lower.endswith(
        (
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".java",
            ".go",
            ".rs",
        )
    ):
        score += 10

    # Prefer shorter paths slightly.
    score -= lower.count("/") * 2

    return score


def github_repository_code_context(
    url,
    requested_files=None,
):
    """
    Read-only repository analysis primitive.

    Returns:
        repository metadata
        complete repository tree
        selected source/configuration files
    """

    target_type, owner, repo = _extract_github_target(
        url
    )

    if target_type != "repo":
        raise ValueError(
            "Expected a GitHub repository URL."
        )

    repo_data, error = _github_get(
        f"/repos/{owner}/{repo}"
    )

    if error:
        raise RuntimeError(error)

    if not repo_data:
        raise RuntimeError(
            "GitHub repository was not found."
        )

    branch = (
        repo_data.get("default_branch")
        or "main"
    )

    tree, tree_error = _github_get_tree(
        owner,
        repo,
        branch,
    )

    if tree_error:
        raise RuntimeError(tree_error)

    files = [
        item
        for item in tree
        if item.get("type") == "blob"
        and _is_useful_code_file(
            item.get("path", "")
        )
    ]

    # --------------------------------------------------------
    # Determine files to fetch
    # --------------------------------------------------------

    selected_paths = []

    if requested_files:

        for requested in requested_files:

            for item in files:

                if item.get("path") == requested:
                    selected_paths.append(
                        item.get("path")
                    )
                    break

    else:

        ranked = sorted(
            files,
            key=lambda item: _score_code_file(
                item.get("path", "")
            ),
            reverse=True,
        )

        # Keep analysis bounded.
        selected_paths = [
            item.get("path")
            for item in ranked[:15]
        ]

    selected_files = []

    for path in selected_paths:

        content, file_error = _github_get_file(
            owner,
            repo,
            path,
            branch,
        )

        if file_error:
            selected_files.append(
                {
                    "path": path,
                    "content": "",
                    "error": file_error,
                }
            )
            continue

        # Avoid sending massive files to the LLM.
        max_chars = 30000

        if len(content) > max_chars:
            content = (
                content[:max_chars]
                + "\n\n"
                "[FILE TRUNCATED FOR ANALYSIS]"
            )

        selected_files.append(
            {
                "path": path,
                "content": content,
            }
        )

    return {
        "repository": {
            "owner": owner,
            "name": repo,
            "full_name": repo_data.get(
                "full_name",
                f"{owner}/{repo}",
            ),
            "branch": branch,
            "description": repo_data.get(
                "description"
            ),
            "language": repo_data.get(
                "language"
            ),
            "stars": repo_data.get(
                "stargazers_count",
                0,
            ),
            "forks": repo_data.get(
                "forks_count",
                0,
            ),
            "open_issues": repo_data.get(
                "open_issues_count",
                0,
            ),
            "url": repo_data.get(
                "html_url",
                url,
            ),
        },
        "tree": tree,
        "selected_files": selected_files,
    }


# ============================================================
# PUBLIC GITHUB CODE FUNCTION
# ============================================================

def analyze_github_repository_code(
    url,
    requested_files=None,
):
    """
    Read-only DevGitHub analysis primitive.

    Returns repository structure and selected
    source/configuration files.

    The existing developer_agent() can use this
    function for richer repository questions.
    """

    return github_repository_code_context(
        url,
        requested_files=requested_files,
    )


# ============================================================
# DEVELOPER AGENT
# ============================================================

def developer_agent(
    query,
    context=None,
    api_key=None,
):
    """
    Developer / DevGitHub Agent.

    Responsibilities:
    - Answer programming questions.
    - Explain errors and provide fixes.
    - Analyze public GitHub repositories and profiles.
    - Analyze repository source code.
    - Use GitHub API context when a GitHub URL is present.
    - Support private GitHub repositories when GITHUB_TOKEN is configured.
    - Never expose credentials.
    - Never expose raw model tool-call markup.
    - Never return safety classifications.

    This function intentionally remains synchronous
    so the existing orchestrator architecture
    does not need to change.
    """

    start_time = time.time()

    if not api_key:
        api_key = os.getenv(
            "OPENROUTER_API_KEY"
        )

    if not api_key:
        return {
            "agent": "developer_agent",
            "status": "error",
            "error": "OPENROUTER_API_KEY is not configured.",
            "answer": (
                "Developer Agent could not start because "
                "OPENROUTER_API_KEY is not configured."
            ),
            "tool_calls": 0,
            "mcp_calls": 0,
            "execution_time": round(
                time.time() - start_time,
                3,
            ),
        }

    github_context = None
    repository_code_context = None

    query_text = str(query)
    query_lower = query_text.lower()

    is_github_query = "github.com" in query_lower

    github_repo_intent = is_github_query and any(
        word in query_lower
        for word in [
            "analyze",
            "analyse",
            "code",
            "architecture",
            "structure",
            "implementation",
            "review",
            "repository",
            "repo",
            "source",
            "files",
        ]
    )

    # ========================================================
    # GITHUB REPOSITORY SOURCE CODE CONTEXT
    # ========================================================
    #
    # IMPORTANT:
    # For repository analysis, retrieve the repository tree/files
    # FIRST. The previous implementation called the general GitHub
    # context helper first, which made several extra GitHub API
    # requests (repo + languages + commits + pull requests).
    #
    # That could consume the unauthenticated GitHub API quota before
    # the actual source-code request was made.
    #
    # Repository analysis now uses ONE primary source retrieval path:
    #
    #   Query -> repository metadata/tree/files -> LLM
    #
    # This keeps the existing architecture but avoids duplicate
    # GitHub API calls.
    # ========================================================

    if github_repo_intent:

        try:

            target_type, owner, repo = (
                _extract_github_target(query)
            )

            if target_type == "repo":

                code_data = (
                    analyze_github_repository_code(
                        query
                    )
                )

                repository_code_context = code_data

                # The repository-code response already contains
                # repository metadata. Do not make another set of
                # GitHub API requests just to rebuild the same context.
                repository = (
                    code_data.get("repository", {})
                    if isinstance(code_data, dict)
                    else {}
                )

                if repository:
                    github_context = (
                        "GitHub Repository Metadata\n"
                        "-------------------------\n"
                        f"Repository: {repository.get('full_name', 'unknown')}\n"
                        f"Description: {repository.get('description') or 'No description provided.'}\n"
                        f"Default branch: {repository.get('branch', 'unknown')}\n"
                        f"Primary language: {repository.get('language') or 'unknown'}\n"
                        f"Stars: {repository.get('stars', 0)}\n"
                        f"Forks: {repository.get('forks', 0)}\n"
                        f"Open issues: {repository.get('open_issues', 0)}\n"
                        f"URL: {repository.get('url', query)}"
                    )

        except Exception as exc:

            repository_code_context = {
                "error": str(exc),
                "repository": {},
                "tree": [],
                "selected_files": [],
            }

            github_context = (
                "GitHub repository source retrieval failed. "
                "Do not invent repository facts. "
                f"Retrieval error: {exc}"
            )

    # ========================================================
    # GENERAL GITHUB CONTEXT
    # ========================================================
    #
    # Keep the existing profile/general GitHub behavior.
    # For repository-analysis queries we intentionally skip this
    # because the repository-code path above already retrieved the
    # important metadata and source files.
    # ========================================================

    elif is_github_query:

        try:

            github_context = _get_github_context(
                query
            )

        except Exception as exc:

            github_context = (
                f"GitHub context unavailable: {exc}"
            )

    # ========================================================
    # BUILD SYSTEM CONTEXT
    # ========================================================

    system_prompt = """
You are DevGitHub AI, a senior software engineer
and GitHub repository analysis assistant.

Your responsibilities:

1. Answer software engineering questions.
2. Debug Python, JavaScript, TypeScript,
   React, Node.js, FastAPI, MCP and related systems.
3. Analyze GitHub profiles.
4. Analyze GitHub repositories.
5. When repository source code is provided,
   reason about the actual source code instead
   of inventing implementation details.
6. Identify architecture, technologies,
   important files, strengths and weaknesses.
7. Give practical improvements.
8. Never invent repository facts.
9. Clearly distinguish observed facts from
   reasonable inferences.
10. Never reveal API keys, tokens or credentials.
11. When ACTUAL REPOSITORY SOURCE CONTEXT is present, use it as the
    primary source for repository analysis.
12. Do not claim that GitHub is inaccessible if repository files are
    present in ACTUAL REPOSITORY SOURCE CONTEXT.
13. Do not invent files, dependencies, architecture, metrics, or code
    behavior that are not supported by the supplied repository data.
14. If some GitHub metadata is unavailable but source files are
    available, analyze the available source files instead of refusing
    the entire request.
15. When a file is truncated, explicitly treat conclusions from the
    missing portion as uncertain.
16. For security findings, report ONLY issues supported by the supplied
    repository context. Do not invent vulnerabilities.
17. Clearly label security findings as VERIFIED, POTENTIAL, or NOT VERIFIED.
18. For every VERIFIED or POTENTIAL security finding, name the file and
    explain the relevant code/configuration evidence when available.
19. Never reproduce secrets, tokens, passwords, private keys, or other
    sensitive values found in repository context. Redact them.
20. Do not call a repository secure or insecure based only on its README.
    Inspect the supplied source/configuration files first.

For GitHub repository analysis, structure the
answer using:

- Repository Overview
- Architecture
- Technology Stack
- Important Files
- Code / Implementation Analysis
- Security Analysis
- Testing Analysis
- Strengths
- Problems / Risks
- Recommended Improvements
- Overall Assessment

For the Security Analysis section, check the supplied context for:
- hardcoded secrets, credentials, API keys, and unsafe environment handling
- authentication and authorization gaps
- SQL injection and unsafe database query construction
- command/subprocess execution risks
- unsafe file/path handling
- CORS and exposed API configuration
- insecure Docker/container configuration
- dependency/configuration risks visible in supplied files
- sensitive data exposure in logs, responses, or frontend code
- unsafe debug/development settings

Use this format where applicable:

Security Analysis
- VERIFIED: [severity] [finding] — file: path — evidence: ...
- POTENTIAL: [severity] [finding] — file: path — evidence: ...
- NOT VERIFIED: [area] — explain what was not available in the supplied context.

Do not manufacture a vulnerability merely because a security best practice
is absent from the visible context. Absence of evidence is not proof of a
vulnerability.

For Testing Analysis, distinguish between tests actually visible in the
supplied context and tests merely mentioned by documentation. Never claim
a test count or passing status unless it is supported by the supplied files.

Be concise but technically useful.
"""

    # ========================================================
    # USER CONTEXT
    # ========================================================

    user_prompt = f"""
USER QUERY:
{query}
"""

    if context:
        user_prompt += f"""

ADDITIONAL CONTEXT:
{context}
"""

    if github_context:
        user_prompt += f"""

GITHUB API CONTEXT:
{github_context}
"""

    if repository_code_context:

        if isinstance(
            repository_code_context,
            dict,
        ):

            repository = (
                repository_code_context.get(
                    "repository",
                    {},
                )
            )

            tree = (
                repository_code_context.get(
                    "tree",
                    [],
                )
            )

            selected_files = (
                repository_code_context.get(
                    "selected_files",
                    [],
                )
            )

            user_prompt += """

ACTUAL REPOSITORY SOURCE CONTEXT
================================

Repository:
"""

            user_prompt += (
                f"{repository.get('full_name')}\n"
            )

            user_prompt += (
                f"Branch: "
                f"{repository.get('branch')}\n"
            )

            user_prompt += "\nRepository Tree:\n"

            for item in tree:

                path = item.get(
                    "path",
                    "",
                )

                if path:
                    user_prompt += (
                        f"- {path}\n"
                    )

            user_prompt += (
                "\nSelected Source Files:\n"
            )

            for item in selected_files:

                path = item.get(
                    "path",
                    "",
                )

                content = item.get(
                    "content",
                    "",
                )

                user_prompt += (
                    f"\n===== {path} =====\n"
                )

                user_prompt += content

                user_prompt += (
                    "\n===== END FILE =====\n"
                )

        else:

            user_prompt += f"""

REPOSITORY SOURCE CONTEXT:
{repository_code_context}
"""

    # ========================================================
    # OPENROUTER CLIENT
    # ========================================================

    try:

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        # Keep your existing OpenRouter architecture.
        model = os.getenv(
            "OPENROUTER_MODEL",
            "openrouter/free",
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        answer = (
            response.choices[0]
            .message
            .content
        )

        if not answer:
            answer = (
                "Developer Agent received an "
                "empty response from the model."
            )

        return {

            "agent": "developer_agent",
            "status": "success",
            "error": None,
            "answer": answer,
            "tool_calls": 0,
            "mcp_calls": 0,
            "execution_time": round(
                time.time() - start_time,
                3,
            ),
        }

    except Exception as exc:

        error_text = str(exc)

        return {

            "agent": "developer_agent",
            "status": "error",
            "error": error_text,
            "answer": (
                "Developer Agent failed while "
                "contacting OpenRouter.\n\n"
                f"Error: {error_text}"
            ),
            "tool_calls": 0,
            "mcp_calls": 0,
            "execution_time": round(
                time.time() - start_time,
                3,
            ),
        }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print(
        developer_agent(
            "What is MCP?"
        )
        .get("answer")
    )