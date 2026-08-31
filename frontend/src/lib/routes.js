export const ORCHESTRATION_PATH = "/orchestration";
export const ORCHESTRATION_DEMO_HREF = "/orchestration?demo=1";

export function isOrchestrationPath(pathname) {
  const path = String(pathname || "").replace(/\/$/, "") || "/";
  return path === ORCHESTRATION_PATH;
}
