import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { classifyFetchFailure, classifyHttpStatus, probePostgrest } from './h3req1_c03_postgrest_probe.mjs';
import { classifyLoginResult, isLoginFailureCode } from './h3req1_c03_login_result.mjs';

const runner = readFileSync(new URL('./h3req1_c03_integrated_drill_r13.sh', import.meta.url), 'utf8');
const runtime = readFileSync(new URL('./h3req1_c03_integrated_runtime.mjs', import.meta.url), 'utf8');
const probe = readFileSync(new URL('./h3req1_c03_postgrest_probe.mjs', import.meta.url), 'utf8');
const extensionSetup = readFileSync(new URL('./sql/h3req1_c03_integrated_extension_setup_r13.sql', import.meta.url), 'utf8');

test('integrated runner uses the manifest path consumed by the runtime', () => {
  assert.match(runner, /readonly MANIFEST='tests\/h3req1-c03-integrated\.sha256'/,
    'runner manifest path differs from the integrated runtime contract');
  assert.match(runtime, /: 'tests\/h3req1-c03-integrated\.sha256'\)/,
    'integrated runtime manifest path changed unexpectedly');
});

test('integrated fixture provides the configured PostgREST extra search path schema', () => {
  assert.match(runner, /PGRST_DB_EXTRA_SEARCH_PATH=public,extensions/,
    'PostgREST extra search path changed without updating the disposable fixture');
  assert.match(extensionSetup,
    /CREATE SCHEMA IF NOT EXISTS extensions AUTHORIZATION postgres;/,
    'fresh PG17 fixture omits the extensions schema required by the configured search path');
});

test('login diagnostics classify each strict acceptance predicate without exposing values', () => {
  const passing = { status: 200, aal: 'aal2', authCookie: true, activityCookie: true };
  assert.equal(classifyLoginResult(passing), null);
  assert.equal(classifyLoginResult({ ...passing, status: 401 }), 'LOGIN_HTTP_STATUS_401');
  assert.equal(classifyLoginResult({ ...passing, status: 503 }), 'LOGIN_HTTP_STATUS_503');
  assert.equal(classifyLoginResult({ ...passing, status: 'private body' }), 'LOGIN_HTTP_STATUS_INVALID');
  assert.equal(classifyLoginResult({ ...passing, status: 600 }), 'LOGIN_HTTP_STATUS_INVALID');
  assert.equal(classifyLoginResult({ ...passing, aal: 'aal1' }), 'LOGIN_AAL_NOT_AAL2');
  assert.equal(classifyLoginResult({ ...passing, authCookie: false }), 'LOGIN_AUTH_COOKIE_MISSING');
  assert.equal(classifyLoginResult({ ...passing, activityCookie: false }), 'LOGIN_ACTIVITY_COOKIE_MISSING');
  assert.deepEqual([
    'LOGIN_HTTP_STATUS_401',
    'LOGIN_HTTP_STATUS_503',
    'LOGIN_AAL_NOT_AAL2',
    'LOGIN_AUTH_COOKIE_MISSING',
    'LOGIN_ACTIVITY_COOKIE_MISSING',
  ].map(isLoginFailureCode), [true, true, true, true, true]);
  assert.equal(isLoginFailureCode('private response body'), false);
  assert.equal(classifyLoginResult({ status: 200, aal: 'private email', authCookie: true, activityCookie: true }),
    'LOGIN_AAL_NOT_AAL2');
});

test('runtime emits only an allowlisted login check code on classified failure', () => {
  assert.match(runtime, /classifyLoginResult\(\{[\s\S]{0,240}activityCookie:[\s\S]{0,160}\}\)/,
    'runtime does not classify the complete login contract');
  assert.match(runtime, /error instanceof IntegratedCheckFailure && isLoginFailureCode\(error\.code\)/,
    'failure response does not validate diagnostic codes against the closed allowlist');
  assert.doesNotMatch(runtime, /error\.message|payload\.(?:message|details|hint)/,
    'runtime exposes untrusted error or response details');
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
