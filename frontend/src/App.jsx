import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";


  const API_URL = import.meta.env.VITE_API_URL;

const SESSION_STORAGE_KEY = "mcp_orchestrator_session_id";
const OPENROUTER_KEY_PATTERN = /^sk-or-[A-Za-z0-9_-]{8,}$/;

function isQuotaOrRateLimitError(message) {
  const normalizedMessage = String(message || "").toLowerCase();

  return (
    normalizedMessage.includes("429") ||
    normalizedMessage.includes("rate limit") ||
    normalizedMessage.includes("free-models-per-day") ||
    normalizedMessage.includes("request limit") ||
    normalizedMessage.includes("quota")
  );
}

function getOrCreateSessionId() {
  try {
    const existing = localStorage.getItem(SESSION_STORAGE_KEY);

    if (existing) {
      return existing;
    }

    const generated =
      typeof crypto !== "undefined" &&
      typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `session-${Date.now()}-${Math.random()
            .toString(36)
            .slice(2, 10)}`;

    localStorage.setItem(
      SESSION_STORAGE_KEY,
      generated
    );

    return generated;
  } catch (storageError) {
    console.warn(
      "Unable to access localStorage. Using an in-memory session ID.",
      storageError
    );

    return `session-${Date.now()}-${Math.random()
      .toString(36)
      .slice(2, 10)}`;
  }
}

