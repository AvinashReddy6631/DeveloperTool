import { useOrchestration } from "../../context/OrchestrationContext";

export default function OrchLoading() {
  const { submittedQuery } = useOrchestration();
  const isRepo = String(submittedQuery || "").toLowerCase().includes("github.com/");
  return (
    <div className="orch-loading">
      <p className="orch-kicker">Processing</p>
      <h3>Analyzing…</h3>
      <p>
        {isRepo
          ? "Routing to Developer Agent for repository analysis."
          : "Routing your question to the selected agent."}
      </p>
      <div className="orch-wait" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}
