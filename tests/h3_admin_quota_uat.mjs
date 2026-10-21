import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import { webcrypto } from 'node:crypto';
import { isolateQuotaCounters } from './h3_local_runtime_quota_fixture.mjs';
const root = new URL('..',import.meta.url);
const require = createRequire(new URL('web/package.json',root));
const ts = require('typescript');
let now = 100000000;
function compile(source) {
  const module = { exports: {} };
  vm.runInNewContext(ts.transpileModule(source,{ compilerOptions: { module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022 } }).outputText,
    { module,exports:module.exports,Request,Response,Headers,URL,TextEncoder,crypto:webcrypto,
      Date: { now:()=>now },console },{ filename:'quota-test.js' });
  return module.exports;
}
const quotaModule = compile(await readFile(new URL('workers/admin-quota/index.ts',root),'utf8'));
const { AdminQuotaCounter } = quotaModule;
const AdminQuotaWorker = quotaModule.default;
const { checkAdminQuota,trustedQuotaIp } = compile(await readFile(new URL('web/functions/_lib/admin-quota.ts',root),'utf8'));
let data = {};
let chain = Promise.resolve();
let failure = false;
const storage = {
  transaction(callback) {
    const next = chain.then(async()=>{
      if(failure) throw Error('fixture unavailable');
      const staged=structuredClone(data);
      const result=await callback({
        get:async key=>staged[key],
        put:async(key,value)=>{staged[key]=value;},
        delete:async key=>{const existed=Object.hasOwn(staged,key);delete staged[key];return existed;},
      });
      data=staged; return result;
    });
    chain=next.catch(()=>{});return next;
  },
  setAlarm:async()=>{},
};
let counter = new AdminQuotaCounter({ storage });
const counters=[{kind:'login-account-ip',digest:'a'.repeat(64)}];
const request=()=>new Request('https://admin-quota.internal/check',{method:'POST',body:JSON.stringify({counters})});
const concurrent=await Promise.all(Array.from({length:25},()=>counter.fetch(request())));
assert.equal(concurrent.filter(r=>r.status===200).length,10);
assert.equal(concurrent.filter(r=>r.status===429).length,15);
assert.equal(concurrent.find(r=>r.status===429).headers.get('Retry-After'),'600');
counter=new AdminQuotaCounter({ storage });
assert.equal((await counter.fetch(request())).status,429,'persistent state must survive instance restart');
await counter.alarm();
assert.equal((await counter.fetch(request())).status,429,'stale alarm must not erase live admissions');
now+=600000;
assert.equal((await counter.fetch(request())).status,200,'rolling window expires exactly at boundary');
assert.equal((await counter.fetch(new Request('https://admin-quota.internal/check',{method:'POST',body:JSON.stringify({counters:[{kind:'arbitrary',digest:'a'.repeat(64)}]})}))).status,400);
assert.equal((await counter.fetch(new Request('https://admin-quota.internal/check',{method:'POST',body:JSON.stringify({counters:[...counters,...counters]})}))).status,400);
failure=true;
assert.equal((await counter.fetch(request())).status,503);
failure=false;
const env={ ADMIN_QUOTA_HMAC_KEY:'local-only-quota-fixture-'.repeat(3),ADMIN_QUOTA:{ fetch:request=>counter.fetch(request) } };
assert.equal(await checkAdminQuota(request(),env,[{kind:'entry',identity:'192.0.2.1'}]),null);
assert.equal((await checkAdminQuota(request(),{},[{kind:'entry',identity:'192.0.2.1'}])).status,503);
assert.equal((await checkAdminQuota(request(),{...env,ADMIN_QUOTA:{fetch:async()=>new Response('{"allowed":false}',{status:200})}},[{kind:'entry',identity:'192.0.2.1'}])).status,503);
let submittedCounters;
const pairedQuotaEnv = {
  ADMIN_QUOTA_HMAC_KEY: env.ADMIN_QUOTA_HMAC_KEY,
  ADMIN_QUOTA: { fetch: async quotaRequest => {
    submittedCounters = (await quotaRequest.json()).counters;
    return new Response('{"allowed":true}', { status: 200 });
  } },
};
assert.equal(await checkAdminQuota(request(), pairedQuotaEnv, [
  { kind: 'login-ip', identity: '192.0.2.1' },
  { kind: 'login-account-ip', identity: 'synthetic@local.test:192.0.2.1', shardIdentity: '192.0.2.1' },
]), null);
assert.equal(submittedCounters[1].shard, submittedCounters[0].digest,
  'account identity must be partitioned under the HMAC of its IP quota');
