import { useReducedMotion } from "motion/react";
import { UX_COPY } from "../../lib/uxStates";
import "./ux-states.css";

function Mark({ kind, still }) {
  return (
    <svg
      className={`ux-mark ux-mark-${kind}${still ? " is-still" : ""}`}
      viewBox="0 0 64 64"
      aria-hidden="true"
    >
      {kind === "empty" && (
        <>
          <rect x="12" y="12" width="40" height="40" rx="8" />
          <path d="M22 32 H42" />
        </>
      )}
      {kind === "loading" && (
        <>
          <rect className="ux-bar" x="12" y="16" width="40" height="6" rx="3" />
          <rect className="ux-bar ux-bar-2" x="12" y="29" width="28" height="6" rx="3" />
          <rect className="ux-bar ux-bar-3" x="12" y="42" width="34" height="6" rx="3" />
        </>
      )}
      {kind === "processing" && (
        <>
          <circle cx="32" cy="32" r="14" />
          <circle className="ux-orbit" cx="32" cy="18" r="3" />
          <circle className="ux-orbit ux-orbit-2" cx="46" cy="32" r="3" />
        </>
      )}
      {kind === "success" && (
        <>
          <circle cx="32" cy="32" r="16" />
          <path d="M22 33 L29 40 L44 24" />
        </>
      )}
      {kind === "error" && (
        <>
          <path d="M32 12 L52 50 H12 Z" />
          <path d="M32 26 V38" />
          <circle cx="32" cy="44" r="1.6" fill="currentColor" stroke="none" />
        </>
      )}
      {kind === "rateLimited" && (
        <>
          <rect x="10" y="24" width="44" height="16" rx="8" />
          <rect className="ux-meter" x="14" y="28" width="12" height="8" rx="4" />
        </>
      )}
      {kind === "unavailable" && (
        <>
          <circle cx="20" cy="32" r="8" />
          <circle cx="44" cy="32" r="8" />
          <path className="ux-break" d="M28 32 H36" />
        </>
      )}
      {kind === "invalid" && (
        <>
          <rect x="10" y="22" width="44" height="20" rx="4" />
          <path className="ux-caret" d="M18 34 H30" />
        </>
      )}
    </svg>
  );
}

export default function UxState({
  kind = "empty",
  kicker,
  title,
  body,
  action,
  compact = false,
  children,
}) {
  const reduced = useReducedMotion();
  const copy = UX_COPY[kind] || UX_COPY.empty;
  const heading = title || copy.title;
  const alert =
    kind === "error" ||
    kind === "rateLimited" ||
    kind === "unavailable" ||
    kind === "invalid";

  return (
    <div
      className={`ux-state ux-${kind}${compact ? " is-compact" : ""}`}
      role={alert ? "alert" : undefined}
      aria-live={alert ? "assertive" : "polite"}
    >
      <Mark kind={kind} still={Boolean(reduced)} />
      <div className="ux-copy">
        <p className="ux-kicker">{kicker || copy.kicker}</p>
        <h3>{heading}</h3>
        {body !== "" && <p>{body || copy.body}</p>}
        {children}
        {action}
      </div>
    </div>
  );
}
