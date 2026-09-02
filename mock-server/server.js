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
  const fixture = FIXTURES[email];
  const token = crypto.randomBytes(32).toString('base64url');
  sessions.set(token, { ...fixture, email, aal });
  return { token, fixture: sessions.get(token) };
}

function getFixture(req) {
  const auth = req.headers.authorization || '';
  const parts = auth.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') return null;
  return sessions.get(parts[1]) || null;
}

async function withIdentity(fixture, callback) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query('SELECT set_config($1, $2, true)', ['request.jwt.claim.sub', fixture.sub]);
    await client.query('SELECT set_config($1, $2, true)', ['request.jwt.claim.aal', fixture.aal || 'aal1']);
    await client.query('SELECT set_config($1, $2, true)', ['request.jwt.claims', JSON.stringify({ sub: fixture.sub, aal: fixture.aal || 'aal1', role: 'authenticated' })]);
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

const server = http.createServer(async (req, res) => {
  const parsed = url.parse(req.url, true);
  const pathname = parsed.pathname;

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, apikey, Authorization');
  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  try {
    if (pathname === '/__test/reset' && req.method === 'POST') {
      if (process.env.NODE_ENV !== 'test' || req.headers['x-h3-test-token'] !== process.env.H3_TEST_RESET_TOKEN) return notFound(res);
      sessions.clear();
      factors.clear();
      challenges.clear();
      res.writeHead(204);
      return res.end();
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
      if (grantType === 'password') {
        const fixture = FIXTURES[body.email];
        if (!fixture || typeof body.password !== 'string' || body.password !== process.env[fixture.passwordEnv]) {
          return badRequest(res, 'Invalid login credentials');
        }
        const session = issueSession(body.email);
        return sendJson(res, 200, {
          access_token: session.token,
          refresh_token: session.token,
          expires_in: 3600,
          token_type: 'bearer',
          user: { id: fixture.sub, email: body.email },
          aal: 'aal1',
        });
      }
      if (grantType === 'refresh_token') {
        const fixture = sessions.get(body.refresh_token);
        if (!fixture) return badRequest(res, 'Invalid refresh token');
        const session = issueSession(fixture.email, fixture.aal);
        return sendJson(res, 200, {
          access_token: session.token,
          refresh_token: session.token,
          expires_in: 3600,
          token_type: 'bearer',
          aal: fixture.aal,
        });
      }
      return badRequest(res, 'Unsupported grant_type');
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
      return sendJson(res, 200, { access_token: session.token, refresh_token: session.token, expires_in: 3600, token_type: 'bearer', aal: 'aal2' });
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
      return sendJson(res, 200, { id: fixture.sub, email: fixture.email, aal: fixture.aal });
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
