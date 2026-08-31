import { useOrchestration } from "../../context/OrchestrationContext";
import UxState from "../ux/UxState";

export default function OrchLocked({ kind = "ai" }) {
  const { setShowUpgrade } = useOrchestration();
  const repo = kind === "repo";
  return (
    <div className="orch-lock">
      <UxState
        kind="rateLimited"
        kicker="Locked"
        title={
          repo
            ? "Repository analysis is locked on Free."
            : "Ask is locked on Free."
        }
          body={
            repo
              ? "Pro includes advanced repository intelligence. Checkout is not implemented."
              : "You have used the free AI request quota on this account."
          }
        action={
          <button type="button" className="orch-btn" onClick={() => setShowUpgrade(true)}>
            Upgrade to Pro
          </button>
        }
      />
    </div>
  );
}
