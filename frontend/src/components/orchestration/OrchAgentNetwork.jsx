import { motion } from "motion/react";
import { AGENT_CATALOG, formatAgentName } from "../../lib/orchestrationAgents";
import { useOrchestration } from "../../context/OrchestrationContext";

export default function OrchAgentNetwork() {
  const { phase, response } = useOrchestration();
  const live = response?.execution_trace?.agents || [];

  return (
    <section className="orch-agents" id="agents" aria-label="Agent network">
      <div className="orch-panel-head">
        <div>
          <p className="orch-kicker">Agent network</p>
          <h2>Five specialists on one mind</h2>
        </div>
      </div>
      <ul>
        {AGENT_CATALOG.map((agent) => {
          const active = live.includes(agent.id);
          const scanning = phase === "thinking";
          return (
            <motion.li
              key={agent.id}
              className={`${active ? "is-live" : ""}${scanning ? " is-scan" : ""}`}
              layout
              animate={{ opacity: active || scanning ? 1 : 0.7 }}
            >
              <span className="orch-agent-mark" aria-hidden="true">
                {agent.mark}
              </span>
              <div>
                <strong>{agent.name}</strong>
                <em>
                  {active
                    ? "Active on this request"
                    : scanning
                      ? "Awaiting route"
                      : "Ready"}
                </em>
              </div>
            </motion.li>
          );
        })}
      </ul>
      {live.length > 0 && (
        <p className="orch-note">
          Routed: {live.map(formatAgentName).join(" · ")}
        </p>
      )}
    </section>
  );
}
