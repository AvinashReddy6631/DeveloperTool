import { useRef } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import Reveal from "./Reveal";
import { useCycle } from "./useCycle";
import { WHAT_IT_DOES_STAGES } from "./homeData";

export default function WhatItDoes() {
  const ref = useRef(null);
  const reduceMotion = useReducedMotion();
  const [index, setIndex] = useCycle(WHAT_IT_DOES_STAGES.length, 2200, ref);
  const current = WHAT_IT_DOES_STAGES[index];

  return (
    <section className="di-section" id="product" ref={ref}>
      <Reveal>
        <p className="di-eyebrow">What it does</p>
        <h2>A question becomes a routed intelligence path.</h2>
        <p className="di-lead di-lead-narrow">
          Watch intent travel from a sentence to a specialist and back as a
          traced response.
        </p>
      </Reveal>

      <div className="di-story">
        <ol className="di-spine" aria-label="Request lifecycle">
          {WHAT_IT_DOES_STAGES.map((stage, i) => (
            <li key={stage.id}>
              <button
                type="button"
                className={i === index ? "is-live" : ""}
                onClick={() => setIndex(i)}
                aria-current={i === index ? "step" : undefined}
              >
                <span>{String(i + 1).padStart(2, "0")}</span>
                {stage.title}
              </button>
            </li>
          ))}
        </ol>

        <AnimatePresence mode="wait">
          <motion.article
            key={current.id}
            className="di-stage"
            aria-live="polite"
            initial={reduceMotion ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduceMotion ? undefined : { opacity: 0, y: -8 }}
            transition={{ duration: 0.28 }}
          >
            <p className="di-stage-kicker">{current.title}</p>
            <h3>{current.line}</h3>
            <p>{current.body}</p>
          </motion.article>
        </AnimatePresence>
      </div>
    </section>
  );
}
