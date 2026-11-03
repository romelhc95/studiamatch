// StudIAMatch-Docs: .context/componentes/admin_portal.md#cola-editorial
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const repoRoot = resolve(fileURLToPath(new URL('..', import.meta.url)));
const adminPage = await readFile(resolve(repoRoot, 'web/src/app/admin/page.tsx'), 'utf8');

test('Admin header stacks its identity and actions below the small-screen breakpoint', () => {
  assert.ok(/mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6/.test(adminPage), 'header must stack on narrow viewports and return to a row at sm');
  assert.ok(/flex w-full flex-wrap items-center justify-end gap-3 sm:w-auto/.test(adminPage), 'admin identity and actions must wrap within the available mobile width');
});
