import { useEffect, useState } from "react";
import "./App.css";

const API_URL =
  "https://mcporchestrator-production-9fa8.up.railway.app";

function App() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [robotState, setRobotState] = useState("idle");
  const [greeting, setGreeting] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => {
      setGreeting("Hello! I'm your MCP Orchestrator.");
    }, 700);

    return () => clearTimeout(timer);
  }, []);

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

    try {
      const result = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: cleanQuery,
        }),
      });

      if (!result.ok) {
        throw new Error(
          `Backend returned HTTP ${result.status}`
        );
      }

      const data = await result.json();

      if (data.status !== "success") {
        throw new Error(
          data.error || "The MCP agent could not process the request."
        );
      }

      setResponse(data);
      setRobotState("success");
    } catch (err) {
      console.error("MCP request failed:", err);

      setError(
        err.message ||
          "Unable to connect to the MCP Orchestrator."
      );

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

          <div className="brand-logo">
            MCP
          </div>

          <div className="brand-text">
            <strong>MCP Orchestrator</strong>
            <span>Multi-Agent Intelligence</span>
          </div>

        </div>

        <nav className="nav-links">
          <a href="#home">Home</a>
          <a href="#agents">Agents</a>
          <a href="#api">API</a>
          <a href="#documentation">Docs</a>
        </nav>

        <div className="online-status">
          <span />
          Online
        </div>

      </header>


      {/* Main */}
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
            MCP Engine · Salary Agent · Company Agent
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
                  {response.answer}
                </div>

              </div>


              {/* Agent information */}
              <div className="agent-information">

                <div className="information-title">
                  MCP EXECUTION
                </div>

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
                        Orchestration
                      </span>
                    </div>

                  </div>


                  <div className="agent-card">

                    <div className="agent-card-icon">
                      $
                    </div>

                    <div>
                      <strong>
                        Salary Agent
                      </strong>

                      <span>
                        Salary analysis
                      </span>
                    </div>

                  </div>


                  <div className="agent-card">

                    <div className="agent-card-icon">
                      ◈
                    </div>

                    <div>
                      <strong>
                        Company Agent
                      </strong>

                      <span>
                        Company analysis
                      </span>
                    </div>

                  </div>

                </div>

              </div>


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