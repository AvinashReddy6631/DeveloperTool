export function isQuotaOrRateLimitError(message) {
  const normalizedMessage = String(message || "").toLowerCase();

  return (
    normalizedMessage.includes("429") ||
    normalizedMessage.includes("rate limit") ||
    normalizedMessage.includes("free-models-per-day") ||
    normalizedMessage.includes("request limit") ||
    normalizedMessage.includes("quota")
  );
}

export function mapOrchestrationError(errorMessage, usingPersonalApiKey) {
  const message = String(errorMessage || "");

  if (
    message.includes("FATAL_LIMIT_ERROR") ||
    message.includes("insufficient") ||
    message.includes("token budget")
  ) {
    return "Repository analysis unavailable: OpenRouter credits/token budget are insufficient. Please try again after adding credits.";
  }

  if (message === "FREE_PLAN_PREVIEW_LIMIT") {
    return "You have used all 3 free AI requests on this account.";
  }

  if (message === "FREE_PLAN_PREVIEW_REPO_LIMIT") {
    return "You have used the 1 free repository analysis on this account.";
  }

  if (isQuotaOrRateLimitError(message)) {
    return usingPersonalApiKey
      ? "Your OpenRouter API key has reached its current AI usage limit. Please try again after the provider limit resets or connect another key."
      : "AI request limit completed for today. " +
          "Your MCP Orchestrator is working correctly, " +
          "but the free AI model quota has been reached. " +
          "Please try again after the daily limit resets.";
  }

  if (
    message === "Failed to fetch" ||
    message.includes("NetworkError") ||
    message.includes("Network request failed")
  ) {
    return "Unable to connect to the analysis server. Please make sure the backend is running and try again.";
  }

  return (
    message ||
    "Unable to connect to the analysis server. Please make sure the backend is running and try again."
  );
}

export const OPENROUTER_KEY_PATTERN = /^sk-or-[A-Za-z0-9_-]{8,}$/;
