// StudIAMatch-Docs: .context/componentes/admin_portal.md#cola-editorial
export function canCommitAdminQueueResponse(requestId, latestRequestId) {
  return Number.isSafeInteger(requestId)
    && requestId > 0
    && requestId === latestRequestId;
}

export function nextAdminQueueRequestId(currentRequestId) {
  const current = Number.isSafeInteger(currentRequestId) && currentRequestId >= 0
    ? currentRequestId
    : 0;
  return current === Number.MAX_SAFE_INTEGER ? 1 : current + 1;
}
