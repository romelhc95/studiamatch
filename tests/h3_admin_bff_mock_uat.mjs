import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import { createHmac } from 'node:crypto';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(root, 'web/package.json'));
const ts = require('typescript');
const source = await readFile(join(root, 'web/functions/_lib/admin-bff.ts'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    esModuleInterop: true,
  },
  reportDiagnostics: true,
});
assert.equal(compiled.diagnostics?.filter((item) => item.category === ts.DiagnosticCategory.Error).length, 0);
const transportSource = await readFile(join(root, 'web/src/lib/supabase-transport.ts'), 'utf8');
const transportCompiled = ts.transpileModule(transportSource, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  reportDiagnostics: true,
});
assert.equal(transportCompiled.diagnostics?.filter((item) => item.category === ts.DiagnosticCategory.Error).length, 0);
const transportModule = { exports: {} };
vm.runInNewContext(transportCompiled.outputText, {
  module: transportModule,
  exports: transportModule.exports,
  Headers,
  Request,
  URL,
}, { filename: 'supabase-transport.js' });

const cookieOptionsSeen = [];
const rpcCalls = [];
const otpCalls = [];
const inviteCalls = [];
let inviteFailure = false;
let inviteFailureCode = 'reconciliation_required';
let rpcFailure = null;
let currentSession = null;
let mockFactors = [{ id: '00000000-0000-4000-8000-000000000001', factor_type: 'totp', status: 'verified' }];
let malformedFactorList = false;
let factorListFailure = false;
let assuranceFailure = false;
let assuranceNextLevelOverride;
let updateUserCalls = 0;
let enrollmentCount = 0;
const pendingFactorId = '00000000-0000-4000-8000-000000000002';
const user = { id: '30000000-0000-0000-0000-000000000001', email: 'admin@local.test' };
const sessionAId = '30000000-0000-4000-8000-000000000011';
const sessionBId = '30000000-0000-4000-8000-000000000012';
const quotaRequests = [];
let rpcQuotaFailure = null;

function syntheticAccessToken(userId, sessionId) {
  const encode = (value) => Buffer.from(JSON.stringify(value)).toString('base64url');
  return `${encode({ alg: 'none', typ: 'JWT' })}.${encode({ sub: userId, session_id: sessionId })}.fixture`;
}

function parseCookieHeader(header) {
  return header.split(';').map((part) => part.trim()).filter(Boolean).map((part) => {
    const index = part.indexOf('=');
    return { name: part.slice(0, index), value: decodeURIComponent(part.slice(index + 1)) };
  });
}

function serializeCookieHeader(name, value, options = {}) {
  cookieOptionsSeen.push({ name, ...options });
  const pieces = [`${name}=${encodeURIComponent(value)}`];
  if (options.path) pieces.push(`Path=${options.path}`);
  if (options.maxAge !== undefined) pieces.push(`Max-Age=${options.maxAge}`);
  if (options.sameSite) pieces.push(`SameSite=${options.sameSite[0].toUpperCase()}${options.sameSite.slice(1)}`);
  if (options.secure) pieces.push('Secure');
  if (options.httpOnly) pieces.push('HttpOnly');
  return pieces.join('; ');
}

function setSession(cookies, aal = 'aal1', sessionId = sessionAId) {
  currentSession = {
    access_token: syntheticAccessToken(user.id, sessionId),
    refresh_token: 'fixture-user-refresh-token',
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    aal,
    user,
  };
  cookies.setAll([{
    name: '__Host-studiamatch-admin-auth',
    value: 'opaque-cookie-session',
    options: { path: '/', sameSite: 'lax', secure: true, httpOnly: true },
  }], { 'Cache-Control': 'private, no-store' });
}

function createServerClient(_url, _key, options) {
  const cookies = options.cookies;
  const currentAal = () => currentSession?.aal ?? null;
  return {
    auth: {
      signInWithPassword: async ({ email, password }) => {
        if (email !== user.email || password !== 'LocalOnly-Password9!') {
          return { error: { status: 400, message: 'Invalid login credentials' } };
        }
        setSession(cookies);
        return { error: null, data: { user } };
      },
      getUser: async () => currentSession
        ? { data: { user }, error: null }
        : { data: { user: null }, error: { message: 'No session' } },
      getSession: async () => ({ data: { session: currentSession }, error: null }),
      signOut: async () => {
        currentSession = null;
        cookies.setAll([{
          name: '__Host-studiamatch-admin-auth',
          value: '',
          options: { path: '/', maxAge: 0, sameSite: 'lax', secure: true, httpOnly: true },
        }], { 'Cache-Control': 'private, no-store' });
        return { error: null };
      },
      exchangeCodeForSession: async () => {
        setSession(cookies);
        return { data: { session: currentSession }, error: null };
      },
      verifyOtp: async (payload) => {
        otpCalls.push(payload);
        setSession(cookies);
        return { data: { session: currentSession }, error: null };
      },
      updateUser: async () => {
        updateUserCalls += 1;
        return { data: { user }, error: null };
      },
      mfa: {
        getAuthenticatorAssuranceLevel: async () => assuranceFailure
          ? { data: null, error: { message: 'fixture assurance service unavailable' } }
          : { data: {
            currentLevel: currentAal(),
            nextLevel: assuranceNextLevelOverride ?? (mockFactors.some((factor) => factor.status === 'verified') ? 'aal2' : currentAal()),
          }, error: null },
        listFactors: async () => factorListFailure
          ? { data: null, error: { message: 'fixture factor service unavailable' } }
          : { data: malformedFactorList ? {} : { all: [...mockFactors] }, error: null },
        enroll: async () => {
          enrollmentCount += 1;
          mockFactors.push({ id: pendingFactorId, factor_type: 'totp', status: 'unverified' });
          return { data: { id: pendingFactorId, totp: { secret: 'fixture-secret', uri: 'otpauth://fixture', qr_code: 'fixture-qr' } }, error: null };
        },
        challenge: async () => ({ data: { id: 'challenge-1' }, error: null }),
        verify: async () => {
          currentSession.aal = 'aal2';
          currentSession.access_token = syntheticAccessToken(user.id, sessionBId);
          return { error: null };
        },
        unenroll: async ({ factorId }) => {
          mockFactors = mockFactors.filter((factor) => factor.id !== factorId);
          return { error: null };
        },
      },
    },
    rpc: async (name, params) => {
      rpcCalls.push({ name, params });
      if (rpcFailure) return { data: null, error: rpcFailure };
      return { data: [{ success: true }], error: null };
    },
    functions: {
      invoke: async (...args) => {
        inviteCalls.push(args);
        if (inviteFailure) {
          const context = new Response(JSON.stringify({
            error: 'Auth delivery outcome requires reconciliation',
            code: inviteFailureCode,
            request_id: args[1].headers['x-request-id'],
          }), { status: 409, headers: { 'Content-Type': 'application/json' } });
          return { data: null, error: Object.assign(new Error('non-2xx response'), { context }) };
        }
        return { data: { success: true }, error: null };
      },
    },
  };
}

