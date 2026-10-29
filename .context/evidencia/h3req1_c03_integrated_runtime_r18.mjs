// Local integrated C03 driver. It is prepared for the separately approved Docker
// drill only; do not run it as a component UAT or against a non-disposable endpoint.
import assert from 'node:assert/strict';
import { createHash, createHmac } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { createServer as createHttpServer } from 'node:http';
import { createServer as createHttpsServer } from 'node:https';
import { createRequire } from 'node:module';
import { mkdir, readFile } from 'node:fs/promises';
import { lstatSync, writeFileSync } from 'node:fs';
import { networkInterfaces } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { digestDirectories } from './h3req1_c03_cache_digest.mjs';
import {
  classifyInviteEarlyResult,
  classifyLoginResult,
  isIntegratedFailureCode,
} from './h3req1_c03_login_result.mjs';

const CONTROL_HOST = '127.0.0.1';
const CONTROL_PORT = 39191;
const HTTP_GATEWAY_PORT = 54321;
const HTTPS_GATEWAY_PORT = 5443;
const POSTGREST_BASE = new URL('http://h3req1-c03-postgrest:3000/');
const EDGE_ACTIVE_ORIGIN = 'http://h3req1-c03-edge-active:9000';
const EDGE_SUSPENDED_ORIGIN = 'http://h3req1-c03-edge-suspended:9000';
const ROOT = resolve(process.env.H3_C03_ROOT || dirname(dirname(fileURLToPath(import.meta.url))));
const TOOLS_ROOT = process.env.H3_C03_TOOLS_ROOT || '/tools';
const WEB_DEPS_ROOT = process.env.H3_C03_WEB_DEPS_ROOT || '/web-deps';
const CERTS_ROOT = process.env.H3_C03_CERTS_ROOT || '/run/c03-certs';
const PRIVATE_ROOT = process.env.H3_C03_PRIVATE_ROOT || '/run/c03-private';
const SOURCE_MANIFEST_SHA256 = process.env.H3_C03_MANIFEST_SHA256 || '';
const STARTUP_SOURCE_MANIFEST = 'tests/h3req1-c03-startup-source-s1-v4.sha256';

const ACTOR_ID = '70000000-0000-0000-0000-000000000001';
const TARGET_ID = '75000000-0000-0000-0000-000000000001';
const ACTOR_EMAIL = 'c03-admin@local.test';
const TARGET_EMAIL = 'c03-inflight@local.test';
const REQUEST_ID = 'c03-inflight-request-20261006';
const BLOCKED_REQUEST_ID = 'c03-suspended-request-20261006';
const DENIED_DISPATCH_NONCE = '77000000-0000-4000-8000-000000000001';
const GATEWAY_KEY_ID = 'local-pg17-k1';
const PROJECT_REF = 'local';
const LOCAL_PASSWORD = 'LocalOnly-Password9!';
const JWT_SECRET = createHash('sha256')
  .update('Studiamatch H3REQ1 C03 disposable PostgREST JWT fixture 2026-10-06')
  .digest('hex');
const PUBLISHABLE_KEY = ['sb', 'publishable', createHash('sha256')
  .update('Studiamatch H3REQ1 C03 publishable fixture 2026-10-06').digest('hex')].join('_');
const SERVICE_KEY = ['sb', 'secret', createHash('sha256')
  .update('Studiamatch H3REQ1 C03 service fixture 2026-10-06').digest('hex')].join('_');

const counters = {
  authUser: 0,
  authUserRequests: 0,
  authUserCredentialRejected: 0,
  authUserSessionRejected: 0,
  authUserAccepted: 0,
  authPassword: 0,
  authAdminUsers: 0,
  authInvite: 0,
  authRecovery: 0,
  requestAdmission: 0,
  invitationReserve: 0,
  adminMemberRequests: 0,
  adminMemberCredentialRejected: 0,
  adminMemberFailureResponses: 0,
  adminMemberLastStatus: 0,
  functionRequests: 0,
  functionCredentialRejected: 0,
  functionSessionRejected: 0,
  functionCalls: 0,
};
const INVITE_DIAGNOSTIC_FIELDS = Object.freeze([
  'authUserRequests', 'authUserCredentialRejected', 'authUserSessionRejected', 'authUserAccepted',
  'adminMemberRequests', 'adminMemberCredentialRejected', 'adminMemberFailureResponses',
  'adminMemberLastStatus', 'functionRequests', 'functionCredentialRejected',
  'functionSessionRejected', 'functionCalls', 'requestAdmission', 'invitationReserve',
]);

function edgeInterfaceAddress() {
  const addresses = Object.values(networkInterfaces()).flat()
    .filter((entry) => entry && !entry.internal && (entry.family === 'IPv4' || entry.family === 4));
  assert.equal(addresses.length, 1, 'runtime must start with exactly one non-loopback IPv4 on EDGE_NETWORK');
  return addresses[0].address;
}

let miniflare;
let workerRequestConstructor;
let workerHeadersConstructor;
let pagesActive;
let pagesSuspended;
let assetRequests = 0;
let cookieJar = new Map();
let inviteHoldStarted = false;
let releaseInvite;
let notifyInviteStarted;
const inviteStarted = new Promise((resolvePromise) => { notifyInviteStarted = resolvePromise; });
let inFlightInvite;
let inFlightResult;
let lastInvitationId;
let servers = [];
let startupGatewayRequests = 0;

const respondJson = (response, status, payload, headers = {}) => {
  response.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', ...headers });
  response.end(JSON.stringify(payload));
};

function signJwt(claims) {
  const encode = (value) => Buffer.from(JSON.stringify(value)).toString('base64url');
  const unsigned = `${encode({ alg: 'HS256', typ: 'JWT' })}.${encode(claims)}`;
  return `${unsigned}.${createHmac('sha256', JWT_SECRET).update(unsigned).digest('base64url')}`;
}

