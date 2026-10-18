import assert from 'node:assert/strict';
import test from 'node:test';
import { sanitize, safeLocalOrigin, safeLocalPath, safeLocalRequest } from './h3_uat_sanitizer.mjs';

const origins = ['http://localhost:3380', 'http://localhost:3381'];

test('local absolute URLs retain only their pathname', () => {
  assert.equal(safeLocalPath('http://localhost:3380/api/admin/rpc?access_token=synthetic-secret#fragment', origins), '/api/admin/rpc');
});

test('external absolute URLs are not serialized', () => {
  assert.equal(safeLocalPath('https://outside.example/private?token=synthetic-secret', origins), '[external]');
  assert.deepEqual(safeLocalRequest('https://outside.example/private?token=synthetic-secret', origins), {
    origin: 'external', path: '[external]',
  });
  assert.equal(sanitize('request https://outside.example/private?token=synthetic-secret failed', origins), 'request [external] failed');
});

test('relative query and fragment strings are omitted from diagnostics', () => {
  assert.equal(sanitize('failed GET /api/admin/rpc?code=synthetic-secret#fragment', origins), 'failed GET [LOCAL_PATH]');
  assert.equal(sanitize('url=/api/admin/rpc?code=synthetic-secret#fragment', origins), 'url=[LOCAL_PATH]');
  assert.equal(sanitize('referer:/api/admin/rpc?state=synthetic-secret', origins), 'referer:[LOCAL_PATH]');
  assert.equal(sanitize('url=api/admin/rpc?code=synthetic-secret', origins), 'url=[LOCAL_PATH]');
  assert.equal(sanitize('referer:api/admin/rpc?state=synthetic-secret', origins), 'referer:[LOCAL_PATH]');
  assert.equal(sanitize('query ?code=synthetic-secret', origins), 'query [QUERY]');
});

test('bearer and token values remain redacted', () => {
  assert.equal(sanitize('Bearer synthetic.jwt.value access_token=synthetic-access', origins), 'Bearer [REDACTED] token=[REDACTED]');
});

test('local paths without query remain available for debugging', () => {
  assert.equal(sanitize('request GET /api/admin/rpc failed', origins), 'request GET /api/admin/rpc failed');
  assert.equal(safeLocalOrigin('http://localhost:3380/api/admin/session', origins), 'local-0');
  assert.deepEqual(safeLocalRequest('http://localhost:3381/__test/reset', origins), {
    origin: 'local-1', path: '/__test/reset',
  });
  assert.equal(safeLocalPath(`http://localhost:3380/admin/auth/callback/${'A'.repeat(48)}`, origins),
    '/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath(`http://localhost:3380/admin/auth/callback/${'a9B'.repeat(11)}`, origins),
    '/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath('http://localhost:3380/courses/123e4567-e89b-12d3-a456-426614174000/', origins),
    '/courses/[REDACTED]/');
  assert.equal(sanitize('/courses/advanced-data/'), '/courses/advanced-data/');
  assert.equal(sanitize('/courses/advanced-data-science-and-engineering-program/'),
    '/courses/[REDACTED]/');
});

test('relative opaque path segments are redacted even without a query string', () => {
  const opaque = 'a9B'.repeat(11);
  const percentEncodedOpaque = Array.from(opaque, (character) => `%${character.charCodeAt(0).toString(16).padStart(2, '0')}`).join('');
  const doublePercentEncodedOpaque = percentEncodedOpaque.replace(/%/g, '%25');
  assert.equal(sanitize(`/admin/auth/callback/${opaque}`, origins), '/admin/auth/callback/[REDACTED]');
  assert.equal(sanitize(`navigationTrace=/admin/auth/callback/${opaque}`, origins),
    'navigationTrace=/admin/auth/callback/[REDACTED]');
  assert.equal(sanitize(`/admin/auth/callback/${percentEncodedOpaque}`, origins), '/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath(`http://localhost:3380/admin/auth/callback/${percentEncodedOpaque}`, origins),
    '/admin/auth/callback/[REDACTED]');
  assert.equal(sanitize(`/admin/auth/callback/${doublePercentEncodedOpaque}`, origins),
    '/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath(`http://localhost:3380/admin/auth/callback/${doublePercentEncodedOpaque}`, origins),
    '/admin/auth/callback/[REDACTED]');
  assert.equal(sanitize('/courses/curso-de-ingenieria-informatica/'),
    '/courses/[REDACTED]/');
});

test('standard base64 path tokens containing an encoded slash are redacted', () => {
  const token = `${'a9B'.repeat(8)}/${'K2c'.repeat(6)}`;
  const encodedToken = encodeURIComponent(token);
  assert.equal(sanitize(`/admin/auth/callback/${encodedToken}`, origins),
    '/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath(`http://localhost:3380/admin/auth/callback/${encodedToken}`, origins),
    '/admin/auth/callback/[REDACTED]');
});

