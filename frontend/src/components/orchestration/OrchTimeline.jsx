import { motion } from "motion/react";
import { formatAgentName } from "../../lib/orchestrationAgents";
import { useOrchestration } from "../../context/OrchestrationContext";

export default function OrchTimeline() {
  const { phase, submittedQuery, response } = useOrchestration();
  const trace = response?.execution_trace;

  const steps = [
    {
      id: "user",
      title: "Question",
      detail: submittedQuery || "Waiting for a command",
      done: Boolean(submittedQuery),
    },
    {
      id: "mcp",
      title: "MCP",
      detail: trace?.orchestrator
        ? `Decision: ${trace.orchestrator}`
        : phase === "thinking"
          ? "Classifying intent"
          : "Idle",
      done: Boolean(trace?.orchestrator) || phase === "success",
    },
    {
      id: "route",
      title: "Agent",
      detail:
        (trace?.agents || []).length > 0
          ? (trace.agents || []).map(formatAgentName).join(", ")
          : phase === "thinking"
            ? "Selecting specialist"
            : "No route yet",
      done: (trace?.agents || []).length > 0,
    },
    {
      id: "exec",
      title: "Processing",
      detail:
        (trace?.mcp_calls || []).length > 0
          ? `${trace.mcp_calls.length} MCP tool call(s)`
          : phase === "thinking"
            ? "Running tools"
            : "No tool calls recorded",
      done: phase === "success",
    },
    {
      id: "response",
      title: "Response",
      detail:
        phase === "success"
          ? "Answer in workspace"
          : phase === "error"
            ? "Failed"
            : "—",
      done: phase === "success",
    },
  ];

  return (
    <section className="orch-timeline" aria-label="Execution timeline">
      <div className="orch-panel-head">
        <div>
          <p className="orch-kicker">Execution timeline</p>
          <h2>Evidence of the route</h2>
        </div>
      </div>
      <ol>
        {steps.map((step) => (
          <motion.li
            key={step.id}
            className={step.done ? "is-done" : phase === "thinking" ? "is-pending" : ""}
            animate={{ opacity: step.done || phase === "thinking" ? 1 : 0.55 }}
          >
            <strong>{step.title}</strong>
            <span>{step.detail}</span>
          </motion.li>
        ))}
      </ol>
    </section>
  );
}
