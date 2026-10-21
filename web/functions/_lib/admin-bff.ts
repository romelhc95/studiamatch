// StudIAMatch-Docs: .context/componentes/admin_runtime.md#bff-cookie-y-rpc-firmada
import {
  createServerClient,
  parseCookieHeader,
  serializeCookieHeader,
  type SetAllCookies,
} from '@supabase/ssr';
import type { Session, SupabaseClient, User } from '@supabase/supabase-js';
import { createApiKeyOnlyFetch } from '../../src/lib/supabase-transport';
import { checkAdminQuota, trustedQuotaIp, type QuotaEnv } from './admin-quota';

export interface AdminBffEnv extends QuotaEnv {
  SUPABASE_URL?: string;
  NEXT_PUBLIC_SUPABASE_URL?: string;
  NEXT_SUPABASE_PUBLISHABLE_KEY?: string;
  ADMIN_SESSION_ACTIVITY_HMAC_KEY?: string;
  ADMIN_RPC_GATEWAY_HMAC_KEY?: string;
  ADMIN_RPC_GATEWAY_KEY_ID?: string;
  ADMIN_BFF_ALLOW_LOCAL_AUTH_MOCK?: string;
  ADMIN_BFF_ALLOW_LOCALHOST?: string;
  ADMIN_ALLOWED_HOSTS?: string;
  ADMIN_BFF_SAFE_SUSPEND?: string;
}

export interface AdminBffContext {
  request: Request;
  env: AdminBffEnv;
  next: () => Promise<Response>;
}

interface CookieState {
  headers: Headers;
  setCookies: string[];
}

interface ServerSessionSummary {
  email: string | null;
  aal: 'aal1' | 'aal2';
  expiresAt: number | null;
}

interface AuthenticatedSession {
  user: User;
  session: Session;
  sessionId: string;
}

interface BoundSessionSummary {
  summary: ServerSessionSummary;
  sessionId: string;
}

const ADMIN_AUTH_COOKIE = '__Host-studiamatch-admin-auth';
const ADMIN_ACTIVITY_COOKIE = '__Host-studiamatch-admin-activity';
const CALLBACK_CSRF_COOKIE = '__Host-studiamatch-admin-callback-csrf';
const ADMIN_IDLE_TIMEOUT_MS = 30 * 60 * 1000;
const ADMIN_COOKIE_MAX_AGE_SECONDS = Math.floor(ADMIN_IDLE_TIMEOUT_MS / 1000);
const CALLBACK_CSRF_MAX_AGE_SECONDS = 5 * 60;
const MAX_BODY_BYTES = 64 * 1024;
const MAX_CALLBACK_QUERY_CHARS = 4096;

// BFF_USER_SESSION_JWT_RPC_ALLOWLIST_EXCEPTION: Supabase SSR reads the HttpOnly
// session and permits user-scoped Data API calls only through this RPC list.
const ADMIN_RPC_ALLOWLIST = new Set([
  'admin_current_user_role',
  'admin_accept_current_invitation',
  'admin_get_onboarding_status',
  'admin_complete_password_setup',
  'admin_get_course_audit',
  'admin_get_course_editorial',
  'admin_update_course',
  'admin_set_course_availability',
  'admin_publish_course',
  'admin_unpublish_course',
  'admin_archive_course',
  'admin_update_quality_status',
  'admin_get_course_queue_facets',
  'admin_get_course_queue_filtered',
  'admin_count_course_queue_filtered',
  'admin_list_members_onboarding',
  'admin_update_member',
]);

const ADMIN_RPC_READS = new Set([
  'admin_current_user_role',
  'admin_get_onboarding_status',
  'admin_get_course_audit',
  'admin_get_course_editorial',
  'admin_get_course_queue_facets',
  'admin_get_course_queue_filtered',
  'admin_count_course_queue_filtered',
  'admin_list_members_onboarding',
  'admin_get_course_queue',
  'admin_count_course_queue',
  'admin_list_members',
]);

const SAFE_INVITE_ERROR_CODES = new Set([
  'quota_rate_limited',
  'quota_unavailable',
  'maintenance_mode',
  'reconciliation_required',
  'auth_rate_limited',
  'unauthorized',
  'forbidden',
  'mfa_required',
]);

function baseHeaders(state?: CookieState): Headers {
  const headers = new Headers(state?.headers);
  headers.set('Cache-Control', 'private, no-store, max-age=0');
  headers.set('Pragma', 'no-cache');
  headers.set('Expires', '0');
  headers.set('Referrer-Policy', 'no-referrer');
  headers.set('X-Content-Type-Options', 'nosniff');
  headers.set('Vary', 'Cookie, Origin');
  for (const cookie of state?.setCookies ?? []) headers.append('Set-Cookie', cookie);
  return headers;
}

function jsonResponse(
  state: CookieState,
  body: unknown,
  status = 200,
): Response {
  const headers = baseHeaders(state);
  headers.set('Content-Type', 'application/json; charset=utf-8');
  return new Response(JSON.stringify(body), { status, headers });
}

function requestIdFor(request: Request): string {
  const supplied = request.headers.get('x-request-id')?.trim() || '';
  return /^[A-Za-z0-9._:-]{1,100}$/.test(supplied) ? supplied : crypto.randomUUID();
}

