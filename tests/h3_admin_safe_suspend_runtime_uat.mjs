// Local workerd execution of the actual Pages middleware's safe-suspend path.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile, stat } from 'node:fs/promises';
import { dirname, extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(process.env.H3_RUNTIME_ROOT || dirname(dirname(fileURLToPath(import.meta.url))));
const toolsRoot = process.env.H3_QUOTA_TOOLS || '/tmp/h3-quota-runtime-tools';
const tools = createRequire(join(toolsRoot, 'package.json'));
const { Miniflare } = tools('miniflare');
const { build } = tools('esbuild');
const assetRoot = join(root, 'web/out');
let assetRequests = 0;
const mime = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp', '.woff2': 'font/woff2' };

const bundle = await build({
  stdin: {
    contents: "import { onRequest } from './web/functions/_middleware.ts'; export default { fetch(request, env) { return onRequest({ request, env, next: () => env.ASSETS.fetch(request) }); } };",
    resolveDir: root,
    sourcefile: 'h3-safe-suspend-pages-entry.ts',
  },
  bundle: true,
  write: false,
  format: 'esm',
  platform: 'browser',
  target: 'es2022',
});

const assets = async (request) => {
  assetRequests += 1;
  try {
    const pathname = decodeURIComponent(new URL(request.url).pathname);
    let file = resolve(assetRoot, `.${pathname}`);
    if (!file.startsWith(`${assetRoot}/`) && file !== assetRoot) return new Response('Not found', { status: 404 });
    if ((await stat(file)).isDirectory()) file = join(file, 'index.html');
    return new Response(await readFile(file), { headers: { 'Content-Type': mime[extname(file)] || 'application/octet-stream' } });
  } catch { return new Response('Not found', { status: 404 }); }
};

const miniflare = new Miniflare({
  workers: [{
    name: 'pages-safe-suspend',
    modules: [{ type: 'ESModule', path: 'pages-safe-suspend.mjs', contents: bundle.outputFiles[0].text }],
    compatibilityDate: '2026-07-30',
    compatibilityFlags: ['nodejs_compat'],
    bindings: { ADMIN_ALLOWED_HOSTS: 'localhost,127.0.0.1', ADMIN_BFF_SAFE_SUSPEND: 'true' },
    serviceBindings: { ASSETS: assets },
  }],
});

try {
  const pages = await miniflare.getWorker('pages-safe-suspend');
  const cookie = [
    '__Host-studiamatch-admin-auth.0=local-fixture',
    '__Host-studiamatch-admin-auth-code-verifier.0=local-verifier',
    '__Host-studiamatch-admin-activity=local-activity',
    '__Host-studiamatch-admin-callback-csrf=local-csrf',
  ].join('; ');
  for (const pathname of ['/admin/', '/admin/login/', '/api/admin/session']) {
    const response = await pages.fetch(`https://localhost${pathname}`, { headers: { Cookie: cookie } });
    assert.equal(response.status, 503, `${pathname} stays safely suspended`);
    assert.equal(response.headers.get('Cache-Control'), 'private, no-store');
    assert.equal(response.headers.get('Retry-After'), '60');
    const setCookies = typeof response.headers.getSetCookie === 'function'
      ? response.headers.getSetCookie().join('\n') : response.headers.get('Set-Cookie') || '';
    for (const name of ['__Host-studiamatch-admin-auth.0', '__Host-studiamatch-admin-auth-code-verifier.0', '__Host-studiamatch-admin-activity', '__Host-studiamatch-admin-callback-csrf']) {
      assert(setCookies.includes(`${name}=`) && setCookies.includes('Max-Age=0'), `${name} must be cleared`);
    }
  }
  for (const pathname of ['/', '/courses/', '/%63ourses/']) {
    const response = await pages.fetch(`https://localhost${pathname}`);
    assert.equal(response.status, 200, `${pathname} public static page remains available`);
    assert((await response.text()).length > 0);
  }
  const publicAssetRequests = assetRequests;
  for (const pathname of ['/%61dmin/', '/%2561dmin/', '/%2525252561dmin/', '/%252e/admin/', '/admin/%61uth/callback', '/api/%61dmin/session', '/%25252fadmin/', '//admin/']) {
    const response = await pages.fetch(`https://localhost${pathname}`);
    assert([404, 503].includes(response.status), `${pathname} must stay inside the Admin perimeter`);
    assert.notEqual(response.status, 200, `${pathname} must never expose a static Admin asset`);
  }
  assert.equal(assetRequests, publicAssetRequests, 'encoded Admin aliases must not reach static asset fallback');
  const publicAdmin = await pages.fetch('https://studiamatch.com/admin/');
  assert.equal(publicAdmin.status, 404, 'public hostname continues to hide Admin');
  console.log(JSON.stringify({ result: 'PASS', runtime: 'workerd/Miniflare', suspendedAdminRoutes: 3, publicRoutes: 3, encodedAdminAliasesRejected: 8, cookiesCleared: 4 }));
} finally {
  await miniflare.dispose();
}
