// StudIAMatch-Docs: .context/componentes/admin_portal.md#admin-session-guard
// StudIAMatch-Docs: .context/componentes/admin_portal.md#cola-editorial
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import vm from 'node:vm';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(root, 'web/package.json'));
const ts = require('typescript');
const flushPromises = async () => {
  for (let index = 0; index < 12; index += 1) await Promise.resolve();
};

function compileTsx(source, filename) {
  const compiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true,
    },
    reportDiagnostics: true,
  });
  const errors = compiled.diagnostics?.filter((item) => item.category === ts.DiagnosticCategory.Error) || [];
  assert.equal(errors.length, 0, `${filename} should transpile without TypeScript diagnostics`);
  return compiled.outputText;
}

function mockComponent(name) {
  const component = () => null;
  Object.defineProperty(component, 'mockName', { value: name });
  return component;
}

function jsxRuntime() {
  const makeNode = (type, props) => ({
    type: typeof type === 'string' ? type : type?.mockName || type?.name || 'Component',
    props: props || {},
  });
  return { jsx: makeNode, jsxs: makeNode, Fragment: 'Fragment' };
}

function loadComponent(relativePath, mocks, globals = {}) {
  const source = awaitRead(relativePath);
  return source.then((text) => {
    const moduleObject = { exports: {} };
    const componentProxy = new Proxy({}, {
      get: (_target, key) => mockComponent(String(key)),
    });
    const sandbox = {
      module: moduleObject,
      exports: moduleObject.exports,
      console,
      Promise,
      Date,
      JSON,
      Error,
      RegExp,
      String,
      Number,
      Boolean,
      Math,
      ...globals,
      require: (id) => {
        if (id === 'react') return mocks.react;
        if (id === 'react/jsx-runtime') return jsxRuntime();
        if (Object.hasOwn(mocks, id)) return mocks[id];
        if (id === 'next/link') return { default: mockComponent('Link') };
        if (id === 'next/navigation') return mocks.navigation || {};
        if (id.startsWith('lucide-react') || id.startsWith('@/components/')) return componentProxy;
        if (id === '@/lib/admin-auth') return mocks.auth;
        if (id === '@/lib/admin-queue-request-guard.mjs') return mocks.queueGuard;
        return componentProxy;
      },
    };
    vm.runInNewContext(compileTsx(text, relativePath), sandbox, { filename: relativePath });
    return moduleObject.exports.default;
  });
}

function awaitRead(relativePath) {
  return readFile(join(root, 'web/src', relativePath), 'utf8');
}

function makeWindow() {
  let timerId = 0;
  const listeners = new Map();
  const timers = new Map();
  return {
    listeners,
    timers,
    addEventListener: (name, handler) => listeners.set(name, handler),
    removeEventListener: (name, handler) => {
      if (listeners.get(name) === handler) listeners.delete(name);
    },
    setTimeout: (handler) => {
      timerId += 1;
      timers.set(timerId, handler);
      return timerId;
    },
    clearTimeout: (id) => timers.delete(id),
    runTimers: async () => {
      const pending = [...timers.values()];
      timers.clear();
      for (const callback of pending) callback();
      await flushPromises();
    },
  };
}

function createGuardHarness(sessionProvider, startTime = 2_000_000) {
  let pathname = '/admin/';
  let effectCallback;
  let now = startTime;
  let activity = startTime;
  let recorded = 0;
  let touched = 0;
  let signedOut = 0;
  const refs = [];
  let refIndex = 0;
  const fakeWindow = makeWindow();
  const router = { replace: (path) => { pathname = path; } };
  const auth = {
    ADMIN_ACTIVITY_EVENT_KEY: 'admin-activity',
    ADMIN_IDLE_TIMEOUT_MS: 300_000,
    ADMIN_LOGOUT_EVENT_KEY: 'admin-logout',
    getAdminLastActivity: () => activity,
    getAuthSession: sessionProvider,
    recordAdminActivity: (timestamp) => { activity = timestamp; recorded += 1; },
    signOutAdmin: async () => { signedOut += 1; activity = null; },
    touchAdminSession: async () => { touched += 1; },
  };
  const react = {
    useRef: (initial) => {
      const index = refIndex++;
      if (!(index in refs)) refs[index] = { current: initial };
      return refs[index];
    },
    useEffect: (callback) => { effectCallback = callback; },
  };
  const FakeDate = class extends Date {
    static now() { return now; }
  };
  let component;
  const mount = async (path = '/admin/') => {
    pathname = path;
    refIndex = 0;
    component();
    const cleanup = effectCallback();
    await flushPromises();
    return cleanup;
  };

  component = null;
  const loaded = loadComponent('components/admin/AdminSessionGuard.tsx', {
    react,
    auth,
    navigation: {
      usePathname: () => pathname,
      useRouter: () => router,
    },
  }, { window: fakeWindow, Date: FakeDate });

  return loaded.then((Component) => {
    component = Component;
    return {
      mount,
      window: fakeWindow,
      router,
      advance: (delta) => { now += delta; },
      counts: () => ({ recorded, touched, signedOut }),
      currentPath: () => pathname,
    };
  });
}

