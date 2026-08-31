import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import ApiDocsView from "./pages/ApiDocsView.jsx";
import DocsChrome from "./pages/DocsChrome.jsx";
import DocumentationView from "./pages/DocumentationView.jsx";
import HomePage from "./pages/HomePage.jsx";
import OrchestrationPage from "./pages/OrchestrationPage.jsx";

const DOC_SECTION_HASHES = new Set([
  "#documentation",
  "#architecture",
  "#agents-docs",
  "#sessions",
  "#flow",
]);

function getHashView() {
  const hash = window.location.hash;

  if (hash === "#api" || hash.startsWith("#api-")) return "api";
  if (DOC_SECTION_HASHES.has(hash)) return "docs";
  return null;
}

function App() {
  const [hashView, setHashView] = useState(getHashView);

  useEffect(() => {
    const onHashChange = () => {
      setHashView(getHashView());
    };

    window.addEventListener("hashchange", onHashChange);
    onHashChange();

    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const showingDocs = hashView === "api" || hashView === "docs";

  return showingDocs ? (
    <DocsChrome activeView={hashView}>
      {hashView === "api" ? <ApiDocsView /> : <DocumentationView />}
    </DocsChrome>
  ) : (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/orchestration" element={<OrchestrationPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