function verifyJwt(token) {
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const unsigned = `${parts[0]}.${parts[1]}`;
  const expected = createHmac('sha256', JWT_SECRET).update(unsigned).digest();
  let received;
  try { received = Buffer.from(parts[2], 'base64url'); } catch { return null; }
  if (received.length !== expected.length || !expected.equals(received)) return null;
  try {
    const claims = JSON.parse(Buffer.from(parts[1], 'base64url').toString('utf8'));
    if (claims.exp <= Math.floor(Date.now() / 1000) || claims.aud !== 'authenticated') return null;
    return claims;
  } catch { return null; }
}

function userJwt() {
  const now = Math.floor(Date.now() / 1000);
  return signJwt({
    iss: 'supabase', aud: 'authenticated', role: 'authenticated',
    sub: ACTOR_ID, aal: 'aal2', email: ACTOR_EMAIL, iat: now, exp: now + 3600,
  });
}

function serviceJwt() {
  const now = Math.floor(Date.now() / 1000);
  return signJwt({
    iss: 'supabase', aud: 'authenticated', role: 'service_role',
    iat: now, exp: now + 3600,
  });
}

function parseBearer(request) {
  const value = request.headers.authorization || '';
  return value.startsWith('Bearer ') ? value.slice(7) : '';
}

async function readBody(request, maxBytes = 128 * 1024) {
  const parts = [];
  let bytes = 0;
  for await (const chunk of request) {
    bytes += chunk.length;
    if (bytes > maxBytes) throw new Error('request body exceeded local fixture limit');
    parts.push(chunk);
  }
  return Buffer.concat(parts);
}

function postgrestDestination(pathname, search) {
  const restPath = pathname.replace(/^\/rest\/v1(?=\/|$)/, '') || '/';
  if (!restPath.startsWith('/') || restPath.startsWith('//') || restPath.includes('\\')) return null;
  const destination = new URL(`${restPath}${search}`, POSTGREST_BASE);
  if (destination.origin !== POSTGREST_BASE.origin || destination.username || destination.password || destination.hash) return null;
  return destination;
}

function relayResponse(response, upstream) {
  const headers = {};
  for (const name of [
    'content-type', 'content-range', 'content-profile', 'accept-profile',
    'preference-applied', 'retry-after', 'cache-control', 'location',
  ]) {
    const value = upstream.headers.get(name);
    if (value) headers[name] = value;
  }
  response.writeHead(upstream.status, headers);
  upstream.arrayBuffer().then((body) => response.end(Buffer.from(body))).catch(() => response.end());
}

function localUser(id, email, confirmed = false) {
  const timestamp = new Date(0).toISOString();
  return {
    id,
    aud: 'authenticated',
    role: 'authenticated',
    email,
    email_confirmed_at: confirmed ? timestamp : null,
    confirmed_at: confirmed ? timestamp : null,
    phone: '',
    last_sign_in_at: timestamp,
    app_metadata: { provider: 'email', providers: ['email'] },
    user_metadata: {},
    identities: [],
    created_at: timestamp,
    updated_at: timestamp,
    aal: 'aal2',
  };
}

async function handleAuth(request, response, url, body) {
  const pathname = url.pathname;
  const isUserRequest = pathname === '/auth/v1/user' && request.method === 'GET';
  if (isUserRequest) counters.authUserRequests += 1;
  const apiKey = request.headers.apikey || '';
  const isService = apiKey === SERVICE_KEY;
  const isPublishable = apiKey === PUBLISHABLE_KEY;
  if (!isService && !isPublishable) {
    if (isUserRequest) counters.authUserCredentialRejected += 1;
    return respondJson(response, 401, { message: 'local fixture API key rejected' });
  }

  if (isUserRequest) {
    counters.authUser += 1;
    const claims = verifyJwt(parseBearer(request));
    if (!claims || claims.sub !== ACTOR_ID) {
      counters.authUserSessionRejected += 1;
      return respondJson(response, 401, { message: 'local synthetic session rejected' });
    }
    counters.authUserAccepted += 1;
    return respondJson(response, 200, localUser(ACTOR_ID, ACTOR_EMAIL, true));
  }

  if (pathname === '/auth/v1/token' && request.method === 'POST' && url.searchParams.get('grant_type') === 'password') {
    counters.authPassword += 1;
    let payload;
    try { payload = JSON.parse(body.toString('utf8')); } catch { return respondJson(response, 400, { message: 'invalid local fixture request' }); }
    if (payload.email !== ACTOR_EMAIL || payload.password !== LOCAL_PASSWORD) {
      return respondJson(response, 400, { message: 'invalid local fixture credentials' });
    }
    const accessToken = userJwt();
    return respondJson(response, 200, {
      access_token: accessToken,
      token_type: 'bearer',
      expires_in: 3600,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      refresh_token: 'synthetic-refresh-token-not-for-any-service',
      user: localUser(ACTOR_ID, ACTOR_EMAIL, true),
    });
  }

  if (pathname === '/auth/v1/admin/users' && request.method === 'GET' && isService) {
    counters.authAdminUsers += 1;
    return respondJson(response, 200, {
      users: [localUser(ACTOR_ID, ACTOR_EMAIL, true), localUser(TARGET_ID, TARGET_EMAIL, false)],
      aud: 'authenticated',
    });
  }

  if (pathname === '/auth/v1/invite' && request.method === 'POST' && isService) {
    counters.authInvite += 1;
    let payload;
    try { payload = JSON.parse(body.toString('utf8')); } catch { return respondJson(response, 400, { message: 'invalid local fixture request' }); }
    if (payload.email !== TARGET_EMAIL) return respondJson(response, 400, { message: 'unexpected synthetic recipient' });
    if (inviteHoldStarted) return respondJson(response, 409, { message: 'unexpected duplicate local invite call' });
    inviteHoldStarted = true;
    notifyInviteStarted();
    await new Promise((resolvePromise) => { releaseInvite = resolvePromise; });
    return respondJson(response, 200, localUser(TARGET_ID, TARGET_EMAIL, false));
  }

  if (pathname === '/auth/v1/recover' && request.method === 'POST' && isService) {
    counters.authRecovery += 1;
    return respondJson(response, 200, { message: 'synthetic recovery fixture; no email sent' });
  }

  if (pathname === '/auth/v1/factors' && request.method === 'GET') {
    const claims = verifyJwt(parseBearer(request));
    if (!claims || claims.sub !== ACTOR_ID) return respondJson(response, 401, { message: 'local synthetic session rejected' });
    return respondJson(response, 200, { factors: [{ id: '76000000-0000-0000-0000-000000000001', factor_type: 'totp', status: 'verified' }] });
  }

  return respondJson(response, 404, { message: 'unsupported local Auth fixture route' });
}