test('standard base64 path tokens with slash and no digits are redacted', () => {
  const token = `${'A'.repeat(43)}/`;
  const encodedToken = encodeURIComponent(token);
  assert.equal(sanitize(`/admin/auth/callback/${encodedToken}`, origins),
    '/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath(`http://localhost:3380/admin/auth/callback/${encodedToken}`, origins),
    '/admin/auth/callback/[REDACTED]');
});

test('short opaque tokens remain redacted when percent encoding expands their path segment', () => {
  const token = 'g9H'.repeat(8);
  const encodedToken = Array.from(token, (character) => `%${character.charCodeAt(0).toString(16).padStart(2, '0')}`).join('');
  assert.equal(sanitize(`/admin/auth/callback/${token}`, origins), '/admin/auth/callback/[REDACTED]');
  assert.equal(sanitize(`/admin/auth/callback/${encodedToken}`, origins), '/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath(`http://localhost:3380/admin/auth/callback/${encodedToken}`, origins),
    '/admin/auth/callback/[REDACTED]');
});

test('the opaque path redaction boundary keeps shorter readable segments', () => {
  const belowBoundary = 'a'.repeat(11);
  const lowercaseToken = 'a'.repeat(12);
  const atBoundary = 'a'.repeat(24);
  const shortMixedToken = 'g9H'.repeat(4);
  assert.equal(sanitize(`/courses/${belowBoundary}`), `/courses/${belowBoundary}`);
  assert.equal(sanitize(`/courses/${lowercaseToken}`), '/courses/[REDACTED]');
  assert.equal(sanitize(`/courses/${atBoundary}`), '/courses/[REDACTED]');
  assert.equal(sanitize(`/courses/${shortMixedToken}`), '/courses/[REDACTED]');
  assert.equal(sanitize('/courses/advanced-data/'), '/courses/advanced-data/');
});

test('admin auth callback path values redact regardless of token length', () => {
  assert.equal(sanitize('/admin/auth/callback/x'), '/admin/auth/callback/[REDACTED]');
  assert.equal(sanitize('admin/auth/callback/x'), '/admin/auth/callback/[REDACTED]');
  assert.equal(sanitize('route=admin/auth/callback/x'), 'route=/admin/auth/callback/[REDACTED]');
  assert.equal(sanitize('route=admin%2Fauth%2Fcallback%2Fx'), 'route=/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath('http://localhost:3380/admin/auth/callback/x', origins),
    '/admin/auth/callback/[REDACTED]');
  assert.equal(sanitize('/admin%2Fauth%2Fcallback%2Fx'), '/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath('http://localhost:3380/admin/auth%2Fcallback%2Fx', origins),
    '/admin/auth/callback/[REDACTED]');
});

test('32-character mixed alphanumeric path tokens outside hex are redacted', () => {
  const token = 'g9H'.repeat(11);
  assert.equal(sanitize(`/admin/auth/callback/${token}`, origins),
    '/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath(`http://localhost:3380/admin/auth/callback/${token}`, origins),
    '/admin/auth/callback/[REDACTED]');
});

test('32-character lowercase alphanumeric path tokens are redacted', () => {
  const token = 'g9h'.repeat(11);
  assert.equal(sanitize(`/admin/auth/callback/${token}`, origins),
    '/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath(`http://localhost:3380/admin/auth/callback/${token}`, origins),
    '/admin/auth/callback/[REDACTED]');
});

test('long lowercase hyphenated path values are redacted like opaque tokens', () => {
  const slugShapedValue = 'advanced-data-science-and-engineering-program';
  assert.equal(sanitize(`/courses/${slugShapedValue}`, origins), '/courses/[REDACTED]');
  assert.equal(safeLocalPath(`http://localhost:3380/courses/${slugShapedValue}`, origins), '/courses/[REDACTED]');
});

test('malformed percent escapes in opaque path values are redacted', () => {
  const malformedOpaque = `${'a9B'.repeat(11)}%`;
  assert.equal(sanitize(`/admin/auth/callback/${malformedOpaque}`, origins),
    '/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath(`http://localhost:3380/admin/auth/callback/${malformedOpaque}`, origins),
    '/admin/auth/callback/[REDACTED]');
});

test('opaque path values fail closed beyond the percent-decoding safety bound', () => {
  const opaque = 'a9B'.repeat(11);
  let encoded = Array.from(opaque, (character) => `%${character.charCodeAt(0).toString(16).padStart(2, '0')}`).join('');
  for (let depth = 0; depth < 9; depth += 1) encoded = encoded.replace(/%/g, '%25');
  assert.equal(sanitize(`/admin/auth/callback/${encoded}`, origins),
    '/admin/auth/callback/[REDACTED]');
  assert.equal(safeLocalPath(`http://localhost:3380/admin/auth/callback/${encoded}`, origins),
    '/admin/auth/callback/[REDACTED]');
});
