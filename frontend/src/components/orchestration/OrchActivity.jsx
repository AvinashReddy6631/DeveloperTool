import { formatAgentName } from "../../lib/orchestrationAgents";
import { useOrchestration } from "../../context/OrchestrationContext";

export default function OrchActivity() {
  const { phase, response } = useOrchestration();
  const trace = response?.execution_trace;
  const calls = trace?.mcp_calls || [];
  const agents = trace?.agents || [];

  return (
    <section className="orch-activity" aria-label="Agent activity">
      <div className="orch-panel-head">
        <div>
          <p className="orch-kicker">Agent activity</p>
          <h2>Tools from the real trace</h2>
        </div>
      </div>
      {phase === "thinking" && (
        <p className="orch-note">MCP tools appear here after the real trace returns.</p>
      )}
      {phase !== "thinking" && calls.length === 0 && agents.length === 0 && (
        <p className="orch-note">No MCP calls on the last request.</p>
      )}

      {agents.length > 0 && (
        <ul className="orch-activity-agents">
          {agents.map((agent) => (
            <li key={agent}>{formatAgentName(agent)}</li>
          ))}
        </ul>
      )}

      {calls.length > 0 && (
        <ul className="orch-tools">
          {calls.map((call, index) => (
            <li key={`${call.tool}-${index}`}>
              <div>
                <strong>{call.tool}</strong>
                <span>{call.agent || "MCP Agent"}</span>
              </div>
              <div className="orch-tool-meta">
                <span>{call.status}</span>
                <span>{Number(call.execution_time || 0).toFixed(2)}s</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
