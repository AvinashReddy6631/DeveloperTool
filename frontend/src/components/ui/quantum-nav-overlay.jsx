import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { isOrchestrationPath } from "../../lib/routes";
import QuantumCloudLoader from "./quantum-cloud-loader";
import "./quantum-nav-overlay.css";

const NAVIGATION_LOADING_DURATION = 6000;

const DOC_SECTION_HASHES = new Set([
  "#documentation",
  "#architecture",
  "#agents-docs",
  "#sessions",
  "#flow",
]);

function getHashView(hash) {
  if (hash === "#api" || hash.startsWith("#api-")) return "api";
  if (DOC_SECTION_HASHES.has(hash)) return "docs";
  return null;
}

function locationKey(url) {
  return `${url.pathname}${url.search}${url.hash}`;
}

function isViewChangingNav(from, to) {
  if (from.pathname !== to.pathname || from.search !== to.search) return true;
  return getHashView(from.hash) !== getHashView(to.hash);
}

function shouldIgnoreAnchor(anchor, event) {
  if (!anchor) return true;
  if (event.button !== 0) return true;
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return true;
  if (anchor.hasAttribute("download")) return true;
  if (anchor.target && anchor.target !== "_self") return true;
  if (anchor.getAttribute("rel")?.includes("external")) return true;
  return false;
}

function loadingDuration() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return 400;
  return NAVIGATION_LOADING_DURATION;
}

export default function QuantumNavOverlay() {
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const navTimer = useRef(0);
  const pending = useRef(null);
  const busy = useRef(false);
  const locKey = locationKey(location);
  const startedKey = useRef(locKey);

  const finishOverlay = () => {
    busy.current = false;
    pending.current = null;
    setOpen(false);
    delete document.documentElement.dataset.quantumNav;
  };

  useEffect(() => {
    const onClick = (event) => {
      const anchor = event.target.closest?.("a[href]");
      if (shouldIgnoreAnchor(anchor, event)) return;

      let next;
      try {
        next = new URL(anchor.href, window.location.href);
      } catch {
        return;
      }

      if (next.origin !== window.location.origin) return;
      if (!isViewChangingNav(window.location, next)) return;
      if (locationKey(window.location) === locationKey(next)) return;

      // Try Demo / live workspace must enter orchestration immediately.
      // Do not apply the 6s quantum delay to that CTA or its equivalents.
      if (
        isOrchestrationPath(next.pathname) &&
        !isOrchestrationPath(window.location.pathname)
      ) {
        return;
      }

      event.preventDefault();

      if (busy.current) return;

      busy.current = true;
      pending.current = next;
      startedKey.current = locationKey(window.location);
      document.documentElement.dataset.quantumNav = "1";
      setOpen(true);

      window.clearTimeout(navTimer.current);
      navTimer.current = window.setTimeout(() => {
        const dest = pending.current;
        if (!dest) {
          finishOverlay();
          return;
        }
        navigate(`${dest.pathname}${dest.search}${dest.hash}`);
        window.clearTimeout(navTimer.current);
        navTimer.current = window.setTimeout(finishOverlay, 800);
      }, loadingDuration());
    };

    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, [navigate]);

  useEffect(() => {
    if (!open || !busy.current) return;
    if (locKey === startedKey.current) return;
    window.clearTimeout(navTimer.current);
    finishOverlay();
  }, [locKey, open]);

  useEffect(
    () => () => {
      window.clearTimeout(navTimer.current);
      delete document.documentElement.dataset.quantumNav;
    },
    []
  );

  return (
    <div
      className={`quantum-nav-overlay${open ? " is-on" : ""}`}
      role="status"
      aria-live="polite"
      aria-atomic="true"
      aria-busy={open}
      aria-hidden={!open}
    >
      {open ? (
        <>
          <QuantumCloudLoader className="quantum-cloud-loader" />
          <p className="quantum-nav-copy">Connecting intelligence</p>
        </>
      ) : null}
    </div>
  );
}
