import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import { webcrypto } from 'node:crypto';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(root, 'web/package.json'));
const ts = require('typescript');
const sourcePath = join(root, 'supabase/functions/admin-invite/index.ts');
const source = (await readFile(sourcePath, 'utf8'))
  .replace(/^import .*;\s*$/gm, '');
const instrumented = `${source}\n;globalThis.__h3AdminInviteTest = { corsHeaders, authEmailError, configuredRedirect, configuredRecoveryRedirect, isValidSupabaseConfiguration, createApiKeyOnlyFetch };`;
const compiled = ts.transpileModule(instrumented, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    esModuleInterop: true,
  },
  reportDiagnostics: true,
});
assert.equal(compiled.diagnostics?.filter((item) => item.category === ts.DiagnosticCategory.Error).length, 0);

function makeRuntime(mode = 'invite') {
  const isResend = mode.startsWith('resend-');
  const allowedOrigin = 'https://admin.example.test';
  const redirect = `${allowedOrigin}/admin/auth/callback/`;
  const env = new Map([
    ['SUPABASE_URL', 'https://aqrldlmlszjtgpqiegaa.supabase.co'],
    ['NEXT_SUPABASE_SECRET_KEY', ['sb', 'secret', 'local_test'].join('_')],
    ['ADMIN_QUOTA_HMAC_KEY', 'local-only-quota-fixture-'.repeat(3)],
    ['ADMIN_INVITE_ALLOWED_ORIGINS', mode === 'opaque-cors' ? 'file://' : allowedOrigin],
    ['ADMIN_INVITE_ALLOWED_REDIRECTS', redirect],
    ['ADMIN_INVITE_REDIRECT_URL', redirect],
    ['ADMIN_INVITE_RECOVERY_REDIRECT_URL', redirect],
    ['APP_ENV', 'test'],
  ]);
  if (mode === 'missing-redirect') {
    env.delete('ADMIN_INVITE_REDIRECT_URL');
    env.delete('ADMIN_INVITE_RECOVERY_REDIRECT_URL');
  }
  if (mode === 'expired-pending-no-quota-key') env.delete('ADMIN_QUOTA_HMAC_KEY');
  if (mode === 'safe-suspend') env.set('ADMIN_INVITE_SAFE_SUSPEND','true');
  if (mode === 'unallowlisted-redirect') {
    env.set('ADMIN_INVITE_REDIRECT_URL', `${allowedOrigin}/admin/auth/callback/`);
    env.set('ADMIN_INVITE_RECOVERY_REDIRECT_URL', `${allowedOrigin}/admin/auth/callback/`);
    env.set('ADMIN_INVITE_ALLOWED_REDIRECTS', `${allowedOrigin}/admin/other/`);
  }
  if (mode === 'invalid-redirect-protocol') {
    const invalidRedirect = 'ftp://localhost/admin/auth/callback/';
    env.set('ADMIN_INVITE_REDIRECT_URL', invalidRedirect);
    env.set('ADMIN_INVITE_RECOVERY_REDIRECT_URL', invalidRedirect);
    env.set('ADMIN_INVITE_ALLOWED_REDIRECTS', invalidRedirect);
  }
  if (mode === 'http-local-redirect') {
    const invalidRedirect = 'http://localhost/admin/auth/callback/';
    env.set('ADMIN_INVITE_REDIRECT_URL', invalidRedirect);
    env.set('ADMIN_INVITE_RECOVERY_REDIRECT_URL', invalidRedirect);
    env.set('ADMIN_INVITE_ALLOWED_REDIRECTS', invalidRedirect);
  }
  const calls = [];
  let handler;
  let completed = false;
  let reservationMetadata = {};

  const query = (table) => {
    const filters = [];
    let requestFilter = false;
    const builder = {
      select() { return this; },
      eq(column, value) { filters.push([column, value]); return this; },
      filter() { requestFilter = true; return this; },
      order() { return this; },
      limit() { return this; },
      update(payload) { calls.push({ kind: 'table_update', table, payload }); return this; },
      async maybeSingle() {
        if (table === 'admin_members') {
          const userId = filters.find(([column]) => column === 'user_id')?.[1];
          if (userId === 'edge-test-admin') {
            return { data: { user_id: userId, role: 'admin', is_active: true, account_status: 'ready' }, error: null };
          }
          if (userId === 'edge-test-existing-user') {
            return { data: { user_id: userId, role: 'user', is_active: false, account_status: 'invited' }, error: null };
          }
          return { data: null, error: null };
        }
        if (table === 'admin_invitations') {
          const status = filters.find(([column]) => column === 'status')?.[1];
          if (requestFilter && completed) {
            return { data: {
              id: 'edge-test-new-invitation', status: 'pending',
              admin_member_user_id: isResend ? 'edge-test-existing-user' : 'edge-test-created-user',
              resend_of_invitation_id: isResend ? 'edge-test-old-invitation' : null,
              metadata: { ...reservationMetadata, delivery_state: 'completed' },
            }, error: null };
          }
          if (!requestFilter && mode.startsWith('expired-pending') && status === 'pending') {
            return {
              data: {
                id: 'edge-test-expired-invitation',
                status: 'pending',
                expires_at: new Date(Date.now() - 60_000).toISOString(),
                last_sent_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
              },
              error: null,
            };
          }
          if (requestFilter && mode.startsWith('replay-')) {
            return {
              data: {
                id: 'edge-test-replayed-invitation',
                status: 'pending',
                admin_member_user_id: 'edge-test-existing-user',
                resend_of_invitation_id: null,
                metadata: mode === 'replay-completed'
                  ? { delivery_state: 'completed' }
                  : mode === 'replay-unknown'
                    ? { reconciliation_required: true, delivery_outcome: 'unknown', delivery_state: 'reconciliation_required' }
                    : { delivery_state: 'reserved' },
              },
              error: null,
            };
          }
          if (requestFilter || !isResend) return { data: null, error: null };
          return {
            data: {
              id: 'edge-test-old-invitation',
              status: 'pending',
              expires_at: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
              last_sent_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
            },
            error: null,
          };
        }
        return { data: null, error: null };
      },
    };
    return builder;
  };

  const client = {
    auth: {
      async getUser() {
        return { data: { user: { id: 'edge-test-admin', email: 'admin@example.test' } }, error: null };
      },
      admin: {
        async listUsers() {
          const users = isResend
            ? [{
              id: 'edge-test-existing-user',
              email: 'existing@example.test',
              email_confirmed_at: mode === 'resend-unconfirmed-success' ? null : new Date().toISOString(),
            }]
            : [];
          return { data: { users }, error: null };
        },
        async inviteUserByEmail() {
          calls.push({ kind: 'auth_invite' });
          if (mode === 'invite-throw') throw new Error('fixture connection reset after request write');
          if (mode === 'invite-408') return { data: { user: null }, error: { status: 408, message: 'fixture timeout' } };
          if (mode === 'invite-503-rate-limit') return { data: { user: null }, error: { status: 503, message: 'rate limit service unavailable' } };
          if (['invite-complete-failure', 'invite-success', 'resend-unconfirmed-success'].includes(mode)) {
            return { data: { user: {
              id: isResend ? 'edge-test-existing-user' : 'edge-test-created-user',
              email: isResend ? 'existing@example.test' : 'new@example.test',
            } }, error: null };
          }
          return { data: { user: null }, error: { status: 503, message: 'fixture upstream timeout' } };
        },
      },
      async resetPasswordForEmail() {
        calls.push({ kind: 'auth_recovery' });
        if (mode === 'resend-success') return { error: null };
        if (mode === 'resend-throw') throw new Error('fixture recovery connection reset after request write');
        if (mode === 'resend-408') return { error: { status: 408, message: 'fixture timeout' } };
        if (mode === 'resend-503-rate-limit') return { error: { status: 503, message: 'rate limit service unavailable' } };
        return { error: { status: 503, message: 'fixture upstream timeout' } };
      },
    },
    from: query,
    async rpc(name, params) {
      if (name === 'admin_invitation_request_admit') {
        calls.push({ kind:'quota_request',name,params });
        if (mode === 'request-quota-exceeded') return {data:null,error:{code:'quota_rate_limited',details:'60'}};
        return {data:true,error:null};
      }
      calls.push({ kind: 'rpc', name, params });
      if (name === 'admin_invitation_reserve') {
        reservationMetadata = structuredClone(params.p_metadata);
        assert.match(params.p_metadata.quota_recipient, /^[a-f0-9]{64}$/);
        if (mode === 'quota-exceeded') return { data: null, error: { code: 'quota_rate_limited', details: '60' } };
        if (mode === 'reserve-replay') {
          return {
            data: [{ success: false, invitation_id: null, member_id: null, old_status: 'pending', resent: false, error_code: 'reconciliation_required' }],
            error: null,
          };
        }
        return {
          data: [{
            success: true,
            invitation_id: 'edge-test-new-invitation',
            member_id: null,
            old_status: isResend ? 'pending' : null,
            resent: isResend,
            error_code: null,
          }],
          error: null,
        };
      }
      if (name === 'admin_invitation_mark_delivery_reconciliation') {
        if (mode === 'invite-marker-failure') return { data: null, error: new Error('fixture reconciliation RPC timeout') };
        return { data: [{ success: true, error_code: null }], error: null };
      }
      if (name === 'admin_invitation_expire') {
        return { data: [{ success: true, error_code: null }], error: null };
      }
      if (name === 'admin_invitation_complete' && mode === 'invite-complete-failure') {
        return { data: null, error: new Error('fixture database unavailable after Auth accepted') };
      }
      if (name === 'admin_invitation_fail' || name === 'admin_invitation_complete') {
        if (name === 'admin_invitation_complete') completed = true;
        return { data: [{ success: true, error_code: null }], error: null };
      }
      return { data: null, error: new Error(`unexpected rpc ${name}`) };
    },
  };

  const sandbox = {
    Deno: {
      env: { get: (name) => env.get(name) },
      serve: (value) => { handler = value; },
    },
    createClient: () => client,
    crypto: webcrypto,
    TextEncoder,
    atob: globalThis.atob,
    Request,
    Response,
    Headers,
    URL,
    TextDecoder,
    Uint8Array,
    Set,
    Map,
    Date,
    JSON,
    Error,
    console: { error() {} },
    exports: {},
    require() { throw new Error('unexpected runtime import'); },
  };
  vm.runInNewContext(compiled.outputText, sandbox, { filename: sourcePath });
  return { allowedOrigin, calls, handler, api: sandbox.__h3AdminInviteTest };
}

