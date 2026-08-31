import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  mapOrchestrationError,
  OPENROUTER_KEY_PATTERN,
} from "../lib/orchestrationErrors";
import { GITHUB_PROFILE_PATTERN } from "../lib/uxStates";
import { getOrCreateSessionId } from "../lib/orchestrationSession";
import {
  clearStoredToken,
  readStoredToken,
  storeToken,
} from "../lib/authStorage";
import {
  FREE_PLAN_PREVIEW_LIMIT,
  FREE_PLAN_PREVIEW_REPO_LIMIT,
  isRepoAnalysisQuery,
  readApiUsage,
} from "../lib/freePlan";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const OrchestrationContext = createContext(null);

function emptyUsage() {
  return {
    source: "api",
    aiUsed: 0,
    aiLimit: 3,
    aiRemaining: 3,
    repoUsed: 0,
    repoLimit: 1,
    repoRemaining: 1,
  };
}

function detailMessage(data, fallback) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") {
    return detail.error || detail.message || JSON.stringify(detail);
  }
  return fallback;
}

export function OrchestrationProvider({ children }) {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [phase, setPhase] = useState("idle");
  const [error, setError] = useState("");
  const [errorCode, setErrorCode] = useState("");
  const [technicalError, setTechnicalError] = useState("");
  const [token, setToken] = useState(readStoredToken);
  const [user, setUser] = useState(null);
  const [sessionId, setSessionId] = useState(() => getOrCreateSessionId(null));

  const [githubProfile, setGithubProfile] = useState("");
  const [githubRepos, setGithubRepos] = useState([]);
  const [isFetchingRepos, setIsFetchingRepos] = useState(false);
  const [githubError, setGithubError] = useState("");
  const [repoOverviews, setRepoOverviews] = useState({});
  const [fetchingOverviewFor, setFetchingOverviewFor] = useState(null);
  const [selectedRepoFullName, setSelectedRepoFullName] = useState("");
  const [analyzingRepoUrl, setAnalyzingRepoUrl] = useState("");

  const [showAiAccess, setShowAiAccess] = useState(false);
  const [showAccount, setShowAccount] = useState(false);
  const [accountMode, setAccountMode] = useState("login");
  const [accountEmail, setAccountEmail] = useState("");
  const [accountPassword, setAccountPassword] = useState("");
  const [accountError, setAccountError] = useState("");
  const [accountBusy, setAccountBusy] = useState(false);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [personalApiKey, setPersonalApiKey] = useState("");
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [apiKeyError, setApiKeyError] = useState("");
  const [apiUsage, setApiUsage] = useState(null);
  const queryInputRef = useRef(null);

  const loading = phase === "thinking";
  const isPersonalApiKeyConnected = Boolean(personalApiKey);
  const usage = user
    ? apiUsage || {
        source: "api",
        aiUsed: null,
        aiLimit: 3,
        aiRemaining: null,
        repoUsed: null,
        repoLimit: 1,
        repoRemaining: null,
      }
    : emptyUsage();
  const aiLocked =
    Boolean(user) &&
    usage.aiRemaining != null &&
    Number(usage.aiRemaining) <= 0;
  const repoLocked =
    Boolean(user) &&
    usage.repoRemaining != null &&
    Number(usage.repoRemaining) <= 0;

  const authHeaders = (extra = {}) => ({
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  });

  const applyAuthPayload = (data) => {
    if (!data?.token || !data?.user) {
      throw new Error("Authentication did not return a user session.");
    }
    storeToken(data.token);
    setToken(data.token);
    setUser(data.user);
    setSessionId(getOrCreateSessionId(data.user.id));
    const fromApi = readApiUsage(data);
    setApiUsage(fromApi || emptyUsage());
    setQuery("");
    setSubmittedQuery("");
    setResponse(null);
    setError("");
    setErrorCode("");
    setTechnicalError("");
    setPhase("idle");
    setGithubRepos([]);
    setRepoOverviews({});
    setGithubError("");
    setSelectedRepoFullName("");
    setAnalyzingRepoUrl("");
  };

  const resetWorkspace = () => {
    setQuery("");
    setSubmittedQuery("");
    setResponse(null);
    setError("");
    setErrorCode("");
    setTechnicalError("");
    setPhase("idle");
    setGithubProfile("");
    setGithubRepos([]);
    setGithubError("");
    setRepoOverviews({});
    setSelectedRepoFullName("");
    setAnalyzingRepoUrl("");
    setPersonalApiKey("");
  };

  const loadSession = async (activeToken) => {
    if (!activeToken || !API_URL) return;
    try {
      const result = await fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${activeToken}` },
      });
      const data = await result.json().catch(() => null);
      if (!result.ok) {
        clearStoredToken();
        setToken("");
        setUser(null);
        setApiUsage(null);
        return;
      }
      setUser(data.user);
      setSessionId(getOrCreateSessionId(data.user.id));
      let usagePayload = readApiUsage(data);
      const usageResult = await fetch(`${API_URL}/usage`, {
        headers: { Authorization: `Bearer ${activeToken}` },
      });
      const usageData = await usageResult.json().catch(() => null);
      if (usageResult.ok) {
        usagePayload = readApiUsage(usageData) || usagePayload;
      }
      setApiUsage(usagePayload || emptyUsage());
    } catch {
      setUser(null);
    }
  };

  useEffect(() => {
    if (token) loadSession(token);
  }, []);

  const registerAccount = async () => {
    setAccountBusy(true);
    setAccountError("");
    try {
      const result = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: accountEmail.trim(),
          password: accountPassword,
        }),
      });
      const data = await result.json().catch(() => null);
      if (!result.ok) {
        throw new Error(detailMessage(data, "Could not create the account."));
      }
      applyAuthPayload(data);
      setAccountPassword("");
      setShowAccount(false);
    } catch (err) {
      setAccountError(err.message || "Could not create the account.");
    } finally {
      setAccountBusy(false);
    }
  };

  const loginAccount = async () => {
    setAccountBusy(true);
    setAccountError("");
    try {
      const result = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: accountEmail.trim(),
          password: accountPassword,
        }),
      });
      const data = await result.json().catch(() => null);
      if (!result.ok) {
        throw new Error(detailMessage(data, "Could not sign in."));
      }
      applyAuthPayload(data);
      setAccountPassword("");
      setShowAccount(false);
    } catch (err) {
      setAccountError(err.message || "Could not sign in.");
    } finally {
      setAccountBusy(false);
    }
  };

  const logoutAccount = async () => {
    try {
      if (token) {
        await fetch(`${API_URL}/auth/logout`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
      }
    } catch {
      /* logout is best-effort */
    }
    clearStoredToken();
    setToken("");
    setUser(null);
    setApiUsage(null);
    setSessionId(getOrCreateSessionId(null));
    resetWorkspace();
  };

  const connectPersonalApiKey = () => {
    const cleanKey = apiKeyInput.trim();

    if (!cleanKey) {
      setApiKeyError("Enter your OpenRouter API key to connect.");
      return;
    }

    if (!OPENROUTER_KEY_PATTERN.test(cleanKey)) {
      setApiKeyError(
        "Enter a valid OpenRouter API key. Keys normally start with sk-or-."
      );
      return;
    }

    setPersonalApiKey(cleanKey);
    setApiKeyInput("");
    setApiKeyError("");
    setShowAiAccess(false);

    window.requestAnimationFrame(() => {
      queryInputRef.current?.focus();
    });
  };

  const disconnectPersonalApiKey = () => {
    setPersonalApiKey("");
    setApiKeyInput("");
    setApiKeyError("");
  };

  const executeQuery = async (textToQuery) => {
    const cleanQuery = textToQuery.trim();

    if (!cleanQuery || loading) {
      return;
    }

    if (!user) {
      setSubmittedQuery(cleanQuery);
      setError("Sign in to send a request. Usage is stored on your account.");
      setErrorCode("AUTH_REQUIRED");
      setPhase("error");
      setShowAccount(true);
      return;
    }

    const usingPersonalApiKey = Boolean(personalApiKey);

    if (isRepoAnalysisQuery(cleanQuery) && usage.repoRemaining <= 0) {
      setSubmittedQuery(cleanQuery);
      setError(mapOrchestrationError(FREE_PLAN_PREVIEW_REPO_LIMIT, usingPersonalApiKey));
      setErrorCode("QUOTA_EXCEEDED");
      setPhase("error");
      return;
    }

    if (usage.aiRemaining <= 0) {
      setSubmittedQuery(cleanQuery);
      setError(mapOrchestrationError(FREE_PLAN_PREVIEW_LIMIT, usingPersonalApiKey));
      setErrorCode("QUOTA_EXCEEDED");
      setPhase("error");
      return;
    }

    setSubmittedQuery(cleanQuery);
    setPhase("thinking");
    setError("");
    setErrorCode("");
    setTechnicalError("");
    setResponse(null);

    try {
      const result = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: authHeaders(
          usingPersonalApiKey ? { "X-OpenRouter-Key": personalApiKey } : {}
        ),
        body: JSON.stringify({
          query: cleanQuery,
          session_id: sessionId,
        }),
      });

      const data = await result.json().catch(() => null);

      if (data && readApiUsage(data)) {
        setApiUsage(readApiUsage(data));
      }

      if (!result.ok) {
        const backendError = detailMessage(
          data,
          typeof data?.error === "string"
            ? data.error
            : `Backend returned HTTP ${result.status}`
        );
        throw new Error(backendError);
      }

      if (!data) {
        throw new Error("Invalid or empty response from the analysis server.");
      }

      if (data.status === "error") {
        const backendError =
          typeof data.error === "string"
            ? data.error
            : "The request could not be completed.";
        setTechnicalError(
          [data.error_code, typeof data.error === "string" ? data.error : ""]
            .filter(Boolean)
            .join(" · ")
        );
        setErrorCode(data.error_code || "QUERY_FAILED");
        throw new Error(backendError);
      }

      if (data.status !== "success" && data.status !== "partial") {
        throw new Error(`Unexpected response status: ${data.status}`);
      }

      setResponse(data);
      setPhase("success");
    } catch (err) {
      setError(mapOrchestrationError(err?.message, usingPersonalApiKey));
      setPhase("error");
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    executeQuery(query);
  };

  const handleLoadRepos = async (event) => {
    event.preventDefault();
    const cleanUrl = githubProfile.trim();
    if (!cleanUrl || isFetchingRepos) return;

    if (!GITHUB_PROFILE_PATTERN.test(cleanUrl)) {
      setGithubError("Enter a valid GitHub profile URL or username.");
      return;
    }

    setIsFetchingRepos(true);
    setGithubError("");
    setGithubRepos([]);
    setRepoOverviews({});
    setSelectedRepoFullName("");
    setAnalyzingRepoUrl("");

    try {
      const result = await fetch(`${API_URL}/github/repositories`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ profile_url: cleanUrl }),
      });

      const data = await result.json().catch(() => null);

      if (!result.ok) {
        throw new Error(detailMessage(data, `GitHub API error: ${result.status}`));
      }

      if (data?.status === "success") {
        setGithubRepos(data.repositories || []);
      } else {
        throw new Error("Failed to load repositories.");
      }
    } catch (err) {
      const message = err.message || "Failed to fetch GitHub repositories.";
      setGithubError(
        message === "Failed to fetch"
          ? "Unable to connect to the analysis server. Please make sure the backend is running and try again."
          : message
      );
    } finally {
      setIsFetchingRepos(false);
    }
  };

  const handleViewOverview = async (repoUrl, repoFullName) => {
    setSelectedRepoFullName(repoFullName);
    if (repoOverviews[repoFullName] && !repoOverviews[repoFullName].error) {
      setRepoOverviews((prev) => ({
        ...prev,
        [repoFullName]: {
          ...prev[repoFullName],
          isHidden: !prev[repoFullName].isHidden,
        },
      }));
      return;
    }

    setFetchingOverviewFor(repoFullName);
    try {
      const result = await fetch(`${API_URL}/github/repository/overview`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ repository_url: repoUrl }),
      });

      const data = await result.json().catch(() => null);

      if (!result.ok) {
        throw new Error(detailMessage(data, `Overview fetch failed: ${result.status}`));
      }

      if (data?.status === "success") {
        setRepoOverviews((prev) => ({
          ...prev,
          [repoFullName]: { ...data, isHidden: false },
        }));
      } else {
        throw new Error("Failed to load overview.");
      }
    } catch (err) {
      setRepoOverviews((prev) => ({
        ...prev,
        [repoFullName]: {
          error: err.message || "Failed to load.",
          isHidden: false,
        },
      }));
    } finally {
      setFetchingOverviewFor(null);
    }
  };

  const handleAnalyzeRepo = (repoUrl, repoFullName) => {
    if (repoFullName) {
      setSelectedRepoFullName(repoFullName);
    }
    setAnalyzingRepoUrl(repoUrl);
    const analysisQuery = `Analyze ${repoUrl}. Find real issues, explain the architecture, and analyze the repository based only on supplied repository evidence.`;
    setQuery(analysisQuery);
    executeQuery(analysisQuery);
    window.requestAnimationFrame(() => {
      document.getElementById("repository")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  };

  const handleNewQuestion = () => {
    setQuery("");
    setSubmittedQuery("");
    setResponse(null);
    setError("");
    setErrorCode("");
    setTechnicalError("");
    setPhase("idle");
  };

  const handleSuggestion = (text) => {
    setQuery(text);
  };

  const handleRetryClear = () => {
    const retryQuery = submittedQuery || query;
    setError("");
    setErrorCode("");
    setTechnicalError("");
    setResponse(null);
    if (retryQuery) {
      executeQuery(retryQuery);
    } else {
      setPhase("idle");
    }
  };

  const value = useMemo(
    () => ({
      query,
      setQuery,
      submittedQuery,
      response,
      phase,
      loading,
      error,
      errorCode,
      technicalError,
      sessionId,
      user,
      githubProfile,
      setGithubProfile,
      githubRepos,
      isFetchingRepos,
      githubError,
      repoOverviews,
      fetchingOverviewFor,
      selectedRepoFullName,
      setSelectedRepoFullName,
      analyzingRepoUrl,
      showAiAccess,
      setShowAiAccess,
      showAccount,
      setShowAccount,
      accountMode,
      setAccountMode,
      accountEmail,
      setAccountEmail,
      accountPassword,
      setAccountPassword,
      accountError,
      setAccountError,
      accountBusy,
      registerAccount,
      loginAccount,
      logoutAccount,
      showUpgrade,
      setShowUpgrade,
      personalApiKey,
      apiKeyInput,
      setApiKeyInput,
      apiKeyError,
      setApiKeyError,
      queryInputRef,
      isPersonalApiKeyConnected,
      connectPersonalApiKey,
      disconnectPersonalApiKey,
      executeQuery,
      handleSubmit,
      handleLoadRepos,
      handleViewOverview,
      handleAnalyzeRepo,
      handleNewQuestion,
      handleSuggestion,
      handleRetryClear,
      usage,
      aiLocked,
      repoLocked,
    }),
    [
      query,
      submittedQuery,
      response,
      phase,
      loading,
      error,
      errorCode,
      technicalError,
      sessionId,
      user,
      githubProfile,
      githubRepos,
      isFetchingRepos,
      githubError,
      repoOverviews,
      fetchingOverviewFor,
      selectedRepoFullName,
      analyzingRepoUrl,
      showAiAccess,
      showAccount,
      accountMode,
      accountEmail,
      accountPassword,
      accountError,
      accountBusy,
      showUpgrade,
      personalApiKey,
      apiKeyInput,
      apiKeyError,
      isPersonalApiKeyConnected,
      usage,
      aiLocked,
      repoLocked,
      token,
    ]
  );

  return (
    <OrchestrationContext.Provider value={value}>
      {children}
    </OrchestrationContext.Provider>
  );
}

export function useOrchestration() {
  const context = useContext(OrchestrationContext);
  if (!context) {
    throw new Error("useOrchestration must be used within OrchestrationProvider");
  }
  return context;
}