assert.equal(JSON.stringify(submittedCounters).includes('synthetic@local.test'), false);
assert.equal(JSON.stringify(data).includes('192.0.2.1'),false);
assert.equal(JSON.stringify(data).includes(env.ADMIN_QUOTA_HMAC_KEY),false);
for (const [kind, limit] of [['rpc-read',120],['rpc-write',30]]) {
  const rpcRequest = () => new Request('https://admin-quota.internal/check', {
    method:'POST', body:JSON.stringify({counters:[{kind,digest:kind==='rpc-read'?'b'.repeat(64):'c'.repeat(64)}]}),
  });
  for (let index=0;index<limit;index+=1) assert.equal((await counter.fetch(rpcRequest())).status,200);
  const exceededRpc = await counter.fetch(rpcRequest());
  assert.equal(exceededRpc.status,429,`${kind} must enforce the accepted per-actor limit`);
  assert.equal(Number(exceededRpc.headers.get('Retry-After'))>=1,true);
}
assert.equal(trustedQuotaIp(new Request('https://admin.local',{headers:{'X-Forwarded-For':'192.0.2.1'}})),null);
assert.equal(trustedQuotaIp(new Request('https://admin.local',{headers:{'CF-Connecting-IP':'999.1.1.1'}})),null);

const quotaObjects = new Map();
const objectNames = new Set();
const namespace = {
  idFromName(name) { objectNames.add(name); return name; },
  get(id) {
    if (!quotaObjects.has(id)) {
      const objectData = {};
      const objectStorage = {
        async transaction(callback) {
          const staged = structuredClone(objectData);
          const result = await callback({
            get: async key => staged[key],
            put: async (key, value) => { staged[key] = value; },
            delete: async key => { const existed = Object.hasOwn(staged, key); delete staged[key]; return existed; },
          });
          for (const key of Object.keys(objectData)) delete objectData[key];
          Object.assign(objectData, staged);
          return result;
        },
        setAlarm: async () => {},
        inspect: () => objectData,
      };
      quotaObjects.set(id, { counter: new AdminQuotaCounter({ storage: objectStorage }), storage: objectStorage });
    }
    return { fetch: request => quotaObjects.get(id).counter.fetch(request) };
  },
};
const ipDigest = 'f'.repeat(64);
const loginRequest = (accountDigest, includeShard = true) => new Request('https://admin-quota.internal/check', {
  method: 'POST',
  body: JSON.stringify({ counters: [
    { kind: 'login-ip', digest: ipDigest },
    { kind: 'login-account-ip', digest: accountDigest, ...(includeShard ? { shard: ipDigest } : {}) },
  ] }),
});
const legacyAccountDigest = 'a'.repeat(64);
assert.equal((await AdminQuotaWorker.fetch(loginRequest(legacyAccountDigest, false), {
  ADMIN_QUOTA_COUNTER: namespace,
})).status, 200, 'the previous BFF payload must remain accepted during compatibility');
assert.equal(objectNames.size, 1, 'the previous BFF payload must infer the same IP Durable Object shard');
for (let index = 1; index <= 19; index += 1) {
  const digest = index.toString(16).padStart(64, '0');
  assert.equal((await AdminQuotaWorker.fetch(loginRequest(digest), { ADMIN_QUOTA_COUNTER: namespace })).status, 200);
}
assert.equal(objectNames.size, 1, 'arbitrary login identities for one IP must share one Durable Object shard');
const deniedDigest = 'e'.repeat(64);
assert.equal((await AdminQuotaWorker.fetch(loginRequest(deniedDigest), { ADMIN_QUOTA_COUNTER: namespace })).status, 429);
assert.equal(objectNames.size, 1, 'an IP-blocked request must not allocate an account-specific Durable Object');
const onlyQuotaObject = [...quotaObjects.values()][0];
const ledgerBeforeExpiry = onlyQuotaObject.storage.inspect().ledger;
assert.equal(Object.keys(ledgerBeforeExpiry).length, 21, 'the IP shard retains at most admitted IP/account keys');
assert.equal(Object.hasOwn(ledgerBeforeExpiry, `login-account-ip:${deniedDigest}`), false);
assert.equal((await AdminQuotaWorker.fetch(new Request('https://admin-quota.internal/check', {
  method: 'POST', body: JSON.stringify({ counters: [{ kind: 'login-account-ip', digest: deniedDigest }] }),
}), { ADMIN_QUOTA_COUNTER: namespace })).status, 400, 'account quotas require their paired IP counter');
assert.equal((await AdminQuotaWorker.fetch(new Request('https://admin-quota.internal/check', {
  method: 'POST', body: JSON.stringify({ counters: [
    { kind: 'login-ip', digest: 'a'.repeat(64) },
    { kind: 'login-account-ip', digest: 'b'.repeat(64) },
    { kind: 'login-account-ip', digest: 'c'.repeat(64) },
  ] }),
}), { ADMIN_QUOTA_COUNTER: namespace })).status, 400, 'one request cannot multiply account keys within an IP shard');
assert.equal((await AdminQuotaWorker.fetch(new Request('https://admin-quota.internal/check', {
  method: 'POST', body: JSON.stringify({ counters: [
    { kind: 'login-ip', digest: '2'.repeat(64) },
    { kind: 'login-ip', digest: '3'.repeat(64) },
  ] }),
}), { ADMIN_QUOTA_COUNTER: namespace })).status, 400, 'one request cannot fan out to multiple IP quota shards');
const originalAccountDigest = 'd'.repeat(64);
const isolatedLoginCounters = isolateQuotaCounters([
  { kind: 'login-ip', digest: ipDigest },
  { kind: 'login-account-ip', digest: originalAccountDigest, shard: ipDigest },
], 7);
assert.equal(isolatedLoginCounters[0].digest, isolatedLoginCounters[1].shard,
  'the local runtime namespace reset must preserve paired counter routing');
assert.notEqual(isolatedLoginCounters[0].digest, ipDigest, 'the IP digest must be isolated from other test epochs');
assert.notEqual(isolatedLoginCounters[1].digest, originalAccountDigest, 'the account digest must be isolated from other test epochs');
assert.notEqual(isolatedLoginCounters[1].shard, ipDigest, 'the account shard must be isolated with the matching IP digest');
now += 600001;
await [...quotaObjects.values()][0].counter.alarm();
assert.equal(Object.hasOwn(onlyQuotaObject.storage.inspect(), 'ledger'), false, 'expired ledger storage is deleted atomically');
assert.equal((await AdminQuotaWorker.fetch(loginRequest(deniedDigest), { ADMIN_QUOTA_COUNTER: namespace })).status, 200);
console.log(JSON.stringify({result:'PASS',concurrentRequests:25,admitted:10,rpcReadLimit:120,rpcWriteLimit:30,
  accountIdentitiesPerIp:20,accountShardObjects:objectNames.size,expiredLedgerDeleted:true,
  persistence:'emulated',runtime:'unit-intercepted'}));
