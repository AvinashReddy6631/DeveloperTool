import time
import uuid

from fastapi import FastAPI, HTTPException, Request
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
# REQUEST MODEL
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
    request: QueryRequest
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
            session_id
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