import { isQuotaOrRateLimitError } from "./orchestrationErrors";

export const UX_KINDS = [
  "empty",
  "loading",
  "processing",
  "success",
  "error",
  "rateLimited",
  "unavailable",
  "invalid",
];

export const UX_COPY = {
  empty: {
    kicker: "Empty",
    title: "Nothing on the fabric yet.",
    body: "A command or repository has to land before agents can route.",
  },
  loading: {
    kicker: "Loading",
    title: "Fetching evidence.",
    body: "Reading the catalog or overview. This is a data load, not a model pass.",
  },
  processing: {
    kicker: "Processing",
    title: "Agents are on the request.",
    body: "The orchestrator has the question and specialists are working it.",
  },
  success: {
    kicker: "Success",
    title: "A traced result is ready.",
    body: "The answer is backed by the route that produced it.",
  },
  error: {
    kicker: "Error",
    title: "We couldn't complete that request.",
    body: "Try again. If this keeps happening, the analysis service may be unavailable.",
  },
  rateLimited: {
    kicker: "Rate limited",
    title: "The AI quota is exhausted.",
    body: "The product path is intact. Upstream model capacity has to reset.",
  },
  unavailable: {
    kicker: "Unavailable",
    title: "The analysis server is unreachable.",
    body: "Confirm the backend is running, then try the same request again.",
  },
  invalid: {
    kicker: "Invalid input",
    title: "That value cannot be routed.",
    body: "Fix the field — profile URL, key shape, or empty command — and resubmit.",
  },
};

export function classifyUxKind(message) {
  const text = String(message || "");
  const lower = text.toLowerCase();

  if (!text.trim()) return "error";

  if (
    isQuotaOrRateLimitError(text) ||
    lower.includes("frontend-only") ||
    lower.includes("free plan preview") ||
    lower.includes("usage limit") ||
    lower.includes("quota has been reached") ||
    lower.includes("limit completed") ||
    lower.includes("token budget") ||
    lower.includes("fatal_limit")
  ) {
    return "rateLimited";
  }

  if (
    lower.includes("unable to connect") ||
    lower === "failed to fetch" ||
    lower.includes("networkerror") ||
    lower.includes("network request failed") ||
    lower.includes("503") ||
    lower.includes("unavailable")
  ) {
    return "unavailable";
  }

  if (
    lower.includes("invalid") ||
    lower.includes("enter a valid") ||
    lower.includes("enter your") ||
    lower.includes("400")
  ) {
    return "invalid";
  }

  return "error";
}

export const GITHUB_PROFILE_PATTERN =
  /^(?:https?:\/\/)?(?:www\.)?(?:github\.com\/)?[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}\/?$/i;
