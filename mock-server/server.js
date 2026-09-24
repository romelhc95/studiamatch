const http = require('http');
const crypto = require('crypto');
const { Pool } = require('pg');
const url = require('url');

const FIXTURES = {
  'admin@local.test': { role: 'admin', sub: '30000000-0000-0000-0000-000000000001', passwordEnv: 'MOCK_ADMIN_PASSWORD' },
  'user@local.test': { role: 'user', sub: '31000000-0000-0000-0000-000000000002', passwordEnv: 'MOCK_USER_PASSWORD' },
  'auth@local.test': { role: 'authenticated', sub: '31000000-0000-0000-0000-000000000003', passwordEnv: 'MOCK_AUTH_PASSWORD' },
  'inactive@local.test': { role: 'inactive', sub: '31000000-0000-0000-0000-000000000004', passwordEnv: 'MOCK_INACTIVE_PASSWORD' },
};

const requiredEnvironment = [
  'MOCK_DB_PASSWORD',
  'MOCK_TOTP_CODE',
  'H3_TEST_RESET_TOKEN',
  ...Object.values(FIXTURES).map((fixture) => fixture.passwordEnv),
];
const missingEnvironment = requiredEnvironment.filter((name) => !process.env[name]);
if (missingEnvironment.length > 0) {
  throw new Error('Required mock environment is missing');
}

const pool = new Pool({
  host: process.env.MOCK_DB_HOST || '172.17.0.3',
  port: 5432,
  database: process.env.MOCK_DB_NAME || 'studiamatch_h3',
  user: process.env.MOCK_DB_USER || 'postgres',
  password: process.env.MOCK_DB_PASSWORD,
});
const sessions = new Map();
const factors = new Map();
const challenges = new Map();
const pkceCodes = new Map();
const authUsers = new Map(Object.entries(FIXTURES).map(([email, fixture]) => [email, {
  id: fixture.sub,
  email,
  password: process.env[fixture.passwordEnv],
  emailConfirmed: true,
  role: fixture.role,
  invitationToken: null,
}]));
const invitationRecords = new Map();
const inboxMessages = new Map();
const temporaryUserIds = new Set();
const temporaryInvitationIds = new Set();
let mockClockOffsetMs = 0;

const TEST_TOKEN = process.env.H3_TEST_RESET_TOKEN;
const APP_ORIGIN = process.env.MOCK_APP_ORIGIN || 'http://localhost:3000';
const MOCK_ORIGIN = process.env.MOCK_PUBLIC_ORIGIN || `http://localhost:${process.env.PORT || 3001}`;
const INVITE_REDIRECT_URL = process.env.MOCK_ADMIN_INVITE_REDIRECT_URL || `${APP_ORIGIN}/admin/auth/callback/`;
const INVITE_ALLOWED_REDIRECTS = (process.env.MOCK_ADMIN_INVITE_ALLOWED_REDIRECTS || INVITE_REDIRECT_URL)
  .split(',').map((value) => value.trim()).filter(Boolean);
const RESEND_COOLDOWN_SECONDS = Number.isFinite(Number(process.env.MOCK_ADMIN_INVITE_RESEND_COOLDOWN_SECONDS))
  ? Math.max(0, Number(process.env.MOCK_ADMIN_INVITE_RESEND_COOLDOWN_SECONDS))
  : 60;

function now() {
  return new Date(Date.now() + mockClockOffsetMs);
}

function nowIso() {
  return now().toISOString();
}

