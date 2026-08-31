import { useRef } from "react";
import { motion, useReducedMotion } from "motion/react";
import Reveal from "./Reveal";
import { useCycle } from "./useCycle";
import { AGENTS } from "./homeData";

const CORE = { x: 50, y: 46 };

export default function AgentNetwork() {
  const ref = useRef(null);
  const reduceMotion = useReducedMotion();
  const [index] = useCycle(AGENTS.length, 2400, ref);
  const live = AGENTS[index];

  return (
    <section className="di-section" id="agents" ref={ref}>
      <Reveal>
        <p className="di-eyebrow">Agent network</p>
        <h2>Five specialists. One routing mind.</h2>
        <p className="di-lead di-lead-narrow">
          Salary, company, weather, general, and repository intelligence hang
          off a single orchestrator — a connected system, not a menu of tools.
        </p>
      </Reveal>

      <div className="di-constellation" role="group" aria-label="Connected agent system">
        <svg className="di-constellation-links" viewBox="0 0 100 100" aria-hidden="true">
          {AGENTS.map((agent, i) => (
            <line
              key={agent.id}
              x1={CORE.x}
              y1={CORE.y}
              x2={agent.x}
              y2={agent.y}
              className={i === index ? "is-live" : ""}
            />
          ))}
        </svg>

        <div className="di-constellation-core">
          <span>MCP</span>
          Orchestrator
        </div>

        {AGENTS.map((agent, i) => (
          <motion.article
            key={agent.id}
            className={`di-satellite${i === index ? " is-live" : ""}`}
            style={{ left: `${agent.x}%`, top: `${agent.y}%` }}
            initial={reduceMotion ? false : { opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: reduceMotion ? 0 : i * 0.04, duration: 0.4 }}
          >
            <span aria-hidden="true">{agent.mark}</span>
            <h3>{agent.name}</h3>
            <p>{agent.summary}</p>
          </motion.article>
        ))}
      </div>

      <p className="di-constellation-status">
        Live spoke · <strong>{live.name}</strong>
      </p>
    </section>
  );
}