const corsRuntime = makeRuntime();
assert.equal(corsRuntime.api.configuredRedirect()?.url, `${corsRuntime.allowedOrigin}/admin/auth/callback/`);
assert.equal(corsRuntime.api.configuredRecoveryRedirect()?.url, `${corsRuntime.allowedOrigin}/admin/auth/callback/`);

const missingRedirectRuntime = makeRuntime('missing-redirect');
assert.equal(missingRedirectRuntime.api.configuredRedirect(), null, 'invite callback must not default to a compiled Preview hostname');
assert.equal(missingRedirectRuntime.api.configuredRecoveryRedirect(), null, 'recovery callback must not default to a compiled Preview hostname');

const unallowlistedRedirectRuntime = makeRuntime('unallowlisted-redirect');
assert.equal(unallowlistedRedirectRuntime.api.configuredRedirect(), null, 'invite callback must match the explicit redirect allowlist');
assert.equal(unallowlistedRedirectRuntime.api.configuredRecoveryRedirect(), null, 'recovery callback must match the explicit redirect allowlist');

for (const mode of ['invalid-redirect-protocol', 'http-local-redirect']) {
  const runtime = makeRuntime(mode);
  assert.equal(runtime.api.configuredRedirect(), null, `${mode}: invitation redirects require HTTPS`);
  assert.equal(runtime.api.configuredRecoveryRedirect(), null, `${mode}: recovery redirects require HTTPS`);
}