function App() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [robotState, setRobotState] = useState("idle");
  const [greeting, setGreeting] = useState("");
  const [sessionId] = useState(getOrCreateSessionId);

  // BYOK / AI access state.
  // The personal API key is intentionally kept only in React memory.
  // It is never written to localStorage/sessionStorage.
  const [showAiAccess, setShowAiAccess] = useState(false);
  const [personalApiKey, setPersonalApiKey] = useState("");
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [apiKeyError, setApiKeyError] = useState("");
  const queryInputRef = useRef(null);
  const isPersonalApiKeyConnected = Boolean(personalApiKey);

  const [currentView, setCurrentView] = useState(() => {
    const hash = window.location.hash;
    if (hash === "#api") return "api";
    if (hash === "#documentation") return "docs";
    return "home";
  });

  useEffect(() => {
    const timer = setTimeout(() => {
      setGreeting("Hello! I'm your MCP Orchestrator.");
    }, 700);

    const onHashChange = () => {
      const hash = window.location.hash;
      if (hash === "#api") setCurrentView("api");
      else if (hash === "#documentation") setCurrentView("docs");
      else setCurrentView("home");
    };

    window.addEventListener("hashchange", onHashChange);

    return () => {
      clearTimeout(timer);
      window.removeEventListener("hashchange", onHashChange);
    };
  }, []);

  const connectPersonalApiKey = () => {
    const cleanKey = apiKeyInput.trim();

    if (!cleanKey) {
      setApiKeyError("Enter your OpenRouter API key to connect.");
      return;
    }

    if (!OPENROUTER_KEY_PATTERN.test(cleanKey)) {
      setApiKeyError(
        "Enter a valid OpenRouter API key. Keys normally start with sk-or-."
      );
      return;
    }

    setPersonalApiKey(cleanKey);
    setApiKeyInput("");
    setApiKeyError("");

    // Connected: close the setup dialog and return the user
    // directly to the main chat box.
    setShowAiAccess(false);

    window.requestAnimationFrame(() => {
      queryInputRef.current?.focus();
    });
  };

  const disconnectPersonalApiKey = () => {
    setPersonalApiKey("");
    setApiKeyInput("");
    setApiKeyError("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const cleanQuery = query.trim();

    if (!cleanQuery || loading) {
      return;
    }

    setLoading(true);
    setError("");
    setResponse(null);
    setRobotState("thinking");
    const usingPersonalApiKey = Boolean(personalApiKey);

    try {
      const result = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(usingPersonalApiKey
            ? { "X-OpenRouter-Key": personalApiKey }
            : {}),
        },
        body: JSON.stringify({
          query: cleanQuery,
          session_id: sessionId,
        }),
      });

      const data = await result.json().catch(() => null);
      const backendError =
        typeof data?.error === "string" ? data.error : "";

      if (!result.ok) {
        throw new Error(
          backendError || `Backend returned HTTP ${result.status}`
        );
      }

      if (data?.status !== "success") {
        throw new Error(
          backendError ||
            "The MCP Orchestrator could not process the request."
        );
      }

      setResponse(data);
      setRobotState("success");
    } catch (err) {
      const errorMessage = String(
        err?.message || ""
      );

      const isRateLimitError = isQuotaOrRateLimitError(errorMessage);

      if (isRateLimitError) {
        setError(
          usingPersonalApiKey
            ? "Your OpenRouter API key has reached its current AI usage limit. Please try again after the provider limit resets or connect another key."
            : "AI request limit completed for today. " +
              "Your MCP Orchestrator is working correctly, " +
              "but the free AI model quota has been reached. " +
              "Please try again after the daily limit resets."
        );
      } else {
        setError(
          errorMessage ||
            "Unable to connect to the MCP Orchestrator."
        );
      }

      setRobotState("error");
    } finally {
      setLoading(false);
    }
  };

  const handleNewQuestion = () => {
    setQuery("");
    setResponse(null);
    setError("");
    setRobotState("idle");
  };

  const handleSuggestion = (text) => {
    setQuery(text);
  };

  return (
    <div className="app">

      {/* Animated background */}
      <div className="background">
        <div className="gradient-orb orb-purple" />
        <div className="gradient-orb orb-blue" />
        <div className="gradient-orb orb-cyan" />

        <div className="grid-background" />

        <div className="scan-line" />
      </div>

      {/* Navigation */}
      <header className="navbar">

        <div className="brand">

          <img
            className="brand-logo"
            src="/mcp-orchestration-logo.jpeg"
            alt="MCP Orchestration"
          />

          <div className="brand-text">
            <strong>MCP Orchestrator</strong>
            <span>Multi-Agent Intelligence</span>
          </div>

        </div>

        <nav className="nav-links">
          <a
            className={currentView === "home" ? "active" : ""}
            href="#home"
          >
            Home
          </a>

          <a
            href="#agents"
            onClick={() => {
              setCurrentView("home");
              setTimeout(() => {
                document.getElementById("agents")?.scrollIntoView({
                  behavior: "smooth",
                  block: "start",
                });
              }, 0);
            }}
          >
            Agents
          </a>

          <a
            className={currentView === "api" ? "active" : ""}
            href="#api"
          >
            API
          </a>

          <a
            className={currentView === "docs" ? "active" : ""}
            href="#documentation"
          >
            Docs
          </a>
        </nav>

        <div className="navbar-actions">
          <button
            type="button"
            className={`ai-access-button ${
              isPersonalApiKeyConnected ? "connected" : ""
            }`}
            onClick={() => {
              setShowAiAccess(true);
              setApiKeyError("");
            }}
          >
            <span className="ai-access-dot" />
            AI Access
            {isPersonalApiKeyConnected && (
              <span className="ai-access-check">✓</span>
            )}
          </button>

          <div className="online-status">
            <span />
            Online
          </div>
        </div>

      </header>

      {showAiAccess && (
        <div
          className="ai-access-overlay"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setShowAiAccess(false);
          }}
        >
          <div
            className="ai-access-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="ai-access-title"
          >
            <div className="ai-access-modal-header">
              <div>
                <div className="ai-access-kicker">AI ACCESS</div>
                <h2 id="ai-access-title">AI Access</h2>
                <p>
                  Connect your own OpenRouter API key for this page session.
                </p>
              </div>
              <button
                type="button"
                className="ai-access-close"
                aria-label="Close AI access dialog"
                onClick={() => setShowAiAccess(false)}
              >
                ×
              </button>
            </div>

            <div className="ai-mode-card selected">
              {isPersonalApiKeyConnected ? (
                <>
                  <div className="ai-mode-topline">
                    <span className="ai-mode-badge byok">BYOK</span>
                    <span className="ai-mode-selected">✓ CONNECTED</span>
                  </div>
                  <h3>✓ Connected</h3>
                  <p>
                    Your OpenRouter key is active for all questions in this
                    page session.
                  </p>
                  <div className="ai-access-actions">
                    <button
                      type="button"
                      className="ai-disconnect-button"
                      onClick={disconnectPersonalApiKey}
                    >
                      Disconnect
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <h3>Use your own OpenRouter API key</h3>
                  <label className="ai-key-label" htmlFor="openrouter-key">
                    OPENROUTER API KEY
                  </label>
                  <div className="ai-key-input-wrap">
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
                  </div>
                  <div className="ai-access-actions">
                    <button
                      type="button"
                      className="ai-connect-button"
                      onClick={connectPersonalApiKey}
                    >
                      Connect
                    </button>
                  </div>
                </>
              )}
            </div>

            <div className="ai-access-security">
              <span className="security-icon">✓</span>
              <div>
                <strong>Session-only key handling</strong>
                <span>Your key is kept only in React memory.</span>
              </div>
            </div>

            {apiKeyError && (
              <div className="ai-access-message error">{apiKeyError}</div>
            )}
          </div>
        </div>
      )}

        <main className="main" id="home">

        {/* Badge */}
        <div className="hero-badge">
          <span>✦</span>
          Intelligent MCP Multi-Agent System
        </div>


        {/* Hero */}
        <section className="hero">

          <div className="hero-title-small">
            One interface.
          </div>

          <h1>
            Multiple intelligent{" "}
            <span>agents.</span>
          </h1>

          <p className="hero-description">
            Ask a question and let the MCP Orchestrator
            intelligently route your request to the right
            specialized agent.
          </p>

        </section>


        {/* Robot + Cube */}
        <section className="visual-section">

          <div
            className={`robot ${
              robotState === "thinking"
                ? "robot-thinking"
                : ""
            } ${
              robotState === "success"
                ? "robot-success"
                : ""
            } ${
              robotState === "error"
                ? "robot-error"
                : ""
            }`}
          >

            <div className="robot-antenna">
              <span />
            </div>

            <div className="robot-head">

              <div className="robot-ear left-ear" />
              <div className="robot-ear right-ear" />

              <div className="robot-face">

                <div className="robot-eyes">
                  <span />
                  <span />
                </div>

                <div className="robot-mouth">
                  {robotState === "error"
                    ? "!"
                    : robotState === "thinking"
                    ? "..."
                    : robotState === "success"
                    ? "✓"
                    : "•"}
                </div>

              </div>

            </div>

            <div className="robot-body">
              MCP
            </div>

            <div className="robot-arm left-arm" />
            <div className="robot-arm right-arm" />

          </div>


          <div className="cube-scene">

            <div className="cube-glow" />

            <div className="text-cube">

              <div className="cube-face front">
                MCP
              </div>

              <div className="cube-face back">
                MCP
              </div>

              <div className="cube-face right">
                MCP
              </div>

              <div className="cube-face left">
                MCP
              </div>

              <div className="cube-face top">
                MCP
              </div>

              <div className="cube-face bottom">
                MCP
              </div>

            </div>

          </div>

        </section>


        {/* Greeting */}
        <div
          className={`robot-greeting ${
            greeting ? "show" : ""
          }`}
        >
          <span>✦</span>
          {greeting ||
            "Your multi-agent system is ready."}
        </div>


        {/* Query */}
        <section className="query-section">

          <form
            className={`query-box ${
              loading ? "query-loading" : ""
            }`}
            onSubmit={handleSubmit}
          >

            <div className="query-icon">
              ✦
            </div>

            <input
              ref={queryInputRef}
              type="text"
              value={query}
              onChange={(event) =>
                setQuery(event.target.value)
              }
              placeholder="Ask your agents anything..."
              disabled={loading}
            />

            <button
              type="submit"
              disabled={!query.trim() || loading}
            >
              {loading ? (
                <>
                  <span className="button-spinner" />
                  Thinking
                </>
              ) : (
                <>
                  Ask
                  <span>→</span>
                </>
              )}
            </button>

          </form>


          <div className="query-hint">
            <span>MCP Engine</span>
            <span>Salary Agent</span>
            <span>Company Agent</span>
            <span>Weather Agent</span>
            <span>General Agent</span>
            {isPersonalApiKeyConnected ? (
              <span className="ai-key-status active">
                ✓ Using your OpenRouter key
              </span>
            ) : (
              <span className="ai-key-status">
                Demo AI access
              </span>
            )}
          </div>


          {/* Suggestions */}
          {!response && !loading && !error && (
            <div className="suggestions">

              <button
                onClick={() =>
                  handleSuggestion(
                    "Who is the highest paid employee at Google?"
                  )
                }
              >
                Highest paid employee
              </button>

              <button
                onClick={() =>
                  handleSuggestion(
                    "Analyze Google and tell me what roles exist."
                  )
                }
              >
                Company analysis
              </button>

              <button
                onClick={() =>
                  handleSuggestion(
                    "What roles are available at Google?"
                  )
                }
              >
                Available roles
              </button>

              <button
                onClick={() =>
                  handleSuggestion(
                    "What is the weather in Hyderabad?"
                  )
                }
              >
                Weather
              </button>

            </div>
          )}


          {/* Thinking */}
          {loading && (
            <div className="response-panel">

              <div className="response-header">

                <div className="response-agent">

                  <div className="response-icon thinking-icon">
                    ✦
                  </div>

                  <div>
                    <strong>
                      MCP Orchestrator
                    </strong>

                    <span>
                      Selecting specialized agents
                    </span>
                  </div>

                </div>

                <div className="thinking-status">
                  <span />
                  THINKING
                </div>

              </div>

              <div className="response-divider" />

              <div className="thinking-area">

                <div className="thinking-dots">
                  <span />
                  <span />
                  <span />
                </div>

                <p>
                  Routing your request through the
                  MCP agent system...
                </p>

              </div>

            </div>
          )}


          {/* Error */}
          {error && !loading && (
            <div className="response-panel error-panel">

              <div className="response-header">

                <div className="response-agent">

                  <div className="response-icon error-icon">
                    !
                  </div>

                  <div>
                    <strong>
                      MCP Orchestrator
                    </strong>

                    <span>
                      Request failed
                    </span>
                  </div>

                </div>

                <div className="error-status">
                  ERROR
                </div>

              </div>

              <div className="response-divider" />

              <p className="error-message">
                {error}
              </p>

              <button
                className="retry-button"
                onClick={() => {
                  setError("");
                  setRobotState("idle");
                }}
              >
                Try again →
              </button>

            </div>
          )}


          {/* Real answer */}
          {response && !loading && !error && (
            <div className="response-panel answer-panel">

              <div className="response-header">

                <div className="response-agent">

                  <div className="response-icon success-icon">
                    ✦
                  </div>

                  <div>
                    <strong>
                      MCP Orchestrator
                    </strong>

                    <span>
                      Response generated successfully
                    </span>
                  </div>

                </div>

                <div className="success-status">
                  <span />
                  COMPLETE
                </div>

              </div>


              <div className="response-divider" />


              {/* Question */}
              <div className="question-block">

                <span>
                  YOUR QUESTION
                </span>

                <p>
                  {query}
                </p>

              </div>


              {/* Answer */}
              <div className="answer-box">

                <div className="answer-label">
                  AGENT RESPONSE
                </div>

                <div className="answer-text">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      table: ({ node, ...props }) => (
                        <div className="markdown-table-wrapper">
                          <table {...props} />
                        </div>
                      ),
                      a: ({ node, ...props }) => (
                        <a
                          {...props}
                          target="_blank"
                          rel="noreferrer"
                        />
                      ),
                    }}
                  >
                    {response.answer || ""}
                  </ReactMarkdown>
                </div>

              </div>


              {/* Real MCP execution trace */}
              <div className="agent-information">

                <div className="information-title">
                  MCP EXECUTION TRACE
                </div>

                {response.execution_trace ? (
                  <>
                    <div className="agent-cards">

                      <div className="agent-card">
                        <div className="agent-card-icon">
                          ✦
                        </div>

                        <div>
                          <strong>
                            MCP Engine
                          </strong>

                          <span>
                            {response.execution_trace.orchestrator
                              ? `Decision: ${response.execution_trace.orchestrator}`
                              : "Orchestration"}
                          </span>
                        </div>
                      </div>

                      {(response.execution_trace.agents || []).map(
                        (agentName) => (
                          <div
                            className="agent-card"
                            key={agentName}
                          >
                            <div className="agent-card-icon">
                              {agentName === "salary_agent" ? "$" : "◈"}
                            </div>

                            <div>
                              <strong>
                                {agentName === "salary_agent"
                                  ? "Salary Agent"
                                  : agentName === "company_agent"
                                    ? "Company Agent"
                                    : agentName}
                              </strong>

                              <span>
                                Completed successfully
                              </span>
                            </div>
                          </div>
                        )
                      )}

                    </div>

                    {(response.execution_trace.mcp_calls || []).length > 0 && (
                      <div className="trace-tools">
                        {(response.execution_trace.mcp_calls || []).map(
                          (call, index) => (
                            <div
                              className="trace-tool"
                              key={`${call.tool}-${index}`}
                            >
                              <div className="trace-tool-main">
                                <span className="trace-check">✓</span>

                                <div>
                                  <strong>{call.tool}</strong>

                                  <span>
                                    {call.agent || "MCP Agent"}
                                  </span>
                                </div>
                              </div>

                              <div className="trace-tool-meta">
                                <span>{call.status}</span>

                                <span>
                                  {Number(call.execution_time || 0).toFixed(2)}s
                                </span>
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    )}

                    <div className="trace-summary">
                      <div>
                        <span>ORCHESTRATOR</span>
                        <strong>
                          {response.execution_trace.orchestrator || "—"}
                        </strong>
                      </div>

                      <div>
                        <span>AGENTS</span>
                        <strong>
                          {(response.execution_trace.agents || []).length}
                        </strong>
                      </div>

                      <div>
                        <span>MCP CALLS</span>
                        <strong>
                          {(response.execution_trace.mcp_calls || []).length}
                        </strong>
                      </div>

                      <div>
                        <span>TOTAL TRACE</span>
                        <strong>
                          {Number(
                            response.execution_trace.total_execution_time || 0
                          ).toFixed(2)}
                          s
                        </strong>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="agent-cards">
                    <div className="agent-card">
                      <div className="agent-card-icon">
                        ✦
                      </div>

                      <div>
                        <strong>MCP Engine</strong>
                        <span>Orchestration</span>
                      </div>
                    </div>

                    <div className="agent-card">
                      <div className="agent-card-icon">
                        $
                      </div>

                      <div>
                        <strong>Salary Agent</strong>
                        <span>Salary analysis</span>
                      </div>
                    </div>

                    <div className="agent-card">
                      <div className="agent-card-icon">
                        ◈
                      </div>

                      <div>
                        <strong>Company Agent</strong>
                        <span>Company analysis</span>
                      </div>
                    </div>
                  </div>
                )}

              </div>

      {currentView === "api" && (
        <main className="docs-page main" id="api">
          <section className="docs-hero">
            <div className="hero-badge">
              <span>✦</span>
              MCP Orchestrator API
            </div>
            <h1>Build with the orchestrator.</h1>
            <p>
              Send natural-language requests to the MCP Orchestrator and
              receive specialized-agent answers together with a detailed
              execution trace.
            </p>
          </section>

          <section className="docs-layout">
            <aside className="docs-sidebar">
              <a href="#api">Overview</a>
              <a href="#api-query">POST /query</a>
              <a href="#api-health">GET /health</a>
              <a href="#api-response">Response</a>
              <a href="#api-errors">Errors</a>
            </aside>

            <div className="docs-content">
              <section className="doc-section" id="api-query">
                <div className="doc-kicker">QUERY ENDPOINT</div>
                <div className="endpoint-card">
                  <span className="method-badge post">POST</span>
                  <code>/query</code>
                </div>
                <p>
                  Routes a user request to Salary, Company, Weather, or
                  multiple specialized agents.
                </p>

                <h3>Request body</h3>
                <pre className="code-block"><code>{`{
  "query": "What is the weather in Hyderabad?",
  "session_id": "session-123"
}`}</code></pre>

                <h3>cURL</h3>
                <pre className="code-block"><code>{`curl -X POST \\
  "$VITE_API_URL/query" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "What is the weather in Hyderabad?",
    "session_id": "session-123"
  }'`}</code></pre>
              </section>

              <section className="doc-section" id="api-health">
                <div className="doc-kicker">HEALTH CHECK</div>
                <div className="endpoint-card">
                  <span className="method-badge get">GET</span>
                  <code>/health</code>
                </div>
                <p>
                  Verifies that the FastAPI service is running and the
                  database connection is available.
                </p>
                <pre className="code-block"><code>{`{
  "status": "healthy",
  "service": "MCP Agent Orchestrator",
  "database": "connected"
}`}</code></pre>
              </section>

              <section className="doc-section" id="api-response">
                <div className="doc-kicker">RESPONSE SHAPE</div>
                <pre className="code-block"><code>{`{
  "request_id": "uuid",
  "status": "success",
  "answer": "Generated answer...",
  "execution_time": 1.24,
  "error": null,
  "execution_trace": {
    "orchestrator": "WEATHER",
    "agents": ["weather_agent"],
    "mcp_calls": [],
    "final_status": "success"
  }
}`}</code></pre>

                <div className="api-field-grid">
                  <div>
                    <strong>request_id</strong>
                    <span>Unique request identifier.</span>
                  </div>
                  <div>
                    <strong>status</strong>
                    <span>Success or error state.</span>
                  </div>
                  <div>
                    <strong>answer</strong>
                    <span>Final generated response.</span>
                  </div>
                  <div>
                    <strong>execution_trace</strong>
                    <span>Routing, agents, tools, and timings.</span>
                  </div>
                </div>
              </section>

              <section className="doc-section" id="api-errors">
                <div className="doc-kicker">ERRORS</div>
                <div className="status-grid">
                  <div>
                    <span>400</span>
                    <p>Invalid or empty request.</p>
                  </div>
                  <div>
                    <span>500</span>
                    <p>Unexpected backend failure.</p>
                  </div>
                  <div>
                    <span>429</span>
                    <p>Upstream AI rate limit.</p>
                  </div>
                </div>
              </section>
            </div>
          </section>
        </main>
      )}


      {currentView === "docs" && (
        <main className="docs-page main" id="documentation">
          <section className="docs-hero">
            <div className="hero-badge">
              <span>✦</span>
              Developer Documentation
            </div>
            <h1>How the MCP system works.</h1>
            <p>
              Understand the architecture, specialized agents, persistent
              session memory, and request lifecycle behind the project.
            </p>
          </section>

          <section className="architecture-panel">
            <div className="architecture-flow">
              <div className="flow-node primary"><span>01</span>React UI</div>
              <div className="flow-arrow">→</div>
              <div className="flow-node"><span>02</span>FastAPI</div>
              <div className="flow-arrow">→</div>
              <div className="flow-node"><span>03</span>MCP Orchestrator</div>
              <div className="flow-arrow">→</div>
              <div className="flow-node"><span>04</span>Specialized Agents</div>
            </div>
            <div className="architecture-subflow">
              <span>PostgreSQL memory</span>
              <span>•</span>
              <span>MCP tool execution</span>
              <span>•</span>
              <span>Execution trace</span>
            </div>
          </section>

          <section className="docs-layout">
            <aside className="docs-sidebar">
              <a href="#documentation">Overview</a>
              <a href="#architecture">Architecture</a>
              <a href="#agents-docs">Agents</a>
              <a href="#sessions">Sessions</a>
              <a href="#flow">Request Flow</a>
            </aside>

            <div className="docs-content">
              <section className="doc-section" id="architecture">
                <div className="doc-kicker">ARCHITECTURE</div>
                <h2>One interface, multiple specialized agents.</h2>
                <p>
                  The frontend sends a natural-language request to FastAPI.
                  The orchestrator resolves context, chooses the route,
                  invokes specialized agents, and returns the answer plus
                  observability data.
                </p>

                <div className="docs-card-grid">
                  <div>
                    <strong>MCP Engine</strong>
                    <span>Routes and coordinates execution.</span>
                  </div>
                  <div>
                    <strong>Salary Agent</strong>
                    <span>Compensation and salary analysis.</span>
                  </div>
                  <div>
                    <strong>Company Agent</strong>
                    <span>Companies, employees, and roles.</span>
                  </div>
                  <div>
                    <strong>Weather Agent</strong>
                    <span>Location resolution and live weather.</span>
                  </div>
                </div>
              </section>

              <section className="doc-section" id="agents-docs">
                <div className="doc-kicker">SPECIALIZED AGENTS</div>
                <h2>Current capabilities</h2>

                <div className="agent-doc-list">
                  <div>
                    <span className="agent-doc-icon">$</span>
                    <div>
                      <strong>Salary Agent</strong>
                      <p>
                        Salary statistics, highest-paid employees,
                        comparisons, and compensation analysis.
                      </p>
                    </div>
                  </div>

                  <div>
                    <span className="agent-doc-icon">◈</span>
                    <div>
                      <strong>Company Agent</strong>
                      <p>
                        Company analysis, employees, workforce,
                        and available roles.
                      </p>
                    </div>
                  </div>

                  <div>
                    <span className="agent-doc-icon">☁</span>
                    <div>
                      <strong>Weather Agent</strong>
                      <p>
                        Current weather, humidity, temperature, wind,
                        and geocoded location resolution.
                      </p>
                    </div>
                  </div>
                </div>
              </section>

              <section className="doc-section" id="sessions">
                <div className="doc-kicker">SESSION MEMORY</div>
                <h2>Context that survives backend restarts.</h2>
                <p>
                  Each conversation has a session ID. Conversation turns are
                  persisted in PostgreSQL so follow-ups can use earlier context
                  even after the backend restarts.
                </p>

                <pre className="code-block"><code>{`session_id
    ↓
PostgreSQL conversations
    ↓
recent context
    ↓
follow-up resolver
    ↓
specialized agent`}</code></pre>
              </section>

              <section className="doc-section" id="flow">
                <div className="doc-kicker">REQUEST FLOW</div>
                <h2>From question to traceable answer.</h2>

                <ol className="flow-list">
                  <li>
                    <strong>Receive</strong>
                    <span>FastAPI validates the request and creates a request ID.</span>
                  </li>
                  <li>
                    <strong>Resolve</strong>
                    <span>The orchestrator checks routing and conversation context.</span>
                  </li>
                  <li>
                    <strong>Route</strong>
                    <span>A specialized agent is selected.</span>
                  </li>
                  <li>
                    <strong>Execute</strong>
                    <span>The agent runs its MCP tools and services.</span>
                  </li>
                  <li>
                    <strong>Trace</strong>
                    <span>The answer includes agents, tools, and timing.</span>
                  </li>
                </ol>
              </section>
            </div>
          </section>
        </main>
      )}
      {/* Footer */}
              <div className="response-footer">

                <div className="execution-info">

                  <span>
                    REQUEST
                  </span>

                  <strong>
                    {response.request_id
                      ? response.request_id.slice(
                          0,
                          8
                        )
                      : "—"}
                  </strong>

                </div>


                <div className="execution-info">

                  <span>
                    EXECUTION
                  </span>

                  <strong>
                    {response.execution_time
                      ? `${response.execution_time.toFixed(
                          2
                        )}s`
                      : "—"}
                  </strong>

                </div>


                <button
                  onClick={
                    handleNewQuestion
                  }
                >
                  New question →
                </button>

              </div>

            </div>
          )}

        </section>


        {/* Agents */}
        <section
          className="agents-section"
          id="agents"
        >

          <div className="agent-feature-card">

            <span className="agent-status">
              ● READY
            </span>

            <div className="feature-icon">
              $
            </div>

            <h3>
              Salary Agent
            </h3>

            <p>
              Analyzes employee compensation,
              salaries and rankings.
            </p>

          </div>


          <div className="agent-feature-card">

            <span className="agent-status">
              ● READY
            </span>

            <div className="feature-icon">
              ◈
            </div>

            <h3>
              Company Agent
            </h3>

            <p>
              Analyzes companies, employees and
              available roles.
            </p>

          </div>


          <div className="agent-feature-card">

            <span className="agent-status">
              ● READY
            </span>

            <div className="feature-icon weather-feature-icon">
              ☁
            </div>

            <h3>
              Weather Agent
            </h3>

            <p>
              Resolves locations and retrieves
              current weather data.
            </p>

          </div>


          <div className="agent-feature-card">

            <span className="agent-status">
              ● READY
            </span>

            <div className="feature-icon">
              ✦
            </div>

            <h3>
              MCP Engine
            </h3>

            <p>
              Routes requests and coordinates
              specialized agents.
            </p>

          </div>

        </section>

      </main>


      {/* Footer */}
      <footer className="footer">

        <span>
          MCP Agent Orchestrator
        </span>

        <span>
          Built with FastAPI · PostgreSQL · MCP
        </span>

      </footer>

    </div>
  );
}

export default App;