async function resetMockState() {
  if (temporaryInvitationIds.size > 0) {
    await pool.query(
      "UPDATE public.admin_invitations SET status = 'revoked', revoked_at = COALESCE(revoked_at, now()), revoked_by_user_id = $1 WHERE id = ANY($2::uuid[]) AND status = 'pending'",
      [FIXTURES['admin@local.test'].sub, [...temporaryInvitationIds]],
    );
  }
  if (temporaryUserIds.size > 0) {
    await pool.query('DELETE FROM public.admin_members WHERE user_id = ANY($1::uuid[])', [[...temporaryUserIds]]);
    await pool.query('DELETE FROM auth.users WHERE id = ANY($1::uuid[])', [[...temporaryUserIds]]);
  }
  sessions.clear();
  factors.clear();
  challenges.clear();
  pkceCodes.clear();
  invitationRecords.clear();
  inboxMessages.clear();
  temporaryUserIds.clear();
  temporaryInvitationIds.clear();
  mockClockOffsetMs = 0;
  for (const email of authUsers.keys()) {
    if (!Object.prototype.hasOwnProperty.call(FIXTURES, email)) authUsers.delete(email);
  }
  for (const [email, fixture] of Object.entries(FIXTURES)) {
    authUsers.set(email, {
      id: fixture.sub,
      email,
      password: process.env[fixture.passwordEnv],
      emailConfirmed: true,
      role: fixture.role,
      invitationToken: null,
    });
  }

  // Recreate the stable local RBAC identities before each browser run. The
  // canonical seed intentionally uses different emails, so the mock owns
  // these IDs and keeps the UAT independent from prior local mutations.
  for (const fixture of Object.values(FIXTURES)) {
    await pool.query(
      `INSERT INTO auth.users (id, email, role, aud, email_confirmed_at, created_at, updated_at)
       VALUES ($1, $2, 'authenticated', 'authenticated', now(), now(), now())
       ON CONFLICT (id) DO NOTHING`,
      [fixture.sub, Object.entries(FIXTURES).find(([, value]) => value === fixture)?.[0] || 'fixture@local.test'],
    );
    if (fixture.role === 'admin' || fixture.role === 'user' || fixture.role === 'inactive') {
      await pool.query(
        `INSERT INTO public.admin_members (user_id, role, is_active, account_status)
         VALUES ($1, $2, $3, 'ready')
         ON CONFLICT (user_id) DO UPDATE
           SET role = EXCLUDED.role,
               is_active = EXCLUDED.is_active,
               account_status = 'ready'`,
        [fixture.sub, fixture.role === 'inactive' ? 'user' : fixture.role, fixture.role !== 'inactive'],
      );
    }
  }
}

function testRequestAllowed(req) {
  return process.env.NODE_ENV === 'test' && req.headers['x-h3-test-token'] === TEST_TOKEN;
}

function normalizeEmail(value) {
  return typeof value === 'string' ? value.trim().toLowerCase() : '';
}

function validEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function getIdentity(email) {
  const normalized = normalizeEmail(email);
  const identity = authUsers.get(normalized);
  if (!identity) return null;
  const fixture = FIXTURES[normalized];
  return {
    ...(fixture || {}),
    ...identity,
    email: normalized,
    sub: identity.id,
    role: identity.role || fixture?.role || 'authenticated',
  };
}

function issueInvitationToken() {
  return crypto.randomBytes(32).toString('base64url');
}

function invitationByToken(token) {
  for (const record of invitationRecords.values()) {
    if (record.token === token) return record;
  }
  return null;
}

function invitationIsExpired(record) {
  return !record || new Date(record.expiresAt).getTime() <= now().getTime();
}

function invitationRedirect() {
  if (!INVITE_REDIRECT_URL || !INVITE_ALLOWED_REDIRECTS.includes(INVITE_REDIRECT_URL)) return null;
  try {
    const parsed = new URL(INVITE_REDIRECT_URL);
    if ((parsed.protocol !== 'https:' && !['localhost', '127.0.0.1'].includes(parsed.hostname)) || parsed.username || parsed.password || parsed.hash) return null;
    return parsed.toString();
  } catch {
    return null;
  }
}

function fakeInboxLink(token) {
  return `${MOCK_ORIGIN.replace(/\/$/, '')}/__auth/invite/${encodeURIComponent(token)}`;
}

function authErrorResponse(res, error, description = error) {
  sendJson(res, 400, { error, error_description: description, msg: description, message: description });
}

async function queryAuthUser(email) {
  const normalized = normalizeEmail(email);
  const known = getIdentity(normalized);
  if (known) return known;
  const result = await pool.query('SELECT id, email, email_confirmed_at FROM auth.users WHERE lower(email::text) = $1 LIMIT 1', [normalized]);
  const row = result.rows[0];
  if (!row) return null;
  const identity = {
    id: row.id,
    email: normalized,
    password: null,
    emailConfirmed: Boolean(row.email_confirmed_at),
    role: 'authenticated',
    invitationToken: null,
  };
  authUsers.set(normalized, identity);
  temporaryUserIds.add(identity.id);
  return getIdentity(normalized);
}

async function ensureAuthUser(email) {
  const normalized = normalizeEmail(email);
  const existing = await queryAuthUser(normalized);
  if (existing) return existing;
  const identity = {
    id: crypto.randomUUID(),
    email: normalized,
    password: null,
    emailConfirmed: false,
    role: 'authenticated',
    invitationToken: null,
  };
  await pool.query(
    'INSERT INTO auth.users (id, email) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING',
    [identity.id, normalized],
  );
  authUsers.set(normalized, identity);
  return getIdentity(normalized);
}

async function readInvitation(invitationId) {
  const result = await pool.query(
    'SELECT id, email, role, status, expires_at, last_sent_at, admin_member_user_id, resend_of_invitation_id FROM public.admin_invitations WHERE id = $1',
    [invitationId],
  );
  return result.rows[0] || null;
}

