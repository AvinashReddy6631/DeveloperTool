import PlanCards from "../pricing/PlanCards";
import FeatureCompare from "../pricing/FeatureCompare";
import LockedFeatures from "../pricing/LockedFeatures";
import { useOrchestration } from "../../context/OrchestrationContext";
import "../pricing/pricing.css";

export default function OrchPricing() {
  const { setShowUpgrade } = useOrchestration();

  return (
    <section className="orch-pricing di-pricing" id="pricing" aria-label="Pricing">
      <p className="orch-kicker">Pricing</p>
      <h2>Free and Pro on the same fabric.</h2>
      <p className="orch-note">
        Upgrade opens a positioning dialog. Payment is not implemented.
      </p>
      <PlanCards onUpgrade={() => setShowUpgrade(true)} />
      <FeatureCompare />
      <LockedFeatures />
    </section>
  );
}
