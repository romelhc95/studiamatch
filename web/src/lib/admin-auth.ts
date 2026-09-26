'use client';

import { supabaseBrowserClient, SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL } from '@/lib/supabase';

const SESSION_COOKIE = 'studiamatch_admin_session';
const SESSION_AAL = 'studiamatch_admin_aal';

export type AdminRole = 'admin' | 'user' | 'authenticated' | 'anon';

export interface AdminSession {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
  aal: 'aal1' | 'aal2';
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  expires_at?: number;
  aal?: 'aal1' | 'aal2';
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

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const segment = token.split('.')[1];
    if (!segment) return null;
    const base64 = segment.replace(/-/g, '+').replace(/_/g, '/');
    const json = decodeURIComponent(
      atob(base64)
        .split('')
        .map((character) => `%${`00${character.charCodeAt(0).toString(16)}`.slice(-2)}`)
        .join('')
    );
    return JSON.parse(json) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function resolveAal(tokens: Pick<TokenResponse, 'aal' | 'access_token'>): 'aal1' | 'aal2' {
  if (tokens.aal === 'aal1' || tokens.aal === 'aal2') return tokens.aal;
  const payload = tokens.access_token ? decodeJwtPayload(tokens.access_token) : null;
  if (payload?.aal === 'aal1' || payload?.aal === 'aal2') return payload.aal;
  return 'aal1';
}

function getAdminPath(value: string | null): string {
  if (!value) return '/admin/';
  const normalized = value.startsWith('/') ? value : `/${value}`;
  if (normalized === '/admin' || normalized === '/admin/') return '/admin/';
  if (normalized.startsWith('/admin/edit')) return '/admin/edit/';
  if (normalized.startsWith('/admin/users')) return '/admin/users/';
  if (normalized.startsWith('/admin/accept-invite')) return '/admin/accept-invite/';
  if (normalized.startsWith('/admin/setup-password')) return '/admin/setup-password/';
  return '/admin/';
}

export function sanitizeAdminRedirect(value: string | null): string {
  return getAdminPath(value);
}

export function clearAdminSession(): void {
  if (typeof window === 'undefined') return;
  document.cookie = `${SESSION_COOKIE}=; Max-Age=0; Path=/; SameSite=Strict; Secure`;
  window.sessionStorage.removeItem(SESSION_AAL);
}

function storedAal(): 'aal1' | 'aal2' {
  if (typeof window === 'undefined') return 'aal1';
  const value = window.sessionStorage.getItem(SESSION_AAL);
  return value === 'aal2' ? 'aal2' : 'aal1';
}

function firstRpcRow<T>(result: unknown): T {
  const row = Array.isArray(result) ? result[0] : result;
  if (!row || typeof row !== 'object') throw new Error('Invalid onboarding response');
  return row as T;
}

function authErrorMessage(error: { message?: string; code?: string } | null): string {
  if (!error) return 'Authentication failed';
  if (error.code === 'otp_expired' || error.code === 'invalid_grant') return 'El enlace de invitación ya no es válido.';
  return error.message || 'Authentication failed';
}

function invitationAuthError(): Error {
  return new Error('El enlace de invitación es inválido, expiró o ya fue utilizado.');
}

export async function exchangeCodeForSession(code: string): Promise<TokenResponse> {
  const normalizedCode = code.trim();
  if (!normalizedCode) throw new Error('Missing invitation code');
  const { data, error } = await supabaseBrowserClient.auth.exchangeCodeForSession(normalizedCode);
  if (error || !data.session) throw invitationAuthError();
  const tokens: TokenResponse = {
    access_token: data.session.access_token,
    refresh_token: data.session.refresh_token,
    expires_in: data.session.expires_in,
    expires_at: data.session.expires_at,
    aal: resolveAal({ access_token: data.session.access_token }),
  };
  saveAdminSession(tokens);
  return tokens;
}

export async function consumeInviteSessionFromHash(hash: string): Promise<TokenResponse> {
  const value = hash.startsWith('#') ? hash.slice(1) : hash;
  const params = new URLSearchParams(value);
  const accessToken = params.get('access_token')?.trim() || '';
  const refreshToken = params.get('refresh_token')?.trim() || '';
  const expiresIn = Number(params.get('expires_in') || 3600);
  if (!accessToken || !refreshToken || !Number.isFinite(expiresIn) || expiresIn <= 0) {
    throw invitationAuthError();
  }
  const { data, error } = await supabaseBrowserClient.auth.setSession({
    access_token: accessToken,
    refresh_token: refreshToken,
  });
  if (error || !data.session) throw invitationAuthError();
  const tokens: TokenResponse = {
    access_token: data.session.access_token,
    refresh_token: data.session.refresh_token,
    expires_in: data.session.expires_in || expiresIn,
    expires_at: data.session.expires_at,
    aal: resolveAal({ access_token: data.session.access_token }),
  };
  saveAdminSession(tokens);
  return tokens;
}

export async function getAuthSession(): Promise<AdminSession | null> {
  const { data } = await supabaseBrowserClient.auth.getSession();
  if (!data.session) return null;
  return saveAdminSession({
    access_token: data.session.access_token,
    refresh_token: data.session.refresh_token,
    expires_in: data.session.expires_in,
    aal: storedAal(),
  });
}

export async function updateAdminPassword(password: string): Promise<void> {
  const { error } = await supabaseBrowserClient.auth.updateUser({ password });
  if (error) throw new Error(authErrorMessage(error));
}

export async function acceptCurrentInvitation(invitationId?: string | null): Promise<InvitationAcceptanceResult> {
  const result = await adminRpc('admin_accept_current_invitation', invitationId ? { p_invitation_id: invitationId } : {});
  return firstRpcRow<InvitationAcceptanceResult>(result);
}

export async function getOnboardingStatus(): Promise<OnboardingStatusResult> {
  const result = await adminRpc('admin_get_onboarding_status', {});
  return firstRpcRow<OnboardingStatusResult>(result);
}

export async function completePasswordSetup(): Promise<PasswordSetupResult> {
  const result = await adminRpc('admin_complete_password_setup', {});
  return firstRpcRow<PasswordSetupResult>(result);
}

export async function signOutAdmin(): Promise<void> {
  try {
    await supabaseBrowserClient.auth.signOut({ scope: 'local' });
  } finally {
    clearAdminSession();
  }
}

export function saveAdminSession(tokens: TokenResponse): AdminSession {
  const session: AdminSession = {
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
    expiresAt: Date.now() + tokens.expires_in * 1000,
    aal: resolveAal(tokens),
  };
  if (typeof window !== 'undefined') document.cookie = `${SESSION_COOKIE}=1; Path=/; SameSite=Strict; Secure`;
  if (typeof window !== 'undefined') window.sessionStorage.setItem(SESSION_AAL, session.aal);
  if (typeof window !== 'undefined') {
    const authStorageKey = Object.keys(window.sessionStorage).find((key) => key.endsWith('-auth-token') && !key.endsWith('-code-verifier'));
    const authSession = authStorageKey ? JSON.parse(window.sessionStorage.getItem(authStorageKey) || '{}') as Record<string, unknown> : null;
    if (authStorageKey && authSession) window.sessionStorage.setItem(authStorageKey, JSON.stringify({ ...authSession, aal: session.aal }));
  }
  return session;
}

async function getFreshSession(): Promise<AdminSession> {
  const { data, error } = await supabaseBrowserClient.auth.getSession();
  if (error || !data.session) throw new Error('No session');
  return saveAdminSession({
    access_token: data.session.access_token,
    refresh_token: data.session.refresh_token,
    expires_in: data.session.expires_in,
    aal: storedAal() === 'aal2' ? 'aal2' : resolveAal({ access_token: data.session.access_token }),
  });
}

async function adminRequest(path: string, options: RequestInit = {}): Promise<Response> {
  const session = await getFreshSession();
  return fetch(`${SUPABASE_URL}/rest/v1${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      apikey: SUPABASE_PUBLISHABLE_KEY,
      Authorization: `Bearer ${session.accessToken}`,
      ...options.headers,
    },
  });
}

void adminRequest;

export async function adminRpc(functionName: string, params: unknown): Promise<unknown> {
  const session = await getFreshSession();
  const response = await fetch(`${SUPABASE_URL}/rest/v1/rpc/${functionName}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      apikey: SUPABASE_PUBLISHABLE_KEY,
      Authorization: `Bearer ${session.accessToken}`,
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(error.message || `RPC ${functionName} failed: ${response.status}`);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return null;
}

export interface InviteMemberResult {
  success: boolean;
  user_id: string | null;
  email: string;
  invitation_id?: string | null;
  status?: string | null;
  resent?: boolean;
}

export async function inviteAdminMember(email: string, role: 'admin' | 'user'): Promise<InviteMemberResult> {
  const session = await getFreshSession();
  const response = await fetch(`${SUPABASE_URL}/functions/v1/admin-invite`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      apikey: SUPABASE_PUBLISHABLE_KEY,
      Authorization: `Bearer ${session.accessToken}`,
    },
    body: JSON.stringify({ email, role }),
  });
  const data = (await response.json().catch(() => ({}))) as Partial<InviteMemberResult> & { error?: string };
  if (!response.ok || data.success !== true) {
    throw new Error(data.error || `admin-invite failed: ${response.status}`);
  }
  return data as InviteMemberResult;
}

