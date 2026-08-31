export const NAV_LINKS = [
  { href: "#home", label: "Home" },
  { href: "#agents", label: "Agents" },
  { href: "#how-it-works", label: "How It Works" },
  { href: "#repository", label: "Repository" },
  { href: "#pricing", label: "Pricing" },
  { href: "#documentation", label: "Docs" },
];

export const GITHUB_URL = "https://github.com";

export const HERO_SIGNALS = [
  "AI agents",
  "MCP orchestration",
  "Intelligent routing",
  "Developer workflows",
  "Repository intelligence",
];

export const WHAT_IT_DOES_STAGES = [
  {
    id: "question",
    title: "User Question",
    line: "What is the compensation spread for senior roles at Acme?",
    body: "A developer asks in plain language. No tickets, no tool picker — just intent.",
  },
  {
    id: "intent",
    title: "Intent Understanding",
    line: "Domain: compensation · Entity: Acme · Depth: comparative",
    body: "The request is classified before any specialist is woken. The system decides what kind of work this is.",
  },
  {
    id: "orchestrator",
    title: "MCP Orchestrator",
    line: "Route committed → salary_agent",
    body: "The orchestrator selects a path, carries session context, and refuses to dump the job into a generic model.",
  },
  {
    id: "agent",
    title: "Specialized Agent",
    line: "Salary Agent owns the execution",
    body: "One narrow mandate. Compensation tools run against structured evidence, not improvisation.",
  },
  {
    id: "processing",
    title: "Processing",
    line: "MCP tools · memory · timed calls",
    body: "Tools execute, timings accumulate, and the pipeline stays observable instead of opaque.",
  },
  {
    id: "response",
    title: "Response",
    line: "Answer + route + execution trace",
    body: "The developer receives the result with enough context to trust — or challenge — the path that produced it.",
  },
];

export const AGENTS = [
  {
    id: "salary",
    name: "Salary",
    mark: "$",
    summary: "Compensation rankings, comparisons, and salary statistics.",
    x: 20,
    y: 20,
  },
  {
    id: "company",
    name: "Company",
    mark: "◈",
    summary: "Organizations, employees, workforce shape, and roles.",
    x: 80,
    y: 20,
  },
  {
    id: "weather",
    name: "Weather",
    mark: "◎",
    summary: "Location resolution with live temperature and wind.",
    x: 18,
    y: 68,
  },
  {
    id: "general",
    name: "General",
    mark: "✦",
    summary: "Open questions that still need a disciplined route.",
    x: 82,
    y: 68,
  },
  {
    id: "repository",
    name: "Repository",
    mark: "{}",
    summary: "Structure, quality, and evidence-backed code insight.",
    x: 50,
    y: 84,
  },
];

export const REPO_FLOW = [
  { id: "github", title: "GitHub Repository", detail: "github.com/workspace/mcp-learning" },
  { id: "intel", title: "Repository Intelligence", detail: "Specialist assigned by MCP" },
  { id: "structure", title: "Structure", detail: "api.py · orchestrator.py · agents/ · frontend/" },
  { id: "deps", title: "Dependencies", detail: "FastAPI · PostgreSQL · MCP · React" },
  { id: "quality", title: "Code Quality", detail: "Layered service · traced execution" },
  { id: "issues", title: "Issues", detail: "Shared quota · unscoped analysis prompts" },
  { id: "insights", title: "AI Insights", detail: "Illustrative architecture notes only" },
];

export const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Ask",
    body: "A developer writes a question — compensation, a company, weather, or a repository.",
  },
  {
    step: "02",
    title: "Orchestrate",
    body: "MCP reads intent and commits a specialist instead of guessing with one model.",
  },
  {
    step: "03",
    title: "Analyze",
    body: "The chosen agent runs tools against evidence: data, context, or repository structure.",
  },
  {
    step: "04",
    title: "Respond",
    body: "An answer returns with the route that produced it — ready for the next follow-up.",
  },
];

export const PREVIEW_FRAMES = [
  {
    label: "Question",
    query: "Map this repository’s architecture and name real risk areas.",
    agent: "—",
    status: "IDLE",
    answer: "",
  },
  {
    label: "MCP activation",
    query: "Map this repository’s architecture and name real risk areas.",
    agent: "Orchestrator classifying intent",
    status: "ROUTING",
    answer: "",
  },
  {
    label: "Agent activation",
    query: "Map this repository’s architecture and name real risk areas.",
    agent: "Repository Intelligence",
    status: "ASSIGNED",
    answer: "",
  },
  {
    label: "Processing",
    query: "Map this repository’s architecture and name real risk areas.",
    agent: "Repository Intelligence",
    status: "RUNNING",
    answer: "Reading tree, languages, entry points, and configuration…",
  },
  {
    label: "Response",
    query: "Map this repository’s architecture and name real risk areas.",
    agent: "Repository Intelligence",
    status: "COMPLETE",
    answer:
      "Layered FastAPI service with an MCP orchestrator in front of specialized agents. Illustrative risks: unscoped analysis prompts and shared model quota on the free path.",
  },
];