async function handlePostgrest(request, response, url, body) {
  const isAdminMemberRequest = url.pathname === '/rest/v1/admin_members';
  if (isAdminMemberRequest) counters.adminMemberRequests += 1;
  const apiKey = request.headers.apikey || '';
  if (apiKey !== SERVICE_KEY && apiKey !== PUBLISHABLE_KEY) {
    if (isAdminMemberRequest) counters.adminMemberCredentialRejected += 1;
    return respondJson(response, 401, { code: 'fixture_api_key_rejected', message: 'Local fixture only' });
  }
  const headers = new Headers();
  for (const [name, value] of Object.entries(request.headers)) {
    if (typeof value === 'string' && !['host', 'connection', 'content-length'].includes(name.toLowerCase())) {
      headers.set(name, value);
    }
  }
  if (apiKey === SERVICE_KEY) headers.set('authorization', `Bearer ${serviceJwt()}`);
  const pathname = url.pathname;
  if (/^\/rest\/v1\/rpc\/admin_invitation_request_admit$/.test(pathname)) counters.requestAdmission += 1;
  if (/^\/rest\/v1\/rpc\/admin_invitation_reserve$/.test(pathname)) counters.invitationReserve += 1;

  const destination = postgrestDestination(url.pathname, url.search);
  if (!destination) return respondJson(response, 400, { code: 'invalid_local_data_path', message: 'Local fixture only' });
  const init = { method: request.method, headers, redirect: 'manual' };
  if (!['GET', 'HEAD'].includes(request.method)) init.body = body;
  const upstream = await fetch(destination, init);
  if (isAdminMemberRequest) {
    counters.adminMemberLastStatus = upstream.status;
    if (upstream.status < 200 || upstream.status >= 300) counters.adminMemberFailureResponses += 1;
  }
  relayResponse(response, upstream);
}

async function handleFunction(request, response, url, body) {
  counters.functionRequests += 1;
  if ((request.headers.apikey || '') !== PUBLISHABLE_KEY) {
    counters.functionCredentialRejected += 1;
    return respondJson(response, 401, { message: 'local function fixture API key rejected' });
  }
  const claims = verifyJwt(parseBearer(request));
  if (!claims || claims.sub !== ACTOR_ID) {
    counters.functionSessionRejected += 1;
    return respondJson(response, 401, { message: 'local synthetic session rejected' });
  }
  counters.functionCalls += 1;
  const destination = new URL(`/admin-invite${url.search}`, EDGE_ACTIVE_ORIGIN);
  const headers = new Headers();
  for (const [name, value] of Object.entries(request.headers)) {
    if (typeof value === 'string' && !['host', 'connection', 'content-length'].includes(name.toLowerCase())) headers.set(name, value);
  }
  const init = { method: request.method, headers, redirect: 'manual' };
  if (!['GET', 'HEAD'].includes(request.method)) init.body = body;
  const upstream = await fetch(destination, init);
  relayResponse(response, upstream);
}

async function handleGateway(request, response) {
  let url;
  try { url = new URL(request.url, 'https://local.supabase.co'); } catch { return respondJson(response, 400, { message: 'invalid local URL' }); }
  try {
    const body = ['GET', 'HEAD'].includes(request.method) ? Buffer.alloc(0) : await readBody(request);
    if (url.pathname.startsWith('/auth/v1/')) return await handleAuth(request, response, url, body);
    if (url.pathname === '/functions/v1/admin-invite') return await handleFunction(request, response, url, body);
    if (url.pathname.startsWith('/rest/v1/')) return await handlePostgrest(request, response, url, body);
    return respondJson(response, 404, { message: 'unsupported local Supabase fixture route' });
  } catch {
    if (!response.headersSent) respondJson(response, 502, { message: 'local fixture upstream unavailable' });
    else response.end();
  }
}

async function readGatewaySecret() {
  const sql = await readFile(join(ROOT, 'tests/sql/h3req1_c03_integrated_setup.sql'), 'utf8');
  const match = /^\\set gateway_secret '([^']+)'$/m.exec(sql);
  assert(match, 'the existing SQL harness must expose its synthetic local gateway fixture');
  assert(Buffer.byteLength(match[1]) >= 32, 'synthetic local RPC fixture must satisfy the SQL minimum');
  return match[1];
}

function createSyntheticTls() {
  const caKey = join(PRIVATE_ROOT, 'c03-ca.key');
  const caCert = join(CERTS_ROOT, 'ca.pem');
  const serverKey = join(PRIVATE_ROOT, 'c03-server.key');
  const serverCsr = join(PRIVATE_ROOT, 'c03-server.csr');
  const serverCert = join(PRIVATE_ROOT, 'c03-server.pem');
  const extensions = join(PRIVATE_ROOT, 'c03-server.ext');
  execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-sha256', '-days', '2',
    '-subj', '/CN=H3REQ1 C03 synthetic local CA', '-keyout', caKey, '-out', caCert], { stdio: 'ignore' });
  execFileSync('openssl', ['req', '-new', '-newkey', 'rsa:2048', '-nodes', '-sha256',
    '-subj', '/CN=local.supabase.co', '-keyout', serverKey, '-out', serverCsr], { stdio: 'ignore' });
  const extensionText = [
    'basicConstraints=critical,CA:FALSE',
    'keyUsage=critical,digitalSignature,keyEncipherment',
    'extendedKeyUsage=serverAuth',
    'subjectAltName=DNS:local.supabase.co',
  ].join('\n') + '\n';
  writeFileSync(extensions, extensionText, { mode: 0o600 });
  execFileSync('openssl', ['x509', '-req', '-sha256', '-days', '2', '-in', serverCsr,
    '-CA', caCert, '-CAkey', caKey, '-CAcreateserial', '-extfile', extensions, '-out', serverCert], { stdio: 'ignore' });
  return { key: serverKey, cert: serverCert };
}

