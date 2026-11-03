import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { classifyFetchFailure, classifyHttpStatus, probePostgrest } from './h3req1_c03_postgrest_probe.mjs';
import {
  classifyInviteEarlyResult,
  classifyLoginResult,
  classifyRecoveryReplayFailure,
  isIntegratedFailureCode,
  isLoginFailureCode,
} from './h3req1_c03_login_result.mjs';
import {
  readSafePostgrestErrorCode,
  readSafePostgrestErrorDiagnostic,
} from './h3req1_c03_safe_postgrest_error_code.mjs';
import { classifyRecoveryInvitationRows } from './h3req1_c03_replay_state_diagnostic.mjs';

const runner = readFileSync(new URL('./h3req1_c03_integrated_drill_r50.sh', import.meta.url), 'utf8');
const runtime = readFileSync(new URL('./h3req1_c03_integrated_runtime.mjs', import.meta.url), 'utf8');
const loginResult = readFileSync(new URL('./h3req1_c03_login_result.mjs', import.meta.url), 'utf8');
const edgeInvite = readFileSync(new URL('../supabase/functions/admin-invite/index.ts', import.meta.url), 'utf8');
const postgrestErrorCode = readFileSync(new URL('./h3req1_c03_safe_postgrest_error_code.mjs', import.meta.url), 'utf8');
const probe = readFileSync(new URL('./h3req1_c03_postgrest_probe.mjs', import.meta.url), 'utf8');
const extensionSetup = readFileSync(new URL('./sql/h3req1_c03_integrated_extension_setup_r13.sql', import.meta.url), 'utf8');
const integratedSetup = readFileSync(new URL('./sql/h3req1_c03_integrated_setup.sql', import.meta.url), 'utf8');
const suspendedAssertions = readFileSync(new URL('./sql/h3req1_c03_integrated_assert_suspended.sql', import.meta.url), 'utf8');
const completedSuspendedAssertions = readFileSync(new URL('./sql/h3req1_c03_integrated_assert_completed_suspended.sql', import.meta.url), 'utf8');
const memberGrantMigration = readFileSync(new URL('../db/migrations/20261010_h3_admin_members_service_select.sql', import.meta.url), 'utf8');
const h3Bootstrap = readFileSync(new URL('./sql/h3_from_h2_pro_pg17_harness.sql', import.meta.url), 'utf8');

test('admin-invite membership lookup has a narrow service-role table grant in the PG17 chain', () => {
  assert.match(memberGrantMigration, /^GRANT SELECT ON TABLE public\.admin_members TO service_role;$/m);
  assert.doesNotMatch(memberGrantMigration, /\b(?:anon|authenticated)\b/);
  assert.match(h3Bootstrap, /\\ir \.\.\/\.\.\/db\/migrations\/20261010_h3_admin_members_service_select\.sql/);
  assert.match(h3Bootstrap, /has_table_privilege\('service_role', 'public\.admin_members', 'SELECT'\)/);
});

test('Pages suspension failures expose only a fixed predicate code', () => {
  assert.equal(isIntegratedFailureCode('PAGES_SUSPEND_CONTRACT_FAILED'), true);
  assert.equal(isIntegratedFailureCode('PAGES_SUSPEND_CONTRACT_FAILED_private_detail'), false);
  assert.ok(runtime.includes('function requirePagesSuspensionPredicate(condition, predicate)'));
  assert.ok(runtime.includes('!/^PAGES_[A-Z0-9_]{1,48}$/.test(predicate)'));
  assert.ok(runtime.includes("{ predicate }"));
  assert.doesNotMatch(runtime, /error\.message|payload\.(?:message|details|hint)/,
    'suspension diagnostics must not expose assertion text or response metadata');
});

