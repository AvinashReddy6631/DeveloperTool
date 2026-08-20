import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
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
# REQUEST MODEL
# ============================================================

class QueryRequest(BaseModel):

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User query for the MCP orchestrator."
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

    request_id = str(
        uuid.uuid4()
    )

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

    request_id = str(
        uuid.uuid4()
    )

    query = request.query.strip()

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

    print("=" * 60)

    try:

        # ----------------------------------------------------
        # ORCHESTRATOR
        # ----------------------------------------------------

        result = await orchestrate(
            query
        )

        # ----------------------------------------------------
        # EXECUTION TIME
        # ----------------------------------------------------

        execution_time = round(
            time.perf_counter()
            - start_time,
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
                )
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
        # API ANSWER DEBUG
        # ----------------------------------------------------

        print()
        print("API ANSWER BEFORE RESPONSE:")
        print(repr(answer))
        print()

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

            error=error
        )

    except Exception as exc:

        execution_time = round(
            time.perf_counter()
            - start_time,
            3
        )

        print()
        print("=" * 60)
        print("MCP API REQUEST FAILED")
        print("=" * 60)

        print(
            "Request ID:",
            request_id
        )

        print(
            "Error:",
            str(exc)
        )

        print(
            "Execution Time:",
            f"{execution_time:.3f}s"
        )

        print("=" * 60)

        return QueryResponse(

            request_id=request_id,

            status="error",

            answer=None,

            execution_time=execution_time,

            error=str(exc)
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