@'
# MCP Agent Orchestrator

A production-oriented MCP (Model Context Protocol) Agent Orchestrator built with Python, FastAPI, PostgreSQL, Docker, and LLM-powered agents.

## Overview

The MCP Agent Orchestrator receives natural-language queries, determines the required agent, connects to MCP tools, retrieves data from PostgreSQL, and produces a structured response.

The current system supports:

- Salary analysis
- Company analysis
- Employee information
- Company roles
- Multi-agent orchestration
- Follow-up query routing
- MCP tool execution tracing
- Failure and timeout handling
- Request IDs and execution timing
- PostgreSQL-backed data
- Docker deployment
- Automated CI testing

## Architecture

```text
Client
  |
  v
FastAPI API
  |
  v
Orchestrator
  |
  +--------------------+
  |                    |
  v                    v
Salary Agent       Company Agent
  |                    |
  +---------+----------+
            |
            v
        MCP Server
            |
            v
       PostgreSQL


Technology Stack
Python 3.13
FastAPI
Uvicorn
PostgreSQL
psycopg2
Model Context Protocol (MCP)
OpenAI / OpenRouter-compatible LLM integration
Docker
Docker Compose
pytest
GitHub Actions




MCPOrchestrator/
|
├── api.py
├── orchestrator.py
├── harness.py
├── salary_agent.py
├── company_agent.py
├── database.py
├── postgres_database.py
├── requirements.txt
├── Dockerfile
├── compose.yaml
├── .dockerignore
├── .gitignore
├── README.md
|
├── tests/
│   ├── test_api.py
│   ├── test_company.py
│   ├── test_end_to_end.py
│   ├── test_failure_handling.py
│   ├── test_integration.py
│   ├── test_mcp_resilience.py
│   ├── test_orchestrator.py
│   └── test_salary.py
|
└── .github/
    └── workflows/
        └── ci.yml



API
Health Check
GET /health

Example:

{
  "status": "healthy",
  "service": "MCP Agent Orchestrator",
  "database": "connected"
}
Root Endpoint
GET /

Returns basic service information.

Query Endpoint
POST /query

Request:

{
  "query": "Who is the highest paid employee at Google?"
}

Example response:

{
  "request_id": "example-request-id",
  "status": "success",
  "answer": "The highest-paid employee at **Google** is **Priya**, earning **85000** as a **ML Engineer**.",
  "execution_time": 7.4,
  "error": null
}
Supported Query Examples
Who is the highest paid employee at Google?


Tell me about Google.


Show me employees working at Google.


What roles exist at Google?


Analyze Google and tell me who earns the most and what roles exist.


Give me a complete analysis of Tesla.

The system can return a meaningful "no information available" response when a company is not present in the database.

Database

The project uses PostgreSQL.

Database configuration is loaded from environment variables:

DB_HOST
DB_NAME
DB_USER
DB_PASSWORD
DB_PORT

API credentials are also supplied through environment variables.


Never commit .env or API keys to Git.

Database Seeding

The project contains postgres_database.py for initializing the employee table and inserting seed data.

The seed operation is idempotent: running the script repeatedly does not insert duplicate employee records.

Run:

python postgres_database.py
Docker

Build and start the application:

docker compose up -d --build

Check the container:

docker compose ps

Check health:

curl.exe http://localhost:8000/health

Stop the application:

docker compose down
Container Security

The application container runs as a non-root user.

The application filesystem is configured as read-only while temporary runtime writes can still use /tmp.

A Docker health check is also configured for the API.

Testing

Run the complete test suite:

python -m pytest -v tests

Current test status:

86 passed

The test suite covers:

API behavior
Company agent
Salary agent
End-to-end orchestration
Failure handling
MCP resilience
Integration
Routing
Follow-up queries
Validation
Timeout handling
MCP tool-call limits
Recovery after MCP failures
CI/CD

GitHub Actions runs automatically on pushes and pull requests targeting main.

The CI pipeline:

Checks out the repository
Installs Python 3.13
Installs dependencies
Runs the test suite
Builds the Docker image

Workflow:

.github/workflows/ci.yml
MCP Execution Trace

The orchestrator records MCP activity including:

Agent name
MCP tool name
Tool arguments
Execution status
Execution time
Number of MCP calls
Final execution status

This provides visibility into how a request was processed.

Failure Handling

The system includes protection against:

MCP tool failures
Invalid MCP responses
MCP timeouts
Agent timeouts
Agent iteration limits
MCP tool-call limits
Partial MCP data
Failed MCP calls
Database connectivity failures

The health endpoint reports database connectivity separately from API availability.

Development

Create and activate a virtual environment:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Run the API locally:

uvicorn api:app --host 0.0.0.0 --port 8000
Environment Variables

Create a .env file locally:

OPENROUTER_API_KEY=your_api_key


DB_HOST=your_database_host
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_PORT=5432

Do not commit real credentials.

Project Status

The current implementation has completed:

Core MCP orchestration
Salary agent
Company agent
PostgreSQL integration
API layer
Docker deployment
Container hardening
Automated testing
MCP resilience testing
CI pipeline
Idempotent database seeding
License

This project is currently intended as a personal/portfolio MCP orchestration project.
'@ | Set-Content README.md



Then verify that the file contains the documentation:


```powershell
Get-Content README.md | Select-Object -First 30