function adminHmacKeysInvalid(env: AdminBffEnv): boolean {
  const quotaKey = env.ADMIN_QUOTA_HMAC_KEY;
  const gatewayKey = env.ADMIN_RPC_GATEWAY_HMAC_KEY;
  const activityKey = env.ADMIN_SESSION_ACTIVITY_HMAC_KEY;
  return Boolean(
    (quotaKey && gatewayKey && quotaKey === gatewayKey)
    || !activityKey
    || new TextEncoder().encode(activityKey).byteLength < 32
    || activityKey === quotaKey
    || activityKey === gatewayKey,
  );
}

function redirectResponse(
  state: CookieState,
  url: URL,
  pathname: string,
  query = '',
): Response {
  const headers = baseHeaders(state);
  headers.set('Location', `${url.origin}${pathname}${query}`);
  return new Response(null, { status: 303, headers });
}

function createCookieState(request: Request, env: AdminBffEnv): {
  client: SupabaseClient;
  state: CookieState;
} {
  const configuredUrl = (env.SUPABASE_URL || env.NEXT_PUBLIC_SUPABASE_URL || '').trim();
  const publishableKey = (env.NEXT_SUPABASE_PUBLISHABLE_KEY || '').trim();
  if (
    !configuredUrl
    || !publishableKey.startsWith('sb_publishable_')
    || publishableKey.length <= 'sb_publishable_'.length
  ) {
    throw new Error('Admin BFF server configuration is incomplete.');
  }

  const supabaseUrl = new URL(configuredUrl);
  const localMockAllowed = env.ADMIN_BFF_ALLOW_LOCAL_AUTH_MOCK === 'true';
  const isSupabaseHost = /^[a-z0-9-]+\.supabase\.co$/i.test(supabaseUrl.hostname);
  const isLocalMock = localMockAllowed && supabaseUrl.protocol === 'http:'
    && ['localhost', '127.0.0.1'].includes(supabaseUrl.hostname);
  if ((!isSupabaseHost || supabaseUrl.protocol !== 'https:') && !isLocalMock) {
    throw new Error('Admin BFF Supabase URL is not an approved HTTPS project URL.');
  }
  if (
    supabaseUrl.pathname !== '/'
    || supabaseUrl.username
    || supabaseUrl.password
    || supabaseUrl.search
    || supabaseUrl.hash
  ) {
    throw new Error('Admin BFF Supabase URL contains unsupported components.');
  }

  const state: CookieState = { headers: new Headers(), setCookies: [] };
  const projectRef = isSupabaseHost
    ? supabaseUrl.hostname.slice(0, -'.supabase.co'.length)
    : 'local';
  const client = createServerClient(supabaseUrl.origin, publishableKey, {
    global: { fetch: createApiKeyOnlyFetch(publishableKey, fetch, {
      projectOrigin: supabaseUrl.origin,
      rpcAllowlist: ADMIN_RPC_ALLOWLIST,
      rpcGateway: {
        projectRef,
        keyId: env.ADMIN_RPC_GATEWAY_KEY_ID || '',
        hmacKey: env.ADMIN_RPC_GATEWAY_HMAC_KEY || '',
      },
    }) },
    cookieOptions: {
      name: ADMIN_AUTH_COOKIE,
      path: '/',
      sameSite: 'lax',
      secure: true,
      httpOnly: true,
    },
    cookies: {
      // Keep the verified user snapshot in the HttpOnly cookie. The SSR
      // tokens-only mode puts user data in per-request memory storage, which
      // cannot supply MFA assurance checks on a later Pages Function request.
      getAll: () => parseCookieHeader(request.headers.get('Cookie') || '')
        .filter((cookie): cookie is { name: string; value: string } => typeof cookie.value === 'string'),
      setAll: ((cookies, responseHeaders) => {
        for (const [name, value] of Object.entries(responseHeaders)) {
          state.headers.set(name, value);
        }
        for (const cookie of cookies) {
          // Force host-only, HttpOnly cookies regardless of SDK defaults.
          const options = { ...cookie.options };
          delete options.domain;
          state.setCookies.push(serializeCookieHeader(cookie.name, cookie.value, {
            ...options,
            path: '/',
            sameSite: 'lax',
            secure: true,
            httpOnly: true,
            maxAge: options.maxAge === 0 ? 0 : ADMIN_COOKIE_MAX_AGE_SECONDS,
          }));
        }
      }) satisfies SetAllCookies,
    },
    auth: {
      flowType: 'pkce',
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: false,
    },
  });
  return { client, state };
}

function activityPayload(timestamp: string, sessionId: string): ArrayBuffer {
  return new TextEncoder().encode(`studiamatch-admin-activity-v1:${sessionId}:${timestamp}`).buffer as ArrayBuffer;
}

async function importActivitySigningKey(key: string, usages: KeyUsage[]): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(key),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    usages,
  );
}

