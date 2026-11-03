import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHmac, webcrypto } from 'node:crypto';
import vm from 'node:vm';

const root = join(fileURLToPath(new URL('..', import.meta.url)));
const require = createRequire(join(root, 'web/package.json'));
const ts = require('typescript');
globalThis.WebSocket = class WebSocket {};

const { createClient } = require('@supabase/supabase-js');
const source = await readFile(join(root, 'web/src/lib/supabase-transport.ts'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
  reportDiagnostics: true,
});
assert.equal(compiled.diagnostics?.filter((item) => item.category === ts.DiagnosticCategory.Error).length, 0);

const moduleObject = { exports: {} };
vm.runInNewContext(compiled.outputText, {
  module: moduleObject,
  exports: moduleObject.exports,
  Headers,
  Request,
  URL,
  TextEncoder,
  TextDecoder,
  atob,
  crypto: webcrypto,
}, { filename: 'supabase-transport.js' });
const { createApiKeyOnlyFetch } = moduleObject.exports;
const API_URL = 'https://aqrldlmlszjtgpqiegaa.supabase.co';
const RPC_HMAC_KEY = 'local-only-rpc-gateway-fixture-key-32-bytes';
const RPC_KEY_ID = 'local-k1';
const PROJECT_REF = 'aqrldlmlszjtgpqiegaa';
// Structurally JWT-shaped, deliberately unsigned local fixture. No real identity
// or credential; Supabase verification is not claimed by an intercepted test.
const USER_JWT = [
  Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url'),
  Buffer.from(JSON.stringify({ sub: '30000000-0000-0000-0000-000000000001', aal: 'aal2', exp: Math.floor(Date.now() / 1000) + 3600 })).toString('base64url'),
  Buffer.from('local-test-signature').toString('base64url'),
].join('.');
const policy = {
  projectOrigin: API_URL,
  rpcAllowlist: new Set(['admin_current_user_role']),
  rpcGateway: { projectRef: PROJECT_REF, keyId: RPC_KEY_ID, hmacKey: RPC_HMAC_KEY },
};
let checks = 0;

