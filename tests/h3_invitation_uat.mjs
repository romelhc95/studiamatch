import { createRequire } from 'node:module';
import { mkdir, unlink } from 'node:fs/promises';
import { join } from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.H3_PLAYWRIGHT_MODULE || '/app/mock-server/node_modules/playwright');
const BASE_URL = process.env.H3_BASE_URL || 'http://localhost:3000';
const MOCK_URL = process.env.H3_MOCK_URL || 'http://localhost:3001';
const RESET_TOKEN = process.env.H3_TEST_RESET_TOKEN || '';
const ADMIN_EMAIL = process.env.H3_ADMIN_EMAIL || 'admin@local.test';
const ADMIN_PASSWORD = process.env.H3_ADMIN_PASSWORD || process.env.MOCK_ADMIN_PASSWORD || '';
const TOTP_CODE = process.env.H3_TOTP_CODE || process.env.MOCK_TOTP_CODE || '';
const RUN_ID = `${process.pid}-${Date.now()}`;
const MIN_INVITE_SPACING_MS = 20_100;
const EVIDENCE_DIR = process.env.H3_EVIDENCE_DIR || '';
const SCREENSHOT_DIR = EVIDENCE_DIR ? join(EVIDENCE_DIR, 'screenshots') : '';
const VIDEO_DIR = EVIDENCE_DIR ? join(EVIDENCE_DIR, 'videos') : '';
let lastInviteStartedAt = 0;