async function createMiniflare({ startupOnly = false } = {}) {
  const require = createRequire(join(TOOLS_ROOT, 'package.json'));
  const { Log, LogLevel, Miniflare } = require('miniflare');
  const { Request: MiniflareRequest, Headers: MiniflareHeaders } = require('undici');
  const { build } = require('esbuild');
  assert.equal(typeof MiniflareRequest, 'function', 'Miniflare-compatible Request constructor must be available');
  assert.equal(typeof MiniflareHeaders, 'function', 'Miniflare-compatible Headers constructor must be available');
  workerRequestConstructor = MiniflareRequest;
  workerHeadersConstructor = MiniflareHeaders;
  const root = ROOT;
  const pagesBundle = await build({
    stdin: {
      contents: "import { onRequest } from './web/functions/_middleware.ts'; export default { fetch(request, env) { return onRequest({ request, env, next: () => env.ASSETS.fetch(request) }); } };",
      resolveDir: root,
      sourcefile: 'h3-c03-pages-entry.ts',
    },
    bundle: true,
    write: false,
    format: 'esm',
    platform: 'browser',
    target: 'es2022',
    nodePaths: [join(WEB_DEPS_ROOT, 'node_modules')],
  });
  const quotaBundle = await build({
    entryPoints: [join(root, 'workers/admin-quota/index.ts')],
    bundle: true,
    write: false,
    format: 'esm',
    platform: 'browser',
    target: 'es2022',
    nodePaths: [join(WEB_DEPS_ROOT, 'node_modules')],
  });
  const assets = async (request) => {
    assetRequests += 1;
    const pathname = new URL(request.url).pathname;
    if (pathname === '/' || pathname === '/courses/' || pathname.startsWith('/courses/')) {
      return new Response(`C03 synthetic public asset ${pathname}`, {
        status: 200,
        headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'public, max-age=0' },
      });
    }
    return new Response('Not found', { status: 404, headers: { 'Content-Type': 'text/plain' } });
  };
  const gatewaySecret = startupOnly
    ? 'S1_TEST_ONLY_NONSECRET_NO_REQUESTS_20261006'
    : await readGatewaySecret();
  const pagesActiveConfig = {
    name: 'h3-c03-pages-active',
    routes: ['admin.local.test/*', 'studiamatch.com/*'],
    modules: [{ type: 'ESModule', path: 'h3-c03-pages-active.mjs', contents: pagesBundle.outputFiles[0].text }],
    compatibilityDate: '2026-07-30',
    compatibilityFlags: ['nodejs_compat'],
    bindings: {
      ADMIN_ALLOWED_HOSTS: 'admin.local.test',
      ADMIN_BFF_ALLOW_LOCAL_AUTH_MOCK: startupOnly ? 'false' : 'true',
      ADMIN_BFF_SAFE_SUSPEND: 'false',
      ADMIN_RPC_GATEWAY_HMAC_KEY: gatewaySecret,
      ADMIN_RPC_GATEWAY_KEY_ID: GATEWAY_KEY_ID,
      ADMIN_QUOTA_HMAC_KEY: createHash('sha256').update('Studiamatch H3REQ1 C03 admin quota fixture 2026-10-06').digest('hex'),
      SUPABASE_URL: `http://127.0.0.1:${HTTP_GATEWAY_PORT}`,
      NEXT_SUPABASE_PUBLISHABLE_KEY: PUBLISHABLE_KEY,
    },
    serviceBindings: { ASSETS: assets, ADMIN_QUOTA: 'h3-c03-admin-quota' },
  };
  const pagesSuspendedConfig = {
    ...pagesActiveConfig,
    name: 'h3-c03-pages-suspended',
    modules: [{ type: 'ESModule', path: 'h3-c03-pages-suspended.mjs', contents: pagesBundle.outputFiles[0].text }],
    bindings: { ...pagesActiveConfig.bindings, ADMIN_BFF_SAFE_SUSPEND: 'true' },
  };
  const quotaConfig = {
    name: 'h3-c03-admin-quota',
    modules: [{ type: 'ESModule', path: 'h3-c03-admin-quota.mjs', contents: quotaBundle.outputFiles[0].text }],
    compatibilityDate: '2026-07-30',
    compatibilityFlags: ['nodejs_compat'],
    durableObjects: { ADMIN_QUOTA_COUNTER: 'AdminQuotaCounter' },
  };
  assert(gatewaySecret.length >= 32);
  miniflare = new Miniflare({
    durableObjectsPersist: false,
    workers: [quotaConfig, pagesActiveConfig, pagesSuspendedConfig],
    log: new Log(LogLevel.ERROR),
  });
  pagesActive = await miniflare.getWorker('h3-c03-pages-active');
  pagesSuspended = await miniflare.getWorker('h3-c03-pages-suspended');
  assert(pagesActive && pagesSuspended, 'both actual workerd Pages states must boot');
}

function getSetCookies(response) {
  if (typeof response.headers.getSetCookie === 'function') return response.headers.getSetCookie();
  const single = response.headers.get('set-cookie');
  return single ? [single] : [];
}

function mergeSetCookies(jar, response) {
  for (const line of getSetCookies(response)) {
    const pair = line.split(';', 1)[0];
    const separator = pair.indexOf('=');
    if (separator < 1) continue;
    const name = pair.slice(0, separator);
    const value = pair.slice(separator + 1);
    if (/;\s*Max-Age=0(?:;|$)/i.test(line)) jar.delete(name);
    else jar.set(name, value);
  }
}

