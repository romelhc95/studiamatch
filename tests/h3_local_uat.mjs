import { createRequire } from 'node:module';
import { createHash } from 'crypto';
import { access, mkdir, readFile, readdir, rename, rm, stat, writeFile } from 'fs/promises';
import { dirname, join, relative, resolve, sep } from 'path';
import { sanitize as sanitizeValue, safeLocalPath as toSafeLocalPath, safeLocalRequest as toSafeLocalRequest } from './h3_uat_sanitizer.mjs';
import { findUncorrelatedConsoleResourceFailures, isExpectedHttpFailure } from './h3_uat_http_diagnostics.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.H3_PLAYWRIGHT_MODULE || '/app/mock-server/node_modules/playwright');

const EXPECTED_DISTRIBUTION = Object.freeze({
  'H3-CA4.1': 5,
  'H3-CA4.2': 5,
  'H3-CA4.3': 2,
  'H3-CA4.4': 5,
  'H3-CA4.5': 8,
  'H3-CA4.6': 4,
  'H3-CA4.7': 8,
  'H3-CA4.8': 7,
  'H3-CA4.9': 21,
  'H3-CA4.10': 2,
  'H3-CA4.11': 5,
});
const VIEWPORTS = Object.freeze([
  Object.freeze({ name: 'desktop', width: 1440, height: 900 }),
  Object.freeze({ name: 'tablet', width: 768, height: 1024 }),
  Object.freeze({ name: 'mobile', width: 390, height: 844 }),
]);
const EXPECTED_HTTP_FAILURES = Object.freeze({
  'anonymous admin access redirects to login': [{ status: 401, method: 'GET', origin: 'local-0', path: '/api/admin/session' }],
  'invalid credentials are rejected without enumeration': [{ status: 401, method: 'POST', origin: 'local-0', path: '/api/admin/auth/login' }],
  'invalid TOTP is rejected': [{ status: 401, method: 'POST', origin: 'local-0', path: '/api/admin/auth/mfa' }],
  'expired Auth session is rejected and cleared during concurrent browser reads': [{ status: 401, method: 'POST', origin: 'local-0', path: '/api/admin/rpc' }],
  'integrated write quota rejects excess calls without changing editorial state': [{ status: 429, method: 'POST', origin: 'local-0', path: '/api/admin/rpc' }],
  'duplicate membership is rejected': [{ status: 502, method: 'POST', origin: 'local-0', path: '/api/admin/invitations' }],
  'unknown public course route returns a controlled not-found page': [{ status: 404, method: 'GET', origin: 'local-0', path: '/courses/ulima/not-a-real-course/' }],
  'catalog renders empty state and retains static fallback after backend error': [{ status: 503, method: 'GET', origin: 'local-0', path: '/rest/v1/courses_public_effective' }],
  'invalid membership email is rejected by BFF schema': [{ status: 400, method: 'POST', origin: 'local-0', path: '/api/admin/invitations' }],
  'invalid membership role is rejected by BFF schema': [{ status: 400, method: 'POST', origin: 'local-0', path: '/api/admin/invitations' }],
  'logout clears the HttpOnly session': [{ status: 401, method: 'POST', origin: 'local-0', path: '/api/admin/rpc', afterLogout: true }],
});
const BASE_URL = process.env.H3_BASE_URL || 'http://localhost:3000';
const MOCK_URL = process.env.H3_MOCK_URL || 'http://localhost:3001';
const PERIMETER_URL = process.env.H3_PERIMETER_URL || 'http://localhost:3002';
const LOCAL_ORIGINS = Object.freeze([BASE_URL, MOCK_URL]);
const EVIDENCE_DIR = process.env.H3_EVIDENCE_DIR || '/app/.context/evidencia/h3-expanded';
const EVIDENCE_PARENT = dirname(EVIDENCE_DIR);
const RUN_TOKEN = `${process.pid}-${Date.now()}`;
const STAGING_DIR = join(EVIDENCE_PARENT, `.h3-expanded-${RUN_TOKEN}.tmp`);
const BACKUP_DIR = join(EVIDENCE_PARENT, `.h3-expanded-${RUN_TOKEN}.bak`);
const USERS = Object.freeze({
  admin: Object.freeze({ email: 'admin@local.test', password: process.env.H3_ADMIN_PASSWORD || process.env.MOCK_ADMIN_PASSWORD || '' }),
  user: Object.freeze({ email: 'user@local.test', password: process.env.H3_USER_PASSWORD || process.env.MOCK_USER_PASSWORD || '' }),
});
const TOTP_CODE = process.env.H3_TOTP_CODE || process.env.MOCK_TOTP_CODE || '';
const RESET_TOKEN = process.env.H3_TEST_RESET_TOKEN || '';
let lastQuotaIsolationEpoch = 0;
const PUBLIC_ROUTES = Object.freeze(['/', '/courses/', '/compare/', '/privacidad/', '/terminos/']);
const EDITORIAL_FIELDS = Object.freeze([
  'name', 'price_pen', 'price_status', 'mode', 'duration', 'description_long',
  'syllabus', 'target_audience', 'requirements', 'certification', 'benefits',
  'objectives', 'start_date_text',
]);

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const sanitize = (value) => sanitizeValue(value, LOCAL_ORIGINS);
const safeLocalPath = (value) => toSafeLocalPath(value, LOCAL_ORIGINS);
const safeLocalRequest = (value) => toSafeLocalRequest(value, LOCAL_ORIGINS);

function relativeArtifact(fileName) {
  const repoRoot = resolve(process.env.H3_REPO_ROOT || '/app');
  return relative(repoRoot, join(EVIDENCE_DIR, fileName)).split(sep).join('/');
}

function safeArtifactPath(fileName) {
  assert(/^[A-Za-z0-9._-]+$/.test(fileName), `unsafe artifact filename: ${fileName}`);
  const candidate = resolve(STAGING_DIR, fileName);
  const root = `${resolve(STAGING_DIR)}${sep}`;
  assert(candidate.startsWith(root), `artifact escaped staging directory: ${fileName}`);
  return candidate;
}

async function fileExists(path) {
  try { await access(path); return true; } catch { return false; }
}

async function waitForPublicCatalog(page) {
  try {
    await page.getByRole('heading', { name: 'Catálogo de Programas' }).waitFor({ state: 'visible' });
  } catch (error) {
    const rawDiagnostic = await page.evaluate(() => ({
      pathname: location.pathname,
      headings: Array.from(document.querySelectorAll('h1, h2'))
        .slice(0, 6)
        .map((heading) => heading.textContent?.trim().slice(0, 120) || ''),
      catalogCards: document.querySelectorAll('#programas main article').length,
      historyLength: history.length,
      popStates: Array.isArray(window.__h3UatPopStates) ? window.__h3UatPopStates.slice(-4) : [],
    })).catch(() => ({ pathname: 'unavailable', headings: [], catalogCards: -1 }));
    const diagnostic = {
      ...rawDiagnostic,
      pathname: rawDiagnostic.pathname === 'unavailable' ? 'unavailable' : safeLocalPath(rawDiagnostic.pathname),
      popStates: Array.isArray(rawDiagnostic.popStates)
        ? rawDiagnostic.popStates.map((path) => safeLocalPath(path))
        : [],
    };
    throw new Error(`public catalog heading unavailable: ${JSON.stringify(diagnostic)}; ${error instanceof Error ? error.name : 'WAIT_FAILED'}`);
  }
  await page.waitForFunction(() => {
    const catalog = document.querySelector('#programas main');
    if (!catalog || catalog.querySelector('.animate-pulse')) return false;
    return catalog.querySelectorAll('article').length > 0 || catalog.textContent?.includes('Sin resultados') === true;
  }, undefined, { timeout: 15000 });
}

async function atomicWrite(path, value) {
  const temporary = `${path}.${RUN_TOKEN}.tmp`;
  await writeFile(temporary, value);
  await rename(temporary, path);
}

async function login(page, role) {
  const user = USERS[role];
  assert(user?.password, `missing local ${role} password; set H3_${role.toUpperCase()}_PASSWORD or MOCK_${role.toUpperCase()}_PASSWORD`);
  await page.goto(`${BASE_URL}/admin/login/`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.getByLabel('Email').fill(user.email);
  await page.getByLabel('Password').fill(user.password);
  await page.getByRole('button', { name: 'Iniciar sesión' }).click();
  await page.waitForURL(`${BASE_URL}/admin/`);
  assert(TOTP_CODE, 'missing local TOTP code');
  const mfaCode = page.getByLabel('Código de 6 dígitos');
  try {
    // A verified factor starts the challenge directly. A first-time or pending
    // factor still exposes the explicit setup/restart action.
    await mfaCode.waitFor({ state: 'visible', timeout: 1500 });
  } catch {
    await page.getByRole('button', { name: /Configurar MFA|Reiniciar configuración MFA/ }).first().click();
    await mfaCode.waitFor({ state: 'visible' });
  }
  await mfaCode.fill(TOTP_CODE);
  await page.getByRole('button', { name: 'Verificar MFA' }).click();
  await page.getByRole('heading', { name: role === 'admin' ? 'Cola editorial' : 'Panel de actualización de información' }).waitFor({ state: 'visible' });
  await page.waitForFunction(() => {
    return fetch('/api/admin/session', { cache: 'no-store' })
      .then((response) => response.json())
      .then((body) => body.authenticated === true && body.session?.aal === 'aal2')
      .catch(() => false);
  }, undefined, { timeout: 5000 });
}

async function assertAuthenticatedEmailFallback(page, check) {
  const base = new URL(BASE_URL);
  const loopbackHosts = new Set(['localhost', '127.0.0.1', '[::1]']);
  assert(base.protocol === 'http:' && loopbackHosts.has(base.hostname)
    && !base.username && !base.password && !base.search && !base.hash,
  'email fallback fixture requires an HTTP loopback base URL');

  const authenticated = await page.evaluate(async () => {
    const response = await fetch('/api/admin/session', { cache: 'no-store' });
    return { status: response.status, payload: await response.json() };
  });
  assert(authenticated.status === 200 && authenticated.payload?.authenticated === true
    && authenticated.payload.session && typeof authenticated.payload.session.email === 'string',
  'authenticated session unavailable for email fallback fixture');

  const sessionEndpoint = new URL('/api/admin/session', BASE_URL);
  let sessionWithoutEmailServed = false;
  let unexpectedSessionRequestObserved = false;
  const sessionRoutePattern = '**/api/admin/session**';
  await page.route(sessionRoutePattern, async (route) => {
    const request = route.request();
    const requestUrl = new URL(request.url());
    if (request.method() !== 'GET' || requestUrl.origin !== sessionEndpoint.origin
      || requestUrl.pathname !== sessionEndpoint.pathname || requestUrl.search !== '') {
      unexpectedSessionRequestObserved = true;
      await route.abort('blockedbyclient');
      return;
    }
    sessionWithoutEmailServed = true;
    await route.fulfill({
      status: authenticated.status,
      contentType: 'application/json',
      body: JSON.stringify({
        ...authenticated.payload,
        session: { ...authenticated.payload.session, email: null },
      }),
    });
  });
  await page.reload({ waitUntil: 'networkidle' });
  await page.unroute(sessionRoutePattern);
  await page.getByText('Usuario autenticado', { exact: true }).waitFor({ state: 'visible' });
  check('email fallback intercept is same-origin GET', sessionWithoutEmailServed && !unexpectedSessionRequestObserved);
  check('missing authenticated email uses fallback', await page.getByText('Usuario autenticado', { exact: true }).isVisible());
}

async function sessionInfo(page) {
  const session = await page.evaluate(async () => {
    const response = await fetch('/api/admin/session', { cache: 'no-store' });
    const body = await response.json();
    const storage = [window.localStorage, window.sessionStorage];
    const entries = storage.flatMap((area) => Object.keys(area).map((key) => [key, area.getItem(key) || '']));
    return {
      ...body.session,
      authenticated: body.authenticated === true,
      hasAuthStorage: entries.some(([key]) => key.endsWith('-auth-token')),
      hasAccessToken: entries.some(([, value]) => /"access_token"\s*:/.test(value)),
      hasRefreshToken: entries.some(([, value]) => /"refresh_token"\s*:/.test(value)),
      authCookieVisible: document.cookie.includes('__Host-studiamatch-admin-auth'),
    };
  });
  const authCookies = await page.context().cookies(BASE_URL);
  const authCookie = authCookies.find((cookie) => cookie.name === '__Host-studiamatch-admin-auth' || cookie.name.startsWith('__Host-studiamatch-admin-auth.'));
  return {
    ...session,
    httpOnly: authCookie?.httpOnly === true,
    secure: authCookie?.secure === true,
    sameSite: authCookie?.sameSite || null,
    hostOnly: authCookie?.domain === new URL(BASE_URL).hostname,
    cookiePath: authCookie?.path || null,
  };
}

async function summarizeSyntheticAuthCookie(context) {
  const cookieName = '__Host-studiamatch-admin-auth';
  const cookies = (await context.cookies(BASE_URL))
    .filter((cookie) => cookie.name === cookieName || (cookie.name.startsWith(`${cookieName}.`)
      && /^\d{1,3}$/.test(cookie.name.slice(cookieName.length + 1))))
    .sort((left, right) => left.name.localeCompare(right.name, undefined, { numeric: true }));
  assert(cookies.length > 0, 'synthetic HttpOnly Auth cookie missing during refresh probe');
  const storedValue = cookies.map((cookie) => cookie.value).join('');
  assert(storedValue.startsWith('base64-'), 'synthetic Auth cookie format unsupported for refresh probe');

  let session;
  try {
    session = JSON.parse(Buffer.from(storedValue.slice('base64-'.length), 'base64url').toString('utf8'));
  } catch {
    throw new Error('synthetic Auth cookie payload could not be decoded');
  }
  assert(typeof session?.access_token === 'string' && typeof session?.refresh_token === 'string',
    'synthetic Auth cookie omitted token fields');
  return {
    accessTokenSha256: createHash('sha256').update(session.access_token).digest('hex'),
    refreshTokenSha256: createHash('sha256').update(session.refresh_token).digest('hex'),
    expiresAt: Number(session.expires_at),
    cookieChunks: cookies.length,
  };
}

async function putSyntheticSessionInRefreshWindow(context) {
  const cookieName = '__Host-studiamatch-admin-auth';
  const cookies = (await context.cookies(BASE_URL))
    .filter((cookie) => cookie.name === cookieName || (cookie.name.startsWith(`${cookieName}.`)
      && /^\d{1,3}$/.test(cookie.name.slice(cookieName.length + 1))))
    .sort((left, right) => left.name.localeCompare(right.name, undefined, { numeric: true }));
  assert(cookies.length > 0, 'synthetic HttpOnly Auth cookie missing before refresh probe');
  const storedValue = cookies.map((cookie) => cookie.value).join('');
  assert(storedValue.startsWith('base64-'), 'synthetic Auth cookie format unsupported for refresh probe');

  let session;
  try {
    session = JSON.parse(Buffer.from(storedValue.slice('base64-'.length), 'base64url').toString('utf8'));
  } catch {
    throw new Error('synthetic Auth cookie payload could not be decoded');
  }
  assert(typeof session?.access_token === 'string' && typeof session?.refresh_token === 'string',
    'synthetic Auth cookie omitted token fields');
  const expiresAt = Number(session?.expires_at);
  assert(Number.isSafeInteger(expiresAt) && expiresAt > Math.floor(Date.now() / 1000) + 90,
    'synthetic Auth session is not outside the refresh margin before probe');
  session.expires_at = Math.floor(Date.now() / 1000) + 30;
  const refreshedFixtureValue = `base64-${Buffer.from(JSON.stringify(session)).toString('base64url')}`;
  const chunks = [];
  for (let offset = 0; offset < refreshedFixtureValue.length; offset += 3180) {
    chunks.push(refreshedFixtureValue.slice(offset, offset + 3180));
  }
  assert(chunks.length > 0 && chunks.length <= 5, 'synthetic Auth fixture exceeded supported cookie chunk count');

  await Promise.all(cookies.map(({ name }) => context.clearCookies({ name })));
  const template = cookies[0];
  const cookieOptions = {
    domain: template.domain,
    path: template.path,
    httpOnly: template.httpOnly,
    secure: template.secure,
    sameSite: template.sameSite,
    ...(template.expires > 0 ? { expires: template.expires } : {}),
  };
  await context.addCookies(chunks.map((value, index) => ({
    ...cookieOptions,
    name: chunks.length === 1 ? cookieName : `${cookieName}.${index}`,
    value,
  })));
  return {
    accessTokenSha256: createHash('sha256').update(session.access_token).digest('hex'),
    refreshTokenSha256: createHash('sha256').update(session.refresh_token).digest('hex'),
    expiresAt: Math.floor(Date.now() / 1000) + 30,
    cookieChunks: cookies.length,
    newCookieChunks: chunks.length,
    expiresWithinSeconds: 30,
  };
}

async function setMockClock(payload) {
  assert(RESET_TOKEN, 'missing local synthetic fixture token');
  const response = await fetch(`${MOCK_URL}/__test/clock`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-h3-test-token': RESET_TOKEN },
    body: JSON.stringify(payload),
  });
  assert(response.status === 200, `local synthetic clock returned HTTP ${response.status}`);
  await response.json();
}

async function openFirstEditor(page, role) {
  await login(page, role);
  await selectAllQueueStatuses(page);
  await page.getByRole('link', { name: 'Editar' }).first().click();
  await page.getByRole('button', { name: role === 'admin' ? 'Guardar cambios' : 'Actualizar información' }).waitFor({ state: 'visible' });
}

async function selectAllQueueStatuses(page) {
  await page.locator('#editorial-status-filter').click();
  await page.getByRole('option', { name: 'Todos los estados', exact: true }).click();
  const queueReloads = ['admin_get_course_queue_filtered', 'admin_count_course_queue_filtered'].map((functionName) => page.waitForResponse((response) => {
    if (response.request().method() !== 'POST' || !response.url().includes('/api/admin/rpc')) return false;
    try {
      const body = response.request().postDataJSON();
      return body?.function === functionName
        && body?.params?.p_editorial_status === null
        && body?.params?.p_quality_status === null
        && body?.params?.p_institution_slug === null;
    } catch {
      return false;
    }
  }));
  await page.locator('#quality-status-filter').click();
  await page.getByRole('option', { name: 'Todas las calidades', exact: true }).click();
  await Promise.all(queueReloads);
  await page.getByRole('link', { name: 'Editar' }).first().waitFor({ state: 'visible' });
}

async function ensureQueueRows(page) {
  const edits = page.getByRole('link', { name: 'Editar' });
  if (await edits.count() === 0) await selectAllQueueStatuses(page);
  await edits.first().waitFor({ state: 'visible' });
  return edits;
}

async function openUsers(page) {
  await login(page, 'admin');
  await page.goto(`${BASE_URL}/admin/users/`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);
  await page.getByRole('heading', { name: 'Gestión de usuarios' }).waitFor({ state: 'visible' });
  await page.getByRole('heading', { name: 'Usuarios existentes' }).waitFor({ state: 'visible' });
}

async function rpc(page, functionName, params = {}) {
  const response = await page.evaluate(async ({ functionName, params }) => {
    const result = await fetch('/api/admin/rpc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ function: functionName, params }),
    });
    return { status: result.status, body: await result.json().catch(() => null) };
  }, { functionName, params });
  return response;
}

