export function classifyRecoveryInvitationRows(rows, expected = {}) {
  if (!Array.isArray(rows)) return { rowCountClass: 'INVALID' };
  if (rows.length === 0) return { rowCountClass: 'ZERO' };
  if (rows.length > 1) return { rowCountClass: 'MULTIPLE' };

  const [row] = rows;
  const metadata = row?.metadata && typeof row.metadata === 'object' && !Array.isArray(row.metadata)
    ? row.metadata
    : {};
  const deliveryStateClass = metadata.delivery_state === 'completed'
    ? 'COMPLETED'
    : metadata.delivery_state === 'unknown'
      ? 'UNKNOWN'
      : metadata.delivery_state === undefined ? 'MISSING' : 'OTHER';

  return {
    rowCountClass: 'ONE',
    requestIdMatches: metadata.request_id === expected.requestId,
    actorMatches: row?.created_by_user_id === expected.actorId,
    emailMatches: row?.email === expected.email,
    roleMatches: row?.role === expected.role,
    statusClass: row?.status === 'pending' ? 'PENDING' : row?.status === 'send_failed' ? 'SEND_FAILED' : 'OTHER',
    userIdPresent: typeof row?.admin_member_user_id === 'string' && row.admin_member_user_id.length > 0,
    userIdMatches: row?.admin_member_user_id === expected.targetId,
    reconciliationRequired: metadata.reconciliation_required === true,
    deliveryStateClass,
  };
}
