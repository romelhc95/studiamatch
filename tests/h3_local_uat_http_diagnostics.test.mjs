import assert from 'node:assert/strict';
import test from 'node:test';
import { findUncorrelatedConsoleResourceFailures, isExpectedHttpFailure } from './h3_uat_http_diagnostics.mjs';

const logoutCase = { title: 'logout clears the HttpOnly session' };
const allowlist = {
  [logoutCase.title]: [{ status: 401, method: 'POST', origin: 'local-0', path: '/api/admin/rpc', afterLogout: true }],
};
const expectedPost = {
  status: 401,
  method: 'POST',
  origin: 'local-0',
  path: '/api/admin/rpc',
  beforeLogoutRequest: false,
  afterLogoutResponse: true,
};

test('expected HTTP failures require exact method, origin, path and status', () => {
  assert.equal(isExpectedHttpFailure(logoutCase, expectedPost, allowlist), true);
  assert.equal(isExpectedHttpFailure(logoutCase, { ...expectedPost, method: 'GET' }, allowlist), false);
  assert.equal(isExpectedHttpFailure(logoutCase, { ...expectedPost, origin: 'external' }, allowlist), false);
  assert.equal(isExpectedHttpFailure(logoutCase, { ...expectedPost, path: '/api/admin/session' }, allowlist), false);
  assert.equal(isExpectedHttpFailure(logoutCase, { ...expectedPost, afterLogoutResponse: false }, allowlist), false);
});

test('console resource messages require a unique method-aware response match', () => {
  const failure = { status: 401, origin: 'local-0', path: '/api/admin/rpc', observedOffsetMs: 1000 };
  const response = { ...expectedPost, responseOffsetMs: 950 };
  assert.deepEqual(findUncorrelatedConsoleResourceFailures(logoutCase, [failure], [response], allowlist), []);
  assert.equal(findUncorrelatedConsoleResourceFailures(logoutCase, [failure], [], allowlist).length, 1);
  assert.equal(findUncorrelatedConsoleResourceFailures(logoutCase, [failure], [
    response,
    { ...expectedPost, method: 'GET', responseOffsetMs: 1050 },
  ], allowlist).length, 1);
  assert.equal(findUncorrelatedConsoleResourceFailures(logoutCase, [failure, failure], [response], allowlist).length, 1);
  assert.equal(findUncorrelatedConsoleResourceFailures(logoutCase, [failure], [
    { ...response, responseOffsetMs: 2500 },
  ], allowlist).length, 1);
});
