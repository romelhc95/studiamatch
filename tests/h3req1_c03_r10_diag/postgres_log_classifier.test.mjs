import assert from 'node:assert/strict';
import test from 'node:test';
import {
  classifyPostgresLog,
  classifyPostgrestLog,
  LOG_INPUT_LIMIT_BYTES,
} from './postgres_log_classifier.mjs';

test('extracts only the SQLSTATE from a PostgreSQL prefix', () => {
  const raw = Buffer.from('SQLSTATE=42501 ERROR private relation and query text');
  const result = classifyPostgresLog(raw);
  assert.equal(result, 'phase=postgres-log|error_code=SQLSTATE_42501');
  assert.equal(result.includes('private'), false);
  assert.equal(result.includes('query'), false);
});

test('returns the latest structured PostgreSQL SQLSTATE', () => {
  const raw = Buffer.from('SQLSTATE=08006 ERROR connection\nSQLSTATE=28P01 ERROR auth');
  assert.equal(classifyPostgresLog(raw), 'phase=postgres-log|error_code=SQLSTATE_28P01');
});

test('does not treat arbitrary text or a PostgREST code as a SQLSTATE', () => {
  const raw = Buffer.from('PGRST002 Could not query schema cache; private text');
  assert.equal(classifyPostgresLog(raw), 'phase=postgres-log|error_code=NO_SCHEMA_CACHE_SQLSTATE');
});

test('extracts a SQLSTATE only from a schema-cache JSON record', () => {
  const raw = Buffer.from('2026-10-10: Failed to load the schema cache: {"code":"42501","message":"private"}');
  const result = classifyPostgrestLog(raw);
  assert.equal(result, 'phase=postgrest-log|error_code=SQLSTATE_42501');
  assert.equal(result.includes('private'), false);
});

test('classifies the PostgREST 13 schema-cache log marker and keeps only an allowlisted code', () => {
  const raw = Buffer.from('2026-10-10: Schema Cache load error: {"code":"42501","message":"private"}');
  const result = classifyPostgrestLog(raw);
  assert.equal(result, 'phase=postgrest-log|error_code=SQLSTATE_42501');
  assert.equal(result.includes('private'), false);
});

test('classifies the observed PostgREST 13 failed-load record without retaining its message', () => {
  const raw = Buffer.from(
    '2026-10-10: Failed to load the schema cache using db-schemas=public. {"code":"XX000","details":"private","message":"private"}',
  );
  const result = classifyPostgrestLog(raw);
  assert.equal(result, 'phase=postgrest-log|error_code=SQLSTATE_XX000');
  assert.equal(result.includes('private'), false);
});

test('classifies schema-cache PostgREST codes without exposing the message', () => {
  assert.equal(classifyPostgrestLog(Buffer.from(
    '2026-10-10: Could not query the database for the schema cache. {"code":"PGRST002","message":"private"}',
  )), 'phase=postgrest-log|error_code=POSTGREST_CODE_PGRST002');
});

test('extracts a closed SQLSTATE from a structured record without requiring a marker', () => {
  const result = classifyPostgrestLog(Buffer.from('runtime record {"code":"42501","detail":"private"}'));
  assert.equal(result, 'phase=postgrest-log|error_code=STRUCTURED_SQLSTATE_42501');
  assert.equal(result.includes('private'), false);
});

test('keeps only allowlisted codes from structured logs and rejects malformed schema-cache records', () => {
  assert.equal(classifyPostgrestLog(Buffer.from('GET / 503 {"code":"PGRST002"}')),
    'phase=postgrest-log|error_code=STRUCTURED_POSTGREST_CODE_PGRST002');
  assert.equal(classifyPostgrestLog(Buffer.from('Failed to load the schema cache: {not-json private}')),
    'phase=postgrest-log|error_code=SCHEMA_CACHE_CODE_NOT_EXPOSED');
});

test('distinguishes empty, plain-text, and JSON-without-code logs using closed codes', () => {
  assert.equal(classifyPostgrestLog(Buffer.alloc(0)), 'phase=postgrest-log|error_code=LOG_EMPTY');
  assert.equal(classifyPostgrestLog(Buffer.from('startup complete private')),
    'phase=postgrest-log|error_code=NO_JSON_RECORD');
  assert.equal(classifyPostgrestLog(Buffer.from('{"level":"info","message":"private"}')),
    'phase=postgrest-log|error_code=JSON_CODE_NOT_EXPOSED');
});

test('rejects oversized or invalid UTF-8 log input with closed codes', () => {
  assert.equal(classifyPostgresLog(Buffer.alloc(LOG_INPUT_LIMIT_BYTES + 1, 0x41)),
    'phase=postgres-log|error_code=LOG_INPUT_LIMIT');
  assert.equal(classifyPostgrestLog(Buffer.from([0xc3, 0x28])),
    'phase=postgrest-log|error_code=LOG_ENCODING_INVALID');
});
