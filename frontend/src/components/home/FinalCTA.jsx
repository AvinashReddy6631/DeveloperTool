import { Link } from "react-router-dom";
import { ORCHESTRATION_DEMO_HREF } from "../../lib/routes";
import Reveal from "./Reveal";

export default function FinalCTA() {
  return (
    <section className="di-cta">
      <Reveal>
        <p className="di-eyebrow">Enter the fabric</p>
        <h2>The story ends where the live orchestrator begins.</h2>
        <p className="di-lead">
          Take a real question into the existing MCP workspace — routing,
          traces, and repository tools — unchanged in this phase.
        </p>
        <Link
          className="di-btn di-btn-primary"
          to={ORCHESTRATION_DEMO_HREF}
          aria-label="Open the live demo"
        >
          Try Live Demo
          <span className="di-btn-arrow" aria-hidden="true">
            →
          </span>
        </Link>
      </Reveal>
    </section>
  );
}
