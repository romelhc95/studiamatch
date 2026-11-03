import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { classifyFetchFailure, classifyHttpStatus, probePostgrest } from './h3req1_c03_postgrest_probe.mjs';

const runner = readFileSync(new URL('./h3req1_c03_integrated_drill_r5.sh', import.meta.url), 'utf8');

test('every Docker image run forbids implicit pulls', () => {
  const runLines = runner.split(/\r?\n/).filter((line) => /\bdocker run\b/.test(line));

  assert.ok(runLines.length >= 7, `expected at least seven image runs, got ${runLines.length}`);
  for (const line of runLines) {
    assert.match(line, /\bdocker run\b.*--pull=never\b/, 'a Docker image run lacks --pull=never');
  }
});

test('Docker operations stay on the attested endpoint after target verification', () => {
  assert.match(runner, /readonly DOCKER_BIN='\/usr\/bin\/docker'/, 'Docker CLI path is not fixed');
  assert.match(
    runner,
    /if \(\( DOCKER_TARGET_VERIFIED == 1 \)\); then\s+"\$DOCKER_BIN" --host "\$EXPECTED_DOCKER_HOST"/,
    'post-attestation Docker calls are not pinned to the verified endpoint',
  );
  assert.match(runner, /DOCKER_TARGET_VERIFIED=1\s+printf 'Docker target PASS:/, 'target verification is not recorded');
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

test('successful cleanup revalidates ownership once and removes immutable IDs only', () => {
  assert.match(runner, /cleanup_run_containers_and_networks\(\) \{[\s\S]{0,700}\{\{\.Id\}\}\|\{\{\.State\.Status\}\}\|\{\{index \.Config\.Labels/, 'cleanup does not combine identity and ownership checks');
  assert.match(runner, /docker rm "\$container_id"/, 'container cleanup does not use inspected immutable ID');
  assert.match(runner, /docker network rm "\$network_id"/, 'network cleanup does not use inspected immutable ID');
  assert.doesNotMatch(runner, /docker rm "\$requested"/, 'container cleanup removes by mutable name');
  assert.doesNotMatch(runner, /docker network rm "\$requested"/, 'network cleanup removes by mutable name');
  assert.doesNotMatch(runner, /docker (?:system|volume) prune|docker volume rm/, 'cleanup includes broad or volume deletion');
});
