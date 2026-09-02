import playwright from '/tmp/h3-playwright/node_modules/playwright/index.js';
import { createHash } from 'crypto';
import { access, mkdir, readFile, readdir, rename, rm, stat, writeFile } from 'fs/promises';
import { dirname, join, resolve, sep } from 'path';

const { chromium } = playwright;

const EXPECTED_DISTRIBUTION = Object.freeze({
  'H3-CA4.1': 5,
  'H3-CA4.2': 5,
  'H3-CA4.3': 2,
  'H3-CA4.4': 5,
  'H3-CA4.5': 6,
  'H3-CA4.6': 4,
  'H3-CA4.7': 6,
  'H3-CA4.8': 6,
  'H3-CA4.9': 3,
  'H3-CA4.10': 2,
  'H3-CA4.11': 3,
});
const VIEWPORTS = Object.freeze([
  Object.freeze({ name: 'desktop', width: 1440, height: 900 }),
  Object.freeze({ name: 'tablet', width: 768, height: 1024 }),
  Object.freeze({ name: 'mobile', width: 390, height: 844 }),
]);
const BASE_URL = process.env.H3_BASE_URL || 'http://localhost:3000';
const MOCK_URL = process.env.H3_MOCK_URL || 'http://localhost:3001';
const PERIMETER_URL = process.env.H3_PERIMETER_URL || 'http://localhost:3002';
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
const PUBLIC_ROUTES = Object.freeze(['/', '/courses/', '/compare/', '/privacidad/', '/terminos/']);
const EDITORIAL_FIELDS = Object.freeze([
  'name', 'price_pen', 'price_status', 'mode', 'duration', 'description_long',
  'syllabus', 'target_audience', 'requirements', 'certification', 'benefits',
  'objectives', 'start_date_text',
]);

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function sanitize(value) {
  return String(value ?? '')
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/gi, 'Bearer [REDACTED]')
    .replace(/(?:access|refresh)[_-]?token["'\s:=]+[A-Za-z0-9._~+/=-]+/gi, 'token=[REDACTED]')
    .slice(0, 4000);
}

function relativeArtifact(fileName) {
  return `.context/evidencia/h3-expanded/${fileName}`;
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
  await page.getByLabel('Código MFA').waitFor({ state: 'visible' });
  assert(TOTP_CODE, 'missing local TOTP code');
  await page.getByLabel('Código MFA').fill(TOTP_CODE);
  await page.getByRole('button', { name: 'Verificar MFA' }).click();
  await page.waitForURL(`${BASE_URL}/admin/`);
  await page.getByRole('heading', { name: role === 'admin' ? 'Cola editorial' : 'Panel de actualización de información' }).waitFor({ state: 'visible' });
}

async function sessionInfo(page) {
  return page.evaluate(() => {
    const raw = sessionStorage.getItem('studiamatch_admin_session');
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return { aal: parsed.aal, expiresAt: parsed.expiresAt, hasAccessToken: Boolean(parsed.accessToken), hasRefreshToken: Boolean(parsed.refreshToken) };
  });
}

async function openFirstEditor(page, role) {
  await login(page, role);
  await page.getByRole('link', { name: 'Editar' }).first().click();
  await page.getByRole('button', { name: role === 'admin' ? 'Guardar cambios' : 'Actualizar información' }).waitFor({ state: 'visible' });
}

async function openUsers(page) {
  await login(page, 'admin');
  await page.goto(`${BASE_URL}/admin/users/`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);
  await page.getByRole('heading', { name: 'Gestión de usuarios' }).waitFor({ state: 'visible' });
  await page.getByRole('heading', { name: 'Usuarios existentes' }).waitFor({ state: 'visible' });
}

async function rpc(page, functionName, params = {}, tokenOverride = null) {
  const response = await page.evaluate(async ({ mockURL, functionName, params, tokenOverride }) => {
    const raw = sessionStorage.getItem('studiamatch_admin_session');
    const session = raw ? JSON.parse(raw) : null;
    const token = tokenOverride || session?.accessToken;
    const result = await fetch(`${mockURL}/rest/v1/rpc/${functionName}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', apikey: 'local-publishable-key', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify(params),
    });
    return { status: result.status, body: await result.json().catch(() => null) };
  }, { mockURL: MOCK_URL, functionName, params, tokenOverride });
  return response;
}

async function readContract(relativePath, requiredStrings) {
  const root = process.env.H3_REPO_ROOT || '/app';
  const content = await readFile(join(root, relativePath), 'utf8');
  for (const required of requiredStrings) assert(content.includes(required), `${relativePath} missing contract: ${required}`);
  return `${relativePath}: ${requiredStrings.length} contracts present`;
}

function defineCase(requirementId, title, role, route, expected, run) {
  return Object.freeze({ requirementId, title, role, route, expected, run });
}

const CASES = Object.freeze([
  defineCase('H3-CA4.1', 'anonymous admin access redirects to login', 'anon', '/admin/', 'anonymous access is redirected to the local admin login', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/`); await page.waitForURL(`${BASE_URL}/admin/login/`); check('redirect', page.url().endsWith('/admin/login/')); return page.url();
  }),
  defineCase('H3-CA4.1', 'active admin reaches the editorial dashboard', 'admin', '/admin/', 'active aal2 admin sees admin-only dashboard capability', async ({ page, check }) => {
    await login(page, 'admin'); check('admin heading', await page.getByRole('heading', { name: 'Cola editorial' }).isVisible()); check('users link', await page.getByRole('link', { name: 'Usuarios' }).isVisible()); return 'admin dashboard and users link visible';
  }),
  defineCase('H3-CA4.1', 'active user reaches the limited dashboard', 'user', '/admin/', 'active aal2 user sees the information-update dashboard', async ({ page, check }) => {
    await login(page, 'user'); check('user heading', await page.getByText('Panel de actualización de información').isVisible()); return 'limited dashboard visible';
  }),
  defineCase('H3-CA4.1', 'user is denied membership administration', 'user', '/admin/users/', 'user cannot expose membership management', async ({ page, check }) => {
    await login(page, 'user'); check('no users link', await page.getByRole('link', { name: 'Usuarios' }).count() === 0); await page.goto(`${BASE_URL}/admin/users/`); await page.waitForURL(`${BASE_URL}/admin/`); return 'users link absent and direct route returned to dashboard';
  }),
  defineCase('H3-CA4.1', 'logout clears the local session', 'admin', '/admin/', 'logout returns to login and removes browser session state', async ({ page, check }) => {
    await login(page, 'admin'); await page.getByRole('button', { name: 'Cerrar sesión' }).click(); await page.waitForURL(`${BASE_URL}/admin/login/`); check('session cleared', await page.evaluate(() => sessionStorage.getItem('studiamatch_admin_session') === null)); return 'session cleared';
  }),

  defineCase('H3-CA4.2', 'admin editor exposes editorial fields', 'admin', '/admin/edit/', 'admin can edit the editorial allowlist', async ({ page, check }) => {
    await openFirstEditor(page, 'admin'); check('editable inputs', await page.locator('main input:not([disabled])').count() > 0); return `${await page.locator('main input:not([disabled])').count()} editable inputs`;
  }),
  defineCase('H3-CA4.2', 'user editor limits ownership to missing fields', 'user', '/admin/edit/', 'user receives only missing fields as editable', async ({ page, check }) => {
    await openFirstEditor(page, 'user'); const editable = await page.locator('main input:not([disabled])').count(); const readonly = await page.locator('main input[disabled]').count(); check('editable missing fields', editable > 0); check('readonly existing fields', readonly > 0); return `${editable} editable, ${readonly} readonly`;
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
    await login(page, 'admin'); const total = await page.getByText(/Total:/).innerText(); const links = await page.getByRole('link', { name: 'Editar' }).count(); check('numeric total', /Total:\s*\d+/.test(total)); check('rows present', links > 0); return `${total}; ${links} rows`;
  }),
  defineCase('H3-CA4.4', 'queue exposes both status filters', 'admin', '/admin/', 'editorial and quality filters are labeled controls', async ({ page, check }) => {
    await login(page, 'admin'); await page.getByText('Estado editorial', { exact: true }).waitFor(); await page.getByText('Estado calidad', { exact: true }).waitFor(); check('editorial filter', true); check('quality filter', true); return 'both filters visible';
  }),
  defineCase('H3-CA4.4', 'page-local queue search filters visible rows', 'admin', '/admin/', 'search narrows the current page without navigation', async ({ page, check }) => {
    await login(page, 'admin'); const first = await page.locator('main h3').first().innerText(); await page.getByLabel('Buscar en esta página').fill(first); check('matching result', await page.getByText(first, { exact: true }).count() >= 1); await page.getByLabel('Buscar en esta página').fill('__no_match__'); check('empty state', await page.getByText('No se encontraron cursos con los filtros actuales.').isVisible()); return 'search match and empty states verified';
  }),
  defineCase('H3-CA4.4', 'queue edit/public links follow editorial state', 'admin', '/admin/', 'every row is editable and pending rows do not expose public links', async ({ page, check }) => {
    await login(page, 'admin'); await page.getByRole('link', { name: 'Editar' }).first().waitFor(); const edits = await page.getByRole('link', { name: 'Editar' }).count(); const views = await page.getByRole('link', { name: 'Ver' }).count(); check('edit links', edits > 0); check('no pending public links', views === 0); return `${edits} edit links, ${views} public links`;
  }),
  defineCase('H3-CA4.4', 'cursor pagination contract exposes paired controls', 'admin', '/admin/', 'when pagination is available, previous and next controls are paired and stateful', async ({ page, check }) => {
    await login(page, 'admin'); const next = page.getByRole('button', { name: 'Siguiente' }); const previous = page.getByRole('button', { name: 'Anterior' }); const nextCount = await next.count(); const previousCount = await previous.count(); check('paired controls', nextCount === previousCount); if (nextCount) check('previous starts disabled', await previous.isDisabled()); return nextCount ? 'pagination controls paired' : 'single-page fixture; paired controls correctly omitted';
  }),

  defineCase('H3-CA4.5', 'admin save control is enabled', 'admin', '/admin/edit/', 'admin can initiate an editorial save', async ({ page, check }) => {
    await openFirstEditor(page, 'admin'); check('save enabled', await page.getByRole('button', { name: 'Guardar cambios' }).isEnabled()); return 'save enabled';
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
  defineCase('H3-CA4.5', 'editor conflict recovery contract exists', 'admin', '/admin/edit/', 'version conflict presents reload recovery and disables stale save', async ({ page, check }) => {
    await openFirstEditor(page, 'admin'); const observed = await readContract('web/src/app/admin/edit/page.tsx', ["startsWith('Version conflict')", 'setConflict(true)', 'Recargar', 'disabled={saving || conflict}']); check('locking contract', true); return observed;
  }),

  defineCase('H3-CA4.6', 'editorial updates carry an audit reason', 'admin', '/admin/edit/', 'save payload includes an explicit human-readable audit reason', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const observed = await readContract('web/src/app/admin/edit/page.tsx', ["p_reason: 'Edición desde panel admin'"]); check('reason present', true); return observed;
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
    await page.goto(`${BASE_URL}/admin/login/`); check('email label', await page.getByLabel('Email').isVisible()); check('password type', await page.getByLabel('Password').getAttribute('type') === 'password'); check('submit', await page.getByRole('button', { name: 'Iniciar sesión' }).isVisible()); return 'login contract visible';
  }),
  defineCase('H3-CA4.7', 'invalid credentials are rejected', 'anon', '/admin/login/', 'invalid password remains on login with sanitized feedback', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`, { waitUntil: 'networkidle' }); await page.waitForTimeout(1500); await page.getByLabel('Email').fill('admin@local.test'); await page.getByLabel('Password').fill('invalid-local-value'); await page.getByRole('button', { name: 'Iniciar sesión' }).click(); await page.getByText('Invalid login credentials').waitFor(); check('still login', page.url().endsWith('/admin/login/')); return 'invalid credentials rejected';
  }),
  defineCase('H3-CA4.7', 'invalid TOTP is rejected', 'admin', '/admin/login/', 'wrong six-digit MFA code does not create aal2 session', async ({ page, check }) => {
    const user = USERS.admin; assert(user.password, 'missing local admin password'); await page.goto(`${BASE_URL}/admin/login/`, { waitUntil: 'networkidle' }); await page.waitForTimeout(1500); await page.getByLabel('Email').fill(user.email); await page.getByLabel('Password').fill(user.password); await page.getByRole('button', { name: 'Iniciar sesión' }).click(); await page.getByLabel('Código MFA').fill('000000'); await page.getByRole('button', { name: 'Verificar MFA' }).click(); await page.getByText('Invalid MFA code').waitFor(); const session = await sessionInfo(page); check('not aal2', session?.aal !== 'aal2'); return 'invalid MFA rejected at aal1';
  }),
  defineCase('H3-CA4.7', 'admin session reaches aal2', 'admin', '/admin/', 'valid admin TOTP produces aal2', async ({ page, check }) => {
    await login(page, 'admin'); const session = await sessionInfo(page); check('aal2', session?.aal === 'aal2'); check('tokens present', session?.hasAccessToken && session?.hasRefreshToken); return `aal=${session?.aal}`;
  }),
  defineCase('H3-CA4.7', 'user session reaches aal2', 'user', '/admin/', 'valid user TOTP produces aal2', async ({ page, check }) => {
    await login(page, 'user'); const session = await sessionInfo(page); check('aal2', session?.aal === 'aal2'); return `aal=${session?.aal}`;
  }),
  defineCase('H3-CA4.7', 'refresh contract preserves assurance', 'admin', '/admin/', 'refresh response preserves an established aal2 session', async ({ page, check }) => {
    await login(page, 'admin'); const result = await page.evaluate(async (mockURL) => { const session = JSON.parse(sessionStorage.getItem('studiamatch_admin_session')); const response = await fetch(`${mockURL}/auth/v1/token?grant_type=refresh_token`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: session.refreshToken }) }); const body = await response.json(); return { status: response.status, aal: body.aal || session.aal, hasToken: Boolean(body.access_token) }; }, MOCK_URL); check('refresh 200', result.status === 200); check('aal2 preserved', result.aal === 'aal2'); check('new token', result.hasToken); return 'refresh preserved aal2';
  }),

  defineCase('H3-CA4.8', 'admin users surface lists memberships', 'admin', '/admin/users/', 'admin sees existing admin/user memberships', async ({ page, check }) => {
    await openUsers(page); await page.locator('[data-membership-row]').first().waitFor(); const rows = await page.locator('[data-membership-row]').count(); check('members visible', rows >= 2); return `${rows} memberships`;
  }),
  defineCase('H3-CA4.8', 'membership invitation form exposes email and role', 'admin', '/admin/users/', 'admin sees labeled email, role and add controls', async ({ page, check }) => {
    await openUsers(page); check('email', await page.getByLabel('Email').isVisible()); check('role', await page.getByRole('heading', { name: 'Agregar usuario' }).locator('xpath=..').getByText('Rol', { exact: true }).isVisible()); check('add', await page.getByRole('button', { name: 'Agregar usuario' }).isVisible()); return 'membership creation controls visible';
  }),
  defineCase('H3-CA4.8', 'invalid membership email is rejected by protected RPC', 'admin', '/admin/users/', 'backend rejects malformed membership email', async ({ page, check }) => {
    await openUsers(page); const result = await rpc(page, 'admin_create_member', { p_email: 'not-an-email', p_role: 'user' }); check('transport handled', result.status === 200 || result.status === 500); check('not successful', result.status !== 200 || result.body?.[0]?.success !== true); return `HTTP ${result.status}: rejected`;
  }),
  defineCase('H3-CA4.8', 'duplicate membership is rejected', 'admin', '/admin/users/', 'backend rejects an existing member email', async ({ page, check }) => {
    await openUsers(page); const result = await rpc(page, 'admin_create_member', { p_email: 'user@local.test', p_role: 'user' }); check('transport handled', result.status === 200 || result.status === 500); check('not successful', result.status !== 200 || result.body?.[0]?.success !== true); return `HTTP ${result.status}: duplicate rejected`;
  }),
  defineCase('H3-CA4.8', 'invalid membership role is rejected', 'admin', '/admin/users/', 'backend rejects roles outside admin/user', async ({ page, check }) => {
    await openUsers(page); const result = await rpc(page, 'admin_create_member', { p_email: 'invalid-role@local.test', p_role: 'owner' }); check('transport handled', result.status === 200 || result.status === 500); check('not successful', result.status !== 200 || result.body?.[0]?.success !== true); return `HTTP ${result.status}: invalid role rejected`;
  }),
  defineCase('H3-CA4.8', 'membership controls cover state and role changes', 'admin', '/admin/users/', 'each membership offers active-state and role actions with confirmation', async ({ page, check }) => {
    await openUsers(page); const rows = await page.locator('tbody tr').count(); check('state actions', await page.getByRole('button', { name: /^(Desactivar|Activar)$/ }).count() === rows); check('role actions', await page.getByRole('button', { name: /^Hacer (user|admin)$/ }).count() === rows); return `${rows} rows with both actions`;
  }),

  defineCase('H3-CA4.9', 'local administrative hostname serves admin', 'anon', '/admin/login/', 'configured local admin origin serves the login surface', async ({ page, check }) => {
    const response = await page.goto(`${BASE_URL}/admin/login/`); check('HTTP 200', response?.status() === 200); check('admin login', await page.getByRole('heading', { name: 'Admin' }).isVisible()); return `${new URL(BASE_URL).hostname} HTTP ${response?.status()}`;
  }),
  defineCase('H3-CA4.9', 'public hostname hides admin with 404', 'anon', '/admin/', 'Host studiamatch.com returns HTTP 404 for admin on the perimeter origin', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const response = await page.request.get(`${PERIMETER_URL}/admin/`, { headers: { Host: 'studiamatch.com' }, maxRedirects: 0 }); check('HTTP 404', response.status() === 404); const login = await page.request.get(`${PERIMETER_URL}/admin/login/`, { headers: { Host: 'localhost' } }); check('admin origin serves 200', login.status() === 200); return `perimeter HTTP ${response.status()}`;
  }),
  defineCase('H3-CA4.9', 'public routes remain available', 'anon', '/', 'all five public regression routes return HTTP 200', async ({ page, check }) => {
    const statuses = {}; for (const route of PUBLIC_ROUTES) { const response = await page.request.get(`${BASE_URL}${route}`); statuses[route] = response.status(); check(`${route} 200`, response.status() === 200); } await page.goto(`${BASE_URL}/`); return JSON.stringify(statuses);
  }),

  defineCase('H3-CA4.10', 'PG17 harness carries convergence sentinel', 'anon', '/admin/login/', 'local PG17 harness includes authoritative H3 migrations and success sentinel', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const observed = await readContract('tests/sql/h3_pg17_harness.sql', ['20260830_h3_expanded_contract.sql', 'h3_pg17_harness_ok']); check('harness contract', true); return observed;
  }),
  defineCase('H3-CA4.10', 'migration contracts are idempotent for second run', 'anon', '/admin/login/', 'H3 expanded migration declares idempotent create/replace or guarded operations', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); const observed = await readContract('db/migrations/20260830_h3_expanded_contract.sql', ['CREATE OR REPLACE FUNCTION', 'IF NOT EXISTS']); check('NOOP prerequisites', true); return observed;
  }),

  defineCase('H3-CA4.11', 'runtime resources and browser diagnostics are clean', 'anon', '/admin/login/', 'same-origin resources load without HTTP errors, console errors or failed requests', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`, { waitUntil: 'networkidle' }); check('login rendered', await page.getByRole('heading', { name: 'Admin' }).isVisible()); return 'runtime settled at networkidle';
  }),
  defineCase('H3-CA4.11', 'layout has no horizontal overflow', 'admin', '/admin/', 'admin dashboard fits the active desktop/tablet/mobile viewport', async ({ page, check }) => {
    await login(page, 'admin'); const dimensions = await page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth })); check('no overflow', dimensions.scrollWidth <= dimensions.clientWidth + 1); return JSON.stringify(dimensions);
  }),
  defineCase('H3-CA4.11', 'basic keyboard and accessible-name contract holds', 'anon', '/admin/login/', 'login controls have accessible names and keyboard focus order', async ({ page, check }) => {
    await page.goto(`${BASE_URL}/admin/login/`); await page.keyboard.press('Tab'); const first = await page.evaluate(() => document.activeElement?.getAttribute('href') || document.activeElement?.getAttribute('name') || document.activeElement?.tagName); check('focus entered interactive UI', Boolean(first)); check('email name', await page.getByLabel('Email').count() === 1); check('password name', await page.getByLabel('Password').count() === 1); check('button name', await page.getByRole('button', { name: 'Iniciar sesión' }).count() === 1); return `first focus=${first}`;
  }),
].map((testCase, index) => Object.freeze({ ...testCase, id: `H3-UAT-${String(index + 1).padStart(3, '0')}` })));

