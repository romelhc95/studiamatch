export function isExpectedHttpFailure(testCase, diagnostic, expectedFailures) {
  return (expectedFailures[testCase.title] || []).some((expected) =>
    expected.status === diagnostic.status
      && expected.method === diagnostic.method
      && expected.origin === diagnostic.origin
      && expected.path === diagnostic.path
      && (!expected.afterLogout || diagnostic.beforeLogoutRequest === false && diagnostic.afterLogoutResponse === true));
}

export function findUncorrelatedConsoleResourceFailures(testCase, consoleFailures, httpDiagnostics, expectedFailures) {
  const consumedResponses = new Set();
  const uncorrelated = [];
  for (const failure of consoleFailures) {
    const candidates = httpDiagnostics
      .map((diagnostic, index) => ({ diagnostic, index }))
      .filter(({ diagnostic, index }) =>
        !consumedResponses.has(index)
          && diagnostic.status === failure.status
          && diagnostic.origin === failure.origin
          && diagnostic.path === failure.path
          && Number.isFinite(failure.observedOffsetMs)
          && Number.isFinite(diagnostic.responseOffsetMs)
          && Math.abs(diagnostic.responseOffsetMs - failure.observedOffsetMs) <= 1000);
    if (candidates.length !== 1
      || !isExpectedHttpFailure(testCase, candidates[0]?.diagnostic, expectedFailures)) {
      uncorrelated.push(failure);
      continue;
    }
    consumedResponses.add(candidates[0].index);
  }
  return uncorrelated;
}
