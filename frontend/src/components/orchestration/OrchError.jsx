import { useState } from "react";
import { useOrchestration } from "../../context/OrchestrationContext";

export default function OrchError() {
  const { error, technicalError, handleRetryClear } = useOrchestration();
  const [open, setOpen] = useState(false);
  const details = technicalError && technicalError !== error ? technicalError : "";

  return (
    <div className="orch-fail">
      <p className="orch-kicker">Error</p>
      <h3>Something went wrong</h3>
      <p>{error || "We couldn't complete that request."}</p>
      <button type="button" className="orch-btn" onClick={handleRetryClear}>
        Try again
      </button>
      {details ? (
        <div className="orch-tech">
          <button
            type="button"
            className="orch-btn ghost"
            onClick={() => setOpen((value) => !value)}
          >
            {open ? "Hide technical details" : "Technical details"}
          </button>
          {open ? <pre className="orch-trace">{details}</pre> : null}
        </div>
      ) : null}
    </div>
  );
}
