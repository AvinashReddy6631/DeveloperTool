import time
import json
from datetime import datetime


class ExecutionTrace:
    """
    Production-style execution tracing for MCP agents.

    Tracks:
    - User query
    - Orchestrator decision
    - Agents used
    - MCP tool calls
    - Tool arguments
    - Tool results
    - Agent execution time
    - Errors
    - Final status
    - Final answer
    """

    def __init__(self, query=None):

        self.query = query

        self.start_time = time.perf_counter()

        self.orchestrator_decision = None

        self.agents = []

        self.tool_calls = []

        self.events = []

        self.errors = []

        self.final_status = "running"

        self.final_answer = None

        self.created_at = datetime.now().isoformat()

    # ========================================================
    # EVENT
    # ========================================================

    def add_event(self, event_type, data=None):

        event = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "data": data or {}
        }

        self.events.append(event)

    # ========================================================
    # ORCHESTRATOR
    # ========================================================

    def record_orchestrator(self, decision):

        self.orchestrator_decision = decision

        self.add_event(
            "orchestrator_decision",
            {
                "decision": decision
            }
        )

    # ========================================================
    # AGENT START
    # ========================================================

    def record_agent_start(self, agent_name):

        if agent_name not in self.agents:
            self.agents.append(agent_name)

        self.add_event(
            "agent_start",
            {
                "agent": agent_name
            }
        )

    # ========================================================
    # AGENT RESULT
    # ========================================================

    def record_agent_result(
        self,
        agent_name,
        status,
        execution_time=None,
        tool_calls=0
    ):

        if agent_name not in self.agents:
            self.agents.append(agent_name)

        self.add_event(
            "agent_result",
            {
                "agent": agent_name,
                "status": status,
                "execution_time": execution_time,
                "tool_calls": tool_calls
            }
        )

    # ========================================================
    # IMPORT AGENT RESULT
    # ========================================================

    def record_agent_execution(
        self,
        agent_name,
        result
    ):
        """
        Connect an AgentHarness result to the execution trace.

        Example result:

        {
            "agent": "salary_agent",
            "status": "success",
            "answer": "...",
            "tool_calls": 1,
            "iterations": 0,
            "execution_time": 1.05,
            "error": null
        }
        """

        if not result:
            return

        if agent_name not in self.agents:
            self.agents.append(agent_name)

        status = result.get(
            "status",
            "unknown"
        )

        tool_calls = result.get(
            "tool_calls",
            0
        )

        execution_time = result.get(
            "execution_time"
        )

        answer = result.get(
            "answer"
        )

        error = result.get(
            "error"
        )

        # Record agent result
        self.record_agent_result(
            agent_name=agent_name,
            status=status,
            execution_time=execution_time,
            tool_calls=tool_calls
        )

        # ----------------------------------------------------
        # IMPORTANT
        # ----------------------------------------------------
        # AgentHarness only gives us the number of MCP calls.
        # It does not necessarily contain individual tool names
        # and arguments.
        #
        # Therefore we record the count accurately here.
        # Individual MCP details can be added by the agent itself.
        # ----------------------------------------------------

        self.add_event(
            "agent_execution",
            {
                "agent": agent_name,
                "status": status,
                "tool_calls": tool_calls,
                "execution_time": execution_time,
                "answer": answer
            }
        )

        if error:

            self.record_error(
                error,
                source=agent_name
            )

    # ========================================================
    # MCP TOOL CALL
    # ========================================================

    def record_tool_call(
        self,
        agent,
        tool,
        arguments=None,
        result=None,
        status="success",
        execution_time=None
    ):

        tool_call = {

            "agent": agent,

            "tool": tool,

            "arguments": arguments or {},

            "result": result,

            "status": status,

            "execution_time": execution_time
        }

        self.tool_calls.append(
            tool_call
        )

        self.add_event(
            "mcp_tool_call",
            tool_call
        )

    # ========================================================
    # RECORD TOOL COUNT
    # ========================================================

    def record_tool_count(
        self,
        agent_name,
        count
    ):
        """
        Record MCP calls when only the count is available.

        This prevents the real execution trace from incorrectly
        showing MCP Calls: 0.
        """

        try:
            count = int(count)
        except (TypeError, ValueError):
            count = 0

        # Count already recorded individually
        existing = sum(
            1
            for call in self.tool_calls
            if call.get("agent") == agent_name
        )

        missing = count - existing

        if missing <= 0:
            return

        for _ in range(missing):

            self.tool_calls.append(
                {
                    "agent": agent_name,
                    "tool": "MCP tool call",
                    "arguments": {},
                    "result": None,
                    "status": "success",
                    "execution_time": None
                }
            )

        self.add_event(
            "mcp_tool_count",
            {
                "agent": agent_name,
                "count": count
            }
        )

    # ========================================================
    # ERROR
    # ========================================================

    def record_error(
        self,
        error,
        source=None
    ):

        error_data = {

            "source": source,

            "error": str(error)
        }

        self.errors.append(
            error_data
        )

        self.add_event(
            "error",
            error_data
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    def finish(
        self,
        status="success",
        answer=None
    ):

        self.final_status = status

        self.final_answer = answer

        self.add_event(
            "execution_finished",
            {
                "status": status
            }
        )

    # ========================================================
    # EXECUTION TIME
    # ========================================================

    def execution_time(self):

        return round(
            time.perf_counter()
            - self.start_time,
            3
        )

    # ========================================================
    # TRACE RESULT
    # ========================================================

    def to_dict(self):

        return {

            "query": self.query,

            "created_at": self.created_at,

            "orchestrator_decision":
                self.orchestrator_decision,

            "agents":
                self.agents,

            "tool_calls":
                self.tool_calls,

            "errors":
                self.errors,

            "final_status":
                self.final_status,

            "final_answer":
                self.final_answer,

            "execution_time":
                self.execution_time(),

            "events":
                self.events
        }

    # ========================================================
    # JSON
    # ========================================================

    def to_json(self):

        return json.dumps(
            self.to_dict(),
            indent=2,
            default=str
        )

    # ========================================================
    # PRINT TRACE
    # ========================================================

    def print_trace(self):

        trace = self.to_dict()

        print()
        print("=" * 60)
        print("MCP EXECUTION TRACE")
        print("=" * 60)

        print()

        print(
            "Query:",
            trace["query"]
        )

        print()

        print(
            "Orchestrator:",
            trace["orchestrator_decision"]
        )

        print()

        print(
            "Agents:",
            ", ".join(trace["agents"])
            if trace["agents"]
            else "None"
        )

        print()

        print(
            "MCP Calls:",
            len(trace["tool_calls"])
        )

        print()

        # ----------------------------------------------------
        # TOOL CALL DETAILS
        # ----------------------------------------------------

        for index, call in enumerate(
            trace["tool_calls"],
            start=1
        ):

            print(
                f"Tool Call #{index}"
            )

            print(
                "  Agent:",
                call["agent"]
            )

            print(
                "  Tool:",
                call["tool"]
            )

            print(
                "  Arguments:",
                call["arguments"]
            )

            print(
                "  Status:",
                call["status"]
            )

            if call["execution_time"] is not None:

                print(
                    "  Execution Time:",
                    call["execution_time"]
                )

            print()

        # ----------------------------------------------------
        # ERRORS
        # ----------------------------------------------------

        if trace["errors"]:

            print(
                "Errors:"
            )

            for error in trace["errors"]:

                print(
                    "  Source:",
                    error["source"]
                )

                print(
                    "  Error:",
                    error["error"]
                )

                print()

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        print(
            "Final Status:",
            trace["final_status"]
        )

        print()

        if trace["final_answer"]:

            print(
                "Final Answer:"
            )

            print(
                trace["final_answer"]
            )

            print()

        print(
            "Total Execution Time:",
            f"{trace['execution_time']:.3f}s"
        )

        print()

        print("=" * 60)


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    trace = ExecutionTrace(
        "Analyze Google"
    )

    trace.record_orchestrator(
        "COMPANY"
    )

    trace.record_agent_start(
        "company_agent"
    )

    trace.record_agent_execution(
        "company_agent",
        {
            "agent": "company_agent",
            "status": "success",
            "answer": "Google has 2 employees.",
            "tool_calls": 1,
            "iterations": 0,
            "execution_time": 0.91,
            "error": None
        }
    )

    trace.record_tool_call(
        agent="company_agent",
        tool="get_company_statistics",
        arguments={
            "company": "Google"
        },
        result={
            "employees": 2,
            "average_salary": 82500
        },
        status="success",
        execution_time=0.91
    )

    trace.finish(
        status="success",
        answer="Google has 2 employees."
    )

    trace.print_trace()