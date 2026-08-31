export const NOT_DETECTED = "Not detected from supplied repository evidence.";

export const REPO_STAGES = [
  "Repository",
  "Scanning",
  "Structure",
  "Dependencies",
  "Code Quality",
  "Issues",
  "AI Insights",
];

export function isDetectedList(list) {
  if (!Array.isArray(list) || list.length === 0) return false;
  if (list.length === 1 && String(list[0]).includes("Not detected")) {
    return false;
  }
  return true;
}

export function asList(list) {
  return isDetectedList(list) ? list : [];
}

export function repoStageState({
  selected,
  scanning,
  overview,
  analyzing,
  analysisReady,
  analysisError,
}) {
  const hasOverview = Boolean(overview && !overview.error && !overview.isHidden);
  const structure = hasOverview && isDetectedList(overview.structure);
  const deps =
    hasOverview &&
    (isDetectedList(overview.dependencies) || isDetectedList(overview.frameworks));
  const quality =
    hasOverview &&
    (Boolean(overview.architecture?.summary) ||
      isDetectedList(overview.testing) ||
      isDetectedList(overview.configuration) ||
      isDetectedList(overview.languages));

  let index = 0;
  if (!selected) return { index: 0, current: "Repository" };
  if (scanning || analyzing) index = 1;
  else if (analysisError) index = 5;
  else if (analysisReady) index = 6;
  else if (quality) index = 4;
  else if (deps) index = 3;
  else if (structure || hasOverview) index = 2;
  else index = 0;

  return { index, current: REPO_STAGES[index] };
}