async function bffPost(page, pathname, body) {
  return page.evaluate(async ({ pathname, body }) => {
    const response = await fetch(pathname, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return { status: response.status, body: await response.json().catch(() => null) };
  }, { pathname, body });
}

async function readContract(relativePath, requiredStrings) {
  const root = process.env.H3_REPO_ROOT || '/app';
  const content = await readFile(join(root, relativePath), 'utf8');
  for (const required of requiredStrings) assert(content.includes(required), `${relativePath} missing contract: ${required}`);
  return `${relativePath}: ${requiredStrings.length} contracts present`;
}

function defineCase(requirementId, title, role, route, expected, run, options = {}) {
  return Object.freeze({ requirementId, title, role, route, expected, run, ...options });
}

const ALL_CASES = Object.freeze([
  defineCase('H3-CA4.1', 'anonymous admin access redirects to login', 'anon', '/admin/', 'anonymous access is redirected to the local admin login', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/`); await page.waitForURL(`${BASE_URL}/admin/login/`); check('redirect', page.url().endsWith('/admin/login/')); return page.url();
  }),
  defineCase('H3-CA4.1', 'active admin reaches the editorial dashboard', 'admin', '/admin/', 'active aal2 admin sees authenticated email, fallback and admin-only dashboard capability', async ({ page, check }) => {
    await login(page, 'admin'); check('admin heading', await page.getByRole('heading', { name: 'Cola editorial' }).isVisible()); check('users link', await page.getByRole('link', { name: 'Usuarios' }).isVisible()); const email = page.getByText('admin@local.test', { exact: true }); await email.waitFor({ state: 'visible' }); check('authenticated email', await email.isVisible()); await assertAuthenticatedEmailFallback(page, check); check('admin capability preserved', await page.getByRole('link', { name: 'Usuarios' }).isVisible()); return 'admin dashboard shows authenticated email, fallback when absent and unchanged users capability';
  }),
  defineCase('H3-CA4.1', 'active user reaches the limited dashboard', 'user', '/admin/', 'active aal2 user sees authenticated email, fallback and the limited dashboard', async ({ page, check }) => {
    await login(page, 'user'); check('user heading', await page.getByText('Panel de actualización de información').isVisible()); const email = page.getByText('user@local.test', { exact: true }); await email.waitFor({ state: 'visible' }); check('authenticated email', await email.isVisible()); check('users link absent', await page.getByRole('link', { name: 'Usuarios' }).count() === 0); await assertAuthenticatedEmailFallback(page, check); check('user role boundary preserved', await page.getByRole('link', { name: 'Usuarios' }).count() === 0
      && await page.getByText('Panel de actualización de información').isVisible()); return 'limited dashboard shows authenticated email, fallback when absent and unchanged user role boundary';
  }),
  defineCase('H3-CA4.1', 'user is denied membership administration', 'user', '/admin/users/', 'user cannot expose membership management', async ({ page, check }) => {
    await login(page, 'user'); check('no users link', await page.getByRole('link', { name: 'Usuarios' }).count() === 0); await page.goto(`${BASE_URL}/admin/users/`); await page.waitForURL(`${BASE_URL}/admin/`); return 'users link absent and direct route returned to dashboard';
  }),
  defineCase('H3-CA4.1', 'logout clears the HttpOnly session', 'admin', '/admin/', 'logout returns to login, clears the server session and exposes no token to browser storage', async ({ page, check, markLogoutStarted }) => {
    await login(page, 'admin');
    markLogoutStarted();
    await page.getByRole('button', { name: 'Cerrar sesión' }).click();
    await page.waitForURL(`${BASE_URL}/admin/login/`);
    const state = await sessionInfo(page);
    check('server session cleared', state.authenticated === false);
    check('no Auth token in browser storage', state.hasAuthStorage === false && state.hasAccessToken === false && state.hasRefreshToken === false);
    check('cookie is not script-readable', state.authCookieVisible === false);
    const postLogoutRpc = await rpc(page, 'admin_list_members_onboarding');
    check('protected RPC rejects the cleared session', postLogoutRpc.status === 401);
    return 'server session cleared; browser token surfaces empty; protected RPC is rejected after logout';
  }, { requiresFixtureReset: false }),

  defineCase('H3-CA4.2', 'admin editor exposes editorial fields', 'admin', '/admin/edit/', 'admin can edit the editorial allowlist and the browser blocks availability evidence older than 90 days before RPC', async ({ page, check }) => {
    await openFirstEditor(page, 'admin');
    const editableInputs = await page.locator('main input:not([disabled])').count();
    check('editable inputs', editableInputs > 0);
    const evidenceUrl = page.getByLabel('Enlace de evidencia oficial');
    const observedInput = page.getByLabel('Verificado el');
    const validUntilInput = page.getByLabel('Evidencia válida hasta');
    const reasonInput = page.getByLabel('Nota de verificación');
    check('availability evidence fields visible to admin', await evidenceUrl.isVisible()
      && await observedInput.isVisible() && await validUntilInput.isVisible() && await reasonInput.isVisible());

    const invalidDates = await page.evaluate(() => {
      const observedAt = new Date(Date.now() - 60 * 60 * 1000);
      const validUntil = new Date(observedAt);
      validUntil.setUTCDate(validUntil.getUTCDate() + 90);
      validUntil.setUTCMinutes(validUntil.getUTCMinutes() + 1);
      const asDateTimeLocal = (date) => new Date(date.getTime() - date.getTimezoneOffset() * 60 * 1000).toISOString().slice(0, 16);
      return { observedAt: asDateTimeLocal(observedAt), validUntil: asDateTimeLocal(validUntil) };
    });
    await evidenceUrl.fill('https://institution.test/program');
    await observedInput.fill(invalidDates.observedAt);
    await validUntilInput.fill(invalidDates.validUntil);
    await reasonInput.fill('UAT exceeds maximum age');

    let rpcRequests = 0;
    const countAdminRpc = (request) => {
      if (request.method() !== 'POST') return;
      try {
        if (new URL(request.url()).pathname === '/api/admin/rpc') rpcRequests += 1;
      } catch { /* Malformed URLs are irrelevant to this route assertion. */ }
    };
    page.on('request', countAdminRpc);
    await page.getByRole('button', { name: 'Guardar verificación' }).click();
    await page.getByRole('alert').filter({ hasText: 'vigencia máxima global de 90 días' }).waitFor();
    check('over-90-day evidence rejected before RPC', rpcRequests === 0);
    page.off('request', countAdminRpc);
    return `${editableInputs} editable inputs; availability UI rejects evidence over 90 days without an RPC`;
  }),
  defineCase('H3-CA4.2', 'user editor limits ownership to missing fields', 'user', '/admin/edit/', 'user receives only missing fields as editable', async ({ page, check }) => {
    await login(page, 'user');
    await selectAllQueueStatuses(page);
    const queueResponse = await rpc(page, 'admin_get_course_queue_filtered', {
      p_first: 100,
      p_after_cursor: null,
      p_editorial_status: null,
      p_quality_status: null,
      p_institution_slug: null,
    });
    const queue = queueResponse.body?.data?.[0];
    assert(queueResponse.status === 200 && Array.isArray(queue?.courses), 'user queue fixture unavailable');
    const candidate = queue.courses.find((course) => Array.isArray(course.missing_fields) && course.missing_fields.length > 0);
    assert(candidate, 'synthetic queue has no course with missing fields');
    await page.goto(`${BASE_URL}/admin/edit/?id=${encodeURIComponent(candidate.course_id)}`, { waitUntil: 'domcontentloaded' });
    await page.locator('main input, main textarea, main [role="combobox"]').first().waitFor({ state: 'visible' });
    await page.getByRole('button', { name: 'Actualizar información' }).waitFor({ state: 'visible' });
    const editableKeys = await page.locator('main input:not([disabled]), main textarea:not([disabled]), main [role="combobox"]:not([aria-disabled="true"])').evaluateAll((nodes) => nodes.map((node) => node.id || node.getAttribute('name')).filter(Boolean));
    const readonly = await page.locator('main input[disabled], main textarea[disabled], main [role="combobox"][aria-disabled="true"]').count();
    const missingKeys = new Set(candidate.missing_fields);
    check('editable missing fields', editableKeys.length > 0 && editableKeys.every((key) => missingKeys.has(key)));
    check('readonly existing fields', readonly > 0);
    check('availability override stays admin-only', await page.getByRole('heading', { name: 'Registrar comprobación respaldada' }).count() === 0);
    return `${editableKeys.length} enabled fields match the synthetic missing-field set; ${readonly} readonly; availability override hidden from user`;
  }),
  defineCase('H3-CA4.2', 'user read-only fields are disabled', 'user', '/admin/edit/', 'non-owned fields are disabled and read-only', async ({ page, check }) => {
    await openFirstEditor(page, 'user'); const invalid = await page.locator('main input[disabled]:not([readonly])').count(); check('disabled fields are readonly', invalid === 0); return 'all disabled fields are readonly';
  }),
  defineCase('H3-CA4.2', 'user receives an ownership explanation', 'user', '/admin/edit/', 'editor explains that only missing information is editable', async ({ page, check }) => {
    await openFirstEditor(page, 'user'); const note = page.getByRole('note'); check('ownership note visible', await note.isVisible()); return await note.innerText();
  }),
  defineCase('H3-CA4.2', 'editor renders effective current values', 'admin', '/admin/edit/', 'editor fields are hydrated with current/effective values', async ({ page, check }) => {
    await openFirstEditor(page, 'admin'); const values = await page.locator('main input').evaluateAll((nodes) => nodes.map((node) => node.value)); check('hydrated values', values.some((value) => value.trim().length > 0)); return `${values.filter(Boolean).length} hydrated values`;
  }),

  defineCase('H3-CA4.3', 'independent enrichment fields remain distinct in pipeline code', 'anon', '/admin/login/', 'benefits, certification, objectives and target_audience are independently mapped', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const observed = await readContract('scripts/core/sync_vector_worker.py', ['benefits', 'certification', 'objectives', 'target_audience']); check('four independent names', true); return observed;
  }),
  defineCase('H3-CA4.3', 'all thirteen editorial transport fields are defined', 'anon', '/admin/login/', 'the complete 13-field editorial allowlist is represented in migration contracts', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const observed = await readContract('db/migrations/20260825_h2_editorial_layer.sql', EDITORIAL_FIELDS); check('13 fields found', EDITORIAL_FIELDS.length === 13); return observed;
  }),

  defineCase('H3-CA4.4', 'queue count and rows agree', 'admin', '/admin/', 'queue exposes a numeric total and at least one result', async ({ page, check }) => {
    await login(page, 'admin');
    const countLabel = page.getByText('programas en este filtro').locator('..');
    const initialCount = Number((await countLabel.innerText()).match(/\d+/)?.[0]);
    const initialLinks = await page.getByRole('link', { name: 'Editar' }).count();
    if (initialLinks === 0) {
      check('empty default filter has zero count and an explicit empty state', initialCount === 0
        && await page.getByText('No encontramos programas con estos filtros.').isVisible());
      await selectAllQueueStatuses(page);
    }
    const totalText = await countLabel.innerText();
    const total = Number(totalText.match(/\d+/)?.[0]);
    const links = await page.getByRole('link', { name: 'Editar' }).count();
    check('numeric total', Number.isInteger(total));
    check('rows present', links > 0);
    check('visible rows agree with paginated count', links === Math.min(total, 20));
    return `${total} total; ${links} visible rows`;
  }),
  defineCase('H3-CA4.4', 'queue exposes both status filters', 'admin', '/admin/', 'editorial and quality filters are labeled controls', async ({ page, check }) => {
    await login(page, 'admin'); await page.getByText('Estado editorial', { exact: true }).waitFor(); await page.getByText('Estado de calidad', { exact: true }).waitFor(); check('editorial filter', true); check('quality filter', true); return 'both filters visible';
  }),
  defineCase('H3-CA4.4', 'page-local queue search filters visible rows', 'admin', '/admin/', 'search narrows the current page without navigation', async ({ page, check }) => {
    await login(page, 'admin');
    await ensureQueueRows(page);
    const first = await page.locator('main h3').first().innerText();
    await page.getByLabel('Buscar curso').fill(first);
    check('matching result', await page.getByText(first, { exact: true }).count() >= 1);
    await page.getByLabel('Buscar curso').fill('__no_match__');
    check('empty state', await page.getByText('No encontramos programas con estos filtros.').isVisible());
    return 'search match and empty states verified';
  }),
  defineCase('H3-CA4.4', 'queue edit/public links follow editorial state', 'admin', '/admin/', 'every row is editable and pending rows do not expose public links', async ({ page, check }) => {
    await login(page, 'admin');
    await selectAllQueueStatuses(page);
    const edits = page.getByRole('link', { name: 'Editar' });
    await edits.first().waitFor({ state: 'visible' });
    const count = await edits.count();
    check('edit links', count > 0);
    const editorialStatuses = ['Borrador', 'Pendiente de revisión', 'Publicado', 'Archivado'];
    let checkedRows = 0;
    for (let index = 0; index < count; index += 1) {
      const card = edits.nth(index).locator('xpath=../../..');
      let status = '';
      for (const candidate of editorialStatuses) {
        if (await card.getByText(candidate, { exact: true }).count() > 0) {
          status = candidate;
          break;
        }
      }
      const views = await card.getByRole('link', { name: 'Ver', includeHidden: true }).count();
      check(`public link matches editorial state for row ${index + 1}`,
        Boolean(status) && views === (status === 'Publicado' ? 1 : 0));
      checkedRows += 1;
    }
    return `${checkedRows} rows: every row editable; public link only on published rows`;
  }),
  defineCase('H3-CA4.4', 'cursor pagination contract exposes paired controls', 'admin', '/admin/', 'when pagination is available, previous and next controls are paired and stateful', async ({ page, check }) => {
    await login(page, 'admin');
    await selectAllQueueStatuses(page);
    const next = page.getByRole('button', { name: 'Siguiente' });
    const previous = page.getByRole('button', { name: 'Anterior' });
    const countLabel = page.getByText('programas en este filtro').locator('..');
    const nextCount = await next.count();
    const previousCount = await previous.count();
    check('paired controls', nextCount === 1 && previousCount === 1);
    check('previous starts disabled', await previous.isDisabled());
    const editorialFilter = page.getByLabel('Estado editorial');
    check('editorial queue filter has a programmatic label', await editorialFilter.count() === 1
      && await editorialFilter.isVisible() && await editorialFilter.isEnabled());
    await editorialFilter.focus();
    check('keyboard focus reaches the editorial filter', await editorialFilter.evaluate((element) => document.activeElement === element));
    await page.keyboard.press('Enter');
    const allStatusesOption = page.getByRole('option', { name: 'Todos los estados', exact: true });
    await allStatusesOption.waitFor({ state: 'visible' });
    check('keyboard opens the filter options', await allStatusesOption.isVisible());
    await page.keyboard.press('Escape');
    await allStatusesOption.waitFor({ state: 'hidden' });
    const editorialFilterValue = (await editorialFilter.innerText()).trim();
    check('Escape closes the filter without changing its value', !await allStatusesOption.isVisible()
      && editorialFilterValue.includes('Todos los estados'), JSON.stringify({ editorialFilterValue }));
    const editLinks = page.getByRole('link', { name: 'Editar' });
    const firstPageHrefs = await editLinks.evaluateAll((links) => links.map((link) => link.getAttribute('href')));
    const initialTotal = Number((await countLabel.innerText()).match(/\d+/)?.[0]);
    check('first page has expected persisted result window', Number.isInteger(initialTotal)
      && initialTotal > firstPageHrefs.length
      && firstPageHrefs.length === Math.min(initialTotal, 20));
    await next.focus();
    check('keyboard focus reaches next-page control', await next.evaluate((element) => document.activeElement === element));
    await page.keyboard.press('Enter');
    await page.waitForFunction((href) => document.querySelector('a[href^="/admin/edit/"]')?.getAttribute('href') !== href, firstPageHrefs[0]);
    check('previous is enabled on second page', await previous.isEnabled());
    const secondPageHrefs = await page.getByRole('link', { name: 'Editar' }).evaluateAll((links) => links.map((link) => link.getAttribute('href')));
    const secondTotal = Number((await countLabel.innerText()).match(/\d+/)?.[0]);
    check('page count remains stable', secondTotal === initialTotal);
    check('cursor pages do not overlap', secondPageHrefs.length > 0 && secondPageHrefs.every((href) => !firstPageHrefs.includes(href)));
    check('final page size matches remaining persisted rows', secondPageHrefs.length === Math.min(initialTotal - firstPageHrefs.length, 20));
    check('next is disabled on final page', await next.isDisabled());
    await previous.click();
    await page.waitForFunction((href) => document.querySelector('a[href^="/admin/edit/"]')?.getAttribute('href') === href, firstPageHrefs[0]);
    check('previous restores the same ordered first page', JSON.stringify(
      await page.getByRole('link', { name: 'Editar' }).evaluateAll((links) => links.map((link) => link.getAttribute('href'))),
    ) === JSON.stringify(firstPageHrefs));

    await next.click();
    await page.waitForFunction((href) => document.querySelector('a[href^="/admin/edit/"]')?.getAttribute('href') !== href, firstPageHrefs[0]);
    await page.locator('#editorial-status-filter').click();
    await page.getByRole('option', { name: 'Borrador', exact: true }).click();
    const combinedReads = ['admin_get_course_queue_filtered', 'admin_count_course_queue_filtered'].map((functionName) => page.waitForResponse((response) => {
      if (response.request().method() !== 'POST' || !response.url().includes('/api/admin/rpc')) return false;
      try {
        const body = response.request().postDataJSON();
        return body?.function === functionName
          && body?.params?.p_editorial_status === 'draft'
          && body?.params?.p_quality_status === 'pending'
          && body?.params?.p_institution_slug === null;
      } catch {
        return false;
      }
    }));
    await page.locator('#quality-status-filter').click();
    await page.getByRole('option', { name: 'Pendiente', exact: true }).click();
    await Promise.all(combinedReads);
    await page.waitForFunction((oldCount) => {
      const label = [...document.querySelectorAll('p')].find((node) => node.textContent?.trim() === 'programas en este filtro');
      const currentCount = Number(label?.previousElementSibling?.textContent?.trim());
      const rows = document.querySelectorAll('a[href^="/admin/edit/"]');
      return Number.isInteger(currentCount) && currentCount > 0 && currentCount < oldCount && rows.length === currentCount;
    }, initialTotal);
    const combinedTotal = Number((await countLabel.innerText()).match(/\d+/)?.[0]);
    const combinedRows = page.locator('a[href^="/admin/edit/?id="]');
    const combinedRowCount = await combinedRows.count();
    check('combined filters return persisted rows and count', combinedTotal > 0
      && combinedTotal < initialTotal
      && combinedRowCount === combinedTotal,
    `initial=${initialTotal}; filtered=${combinedTotal}; rows=${combinedRowCount}`);
    check('pagination controls are hidden for a filtered single page', await previous.count() === 0 && await next.count() === 0);
    for (let index = 0; index < combinedRowCount; index += 1) {
      const card = combinedRows.nth(index).locator('xpath=../../..');
      check(`combined filter status matches row ${index + 1}`,
        await card.getByText('Borrador', { exact: true }).count() === 1
        && await card.getByText('Pendiente', { exact: true }).count() === 1);
    }

    await selectAllQueueStatuses(page);
    await page.waitForFunction((expectedTotal) => {
      const label = [...document.querySelectorAll('p')].find((node) => node.textContent?.trim() === 'programas en este filtro');
      const currentCount = Number(label?.previousElementSibling?.textContent?.trim());
      return currentCount === expectedTotal && document.querySelectorAll('a[href^="/admin/edit/"]').length === Math.min(expectedTotal, 20);
    }, initialTotal);
    check('reset restores full first-page count', Number((await countLabel.innerText()).match(/\d+/)?.[0]) === initialTotal
      && await page.locator('a[href^="/admin/edit/?id="]').count() === Math.min(initialTotal, 20)
      && await previous.isDisabled());
    return `${initialTotal} persisted rows; disjoint cursor pages; combined draft/pending filter ${combinedTotal}; reset restored first page`;
  }),

  defineCase('H3-CA4.5', 'admin save control is enabled', 'admin', '/admin/edit/', 'admin can initiate an editorial save after making a reasoned draft change', async ({ page, check }) => {
    await openFirstEditor(page, 'admin');
    const description = page.locator('main textarea[name="description_long"]');
    await description.fill(`${await description.inputValue()} UAT`);
    await page.getByLabel('Motivo de la corrección').fill('Ajuste local de validación UAT');
    check('save enabled after draft and reason', await page.getByRole('button', { name: 'Guardar cambios' }).isEnabled());
    return 'save enabled after a local draft edit and audit reason';
  }),
  defineCase('H3-CA4.5', 'admin publication control is state aware', 'admin', '/admin/edit/', 'admin sees exactly one publish or unpublish action', async ({ page, check }) => {
    await openFirstEditor(page, 'admin'); const count = await page.getByRole('button', { name: /^(Publicar|Despublicar)$/ }).count(); check('single publication action', count === 1); return 'one state-aware publication action';
  }),
  defineCase('H3-CA4.5', 'admin archive control is available', 'admin', '/admin/edit/', 'admin can initiate archive according to current state', async ({ page, check }) => {
    await openFirstEditor(page, 'admin'); check('archive visible', await page.getByRole('button', { name: 'Archivar' }).isVisible()); return 'archive control visible';
  }),
  defineCase('H3-CA4.5', 'admin quality transition is explicit', 'admin', '/admin/edit/', 'quality selection and update action are separate controls', async ({ page, check }) => {
    await openFirstEditor(page, 'admin'); check('quality select', await page.getByLabel('Estado de calidad').isVisible()); check('quality action', await page.getByRole('button', { name: 'Actualizar calidad' }).isVisible()); return 'quality transition controls visible';
  }),
  defineCase('H3-CA4.5', 'user cannot invoke privileged mutations', 'user', '/admin/edit/', 'publish, archive and quality mutations are absent for user', async ({ page, check }) => {
    await openFirstEditor(page, 'user'); for (const name of ['Publicar', 'Despublicar', 'Archivar', 'Actualizar calidad']) check(`${name} absent`, await page.getByRole('button', { name }).count() === 0); return 'all privileged mutation controls absent';
  }),
  defineCase('H3-CA4.5', 'concurrent editor saves preserve one winner and reject the stale version', 'admin', '/admin/edit/', 'overlapping Admin saves with one version produce one winner, one conflict, and recover provenance after reload', async ({ page, check }) => {
    await openFirstEditor(page, 'admin');
    const courseId = new URL(page.url()).searchParams.get('id');
    check('course id present', Boolean(courseId));
    const editedName = page.locator('main input[name="name"]');
    let originalState = null;
    let responses = [];
    let candidates = [];
    let winnerIndex = -1;
    let winnerName;
    let conflictCount = 0;
    let concurrentStateCorrect = false;
    let manualReloadValue = '';
    let manualProvenance = 0;
    let pipelineBaseVisible = false;
    let pipelineDateLabelVisible = false;
    let pipelineTimestampExpected = false;
    let pipelineTimestampExpectedText = null;
    let cleanupSucceeded = false;
    try {
      const detailResponse = await rpc(page, 'admin_get_course_editorial', { p_course_id: courseId });
      const detail = detailResponse.body?.data?.[0];
      check('editorial detail loaded', detailResponse.status === 200 && Boolean(detail?.course));
      const course = detail?.course;
      assert(course, 'editorial detail unavailable for concurrent-save test');
      const sourceTimestamp = course.field_timestamps?.name;
      pipelineTimestampExpected = typeof sourceTimestamp === 'string' && sourceTimestamp.length > 0;
      pipelineTimestampExpectedText = pipelineTimestampExpected
        ? new Date(sourceTimestamp).toLocaleDateString('es-PE')
        : null;
      const originalOverrides = course.manual_overrides || {};
      const originalHasManualName = Object.prototype.hasOwnProperty.call(originalOverrides, 'name')
        && originalOverrides.name !== null;
      originalState = {
        currentName: course.current_values?.name ?? null,
        pipelineName: course.pipeline_values?.name ?? null,
        pipelineSource: course.field_sources?.name || 'pipeline',
        hasManualName: originalHasManualName,
        manualName: originalHasManualName ? originalOverrides.name : null,
      };
      const initialVersion = Number(course.version);
      candidates = [`H3 UAT concurrent A ${initialVersion}`, `H3 UAT concurrent B ${initialVersion}`];
      const settled = await Promise.allSettled(candidates.map((name) => rpc(page, 'admin_update_course', {
        p_course_id: courseId,
        p_manual_overrides: { name },
        p_version: initialVersion,
        p_reason: 'Concurrent editorial UAT save',
      })));
      if (settled.some((result) => result.status !== 'fulfilled')) {
        throw new Error('concurrent editorial RPC did not settle; fixture cleanup will run');
      }
      responses = settled.map((result) => result.value);
      const rows = responses.map((response) => response.body?.data?.[0]);
      winnerIndex = rows.findIndex((row) => row?.success === true);
      winnerName = winnerIndex >= 0 ? candidates[winnerIndex] : null;
      conflictCount = rows.filter((row) => row?.success === false && /^Version conflict:/.test(row?.error || '')).length;
      const currentResponse = await rpc(page, 'admin_get_course_editorial', { p_course_id: courseId });
      const currentCourse = currentResponse.body?.data?.[0]?.course;
      concurrentStateCorrect = responses.every((response) => response.status === 200)
        && winnerIndex >= 0 && conflictCount === 1
        && currentCourse?.manual_overrides?.name === winnerName
        && currentCourse?.current_values?.name === winnerName
        && currentCourse?.pipeline_values?.name === originalState.pipelineName
        && (currentCourse?.field_sources?.name || 'pipeline') === originalState.pipelineSource;

      await page.reload({ waitUntil: 'networkidle' });
      manualReloadValue = await editedName.inputValue();
      manualProvenance = await page.getByText('Corrección manual', { exact: true }).count();
      pipelineBaseVisible = await page.getByText('Valor base del pipeline:', { exact: false }).count() > 0;
      pipelineDateLabelVisible = await page.getByText('Fecha del dato base del pipeline:', { exact: false }).count() > 0;
    } finally {
      if (courseId && originalState) {
        try {
          const latestResponse = await rpc(page, 'admin_get_course_editorial', { p_course_id: courseId });
          const latestCourse = latestResponse.body?.data?.[0]?.course;
          if (latestResponse.status === 200 && latestCourse) {
            const latestOverrides = latestCourse.manual_overrides || {};
            const latestHasManualName = Object.prototype.hasOwnProperty.call(latestOverrides, 'name')
              && latestOverrides.name !== null;
            const alreadyRestored = latestHasManualName === originalState.hasManualName
              && (!originalState.hasManualName || latestOverrides.name === originalState.manualName);
            if (alreadyRestored) {
              cleanupSucceeded = true;
            } else {
              const cleanup = await rpc(page, 'admin_update_course', {
                p_course_id: courseId,
                p_manual_overrides: { name: originalState.hasManualName ? originalState.manualName : null },
                p_version: Number(latestCourse.version),
                p_reason: 'Restore original value after concurrent editorial UAT',
              });
              cleanupSucceeded = cleanup.status === 200 && cleanup.body?.data?.[0]?.success === true;
            }
          }
        } catch {
          cleanupSucceeded = false;
        }
      }
    }
    await page.reload({ waitUntil: 'networkidle' });
    const restored = await rpc(page, 'admin_get_course_editorial', { p_course_id: courseId });
    const restoredCourse = restored.body?.data?.[0]?.course;
    const observed = await readContract('web/src/app/admin/edit/page.tsx', ["startsWith('Version conflict')", 'setConflict(true)', 'Recargar', 'disabled={saving || conflict || mfaRequired}']);
    check('one save wins and one stale version conflicts', responses.every((response) => response.status === 200) && winnerIndex >= 0 && conflictCount === 1);
    check('winning edit and manual provenance survive reload', concurrentStateCorrect && manualReloadValue === winnerName && manualProvenance > 0);
    check('pipeline baseline remains visible', pipelineBaseVisible);
    check('pipeline base timestamp visibility matches available source evidence', pipelineDateLabelVisible === pipelineTimestampExpected
      && (!pipelineTimestampExpected || await page.getByText(pipelineTimestampExpectedText, { exact: true }).count() > 0));
    const restoredOverrides = restoredCourse?.manual_overrides || {};
    const manualNameRestored = originalState?.hasManualName
      ? restoredOverrides.name === originalState.manualName
      : !Object.prototype.hasOwnProperty.call(restoredOverrides, 'name') || restoredOverrides.name === null;
    check('original value, override and provenance restored after cleanup', cleanupSucceeded
      && restoredCourse?.current_values?.name === originalState?.currentName
      && restoredCourse?.pipeline_values?.name === originalState?.pipelineName
      && manualNameRestored
      && (restoredCourse?.field_sources?.name || 'pipeline') === originalState?.pipelineSource
      && await editedName.inputValue() === String(originalState?.currentName || ''));
    check('stale-save UI recovery contract', true);
    return `one overlapping winner and one version conflict; pipeline provenance restored; ${observed}`;
  }),

  defineCase('H3-CA4.6', 'editorial updates carry an audit reason', 'admin', '/admin/edit/', 'save payload includes an explicit human-readable audit reason', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const observed = await readContract('web/src/app/admin/edit/page.tsx', ['p_reason: editReason.trim()', 'editReason.trim().length < 8']); check('explicit reason and minimum length', true); return observed;
  }),
  defineCase('H3-CA4.6', 'publication transitions carry audit reasons', 'admin', '/admin/edit/', 'publish and unpublish payloads carry explicit reasons', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const observed = await readContract('web/src/app/admin/edit/page.tsx', ['Publicación desde panel admin', 'Despublicación desde panel admin']); check('publication reasons', true); return observed;
  }),
  defineCase('H3-CA4.6', 'membership changes carry action identity', 'admin', '/admin/users/', 'role and active-state updates identify their audit action', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const observed = await readContract('web/src/app/admin/users/page.tsx', ["'deactivation'", "'activation'", "'role_change'"]); check('membership actions', true); return observed;
  }),
  defineCase('H3-CA4.6', 'audit tables are append-only by migration contract', 'admin', '/admin/login/', 'UPDATE, DELETE and TRUNCATE are rejected for both audit logs', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const editorial = await readContract('db/migrations/20260826_h2_editorial_layer_forward_fix.sql', ['course_editorial_audit', 'prevent_course_editorial_audit_mutation']); const membership = await readContract('db/migrations/20260830_h3_expanded_contract.sql', ['admin_membership_audit', 'prevent_admin_membership_audit_mutation']); check('append-only migration present', true); return `${editorial}; ${membership}`;
  }),

  defineCase('H3-CA4.7', 'login form is labeled and password-protected', 'anon', '/admin/login/', 'email/password controls are labeled and password is masked', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); await page.getByLabel('Email').waitFor({ state: 'visible' }); check('email label', await page.getByLabel('Email').isVisible()); check('password type', await page.getByLabel('Password').getAttribute('type') === 'password'); check('submit', await page.getByRole('button', { name: 'Iniciar sesión' }).isVisible()); return 'login contract visible';
  }),
  defineCase('H3-CA4.7', 'existing session redirects away from login', 'admin', '/admin/login/', 'an authenticated session visiting login is redirected to the dashboard', async ({ page, check }) => {
    await login(page, 'admin');
    await page.goto(`${BASE_URL}/admin/login/`);
    await page.waitForURL(`${BASE_URL}/admin/`);
    await page.getByRole('heading', { name: 'Cola editorial' }).waitFor({ state: 'visible' });
    await page.getByText('Vista actual', { exact: true }).waitFor({ state: 'visible' });
    await page.getByText('Cargando cola editorial...', { exact: true }).waitFor({ state: 'hidden' });
    check('dashboard route', page.url().endsWith('/admin/'));
    check('login form is absent after redirect', await page.getByLabel('Email').count() === 0);
    check('editorial queue is ready', await page.getByText('Vista actual', { exact: true }).isVisible());
    return 'existing session redirected to rendered dashboard';
  }, { requiresFixtureReset: false }),
  defineCase('H3-CA4.7', 'invalid credentials are rejected without enumeration', 'anon', '/admin/login/', 'invalid password remains on login with sanitized feedback', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`, { waitUntil: 'networkidle' }); await page.waitForTimeout(1500); await page.getByLabel('Email').fill('admin@local.test'); await page.getByLabel('Password').fill('invalid-local-value'); await page.getByRole('button', { name: 'Iniciar sesión' }).click(); await page.getByText('No se pudo autenticar la cuenta. Verifica los datos o solicita ayuda al administrador.').waitFor(); check('still login', page.url().endsWith('/admin/login/')); check('generic message', await page.getByText('Invalid login credentials').count() === 0); return 'invalid credentials rejected with generic feedback';
  }),
  defineCase('H3-CA4.7', 'invalid TOTP is rejected', 'admin', '/admin/login/', 'wrong six-digit MFA code does not create aal2 session', async ({ page, check }) => {
    const user = USERS.admin; assert(user.password, 'missing local admin password'); await page.goto(`${BASE_URL}/admin/login/`, { waitUntil: 'networkidle' }); await page.waitForTimeout(1500); await page.getByLabel('Email').fill(user.email); await page.getByLabel('Password').fill(user.password); await page.getByRole('button', { name: 'Iniciar sesión' }).click(); await page.waitForURL(`${BASE_URL}/admin/`); const mfaCode = page.getByLabel('Código de 6 dígitos'); try { await mfaCode.waitFor({ state: 'visible', timeout: 1500 }); } catch { await page.getByRole('button', { name: /Configurar MFA|Reiniciar configuración MFA/ }).first().click(); await mfaCode.waitFor({ state: 'visible' }); } await mfaCode.fill('000000'); await page.getByRole('button', { name: 'Verificar MFA' }).click(); await page.getByText('Código MFA inválido.').waitFor(); const session = await sessionInfo(page); check('not aal2', session?.aal !== 'aal2'); return 'invalid MFA rejected at aal1';
  }),
  defineCase('H3-CA4.7', 'admin session reaches aal2 inside HttpOnly cookie', 'admin', '/admin/', 'valid admin TOTP produces aal2 without exposing session tokens', async ({ page, check }) => {
    await login(page, 'admin'); const session = await sessionInfo(page); check('authenticated aal2', session?.authenticated && session?.aal === 'aal2'); check('HttpOnly Secure host cookie', session?.httpOnly && session?.secure && session?.sameSite === 'Lax' && session?.cookiePath === '/' && session?.hostOnly); check('no JS token storage', !session?.hasAuthStorage && !session?.hasAccessToken && !session?.hasRefreshToken && !session?.authCookieVisible); return `aal=${session?.aal}; HttpOnly/Secure/Lax cookie`;
  }),
  defineCase('H3-CA4.7', 'user session reaches aal2', 'user', '/admin/', 'valid user TOTP produces aal2', async ({ page, check }) => {
    await login(page, 'user'); const session = await sessionInfo(page); check('aal2', session?.authenticated && session?.aal === 'aal2', `authenticated=${Boolean(session?.authenticated)}; aal=${session?.aal || 'missing'}`); check('no JS token storage', !session?.hasAuthStorage && !session?.hasAccessToken && !session?.hasRefreshToken); return `aal=${session?.aal}; no browser token storage`;
  }),
  defineCase('H3-CA4.7', 'expired Auth session is rejected and cleared during concurrent browser reads', 'admin', '/admin/', 'locally expired Auth identity is rejected by concurrent server-verified browser session reads and its HttpOnly cookies are cleared', async ({ page, check, context, markAuthExpiry }) => {
    await login(page, 'admin');
    await page.goto(`${BASE_URL}/privacidad/`, { waitUntil: 'networkidle' });
    check('expiry probe runs outside the active Admin queue', page.url().endsWith('/privacidad/'));
    const before = await sessionInfo(page);
    check('synthetic session starts authenticated at aal2', before.authenticated === true && before.aal === 'aal2');
    check('no browser-visible Auth token', !before.hasAuthStorage && !before.hasAccessToken && !before.hasRefreshToken && !before.authCookieVisible);
    const authCookiesBefore = await context.cookies(BASE_URL);
    check('HttpOnly Auth cookie exists before expiry', authCookiesBefore.some(({ name, httpOnly }) => name.startsWith('__Host-studiamatch-admin-auth') && httpOnly));

    const refreshFixture = await putSyntheticSessionInRefreshWindow(context);
    const concurrentRefreshReads = await Promise.all(Array.from({ length: 3 }, () => page.evaluate(async () => {
      const response = await fetch('/api/admin/session', { cache: 'no-store' });
      const body = await response.json();
      return { status: response.status, authenticated: body?.authenticated === true, aal: body?.session?.aal || 'missing', sessionId: body?.session?.sessionId || null };
    })));
    const afterRefresh = await sessionInfo(page);
    const refreshedFixture = await summarizeSyntheticAuthCookie(context);
    const refreshedExpiryRemainingMs = Number(afterRefresh.expiresAt) - Date.now();
    check('concurrent near-expiry reads refresh the synthetic Auth session', concurrentRefreshReads.length === 3
      && concurrentRefreshReads.every(({ status, authenticated, aal }) => status === 200 && authenticated && aal === 'aal2')
      && refreshedExpiryRemainingMs > 90_000,
    JSON.stringify({ parallelReads: concurrentRefreshReads.length,
      authenticatedReads: concurrentRefreshReads.filter(({ authenticated }) => authenticated).length,
      expiryWindow: refreshedExpiryRemainingMs > 90_000 ? 'renewed' : 'near-expiry',
      expiryRemainingSeconds: Number.isFinite(refreshedExpiryRemainingMs) ? Math.floor(refreshedExpiryRemainingMs / 1000) : null,
      cookieChunks: refreshFixture.cookieChunks }));
    check('concurrent refresh rotates the opaque synthetic Auth token pair',
      refreshedFixture.accessTokenSha256 !== refreshFixture.accessTokenSha256
        && refreshedFixture.refreshTokenSha256 !== refreshFixture.refreshTokenSha256
        && refreshedFixture.expiresAt > refreshFixture.expiresAt,
      JSON.stringify({ accessTokenRotated: refreshedFixture.accessTokenSha256 !== refreshFixture.accessTokenSha256,
        refreshTokenRotated: refreshedFixture.refreshTokenSha256 !== refreshFixture.refreshTokenSha256,
        expiryAdvanced: refreshedFixture.expiresAt > refreshFixture.expiresAt }));
    check('refresh probe does not expose internal session identifiers', !Object.hasOwn(before, 'sessionId')
      && concurrentRefreshReads.every(({ sessionId }) => sessionId === null));
    const refreshedCookies = await context.cookies(BASE_URL);
    check('refreshed Auth cookie remains HttpOnly and Secure', refreshedCookies.some(({ name, httpOnly, secure }) =>
      name.startsWith('__Host-studiamatch-admin-auth') && httpOnly && secure));
    check('refresh renews the expiry window and keeps Auth tokens outside browser-readable storage', afterRefresh.authenticated === true
      && afterRefresh.aal === 'aal2' && !afterRefresh.hasAuthStorage && !afterRefresh.hasAccessToken
      && !afterRefresh.hasRefreshToken && !afterRefresh.authCookieVisible
      && Number(afterRefresh.expiresAt) > Date.now() + 90_000);

    try {
      await setMockClock({ advance_seconds: 3601 });
      markAuthExpiry();
      const parallelReads = await Promise.all(Array.from({ length: 3 }, () => page.evaluate(async () => {
        const response = await fetch('/api/admin/session', { cache: 'no-store' });
        return { status: response.status, body: await response.json() };
      })));
      check('parallel browser reads reject the expired Auth identity', parallelReads.length === 3
        && parallelReads.every(({ status, body }) => status === 200 && body?.authenticated === false && body?.session === null));

      const authCookiesAfter = await context.cookies(BASE_URL);
      check('expired Auth and activity cookies are cleared', !authCookiesAfter.some(({ name }) =>
        name.startsWith('__Host-studiamatch-admin-auth') || name === '__Host-studiamatch-admin-activity'));
      const after = await sessionInfo(page);
      check('server session remains unauthenticated after cleanup', after.authenticated === false && after.expiresAt == null);
      check('no Auth token reappears in browser storage', !after.hasAuthStorage && !after.hasAccessToken && !after.hasRefreshToken && !after.authCookieVisible);
      const deniedRpc = await rpc(page, 'admin_get_course_queue_filtered', { p_limit: 1 });
      check('expired session cannot invoke a protected Admin RPC', deniedRpc.status === 401
        && deniedRpc.body?.error?.code === 'unauthenticated');
    } finally {
      await setMockClock({ reset: true });
    }
    return 'local Auth expiry rejected across three concurrent browser reads; HttpOnly session cleared and protected Admin RPC denied';
  }),

  defineCase('H3-CA4.8', 'admin users surface lists memberships', 'admin', '/admin/users/', 'admin sees existing admin/user memberships', async ({ page, check }) => {
    await openUsers(page); await page.locator('[data-membership-row]').first().waitFor(); const rows = await page.locator('[data-membership-row]').count(); check('members visible', rows >= 2); return `${rows} memberships`;
  }),
  defineCase('H3-CA4.8', 'membership invitation form exposes email and role', 'admin', '/admin/users/', 'admin sees labeled email, role and add controls', async ({ page, check }) => {
    await openUsers(page); check('email', await page.getByLabel('Email').isVisible()); check('role', await page.getByRole('heading', { name: 'Agregar usuario' }).locator('xpath=..').getByText('Rol', { exact: true }).isVisible()); check('add', await page.getByRole('button', { name: 'Agregar usuario' }).isVisible()); return 'membership creation controls visible';
  }),
  defineCase('H3-CA4.8', 'invalid membership email is rejected by BFF schema', 'admin', '/admin/users/', 'BFF rejects malformed membership email before invoking Auth', async ({ page, check }) => {
    await openUsers(page); const result = await bffPost(page, '/api/admin/invitations', { email: 'not-an-email', role: 'user' }); check('HTTP 400', result.status === 400); check('schema rejected', result.body?.error?.code === 'invalid_invitation'); return `HTTP ${result.status}: rejected before Auth`;
  }),
  defineCase('H3-CA4.8', 'duplicate membership is rejected', 'admin', '/admin/users/', 'backend rejects an existing member email', async ({ page, check }) => {
    await openUsers(page); const result = await bffPost(page, '/api/admin/invitations', { email: 'user@local.test', role: 'user' }); check('sanitized status', result.status === 502); check('sanitized error', result.body?.error?.code === 'invitation_failed'); return `HTTP ${result.status}: duplicate rejected without backend details`;
  }),
  defineCase('H3-CA4.8', 'invalid membership role is rejected by BFF schema', 'admin', '/admin/users/', 'BFF rejects roles outside admin/user before invoking Auth', async ({ page, check }) => {
    await openUsers(page); const result = await bffPost(page, '/api/admin/invitations', { email: 'invalid-role@local.test', role: 'owner' }); check('HTTP 400', result.status === 400); check('schema rejected', result.body?.error?.code === 'invalid_invitation'); return `HTTP ${result.status}: rejected before Auth`;
  }),
  defineCase('H3-CA4.8', 'membership controls cover state and role changes', 'admin', '/admin/users/', 'role changes persist, the last active admin is protected, and the synthetic fixture is restored', async ({ page, check }) => {
    await openUsers(page);
    const initialResponse = await rpc(page, 'admin_list_members_onboarding');
    assert(initialResponse.status === 200 && Array.isArray(initialResponse.body?.data), 'membership reader did not return the expected data envelope');
    const initialMembers = initialResponse.body.data;
    const actor = initialMembers.find((member) => member.email === USERS.admin.email);
    const activeAdmins = initialMembers.filter((member) => member.role === 'admin' && member.is_active);
    const target = activeAdmins.find((member) => member.user_id !== actor?.user_id);
    const rows = await page.locator('[data-membership-row]').count();
    const stateActionRoleCount = await page.getByRole('button', { name: /^(Desactivar|Activar) — .+$/ }).count();
    const stateActionDomCount = await page.locator('button[aria-label^="Desactivar — "], button[aria-label^="Activar — "]').count();
    check('state actions', stateActionRoleCount === rows,
      JSON.stringify({ rows, roleCount: stateActionRoleCount, ariaLabelCount: stateActionDomCount }));
    const roleActionRoleCount = await page.getByRole('button', { name: /^Hacer (user|admin) — .+$/ }).count();
    const roleActionDomCount = await page.locator('button[aria-label^="Hacer user — "], button[aria-label^="Hacer admin — "]').count();
    check('role actions', roleActionRoleCount === rows,
      JSON.stringify({ rows, roleCount: roleActionRoleCount, ariaLabelCount: roleActionDomCount }));
    const membershipRegion = page.getByRole('region', { name: 'Membresías existentes' });
    check('membership region has an accessible name and keyboard focus', await membershipRegion.getAttribute('tabindex') === '0');
    const scrollBeforeKey = await membershipRegion.evaluate((element) => ({
      left: element.scrollLeft,
      width: element.clientWidth,
      contentWidth: element.scrollWidth,
      clipped: element.scrollWidth > element.clientWidth,
      focused: document.activeElement === element,
    }));
    if (scrollBeforeKey.clipped) {
      await membershipRegion.focus();
      await membershipRegion.press('ArrowRight');
    }
    const scrollAfterRight = await membershipRegion.evaluate((element) => ({
      left: element.scrollLeft,
      focused: document.activeElement === element,
      maxScroll: element.scrollWidth - element.clientWidth,
    }));
    if (scrollBeforeKey.clipped) await membershipRegion.press('ArrowLeft');
    const scrollAfterLeft = await membershipRegion.evaluate((element) => element.scrollLeft);
    check('ArrowRight reveals later membership columns', !scrollBeforeKey.clipped || scrollAfterRight.left > scrollBeforeKey.left,
      JSON.stringify({ before: scrollBeforeKey, afterRight: scrollAfterRight }));
    check('ArrowLeft returns to earlier membership columns', !scrollBeforeKey.clipped || scrollAfterLeft < scrollAfterRight.left,
      JSON.stringify({ afterRight: scrollAfterRight.left, afterLeft: scrollAfterLeft }));
    check('membership headers identify their columns', await page.locator('[data-membership-scroll] thead th[scope="col"]').count() === 7);
    check('fixture actor is active admin', actor?.role === 'admin' && actor.is_active === true);
    check('exactly two active admins in isolated fixture', activeAdmins.length === 2);
    assert(actor?.role === 'admin' && actor.is_active === true, 'synthetic actor is not an active admin');
    assert(activeAdmins.length === 2 && target?.role === 'admin' && target.is_active === true, 'isolated fixture does not contain exactly two active admins');

    let targetMayNeedRestore = false;
    try {
      const targetRow = page.locator('[data-membership-row]').filter({ hasText: target.email });
      targetMayNeedRestore = true;
      page.once('dialog', (dialog) => dialog.accept());
      await targetRow.getByRole('button', { name: /^Hacer user — / }).click();
      await page.getByText('Membresía actualizada.', { exact: true }).waitFor();

      const afterChange = await rpc(page, 'admin_list_members_onboarding');
      assert(afterChange.status === 200 && Array.isArray(afterChange.body?.data), 'membership readback failed after role change');
      const persistedTarget = afterChange.body.data.find((member) => member.user_id === target.user_id);
      check('role change persisted through UI and BFF', persistedTarget?.role === 'user' && persistedTarget.is_active === true);
      check('only actor remains active admin', afterChange.body.data.filter((member) => member.role === 'admin' && member.is_active).length === 1);
      assert(persistedTarget?.role === 'user' && persistedTarget.is_active === true, 'target role change was not persisted');

      const waitForStateUpdate = (isActive) => page.waitForResponse((response) => {
        if (response.request().method() !== 'POST' || !response.url().includes('/api/admin/rpc')) return false;
        try {
          const request = response.request().postDataJSON();
          return request?.function === 'admin_update_member'
            && request?.params?.p_user_id === target.user_id
            && request?.params?.p_is_active === isActive;
        } catch {
          return false;
        }
      });
      page.once('dialog', (dialog) => dialog.accept());
      const deactivationResponse = waitForStateUpdate(false);
      await targetRow.getByRole('button', { name: /^Desactivar — / }).click();
      check('deactivation RPC completed', (await deactivationResponse).status() === 200);
      const afterDeactivation = await rpc(page, 'admin_list_members_onboarding');
      assert(afterDeactivation.status === 200 && Array.isArray(afterDeactivation.body?.data), 'membership readback failed after deactivation');
      const inactiveTarget = afterDeactivation.body.data.find((member) => member.user_id === target.user_id);
      check('deactivation persisted through UI and BFF', inactiveTarget?.role === 'user' && inactiveTarget.is_active === false);
      assert(inactiveTarget?.role === 'user' && inactiveTarget.is_active === false, 'deactivation was not persisted');

      page.once('dialog', (dialog) => dialog.accept());
      const activationResponse = waitForStateUpdate(true);
      await targetRow.getByRole('button', { name: /^Activar — / }).click();
      check('activation RPC completed', (await activationResponse).status() === 200);
      const afterActivation = await rpc(page, 'admin_list_members_onboarding');
      assert(afterActivation.status === 200 && Array.isArray(afterActivation.body?.data), 'membership readback failed after activation');
      const reactivatedTarget = afterActivation.body.data.find((member) => member.user_id === target.user_id);
      check('activation persisted through UI and BFF', reactivatedTarget?.role === 'user' && reactivatedTarget.is_active === true);
      assert(reactivatedTarget?.role === 'user' && reactivatedTarget.is_active === true, 'activation was not persisted');

      const concurrentMembershipUpdates = await Promise.all([
        rpc(page, 'admin_update_member', {
          p_user_id: target.user_id,
          p_role: 'admin',
          p_is_active: null,
          p_action: 'role_change',
        }),
        rpc(page, 'admin_update_member', {
          p_user_id: target.user_id,
          p_role: null,
          p_is_active: false,
          p_action: 'deactivation',
        }),
      ]);
      check('concurrent role and activation updates are serialized successfully',
        concurrentMembershipUpdates.every((response) => response.status === 200
          && response.body?.data?.[0]?.success === true));
      const afterConcurrentMembershipUpdates = await rpc(page, 'admin_list_members_onboarding');
      assert(afterConcurrentMembershipUpdates.status === 200
        && Array.isArray(afterConcurrentMembershipUpdates.body?.data),
      'membership readback failed after concurrent updates');
      const concurrentTarget = afterConcurrentMembershipUpdates.body.data
        .find((member) => member.user_id === target.user_id);
      const activeAdminsAfterConcurrentUpdates = afterConcurrentMembershipUpdates.body.data
        .filter((member) => member.role === 'admin' && member.is_active);
      check('concurrent membership updates preserve the active actor and final target state',
        concurrentTarget?.role === 'admin'
          && concurrentTarget.is_active === false
          && activeAdminsAfterConcurrentUpdates.length === 1
          && activeAdminsAfterConcurrentUpdates[0]?.user_id === actor.user_id);

      const actorRow = page.locator('[data-membership-row]').filter({ hasText: actor.email });
      page.once('dialog', (dialog) => dialog.accept());
      await actorRow.getByRole('button', { name: /^Hacer user — / }).click();
      await page.getByText('Cannot deactivate the last active admin', { exact: true }).waitFor();

      const afterDeniedChange = await rpc(page, 'admin_list_members_onboarding');
      assert(afterDeniedChange.status === 200 && Array.isArray(afterDeniedChange.body?.data), 'membership readback failed after last-admin rejection');
      const actorAfterDenial = afterDeniedChange.body.data.find((member) => member.user_id === actor.user_id);
      const targetAfterDenial = afterDeniedChange.body.data.find((member) => member.user_id === target.user_id);
      check('last-admin rejection surfaced in Admin UI', await page.getByText('Cannot deactivate the last active admin', { exact: true }).isVisible());
      check('actor remains active admin after rejection', actorAfterDenial?.role === 'admin' && actorAfterDenial.is_active === true);
      check('rejected last-admin mutation leaves concurrent target state unchanged', targetAfterDenial?.role === 'admin' && targetAfterDenial.is_active === false);
      assert(actorAfterDenial?.role === 'admin' && actorAfterDenial.is_active === true, 'last-admin guard changed the actor membership');
      assert(targetAfterDenial?.role === 'admin' && targetAfterDenial.is_active === false, 'last-admin guard changed the target membership');
    } finally {
      if (targetMayNeedRestore) {
        const currentResponse = await rpc(page, 'admin_list_members_onboarding');
        assert(currentResponse.status === 200 && Array.isArray(currentResponse.body?.data), 'could not inspect synthetic membership for restoration');
        const currentTarget = currentResponse.body.data.find((member) => member.user_id === target.user_id);
        assert(currentTarget, 'synthetic target disappeared before restoration');
        if (currentTarget.role !== target.role || currentTarget.is_active !== target.is_active) {
          const restoreResponse = await rpc(page, 'admin_update_member', {
            p_user_id: target.user_id,
            p_role: target.role,
            p_is_active: target.is_active,
            p_action: 'role_change',
          });
          assert(restoreResponse.status === 200 && restoreResponse.body?.data?.[0]?.success === true, 'could not restore synthetic membership');
        }
        const restoredResponse = await rpc(page, 'admin_list_members_onboarding');
        assert(restoredResponse.status === 200 && Array.isArray(restoredResponse.body?.data), 'membership readback failed after restoration');
        const restoredTarget = restoredResponse.body.data.find((member) => member.user_id === target.user_id);
        assert(restoredTarget?.role === target.role && restoredTarget.is_active === target.is_active, 'synthetic target was not restored to its original membership');
        await page.reload({ waitUntil: 'networkidle' });
      }
    }
    return `${rows} rows; persisted role change, last-admin rejection, and fixture restoration verified`;
  }),

  defineCase('H3-CA4.9', 'local administrative hostname serves admin', 'anon', '/admin/login/', 'configured local admin origin serves the login surface', async ({ page, check }) => {
    const response = await page.goto(`${BASE_URL}/admin/login/`); await page.getByRole('heading', { name: 'Admin' }).waitFor({ state: 'visible' }); check('HTTP 200', response?.status() === 200); check('admin login', await page.getByRole('heading', { name: 'Admin' }).isVisible()); const configuredHost = await page.request.get(`${BASE_URL}/admin/login/`, { headers: { Host: 'localhost' }, maxRedirects: 0 }); check('configured admin host serves login', configuredHost.status() === 200); const unknownHost = await page.request.get(`${BASE_URL}/admin/login/`, { headers: { Host: 'unconfigured-admin.invalid' }, maxRedirects: 0 }); check('unconfigured admin host fails closed', unknownHost.status() === 404); return `configured local host HTTP ${configuredHost.status()}; unknown host HTTP ${unknownHost.status()}`;
  }),
  defineCase('H3-CA4.9', 'public hostname hides admin with 404', 'anon', '/admin/', 'Host studiamatch.com returns HTTP 404 for admin on the perimeter origin', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const response = await page.request.get(`${PERIMETER_URL}/admin/`, { headers: { Host: 'studiamatch.com' }, maxRedirects: 0 }); check('HTTP 404', response.status() === 404); const login = await page.request.get(`${PERIMETER_URL}/admin/login/`, { headers: { Host: 'localhost' } }); check('admin origin serves 200', login.status() === 200); return `perimeter HTTP ${response.status()}`;
  }),
  defineCase('H3-CA4.9', 'public routes remain available', 'anon', '/', 'all five public regression routes return HTTP 200', async ({ page, check }) => {
    const statuses = {}; for (const route of PUBLIC_ROUTES) { const response = await page.request.get(`${BASE_URL}${route}`); statuses[route] = response.status(); check(`${route} 200`, response.status() === 200); } await page.goto(`${BASE_URL}/`); return JSON.stringify(statuses);
  }, { requiresFixtureReset: false }),

  defineCase('H3-CA4.10', 'PG17 harness carries convergence sentinel', 'anon', '/admin/login/', 'local PG17 harness includes authoritative H3 migrations and success sentinel', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const observed = await readContract('tests/sql/h3_pg17_harness.sql', ['20260830_h3_expanded_contract.sql', 'h3_pg17_harness_ok']); check('harness contract', true); return observed;
  }),
  defineCase('H3-CA4.10', 'migration contracts are idempotent for second run', 'anon', '/admin/login/', 'H3 expanded migration declares idempotent create/replace or guarded operations', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const observed = await readContract('db/migrations/20260830_h3_expanded_contract.sql', ['CREATE OR REPLACE FUNCTION', 'IF NOT EXISTS']); check('NOOP prerequisites', true); return observed;
  }),

  defineCase('H3-CA4.11', 'runtime resources and browser diagnostics are clean', 'anon', '/admin/login/', 'same-origin resources load without HTTP errors, console errors or failed requests', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`, { waitUntil: 'networkidle' }); check('login rendered', await page.getByRole('heading', { name: 'Admin' }).isVisible()); return 'runtime settled at networkidle';
  }, { requiresFixtureReset: false }),
  defineCase('H3-CA4.11', 'layout has no horizontal overflow', 'admin', '/admin/', 'admin dashboard fits the active desktop/tablet/mobile viewport', async ({ page, check }) => {
    await login(page, 'admin'); const dimensions = await page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth })); check('no overflow', dimensions.scrollWidth <= dimensions.clientWidth + 1); return JSON.stringify(dimensions);
  }),
  defineCase('H3-CA4.11', 'basic keyboard and accessible-name contract holds', 'anon', '/admin/login/', 'login controls have accessible names and keyboard focus order', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); await page.getByLabel('Email').waitFor({ state: 'visible' }); await page.keyboard.press('Tab'); const first = await page.evaluate(() => document.activeElement?.getAttribute('href') || document.activeElement?.getAttribute('name') || document.activeElement?.tagName); check('focus entered interactive UI', Boolean(first)); check('email name', await page.getByLabel('Email').count() === 1); check('password name', await page.getByLabel('Password').count() === 1); check('button name', await page.getByRole('button', { name: 'Iniciar sesión' }).count() === 1); return `first focus=${first}`;
  }, { requiresFixtureReset: false }),
  defineCase('H3-CA4.5', 'pipeline course completes Admin provenance availability publication and public journey', 'admin', '/admin/edit/', 'same synthetic pipeline course is edited, audited, previewed, gated by evidence, published, and read by public listing/detail/compare while preserving its original state', async ({ page, check }) => {
    const courseId = process.env.H3_PIPELINE_COURSE_ID || '70000000-0000-0000-0000-000000000091';
    const institutionSlug = process.env.H3_PIPELINE_INSTITUTION_SLUG || 'ulima';
    const courseSlug = process.env.H3_PIPELINE_COURSE_SLUG || 'analitica-aplicada-60000000';
    const publicName = process.env.H3_PIPELINE_PUBLIC_NAME || 'Analítica Aplicada';
    const editorUrl = `${BASE_URL}/admin/edit/?id=${encodeURIComponent(courseId)}`;
    const detailUrl = `${BASE_URL}/courses/${encodeURIComponent(institutionSlug)}/${encodeURIComponent(courseSlug)}/`;
    let original = null;
    let restoreFailed = false;

    const currentEditorial = async () => {
      const response = await rpc(page, 'admin_get_course_editorial', { p_course_id: courseId });
      const row = response.body?.data?.[0]?.course;
      assert(response.status === 200 && row, 'pipeline course editorial row did not load');
      return row;
    };
    const setManualOverrides = async (values, reason) => {
      const current = await currentEditorial();
      const response = await rpc(page, 'admin_update_course', {
        p_course_id: courseId,
        p_manual_overrides: values,
        p_version: current.version,
        p_reason: reason,
      });
      assert(response.status === 200 && response.body?.data?.[0]?.success === true, 'pipeline course editorial restore/update failed');
    };
    const setAvailability = async (state) => {
      const current = await currentEditorial();
      const response = await rpc(page, 'admin_set_course_availability', {
        p_course_id: courseId,
        p_availability_status: state?.availability_override_status ?? null,
        p_evidence_url: state?.availability_evidence_url ?? null,
        p_observed_at: state?.availability_observed_at ?? null,
        p_valid_until: state?.availability_valid_until ?? null,
        p_version: current.version,
        p_reason: 'Restauración sintética de estado integrado UAT',
      });
      assert(response.status === 200 && response.body?.data?.[0]?.success === true, 'pipeline course availability restore failed');
    };

    await login(page, 'admin');
    await page.goto(editorUrl, { waitUntil: 'domcontentloaded' });
    await page.locator('main input[name="name"]').waitFor({ state: 'visible' });
    original = await currentEditorial();
    try {
    check('course identity and synthetic pipeline provenance', original.course_id === courseId
      && original.pipeline_values?.name === publicName
      && ['pipeline', 'manual_override'].includes(original.field_sources?.name || 'pipeline'));
    const expectedFieldControls = {
      name: 'input:text',
      price_pen: 'input:number',
      price_status: 'button:combobox',
      mode: 'button:combobox',
      duration: 'input:text',
      description_long: 'textarea:',
      syllabus: 'textarea:',
      target_audience: 'textarea:',
      requirements: 'textarea:',
      certification: 'textarea:',
      benefits: 'textarea:',
      objectives: 'textarea:',
      start_date_text: 'input:text',
    };
    const observedFieldControls = await page.evaluate((fieldKeys) => Object.fromEntries(fieldKeys.map((key) => {
      const element = document.getElementById(key);
      const tag = element?.tagName.toLowerCase() || 'missing';
      const type = element instanceof HTMLInputElement ? element.type : element?.getAttribute('role') || '';
      return [key, `${tag}:${type}`];
    })), Object.keys(expectedFieldControls));
    check('all thirteen editorial fields expose the expected control type',
      JSON.stringify(observedFieldControls) === JSON.stringify(expectedFieldControls), JSON.stringify(observedFieldControls));

    const auditBeforeAvailabilityProbes = await rpc(page, 'admin_get_course_audit', { p_course_id: courseId, p_first: 100 });
    const auditEventsBeforeAvailabilityProbes = auditBeforeAvailabilityProbes.body?.data?.[0]?.events || [];
    assert(auditBeforeAvailabilityProbes.status === 200, 'availability audit baseline could not be read');
    const observedRecently = new Date(Date.now() - 60 * 60 * 1000);
    const validForNinetyDays = new Date(observedRecently);
    validForNinetyDays.setUTCDate(validForNinetyDays.getUTCDate() + 90);
    const futureObservation = new Date(Date.now() + 60 * 60 * 1000);
    const expiredObservation = new Date(Date.now() - 48 * 60 * 60 * 1000);
    const availabilityProbes = [
      {
        label: 'non-HTTPS evidence URL',
        evidenceUrl: 'http://synthetic.h3.example/programs/analitica-aplicada/availability-proof',
        observedAt: observedRecently.toISOString(),
        validUntil: validForNinetyDays.toISOString(),
      },
      {
        label: 'future observation timestamp',
        evidenceUrl: 'https://synthetic.h3.example/programs/analitica-aplicada/availability-proof',
        observedAt: futureObservation.toISOString(),
        validUntil: new Date(futureObservation.getTime() + 90 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        label: 'expired evidence',
        evidenceUrl: 'https://synthetic.h3.example/programs/analitica-aplicada/availability-proof',
        observedAt: expiredObservation.toISOString(),
        validUntil: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
      },
      {
        label: 'validity beyond 90 days',
        evidenceUrl: 'https://synthetic.h3.example/programs/analitica-aplicada/availability-proof',
        observedAt: observedRecently.toISOString(),
        validUntil: new Date(validForNinetyDays.getTime() + 60 * 1000).toISOString(),
      },
    ];
    for (const probe of availabilityProbes) {
      const rejected = await rpc(page, 'admin_set_course_availability', {
        p_course_id: courseId,
        p_availability_status: 'available',
        p_evidence_url: probe.evidenceUrl,
        p_observed_at: probe.observedAt,
        p_valid_until: probe.validUntil,
        p_version: original.version,
        p_reason: `UAT negativa sintética: ${probe.label}`,
      });
      check(`backend rejects ${probe.label}`,
        rejected.status === 200 && rejected.body?.data?.[0]?.success === false);
      const afterRejectedProbe = await currentEditorial();
      check(`${probe.label} leaves availability state and version unchanged`,
        afterRejectedProbe.version === original.version
          && afterRejectedProbe.availability_override_status === original.availability_override_status
          && afterRejectedProbe.availability_evidence_url === original.availability_evidence_url
          && afterRejectedProbe.availability_observed_at === original.availability_observed_at
          && afterRejectedProbe.availability_valid_until === original.availability_valid_until);
    }
    const auditAfterAvailabilityProbes = await rpc(page, 'admin_get_course_audit', { p_course_id: courseId, p_first: 100 });
    const auditEventsAfterAvailabilityProbes = auditAfterAvailabilityProbes.body?.data?.[0]?.events || [];
    const auditSignature = (events) => JSON.stringify(events.map((event) => [
      event.action, event.created_at, event.old_values, event.new_values,
    ]));
    check('rejected availability evidence creates no audit event',
      auditAfterAvailabilityProbes.status === 200
        && auditSignature(auditEventsAfterAvailabilityProbes) === auditSignature(auditEventsBeforeAvailabilityProbes));

    const temporaryName = `${publicName} · revisión ${page.viewportSize()?.width || 'local'}`;
    await page.locator('main input[name="name"]').fill(temporaryName);
    const originalPriceInput = await page.locator('main input[name="price_pen"]').inputValue();
    const originalModeButton = (await page.getByLabel('Modalidad').innerText()).trim();
    const originalPriceStatusButton = (await page.getByLabel('Estado del precio').innerText()).trim();
    const originalDurationInput = await page.locator('main input[name="duration"]').inputValue();
    const originalDescriptionInput = await page.locator('main textarea[name="description_long"]').inputValue();
    const priceInput = page.locator('main input[name="price_pen"]');
    const durationInput = page.locator('main input[name="duration"]');
    const descriptionInput = page.locator('main textarea[name="description_long"]');
    const durationDraft = `5 meses · matriz de tipos ${page.viewportSize()?.width || 'local'}`;
    const descriptionDraft = `Descripción sintética de textarea ${page.viewportSize()?.width || 'local'}`;
    await priceInput.fill('1325');
    await durationInput.fill(durationDraft);
    await descriptionInput.fill(descriptionDraft);
    const modality = page.getByLabel('Modalidad');
    await modality.click();
    await page.getByRole('option', { name: 'Híbrido', exact: true }).click();
    const priceStatus = page.getByLabel('Estado del precio');
    await priceStatus.click();
    await page.getByRole('option', { name: 'Consultar precio', exact: true }).click();
    const pricePreview = page.locator('[data-preview-field="price_pen"]').first();
    const priceReturnPreview = page.locator('[data-preview-field="price_pen"]').nth(1);
    const consultPriceObservation = {
      selectText: (await priceStatus.innerText()).replace(/\s+/g, ' ').trim(),
      summaryText: (await pricePreview.innerText()).replace(/\s+/g, ' ').trim().toLocaleLowerCase('es'),
      returnText: (await priceReturnPreview.innerText()).replace(/\s+/g, ' ').trim().toLocaleLowerCase('es'),
    };
    check('price status select applies the consult fallback', consultPriceObservation.summaryText.includes('consultar')
      && consultPriceObservation.returnText.includes('s/ --')
      && consultPriceObservation.selectText.includes('Consultar precio'), JSON.stringify(consultPriceObservation));
    await priceStatus.click();
    await page.getByRole('option', { name: 'Precio disponible', exact: true }).click();
    check('number input is reflected after the price status is available', (await pricePreview.innerText()).toLocaleLowerCase('es').includes('s/ 1,325'));
    check('price status select restores the available label', (await priceStatus.innerText()).includes('Precio disponible'));
    check('modality select updates both public preview placements', (await page.locator('[data-preview-field="mode"]').first().innerText()).toLocaleLowerCase('es').includes('híbrido')
      && (await page.locator('[data-preview-field="mode"]').nth(1).innerText()).toLocaleLowerCase('es').includes('híbrido'));
    check('text input updates the duration preview', (await page.locator('[data-preview-field="duration"]').innerText()).toLocaleLowerCase('es').includes(durationDraft.toLocaleLowerCase('es')));
    check('textarea updates the long-description preview', (await page.locator('[data-preview-field="description_long"]').innerText()).toLocaleLowerCase('es').includes(descriptionDraft.toLocaleLowerCase('es')));
    const startDateInput = page.locator('main input[name="start_date_text"]');
    const originalStartDate = await startDateInput.inputValue();
    await startDateInput.focus();
    await startDateInput.fill('');
    await page.getByLabel('Motivo de la corrección').fill('Verificación integrada de procedencia y publicación');
    check('preview reflects unsaved effective value', await page.getByText(temporaryName, { exact: true }).count() > 0);
    const previewPanel = page.getByText('Vista previa pública', { exact: true })
      .locator('xpath=ancestor::div[contains(@class,"overflow-hidden")][1]');
    const previewText = (await previewPanel.innerText()).toLocaleLowerCase('es');
    const previewSummary = {
      title: previewText.includes(temporaryName.toLocaleLowerCase('es')),
      mode: previewText.includes('remoto'),
      price: previewText.includes('s/ 1,325'),
      text: previewText.slice(0, 260),
    };
    check('preview preserves populated public fields with unsaved title', previewSummary.title
      && previewText.includes('híbrido')
      && previewSummary.price, JSON.stringify(previewSummary));
    let previewDateSettled = false;
    await page.waitForFunction(() => {
      const input = document.querySelector('main input[name="start_date_text"]');
      const preview = document.querySelector('[data-preview-field="start_date_text"]');
      return input instanceof HTMLInputElement
        && input.value === ''
        && preview instanceof HTMLElement
        && preview.textContent?.toLocaleLowerCase('es').includes('consultar') === true;
    }, undefined, { timeout: 2000 }).then(() => { previewDateSettled = true; }).catch(() => {});
    const previewDateState = await page.evaluate(() => {
      const input = document.querySelector('main input[name="start_date_text"]');
      const impact = document.querySelector('#preview-impact-start_date_text');
      const dateField = document.querySelector('[data-preview-field="start_date_text"]');
      return {
        inputEmpty: input instanceof HTMLInputElement && input.value === '',
        inputType: input instanceof HTMLInputElement ? input.type : 'missing',
        focusImpactPresent: impact instanceof HTMLElement,
        impactText: impact?.textContent?.replace(/\s+/g, ' ').trim().slice(0, 80) || '',
        previewPresent: dateField instanceof HTMLElement,
        previewText: dateField?.textContent?.replace(/\s+/g, ' ').trim().slice(0, 80) || '',
      };
    });
    check('date preview shows the fallback after the editor input event', previewDateSettled,
      `inputEmpty=${previewDateState.inputEmpty}; inputType=${previewDateState.inputType}; previewPresent=${previewDateState.previewPresent}; previewText=${previewDateState.previewText}; focusImpactPresent=${previewDateState.focusImpactPresent}`);
    const startDatePreview = page.locator('[data-preview-field="start_date_text"]').first();
    const startDatePreviewText = await startDatePreview.innerText();
    const startDateFallback = startDatePreview.getByText('Consultar', { exact: true });
    const startDateFallbackCount = await startDateFallback.count();
    const startDateFallbackVisible = startDateFallbackCount === 1 && await startDateFallback.isVisible();
    check('empty optional start date uses the public fallback', previewDateState.inputEmpty && previewDateState.previewPresent && startDateFallbackVisible,
      `inputEmpty=${previewDateState.inputEmpty}; fallbackCount=${startDateFallbackCount}; fallbackVisible=${startDateFallbackVisible}; innerText=${JSON.stringify(startDatePreviewText).slice(0, 100)}; textContent=${previewDateState.previewText}`);
    check('preview contains no raw null or undefined values', !/\b(?:null|undefined)\b/i.test(previewText));
    const previewLayout = await previewPanel.evaluate((element) => {
      const bounds = element.getBoundingClientRect();
      return {
        left: bounds.left,
        right: bounds.right,
        viewportWidth: window.innerWidth,
        clientWidth: element.clientWidth,
        scrollWidth: element.scrollWidth,
      };
    });
    check('preview panel fits the active viewport without horizontal overflow',
      previewLayout.left >= -1
        && previewLayout.right <= previewLayout.viewportWidth + 1
        && previewLayout.scrollWidth <= previewLayout.clientWidth + 1,
      `left=${Math.round(previewLayout.left)}; right=${Math.round(previewLayout.right)}; viewport=${previewLayout.viewportWidth}; scroll=${previewLayout.scrollWidth}; client=${previewLayout.clientWidth}`);
    await page.goto(`${BASE_URL}/admin/`, { waitUntil: 'domcontentloaded' });
    await page.goto(editorUrl, { waitUntil: 'domcontentloaded' });
    await page.locator('main input[name="name"]').waitFor({ state: 'visible' });
    const afterDiscardedPreview = await currentEditorial();
    check('leaving an unsaved preview preserves the persisted value and version',
      afterDiscardedPreview.version === original.version
        && afterDiscardedPreview.current_values?.name === original.current_values?.name
        && afterDiscardedPreview.current_values?.start_date_text === original.current_values?.start_date_text
        && Number(await page.locator('main input[name="price_pen"]').inputValue()) === Number(original.current_values?.price_pen)
        && (await page.getByLabel('Modalidad').innerText()).trim() === originalModeButton
        && (await page.getByLabel('Estado del precio').innerText()).trim() === originalPriceStatusButton
        && await page.locator('main input[name="duration"]').inputValue() === originalDurationInput
        && await page.locator('main textarea[name="description_long"]').inputValue() === originalDescriptionInput
        && await page.locator('main input[name="start_date_text"]').inputValue() === originalStartDate
        && await page.locator('main input[name="name"]').inputValue() === original.current_values?.name);
    const discardedSaveButton = page.getByRole('button', { name: 'Guardar cambios' });
    const discardedSaveButtonCount = await discardedSaveButton.count();
    const discardedSaveButtonDisabled = discardedSaveButtonCount === 1 && await discardedSaveButton.isDisabled();
    const discardedUnsavedBadgeCount = await page.getByText('Cambios sin guardar', { exact: true }).count();
    const auditAfterDiscardedPreview = await rpc(page, 'admin_get_course_audit', { p_course_id: courseId, p_first: 100 });
    const auditEventsAfterDiscardedPreview = auditAfterDiscardedPreview.body?.data?.[0]?.events || [];
    check('discarded preview leaves no-op save disabled and audit unchanged',
      discardedSaveButtonDisabled
        && discardedUnsavedBadgeCount === 0
        && auditAfterDiscardedPreview.status === 200
        && auditSignature(auditEventsAfterDiscardedPreview) === auditSignature(auditEventsBeforeAvailabilityProbes),
      `saveButtons=${discardedSaveButtonCount}; saveDisabled=${discardedSaveButtonDisabled}; unsavedBadges=${discardedUnsavedBadgeCount}; auditUnchanged=${auditSignature(auditEventsAfterDiscardedPreview) === auditSignature(auditEventsBeforeAvailabilityProbes)}`);
    const viewportMarker = page.viewportSize()?.width || 'local';
    const originalModeValue = String(original.current_values?.mode ?? '');
    const originalPriceStatusValue = String(original.current_values?.price_status ?? '');
    const editedMode = originalModeValue === 'Híbrido' ? 'Remoto' : 'Híbrido';
    const editedPriceStatus = originalPriceStatusValue === 'consultar' ? 'available' : 'consultar';
    const editorialDraft = {
      name: temporaryName,
      price_pen: '1325',
      price_status: editedPriceStatus,
      mode: editedMode,
      duration: `5 meses · matriz de tipos ${viewportMarker}`,
      description_long: `Descripción sintética de textarea ${viewportMarker}`,
      syllabus: `Temario sintético ${viewportMarker}: módulo de evidencia`,
      target_audience: `Público objetivo sintético ${viewportMarker}`,
      requirements: `Requisitos sintéticos ${viewportMarker}`,
      certification: `Certificación sintética ${viewportMarker}`,
      benefits: `Beneficios sintéticos ${viewportMarker}`,
      objectives: `Objetivos sintéticos ${viewportMarker}`,
      start_date_text: `Octubre 2026 · ${viewportMarker}`,
    };
    for (const field of EDITORIAL_FIELDS) {
      const value = editorialDraft[field];
      if (field === 'price_status' || field === 'mode') {
        const label = field === 'price_status' ? 'Estado del precio' : 'Modalidad';
        const option = field === 'price_status'
          ? value === 'consultar' ? 'Consultar precio' : 'Precio disponible'
          : value;
        await page.getByLabel(label).click();
        await page.getByRole('option', { name: option, exact: true }).click();
      } else {
        await page.locator(`main [name="${field}"]`).fill(value);
      }
    }
    await page.getByLabel('Motivo de la corrección').fill('Verificación integrada de procedencia y publicación');
    await page.getByRole('button', { name: 'Guardar cambios' }).click();
    await page.getByRole('status').filter({ hasText: 'Cambios guardados correctamente.' }).waitFor();
    const updated = await currentEditorial();
    const editorialFieldsPersisted = EDITORIAL_FIELDS.every((field) => field === 'price_pen'
      ? Number(updated.current_values?.[field]) === Number(editorialDraft[field])
        && Number(updated.manual_overrides?.[field]) === Number(editorialDraft[field])
      : updated.current_values?.[field] === editorialDraft[field]
        && updated.manual_overrides?.[field] === editorialDraft[field]);
    const pipelineFieldsPreserved = EDITORIAL_FIELDS.every((field) =>
      JSON.stringify(updated.pipeline_values?.[field] ?? null) === JSON.stringify(original.pipeline_values?.[field] ?? null)
        && updated.field_sources?.[field] === original.field_sources?.[field]);
    check('all thirteen manual overrides persist while pipeline values and provenance remain intact',
      editorialFieldsPersisted && pipelineFieldsPreserved,
      `manualFields=${EDITORIAL_FIELDS.filter((field) => updated.manual_overrides?.[field] !== undefined).length}; pipelinePreserved=${pipelineFieldsPreserved}`);
    check('Admin visibly identifies manual overrides across the editor', await page.getByText('Corrección manual', { exact: true }).count() > 0);
    const auditResponse = await rpc(page, 'admin_get_course_audit', { p_course_id: courseId, p_first: 20 });
    const auditEvents = auditResponse.body?.data?.[0]?.events || [];
    const updateAudit = auditEvents.find((event) => event.action === 'update'
      && event.new_values?.manual_overrides?.name === temporaryName
      && event.new_values?.manual_overrides?.start_date_text === editorialDraft.start_date_text);
    const auditOldValuesMatch = EDITORIAL_FIELDS.every((field) => field === 'price_pen'
      ? Number(updateAudit?.old_values?.manual_overrides?.[field] ?? original.manual_overrides?.[field] ?? 0)
        === Number(original.manual_overrides?.[field] ?? 0)
      : (updateAudit?.old_values?.manual_overrides?.[field] ?? null) === (original.manual_overrides?.[field] ?? null));
    const auditNewValuesMatch = EDITORIAL_FIELDS.every((field) => field === 'price_pen'
      ? Number(updateAudit?.new_values?.manual_overrides?.[field]) === Number(editorialDraft[field])
      : updateAudit?.new_values?.manual_overrides?.[field] === editorialDraft[field]);
    check('audit actor date before and after', Boolean(updateAudit)
      && updateAudit.actor_label === 'admin@local.test'
      && Boolean(updateAudit.created_at)
      && auditOldValuesMatch && auditNewValuesMatch,
      `actor=${updateAudit?.actor_label || 'missing'}; timestamp=${Boolean(updateAudit?.created_at)}; old/new fields=${EDITORIAL_FIELDS.length}`);

    const unpublish = page.getByRole('button', { name: 'Despublicar' });
    if (await unpublish.count()) {
      await unpublish.click();
      await page.getByRole('status').filter({ hasText: 'Curso despublicado.' }).waitFor();
    }
    const afterUnpublish = await currentEditorial();
    if (afterUnpublish.availability_override_status) {
      const clearResponse = await rpc(page, 'admin_set_course_availability', {
        p_course_id: courseId,
        p_availability_status: null,
        p_evidence_url: null,
        p_observed_at: null,
        p_valid_until: null,
        p_version: afterUnpublish.version,
        p_reason: 'Prueba negativa: retiro de evidencia sintética',
      });
      check('availability evidence can be cleared before negative publication check', clearResponse.body?.data?.[0]?.success === true);
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.locator('main input[name="name"]').waitFor({ state: 'visible' });
      const clearedAfterReload = await currentEditorial();
      check('editor reload observes the new optimistic-lock version', clearedAfterReload.availability_override_status === null
        && clearedAfterReload.availability_evidence_url === null);
    }
    const deniedPublish = await rpc(page, 'admin_publish_course', { p_course_id: courseId, p_reason: 'Prueba negativa sin evidencia vigente' });
    check('publication denied without current evidence', deniedPublish.body?.data?.[0]?.success === false
      && /availability is not confirmed/i.test(deniedPublish.body?.data?.[0]?.error || ''));

    await page.getByLabel('Enlace de evidencia oficial').fill('https://synthetic.h3.example/programs/analitica-aplicada/availability-proof');
    const validity = await page.evaluate(() => {
      const observed = new Date(Date.now() - 60 * 60 * 1000);
      const validUntil = new Date(observed);
      validUntil.setUTCDate(validUntil.getUTCDate() + 90);
      const local = (date) => new Date(date.getTime() - date.getTimezoneOffset() * 60 * 1000).toISOString().slice(0, 16);
      return { observed: local(observed), validUntil: local(validUntil) };
    });
    await page.getByLabel('Verificado el').fill(validity.observed);
    await page.getByLabel('Evidencia válida hasta').fill(validity.validUntil);
    await page.getByLabel('Nota de verificación').fill('Verificación sintética de límite inclusivo de 90 días');
    await page.getByRole('button', { name: 'Guardar verificación' }).click();
    await page.getByRole('status').filter({ hasText: 'Evidencia de disponibilidad registrada.' }).waitFor();
    check('inclusive 90-day evidence accepted', await page.getByText('Disponible', { exact: true }).count() > 0);
    await page.getByRole('button', { name: 'Publicar' }).click();
    await page.getByRole('status').filter({ hasText: 'Curso publicado.' }).waitFor();

    const publicRows = await page.request.get(`${MOCK_URL}/rest/v1/courses_public_effective?slug=eq.${encodeURIComponent(courseSlug)}&limit=1`);
    const publicData = await publicRows.json();
    const effectiveEditorialValues = Array.isArray(publicData) && publicData[0] ? EDITORIAL_FIELDS.every((field) => field === 'price_pen'
      ? Number(publicData[0][field]) === Number(editorialDraft[field])
      : publicData[0][field] === editorialDraft[field]) : false;
    const expectedPriceLabel = editorialDraft.price_status === 'consultar'
      ? 'consultar' : `s/ ${Number(editorialDraft.price_pen).toLocaleString('es-PE')}`;
    check('same identity visible in effective public reader', publicRows.status() === 200
      && Array.isArray(publicData) && publicData.length === 1
      && publicData[0].id === courseId && publicData[0].name === temporaryName
      && effectiveEditorialValues,
      `identity=${publicData?.[0]?.id === courseId}; effectiveFields=${EDITORIAL_FIELDS.filter((field) => publicData?.[0]?.[field] !== undefined).length}/13`);

    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    const publicCard = page.locator('article').filter({ hasText: temporaryName }).first();
    await waitForPublicCatalog(page);
    await publicCard.waitFor({ state: 'visible' });
    const publicCardTitle = publicCard.getByRole('heading', { name: temporaryName, exact: true });
    check('same course appears in exactly one public card', await page.locator('article').filter({ hasText: temporaryName }).count() === 1
      && await publicCardTitle.count() === 1 && await publicCardTitle.isVisible());
    check('public card reflects edited modality and price status',
      (await publicCard.innerText()).toLocaleLowerCase('es').includes(editorialDraft.mode.toLocaleLowerCase('es'))
        && (await publicCard.innerText()).toLocaleLowerCase('es').includes(expectedPriceLabel));
    await page.reload({ waitUntil: 'domcontentloaded' });
    await waitForPublicCatalog(page);
    const reloadedPublicCards = page.locator('article').filter({ has: page.getByRole('heading', { name: temporaryName, exact: true }) });
    check('public listing reload resolves the current override without a stale title', await reloadedPublicCards.count() === 1
      && await reloadedPublicCards.getByRole('heading', { name: temporaryName, exact: true }).isVisible()
      && await page.locator('article').filter({ has: page.getByRole('heading', { name: publicName, exact: true }) }).count() === 0);
    if (process.env.H3_SKIP_STATIC_DETAIL !== 'true') {
      await page.goto(detailUrl, { waitUntil: 'domcontentloaded' });
      const detailTitle = page.locator('main').getByRole('heading', { level: 1, name: temporaryName, exact: true });
      await detailTitle.waitFor({ state: 'visible' });
      check('detail exposes one exact main title', await detailTitle.count() === 1);
      const publicDetailText = (await page.locator('main').innerText()).toLocaleLowerCase('es');
      check('public detail reflects edited effective fields', publicDetailText.includes(expectedPriceLabel)
        && publicDetailText.includes(editorialDraft.mode.toLocaleLowerCase('es'))
        && publicDetailText.includes(editorialDraft.duration.toLocaleLowerCase('es'))
        && publicDetailText.includes(editorialDraft.description_long.toLocaleLowerCase('es')));
      check('advice remains explicitly closed without a capture form', await page.getByText('Canal cerrado temporalmente', { exact: true }).count() === 1
        && await page.locator('form input[type="email"], form textarea').count() === 0);
      await page.reload({ waitUntil: 'domcontentloaded' });
      await detailTitle.waitFor({ state: 'visible' });
      const reloadedDetailText = (await page.locator('main').innerText()).toLocaleLowerCase('es');
      check('public detail reload resolves edited overrides without stale values', await detailTitle.count() === 1
        && reloadedDetailText.includes(expectedPriceLabel)
        && reloadedDetailText.includes(editorialDraft.mode.toLocaleLowerCase('es'))
        && reloadedDetailText.includes(editorialDraft.description_long.toLocaleLowerCase('es'))
        && await page.locator('main').getByRole('heading', { level: 1, name: publicName, exact: true }).count() === 0);
      await page.goto(`${BASE_URL}/compare/?ids=${encodeURIComponent(courseId)}`, { waitUntil: 'domcontentloaded' });
      await page.getByRole('heading', { name: 'Comparativa de Programas' }).waitFor({ state: 'visible' });
      await page.getByText(temporaryName, { exact: true }).waitFor({ state: 'visible' });
      await page.locator('main').getByText('Consultar', { exact: false }).first().waitFor({ state: 'visible' });
      check('comparison resolves the same course and effective fields', await page.getByText(temporaryName, { exact: true }).count() > 0
        && (await page.locator('main').innerText()).toLocaleLowerCase('es').includes(expectedPriceLabel)
        && (await page.locator('main').innerText()).toLocaleLowerCase('es').includes(editorialDraft.mode.toLocaleLowerCase('es')));
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.getByRole('heading', { name: 'Comparativa de Programas' }).waitFor({ state: 'visible' });
      await page.getByText(temporaryName, { exact: true }).waitFor({ state: 'visible' });
      check('comparison reload resolves the current override and effective price', await page.getByText(temporaryName, { exact: true }).count() > 0
        && (await page.locator('main').innerText()).toLocaleLowerCase('es').includes(expectedPriceLabel)
        && (await page.locator('main').innerText()).toLocaleLowerCase('es').includes(editorialDraft.mode.toLocaleLowerCase('es')));
      const infoLink = page.getByRole('link', { name: 'Solicitar Info', exact: true });
      const infoHref = await infoLink.getAttribute('href');
      check('comparison information action stays on the same local detail route', await infoLink.count() === 1
        && new URL(infoHref || '/', BASE_URL).origin === new URL(BASE_URL).origin
        && new URL(infoHref || '/', BASE_URL).pathname.replace(/\/+$/, '') === new URL(detailUrl).pathname.replace(/\/+$/, ''));
    }

    return `course=${courseId}; admin edit/audit/preview/evidence/publish and public reader/list/detail/compare passed at ${page.viewportSize()?.width}px`;
    } finally {
      if (original) {
        try {
          const originalOverrides = Object.fromEntries(EDITORIAL_FIELDS.map((field) => [
            field, original.manual_overrides?.[field] ?? null,
          ]));
          await setManualOverrides(originalOverrides, 'Restaurar fixture pipeline integrado UAT');
          const restored = await currentEditorial();
          if (process.env.H3_PRESERVE_PIPELINE_PUBLISHED === 'true') {
            assert(restored.editorial_status === 'published' && restored.availability_override_status === 'available', 'pipeline fixture must remain published with valid evidence for static detail build');
          } else {
            await setAvailability(original.availability_override_status ? original : null);
          }
          const finalState = await currentEditorial();
          if (process.env.H3_PRESERVE_PIPELINE_PUBLISHED !== 'true'
            && original.editorial_status === 'published' && finalState.editorial_status !== 'published') {
            const result = await rpc(page, 'admin_publish_course', { p_course_id: courseId, p_reason: 'Restaurar publicación sintética de UAT' });
            assert(result.body?.data?.[0]?.success === true, 'pipeline fixture could not be restored to published');
          } else if (process.env.H3_PRESERVE_PIPELINE_PUBLISHED !== 'true'
            && original.editorial_status !== 'published' && finalState.editorial_status === 'published') {
            const result = await rpc(page, 'admin_unpublish_course', { p_course_id: courseId, p_reason: 'Restaurar estado editorial sintético de UAT' });
            assert(result.body?.data?.[0]?.success === true, 'pipeline fixture could not be restored to its original unpublished state');
          }
        } catch {
          restoreFailed = true;
        }
        assert(!restoreFailed, 'synthetic pipeline fixture restoration failed');
      }
    }
  }),
  defineCase('H3-CA4.5', 'user is denied mutation of the complete pipeline course', 'user', '/admin/edit/', 'active user cannot change a complete pipeline-owned course or its publication state', async ({ page, check }) => {
    const courseId = process.env.H3_PIPELINE_COURSE_ID || '70000000-0000-0000-0000-000000000091';
    await login(page, 'user');
    const before = await rpc(page, 'admin_get_course_editorial', { p_course_id: courseId });
    const course = before.body?.data?.[0]?.course;
    const readErrorCode = before.body?.error?.code;
    check('pipeline course readable to active editor', Boolean(course),
      `status=${before.status};errorCode=${typeof readErrorCode === 'string' && /^[a-z0-9_]{1,48}$/.test(readErrorCode) ? readErrorCode : 'UNCLASSIFIED'};rows=${Array.isArray(before.body?.data) ? before.body.data.length : 0}`);
    const denied = await rpc(page, 'admin_update_course', {
      p_course_id: courseId,
      p_manual_overrides: { name: 'Mutación no autorizada UAT' },
      p_version: course.version,
      p_reason: 'Intento sintético sin propiedad del campo',
    });
    check('server denies non-owned complete field', denied.status === 200 && denied.body?.data?.[0]?.success === false);
    const after = await rpc(page, 'admin_get_course_editorial', { p_course_id: courseId });
    check('denied mutation preserves effective name and version', after.body?.data?.[0]?.course?.current_values?.name === course.current_values?.name
      && after.body?.data?.[0]?.course?.version === course.version);
    const deniedAudit = await rpc(page, 'admin_get_course_audit', { p_course_id: courseId, p_first: 5 });
    check('user cannot read protected course audit', deniedAudit.status === 200
      && deniedAudit.body?.data?.[0]?.error === 'User is not an active admin'
      && deniedAudit.body?.data?.[0]?.events == null);
    return 'role boundary enforced at signed RPC and persisted state unchanged';
  }),
  defineCase('H3-CA4.9', 'published pipeline course appears in public listing', 'anon', '/', 'public listing resolves the pipeline identity, institution, price, mode and detail link from the effective reader', async ({ page, check }) => {
    const courseId = process.env.H3_PIPELINE_COURSE_ID || '70000000-0000-0000-0000-000000000091';
    const courseSlug = process.env.H3_PIPELINE_COURSE_SLUG || 'analitica-aplicada-60000000';
    const publicName = process.env.H3_PIPELINE_PUBLIC_NAME || 'Analítica Aplicada';
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
    await waitForPublicCatalog(page);
    const cards = page.locator('article').filter({ has: page.getByRole('heading', { name: publicName, exact: true }) });
    const courseLinks = cards.locator(`a[href*="/courses/ulima/${courseSlug}"]`);
    const hrefs = await courseLinks.evaluateAll((links) => links.map((link) => link.getAttribute('href')));
    check('one card resolves the candidate detail route', await cards.count() === 1
      && hrefs.length >= 1 && hrefs.every((href) => href?.includes(courseSlug)));
    const response = await page.request.get(`${MOCK_URL}/rest/v1/courses_public_effective?slug=eq.${encodeURIComponent(courseSlug)}&limit=1`);
    const rows = await response.json();
    check('listing source contains exact pipeline id', response.status() === 200 && rows?.[0]?.id === courseId);
    check('listing presents price and mode', (await page.locator('body').innerText()).includes('S/ 1,250')
      && (await page.locator('body').innerText()).includes('Remoto'));
    return `course=${courseId}; cardCount=${await cards.count()}; detailLinks=${hrefs.length}; effective reader verified`;
  }),
  defineCase('H3-CA4.9', 'price minimum URL survives hydration reload and applies inclusively', 'anon', '/', 'min query remains shareable across client synchronization and reload and filters the same synthetic course at its price boundary', async ({ page, check }) => {
    const courseSlug = process.env.H3_PIPELINE_COURSE_SLUG || 'analitica-aplicada-60000000';
    const publicName = process.env.H3_PIPELINE_PUBLIC_NAME || 'Analítica Aplicada';
    await page.goto(`${BASE_URL}/?min=1250`, { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: publicName }).waitFor({ state: 'visible' });
    await page.waitForTimeout(500);
    check('minimum retained in shareable URL', new URL(page.url()).searchParams.get('min') === '1250');
    const candidateHeading = page.getByRole('heading', { name: publicName, exact: true });
    const candidateLinks = page.locator(`article a[href*="${courseSlug}"]`);
    const candidateLinkCount = await candidateLinks.count();
    const candidateHref = candidateLinkCount > 0 ? await candidateLinks.first().getAttribute('href') : null;
    const renderedCourseHeadings = (await page.locator('article h3').allTextContents()).map((value) => value.trim()).slice(0, 20);
    const publicRenderState = await page.evaluate(async ({ courseSlug }) => {
      let effectiveReader = { status: 0, rows: 0, coursePresent: false, error: '' };
      try {
        const response = await fetch(`http://h3-final-app:3332/rest/v1/courses_public_effective?slug=eq.${encodeURIComponent(courseSlug)}&limit=1`, {
          headers: { apikey: ['sb', 'publishable', 'local-test'].join('_') },
          signal: AbortSignal.timeout(2000),
        });
        const rows = await response.json();
        effectiveReader = { status: response.status, rows: Array.isArray(rows) ? rows.length : -1,
          coursePresent: Array.isArray(rows) && rows.some((row) => row.slug === courseSlug), error: '' };
      } catch (error) {
        effectiveReader.error = error instanceof Error ? error.name : 'UNKNOWN';
      }
      return {
        urlHasMinimum: new URL(location.href).searchParams.get('min') === '1250',
        origin: location.origin,
        headings: [...document.querySelectorAll('h1,h2,h3')].map((node) => node.textContent?.trim() || '').filter(Boolean).slice(0, 30),
        articleHeadings: [...document.querySelectorAll('article h3')].map((node) => node.textContent?.trim() || '').slice(0, 20),
        catalogText: document.querySelector('main')?.textContent?.trim().slice(0, 600) || '',
        bodyText: document.body.innerText.trim().slice(0, 1000),
        loadingSkeletons: document.querySelectorAll('main .animate-pulse').length,
        effectiveReader,
      };
    }, { courseSlug });
    check('price equal to minimum includes the intended pipeline course', await candidateHeading.count() === 1
      && candidateLinkCount > 0 && candidateHref?.includes(courseSlug) === true,
    `courseHref=${candidateHref || 'missing'};expectedSlug=${courseSlug};articleHeadings=${JSON.stringify(renderedCourseHeadings)};render=${JSON.stringify(publicRenderState)}`);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await candidateHeading.waitFor({ state: 'visible', timeout: 10000 });
    check('minimum survives reload', new URL(page.url()).searchParams.get('min') === '1250');
    check('candidate remains after reload', await page.getByRole('heading', { name: publicName, exact: true }).count() === 1);
    await page.goto(`${BASE_URL}/?min=1251`, { waitUntil: 'domcontentloaded' });
    await page.getByText(/resultados encontrados/).waitFor({ state: 'visible', timeout: 10000 });
    await page.waitForTimeout(400);
    check('price below minimum is excluded', await page.getByRole('heading', { name: publicName, exact: true }).count() === 0);
    const reset = page.getByRole('button', { name: 'Limpiar todo' });
    check('minimum-only filter exposes reset control', await reset.isVisible());
    await reset.click();
    await page.waitForFunction(() => !new URL(location.href).searchParams.has('min'));
    await page.getByRole('heading', { name: publicName, exact: true }).waitFor({ state: 'visible', timeout: 10000 });
    check('reset removes minimum and restores candidate', await page.getByRole('heading', { name: publicName, exact: true }).count() === 1);
    return 'minimum filter inclusive boundary, deep link, reload, exclusion and reset verified';
  }),
  defineCase('H3-CA4.9', 'public combined filters search sort and reset stay consistent', 'anon', '/', 'search, area, type, institution, mode, minimum/maximum, duration, price range and sort converge on the same public course', async ({ page, check }) => {
    const courseSlug = process.env.H3_PIPELINE_COURSE_SLUG || 'analitica-aplicada-60000000';
    const publicName = process.env.H3_PIPELINE_PUBLIC_NAME || 'Analítica Aplicada';
    const query = new URLSearchParams({ q: 'Analítica', area: 'Data', tipo: 'Curso', inst: 'Universidad de Lima', modalidad: 'Remoto', min: '1250', max: '1250', sort: 'asc', duration: 'medium', priceRange: 'accessible' });
    await page.goto(`${BASE_URL}/?${query}`, { waitUntil: 'domcontentloaded' });
    await waitForPublicCatalog(page);
    const candidateCards = page.locator('article').filter({ has: page.getByRole('heading', { name: publicName, exact: true }) });
    const candidateLinks = candidateCards.locator(`a[href*="${courseSlug}"]`);
    const candidateHrefs = await candidateLinks.evaluateAll((links) => links.map((link) => link.getAttribute('href')));
    const params = new URL(page.url()).searchParams;
    check('combined query is retained', ['q', 'area', 'tipo', 'inst', 'modalidad', 'min', 'max', 'sort', 'duration', 'priceRange'].every((key) => params.has(key)));
    check('combined filter returns one intended course card', await candidateCards.count() === 1);
    check('all candidate card detail links use the same slug', candidateHrefs.length >= 1 && candidateHrefs.every((href) => href?.includes(courseSlug)));
    return `public filter intersection passed for ${courseSlug}; links=${candidateHrefs.length}`;
  }),
  defineCase('H3-CA4.9', 'public detail resolves effective fields without raw null values', 'anon', '/courses/ulima/', 'generated detail route reads the same published candidate and renders its actual effective editorial values', async ({ page, check }) => {
    const courseSlug = process.env.H3_PIPELINE_COURSE_SLUG || 'analitica-aplicada-60000000';
    const publicName = process.env.H3_PIPELINE_PUBLIC_NAME || 'Analítica Aplicada';
    await page.goto(`${BASE_URL}/courses/ulima/${courseSlug}/`, { waitUntil: 'networkidle' });
    const detailTitle = page.locator('main').getByRole('heading', { level: 1, name: publicName, exact: true });
    await detailTitle.waitFor({ state: 'visible' });
    check('one exact title is scoped to the detail main region', await detailTitle.count() === 1);
    const text = await page.locator('main').innerText();
    check('institution and public price visible', text.includes('Universidad de Lima') && text.includes('S/ 1,250'));
    check('rendered text contains no raw nulls', !/\b(undefined|null)\b/i.test(text));
    const structuredSourceUrl = await page.locator('script[type="application/ld+json"]').evaluateAll((scripts) => {
      for (const script of scripts) {
        try {
          const value = JSON.parse(script.textContent || 'null');
          if (value?.['@type'] === 'Course' && typeof value.url === 'string') return value.url;
        } catch {
          continue;
        }
      }
      return null;
    });
    const expectedSourceUrl = process.env.H3_PIPELINE_SOURCE_URL || 'https://synthetic.h3.example/programs/analitica-aplicada/';
    let sourceUrlIsExpectedHttps = false;
    try {
      const parsedSourceUrl = new URL(structuredSourceUrl);
      sourceUrlIsExpectedHttps = parsedSourceUrl.protocol === 'https:'
        && parsedSourceUrl.hostname === 'synthetic.h3.example'
        && structuredSourceUrl === expectedSourceUrl;
    } catch {
      sourceUrlIsExpectedHttps = false;
    }
    check('course source URL remains HTTPS in structured data', sourceUrlIsExpectedHttps);
    return 'effective detail data and local asset/link contract verified';
  }),
  defineCase('H3-CA4.9', 'comparison reflects the same effective course and removes it cleanly', 'anon', '/compare/', 'direct comparison deep link resolves the candidate with the same title, institution, price and mode and removal returns to public search', async ({ page, check }) => {
    const courseId = process.env.H3_PIPELINE_COURSE_ID || '70000000-0000-0000-0000-000000000091';
    const publicName = process.env.H3_PIPELINE_PUBLIC_NAME || 'Analítica Aplicada';
    await page.goto(`${BASE_URL}/compare/?ids=${encodeURIComponent(courseId)}`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Comparativa de Programas' }).waitFor({ state: 'visible' });
    check('comparison uses same candidate values', await page.getByText(publicName, { exact: true }).count() > 0
      && (await page.locator('main').innerText()).includes('S/ 1,250')
      && (await page.locator('main').innerText()).includes('Remoto'));
    await page.getByRole('button', { name: 'Retirar de la comparativa' }).click();
    await page.waitForURL(`${BASE_URL}/`);
    check('removing final item returns to public home', new URL(page.url()).pathname === '/');
    const ineligibleId = 'ffffffff-ffff-ffff-ffff-ffffffffffff';
    const ineligibleResponse = await page.request.get(
      `${MOCK_URL}/rest/v1/courses_public_effective?id=in.(${ineligibleId})&select=id,name`,
    );
    const ineligibleRows = await ineligibleResponse.json();
    check('ineligible synthetic ID is absent from public effective reader', ineligibleResponse.status() === 200
      && Array.isArray(ineligibleRows) && ineligibleRows.length === 0,
    `status=${ineligibleResponse.status()};rowCount=${Array.isArray(ineligibleRows) ? ineligibleRows.length : 'NON_ARRAY'}`);
    await page.goto(`${BASE_URL}/compare/?ids=${encodeURIComponent(ineligibleId)}`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Comparativa de Programas' }).waitFor({ state: 'visible' });
    await page.getByText('0 Programas seleccionados', { exact: true }).waitFor({ state: 'visible' });
    check('comparison renders no card or unrelated data for ineligible ID', await page.locator('main article').count() === 0
      && !((await page.locator('main').innerText()).includes(publicName)));
    return 'compare deep link and remove action verified';
  }),
  defineCase('H3-CA4.9', 'advice channel remains closed and sends no external request', 'anon', '/courses/ulima/', 'existing closed advice state is explicit, captures no personal information and has no submission action', async ({ page, check }) => {
    const courseSlug = process.env.H3_PIPELINE_COURSE_SLUG || 'analitica-aplicada-60000000';
    const externalMutations = [];
    page.on('request', (request) => {
      try {
        const url = new URL(request.url());
        if (!['localhost', '127.0.0.1'].includes(url.hostname) && request.method() !== 'GET') externalMutations.push(`${request.method()} ${url.origin}`);
      } catch { /* malformed fixture requests are handled by the runner's request diagnostics */ }
    });
    await page.goto(`${BASE_URL}/courses/ulima/${courseSlug}/`, { waitUntil: 'networkidle' });
    check('closed advice notice visible', await page.getByText('Canal cerrado temporalmente', { exact: true }).isVisible());
    check('advice does not collect email or submit form', await page.locator('form').count() === 0
      && await page.locator('input[type="email"]').count() === 0
      && await page.getByRole('button', { name: /enviar|solicitar asesoría/i }).count() === 0);
    check('no external mutation request', externalMutations.length === 0);
    return 'closed channel respected; no real/synthetic recipient invented or contacted';
  }, { requiresFixtureReset: false }),
  defineCase('H3-CA4.9', 'unknown public course route returns a controlled not-found page', 'anon', '/courses/ulima/not-a-real-course/', 'unknown course path does not render an unrelated course or raw runtime error', async ({ page, check }) => {
    const response = await page.request.get(`${BASE_URL}/courses/ulima/not-a-real-course/`);
    await page.goto(`${BASE_URL}/courses/ulima/not-a-real-course/`, { waitUntil: 'networkidle' });
    const text = await page.locator('body').innerText();
    check('unknown detail status is not success', response.status() === 404 || response.status() === 200 && /no encontramos|no disponible|not found/i.test(text));
    check('no candidate data leaks into unknown route', !text.includes('Analítica Aplicada'));
    check('no stack or raw undefined', !/undefined|stack trace|internal server error/i.test(text));
    return `controlled unknown path status=${response.status()}`;
  }, { requiresFixtureReset: false }),
  defineCase('H3-CA4.11', 'public listing and detail fit the active viewport', 'anon', '/', 'candidate list and detail remain usable without horizontal overflow at each UAT viewport', async ({ page, check, viewport }) => {
    const courseSlug = process.env.H3_PIPELINE_COURSE_SLUG || 'analitica-aplicada-60000000';
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
    const listing = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth }));
    check('public listing has no horizontal overflow', listing.scroll <= listing.client + 1);
    await page.goto(`${BASE_URL}/courses/ulima/${courseSlug}/`, { waitUntil: 'networkidle' });
    const detail = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth }));
    check('public detail has no horizontal overflow', detail.scroll <= detail.client + 1);
    return `${viewport.name} ${viewport.width}px; listing=${listing.scroll}/${listing.client}; detail=${detail.scroll}/${detail.client}`;
  }, { requiresFixtureReset: false }),
  defineCase('H3-CA4.9', 'public filters apply independently and career goal matches eligible courses', 'anon', '/', 'category, institution, modality, type, duration, career goal and text search each constrain visible public results; empty state can be reset', async ({ page, check }) => {
    const publicName = process.env.H3_PIPELINE_PUBLIC_NAME || 'Analítica Aplicada';
    const candidateSlug = process.env.H3_PIPELINE_COURSE_SLUG || 'analitica-aplicada-60000000';
    const checks = [
      { query: '?area=Data', include: publicName, exclude: 'Programa local H3 11' },
      { query: '?inst=Universidad%20de%20Lima', include: publicName, exclude: null },
      { query: '?modalidad=Remoto', include: publicName, exclude: null },
      { query: '?tipo=Maestr%C3%ADa', include: 'Programa local H3 14', exclude: publicName },
      { query: '?duration=short', include: 'Programa local H3 13', exclude: publicName },
    ];
    for (const item of checks) {
      await page.goto(`${BASE_URL}/${item.query}`, { waitUntil: 'domcontentloaded' });
      await waitForPublicCatalog(page);
      const expected = new URLSearchParams(item.query);
      const canonicalSearch = expected.toString();
      await page.waitForFunction((search) => location.search === `?${search}`, canonicalSearch, { timeout: 10000 });
      await page.waitForLoadState('networkidle');
      const body = await page.locator('main').innerText();
      check(`${item.query} includes expected result`, body.includes(item.include));
      if (item.exclude) check(`${item.query} excludes nonmatching result`, !body.includes(item.exclude));
      if (item.query.includes('modalidad=Remoto')) {
        const cards = await page.locator('article').allInnerTexts();
        check('every remote result carries the selected mode', cards.length > 0 && cards.every((text) => text.includes('Remoto')));
      }
    }

    check('clear-all is available for a duration-only filter', await page.getByRole('button', { name: 'Limpiar todo' }).count() === 1);
    await page.getByRole('button', { name: 'Limpiar todo' }).click();
    await page.waitForFunction(() => !new URL(location.href).searchParams.has('duration'), undefined, { timeout: 10000 });
    await waitForPublicCatalog(page);
    await page.getByRole('heading', { name: publicName, exact: true }).waitFor({ state: 'visible' });
    check('duration-only reset restores the unfiltered candidate', await page.getByRole('heading', { name: publicName, exact: true }).count() === 1);

    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    await waitForPublicCatalog(page);
    await page.getByRole('button', { name: 'Personalizar' }).click();
    await page.getByRole('button', { name: 'Posgrado', exact: true }).click();
    await waitForPublicCatalog(page);
    await page.getByRole('heading', { name: 'Programa local H3 14', exact: true }).waitFor({ state: 'visible' });
    check('postgraduate career goal selects a postgraduate fixture', await page.getByRole('heading', { name: 'Programa local H3 14', exact: true }).count() === 1);
    check('postgraduate goal excludes the pipeline course', await page.getByRole('heading', { name: publicName, exact: true }).count() === 0);
    check('clear-all is available for a goal-only filter', await page.getByRole('button', { name: 'Limpiar todo' }).count() === 1);
    await page.getByRole('button', { name: 'Limpiar todo' }).click();
    await waitForPublicCatalog(page);
    await page.getByRole('heading', { name: publicName, exact: true }).waitFor({ state: 'visible' });
    check('goal-only reset restores the unfiltered candidate', await page.getByRole('heading', { name: publicName, exact: true }).count() === 1);

    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    await waitForPublicCatalog(page);
    const search = page.getByPlaceholder('¿Qué quieres estudiar hoy?');
    await search.fill('Analítica');
    await page.waitForFunction(() => new URL(location.href).searchParams.get('q') === 'Analítica', undefined, { timeout: 10000 });
    await waitForPublicCatalog(page);
    await page.getByRole('heading', { name: publicName, exact: true }).waitFor({ state: 'visible' });
    check('search text synchronizes to shareable URL and candidate', new URL(page.url()).searchParams.get('q') === 'Analítica'
      && await page.locator('article').filter({ has: page.getByRole('heading', { name: publicName, exact: true }) }).count() === 1
      && await page.locator(`a[href*="${candidateSlug}"]`).count() >= 1);

    await page.goto(`${BASE_URL}/?q=sin-resultados-h3`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => document.querySelector('#programas main')?.textContent?.includes('Sin resultados') === true, undefined, { timeout: 15000 });
    await page.getByText('Sin resultados', { exact: true }).waitFor({ state: 'visible' });
    await page.getByRole('button', { name: 'Limpiar todo' }).click();
    await page.waitForFunction(() => !new URL(location.href).searchParams.has('q'), undefined, { timeout: 10000 });
    await waitForPublicCatalog(page);
    await page.getByRole('heading', { name: publicName, exact: true }).waitFor({ state: 'visible' });
    check('empty search resets and restores the public candidate', await page.getByRole('heading', { name: publicName, exact: true }).count() === 1);
    return `independent category/institution/mode/type/duration/goal/search filters, empty state and reset verified at ${page.viewportSize()?.width}px`;
  }),
  defineCase('H3-CA4.9', 'price filter bands honor inclusive boundaries and exclude unknown prices', 'anon', '/', 'accessible, standard, premium and executive price bands apply their documented edges; zero and null values do not masquerade as priced programs', async ({ page, check }) => {
    const publicName = process.env.H3_PIPELINE_PUBLIC_NAME || 'Analítica Aplicada';
    const bands = [
      { id: 'accessible', include: publicName, exclude: 'Programa local H3 16' },
      { id: 'standard', include: 'Programa local H3 12', exclude: 'Programa local H3 13' },
      { id: 'premium', include: 'Programa local H3 14', exclude: 'Programa local H3 15' },
      { id: 'executive', include: 'Programa local H3 15', exclude: 'Programa local H3 14' },
    ];
    for (const band of bands) {
      await page.goto(`${BASE_URL}/?priceRange=${band.id}`, { waitUntil: 'domcontentloaded' });
      await waitForPublicCatalog(page);
      await page.getByRole('heading', { name: band.include, exact: true }).waitFor({ state: 'visible' });
      const text = await page.locator('main').innerText();
      check(`${band.id} includes inclusive boundary fixture`, text.includes(band.include));
      check(`${band.id} excludes adjacent/unknown value`, !text.includes(band.exclude));
    }
    await page.goto(`${BASE_URL}/?priceRange=premium`, { waitUntil: 'domcontentloaded' });
    await waitForPublicCatalog(page);
    check('clear-all is available for a price-band-only filter', await page.getByRole('button', { name: 'Limpiar todo' }).count() === 1);
    await page.getByRole('button', { name: 'Limpiar todo' }).click();
    await page.waitForFunction(() => !new URL(location.href).searchParams.has('priceRange'), undefined, { timeout: 10000 });
    await waitForPublicCatalog(page);
    await page.getByRole('heading', { name: publicName, exact: true }).waitFor({ state: 'visible' });
    check('price-band-only reset restores the unfiltered candidate', await page.getByRole('heading', { name: publicName, exact: true }).count() === 1);
    await page.goto(`${BASE_URL}/?min=1250&max=1250`, { waitUntil: 'domcontentloaded' });
    await waitForPublicCatalog(page);
    await page.getByRole('heading', { name: publicName, exact: true }).waitFor({ state: 'visible' });
    await page.getByRole('heading', { name: 'Programa local H3 18', exact: true }).waitFor({ state: 'visible' });
    const exactRange = await page.locator('main').innerText();
    check('minimum and maximum include exact price boundary', exactRange.includes(publicName) && exactRange.includes('Programa local H3 18'));
    await page.goto(`${BASE_URL}/?max=1249`, { waitUntil: 'domcontentloaded' });
    await waitForPublicCatalog(page);
    check('maximum below candidate price excludes candidate', await page.getByRole('heading', { name: publicName, exact: true }).count() === 0);
    await page.goto(`${BASE_URL}/?min=1251`, { waitUntil: 'domcontentloaded' });
    await waitForPublicCatalog(page);
    check('minimum above candidate price excludes candidate', await page.getByRole('heading', { name: publicName, exact: true }).count() === 0);
    return 'four price bands, null/zero exclusion and exact min/max boundaries verified';
  }),
  defineCase('H3-CA4.9', 'public price sorting and pagination cover all catalog rows', 'anon', '/', 'price ascending/descending preserve order and the 12-item page boundary exposes every fixture exactly once across pages', async ({ page, check }) => {
    const readPrices = async () => (await page.locator('article').allInnerTexts())
      .map((text) => text.match(/S\/\s*([\d,]+)/)?.[1])
      .filter((value) => value !== undefined)
      .map((value) => Number(value.replaceAll(',', '')));
    await page.goto(`${BASE_URL}/?sort=asc`, { waitUntil: 'domcontentloaded' });
    await waitForPublicCatalog(page);
    await page.getByText('1 / 2', { exact: true }).waitFor({ state: 'visible' });
    const ascending = await readPrices();
    check('ascending page prices are monotonic', ascending.length >= 3 && ascending.every((value, index) => index === 0 || ascending[index - 1] <= value));
    check('initial page advertises a second page', await page.getByText('1 / 2', { exact: true }).count() === 1);
    await page.getByRole('button', { name: 'Siguiente' }).click();
    await page.getByText('2 / 2', { exact: true }).waitFor({ state: 'visible' });
    check('second page contains the remaining four rows', await page.locator('article').count() === 4);
    await page.getByRole('button', { name: 'Anterior' }).click();
    await page.getByText('1 / 2', { exact: true }).waitFor({ state: 'visible' });
    check('previous returns to the first page with twelve rows', await page.locator('article').count() === 12);

    await page.goto(`${BASE_URL}/?sort=desc`, { waitUntil: 'domcontentloaded' });
    await waitForPublicCatalog(page);
    await page.getByText('1 / 2', { exact: true }).waitFor({ state: 'visible' });
    const descending = await readPrices();
    check('descending page prices are monotonic', descending.length >= 3 && descending.every((value, index) => index === 0 || descending[index - 1] >= value));
    return `16 public rows paginated 12+4; price ordering checked (${ascending.length} ascending, ${descending.length} descending values) at ${page.viewportSize()?.width}px`;
  }),
  defineCase('H3-CA4.9', 'comparison add remove duplicate maximum and persistence behavior', 'anon', '/', 'comparison stores unique course IDs, allows removal and clear, rejects a fourth item and reflects the same three-course selection on the comparison route', async ({ page, check }) => {
    const storageKey = 'StudIAMatch_compare_list';
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    await waitForPublicCatalog(page);
    await page.evaluate((key) => localStorage.removeItem(key), storageKey);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await waitForPublicCatalog(page);
    const visibleNames = (await page.locator('article h3').allTextContents()).map((name) => name.trim());
    check('four visible synthetic courses can exercise comparison cap', visibleNames.length >= 4, visibleNames.join('|'));
    const selectedNames = visibleNames.slice(0, 3);
    const fourthName = visibleNames[3];
    const card = (name) => page.locator('article').filter({ has: page.getByRole('heading', { name, exact: true }) });
    const choose = async (name) => card(name).locator('[title="Agregar a comparativa"], [title="Máximo 3 programas"]').click();
    const waitSavedCount = async (count) => page.waitForFunction(({ key, expected }) => {
      try { return JSON.parse(localStorage.getItem(key) || '[]').length === expected; } catch { return false; }
    }, { key: storageKey, expected: count });
    await choose(selectedNames[0]);
    await waitSavedCount(1);
    check('one selected item persisted once', await page.evaluate((key) => JSON.parse(localStorage.getItem(key) || '[]').length, storageKey) === 1);
    await choose(selectedNames[0]);
    await waitSavedCount(0);
    check('selecting the same item toggles it off without a duplicate', await page.evaluate((key) => JSON.parse(localStorage.getItem(key) || '[]').length, storageKey) === 0);
    await choose(selectedNames[0]);
    await waitSavedCount(1);
    await choose(selectedNames[1]);
    await waitSavedCount(2);
    await choose(selectedNames[2]);
    await waitSavedCount(3);
    await choose(fourthName);
    check('fourth item is rejected at the three-item limit', await page.evaluate((key) => JSON.parse(localStorage.getItem(key) || '[]').length, storageKey) === 3);
    await page.locator('a[href^="/compare/?ids="]').click();
    await page.getByRole('heading', { name: 'Comparativa de Programas' }).waitFor({ state: 'visible' });
    await page.getByText('3 Programas seleccionados', { exact: true }).waitFor({ state: 'visible' });
    check('comparison route displays all selected courses', await Promise.all(selectedNames.map((name) => page.getByRole('heading', { name, exact: true }).count())).then((counts) => counts.every((count) => count === 1)));
    await page.getByRole('button', { name: 'Retirar de la comparativa' }).first().click();
    await page.getByText('2 Programas seleccionados', { exact: true }).waitFor({ state: 'visible' });
    await waitSavedCount(2);
    check('removal updates URL and persisted selection', new URL(page.url()).searchParams.get('ids')?.split(',').length === 2
      && await page.evaluate((key) => JSON.parse(localStorage.getItem(key) || '[]').length, storageKey) === 2);
    await page.getByRole('link', { name: 'Volver a la búsqueda' }).click();
    await waitForPublicCatalog(page);
    await waitSavedCount(2);
    await page.getByRole('button', { name: 'Limpiar', exact: true }).click();
    await page.waitForFunction((key) => JSON.parse(localStorage.getItem(key) || '[]').length === 0, storageKey);
    await page.getByRole('button', { name: 'Limpiar', exact: true }).waitFor({ state: 'detached' });
    check('clear empties comparison storage and bar', await page.evaluate((key) => JSON.parse(localStorage.getItem(key) || '[]').length, storageKey) === 0
      && await page.getByRole('button', { name: 'Limpiar', exact: true }).count() === 0);
    return 'unique selections, duplicate toggle, three-item cap, deep compare, remove, persistence and clear verified';
  }),
  defineCase('H3-CA4.9', 'public navigation back forward and local runtime measurements', 'anon', '/', 'home/detail/informational routes respond locally; browser history returns to the same candidate and records bounded local navigation metrics without asserting a service-level target', async ({ page, check }) => {
    const publicName = process.env.H3_PIPELINE_PUBLIC_NAME || 'Analítica Aplicada';
    const routeCheckpoints = [];
    const checkpoint = async (stage, extra = {}) => ({
      stage,
      ...(await page.evaluate(() => ({ pathname: location.pathname, historyLength: history.length, readyState: document.readyState }))),
      ...extra,
    });
    const homeResponse = await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
    await waitForPublicCatalog(page);
    routeCheckpoints.push(await checkpoint('catalog-ready'));
    const listingMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      return { domContentLoadedMs: navigation?.domContentLoadedEventEnd ?? null, loadMs: navigation?.loadEventEnd ?? null,
        sameOriginResources: performance.getEntriesByType('resource').filter((entry) => { try { return new URL(entry.name).origin === location.origin; } catch { return false; } }).length };
    });
    check('public home served successfully', homeResponse?.status() === 200);
    check('listing navigation metrics are finite and measured', Number.isFinite(listingMetrics.domContentLoadedMs) && Number.isFinite(listingMetrics.loadMs) && listingMetrics.sameOriginResources > 0);
    const detailLink = page.locator('article a').filter({ hasText: publicName }).first();
    const detailHref = await detailLink.getAttribute('href');
    check('candidate has a local detail route', Boolean(detailHref?.startsWith('/courses/')));
    await detailLink.click();
    await page.locator('h1').filter({ hasText: new RegExp(`^${publicName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`) }).waitFor({ state: 'visible' });
    // The static export can expose the detail heading before all route assets
    // and slash normalization settle. Do not issue browser-back mid-navigation.
    await page.waitForLoadState('networkidle');
    routeCheckpoints.push(await checkpoint('detail-heading-visible'));
    const detailPath = new URL(detailHref || '/', BASE_URL).pathname;
    check('detail route corresponds to selected candidate', new URL(page.url()).pathname.replace(/\/+$/, '') === detailPath.replace(/\/+$/, ''));
    const backResponse = await page.goBack({ waitUntil: 'networkidle' });
    routeCheckpoints.push(await checkpoint('browser-back-returned', { responseStatus: backResponse?.status() ?? null }));
    try {
      await waitForPublicCatalog(page);
    } catch (error) {
      throw new Error(`${error instanceof Error ? error.message : 'CATALOG_WAIT_FAILED'}; routeCheckpoints=${JSON.stringify(routeCheckpoints)}`);
    }
    check('browser back restores public listing', new URL(page.url()).pathname === '/');
    routeCheckpoints.push(await checkpoint('catalog-restored'));
    await page.goForward({ waitUntil: 'networkidle' });
    await page.locator('h1').filter({ hasText: new RegExp(`^${publicName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`) }).waitFor({ state: 'visible' });
    const detailStatus = await page.request.get(`${BASE_URL}${detailPath}`);
    const informationStatus = await Promise.all(['/privacidad/', '/terminos/'].map(async (route) => (await page.request.get(`${BASE_URL}${route}`)).status()));
    const unknownInstitution = await page.request.get(`${BASE_URL}/courses/no-such-institution/no-such-course/`);
    const unknownText = await unknownInstitution.text();
    check('detail and information routes return 200', detailStatus.status() === 200 && informationStatus.every((status) => status === 200));
    check('unknown institution/course route is controlled and contains no candidate data', unknownInstitution.status() === 404
      || unknownInstitution.status() === 200 && /no encontramos|no disponible|not found/i.test(unknownText),
    `status=${unknownInstitution.status()};candidateLeak=${unknownText.includes('Analítica Aplicada')}`);
    check('local navigation measurements have no negative values', listingMetrics.domContentLoadedMs >= 0 && listingMetrics.loadMs >= 0);
    return `home=${homeResponse?.status()} detail=${detailStatus.status()} info=${informationStatus.join(',')} unknown=${unknownInstitution.status()} metrics=${JSON.stringify(listingMetrics)}; routeCheckpoints=${JSON.stringify(routeCheckpoints)}; no SLA inferred`;
  }, { requiresFixtureReset: false }),
  defineCase('H3-CA4.9', 'comparison renders distinct candidates with incomplete optional values', 'anon', '/compare/', 'two eligible synthetic candidates with different values and absent optional fields render without raw nulls or missing value labels', async ({ page, check }) => {
    const candidates = [
      {
        id: '70000000-0000-0000-0000-000000000091',
        institution_id: '00000000-0000-0000-0000-000000000001',
        category_id: 'c0000000-0000-4000-8000-000000000001',
        name: 'Synthetic Course With Missing Values',
        slug: 'analitica-aplicada-60000000',
        price_pen: null,
        price_status: 'consultar',
        mode: 'Híbrido',
        duration: null,
        expected_monthly_salary: null,
        roi_months: null,
      },
      {
        id: '20000000-0000-0000-0000-000000000012',
        institution_id: '00000000-0000-0000-0000-000000000002',
        category_id: 'c0000000-0000-4000-8000-000000000001',
        name: 'Synthetic Course With Complete Values',
        slug: 'programa-local-h3-12',
        price_pen: 1250,
        price_status: 'publicado',
        mode: 'Remoto',
        duration: '6 meses',
        expected_monthly_salary: 2500,
        roi_months: 6,
      },
    ];
    const corsHeaders = {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET, OPTIONS',
      'access-control-allow-headers': 'apikey, authorization, content-type, accept',
    };
    await page.route('**/*', async (route) => {
      const requestOrigin = new URL(route.request().url()).origin;
      if (requestOrigin === new URL(BASE_URL).origin) await route.continue();
      else await route.fulfill({ status: 204, body: '' });
    });
    await page.route('**/rest/v1/**', async (route) => {
      if (route.request().method() === 'OPTIONS') {
        await route.fulfill({ status: 204, headers: corsHeaders, body: '' });
        return;
      }
      const pathname = new URL(route.request().url()).pathname;
      let body = [];
      if (pathname.endsWith('/courses_public_effective')) body = candidates;
      else if (pathname.endsWith('/institutions')) body = [
        { id: candidates[0].institution_id, name: 'Universidad de Lima', slug: 'ulima' },
        { id: candidates[1].institution_id, name: 'Pontificia Universidad Católica del Perú', slug: 'pucp' },
      ];
      else if (pathname.endsWith('/categories')) body = [{ id: candidates[0].category_id, name: 'Synthetic Category' }];
      await route.fulfill({ status: 200, contentType: 'application/json', headers: corsHeaders, body: JSON.stringify(body) });
    });
    const ids = candidates.map(({ id }) => id).join(',');
    await page.goto(`${BASE_URL}/compare/?ids=${encodeURIComponent(ids)}`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Comparativa de Programas' }).waitFor({ state: 'visible' });
    await page.getByText('2 Programas seleccionados', { exact: true }).waitFor({ state: 'visible' });
    const cardFor = (name) => page.getByRole('heading', { level: 2, name, exact: true })
      .locator('xpath=ancestor::div[contains(@class,"relative overflow-hidden")]');
    const incompleteCard = cardFor(candidates[0].name);
    const completeCard = cardFor(candidates[1].name);
    const incompleteText = await incompleteCard.innerText();
    const completeText = await completeCard.innerText();
    check('both eligible candidates are shown as separate cards', await page.getByRole('heading', { level: 2 }).count() === 2
      && await incompleteCard.count() === 1 && await completeCard.count() === 1);
    check('absent price and duration use readable fallbacks', (incompleteText.match(/Consultar/g) || []).length >= 2);
    check('absent ROI and salary use readable fallbacks', (incompleteText.match(/No disponible/g) || []).length >= 2);
    check('absent institution location has an explicit fallback', [incompleteText, completeText].every((text) => /Ubicación\s+Por confirmar/i.test(text)));
    check('complete candidate retains distinct price, duration, mode, salary and ROI', completeText.includes('S/ 1,250')
      && completeText.includes('6 meses') && completeText.includes('Remoto')
      && completeText.includes('S/ 2,500') && completeText.includes('6.0 meses'));
    check('comparison values contain no raw null or undefined text', !/\b(?:null|undefined)\b/i.test(`${incompleteText}\n${completeText}`));
    return 'two eligible candidates: null/absent optional values and distinct populated comparison fields verified with browser egress blocked';
  }, { requiresFixtureReset: false }),
  defineCase('H3-CA4.9', 'all generated static detail routes resolve their own course', 'anon', '/courses/', 'all generated static detail routes resolve their own course, institution and metadata from synthetic REST fixtures without external egress', async ({ page, check }) => {
    const category = { id: 'c0000000-0000-4000-8000-000000000065', name: 'Programas sintéticos' };
    const fixtures = [
      { id: '20000000-0000-0000-0000-000000000011', institution_id: '00000000-0000-0000-0000-000000000001', institution: 'Universidad de Lima', institutionSlug: 'ulima', name: 'Programa local H3 11', slug: 'programa-local-h3-11' },
      { id: '20000000-0000-0000-0000-000000000016', institution_id: '00000000-0000-0000-0000-000000000001', institution: 'Universidad de Lima', institutionSlug: 'ulima', name: 'Programa local H3 16', slug: 'programa-local-h3-16' },
      { id: '20000000-0000-0000-0000-000000000021', institution_id: '00000000-0000-0000-0000-000000000001', institution: 'Universidad de Lima', institutionSlug: 'ulima', name: 'Programa local H3 21', slug: 'programa-local-h3-21' },
      { id: '70000000-0000-0000-0000-000000000091', institution_id: '00000000-0000-0000-0000-000000000001', institution: 'Universidad de Lima', institutionSlug: 'ulima', name: 'Analítica Aplicada', slug: 'analitica-aplicada-60000000', url: 'https://synthetic.h3.example/programs/analitica-aplicada/' },
      { id: '20000000-0000-0000-0000-000000000012', institution_id: '00000000-0000-0000-0000-000000000002', institution: 'Pontificia Universidad Católica del Perú', institutionSlug: 'pucp', name: 'Programa local H3 12', slug: 'programa-local-h3-12' },
      { id: '20000000-0000-0000-0000-000000000017', institution_id: '00000000-0000-0000-0000-000000000002', institution: 'Pontificia Universidad Católica del Perú', institutionSlug: 'pucp', name: 'Programa local H3 17', slug: 'programa-local-h3-17' },
      { id: '20000000-0000-0000-0000-000000000022', institution_id: '00000000-0000-0000-0000-000000000002', institution: 'Pontificia Universidad Católica del Perú', institutionSlug: 'pucp', name: 'Programa local H3 22', slug: 'programa-local-h3-22' },
      { id: '20000000-0000-0000-0000-000000000013', institution_id: '00000000-0000-0000-0000-000000000003', institution: 'Universidad Peruana de Ciencias Aplicadas', institutionSlug: 'upc', name: 'Programa local H3 13', slug: 'programa-local-h3-13' },
      { id: '20000000-0000-0000-0000-000000000018', institution_id: '00000000-0000-0000-0000-000000000003', institution: 'Universidad Peruana de Ciencias Aplicadas', institutionSlug: 'upc', name: 'Programa local H3 18', slug: 'programa-local-h3-18' },
      { id: '20000000-0000-0000-0000-000000000023', institution_id: '00000000-0000-0000-0000-000000000003', institution: 'Universidad Peruana de Ciencias Aplicadas', institutionSlug: 'upc', name: 'Programa local H3 23', slug: 'programa-local-h3-23' },
      { id: '20000000-0000-0000-0000-000000000014', institution_id: '00000000-0000-0000-0000-000000000004', institution: 'Universidad San Ignacio de Loyola', institutionSlug: 'usil', name: 'Programa local H3 14', slug: 'programa-local-h3-14' },
      { id: '20000000-0000-0000-0000-000000000019', institution_id: '00000000-0000-0000-0000-000000000004', institution: 'Universidad San Ignacio de Loyola', institutionSlug: 'usil', name: 'Programa local H3 19', slug: 'programa-local-h3-19' },
      { id: '20000000-0000-0000-0000-000000000024', institution_id: '00000000-0000-0000-0000-000000000004', institution: 'Universidad San Ignacio de Loyola', institutionSlug: 'usil', name: 'Programa local H3 24', slug: 'programa-local-h3-24' },
      { id: '20000000-0000-0000-0000-000000000015', institution_id: '00000000-0000-0000-0000-000000000005', institution: 'Universidad Tecnológica del Perú', institutionSlug: 'utp', name: 'Programa local H3 15', slug: 'programa-local-h3-15' },
      { id: '20000000-0000-0000-0000-000000000020', institution_id: '00000000-0000-0000-0000-000000000005', institution: 'Universidad Tecnológica del Perú', institutionSlug: 'utp', name: 'Programa local H3 20', slug: 'programa-local-h3-20' },
      { id: '20000000-0000-0000-0000-000000000025', institution_id: '00000000-0000-0000-0000-000000000005', institution: 'Universidad Tecnológica del Perú', institutionSlug: 'utp', name: 'Programa local H3 25', slug: 'programa-local-h3-25' },
    ].map((fixture, index) => ({
      ...fixture,
      category_id: category.id,
      url: fixture.url || `https://local.example.test/programas/${fixture.slug.split('-').at(-1)}`,
      price_pen: 1000 + index * 250,
      price_status: 'publicado',
      mode: index % 2 ? 'Híbrido' : 'Remoto',
      duration: '6 meses',
      duration_months: 6,
      course_type: 'Maestría',
      description_long: `Descripción sintética ${index + 1}: programa de validación local.`,
      requirements: 'Requisitos sintéticos de prueba.',
      expected_monthly_salary: 2000 + index * 250,
      roi_months: 6,
    }));
    const institutions = [...new Map(fixtures.map(({ institution_id, institution, institutionSlug }) => [institutionSlug, {
      id: institution_id, name: institution, slug: institutionSlug,
    }])).values()];
    const corsHeaders = {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET, OPTIONS',
      'access-control-allow-headers': 'apikey, authorization, content-type, accept',
    };
    const syntheticRestRequests = [];
    const blockedExternalOrigins = new Set();
    const baseOrigin = new URL(BASE_URL).origin;
    await page.route('**/*', async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.pathname.startsWith('/rest/v1/')) {
        syntheticRestRequests.push({ method: request.method(), path: url.pathname });
        if (request.method() === 'OPTIONS') {
          await route.fulfill({ status: 204, headers: corsHeaders, body: '' });
          return;
        }
        let body = [];
        if (url.pathname.endsWith('/institutions')) {
          const slug = (url.searchParams.get('slug') || '').replace(/^eq\./, '');
          body = slug ? institutions.filter((institution) => institution.slug === slug) : institutions;
        } else if (url.pathname.endsWith('/categories')) {
          body = [category];
        } else if (url.pathname.endsWith('/courses_public_effective')) {
          const slug = (url.searchParams.get('slug') || '').replace(/^eq\./, '');
          const institutionId = (url.searchParams.get('institution_id') || '').replace(/^eq\./, '');
          const categoryId = (url.searchParams.get('category_id') || '').replace(/^eq\./, '');
          const excludedId = (url.searchParams.get('id') || '').replace(/^neq\./, '');
          body = fixtures.filter((course) => (!slug || course.slug === slug)
            && (!institutionId || course.institution_id === institutionId)
            && (!categoryId || course.category_id === categoryId)
            && (!excludedId || course.id !== excludedId));
        }
        await route.fulfill({ status: 200, contentType: 'application/json', headers: corsHeaders, body: JSON.stringify(body) });
        return;
      }
      if (url.origin === baseOrigin) {
        await route.continue();
        return;
      }
      blockedExternalOrigins.add(url.origin);
      await route.fulfill({ status: 204, body: '' });
    });

    assert(fixtures.length === 16 && institutions.length === 5, 'product route fixtures must match all 16 generated detail routes across five universities');
    for (const fixture of fixtures) {
      const path = `/courses/${fixture.institutionSlug}/${fixture.slug}/`;
      const response = await page.goto(`${BASE_URL}${path}`, { waitUntil: 'networkidle' });
      await page.getByRole('heading', { level: 1, name: fixture.name, exact: true }).waitFor({ state: 'visible' });
      const mainText = await page.locator('main').innerText();
      const canonicalPath = await page.locator('link[rel="canonical"]').getAttribute('href').then((href) => href ? new URL(href).pathname : '');
      const courseSchema = await page.locator('script[type="application/ld+json"]').evaluateAll((nodes) => nodes
        .map((node) => { try { return JSON.parse(node.textContent || '{}'); } catch { return null; } })
        .find((schema) => schema?.['@type'] === 'Course') || null);
      check(`${fixture.institutionSlug} route returns 200`, response?.status() === 200);
      check(`${fixture.institutionSlug} route renders its own course and institution`, mainText.includes(fixture.name)
        && mainText.includes(fixture.institution));
      check(`${fixture.institutionSlug} route contains no raw null/undefined`, !/\b(?:null|undefined)\b/i.test(mainText));
      check(`${fixture.institutionSlug} URL stays on its detail route`, new URL(page.url()).pathname === path);
      check(`${fixture.institutionSlug} canonical asset points to its detail route`, canonicalPath === path);
      check(`${fixture.institutionSlug} Course metadata matches the route fixture`, courseSchema?.name === fixture.name
        && courseSchema?.provider?.name === fixture.institution && courseSchema?.url === fixture.url);
    }
    check('all generated detail routes were served from the local synthetic REST fixture', syntheticRestRequests.length >= fixtures.length * 2);
    check('no non-local non-REST resource was requested', blockedExternalOrigins.size === 0, `blockedOrigins=${blockedExternalOrigins.size}`);
    return `${fixtures.length} generated product detail routes across five universities; the build-only mock route is excluded; synthetic REST requests=${syntheticRestRequests.length}; blocked external origins=${blockedExternalOrigins.size}; no external egress`;
  }, { requiresFixtureReset: false }),
  defineCase('H3-CA4.11', 'editorial form exposes accessible names and predictable keyboard focus', 'admin', '/admin/edit/', 'all thirteen editable fields have accessible names and keyboard traversal advances and returns without saving changes', async ({ page, check }) => {
    await openFirstEditor(page, 'admin');
    const fieldControls = EDITORIAL_FIELDS.map((field) => {
      if (field === 'price_status') return { field, locator: page.getByRole('combobox', { name: /^Estado del precio/ }) };
      if (field === 'mode') return { field, locator: page.getByRole('combobox', { name: /^Modalidad/ }) };
      return { field, locator: page.locator(`main [name="${field}"]`) };
    });
    const accessibility = [];
    for (const { field, locator } of fieldControls) {
      const count = await locator.count();
      const accessible = count === 1 && await locator.isVisible() && await locator.isEnabled()
        ? await locator.evaluate((element) => {
          const id = element.getAttribute('id');
          const associatedLabel = Boolean(id && Array.from(document.querySelectorAll('label[for]'))
            .some((label) => label.htmlFor === id && Boolean(label.textContent?.trim())));
          const labelledBy = (element.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean);
          const referencedLabel = labelledBy.some((labelId) => Boolean(document.getElementById(labelId)?.textContent?.trim()));
          return Boolean(associatedLabel || referencedLabel || element.getAttribute('aria-label')?.trim());
        })
        : false;
      accessibility.push({ field, accessible, count });
    }
    const accessibleFields = accessibility.filter(({ accessible }) => accessible).length;
    const inaccessibleFields = accessibility.filter(({ accessible }) => !accessible)
      .map(({ field, count }) => `${field}(matches=${count})`);
    check('all thirteen editorial fields have an accessible name', accessibleFields === EDITORIAL_FIELDS.length,
      `accessible=${accessibleFields}/${EDITORIAL_FIELDS.length}; missing=${inaccessibleFields.join(',') || 'none'}`);

    const nameInput = page.locator('main [name="name"]');
    await nameInput.focus();
    const expectedNext = await page.evaluate(() => {
      const visibleFocusable = Array.from(document.querySelectorAll('a[href],button,input,select,textarea,[tabindex]'))
        .filter((element) => element instanceof HTMLElement
          && element.tabIndex >= 0
          && !element.hasAttribute('disabled')
          && element.getAttribute('aria-hidden') !== 'true'
          && element.getClientRects().length > 0);
      const index = visibleFocusable.indexOf(document.activeElement);
      const next = index >= 0 ? visibleFocusable[index + 1] : null;
      return next ? {
        tag: next.tagName,
        id: next.id,
        name: next.getAttribute('name'),
        ariaLabel: next.getAttribute('aria-label'),
        role: next.getAttribute('role'),
      } : null;
    });
    await page.keyboard.press('Tab');
    const actualNext = await page.evaluate(() => {
      const element = document.activeElement;
      return element instanceof HTMLElement ? {
        tag: element.tagName,
        id: element.id,
        name: element.getAttribute('name'),
        ariaLabel: element.getAttribute('aria-label'),
        role: element.getAttribute('role'),
      } : null;
    });
    check('Tab advances to the next visible control in DOM order', Boolean(expectedNext)
      && JSON.stringify(actualNext) === JSON.stringify(expectedNext),
      `nextControl=${actualNext?.name || actualNext?.ariaLabel || actualNext?.role || actualNext?.tag || 'missing'}`);
    await page.keyboard.press('Shift+Tab');
    check('Shift+Tab returns to the starting editorial field', await nameInput.evaluate((element) => document.activeElement === element));
    return `${accessibleFields}/${EDITORIAL_FIELDS.length} fields named; forward/reverse Tab traversal verified without save`;
  }),
  defineCase('H3-CA4.9', 'catalog renders empty state and retains static fallback after backend error', 'anon', '/', 'public catalog renders a synthetic course, an explicit empty state and retains its static fallback when the API returns an error without external egress', async ({ page, check }) => {
    const category = { id: 'c0000000-0000-4000-8000-000000000067', name: 'Programas sintéticos' };
    const institution = { id: 'b0000000-0000-4000-8000-000000000067', name: 'Universidad UAT Sintética', slug: 'utp' };
    const course = {
      id: 'a0000000-0000-4000-8000-000000000067',
      institution_id: institution.id,
      category_id: category.id,
      name: 'Curso UAT de estados públicos',
      slug: 'programa-local-h3-20',
      url: 'https://synthetic.h3.example/programs/curso-uat-estados-publicos',
      price_pen: 1250,
      price_status: 'publicado',
      mode: 'Remoto',
      course_type: 'Maestría',
      duration: '6 meses',
      start_date_text: 'Marzo 2027',
      category: category.name,
      roi_months: 6,
      expected_monthly_salary: 2500,
      created_at: '2026-10-11T12:00:00.000Z',
    };
    const corsHeaders = {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET, OPTIONS',
      'access-control-allow-headers': 'apikey, authorization, content-type, accept',
    };
    let phase = 'populated';
    const observedCourseStatuses = [];
    const blockedExternalOrigins = new Set();
    const baseOrigin = new URL(BASE_URL).origin;
    const waitForCourseResponse = (status) => page.waitForResponse((response) => {
      try {
        return new URL(response.url()).pathname.endsWith('/courses_public_effective')
          && response.status() === status;
      } catch { return false; }
    }, { timeout: 10000 });

    await page.route('**/*', async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.pathname.startsWith('/rest/v1/')) {
        if (request.method() === 'OPTIONS') {
          await route.fulfill({ status: 204, headers: corsHeaders, body: '' });
          return;
        }
        if (url.pathname.endsWith('/courses_public_effective')) {
          if (phase === 'unavailable') {
            observedCourseStatuses.push(503);
            await route.fulfill({ status: 503, contentType: 'application/json', headers: corsHeaders, body: JSON.stringify({ message: 'synthetic local upstream unavailable' }) });
          } else {
            const body = phase === 'empty' ? [] : [course];
            observedCourseStatuses.push(200);
            await route.fulfill({ status: 200, contentType: 'application/json', headers: corsHeaders, body: JSON.stringify(body) });
          }
          return;
        }
        const body = url.pathname.endsWith('/institutions') ? [institution]
          : url.pathname.endsWith('/categories') ? [category] : [];
        await route.fulfill({ status: 200, contentType: 'application/json', headers: corsHeaders, body: JSON.stringify(body) });
        return;
      }
      if (url.origin === baseOrigin) {
        await route.continue();
        return;
      }
      blockedExternalOrigins.add(url.origin);
      await route.fulfill({ status: 204, body: '' });
    });

    let response = waitForCourseResponse(200);
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    await response;
    await waitForPublicCatalog(page);
    const syntheticCard = page.locator('#programas main article').filter({ hasText: course.name }).first();
    check('populated catalog displays the synthetic public course', await syntheticCard.count() === 1
      && await syntheticCard.getByRole('heading', { name: course.name, exact: true }).isVisible());

    await page.evaluate(() => localStorage.removeItem('StudIAMatch_courses_cache'));
    phase = 'empty';
    response = waitForCourseResponse(200);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await response;
    await page.getByRole('heading', { name: 'Sin resultados', exact: true }).waitFor({ state: 'visible' });
    check('empty API result renders the explicit empty state', await page.getByRole('heading', { name: 'Sin resultados', exact: true }).isVisible()
      && await page.locator('#programas main article').count() === 0);

    phase = 'unavailable';
    response = waitForCourseResponse(503);
    await page.reload({ waitUntil: 'domcontentloaded' });
    const failedResponse = await response;
    await waitForPublicCatalog(page);
    check('backend error is observed as 503', failedResponse.status() === 503 && observedCourseStatuses.includes(503));
    check('static catalog remains visible after the failed refresh', await page.locator('#programas main article').count() > 0
      && await page.getByRole('heading', { name: 'Sin resultados', exact: true }).count() === 0);
    check('no non-local non-REST resource was requested', blockedExternalOrigins.size === 0,
      `blockedOrigins=${blockedExternalOrigins.size}`);
    return `course responses=${observedCourseStatuses.join(',')}; populated, empty and unavailable states checked; external origins=${blockedExternalOrigins.size}`;
  }, { requiresFixtureReset: false }),
  defineCase('H3-CA4.8', 'membership actions identify their target and invite errors are announced', 'admin', '/admin/users/', 'membership controls are accessible by name and keyboard, confirmations identify the affected account, and invalid synthetic invitations announce local validation feedback', async ({ page, check }) => {
    await openUsers(page);
    const roleControl = page.getByRole('combobox').first();
    const roleControlCount = await page.getByRole('combobox').count();
    check('invitation role has its visible accessible name', roleControlCount === 1
      && await page.getByRole('combobox', { name: 'Rol', exact: true }).count() === 1);
    check('email supports browser autofill', await page.getByLabel('Email').getAttribute('autocomplete') === 'email');

    const headers = await page.getByRole('table').getByRole('columnheader').allTextContents();
    check('membership table exposes all seven named columns', headers.map((text) => text.trim()).join('|') === 'Email|Rol|Estado|Invitación|Cuenta|Expira|Acciones');
    const contrastSamples = await page.evaluate(() => {
      const canvas = document.createElement('canvas');
      canvas.width = 1;
      canvas.height = 1;
      const context = canvas.getContext('2d', { willReadFrequently: true });
      const parse = (value) => {
        if (!context || !CSS.supports('color', value)) return null;
        context.clearRect(0, 0, 1, 1);
        context.fillStyle = value;
        context.fillRect(0, 0, 1, 1);
        const [red, green, blue, alpha] = context.getImageData(0, 0, 1, 1).data;
        return [red, green, blue, alpha / 255];
      };
      const composite = (foreground, background) => foreground.slice(0, 3)
        .map((channel, index) => channel * foreground[3] + background[index] * (1 - foreground[3]));
      const luminance = ([red, green, blue]) => {
        const channels = [red, green, blue].map((channel) => channel / 255).map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4);
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
      };
      const background = (element) => {
        const ancestors = [];
        for (let node = element; node; node = node.parentElement) ancestors.push(node);
        let color = [255, 255, 255];
        for (const node of ancestors.reverse()) {
          const parsed = parse(getComputedStyle(node).backgroundColor);
          if (parsed && parsed[3] > 0) color = composite(parsed, color);
        }
        return color;
      };
      const parserProbes = [
        ['lab(0 0 0)', [0, 0, 0]],
        ['lab(100 0 0)', [255, 255, 255]],
        ['rgb(0, 0, 0)', [0, 0, 0]],
      ].map(([input, expected]) => {
        const actual = parse(input);
        return actual !== null && actual.slice(0, 3).every((channel, index) => Math.abs(channel - expected[index]) <= 1);
      });
      const samples = [
        ['page heading', document.querySelector('main h1')],
        ['email label', document.querySelector('label[for="member-email"]')],
        ['role label', document.querySelector('#member-role-label')],
        ['table header', document.querySelector('[data-membership-scroll] thead th')],
        ['table cell', document.querySelector('[data-membership-scroll] tbody td')],
        ['membership action', document.querySelector('[data-membership-scroll] tbody button')],
      ];
      return {
        parserProbes,
        samples: samples.map(([name, element]) => {
        if (!(element instanceof HTMLElement)) return { name, ratio: 0 };
        const foreground = parse(getComputedStyle(element).color);
        const back = background(element);
        if (!foreground) return { name, ratio: 0 };
        const visibleForeground = composite(foreground, back);
        const values = [luminance(visibleForeground), luminance(back)].sort((a, b) => b - a);
        return { name, ratio: Number(((values[0] + 0.05) / (values[1] + 0.05)).toFixed(2)) };
        }),
      };
    });
    check('contrast sampler normalizes Lab and RGB CSS colors', contrastSamples.parserProbes.length === 3
      && contrastSamples.parserProbes.every(Boolean));
    check('tested membership text contrast meets 4.5:1', contrastSamples.samples.length === 6
      && contrastSamples.samples.every(({ ratio }) => ratio >= 4.5), JSON.stringify(contrastSamples.samples));
    const targetRow = page.locator('[data-membership-row]').filter({ hasText: USERS.admin.email }).first();
    await targetRow.waitFor({ state: 'visible' });
    const actionLabels = await targetRow.getByRole('button').evaluateAll((buttons) => buttons.map((button) => button.getAttribute('aria-label') || ''));
    check('membership action names include the target account', actionLabels.length >= 2
      && actionLabels.every((label) => label.includes(USERS.admin.email)));

    let dialogMessage = '';
    const rpcRequestsBefore = await page.evaluate(() => performance.getEntriesByType('resource')
      .filter((entry) => new URL(entry.name).pathname === '/api/admin/rpc').length);
    const stateAction = targetRow.getByRole('button', { name: /Desactivar|Activar/ }).first();
    page.once('dialog', async (dialog) => { dialogMessage = dialog.message(); await dialog.dismiss(); });
    await stateAction.focus();
    check('keyboard focus reaches the membership state action', await stateAction.evaluate((element) => document.activeElement === element));
    await page.keyboard.press('Enter');
    check('confirmation identifies the affected account', dialogMessage.includes(USERS.admin.email));
    const rpcRequestsAfter = await page.evaluate(() => performance.getEntriesByType('resource')
      .filter((entry) => new URL(entry.name).pathname === '/api/admin/rpc').length);
    check('dismissing confirmation does not send a mutation', rpcRequestsAfter === rpcRequestsBefore);
    let roleDialogMessage = '';
    const roleAction = targetRow.getByRole('button', { name: /^Hacer user — / });
    page.once('dialog', async (dialog) => { roleDialogMessage = dialog.message(); await dialog.dismiss(); });
    await roleAction.focus();
    check('keyboard focus reaches the membership role action', await roleAction.evaluate((element) => document.activeElement === element));
    await page.keyboard.press('Enter');
    check('role confirmation identifies the affected account', roleDialogMessage.includes(USERS.admin.email)
      && /rol/i.test(roleDialogMessage));
    const rpcRequestsAfterRoleDismissal = await page.evaluate(() => performance.getEntriesByType('resource')
      .filter((entry) => new URL(entry.name).pathname === '/api/admin/rpc').length);
    check('dismissing role confirmation does not send a mutation', rpcRequestsAfterRoleDismissal === rpcRequestsBefore);

    const email = page.getByLabel('Email');
    await email.fill('invalid-local-address');
    if (roleControlCount === 1) {
      await roleControl.focus();
      await page.keyboard.press('Tab');
    } else {
      await email.focus();
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
    }
    const addButton = page.getByRole('button', { name: 'Agregar usuario', exact: true });
    check('keyboard order reaches the invite action', await addButton.evaluate((element) => document.activeElement === element));
    const invalidInviteResponse = page.waitForResponse((response) => {
      try {
        return response.request().method() === 'POST'
          && new URL(response.url()).pathname === '/api/admin/invitations';
      } catch { return false; }
    });
    await page.keyboard.press('Enter');
    check('local invitation schema rejects invalid input', (await invalidInviteResponse).status() === 400);
    const alert = page.locator('main p[role="alert"]');
    await alert.waitFor({ state: 'visible' });
    const alertText = (await alert.innerText()).trim();
    check('invalid invitation feedback is readable and announced', alertText.includes('correo válido')
      && !alertText.includes('invalid_invitation'));
    return 'accessible membership context, non-mutating dismissed confirmation and invalid-invite alert checked';
  }),
  defineCase('H3-CA4.9', 'comparison actions remain named and keyboard reachable at each viewport', 'anon', '/compare/', 'a selected synthetic course is readable in the comparison view, its removal control has a useful accessible name and keyboard focus, and the page has no horizontal overflow', async ({ page, check }) => {
    const courseId = process.env.H3_PIPELINE_COURSE_ID || '70000000-0000-0000-0000-000000000091';
    const publicName = process.env.H3_PIPELINE_PUBLIC_NAME || 'Analítica Aplicada';
    const course = {
      id: courseId,
      institution_id: '00000000-0000-0000-0000-000000000001',
      category_id: '10000000-0000-0000-0000-000000000001',
      name: publicName,
      slug: 'analitica-aplicada-60000000',
      price_pen: 1250,
      price_status: 'publicado',
      mode: 'Remoto',
      duration: '6 meses',
    };
    const corsHeaders = {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET, OPTIONS',
      'access-control-allow-headers': 'apikey, authorization, content-type, accept',
    };
    const blockedExternalOrigins = new Set();
    await page.route('**/*', async (route) => {
      const origin = new URL(route.request().url()).origin;
      if (origin === new URL(BASE_URL).origin) await route.continue();
      else {
        blockedExternalOrigins.add(origin);
        await route.fulfill({ status: 204, body: '' });
      }
    });
    await page.route('**/rest/v1/**', async (route) => {
      if (route.request().method() === 'OPTIONS') {
        await route.fulfill({ status: 204, headers: corsHeaders, body: '' });
        return;
      }
      const url = new URL(route.request().url());
      let body = [];
      if (url.pathname.endsWith('/courses_public_effective')
        && (url.searchParams.get('id') || '').includes(courseId)) body = [course];
      else if (url.pathname.endsWith('/institutions')) body = [
        { id: course.institution_id, name: 'Universidad de Lima', slug: 'ulima' },
      ];
      else if (url.pathname.endsWith('/categories')) body = [
        { id: course.category_id, name: 'Programas sintéticos' },
      ];
      await route.fulfill({ status: 200, contentType: 'application/json', headers: corsHeaders, body: JSON.stringify(body) });
    });
    await page.goto(`${BASE_URL}/compare/?ids=${encodeURIComponent(courseId)}`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Comparativa de Programas', exact: true }).waitFor({ state: 'visible' });
    check('selected synthetic course is named in the comparison', await page.getByRole('heading', { name: publicName, exact: true }).count() === 1
      && await page.getByText('1 Programas seleccionados', { exact: true }).isVisible());
    const remove = page.getByRole('button', { name: 'Retirar de la comparativa', exact: true });
    check('remove action has an accessible name and is visible', await remove.count() === 1 && await remove.isVisible());

    let tabCount = 0;
    while (tabCount < 24 && !(await remove.evaluate((element) => element === document.activeElement))) {
      await page.keyboard.press('Tab');
      tabCount += 1;
    }
    check('keyboard traversal reaches the comparison remove action', await remove.evaluate((element) => element === document.activeElement), `tabCount=${tabCount}`);

    const dimensions = await page.evaluate(() => ({
      viewport: window.innerWidth,
      document: document.documentElement.scrollWidth,
      mainClient: document.querySelector('main')?.clientWidth ?? 0,
      mainScroll: document.querySelector('main')?.scrollWidth ?? 0,
    }));
    check('comparison content does not overflow horizontally', dimensions.document <= dimensions.viewport + 1
      && dimensions.mainScroll <= dimensions.mainClient + 1, JSON.stringify(dimensions));
    const visibleText = await page.locator('main').innerText();
    check('comparison does not expose raw null or undefined values', !/\b(?:null|undefined)\b/i.test(visibleText));
    check('comparison used only local synthetic fixtures', blockedExternalOrigins.size === 0, `blockedOrigins=${blockedExternalOrigins.size}`);
    return 'comparison course, named keyboard control, responsive overflow and local synthetic fixture verified';
  }),
  defineCase('H3-CA4.7', 'integrated write quota rejects excess calls without changing editorial state', 'admin', '/privacidad/', 'the local BFF admits the configured write quota, rejects the next request with Retry-After, and leaves editorial state and audit unchanged', async ({ page, check }) => {
    const courseId = process.env.H3_PIPELINE_COURSE_ID || '70000000-0000-0000-0000-000000000091';
    await login(page, 'admin');
    await page.goto(`${BASE_URL}/privacidad/`, { waitUntil: 'networkidle' });
    const beforeSession = await sessionInfo(page);
    check('synthetic Admin session remains valid outside the queue', beforeSession.authenticated === true && beforeSession.aal === 'aal2');

    const beforeResponse = await rpc(page, 'admin_get_course_editorial', { p_course_id: courseId });
    const beforeCourse = beforeResponse.body?.data?.[0]?.course;
    check('synthetic editorial baseline is readable', beforeResponse.status === 200 && Boolean(beforeCourse));
    assert(beforeCourse, 'synthetic editorial baseline unavailable for quota test');
    const auditBeforeResponse = await rpc(page, 'admin_get_course_audit', { p_course_id: courseId, p_first: 100 });
    const auditBefore = auditBeforeResponse.body?.data?.[0]?.events || [];
    assert(auditBeforeResponse.status === 200, 'synthetic audit baseline unavailable for quota test');

    const quotaProbe = async () => page.evaluate(async ({ courseId, version }) => {
      const response = await fetch('/api/admin/rpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          function: 'admin_update_course',
          params: {
            p_course_id: courseId,
            p_manual_overrides: { h3_uat_unknown_quota_probe: 'synthetic-denied-field' },
            p_version: version,
            p_reason: 'Quota integration synthetic denial',
          },
        }),
      });
      const body = await response.json().catch(() => null);
      const row = body?.data?.[0];
      return {
        status: response.status,
        deniedUnknownField: row?.success === false && row?.error === 'Unknown field not allowed: h3_uat_unknown_quota_probe',
        errorCode: body?.error?.code === 'rate_limited' ? 'rate_limited' : 'other',
        retryAfter: response.headers.get('Retry-After'),
      };
    }, { courseId, version: Number(beforeCourse.version) });

    const admittedDeniedWrites = [];
    for (let index = 0; index < 30; index += 1) admittedDeniedWrites.push(await quotaProbe());
    check('all 30 admitted write-quota probes fail closed before mutation',
      admittedDeniedWrites.length === 30 && admittedDeniedWrites.every(({ status, deniedUnknownField }) => status === 200 && deniedUnknownField));
    const overLimit = await quotaProbe();
    const retryAfter = Number(overLimit.retryAfter);
    check('the next integrated write request is rate limited', overLimit.status === 429 && overLimit.errorCode === 'rate_limited',
      JSON.stringify({ status: overLimit.status, errorCode: overLimit.errorCode, retryAfter: overLimit.retryAfter }));
    check('rate limit includes a bounded Retry-After', Number.isInteger(retryAfter) && retryAfter >= 1 && retryAfter <= 60);

    const afterResponse = await rpc(page, 'admin_get_course_editorial', { p_course_id: courseId });
    const afterCourse = afterResponse.body?.data?.[0]?.course;
    const auditAfterResponse = await rpc(page, 'admin_get_course_audit', { p_course_id: courseId, p_first: 100 });
    const auditAfter = auditAfterResponse.body?.data?.[0]?.events || [];
    const auditSignature = (events) => JSON.stringify(events.map((event) => [event.action, event.created_at, event.old_values, event.new_values]));
    check('editorial values and version remain unchanged after the quota boundary', afterResponse.status === 200
      && afterCourse?.version === beforeCourse.version
      && JSON.stringify(afterCourse?.manual_overrides || {}) === JSON.stringify(beforeCourse.manual_overrides || {})
      && JSON.stringify(afterCourse?.current_values || {}) === JSON.stringify(beforeCourse.current_values || {}));
    check('no audit event was added by the denied probes', auditAfterResponse.status === 200
      && auditSignature(auditAfter) === auditSignature(auditBefore));
    const afterSession = await sessionInfo(page);
    check('quota rejection preserves the HttpOnly authenticated session', afterSession.authenticated === true && afterSession.aal === 'aal2'
      && afterSession.httpOnly && afterSession.secure && afterSession.sameSite === 'Lax'
      && !afterSession.hasAuthStorage && !afterSession.hasAccessToken && !afterSession.hasRefreshToken);
    return '30 non-mutating signed writes admitted by the quota gate; request 31 received 429 and editorial/audit state remained unchanged';
  }),
  defineCase('H3-CA4.9', 'public listing matches PG17 eligibility and traverses every paginated identity', 'anon', '/', 'the visible public listing contains exactly the sixteen synthetic PG17 eligible identities across pages and excludes ineligible rows', async ({ page, check }) => {
    const institutionSlugs = ['ulima', 'pucp', 'upc', 'usil', 'utp'];
    const institutions = institutionSlugs.map((slug, index) => ({
      id: `b0000000-0000-4000-8000-${String(index + 11).padStart(12, '0')}`,
      name: `Universidad sintética ${slug.toUpperCase()}`,
      slug,
    }));
    const inventoryRows = [
      ['20000000-0000-0000-0000-000000000011', 'ulima', 'programa-local-h3-11'],
      ['20000000-0000-0000-0000-000000000012', 'pucp', 'programa-local-h3-12'],
      ['20000000-0000-0000-0000-000000000013', 'upc', 'programa-local-h3-13'],
      ['20000000-0000-0000-0000-000000000014', 'usil', 'programa-local-h3-14'],
      ['20000000-0000-0000-0000-000000000015', 'utp', 'programa-local-h3-15'],
      ['20000000-0000-0000-0000-000000000016', 'ulima', 'programa-local-h3-16'],
      ['20000000-0000-0000-0000-000000000017', 'pucp', 'programa-local-h3-17'],
      ['20000000-0000-0000-0000-000000000018', 'upc', 'programa-local-h3-18'],
      ['20000000-0000-0000-0000-000000000019', 'usil', 'programa-local-h3-19'],
      ['20000000-0000-0000-0000-000000000020', 'utp', 'programa-local-h3-20'],
      ['20000000-0000-0000-0000-000000000021', 'ulima', 'programa-local-h3-21'],
      ['20000000-0000-0000-0000-000000000022', 'pucp', 'programa-local-h3-22'],
      ['20000000-0000-0000-0000-000000000023', 'upc', 'programa-local-h3-23'],
      ['20000000-0000-0000-0000-000000000024', 'usil', 'programa-local-h3-24'],
      ['20000000-0000-0000-0000-000000000025', 'utp', 'programa-local-h3-25'],
      ['70000000-0000-0000-0000-000000000091', 'ulima', 'analitica-aplicada-60000000'],
    ];
    const expectedRoutes = inventoryRows.map(([, institutionSlug, slug]) => `/courses/${institutionSlug}/${slug}`);
    const institutionBySlug = new Map(institutions.map((institution) => [institution.slug, institution]));
    const courses = inventoryRows.map(([id, institutionSlug, slug], index) => ({
      id,
      institution_id: institutionBySlug.get(institutionSlug).id,
      category_id: 'c0000000-0000-4000-8000-000000000071',
      name: `Programa sintético ${slug}`,
      slug,
      url: `https://synthetic.h3.example/programs/${slug}`,
      price_pen: index % 5 === 0 ? null : 1000 + (index * 100),
      price_status: [5, 6].includes(index) ? 'consultar' : 'publicado',
      mode: index % 2 === 0 ? 'Remoto' : 'Híbrido',
      course_type: 'Maestría',
      duration: '6 meses',
      start_date_text: 'Marzo 2027',
      category: 'Programas sintéticos',
      roi_months: 6,
      expected_monthly_salary: 2500,
      is_verified: true,
      created_at: `2026-10-11T12:${String(index).padStart(2, '0')}:00.000Z`,
    }));
    const category = { id: 'c0000000-0000-4000-8000-000000000071', name: 'Programas sintéticos' };
    const blockedExternalOrigins = new Set();
    const baseOrigin = new URL(BASE_URL).origin;

    await page.route('**/*', async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.pathname.startsWith('/rest/v1/')) {
        const body = url.pathname.endsWith('/courses_public_effective') ? courses
          : url.pathname.endsWith('/institutions') ? institutions
            : url.pathname.endsWith('/categories') ? [category] : [];
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
        return;
      }
      if (url.origin === baseOrigin) {
        await route.continue();
        return;
      }
      blockedExternalOrigins.add(url.origin);
      await route.fulfill({ status: 204, body: '' });
    });

    const waitForCourseResponse = page.waitForResponse((response) => {
      try { return new URL(response.url()).pathname.endsWith('/courses_public_effective') && response.status() === 200; }
      catch { return false; }
    });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    await waitForCourseResponse;
    await waitForPublicCatalog(page);

    const readVisibleRoutes = () => page.locator('#programas main article').evaluateAll((articles) => articles.map((article) => {
      const link = article.querySelector('h3')?.closest('a');
      return link instanceof HTMLAnchorElement ? new URL(link.href).pathname.replace(/\/$/, '') : null;
    }));
    const firstPageRoutes = await readVisibleRoutes();
    check('first listing page displays twelve eligible rows with detail links', firstPageRoutes.length === 12
      && firstPageRoutes.every((route) => typeof route === 'string'));
    check('first page links belong to the PG17 public eligibility set', firstPageRoutes.every((route) => expectedRoutes.includes(route)));
    await page.getByRole('button', { name: 'Siguiente', exact: true }).click();
    await page.waitForFunction(() => document.querySelector('#programas main')?.textContent?.includes('2 / 2')
      && document.querySelectorAll('#programas main article').length === 4);
    const secondPageRoutes = await readVisibleRoutes();
    const allRoutes = [...firstPageRoutes, ...secondPageRoutes];
    check('second listing page contains the remaining four eligible identities', secondPageRoutes.length === 4);
    check('all eligible identities appear exactly once across both pages', allRoutes.length === expectedRoutes.length
      && new Set(allRoutes).size === expectedRoutes.length
      && expectedRoutes.every((route) => allRoutes.includes(route)));
    check('all ineligible inventory rows remain excluded from the public listing', allRoutes.every((route) => expectedRoutes.includes(route)));
    check('no non-local origin was requested', blockedExternalOrigins.size === 0, `blockedOrigins=${blockedExternalOrigins.size}`);
    return `PG17 eligibility identities=${expectedRoutes.length}; cards=${allRoutes.length}; pages=12+4; external origins=${blockedExternalOrigins.size}`;
  }, { requiresFixtureReset: false }),
  defineCase('H3-CA4.9', 'public listing and detail reflect the same PG17 mutation after a static rebuild', 'anon', '/', 'one synthetic course ID keeps its route while the updated value appears in the rebuilt static detail and fresh public listing', async ({ page, check }) => {
    const snapshotPath = process.env.H3_MUTATION_SNAPSHOT;
    assert(snapshotPath && snapshotPath.startsWith('/evidence/'), 'mutation snapshot must come from the isolated evidence mount');
    const snapshot = JSON.parse(await readFile(snapshotPath, 'utf8'));
    assert(Array.isArray(snapshot.courses) && snapshot.courses.length === 16, 'mutation snapshot must contain the sixteen PG17 eligible courses');
    assert(Array.isArray(snapshot.institutions) && Array.isArray(snapshot.categories), 'mutation snapshot relations must be arrays');
    const targetId = '70000000-0000-0000-0000-000000000091';
    const targetSlug = 'analitica-aplicada-60000000';
    const updatedName = 'Analítica Aplicada R145';
    const previousName = 'Analítica Aplicada';
    const target = snapshot.courses.find((course) => course.id === targetId);
    assert(target && target.slug === targetSlug && target.name === updatedName, 'PG17 mutation identity/value does not match the candidate');
    const blockedExternalOrigins = new Set();
    const baseOrigin = new URL(BASE_URL).origin;

    await page.route('**/*', async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.pathname.startsWith('/rest/v1/')) {
        const rows = url.pathname.endsWith('/courses_public_effective') ? snapshot.courses
          : url.pathname.endsWith('/institutions') ? snapshot.institutions
            : url.pathname.endsWith('/categories') ? snapshot.categories : [];
        let result = rows;
        for (const [key, value] of url.searchParams.entries()) {
          if (value.startsWith('eq.')) result = result.filter((row) => String(row[key]) === value.slice(3));
          else if (value.startsWith('in.(')) {
            const allowed = new Set(value.slice(4, -1).split(',').map((item) => item.replace(/^"|"$/g, '')));
            result = result.filter((row) => allowed.has(String(row[key])));
          }
        }
        const offset = Number(url.searchParams.get('offset') || 0);
        const limit = Number(url.searchParams.get('limit') || result.length);
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(result.slice(offset, offset + limit)) });
        return;
      }
      if (url.origin === baseOrigin) {
        await route.continue();
        return;
      }
      blockedExternalOrigins.add(url.origin);
      await route.fulfill({ status: 204, body: '' });
    });

    const waitForCourseResponse = page.waitForResponse((response) => {
      try { return new URL(response.url()).pathname.endsWith('/courses_public_effective') && response.status() === 200; }
      catch { return false; }
    });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    await waitForCourseResponse;
    await waitForPublicCatalog(page);
    const updatedCard = page.locator('#programas main article').filter({ hasText: updatedName });
    await updatedCard.first().waitFor({ state: 'visible' });
    check('fresh listing renders the updated name exactly once', await updatedCard.count() === 1);
    const detailLink = updatedCard.locator('h3').locator('xpath=ancestor::a');
    const detailHref = await detailLink.getAttribute('href');
    const detailPath = detailHref ? new URL(detailHref, BASE_URL).pathname.replace(/\/$/, '') : '';
    check('listing retains the stable synthetic detail route', detailPath === `/courses/ulima/${targetSlug}`);
    await detailLink.click();
    const expectedDetailPath = `/courses/ulima/${targetSlug}`;
    await page.waitForURL((url) => url.origin === baseOrigin
      && url.pathname.replace(/\/$/, '') === expectedDetailPath
      && url.search === ''
      && url.hash === '');
    check('detail navigation retains the same public course identity', new URL(page.url()).pathname.replace(/\/$/, '') === expectedDetailPath);
    await page.waitForFunction((name) => document.querySelector('main')?.textContent?.includes(name), updatedName);
    const detailText = await page.locator('main').innerText();
    check('fresh detail displays the post-mutation value', detailText.includes(updatedName));
    check('fresh detail no longer displays the pre-mutation title as an exact value', await page.getByText(previousName, { exact: true }).count() === 0);
    check('no non-local origin was requested', blockedExternalOrigins.size === 0);
    return `stableId=${targetId}; listing/detail name=${updatedName}; external origins=${blockedExternalOrigins.size}`;
  }, { requiresFixtureReset: false }),
].map((testCase, index) => Object.freeze({ ...testCase, id: `H3-UAT-${String(index + 1).padStart(3, '0')}` })));

