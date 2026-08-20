import time


class AgentHarness:
    """
    Production-style execution harness for MCP agents.

    Responsibilities:
    - Track agent iterations
    - Track actual MCP tool calls
    - Enforce safety limits
    - Track execution time
    - Store MCP observability information
    - Produce standardized success/error results
    """

    def __init__(
        self,
        agent_name,
        max_iterations=5,
        max_tool_calls=10,
        timeout_seconds=60
    ):
        self.agent_name = agent_name

        # Safety limits
        self.max_iterations = max_iterations
        self.max_tool_calls = max_tool_calls
        self.timeout_seconds = timeout_seconds

        # Runtime state
        self.start_time = None
        self.tool_calls = 0
        self.iterations = 0

        # MCP observability
        self.mcp_calls = []

    # =========================================================
    # START
    # =========================================================

    def start(self):
        """Start a fresh agent execution."""

        self.start_time = time.perf_counter()

        self.tool_calls = 0
        self.iterations = 0
        self.mcp_calls = []

    # =========================================================
    # ITERATION
    # =========================================================

    def next_iteration(self):
        """
        Register the next agent iteration.

        Raises RuntimeError if the maximum iteration
        limit is exceeded.
        """

        self.iterations += 1

        if self.iterations > self.max_iterations:
            raise RuntimeError(
                f"Maximum iterations exceeded: "
                f"{self.max_iterations}"
            )

        self.check_timeout()

        return self.iterations

    # =========================================================
    # TOOL CALL LIMIT
    # =========================================================

    def check_tool_call_limit(self):
        """
        Register one actual tool call and enforce
        the maximum tool-call limit.
        """

        self.tool_calls += 1

        if self.tool_calls > self.max_tool_calls:
            raise RuntimeError(
                f"Maximum tool calls exceeded: "
                f"{self.max_tool_calls}"
            )

        self.check_timeout()

        return self.tool_calls

    # =========================================================
    # MCP TOOL CALL
    # =========================================================

    def record_tool_call(
        self,
        tool,
        arguments=None,
        result=None,
        status="success",
        execution_time=None,
        agent=None
    ):
        """
        Record an actual MCP tool call.

        IMPORTANT:
        Every recorded MCP call also increments
        self.tool_calls.

        agent is optional so existing agent code that calls:

            harness.record_tool_call(
                tool=...
            )

        continues to work.
        """

        # Use current agent if caller doesn't provide one
        if agent is None:
            agent = self.agent_name

        # Count this as an actual tool call
        self.check_tool_call_limit()

        call = {
            "agent": agent,
            "tool": tool,
            "arguments": arguments or {},
            "result": result,
            "status": status,
            "execution_time": execution_time
        }

        self.mcp_calls.append(call)

        return call

    # =========================================================
    # TIMEOUT
    # =========================================================

    def check_timeout(self):
        """Check whether agent execution exceeded timeout."""

        if self.start_time is None:
            return

        elapsed = (
            time.perf_counter()
            - self.start_time
        )

        if elapsed > self.timeout_seconds:
            raise TimeoutError(
                f"Agent execution exceeded "
                f"{self.timeout_seconds} seconds."
            )

    # =========================================================
    # EXECUTION TIME
    # =========================================================

    def execution_time(self):
        """Return current execution time in seconds."""

        if self.start_time is None:
            return 0

        return round(
            time.perf_counter()
            - self.start_time,
            3
        )

    # =========================================================
    # STATUS
    # =========================================================

    def status(self):
        """Return current runtime status."""

        return {
            "agent": self.agent_name,
            "iterations": self.iterations,
            "tool_calls": self.tool_calls,
            "execution_time": self.execution_time(),
            "mcp_calls": self.mcp_calls
        }

    # =========================================================
    # SUCCESS RESULT
    # =========================================================

    def success(self, answer):
        """Create standardized successful agent result."""

        return {
            "agent": self.agent_name,
            "status": "success",
            "answer": answer,
            "tool_calls": self.tool_calls,
            "iterations": self.iterations,
            "execution_time": self.execution_time(),
            "mcp_calls": self.mcp_calls,
            "error": None
        }

    # =========================================================
    # ERROR RESULT
    # =========================================================

    def error(self, error):
        """Create standardized error agent result."""

        return {
            "agent": self.agent_name,
            "status": "error",
            "answer": None,
            "tool_calls": self.tool_calls,
            "iterations": self.iterations,
            "execution_time": self.execution_time(),
            "mcp_calls": self.mcp_calls,
            "error": str(error)
        }

    # =========================================================
    # VALIDATE RESULT
    # =========================================================

    @staticmethod
    def validate_result(
        result,
        expected_agent
    ):
        """
        Validate standardized agent result.

        Returns a valid error structure if the
        supplied result is malformed.
        """

        # -----------------------------------------------------
        # Result must be dictionary
        # -----------------------------------------------------

        if not isinstance(result, dict):
            return {
                "agent": expected_agent,
                "status": "error",
                "answer": None,
                "tool_calls": 0,
                "iterations": 0,
                "execution_time": 0,
                "mcp_calls": [],
                "error": (
                    "Agent returned invalid "
                    "result format."
                )
            }

        # -----------------------------------------------------
        # Required fields
        # -----------------------------------------------------

        required_fields = [
            "agent",
            "status",
            "answer",
            "tool_calls",
            "iterations",
            "execution_time",
            "mcp_calls",
            "error"
        ]

        for field in required_fields:
            if field not in result:
                return {
                    "agent": expected_agent,
                    "status": "error",
                    "answer": None,
                    "tool_calls": result.get(
                        "tool_calls",
                        0
                    ),
                    "iterations": result.get(
                        "iterations",
                        0
                    ),
                    "execution_time": result.get(
                        "execution_time",
                        0
                    ),
                    "mcp_calls": result.get(
                        "mcp_calls",
                        []
                    ),
                    "error": (
                        f"Missing field: {field}"
                    )
                }

        # -----------------------------------------------------
        # Validate status
        # -----------------------------------------------------

        if result["status"] not in [
            "success",
            "error"
        ]:
            result["status"] = "error"
            result["answer"] = None
            result["error"] = (
                "Invalid agent status."
            )

        # -----------------------------------------------------
        # Validate agent name
        # -----------------------------------------------------

        if result["agent"] != expected_agent:
            result["status"] = "error"
            result["answer"] = None
            result["error"] = (
                f"Unexpected agent name: "
                f"{result['agent']}"
            )

        # -----------------------------------------------------
        # Validate tool calls
        # -----------------------------------------------------

        if not isinstance(
            result["tool_calls"],
            int
        ):
            result["status"] = "error"
            result["answer"] = None
            result["error"] = (
                "tool_calls must be an integer."
            )

        # -----------------------------------------------------
        # Validate MCP calls
        # -----------------------------------------------------

        if not isinstance(
            result["mcp_calls"],
            list
        ):
            result["status"] = "error"
            result["answer"] = None
            result["error"] = (
                "mcp_calls must be a list."
            )

        return result

    # =========================================================
    # PRINT SUMMARY
    # =========================================================

    def print_summary(self, result):
        """Print human-readable agent execution summary."""

        print()

        print(
            f"[{self.agent_name}]"
        )

        print(
            "Status:",
            result.get(
                "status",
                "unknown"
            )
        )

        print(
            "Iterations:",
            result.get(
                "iterations",
                self.iterations
            )
        )

        print(
            "Tool calls:",
            result.get(
                "tool_calls",
                self.tool_calls
            )
        )

        print(
            "MCP calls:",
            len(
                result.get(
                    "mcp_calls",
                    self.mcp_calls
                )
            )
        )

        print(
            "Execution time:",
            f"{result.get('execution_time', 0):.3f}s"
        )

        if result.get("status") == "error":
            print(
                "Error:",
                result.get(
                    "error",
                    "Unknown error"
                )
            )
        else:
            print(
                "Agent completed successfully."
            )

    # =========================================================
    # DEBUG INFORMATION
    # =========================================================

    def debug_info(self):
        """Return detailed runtime debugging information."""

        return {
            "agent": self.agent_name,
            "max_iterations": self.max_iterations,
            "max_tool_calls": self.max_tool_calls,
            "timeout_seconds": self.timeout_seconds,
            "iterations": self.iterations,
            "tool_calls": self.tool_calls,
            "execution_time": self.execution_time(),
            "mcp_calls": self.mcp_calls
        }


# =============================================================
# SIMPLE HARNESS TEST
# =============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("AGENT HARNESS TEST")
    print("=" * 60)

    harness = AgentHarness(
        agent_name="test_agent"
    )

    harness.start()

    harness.record_tool_call(
        tool="get_company_statistics",
        arguments={
            "company": "Google"
        },
        result={
            "employees": 2
        },
        status="success",
        execution_time=0.91
    )

    result = harness.success(
        "Google has 2 employees."
    )

    harness.print_summary(result)

    print()
    print("DEBUG INFO")
    print("=" * 60)

    print(
        harness.debug_info()
    )

    print()
    print("STRUCTURED RESULT")
    print("=" * 60)

    import json

    print(
        json.dumps(
            result,
            indent=2,
            default=str
        )
    )