async function syncVirtualExpiry() {
  const expiredIds = [];
  for (const record of invitationRecords.values()) {
    if (record.status === 'pending' && invitationIsExpired(record)) expiredIds.push(record.id);
  }
  if (expiredIds.length === 0) return;
  await pool.query(
    "UPDATE public.admin_invitations SET status = 'expired' WHERE id = ANY($1::uuid[]) AND status = 'pending'",
    [expiredIds],
  );
  for (const id of expiredIds) {
    const record = invitationRecords.get(id);
    if (record) record.status = 'expired';
  }
}

async function persistInvitationRecord(invitationId, token, identity) {
  const row = await readInvitation(invitationId);
  if (!row) throw new Error('Invitation persistence record not found');
  const record = {
    id: row.id,
    email: row.email,
    role: row.role,
    status: row.status,
    expiresAt: row.expires_at,
    lastSentAt: row.last_sent_at,
    token,
    userId: identity.id,
    redirectTo: invitationRedirect(),
  };
  invitationRecords.set(record.id, record);
  temporaryInvitationIds.add(record.id);
  identity.invitationToken = token;
  return record;
}

function deliverInvitation(record, resent) {
  const message = {
    id: crypto.randomUUID(),
    to: record.email,
    subject: 'Invitación a StudIAMatch',
    createdAt: nowIso(),
    expiresAt: record.expiresAt,
    invitationId: record.id,
    status: 'delivered',
    resent: Boolean(resent),
    link: fakeInboxLink(record.token),
  };
  inboxMessages.set(message.id, message);
  return message;
}

function isAdminInviteActor(fixture) {
  return Boolean(fixture && fixture.role === 'admin' && (fixture.aal === 'aal2' || (factors.get(fixture.sub) || []).some((factor) => factor.status === 'verified')));
}

function parseBody(req) {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      try { resolve(JSON.parse(body)); } catch { resolve({}); }
    });
  });
}

function sendJson(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(body));
}

function badRequest(res, message) {
  sendJson(res, 400, { message });
}

function notFound(res) {
  sendJson(res, 404, { message: 'Not found' });
}

function unauthorized(res) {
  sendJson(res, 401, { message: 'Invalid or expired session' });
}

function issueSession(email, aal = 'aal1') {
  const fixture = getIdentity(email);
  if (!fixture) return null;
  const issuedAt = Math.floor(now().getTime() / 1000);
  const expiresAt = now().getTime() + 3600 * 1000;
  const payload = {
    aud: 'authenticated',
    exp: Math.floor(expiresAt / 1000),
    iat: issuedAt,
    role: 'authenticated',
    sub: fixture.sub,
    aal,
  };
  const encodeSegment = (value) => Buffer.from(JSON.stringify(value)).toString('base64url');
  const token = `${encodeSegment({ alg: 'HS256', typ: 'JWT' })}.${encodeSegment(payload)}.${crypto.randomBytes(24).toString('base64url')}`;
  sessions.set(token, { ...fixture, email: fixture.email, aal, expiresAt });
  return { token, fixture: sessions.get(token) };
}

function sessionPayload(session) {
  return {
    access_token: session.token,
    refresh_token: session.token,
    expires_in: 3600,
    expires_at: Math.floor(session.fixture.expiresAt / 1000),
    token_type: 'bearer',
    user: { id: session.fixture.sub, email: session.fixture.email, role: 'authenticated' },
    aal: session.fixture.aal,
  };
}

function getFixture(req) {
  const auth = req.headers.authorization || '';
  const parts = auth.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') return null;
  const session = sessions.get(parts[1]) || null;
  if (session && session.expiresAt <= now().getTime()) {
    sessions.delete(parts[1]);
    return null;
  }
  return session;
}