test('AdminSessionGuard re-enables activity only after a new validated session and keeps later expiry/logout active', async () => {
  let session = { user: { id: 'synthetic-admin' } };
  const harness = await createGuardHarness(async () => session);
  let cleanup = await harness.mount();
  assert.deepEqual(harness.counts(), { recorded: 1, touched: 1, signedOut: 0 });

  const stalePointer = harness.window.listeners.get('pointerdown');
  const firstStorageHandler = harness.window.listeners.get('storage');
  firstStorageHandler({ key: 'admin-logout', newValue: 'logout-1' });
  firstStorageHandler({ key: 'admin-logout', newValue: 'logout-duplicate' });
  await flushPromises();
  assert.equal(harness.counts().signedOut, 1, 'duplicate events must not close the same session twice');
  assert.equal(harness.currentPath(), '/admin/login/');
  cleanup();

  session = { user: { id: 'synthetic-admin-relogin' } };
  cleanup = await harness.mount('/admin/');
  assert.deepEqual(harness.counts(), { recorded: 2, touched: 2, signedOut: 1 }, 'valid re-login restores local activity and server heartbeat');
  stalePointer();
  assert.equal(harness.counts().recorded, 2, 'a callback from the old effect cannot mutate the new session');

  harness.advance(300_001);
  await harness.window.runTimers();
  assert.equal(harness.counts().signedOut, 2, 'the second session can expire independently');
  assert.equal(harness.currentPath(), '/admin/login/');
  cleanup();

  session = { user: { id: 'synthetic-admin-third-session' } };
  cleanup = await harness.mount('/admin/');
  harness.window.listeners.get('storage')({ key: 'admin-logout', newValue: 'logout-from-other-tab' });
  await flushPromises();
  assert.equal(harness.counts().signedOut, 3, 'cross-tab logout remains active after re-login');
  assert.equal(harness.currentPath(), '/admin/login/');
  cleanup();
});

test('AdminSessionGuard does not record activity before an authenticated session is validated', async () => {
  const harness = await createGuardHarness(async () => null);
  const cleanup = await harness.mount();
  harness.window.listeners.get('pointerdown')();
  await flushPromises();
  assert.deepEqual(harness.counts(), { recorded: 0, touched: 0, signedOut: 0 });
  assert.equal(harness.currentPath(), '/admin/login/');
  cleanup();
});

test('AdminSessionGuard ignores an initial session response invalidated by cross-tab logout', async () => {
  let resolveSession;
  const harness = await createGuardHarness(() => new Promise((resolve) => { resolveSession = resolve; }));
  const cleanup = await harness.mount();

  harness.window.listeners.get('storage')({ key: 'admin-logout', newValue: 'logout-during-validation' });
  resolveSession({ user: { id: 'stale-initial-session' } });
  await flushPromises();
  harness.window.listeners.get('pointerdown')?.();
  await flushPromises();

  assert.deepEqual(harness.counts(), { recorded: 0, touched: 0, signedOut: 0 }, 'a stale initial response cannot restart activity or heartbeat');
  assert.equal(harness.currentPath(), '/admin/login/', 'logout keeps protected navigation at the login route');
  cleanup();
});

