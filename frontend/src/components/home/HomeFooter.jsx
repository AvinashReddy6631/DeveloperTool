import { Link } from "react-router-dom";
import { ORCHESTRATION_DEMO_HREF } from "../../lib/routes";

export default function HomeFooter() {
  return (
    <footer className="di-footer">
      <div>
        <strong>Developer Intelligence</strong>
        <span>MCP agent orchestration for developer workflows</span>
      </div>
      <nav aria-label="Footer">
        <a href="#home">Home</a>
        <a href="#agents">Agents</a>
        <a href="#how-it-works">How It Works</a>
        <a href="#repository">Repository</a>
        <a href="#pricing">Pricing</a>
        <a href="#documentation">Docs</a>
          <Link to={ORCHESTRATION_DEMO_HREF}>Live Demo</Link>
      </nav>
      <p className="di-footer-meta">© 2026 · Evidence over spectacle</p>
    </footer>
  );
}
