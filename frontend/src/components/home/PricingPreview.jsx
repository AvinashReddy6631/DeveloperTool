import { useState } from "react";
import Reveal from "./Reveal";
import PlanCards from "../pricing/PlanCards";
import FeatureCompare from "../pricing/FeatureCompare";
import LockedFeatures from "../pricing/LockedFeatures";
import UpgradeModal from "../pricing/UpgradeModal";
import "../pricing/pricing.css";

export default function PricingPreview() {
  const [upgradeOpen, setUpgradeOpen] = useState(false);

  return (
    <section className="di-section di-pricing" id="pricing">
      <Reveal>
        <p className="di-eyebrow">Pricing</p>
        <h2>Free to explore. Pro when billing exists.</h2>
        <p className="di-lead di-lead-narrow">
          Planned ceilings only. Home does not charge, and Upgrade does not
          complete a purchase.
        </p>
      </Reveal>

      <PlanCards
        freeHref="/orchestration?demo=1"
        onUpgrade={() => setUpgradeOpen(true)}
      />
      <FeatureCompare />
      <LockedFeatures />
      <UpgradeModal open={upgradeOpen} onClose={() => setUpgradeOpen(false)} />
    </section>
  );
}