function sameDeps(left, right) {
  return Boolean(left && right && left.length === right.length && left.every((value, index) => Object.is(value, right[index])));
}

function walkNodes(node, visit) {
  if (node === null || node === undefined || typeof node === 'boolean') return;
  if (Array.isArray(node)) {
    for (const child of node) walkNodes(child, visit);
    return;
  }
  if (typeof node === 'string' || typeof node === 'number') {
    visit(node);
    return;
  }
  if (typeof node === 'object') {
    visit(node);
    walkNodes(node.props?.children, visit);
  }
}

function renderQueueHarness(assuranceProvider) {
  const state = [];
  const refs = [];
  const memoValues = [];
  const memoDeps = [];
  const callbackValues = [];
  const callbackDeps = [];
  const effectDeps = [];
  const effectCleanup = [];
  const timerWindow = makeWindow();
  const rpcCalls = [];
  let stateIndex = 0;
  let refIndex = 0;
  let memoIndex = 0;
  let callbackIndex = 0;
  let effectIndex = 0;
  let pendingEffects = [];
  const react = {
    useState: (initial) => {
      const index = stateIndex++;
      if (!(index in state)) state[index] = typeof initial === 'function' ? initial() : initial;
      return [state[index], (value) => { state[index] = typeof value === 'function' ? value(state[index]) : value; }];
    },
    useRef: (initial) => {
      const index = refIndex++;
      if (!(index in refs)) refs[index] = { current: initial };
      return refs[index];
    },
    useCallback: (callback, deps) => {
      const index = callbackIndex++;
      if (callbackDeps[index] === undefined || !sameDeps(callbackDeps[index], deps)) {
        callbackDeps[index] = deps;
        callbackValues[index] = callback;
      }
      return callbackValues[index];
    },
    useMemo: (callback, deps) => {
      const index = memoIndex++;
      if (memoDeps[index] === undefined || !sameDeps(memoDeps[index], deps)) {
        memoDeps[index] = deps;
        memoValues[index] = callback();
      }
      return memoValues[index];
    },
    useEffect: (callback, deps) => {
      const index = effectIndex++;
      if (effectDeps[index] === undefined || !sameDeps(effectDeps[index], deps)) {
        effectDeps[index] = deps;
        pendingEffects.push({ index, callback });
      }
    },
  };
  const auth = {
    adminRpc: async (name) => {
      rpcCalls.push(name);
      if (name === 'admin_get_course_queue_facets') return [{ editorial_counts: {}, quality_counts: {}, institutions: [], error: null }];
      if (name === 'admin_get_course_queue_filtered') return [{ courses: [], page_info: { hasNextPage: false, endCursor: null }, error: null }];
      if (name === 'admin_count_course_queue_filtered') return [{ total: 0, error: null }];
      throw new Error(`unexpected RPC: ${name}`);
    },
    getAuthenticatorAssuranceLevel: assuranceProvider,
    isMfaRequiredError: (reason) => reason?.code === 'mfa_required',
  };
  const queueGuard = {
    canCommitAdminQueueResponse: (requestId, latestId) => requestId === latestId,
    nextAdminQueueRequestId: (id) => id + 1,
  };
  const statusMeta = (label) => ({ label, description: label, className: '', icon: mockComponent('Icon') });
  const editorialUi = {
    EDITORIAL_STATUS_META: {
      draft: statusMeta('Borrador'),
      pending_review: statusMeta('Pendiente'),
      published: statusMeta('Publicado'),
      archived: statusMeta('Archivado'),
    },
    QUALITY_STATUS_META: {
      pending: statusMeta('Pendiente'),
      complete: statusMeta('Completo'),
      blocked: statusMeta('Bloqueado'),
    },
    StatusBadge: mockComponent('StatusBadge'),
  };
  const ComponentPromise = loadComponent('components/AdminCourseQueue.tsx', {
    react,
    auth,
    queueGuard,
    '@/components/admin/editorial-ui': editorialUi,
  }, { window: timerWindow });
  let Component;

  const render = async () => {
    Component ||= await ComponentPromise;
    stateIndex = 0;
    refIndex = 0;
    memoIndex = 0;
    callbackIndex = 0;
    effectIndex = 0;
    pendingEffects = [];
    const tree = Component({ role: 'admin' });
    for (const { index, callback } of pendingEffects) {
      effectCleanup[index]?.();
      effectCleanup[index] = callback();
    }
    return tree;
  };

  return {
    render,
    window: timerWindow,
    rpcCalls,
    counts: () => ({ ...state }),
  };
}