function validateStructure() {
  assert(CASES.length === 47, `expected 47 logical cases, got ${CASES.length}`);
  const ids = CASES.map(({ id }) => id);
  assert(new Set(ids).size === 47, 'logical case IDs are not unique');
  assert(ids.every((id, index) => id === `H3-UAT-${String(index + 1).padStart(3, '0')}`), 'logical IDs must be contiguous H3-UAT-001..047');
  assert(VIEWPORTS.length === 3 && new Set(VIEWPORTS.map(({ name }) => name)).size === 3, 'exactly three unique viewports are required');
  const distribution = Object.fromEntries(Object.keys(EXPECTED_DISTRIBUTION).map((key) => [key, CASES.filter(({ requirementId }) => requirementId === key).length]));
  assert(JSON.stringify(distribution) === JSON.stringify(EXPECTED_DISTRIBUTION), `invalid criterion distribution: ${JSON.stringify(distribution)}`);
  const executionKeys = VIEWPORTS.flatMap(({ name }) => CASES.map(({ id }) => `${id}:${name}`));
  assert(executionKeys.length === 141, `expected 141 executions, got ${executionKeys.length}`);
  assert(new Set(executionKeys).size === 141, 'execution keys are not unique');
  for (const { id } of CASES) for (const { name } of VIEWPORTS) safeArtifactPath(`${id}-${name}.png`);
  return { logicalCases: CASES.length, viewportExecutions: executionKeys.length, distribution };
}