async function withIdentity(fixture, callback) {
  const client = await pool.connect();
  try {
    const effectiveAal = fixture.aal === 'aal2' || (factors.get(fixture.sub) || []).some((factor) => factor.status === 'verified') ? 'aal2' : 'aal1';
    await client.query('BEGIN');
    await client.query('SELECT set_config($1, $2, true)', ['request.jwt.claim.sub', fixture.sub]);
    await client.query('SELECT set_config($1, $2, true)', ['request.jwt.claim.aal', effectiveAal]);
    await client.query('SELECT set_config($1, $2, true)', ['request.jwt.claims', JSON.stringify({ sub: fixture.sub, aal: effectiveAal, role: 'authenticated' })]);
    const result = await callback(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

function writeRows(res, result) {
  sendJson(res, 200, result.rows);
}

function redirectForInvitation(res, record, error) {
  const redirectTo = record?.redirectTo || invitationRedirect() || INVITE_REDIRECT_URL;
  const target = new URL(redirectTo);
  if (error) {
    target.searchParams.set('error', 'access_denied');
    target.searchParams.set('error_code', error);
    target.searchParams.set('error_description', 'Invitation is not available');
  }
  res.writeHead(302, { Location: target.toString() });
  res.end();
}

function redirectWithInviteSession(res, record) {
  const target = new URL(record.redirectTo || invitationRedirect() || INVITE_REDIRECT_URL);
  const session = issueSession(record.email);
  if (!session) return redirectForInvitation(res, record, 'missing_auth_user');
  target.hash = new URLSearchParams({
    access_token: session.token,
    refresh_token: session.token,
    expires_in: '3600',
    token_type: 'bearer',
    type: 'invite',
  }).toString();
  res.writeHead(302, { Location: target.toString() });
  return res.end();
}

async function handleAdminInvite(req, res) {
  const actor = getFixture(req);
  if (!actor) return unauthorized(res);
  if (!isAdminInviteActor(actor)) return sendJson(res, 403, { error: 'MFA aal2 required', code: 'mfa_required' });
  const redirectTo = invitationRedirect();
  if (!redirectTo) return sendJson(res, 500, { error: 'Invitation redirect is not configured', code: 'redirect_not_configured' });

  const body = await parseBody(req);
  const email = normalizeEmail(body.email);
  const role = typeof body.role === 'string' ? body.role.trim().toLowerCase() : '';
  const resend = body.resend === true || body.resend === 'true';
  const requestId = typeof req.headers['x-request-id'] === 'string' && /^[A-Za-z0-9._:-]{1,100}$/.test(req.headers['x-request-id'])
    ? req.headers['x-request-id']
    : crypto.randomUUID();
  if (!validEmail(email)) return sendJson(res, 400, { error: 'Invalid email', code: 'invalid_email', request_id: requestId });
  if (!['admin', 'user'].includes(role)) return sendJson(res, 400, { error: 'Invalid role: must be admin or user', code: 'invalid_role', request_id: requestId });

  await syncVirtualExpiry();
  const existingIdentity = await queryAuthUser(email);
  const identity = existingIdentity || await ensureAuthUser(email);
  const existingMember = await pool.query(
    'SELECT user_id, role, account_status, is_active FROM public.admin_members WHERE user_id = $1',
    [identity.id],
  );
  const member = existingMember.rows[0] || null;
  if (member?.role && member.role !== role) return sendJson(res, 409, { error: 'Existing membership role must be managed separately', code: 'role_mismatch', request_id: requestId });
  if (member?.account_status === 'ready') return sendJson(res, 409, { error: 'User already has a ready membership', code: 'duplicate_ready', request_id: requestId });
  if (member && ['inactive', 'revoked'].includes(member.account_status)) return sendJson(res, 409, { error: 'User membership is inactive or revoked', code: 'membership_blocked', request_id: requestId });
  if (member && !['invited'].includes(member.account_status)) return sendJson(res, 409, { error: 'User onboarding is already in progress', code: 'onboarding_in_progress', request_id: requestId });
  if (identity.emailConfirmed && !member) {
    identity.emailConfirmed = false;
    identity.password = null;
  }

  const pendingResult = await pool.query(
    "SELECT id, status, expires_at, last_sent_at FROM public.admin_invitations WHERE email = $1 AND status = 'pending' ORDER BY created_at DESC LIMIT 1",
    [email],
  );
  const pending = pendingResult.rows[0] || null;
  if (pending && !resend) return sendJson(res, 409, { error: 'Invitation already pending', code: 'duplicate_pending', request_id: requestId });
  if (pending && resend && now().getTime() - new Date(pending.last_sent_at).getTime() < RESEND_COOLDOWN_SECONDS * 1000) {
    return sendJson(res, 409, { error: 'Invitation resend is temporarily unavailable', code: 'resend_cooldown', request_id: requestId });
  }

  const result = await withIdentity(actor, async (client) => client.query(
    'SELECT * FROM public.admin_invitation_reserve($1, $2, $3, $4, $5, $6, $7::jsonb, $8)',
    [email, role, actor.sub, identity.id, resend, requestId, JSON.stringify({ source: 'admin-invite', environment: 'test', redirect_origin: new URL(redirectTo).origin }), new Date(now().getTime() - (RESEND_COOLDOWN_SECONDS * 1000)).toISOString()],
  ));
  const reserved = result.rows[0];
  if (!reserved?.success) {
    const status = ['duplicate_pending', 'resend_cooldown', 'duplicate_ready', 'membership_blocked', 'onboarding_in_progress', 'role_mismatch'].includes(reserved?.error_code) ? 409 : 400;
    return sendJson(res, status, { error: reserved?.error_code || 'Invitation could not be reserved', code: reserved?.error_code || 'persistence_failed', request_id: requestId });
  }

  const completed = await withIdentity(actor, async (client) => client.query(
    'SELECT * FROM public.admin_invitation_complete($1, $2)',
    [reserved.invitation_id, identity.id],
  ));
  if (!completed.rows[0]?.success) {
    return sendJson(res, 500, { error: 'Invitation persistence requires reconciliation', code: 'reconciliation_required', request_id: requestId });
  }

  const token = issueInvitationToken();
  const record = await persistInvitationRecord(reserved.invitation_id, token, identity);
  if (pending && reserved.resent) {
    const previous = invitationRecords.get(pending.id);
    if (previous) previous.status = 'superseded';
  }
  deliverInvitation(record, reserved.resent);
  return sendJson(res, 200, {
    success: true,
    email,
    user_id: identity.id,
    invitation_id: record.id,
    status: 'pending',
    resent: Boolean(reserved.resent),
  });
}

const server = http.createServer(async (req, res) => {
  const parsed = url.parse(req.url, true);
  const pathname = parsed.pathname;

  const origin = req.headers.origin;
  const allowedOrigin = origin === APP_ORIGIN ? origin : '*';
  res.setHeader('Access-Control-Allow-Origin', allowedOrigin);
  if (allowedOrigin !== '*') res.setHeader('Vary', 'Origin');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, apikey, Authorization, x-client-info, x-request-id, x-supabase-api-version');
  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  try {
    if (pathname === '/__test/reset' && req.method === 'POST') {
      if (!testRequestAllowed(req)) return notFound(res);
      await resetMockState();
      res.writeHead(204);
      return res.end();
    }

    if (pathname === '/__test/inbox' && req.method === 'GET') {
      if (!testRequestAllowed(req)) return notFound(res);
      await syncVirtualExpiry();
      const email = normalizeEmail(parsed.query.email);
      const messages = [...inboxMessages.values()]
        .filter((message) => !email || message.to === email)
        .map((message) => ({ ...message }));
      return sendJson(res, 200, { messages });
    }

    if (pathname === '/__test/clock' && req.method === 'POST') {
      if (!testRequestAllowed(req)) return notFound(res);
      const body = await parseBody(req);
      if (body.reset === true) {
        mockClockOffsetMs = 0;
        return sendJson(res, 200, { now: nowIso() });
      }
      const seconds = Number(body.advance_seconds);
      if (!Number.isFinite(seconds) || seconds < 0 || seconds > 7 * 24 * 60 * 60) return badRequest(res, 'Invalid clock advance');
      mockClockOffsetMs += seconds * 1000;
      await syncVirtualExpiry();
      return sendJson(res, 200, { now: nowIso() });
    }

    if (pathname === '/__test/invitation' && req.method === 'POST') {
      if (!testRequestAllowed(req)) return notFound(res);
      const body = await parseBody(req);
      const invitationId = typeof body.invitation_id === 'string' ? body.invitation_id : '';
      const action = typeof body.action === 'string' ? body.action : '';
      if (!invitationId || !['revoke', 'expire'].includes(action)) return badRequest(res, 'Invalid invitation action');
      if (action === 'expire') {
        mockClockOffsetMs = Math.max(mockClockOffsetMs, 24 * 60 * 60 * 1000 + 1000);
        await syncVirtualExpiry();
      } else {
        await pool.query("UPDATE public.admin_invitations SET status = 'revoked', revoked_at = now(), revoked_by_user_id = $1 WHERE id = $2 AND status = 'pending'", [FIXTURES['admin@local.test'].sub, invitationId]);
        const record = invitationRecords.get(invitationId);
        if (record) record.status = 'revoked';
      }
      return sendJson(res, 200, { invitation_id: invitationId, action });
    }

    if (pathname === '/__test/pkce' && req.method === 'POST') {
      if (!testRequestAllowed(req)) return notFound(res);
      const body = await parseBody(req);
      const fixture = getIdentity(body.email);
      if (!fixture || typeof body.code_verifier !== 'string' || !body.code_verifier) return badRequest(res, 'Invalid PKCE fixture');
      const code = crypto.randomBytes(24).toString('base64url');
      pkceCodes.set(code, { email: normalizeEmail(body.email), userId: fixture.sub, codeVerifier: body.code_verifier, used: false, createdAt: now().getTime(), expiresAt: now().getTime() + (5 * 60 * 1000) });
      return sendJson(res, 200, { code });
    }

    if (pathname.startsWith('/__auth/invite/') && req.method === 'GET') {
      if (process.env.NODE_ENV !== 'test') return notFound(res);
      const token = decodeURIComponent(pathname.slice('/__auth/invite/'.length));
      const record = invitationByToken(token);
      if (!record) return notFound(res);
      if (record.status !== 'pending') return redirectForInvitation(res, record, `invitation_${record.status}`);
      const target = new URL(`${MOCK_ORIGIN}/auth/v1/verify`);
      target.searchParams.set('token', token);
      target.searchParams.set('type', 'invite');
      target.searchParams.set('redirect_to', record.redirectTo);
      res.writeHead(302, { Location: target.toString() });
      return res.end();
    }

    if (pathname === '/auth/v1/verify' && req.method === 'GET') {
      if (process.env.NODE_ENV !== 'test') return notFound(res);
      const token = typeof parsed.query.token === 'string' ? parsed.query.token : '';
      const redirectTo = typeof parsed.query.redirect_to === 'string' ? parsed.query.redirect_to : '';
      const record = invitationByToken(token);
      if (!record || redirectTo !== record.redirectTo || !INVITE_ALLOWED_REDIRECTS.includes(redirectTo)) return notFound(res);
      if (record.status !== 'pending') return redirectForInvitation(res, record, `invitation_${record.status}`);
      if (invitationIsExpired(record)) {
        record.status = 'expired';
        await pool.query("UPDATE public.admin_invitations SET status = 'expired' WHERE id = $1 AND status = 'pending'", [record.id]);
        return redirectForInvitation(res, record, 'invitation_expired');
      }
      if (record.linkOpened) return redirectForInvitation(res, record, 'invitation_used');
      record.linkOpened = true;
      return redirectWithInviteSession(res, record);
    }

    if (pathname === '/functions/v1/admin-invite' && req.method === 'POST') {
      return handleAdminInvite(req, res);
    }

    if (pathname === '/auth/v1/logout' && req.method === 'POST') {
      const auth = req.headers.authorization || '';
      const token = auth.startsWith('Bearer ') ? auth.slice(7) : '';
      if (!token || !sessions.has(token)) return unauthorized(res);
      sessions.delete(token);
      res.writeHead(204);
      return res.end();
    }

    if (pathname === '/auth/v1/token') {
      const body = await parseBody(req);
      const grantType = body.grant_type || parsed.query.grant_type;
      if (grantType === 'pkce') {
        const invitation = pkceCodes.get(body.auth_code);
        if (!invitation || invitation.used || invitation.expiresAt <= now().getTime() || typeof body.code_verifier !== 'string' || !body.code_verifier) return authErrorResponse(res, 'invalid_grant', 'Invalid or expired code');
        if (invitation.codeVerifier && body.code_verifier !== invitation.codeVerifier) return authErrorResponse(res, 'invalid_grant', 'Invalid code verifier');
        if (invitation.codeChallenge) {
          const calculatedChallenge = crypto.createHash('sha256').update(body.code_verifier).digest('base64url');
          if (calculatedChallenge !== invitation.codeChallenge) return authErrorResponse(res, 'invalid_grant', 'Invalid code verifier');
        }
        invitation.used = true;
        invitation.codeVerifier = body.code_verifier;
        const session = issueSession(invitation.email);
        if (!session) return authErrorResponse(res, 'invalid_grant', 'Invitation identity is unavailable');
        return sendJson(res, 200, sessionPayload(session));
      }
      if (grantType === 'password') {
        const fixture = getIdentity(body.email);
        if (!fixture || typeof body.password !== 'string' || body.password !== fixture.password) {
          return authErrorResponse(res, 'invalid_grant', 'Invalid login credentials');
        }
        const session = issueSession(body.email);
        if (!session) return authErrorResponse(res, 'invalid_grant', 'Invalid login credentials');
        return sendJson(res, 200, sessionPayload(session));
      }
      if (grantType === 'refresh_token') {
        const fixture = sessions.get(body.refresh_token);
        if (!fixture) return badRequest(res, 'Invalid refresh token');
        const session = issueSession(fixture.email, fixture.aal);
        return sendJson(res, 200, sessionPayload(session));
      }
      return badRequest(res, 'Unsupported grant_type');
    }

    if (pathname === '/auth/v1/user' && req.method === 'PUT') {
      const fixture = getFixture(req);
      if (!fixture) return unauthorized(res);
      const body = await parseBody(req);
      if (typeof body.password !== 'string' || body.password.length < 12) return badRequest(res, 'Password is too short');
      const identity = authUsers.get(fixture.email);
      if (identity) {
        identity.password = body.password;
        identity.emailConfirmed = true;
      }
      return sendJson(res, 200, { id: fixture.sub, email: fixture.email });
    }

    if (pathname === '/auth/v1/factors' && req.method === 'GET') {
      const fixture = getFixture(req);
      if (!fixture) return unauthorized(res);
      return sendJson(res, 200, { all: factors.get(fixture.sub) || [], totp: factors.get(fixture.sub) || [] });
    }

    if (pathname.match(/^\/auth\/v1\/factors\/[^/]+\/unenroll$/) && req.method === 'POST') {
      const fixture = getFixture(req);
      if (!fixture) return unauthorized(res);
      const factorId = pathname.split('/')[4];
      factors.set(fixture.sub, (factors.get(fixture.sub) || []).filter((item) => item.id !== factorId));
      return sendJson(res, 200, {});
    }

    if (pathname === '/auth/v1/factors' && req.method === 'POST') {
      const fixture = getFixture(req);
      if (!fixture) return unauthorized(res);
      const body = await parseBody(req);
      if (body.factor_type !== 'totp') return badRequest(res, 'Unsupported factor type');
      const factor = { id: crypto.randomUUID(), factor_type: 'totp', status: 'unverified', secret: crypto.randomBytes(20).toString('base64url') };
      factors.set(fixture.sub, [factor]);
      return sendJson(res, 200, { id: factor.id, type: 'totp', totp: { secret: factor.secret, uri: `otpauth://totp/StudIAMatch?secret=${factor.secret}` } });
    }

    if (pathname.match(/^\/auth\/v1\/factors\/[^/]+\/challenge$/) && req.method === 'POST') {
      const fixture = getFixture(req);
      if (!fixture) return unauthorized(res);
      const factorId = pathname.split('/')[4];
      const factor = (factors.get(fixture.sub) || []).find((item) => item.id === factorId && (item.status === 'verified' || item.status === 'unverified'));
      if (!factor) return badRequest(res, 'Factor not verified');
      const challengeId = crypto.randomUUID();
      challenges.set(challengeId, { sub: fixture.sub, factorId });
      return sendJson(res, 200, { id: challengeId, factor_id: factorId });
    }

    if (pathname.match(/^\/auth\/v1\/factors\/[^/]+\/verify$/) && req.method === 'POST') {
      const fixture = getFixture(req);
      if (!fixture) return unauthorized(res);
      const body = await parseBody(req);
      const challenge = body.challenge_id ? challenges.get(body.challenge_id) : null;
      const factorId = pathname.split('/')[4];
      const factor = (factors.get(fixture.sub) || []).find((item) => item.id === factorId);
      if (!factor || !challenge || body.code !== process.env.MOCK_TOTP_CODE || challenge.sub !== fixture.sub || challenge.factorId !== factorId) return badRequest(res, 'Invalid MFA code');
      challenges.delete(body.challenge_id);
      factor.status = 'verified';
      const session = issueSession(fixture.email, 'aal2');
      return sendJson(res, 200, { access_token: session.token, refresh_token: session.token, expires_in: 3600, token_type: 'bearer', aal: 'aal2', user: { id: session.fixture.sub, email: session.fixture.email, aal: 'aal2' } });
    }

    if (pathname.match(/^\/auth\/v1\/factors\/[^/]+$/) && req.method === 'DELETE') {
      const fixture = getFixture(req);
      if (!fixture) return unauthorized(res);
      const factorId = pathname.split('/')[4];
      factors.set(fixture.sub, (factors.get(fixture.sub) || []).filter((item) => item.id !== factorId));
      for (const [token, session] of sessions) if (session.sub === fixture.sub) sessions.delete(token);
      return sendJson(res, 200, {});
    }

    if (pathname === '/auth/v1/user' && req.method === 'GET') {
      const fixture = getFixture(req);
      if (!fixture) return unauthorized(res);
      const verifiedFactor = (factors.get(fixture.sub) || []).some((factor) => factor.status === 'verified');
      return sendJson(res, 200, { id: fixture.sub, email: fixture.email, aal: verifiedFactor || fixture.aal === 'aal2' ? 'aal2' : fixture.aal, role: 'authenticated' });
    }

    if (pathname === '/rest/v1/institutions') {
      const params = parsed.query;
      const values = [];
      let query = 'SELECT id, name, slug FROM public.institutions';
      if (typeof params.slug === 'string' && params.slug.startsWith('eq.')) {
        values.push(params.slug.slice(3));
        query += ` WHERE slug = $${values.length}`;
      }
      query += ' ORDER BY name';
      if (params.limit) {
        values.push(Number(params.limit));
        query += ` LIMIT $${values.length}`;
      }
      const result = await pool.query(query, values);
      return writeRows(res, result);
    }

    if (pathname === '/rest/v1/categories') {
      const result = await pool.query('SELECT id, name FROM public.categories ORDER BY name');
      return writeRows(res, result);
    }

    if (pathname === '/rest/v1/courses_public_effective') {
      const params = parsed.query;
      const values = [];
      const conditions = ["es.editorial_status = 'published'", 'c.is_active = true', 'c.is_verified = true'];
      if (typeof params.institution_id === 'string' && params.institution_id.startsWith('eq.')) {
        values.push(params.institution_id.slice(3));
        conditions.push(`c.institution_id = $${values.length}`);
      }
      if (typeof params.slug === 'string' && params.slug.startsWith('eq.')) {
        values.push(params.slug.slice(3));
        conditions.push(`c.slug = $${values.length}`);
      }
      const result = await pool.query(`SELECT c.id, c.institution_id, c.name, c.slug, c.url, c.price_pen, c.price_status, c.mode, c.duration, c.description_long, c.syllabus, c.target_audience, c.requirements, c.certification, c.benefits, c.objectives, c.start_date, c.start_date_text, c.course_type, c.brochure_url, c.expected_monthly_salary, c.seniority_level, c.roi_months, c.view_count, c.comparison_count, c.created_at, c.updated_at FROM public.courses c JOIN public.course_editorial_state es ON es.course_id = c.id WHERE ${conditions.join(' AND ')} ORDER BY c.updated_at DESC${params.limit ? ` LIMIT ${Number(params.limit)}` : ''}`, values);
      return writeRows(res, result);
    }

    if (pathname.startsWith('/rest/v1/rpc/')) {
      const fixture = getFixture(req);
      if (!fixture) return unauthorized(res);
      const rpc = pathname.replace('/rest/v1/rpc/', '');
      const body = await parseBody(req);
      const result = await withIdentity(fixture, async (client) => {
        switch (rpc) {
          case 'admin_current_user_role':
            return client.query('SELECT public.admin_current_user_role() AS admin_current_user_role');
          case 'admin_is_active_admin':
            return client.query('SELECT public.admin_is_active_admin() AS is_admin');
          case 'admin_is_active_editor':
            return client.query('SELECT public.admin_is_active_editor() AS is_editor');
          case 'admin_get_course_queue':
            return client.query('SELECT * FROM public.admin_get_course_queue($1, $2, $3, $4)', [body.p_first, body.p_after_cursor, body.p_editorial_status, body.p_quality_status]);
          case 'admin_count_course_queue':
            return client.query('SELECT * FROM public.admin_count_course_queue($1, $2)', [body.p_editorial_status, body.p_quality_status]);
          case 'admin_get_course_editorial':
            return client.query('SELECT * FROM public.admin_get_course_editorial($1)', [body.p_course_id]);
          case 'admin_update_course':
            return client.query('SELECT * FROM public.admin_update_course($1, $2, $3, $4)', [body.p_course_id, body.p_manual_overrides, body.p_version, body.p_reason]);
          case 'admin_publish_course':
            return client.query('SELECT * FROM public.admin_publish_course($1, $2)', [body.p_course_id, body.p_reason]);
          case 'admin_unpublish_course':
            return client.query('SELECT * FROM public.admin_unpublish_course($1, $2)', [body.p_course_id, body.p_reason]);
          case 'admin_archive_course':
            return client.query('SELECT * FROM public.admin_archive_course($1, $2)', [body.p_course_id, body.p_reason]);
          case 'admin_update_quality_status':
            return client.query('SELECT * FROM public.admin_update_quality_status($1, $2, $3)', [body.p_course_id, body.p_quality_status, body.p_reason]);
          case 'admin_list_members':
            return client.query('SELECT * FROM public.admin_list_members()');
          case 'admin_create_member':
             return client.query('SELECT * FROM public.admin_create_member($1, $2)', [body.p_email, body.p_role]);
          case 'admin_update_member':
             return client.query('SELECT * FROM public.admin_update_member($1, $2, $3, $4)', [body.p_user_id, body.p_role, body.p_is_active, body.p_action]);
           case 'admin_accept_current_invitation':
             return client.query('SELECT * FROM public.admin_accept_current_invitation($1)', [body.p_invitation_id || null]);
           case 'admin_complete_password_setup':
             return client.query('SELECT * FROM public.admin_complete_password_setup()');
           case 'admin_get_onboarding_status':
             return client.query('SELECT * FROM public.admin_get_onboarding_status()');
          default:
            return null;
        }
      });
      if (!result) return notFound(res);
      return writeRows(res, result);
    }

    return notFound(res);
  } catch (error) {
    console.error('Mock request failed', pathname, error.message);
    return sendJson(res, 500, { message: 'Mock request failed' });
  }
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, '0.0.0.0', () => {
  console.log(`H3 mock server listening on ${PORT}`);
});
