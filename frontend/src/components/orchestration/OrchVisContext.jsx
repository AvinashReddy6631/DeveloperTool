import { createContext, useContext } from "react";
import { useOrchestration } from "../../context/OrchestrationContext";
import { useOrchestrationVis } from "../../lib/orchestrationScene";

const OrchVisContext = createContext(null);

export function OrchVisProvider({ children }) {
  const { phase, submittedQuery, response } = useOrchestration();
  const vis = useOrchestrationVis(phase, submittedQuery, response);
  return (
    <OrchVisContext.Provider value={vis}>{children}</OrchVisContext.Provider>
  );
}

export function useOrchVis() {
  const vis = useContext(OrchVisContext);
  if (!vis) {
    throw new Error("useOrchVis must be used inside OrchVisProvider");
  }
  return vis;
}
