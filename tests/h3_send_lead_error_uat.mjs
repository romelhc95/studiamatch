import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(root, 'web/package.json'));
const ts = require('typescript');
const source = await readFile(
  join(root, 'supabase/functions/send-lead-emails/index.ts'),
  'utf8',
);
const sourceFile = ts.createSourceFile(
  'send-lead-emails/index.ts',
  source,
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.TS,
);
const importStatement = sourceFile.statements.find(ts.isImportDeclaration);
assert.ok(importStatement, 'the Edge Runtime type import must be present');
const implementation = source.slice(importStatement.end);
const compiled = ts.transpileModule(implementation, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
  reportDiagnostics: true,
});
assert.equal(compiled.diagnostics?.filter((item) => item.category === ts.DiagnosticCategory.Error).length, 0);

let handler;
let fetchCalls = 0;
const marker = 'FIXTURE_INTERNAL_ERROR_DETAIL';
const failure = new Error(marker);
failure.stack = marker + '\n    at private/server/path.ts:42';
const context = {
  Deno: {
    env: {
      get(name) {
        if (name === 'RESEND_API_KEY') return 'synthetic-resend-key-not-for-any-service';
        if (name === 'ADMIN_EMAIL') return 'admin@example.test';
        return undefined;
      },
    },
    serve(callback) {
      handler = callback;
    },
  },
  fetch: async () => {
    fetchCalls += 1;
    throw failure;
  },
  Response,
  JSON,
  console: { error() {} },
  exports: {},
  module: { exports: {} },
};
vm.runInNewContext(compiled.outputText, context, {
  filename: 'send-lead-emails-real-handler.js',
});
assert.equal(typeof handler, 'function', 'the Edge Function must register its real request handler');

const response = await handler(new Request('https://edge.example.test/functions/v1/send-lead-emails', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    record: { email: 'fixture@example.test', first_name: 'Fixture' },
    course: { name: 'Fixture course' },
    institution: { name: 'Fixture institution' },
  }),
}));
const body = await response.text();
assert.equal(fetchCalls, 1, 'the real handler must reach the mocked mail-provider failure');
assert.equal(response.status, 500);
assert.equal(response.headers.get('Content-Type'), 'application/json');
assert.equal(response.headers.get('Access-Control-Allow-Origin'), '*');
assert.equal(body, JSON.stringify({ error: 'Internal server error' }));
assert.ok(!body.includes(marker) && !body.includes('private/server/path.ts'));
console.log(JSON.stringify({ result: 'PASS', checks: 7 }));
