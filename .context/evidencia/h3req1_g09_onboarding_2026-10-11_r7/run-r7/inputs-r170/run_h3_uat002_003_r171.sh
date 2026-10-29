#!/usr/bin/env bash
set -Eeuo pipefail

readonly APP='h3req1-g09-onboarding-app-20261011-r8'
readonly APP_ID='9921c96524bf6b97e567248a77198651caf1199b143d9af1ed2327b6032fab07'
readonly APP_IMAGE='sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63'
readonly APP_STATE="$(docker inspect -f '{{.Id}}|{{.Image}}|{{.State.Status}}' "$APP" 2>/dev/null)"
[[ "$APP_STATE" == "$APP_ID|$APP_IMAGE|running" ]] || {
  printf 'phase=container-preflight|error_code=PIN_OR_STATE_MISMATCH\n'
  exit 2
}

docker exec -i "$APP_ID" /bin/bash -s <<'CONTAINER'
set -Eeuo pipefail
readonly APP_ROOT='/app'
readonly HELPER='/evidence/onboarding-r146/runtime-helper/h3_local_runtime_server_r146_uat072.mjs'
readonly STATIC_ROOT='/evidence/onboarding-r146/normal-public-r146'
readonly OUTPUT='/evidence/uat-auth-email-fallback-r171'
readonly RAW='/tmp/h3req1-uat-email-fallback-r171-raw.log'
readonly RUNTIME_LOG='/tmp/h3req1-uat-email-fallback-r171-runtime.log'

[[ ! -e "$OUTPUT" ]] || { printf 'phase=preflight|error_code=EVIDENCE_TARGET_EXISTS\n'; exit 2; }
[[ -s "$HELPER" && -d "$STATIC_ROOT" && -s "$APP_ROOT/tests/h3_local_uat.mjs" ]] || {
  printf 'phase=preflight|error_code=R146_OR_RUNNER_INPUT_MISSING\n'
  exit 2
}
node --check "$APP_ROOT/tests/h3_local_uat.mjs" >/dev/null 2>&1 || {
  printf 'phase=runner-syntax|error_code=CHECK_FAILED\n'
  exit 2
}
node --check "$HELPER" >/dev/null 2>&1 || {
  printf 'phase=runtime-syntax|error_code=CHECK_FAILED\n'
  exit 2
}
node --input-type=module <<'NODE'
import net from 'node:net';
for (const port of [3380, 3381, 3383]) {
  await new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(port, '127.0.0.1', () => server.close(resolve));
  });
}
NODE
printf 'phase=preflight|error_code=PASS|runner=H3-UAT-002,003|ports=3380,3381,3383\n'

export H3_RUNTIME_ROOT="$APP_ROOT"
export H3_QUOTA_TOOLS='/tmp/h3-quota-runtime-tools'
export H3_RUNTIME_BIND_HOST='127.0.0.1'
export H3_RUNTIME_PORT_BASE='3380'
export H3_STATIC_ROOT="$STATIC_ROOT"
node "$HELPER" >"$RUNTIME_LOG" 2>&1 &
readonly HELPER_PID=$!
cleanup() {
  local status=$?
  trap - EXIT
  kill "$HELPER_PID" 2>/dev/null || true
  wait "$HELPER_PID" 2>/dev/null || true
  rm -f -- "$RAW" "$RUNTIME_LOG"
  exit "$status"
}
trap cleanup EXIT

if ! node --input-type=module <<'NODE'
const end = Date.now() + 15000;
while (Date.now() < end) {
  try {
    const response = await fetch('http://localhost:3380/admin/login/');
    if (response.status === 200) process.exit(0);
  } catch {}
  await new Promise((resolve) => setTimeout(resolve, 200));
}
process.exit(1);
NODE
then
  printf 'phase=pages-workerd-readiness|error_code=HEALTH_NOT_READY\n'
  exit 1
fi
printf 'phase=pages-workerd-readiness|error_code=PASS|runtime=R146|ports=3380,3381,3383|bind=127.0.0.1\n'

set +e
H3_BASE_URL='http://localhost:3380' \
H3_MOCK_URL='http://localhost:3381' \
H3_PERIMETER_URL='http://localhost:3383' \
H3_REPO_ROOT="$APP_ROOT" \
H3_UAT_CASES='H3-UAT-002,H3-UAT-003' \
H3_QUOTA_TEST_ISOLATION='true' \
H3_EVIDENCE_DIR="$OUTPUT" \
/usr/bin/timeout --foreground --signal=TERM --kill-after=10s 240s \
  node "$APP_ROOT/tests/h3_local_uat.mjs" >"$RAW" 2>&1
readonly RUN_EXIT=$?
set -e

node - "$RUN_EXIT" "$RAW" "$OUTPUT/runner-summary.json" <<'NODE'
import fs from 'node:fs';
const exit = Number(process.argv[2]);
const rawPath = process.argv[3];
const summaryPath = process.argv[4];
let parsed;
try {
  parsed = JSON.parse(fs.readFileSync(rawPath, 'utf8').trim().split(/\r?\n/).filter(Boolean).at(-1));
} catch {}
const valid = parsed && ['PASS', 'FAIL'].includes(parsed.result)
  && Number.isInteger(parsed.logicalCasesPassed)
  && Number.isInteger(parsed.viewportExecutionsPassed)
  && Number.isInteger(parsed.screenshots) && parsed.retries === 0;
const summary = valid ? {
  result: parsed.result,
  exit,
  logicalCases: parsed.logicalCases,
  logicalCasesPassed: parsed.logicalCasesPassed,
  viewportExecutions: parsed.viewportExecutions,
  viewportExecutionsPassed: parsed.viewportExecutionsPassed,
  screenshots: parsed.screenshots,
  retries: parsed.retries,
  server: 'Pages/workerd normal R146, ports 3380/3381/3383, loopback only',
  browser: 'Playwright Chromium 1228 headless',
  data: 'synthetic Auth/PostgREST and PostgreSQL 17.11 fixture',
} : { result: 'FAIL', exit, error_code: 'SUMMARY_MISSING_OR_INVALID', retries: 0 };
fs.writeFileSync(summaryPath, `${JSON.stringify(summary, null, 2)}\n`);
process.stdout.write(`phase=uat-email-fallback-r171|exit=${exit}|result=${summary.result}|cases=${summary.logicalCasesPassed ?? 0}/2|viewports=${summary.viewportExecutionsPassed ?? 0}/6|screenshots=${summary.screenshots ?? 0}|retries=0\n`);
if (exit !== 0 || summary.result !== 'PASS' || summary.logicalCases !== 2 || summary.logicalCasesPassed !== 2
  || summary.viewportExecutions !== 6 || summary.viewportExecutionsPassed !== 6 || summary.screenshots !== 6) process.exitCode = 1;
NODE
CONTAINER
