import { Link } from "react-router-dom";
import { PLAN_FEATURES } from "../../lib/pricing";
import ProBadge from "./ProBadge";

export default function PlanCards({ onUpgrade, freeHref }) {
  return (
    <div className="plan-grid">
      <article className="plan-card">
        <ProBadge plan="free" />
        <h3>Free</h3>
        <p className="plan-price">$0</p>
        <p className="plan-price-note">Current plan · no charge</p>
        <p>Explore the fabric with a preview ceiling.</p>
        <ul>
          {PLAN_FEATURES.free.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        {freeHref ? (
          <Link className="orch-btn di-btn di-btn-primary" to={freeHref}>
            Continue on Free
          </Link>
        ) : (
          <p className="orch-note">You are on the Free presentation.</p>
        )}
      </article>

      <article className="plan-card is-pro">
        <span className="plan-rec">Recommended</span>
        <ProBadge plan="pro" />
        <h3>Pro</h3>
        <p className="plan-price">Billing not live</p>
        <p className="plan-price-note">Checkout is not implemented</p>
        <p>The same intelligence without the preview ceiling — when billing exists.</p>
        <ul>
          {PLAN_FEATURES.pro.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <button type="button" className="orch-btn di-btn di-btn-primary" onClick={onUpgrade}>
          Upgrade to Pro
        </button>
      </article>
    </div>
  );
}
