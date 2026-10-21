const LOGIN_FAILURE_CODES = Object.freeze([
  'LOGIN_AAL_NOT_AAL2',
  'LOGIN_AUTH_COOKIE_MISSING',
  'LOGIN_ACTIVITY_COOKIE_MISSING',
]);

const INVITE_EARLY_ERROR_CODES = Object.freeze({
  csrf_rejected: 'INVITE_EARLY_CSRF_REJECTED',
  mfa_required: 'INVITE_EARLY_MFA_REQUIRED',
  unauthenticated: 'INVITE_EARLY_UNAUTHENTICATED',
  invalid_invitation: 'INVITE_EARLY_INVALID_INVITATION',
  quota_unavailable: 'INVITE_EARLY_QUOTA_UNAVAILABLE',
  quota_rate_limited: 'INVITE_EARLY_QUOTA_RATE_LIMITED',
  maintenance_mode: 'INVITE_EARLY_MAINTENANCE_MODE',
  reconciliation_required: 'INVITE_EARLY_RECONCILIATION_REQUIRED',
  duplicate_ready: 'INVITE_EARLY_DUPLICATE_READY',
  duplicate_pending: 'INVITE_EARLY_DUPLICATE_PENDING',
  resend_cooldown: 'INVITE_EARLY_RESEND_COOLDOWN',
  membership_blocked: 'INVITE_EARLY_MEMBERSHIP_BLOCKED',
  onboarding_in_progress: 'INVITE_EARLY_ONBOARDING_IN_PROGRESS',
  role_mismatch: 'INVITE_EARLY_ROLE_MISMATCH',
  auth_rate_limited: 'INVITE_EARLY_AUTH_RATE_LIMITED',
  unauthorized: 'INVITE_EARLY_UNAUTHORIZED',
  forbidden: 'INVITE_EARLY_FORBIDDEN',
  server_configuration_error: 'INVITE_EARLY_SERVER_CONFIGURATION_ERROR',
  rpc_gateway_unavailable: 'INVITE_EARLY_RPC_GATEWAY_UNAVAILABLE',
  rpc_failed: 'INVITE_EARLY_RPC_FAILED',
});

const INVITE_EARLY_FAILURE_CODES = Object.freeze([
  ...Object.values(INVITE_EARLY_ERROR_CODES),
  'INVITE_AUTH_HOLD_TIMEOUT',
  'INVITE_REQUEST_TRANSPORT_FAILURE',
  'INVITE_COMPLETED_BEFORE_AUTH_HOLD',
]);

export function classifyLoginResult({ status, aal, authCookie, activityCookie, errorCode } = {}) {
  if (status !== 200) {
    if (status === 403 && errorCode === 'csrf_rejected') return 'LOGIN_CSRF_REJECTED';
    return Number.isInteger(status) && status >= 100 && status <= 599
      ? `LOGIN_HTTP_STATUS_${status}`
      : 'LOGIN_HTTP_STATUS_INVALID';
  }
  if (aal !== 'aal2') return LOGIN_FAILURE_CODES[0];
  if (authCookie !== true) return LOGIN_FAILURE_CODES[1];
  if (activityCookie !== true) return LOGIN_FAILURE_CODES[2];
  return null;
}

export function isLoginFailureCode(value) {
  return value === 'LOGIN_CSRF_REJECTED'
    || LOGIN_FAILURE_CODES.includes(value)
    || (typeof value === 'string' && /^LOGIN_HTTP_STATUS_(?:[1-5][0-9]{2}|INVALID)$/.test(value));
}

export function classifyInviteEarlyResult({ status, errorCode } = {}) {
  if (typeof errorCode === 'string' && Object.hasOwn(INVITE_EARLY_ERROR_CODES, errorCode)) {
    return INVITE_EARLY_ERROR_CODES[errorCode];
  }
  if (Number.isInteger(status) && status >= 200 && status < 300) return 'INVITE_COMPLETED_BEFORE_AUTH_HOLD';
  return Number.isInteger(status) && status >= 100 && status <= 599
    ? `INVITE_EARLY_HTTP_${status}`
    : 'INVITE_EARLY_HTTP_INVALID';
}

export function classifyRecoveryReplayFailure({ status, errorCode } = {}) {
  const safeStatus = Number.isInteger(status) && status >= 100 && status <= 599 ? status : 'INVALID';
  const knownErrorCode = typeof errorCode === 'string' && Object.hasOwn(INVITE_EARLY_ERROR_CODES, errorCode);
  let errorCodeClass = 'ABSENT';
  if (safeStatus === 'INVALID') errorCodeClass = 'STATUS_INVALID';
  else if (knownErrorCode) errorCodeClass = 'ALLOWLISTED';
  else if (typeof errorCode === 'string' && errorCode.length > 0) errorCodeClass = 'UNRECOGNIZED';
  return {
    status: safeStatus,
    errorCodeClass,
    classification: safeStatus === 'INVALID'
      ? classifyInviteEarlyResult()
      : classifyInviteEarlyResult({ status, errorCode }),
  };
}

export function isIntegratedFailureCode(value) {
  return isLoginFailureCode(value)
    || INVITE_EARLY_FAILURE_CODES.includes(value)
    || value === 'PAGES_SUSPEND_CONTRACT_FAILED'
    || value === 'SIGNED_DISPATCHER_CONTRACT_FAILED'
    || value === 'RECOVERY_CONTRACT_FAILED'
    || (typeof value === 'string' && /^INVITE_EARLY_HTTP_(?:[1-5][0-9]{2}|INVALID)$/.test(value));
}