function cookieHeader(jar) {
  return [...jar.entries()].map(([name, value]) => `${name}=${value}`).join('; ');
}

async function pagesRequest(worker, pathname, {
  method = 'GET', body, cookie = cookieHeader(cookieJar), requestId, hostname = 'admin.local.test',
} = {}) {
  const url = new URL(pathname, `https://${hostname}`);
  const headers = new workerHeadersConstructor({
    'CF-Connecting-IP': '192.0.2.44',
    ...(cookie ? { Cookie: cookie } : {}),
  });
  if (body !== undefined) {
    headers.set('Content-Type', 'application/json');
    headers.set('Origin', url.origin);
    headers.set('Sec-Fetch-Site', 'same-origin');
  }
  if (requestId) headers.set('x-request-id', requestId);
  const request = new workerRequestConstructor(url, {
    method,
    headers,
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  if (body !== undefined) {
    assert.equal(new URL(request.headers.get('Origin')).origin, new URL(request.url).origin,
      'synthetic mutation Origin must match its request URL');
    assert.equal(request.headers.get('Sec-Fetch-Site'), 'same-origin',
      'synthetic mutation must carry the same-origin fetch-site value');
  }
  const response = await worker.fetch(request);
  if (worker === pagesActive) mergeSetCookies(cookieJar, response);
  return response;
}

async function readJson(response) {
  return response.json().catch(() => ({}));
}

async function loginPages() {
  cookieJar.clear();
  const response = await pagesRequest(pagesActive, '/api/admin/auth/login', {
    method: 'POST',
    body: { email: ACTOR_EMAIL, password: LOCAL_PASSWORD },
  });
  const payload = await readJson(response);
  const checkCode = classifyLoginResult({
    status: response.status,
    errorCode: payload.error?.code,
    aal: payload.session?.aal,
    authCookie: cookieJar.has('__Host-studiamatch-admin-auth'),
    activityCookie: cookieJar.has('__Host-studiamatch-admin-activity'),
  });
  if (checkCode) throw new IntegratedCheckFailure(checkCode);
  return { result: 'PASS', aal: payload.session?.aal, authCookie: true, activityCookie: true };
}

class IntegratedCheckFailure extends Error {
  constructor(code, diagnostic = null) {
    super('integrated predicate failed');
    this.code = isIntegratedFailureCode(code) ? code : null;
    this.diagnostic = diagnostic;
  }
}

function inviteDiagnostic(baseline) {
  return Object.fromEntries(INVITE_DIAGNOSTIC_FIELDS.map((name) => [
    name,
    name === 'adminMemberLastStatus' ? counters[name] : counters[name] - baseline[name],
  ]));
}

async function waitForInviteHold(baseline, timeoutMs = 30_000) {
  if (inviteHoldStarted) return;
  let timeout;
  const outcome = await Promise.race([
    inviteStarted.then(() => ({ kind: 'held' })),
    inFlightInvite.then(
      (result) => ({ kind: 'early-response', result }),
      () => ({ kind: 'transport-failure' }),
    ),
    new Promise((resolvePromise) => {
      timeout = setTimeout(() => resolvePromise({ kind: 'timeout' }), timeoutMs);
    }),
  ]).finally(() => clearTimeout(timeout));
  if (outcome.kind === 'early-response') {
    throw new IntegratedCheckFailure(classifyInviteEarlyResult({
      status: outcome.result.response.status,
      errorCode: outcome.result.payload?.error?.code,
    }), inviteDiagnostic(baseline));
  }
  if (outcome.kind === 'transport-failure') {
    throw new IntegratedCheckFailure('INVITE_REQUEST_TRANSPORT_FAILURE', inviteDiagnostic(baseline));
  }
  if (outcome.kind === 'timeout') {
    throw new IntegratedCheckFailure('INVITE_AUTH_HOLD_TIMEOUT', inviteDiagnostic(baseline));
  }
}

async function triggerInFlight() {
  assert.equal(inviteHoldStarted, false, 'only one synthetic Auth invite may be held');
  const baseline = publicCounters();
  inFlightInvite = pagesRequest(pagesActive, '/api/admin/invitations', {
    method: 'POST',
    requestId: REQUEST_ID,
    body: { email: TARGET_EMAIL, role: 'user' },
  }).then(async (response) => ({ response, payload: await readJson(response) }));
  await waitForInviteHold(baseline);
  return { result: 'PASS', phase: 'auth-invite-held-after-reservation', counters: publicCounters() };
}

function publicCounters() {
  return { ...counters };
}

function suspendedCookieFixture() {
  return [
    '__Host-studiamatch-admin-auth.0=synthetic-chunk-a',
    '__Host-studiamatch-admin-auth.1=synthetic-chunk-b',
    '__Host-studiamatch-admin-auth-code-verifier.0=synthetic-verifier',
    '__Host-studiamatch-admin-activity=1760000000000',
    '__Host-studiamatch-admin-callback-csrf=synthetic-csrf',
  ].join('; ');
}

async function checkPagesSuspended() {
  const protectedRoutes = [
    '/admin/', '/admin/login/', '/admin/auth/callback/?token_hash=local-fixture', '/api/admin/session',
  ];
  for (const pathname of protectedRoutes) {
    const response = await pagesRequest(pagesSuspended, pathname, { cookie: suspendedCookieFixture() });
    assert.equal(response.status, 503, `${pathname} must stay suspended in actual workerd`);
    assert.equal(response.headers.get('Cache-Control'), 'private, no-store');
    assert.equal(response.headers.get('Retry-After'), '60');
    const setCookies = getSetCookies(response).join('\n');
    for (const name of [
      '__Host-studiamatch-admin-auth',
      '__Host-studiamatch-admin-auth-code-verifier',
      '__Host-studiamatch-admin-activity',
      '__Host-studiamatch-admin-callback-csrf',
      '__Host-studiamatch-admin-auth.0',
      '__Host-studiamatch-admin-auth.1',
      '__Host-studiamatch-admin-auth-code-verifier.0',
    ]) assert(setCookies.includes(`${name}=`) && setCookies.includes('Max-Age=0'), `${name} must be expired`);
  }

  for (const pathname of ['/', '/courses/', '/courses/c03-synthetic/']) {
    const response = await pagesRequest(pagesSuspended, pathname, { cookie: '', hostname: 'studiamatch.com' });
    assert.equal(response.status, 200, `${pathname} public fixture must remain available`);
    assert((await response.text()).includes('C03 synthetic public asset'));
  }
  const publicAssetCount = assetRequests;
  for (const pathname of [
    '/%61dmin/', '/%2561dmin/', '/%2525252561dmin/', '/%252e/admin/',
    '/admin/%61uth/callback', '/api/%61dmin/session', '/%25252fadmin/', '//admin/',
  ]) {
    const response = await pagesRequest(pagesSuspended, pathname, { cookie: '' });
    assert([404, 503].includes(response.status), `${pathname} must remain in the Admin perimeter`);
    assert.notEqual(response.status, 200, `${pathname} must not expose an asset`);
  }
  assert.equal(assetRequests, publicAssetCount, 'encoded Admin aliases must not reach the asset fallback');
  const publicHost = await pagesRequest(pagesSuspended, '/admin/', { cookie: '', hostname: 'studiamatch.com' });
  assert.equal(publicHost.status, 404, 'public hostname must not expose Admin');
  assert.equal(assetRequests, publicAssetCount, 'public hostname Admin rejection must not reach static assets');
  cookieJar.clear();
  return { result: 'PASS', routes503: protectedRoutes.length, cookiesExpired: 7, publicFixtures: 3, aliasesRejected: 8 };
}

async function checkEdgeSuspended() {
  const before = publicCounters();
  const response = await fetch(`${EDGE_SUSPENDED_ORIGIN}/admin-invite`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${userJwt()}`, 'Content-Type': 'application/json', 'x-request-id': BLOCKED_REQUEST_ID },
    body: JSON.stringify({ email: 'c03-suspended@local.test', role: 'user' }),
    redirect: 'manual',
  });
  const payload = await readJson(response);
  assert.equal(response.status, 503, 'safe-suspended real Edge Runtime must reject a new invitation');
  assert.equal(payload.code, 'maintenance_mode');
  const after = publicCounters();
  assert.equal(after.authUser - before.authUser, 1, 'Edge authorization still performs its synthetic getUser check before the guard');
  assert.equal(after.authInvite - before.authInvite, 0, 'no Auth invitation/email call may occur while suspended');
  assert.equal(after.authRecovery - before.authRecovery, 0, 'no Auth recovery/email call may occur while suspended');
  assert.equal(after.invitationReserve - before.invitationReserve, 0, 'no invitation reservation may occur while suspended');
  assert.equal(after.requestAdmission - before.requestAdmission, 1, 'the pre-guard admission RPC creates one measured quota event');
  return { result: 'PASS', status: response.status, code: payload.code, syntheticGetUser: 1, admissionEvents: 1, reservations: 0, authEmailCalls: 0 };
}

async function checkEdgeReady(origin) {
  const response = await fetch(`${origin}/admin-invite`, {
    method: 'OPTIONS',
    headers: { Origin: 'https://admin.local.test' },
    redirect: 'manual',
  });
  assert.equal(response.status, 200, 'real Edge Runtime function must finish its OPTIONS startup path');
  return { result: 'PASS', runtime: origin === EDGE_ACTIVE_ORIGIN ? 'edge-active' : 'edge-suspended', status: response.status };
}

async function checkSignedDispatcherDenied() {
  const args = {
    p_course_id: '20000000-0000-0000-0000-000000000001',
    p_manual_overrides: { name: 'C03 suspended dispatcher must be blocked' },
    p_version: 1,
    p_reason: 'C03 suspended dispatcher synthetic attempt',
  };
  const signedPayload = JSON.stringify(args);
  const issuedAt = String(Math.floor(Date.now() / 1000));
  const gatewaySecret = await readGatewaySecret();
  const canonical = [
    'studiamatch-admin-rpc-v1', PROJECT_REF, 'POST', 'admin_signed_rpc', ACTOR_ID,
    issuedAt, DENIED_DISPATCH_NONCE, GATEWAY_KEY_ID,
  ].join('\n');
  const payloadCanonical = [
    'studiamatch-admin-rpc-payload-v1', PROJECT_REF, 'POST', 'admin_signed_rpc',
    'admin_update_course', ACTOR_ID, issuedAt, DENIED_DISPATCH_NONCE,
    GATEWAY_KEY_ID, signedPayload,
  ].join('\n');
  const headers = {
    apikey: PUBLISHABLE_KEY,
    Authorization: `Bearer ${userJwt()}`,
    'Content-Type': 'application/json',
    'x-studiamatch-admin-rpc-key-id': GATEWAY_KEY_ID,
    'x-studiamatch-admin-rpc-actor': ACTOR_ID,
    'x-studiamatch-admin-rpc-issued-at': issuedAt,
    'x-studiamatch-admin-rpc-nonce': DENIED_DISPATCH_NONCE,
    'x-studiamatch-admin-rpc-signature': createHmac('sha256', gatewaySecret).update(canonical).digest('hex'),
    'x-studiamatch-admin-rpc-payload-signature': createHmac('sha256', gatewaySecret).update(payloadCanonical).digest('hex'),
  };
  const response = await fetch(`${POSTGREST_BASE.origin}/rpc/admin_signed_rpc`, {
    method: 'POST', headers,
    body: JSON.stringify({ p_rpc_name: 'admin_update_course', p_args: args, p_signed_payload: signedPayload }),
    redirect: 'manual',
  });
  const payload = await readJson(response);
  assert([401, 403].includes(response.status), 'valid proof must be denied by suspended dispatcher ACL');
  assert.equal(payload.code, '42501', 'PostgREST must report permission denial before the SECURITY DEFINER target runs');
  return { result: 'PASS', status: response.status, code: payload.code, noncePreserved: true };
}

async function releaseInFlight() {
  assert(inviteHoldStarted && typeof releaseInvite === 'function', 'the synthetic Auth request must be held before release');
  releaseInvite();
  inFlightResult = await inFlightInvite;
  assert.equal(inFlightResult.response.status, 200, 'in-flight Pages→Edge operation must complete after safe suspension');
  assert.equal(inFlightResult.payload.success, true);
  assert.equal(inFlightResult.payload.email, TARGET_EMAIL);
  assert.equal(counters.authInvite, 1, 'exactly one synthetic Auth invite request reached the local gate');
  lastInvitationId = inFlightResult.payload.invitation_id;
  assert.match(lastInvitationId || '', /^[0-9a-f-]{36}$/i);
  return { result: 'PASS', status: inFlightResult.response.status, completedOnce: true, syntheticAuthCalls: counters.authInvite };
}

async function pagesAndEdgeRecovery() {
  const inviteCountBeforeReplay = counters.authInvite;
  const edgeReplay = await fetch(`${EDGE_ACTIVE_ORIGIN}/admin-invite`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${userJwt()}`,
      'Content-Type': 'application/json',
      Origin: 'https://admin.local.test',
      'x-request-id': REQUEST_ID,
    },
    body: JSON.stringify({ email: TARGET_EMAIL, role: 'user' }),
    redirect: 'manual',
  });
  const edgeReplayPayload = await readJson(edgeReplay);
  assert.equal(edgeReplay.status, 200, 'Edge must recover and replay the completed request before Pages smoke');
  assert.equal(edgeReplayPayload.invitation_id, lastInvitationId);
  assert.equal(counters.authInvite, inviteCountBeforeReplay, 'Edge recovery replay must not send a second Auth email');

  await loginPages();
  const session = await pagesRequest(pagesActive, '/api/admin/session');
  const sessionPayload = await readJson(session);
  assert.equal(session.status, 200, 'Pages session must work after SQL safe-resume');
  assert.equal(sessionPayload.authenticated, true);
  assert.equal(sessionPayload.session?.aal, 'aal2');

  const role = await pagesRequest(pagesActive, '/api/admin/rpc', {
    method: 'POST', body: { function: 'admin_current_user_role', params: {} },
  });
  const rolePayload = await readJson(role);
  assert.equal(role.status, 200, 'BFF signed dispatcher call must recover after safe-resume');
  assert.equal(rolePayload.data, 'admin');

  return { result: 'PASS', edgeReplaySameInvitation: true, sessionAal: sessionPayload.session.aal, role: rolePayload.data, secondAuthEmail: false };
}