assert.equal(
  corsRuntime.api.isValidSupabaseConfiguration('https://aqrldlmlszjtgpqiegaa.supabase.co', ['sb', 'secret', 'local_test'].join('_')),
  true,
);
for (const [url, key] of [
  ['http://aqrldlmlszjtgpqiegaa.supabase.co', ['sb', 'secret', 'local_test'].join('_')],
  ['https://example.invalid', ['sb', 'secret', 'local_test'].join('_')],
  ['https://user@aqrldlmlszjtgpqiegaa.supabase.co', ['sb', 'secret', 'local_test'].join('_')],
  ['https://aqrldlmlszjtgpqiegaa.supabase.co/path', ['sb', 'secret', 'local_test'].join('_')],
  ['https://aqrldlmlszjtgpqiegaa.supabase.co', 'not-a-secret-key'],
]) {
  assert.equal(corsRuntime.api.isValidSupabaseConfiguration(url, key), false, 'invalid privileged Supabase configuration must fail closed');
}

const edgeSecretKey = ['sb', 'secret', 'local_test'].join('_');
for(const status of [301,302,303,307,308]) {
  let calls=0;
  const blocked=corsRuntime.api.createApiKeyOnlyFetch(edgeSecretKey,async(_input,init)=>{
    calls++;assert.equal(init.redirect,'manual');
    return new Response(null,{status,headers:{Location:'https://unapproved.example/collect'}});
  });
  await assert.rejects(blocked('https://aqrldlmlszjtgpqiegaa.supabase.co/auth/v1/user'),/redirects are not allowed/);
  assert.equal(calls,1);
}
let edgeHeaders = null;
let edgeSends = 0;
const edgeKeyOnlyFetch = corsRuntime.api.createApiKeyOnlyFetch(edgeSecretKey, async (_input, init) => {
  edgeSends += 1;
  edgeHeaders = new Headers(init?.headers);
  assert.equal(init.redirect, 'manual');
  return new Response('{}', { status: 200 });
});
await edgeKeyOnlyFetch('https://aqrldlmlszjtgpqiegaa.supabase.co/rest/v1/rpc/test', {
  headers: { apikey: edgeSecretKey, authorization: `Bearer ${edgeSecretKey}` },
});
assert.equal(edgeHeaders.get('apikey'), edgeSecretKey);
assert.equal(edgeHeaders.has('authorization'), false, 'Edge API keys must never become bearer identities');
const edgeJwtFixture = 'localHeader.localPayload.localSignature';
await edgeKeyOnlyFetch('https://aqrldlmlszjtgpqiegaa.supabase.co/auth/v1/user', {
  headers: { apikey: edgeSecretKey, authorization: `Bearer ${edgeJwtFixture}` },
});
assert.equal(edgeHeaders.get('authorization'), `Bearer ${edgeJwtFixture}`, 'user JWT must reach only Auth identity verification');
await edgeKeyOnlyFetch(new Request('https://aqrldlmlszjtgpqiegaa.supabase.co/auth/v1/user', {
  method: 'PUT', headers: { authorization: 'Basic forbidden' },
}), { method: 'GET', headers: { authorization: `Bearer ${edgeJwtFixture}` }, redirect: 'follow' });
const beforeEdgeOverride = edgeSends;
await assert.rejects(edgeKeyOnlyFetch(new Request('https://aqrldlmlszjtgpqiegaa.supabase.co/auth/v1/user', {
  headers: { authorization: `Bearer ${edgeJwtFixture}` },
}), { method: 'PUT' }), /not allowed/);
assert.equal(edgeSends, beforeEdgeOverride);
for (const [destination, method] of [
  ['https://aqrldlmlszjtgpqiegaa.supabase.co/rest/v1/rpc/test', 'POST'],
  ['https://aqrldlmlszjtgpqiegaa.supabase.co/auth/v1/user', 'PUT'],
  ['https://example.invalid/auth/v1/user', 'GET'],
]) {
  await assert.rejects(edgeKeyOnlyFetch(destination, {
    method, headers: { authorization: `Bearer ${edgeJwtFixture}` },
  }), /not allowed/);
}

