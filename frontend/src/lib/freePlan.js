export const FREE_AI_LIMIT = 3;
export const FREE_REPO_LIMIT = 1;

export const ANALYZE_PROMPT_PREFIX = "Analyze ";
export const ANALYZE_PROMPT_MARKER =
  "analyze the repository based only on supplied repository evidence";

export function isRepoAnalysisQuery(text) {
  const value = String(text || "").toLowerCase();
  return (
    value.startsWith(ANALYZE_PROMPT_PREFIX.toLowerCase()) &&
    value.includes(ANALYZE_PROMPT_MARKER)
  );
}

function asCount(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function readApiUsage(payload) {
  const usage = payload?.usage || payload?.quota || payload?.plan_usage;
  if (!usage || typeof usage !== "object") {
    return null;
  }

  const aiUsed = asCount(
    usage.ai_used ?? usage.requests_used ?? usage.ai_requests
  );
  const aiLimit = asCount(
    usage.ai_limit ?? usage.request_limit ?? usage.max_ai_requests
  );
  const aiRemaining = asCount(
    usage.ai_remaining ?? usage.requests_remaining
  );
  const repoUsed = asCount(
    usage.repo_used ?? usage.repository_analyses_used
  );
  const repoLimit = asCount(
    usage.repo_limit ?? usage.repository_analysis_limit
  );
  const repoRemaining = asCount(
    usage.repo_remaining ?? usage.repository_analyses_remaining
  );

  if (
    aiUsed == null &&
    aiRemaining == null &&
    repoUsed == null &&
    repoRemaining == null
  ) {
    return null;
  }

  return {
    source: "api",
    aiUsed: aiUsed ?? 0,
    aiLimit: aiLimit ?? FREE_AI_LIMIT,
    aiRemaining:
      aiRemaining ??
      Math.max(0, (aiLimit ?? FREE_AI_LIMIT) - (aiUsed ?? 0)),
    repoUsed: repoUsed ?? 0,
    repoLimit: repoLimit ?? FREE_REPO_LIMIT,
    repoRemaining:
      repoRemaining ??
      Math.max(0, (repoLimit ?? FREE_REPO_LIMIT) - (repoUsed ?? 0)),
  };
}

export function buildPreviewUsage(aiUsed, repoUsed) {
  return {
    source: "preview",
    aiUsed,
    aiLimit: FREE_AI_LIMIT,
    aiRemaining: Math.max(0, FREE_AI_LIMIT - aiUsed),
    repoUsed,
    repoLimit: FREE_REPO_LIMIT,
    repoRemaining: Math.max(0, FREE_REPO_LIMIT - repoUsed),
  };
}

export const FREE_PLAN_PREVIEW_LIMIT = "FREE_PLAN_PREVIEW_LIMIT";
export const FREE_PLAN_PREVIEW_REPO_LIMIT = "FREE_PLAN_PREVIEW_REPO_LIMIT";
