import { AnimatePresence, motion } from "motion/react";
import { useState, useMemo } from "react";
import { useOrchestration } from "../../context/OrchestrationContext";
import { formatAgentName } from "../../lib/orchestrationAgents";
import OrchEmpty from "./OrchEmpty";
import OrchError from "./OrchError";
import OrchAnalysisDashboard from "./OrchAnalysisDashboard";
import OrchLoading from "./OrchLoading";
import OrchMarkdown from "./OrchMarkdown";

const fade = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.28 },
};

export default function OrchWorkspace() {
  const { phase, response, submittedQuery, handleNewQuestion } = useOrchestration();
  const [showTrace, setShowTrace] = useState(false);
  const agent = response?.agent || response?.execution_trace?.agents?.[0];

  const answerElement = useMemo(() => {
    if (!response?.answer) return <OrchMarkdown>{""}</OrchMarkdown>;
    try {
      const parsed = JSON.parse(response.answer);
      if (parsed && typeof parsed === "object" && (parsed.findings || parsed.total_findings !== undefined || parsed.status)) {
        return <OrchAnalysisDashboard data={parsed} />;
      }
    } catch (e) {
      // Not JSON, fallback to markdown
    }
    return <OrchMarkdown>{response.answer}</OrchMarkdown>;
  }, [response?.answer]);

  return (
    <section className="orch-workspace" aria-label="Answer">
      <AnimatePresence mode="sync">
      {phase === "idle" && (
        <motion.div key="empty" {...fade}>
          <OrchEmpty />
        </motion.div>
      )}
      {phase === "thinking" && (
        <motion.div key="load" {...fade}>
          <OrchLoading />
        </motion.div>
      )}
      {phase === "error" && (
        <motion.div key="fail" {...fade}>
          <OrchError />
        </motion.div>
      )}
      {phase === "success" && response && (
        <motion.article key="answer" className="orch-answer is-arrive" {...fade}>
          <div className="orch-question">
            <span>Question</span>
            <p>{submittedQuery}</p>
          </div>
          <h3>Answer</h3>
          {answerElement}
          <footer className="orch-answer-foot">
            <div>
              <span>Agent</span>
              <strong>{formatAgentName(agent)}</strong>
            </div>
            <div>
              <span>Request ID</span>
              <strong>
                {response.request_id ? response.request_id.slice(0, 8) : "—"}
              </strong>
            </div>
            <div>
              <span>Execution</span>
              <strong>
                {response.execution_time
                  ? `${response.execution_time.toFixed(2)}s`
                  : "—"}
              </strong>
            </div>
            <button
              type="button"
              className="orch-btn ghost"
              onClick={() => setShowTrace((value) => !value)}
            >
              {showTrace ? "Hide trace" : "View trace"}
            </button>
            <button type="button" className="orch-btn ghost" onClick={handleNewQuestion}>
              New question
            </button>
          </footer>
          {showTrace && response.execution_trace ? (
            <pre className="orch-trace">{JSON.stringify(response.execution_trace, null, 2)}</pre>
          ) : null}
        </motion.article>
      )}
      </AnimatePresence>
    </section>
  );
}