const allowedCors = corsRuntime.api.corsHeaders(new Request('https://edge.example.test/', {
  headers: { Origin: corsRuntime.allowedOrigin },
}));
assert.equal(allowedCors['Access-Control-Allow-Origin'], corsRuntime.allowedOrigin);

for (const origin of ['https://unapproved.example.test', 'null', 'file://']) {
  const headers = corsRuntime.api.corsHeaders(new Request('https://edge.example.test/', { headers: { Origin: origin } }));
  assert.equal(Object.hasOwn(headers, 'Access-Control-Allow-Origin'), false, `unapproved Origin ${origin} must not receive ACAO`);
}
const opaqueCorsRuntime = makeRuntime('opaque-cors');
const opaqueOriginHeaders = opaqueCorsRuntime.api.corsHeaders(new Request('https://edge.example.test/', {
  headers: { Origin: 'file://' },
}));
assert.equal(Object.hasOwn(opaqueOriginHeaders, 'Access-Control-Allow-Origin'), false, 'opaque URL origins must never serialize ACAO: null');
const noOriginHeaders = corsRuntime.api.corsHeaders(new Request('https://edge.example.test/'));
assert.equal(Object.hasOwn(noOriginHeaders, 'Access-Control-Allow-Origin'), false, 'missing Origin must not receive ACAO');
assert.equal(noOriginHeaders['Access-Control-Allow-Methods'], 'POST, OPTIONS');

