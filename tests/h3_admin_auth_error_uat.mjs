import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import { webcrypto } from 'node:crypto';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(root, 'web/package.json'));
const ts = require('typescript');
const source = await readFile(join(root, 'web/src/lib/admin-auth.ts'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    esModuleInterop: true,
  },
  reportDiagnostics: true,
});
assert.equal(compiled.diagnostics?.filter((item) => item.category === ts.DiagnosticCategory.Error).length, 0);

let response = new Response(JSON.stringify({
  error: { code: 'reconciliation_required', message: 'Delivery needs reconciliation.' },
  request_id: 'invite-reference-fixture-2026-10-01',
}), { status: 409, headers: { 'Content-Type': 'application/json' } });
let requestSeen;
const moduleObject = { exports: {} };
const sandbox = {
  module: moduleObject,
  exports: moduleObject.exports,
  require,
  fetch: async (path, options) => {
    requestSeen = { path, options };
    return response;
  },
  crypto: webcrypto,
  Response,
  Headers,
  Request,
  URL,
  URLSearchParams,
  Date,
  Math,
  JSON,
  RegExp,
  String,
  Number,
  Boolean,
  Promise,
  Error,
};
vm.runInNewContext(compiled.outputText, sandbox, { filename: 'admin-auth.js' });

const { AdminApiError, inviteAdminMember } = moduleObject.exports;
const requestId = 'invite-reference-fixture-2026-10-01';
await assert.rejects(
  inviteAdminMember('new-user@local.test', 'user', { requestId }),
  (error) => {
    assert.ok(error instanceof AdminApiError);
    assert.equal(error.code, 'reconciliation_required');
    assert.equal(error.requestId, requestId);
    assert.equal(error.status, 409);
    return true;
  },
);
assert.equal(requestSeen.path, '/api/admin/invitations');
assert.equal(requestSeen.options.headers['x-request-id'], requestId, 'retry reference must reach the BFF unchanged');

response = new Response(JSON.stringify({
  success: true,
  email: 'new-user@local.test',
  user_id: 'fixture-user',
  invitation_id: 'fixture-invitation',
}), { status: 200, headers: { 'Content-Type': 'application/json' } });
const result = await inviteAdminMember('new-user@local.test', 'user', { requestId });
assert.equal(result.invitation_id, 'fixture-invitation');
console.log(JSON.stringify({ result: 'PASS', checks: 7 }));