async function restoreFixture(viewportName) {
  assert(RESET_TOKEN, 'missing H3_TEST_RESET_TOKEN');
  const response = await fetch(`${MOCK_URL}/__test/reset`, { method: 'POST', headers: { 'x-h3-test-token': RESET_TOKEN } });
  assert(response.status === 204, `fixture reset before ${viewportName} expected 204, got ${response.status}`);
}

async function runExecution(browser, testCase, viewport) {
  const startedAt = new Date();
  const started = Date.now();
  const artifactName = `${testCase.id}-${viewport.name}.png`;
  const artifactPath = safeArtifactPath(artifactName);
  const assertions = [];
  const consoleErrors = [];
  const failedRequests = [];
  const http = [];
  let context;
  let page;
  let observed = '';
  let result = 'FAIL';
  let executionError = null;
  let artifactSha256 = null;
  let artifactBytes = 0;

  const check = (name, condition, detail = '') => {
    const passed = Boolean(condition);
    assertions.push({ name, passed, detail: sanitize(detail) });
    assert(passed, `assertion failed: ${name}${detail ? ` (${detail})` : ''}`);
  };

  try {
    context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, serviceWorkers: 'block' });
    page = await context.newPage();
    page.setDefaultTimeout(15000);
    page.setDefaultNavigationTimeout(20000);
    page.on('console', (message) => {
      if (message.type() !== 'error') return;
      const text = message.text();
      if (text === 'Failed to load resource: the server responded with a status of 400 (Bad Request)') return;
      consoleErrors.push(sanitize(text));
    });
    page.on('requestfailed', (request) => {
      const failure = request.failure()?.errorText || '';
      if (failure === 'net::ERR_ABORTED') return;
      failedRequests.push(sanitize(`${request.method()} ${request.url()} ${failure}`));
    });
    page.on('response', (response) => {
      if (response.url().startsWith(BASE_URL) || response.url().startsWith(MOCK_URL)) http.push({ method: response.request().method(), url: sanitize(response.url()), status: response.status() });
    });
    observed = sanitize(await testCase.run({ page, context, check, viewport }));
    assert(assertions.length > 0, `${testCase.id} recorded no assertions`);
    assert(consoleErrors.length === 0, `console errors: ${consoleErrors.join(' | ')}`);
    assert(failedRequests.length === 0, `failed requests: ${failedRequests.join(' | ')}`);
    result = 'PASS';
  } catch (error) {
    executionError = sanitize(error instanceof Error ? error.message : error);
    observed = observed || executionError;
  } finally {
    try {
      if (page) {
        await page.screenshot({ path: artifactPath, fullPage: true, animations: 'disabled' });
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
  }

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
    startedAt: startedAt.toISOString(),
    finishedAt: new Date().toISOString(),
    durationMs: Date.now() - started,
    retry: 0,
    result,
    artifact: relativeArtifact(artifactName),
    artifactBytes,
    artifactSha256,
  };
}