const moduleObject = { exports: {} };
const quotaCompiled = ts.transpileModule(await readFile(join(root, 'web/functions/_lib/admin-quota.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
});
const quotaModule = { exports: {} };
vm.runInNewContext(quotaCompiled.outputText, {
  module: quotaModule, exports: quotaModule.exports, Request, Response, Headers,
  TextEncoder, crypto: require('node:crypto').webcrypto,
}, { filename: 'admin-quota.js' });
const sandbox = {
  module: moduleObject,
  exports: moduleObject.exports,
  require: (name) => {
    if (name === '@supabase/ssr') return { createServerClient, parseCookieHeader, serializeCookieHeader };
    if (name === '@supabase/supabase-js') return {};
    if (name === '../../src/lib/supabase-transport') return transportModule.exports;
    if (name === './admin-quota') return quotaModule.exports;
    return require(name);
  },
  URL,
  URLSearchParams,
  Headers,
  Request,
  Response,
  fetch: async () => new Response('[]', { status: 200 }),
  TextDecoder,
  TextEncoder,
  atob,
  Date,
  Math,
  JSON,
  RegExp,
  String,
  Number,
  Boolean,
  Set,
  Uint8Array,
  crypto: require('node:crypto').webcrypto,
  Promise,
  console,
};
vm.runInNewContext(compiled.outputText, sandbox, { filename: 'admin-bff.js' });
const { routeAdminBff } = moduleObject.exports;
const activitySigningKey = 'local-only-admin-activity-fixture-key-32-bytes';
function signedActivityCookie(timestamp = Date.now(), sessionId = sessionAId) {
  const canonicalTimestamp = String(timestamp);
  const signature = createHmac('sha256', activitySigningKey)
    .update(`studiamatch-admin-activity-v1:${sessionId}:${canonicalTimestamp}`)
    .digest('hex');
  return `${canonicalTimestamp}.${signature}`;
}
const env = {
  SUPABASE_URL: 'http://localhost:3001',
  NEXT_SUPABASE_PUBLISHABLE_KEY: 'sb_publishable_localmock',
  ADMIN_BFF_ALLOW_LOCAL_AUTH_MOCK: 'true',
  ADMIN_QUOTA_HMAC_KEY: 'local-only-quota-fixture-'.repeat(3),
  ADMIN_SESSION_ACTIVITY_HMAC_KEY: activitySigningKey,
  ADMIN_RPC_GATEWAY_HMAC_KEY: 'local-only-rpc-gateway-fixture-key-32-bytes',
  ADMIN_RPC_GATEWAY_KEY_ID: 'local-k1',
  ADMIN_QUOTA: { fetch: async (request) => {
    const counters = (await request.json()).counters;
    quotaRequests.push(counters.map((counter) => counter.kind));
    if (rpcQuotaFailure && counters.some((counter) => counter.kind.startsWith('rpc-'))) {
      return new Response(JSON.stringify({ allowed: false }), {
        status: rpcQuotaFailure,
        headers: rpcQuotaFailure === 429 ? { 'Retry-After': '37' } : {},
      });
    }
    return new Response(JSON.stringify({ allowed: true }), { status: 200 });
  } },
};

function request(path, { method = 'GET', body, headers = {}, cookie, fetchSite = 'same-origin' } = {}) {
  const requestHeaders = new Headers(headers);
  if (fetchSite && !requestHeaders.has('Sec-Fetch-Site')) requestHeaders.set('Sec-Fetch-Site', fetchSite);
  if (!requestHeaders.has('CF-Connecting-IP')) requestHeaders.set('CF-Connecting-IP', '192.0.2.1');
  if (body !== undefined && !requestHeaders.has('Content-Type')) requestHeaders.set('Content-Type', 'application/json');
  if (cookie) requestHeaders.set('Cookie', cookie);
  return new Request(`https://admin.preview.local${path}`, {
    method,
    headers: requestHeaders,
    body: body === undefined ? undefined : typeof body === 'string' ? body : JSON.stringify(body),
  });
}

async function route(req, overrides = {}) {
  return routeAdminBff({ request: req, env: { ...env, ...overrides }, next: async () => new Response('next') });
}

const crossSite = await route(request('/api/admin/auth/login', {
  method: 'POST',
  headers: { Origin: 'https://evil.example' },
  body: { email: user.email, password: 'LocalOnly-Password9!' },
}), {});
assert.equal(crossSite.status, 403, 'cross-origin mutation must be rejected before Supabase configuration is used');

const quotaCountBeforeHmacCollision = quotaRequests.length;
const reusedHmacKey = await route(request('/api/admin/auth/login', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  body: { email: user.email, password: 'LocalOnly-Password9!' },
}), { ADMIN_RPC_GATEWAY_HMAC_KEY: env.ADMIN_QUOTA_HMAC_KEY });
assert.equal(reusedHmacKey.status, 503, 'quota and RPC gateway HMAC keys must be distinct');
assert.equal((await reusedHmacKey.json()).error.code, 'server_configuration_error');
assert.equal(quotaRequests.length, quotaCountBeforeHmacCollision, 'colliding HMAC keys must be rejected before quota admission');
assert.equal(rpcCalls.length, 0, 'colliding HMAC keys must be rejected before any RPC call');

