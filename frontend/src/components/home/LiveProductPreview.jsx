import { useRef } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import Reveal from "./Reveal";
import { useCycle } from "./useCycle";
import { PREVIEW_FRAMES } from "./homeData";
import UxState from "../ux/UxState";
import { UX_COPY, UX_KINDS } from "../../lib/uxStates";

const FRAME_KIND = {
  Question: "empty",
  "MCP activation": "loading",
  "Agent activation": "processing",
  Processing: "processing",
  Response: "success",
};

export default function LiveProductPreview() {
  const ref = useRef(null);
  const reduceMotion = useReducedMotion();
  const [index] = useCycle(PREVIEW_FRAMES.length, 2300, ref);
  const [uxIndex] = useCycle(UX_KINDS.length, 2600, ref);
  const current = PREVIEW_FRAMES[index];
  const uxKind = UX_KINDS[uxIndex];

  return (
    <section className="di-section" id="preview" aria-labelledby="preview-title" ref={ref}>
      <Reveal>
        <p className="di-eyebrow">Live product preview</p>
        <h2 id="preview-title">A scripted pass through the live product.</h2>
        <p className="di-lead di-lead-narrow">
          Question, MCP activation, agent activation, processing, response. No
          real API calls from Home. Interface states below are illustrative.
        </p>
      </Reveal>

      <div className="di-preview-shell">
        <ol className="di-preview-steps">
          {PREVIEW_FRAMES.map((frame, i) => (
            <li key={frame.label} className={i === index ? "is-live" : ""}>
              {frame.label}
            </li>
          ))}
        </ol>

        <AnimatePresence mode="wait">
          <motion.article
            key={current.label}
            className="di-preview"
            aria-live="polite"
            initial={reduceMotion ? false : { opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduceMotion ? undefined : { opacity: 0, y: -10 }}
            transition={{ duration: 0.28 }}
          >
            <div className="di-preview-meta">
              <span>{current.label}</span>
              <span className="di-status">{current.status}</span>
            </div>
            <p className="di-preview-query">{current.query}</p>
            <div className="di-preview-route">
              <span>Agent</span>
              <strong>{current.agent}</strong>
            </div>
            <UxState
              compact
              kind={FRAME_KIND[current.label] || "empty"}
              title={current.answer || current.agent}
              body={
                current.answer
                  ? "Scripted success readout. Home does not call the live API."
                  : "Scripted wait. The live product uses the same state marks."
              }
            />
          </motion.article>
        </AnimatePresence>
      </div>

      <div className="di-ux-board">
        <p className="di-eyebrow">Interface states</p>
        <ol className="di-ux-kinds">
          {UX_KINDS.map((kind, i) => (
            <li key={kind} className={i === uxIndex ? "is-live" : ""}>
              {UX_COPY[kind].kicker}
            </li>
          ))}
        </ol>
        <AnimatePresence mode="wait">
          <motion.div
            key={uxKind}
            initial={reduceMotion ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduceMotion ? undefined : { opacity: 0 }}
            transition={{ duration: 0.24 }}
          >
            <UxState kind={uxKind} />
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}
