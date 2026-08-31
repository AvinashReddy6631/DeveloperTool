import { AnimatePresence, motion } from "motion/react";
import { useOrchestration } from "../../context/OrchestrationContext";
import UxState from "../ux/UxState";

export default function AiAccessModal() {
  const {
    showAiAccess,
    setShowAiAccess,
    isPersonalApiKeyConnected,
    apiKeyInput,
    setApiKeyInput,
    apiKeyError,
    setApiKeyError,
    connectPersonalApiKey,
    disconnectPersonalApiKey,
  } = useOrchestration();

  return (
    <AnimatePresence>
      {showAiAccess && (
    <motion.div
      className="orch-overlay"
      role="presentation"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) setShowAiAccess(false);
      }}
    >
      <motion.div
        className="orch-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ai-access-title"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 8 }}
      >
        <div className="orch-modal-head">
          <div>
            <p className="orch-kicker">AI access</p>
            <h2 id="ai-access-title">AI Access</h2>
            <p>Connect your own OpenRouter API key for this page session.</p>
          </div>
          <button
            type="button"
            className="orch-icon-btn"
            aria-label="Close AI access dialog"
            onClick={() => setShowAiAccess(false)}
          >
            ×
          </button>
        </div>

        {isPersonalApiKeyConnected ? (
          <div className="orch-modal-card">
            <p className="orch-kicker">BYOK · connected</p>
            <h3>Connected</h3>
            <p>
              Your OpenRouter key is active for all questions in this page
              session.
            </p>
            <button type="button" className="orch-btn ghost" onClick={disconnectPersonalApiKey}>
              Disconnect
            </button>
          </div>
        ) : (
          <div className="orch-modal-card">
            <h3>Use your own OpenRouter API key</h3>
            <label className="orch-label" htmlFor="openrouter-key">
              OpenRouter API key
            </label>
            <input
              id="openrouter-key"
              type="password"
              value={apiKeyInput}
              onChange={(event) => {
                setApiKeyInput(event.target.value);
                setApiKeyError("");
              }}
              placeholder="Paste your API key here"
              autoComplete="off"
              spellCheck="false"
            />
            <button type="button" className="orch-btn" onClick={connectPersonalApiKey}>
              Connect
            </button>
          </div>
        )}

        <p className="orch-secure">
          Session-only key handling. Your key is kept only in React memory.
        </p>
        {apiKeyError && (
          <UxState compact kind="invalid" body={apiKeyError} />
        )}
      </motion.div>
    </motion.div>
      )}
    </AnimatePresence>
  );
}
