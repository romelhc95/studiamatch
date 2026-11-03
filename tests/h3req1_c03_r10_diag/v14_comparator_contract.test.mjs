import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const runnerPath = new URL('../h3req1_c03_integrated_diagnostic_r11_v14_comparator.sh', import.meta.url);
const drillPath = new URL('../h3req1_c03_integrated_drill_r9.sh', import.meta.url);
const manifestPath = new URL('./inputs_v14.sha256', import.meta.url);
const runner = readFileSync(runnerPath, 'utf8');
const drill = readFileSync(drillPath, 'utf8');
const manifest = readFileSync(manifestPath, 'utf8');

test('comparator pins the official PostgREST v14.0 digest and checks its executable version', () => {
  assert.match(runner,
    /readonly POSTGREST_IMAGE='postgrest\/postgrest@sha256:f8176256ad55a794a61ee6d76d00121635fac4d63bb3d51594e5ed6790f91c72'/);
  assert.match(runner,
    /postgrest_version="\$\(bounded_docker 15 run --pull=never --platform linux\/amd64 --rm --network none/);
  assert.match(runner, /\[\[ "\$postgrest_version" == 'PostgREST 14\.0' \]\]/);
  assert.match(runner, /r11-diagnostic-inputs=8\/8 PASS/);
  assert.match(manifest,
    /^[a-f0-9]{64}  tests\/h3req1_c03_r10_diag\/v14_comparator_contract\.test\.mjs$/m);
});

test('comparator uses unique isolated resources and a distinct evidence file', () => {
  assert.match(runner, /readonly JIT='H3-CLOSE-03-DIAGNOSTIC-R11-V14-COMPARATOR'/);
  assert.match(runner, /readonly DATA_NETWORK='h3req1-c03-diagnostic-data-20261010-r11-v14'/);
  assert.match(runner, /readonly PG='h3req1-c03-diagnostic-pg17-20261010-r11-v14'/);
  assert.match(runner, /readonly POSTGREST='h3req1-c03-diagnostic-postgrest-20261010-r11-v14'/);
  assert.match(runner, /readonly RESULT_FILE='\.context\/evidencia\/h3req1_c03_integrated_diagnostic_r11_v14\.txt'/);
  assert.match(runner, /raw_logs_persisted=false edge_started=false/);
});

test('the candidate runtime remains pinned to PostgREST 13.0.7', () => {
  assert.match(drill,
    /readonly POSTGREST_IMAGE='postgrest\/postgrest@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228'/);
});

test('PostgREST logs are filtered through the bounded classifier and never echoed raw', () => {
  assert.match(runner, /bounded_docker 30 logs --tail 64/);
  assert.match(runner, /node "\/diag\/postgres_log_classifier\.mjs" "\$kind"/);
  assert.match(runner, /error_code=\(SQLSTATE_\[A-Z0-9\]\{5\}\|POSTGREST_CODE_PGRST/);
  assert.doesNotMatch(runner, /printf[^\n]*(?:docker logs|\$raw|\$log_output)/);
});