const login = await route(request('/api/admin/auth/login', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  body: { email: user.email, password: 'LocalOnly-Password9!' },
}));
assert.equal(login.status, 200);
const loginBody = await login.json();
assert.equal(loginBody.session.email, user.email);
assert.equal(loginBody.session.aal, 'aal1');
assert.equal(JSON.stringify(loginBody).includes('fixture-user-session-jwt'), false, 'session JWT must not be returned to JavaScript');
assert.equal(JSON.stringify(loginBody).includes('fixture-user-refresh-token'), false, 'refresh token must not be returned to JavaScript');
const loginCookies = login.headers.get('set-cookie') || '';
assert.match(loginCookies, /__Host-studiamatch-admin-auth=opaque-cookie-session/);
assert.match(loginCookies, /HttpOnly/);
assert.match(loginCookies, /Secure/);
assert.match(loginCookies, /SameSite=Lax/);
assert.match(loginCookies, /Max-Age=1800/);
assert.match(loginCookies, /__Host-studiamatch-admin-activity=/);
assert.match(loginCookies, /__Host-studiamatch-admin-activity=\d{13}\.[a-f0-9]{64}/,
  'activity cookie must contain a signed timestamp');
assert.equal(loginCookies.includes(activitySigningKey), false, 'activity signing key must not be emitted');
assert.equal(loginCookies.includes(sessionAId), false, 'session identifier must not be emitted in activity cookie');
assert.equal(JSON.stringify(loginBody).includes(sessionAId), false, 'session identifier must not be returned to JavaScript');

const csrfCookie = `__Host-studiamatch-admin-auth=opaque-cookie-session; __Host-studiamatch-admin-activity=${signedActivityCookie()}`;
const session = await route(request('/api/admin/session', {
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
}));
assert.equal(session.status, 200);

const recoveryPassword = 'Recovery-Password9!';
const passwordUpdateWithMfaAal1 = await route(request('/api/admin/auth/password', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { password: recoveryPassword },
}));
assert.equal(passwordUpdateWithMfaAal1.status, 403, 'the BFF must reject direct password updates when a verified MFA factor exists but the session is not aal2');
assert.deepEqual(await passwordUpdateWithMfaAal1.json(), {
  error: { code: 'mfa_required', message: 'Completa la verificación MFA antes de cambiar la contraseña.' },
});
assert.equal(updateUserCalls, 0, 'the Auth password mutation must not run for an aal1 session with verified MFA');

malformedFactorList = true;
const passwordUpdateWithMalformedFactors = await route(request('/api/admin/auth/password', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { password: recoveryPassword },
}));
assert.equal(passwordUpdateWithMalformedFactors.status, 503, 'the BFF must fail closed when it cannot validate the MFA inventory');
assert.deepEqual(await passwordUpdateWithMalformedFactors.json(), {
  error: { code: 'mfa_unavailable', message: 'No se pudo confirmar el estado MFA. Inténtalo de nuevo.' },
});
assert.equal(updateUserCalls, 0, 'malformed factors must never reach the Auth password mutation');
malformedFactorList = false;

factorListFailure = true;
const passwordUpdateWithUnavailableFactors = await route(request('/api/admin/auth/password', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { password: recoveryPassword },
}));
assert.equal(passwordUpdateWithUnavailableFactors.status, 503, 'the BFF must fail closed when Auth cannot list MFA factors');
assert.equal(updateUserCalls, 0, 'an unavailable MFA inventory must never reach the Auth password mutation');
factorListFailure = false;

assuranceFailure = true;
const passwordUpdateWithUnavailableAssurance = await route(request('/api/admin/auth/password', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { password: recoveryPassword },
}));
assert.equal(passwordUpdateWithUnavailableAssurance.status, 503, 'the BFF must fail closed when Auth cannot determine session assurance');
assert.equal(updateUserCalls, 0, 'unavailable assurance must never reach the Auth password mutation');
assuranceFailure = false;

currentSession.aal = 'aal2';
const passwordUpdateWithVerifiedMfa = await route(request('/api/admin/auth/password', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { password: recoveryPassword },
}));
assert.equal(passwordUpdateWithVerifiedMfa.status, 200, 'aal2 sessions with a verified factor may update the password');
assert.equal(updateUserCalls, 1);

currentSession.aal = 'aal1';
mockFactors = [];
const passwordUpdateWithoutMfa = await route(request('/api/admin/auth/password', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { password: recoveryPassword },
}));
assert.equal(passwordUpdateWithoutMfa.status, 200, 'password setup remains available to a session without verified MFA factors');
assert.equal(updateUserCalls, 2);
assuranceNextLevelOverride = 'aal2';
const passwordUpdateWithMfaAssuranceMismatch = await route(request('/api/admin/auth/password', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { password: recoveryPassword },
}));
assert.equal(passwordUpdateWithMfaAssuranceMismatch.status, 403, 'a next aal2 assurance level must stay gated even if the separate factor inventory omits a verified factor');
assert.deepEqual(await passwordUpdateWithMfaAssuranceMismatch.json(), {
  error: { code: 'mfa_required', message: 'Completa la verificación MFA antes de cambiar la contraseña.' },
});
assert.equal(updateUserCalls, 2, 'inconsistent assurance and factor reads must never reach the Auth password mutation');
assuranceNextLevelOverride = undefined;
mockFactors = [{ id: '00000000-0000-4000-8000-000000000001', factor_type: 'totp', status: 'verified' }];
assert(!/__Host-studiamatch-admin-auth(?:\.|=)/.test(session.headers.get('set-cookie') || ''),
  'read response must not echo stale Auth cookies and race MFA upgrade');
assert.equal((await session.json()).authenticated, true);