test('suspended dispatcher diagnostics expose only status and allowlisted SQLSTATE predicates', () => {
  assert.equal(isIntegratedFailureCode('SIGNED_DISPATCHER_CONTRACT_FAILED'), true);
  assert.equal(isIntegratedFailureCode('SIGNED_DISPATCHER_CONTRACT_FAILED_private_detail'), false);
  assert.ok(runtime.includes('function requireSignedDispatcherPredicate(condition, predicate, errorDiagnostic = null)'));
  assert.ok(runtime.includes('!/^SIGNED_DISPATCHER_[A-Z0-9_]{1,40}$/.test(predicate)'));
  assert.ok(runtime.includes('/^(?:PGRST[0-9]{3}|[0-9A-Z]{5}|UNCLASSIFIED)$/'));
  assert.ok(runtime.includes("['NO_BODY', 'OVERSIZED', 'INVALID_JSON', 'CODE_UNRECOGNIZED', 'ALLOWLISTED_CODE', 'READ_FAILED']"));
  assert.ok(runtime.includes("bodyClass === 'ALLOWLISTED_APPLICATION_CODE'"));
  assert.match(runtime, /diagnostic\.responseApplicationCode = \/\^\(\?:RPC_ARGUMENTS_INVALID\|RPC_GATEWAY_UNAVAILABLE\|RPC_METHOD_REJECTED\|RPC_NOT_ALLOWLISTED\|RPC_REPLAY_REJECTED\|RPC_SIGNATURE_INVALID\|RPC_SIGNATURE_REQUIRED\|RPC_SIGNED_WRAPPER_REQUIRED\)\$\//);
  assert.match(runtime,
    /const errorDiagnostic = await readSafePostgrestErrorDiagnostic\(response\);\s*const \{ code \} = errorDiagnostic;\s*requireSignedDispatcherPredicate\(\[401, 403\]\.includes\(response\.status\), 'SIGNED_DISPATCHER_HTTP_STATUS'\);\s*requireSignedDispatcherPredicate\(code === '42501', 'SIGNED_DISPATCHER_SQLSTATE', errorDiagnostic\);/);
  assert.doesNotMatch(runtime, /error\.message|payload\.(?:message|details|hint)/,
    'dispatcher diagnostics must not expose response text or metadata');
});

test('post-resume recovery failures expose only fixed predicates', () => {
  assert.equal(isIntegratedFailureCode('RECOVERY_CONTRACT_FAILED'), true);
  assert.equal(isIntegratedFailureCode('RECOVERY_CONTRACT_FAILED_private_detail'), false);
  assert.ok(runtime.includes('function requireRecoveryPredicate(condition, predicate)'));
  assert.ok(runtime.includes("!/^RECOVERY_[A-Z0-9_]{1,48}$/.test(predicate)"));
  assert.ok(runtime.includes("throw new IntegratedCheckFailure('RECOVERY_CONTRACT_FAILED', { predicate })"));
  for (const predicate of [
    'RECOVERY_EDGE_REPLAY_STATUS', 'RECOVERY_EDGE_REPLAY_INVITATION',
    'RECOVERY_EDGE_REPLAY_NO_SECOND_EMAIL', 'RECOVERY_PAGES_SESSION_STATUS',
    'RECOVERY_PAGES_SESSION_AUTHENTICATED', 'RECOVERY_PAGES_SESSION_AAL2',
    'RECOVERY_ADMIN_RPC_STATUS', 'RECOVERY_ADMIN_ROLE',
  ]) assert.ok(runtime.includes(predicate));
  assert.doesNotMatch(runtime, /error\.message|payload\.(?:message|details|hint)/,
    'recovery diagnostics must not expose assertion text or response metadata');
});

test('replay recovery diagnostics retain bounded status and closed error-code classes', () => {
  assert.deepEqual(classifyRecoveryReplayFailure({ status: 409, errorCode: 'duplicate_pending' }), {
    status: 409,
    errorCodeClass: 'ALLOWLISTED',
    classification: 'INVITE_EARLY_DUPLICATE_PENDING',
  });
  assert.deepEqual(classifyRecoveryReplayFailure({ status: 503, errorCode: 'quota_unavailable' }), {
    status: 503,
    errorCodeClass: 'ALLOWLISTED',
    classification: 'INVITE_EARLY_QUOTA_UNAVAILABLE',
  });
  assert.deepEqual(classifyRecoveryReplayFailure({ status: 403, errorCode: 'secret-like-raw-detail' }), {
    status: 403,
    errorCodeClass: 'UNRECOGNIZED',
    classification: 'INVITE_EARLY_HTTP_403',
  });
  assert.deepEqual(classifyRecoveryReplayFailure({ status: 409 }), {
    status: 409,
    errorCodeClass: 'ABSENT',
    classification: 'INVITE_EARLY_HTTP_409',
  });
  assert.deepEqual(classifyRecoveryReplayFailure({ status: '503', errorCode: 'quota_unavailable' }), {
    status: 'INVALID',
    errorCodeClass: 'STATUS_INVALID',
    classification: 'INVITE_EARLY_HTTP_INVALID',
  });
  assert.equal(isIntegratedFailureCode('INVITE_EARLY_DUPLICATE_PENDING'), true);
  assert.match(runtime, /function requireRecoveryReplayStatus\(response, payload, replayState\)/);
  assert.match(runtime, /classifyRecoveryReplayFailure\(\{[\s\S]*?errorCode: payload\?\.code/);
  assert.match(loginResult, /classification: safeStatus === 'INVALID'[\s\S]*?classifyInviteEarlyResult\(\{ status, errorCode \}\)/);
  assert.match(runtime, /requireRecoveryReplayStatus\(edgeReplay, edgeReplayPayload, replayState\)/);
  assert.doesNotMatch(runtime, /edgeReplayPayload\?\.(?:error\?\.)?(?:message|details|hint)/,
    'replay diagnostics must not include raw response text');
});

test('direct Edge error classification reads only its top-level code field', () => {
  const edgePayload = { error: 'synthetic-only-detail', code: 'duplicate_pending', request_id: 'fixture-id' };
  assert.deepEqual(classifyRecoveryReplayFailure({ status: 409, errorCode: edgePayload.code }), {
    status: 409,
    errorCodeClass: 'ALLOWLISTED',
    classification: 'INVITE_EARLY_DUPLICATE_PENDING',
  });
  assert.deepEqual(classifyRecoveryReplayFailure({ status: 409, errorCode: edgePayload.error?.code }), {
    status: 409,
    errorCodeClass: 'ABSENT',
    classification: 'INVITE_EARLY_HTTP_409',
  });
  assert.match(edgeInvite, /return json\(\{ error: failure\.message, code: failure\.code, request_id: requestId \}/);
  const replayClassifier = runtime.match(/function requireRecoveryReplayStatus\(response, payload, replayState\) \{([\s\S]*?)\n\}/)?.[1] || '';
  assert.match(replayClassifier, /errorCode: payload\?\.code/);
  assert.doesNotMatch(replayClassifier, /payload\?\.error\?\.code/);
  assert.ok(runtime.includes('errorCode: outcome.result.payload?.error?.code'),
    'Pages BFF early responses must keep their nested error.code contract');
  assert.match(runtime, /errorCode: outcome\.result\.payload\?\.error\?\.code/);
  assert.match(runtime, /errorCode: payload\?\.code/);
});

test('replay-state probe emits only fixed classes and synthetic match booleans', () => {
  const expected = {
    requestId: 'fixture-request-id',
    actorId: 'fixture-actor-id',
    email: 'fixture-target@local.test',
    role: 'user',
    targetId: 'fixture-target-id',
  };
  const rows = [{
    id: 'private-invitation-id',
    status: 'pending',
    admin_member_user_id: 'fixture-target-id',
    created_by_user_id: 'fixture-actor-id',
    email: 'fixture-target@local.test',
    role: 'user',
    metadata: {
      request_id: 'fixture-request-id',
      reconciliation_required: false,
      delivery_state: 'completed',
      delivery_method: 'invite',
      redirect: 'https://synthetic-private-value.invalid',
    },
  }];
  const diagnostic = classifyRecoveryInvitationRows(rows, expected);
  assert.deepEqual(diagnostic, {
    rowCountClass: 'ONE',
    requestIdMatches: true,
    actorMatches: true,
    emailMatches: true,
    roleMatches: true,
    statusClass: 'PENDING',
    userIdPresent: true,
    userIdMatches: true,
    reconciliationRequired: false,
    deliveryStateClass: 'COMPLETED',
  });
  assert.doesNotMatch(JSON.stringify(diagnostic), /private-invitation|fixture-|synthetic-private|https?:/);
  assert.deepEqual(classifyRecoveryInvitationRows([{
    ...rows[0],
    status: 'send_failed',
    admin_member_user_id: null,
    created_by_user_id: 'other-actor',
    email: 'other-target@local.test',
    role: 'admin',
    metadata: { request_id: 'other-request', reconciliation_required: true, delivery_state: 'unknown' },
  }], expected), {
    rowCountClass: 'ONE',
    requestIdMatches: false,
    actorMatches: false,
    emailMatches: false,
    roleMatches: false,
    statusClass: 'SEND_FAILED',
    userIdPresent: false,
    userIdMatches: false,
    reconciliationRequired: true,
    deliveryStateClass: 'UNKNOWN',
  });
  assert.deepEqual(classifyRecoveryInvitationRows([], expected), { rowCountClass: 'ZERO' });
  assert.deepEqual(classifyRecoveryInvitationRows([rows[0], rows[0]], expected), { rowCountClass: 'MULTIPLE' });
  assert.deepEqual(classifyRecoveryInvitationRows(null, expected), { rowCountClass: 'INVALID' });
});

test('integrated replay probe is bounded, read-only, fixed-target and output-sanitized', () => {
  const probe = runtime.match(/async function readRecoveryInvitationState\(\) \{([\s\S]*?)\n\}/)?.[1] || '';
  assert.match(runtime, /const POSTGREST_BASE = new URL\('http:\/\/h3req1-c03-postgrest:3000\/'\)/);
  assert.match(probe, /new URL\('\/admin_invitations', POSTGREST_BASE\)/);
  assert.match(runtime, /const TARGET_EMAIL = 'c03-inflight@local\.test'/);
  assert.match(probe, /query\.searchParams\.set\('email', `eq\.\$\{TARGET_EMAIL\}`\)/);
  assert.doesNotMatch(probe, /query\.searchParams\.set\('metadata->>request_id'/);
  assert.doesNotMatch(probe, /\/rest\/v1\/admin_invitations/);
  assert.match(probe, /query\.searchParams\.set\('limit', '2'\)/);
  assert.match(probe, /method: 'GET'/);
  assert.match(probe, /apikey: SERVICE_KEY, Authorization: `Bearer \$\{serviceJwt\(\)\}`/);
  assert.match(probe, /byteLength > 8_192/);
  assert.match(probe, /classifyRecoveryInvitationRows\(rows/);
  assert.doesNotMatch(probe, /console\.|process\.stdout|JSON\.stringify\((?:rows|payload)|error\.message/);
  const recoveryFlow = runtime.match(/async function pagesAndEdgeRecovery\(\) \{([\s\S]*?)\n\}/)?.[1] || '';
  assert.ok(recoveryFlow.indexOf('const replayState = await readRecoveryInvitationState()')
    < recoveryFlow.indexOf('const edgeReplay = await fetch('));
  const replayCheck = runtime.match(/function requireRecoveryReplayStatus\(response, payload, replayState\) \{([\s\S]*?)\n\}/)?.[1] || '';
  assert.match(replayCheck, /if \(response\.status === 200\) return/);
  assert.match(replayCheck, /replayState/);
});

test('signed-dispatcher context probe exposes only fixed synthetic booleans', () => {
  assert.match(integratedSetup, /CREATE OR REPLACE FUNCTION public\.h3_c03_request_context_probe\(\)[\s\S]*RETURNS JSONB[\s\S]*SECURITY DEFINER/);
  for (const field of [
    'role_authenticated', 'actor_matches', 'legacy_sub_matches', 'claims_sub_matches',
    'key_id_present', 'actor_header_present',
    'issued_at_present', 'nonce_present', 'metadata_signature_present', 'payload_signature_present',
  ]) assert.ok(integratedSetup.includes(`'${field}'`));
  assert.match(integratedSetup, /REVOKE ALL ON FUNCTION public\.h3_c03_request_context_probe\(\) FROM PUBLIC, anon, service_role/);
  assert.match(integratedSetup, /GRANT EXECUTE ON FUNCTION public\.h3_c03_request_context_probe\(\) TO authenticated/);
  assert.match(h3Bootstrap,
    /CREATE FUNCTION auth\.uid\(\)[\s\S]*?SELECT COALESCE\([\s\S]*?current_setting\('request\.jwt\.claim\.sub'[\s\S]*?current_setting\('request\.jwt\.claims'[\s\S]*?->> 'sub'[\s\S]*?\)::UUID/);
  assert.match(runtime, /SIGNED_DISPATCHER_CONTEXT_SUB_SOURCE/);
  assert.match(runtime, /\/rpc\/h3_c03_request_context_probe/);
  assert.doesNotMatch(runtime, /console\.log\(requestContext|process\.stdout\.write\(.*requestContext/);
});

test('suspension SQL failures are classified by SQLSTATE without emitting raw psql output', () => {
  const expectedSqlstates = Array.from({ length: 12 }, (_, index) => `H3S${String(index + 1).padStart(2, '0')}`);
  const actualSqlstates = [...suspendedAssertions.matchAll(/ERRCODE = '(H3S[0-9]{2})'/g)].map((match) => match[1]);
  assert.deepEqual(actualSqlstates, expectedSqlstates);
  assert.match(runner, /-v VERBOSITY=verbose -v ON_ERROR_STOP=1/);
  assert.ok(runner.includes('^psql:.*:[0-9]+:[[:space:]]+ERROR:[[:space:]]+([A-Z0-9]{5}):'));
  assert.equal('psql:/tmp/synthetic.sql:1: ERROR:  H3S04: synthetic-only'.match(/^psql:.*:[0-9]+:\s+ERROR:\s+([A-Z0-9]{5}):/)?.[1], 'H3S04');
  assert.equal('psql:/tmp/synthetic.sql:1: ERROR:  private: synthetic-only'.match(/^psql:.*:[0-9]+:\s+ERROR:\s+([A-Z0-9]{5}):/)?.[1], undefined);
  assert.ok(runner.includes('^ERROR:[[:space:]]+([A-Z0-9]{5}):'));
  assert.equal('ERROR:  H3S04: synthetic-only'.match(/^ERROR:\s+([A-Z0-9]{5}):/)?.[1], 'H3S04');
  assert.equal('SQL state: 42501'.match(/^SQL state: ([A-Z0-9]{5})$/)?.[1], '42501');
  assert.equal('ERROR:  private: synthetic-only'.match(/^ERROR:\s+([A-Z0-9]{5}):/)?.[1], undefined);
  assert.match(runner, /SQL\\ state:\\ \(\[A-Z0-9\]\{5\}\)/);
  assert.match(runner, /sql-gate-failure\|label=%s\|exit=%s\|code=%s/);
  assert.doesNotMatch(runner, /printf[^\n]*sql_output|fail[^\n]*sql_output/);
});

test('suspended admin continuity and invitation audit are separate predicates', () => {
  assert.match(suspendedAssertions, /SELECT 1 FROM public\.admin_members[\s\S]*?ERRCODE = 'H3S11'/);
  assert.match(suspendedAssertions, /IF EXISTS \([\s\S]*?public\.admin_membership_audit[\s\S]*?ERRCODE = 'H3S12'/);
  assert.match(completedSuspendedAssertions, /count\(\*\) FROM public\.admin_membership_audit[\s\S]*?IS DISTINCT FROM 1/);
});

test('Pages requests preserve a literal double-slash path on the original host', () => {
  assert.match(runtime, /const url = new URL\(`https:\/\/\$\{hostname\}\$\{pathname\}`\)/);
  const oldReference = new URL('//admin/', 'https://admin.local.test');
  const literalPath = new URL('https://admin.local.test//admin/');
  assert.equal(oldReference.hostname, 'admin');
  assert.equal(oldReference.pathname, '/');
  assert.equal(literalPath.hostname, 'admin.local.test');
  assert.equal(literalPath.pathname, '//admin/');
});

test('PostgREST diagnostics expose only bounded allowlisted error codes', async () => {
  assert.equal(await readSafePostgrestErrorCode(new Response(JSON.stringify({ code: 'PGRST116', message: 'private detail' }), { status: 403 })), 'PGRST116');
  assert.equal(await readSafePostgrestErrorCode(new Response(JSON.stringify({ code: '42501', message: 'private detail' }), { status: 403 })), '42501');
  assert.equal(await readSafePostgrestErrorCode(new Response(JSON.stringify({ code: 'pgrst116' }), { status: 403 })), 'UNCLASSIFIED');
  assert.equal(await readSafePostgrestErrorCode(new Response(JSON.stringify({ code: 'PGRST12' }), { status: 403 })), 'UNCLASSIFIED');
  assert.equal(await readSafePostgrestErrorCode(new Response(JSON.stringify({ code: 42501 }), { status: 403 })), 'UNCLASSIFIED');
  assert.equal(await readSafePostgrestErrorCode(new Response(JSON.stringify([{ code: '42501' }]), { status: 403 })), 'UNCLASSIFIED');
  assert.equal(await readSafePostgrestErrorCode(new Response(JSON.stringify({ code: 'fixture_api_key_rejected', message: 'private detail' }), { status: 403 })), 'UNCLASSIFIED');
  assert.equal(await readSafePostgrestErrorCode(new Response(JSON.stringify({ message: 'private detail' }), { status: 403 })), 'UNCLASSIFIED');
  assert.equal(await readSafePostgrestErrorCode(new Response('{not-json', { status: 403 })), 'UNCLASSIFIED');
  assert.equal(await readSafePostgrestErrorCode(new Response(null, { status: 403 })), 'UNCLASSIFIED');
  assert.equal(await readSafePostgrestErrorCode(new Response(JSON.stringify({ code: '42501', details: 'x'.repeat(9000) }), { status: 403 })), 'UNCLASSIFIED');
  assert.deepEqual(await readSafePostgrestErrorDiagnostic(new Response(JSON.stringify({ code: '42501' }), { status: 403 })),
    { code: '42501', bodyClass: 'ALLOWLISTED_CODE' });
  assert.deepEqual(await readSafePostgrestErrorDiagnostic(new Response(null, { status: 403 })),
    { code: 'UNCLASSIFIED', bodyClass: 'NO_BODY' });
  assert.deepEqual(await readSafePostgrestErrorDiagnostic(new Response('{not-json', { status: 403 })),
    { code: 'UNCLASSIFIED', bodyClass: 'INVALID_JSON' });
  assert.deepEqual(await readSafePostgrestErrorDiagnostic(new Response(JSON.stringify({ code: 'private' }), { status: 403 })),
    { code: 'UNCLASSIFIED', bodyClass: 'CODE_UNRECOGNIZED' });
  for (const [code, classified] of [
    ['rpc_arguments_invalid', 'RPC_ARGUMENTS_INVALID'],
    ['rpc_gateway_unavailable', 'RPC_GATEWAY_UNAVAILABLE'],
    ['rpc_method_rejected', 'RPC_METHOD_REJECTED'],
    ['rpc_not_allowlisted', 'RPC_NOT_ALLOWLISTED'],
    ['rpc_replay_rejected', 'RPC_REPLAY_REJECTED'],
    ['rpc_signature_invalid', 'RPC_SIGNATURE_INVALID'],
    ['rpc_signature_required', 'RPC_SIGNATURE_REQUIRED'],
    ['rpc_signed_wrapper_required', 'RPC_SIGNED_WRAPPER_REQUIRED'],
  ]) {
    assert.deepEqual(await readSafePostgrestErrorDiagnostic(new Response(JSON.stringify({ code }), { status: 403 })),
      { code: 'UNCLASSIFIED', bodyClass: 'ALLOWLISTED_APPLICATION_CODE', applicationCode: classified });
  }
  assert.deepEqual(await readSafePostgrestErrorDiagnostic(new Response(JSON.stringify({ code: 'rpc_custom_private' }), { status: 403 })),
    { code: 'UNCLASSIFIED', bodyClass: 'CODE_UNRECOGNIZED' });
  assert.deepEqual(await readSafePostgrestErrorDiagnostic(new Response(JSON.stringify({ code: '42501', details: 'x'.repeat(9000) }), { status: 403 })),
    { code: 'UNCLASSIFIED', bodyClass: 'OVERSIZED' });
  assert.match(await (async () => {
    const response = new Response(JSON.stringify({ code: '42501', message: 'private detail' }), { status: 403 });
    await readSafePostgrestErrorCode(response);
    return response.text();
  })(), /private detail/);
  assert.match(runtime, /adminMemberLastCode: 'NONE'/);
  assert.match(runtime, /counters\.adminMemberLastCode = await readSafePostgrestErrorCode\(upstream\)/);
  assert.match(runtime, /'adminMemberLastStatus', 'adminMemberLastCode'/);
  assert.match(postgrestErrorCode, /PGRST\[0-9\]\{3\}/);
  assert.match(postgrestErrorCode, /MAX_ERROR_BODY_BYTES = 8192/);
  assert.doesNotMatch(runtime, /upstream\.(?:text|json)\(\)/);
});

test('synthetic Edge TLS trust anchor is merged into the system bundle before runtime startup', () => {
  assert.ok(runner.includes('--env DENO_CERT=/tmp/ca-bundle.pem'),
    'Edge Runtime must receive the temporary local CA bundle path');
  assert.ok(runner.includes('--env DENO_TLS_CA_STORE=system --env SSL_CERT_FILE=/tmp/ca-bundle.pem'),
    'Edge Runtime must use the verified system bundle and Deno system store');
  assert.ok(runner.includes('cat /etc/ssl/certs/ca-certificates.crt /run/c03-certs/ca.pem > /tmp/ca-bundle.pem'),
    'Edge Runtime must append only the synthetic CA to the pinned image system roots');
  assert.ok(runner.includes('test -s /tmp/ca-bundle.pem && exec edge-runtime start'),
    'Edge Runtime must start only after the bundle exists');
  assert.ok(runtime.includes("'-addext', 'basicConstraints=critical,CA:TRUE'"),
    'synthetic root certificate must be marked as a CA');
  assert.ok(runtime.includes("'-addext', 'keyUsage=critical,keyCertSign,cRLSign'"),
    'synthetic root certificate must be authorized to sign certificates');
  assert.ok(runtime.includes('assert.match(caDetails, /X509v3 Basic Constraints: critical\\s+CA:TRUE/'),
    'runtime must fail closed when the generated root is not a CA');
  assert.ok(runtime.includes('assert.match(caDetails, /X509v3 Key Usage: critical\\s+Certificate Sign, CRL Sign/'),
    'runtime must fail closed when the generated root cannot sign certificates');
  assert.ok(runtime.includes('assert.match(serverDetails, /X509v3 Basic Constraints: critical\\s+CA:FALSE/'),
    'runtime must reject a leaf certificate marked as a CA');
  assert.ok(runtime.includes('assert.match(serverDetails, /DNS:local\\.supabase\\.co/'),
    'runtime must verify the gateway hostname in the leaf SAN');
  assert.ok(runtime.includes("['verify', '-CAfile', caCert, serverCert]"),
    'runtime must verify the generated server certificate against the root');
});

test('pinned OpenSSL emits the constrained CA and a hostname-valid TLS server leaf', () => {
  const directory = mkdtempSync(join(tmpdir(), 'h3req1-c03-ca-contract-'));
  const caKey = join(directory, 'ca.key');
  const caCert = join(directory, 'ca.pem');
  const serverKey = join(directory, 'server.key');
  const serverCsr = join(directory, 'server.csr');
  const serverCert = join(directory, 'server.pem');
  const extensions = join(directory, 'server.ext');
  try {
    execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-sha256', '-days', '2',
      '-subj', '/CN=H3REQ1 C03 synthetic local CA',
      '-addext', 'basicConstraints=critical,CA:TRUE',
      '-addext', 'keyUsage=critical,keyCertSign,cRLSign',
      '-addext', 'subjectKeyIdentifier=hash', '-keyout', caKey, '-out', caCert], { stdio: 'ignore' });
    execFileSync('openssl', ['req', '-new', '-newkey', 'rsa:2048', '-nodes', '-sha256',
      '-subj', '/CN=local.supabase.co', '-keyout', serverKey, '-out', serverCsr], { stdio: 'ignore' });
    writeFileSync(extensions, [
      'basicConstraints=critical,CA:FALSE',
      'keyUsage=critical,digitalSignature,keyEncipherment',
      'extendedKeyUsage=serverAuth',
      'subjectAltName=DNS:local.supabase.co',
    ].join('\n') + '\n');
    execFileSync('openssl', ['x509', '-req', '-sha256', '-days', '2', '-in', serverCsr,
      '-CA', caCert, '-CAkey', caKey, '-CAcreateserial', '-extfile', extensions, '-out', serverCert], { stdio: 'ignore' });
    const caDetails = execFileSync('openssl', ['x509', '-in', caCert, '-noout', '-text'], { encoding: 'utf8' });
    const serverDetails = execFileSync('openssl', ['x509', '-in', serverCert, '-noout', '-text'], { encoding: 'utf8' });
    const verification = execFileSync('openssl', ['verify', '-CAfile', caCert, serverCert], { encoding: 'utf8' });
    assert.match(caDetails, /X509v3 Basic Constraints: critical\s+CA:TRUE/);
    assert.match(caDetails, /X509v3 Key Usage: critical\s+Certificate Sign, CRL Sign/);
    assert.match(serverDetails, /X509v3 Basic Constraints: critical\s+CA:FALSE/);
    assert.match(serverDetails, /X509v3 Extended Key Usage:\s+TLS Web Server Authentication/);
    assert.match(serverDetails, /DNS:local\.supabase\.co/);
    assert.match(verification, /: OK\s*$/);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('integrated runner uses the manifest path consumed by the runtime', () => {
  assert.match(runner, /readonly MANIFEST='tests\/h3req1-c03-integrated-r50\.sha256'/,
    'runner manifest path differs from the integrated runtime contract');
  assert.match(runtime, /INTEGRATED_SOURCE_MANIFEST = process\.env\.H3_C03_MANIFEST_PATH \|\| 'tests\/h3req1-c03-integrated\.sha256'/,
    'integrated runtime does not preserve the legacy default manifest path');
  assert.ok(runner.includes('--env H3_C03_MANIFEST_PATH="$MANIFEST"'),
    'runner does not pass its pinned manifest path to the runtime');
});

test('integrated fixture provides the configured PostgREST extra search path schema', () => {
  assert.match(runner, /PGRST_DB_EXTRA_SEARCH_PATH=public,extensions/,
    'PostgREST extra search path changed without updating the disposable fixture');
  assert.match(extensionSetup,
    /CREATE SCHEMA IF NOT EXISTS extensions AUTHORIZATION postgres;/,
    'fresh PG17 fixture omits the extensions schema required by the configured search path');
});

test('integrated PG17 service role mirrors Supabase row security bypass', () => {
  assert.match(extensionSetup, /ALTER ROLE service_role BYPASSRLS;/,
    'isolated PostgREST fixture role cannot read the RLS-protected invitation reservation');
  assert.match(extensionSetup,
    /rolbypassrls[\s\S]{0,160}service_role[\s\S]{0,160}RAISE EXCEPTION/,
    'fixture does not assert that the role attribute was applied');
});

test('login diagnostics classify each strict acceptance predicate without exposing values', () => {
  const passing = { status: 200, aal: 'aal2', authCookie: true, activityCookie: true };
  assert.equal(classifyLoginResult(passing), null);
  assert.equal(classifyLoginResult({ ...passing, status: 401 }), 'LOGIN_HTTP_STATUS_401');
  assert.equal(classifyLoginResult({ ...passing, status: 503 }), 'LOGIN_HTTP_STATUS_503');
  assert.equal(classifyLoginResult({ status: 403, errorCode: 'csrf_rejected' }), 'LOGIN_CSRF_REJECTED');
  assert.equal(classifyLoginResult({ status: 403, errorCode: 'private or unknown code' }), 'LOGIN_HTTP_STATUS_403');
  assert.equal(classifyLoginResult({ status: 403, errorCode: 'csrf_rejected_private_detail' }), 'LOGIN_HTTP_STATUS_403');
  assert.equal(classifyLoginResult({ ...passing, status: 'private body' }), 'LOGIN_HTTP_STATUS_INVALID');
  assert.equal(classifyLoginResult({ ...passing, status: 600 }), 'LOGIN_HTTP_STATUS_INVALID');
  assert.equal(classifyLoginResult({ ...passing, aal: 'aal1' }), 'LOGIN_AAL_NOT_AAL2');
  assert.equal(classifyLoginResult({ ...passing, authCookie: false }), 'LOGIN_AUTH_COOKIE_MISSING');
  assert.equal(classifyLoginResult({ ...passing, activityCookie: false }), 'LOGIN_ACTIVITY_COOKIE_MISSING');
  assert.deepEqual([
    'LOGIN_HTTP_STATUS_401',
    'LOGIN_HTTP_STATUS_503',
    'LOGIN_CSRF_REJECTED',
    'LOGIN_AAL_NOT_AAL2',
    'LOGIN_AUTH_COOKIE_MISSING',
    'LOGIN_ACTIVITY_COOKIE_MISSING',
  ].map(isLoginFailureCode), [true, true, true, true, true, true]);
  assert.equal(isLoginFailureCode('LOGIN_CSRF_REJECTED_private_detail'), false);
  assert.equal(isLoginFailureCode('private response body'), false);
  assert.equal(classifyLoginResult({ status: 200, aal: 'private email', authCookie: true, activityCookie: true }),
    'LOGIN_AAL_NOT_AAL2');
});

test('early invitation outcomes use fixed allowlisted codes and never return raw payload data', () => {
  assert.equal(classifyInviteEarlyResult({ status: 403, errorCode: 'mfa_required' }), 'INVITE_EARLY_MFA_REQUIRED');
  assert.equal(classifyInviteEarlyResult({ status: 403, errorCode: 'csrf_rejected' }), 'INVITE_EARLY_CSRF_REJECTED');
  assert.equal(classifyInviteEarlyResult({ status: 503, errorCode: 'private or unknown code' }), 'INVITE_EARLY_HTTP_503');
  assert.equal(classifyInviteEarlyResult({ status: 200 }), 'INVITE_COMPLETED_BEFORE_AUTH_HOLD');
  assert.equal(classifyInviteEarlyResult({ status: 204 }), 'INVITE_COMPLETED_BEFORE_AUTH_HOLD');
  assert.equal(classifyInviteEarlyResult({ status: 900 }), 'INVITE_EARLY_HTTP_INVALID');
  assert.deepEqual([
    'INVITE_EARLY_MFA_REQUIRED', 'INVITE_EARLY_HTTP_503',
    'INVITE_AUTH_HOLD_TIMEOUT', 'INVITE_REQUEST_TRANSPORT_FAILURE',
  ].map(isIntegratedFailureCode), [true, true, true, true]);
  assert.equal(isIntegratedFailureCode('INVITE_EARLY_MFA_REQUIRED_private_detail'), false);
});

test('early invitation diagnostics expose only fixed synthetic stage counters', () => {
  const fields = [
    'authUserRequests', 'authUserCredentialRejected', 'authUserSessionRejected', 'authUserAccepted',
    'adminMemberRequests', 'adminMemberCredentialRejected', 'adminMemberFailureResponses',
    'adminMemberLastStatus', 'functionRequests', 'functionCredentialRejected',
    'functionSessionRejected', 'functionCalls', 'requestAdmission', 'invitationReserve',
  ];
  assert.ok(fields.every((field) => !/(?:api.?key|token|secret|password|authorization|bearer)/i.test(field)),
    'diagnostic field names must survive the credential-oriented output filter');
  for (const field of fields) assert.ok(runtime.includes(`'${field}'`), `missing closed diagnostic field ${field}`);
  assert.match(runtime, /function inviteDiagnostic\(baseline\)/,
    'early invitation diagnostic does not use the fixed counter selector');
  assert.match(runtime, /diagnostic: error\.diagnostic/,
    'control failure does not return the synthetic diagnostic object');
  assert.doesNotMatch(runtime, /error\.message|payload\.(?:message|details|hint)/,
    'early diagnostic exposes untrusted error or response text');
});

test('in-flight wait classifies an early response before the exec timeout', () => {
  assert.ok(runtime.includes('async function waitForInviteHold(baseline, timeoutMs = 30_000)'),
    'invite hold diagnostic still waits as long as its enclosing exec deadline');
  assert.ok(runtime.includes('inFlightInvite.then('),
    'invite hold diagnostic does not observe completion before the Auth hold');
  assert.ok(runtime.includes('classifyInviteEarlyResult({'),
    'early invite result is not classified by the closed helper');
  assert.ok(runtime.includes('errorCode: outcome.result.payload?.error?.code'),
    'early diagnostic does not read only the allowlisted response code');
  assert.ok(runtime.includes('INVITE_REQUEST_TRANSPORT_FAILURE'),
    'transport rejection has no closed diagnostic code');
  assert.ok(runtime.includes('INVITE_AUTH_HOLD_TIMEOUT'),
    'hold timeout has no closed diagnostic code');
  assert.doesNotMatch(runtime, /payload\.(?:message|details|hint)/,
    'early response diagnosis reads untrusted text metadata');
});

test('runtime emits only an allowlisted login check code on classified failure', () => {
  assert.match(runtime, /classifyLoginResult\(\{[\s\S]{0,240}activityCookie:[\s\S]{0,160}\}\)/,
    'runtime does not classify the complete login contract');
  assert.match(runtime, /errorCode:\s*payload\.error\?\.code/,
    'runtime does not pass the closed BFF error code into the login classifier');
  assert.match(runtime, /error instanceof IntegratedCheckFailure && isIntegratedFailureCode\(error\.code\)/,
    'failure response does not validate diagnostic codes against the closed allowlist');
  assert.doesNotMatch(runtime, /error\.message|payload\.(?:message|details|hint)/,
    'runtime exposes untrusted error or response details');
});

test('synthetic mutation request preserves the same origin workerd validates', () => {
  assert.match(runtime, /const url = new URL\(`https:\/\/\$\{hostname\}\$\{pathname\}`\)/,
    'request URL is not constructed from the same host used by the synthetic browser');
  assert.match(runtime, /headers\.set\('Origin', url\.origin\)/,
    'mutation Origin is not derived from its request URL');
  assert.match(runtime, /headers\.set\('Sec-Fetch-Site', 'same-origin'\)/,
    'mutation is missing the browser same-origin fetch metadata');
  assert.ok(/const request = new workerRequestConstructor\(url,/.test(runtime),
    'worker input is not a Request with the asserted URL and headers');
  assert.match(runtime, /const response = await worker\.fetch\(request\)/,
    'workerd is not invoked with the Request whose origin was checked');
  assert.match(runtime, /new URL\(request\.headers\.get\('Origin'\)\)\.origin,[\s\S]{0,120}new URL\(request\.url\)\.origin/,
    'synthetic mutation request does not assert matching URL and Origin before dispatch');
});

test('Miniflare request uses its compatible Undici classes and explicit admin host route', () => {
  assert.match(runtime, /const \{ Request: MiniflareRequest, Headers: MiniflareHeaders \} = require\('undici'\)/,
    'runtime does not load the HTTP classes from the pinned Miniflare dependency');
  assert.match(runtime, /workerRequestConstructor = MiniflareRequest/,
    'runtime does not use Miniflare-compatible Request class');
  assert.match(runtime, /workerHeadersConstructor = MiniflareHeaders/,
    'runtime does not use Miniflare-compatible Headers class');
  assert.ok(runtime.includes("routes: ['admin.local.test/*', 'studiamatch.com/*']"),
    'Miniflare must allow the exact Admin and public hostnames used by the smoke cases');
  assert.match(runtime, /new workerHeadersConstructor\(/,
    'synthetic request headers are constructed outside the Miniflare-compatible HTTP implementation');
  assert.match(runtime, /new workerRequestConstructor\(url,/,
    'synthetic request is not constructed with the Miniflare-compatible Request class');
});

test('every Docker image run forbids implicit pulls', () => {
  const runLines = runner.split(/\r?\n/).filter((line) => /\b(?:docker run|bounded_docker \d+ run)\b/.test(line));

  assert.ok(runLines.length >= 7, `expected at least seven image runs, got ${runLines.length}`);
  for (const line of runLines) {
    assert.match(line, /--pull=never\b/, 'a Docker image run lacks --pull=never');
  }
});

test('Docker operations stay on the attested endpoint after target verification', () => {
  assert.match(runner, /readonly DOCKER_BIN='\/usr\/bin\/docker'/, 'Docker CLI path is not fixed');
  assert.match(
    runner,
    /docker\(\) \{[\s\S]{0,180}if \(\( DOCKER_TARGET_VERIFIED == 1 \)\); then\s+docker_target=\(--host "\$EXPECTED_DOCKER_HOST"\)/,
    'post-attestation Docker calls are not pinned to the verified endpoint',
  );
  assert.match(runner, /\/usr\/bin\/timeout --foreground --signal=TERM --kill-after=3s 60s[\s\S]{0,100}"\$DOCKER_BIN" "\$\{docker_target\[@\]\}" "\$@"/,
    'direct Docker CLI calls do not have a host deadline');
  assert.match(runner, /DOCKER_TARGET_VERIFIED=1\s+printf 'Docker target PASS:/, 'target verification is not recorded');
});

test('foreground snapshot and cache verifier runs have individual deadlines', () => {
  assert.match(runner, /bounded_docker 300 run --pull=never[\s\S]{0,220}\$SNAPSHOT_BOOTSTRAP/,
    'snapshot bootstrap Docker run is not bounded');
  assert.match(runner, /DEPENDENCY_DIGESTS="\$\(bounded_docker 180 run --pull=never[\s\S]{0,220}\$CACHE_VERIFY/,
    'dependency cache verifier Docker run is not bounded');
});

test('timeout-wrapped Docker helpers pin the attested endpoint outside the shell wrapper', () => {
  const boundedDocker = runner.match(/bounded_docker\(\) \{([\s\S]*?)\n\}/)?.[1] ?? '';
  const boundedExec = runner.match(/bounded_exec\(\) \{([\s\S]*?)\n\}/)?.[1] ?? '';

  assert.match(boundedDocker, /if \(\( DOCKER_TARGET_VERIFIED == 1 \)\); then[\s\S]*docker_target=\(--host "\$EXPECTED_DOCKER_HOST"\)/,
    'bounded Docker helper does not select the verified endpoint');
  assert.match(boundedDocker, /"\$DOCKER_BIN" "\$\{docker_target\[@\]\}" "\$@"/,
    'bounded Docker helper bypasses the fixed CLI or endpoint arguments');
  assert.match(boundedExec, /if \(\( DOCKER_TARGET_VERIFIED == 1 \)\); then[\s\S]*docker_target=\(--host "\$EXPECTED_DOCKER_HOST"\)/,
    'bounded exec helper does not select the verified endpoint');
  assert.match(boundedExec, /"\$DOCKER_BIN" "\$\{docker_target\[@\]\}" exec "\$container"/,
    'bounded exec helper bypasses the fixed CLI or endpoint arguments');
});

test('Docker exec has host and in-container deadlines', () => {
  assert.match(
    runner,
    /outer_seconds=\$\(\(seconds \+ 10\)\)[\s\S]{0,350}"\$DOCKER_BIN" "\$\{docker_target\[@\]\}" exec "\$container"[\s\S]{0,150}\/usr\/bin\/timeout[\s\S]{0,100}"\$\{seconds\}s"/,
    'docker exec does not have nested bounded timeouts',
  );
  assert.match(runner, /bounded_exec "\$PG" 90 psql/, 'SQL execution has no deadline');
  assert.match(runner, /bounded_exec "\$PG" 2 pg_isready/, 'PostgreSQL readiness has no deadline');
  assert.match(runner, /bounded_exec "\$RUNTIME" 5 node \/candidate\/tests\/h3req1_c03_postgrest_probe\.mjs/,
    'PostgREST readiness has no classified bounded probe');
  assert.match(runner, /control "\$command" 5/, 'control readiness has no short deadline');
});

test('PostgREST probe separates sanitized HTTP and transport failures', async () => {
  assert.equal(classifyHttpStatus(200), 'OK');
  assert.equal(classifyHttpStatus(503), 'HTTP_503');
  assert.equal(classifyHttpStatus(Number.NaN), 'HTTP_STATUS_INVALID');
  assert.equal(classifyFetchFailure({ cause: { code: 'ECONNREFUSED' }, message: 'private detail' }), 'ECONNREFUSED');
  assert.equal(classifyFetchFailure({ name: 'TimeoutError', message: 'private detail' }), 'TIMEOUT');
  assert.equal(classifyFetchFailure({ cause: { code: 'PRIVATE_CODE' }, message: 'private detail' }), 'FETCH_FAILED');
  assert.equal(await probePostgrest(async () => ({ status: 204 })), 'phase=postgrest-probe|error_code=OK');
  assert.equal(await probePostgrest(async () => ({ status: 503 })), 'phase=postgrest-probe|error_code=HTTP_503');
  assert.equal(await probePostgrest(async () => { throw new Error('private detail'); }),
    'phase=postgrest-probe|error_code=FETCH_FAILED');
  assert.match(runner, /probe_output="\$\(bounded_exec "\$RUNTIME" 5 node \/candidate\/tests\/h3req1_c03_postgrest_probe\.mjs/,
    'integrated run does not execute the classified probe');
  assert.match(runner, /error_code=\(HTTP_\[1-5\]\[0-9\]\{2\}/,
    'failure evidence does not preserve sanitized HTTP classification');
  assert.match(runner, /error_code=\(HTTP_\[1-5\]\[0-9\]\{2\}\(_\(PGRST/,
    'runner rejects allowlisted PostgREST error codes');
});

test('HTTP error diagnosis reads only bounded JSON code values', async () => {
  const encoded = (value) => new TextEncoder().encode(value);
  const readResponse = (status, bytes) => {
    let offset = 0;
    let bytesDelivered = 0;
    let cancelled = false;
    return {
      response: {
        status,
        body: {
          getReader(options) {
            assert.deepEqual(options, { mode: 'byob' }, 'probe must use a bounded byte reader');
            return {
              async read(view) {
                if (offset >= bytes.byteLength) return { done: true };
                const size = Math.min(view.byteLength, bytes.byteLength - offset);
                view.set(bytes.subarray(offset, offset + size));
                offset += size;
                bytesDelivered += size;
                return { done: false, value: view.subarray(0, size) };
              },
              async cancel() { cancelled = true; },
              releaseLock() {},
            };
          },
        },
      },
      get bytesDelivered() { return bytesDelivered; },
      get cancelled() { return cancelled; },
    };
  };

  const pgrst = readResponse(503, encoded(
    JSON.stringify({ code: 'PGRST000', message: 'private detail', details: 'private metadata' }),
  ));
  assert.equal(await probePostgrest(async () => pgrst.response), 'phase=postgrest-probe|error_code=HTTP_503_PGRST000');
  assert.ok(pgrst.bytesDelivered <= 8192);

  const sqlstate = readResponse(503, encoded(
    JSON.stringify({ code: '08006', message: 'private detail' }),
  ));
  assert.equal(await probePostgrest(async () => sqlstate.response), 'phase=postgrest-probe|error_code=HTTP_503_08006');

  const privateCode = readResponse(503, encoded(
    JSON.stringify({ code: 'SECRET_VALUE', message: 'private detail' }),
  ));
  assert.equal(await probePostgrest(async () => privateCode.response), 'phase=postgrest-probe|error_code=HTTP_503');
  const invalidJson = readResponse(503, encoded('not-json'));
  assert.equal(await probePostgrest(async () => invalidJson.response), 'phase=postgrest-probe|error_code=HTTP_503');

  const oversized = readResponse(503, new Uint8Array(8193));
  assert.equal(await probePostgrest(async () => oversized.response), 'phase=postgrest-probe|error_code=HTTP_503');
  assert.equal(oversized.bytesDelivered, 8192, 'probe consumed more than the byte cap');
  assert.equal(oversized.cancelled, true, 'oversized error body was not cancelled');

  const liveResponse = new Response(JSON.stringify({ code: 'PGRST000', message: 'private detail' }), { status: 503 });
  assert.equal(await probePostgrest(async () => liveResponse), 'phase=postgrest-probe|error_code=HTTP_503_PGRST000',
    'the Fetch response byte stream must support bounded BYOB reads');
  assert.match(probe, /ERROR_BODY_LIMIT_BYTES = 8192/, 'HTTP body byte cap changed');
  assert.match(probe, /getReader\(\{ mode: 'byob' \}\)/, 'probe must not use an unbounded default stream reader');
  assert.match(probe, /bytesRead >= ERROR_BODY_LIMIT_BYTES/, 'HTTP body limit is not enforced while streaming');
  assert.match(probe, /SAFE_SERVER_ERROR_CODE = \/\^\(\?:PGRST\[0-9\]\{3\}\|\[A-Z0-9\]\{5\}\)\$\//,
    'error code allowlist changed unexpectedly');
  assert.doesNotMatch(probe, /payload\.(?:message|details|hint)/,
    'probe reads message/detail fields from server responses');
});

test('failure handling only stops this run after local daemon attestation', () => {
  assert.match(runner, /stop_owned_running_services_best_effort\(\) \{\s+\(\( DOCKER_TARGET_VERIFIED == 1 \)\) \|\| return 0/, 'failure stop is not daemon-gated');
  assert.match(runner, /\$jit_label" == "\$JIT"[\s\S]{0,140}\$manifest_label" == "\$APPROVED_MANIFEST_SHA256"[\s\S]{0,100}\$run_label" == "\$RUN_NONCE"/, 'failure stop does not verify all run labels');
  assert.match(runner, /on_error\(\) \{[\s\S]{0,150}stop_owned_running_services_best_effort/, 'error trap does not stop run-owned services');
  assert.match(runner, /on_signal\(\) \{[\s\S]{0,300}stop_owned_running_services_best_effort/, 'signal trap does not stop run-owned services');
  assert.match(runner, /fail\(\) \{[\s\S]{0,100}stop_owned_running_services_best_effort/, 'explicit failures do not stop run-owned services');
  assert.match(runner, /bounded_docker 90 run --pull=never --rm --name "\$CONTRACT_TEST"/, 'contract test container is not bounded and run-owned');
  assert.match(runner, /--label "com\.studiamatch\.h3\.c03\.run=\$RUN_NONCE"[\s\S]{0,450}\$NODE_IMAGE" node --test/, 'contract test container lacks current run labels');
  assert.match(runner, /check_free_container "\$CONTRACT_TEST"/, 'auto-removed contract test container is not verified absent');
});

test('failure handling also stops owned snapshot and cache verifier helpers', () => {
  const stopLoop = runner.match(/stop_owned_running_services_best_effort\(\) \{[\s\S]*?for requested in ([^\n]+); do/)?.[1] ?? '';

  assert.match(stopLoop, /"\$SNAPSHOT_BOOTSTRAP"/, 'failure stop omits the snapshot bootstrap helper');
  assert.match(stopLoop, /"\$CACHE_VERIFY"/, 'failure stop omits the cache verifier helper');
});

test('successful cleanup revalidates ownership once and removes immutable IDs only', () => {
  assert.match(runner, /cleanup_run_containers_and_networks\(\) \{[\s\S]{0,700}\{\{\.Id\}\}\|\{\{\.State\.Status\}\}\|\{\{index \.Config\.Labels/, 'cleanup does not combine identity and ownership checks');
  assert.match(runner, /docker rm "\$container_id"/, 'container cleanup does not use inspected immutable ID');
  assert.match(runner, /docker network rm "\$network_id"/, 'network cleanup does not use inspected immutable ID');
  assert.doesNotMatch(runner, /docker rm "\$requested"/, 'container cleanup removes by mutable name');
  assert.doesNotMatch(runner, /docker network rm "\$requested"/, 'network cleanup removes by mutable name');
  assert.doesNotMatch(runner, /docker (?:system|volume) prune|docker volume rm/, 'cleanup includes broad or volume deletion');
});

test('R50 runtime uses its separately pinned integrated source manifest with a fixed path allowlist', () => {
  assert.match(runtime, /INTEGRATED_SOURCE_MANIFEST = process\.env\.H3_C03_MANIFEST_PATH/);
  assert.match(runtime, /integrated source manifest path is outside the test allowlist/);
  assert.ok(runner.includes('--env H3_C03_MANIFEST_PATH=\"$MANIFEST\"'));
});
