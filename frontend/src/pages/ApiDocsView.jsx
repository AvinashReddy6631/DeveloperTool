export default function ApiDocsView() {
  return (
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
  );
}