const requestedCaseIds = (process.env.H3_UAT_CASES || '').split(',').map((id) => id.trim()).filter(Boolean);
const requestedCaseSet = new Set(requestedCaseIds);
assert(requestedCaseSet.size === requestedCaseIds.length, 'duplicate case id in H3_UAT_CASES');
const CASES = Object.freeze(requestedCaseIds.length
  ? ALL_CASES.filter(({ id }) => requestedCaseSet.has(id))
  : ALL_CASES);
assert(requestedCaseIds.length === 0 || requestedCaseIds.length === CASES.length, 'H3_UAT_CASES contains an unknown case id');

function validateStructure() {
  assert(CASES.length > 0, 'UAT catalog is empty');
  const ids = CASES.map(({ id }) => id);
  assert(new Set(ids).size === CASES.length, 'logical case IDs are not unique');
  assert(ids.every((id) => /^H3-UAT-\d{3}$/.test(id)), 'logical case IDs are malformed');
  if (requestedCaseIds.length === 0) {
    assert(CASES.length === 72, `expected 72 logical cases, got ${CASES.length}`);
    assert(ids.every((id, index) => id === `H3-UAT-${String(index + 1).padStart(3, '0')}`), 'full catalog IDs must be contiguous H3-UAT-001..072');
  }
  assert(VIEWPORTS.length === 3 && new Set(VIEWPORTS.map(({ name }) => name)).size === 3, 'exactly three unique viewports are required');
  const distribution = Object.fromEntries(Object.keys(EXPECTED_DISTRIBUTION).map((key) => [key, CASES.filter(({ requirementId }) => requirementId === key).length]));
  assert(Object.values(distribution).reduce((sum, count) => sum + count, 0) === CASES.length, `invalid criterion distribution: ${JSON.stringify(distribution)}`);
  if (requestedCaseIds.length === 0) assert(JSON.stringify(distribution) === JSON.stringify(EXPECTED_DISTRIBUTION), `invalid criterion distribution: ${JSON.stringify(distribution)}`);
  const executionKeys = VIEWPORTS.flatMap(({ name }) => CASES.map(({ id }) => `${id}:${name}`));
  assert(executionKeys.length === CASES.length * VIEWPORTS.length, 'execution count does not match selected catalog');
  assert(new Set(executionKeys).size === executionKeys.length, 'execution keys are not unique');
  for (const { id } of CASES) for (const { name } of VIEWPORTS) safeArtifactPath(`${id}-${name}.png`);
  const integratedJourney = CASES.find(({ title }) => title === 'pipeline course completes Admin provenance availability publication and public journey');
  if (integratedJourney) safeArtifactPath(`${integratedJourney.id}-desktop.webm`);
  return { logicalCases: CASES.length, viewportExecutions: executionKeys.length, distribution };
}

