export const AGENT_CATALOG = [
  { id: "salary_agent", name: "Salary Agent", mark: "$", tint: "90,210,255" },
  { id: "company_agent", name: "Company Agent", mark: "◈", tint: "168,140,255" },
  { id: "weather_agent", name: "Weather Agent", mark: "◎", tint: "90,230,210" },
  { id: "general_agent", name: "General Agent", mark: "✦", tint: "190,150,255" },
  { id: "developer_agent", name: "Repository Intelligence", mark: "{}", tint: "110,200,255" },
];

export function formatAgentName(agentName) {
  if (agentName === "salary_agent") return "Salary Agent";
  if (agentName === "company_agent") return "Company Agent";
  if (agentName === "weather_agent") return "Weather Agent";
  if (agentName === "developer_agent") return "Developer Agent";
  if (agentName === "general_agent") return "General Agent";
  return agentName || "MCP Agent";
}

export const SUGGESTIONS = [
  {
    label: "Developer",
    text: "What is the difference between Python and C?",
  },
  {
    label: "Weather",
    text: "What is the weather in Hyderabad?",
  },
  {
    label: "Repository",
    text: "Analyze https://github.com/pallets/flask. Find real issues, explain the architecture, and analyze the repository based only on supplied repository evidence.",
  },
  {
    label: "MCP",
    text: "What is MCP and how does the orchestrator choose an agent?",
  },
];
