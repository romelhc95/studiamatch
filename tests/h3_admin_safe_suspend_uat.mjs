import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import vm from 'node:vm';
const root=new URL('..',import.meta.url);
const require=createRequire(new URL('web/package.json',root));
const ts=require('typescript');
const module={exports:{}};
let bffCalls=0;let publicCalls=0;
vm.runInNewContext(ts.transpileModule(await readFile(new URL('web/functions/_middleware.ts',root),'utf8'),{
  compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022},
}).outputText,{module,exports:module.exports,Headers,Response,URL,Set,require:()=>({routeAdminBff:async()=>{bffCalls++;return null;}})});
const onRequest=module.exports.onRequest;
const env={ADMIN_ALLOWED_HOSTS:'admin.local.test',ADMIN_BFF_SAFE_SUSPEND:'true'};
for(const path of ['/admin/','/admin/login/','/admin/auth/callback/?token_hash=local-fixture','/api/admin/session','/api/admin/rpc']) {
  const result=await onRequest({request:new Request(`https://admin.local.test${path}`,{
    headers:{Cookie:'__Host-studiamatch-admin-auth.0=local-fixture; unrelated=keep'},
  }),env,next:async()=>{publicCalls++;return new Response('static');}});
  assert.equal(result.status,503);
  assert.match(result.headers.get('set-cookie'),/__Host-studiamatch-admin-auth\.0=; Path=\/; Max-Age=0; Secure; HttpOnly/);
  assert(!result.headers.get('set-cookie').includes('unrelated'));
  assert.equal(result.headers.get('Retry-After'),'60');
}
for(const path of ['/%61dmin/','/%2561dmin/','/%2525252561dmin/','/%252e/admin/','/admin/%61uth/callback','/api/%61dmin/session','/%25252fadmin/','//admin/']) {
  const result=await onRequest({request:new Request(`https://admin.local.test${path}`),env,next:async()=>{publicCalls++;return new Response('static');}});
  assert.equal(result.status,404,`${path} must not reach static assets or bypass the Admin perimeter`);
  assert.equal(await result.text(),'Not found');
}
const pub=await onRequest({request:new Request('https://studiamatch.com/courses/'),env,next:async()=>{publicCalls++;return new Response('public static');}});
assert.equal(pub.status,200);assert.equal(await pub.text(),'public static');
const blocked=await onRequest({request:new Request('https://studiamatch.com/admin/'),env,next:async()=>new Response('bad')});
assert.equal(blocked.status,404,'public perimeter must not disclose Admin during rollback');
const encodedPublic=await onRequest({request:new Request('https://admin.local.test/%63ourses/'),env,next:async()=>{publicCalls++;return new Response('static');}});
assert.equal(encodedPublic.status,200,'encoded public routes must remain available');
assert.equal(bffCalls,0);assert.equal(publicCalls,2);
const redirect=await onRequest({request:new Request('https://admin.local.test/admin/edit?id=local-fixture'),
  env:{...env,ADMIN_BFF_SAFE_SUSPEND:'false'},next:async()=>new Response('static')});
assert.equal(redirect.status,302);
assert.equal(redirect.headers.get('Location'),'/admin/edit/?id=local-fixture','slash normalization must preserve editor identity');
console.log(JSON.stringify({result:'PASS',adminSuspendCases:5,encodedAdminAliasesRejected:8,publicPagesPreserved:true,sessionCookiesCleared:true,runtime:'middleware fixture'}));
