export default function DocumentationView() {
  return (
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
  );
}