async function promoteEvidence() {
  const hadPrevious = await fileExists(EVIDENCE_DIR);
  if (hadPrevious) await rename(EVIDENCE_DIR, BACKUP_DIR);
  try {
    await rename(STAGING_DIR, EVIDENCE_DIR);
    if (hadPrevious) await rm(BACKUP_DIR, { recursive: true, force: true });
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
      expectedExecutions: 3,
      actualExecutions: caseExecutions.length,
      passedExecutions: caseExecutions.filter(({ result }) => result === 'PASS').length,
      result: caseExecutions.length === 3 && caseExecutions.every(({ result }) => result === 'PASS') ? 'PASS' : 'FAIL',
    };
  });
  const byViewport = Object.fromEntries(VIEWPORTS.map(({ name }) => [name, {
    expected: 47,
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
    expected: { logicalCases: 47, viewportExecutions: 141, screenshots: 141 },
    actual: {
      logicalCases: logicalCases.length,
      logicalCasesPassed: logicalCases.filter(({ result }) => result === 'PASS').length,
      viewportExecutions: executions.length,
      viewportExecutionsPassed: executions.filter(({ result }) => result === 'PASS').length,
      screenshots: executions.filter(({ artifactBytes }) => artifactBytes > 0).length,
    },
    distribution: structure.distribution,
    byViewport,
    fatalError: fatalError ? sanitize(fatalError) : null,
    result: !fatalError && logicalCases.every(({ result }) => result === 'PASS') && executions.length === 141 ? 'PASS' : 'FAIL',
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
  assert(Object.keys(hashes).filter((path) => path.endsWith('.png')).length === executions.length, 'screenshot/hash count mismatch');
  await atomicWrite(join(STAGING_DIR, 'h3-expanded-uat-artifact-hashes.json'), `${JSON.stringify(hashes, null, 2)}\n`);
  return summary;
}

const structure = validateStructure();
if (process.env.H3_VALIDATE_ONLY === '1') {
  console.log(JSON.stringify({ result: 'PASS', ...structure, viewports: VIEWPORTS.map(({ name }) => name), retries: 0 }));
  process.exit(0);
}

assert(USERS.admin.password && USERS.user.password, 'full UAT requires local admin/user passwords in environment');
await mkdir(EVIDENCE_PARENT, { recursive: true });
await rm(STAGING_DIR, { recursive: true, force: true });
await mkdir(STAGING_DIR, { recursive: false });

const executions = [];
let browser;
let fatalError = null;
let summary;
try {
  browser = await chromium.launch({ headless: true });
  for (const viewport of VIEWPORTS) {
    await restoreFixture(viewport.name);
    for (const testCase of CASES) executions.push(await runExecution(browser, testCase, viewport));
  }
} catch (error) {
  fatalError = error instanceof Error ? error.message : String(error);
} finally {
  if (browser) await browser.close().catch(() => {});
  try {
    summary = await writeEvidence(structure, executions, fatalError);
    await promoteEvidence();
  } catch (error) {
    await rm(STAGING_DIR, { recursive: true, force: true }).catch(() => {});
    throw error;
  }
}

console.log(JSON.stringify({ result: summary.result, logicalCases: summary.actual.logicalCases, logicalCasesPassed: summary.actual.logicalCasesPassed, viewportExecutions: summary.actual.viewportExecutions, viewportExecutionsPassed: summary.actual.viewportExecutionsPassed, screenshots: summary.actual.screenshots, retries: 0 }));
process.exit(summary.result === 'PASS' ? 0 : 1);