function findNode(tree, name) {
  let found;
  walkNodes(tree, (node) => {
    if (!found && node && typeof node === 'object' && node.type === name) found = node;
  });
  return found;
}

function collectText(tree) {
  const parts = [];
  walkNodes(tree, (node) => {
    if (typeof node === 'string' || typeof node === 'number') parts.push(String(node));
  });
  return parts.join(' ');
}

test('AdminCourseQueue shows assurance errors, rechecks on retry, and fetches only after aal2', async () => {
  const assuranceResults = [
    () => Promise.reject(new Error('assurance unavailable')),
    () => Promise.reject(new Error('still unavailable')),
    () => Promise.resolve({ currentLevel: 'aal1' }),
    () => Promise.resolve({ currentLevel: 'aal2' }),
  ];
  let assuranceCalls = 0;
  const harness = renderQueueHarness(() => {
    assuranceCalls += 1;
    return assuranceResults.shift()();
  });

  let tree = await harness.render();
  await harness.window.runTimers();
  tree = await harness.render();
  assert.match(collectText(tree), /assurance unavailable/);
  assert.equal(findNode(tree, 'Button')?.props?.children, 'Reintentar');
  assert.equal(assuranceCalls, 1);
  assert.equal(harness.rpcCalls.length, 0, 'no queue or facets are loaded after an assurance error');

  findNode(tree, 'Button').props.onClick();
  await flushPromises();
  tree = await harness.render();
  assert.match(collectText(tree), /still unavailable/);
  assert.equal(assuranceCalls, 2, 'retry performs a fresh assurance request');
  assert.equal(harness.rpcCalls.length, 0);

  findNode(tree, 'Button').props.onClick();
  await flushPromises();
  tree = await harness.render();
  assert.ok(findNode(tree, 'MfaRequiredCard'), 'aal1 continues to require MFA');
  assert.equal(assuranceCalls, 3);
  assert.equal(harness.rpcCalls.length, 0, 'aal1 never loads queue data');

  findNode(tree, 'MfaRequiredCard').props.onVerified();
  await flushPromises();
  tree = await harness.render();
  await harness.window.runTimers();
  tree = await harness.render();
  assert.equal(assuranceCalls, 4, 'post-MFA callback rechecks the actual assurance level');
  assert.deepEqual(harness.rpcCalls.sort(), [
    'admin_count_course_queue_filtered',
    'admin_get_course_queue_facets',
    'admin_get_course_queue_filtered',
  ].sort());
  assert.doesNotMatch(collectText(tree), /Verificando la seguridad de la sesión/);
});

test('AdminCourseQueue ignores an obsolete assurance response after a newer retry', async () => {
  const pending = [];
  const harness = renderQueueHarness(() => new Promise((resolve, reject) => pending.push({ resolve, reject })));

  await harness.render();
  await harness.window.runTimers();
  pending[0].reject(new Error('initial assurance failure'));
  await flushPromises();
  let tree = await harness.render();
  assert.match(collectText(tree), /initial assurance failure/);

  const retry = findNode(tree, 'Button').props.onClick;
  retry();
  retry();
  assert.equal(pending.length, 3, 'both retries issue an assurance check');

  pending[2].resolve({ currentLevel: 'aal1' });
  await flushPromises();
  tree = await harness.render();
  assert.ok(findNode(tree, 'MfaRequiredCard'), 'the latest AAL1 response keeps the queue closed');

  pending[1].resolve({ currentLevel: 'aal2' });
  await flushPromises();
  tree = await harness.render();
  await harness.window.runTimers();
  tree = await harness.render();
  assert.ok(findNode(tree, 'MfaRequiredCard'), 'an older AAL2 response cannot override the latest AAL1 result');
  assert.equal(harness.rpcCalls.length, 0, 'stale AAL2 cannot start queue or facet reads');
});
