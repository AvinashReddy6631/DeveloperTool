import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import ProBadge from "../pricing/ProBadge";
import { useOrchestration } from "../../context/OrchestrationContext";

export default function OrchHeader() {
  const {
    isPersonalApiKeyConnected,
    setShowAiAccess,
    setApiKeyError,
    usage,
    user,
    setShowAccount,
    setShowUpgrade,
  } = useOrchestration();
  const { pathname, hash } = useLocation();
  const [open, setOpen] = useState(false);
  const section = hash || "";

  const remaining =
    usage.aiRemaining == null ? "—" : `${usage.aiRemaining} AI left`;

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
      <Link to="/" onClick={close} className={pathname === "/" ? "is-on" : undefined}>
        Home
      </Link>
      <a
        href="#agents"
        onClick={close}
        className={section === "#agents" ? "is-on" : undefined}
        aria-current={section === "#agents" ? "location" : undefined}
      >
        Agents
      </a>
      <a
        href="#repository"
        onClick={close}
        className={section === "#repository" ? "is-on" : undefined}
        aria-current={section === "#repository" ? "location" : undefined}
      >
        Repository
      </a>
      <a
        href="#pricing"
        onClick={close}
        className={section === "#pricing" ? "is-on" : undefined}
        aria-current={section === "#pricing" ? "location" : undefined}
      >
        Pricing
      </a>
      <a href="#api" onClick={close}>
        API
      </a>
      <a href="#documentation" onClick={close}>
        Docs
      </a>
    </>
  );

  const actions = (
    <>
      <ProBadge plan="free" />
      {user ? <p className="orch-usage-pill">{remaining}</p> : null}
      <button
        type="button"
        className="orch-btn ghost"
        onClick={() => {
          close();
          setShowUpgrade(true);
        }}
      >
        Upgrade
      </button>
      <button
        type="button"
        className="orch-btn ghost"
        onClick={() => {
          close();
          setShowAccount(true);
        }}
      >
        {user ? user.email : "Account"}
      </button>
      <button
        type="button"
        className={`orch-access${isPersonalApiKeyConnected ? " is-on" : ""}`}
        onClick={() => {
          close();
          setShowAiAccess(true);
          setApiKeyError("");
        }}
      >
        <span className="orch-access-dot" aria-hidden="true" />
        AI Access
        {isPersonalApiKeyConnected ? (
          <span className="orch-access-extra"> · connected</span>
        ) : null}
      </button>
    </>
  );

  return (
    <header className={`orch-header${open ? " is-open" : ""}`}>
      <div className="orch-header-bar">
      <Link className="orch-brand" to="/" onClick={close}>
        <span className="orch-brand-mark" aria-hidden="true" />
        <span>
          <strong>Developer Intelligence</strong>
          <em>Ask. Route. Answer.</em>
        </span>
      </Link>

      <nav className="orch-nav" aria-label="Orchestration">
        {nav}
      </nav>

      <div className="orch-header-actions">{actions}</div>

      <button
        type="button"
        className="orch-toggle"
        aria-expanded={open}
        aria-controls="orch-mobile-nav"
        aria-label={open ? "Close menu" : "Open menu"}
        onClick={() => setOpen((value) => !value)}
      >
        <span aria-hidden="true" />
        <span aria-hidden="true" />
      </button>
      </div>

      <div className="orch-mobile-nav" id="orch-mobile-nav" hidden={!open}>
        <nav aria-label="Orchestration mobile">{nav}</nav>
        <div className="orch-header-actions is-drawer">{actions}</div>
      </div>
    </header>
  );
}
