import { useState } from "react";
import UxState from "../ux/UxState";

export default function OrchAnalysisDashboard({ data }) {
  const [showRaw, setShowRaw] = useState(false);

  if (!data || typeof data !== "object") {
    return <p>Invalid analysis data.</p>;
  }

  const {
    status,
    total_findings,
    findings = [],
    positive_findings = [],
    gaps = [],
    group_results = [],
    repository_metadata,
    error_message
  } = data;

  const getSeverityLabel = (severity) => {
    switch (severity?.toUpperCase()) {
      case "P1": return "CRITICAL";
      case "P2": return "HIGH";
      case "P3": return "MEDIUM";
      case "P4": return "LOW";
      default: return severity;
    }
  };

  const getStatusMessage = () => {
    if (status === "error") {
      return { kind: "error", title: "Analysis Failed", body: error_message || "GitHub repository analysis could not be completed." };
    }
    if (status === "partial") {
      return { kind: "warning", title: "Partial Analysis", body: "Some repository analysis operations could not be completed." };
    }
    if (status === "success") {
      return { kind: "success", title: "Analysis Complete", body: "" };
    }
    return { kind: "info", title: "Analysis Status", body: status || "Unknown" };
  };

  const statusMsg = getStatusMessage();
  const displayTotalFindings = total_findings !== undefined ? total_findings : findings.length;

  // Calculate summary counts
  const categoryCounts = {};
  findings.forEach((f) => {
    const cat = f.category || "OTHER";
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  });

  return (
    <div className="orch-analysis-dashboard" style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
      
      {/* HEADER & STATUS */}
      <div className="orch-dashboard-header">
        <p className="orch-kicker">Repository Analysis</p>
        <UxState compact kind={statusMsg.kind} title={statusMsg.title} body={statusMsg.body} />
        
        {repository_metadata && (
          <div style={{ marginTop: "1rem", padding: "1rem", background: "rgba(255, 255, 255, 0.05)", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.1)" }}>
            <h4 style={{ margin: "0 0 0.5rem 0" }}>Repository</h4>
            <div style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>{repository_metadata.name || "Unknown"}</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", color: "var(--orch-text-muted, #a0a0a0)", fontSize: "0.9rem" }}>
              <span>Branch:<br/><strong style={{ color: "#fff" }}>{repository_metadata.branch || "main"}</strong></span>
              <span>Language:<br/><strong style={{ color: "#fff" }}>{repository_metadata.language || "Unknown"}</strong></span>
              <span>Stars:<br/><strong style={{ color: "#fff" }}>{repository_metadata.stars ?? 0}</strong></span>
              <span>Forks:<br/><strong style={{ color: "#fff" }}>{repository_metadata.forks ?? 0}</strong></span>
              <span>Issues:<br/><strong style={{ color: "#fff" }}>{repository_metadata.issues ?? 0}</strong></span>
              <span>License:<br/><strong style={{ color: "#fff" }}>{repository_metadata.license || "Not specified"}</strong></span>
            </div>
          </div>
        )}
      </div>

      {/* SUMMARY */}
      {(displayTotalFindings > 0 || status === "success") && (
        <div style={{ border: "1px solid rgba(255, 255, 255, 0.1)", padding: "1.5rem", borderRadius: "8px" }}>
          <h4 style={{ margin: "0 0 1rem 0" }}>ANALYSIS SUMMARY</h4>
          <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
            <div>
              <div style={{ fontSize: "2rem", fontWeight: "bold" }}>{displayTotalFindings}</div>
              <div style={{ color: "var(--orch-text-muted, #a0a0a0)", fontSize: "0.9rem" }}>Findings</div>
            </div>
            {Object.entries(categoryCounts).map(([cat, count]) => (
              <div key={cat}>
                <div style={{ fontSize: "2rem", fontWeight: "bold" }}>{count}</div>
                <div style={{ color: "var(--orch-text-muted, #a0a0a0)", fontSize: "0.9rem", textTransform: "capitalize" }}>{cat.toLowerCase()}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* FINDINGS EMPTY STATE */}
      {findings.length === 0 && status !== "error" && (
        <UxState compact kind="success" title="No issues found" body="The repository analysis didn't find any issues." />
      )}

      {/* FINDINGS CARDS */}
      {findings.length > 0 && (
        <div>
          <h4 style={{ margin: "0 0 1rem 0" }}>Findings</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {findings.map((f, i) => (
              <div key={i} style={{ border: "1px solid rgba(255, 255, 255, 0.1)", padding: "1.5rem", borderRadius: "8px", background: "rgba(0, 0, 0, 0.2)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem", marginBottom: "1rem" }}>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "center" }}>
                    {f.category && (
                      <span style={{ padding: "0.2rem 0.6rem", background: "rgba(255, 255, 255, 0.1)", borderRadius: "4px", fontSize: "0.75rem", fontWeight: "bold", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                        {f.category}
                      </span>
                    )}
                    {f.severity && (
                      <span style={{ padding: "0.2rem 0.6rem", background: "rgba(255, 100, 100, 0.1)", color: "#ff8888", borderRadius: "4px", fontSize: "0.75rem", fontWeight: "bold", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                        {f.severity} • {getSeverityLabel(f.severity)}
                      </span>
                    )}
                  </div>
                </div>

                <h5 style={{ fontSize: "1.1rem", margin: "0 0 1rem 0", lineHeight: "1.4" }}>{f.title}</h5>

                <div style={{ display: "flex", flexWrap: "wrap", gap: "2rem", marginBottom: "1.5rem", color: "var(--orch-text-muted, #a0a0a0)", fontSize: "0.9rem" }}>
                  <div>
                    <span style={{ display: "block", marginBottom: "0.2rem" }}>File</span>
                    <strong style={{ color: "#fff", wordBreak: "break-all" }}>{f.file || "Unknown"}</strong>
                  </div>
                  <div>
                    <span style={{ display: "block", marginBottom: "0.2rem" }}>Lines</span>
                    <strong style={{ color: "#fff" }}>
                      {!f.line_start && !f.line_end ? "Unknown" :
                        f.line_start === f.line_end ? f.line_start : `${f.line_start}–${f.line_end}`}
                    </strong>
                  </div>
                  {f.confidence && (
                    <div>
                      <span style={{ display: "block", marginBottom: "0.2rem" }}>Confidence</span>
                      <strong style={{ color: "#fff" }}>{f.confidence}</strong>
                    </div>
                  )}
                </div>

                {f.evidence && (
                  <div style={{ marginBottom: "1.5rem" }}>
                    <div style={{ fontSize: "0.9rem", color: "var(--orch-text-muted, #a0a0a0)", marginBottom: "0.5rem" }}>Evidence</div>
                    <pre style={{ margin: 0, padding: "1rem", background: "rgba(255, 255, 255, 0.03)", borderRadius: "4px", fontSize: "0.85rem", overflowX: "auto", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                      {f.evidence}
                    </pre>
                  </div>
                )}
                
                {f.problem && (
                  <div style={{ marginBottom: "1rem" }}>
                    <div style={{ fontSize: "0.9rem", color: "var(--orch-text-muted, #a0a0a0)", marginBottom: "0.2rem" }}>Problem</div>
                    <p style={{ margin: 0, color: "#e0e0e0", fontSize: "0.95rem", lineHeight: "1.5" }}>{f.problem}</p>
                  </div>
                )}
                
                {f.impact && (
                  <div style={{ marginBottom: "1rem" }}>
                    <div style={{ fontSize: "0.9rem", color: "var(--orch-text-muted, #a0a0a0)", marginBottom: "0.2rem" }}>Impact</div>
                    <p style={{ margin: 0, color: "#e0e0e0", fontSize: "0.95rem", lineHeight: "1.5" }}>{f.impact}</p>
                  </div>
                )}
                
                {f.recommendation && (
                  <div>
                    <div style={{ fontSize: "0.9rem", color: "var(--orch-text-muted, #a0a0a0)", marginBottom: "0.2rem" }}>Recommendation</div>
                    <p style={{ margin: 0, color: "#e0e0e0", fontSize: "0.95rem", lineHeight: "1.5" }}>{f.recommendation}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* POSITIVE FINDINGS */}
      {positive_findings.length > 0 && (
        <div>
          <h4 style={{ margin: "0 0 1rem 0" }}>## Positive Findings</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {positive_findings.map((pf, i) => (
              <div key={i} style={{ border: "1px solid rgba(136, 255, 136, 0.2)", padding: "1.5rem", borderRadius: "8px", background: "rgba(136, 255, 136, 0.05)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem", color: "#88ff88", fontWeight: "bold" }}>
                  ✓ Positive Finding
                </div>
                <div style={{ fontWeight: "bold", marginBottom: "0.5rem", fontSize: "1.1rem" }}>{pf.file}</div>
                {pf.evidence && <div style={{ marginBottom: "0.8rem", fontSize: "0.95rem", color: "#e0e0e0", lineHeight: "1.5" }}>{pf.evidence}</div>}
                {pf.explanation && (
                  <div>
                    <div style={{ fontSize: "0.9rem", color: "rgba(136, 255, 136, 0.7)", marginBottom: "0.2rem" }}>Explanation</div>
                    <div style={{ fontSize: "0.95rem", color: "#e0e0e0", lineHeight: "1.5" }}>{pf.explanation}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* GAPS */}
      {gaps.length > 0 && (
        <div>
          <h4 style={{ margin: "0 0 1rem 0" }}>## Architecture / Repository Gaps</h4>
          <div style={{ border: "1px solid rgba(255, 255, 255, 0.1)", padding: "1.5rem", borderRadius: "8px", background: "rgba(0, 0, 0, 0.2)" }}>
            <ul style={{ paddingLeft: "1.5rem", margin: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {gaps.map((gap, i) => (
                <li key={i} style={{ color: "#d0d0d0", lineHeight: "1.5" }}>{gap}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* GROUP RESULTS */}
      {group_results.length > 0 && (
        <div>
          <h4 style={{ margin: "0 0 1rem 0" }}>## Findings by Category</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {group_results.map((group, i) => (
              <details key={i} style={{ border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "8px", padding: "0.5rem 1rem", background: "rgba(255, 255, 255, 0.02)" }}>
                <summary style={{ cursor: "pointer", fontWeight: "bold", padding: "0.5rem 0", listStyle: "none", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ color: "var(--orch-primary, #7e57c2)" }}>▶</span>
                  {group.category || "Group"}
                </summary>
                <ul style={{ paddingLeft: "1.5rem", margin: "0.5rem 0 1rem 0", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {group.findings?.map((fTitle, j) => (
                    <li key={j} style={{ color: "#d0d0d0", lineHeight: "1.5" }}>{fTitle}</li>
                  ))}
                </ul>
              </details>
            ))}
          </div>
        </div>
      )}

      {/* RAW JSON FALLBACK */}
      <div style={{ marginTop: "1rem", paddingTop: "2rem", borderTop: "1px solid rgba(255, 255, 255, 0.1)" }}>
        <button type="button" className="orch-btn ghost" onClick={() => setShowRaw(!showRaw)}>
          {showRaw ? "Hide Raw JSON" : "View Raw JSON"}
        </button>
        {showRaw && (
          <pre style={{ marginTop: "1rem", padding: "1rem", background: "rgba(0, 0, 0, 0.5)", borderRadius: "8px", overflowX: "auto", fontSize: "0.85rem", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