async function paceInviteRequest() {
  const waitMs = Math.max(0, MIN_INVITE_SPACING_MS - (Date.now() - lastInviteStartedAt));
  if (waitMs > 0) await new Promise((resolve) => setTimeout(resolve, waitMs));
  lastInviteStartedAt = Date.now();
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function captureCase(id, page) {
  if (!EVIDENCE_DIR) return;
  await mkdir(SCREENSHOT_DIR, { recursive: true });
  await page.screenshot({ path: join(SCREENSHOT_DIR, `${id}.png`), fullPage: true });
}

async function saveUserVideo(video) {
  if (!video || !EVIDENCE_DIR) return;
  const target = join(VIDEO_DIR, 'onboarding-user-flow.webm');
  const generated = await video.path();
  await video.saveAs(target);
  if (generated !== target) await unlink(generated);
}

async function mockRequest(path, options = {}) {
  assert(RESET_TOKEN, 'missing H3_TEST_RESET_TOKEN');
  const response = await fetch(`${MOCK_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      'x-h3-test-token': RESET_TOKEN,
      ...(options.headers || {}),
    },
  });
  const body = await response.json().catch(() => null);
  return { response, body };
}

async function resetMock() {
  const { response } = await mockRequest('/__test/reset', { method: 'POST' });
  assert(response.status === 204, `mock reset failed: ${response.status}`);
}

async function readInbox(email) {
  const { response, body } = await mockRequest(`/__test/inbox?email=${encodeURIComponent(email)}`);
  assert(response.ok, `inbox read failed: ${response.status}`);
  assert(Array.isArray(body?.messages), 'inbox response has no messages');
  assert(body.messages.length > 0, `no message delivered to ${email}`);
  return body.messages.at(-1);
}

async function loginAdmin(page) {
  await page.goto(`${BASE_URL}/admin/login/`, { waitUntil: 'networkidle' });
  await page.getByLabel('Email').fill(ADMIN_EMAIL);
  await page.getByLabel('Password').fill(ADMIN_PASSWORD);
  await page.getByRole('button', { name: 'Iniciar sesión' }).click();
  await page.waitForURL(`${BASE_URL}/admin/`);
  await page.getByRole('button', { name: /Configurar MFA|Reiniciar configuración MFA/ }).first().click();
  await page.getByLabel('Código de 6 dígitos').waitFor({ state: 'visible' });
  await page.getByLabel('Código de 6 dígitos').fill(TOTP_CODE);
  await page.getByRole('button', { name: 'Verificar MFA' }).click();
  await page.getByRole('heading', { name: 'Cola editorial' }).waitFor({ state: 'visible' });
  await page.waitForFunction(() => fetch('/api/admin/session', { cache: 'no-store' })
    .then((response) => response.json())
    .then((body) => body.authenticated === true && body.session?.aal === 'aal2')
    .catch(() => false), undefined, { timeout: 10000 });
}

async function directInvite(page, email, role, resend = false, extra = {}) {
  await paceInviteRequest();
  return page.evaluate(async ({ emailValue, roleValue, resendValue, extraValue }) => {
    const result = await fetch('/api/admin/invitations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: emailValue, role: roleValue, resend: resendValue, ...extraValue }),
    });
    return { status: result.status, body: await result.json().catch(() => null) };
  }, { emailValue: email, roleValue: role, resendValue: resend, extraValue: extra });
}

async function inviteFromUi(page, email, role) {
  await page.goto(`${BASE_URL}/admin/users/`, { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Gestión de usuarios' }).waitFor({ state: 'visible' });
  await page.getByLabel('Email').fill(email);
  await page.getByRole('combobox').click();
  await page.getByRole('option', { name: role === 'admin' ? 'Admin' : 'User' }).click();
  const button = page.getByRole('button', { name: 'Agregar usuario' });
  assert(await button.isEnabled(), 'invitation UI remained disabled after the session reached AAL2');
  await paceInviteRequest();
  const appOrigin = new URL(BASE_URL).origin;
  const responsePromise = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.origin === appOrigin && url.pathname === '/api/admin/invitations';
  }, { timeout: 60000 });
  await button.click();
  const response = await responsePromise;
  assert(response.status() === 200, `UI invitation failed: ${response.status()} ${await response.text()}`);
  const body = await response.json();
  assert(body.success === true, 'UI invitation did not return success');
  assert(!JSON.stringify(body).toLowerCase().includes('token'), 'admin-invite response exposed token material');
  return body;
}

async function openInvite(context, message) {
  assert(typeof message.link === 'string' && message.link.includes('/__auth/invite/'), 'fake inbox did not return an Auth invite link');
  const page = await context.newPage();
  const callbackPosts = [];
  page.on('request', (request) => {
    if (request.url().includes('/api/admin/auth/callback')) callbackPosts.push(request.method());
  });
  await page.goto(message.link, { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Confirma tu invitación' }).waitFor({ state: 'visible' });
  assert(callbackPosts.length === 0, 'opening the email link must not consume its one-time token');
  await page.getByRole('button', { name: 'Continuar con la invitación' }).click();
  await page.waitForURL(`${BASE_URL}/admin/auth/callback/?flow=invite`);
  assert(callbackPosts.includes('POST'), 'explicit confirmation must submit the one-time token to the same-origin BFF');
  return page;
}

async function openInviteExpectingError(context, message, textPattern) {
  assert(typeof message.link === 'string' && message.link.includes('/__auth/invite/'), 'fake inbox did not return an Auth invite link');
  const page = await context.newPage();
  await page.goto(message.link, { waitUntil: 'networkidle' });
  const confirmation = page.getByRole('heading', { name: 'Confirma tu invitación' });
  if (await confirmation.count()) {
    await page.getByRole('button', { name: 'Continuar con la invitación' }).click();
    await page.waitForURL(`${BASE_URL}/admin/auth/callback/?error=invalid`);
  }
  await page.getByText(textPattern).waitFor({ state: 'visible' });
  return page;
}

async function completePasswordSetup(page, password) {
  await page.getByRole('button', { name: 'Definir password' }).click();
  await page.waitForURL(`${BASE_URL}/admin/setup-password/`);
  const requests = [];
  page.on('request', (request) => {
    if (request.url().includes('/api/admin/auth/password') || request.url().includes('/api/admin/rpc')) {
      requests.push({ url: request.url(), body: request.postData() || '' });
    }
  });
  await page.getByLabel('Nueva contraseña', { exact: true }).fill(password);
  await page.getByLabel('Confirmar contraseña', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Guardar password' }).click();
  await page.waitForURL(`${BASE_URL}/admin/`);
  assert(requests.some((request) => request.url.endsWith('/api/admin/auth/password') && request.body.includes(password)), 'BFF Auth password update was not observed');
  const rpcWithPassword = requests.find((request) => request.url.includes('/api/admin/rpc') && request.body.includes(password));
  assert(!rpcWithPassword, 'password was sent to an onboarding RPC');
  return requests.map((request) => ({ url: request.url, containsPassword: request.body.includes(password) }));
}

async function assertInvitationPage(page, heading) {
  await page.getByRole('heading', { name: heading }).waitFor({ state: 'visible' });
}

async function run() {
  assert(ADMIN_PASSWORD, 'missing admin password');
  assert(TOTP_CODE, 'missing TOTP code');
  await resetMock();
  const browser = await chromium.launch({ headless: true, executablePath: process.env.H3_CHROMIUM_PATH || '/ms-playwright/chromium-1228/chrome-linux64/chrome' });
  const adminContext = await browser.newContext();
  const adminPage = await adminContext.newPage();
  const results = [];
  let userContext;
  let userPage;
  let userVideo;

  try {
    await loginAdmin(adminPage);

    const userEmail = `uat-user-${RUN_ID}@local.test`;
    const userPassword = `UatUser-${RUN_ID}!9x`;
    await inviteFromUi(adminPage, userEmail, 'user');
    const userMessage = await readInbox(userEmail);
    const scannerContext = await browser.newContext();
    const scannerPage = await scannerContext.newPage();
    const scannerCallbackPosts = [];
    scannerPage.on('request', (request) => {
      if (request.url().includes('/api/admin/auth/callback')) scannerCallbackPosts.push(request.method());
    });
    await scannerPage.goto(userMessage.link, { waitUntil: 'networkidle' });
    await scannerPage.getByRole('heading', { name: 'Confirma tu invitación' }).waitFor({ state: 'visible' });
    assert(scannerCallbackPosts.length === 0, 'mail-link scanner GET must not consume the invitation token');
    await captureCase('INV-013', scannerPage);
    await scannerContext.close();
    results.push({ id: 'INV-013', result: 'PASS' });

    if (EVIDENCE_DIR) await mkdir(VIDEO_DIR, { recursive: true });
    userContext = await browser.newContext(EVIDENCE_DIR
      ? { recordVideo: { dir: VIDEO_DIR, size: { width: 1280, height: 720 } } }
      : {});
    userPage = await openInvite(userContext, userMessage);
    userVideo = userPage.video();
    await assertInvitationPage(userPage, 'Invitación aceptada');
    let acceptanceRouteReached = false;
    let bouncedAfterAcceptanceRoute = false;
    userPage.on('framenavigated', (frame) => {
      if (frame !== userPage.mainFrame()) return;
      const pathname = new URL(frame.url()).pathname;
      if (pathname === '/admin/accept-invite/') acceptanceRouteReached = true;
      else if (acceptanceRouteReached && ['/admin/', '/admin/login/'].includes(pathname)) bouncedAfterAcceptanceRoute = true;
    });
    await userPage.goto(`${BASE_URL}/admin/`);
    await userPage.waitForURL(`${BASE_URL}/admin/accept-invite/`);
    await userPage.getByRole('heading', { name: 'Invitación aceptada' }).waitFor({ state: 'visible' });
    await userPage.getByText('La invitación quedó asociada a tu cuenta. Define tu password inicial para activar el acceso editorial.').waitFor({ state: 'visible' });
    assert(await userPage.getByRole('button', { name: 'Definir password' }).isVisible(), 'pending invite session must return to password setup, not the login redirect loop');
    assert(await userPage.getByText('Panel de actualización de información').count() === 0, 'pending invite session must not reach the editorial panel before password setup');
    // Prior focused diagnosis observed six /admin ↔ /admin/login transitions in 1.25 s.
    await userPage.waitForTimeout(1250);
    assert(new URL(userPage.url()).pathname === '/admin/accept-invite/', 'password-pending invite route remains stable');
    assert(!bouncedAfterAcceptanceRoute, 'password-pending invite does not restart the admin/login redirect loop');
    await captureCase('INV-008', userPage);
    results.push({ id: 'INV-008', result: 'PASS' });
    const userRequests = await completePasswordSetup(userPage, userPassword);
    await userPage.getByText('Panel de actualización de información').waitFor({ state: 'visible' });
    await captureCase('INV-001', userPage);
    results.push({ id: 'INV-001', result: 'PASS', requests: userRequests });
    await userContext.close();
    await saveUserVideo(userVideo);
    userContext = undefined;
    userVideo = undefined;

    const adminEmail = `uat-admin-${RUN_ID}@local.test`;
    const adminPassword = `UatAdmin-${RUN_ID}!9x`;
    await inviteFromUi(adminPage, adminEmail, 'admin');
    const adminMessage = await readInbox(adminEmail);
    const invitedAdminContext = await browser.newContext();
    const adminInvitePage = await openInvite(invitedAdminContext, adminMessage);
    await adminInvitePage.getByRole('heading', { name: 'Invitación aceptada' }).waitFor({ state: 'visible' });
    await completePasswordSetup(adminInvitePage, adminPassword);
    await adminInvitePage.getByRole('link', { name: 'Usuarios' }).waitFor({ state: 'visible' });
    await captureCase('INV-002', adminInvitePage);
    results.push({ id: 'INV-002', result: 'PASS' });
    await invitedAdminContext.close();

    const redirectEmail = `uat-redirect-${RUN_ID}@local.test`;
    const redirectInvite = await directInvite(adminPage, redirectEmail, 'user', false, { next: 'https://evil.example/' });
    assert(redirectInvite.status === 200, `redirect allowlist fixture failed: ${redirectInvite.status}`);
    assert(!JSON.stringify(redirectInvite.body).includes('evil.example'), 'external redirect was echoed by admin-invite');
    await captureCase('INV-009', adminPage);
    results.push({ id: 'INV-009', result: 'PASS' });

    const pendingEmail = `uat-pending-${RUN_ID}@local.test`;
    await directInvite(adminPage, pendingEmail, 'user');
    const pendingMessage = await readInbox(pendingEmail);
    const passwordPendingContext = await browser.newContext();
    const pendingPage = await openInvite(passwordPendingContext, pendingMessage);
    await assertInvitationPage(pendingPage, 'Invitación aceptada');
    await pendingPage.goto(`${BASE_URL}/admin/accept-invite/`);
    await pendingPage.getByText(/password inicial/i).waitFor({ state: 'visible' });
    await pendingPage.getByRole('button', { name: 'Definir password' }).click();
    await pendingPage.waitForURL(`${BASE_URL}/admin/setup-password/`);
    await pendingPage.getByLabel('Nueva contraseña', { exact: true }).waitFor({ state: 'visible' });
    await captureCase('INV-007', pendingPage);
    results.push({ id: 'INV-007', result: 'PASS' });
    await passwordPendingContext.close();

    const expiredEmail = `uat-expired-${RUN_ID}@local.test`;
    const expiredInvite = await directInvite(adminPage, expiredEmail, 'user');
    assert(expiredInvite.status === 200, `expired fixture invite failed: ${expiredInvite.status}`);
    const expiredMessage = await readInbox(expiredEmail);
    await mockRequest('/__test/clock', { method: 'POST', body: JSON.stringify({ advance_seconds: 86401 }) });
    const expiredContext = await browser.newContext();
    const expiredPage = await openInviteExpectingError(expiredContext, expiredMessage, /expiró|inválido/i);
    await captureCase('INV-003', expiredPage);
    results.push({ id: 'INV-003', result: 'PASS' });
    await expiredContext.close();
    await mockRequest('/__test/clock', { method: 'POST', body: JSON.stringify({ reset: true }) });

    const revokedEmail = `uat-revoked-${RUN_ID}@local.test`;
    const revokedInvite = await directInvite(adminPage, revokedEmail, 'user');
    assert(revokedInvite.status === 200, `revoked fixture invite failed: ${revokedInvite.status}`);
    const revokedMessage = await readInbox(revokedEmail);
    await mockRequest('/__test/invitation', { method: 'POST', body: JSON.stringify({ invitation_id: revokedInvite.body.invitation_id, action: 'revoke' }) });
    const revokedContext = await browser.newContext();
    const revokedPage = await openInviteExpectingError(revokedContext, revokedMessage, /revocada|inválido/i);
    await captureCase('INV-004', revokedPage);
    results.push({ id: 'INV-004', result: 'PASS' });
    await revokedContext.close();
    await mockRequest('/__test/clock', { method: 'POST', body: JSON.stringify({ reset: true }) });

    const resendEmail = `uat-resend-${RUN_ID}@local.test`;
    const firstInvite = await directInvite(adminPage, resendEmail, 'user');
    assert(firstInvite.status === 200, `resend initial invite failed: ${firstInvite.status}`);
    const oldMessage = await readInbox(resendEmail);
    await mockRequest('/__test/clock', { method: 'POST', body: JSON.stringify({ advance_seconds: 61 }) });
    const resendInvite = await directInvite(adminPage, resendEmail, 'user', true);
    assert(resendInvite.status === 200 && resendInvite.body.resent === true, 'resend did not supersede the pending invitation');
    const newMessage = await readInbox(resendEmail);
    const oldContext = await browser.newContext();
    const oldPage = await openInviteExpectingError(oldContext, oldMessage, /reemplazada|inválido/i);
    await oldContext.close();
    const newContext = await browser.newContext();
    const newPage = await openInvite(newContext, newMessage);
    await newPage.getByRole('heading', { name: 'Invitación aceptada' }).waitFor({ state: 'visible' });
    await captureCase('INV-005', newPage);
    results.push({ id: 'INV-005', result: 'PASS' });
    await newContext.close();

    const callbackContext = await browser.newContext();
    const callbackPage = await openInviteExpectingError(callbackContext, newMessage, /utilizado|inválido/i);
    await captureCase('INV-012', callbackPage);
    results.push({ id: 'INV-012', result: 'PASS' });
    await callbackContext.close();

    console.log(JSON.stringify({ result: 'PASS', minimumInviteSpacingMs: MIN_INVITE_SPACING_MS, cases: results.map(({ id, result }) => ({ id, result })), videos: EVIDENCE_DIR ? ['onboarding-user-flow.webm'] : [] }));
  } finally {
    if (userContext) await userContext.close();
    if (userVideo) await saveUserVideo(userVideo);
    await adminContext.close();
    await browser.close();
    await resetMock();
  }
}

run().catch((error) => {
  console.error(JSON.stringify({ result: 'FAIL', error: String(error.message || error) }));
  process.exitCode = 1;
});
