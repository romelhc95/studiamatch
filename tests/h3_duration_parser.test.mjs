import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const requireFromWeb = createRequire(resolve(repoRoot, 'web/package.json'));
const ts = requireFromWeb('typescript');
const source = await readFile(resolve(repoRoot, 'web/src/lib/supabase.ts'), 'utf8');
const homeSource = await readFile(resolve(repoRoot, 'web/src/app/HomeContent.tsx'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
});
const moduleRecord = { exports: {} };
const requireFromRepo = createRequire(import.meta.url);
const sandbox = {
  exports: moduleRecord.exports,
  module: moduleRecord,
  process: {
    env: {
      NEXT_PUBLIC_SUPABASE_URL: 'http://localhost:3380',
      NEXT_PUBLIC_H3_MOCK_URL: 'http://localhost:3380',
      NODE_ENV: 'test',
    },
  },
  URL,
  fetch,
  __arraySomeSlotsVisited: 0,
  require(specifier) {
    if (specifier === '@supabase/supabase-js') return { createClient: () => ({}) };
    if (specifier === './supabase-transport') {
      return { createApiKeyOnlyFetch: (_key, fetchImpl) => fetchImpl };
    }
    return requireFromRepo(specifier);
  },
};
vm.runInNewContext(`
  const originalSome = Array.prototype.some;
  Array.prototype.some = function (callback, thisArg) {
    globalThis.__arraySomeSlotsVisited += this.length;
    return originalSome.call(this, callback, thisArg);
  };
`, sandbox);
vm.runInNewContext(compiled.outputText, sandbox, { filename: 'supabase.ts' });
const { parseDurationToMonths, isUpdateCareerGoalCourse } = moduleRecord.exports;

test('update goal accepts accented and unaccented hybrid labels for short courses', () => {
  assert.equal(isUpdateCareerGoalCourse('32 horas académicas 1 mes aproximadamente.', 'Hibrido'), true);
  assert.equal(isUpdateCareerGoalCourse('32 horas académicas 1 mes aproximadamente.', 'Híbrido'), true);
  assert.equal(isUpdateCareerGoalCourse('32 horas académicas 1 mes aproximadamente.', ' remoto '), true);
  assert.equal(isUpdateCareerGoalCourse('8 meses', 'Hibrido'), false);
  assert.equal(isUpdateCareerGoalCourse('1 mes', 'Presencial'), false);
});

test('both update-goal consumers use the shared eligibility contract', () => {
  assert.equal((homeSource.match(/isUpdateCareerGoalCourse\(c\.duration,\s*c\.mode\)/g) || []).length, 2);
  assert.doesNotMatch(homeSource, /c\.mode\s*===\s*['"]Híbrido['"]/);
});

test('filter summary wraps the clear-all control instead of forcing a narrow row overflow', () => {
  const labelPosition = homeSource.indexOf('Limpiar todo');
  const buttonStart = homeSource.lastIndexOf('<button', labelPosition);
  const rowStart = homeSource.lastIndexOf('<div', buttonStart);
  const buttonMarkup = homeSource.slice(buttonStart, labelPosition);
  const rowOpeningTag = homeSource.slice(rowStart, homeSource.indexOf('>', rowStart));
  assert.match(rowOpeningTag, /flex-wrap/);
  assert.match(buttonMarkup, /shrink-0/);
});

test('parenthetical equivalent duration is not added twice', () => {
  assert.equal(parseDurationToMonths('6 meses (24 semanas)'), 6);
  assert.equal(parseDurationToMonths('6 months (24 weeks)'), 6);
});

test('additive top-level duration units are still summed', () => {
  assert.equal(parseDurationToMonths('1 año y 6 meses'), 18);
  assert.equal(parseDurationToMonths('1 year and 6 months'), 18);
  assert.equal(parseDurationToMonths('1 año (12 meses) y 6 meses'), 18);
});

test('a duration found only in parentheses remains usable', () => {
  assert.equal(parseDurationToMonths('Duración aproximada (6 meses)'), 6);
});

test('equivalent units inside a parenthetical clarification are not added twice', () => {
  assert.equal(parseDurationToMonths('Duración aproximada (6 meses, 24 semanas)'), 6);
});

test('an equivalent parenthetical unit is skipped while a distinct period is added', () => {
  assert.equal(parseDurationToMonths('6 meses (24 semanas y 2 meses)'), 8);
});

test('a distinct parenthetical period is not skipped just because it matches an intermediate sum', () => {
  assert.equal(parseDurationToMonths('6 meses (24 semanas y 2 meses y 8 meses)'), 16);
});

test('an unclosed parenthetical clarification does not double-count the primary duration', () => {
  assert.equal(parseDurationToMonths('6 meses (24 semanas'), 6);
});

test('zero-duration clarifications do not change the parsed total', () => {
  assert.equal(parseDurationToMonths('1 mes (0 meses) (0 semanas)'), 1);
  assert.equal(parseDurationToMonths('Duración (0 meses) (6 meses)'), 6);
});

test('repeated zero references do not scan a growing array', () => {
  sandbox.__arraySomeSlotsVisited = 0;
  const zeroClarifications = '(0 months) '.repeat(2_000);
  assert.equal(parseDurationToMonths(`1 month ${zeroClarifications}`), 1);
  assert.equal(sandbox.__arraySomeSlotsVisited, 0);
});

test('positive references keep the ten-percent equivalence boundary', () => {
  assert.equal(parseDurationToMonths('10 meses (11 meses)'), 10);
  assert.equal(parseDurationToMonths('10 meses (11.2 meses)'), 21.2);
});

test('overflow-duration tokens preserve the parser total', () => {
  const overflowDuration = `${'9'.repeat(308)} años`;
  assert.equal(parseDurationToMonths(`Duración (${overflowDuration}) (${overflowDuration})`), Infinity);
});
