import { SUGGESTIONS } from "../../lib/orchestrationAgents";
import { useOrchestration } from "../../context/OrchestrationContext";
import OrchLocked from "./OrchLocked";

export default function OrchComposer() {
  const {
    query,
    setQuery,
    loading,
    handleSubmit,
    queryInputRef,
    handleSuggestion,
    phase,
    response,
    error,
    aiLocked,
    user,
    setShowAccount,
  } = useOrchestration();

  const showSuggestions = !response && !loading && !error && !aiLocked;
  const locked = aiLocked && !loading;

  return (
    <section className="orch-composer" aria-label="Ask Developer Intelligence" id="agents">
      <div className="orch-composer-head">
        <div>
          <p className="orch-kicker">Ask</p>
          <h2>Ask Developer Intelligence</h2>
        </div>
      </div>

      {locked && <OrchLocked kind="ai" />}
      {!user && (
        <p className="orch-usage-note">
          Sign in to ask a question. Free plan limits are stored on your account.
          <button
            type="button"
            className="orch-btn ghost"
            onClick={() => setShowAccount(true)}
          >
            Account
          </button>
        </p>
      )}
      <form onSubmit={handleSubmit}>
        <label className="orch-sr-only" htmlFor="orch-query">
          Ask anything or paste a repository URL
        </label>
        <div className="orch-search-shell">
          <div className="orch-composer-row">
            <input
              id="orch-query"
              ref={queryInputRef}
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Ask anything or paste a repository URL..."
              disabled={loading || locked || !user}
              autoComplete="off"
              enterKeyHint="send"
            />
            <button
              type="submit"
              className="orch-btn"
              disabled={!query.trim() || loading || locked || !user}
            >
              {loading ? "Analyzing…" : locked ? "Locked" : "Ask"}
              <span className="orch-btn-arrow" aria-hidden="true">
                →
              </span>
            </button>
          </div>
        </div>
      </form>

      {showSuggestions && (
        <div className="orch-suggestions">
          {SUGGESTIONS.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => handleSuggestion(item.text)}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}

      <p className="orch-sr-only" aria-live="polite">
        {phase === "thinking"
          ? "Analyzing your request"
          : phase === "success"
            ? "Response ready"
            : phase === "error"
              ? "Request failed"
              : "Ready"}
      </p>
    </section>
  );
}
