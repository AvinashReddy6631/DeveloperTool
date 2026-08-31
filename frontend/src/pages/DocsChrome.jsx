import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ORCHESTRATION_DEMO_HREF, ORCHESTRATION_PATH } from "../lib/routes";
import "./docs.css";

export default function DocsChrome({ activeView, children }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth > 1024) setOpen(false);
    };
    const onKey = (event) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("resize", onResize);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("resize", onResize);
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  const close = () => setOpen(false);

  const nav = (
    <>
      <Link to="/" onClick={close}>
        Home
      </Link>
      <Link to={ORCHESTRATION_DEMO_HREF} onClick={close}>
        Live Demo
      </Link>
      <a
        className={activeView === "api" ? "is-on" : ""}
        href="#api"
        onClick={close}
        aria-current={activeView === "api" ? "page" : undefined}
      >
        API
      </a>
      <a
        className={activeView === "docs" ? "is-on" : ""}
        href="#documentation"
        onClick={close}
        aria-current={activeView === "docs" ? "page" : undefined}
      >
        Docs
      </a>
    </>
  );

  return (
    <div className="di-docs">
      <div className="docs-atmosphere" aria-hidden="true">
        <span className="docs-veil docs-veil-a" />
        <span className="docs-veil docs-veil-b" />
        <span className="docs-grain" />
      </div>

      <header className={`docs-header${open ? " is-open" : ""}`}>
        <div className="docs-header-bar">
          <Link className="docs-brand" to="/" onClick={close}>
            <span className="docs-brand-mark" aria-hidden="true" />
            <span>
              <strong>Developer Intelligence</strong>
              <em>{activeView === "api" ? "API reference" : "Documentation"}</em>
            </span>
          </Link>
          <nav className="docs-nav" aria-label="Docs">
            {nav}
          </nav>
          <Link className="docs-cta" to={ORCHESTRATION_DEMO_HREF} onClick={close}>
            Try Live Demo
            <span aria-hidden="true">→</span>
          </Link>
          <button
            type="button"
            className="docs-toggle"
            aria-expanded={open}
            aria-controls="docs-mobile-nav"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((value) => !value)}
          >
            <span aria-hidden="true" />
            <span aria-hidden="true" />
          </button>
        </div>
        <div className="docs-mobile-nav" id="docs-mobile-nav" hidden={!open}>
          <nav aria-label="Docs mobile">{nav}</nav>
          <Link className="docs-cta" to={ORCHESTRATION_DEMO_HREF} onClick={close}>
            Try Live Demo
            <span aria-hidden="true">→</span>
          </Link>
        </div>
      </header>

      <div className="di-page-enter">{children}</div>

      <footer className="docs-footer">
        <strong>Developer Intelligence</strong>
        <span>MCP agent orchestration for developer workflows</span>
        <nav aria-label="Footer">
          <Link to="/">Home</Link>
          <Link to={ORCHESTRATION_PATH}>Live Demo</Link>
          <a href="#api">API</a>
          <a href="#documentation">Docs</a>
        </nav>
      </footer>
    </div>
  );
}