const quotaBeforeCrossSiteSession = quotaRequests.length;
const crossSiteSession = await route(request('/api/admin/session', {
  headers: { Origin: 'https://evil.example', 'Sec-Fetch-Site': 'cross-site' },
  cookie: csrfCookie,
}));
assert.equal(crossSiteSession.status, 403, 'cross-site session reads must not renew activity');
assert.equal(quotaRequests.length, quotaBeforeCrossSiteSession, 'cross-site session reads stop before quota admission');
assert.equal((crossSiteSession.headers.get('set-cookie') || '').includes('admin-activity'), false);

const sameSiteSession = await route(request('/api/admin/session', {
  headers: { 'Sec-Fetch-Site': 'same-site' },
  cookie: csrfCookie,
}));
assert.equal(sameSiteSession.status, 403, 'same-site is insufficient for session renewal');

const missingFetchMetadataSession = await route(request('/api/admin/session', {
  headers: { Origin: 'https://admin.preview.local' },
  fetchSite: null,
  cookie: csrfCookie,
}));
assert.equal(missingFetchMetadataSession.status, 403, 'session renewal requires same-origin fetch metadata');

const mismatchedOriginSession = await route(request('/api/admin/session', {
  headers: { Origin: 'https://evil.example', 'Sec-Fetch-Site': 'same-origin' },
  cookie: csrfCookie,
}));
assert.equal(mismatchedOriginSession.status, 403, 'a supplied mismatched Origin must be rejected');

async function assertActivityCookieRejected(activityCookie, label) {
  const response = await route(request('/api/admin/session', {
    cookie: `__Host-studiamatch-admin-auth=opaque-cookie-session; __Host-studiamatch-admin-activity=${activityCookie}`,
  }));
  assert.equal(response.status, 200, `${label} remains a sanitized unauthenticated result`);
  assert.equal((await response.json()).authenticated, false, label);
  assert.match(response.headers.get('set-cookie') || '', /__Host-studiamatch-admin-activity=;.*Max-Age=0/);
}

await assertActivityCookieRejected(String(Date.now()), 'a client-replayed raw timestamp must not refresh an authenticated session');
const signedTimestamp = String(Date.now());
const signedSignature = signedActivityCookie(Number(signedTimestamp)).split('.')[1];
await assertActivityCookieRejected(`${Number(signedTimestamp) + 1000}.${signedSignature}`, 'timestamp tampering must invalidate activity signature');
await assertActivityCookieRejected(`${signedTimestamp}.${'0'.repeat(64)}`, 'signature tampering must invalidate activity cookie');
await assertActivityCookieRejected(signedActivityCookie(Date.now() - (31 * 60 * 1000)), 'expired activity must be rejected');
await assertActivityCookieRejected(signedActivityCookie(Date.now() + 31_000), 'future activity must be rejected');

const sessionBeforeCrossSessionActivity = currentSession;
currentSession = {
  ...currentSession,
  access_token: syntheticAccessToken(user.id, sessionBId),
  user,
};
const crossSessionActivity = await route(request('/api/admin/session', {
  cookie: `__Host-studiamatch-admin-auth=opaque-cookie-session; __Host-studiamatch-admin-activity=${signedActivityCookie()}`,
}));
assert.equal((await crossSessionActivity.json()).authenticated, false,
  'an activity cookie issued for a different Auth session must not renew this session');
currentSession = sessionBeforeCrossSessionActivity;

const quotaBeforeMissingActivityKey = quotaRequests.length;
const missingActivitySigningKey = await route(request('/api/admin/session', { cookie: csrfCookie }), {
  ADMIN_SESSION_ACTIVITY_HMAC_KEY: undefined,
});
assert.equal(missingActivitySigningKey.status, 503, 'missing activity signing key must fail closed');
assert.equal(quotaRequests.length, quotaBeforeMissingActivityKey, 'missing signing configuration fails before quota admission');

const collidingActivitySigningKey = await route(request('/api/admin/session', { cookie: csrfCookie }), {
  ADMIN_SESSION_ACTIVITY_HMAC_KEY: env.ADMIN_QUOTA_HMAC_KEY,
});
assert.equal(collidingActivitySigningKey.status, 503, 'activity signing key must be distinct from quota key');
const collidingGatewayActivityKey = await route(request('/api/admin/session', { cookie: csrfCookie }), {
  ADMIN_SESSION_ACTIVITY_HMAC_KEY: env.ADMIN_RPC_GATEWAY_HMAC_KEY,
});
assert.equal(collidingGatewayActivityKey.status, 503, 'activity signing key must be distinct from gateway key');
const shortActivitySigningKey = await route(request('/api/admin/session', { cookie: csrfCookie }), {
  ADMIN_SESSION_ACTIVITY_HMAC_KEY: 'short-synthetic-key',
});
assert.equal(shortActivitySigningKey.status, 503, 'activity signing key must be at least 32 bytes');

const wrongKey = await route(request('/api/admin/session'), {
  NEXT_SUPABASE_PUBLISHABLE_KEY: 'not-a-publishable-key',
});
assert.equal(wrongKey.status, 503, 'invalid server key must fail closed');
const emptySuffixedKey = await route(request('/api/admin/session'), {
  NEXT_SUPABASE_PUBLISHABLE_KEY: 'sb_publishable_',
});
assert.equal(emptySuffixedKey.status, 503, 'empty publishable-key suffix must fail closed');

const oversized = await route(request('/api/admin/rpc', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { function: 'admin_current_user_role', params: { padding: 'x'.repeat(66_000) } },
}));
assert.equal(oversized.status, 400, 'streamed request bodies above the limit must be rejected');

const blockedRpc = await route(request('/api/admin/rpc', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { function: 'admin_create_member', params: { p_email: 'x@example.test' } },
}));
assert.equal(blockedRpc.status, 400, 'RPC calls outside the explicit allowlist must be rejected');
assert.equal(rpcCalls.length, 0);

const allowedRpc = await route(request('/api/admin/rpc', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { function: 'admin_current_user_role', params: {} },
}));
assert.equal(allowedRpc.status, 200);
assert.equal(rpcCalls.at(-1).name, 'admin_current_user_role');
assert.deepEqual(quotaRequests.at(-1), ['rpc-read'], 'read RPCs are admitted by the actor quota before PostgREST');