async function handleControl(request, response) {
  const url = new URL(request.url, `http://${CONTROL_HOST}:${CONTROL_PORT}`);
  try {
    if (request.method === 'GET' && url.pathname === '/healthz') {
      return respondJson(response, 200, { ready: Boolean(miniflare && pagesActive && pagesSuspended), workerd: Boolean(pagesActive && pagesSuspended) });
    }
    if (request.method !== 'POST') return respondJson(response, 405, { error: 'method_not_allowed' });
    let result;
    if (url.pathname === '/control/login') result = await loginPages();
    else if (url.pathname === '/control/trigger-inflight') result = await triggerInFlight();
    else if (url.pathname === '/control/pages-suspended') result = await checkPagesSuspended();
    else if (url.pathname === '/control/edge-suspended') result = await checkEdgeSuspended();
    else if (url.pathname === '/control/signed-dispatcher') result = await checkSignedDispatcherDenied();
    else if (url.pathname === '/control/release-inflight') result = await releaseInFlight();
    else if (url.pathname === '/control/edge-active-ready') result = await checkEdgeReady(EDGE_ACTIVE_ORIGIN);
    else if (url.pathname === '/control/edge-suspended-ready') result = await checkEdgeReady(EDGE_SUSPENDED_ORIGIN);
    else if (url.pathname === '/control/recovery') result = await pagesAndEdgeRecovery();
    else if (url.pathname === '/control/counters') result = { result: 'PASS', counters: publicCounters() };
    else if (url.pathname === '/control/finish') {
      assert(!inviteHoldStarted || inFlightResult, 'do not finish while an Auth request remains in flight');
      result = { result: 'PASS', counters: publicCounters() };
      respondJson(response, 200, result);
      setImmediate(() => void closeRuntime());
      return;
    } else return respondJson(response, 404, { error: 'unknown_control_step' });
    return respondJson(response, 200, result);
  } catch (error) {
    const errorType = error instanceof Error && /^[A-Za-z]+Error$/.test(error.name) ? error.name : 'AssertionError';
    const checkCode = error instanceof IntegratedCheckFailure && isIntegratedFailureCode(error.code) ? error.code : undefined;
    const diagnostic = error instanceof IntegratedCheckFailure && error.diagnostic
      ? { diagnostic: error.diagnostic }
      : {};
    process.stderr.write(`${JSON.stringify({ event: 'h3-c03-control-failed', step: url.pathname, error: errorType, ...(checkCode ? { check: checkCode } : {}), ...diagnostic })}\n`);
    return respondJson(response, 500, { error: 'integrated_step_failed', step: url.pathname, type: errorType, ...(checkCode ? { check: checkCode } : {}), ...diagnostic });
  }
}