assert.equal(corsRuntime.api.authEmailError({ status: 429 }, 'fallback').code, 'auth_rate_limited');
assert.equal(corsRuntime.api.authEmailError({ status: 422 }, 'fallback').code, 'auth_invite_failed');
assert.equal(corsRuntime.api.authEmailError({ status: 503 }, 'fallback').code, 'auth_delivery_unknown');
assert.equal(corsRuntime.api.authEmailError({ status: 503, message: 'rate limit service unavailable' }, 'fallback').code, 'auth_delivery_unknown');
assert.equal(corsRuntime.api.authEmailError({ status: 408 }, 'fallback').code, 'auth_delivery_unknown');
assert.equal(corsRuntime.api.authEmailError({ status: 425 }, 'fallback').code, 'auth_delivery_unknown');
assert.equal(corsRuntime.api.authEmailError({ message: 'network timeout' }, 'fallback').code, 'auth_delivery_unknown');

function testBearerToken() {
  const payload = Buffer.from(JSON.stringify({ aal: 'aal2' })).toString('base64url');
  return `header.${payload}.signature`;
}

async function runAmbiguousDelivery(mode) {
  const runtime = makeRuntime(mode);
  const isResend = mode.startsWith('resend-');
  const completesAuth = mode === 'invite-complete-failure';
  const markerFails = mode === 'invite-marker-failure';
  const email = isResend ? 'existing@example.test' : 'new@example.test';
  const requestId = `edge-${mode}-request-id`;
  const body = JSON.stringify({ email, role: 'user', ...(isResend ? { resend: true } : {}) });
  const response = await runtime.handler(new Request('https://edge.example.test/functions/v1/admin-invite', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${testBearerToken()}`,
      Origin: runtime.allowedOrigin,
      'Content-Type': 'application/json',
      'x-request-id': requestId,
    },
    body,
  }));
  const result = await response.json();
  assert.equal(response.status, 409, `${mode} must require reconciliation; got ${response.status}/${result.code}`);
  assert.equal(result.code, 'reconciliation_required');

  const names = runtime.calls.filter((call) => call.kind === 'rpc').map((call) => call.name);
  assert.deepEqual(names, completesAuth
    ? ['admin_invitation_reserve', 'admin_invitation_complete', 'admin_invitation_mark_delivery_reconciliation']
    : ['admin_invitation_reserve', 'admin_invitation_mark_delivery_reconciliation']);
  const reservation = runtime.calls.find((call) => call.kind === 'rpc' && call.name === 'admin_invitation_reserve');
  assert.equal(reservation.params.p_request_id, requestId, 'caller idempotency key must be persisted with reservation');
  const marker = runtime.calls.find((call) => call.kind === 'rpc' && call.name === 'admin_invitation_mark_delivery_reconciliation');
  assert.equal(marker.params.p_invitation_id, 'edge-test-new-invitation');
  assert.equal(marker.params.p_delivery_outcome, completesAuth ? 'auth_accepted' : 'unknown');
  assert.equal(marker.params.p_failure_code, completesAuth ? 'invitation_completion_failed' : 'auth_delivery_unknown');
  assert.equal(runtime.calls.some((call) => call.kind === 'rpc' && call.name === 'admin_invitation_fail'), false);
  assert.equal(runtime.calls.some((call) => call.kind === 'rpc' && call.name === 'admin_invitation_complete'), completesAuth);
  assert.equal(runtime.calls.some((call) => call.kind === 'auth_invite'), !isResend);
  assert.equal(runtime.calls.some((call) => call.kind === 'auth_recovery'), isResend);
}

for (const mode of [
  'invite-503', 'invite-408', 'invite-throw', 'invite-503-rate-limit', 'invite-marker-failure', 'invite-complete-failure',
  'resend-503', 'resend-408', 'resend-throw', 'resend-503-rate-limit',
]) {
  await runAmbiguousDelivery(mode);
}

for (const mode of ['invite-success', 'resend-success', 'resend-unconfirmed-success']) {
  const runtime = makeRuntime(mode);
  const isResend = mode.startsWith('resend-');
  const request = () => new Request('https://edge.example.test/functions/v1/admin-invite', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${testBearerToken()}`, Origin: runtime.allowedOrigin,
      'Content-Type': 'application/json', 'x-request-id': `edge-${mode}-request-id`,
    },
    body: JSON.stringify({ email: isResend ? 'existing@example.test' : 'new@example.test', role: 'user', resend: isResend }),
  });
  const first = await runtime.handler(request());
  const result = await first.json();
  assert.equal(first.status, 200, `${mode} must not reconcile a successfully persisted delivery`);
  assert.equal(result.success, true);
  assert.equal(result.resent, isResend);
  assert.equal(result.recovery_sent, mode === 'resend-success');
  assert.equal(result.invitation_id, 'edge-test-new-invitation');
  assert.equal(runtime.calls.find(call => call.name === 'admin_invitation_reserve').params.p_metadata.delivery_method,
    mode === 'resend-success' ? 'recovery' : 'invite');
  assert.deepEqual(runtime.calls.filter(call => call.kind === 'rpc').map(call => call.name), [
    'admin_invitation_reserve', 'admin_invitation_complete',
  ]);
  assert.equal(runtime.calls.filter(call => call.kind === (mode === 'resend-success' ? 'auth_recovery' : 'auth_invite')).length, 1);
  const count = runtime.calls.filter(c=>c.kind!=='quota_request').length;
  const replay = await runtime.handler(request());
  assert.equal(replay.status, 200);
  assert.deepEqual(await replay.json(), result, 'completed replay must preserve the entire successful response');
  assert.equal(runtime.calls.filter(c=>c.kind!=='quota_request').length, count, 'completed replay must not send again or mark reconciliation');
  assert.equal(runtime.calls.filter(c=>c.kind==='quota_request').length,2,'replay is request-limited without consuming delivery quota');
}

