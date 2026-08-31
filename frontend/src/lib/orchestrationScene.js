import { useEffect, useMemo, useState } from "react";
import { useReducedMotion } from "motion/react";

const EMPTY = [];

export const VIS_FLOW = [
  "Idle",
  "Question received",
  "MCP active",
  "Agent selected",
  "Agent processing",
  "Response returning",
  "Complete",
];

export const COMMAND_PATH = [
  "Question",
  "MCP",
  "Agent",
  "Processing",
  "Response",
];

export function commandPathIndex(play, phase) {
  if (phase === "idle" && play === "idle") return 0;
  if (play === "mcp" || phase === "thinking") return 1;
  if (play === "selected") return 2;
  if (play === "processing") return 3;
  if (play === "returning" || play === "complete") return 4;
  if (play === "error" || phase === "error") return 4;
  return 0;
}

const PLAY_INDEX = {
  idle: 0,
  mcp: 2,
  selected: 3,
  processing: 4,
  returning: 5,
  complete: 6,
  error: 5,
};

export function useOrchestrationVis(phase, submittedQuery, response) {
  const reduced = useReducedMotion();
  const [successPlay, setSuccessPlay] = useState(null);
  const requestId = response?.request_id || "";

  useEffect(() => {
    if (phase !== "success") {
      setSuccessPlay(null);
      return undefined;
    }

    if (reduced) {
      setSuccessPlay("complete");
      return undefined;
    }

    setSuccessPlay("selected");
    const processing = window.setTimeout(() => setSuccessPlay("processing"), 420);
    const returning = window.setTimeout(() => setSuccessPlay("returning"), 980);
    const complete = window.setTimeout(() => setSuccessPlay("complete"), 1580);

    return () => {
      window.clearTimeout(processing);
      window.clearTimeout(returning);
      window.clearTimeout(complete);
    };
  }, [phase, requestId, reduced]);

  const play = useMemo(() => {
    if (phase === "idle") return "idle";
    if (phase === "thinking") return "mcp";
    if (phase === "error") return "error";
    if (phase === "success") {
      return successPlay || (reduced ? "complete" : "selected");
    }
    return "idle";
  }, [phase, successPlay, reduced]);

  const agents = response?.execution_trace?.agents ?? EMPTY;
  const calls = response?.execution_trace?.mcp_calls ?? EMPTY;

  return useMemo(
    () => ({
      play,
      index: PLAY_INDEX[play] ?? 0,
      agents,
      calls,
      reduced: Boolean(reduced),
      queryReceived: Boolean(submittedQuery) && phase !== "idle",
      routedKnown: agents.length > 0,
    }),
    [play, agents, calls, reduced, submittedQuery, phase]
  );
}
