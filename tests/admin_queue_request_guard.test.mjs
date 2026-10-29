// StudIAMatch-Docs: .context/componentes/admin_portal.md#cola-editorial
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import {
  canCommitAdminQueueResponse,
  nextAdminQueueRequestId,
} from '../web/src/lib/admin-queue-request-guard.mjs';

const repoRoot = resolve(fileURLToPath(new URL('..', import.meta.url)));
const queueSource = await readFile(resolve(repoRoot, 'web/src/components/AdminCourseQueue.tsx'), 'utf8');

function deferred() {
  let resolvePromise;
  const promise = new Promise((resolveValue) => { resolvePromise = resolveValue; });
  return { promise, resolve: resolvePromise };
}

test('a slower stale filter response cannot overwrite the latest result or clear its loading state', async () => {
  let latestRequestId = 0;
  let visibleResult = 'initial';
  let loading = true;
  const stale = deferred();
  const latest = deferred();
  const staleId = ++latestRequestId;
  const staleRun = stale.promise.then((result) => {
    if (!canCommitAdminQueueResponse(staleId, latestRequestId)) return;
    visibleResult = result;
    loading = false;
  });
  const latestId = ++latestRequestId;
  const latestRun = latest.promise.then((result) => {
    if (!canCommitAdminQueueResponse(latestId, latestRequestId)) return;
    visibleResult = result;
    loading = false;
  });

  latest.resolve('new-filter-results');
  await latestRun;
  stale.resolve('stale-filter-results');
  await staleRun;

  assert.equal(visibleResult, 'new-filter-results');
  assert.equal(loading, false);
});

test('AdminCourseQueue guards success, error and finally state writes by request generation', () => {
  assert.ok(/const requestId = nextAdminQueueRequestId\(latestQueueRequestId\.current\)/.test(queueSource));
  assert.ok((queueSource.match(/canCommitAdminQueueResponse\(requestId, latestQueueRequestId\.current\)/g) || []).length >= 3);
});

test('changing a filter invalidates an in-flight response before the replacement request starts', async () => {
  const staleRequestId = 7;
  const invalidatedRequestId = nextAdminQueueRequestId(staleRequestId);
  const staleResponse = deferred();
  let visibleResult = 'current-filter-state';

  const staleRun = staleResponse.promise.then((result) => {
    if (!canCommitAdminQueueResponse(staleRequestId, invalidatedRequestId)) return;
    visibleResult = result;
  });
  staleResponse.resolve('old-filter-results');
  await staleRun;

  assert.equal(visibleResult, 'current-filter-state');
  assert.ok(/const updateFilter = \([\s\S]*?latestQueueRequestId\.current = nextAdminQueueRequestId[\s\S]*?setFilters/.test(queueSource));
  assert.ok(/const updateInstitution = \([\s\S]*?latestQueueRequestId\.current = nextAdminQueueRequestId[\s\S]*?setInstitutionSlug/.test(queueSource));
});
