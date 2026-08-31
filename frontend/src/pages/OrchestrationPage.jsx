import { useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { OrchestrationProvider, useOrchestration } from "../context/OrchestrationContext";
import AccountModal from "../components/orchestration/AccountModal";
import AiAccessModal from "../components/orchestration/AiAccessModal";
import OrchComposer from "../components/orchestration/OrchComposer";
import OrchHeader from "../components/orchestration/OrchHeader";
import OrchPricing from "../components/orchestration/OrchPricing";
import OrchRepository from "../components/orchestration/OrchRepository";
import OrchUsage from "../components/orchestration/OrchUsage";
import { OrchVisProvider } from "../components/orchestration/OrchVisContext";
import OrchWorkspace from "../components/orchestration/OrchWorkspace";
import UpgradeModal from "../components/pricing/UpgradeModal";
import { readStoredToken } from "../lib/authStorage";
import "../components/orchestration/orchestration.css";

function OrchestrationShell() {
  const {
    showUpgrade,
    setShowUpgrade,
    setShowAccount,
    queryInputRef,
  } = useOrchestration();
  const [params, setSearchParams] = useSearchParams();
  const demoHandled = useRef(false);

  useEffect(() => {
    if (demoHandled.current) return undefined;
    if (params.get("demo") !== "1") return undefined;
    demoHandled.current = true;

    if (!readStoredToken()) {
      setShowAccount(true);
    }

    const frame = window.requestAnimationFrame(() => {
      queryInputRef.current?.focus();
    });

    const next = new URLSearchParams(params);
    next.delete("demo");
    setSearchParams(next, { replace: true });

    return () => window.cancelAnimationFrame(frame);
  }, [params, queryInputRef, setSearchParams, setShowAccount]);

  return (
    <div className="di-orch">
      <div className="orch-atmosphere" aria-hidden="true">
        <span className="orch-veil orch-veil-a" />
        <span className="orch-veil orch-veil-b" />
        <span className="orch-veil orch-veil-c" />
        <span className="orch-grain" />
      </div>
      <OrchHeader />
      <AccountModal />
      <AiAccessModal />
      <UpgradeModal open={showUpgrade} onClose={() => setShowUpgrade(false)} />
      <main className="orch-main orch-main-simple di-page-enter">
        <OrchComposer />
        <OrchUsage />
        <OrchWorkspace />
        <OrchRepository />
        <OrchPricing />
      </main>
    </div>
  );
}

export default function OrchestrationPage() {
  return (
    <OrchestrationProvider>
      <OrchVisProvider>
        <OrchestrationShell />
      </OrchVisProvider>
    </OrchestrationProvider>
  );
}
