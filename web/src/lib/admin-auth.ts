'use client';

export const ADMIN_IDLE_TIMEOUT_MS = 30 * 60 * 1000;
export const ADMIN_ACTIVITY_EVENT_KEY = 'studiamatch_admin_activity_event';
export const ADMIN_LOGOUT_EVENT_KEY = 'studiamatch_admin_logout';
const ADMIN_LAST_ACTIVITY_KEY = 'studiamatch_admin_last_activity';

export type AdminRole = 'admin' | 'user' | 'authenticated' | 'anon';

export interface AdminSession {
  email: string | null;
  expiresAt: number | null;
  aal: 'aal1' | 'aal2';
}

export type OnboardingStatus = 'invited' | 'accepted' | 'password_pending' | 'ready' | 'expired' | 'revoked' | 'superseded' | 'send_failed' | null;

export interface OnboardingStatusResult {
  success: boolean;
  user_id: string | null;
  email: string | null;
  role: 'admin' | 'user' | null;
  account_status: OnboardingStatus;
  invitation_status: OnboardingStatus;
  invitation_id: string | null;
  expires_at: string | null;
  error_code: string | null;
}

export interface InvitationAcceptanceResult {
  success: boolean;
  invitation_id: string | null;
  member_id: string | null;
  account_status: OnboardingStatus;
  role: 'admin' | 'user' | null;
  error_code: string | null;
}

export interface PasswordSetupResult {
  success: boolean;
  member_id: string | null;
  account_status: OnboardingStatus;
  role: 'admin' | 'user' | null;
  error_code: string | null;
}

export interface AuthenticatorFactor {
  id: string;
  factor_type: 'totp';
  status: 'verified' | 'unverified';
}

export interface TotpEnrollment {
  factorId: string;
  secret: string | null;
  uri: string | null;
  qrCode: string | null;
}

interface AssuranceResponse {
  currentLevel: 'aal1' | 'aal2';
  nextLevel: 'aal1' | 'aal2';
}

interface ApiErrorPayload {
  code?: unknown;
  message?: unknown;
  error?: unknown;
  request_id?: unknown;
}

interface ApiResponse<T> {
  data?: T;
  session?: AdminSession | null;
  authenticated?: boolean;
  success?: boolean;
  error?: ApiErrorPayload | string;
  [key: string]: unknown;
}

export class MfaRequiredError extends Error {
  readonly code = 'mfa_required';

  constructor() {
    super('MFA aal2 required');
    this.name = 'MfaRequiredError';
  }
}

export class AdminApiError extends Error {
  constructor(
    message: string,
    readonly code: string | null,
    readonly requestId: string | null,
    readonly status: number | null,
  ) {
    super(message);
    this.name = 'AdminApiError';
  }
}

function isMfaRequiredMessage(value: unknown): boolean {
  return typeof value === 'string' && /(?:mfa_required|insufficient_aal|aal2\s+required|mfa\s+(?:aal2\s+)?required)/i.test(value);
}

export function isMfaRequiredError(reason: unknown): boolean {
  if (reason instanceof MfaRequiredError) return true;
  if (reason instanceof Error && isMfaRequiredMessage(reason.message)) return true;
  if (!reason || typeof reason !== 'object') return false;
  const candidate = reason as ApiErrorPayload;
  if (isMfaRequiredMessage(candidate.message) || isMfaRequiredMessage(candidate.code)) return true;
  if (candidate.error && typeof candidate.error === 'object') {
    const nested = candidate.error as ApiErrorPayload;
    return isMfaRequiredMessage(nested.message) || isMfaRequiredMessage(nested.code);
  }
  return isMfaRequiredMessage(candidate.error);
}

function errorFromPayload(payload: unknown, fallback: string, status: number | null = null): Error {
  if (isMfaRequiredError(payload)) return new MfaRequiredError();
  if (payload && typeof payload === 'object') {
    const candidate = payload as ApiErrorPayload;
    const nested = typeof candidate.error === 'object' && candidate.error
      ? candidate.error as ApiErrorPayload
      : null;
    const code = typeof nested?.code === 'string'
      ? nested.code
      : typeof candidate.code === 'string' ? candidate.code : null;
    const rawRequestId = typeof candidate.request_id === 'string'
      ? candidate.request_id
      : typeof nested?.request_id === 'string' ? nested.request_id : null;
    const requestId = rawRequestId && /^[A-Za-z0-9._:-]{1,100}$/.test(rawRequestId)
      ? rawRequestId
      : null;
    if (typeof candidate.error === 'object' && candidate.error) {
      if (typeof nested?.message === 'string' && nested.message) return new AdminApiError(nested.message, code, requestId, status);
      if (typeof nested?.code === 'string' && nested.code) return new AdminApiError(nested.code, code, requestId, status);
    }
    if (typeof candidate.message === 'string' && candidate.message) return new AdminApiError(candidate.message, code, requestId, status);
    if (typeof candidate.error === 'string' && candidate.error) return new AdminApiError(candidate.error, code, requestId, status);
    return new AdminApiError(fallback, code, requestId, status);
  }
  return new AdminApiError(fallback, null, null, status);
}