export async function listFactors(): Promise<AuthenticatorFactor[]> {
  const session = await getFreshSession();
  const response = await fetch(`${SUPABASE_URL}/auth/v1/factors`, {
    headers: { apikey: SUPABASE_PUBLISHABLE_KEY, Authorization: `Bearer ${session.accessToken}` },
  });
  if (!response.ok) throw new Error('Unable to list MFA factors');
  const data = (await response.json()) as { all?: AuthenticatorFactor[] };
  return data.all || [];
}

export async function enrollTotp(): Promise<TotpEnrollment> {
  const session = await getFreshSession();
  const response = await fetch(`${SUPABASE_URL}/auth/v1/factors`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', apikey: SUPABASE_PUBLISHABLE_KEY, Authorization: `Bearer ${session.accessToken}` },
    body: JSON.stringify({ factor_type: 'totp', friendly_name: 'StudIAMatch Admin' }),
  });
  if (!response.ok) throw new Error('Unable to enroll MFA');
  const data = (await response.json()) as {
    id?: string;
    totp?: { secret?: string | null; uri?: string | null; qr_code?: string | null };
    secret?: string | null;
    uri?: string | null;
    qr_code?: string | null;
  };
  const factorId = data.id;
  if (!factorId) throw new Error('MFA enrollment did not return a factor id');
  const nested = data.totp || {};
  return {
    factorId,
    secret: nested.secret ?? data.secret ?? null,
    uri: nested.uri ?? data.uri ?? null,
    qrCode: nested.qr_code ?? data.qr_code ?? null,
  };
}

