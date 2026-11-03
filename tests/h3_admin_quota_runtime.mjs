// Run in Docker with Node >=22 and Miniflare 4.20260730.0 installed in an
// isolated tools directory (H3_QUOTA_TOOLS). Never dispatch a remote Worker.
import assert from 'node:assert/strict';
import { readFile,mkdtemp } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const root = new URL('..',import.meta.url);
const require = createRequire(new URL('web/package.json',root));
const tools = createRequire(join(process.env.H3_QUOTA_TOOLS || '/tmp/h3-quota-runtime-tools','package.json'));
const { Miniflare } = tools('miniflare');
const ts = require('typescript');
const script=ts.transpileModule(await readFile(new URL('workers/admin-quota/index.ts',root),'utf8'), {
  compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022},
}).outputText;
const config=JSON.parse(await readFile(new URL('workers/admin-quota/wrangler.jsonc',root),'utf8'));
assert.equal(config.workers_dev,false);
assert.equal(config.preview_urls,false);
assert.equal(config.routes,undefined);
const persistent=await mkdtemp(join(tmpdir(),'h3-quota-runtime-'));
const options={name:'admin-quota',script,modules:true,compatibilityDate:config.compatibility_date,
  durableObjects:{ADMIN_QUOTA_COUNTER:{className:'AdminQuotaCounter',useSQLite:true}},
  durableObjectsPersist:persistent};
let mf=new Miniflare(options);
const ipDigest='a'.repeat(64);
const accountDigest='b'.repeat(64);
const body=JSON.stringify({counters:[
  {kind:'login-ip',digest:ipDigest},
  {kind:'login-account-ip',digest:accountDigest,shard:ipDigest},
]});
try {
  const batch=await Promise.all(Array.from({length:25},()=>mf.dispatchFetch('https://admin-quota.internal/check',{method:'POST',body})));
  assert.equal(batch.filter(r=>r.status===200).length,10);
  assert.equal(batch.filter(r=>r.status===429).length,15);
  assert(Number(batch.find(r=>r.status===429).headers.get('Retry-After'))>0);
  await mf.dispose();
  mf=new Miniflare(options);
  assert.equal((await mf.dispatchFetch('https://admin-quota.internal/check',{method:'POST',body})).status,429);
  const otherIp='c'.repeat(64);
  const other=JSON.stringify({counters:[
    {kind:'login-ip',digest:otherIp},
    {kind:'login-account-ip',digest:'d'.repeat(64),shard:otherIp},
  ]});
  assert.equal((await mf.dispatchFetch('https://admin-quota.internal/check',{method:'POST',body:other})).status,200);
  const legacyIp='e'.repeat(64);
  const legacy=JSON.stringify({counters:[
    {kind:'login-ip',digest:legacyIp},
    {kind:'login-account-ip',digest:'f'.repeat(64)},
  ]});
  assert.equal((await mf.dispatchFetch('https://admin-quota.internal/check',{method:'POST',body:legacy})).status,200,
    'the Worker must infer paired shards for the previous BFF payload during compatibility');
  const unpaired=JSON.stringify({counters:[{kind:'login-account-ip',digest:'1'.repeat(64)}]});
  assert.equal((await mf.dispatchFetch('https://admin-quota.internal/check',{method:'POST',body:unpaired})).status,400);
  assert.equal((await mf.dispatchFetch('https://admin-quota.internal/check',{method:'GET'})).status,404);
  console.log(JSON.stringify({result:'PASS',runtime:'workerd/Miniflare',concurrentRequests:25,admitted:10,
    restartPersistence:true,pairedLoginShard:true,previousBffCompatibility:true,persistent,
    node:process.version,miniflare:tools('miniflare/package.json').version}));
} finally {await mf.dispose();}
