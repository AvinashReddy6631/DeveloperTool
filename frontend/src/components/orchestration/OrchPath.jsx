import { motion } from "motion/react";
import { useOrchestration } from "../../context/OrchestrationContext";
import { commandPathIndex, COMMAND_PATH } from "../../lib/orchestrationScene";
import { useOrchVis } from "./OrchVisContext";

export default function OrchPath() {
  const { phase } = useOrchestration();
  const vis = useOrchVis();
  const index = commandPathIndex(vis.play, phase);
  const failed = phase === "error" || vis.play === "error";

  return (
    <ol className={`orch-path${failed ? " is-fail" : ""}`} aria-label="Request path">
      {COMMAND_PATH.map((label, i) => {
        const isNow = i === index && phase !== "idle";
        const isLive = phase === "idle" ? i === 0 : i <= index;
        return (
          <motion.li
            key={label}
            className={`${isLive ? "is-live" : ""}${isNow ? " is-now" : ""}`}
            animate={{ opacity: isLive ? 1 : 0.38 }}
            transition={{ duration: 0.28 }}
          >
            <b>{String(i + 1).padStart(2, "0")}</b>
            <span>{label}</span>
          </motion.li>
        );
      })}
    </ol>
  );
}