function bytesToHex(bytes: Uint8Array): string {
  return [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

function hexToBytes(hex: string): ArrayBuffer {
  const bytes = new Uint8Array(hex.length / 2);
  for (let index = 0; index < bytes.length; index += 1) {
    bytes[index] = Number.parseInt(hex.slice(index * 2, index * 2 + 2), 16);
  }
  return bytes.buffer as ArrayBuffer;
}

async function appendActivityCookie(
  state: CookieState,
  signingKey: string,
  sessionId: string,
  timestamp = Date.now(),
): Promise<void> {
  const canonicalTimestamp = String(timestamp);
  const key = await importActivitySigningKey(signingKey, ['sign']);
  const signature = new Uint8Array(await crypto.subtle.sign(
    'HMAC', key, activityPayload(canonicalTimestamp, sessionId),
  ));
  state.setCookies = state.setCookies.filter(
    (cookie) => !cookie.startsWith(`${ADMIN_ACTIVITY_COOKIE}=`),
  );
  state.setCookies.push(serializeCookieHeader(ADMIN_ACTIVITY_COOKIE, `${canonicalTimestamp}.${bytesToHex(signature)}`, {
    path: '/',
    maxAge: ADMIN_COOKIE_MAX_AGE_SECONDS,
    sameSite: 'lax',
    secure: true,
    httpOnly: true,
  }));
}

// Only SDK-issued session changes may write Auth cookies. Echoing a request's
// cookie on reads races MFA verification and can overwrite the new AAL2 session
// with the earlier AAL1 token. Activity remains sliding; Auth expiry is bounded.

function clearActivityCookie(state: CookieState): void {
  state.setCookies.push(serializeCookieHeader(ADMIN_ACTIVITY_COOKIE, '', {
    path: '/',
    maxAge: 0,
    expires: new Date(0),
    sameSite: 'lax',
    secure: true,
    httpOnly: true,
  }));
}

async function activityIsFresh(request: Request, signingKey: string, sessionId: string): Promise<boolean> {
  const activity = parseCookieHeader(request.headers.get('Cookie') || '')
    .find((cookie) => cookie.name === ADMIN_ACTIVITY_COOKIE)?.value;
  const match = /^(\d{13})\.([a-f0-9]{64})$/.exec(activity || '');
  if (!match) return false;
  const timestamp = Number(match[1]);
  const now = Date.now();
  if (!Number.isSafeInteger(timestamp) || timestamp > now + 30_000 || now - timestamp > ADMIN_IDLE_TIMEOUT_MS) {
    return false;
  }
  try {
    const key = await importActivitySigningKey(signingKey, ['verify']);
    return await crypto.subtle.verify(
      'HMAC', key, hexToBytes(match[2]), activityPayload(match[1], sessionId),
    );
  } catch {
    return false;
  }
}

function sessionIdFromAccessToken(accessToken: string, userId: string): string | null {
  if (accessToken.length > 16_384) return null;
  const parts = accessToken.split('.');
  if (parts.length !== 3 || !/^[A-Za-z0-9_-]+$/.test(parts[1]) || parts[1].length % 4 === 1) return null;
  try {
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const binary = atob(base64 + '='.repeat((4 - (base64.length % 4)) % 4));
    const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
    const claims = JSON.parse(new TextDecoder().decode(bytes)) as Record<string, unknown>;
    const sessionId = claims.session_id;
    if (
      claims.sub !== userId
      || typeof sessionId !== 'string'
      || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(sessionId)
    ) return null;
    return sessionId;
  } catch {
    return null;
  }
}

async function authenticatedSession(client: SupabaseClient): Promise<AuthenticatedSession | null> {
  const { data: userData, error: userError } = await client.auth.getUser();
  if (userError || !userData.user) return null;
  const { data: sessionData, error: sessionError } = await client.auth.getSession();
  const user = userData.user;
  const session = sessionData.session;
  if (userError || sessionError || !user || !session || session.user.id !== user.id) return null;
  const sessionId = sessionIdFromAccessToken(session.access_token, user.id);
  if (!sessionId) return null;
  return { user, session, sessionId };
}

function sameOriginMutation(request: Request): boolean {
  const origin = request.headers.get('Origin');
  if (!origin) return false;
  try {
    if (new URL(origin).origin !== new URL(request.url).origin) return false;
  } catch {
    return false;
  }
  const fetchSite = request.headers.get('Sec-Fetch-Site');
  return fetchSite !== 'cross-site';
}

function sameOriginSessionRead(request: Request): boolean {
  if (request.headers.get('Sec-Fetch-Site') !== 'same-origin') return false;
  const origin = request.headers.get('Origin');
  if (!origin) return true;
  try {
    return new URL(origin).origin === new URL(request.url).origin;
  } catch {
    return false;
  }
}

async function readJsonObject(request: Request): Promise<Record<string, unknown> | null> {
  if (!request.headers.get('Content-Type')?.toLowerCase().startsWith('application/json')) return null;
  const declaredLength = Number(request.headers.get('Content-Length') || 0);
  if (declaredLength > MAX_BODY_BYTES) return null;
  if (!request.body) return null;

  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > MAX_BODY_BYTES) {
      await reader.cancel();
      return null;
    }
    chunks.push(value);
  }

  try {
    const bytes = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    const value: unknown = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
    if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
    return value as Record<string, unknown>;
  } catch {
    return null;
  }
}

async function readCallbackForm(request: Request): Promise<Record<string, unknown> | null> {
  if (!request.headers.get('Content-Type')?.toLowerCase().startsWith('application/x-www-form-urlencoded')) return null;
  const declaredLength = Number(request.headers.get('Content-Length') || 0);
  if (declaredLength > MAX_BODY_BYTES || !request.body) return null;

  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > MAX_BODY_BYTES) {
      await reader.cancel();
      return null;
    }
    chunks.push(value);
  }

  try {
    const bytes = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    const params = new URLSearchParams(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
    const allowedKeys = new Set(['type', 'code', 'token_hash', 'callback_csrf']);
    if ([...params.keys()].some((key) => !allowedKeys.has(key))) return null;
    if (['type', 'code', 'token_hash', 'callback_csrf'].some((key) => params.getAll(key).length > 1)) return null;
    return {
      type: params.get('type'),
      code: params.get('code'),
      token_hash: params.get('token_hash'),
      callback_csrf: params.get('callback_csrf'),
    };
  } catch {
    return null;
  }
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character] || character);
}

