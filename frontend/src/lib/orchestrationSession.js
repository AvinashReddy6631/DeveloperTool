export function sessionStorageKey(userId) {
  return userId
    ? `mcp_orchestrator_session_id:${userId}`
    : "mcp_orchestrator_session_id:anon";
}

export function getOrCreateSessionId(userId) {
  const key = sessionStorageKey(userId);

  try {
    const existing = localStorage.getItem(key);

    if (existing) {
      return existing;
    }

    const generated =
      typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

    localStorage.setItem(key, generated);
    return generated;
  } catch (storageError) {
    console.warn(
      "Unable to access localStorage. Using an in-memory session ID.",
      storageError
    );

    return `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  }
}