async function handleStartupSmokeControl(request, response) {
  const url = new URL(request.url, `http://${CONTROL_HOST}:${CONTROL_PORT}`);
  if (request.method === 'GET' && url.pathname === '/healthz') {
    return respondJson(response, 200, { ready: Boolean(miniflare && pagesActive && pagesSuspended), workerd: Boolean(pagesActive && pagesSuspended) });
  }
  if (request.method === 'POST' && url.pathname === '/control/finish') {
    assert.equal(startupGatewayRequests, 0, 'startup-only smoke must not dispatch synthetic Auth/PostgREST/Function requests');
    respondJson(response, 200, { result: 'PASS', mode: 'startup-only' });
    setImmediate(() => void closeRuntime());
    return;
  }
  return respondJson(response, 404, { error: 'startup_smoke_route_not_allowlisted' });
}

function handleStartupSmokeGateway(_request, response) {
  startupGatewayRequests += 1;
  return respondJson(response, 404, { error: 'startup_smoke_gateway_disabled' });
}

async function closeRuntime() {
  if (miniflare) await miniflare.dispose().catch(() => {});
  await Promise.all(servers.map((server) => new Promise((resolvePromise) => server.close(resolvePromise))));
  servers = [];
}

async function runServer({ startupOnly = false } = {}) {
  const manifestPath = join(ROOT, startupOnly
    ? STARTUP_SOURCE_MANIFEST
    : 'tests/h3req1-c03-integrated.sha256');
  const manifestBytes = await readFile(manifestPath);
  assert.match(SOURCE_MANIFEST_SHA256, /^[a-f0-9]{64}$/);
  assert.equal(createHash('sha256').update(manifestBytes).digest('hex'), SOURCE_MANIFEST_SHA256,
    'immutable source snapshot manifest digest changed');
  execFileSync('sha256sum', ['-c', manifestPath], { cwd: ROOT, stdio: ['ignore', 'ignore', 'pipe'] });
  const gatewayBindHost = edgeInterfaceAddress();
  assert.equal(postgrestDestination('/rest/v1/rpc/admin_signed_rpc', '').origin, POSTGREST_BASE.origin);
  assert.equal(postgrestDestination('/rest/v1//127.0.0.1:5432/', ''), null);
  assert.equal(postgrestDestination('/rest/v1/\\127.0.0.1:5432/', ''), null);
  if (startupOnly) {
    assert.equal(process.env.H3_C03_DEPENDENCY_BOOTSTRAP_COMPLETE, 'true', 'startup-only smoke requires both locked npm bootstraps to finish');
    for (const root of [join(TOOLS_ROOT, 'node_modules'), join(WEB_DEPS_ROOT, 'node_modules')]) {
      const stat = lstatSync(root);
      assert(stat.isDirectory() && !stat.isSymbolicLink(), 'fresh locked dependency root must be a real directory');
    }
    process.stdout.write(`${JSON.stringify({ event: 'h3-c03-startup-dependency-roots-present' })}\n`);
  } else {
    const actualDependencyDigests = await digestDirectories({
      'deno-cache': '/deno-cache',
      'edge-node-modules': '/edge-node-modules',
      'miniflare-node-modules': '/tools/node_modules',
      'pages-node-modules': '/web-deps/node_modules',
    });
    const expectedDependencyDigests = JSON.parse(process.env.H3_C03_EXPECTED_DEPENDENCY_DIGESTS || '{}');
    assert.deepEqual(actualDependencyDigests, expectedDependencyDigests, 'read-only dependency volume content changed after bootstrap verification');
    process.stdout.write(`${JSON.stringify({ event: 'h3-c03-dependency-digests-verified', digests: actualDependencyDigests })}\n`);
  }
  await mkdir(CERTS_ROOT, { recursive: true });
  await mkdir(PRIVATE_ROOT, { recursive: true });
  const { key, cert } = createSyntheticTls();
  await createMiniflare({ startupOnly });

  const tlsMaterial = { key: await readFile(key), cert: await readFile(cert) };
  const gatewayHandler = startupOnly ? handleStartupSmokeGateway : handleGateway;
  const httpsServer = createHttpsServer(tlsMaterial, (request, response) => void gatewayHandler(request, response));
  const httpServer = createHttpServer((request, response) => void gatewayHandler(request, response));
  const controlHandler = startupOnly ? handleStartupSmokeControl : handleControl;
  const controlServer = createHttpServer((request, response) => void controlHandler(request, response));
  servers = [httpsServer, httpServer, controlServer];
  await Promise.all([
    new Promise((resolvePromise, reject) => httpsServer.listen(HTTPS_GATEWAY_PORT, gatewayBindHost, (error) => error ? reject(error) : resolvePromise())),
    new Promise((resolvePromise, reject) => httpServer.listen(HTTP_GATEWAY_PORT, CONTROL_HOST, (error) => error ? reject(error) : resolvePromise())),
    new Promise((resolvePromise, reject) => controlServer.listen(CONTROL_PORT, CONTROL_HOST, (error) => error ? reject(error) : resolvePromise())),
  ]);
  process.stdout.write(`${JSON.stringify({ event: 'h3-c03-runtime-ready', workerd: true, tls: 'synthetic-local-ca', ports: 'internal-only' })}\n`);
  const stop = () => void closeRuntime();
  process.once('SIGTERM', stop);
  process.once('SIGINT', stop);
}