function createCallbackCsrfToken(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  const entropy = [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('');
  return `${Date.now()}.${entropy}`;
}

function clearCallbackCsrfCookie(state: CookieState): void {
  state.setCookies.push(serializeCookieHeader(CALLBACK_CSRF_COOKIE, '', {
    path: '/',
    maxAge: 0,
    expires: new Date(0),
    sameSite: 'strict',
    secure: true,
    httpOnly: true,
  }));
}

function callbackCsrfMatches(request: Request, body: Record<string, unknown>): boolean {
  const submitted = typeof body.callback_csrf === 'string' ? body.callback_csrf : '';
  if (!/^\d{13}\.[a-f0-9]{64}$/.test(submitted)) return false;
  const issuedAt = Number(submitted.slice(0, 13));
  const ageMs = Date.now() - issuedAt;
  if (!Number.isFinite(issuedAt) || ageMs < -30_000 || ageMs > CALLBACK_CSRF_MAX_AGE_SECONDS * 1000) return false;
  const cookies = parseCookieHeader(request.headers.get('Cookie') || '')
    .filter((cookie): cookie is { name: string; value: string } => cookie.name === CALLBACK_CSRF_COOKIE && typeof cookie.value === 'string');
  if (cookies.length !== 1) return false;
  const cookieToken = cookies[0].value;
  if (!/^\d{13}\.[a-f0-9]{64}$/.test(cookieToken) || cookieToken.length !== submitted.length) return false;
  let difference = 0;
  for (let index = 0; index < submitted.length; index += 1) {
    difference |= submitted.charCodeAt(index) ^ cookieToken.charCodeAt(index);
  }
  return difference === 0;
}

function callbackMutationOriginAllowed(request: Request): boolean {
  if (request.headers.get('Sec-Fetch-Site') === 'cross-site') return false;
  const origin = request.headers.get('Origin');
  if (!origin || origin === 'null') return true;
  try {
    return new URL(origin).origin === new URL(request.url).origin;
  } catch {
    return false;
  }
}

function callbackConfirmationResponse(
  type: 'invite' | 'recovery',
  credential: { name: 'code' | 'token_hash'; value: string },
): Response {
  const csrfToken = createCallbackCsrfToken();
  const label = type === 'invite' ? 'Continuar con la invitación' : 'Continuar para restablecer la contraseña';
  const heading = type === 'invite' ? 'Confirma tu invitación' : 'Confirma el restablecimiento';
  const description = type === 'invite'
    ? 'Selecciona el botón para validar el enlace y continuar con tu acceso editorial.'
    : 'Selecciona el botón para validar el enlace y cambiar tu contraseña.';
  const body = `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${heading} · StudIAMatch</title></head><body><main><h1>${heading}</h1><p>${description}</p><form method="post" action="/api/admin/auth/callback"><input type="hidden" name="type" value="${type}"><input type="hidden" name="${credential.name}" value="${escapeHtml(credential.value)}"><input type="hidden" name="callback_csrf" value="${csrfToken}"><button type="submit">${label}</button></form></main></body></html>`;
  const state: CookieState = { headers: new Headers(), setCookies: [] };
  state.setCookies.push(serializeCookieHeader(CALLBACK_CSRF_COOKIE, csrfToken, {
    path: '/',
    maxAge: CALLBACK_CSRF_MAX_AGE_SECONDS,
    sameSite: 'strict',
    secure: true,
    httpOnly: true,
  }));
  const headers = baseHeaders(state);
  headers.set('Content-Type', 'text/html; charset=utf-8');
  headers.set('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'");
  headers.set('X-Frame-Options', 'DENY');
  headers.set('Origin-Agent-Cluster', '?1');
  return new Response(body, { status: 200, headers });
}

function callbackErrorResponse(): Response {
  const state: CookieState = { headers: new Headers(), setCookies: [] };
  const headers = baseHeaders(state);
  headers.set('Content-Type', 'text/html; charset=utf-8');
  headers.set('Content-Security-Policy', "default-src 'none'; base-uri 'none'; frame-ancestors 'none'");
  headers.set('X-Frame-Options', 'DENY');
  headers.set('Origin-Agent-Cluster', '?1');
  return new Response(
    '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Enlace no disponible · StudIAMatch</title></head><body><main><h1>Enlace no disponible</h1><p>El enlace es inválido, expiró o ya fue utilizado. Solicita uno nuevo al administrador.</p></main></body></html>',
    { status: 200, headers },
  );
}

function clearServerAuthCookies(request: Request,state: CookieState): void {
  const names=new Set([ADMIN_AUTH_COOKIE,`${ADMIN_AUTH_COOKIE}-code-verifier`]);
  for(const part of (request.headers.get('Cookie') || '').split(';')) {
    const name=part.trim().split('=')[0];
    if(/^__Host-studiamatch-admin-auth(?:-code-verifier)?\.\d{1,3}$/.test(name) && names.size<64) names.add(name);
  }
  for(const name of names) state.setCookies.push(serializeCookieHeader(name,'',{
    path:'/',maxAge:0,secure:true,httpOnly:true,sameSite:'lax',
  }));
}

async function verifiedUser(
  client: SupabaseClient,
  request: Request,
  state: CookieState,
  signingKey: string,
) {
  const authenticated = await authenticatedSession(client);
  if (!authenticated || !await activityIsFresh(request, signingKey, authenticated.sessionId)) {
    clearServerAuthCookies(request,state);
    clearActivityCookie(state);
    return null;
  }
  await appendActivityCookie(state, signingKey, authenticated.sessionId);
  return authenticated.user;
}

async function aal2(client: SupabaseClient): Promise<boolean> {
  const { data, error } = await client.auth.mfa.getAuthenticatorAssuranceLevel();
  return !error && data?.currentLevel === 'aal2';
}

function safeAuthMessage(status: number): string {
  if (status === 429) return 'Demasiados intentos. Espera antes de volver a intentarlo.';
  return 'No se pudo autenticar la cuenta. Verifica los datos o solicita ayuda al administrador.';
}

async function sessionSummary(
  client: SupabaseClient,
  authenticated?: AuthenticatedSession,
): Promise<BoundSessionSummary | null> {
  const current = authenticated || await authenticatedSession(client);
  if (!current) return null;
  const { data: assuranceData } = await client.auth.mfa.getAuthenticatorAssuranceLevel();
  return {
    sessionId: current.sessionId,
    summary: {
      email: current.user.email?.trim() || null,
      aal: assuranceData?.currentLevel === 'aal2' ? 'aal2' : 'aal1',
      expiresAt: current.session.expires_at ? current.session.expires_at * 1000 : null,
    },
  };
}

async function routeMutation(
  context: AdminBffContext,
  client: SupabaseClient,
  state: CookieState,
  pathname: string,
): Promise<Response> {
  const request = context.request;
  const isCallback = pathname === '/api/admin/auth/callback';
  const body = pathname === '/api/admin/auth/callback'
    ? await readCallbackForm(request)
    : await readJsonObject(request);
  if (!body) return jsonResponse(state, { error: { code: 'invalid_request', message: 'Solicitud inválida.' } }, 400);
  if (isCallback) {
    if (!callbackMutationOriginAllowed(request) || !callbackCsrfMatches(request, body)) {
      return jsonResponse(state, { error: { code: 'csrf_rejected' } }, 403);
    }
    clearCallbackCsrfCookie(state);
  } else if (!sameOriginMutation(request)) {
    return jsonResponse(state, { error: { code: 'csrf_rejected' } }, 403);
  }

  if (pathname === '/api/admin/auth/login') {
    const email = typeof body.email === 'string' ? body.email.trim().toLowerCase() : '';
    const password = typeof body.password === 'string' ? body.password : '';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || password.length < 1 || password.length > 1024) {
      return jsonResponse(state, { error: { code: 'invalid_credentials', message: 'Revisa el email y la contraseña.' } }, 400);
    }
    const ip = trustedQuotaIp(request);
    if (!ip) return jsonResponse(state, { error: { code: 'quota_unavailable' } }, 503);
    const limited = await checkAdminQuota(request, context.env, [
      { kind: 'login-ip', identity: ip },
      { kind: 'login-account-ip', identity: `${email}:${ip}`, shardIdentity: ip },
    ]);
    if (limited) return limited;
    const { error } = await client.auth.signInWithPassword({ email, password });
    if (error) {
      const status = error.status === 429 ? 429 : 401;
      return jsonResponse(state, { error: { code: status === 429 ? 'rate_limited' : 'invalid_credentials', message: safeAuthMessage(status) } }, status);
    }
    const session = await sessionSummary(client);
    if (!session) return jsonResponse(state, { error: { code: 'session_unavailable' } }, 401);
    await appendActivityCookie(state, context.env.ADMIN_SESSION_ACTIVITY_HMAC_KEY!, session.sessionId);
    return jsonResponse(state, { success: true, session: session.summary });
  }

  if (pathname === '/api/admin/auth/callback') {
    const ip = trustedQuotaIp(request);
    if (!ip) return jsonResponse(state, { error: { code: 'quota_unavailable' } }, 503);
    const limited = await checkAdminQuota(request, context.env, [{ kind: 'callback', identity: ip }]);
    if (limited) return limited;
    const type = body.type;
    const code = typeof body.code === 'string' ? body.code.trim() : '';
    const tokenHash = typeof body.token_hash === 'string' ? body.token_hash.trim() : '';
    const callbackUrl = new URL(request.url);
    if (
      (type !== 'invite' && type !== 'recovery')
      || (Boolean(code) === Boolean(tokenHash))
      || (code && !/^[A-Za-z0-9._~-]{1,2048}$/.test(code))
      || (tokenHash && !/^[A-Za-z0-9_-]{20,512}$/.test(tokenHash))
    ) {
      return redirectResponse(state, callbackUrl, '/admin/auth/callback/', '?error=invalid');
    }
    const result = tokenHash
      ? await client.auth.verifyOtp({ token_hash: tokenHash, type })
      : await client.auth.exchangeCodeForSession(code);
    if (result.error) return redirectResponse(state, callbackUrl, '/admin/auth/callback/', '?error=invalid');
    const authenticated = await authenticatedSession(client);
    if (!authenticated) return redirectResponse(state, callbackUrl, '/admin/auth/callback/', '?error=invalid');
    await appendActivityCookie(state, context.env.ADMIN_SESSION_ACTIVITY_HMAC_KEY!, authenticated.sessionId);
    if (type === 'recovery') return redirectResponse(state, callbackUrl, '/admin/reset-password/');
    return redirectResponse(state, callbackUrl, '/admin/auth/callback/', '?flow=invite');
  }

  const user = await verifiedUser(client, request, state, context.env.ADMIN_SESSION_ACTIVITY_HMAC_KEY!);
  if (!user) return jsonResponse(state, { error: { code: 'unauthenticated' } }, 401);

  if (pathname === '/api/admin/activity') {
    return jsonResponse(state, { success: true });
  }

  if (pathname === '/api/admin/rpc') {
    const functionName = typeof body.function === 'string' ? body.function : '';
    const params = body.params;
    if (!ADMIN_RPC_ALLOWLIST.has(functionName) || !params || typeof params !== 'object' || Array.isArray(params)) {
      return jsonResponse(state, { error: { code: 'rpc_not_allowed' } }, 400);
    }
    const gatewayKey = context.env.ADMIN_RPC_GATEWAY_HMAC_KEY || '';
    const gatewayKeyId = context.env.ADMIN_RPC_GATEWAY_KEY_ID || '';
    if (new TextEncoder().encode(gatewayKey).byteLength < 32 || !/^[A-Za-z0-9._-]{1,32}$/.test(gatewayKeyId)) {
      const response = jsonResponse(state, { error: { code: 'rpc_gateway_unavailable' } }, 503);
      response.headers.set('Retry-After', '30');
      return response;
    }
    const quotaKind = ADMIN_RPC_READS.has(functionName) ? 'rpc-read' : 'rpc-write';
    const rpcQuota = await checkAdminQuota(request, context.env, [{ kind: quotaKind, identity: user.id }]);
    if (rpcQuota) return rpcQuota;
    try {
      const { data, error, status: rpcStatus } = await client.rpc(functionName, params as Record<string, unknown>);
      if (error) {
        if (error.code === 'quota_rate_limited' || error.code === 'quota_unavailable') {
          const retry = Number(error.details);
          const response = jsonResponse(state, { error: { code: error.code } }, error.code === 'quota_rate_limited' ? 429 : 503);
          response.headers.set('Retry-After', String(Number.isInteger(retry) && retry>=1 && retry<=86400 ? retry : 30));
          return response;
        }
        const rowError = Array.isArray(error) && error[0] && typeof error[0] === 'object'
          ? (error[0] as { error?: unknown; error_code?: unknown }).error || (error[0] as { error_code?: unknown }).error_code : '';
        const mfaRequired = rowError === 'mfa_required' || /mfa_required|insufficient_aal|aal2 required/i.test(`${error.code || ''} ${error.message || ''}`);
        return jsonResponse(state, {
          error: {
            code: mfaRequired ? 'mfa_required' : 'rpc_failed',
            message: mfaRequired ? 'Se requiere MFA para esta operación.' : 'No se pudo completar la operación administrativa.',
          },
        }, mfaRequired ? 403 : rpcStatus === 403 ? 403 : rpcStatus === 400 ? 400 : rpcStatus === 503 ? 503 : 502);
      }
      return jsonResponse(state, { data });
    } catch {
      return jsonResponse(state, { error: { code: 'rpc_failed', message: 'No se pudo completar la operación administrativa.' } }, 502);
    }
  }

  if (pathname === '/api/admin/invitations') {
    if (!await aal2(client)) return jsonResponse(state, { error: { code: 'mfa_required', message: 'Se requiere MFA para invitar.' } }, 403);
    const email = typeof body.email === 'string' ? body.email.trim().toLowerCase() : '';
    const role = body.role;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || (role !== 'admin' && role !== 'user') || (body.resend !== undefined && typeof body.resend !== 'boolean')) {
      return jsonResponse(state, { error: { code: 'invalid_invitation' } }, 400);
    }
    const requestId = requestIdFor(context.request);
    const { data, error } = await client.functions.invoke('admin-invite', {
      body: { email, role, resend: body.resend === true },
      headers: { 'x-request-id': requestId },
    });
    if (error) {
      const errorContext = (error as { context?: unknown }).context;
      const edgeResponse = errorContext instanceof Response ? errorContext : null;
      const edgePayload = edgeResponse
        ? await edgeResponse.clone().json().catch(() => null)
        : null;
      const candidate = edgePayload && typeof edgePayload === 'object'
        ? edgePayload as { code?: unknown; request_id?: unknown }
        : null;
      const requestedEdgeCode = typeof candidate?.code === 'string'
        && /^[a-z][a-z0-9_]{1,63}$/.test(candidate.code)
        ? candidate.code
        : '';
      const edgeCode = SAFE_INVITE_ERROR_CODES.has(requestedEdgeCode)
        ? requestedEdgeCode
        : 'invitation_failed';
      const requestIdFromEdge = typeof candidate?.request_id === 'string'
        && /^[A-Za-z0-9._:-]{1,100}$/.test(candidate.request_id)
        ? candidate.request_id
        : requestId;
      const status = edgeCode === 'reconciliation_required'
        ? 409
        : edgeCode === 'auth_rate_limited' || edgeCode === 'quota_rate_limited'
          ? 429
          : edgeCode === 'quota_unavailable' || edgeCode === 'maintenance_mode' ? 503
          : edgeCode === 'unauthorized'
            ? 401
            : edgeCode === 'forbidden' || edgeCode === 'mfa_required'
              ? 403
              : 502;
      const message = edgeCode === 'reconciliation_required'
        ? 'La entrega requiere conciliación. Reintenta la misma operación con esta referencia.'
        : edgeCode === 'auth_rate_limited'
          ? 'El servicio de correo está limitado temporalmente. Reintenta más tarde.'
          : 'No se pudo completar la invitación.';
      const response = jsonResponse(state, {
        error: { code: edgeCode, message },
        request_id: requestIdFromEdge,
      }, status);
      if (status === 429 || status === 503) {
        const retry = Number(edgeResponse?.headers.get('Retry-After'));
        response.headers.set('Retry-After',String(Number.isInteger(retry) && retry>=1 && retry<=86400 ? retry : 30));
      }
      return response;
    }
    return jsonResponse(state, data);
  }

  if (pathname === '/api/admin/auth/password') {
    const limited = await checkAdminQuota(request, context.env, [{ kind: 'password', identity: user.id }]);
    if (limited) return limited;
    const password = typeof body.password === 'string' ? body.password : '';
    const valid = password.length >= 12 && password.length <= 128
      && /[A-Z]/.test(password) && /[a-z]/.test(password)
      && /\d/.test(password) && /[^A-Za-z0-9]/.test(password);
    if (!valid) return jsonResponse(state, { error: { code: 'invalid_password', message: 'La contraseña no cumple los requisitos.' } }, 400);
    const { error } = await client.auth.updateUser({ password });
    if (error) return jsonResponse(state, { error: { code: 'password_update_failed', message: 'No se pudo actualizar la contraseña.' } }, 400);
    return jsonResponse(state, { success: true });
  }

  if (pathname === '/api/admin/auth/mfa') {
    const action = typeof body.action === 'string' ? body.action : '';
    if (action !== 'assurance' && action !== 'list') {
      const limited = await checkAdminQuota(request, context.env, [{ kind: 'mfa', identity: user.id }]);
      if (limited) return limited;
    }
    if (action === 'assurance') {
      const { data, error } = await client.auth.mfa.getAuthenticatorAssuranceLevel();
      if (error) return jsonResponse(state, { error: { code: 'mfa_unavailable' } }, 502);
      return jsonResponse(state, { currentLevel: data.currentLevel, nextLevel: data.nextLevel });
    }
    if (action === 'list') {
      const { data, error } = await client.auth.mfa.listFactors();
      if (error) return jsonResponse(state, { error: { code: 'mfa_unavailable' } }, 502);
      return jsonResponse(state, { factors: (data.all || []).filter((factor) => factor.factor_type === 'totp').map(({ id, factor_type, status }) => ({ id, factor_type, status })) });
    }
    if (action === 'enroll') {
      const { data: factorData, error: factorError } = await client.auth.mfa.listFactors();
      if (factorError) return jsonResponse(state, { error: { code: 'mfa_unavailable' } }, 502);
      const totpFactors = (factorData.all || []).filter((factor) => factor.factor_type === 'totp');
      if (totpFactors.some((factor) => factor.status === 'unverified')) {
        return jsonResponse(state, { error: { code: 'mfa_enrollment_pending' } }, 409);
      }
      if (totpFactors.some((factor) => factor.status === 'verified') && !await aal2(client)) {
        return jsonResponse(state, { error: { code: 'mfa_required', message: 'Verifica tu MFA antes de añadir otro factor.' } }, 403);
      }
      const { data, error } = await client.auth.mfa.enroll({ factorType: 'totp', friendlyName: 'StudIAMatch Admin', issuer: 'StudIAMatch' });
      if (error || !data?.id) return jsonResponse(state, { error: { code: 'mfa_enrollment_failed' } }, 400);
      return jsonResponse(state, { factor: { id: data.id, secret: data.totp?.secret ?? null, uri: data.totp?.uri ?? null, qr_code: data.totp?.qr_code ?? null } });
    }
    const factorId = typeof body.factorId === 'string' && /^[0-9a-f-]{36}$/i.test(body.factorId) ? body.factorId : '';
    if (!factorId) return jsonResponse(state, { error: { code: 'invalid_factor' } }, 400);
    if (action === 'challenge') {
      const { data, error } = await client.auth.mfa.challenge({ factorId });
      if (error || !data?.id) return jsonResponse(state, { error: { code: 'mfa_challenge_failed' } }, 400);
      return jsonResponse(state, { id: data.id });
    }
    if (action === 'verify') {
      const challengeId = typeof body.challengeId === 'string' && /^[0-9a-f-]{36}$/i.test(body.challengeId) ? body.challengeId : '';
      const code = typeof body.code === 'string' ? body.code.trim() : '';
      if (!challengeId || !/^\d{6,8}$/.test(code)) return jsonResponse(state, { error: { code: 'invalid_challenge' } }, 400);
      const { error } = await client.auth.mfa.verify({ factorId, challengeId, code });
      if (error) return jsonResponse(state, { error: { code: 'mfa_verification_failed', message: 'Código MFA inválido.' } }, 401);
      const verifiedSession = await authenticatedSession(client);
      if (!verifiedSession) {
        clearServerAuthCookies(request,state);
        clearActivityCookie(state);
        return jsonResponse(state, { error: { code: 'session_unavailable' } }, 401);
      }
      await appendActivityCookie(state, context.env.ADMIN_SESSION_ACTIVITY_HMAC_KEY!, verifiedSession.sessionId);
      return jsonResponse(state, { success: true });
    }
    if (action === 'unenroll') {
      const { data: factorData, error: factorError } = await client.auth.mfa.listFactors();
      if (factorError) return jsonResponse(state, { error: { code: 'mfa_unavailable' } }, 502);
      const totpFactors = (factorData.all || []).filter((factor) => factor.factor_type === 'totp');
      const targetFactor = totpFactors.find((factor) => factor.id === factorId);
      if (!targetFactor) return jsonResponse(state, { error: { code: 'invalid_factor' } }, 404);
      const hasVerifiedFactor = totpFactors.some((factor) => factor.status === 'verified');
      if ((targetFactor.status === 'verified' || hasVerifiedFactor) && !await aal2(client)) {
        return jsonResponse(state, { error: { code: 'mfa_required' } }, 403);
      }
      const { error } = await client.auth.mfa.unenroll({ factorId });
      if (error) return jsonResponse(state, { error: { code: 'mfa_unenroll_failed' } }, 400);
      return jsonResponse(state, { success: true });
    }
    return jsonResponse(state, { error: { code: 'mfa_action_not_allowed' } }, 400);
  }

  return jsonResponse(state, { error: { code: 'not_found' } }, 404);
}

