import { motion } from "motion/react";
import { useMemo } from "react";
import { useOrchestration } from "../../context/OrchestrationContext";
import {
  asList,
  isDetectedList,
  REPO_STAGES,
  repoStageState,
} from "../../lib/repoOverview";
import UxState from "../ux/UxState";
import { classifyUxKind } from "../../lib/uxStates";
import OrchMarkdown from "./OrchMarkdown";
import OrchAnalysisDashboard from "./OrchAnalysisDashboard";
import OrchLocked from "./OrchLocked";

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString();
}

function Metric({ label, value }) {
  return (
    <div className="orch-repo-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ChipList({ items, empty }) {
  const list = asList(items);
  if (list.length === 0) {
    return <p className="orch-note">{empty}</p>;
  }
  return (
    <ul className="orch-repo-chips">
      {list.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export default function OrchRepository() {
  const {
    githubProfile,
    setGithubProfile,
    githubRepos,
    isFetchingRepos,
    githubError,
    repoOverviews,
    fetchingOverviewFor,
    selectedRepoFullName,
    setSelectedRepoFullName,
    analyzingRepoUrl,
    loading,
    phase,
    error,
    submittedQuery,
    response,
    handleLoadRepos,
    handleViewOverview,
    handleAnalyzeRepo,
    aiLocked,
    repoLocked,
  } = useOrchestration();

  const selected =
    githubRepos.find((repo) => repo.full_name === selectedRepoFullName) || null;
  const overview = selected ? repoOverviews[selected.full_name] : null;
  const scanning = Boolean(
    selected && fetchingOverviewFor === selected.full_name
  );
  const analyzing = Boolean(
    selected && loading && analyzingRepoUrl === selected.url
  );
  const analysisReady = Boolean(
    selected &&
      phase === "success" &&
      submittedQuery.includes(selected.url) &&
      response?.answer
  );
  const analysisError = Boolean(
    selected && phase === "error" && submittedQuery.includes(selected.url)
  );
  const stage = repoStageState({
    selected,
    scanning,
    overview,
    analyzing,
    analysisReady,
    analysisError,
  });
  const showScan =
    overview && !overview.isHidden && (overview.error || overview.status === "success");

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
    <section className="orch-repo" id="repository" aria-label="Repository intelligence">
      <div className="orch-panel-head">
        <div>
          <p className="orch-kicker">Repository intelligence</p>
          <h2>Evidence workspace for GitHub repositories.</h2>
        </div>
      </div>
      <p className="orch-note">
        Uses the existing profile list, overview scan, and developer-agent
        analysis. No extra backend calls.
      </p>

      <ol className="orch-repo-flow">
        {REPO_STAGES.map((label, i) => (
          <li
            key={label}
            className={`${i <= stage.index ? "is-live" : ""}${i === stage.index ? " is-now" : ""}`}
          >
            {label}
          </li>
        ))}
      </ol>

      <form className="orch-repo-form" onSubmit={handleLoadRepos}>
        <label className="orch-sr-only" htmlFor="orch-github">
          GitHub profile URL
        </label>
        <input
          id="orch-github"
          type="text"
          placeholder="https://github.com/username"
          value={githubProfile}
          onChange={(event) => setGithubProfile(event.target.value)}
          disabled={isFetchingRepos || loading}
        />
        <button
          type="submit"
          className="orch-btn ghost"
          disabled={!githubProfile.trim() || isFetchingRepos || loading}
        >
          {isFetchingRepos ? "Scanning profile…" : "Load repositories"}
        </button>
      </form>
      {githubError && (
        <UxState
          compact
          kind={classifyUxKind(githubError)}
          body={githubError}
        />
      )}

      <div className="orch-repo-shell">
        <aside className="orch-repo-catalog" aria-label="Repository catalog">
          <p className="orch-kicker">Catalog</p>
          {isFetchingRepos && (
            <UxState
              compact
              kind="loading"
              title="Loading public repositories."
              body="Contacting the existing GitHub catalog endpoint."
            />
          )}
          {!isFetchingRepos && githubRepos.length === 0 && !githubError && (
            <UxState
              compact
              kind="empty"
              title="No catalog yet."
              body="Load a GitHub profile to list public repositories."
            />
          )}
          {!isFetchingRepos && githubRepos.length === 0 && githubError && (
            <UxState
              compact
              kind={classifyUxKind(githubError)}
              title="Catalog unavailable."
              body=""
            />
          )}
          {githubRepos.length > 0 && (
            <ul>
              {githubRepos.map((repo) => (
                <li key={repo.full_name}>
                  <button
                    type="button"
                    className={repo.full_name === selectedRepoFullName ? "is-on" : ""}
                    onClick={() => setSelectedRepoFullName(repo.full_name)}
                  >
                    <strong>{repo.name}</strong>
                    <em>
                      {repo.language || "Language unknown"} · ★ {repo.stars}
                    </em>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <div className="orch-repo-workspace">
          {!selected && (
            <div className="orch-repo-empty">
              <UxState
                kind="empty"
                kicker="Empty"
                title="Select a repository"
                body="Header, tree, dependencies, quality signals, and AI insights appear after you pick a repo and run the existing scan or analysis."
              />
            </div>
          )}

          {selected && (
            <motion.article
              key={selected.full_name}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="orch-repo-board"
            >
              {(repoLocked || aiLocked) && (
                <OrchLocked kind="repo" />
              )}
              <header className="orch-repo-header">
                <div>
                  <p className="orch-kicker">{selected.visibility}</p>
                  <h3>{selected.full_name}</h3>
                  <p>{selected.description || "No description provided."}</p>
                </div>
                <dl className="orch-repo-meta-grid">
                  <div>
                    <dt>Language</dt>
                    <dd>{selected.language || "—"}</dd>
                  </div>
                  <div>
                    <dt>Stars</dt>
                    <dd>{selected.stars}</dd>
                  </div>
                  <div>
                    <dt>Forks</dt>
                    <dd>{selected.forks}</dd>
                  </div>
                  <div>
                    <dt>Branch</dt>
                    <dd>{selected.default_branch || "—"}</dd>
                  </div>
                  <div>
                    <dt>Updated</dt>
                    <dd>{formatDate(selected.updated_at)}</dd>
                  </div>
                </dl>
                <div className="orch-repo-actions">
                  <a
                    className="orch-btn ghost"
                    href={selected.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open on GitHub
                  </a>
                  <button
                    type="button"
                    className="orch-btn ghost"
                    onClick={() =>
                      handleViewOverview(selected.url, selected.full_name)
                    }
                    disabled={scanning || loading}
                  >
                    {scanning
                      ? "Scanning…"
                      : overview && !overview.error && !overview.isHidden
                        ? "Hide overview"
                        : overview && !overview.error && overview.isHidden
                          ? "Show overview"
                          : "Scan overview"}
                  </button>
                  <button
                    type="button"
                    className="orch-btn"
                    onClick={() =>
                      handleAnalyzeRepo(selected.url, selected.full_name)
                    }
                    disabled={loading || repoLocked || aiLocked}
                  >
                    {analyzing
                      ? "Analyzing…"
                      : repoLocked || aiLocked
                        ? "Locked"
                        : "Analyze repository"}
                  </button>
                </div>
              </header>

              {scanning && (
                <UxState
                  compact
                  kind="loading"
                  title="Scanning repository evidence."
                  body="Reading the git tree from the existing overview endpoint."
                />
              )}
              {analyzing && (
                <UxState
                  compact
                  kind="processing"
                  title="Developer agent is analyzing evidence."
                  body="The existing /query analyze prompt is in flight."
                />
              )}
              {!scanning && !analyzing && (
                <p className="orch-repo-progress" aria-live="polite">
                  Stage · {stage.current}
                </p>
              )}

              {overview?.error && !overview.isHidden && (
                <UxState
                  compact
                  kind={classifyUxKind(overview.error)}
                  body={overview.error}
                />
              )}

              <div className="orch-repo-panels">
                <section>
                  <p className="orch-kicker">Structure</p>
                  <h4>Repository tree</h4>
                  {scanning && (
                    <UxState compact kind="loading" title="Reading git tree." body="" />
                  )}
                  {!scanning && !showScan && (
                    <p className="orch-note">Scan the repository to load its tree.</p>
                  )}
                  {showScan && !overview.error && (
                    <ul className="orch-repo-tree">
                      {(asList(overview.structure).length
                        ? overview.structure
                        : ["No top-level paths in overview."]
                      ).map((path) => (
                        <li key={path}>
                          <span aria-hidden="true">
                            {path.includes(".") ? "◇" : "▣"}
                          </span>
                          {path}
                        </li>
                      ))}
                    </ul>
                  )}
                </section>

                <section>
                  <p className="orch-kicker">Dependencies</p>
                  <h4>Manifests and frameworks</h4>
                  {showScan && !overview.error ? (
                    <>
                      <svg
                        className="orch-repo-deps"
                        viewBox="0 0 320 56"
                        aria-hidden="true"
                      >
                        {(asList(overview.dependencies).slice(0, 5).length
                          ? asList(overview.dependencies).slice(0, 5)
                          : ["None"]
                        ).map((item, i, list) => {
                          const x = 24 + i * (280 / Math.max(list.length, 1));
                          return (
                            <g key={item}>
                              {i > 0 && (
                                <path
                                  d={`M ${24 + (i - 1) * (280 / list.length)} 22 H ${x}`}
                                  stroke="rgba(126,231,255,0.35)"
                                />
                              )}
                              <circle cx={x} cy="22" r="5" fill="#7ee7ff" />
                              <text
                                x={x}
                                y="44"
                                textAnchor="middle"
                                fill="rgba(220,222,236,0.8)"
                                fontSize="7"
                              >
                                {String(item).slice(0, 18)}
                              </text>
                            </g>
                          );
                        })}
                      </svg>
                      <ChipList
                        items={overview.dependencies}
                        empty="No dependency manifests detected in overview evidence."
                      />
                      <ChipList
                        items={overview.frameworks}
                        empty="No frameworks detected in overview evidence."
                      />
                    </>
                  ) : scanning ? (
                    <p className="orch-note">Checking dependencies…</p>
                  ) : null}
                </section>

                <section>
                  <p className="orch-kicker">Code quality</p>
                  <h4>Signals from overview evidence</h4>
                  {showScan && !overview.error ? (
                    <div className="orch-repo-metrics">
                      <Metric
                        label="Architecture"
                        value={overview.architecture?.summary || "—"}
                      />
                      <Metric
                        label="Languages"
                        value={
                          isDetectedList(overview.languages)
                            ? String(overview.languages.length)
                            : "—"
                        }
                      />
                      <Metric
                        label="Testing"
                        value={
                          isDetectedList(overview.testing) ? "Detected" : "Not detected"
                        }
                      />
                      <Metric
                        label="Deployment"
                        value={
                          isDetectedList(overview.deployment)
                            ? overview.deployment.join(", ")
                            : "Not detected"
                        }
                      />
                      <ChipList
                        items={overview.languages}
                        empty="Languages were not detected."
                      />
                      <ChipList
                        items={overview.configuration}
                        empty="No configuration files detected."
                      />
                      <ChipList
                        items={overview.entry_points}
                        empty="No entry points detected."
                      />
                    </div>
                  ) : (
                    <UxState
                      compact
                      kind="empty"
                      title="No quality signals yet."
                      body="Quality metrics come from overview fields, not invented scores."
                    />
                  )}
                </section>

                <section>
                  <p className="orch-kicker">Issues</p>
                  <h4>Evidence gaps and analysis</h4>
                  {analyzing && (
                    <UxState compact kind="processing" title="Waiting for the developer agent." body="" />
                  )}
                  {analysisError && (
                    <UxState compact kind={classifyUxKind(error)} body={error} />
                  )}
                  {showScan && !overview.error && !analyzing && (
                    <ul className="orch-repo-flags">
                      {!isDetectedList(overview.testing) && (
                        <li>No test paths detected in overview evidence.</li>
                      )}
                      {!isDetectedList(overview.deployment) && (
                        <li>No deployment config detected in overview evidence.</li>
                      )}
                      {!isDetectedList(overview.apis) && (
                        <li>No API path evidence detected.</li>
                      )}
                      {isDetectedList(overview.testing) &&
                        isDetectedList(overview.deployment) &&
                        isDetectedList(overview.apis) && (
                          <li>
                            Overview found testing, deployment, and API evidence.
                            Issue detail still requires Analyze repository.
                          </li>
                        )}
                    </ul>
                  )}
                  {!analysisReady && !analyzing && !analysisError && (
                    <UxState
                      compact
                      kind="empty"
                      title="No issue write-up yet."
                      body="Structured issue write-ups are not returned by the overview API. Run Analyze repository to get developer-agent findings."
                    />
                  )}
                  {analysisReady && (
                    <UxState
                      compact
                      kind="success"
                      title="Issue findings are in AI Insights."
                      body=""
                    />
                  )}
                </section>

                <section className="orch-repo-insights">
                  <p className="orch-kicker">AI Insights</p>
                  <h4>Recommendations from the developer agent</h4>
                  {analyzing && (
                    <UxState
                      compact
                      kind="processing"
                      title="Writing insights from repository evidence."
                      body=""
                    />
                  )}
                  {analysisError && (
                    <UxState compact kind={classifyUxKind(error)} body={error} />
                  )}
                  {analysisReady && (
                    <>
                      <UxState compact kind="success" title="Analysis complete." body="" />
                      {answerElement}
                    </>
                  )}
                  {!analyzing && !analysisReady && !analysisError && (
                    <UxState
                      compact
                      kind="empty"
                      title="No insights yet."
                      body="Analyze repository sends the existing evidence prompt to /query. The answer lands here and in the response workspace."
                    />
                  )}
                </section>
              </div>
            </motion.article>
          )}
        </div>
      </div>
    </section>
  );
}
