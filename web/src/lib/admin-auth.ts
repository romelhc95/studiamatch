'use client';

import { SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL } from '@/lib/supabase';

const STORAGE_KEY = 'studiamatch_admin_session';
const SESSION_COOKIE = 'studiamatch_admin_session';

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
  aal?: 'aal1' | 'aal2';
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

interface AuthError {
  message?: string;
  error_description?: string;
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
  return '/admin/';
}

export function sanitizeAdminRedirect(value: string | null): string {
  return getAdminPath(value);
}

export function clearAdminSession(): void {
  if (typeof window === 'undefined') return;
  window.sessionStorage.removeItem(STORAGE_KEY);
  document.cookie = `${SESSION_COOKIE}=; Max-Age=0; Path=/; SameSite=Strict; Secure`;
}

export async function signOutAdmin(): Promise<void> {
  const session = readAdminSession();
  try {
    if (session) {
      await fetch(`${SUPABASE_URL}/auth/v1/logout`, {
        method: 'POST',
        headers: { apikey: SUPABASE_PUBLISHABLE_KEY, Authorization: `Bearer ${session.accessToken}` },
      });
    }
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
  if (typeof window !== 'undefined') {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    document.cookie = `${SESSION_COOKIE}=1; Path=/; SameSite=Strict; Secure`;
  }
  return session;
}

function readAdminSession(): AdminSession | null {
  if (typeof window === 'undefined') return null;
  const raw = window.sessionStorage.getItem(STORAGE_KEY);
  if (!raw) return null;

  try {
    const session = JSON.parse(raw) as AdminSession;
    if (!session.accessToken || !session.refreshToken || !session.expiresAt || !session.aal) {
      clearAdminSession();
      return null;
    }
    return session;
  } catch {
    clearAdminSession();
    return null;
  }
}

async function refreshAdminSession(session: AdminSession): Promise<AdminSession> {
  const response = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=refresh_token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      apikey: SUPABASE_PUBLISHABLE_KEY,
      Authorization: `Bearer ${session.refreshToken}`,
    },
    body: JSON.stringify({ refresh_token: session.refreshToken }),
  });

  if (!response.ok) {
    throw new Error('Session expired');
  }

  const data = (await response.json()) as TokenResponse;
  data.aal = data.aal || session.aal;
  return saveAdminSession(data);
}

async function getFreshSession(): Promise<AdminSession> {
  const session = readAdminSession();
  if (!session) {
    throw new Error('No session');
  }

  if (Date.now() > session.expiresAt - 60000) {
    return refreshAdminSession(session);
  }

  return session;
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
  const response = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      apikey: SUPABASE_PUBLISHABLE_KEY,
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as AuthError;
    throw new Error(error.message || error.error_description || 'Login failed');
  }

  return response.json() as Promise<TokenResponse>;
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