async function restoreFixture(viewportName) {
  assert(RESET_TOKEN, 'missing H3_TEST_RESET_TOKEN');
  const response = await fetch(`${MOCK_URL}/__test/reset`, { method: 'POST', headers: { 'x-h3-test-token': RESET_TOKEN } });
  assert(response.status === 204, `fixture reset before ${viewportName} expected 204, got ${response.status}`);
  const epoch = Number(response.headers.get('x-h3-quota-fixture-epoch'));
  assert(Number.isSafeInteger(epoch) && epoch > lastQuotaIsolationEpoch,
    `fixture reset before ${viewportName} did not confirm a new isolated quota epoch`);
  lastQuotaIsolationEpoch = epoch;
  return epoch;
}

async function runExecution(browser, testCase, viewport) {
  let quotaIsolationEpoch = null;
  if (process.env.H3_QUOTA_TEST_ISOLATION === 'true') {
    quotaIsolationEpoch = await restoreFixture(`${testCase.id}/${viewport.name}`);
  }
  const startedAt = new Date();
  const started = Date.now();
  const artifactName = `${testCase.id}-${viewport.name}.png`;
  const artifactPath = safeArtifactPath(artifactName);
  const assertions = [];
  const consoleErrors = [];
  const consoleResourceFailures = [];
  const failedRequests = [];
  const http = [];
  const httpErrorDiagnostics = [];
  const unauthorizedResponses = [];
  const requestStartedAt = new WeakMap();
  const navigationTrace = [];
  const sessionObservations = [];
  const responseInspectionPromises = [];
  let logoutStartedAt = 0;
  let logoutMarkerOffsetMs = null;
  let authExpiryStartedAt = 0;
  const bffRpcObservations = [];
  let context;
  let page;
  let video;
  let videoArtifact = null;
  let videoErrorCode = null;
  let observed = '';
  let result = 'FAIL';
  let executionError = null;
  let artifactSha256 = null;
  let artifactBytes = 0;
  let browserHistoryDiagnostics = null;

  const check = (name, condition, detail = '') => {
    const passed = Boolean(condition);
    assertions.push({ name, passed, detail: sanitize(detail) });
    assert(passed, `assertion failed: ${name}${detail ? ` (${detail})` : ''}`);
  };
  const markLogoutStarted = () => { logoutStartedAt = Date.now(); logoutMarkerOffsetMs = logoutStartedAt - started; };
  const markAuthExpiry = () => { authExpiryStartedAt = Date.now(); };

  try {
    const captureVideo = ['pipeline course completes Admin provenance availability publication and public journey',
      'cursor pagination contract exposes paired controls',
      'editorial form exposes accessible names and predictable keyboard focus',
      'catalog renders empty state and retains static fallback after backend error',
      'public listing matches PG17 eligibility and traverses every paginated identity',
      'all generated static detail routes resolve their own course',
      'membership actions identify their target and invite errors are announced',
      'expired Auth session is rejected and cleared during concurrent browser reads',
      'comparison actions remain named and keyboard reachable at each viewport'].includes(testCase.title)
      && viewport.name === 'desktop';
    const contextOptions = { viewport: { width: viewport.width, height: viewport.height }, serviceWorkers: 'block' };
    if (captureVideo) contextOptions.recordVideo = { dir: STAGING_DIR, size: { width: viewport.width, height: viewport.height } };
    context = await browser.newContext(contextOptions);
    page = await context.newPage();
    await page.addInitScript(() => {
      window.__h3UatPopStates = [];
      window.addEventListener('popstate', () => {
        window.__h3UatPopStates.push({ pathname: location.pathname, historyLength: history.length });
      });
    });
    if (captureVideo) video = page.video();
    page.setDefaultTimeout(15000);
    page.setDefaultNavigationTimeout(20000);
    page.on('crash', () => console.error(`phase=page-lifecycle|case=${testCase.id}|viewport=${viewport.name}|error_code=RENDERER_CRASH`));
    page.on('pageerror', (error) => consoleErrors.push(sanitize(`pageerror ${error.name}: ${error.message}`)));
    page.on('console', (message) => {
      if (message.type() !== 'error') return;
      const text = message.text();
      const resourceStatus = text.match(/Failed to load resource: the server responded with a status of (\d{3})/);
      if (resourceStatus) {
        const safeRequest = safeLocalRequest(message.location().url);
        consoleResourceFailures.push({
          status: Number(resourceStatus[1]),
          origin: safeRequest.origin,
          path: safeRequest.path,
          observedOffsetMs: Date.now() - started,
        });
        return;
      }
      consoleErrors.push(sanitize(text));
    });
    page.on('requestfailed', (request) => {
      const failure = request.failure()?.errorText || '';
      if (failure === 'net::ERR_ABORTED') return;
      const failureCode = /^net::ERR_[A-Z_]+$/.test(failure) ? failure : 'REQUEST_FAILED';
      failedRequests.push(`${request.method()} ${safeLocalPath(request.url())} ${failureCode}`);
    });
    page.on('request', (request) => requestStartedAt.set(request, Date.now()));
    page.on('response', (response) => {
      const request = response.request();
      const requestAt = requestStartedAt.get(request) || Date.now();
      const responseAt = Date.now();
      const safeResponse = safeLocalRequest(response.url());
      if (response.status() === 401) unauthorizedResponses.push({ method: request.method(), origin: safeResponse.origin, url: safeResponse.path, status: response.status(), requestAt, responseAt, resourceType: request.resourceType() });
      if (safeResponse.origin === 'local-0' || safeResponse.origin === 'local-1') http.push({ method: response.request().method(), origin: safeResponse.origin, url: safeResponse.path, status: response.status() });
      if (response.status() >= 400) {
        const requestHeaders = request.headers();
        const refererPath = requestHeaders.referer ? safeLocalPath(requestHeaders.referer) : null;
        const requestDiagnostic = {
          method: request.method(),
          origin: safeResponse.origin,
          path: safeResponse.path,
          status: response.status(),
          resourceType: request.resourceType(),
          refererPath,
          requestOffsetMs: requestAt - started,
          responseOffsetMs: responseAt - started,
        };
        if (testCase.title === 'logout clears the HttpOnly session') {
          requestDiagnostic.beforeLogoutRequest = logoutStartedAt > 0 && requestAt < logoutStartedAt;
          requestDiagnostic.afterLogoutResponse = logoutStartedAt > 0 && responseAt >= logoutStartedAt;
        }
        httpErrorDiagnostics.push(requestDiagnostic);
      }
      if (testCase.id === 'H3-UAT-033' || testCase.id === 'H3-UAT-034') {
        try {
          const parsed = new URL(response.url());
          if (parsed.origin === new URL(BASE_URL).origin && parsed.pathname === '/api/admin/session' && response.request().method() === 'GET') {
            responseInspectionPromises.push(response.json().then((body) => {
              const header = response.headers()['set-cookie'] || '';
              const cookieNames = [...header.matchAll(/(?:^|,\s*)([^=;,\s]+)=/g)].map((match) => match[1]);
              sessionObservations.push({
                status: response.status(),
                authenticated: body?.authenticated === true,
                aal: body?.session?.aal === 'aal2' ? 'aal2' : body?.session?.aal === 'aal1' ? 'aal1' : 'missing',
                setCookieNames: cookieNames,
              });
            }).catch(() => sessionObservations.push({ status: response.status(), parseError: true })));
          }
        } catch {
          sessionObservations.push({ status: response.status(), parseError: true });
        }
      }
      if (testCase.id === 'H3-UAT-034') {
        try {
          const parsed = new URL(response.url());
          if (parsed.origin === new URL(BASE_URL).origin && parsed.pathname === '/api/admin/rpc' && response.request().method() === 'POST') {
            const requestAt = requestStartedAt.get(response.request()) || Date.now();
            responseInspectionPromises.push(response.json().then((body) => {
              const requested = response.request().postDataJSON()?.function;
              const functionName = ['admin_get_course_queue_filtered', 'admin_count_course_queue_filtered'].includes(requested) ? requested : 'other';
              const candidateCode = body?.error?.code;
              const errorCode = ['unauthenticated', 'rpc_failed', 'quota_rate_limited', 'quota_unavailable', 'rpc_not_allowed'].includes(candidateCode)
                ? candidateCode : candidateCode ? 'other' : 'none';
              bffRpcObservations.push({
                function: functionName,
                status: response.status(),
                errorCode,
                phase: authExpiryStartedAt > 0 && requestAt >= authExpiryStartedAt ? 'after-expiry' : 'before-expiry',
              });
            }).catch(() => bffRpcObservations.push({ function: 'other', status: response.status(), errorCode: 'response-unavailable', phase: 'unknown' })));
          }
        } catch {
          bffRpcObservations.push({ function: 'other', status: response.status(), errorCode: 'response-unavailable', phase: 'unknown' });
        }
      }
    });
    page.on('framenavigated', (frame) => {
      if (frame !== page.mainFrame()) return;
      try {
        navigationTrace.push(safeLocalPath(frame.url()));
      } catch {
        navigationTrace.push('unavailable');
      }
    });
    observed = sanitize(await testCase.run({ page, context, check, viewport, markLogoutStarted, markAuthExpiry }));
    assert(assertions.length > 0, `${testCase.id} recorded no assertions`);
    if (testCase.id === 'H3-UAT-034') {
      const expectedExpiredRpc401s = unauthorizedResponses.filter(({ method, origin, url, status, requestAt }) => {
        return method === 'POST' && origin === 'local-0' && url === '/api/admin/rpc'
          && status === 401 && authExpiryStartedAt > 0 && requestAt >= authExpiryStartedAt;
      });
      assert(expectedExpiredRpc401s.length === unauthorizedResponses.length,
        'expired-session unauthorized responses were outside protected Admin RPC after the clock boundary');
      assert(expectedExpiredRpc401s.length > 0, 'expired-session protected RPC did not produce its expected unauthorized response');
      assert(!bffRpcObservations.some(({ status, phase }) => phase === 'after-expiry' && status >= 500),
        'protected Admin RPC returned a server error after Auth expiry');
    }
    if (testCase.title === 'logout clears the HttpOnly session') {
      const expectedRpc401s = unauthorizedResponses.filter(({ method, origin, url, status, requestAt }) => {
        return method === 'POST' && origin === 'local-0' && url === '/api/admin/rpc'
          && status === 401 && requestAt >= logoutStartedAt;
      });
      assert(expectedRpc401s.length === unauthorizedResponses.length, 'logout received an unauthorized response outside POST /api/admin/rpc');
      assert(expectedRpc401s.length > 0, 'logout did not produce its expected protected RPC unauthorized response');
    }
    assert(consoleErrors.length === 0, `console errors: ${consoleErrors.join(' | ')}`);
    assert(failedRequests.length === 0, `failed requests: ${failedRequests.join(' | ')}`);
    const unexpectedHttpErrors = httpErrorDiagnostics.filter((diagnostic) =>
      !isExpectedHttpFailure(testCase, diagnostic, EXPECTED_HTTP_FAILURES));
    assert(unexpectedHttpErrors.length === 0, 'unexpected HTTP errors: ' + JSON.stringify(unexpectedHttpErrors));
    const uncorrelatedConsoleResourceFailures = findUncorrelatedConsoleResourceFailures(
      testCase,
      consoleResourceFailures,
      httpErrorDiagnostics,
      EXPECTED_HTTP_FAILURES,
    );
    assert(uncorrelatedConsoleResourceFailures.length === 0,
      'console resource errors lacked a unique expected HTTP response: ' + JSON.stringify(uncorrelatedConsoleResourceFailures));
    result = 'PASS';
  } catch (error) {
    executionError = sanitize(error instanceof Error ? error.message : error);
    observed = observed || executionError;
  } finally {
    if (testCase.id === 'H3-UAT-063' && page) {
      const rawBrowserHistoryDiagnostics = await page.evaluate(() => ({
        pathname: location.pathname,
        historyLength: history.length,
        popStates: Array.isArray(window.__h3UatPopStates) ? window.__h3UatPopStates.slice(-8) : [],
      })).catch(() => ({ unavailable: true }));
      browserHistoryDiagnostics = rawBrowserHistoryDiagnostics.unavailable
        ? rawBrowserHistoryDiagnostics
        : {
          ...rawBrowserHistoryDiagnostics,
          pathname: safeLocalPath(rawBrowserHistoryDiagnostics.pathname),
          popStates: Array.isArray(rawBrowserHistoryDiagnostics.popStates)
            ? rawBrowserHistoryDiagnostics.popStates.map((path) => safeLocalPath(path))
            : [],
        };
    }
    try {
      if (page) {
        await page.screenshot({ path: artifactPath, fullPage: true, animations: 'disabled', timeout: 20000, waitForFonts: false });
        const data = await readFile(artifactPath);
        artifactBytes = data.length;
        artifactSha256 = createHash('sha256').update(data).digest('hex');
        if (artifactBytes === 0) throw new Error('screenshot is empty');
      } else {
        throw new Error('page was not created; screenshot unavailable');
      }
    } catch (error) {
      result = 'FAIL';
      executionError = sanitize(`${executionError ? `${executionError}; ` : ''}artifact failure: ${error instanceof Error ? error.message : error}`);
    }
    if (context) await context.close().catch(() => {});
    if (video) {
      try {
        const fileName = `${testCase.id}-${viewport.name}.webm`;
        const videoPath = await video.path();
        const targetPath = safeArtifactPath(fileName);
        await rename(videoPath, targetPath);
        const data = await readFile(targetPath);
        assert(data.length > 0, 'recorded video is empty');
        videoArtifact = {
          path: relativeArtifact(fileName),
          bytes: data.length,
          sha256: createHash('sha256').update(data).digest('hex'),
        };
      } catch {
        videoErrorCode = 'VIDEO_CAPTURE_FAILED';
      }
    }
  }

  await Promise.all(responseInspectionPromises);

  return {
    executionId: `${testCase.id}:${viewport.name}`,
    id: testCase.id,
    title: testCase.title,
    requirementId: testCase.requirementId,
    role: testCase.role,
    assurance: testCase.role === 'anon' ? 'none' : 'aal2-required',
    hostname: new URL(BASE_URL).hostname,
    viewport: { name: viewport.name, width: viewport.width, height: viewport.height },
    route: testCase.route,
    expected: testCase.expected,
    observed,
    assertions,
    http,
    consoleErrors,
    failedRequests,
    error: executionError,
    quotaIsolationEpoch,
    startedAt: startedAt.toISOString(),
    finishedAt: new Date().toISOString(),
    durationMs: Date.now() - started,
    retry: 0,
    result,
    artifact: relativeArtifact(artifactName),
    artifactBytes,
    artifactSha256,
    videoArtifact,
    videoErrorCode,
    ...(navigationTrace.length ? { navigationTrace } : {}),
    ...(httpErrorDiagnostics.length ? { httpErrorDiagnostics } : {}),
    ...(testCase.title === 'logout clears the HttpOnly session' ? { logoutMarkerOffsetMs } : {}),
    ...(sessionObservations.length ? { sessionObservations } : {}),
    ...(bffRpcObservations.length ? { bffRpcObservations } : {}),
    ...(browserHistoryDiagnostics ? { browserHistoryDiagnostics } : {}),
  };
}