async function exerciseClient(key, expectedBearer) {
  const requests = [];
  const transport = createApiKeyOnlyFetch(key, async (input, init) => {
    const headers = new Headers(init?.headers ?? (input instanceof Request ? input.headers : undefined));
    requests.push({
      apikeyMatches: headers.get('apikey') === key,
      authorizationIsKey: headers.get('authorization') === `Bearer ${key}`,
      authorizationIsUser: headers.get('authorization') === `Bearer ${USER_JWT}`,
      authorizationPresent: headers.has('authorization'),
      gatewayKeyId: headers.get('x-studiamatch-admin-rpc-key-id'),
      gatewayActor: headers.get('x-studiamatch-admin-rpc-actor'),
      gatewayIssuedAt: headers.get('x-studiamatch-admin-rpc-issued-at'),
      gatewayNonce: headers.get('x-studiamatch-admin-rpc-nonce'),
      gatewaySignature: headers.get('x-studiamatch-admin-rpc-signature'),
      gatewayPayloadSignature: headers.get('x-studiamatch-admin-rpc-payload-signature'),
      body: typeof init?.body === 'string' ? init.body : null,
      url: String(input),
      method: init?.method,
      redirect: init?.redirect,
    });
    return new Response('[]', {
      status: 200,
      headers: { 'content-type': 'application/json', 'content-range': '*/0' },
    });
  }, expectedBearer === 'user' ? policy : undefined);
  const client = createClient(API_URL, key, {
    global: { fetch: transport },
    auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
    ...(expectedBearer === 'user' ? { accessToken: async () => USER_JWT } : {}),
  });
  const { error } = expectedBearer === 'user'
    ? await client.rpc('admin_current_user_role', {})
    : await client.from('courses').select('id');
  assert.equal(error, null);
  assert.equal(requests.length, 1);
  assert.equal(requests[0].apikeyMatches, true);
  assert.equal(requests[0].authorizationIsKey, false, 'SDK must not send a Supabase API key as Bearer');
  assert.equal(requests[0].authorizationIsUser, expectedBearer === 'user');
  assert.equal(requests[0].authorizationPresent, expectedBearer === 'user');
  assert.equal(requests[0].redirect, 'manual');
  if (expectedBearer === 'user') {
    assert.equal(requests[0].url, `${API_URL}/rest/v1/rpc/admin_signed_rpc`);
    assert.equal(requests[0].method, 'POST');
    assert.equal(requests[0].gatewayKeyId, RPC_KEY_ID);
    assert.equal(requests[0].gatewayActor, '30000000-0000-0000-0000-000000000001');
    assert.match(requests[0].gatewayIssuedAt, /^\d{10}$/);
    assert.match(requests[0].gatewayNonce, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    const canonical = [
      'studiamatch-admin-rpc-v1', PROJECT_REF, 'POST', 'admin_signed_rpc',
      requests[0].gatewayActor, requests[0].gatewayIssuedAt, requests[0].gatewayNonce, RPC_KEY_ID,
    ].join('\n');
    assert.equal(requests[0].gatewaySignature, createHmac('sha256', RPC_HMAC_KEY).update(canonical).digest('hex'));
    const body = JSON.parse(requests[0].body);
    assert.equal(body.p_rpc_name, 'admin_current_user_role');
    assert.deepEqual(body.p_args, {});
    assert.equal(body.p_signed_payload, '{}');
    const payloadCanonical = [
      'studiamatch-admin-rpc-payload-v1', PROJECT_REF, 'POST', 'admin_signed_rpc',
      body.p_rpc_name, requests[0].gatewayActor, requests[0].gatewayIssuedAt,
      requests[0].gatewayNonce, RPC_KEY_ID, body.p_signed_payload,
    ].join('\n');
    assert.equal(
      requests[0].gatewayPayloadSignature,
      createHmac('sha256', RPC_HMAC_KEY).update(payloadCanonical).digest('hex'),
    );
  } else {
    assert.equal(requests[0].gatewaySignature, null, 'public browser requests never carry an RPC signature');
    assert.equal(requests[0].gatewayPayloadSignature, null, 'public browser requests never carry a payload signature');
  }
  checks += 1;
  return requests[0];
}

await exerciseClient('sb_publishable_local_fixture', 'none');
await exerciseClient(['sb', 'secret', 'local_fixture'].join('_'), 'none');
await exerciseClient('sb_publishable_local_fixture', 'user');

const factorListRequests = [];
const listedFactorFixture = {
  id: '00000000-0000-4000-8000-000000000001',
  factor_type: 'totp',
  status: 'verified',
};
const factorListTransport = createApiKeyOnlyFetch('sb_publishable_local_fixture', async (input, init) => {
  const headers = new Headers(init?.headers);
  factorListRequests.push({ url: String(input), method: init?.method, headers, redirect: init?.redirect });
  return new Response(JSON.stringify({ id: '30000000-0000-0000-0000-000000000001', factors: [listedFactorFixture] }), {
    status: 200,
    headers: { 'content-type': 'application/json' },
  });
}, policy);
const factorListClient = createClient(API_URL, 'sb_publishable_local_fixture', {
  global: { fetch: factorListTransport },
  auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
});
const { error: sessionError } = await factorListClient.auth.setSession({
  access_token: USER_JWT,
  refresh_token: 'local-only-refresh-fixture',
  expires_at: Math.floor(Date.now() / 1000) + 3600,
});
assert.equal(sessionError, null, 'the SDK should accept the synthetic local session fixture');
const requestsBeforeListFactors = factorListRequests.length;
const { data: listedFactors, error: factorListError } = await factorListClient.auth.mfa.listFactors();
assert.equal(factorListError, null, 'the official SDK factor-list operation should succeed');
assert.equal(listedFactors.all[0].id, listedFactorFixture.id);
assert.equal(listedFactors.totp[0].id, listedFactorFixture.id);
const sdkListRequests = factorListRequests.slice(requestsBeforeListFactors);
assert.deepEqual(sdkListRequests.map(({ url, method }) => ({ path: new URL(url).pathname, method })), [
  { path: '/auth/v1/user', method: 'GET' },
]);
for (const request of factorListRequests) {
  assert.equal(request.headers.get('apikey'), 'sb_publishable_local_fixture');
  assert.equal(request.headers.get('authorization'), `Bearer ${USER_JWT}`);
  assert.equal(request.redirect, 'manual');
}
checks += 10;

const factor = '00000000-0000-4000-8000-000000000001';
let redirectChecks=0;
for(const status of [300,301,302,303,307,308]) {
  let calls=0;
  const rejectRedirect=createApiKeyOnlyFetch('sb_publishable_local_fixture',async(_input,init)=>{
    calls++;assert.equal(init.redirect,'manual');
    return new Response(null,{status,headers:{Location:'https://unapproved.example/collect'}});
  },policy);
  await assert.rejects(rejectRedirect(`${API_URL}/auth/v1/user`,{headers:{authorization:`Bearer ${USER_JWT}`}}),/redirects are not allowed/);
  assert.equal(calls,1,'must never follow Location');redirectChecks++;
}
await assert.rejects(createApiKeyOnlyFetch('sb_publishable_local_fixture',async()=>({status:0,type:'opaqueredirect'}),policy)(
  `${API_URL}/auth/v1/user`,{headers:{authorization:`Bearer ${USER_JWT}`}},
),/redirects are not allowed/);
redirectChecks++;
let sent = 0;
const guarded = createApiKeyOnlyFetch('sb_publishable_local_fixture', async (input, init) => {
  sent += 1;
  const headers = new Headers(init.headers);
  assert.equal(headers.get('authorization'), `Bearer ${USER_JWT}`);
  assert.equal(init.redirect, 'manual');
  const url = new URL(typeof input === 'string' ? input : input.url);
  if (url.pathname.startsWith('/rest/v1/rpc/')) {
    assert.equal(headers.get('x-studiamatch-admin-rpc-key-id'), RPC_KEY_ID);
    assert.equal(headers.get('x-studiamatch-admin-rpc-actor'), '30000000-0000-0000-0000-000000000001');
    assert.equal(url.pathname, '/rest/v1/rpc/admin_signed_rpc');
    const body = JSON.parse(init.body);
    assert.equal(body.p_rpc_name, 'admin_current_user_role');
    assert.equal(body.p_signed_payload, '{}');
  } else {
    assert.equal(headers.has('x-studiamatch-admin-rpc-signature'), false, 'Auth and Edge calls do not get RPC gateway assertions');
    assert.equal(headers.has('x-studiamatch-admin-rpc-payload-signature'), false, 'Auth and Edge calls do not get payload assertions');
  }
  return new Response('{}', { status: 200 });
}, policy);
for (const [path, method] of [
  ['/rest/v1/rpc/admin_current_user_role', 'POST'],
  ['/auth/v1/user', 'GET'], ['/auth/v1/user', 'PUT'],
  ['/auth/v1/factors', 'POST'],
  [`/auth/v1/factors/${factor}/challenge`, 'POST'],
  [`/auth/v1/factors/${factor}/verify`, 'POST'],
  [`/auth/v1/factors/${factor}`, 'DELETE'],
  ['/functions/v1/admin-invite', 'POST'],
]) {
  await guarded(`${API_URL}${path}`, {
    method,
    headers: { authorization: `Bearer ${USER_JWT}` },
    ...(path.startsWith('/rest/v1/rpc/') ? { body: '{}' } : {}),
  });
  checks += 1;
}
// Request input and init headers must merge without preserving a forbidden key.
await guarded(new Request(`${API_URL}/auth/v1/user`, { headers: { authorization: `Bearer ${USER_JWT}` } }));
checks += 1;
await guarded(new Request(`${API_URL}/auth/v1/user`, {
  method: 'DELETE', headers: { authorization: 'invalid-original-header' },
}), { method: 'GET', headers: { authorization: `Bearer ${USER_JWT}` }, redirect: 'follow' });
checks += 1;
const beforeOverride = sent;
await assert.rejects(guarded(new Request(`${API_URL}/auth/v1/user`, {
  headers: { authorization: `Bearer ${USER_JWT}` },
}), { method: 'DELETE' }), /not allowed/);
await assert.rejects(guarded(new Request(`${API_URL}/auth/v1/user`, {
  headers: { authorization: `Bearer ${USER_JWT}` },
}), { headers: { authorization: 'Basic forbidden' } }), /not allowed/);
assert.equal(sent, beforeOverride);
checks += 2;
await guarded(`${API_URL}/auth/v1/user`, { method: 'GET', headers: {
  authorization: `Bearer ${USER_JWT}`,
  'x-studiamatch-admin-rpc-signature': 'caller-forged',
  'x-studiamatch-admin-rpc-payload-signature': 'caller-forged',
} });
checks += 1;
await assert.rejects(createApiKeyOnlyFetch('sb_publishable_local_fixture', async () => {
  throw new Error('an RPC without a signing key must not reach PostgREST');
}, { ...policy, rpcGateway: undefined })(`${API_URL}/rest/v1/rpc/admin_current_user_role`, {
  method: 'POST', headers: { authorization: `Bearer ${USER_JWT}` }, body: '{}',
}), /gateway is not configured/);
checks += 1;
for (const [url, method, token] of [
  [`${API_URL}/rest/v1/courses`, 'GET', USER_JWT],
  [`${API_URL}/rest/v1/rpc/not_allowed`, 'POST', USER_JWT],
  [`${API_URL}/rest/v1/rpc/admin_current_user_role`, 'GET', USER_JWT],
  ['https://example.invalid/auth/v1/user', 'GET', USER_JWT],
  [`${API_URL}/functions/v1/admin-invite`, 'GET', USER_JWT],
  [`${API_URL}/auth/v1/factors`, 'GET', USER_JWT],
  [`${API_URL}/auth/v1/factors/not-a-uuid/verify`, 'POST', USER_JWT],
  [`${API_URL}/auth/v1/user`, 'DELETE', USER_JWT],
  [`${API_URL}/auth/v1/token?grant_type=password`, 'POST', USER_JWT],
  [`${API_URL}/auth/v1/user`, 'GET', 'fixture-not-a-jwt'],
  [`${API_URL}/auth/v1/user#fragment`, 'GET', USER_JWT],
]) {
  const before = sent;
  await assert.rejects(guarded(url, { method, headers: { authorization: `Bearer ${token}` } }), /not allowed/);
  assert.equal(sent, before, 'blocked identities must never reach fetch');
  checks += 1;
}
await assert.rejects(createApiKeyOnlyFetch('sb_publishable_local_fixture', async () => {
  throw new Error('browser transport must never send a user JWT');
})(`${API_URL}/auth/v1/user`, { headers: { authorization: `Bearer ${USER_JWT}` } }), /not allowed/);
checks += 1;

console.log(JSON.stringify({ result: 'PASS', checks, redirectChecks, network: 'intercepted', jwtVerification: 'delegated-to-supabase' }));