{
  const runtime = makeRuntime('quota-exceeded');
  const response = await runtime.handler(new Request('https://edge.example.test/functions/v1/admin-invite', {
    method: 'POST', headers: { Authorization: `Bearer ${testBearerToken()}`, Origin: runtime.allowedOrigin, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'new@example.test', role: 'user' }),
  }));
  assert.equal(response.status,429);
  assert.equal(response.headers.get('Retry-After'),'60');
  assert.equal((await response.json()).code,'quota_rate_limited');
  assert.deepEqual(runtime.calls.filter(c => c.kind === 'rpc').map(c=>c.name),['admin_invitation_reserve']);
  assert.equal(runtime.calls.some(c=>c.kind.startsWith('auth_')),false,'quota rejection must not send Auth or compensation');
}

for (const mode of ['expired-pending-no-quota-key','request-quota-exceeded','safe-suspend']) {
  const runtime=makeRuntime(mode);
  const response=await runtime.handler(new Request('https://edge.example.test/functions/v1/admin-invite', {
    method:'POST',headers:{Authorization:`Bearer ${testBearerToken()}`,Origin:runtime.allowedOrigin,'Content-Type':'application/json'},
    body:JSON.stringify({email:'new@example.test',role:'user'}),
  }));
  assert.equal(response.status,mode==='request-quota-exceeded'?429:503);
  assert.deepEqual(runtime.calls.filter(c=>c.kind==='rpc'||c.kind.startsWith('auth_')),[],
    'missing config/admission denial must not expire, reserve, send or compensate');
}

