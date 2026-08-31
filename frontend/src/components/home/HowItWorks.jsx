import { useRef } from "react";
import { motion, useReducedMotion } from "motion/react";
import Reveal from "./Reveal";
import { useCycle } from "./useCycle";
import { HOW_IT_WORKS } from "./homeData";

export default function HowItWorks() {
  const ref = useRef(null);
  const reduceMotion = useReducedMotion();
  const [index] = useCycle(HOW_IT_WORKS.length, 2100, ref);

  return (
    <section className="di-section" id="how-it-works" ref={ref}>
      <Reveal>
        <p className="di-eyebrow">How it works</p>
        <h2>Ask. Orchestrate. Analyze. Respond.</h2>
        <p className="di-lead di-lead-narrow">
          Four beats from a natural-language ask to a traced specialist
          response — the same path the live orchestrator uses.
        </p>
      </Reveal>

      <ol className="di-how">
        {HOW_IT_WORKS.map((item, i) => (
          <motion.li
            key={item.step}
            className={i === index ? "is-live" : ""}
            initial={reduceMotion ? false : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: i * 0.05, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          >
            <span>{item.step}</span>
            <h3>{item.title}</h3>
            <p>{item.body}</p>
          </motion.li>
        ))}
      </ol>
    </section>
  );
}