export async function routeAdminBff(context: AdminBffContext): Promise<Response | null> {
  const request = context.request;
  const url = new URL(request.url);

  if (url.pathname === '/admin/auth/callback' || url.pathname === '/admin/auth/callback/') {
    if (request.method !== 'GET') return new Response('Method not allowed', { status: 405 });
    return routeAuthCallback(url);
  }

  if (!url.pathname.startsWith('/api/admin/')) return null;
  if (request.method !== 'GET' && request.method !== 'POST') {
    return new Response('Method not allowed', { status: 405, headers: { Allow: 'GET, POST' } });
  }
  const isCallbackPost = request.method === 'POST' && url.pathname === '/api/admin/auth/callback';
  const mutationOriginAllowed = isCallbackPost
    ? callbackMutationOriginAllowed(request)
    : sameOriginMutation(request);
  if (request.method === 'POST' && !mutationOriginAllowed) {
    const state = { headers: new Headers(), setCookies: [] };
    return jsonResponse(state, { error: { code: 'csrf_rejected' } }, 403);
  }

  // Local logout must work without upstream/config/quota availability. Do not
  // broaden the JWT Auth allowlist to logout; clear this browser's HttpOnly SSR
  // cookie and chunks explicitly. This is not global provider-session revocation.
  if (request.method === 'POST' && url.pathname === '/api/admin/auth/logout') {
    const state={headers:new Headers(),setCookies:[] as string[]};
    clearServerAuthCookies(request,state);
    clearActivityCookie(state);
    clearCallbackCsrfCookie(state);
    return jsonResponse(state,{success:true});
  }

  if (request.method === 'GET' && url.pathname === '/api/admin/session' && !sameOriginSessionRead(request)) {
    return jsonResponse(
      { headers: new Headers(), setCookies: [] },
      { error: { code: 'csrf_rejected' } },
      403,
    );
  }

  if (adminHmacKeysInvalid(context.env)) {
    return jsonResponse(
      { headers: new Headers(), setCookies: [] },
      { error: { code: 'server_configuration_error' } },
      503,
    );
  }

  if (!(request.method === 'POST' && url.pathname === '/api/admin/auth/logout')) {
    const ip = trustedQuotaIp(request);
    if (!ip) return new Response(JSON.stringify({ error: { code: 'quota_unavailable' } }), {
      status: 503, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
    });
    const limited = await checkAdminQuota(request, context.env, [{ kind: 'entry', identity: ip }]);
    if (limited) return limited;
  }

  let client: SupabaseClient;
  let state: CookieState;
  try {
    ({ client, state } = createCookieState(request, context.env));
  } catch {
    return new Response(JSON.stringify({ error: { code: 'server_configuration_error' } }), {
      status: 503,
      headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer' },
    });
  }

  if (url.pathname === '/api/admin/session' && request.method === 'GET') {
    const activityKey = context.env.ADMIN_SESSION_ACTIVITY_HMAC_KEY!;
    const authenticated = await authenticatedSession(client);
    if (!authenticated || !await activityIsFresh(request, activityKey, authenticated.sessionId)) {
      clearServerAuthCookies(request,state);
      clearActivityCookie(state);
      return jsonResponse(state, { authenticated: false, session: null });
    }
    const session = await sessionSummary(client, authenticated);
    if (!session) {
      clearServerAuthCookies(request,state);
      clearActivityCookie(state);
      return jsonResponse(state, { authenticated: false, session: null });
    }
    await appendActivityCookie(state, activityKey, session.sessionId);
    return jsonResponse(state, { authenticated: true, session: session.summary });
  }

  if (request.method !== 'POST') return jsonResponse(state, { error: { code: 'not_found' } }, 404);
  return routeMutation(context, client, state, url.pathname);
}

