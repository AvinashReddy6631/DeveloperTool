import { useOrchestration } from "../../context/OrchestrationContext";

export default function OrchStatus() {
  const { sessionId, isPersonalApiKeyConnected, response, phase, usage } =
    useOrchestration();
  const trace = response?.execution_trace;

  return (
    <section className="orch-status" aria-label="Status">
      <div className="orch-panel-head">
        <div>
          <p className="orch-kicker">Status</p>
          <h2>Session instruments</h2>
        </div>
      </div>
      <dl>
        <div>
          <dt>Session</dt>
          <dd>{sessionId.slice(0, 8)}</dd>
        </div>
        <div>
          <dt>AI access</dt>
          <dd>{isPersonalApiKeyConnected ? "BYOK" : "Demo"}</dd>
        </div>
        <div>
          <dt>Phase</dt>
          <dd>{phase}</dd>
        </div>
        <div>
          <dt>Orchestrator</dt>
          <dd>{trace?.orchestrator || "—"}</dd>
        </div>
        <div>
          <dt>Agents</dt>
          <dd>{(trace?.agents || []).length}</dd>
        </div>
        <div>
          <dt>MCP calls</dt>
          <dd>{(trace?.mcp_calls || []).length}</dd>
        </div>
        <div>
          <dt>Free AI</dt>
          <dd>
            {usage.aiRemaining == null
              ? "—"
              : `${usage.aiRemaining} / ${usage.aiLimit}`}
          </dd>
        </div>
        <div>
          <dt>Free repo</dt>
          <dd>
            {usage.repoRemaining == null
              ? "—"
              : `${usage.repoRemaining} / ${usage.repoLimit}`}
          </dd>
        </div>
        <div>
          <dt>Meter</dt>
          <dd>{usage.source}</dd>
        </div>
        <div>
          <dt>Trace</dt>
          <dd>
            {trace
              ? `${Number(trace.total_execution_time || 0).toFixed(2)}s`
              : "—"}
          </dd>
        </div>
      </dl>
    </section>
  );
}
