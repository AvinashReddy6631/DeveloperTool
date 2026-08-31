import { useOrchestration } from "../../context/OrchestrationContext";

function remainingLabel(value, limit) {
  if (value == null) return "—";
  return `${value} / ${limit} remaining`;
}

export default function OrchUsage() {
  const { usage, user, setShowUpgrade, setShowAccount } = useOrchestration();

  return (
    <section className="orch-usage orch-usage-compact" aria-label="Free plan usage">
      <div className="orch-usage-head">
        <div>
          <p className="orch-kicker">Free plan</p>
          <h2>Usage</h2>
        </div>
        <button type="button" className="orch-btn ghost" onClick={() => setShowUpgrade(true)}>
          Upgrade to Pro
        </button>
      </div>

      {!user ? (
        <p className="orch-usage-note">
          Sign in to load your remaining requests.{" "}
          <button type="button" className="orch-btn ghost" onClick={() => setShowAccount(true)}>
            Account
          </button>
        </p>
      ) : (
        <div className="orch-usage-meters">
          <div>
            <span>AI requests</span>
            <strong>{remainingLabel(usage.aiRemaining, usage.aiLimit)}</strong>
          </div>
          <div>
            <span>Repository analysis</span>
            <strong>{remainingLabel(usage.repoRemaining, usage.repoLimit)}</strong>
          </div>
        </div>
      )}
    </section>
  );
}