async function routeAuthCallback(url: URL): Promise<Response | null> {
  if (url.search.length > MAX_CALLBACK_QUERY_CHARS) {
    const state = { headers: new Headers(), setCookies: [] };
    return redirectResponse(state, url, '/admin/auth/callback/', '?error=invalid');
  }
  const code = url.searchParams.get('code')?.trim() || '';
  const tokenHash = url.searchParams.get('token_hash')?.trim() || '';
  const type = url.searchParams.get('type')?.trim() || '';
  const providerError = url.searchParams.has('error') || url.searchParams.has('error_description');
  if (providerError) return callbackErrorResponse();
  if (!code && !tokenHash && !providerError) return null;
  const state = { headers: new Headers(), setCookies: [] };
  if (
    providerError
    || (type !== 'invite' && type !== 'recovery')
    || (Boolean(code) === Boolean(tokenHash))
    || url.searchParams.getAll('code').length > 1
    || url.searchParams.getAll('token_hash').length > 1
    || url.searchParams.getAll('type').length > 1
    || (code && !/^[A-Za-z0-9._~-]{1,2048}$/.test(code))
    || (tokenHash && !/^[A-Za-z0-9_-]{20,512}$/.test(tokenHash))
  ) {
    return redirectResponse(state, url, '/admin/auth/callback/', '?error=invalid');
  }
  return callbackConfirmationResponse(
    type as 'invite' | 'recovery',
    code ? { name: 'code', value: code } : { name: 'token_hash', value: tokenHash },
  );
}
