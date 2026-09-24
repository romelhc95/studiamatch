import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.H3_PLAYWRIGHT_MODULE || '/app/mock-server/node_modules/playwright');
const BASE_URL = process.env.H3_BASE_URL || 'http://localhost:3000';
const MOCK_URL = process.env.H3_MOCK_URL || 'http://localhost:3001';
const RESET_TOKEN = process.env.H3_TEST_RESET_TOKEN || '';
const ADMIN_EMAIL = process.env.H3_ADMIN_EMAIL || 'admin@local.test';
const ADMIN_PASSWORD = process.env.H3_ADMIN_PASSWORD || process.env.MOCK_ADMIN_PASSWORD || '';
const TOTP_CODE = process.env.H3_TOTP_CODE || process.env.MOCK_TOTP_CODE || '';
const RUN_ID = `${process.pid}-${Date.now()}`;

function assert(condition, message) {
  if (!condition) throw new Error(message);
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
  await page.getByLabel('Código MFA').waitFor({ state: 'visible' });
  await page.getByLabel('Código MFA').fill(TOTP_CODE);
  await page.getByRole('button', { name: 'Verificar MFA' }).click();
  await page.waitForURL(`${BASE_URL}/admin/`);
  await page.getByRole('heading', { name: 'Cola editorial' }).waitFor({ state: 'visible' });
}

async function sessionToken(page) {
  return page.evaluate(() => {
    const key = Object.keys(sessionStorage).find((item) => item.endsWith('-auth-token') && !item.endsWith('-code-verifier'));
    if (!key) return null;
    const value = JSON.parse(sessionStorage.getItem(key) || '{}');
    return value.access_token || null;
  });
}

async function directInvite(page, email, role, resend = false, extra = {}) {
  const token = await sessionToken(page);
  assert(token, 'admin Auth session missing');
  const response = await page.evaluate(async ({ mockUrl, emailValue, roleValue, resendValue, accessToken, extraValue }) => {
    const result = await fetch(`${mockUrl}/functions/v1/admin-invite`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        apikey: 'local-publishable-key',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ email: emailValue, role: roleValue, resend: resendValue, ...extraValue }),
    });
    return { status: result.status, body: await result.json().catch(() => null) };
  }, { mockUrl: MOCK_URL, emailValue: email, roleValue: role, resendValue: resend, accessToken: token, extraValue: extra });
  return response;
}

