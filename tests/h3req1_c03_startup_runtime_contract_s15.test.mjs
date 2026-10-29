import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { pagesWorkerRootProbe } from './h3req1_c03_startup_healthz_probe.mjs';

const runtime = readFileSync(process.env.H3_TEST_RUNTIME_SOURCE, 'utf8');
const runner = readFileSync(process.env.H3_TEST_RUNNER_SOURCE, 'utf8');
const startupHealthHandler = runtime.match(
  /async function handleStartupSmokeControl\([\s\S]*?(?=\nfunction handleStartupSmokeGateway)/,
)?.[0];
const startupDependencyCheck = runtime.match(
  /if \(startupOnly\) \{([\s\S]*?)\n  \} else \{/,
)?.[1];

const cases = [
  ['healthz-dispatches-pages-worker', () => {
    assert.ok(startupHealthHandler);
    assert.match(startupHealthHandler, /pagesWorkerRootProbe\(\s*\(\)\s*=>\s*pagesRequest\(pagesActive,\s*'\/'/);
    assert.doesNotMatch(startupHealthHandler, /workerd:\s*Boolean\(pagesActive\s*&&\s*pagesSuspended\)/);
    assert.match(startupHealthHandler, /startupGatewayRequests\s*===\s*0/);
    assert.match(startupHealthHandler, /assetRequests\s*===\s*1/);
  }],
  ['startup-dependency-content-digests', () => {
    assert.ok(startupDependencyCheck);
    assert.match(startupDependencyCheck, /digestDirectories\(/);
    assert.match(startupDependencyCheck, /H3_C03_EXPECTED_DEPENDENCY_DIGESTS/);
    assert.match(startupDependencyCheck, /assert\.deepEqual\(actualDependencyDigests, expectedDependencyDigests/);
  }],
  ['physical-evidence-path-parents', () => {
    assert.match(runner, /realpath -e -- "\$ROOT\/\.context"/);
    assert.match(runner, /realpath -e -- "\$ROOT\/\.context\/evidencia"/);
    assert.match(runner, /! -L "\$ROOT\/\.context"/);
    assert.match(runner, /! -L "\$ROOT\/\.context\/evidencia"/);
  }],
  ['source-volume-options-and-attachments-are-exact', () => {
    const volumeCheck = runner.match(/verify_source_volume_ownership\(\) \{([\s\S]*?)\n\}/)?.[1];
    assert.ok(volumeCheck);
    assert.match(volumeCheck, /\{\{json \.Options\}\}/);
    assert.match(volumeCheck, /\$SOURCE_VOL\|local\|null\|\$SNAPSHOT_JIT\|\$SNAPSHOT_MANIFEST\|\$SNAPSHOT_RUN/);
    assert.match(volumeCheck, /ps -a --no-trunc --filter "volume=\$SOURCE_VOL"/);
    assert.match(volumeCheck, /\$SNAPSHOT_ID\|\$SNAPSHOT/);
    assert.match(volumeCheck, /\$OLD_RUNTIME_ID\|\$OLD_RUNTIME/);
    assert.match(volumeCheck, /LC_ALL=C sort/);
    assert.match(volumeCheck, /\[\[ "\$\(printf '%s\\n' "\$attachments" \| LC_ALL=C sort\)" == "\$expected_attachments" \]\]/);
    assert.ok(runner.includes("old_mounts\" == 'volume|/candidate|false;bind|/diag-preload.cjs|false;bind|/probe.mjs|false;volume|/tools|false;volume|/web-deps|false;'"));
    assert.equal((runner.match(/verify_source_volume_ownership \|\| fail/g) || []).length, 1);
    assert.match(runner, /verify_source_volume_ownership \|\| \{ printf 'phase=source-volume-recheck/);
  }],
  ['worker-root-fixture-passes', async () => {
    let calls = 0;
    const result = await pagesWorkerRootProbe(async () => {
      calls += 1;
      return new Response('C03 synthetic public asset /', { status: 200 });
    });
    assert.equal(calls, 1);
    assert.deepEqual(result, { ready: true, status: 200, assetMatches: true });
  }],
  ['wrong-status-or-body-fails-closed', async () => {
    const status = await pagesWorkerRootProbe(async () => new Response('C03 synthetic public asset /', { status: 503 }));
    const body = await pagesWorkerRootProbe(async () => new Response('different synthetic asset', { status: 200 }));
    assert.equal(status.ready, false);
    assert.equal(body.ready, false);
  }],
  ['worker-fetch-error-fails-closed', async () => {
    const result = await pagesWorkerRootProbe(async () => { throw new Error('synthetic-only'); });
    assert.deepEqual(result, { ready: false, status: 0, assetMatches: false });
  }],
];

let failedCase = '';
for (const [name, run] of cases) {
  try {
    await run();
  } catch {
    failedCase = name;
    break;
  }
}

if (failedCase) {
  process.stdout.write(`phase=s15-runtime-contract|error_code=FAIL|case=${failedCase}\n`);
  process.exitCode = 1;
} else {
  process.stdout.write(`phase=s15-runtime-contract|error_code=PASS|cases=${cases.length}\n`);
}