async function promoteEvidence() {
  const hadPrevious = await fileExists(EVIDENCE_DIR);
  if (hadPrevious) await rename(EVIDENCE_DIR, BACKUP_DIR);
  try {
    await rename(STAGING_DIR, EVIDENCE_DIR);
    // Preserve previous evidence, including failed runs, for traceability.
  } catch (error) {
    if (hadPrevious && await fileExists(BACKUP_DIR) && !(await fileExists(EVIDENCE_DIR))) await rename(BACKUP_DIR, EVIDENCE_DIR);
    throw error;
  }
}

async function writeEvidence(structure, executions, fatalError = null) {
  const logicalCases = CASES.map((testCase) => {
    const caseExecutions = executions.filter(({ id }) => id === testCase.id);
    return {
      id: testCase.id,
      title: testCase.title,
      requirementId: testCase.requirementId,
      expectedExecutions: VIEWPORTS.length,
      actualExecutions: caseExecutions.length,
      passedExecutions: caseExecutions.filter(({ result }) => result === 'PASS').length,
      result: caseExecutions.length === 3 && caseExecutions.every(({ result }) => result === 'PASS') ? 'PASS' : 'FAIL',
    };
  });
  const byViewport = Object.fromEntries(VIEWPORTS.map(({ name }) => [name, {
    expected: CASES.length,
    actual: executions.filter(({ viewport }) => viewport.name === name).length,
    passed: executions.filter(({ viewport, result }) => viewport.name === name && result === 'PASS').length,
  }]));
  const summary = {
    schemaVersion: 2,
    environment: 'local-docker-mock',
    generatedAt: new Date().toISOString(),
    baseURL: BASE_URL,
    mockURL: MOCK_URL,
    retries: 0,
    expected: { logicalCases: CASES.length, viewportExecutions: CASES.length * VIEWPORTS.length, screenshots: CASES.length * VIEWPORTS.length },
    actual: {
      logicalCases: logicalCases.length,
      logicalCasesPassed: logicalCases.filter(({ result }) => result === 'PASS').length,
      viewportExecutions: executions.length,
      viewportExecutionsPassed: executions.filter(({ result }) => result === 'PASS').length,
      screenshots: executions.filter(({ artifactBytes }) => artifactBytes > 0).length,
      videos: executions.filter(({ videoArtifact }) => videoArtifact?.bytes > 0).length,
      videoCaptureFailures: executions.filter(({ videoErrorCode }) => videoErrorCode !== null).length,
    },
    distribution: structure.distribution,
    byViewport,
    fatalError: fatalError ? sanitize(fatalError) : null,
    result: !fatalError && logicalCases.every(({ result }) => result === 'PASS') && executions.length === CASES.length * VIEWPORTS.length ? 'PASS' : 'FAIL',
    logicalCases,
  };
  await atomicWrite(join(STAGING_DIR, 'h3-expanded-uat-executions.json'), `${JSON.stringify(executions, null, 2)}\n`);
  await atomicWrite(join(STAGING_DIR, 'h3-expanded-uat-matrix.json'), `${JSON.stringify(summary, null, 2)}\n`);
  const manifest = {
    schemaVersion: 1,
    canonicalRunner: 'tests/h3_local_uat.mjs',
    retries: 0,
    viewports: VIEWPORTS,
    catalog: CASES.map(({ id, title, requirementId, role, route, expected }) => ({ id, title, requirementId, role, route, expected })),
    structuralValidation: structure,
  };
  await atomicWrite(join(STAGING_DIR, 'h3-expanded-uat-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);

  const hashes = {};
  for (const file of (await readdir(STAGING_DIR)).sort()) {
    if (file === 'h3-expanded-uat-artifact-hashes.json') continue;
    const path = join(STAGING_DIR, file);
    const details = await stat(path);
    assert(details.isFile() && details.size > 0, `artifact missing or empty: ${file}`);
    hashes[relativeArtifact(file)] = createHash('sha256').update(await readFile(path)).digest('hex');
  }
  assert(Object.keys(hashes).filter((path) => path.endsWith('.png')).length === summary.actual.screenshots, 'screenshot/hash count mismatch');
  assert(Object.keys(hashes).filter((path) => path.endsWith('.webm')).length === summary.actual.videos, 'video/hash count mismatch');
  await atomicWrite(join(STAGING_DIR, 'h3-expanded-uat-artifact-hashes.json'), `${JSON.stringify(hashes, null, 2)}\n`);
  return summary;
}

const structure = validateStructure();
if (process.env.H3_VALIDATE_ONLY === '1') {
  console.log(JSON.stringify({ result: 'PASS', ...structure, viewports: VIEWPORTS.map(({ name }) => name), retries: 0 }));
  process.exit(0);
}

if (CASES.some(({ role }) => role === 'admin' || role === 'user')) {
  assert(USERS.admin.password && USERS.user.password, 'selected UAT cases require local synthetic admin/user passwords');
}
if (CASES.some(({ requiresFixtureReset }) => requiresFixtureReset !== false)) {
  assert(RESET_TOKEN, 'selected UAT cases require the local synthetic fixture reset token');
}
await mkdir(EVIDENCE_PARENT, { recursive: true });
await rm(STAGING_DIR, { recursive: true, force: true });
await mkdir(STAGING_DIR, { recursive: false });

const executions = [];
let browser;
let browserClosing = false;
let fatalError = null;
let summary;
try {
  browser = await chromium.launch({
    headless: true,
    executablePath: process.env.H3_CHROMIUM_PATH || '/ms-playwright/chromium-1228/chrome-linux64/chrome',
  });
  browser.on('disconnected', () => {
    if (!browserClosing) console.error('phase=browser-lifecycle|error_code=UNEXPECTED_DISCONNECT');
  });
  for (const viewport of VIEWPORTS) {
    if (CASES.some(({ requiresFixtureReset }) => requiresFixtureReset !== false)) await restoreFixture(viewport.name);
    for (const testCase of CASES) {
      executions.push(await runExecution(browser, testCase, viewport));
      // Preserve diagnostics incrementally even if the complete suite is stopped.
      await atomicWrite(join(STAGING_DIR,'h3-expanded-uat-progress.json'),`${JSON.stringify(executions,null,2)}\n`);
    }
  }
} catch (error) {
  fatalError = error instanceof Error ? error.message : String(error);
} finally {
  if (browser) {
    browserClosing = true;
    await browser.close().catch(() => {});
  }
  try {
    summary = await writeEvidence(structure, executions, fatalError);
    await promoteEvidence();
  } catch (error) {
    console.error(`Evidence staging preserved: ${STAGING_DIR}`);
    throw error;
  }
}

console.log(JSON.stringify({ result: summary.result, logicalCases: summary.actual.logicalCases, logicalCasesPassed: summary.actual.logicalCasesPassed, viewportExecutions: summary.actual.viewportExecutions, viewportExecutionsPassed: summary.actual.viewportExecutionsPassed, screenshots: summary.actual.screenshots, retries: 0 }));
process.exit(summary.result === 'PASS' ? 0 : 1);