async function invokeControl(command) {
  const response = await fetch(`http://${CONTROL_HOST}:${CONTROL_PORT}/control/${command}`, { method: 'POST' });
  const payload = await readJson(response);
  if (!response.ok) {
    process.stderr.write(`${JSON.stringify(payload)}\n`);
    process.exitCode = 1;
    return;
  }
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

if (process.argv[2] === '--startup-smoke') {
  assert.equal(process.env.H3_C03_STARTUP_ONLY, 'true', 'startup-only mode requires the explicit smoke environment guard');
  await runServer({ startupOnly: true });
} else if (process.argv[2] === '--control') {
  const command = process.argv[3] || '';
  if (!/^(healthz|login|trigger-inflight|pages-suspended|edge-suspended|signed-dispatcher|release-inflight|edge-active-ready|edge-suspended-ready|recovery|counters|finish)$/.test(command)) {
    process.stderr.write('invalid control step\n');
    process.exitCode = 2;
  } else if (command === 'healthz') {
    const response = await fetch(`http://${CONTROL_HOST}:${CONTROL_PORT}/healthz`);
    const payload = await readJson(response);
    process.stdout.write(`${JSON.stringify(payload)}\n`);
    if (!payload.ready) process.exitCode = 1;
  } else await invokeControl(command);
} else {
  await runServer();
}