async function adminApi<T = ApiResponse<unknown>>(
  path: string,
  method: 'GET' | 'POST' = 'GET',
  body?: Record<string, unknown>,
  extraHeaders: Record<string, string> = {},
): Promise<T> {
  const response = await fetch(path, {
    method,
    credentials: 'same-origin',
    cache: 'no-store',
    headers: method === 'POST' ? { 'Content-Type': 'application/json', ...extraHeaders } : undefined,
    body: method === 'POST' ? JSON.stringify(body ?? {}) : undefined,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw errorFromPayload(payload, `Solicitud Admin falló: ${response.status}`, response.status);
  return payload as T;
}

function browserStorages(): Storage[] {
  if (typeof window === 'undefined') return [];
  const storages: Storage[] = [];
  try { storages.push(window.localStorage); } catch { /* Storage can be blocked. */ }
  try { storages.push(window.sessionStorage); } catch { /* Storage can be blocked. */ }
  return storages;
}

function clearLegacyBrowserTokens(broadcast = false): void {
  let removedAny = false;
  for (const storage of browserStorages()) {
    try {
      for (const key of Object.keys(storage)) {
        if (key.endsWith('-auth-token') || key.endsWith('-code-verifier') || key.endsWith('-flows-code-verifier')) {
          storage.removeItem(key);
          removedAny = true;
        }
      }
    } catch {
      // Continue clearing other browser storage even if this one is unavailable.
    }
  }
  if (broadcast && removedAny) {
    try {
      sharedNonSecretStorage()?.setItem(ADMIN_LOGOUT_EVENT_KEY, `${Date.now()}:legacy-session-cleared`);
    } catch {
      // The current tab still drops all legacy browser-held credentials.
    }
  }
}

// Existing browser-held sessions are intentionally not migrated. The user signs
// in again with the same account; no identity or onboarding state is recreated.
if (typeof window !== 'undefined') clearLegacyBrowserTokens(true);

function sharedNonSecretStorage(): Storage | null {
  if (typeof window === 'undefined') return null;
  try { return window.localStorage; } catch {
    try { return window.sessionStorage; } catch { return null; }
  }
}

function getAdminPath(value: string | null): string {
  if (!value) return '/admin/';
  const normalized = value.startsWith('/') ? value : `/${value}`;
  if (normalized === '/admin' || normalized === '/admin/') return '/admin/';
  if (normalized.startsWith('/admin/edit')) return '/admin/edit/';
  if (normalized.startsWith('/admin/users')) return '/admin/users/';
  if (normalized.startsWith('/admin/accept-invite')) return '/admin/accept-invite/';
  if (normalized.startsWith('/admin/setup-password')) return '/admin/setup-password/';
  if (normalized.startsWith('/admin/reset-password')) return '/admin/reset-password/';
  return '/admin/';
}

export function sanitizeAdminRedirect(value: string | null): string {
  return getAdminPath(value);
}

export function clearAdminSession(): void {
  clearLegacyBrowserTokens(false);
  const storage = sharedNonSecretStorage();
  if (!storage) return;
  try {
    storage.removeItem(ADMIN_LAST_ACTIVITY_KEY);
    storage.removeItem(ADMIN_ACTIVITY_EVENT_KEY);
  } catch {
    // Server logout remains authoritative when browser storage is unavailable.
  }
}

export function getAdminLastActivity(): number | null {
  const storage = sharedNonSecretStorage();
  if (!storage) return null;
  try {
    const raw = storage.getItem(ADMIN_LAST_ACTIVITY_KEY);
    if (!raw) return null;
    const value = Number(raw);
    return Number.isFinite(value) && value > 0 ? value : null;
  } catch {
    return null;
  }
}

export function recordAdminActivity(timestamp = Date.now()): void {
  const storage = sharedNonSecretStorage();
  if (!storage) return;
  try {
    storage.setItem(ADMIN_LAST_ACTIVITY_KEY, String(timestamp));
    storage.setItem(ADMIN_ACTIVITY_EVENT_KEY, `${timestamp}:${Math.random().toString(36).slice(2)}`);
  } catch {
    // The in-memory timeout still protects this tab if persistence is blocked.
  }
}

function firstRpcRow<T>(result: unknown): T {
  const row = Array.isArray(result) ? result[0] : result;
  if (!row || typeof row !== 'object') throw new Error('Invalid onboarding response');
  return row as T;
}

export async function getAuthSession(): Promise<AdminSession | null> {
  const result = await adminApi<ApiResponse<unknown>>('/api/admin/session');
  if (result.authenticated !== true || !result.session) return null;
  return result.session;
}

export async function touchAdminSession(): Promise<void> {
  await adminApi('/api/admin/activity', 'POST', {});
}

export async function getAuthenticatedUserEmail(): Promise<string | null> {
  try { return (await getAuthSession())?.email ?? null; } catch { return null; }
}

export async function supabaseAdminLogin(email: string, password: string): Promise<AdminSession> {
  const result = await adminApi<ApiResponse<unknown>>('/api/admin/auth/login', 'POST', { email, password });
  if (!result.session) throw new Error('No se pudo iniciar la sesión.');
  return result.session;
}

export async function updateAdminPassword(password: string): Promise<void> {
  await adminApi('/api/admin/auth/password', 'POST', { password });
}

export async function acceptCurrentInvitation(invitationId?: string | null): Promise<InvitationAcceptanceResult> {
  const result = await adminRpc('admin_accept_current_invitation', invitationId ? { p_invitation_id: invitationId } : {});
  return firstRpcRow<InvitationAcceptanceResult>(result);
}

export async function getOnboardingStatus(): Promise<OnboardingStatusResult> {
  return firstRpcRow<OnboardingStatusResult>(await adminRpc('admin_get_onboarding_status', {}));
}

export async function completePasswordSetup(): Promise<PasswordSetupResult> {
  return firstRpcRow<PasswordSetupResult>(await adminRpc('admin_complete_password_setup', {}));
}

export async function signOutAdmin(options: { broadcast?: boolean } = {}): Promise<void> {
  if (typeof window !== 'undefined' && options.broadcast !== false) {
    try {
      sharedNonSecretStorage()?.setItem(ADMIN_LOGOUT_EVENT_KEY, `${Date.now()}:${Math.random().toString(36).slice(2)}`);
    } catch {
      // Local sign-out continues if cross-tab signaling is unavailable.
    }
  }
  try {
    await adminApi('/api/admin/auth/logout', 'POST', {});
  } finally {
    clearAdminSession();
  }
}

export async function adminRpc(functionName: string, params: unknown): Promise<unknown> {
  if (!params || typeof params !== 'object' || Array.isArray(params)) throw new Error('Invalid RPC parameters');
  const result = await adminApi<ApiResponse<unknown>>('/api/admin/rpc', 'POST', {
    function: functionName,
    params: params as Record<string, unknown>,
  });
  return result.data ?? null;
}

export interface InviteMemberResult {
  success: boolean;
  user_id: string | null;
  email: string;
  invitation_id?: string | null;
  status?: string | null;
  resent?: boolean;
  recovery_sent?: boolean;
}

export async function inviteAdminMember(
  email: string,
  role: 'admin' | 'user',
  options: { resend?: boolean; requestId?: string } = {},
): Promise<InviteMemberResult> {
  const requestId = options.requestId || globalThis.crypto.randomUUID();
  const result = await adminApi<ApiResponse<unknown>>('/api/admin/invitations', 'POST', {
    email,
    role,
    resend: options.resend === true,
  }, { 'x-request-id': requestId });
  if (result.success !== true) throw errorFromPayload(result, 'No se pudo enviar la invitación.');
  return result as unknown as InviteMemberResult;
}

async function mfaRequest<T>(body: Record<string, unknown>): Promise<T> {
  return adminApi<T>('/api/admin/auth/mfa', 'POST', body);
}

export async function listFactors(): Promise<AuthenticatorFactor[]> {
  const result = await mfaRequest<{ factors: AuthenticatorFactor[] }>({ action: 'list' });
  return result.factors || [];
}

export async function enrollTotp(): Promise<TotpEnrollment> {
  const result = await mfaRequest<{ factor: { id: string; secret: string | null; uri: string | null; qr_code: string | null } }>({ action: 'enroll' });
  return {
    factorId: result.factor.id,
    secret: result.factor.secret,
    uri: result.factor.uri,
    qrCode: result.factor.qr_code,
  };
}

export async function challengeTotp(factorId: string): Promise<{ id: string }> {
  return mfaRequest<{ id: string }>({ action: 'challenge', factorId });
}

export async function verifyTotp(factorId: string, challengeId: string | null, code: string): Promise<void> {
  if (!challengeId) throw new Error('No hay un desafío MFA activo.');
  await mfaRequest({ action: 'verify', factorId, challengeId, code });
}

export async function unenrollTotp(factorId: string): Promise<void> {
  await mfaRequest({ action: 'unenroll', factorId });
}

export async function getAuthenticatorAssuranceLevel(): Promise<AssuranceResponse> {
  return mfaRequest<AssuranceResponse>({ action: 'assurance' });
}

export async function currentAdminRole(): Promise<AdminRole> {
  try {
    const result = await adminRpc('admin_current_user_role', {});
    const role = typeof result === 'string'
      ? result
      : Array.isArray(result)
        ? result[0]?.admin_current_user_role
        : (result as { admin_current_user_role?: AdminRole } | null)?.admin_current_user_role;
    if (role === 'admin' || role === 'user' || role === 'authenticated' || role === 'anon') return role;
    return 'anon';
  } catch {
    return 'anon';
  }
}

export async function requireActiveAdmin(): Promise<'admin' | 'user'> {
  const role = await currentAdminRole();
  if (role !== 'admin' && role !== 'user') throw new Error('Not authorized');
  return role;
}

export async function requireAdmin(): Promise<void> {
  if (await currentAdminRole() !== 'admin') throw new Error('Admin required');
}
