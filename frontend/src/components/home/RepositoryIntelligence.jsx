import { useRef } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import Reveal from "./Reveal";
import { useCycle } from "./useCycle";
import { REPO_FLOW } from "./homeData";
import UxState from "../ux/UxState";

const REPO_KIND = {
  github: "empty",
  intel: "loading",
  structure: "processing",
  deps: "success",
  quality: "success",
  issues: "rateLimited",
  insights: "success",
};

export default function RepositoryIntelligence() {
  const ref = useRef(null);
  const reduceMotion = useReducedMotion();
  const [index] = useCycle(REPO_FLOW.length, 2000, ref);
  const current = REPO_FLOW[index];

  return (
    <section className="di-section" id="repository" ref={ref}>
      <Reveal>
        <p className="di-eyebrow">Repository intelligence</p>
        <h2>Turn a GitHub tree into evidence, then insight.</h2>
        <p className="di-lead di-lead-narrow">
          Illustrative walkthrough only. Home never calls GitHub or the
          analysis API. States match the live orchestration workspace.
        </p>
      </Reveal>

      <div className="di-repo-story">
        <ol className="di-flowline">
          {REPO_FLOW.map((step, i) => (
            <li key={step.id} className={i === index ? "is-live" : ""}>
              <span>{step.title}</span>
            </li>
          ))}
        </ol>

        <AnimatePresence mode="wait">
          <motion.div
            key={current.id}
            className="di-repo-stage"
            aria-live="polite"
            initial={reduceMotion ? false : { opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={reduceMotion ? undefined : { opacity: 0, x: -10 }}
            transition={{ duration: 0.28 }}
          >
            <UxState
              kind={REPO_KIND[current.id] || "empty"}
              kicker={current.title}
              title={current.detail}
              body="Sample readout for a fictional workspace — not fetched live."
            />
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}