const rpcCountBeforeMissingKey = rpcCalls.length;
const missingRpcSigningKey = await route(request('/api/admin/rpc', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { function: 'admin_current_user_role', params: {} },
}), { ADMIN_RPC_GATEWAY_HMAC_KEY: undefined });
assert.equal(missingRpcSigningKey.status, 503, 'missing signing configuration fails closed before PostgREST');
assert.equal(rpcCalls.length, rpcCountBeforeMissingKey);

rpcQuotaFailure = 429;
const rpcCountBeforeLimit = rpcCalls.length;
const limitedRpc = await route(request('/api/admin/rpc', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { function: 'admin_current_user_role', params: {} },
}));
assert.equal(limitedRpc.status, 429);
assert.equal(limitedRpc.headers.get('Retry-After'), '37');
assert.equal(rpcCalls.length, rpcCountBeforeLimit, 'a quota denial never calls PostgREST');
rpcQuotaFailure = null;

const validMfaFactorId = '00000000-0000-4000-8000-000000000004';
const validPhoneFactorId = '00000000-0000-4000-8000-000000000005';
mockFactors = [
  { id: validMfaFactorId, factor_type: 'totp', status: 'verified' },
  { id: validPhoneFactorId, factor_type: 'phone', status: 'verified' },
];
const recoveryMfaAssurance = await route(request('/api/admin/auth/mfa', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { action: 'recovery_assurance' },
}));
assert.equal(recoveryMfaAssurance.status, 200);
assert.deepEqual(await recoveryMfaAssurance.json(), {
  currentLevel: 'aal1',
  nextLevel: 'aal2',
  hasVerifiedFactor: true,
  verifiedFactors: [{ id: validMfaFactorId, factor_type: 'totp', status: 'verified' }],
}, 'assurance returns verified factor presence while exposing only TOTP factors usable by this recovery flow');

mockFactors = [];
currentSession.aal = null;
const assuranceWithoutFactors = await route(request('/api/admin/auth/mfa', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { action: 'recovery_assurance' },
}));
assert.equal(assuranceWithoutFactors.status, 200);
assert.deepEqual(await assuranceWithoutFactors.json(), {
  currentLevel: null,
  nextLevel: null,
  hasVerifiedFactor: false,
  verifiedFactors: [],
}, 'nullable SDK AAL levels with no verified factors remain distinguishable from an unavailable MFA state');

mockFactors = [{ id: validPhoneFactorId, factor_type: 'phone', status: 'verified' }];
const phoneOnlyRecoveryAssurance = await route(request('/api/admin/auth/mfa', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { action: 'recovery_assurance' },
}));
assert.equal(phoneOnlyRecoveryAssurance.status, 200);
assert.deepEqual(await phoneOnlyRecoveryAssurance.json(), {
  currentLevel: null,
  nextLevel: 'aal2',
  hasVerifiedFactor: true,
  verifiedFactors: [],
}, 'a verified phone factor is recognized as enrolled but is not returned as a usable TOTP factor');

mockFactors = [
  { id: validMfaFactorId, factor_type: 'totp', status: 'verified' },
  { id: validPhoneFactorId, factor_type: 'phone', status: 'verified' },
];
currentSession.aal = 'aal1';
const listedMfaFactors = await route(request('/api/admin/auth/mfa', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { action: 'list' },
}));
assert.equal(listedMfaFactors.status, 200, 'a well-formed verified TOTP factor remains available to the recovery flow');
assert.deepEqual(await listedMfaFactors.json(), {
  factors: [{ id: validMfaFactorId, factor_type: 'totp', status: 'verified' }],
}, 'a known phone factor must not make the TOTP recovery factor unavailable');

malformedFactorList = true;
const malformedMfaFactors = await route(request('/api/admin/auth/mfa', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { action: 'list' },
}));
assert.equal(malformedMfaFactors.status, 502, 'malformed factor data must fail closed instead of looking like no enrolled MFA');
assert.deepEqual(await malformedMfaFactors.json(), { error: { code: 'mfa_unavailable' } });
const malformedMfaAssurance = await route(request('/api/admin/auth/mfa', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { action: 'recovery_assurance' },
}));
assert.equal(malformedMfaAssurance.status, 502, 'assurance must fail closed if the factor inventory is malformed');
assert.deepEqual(await malformedMfaAssurance.json(), { error: { code: 'mfa_unavailable' } });
malformedFactorList = false;

const verifiedFactorId = '00000000-0000-4000-8000-000000000004';
mockFactors = [{ id: verifiedFactorId, factor_type: 'totp', status: 'verified' }];
currentSession.aal = 'aal1';
const sessionBeforeMfaRotation = { ...currentSession };
const verifiedMfa = await route(request('/api/admin/auth/mfa', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { action: 'verify', factorId: verifiedFactorId, challengeId: '00000000-0000-4000-8000-000000000003', code: '123456' },
}));
assert.equal(verifiedMfa.status, 200);
const mfaActivityCookies = [...(verifiedMfa.headers.get('set-cookie') || '').matchAll(/__Host-studiamatch-admin-activity=(\d{13}\.[a-f0-9]{64})/g)];
assert.equal(mfaActivityCookies.length, 1, 'MFA success replaces the pre-verification activity cookie');
const [mfaTimestamp, mfaSignature] = mfaActivityCookies[0][1].split('.');
assert.equal(mfaSignature, signedActivityCookie(Number(mfaTimestamp), sessionBId).split('.')[1],
  'MFA success rebinds activity to the post-verification Auth session');
const resumedAfterMfa = await route(request('/api/admin/session', {
  cookie: `__Host-studiamatch-admin-auth=opaque-cookie-session; __Host-studiamatch-admin-activity=${mfaActivityCookies[0][1]}`,
}));
assert.equal((await resumedAfterMfa.json()).authenticated, true,
  'the post-MFA activity cookie remains valid for the updated Auth session');
