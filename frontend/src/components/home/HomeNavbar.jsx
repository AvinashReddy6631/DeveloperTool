import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ORCHESTRATION_DEMO_HREF } from "../../lib/routes";
import { NAV_LINKS } from "./homeData";

function isHomeNavActive(hash, href) {
  const current = hash || "#home";
  return current === href;
}

export default function HomeNavbar() {
  const { hash } = useLocation();
  const [compact, setCompact] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let frame = 0;
    const onScroll = () => {
      if (frame) return;
      frame = window.requestAnimationFrame(() => {
        setCompact(window.scrollY > 24);
        frame = 0;
      });
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.cancelAnimationFrame(frame);
    };
  }, []);

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

  useEffect(() => {
    if (!open) return undefined;
    const drawer = document.getElementById("di-mobile-nav");
    const first = drawer?.querySelector("a");
    first?.focus();
    return undefined;
  }, [open]);

  return (
    <header className={`di-nav-wrap${compact ? " is-compact" : ""}${open ? " is-open" : ""}`}>
      <a className="di-skip" href="#di-main">
        Skip to content
      </a>
      <div className="di-nav" role="navigation" aria-label="Primary">
        <Link className="di-brand" to="/" onClick={() => setOpen(false)}>
          <span className="di-brand-mark" aria-hidden="true" />
          <span>Developer Intelligence</span>
        </Link>

        <nav className="di-nav-links" aria-label="Page sections">
          {NAV_LINKS.map((link) => {
            const active = isHomeNavActive(hash, link.href);
            return (
              <a
                key={link.href}
                href={link.href}
                className={active ? "is-on" : undefined}
                aria-current={active ? "location" : undefined}
              >
                {link.label}
              </a>
            );
          })}
        </nav>

        <Link
          className="di-btn di-btn-primary di-nav-cta"
          to={ORCHESTRATION_DEMO_HREF}
          aria-label="Try live demo"
        >
          Try Live Demo
          <span className="di-btn-arrow" aria-hidden="true">
            →
          </span>
        </Link>

        <button
          type="button"
          className="di-nav-toggle"
          aria-expanded={open}
          aria-controls="di-mobile-nav"
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((value) => !value)}
        >
          <span aria-hidden="true" />
          <span aria-hidden="true" />
        </button>
      </div>

      <div className="di-mobile-nav" id="di-mobile-nav" hidden={!open}>
        {NAV_LINKS.map((link) => {
          const active = isHomeNavActive(hash, link.href);
          return (
            <a
              key={link.href}
              href={link.href}
              className={active ? "is-on" : undefined}
              aria-current={active ? "location" : undefined}
              onClick={() => setOpen(false)}
            >
              {link.label}
            </a>
          );
        })}
        <Link
          className="di-btn di-btn-primary"
          to={ORCHESTRATION_DEMO_HREF}
          onClick={() => setOpen(false)}
        >
          Try Live Demo
          <span className="di-btn-arrow" aria-hidden="true">
            →
          </span>
        </Link>
      </div>
    </header>
  );
}
