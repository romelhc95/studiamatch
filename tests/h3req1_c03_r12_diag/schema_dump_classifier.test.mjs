import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import {
  classifyPostgrestPrerequisites,
  classifySchemaDump,
  extractExitMarker,
  CAPTURE_LIMIT_BYTES,
} from './schema_dump_classifier.mjs';

const exitMarker = (code, nonce = 'test-run') => `\n__H3_DUMP_EXIT_${nonce}=${code}\n`;
const classifierPath = fileURLToPath(new URL('./schema_dump_classifier.mjs', import.meta.url));

test('successful schema dump exposes only JSON category and bounded size class', () => {
  const output = Buffer.from('{"dbTables":[],"dbRoutines":[]}');
  assert.equal(
    classifySchemaDump(output, output.byteLength, 0),
    'phase=postgrest-schema-dump|error_code=SCHEMA_JSON exit=0 bytes=LE_8192',
  );
});

test('PGRST code is extracted without carrying message or DSN text', () => {
  const output = Buffer.from('{"code":"PGRST002","message":"password=never-print"}');
  const result = classifySchemaDump(output, output.byteLength, 1);
  assert.equal(result, 'phase=postgrest-schema-dump|error_code=POSTGREST_PGRST002 exit=1 bytes=LE_8192');
  assert.doesNotMatch(result, /password|never-print|message/);
});

test('SQLSTATE is extracted from structured output only', () => {
  const output = Buffer.from('database error {"code":"42501","message":"private detail"}');
  assert.equal(
    classifySchemaDump(output, output.byteLength, 1),
    'phase=postgrest-schema-dump|error_code=SQLSTATE_42501 exit=1 bytes=LE_8192',
  );
});

test('generic schema cache failure is closed without exposing raw output', () => {
  const output = Buffer.from('Could not query the database for the schema cache. secret text');
  assert.equal(
    classifySchemaDump(output, output.byteLength, 1),
    'phase=postgrest-schema-dump|error_code=SCHEMA_CACHE_QUERY_FAILED exit=1 bytes=LE_8192',
  );
});

test('ordinary words are not misreported as SQLSTATE codes', () => {
  const output = Buffer.from('ERROR FATAL ERROR');
  assert.equal(
    classifySchemaDump(output, output.byteLength, 1),
    'phase=postgrest-schema-dump|error_code=EXIT_NONZERO_UNCLASSIFIED exit=1 bytes=LE_8192',
  );
});

test('timeout and Docker launch errors have fixed closed codes', () => {
  assert.match(classifySchemaDump(Buffer.alloc(0), 0, 124), /error_code=TIMEOUT_OR_SIGNAL exit=124/);
  assert.match(classifySchemaDump(Buffer.alloc(0), 0, 137), /error_code=PROCESS_KILLED exit=137/);
  assert.match(classifySchemaDump(Buffer.from('raw'), 3, 125), /error_code=CONTAINER_LAUNCH_FAILED exit=125/);
});

test('invalid UTF-8 is classified with the same bounded size metadata', () => {
  assert.equal(
    classifySchemaDump(Buffer.from([0xff]), 1, 1),
    'phase=postgrest-schema-dump|error_code=OUTPUT_ENCODING_INVALID exit=1 bytes=LE_8192',
  );
});

test('output truncation retains a safe code from the bounded tail', () => {
  const first = Buffer.alloc(CAPTURE_LIMIT_BYTES, 0x78);
  const tail = Buffer.from('{"code":"PGRST002","message":"must not be echoed"}');
  const marker = Buffer.from(exitMarker(1));
  const retained = Buffer.concat([first, tail, marker]);
  const parsedMarker = extractExitMarker(retained, 'test-run');
  assert.deepEqual(parsedMarker, { exitCode: 1, markerBytes: marker.byteLength });
  assert.equal(
    classifySchemaDump(
      retained.subarray(0, retained.byteLength - parsedMarker.markerBytes),
      retained.byteLength + 100_000 - parsedMarker.markerBytes,
      parsedMarker.exitCode,
    ),
    'phase=postgrest-schema-dump|error_code=POSTGREST_PGRST002 exit=1 bytes=GT_131072',
  );
});

test('capture accounting and nonce-mismatched exit marker fail closed', () => {
  assert.equal(classifySchemaDump(Buffer.from('{}'), 1, 0), 'phase=postgrest-schema-dump|error_code=CAPTURE_INVALID');
  const mismatch = Buffer.from(`{}${exitMarker(1, 'different-run')}`);
  assert.equal(extractExitMarker(mismatch, 'test-run'), null);
});

test('stdin adapter emits only the safe classification and hides raw error details', () => {
  const raw = Buffer.from(`{"code":"PGRST002","message":"password=synthetic-only"}${exitMarker(1)}`);
  const result = spawnSync(process.execPath, [classifierPath, 'test-run'], { input: raw, encoding: 'utf8' });
  assert.equal(result.status, 0);
  assert.equal(result.stderr, '');
  assert.equal(result.stdout, 'phase=postgrest-schema-dump|error_code=POSTGREST_PGRST002 exit=1 bytes=LE_8192\n');
  assert.doesNotMatch(result.stdout, /password|synthetic-only|message/);
});

