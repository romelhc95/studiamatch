import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const runnerPath = process.env.H3_R10_RUNNER_PATH
  ?? new URL('../h3req1_c03_integrated_diagnostic_r10.sh', import.meta.url);
const runner = readFileSync(runnerPath, 'utf8');
const snapshotVerifier = readFileSync(new URL('./source_snapshot_verifier.mjs', import.meta.url), 'utf8');

test('R10 is pinned to the R9 source snapshot and the local Docker Desktop target', () => {
  assert.ok(runner.includes("EXPECTED_DOCKER_HOST='unix:///var/run/docker.sock'"));
  assert.ok(runner.includes("EXPECTED_DOCKER_ID='fc2115b2-c3c4-440e-89c6-26899eb7cb04'"));
  assert.ok(runner.includes("SOURCE_SNAPSHOT='h3req1-c03-integrated-source-snapshot-20261010-r9'"));
  assert.ok(runner.includes("R9_MANIFEST_SHA256='6b0a469325b466a59211b3f6e50f16bce49910d78cad994068daa51caba13de9'"));
  assert.ok(runner.includes("R10_INPUTS='tests/h3req1_c03_r10_diag/inputs.sha256'"));
  assert.ok(runner.includes("R10_INPUTS_SHA256='19271aac83e46f84c36d608956d2ff84e1d8ecf7706edb909f09f3a9f8c122a0'"));
  assert.ok(runner.includes("RESULT_FILE='.context/evidencia/h3req1_c03_integrated_diagnostic_r10_v5.txt'"));
  assert.ok(runner.includes('sha256sum "$R10_INPUTS" | cut -d\' \' -f1)" == "$R10_INPUTS_SHA256"'));
  assert.ok(runner.includes('sha256sum -c "$R10_INPUTS"'));
  assert.ok(runner.includes('SNAPSHOT_NONCANDIDATE_PATHS'));
  assert.ok(runner.includes('/diag/source_snapshot_verifier.mjs'));
  assert.ok(runner.includes('source "$CLASSIFIER_DIR/postgres_version_classifier.sh"'));
  assert.ok(runner.includes('h3req1_is_postgres_17_11 "$pg_version"'));
  assert.ok(runner.includes('POSTGREST_CODE_PGRST[0-9]{3}'));
  assert.ok(runner.includes('STRUCTURED_POSTGREST_CODE_PGRST[0-9]{3}'));
  assert.equal(runner.includes("[[ \"$pg_version\" == 'postgres (PostgreSQL) 17.11' ]]"), false);
  assert.ok(snapshotVerifier.includes("path: 'supabase/functions/admin-invite/deno.json'"));
  assert.ok(snapshotVerifier.includes("sha256: '5335690600914ad53e9b4873a8287e0baba01902ef94eec02d01b35ca6d7b3be'"));
  assert.ok(snapshotVerifier.includes("path: 'supabase/functions/admin-invite/deno.lock'"));
  assert.ok(snapshotVerifier.includes("sha256: 'ccb3d17f01947e679fb530ba7cbc9d252263ab1051d1d9ab21429eecde7ba428'"));
  assert.equal(readFileSync(new URL('./inputs.sha256', import.meta.url), 'utf8').includes('integrated_diagnostic_contract.test.mjs'), false);
  assert.ok(readFileSync(new URL('./inputs.sha256', import.meta.url), 'utf8').includes('postgres_version_classifier.sh'));
  assert.ok(readFileSync(new URL('./inputs.sha256', import.meta.url), 'utf8').includes('postgres_version_classifier.test.sh'));
});

test('R10 bounds JSON log retention and uses only the internal data network', () => {
  assert.equal((runner.match(/--log-driver=json-file/g) ?? []).length, 2);
  assert.equal((runner.match(/--log-opt max-size=1m --log-opt max-file=1/g) ?? []).length, 2);
  assert.ok(runner.includes('docker network create --internal'));
  assert.ok(runner.includes('--network "$DATA_NETWORK"'));
  assert.equal(/--network (?:bridge|host)|docker pull|docker compose/.test(runner), false);
});

test('PostgreSQL logs expose only SQLSTATE prefixes and are never printed raw', () => {
  assert.ok(runner.includes('log_line_prefix=SQLSTATE=%e'));
  assert.ok(runner.includes('logs --tail 64'));
  assert.ok(runner.includes('node "/diag/postgres_log_classifier.mjs" "$kind"'));
  assert.equal(/printf[^\n]*(?:docker logs|\$raw|\$log_output)/.test(runner), false);
});

test('the diagnostic probes TCP auth and does not start Edge or access operational env files', () => {
  assert.ok(runner.includes('PGCONNECT_TIMEOUT=3'));
  assert.ok(runner.includes('PGPASSWORD=$PG_PASSWORD'));
  assert.ok(runner.includes('PGRST_DB_URI='));
  assert.equal(/start_edge|\.env\.local|\.env\.gitprod|NEXT_SUPABASE_SECRET_KEY/.test(runner), false);
});