currentSession = sessionBeforeMfaRotation;
currentSession.aal = 'aal2';
const updatedRpc = await route(request('/api/admin/rpc', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { function: 'admin_update_course', params: { p_course_id: 'fixture' } },
}));
assert.equal(updatedRpc.status, 200);
assert.deepEqual(quotaRequests.at(-1), ['rpc-write'], 'mutating RPCs use the lower actor quota');

rpcFailure = { code: 'PGRST116', message: 'internal database detail must not leave the BFF' };
const failedRpc = await route(request('/api/admin/rpc', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { function: 'admin_current_user_role', params: {} },
}));
const failedRpcPayload = await failedRpc.json();
assert.equal(failedRpc.status, 502, 'unknown PostgREST failures must map to a gateway error');
assert.equal(failedRpcPayload.error.code, 'rpc_failed', 'PostgREST codes must not cross the BFF boundary');
assert.equal(failedRpcPayload.error.message, 'No se pudo completar la operación administrativa.');
assert.equal(JSON.stringify(failedRpcPayload).includes('PGRST116'), false);
assert.equal(JSON.stringify(failedRpcPayload).includes('internal database detail'), false);

rpcFailure = { code: 'P0001', message: 'AAL2 required by the RPC' };
const mfaRpc = await route(request('/api/admin/rpc', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { function: 'admin_current_user_role', params: {} },
}));
const mfaRpcPayload = await mfaRpc.json();
assert.equal(mfaRpc.status, 403, 'MFA-required RPC failures retain their safe status');
assert.equal(mfaRpcPayload.error.code, 'mfa_required', 'MFA-required RPC failures retain their safe code');
assert.equal(mfaRpcPayload.error.message, 'Se requiere MFA para esta operación.');
rpcFailure = null;

const inviteCallbackPage = await route(request('/admin/auth/callback/?token_hash=fixture-one-time-hash&type=invite&next=https%3A%2F%2Fevil.example'));
assert.equal(inviteCallbackPage.status, 200);
assert.match(inviteCallbackPage.headers.get('content-type') || '', /text\/html/);
assert.match(inviteCallbackPage.headers.get('content-security-policy') || '', /form-action 'self'/);
const inviteCallbackHtml = await inviteCallbackPage.text();
assert.match(inviteCallbackHtml, /name="token_hash" value="fixture-one-time-hash"/);
const inviteCsrfCookie = inviteCallbackPage.headers.get('set-cookie') || '';
const inviteCsrfToken = /__Host-studiamatch-admin-callback-csrf=(\d{13}\.[a-f0-9]{64})/.exec(inviteCsrfCookie)?.[1];
assert.ok(inviteCsrfToken, 'callback GET must set a short-lived HttpOnly CSRF cookie');
assert.match(inviteCsrfCookie, /HttpOnly/);
assert.match(inviteCsrfCookie, /Secure/);
assert.match(inviteCsrfCookie, /SameSite=Strict/);
assert.match(inviteCsrfCookie, /Max-Age=300/);
assert.match(inviteCallbackHtml, new RegExp(`name="callback_csrf" value="${inviteCsrfToken}"`));
assert.equal(otpCalls.length, 0, 'GET callback must not consume email OTPs');