export async function challengeTotp(factorId: string): Promise<{ id: string }> {
  const session = await getFreshSession();
  const response = await fetch(`${SUPABASE_URL}/auth/v1/factors/${factorId}/challenge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', apikey: SUPABASE_PUBLISHABLE_KEY, Authorization: `Bearer ${session.accessToken}` },
  });
  if (!response.ok) throw new Error('Unable to create MFA challenge');
  return response.json();
}

export async function verifyTotp(factorId: string, challengeId: string | null, code: string): Promise<TokenResponse> {
  const session = await getFreshSession();
  const response = await fetch(`${SUPABASE_URL}/auth/v1/factors/${factorId}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', apikey: SUPABASE_PUBLISHABLE_KEY, Authorization: `Bearer ${session.accessToken}` },
    body: JSON.stringify({ challenge_id: challengeId, code }),
  });
  if (!response.ok) throw new Error('Invalid MFA code');
  const data = (await response.json()) as TokenResponse;
  await supabaseBrowserClient.auth.setSession({
    access_token: data.access_token,
    refresh_token: data.refresh_token,
  });
  saveAdminSession(data);
  return data;
}

export async function unenrollTotp(factorId: string): Promise<void> {
  const session = await getFreshSession();
  const response = await fetch(`${SUPABASE_URL}/auth/v1/factors/${factorId}`, {
    method: 'DELETE',
    headers: { apikey: SUPABASE_PUBLISHABLE_KEY, Authorization: `Bearer ${session.accessToken}` },
  });
  if (!response.ok) throw new Error('Unable to revoke MFA');
}

export async function getAuthenticatorAssuranceLevel(): Promise<AssuranceResponse> {
  const session = await getFreshSession();
  const currentLevel = session.aal;
  return { currentLevel, nextLevel: currentLevel === 'aal1' ? 'aal2' : 'aal2' };
}

export async function supabaseAdminLogin(email: string, password: string): Promise<TokenResponse> {
  const { data, error } = await supabaseBrowserClient.auth.signInWithPassword({ email, password });
  if (error || !data.session) throw new Error(error?.message || 'Login failed');
  const tokens: TokenResponse = {
    access_token: data.session.access_token,
    refresh_token: data.session.refresh_token,
    expires_in: data.session.expires_in,
    expires_at: data.session.expires_at,
    aal: resolveAal({ access_token: data.session.access_token }),
  };
  saveAdminSession(tokens);
  return tokens;
}

export async function currentAdminRole(): Promise<AdminRole> {
  try {
    const result = await adminRpc('admin_current_user_role', {});
    const role = Array.isArray(result) ? result[0]?.admin_current_user_role : (result as { admin_current_user_role?: AdminRole })?.admin_current_user_role;
    if (role === 'admin' || role === 'user') return role;
    if (role === 'authenticated' || role === 'anon') return role;
    return 'anon';
  } catch {
    return 'anon';
  }
}

export async function requireActiveAdmin(): Promise<'admin' | 'user'> {
  const role = await currentAdminRole();
  if (role !== 'admin' && role !== 'user') {
    throw new Error('Not authorized');
  }
  return role;
}

export async function requireAdmin(): Promise<void> {
  const role = await currentAdminRole();
  if (role !== 'admin') {
    throw new Error('Admin required');
  }
}
