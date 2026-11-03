import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const require = createRequire(join(root, 'web/package.json'));
const ts = require('typescript');
const file = resolve(root, 'supabase/functions/admin-invite/index.ts');
const source = readFileSync(file, 'utf8')
  .replace(/^import "jsr:[^\n]+\n/m, '')
  .replace('"npm:@supabase/supabase-js@2"', '"@supabase/supabase-js"');
const denoTypes = `
declare const Deno: {
  env: { get(name: string): string | undefined };
  serve(handler: (request: Request) => Response | Promise<Response>): void;
};
`;
const options = {
  strict: true, noEmit: true, skipLibCheck: true,
  target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext,
  moduleResolution: ts.ModuleResolutionKind.Bundler,
  lib: ['lib.es2022.d.ts', 'lib.dom.d.ts', 'lib.dom.iterable.d.ts'],
  types: [],
};
const host = ts.createCompilerHost(options);
const originalRead = host.readFile.bind(host);
host.readFile = path => resolve(path) === file ? source + denoTypes : originalRead(path);
host.resolveModuleNames = (names, containingFile) => names.map(name => ts.resolveModuleName(
  name, resolve(containingFile) === file ? join(root, 'web/__edge_typecheck__.ts') : containingFile, options, host,
).resolvedModule);
const program = ts.createProgram([file, join(root,'workers/admin-quota/index.ts')], options, host);
const errors = ts.getPreEmitDiagnostics(program).filter(d => d.category === ts.DiagnosticCategory.Error);
if (errors.length) console.error(ts.formatDiagnosticsWithColorAndContext(errors, {
  getCanonicalFileName: path => path, getCurrentDirectory: () => root, getNewLine: () => '\n',
}));
assert.equal(errors.length, 0, 'Edge semantic typecheck must pass with the installed SDK types');
console.log(JSON.stringify({ result: 'PASS', semanticTypecheck: 'admin-invite', sdk: require('@supabase/supabase-js/package.json').version }));