const inviteCallback = await route(request('/api/admin/auth/callback', {
  method: 'POST',
  headers: {
    Origin: 'null',
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  cookie: `__Host-studiamatch-admin-callback-csrf=${inviteCsrfToken}`,
  body: `type=invite&token_hash=fixture-one-time-hash&callback_csrf=${inviteCsrfToken}`,
}));
assert.equal(inviteCallback.status, 303);
assert.equal(inviteCallback.headers.get('location'), 'https://admin.preview.local/admin/auth/callback/?flow=invite');
assert.match(inviteCallback.headers.get('set-cookie') || '', /HttpOnly/);
assert.match(inviteCallback.headers.get('set-cookie') || '', /__Host-studiamatch-admin-callback-csrf=.*Max-Age=0/);
assert.equal(otpCalls.length, 1);
assert.equal(otpCalls[0].type, 'invite');

const recoveryCallbackPage = await route(request('/admin/auth/callback/?token_hash=fixture-recovery-hash&type=recovery'));
assert.equal(recoveryCallbackPage.status, 200);
assert.equal(otpCalls.length, 1, 'recovery GET must not consume the token');
const recoveryCsrfToken = /__Host-studiamatch-admin-callback-csrf=(\d{13}\.[a-f0-9]{64})/.exec(recoveryCallbackPage.headers.get('set-cookie') || '')?.[1];
assert.ok(recoveryCsrfToken, 'recovery GET must set a callback CSRF token');
const recoveryCallback = await route(request('/api/admin/auth/callback', {
  method: 'POST',
  headers: {
    Origin: 'null',
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  cookie: `__Host-studiamatch-admin-callback-csrf=${recoveryCsrfToken}`,
  body: `type=recovery&token_hash=fixture-recovery-hash&callback_csrf=${recoveryCsrfToken}`,
}));
assert.equal(recoveryCallback.status, 303);
assert.equal(recoveryCallback.headers.get('location'), 'https://admin.preview.local/admin/reset-password/');

const noCallbackCsrf = await route(request('/api/admin/auth/callback', {
  method: 'POST',
  headers: { Origin: 'null', 'Content-Type': 'application/x-www-form-urlencoded' },
  body: 'type=invite&token_hash=fixture-no-csrf-hash',
}));
assert.equal(noCallbackCsrf.status, 403, 'opaque-origin callback POST without its bound nonce must be rejected');
assert.equal(otpCalls.length, 2, 'callback without its CSRF nonce must not consume an OTP');

const expiredCsrfToken = `${Date.now() - (6 * 60 * 1000)}.${'a'.repeat(64)}`;
const expiredCallbackCsrf = await route(request('/api/admin/auth/callback', {
  method: 'POST',
  headers: { Origin: 'null', 'Content-Type': 'application/x-www-form-urlencoded' },
  cookie: `__Host-studiamatch-admin-callback-csrf=${expiredCsrfToken}`,
  body: `type=invite&token_hash=fixture-expired-csrf-hash&callback_csrf=${expiredCsrfToken}`,
}));
assert.equal(expiredCallbackCsrf.status, 403, 'opaque-origin callback nonce must expire server-side after five minutes');
assert.equal(otpCalls.length, 2, 'expired callback nonce must not consume an OTP');

const guardedCallbackPage = await route(request('/admin/auth/callback/?token_hash=fixture-csrf-guards-hash&type=invite'));
const guardedCsrfToken = /__Host-studiamatch-admin-callback-csrf=(\d{13}\.[a-f0-9]{64})/.exec(guardedCallbackPage.headers.get('set-cookie') || '')?.[1];
assert.ok(guardedCsrfToken);
const mismatchedCallbackCsrf = await route(request('/api/admin/auth/callback', {
  method: 'POST',
  headers: { Origin: 'null', 'Content-Type': 'application/x-www-form-urlencoded' },
  cookie: `__Host-studiamatch-admin-callback-csrf=${guardedCsrfToken}`,
  body: `type=invite&token_hash=fixture-csrf-guards-hash&callback_csrf=${guardedCsrfToken.slice(0, 14)}.${'b'.repeat(64)}`,
}));
assert.equal(mismatchedCallbackCsrf.status, 403, 'callback form token must match its cookie');
const duplicateCallbackCsrfCookie = await route(request('/api/admin/auth/callback', {
  method: 'POST',
  headers: { Origin: 'null', 'Content-Type': 'application/x-www-form-urlencoded' },
  cookie: `__Host-studiamatch-admin-callback-csrf=${guardedCsrfToken}; __Host-studiamatch-admin-callback-csrf=${guardedCsrfToken}`,
  body: `type=invite&token_hash=fixture-csrf-guards-hash&callback_csrf=${guardedCsrfToken}`,
}));
assert.equal(duplicateCallbackCsrfCookie.status, 403, 'duplicate callback CSRF cookies must be rejected');
const crossSiteOpaqueCallback = await route(request('/api/admin/auth/callback', {
  method: 'POST',
  headers: { Origin: 'null', 'Sec-Fetch-Site': 'cross-site', 'Content-Type': 'application/x-www-form-urlencoded' },
  cookie: `__Host-studiamatch-admin-callback-csrf=${guardedCsrfToken}`,
  body: `type=invite&token_hash=fixture-csrf-guards-hash&callback_csrf=${guardedCsrfToken}`,
}));
assert.equal(crossSiteOpaqueCallback.status, 403, 'opaque Origin does not override cross-site Fetch Metadata');
assert.equal(otpCalls.length, 2, 'mismatched, duplicate, and cross-site callback proofs must not consume an OTP');
const noOriginCallback = await route(request('/api/admin/auth/callback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  cookie: `__Host-studiamatch-admin-callback-csrf=${guardedCsrfToken}`,
  body: `type=invite&token_hash=fixture-csrf-guards-hash&callback_csrf=${guardedCsrfToken}`,
}));
assert.equal(noOriginCallback.status, 303, 'callback may accept an absent Origin only with its valid bound nonce');
assert.equal(otpCalls.length, 3);

const blockedCallbackPage = await route(request('/admin/auth/callback/?token_hash=fixture-blocked-callback-hash&type=invite'));
const blockedCsrfToken = /__Host-studiamatch-admin-callback-csrf=(\d{13}\.[a-f0-9]{64})/.exec(blockedCallbackPage.headers.get('set-cookie') || '')?.[1];
assert.ok(blockedCsrfToken);
const blockedCallbackPost = await route(request('/api/admin/auth/callback', {
  method: 'POST',
  headers: {
    Origin: 'https://evil.example',
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  cookie: `__Host-studiamatch-admin-callback-csrf=${blockedCsrfToken}`,
  body: `type=invite&token_hash=fixture-blocked-callback-hash&callback_csrf=${blockedCsrfToken}`,
}));
assert.equal(blockedCallbackPost.status, 403);
assert.equal(otpCalls.length, 3, 'cross-origin callback POST must not consume an OTP even with a valid nonce');

const wrongCallbackType = await route(request('/admin/auth/callback/?token_hash=fixture-token&type=magiclink'));
assert.equal(wrongCallbackType.status, 303);
assert.match(wrongCallbackType.headers.get('location') || '', /error=invalid/);
const providerCallbackError = await route(request('/admin/auth/callback/?error=access_denied&error_code=invitation_expired&error_description=private-provider-detail'));
assert.equal(providerCallbackError.status, 200, 'provider errors must terminate on a sanitized page, not redirect-loop');
const providerErrorHtml = await providerCallbackError.text();
assert.match(providerErrorHtml, /El enlace es inválido, expiró o ya fue utilizado/);
assert.equal(providerErrorHtml.includes('private-provider-detail'), false);
assert.equal(providerErrorHtml.includes('invitation_expired'), false);

const unsafeProject = await route(request('/api/admin/session'), {
  SUPABASE_URL: 'http://127.0.0.1.attacker.example',
});
assert.equal(unsafeProject.status, 503, 'non-local HTTP project URLs must fail closed');
const pathProject = await route(request('/api/admin/session'), {
  SUPABASE_URL: 'https://project-ref.supabase.co/unexpected-path',
});
assert.equal(pathProject.status, 503, 'project URLs with a path must fail closed');

mockFactors = [{ id: 'verified-factor', factor_type: 'totp', status: 'verified' }];
const blockAdditionalFactor = await route(request('/api/admin/auth/mfa', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { action: 'enroll' },
}));
assert.equal(blockAdditionalFactor.status, 403, 'AAL1 may not add a factor to an identity with an existing verified factor');
assert.equal(enrollmentCount, 0);

mockFactors = [];
const initialFactor = await route(request('/api/admin/auth/mfa', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { action: 'enroll' },
}));
assert.equal(initialFactor.status, 200, 'initial factor setup without a verified factor remains available');
assert.equal(enrollmentCount, 1);
const duplicatePendingFactor = await route(request('/api/admin/auth/mfa', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { action: 'enroll' },
}));
assert.equal(duplicatePendingFactor.status, 409, 'unverified setup cannot be duplicated');
const resetPendingFactor = await route(request('/api/admin/auth/mfa', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local' },
  cookie: csrfCookie,
  body: { action: 'unenroll', factorId: pendingFactorId },
}));
assert.equal(resetPendingFactor.status, 200, 'the user can reset their own unverified first-factor setup at AAL1');

