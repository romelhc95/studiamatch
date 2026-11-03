// Docker-only local PostgREST wire test; local JWT never printed or persisted.
import assert from 'node:assert/strict';
import { createHmac, randomUUID } from 'node:crypto';
import { createRequire } from 'node:module';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const { createClient }=require('@supabase/supabase-js');
const endpoint=process.env.H3_POSTGREST_TEST_URL;
const secret=process.env.H3_POSTGREST_TEST_SECRET;
const gatewaySecret=process.env.H3_POSTGREST_TEST_RPC_SECRET;
const gatewayKeyId=process.env.H3_POSTGREST_TEST_RPC_KEY_ID || 'local-pg17-k1';
const projectRef=process.env.H3_POSTGREST_TEST_PROJECT_REF || 'local';
const localDockerEndpoint=typeof endpoint==='string' && (
  endpoint==='http://127.0.0.1:3233'
  || endpoint==='http://h3req1-postgrest-jit-20261005:3233'
);
assert(localDockerEndpoint,'local Docker URL required');
assert(secret && secret.length>=32,'local signing fixture required');
assert(gatewaySecret && Buffer.byteLength(gatewaySecret)>=32,'separate local RPC gateway fixture required');
const subject='72000000-0000-0000-0000-000000000001';
const encode=value=>Buffer.from(JSON.stringify(value)).toString('base64url');
const unsigned=`${encode({alg:'HS256',typ:'JWT'})}.${encode({role:'authenticated',sub:subject,aal:'aal1',exp:Math.floor(Date.now()/1000)+600})}`;
const jwt=`${unsigned}.${createHmac('sha256',secret).update(unsigned).digest('base64url')}`;
let lastHeaders;
async function signedGatewayFetch(input,init={}) {
  const url=new URL(typeof input==='string'?input:input.url || String(input));
  const headers=new Headers(input instanceof Request?input.headers:undefined);
  new Headers(init.headers).forEach((value,name)=>headers.set(name,value));
  const rpc=/^\/rest\/v1\/rpc\/([a-z][a-z0-9_]*)$/.exec(url.pathname);
  let fetchBody=init.body;
  if(rpc) {
    const method=(init.method || (input instanceof Request?input.method:'GET')).toUpperCase();
    const authorization=headers.get('authorization') || '';
    assert.equal(method,'POST');
    assert.equal(authorization,`Bearer ${jwt}`);
    const actor=JSON.parse(Buffer.from(jwt.split('.')[1],'base64url').toString('utf8')).sub;
    const args=typeof init.body==='string' ? JSON.parse(init.body) : {};
    const signedPayload=JSON.stringify(args);
    const issuedAt=String(Math.floor(Date.now()/1000));
    const nonce=randomUUID();
    const wrapper='admin_signed_rpc';
    const canonical=['studiamatch-admin-rpc-v1',projectRef,method,wrapper,actor,issuedAt,nonce,gatewayKeyId].join('\n');
    const signature=createHmac('sha256',gatewaySecret).update(canonical).digest('hex');
    const payloadCanonical=['studiamatch-admin-rpc-payload-v1',projectRef,method,wrapper,rpc[1],actor,issuedAt,nonce,gatewayKeyId,signedPayload].join('\n');
    const payloadSignature=createHmac('sha256',gatewaySecret).update(payloadCanonical).digest('hex');
    headers.set('x-studiamatch-admin-rpc-key-id',gatewayKeyId);
    headers.set('x-studiamatch-admin-rpc-actor',actor);
    headers.set('x-studiamatch-admin-rpc-issued-at',issuedAt);
    headers.set('x-studiamatch-admin-rpc-nonce',nonce);
    headers.set('x-studiamatch-admin-rpc-signature',signature);
    headers.set('x-studiamatch-admin-rpc-payload-signature',payloadSignature);
    fetchBody=JSON.stringify({p_rpc_name:rpc[1],p_args:args,p_signed_payload:signedPayload});
    url.pathname=url.pathname.replace(/\/rpc\/[a-z][a-z0-9_]*$/,'/rpc/admin_signed_rpc');
  }
  url.pathname=url.pathname.replace(/^\/rest\/v1/, '');
  return fetch(url,{...init,body:fetchBody,headers,redirect:'manual'});
}
const client=createClient(endpoint,['sb','publishable','localfixture'].join('_'),{
  auth:{persistSession:false,autoRefreshToken:false},
  global:{headers:{Authorization:`Bearer ${jwt}`},fetch:async(input,init)=>{
    const url=new URL(typeof input==='string'?input:input.url || String(input));
    assert.equal(url.origin,endpoint);assert(url.pathname.startsWith('/rest/v1/rpc/'));
    const response=await signedGatewayFetch(input,init);
    lastHeaders=new Headers(response.headers);return response;
  }},
});
for(const rpc of ['admin_current_user_role','admin_get_course_queue']) {
  const directUrl=new URL(`${endpoint}/rest/v1/rpc/${rpc}`);
  directUrl.pathname=directUrl.pathname.replace(/^\/rest\/v1/, '');
  const response=await fetch(directUrl,{
    method:'POST',headers:{apikey:['sb','publishable','localfixture'].join('_'),Authorization:`Bearer ${jwt}`,'Content-Type':'application/json'},body:'{}',redirect:'manual',
  });
  assert.equal(response.status,403,`unsigned direct ${rpc} must be rejected before SQL RPC execution`);
  const payload=await response.json();
  assert.equal(payload.code,'rpc_signed_wrapper_required');
}
const partialProof=await fetch(new URL(`${endpoint}/rpc/admin_signed_rpc`),{
  method:'POST',headers:{apikey:['sb','publishable','localfixture'].join('_'),Authorization:`Bearer ${jwt}`,
    'Content-Type':'application/json','x-studiamatch-admin-rpc-key-id':gatewayKeyId},
  body:JSON.stringify({p_rpc_name:'admin_current_user_role',p_args:{},p_signed_payload:'{}'}),redirect:'manual',
});
assert.equal(partialProof.status,403,'partially signed direct RPC must be rejected');
assert.equal((await partialProof.json()).code,'rpc_signature_invalid');
for(const alias of [
  '/rpc/%61dmin_signed_rpc',
  '/%72pc/admin_signed_rpc',
  '/rpc/ADMIN_signed_rpc',
]) {
  const aliasUrl=new URL(`${endpoint}${alias}`);
  const response=await fetch(aliasUrl,{
    method:'POST',headers:{apikey:['sb','publishable','localfixture'].join('_'),Authorization:`Bearer ${jwt}`,'Content-Type':'application/json'},body:'{}',redirect:'manual',
  });
  assert.equal(response.ok,false,`unsigned path alias ${alias} must not invoke an Admin RPC`);
}
const denied=await client.rpc('admin_update_course',{
  p_course_id:'20000000-0000-0000-0000-000000000001',p_manual_overrides:{},p_version:0,p_reason:'local wire quota test',
});
assert.equal(denied.status,403,'MFA rejection must propagate failing HTTP status');
assert(denied.error,'SDK must see rejection rather than successful data');
assert.equal(denied.error[0]?.error,'mfa_required');
for(let i=0;i<120;i++) {
  const result=await client.rpc('admin_current_user_role');
  assert.equal(result.status,200);assert.equal(result.data,'admin');
}
const exceeded=await client.rpc('admin_current_user_role',{});
assert.equal(exceeded.status,429,'signed RPC must share actor read quota');
assert.equal(exceeded.error?.code,'quota_rate_limited');
assert(Number(lastHeaders.get('Retry-After'))>=1 && Number(lastHeaders.get('Retry-After'))<=60);
const forbidden=await client.rpc('admin_invitation_request_admit',{p_actor_user_id:subject});
assert.equal(forbidden.status,403,'authenticated cannot invoke service-only admission');
console.log(JSON.stringify({result:'PASS',runtime:'PostgREST HTTP + installed SDK',mfaStatus:denied.status,readAdmissions:120,
  deniedLegacyStatus:exceeded.status,serviceOnly:true}));
