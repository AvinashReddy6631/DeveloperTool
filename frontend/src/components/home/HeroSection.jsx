import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "motion/react";
import IntelligenceNetwork from "./IntelligenceNetwork";
import { ORCHESTRATION_DEMO_HREF } from "../../lib/routes";
import { GITHUB_URL, HERO_SIGNALS } from "./homeData";

export default function HeroSection() {
  const reduceMotion = useReducedMotion();
  const enter = reduceMotion ? false : { opacity: 0, y: 14 };

  return (
    <section className="di-hero" id="home">
      <div className="di-hero-copy">
        <motion.p
          className="di-eyebrow"
          initial={enter}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          Developer Intelligence
        </motion.p>

        <motion.h1
          initial={enter}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.07, ease: [0.22, 1, 0.36, 1] }}
        >
          Route developer work through a living MCP agent fabric.
        </motion.h1>

        <motion.p
          className="di-lead"
          initial={reduceMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.16 }}
        >
          Natural-language intent hits the orchestrator, which selects a
          specialist — salary, company, weather, general, or repository
          intelligence — then returns a traced answer for real developer
          workflows.
        </motion.p>

        <motion.ul
          className="di-hero-signals"
          initial={reduceMotion ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.65, delay: 0.24 }}
        >
          {HERO_SIGNALS.map((signal) => (
            <li key={signal}>{signal}</li>
          ))}
        </motion.ul>

        <motion.div
          className="di-hero-actions"
          initial={reduceMotion ? false : { opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.65, delay: 0.3 }}
        >
          <Link
            className="di-btn di-btn-primary"
            to={ORCHESTRATION_DEMO_HREF}
            aria-label="Try the live Developer Intelligence demo"
          >
            Try Live Demo
            <span className="di-btn-arrow" aria-hidden="true">
              →
            </span>
          </Link>
          <a
            className="di-btn di-btn-ghost"
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Open GitHub in a new tab"
          >
            GitHub
          </a>
        </motion.div>
      </div>

      <div className="di-hero-visual">
        <IntelligenceNetwork />
      </div>
    </section>
  );
}