currentSession.aal = 'aal2';
const forwardedRequestId = 'invite-operation-fixture-2026-10-01';
const invited = await route(request('/api/admin/invitations', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local', 'x-request-id': forwardedRequestId },
  cookie: csrfCookie,
  body: { email: 'new-user@local.test', role: 'user', resend: false },
}));
assert.equal(invited.status, 200);
assert.equal(inviteCalls.at(-1)[0], 'admin-invite');
assert.equal(inviteCalls.at(-1)[1].headers['x-request-id'], forwardedRequestId, 'BFF must propagate the caller idempotency key to Auth invitation processing');

inviteFailure = true;
const unresolvedRequestId = 'invite-operation-unresolved-2026-10-01';
const unresolvedInvite = await route(request('/api/admin/invitations', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local', 'x-request-id': unresolvedRequestId },
  cookie: csrfCookie,
  body: { email: 'new-user@local.test', role: 'user', resend: false },
}));
const unresolvedPayload = await unresolvedInvite.json();
assert.equal(unresolvedInvite.status, 409, 'BFF must preserve Edge reconciliation status');
assert.equal(unresolvedPayload.error.code, 'reconciliation_required', 'BFF must not hide the Edge outcome code');
assert.equal(unresolvedPayload.request_id, unresolvedRequestId, 'BFF must return the same operation reference');

inviteFailureCode = 'duplicate_ready';
const duplicateRequestId = 'invite-operation-duplicate-2026-10-02';
const duplicateInvite = await route(request('/api/admin/invitations', {
  method: 'POST',
  headers: { Origin: 'https://admin.preview.local', 'x-request-id': duplicateRequestId },
  cookie: csrfCookie,
  body: { email: 'existing-user@local.test', role: 'user', resend: false },
}));
const duplicatePayload = await duplicateInvite.json();
assert.equal(duplicateInvite.status, 502, 'internal membership outcome must not pass through the Edge status');
assert.equal(duplicatePayload.error.code, 'invitation_failed', 'internal membership outcome must be sanitized');
assert.equal(duplicatePayload.error.message, 'No se pudo completar la invitación.', 'sanitized response must use generic copy');
assert.equal(duplicatePayload.request_id, duplicateRequestId, 'sanitization must preserve the operation reference');

for (const [code, status] of [
  ['auth_rate_limited', 429],
  ['quota_rate_limited', 429],
  ['quota_unavailable', 503],
  ['unauthorized', 401],
  ['forbidden', 403],
  ['mfa_required', 403],
]) {
  inviteFailureCode = code;
  const requestId = `invite-operation-safe-${code}-2026-10-02`;
  const response = await route(request('/api/admin/invitations', {
    method: 'POST',
    headers: { Origin: 'https://admin.preview.local', 'x-request-id': requestId },
    cookie: csrfCookie,
    body: { email: 'new-user@local.test', role: 'user', resend: false },
  }));
  const payload = await response.json();
  assert.equal(response.status, status, `${code} must keep its safe HTTP status`);
  assert.equal(payload.error.code, code, `${code} must remain on the explicit safe-code allowlist`);
  assert.equal(payload.request_id, requestId, `${code} must preserve the request reference`);
}
inviteFailure = false;
inviteFailureCode = 'reconciliation_required';

const missingQuota = await route(request('/api/admin/session'), { ADMIN_QUOTA: undefined });
assert.equal(missingQuota.status,503);
const deniedQuota = await route(request('/api/admin/session'), {
  ADMIN_QUOTA:{fetch:async()=>new Response('{"allowed":false}',{status:429,headers:{'Retry-After':'60'}})},
});
assert.equal(deniedQuota.status,429);
assert.equal(deniedQuota.headers.get('Retry-After'),'60');
const forgedIp=request('/api/admin/session');
forgedIp.headers.delete('CF-Connecting-IP');
forgedIp.headers.set('X-Forwarded-For','192.0.2.1');
assert.equal((await route(forgedIp)).status,503);
const cleanup=await route(request('/api/admin/auth/logout',{
  method:'POST',headers:{Origin:'https://admin.preview.local'},cookie:[
    csrfCookie,
    '__Host-studiamatch-admin-auth.0=local-fixture-a',
    '__Host-studiamatch-admin-auth.1=local-fixture-b',
    '__Host-studiamatch-admin-auth.2=local-fixture-c',
    '__Host-studiamatch-admin-auth-code-verifier.0=local-verifier-a',
    '__Host-studiamatch-admin-auth-code-verifier.1=local-verifier-b',
  ].join('; '),body:{},
}),{ADMIN_QUOTA:undefined,SUPABASE_URL:undefined});
assert.equal(cleanup.status,200,'logout remains available when quota service fails');
const clearedAuthCookies=cleanup.headers.get('set-cookie') || '';
for(const name of [
  '__Host-studiamatch-admin-auth',
  '__Host-studiamatch-admin-auth.0',
  '__Host-studiamatch-admin-auth.1',
  '__Host-studiamatch-admin-auth.2',
  '__Host-studiamatch-admin-auth-code-verifier',
  '__Host-studiamatch-admin-auth-code-verifier.0',
  '__Host-studiamatch-admin-auth-code-verifier.1',
]) {
  assert.ok(clearedAuthCookies.includes(`${name}=; Path=/; Max-Age=0;`),`logout must clear ${name}`);
}

assert(cookieOptionsSeen.filter((options) => options.name.startsWith('__Host-studiamatch-admin-auth')).every((options) => options.httpOnly && options.secure && options.path === '/'));
console.log(JSON.stringify({
  result: 'PASS',
  checks: 127,
  quotaCases: 10,
  activityCookieRejectCases: 6,
  mfaSessionRebindCases: 1,
  sessionOriginRejectCases: 4,
  signingKeyConfigRejectCases: 4,
  authCookieNamesCleared: 7,
}));