async function inviteFromUi(page, email, role) {
  await page.goto(`${BASE_URL}/admin/users/`, { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Gestión de usuarios' }).waitFor({ state: 'visible' });
  await page.getByLabel('Email').fill(email);
  await page.getByRole('combobox').click();
  await page.getByRole('option', { name: role === 'admin' ? 'Admin' : 'User' }).click();
  const responsePromise = page.waitForResponse((response) => response.url().endsWith('/functions/v1/admin-invite'));
  await page.getByRole('button', { name: 'Agregar usuario' }).click();
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
  await page.goto(message.link, { waitUntil: 'networkidle' });
  return page;
}

async function openInviteExpectingError(context, message, textPattern) {
  assert(typeof message.link === 'string' && message.link.includes('/__auth/invite/'), 'fake inbox did not return an Auth invite link');
  const page = await context.newPage();
  await page.goto(message.link, { waitUntil: 'networkidle' });
  await page.getByText(textPattern).waitFor({ state: 'visible' });
  return page;
}

async function completePasswordSetup(page, password) {
  await page.getByRole('button', { name: 'Definir password' }).click();
  await page.waitForURL(`${BASE_URL}/admin/setup-password/`);
  const requests = [];
  page.on('request', (request) => {
    if (request.url().includes('/auth/v1/user') || request.url().includes('/rest/v1/rpc/')) {
      requests.push({ url: request.url(), body: request.postData() || '' });
    }
  });
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByLabel('Confirmar password').fill(password);
  await page.getByRole('button', { name: 'Guardar password' }).click();
  await page.waitForURL(`${BASE_URL}/admin/`);
  assert(requests.some((request) => request.url.endsWith('/auth/v1/user') && request.body.includes(password)), 'Auth password update was not observed');
  const rpcWithPassword = requests.find((request) => request.url.includes('/rest/v1/rpc/') && request.body.includes(password));
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

  try {
    await loginAdmin(adminPage);

    const userEmail = `uat-user-${RUN_ID}@local.test`;
    const userPassword = `UatUser-${RUN_ID}!9x`;
    await inviteFromUi(adminPage, userEmail, 'user');
    const userMessage = await readInbox(userEmail);
    const userContext = await browser.newContext();
    const userPage = await openInvite(userContext, userMessage);
    await assertInvitationPage(userPage, 'Invitación aceptada');
    await userPage.goto(`${BASE_URL}/admin/`);
    await userPage.waitForURL(`${BASE_URL}/admin/login/`);
    results.push({ id: 'INV-008', result: 'PASS' });
    await userPage.goto(`${BASE_URL}/admin/accept-invite/`);
    await userPage.getByRole('heading', { name: 'Invitación aceptada' }).waitFor({ state: 'visible' });
    const userRequests = await completePasswordSetup(userPage, userPassword);
    await userPage.getByText('Panel de actualización de información').waitFor({ state: 'visible' });
    results.push({ id: 'INV-001', result: 'PASS', requests: userRequests });
    await userContext.close();

    const adminEmail = `uat-admin-${RUN_ID}@local.test`;
    const adminPassword = `UatAdmin-${RUN_ID}!9x`;
    await inviteFromUi(adminPage, adminEmail, 'admin');
    const adminMessage = await readInbox(adminEmail);
    const invitedAdminContext = await browser.newContext();
    const adminInvitePage = await openInvite(invitedAdminContext, adminMessage);
    await adminInvitePage.getByRole('heading', { name: 'Invitación aceptada' }).waitFor({ state: 'visible' });
    await completePasswordSetup(adminInvitePage, adminPassword);
    await adminInvitePage.getByRole('link', { name: 'Usuarios' }).waitFor({ state: 'visible' });
    results.push({ id: 'INV-002', result: 'PASS' });
    await invitedAdminContext.close();

    const redirectEmail = `uat-redirect-${RUN_ID}@local.test`;
    const redirectInvite = await directInvite(adminPage, redirectEmail, 'user', false, { next: 'https://evil.example/' });
    assert(redirectInvite.status === 200, `redirect allowlist fixture failed: ${redirectInvite.status}`);
    assert(!JSON.stringify(redirectInvite.body).includes('evil.example'), 'external redirect was echoed by admin-invite');
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
    await pendingPage.getByLabel('Password', { exact: true }).waitFor({ state: 'visible' });
    results.push({ id: 'INV-007', result: 'PASS' });
    await passwordPendingContext.close();

    const expiredEmail = `uat-expired-${RUN_ID}@local.test`;
    const expiredInvite = await directInvite(adminPage, expiredEmail, 'user');
    assert(expiredInvite.status === 200, `expired fixture invite failed: ${expiredInvite.status}`);
    const expiredMessage = await readInbox(expiredEmail);
    await mockRequest('/__test/clock', { method: 'POST', body: JSON.stringify({ advance_seconds: 86401 }) });
    const expiredContext = await browser.newContext();
    const expiredPage = await openInviteExpectingError(expiredContext, expiredMessage, /expiró|inválido/i);
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
    results.push({ id: 'INV-005', result: 'PASS' });
    await newContext.close();

    const callbackContext = await browser.newContext();
    const callbackPage = await openInviteExpectingError(callbackContext, newMessage, /utilizado|inválido/i);
    results.push({ id: 'INV-012', result: 'PASS' });
    await callbackContext.close();

    console.log(JSON.stringify({ result: 'PASS', cases: results.map(({ id, result }) => ({ id, result })) }));
  } finally {
    await adminContext.close();
    await browser.close();
    await resetMock();
  }
}

run().catch((error) => {
  console.error(JSON.stringify({ result: 'FAIL', error: String(error.message || error) }));
  process.exitCode = 1;
});