for (const mode of ['replay-unknown', 'replay-inflight', 'replay-marker-failed', 'replay-completed']) {
  const runtime = makeRuntime(mode);
  const response = await runtime.handler(new Request('https://edge.example.test/functions/v1/admin-invite', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${testBearerToken()}`,
      Origin: runtime.allowedOrigin,
      'Content-Type': 'application/json',
      'x-request-id': `edge-${mode}-request-id`,
    },
    body: JSON.stringify({ email: 'existing@example.test', role: 'user' }),
  }));
  const result = await response.json();
  if (mode !== 'replay-completed') {
    assert.equal(response.status, 409, 'idempotent replay must surface unresolved delivery instead of false success');
    assert.equal(result.code, 'reconciliation_required');
  } else {
    assert.equal(response.status, 200, 'completed idempotent replay should return the persisted result');
    assert.equal(result.invitation_id, 'edge-test-replayed-invitation');
  }
  assert.equal(runtime.calls.filter(c=>c.kind!=='quota_request').length, 0, 'idempotent replay must not repeat Auth side effects');
}

{
  const runtime = makeRuntime('reserve-replay');
  const response = await runtime.handler(new Request('https://edge.example.test/functions/v1/admin-invite', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${testBearerToken()}`,
      Origin: runtime.allowedOrigin,
      'Content-Type': 'application/json',
      'x-request-id': 'edge-concurrent-same-request',
    },
    body: JSON.stringify({ email: 'new@example.test', role: 'user', resend: true }),
  }));
  const result = await response.json();
  assert.equal(response.status, 409);
  assert.equal(result.code, 'reconciliation_required');
  assert.deepEqual(runtime.calls.filter((call) => call.kind === 'rpc').map((call) => call.name), ['admin_invitation_reserve']);
  assert.equal(runtime.calls.some((call) => call.kind === 'auth_invite' || call.kind === 'auth_recovery'), false, 'duplicate reservation must stop before an Auth send');
}

{
  const runtime = makeRuntime('expired-pending');
  const response = await runtime.handler(new Request('https://edge.example.test/functions/v1/admin-invite', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${testBearerToken()}`,
      Origin: runtime.allowedOrigin,
      'Content-Type': 'application/json',
      'x-request-id': 'edge-expired-pending-request',
    },
    body: JSON.stringify({ email: 'new@example.test', role: 'user' }),
  }));
  const result = await response.json();
  assert.equal(response.status, 409);
  assert.equal(result.code, 'reconciliation_required');
  const rpcNames = runtime.calls.filter((call) => call.kind === 'rpc').map((call) => call.name);
  assert.deepEqual(rpcNames, [
    'admin_invitation_expire',
    'admin_invitation_reserve',
    'admin_invitation_mark_delivery_reconciliation',
  ]);
  assert.equal(runtime.calls.some((call) => call.kind === 'table_update'), false, 'expiry must never bypass the audited service-role RPC');
}

console.log(JSON.stringify({ result: 'PASS', successAndReplayCases: 3, corsCases: 6, errorClassificationCases: 7, ambiguousDeliveryCases: 10, replayCases: 4, concurrentReplayCases: 1, expiryCases: 1 }));