test('stdin adapter rejects a missing matching nonce without echoing input', () => {
  const raw = Buffer.from(`private-output${exitMarker(1, 'other-run')}`);
  const result = spawnSync(process.execPath, [classifierPath, 'test-run'], { input: raw, encoding: 'utf8' });
  assert.equal(result.status, 0);
  assert.equal(result.stderr, '');
  assert.equal(result.stdout, 'phase=postgrest-schema-dump|error_code=EXIT_MARKER_MISSING\n');
  assert.doesNotMatch(result.stdout, /private-output|other-run/);
});

test('all outputs obey a fixed phase/code schema', () => {
  const cases = [
    [Buffer.from('{}'), 0],
    [Buffer.from('{"code":"PGRST002"}'), 1],
    [Buffer.from('{"code":"42501"}'), 1],
    [Buffer.from('opaque'), 1],
    [Buffer.alloc(0), 124],
    [Buffer.alloc(0), 137],
  ];
  for (const [input, exitCode] of cases) {
    assert.match(classifySchemaDump(input, input.byteLength, exitCode), /^phase=postgrest-schema-dump\|error_code=[A-Z0-9_]+(?:_[A-Z0-9]+)* exit=[0-9]+ bytes=(?:LE_8192|LE_131072|GT_131072)$/);
  }
});

test('PostgREST schema prerequisites are classified without exposing raw values', () => {
  const cases = [
    ['t|t|t', 'ALL_PRESENT'],
    ['f|t|t', 'PUBLIC_SCHEMA_ABSENT'],
    ['t|f|t', 'EXTENSIONS_SCHEMA_ABSENT'],
    ['t|t|f', 'PRE_REQUEST_FUNCTION_ABSENT'],
    ['t|f|f', 'EXTENSIONS_AND_PRE_REQUEST_ABSENT'],
    ['f|f|t', 'PUBLIC_SCHEMA_ABSENT'],
    ['f|t|f', 'PUBLIC_SCHEMA_ABSENT'],
    ['f|f|f', 'PUBLIC_SCHEMA_ABSENT'],
  ];
  for (const [input, code] of cases) {
    assert.equal(
      classifyPostgrestPrerequisites(`${input}\n`),
      `phase=postgres-postgrest-prerequisites|error_code=${code}`,
    );
  }
  for (const input of ['t|t|t\n\n', 'secret-value', 't|t|t|x', null]) {
    const result = classifyPostgrestPrerequisites(input);
    assert.equal(result, 'phase=postgres-postgrest-prerequisites|error_code=OUTPUT_REJECTED');
    assert.doesNotMatch(result, /secret-value/);
  }
});

test('cleanup Go templates use valid label quoting and exact label maps', () => {
  const runnerPath = process.env.H3_R12_RUNNER_PATH;
  assert.ok(runnerPath, 'runner contract mount is required');
  const runner = readFileSync(runnerPath, 'utf8');
  const start = runner.indexOf('cleanup_completed() {');
  const end = runner.indexOf('\nrun_schema_dump() {', start);
  assert.ok(start >= 0 && end > start, 'cleanup function boundaries are present');
  const cleanup = runner.slice(start, end);
  assert.doesNotMatch(cleanup, /\\+"/, 'Go-template map keys must not be backslash-escaped');
  assert.ok(cleanup.includes('{{index .Config.Labels "com.studiamatch.h3.c03.jit"}}'));
  assert.ok(cleanup.includes('{{index .Labels "com.studiamatch.h3.c03.jit"}}'));
  assert.ok(cleanup.includes('{{index .Config.Labels "com.studiamatch.h3.c03.run"}}'));
  assert.ok(cleanup.includes('{{index .Labels "com.studiamatch.h3.c03.run"}}'));
  assert.ok(runner.includes("to_regnamespace('extensions')"));
  assert.ok(runner.includes("to_regprocedure('public.h3_admin_rpc_signed_gateway_pre_request()')"));
});

test('prerequisite stdin adapter emits only a fixed code and rejects invalid bytes', () => {
  const result = spawnSync(
    process.execPath,
    [classifierPath, '--classify-prerequisites'],
    { input: 't|f|t\n', encoding: 'utf8' },
  );
  assert.equal(result.status, 0);
  assert.equal(result.stderr, '');
  assert.equal(
    result.stdout,
    'phase=postgres-postgrest-prerequisites|error_code=EXTENSIONS_SCHEMA_ABSENT\n',
  );
  assert.doesNotMatch(result.stdout, /t\|f\|t/);

  const invalid = spawnSync(
    process.execPath,
    [classifierPath, '--classify-prerequisites'],
    { input: Buffer.from([0xf4, 0x7c, 0x74, 0x7c, 0x74]), encoding: 'utf8' },
  );
  assert.equal(invalid.status, 0);
  assert.equal(invalid.stdout, 'phase=postgres-postgrest-prerequisites|error_code=OUTPUT_REJECTED\n');
});
