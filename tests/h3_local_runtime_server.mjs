// Local-only UAT fixture: actual compiled middleware + actual DO service, mock
// Auth and disposable PG17. Namespace isolation happens at test reset boundaries.
import { createRequire } from 'node:module';
import { readFile,rm,stat,mkdtemp } from 'node:fs/promises';
import { resolve,join,extname } from 'node:path';
import { tmpdir } from 'node:os';
import { createServer,request as httpRequest } from 'node:http';
import assert from 'node:assert/strict';
import { isolateQuotaCounters } from './h3_local_runtime_quota_fixture.mjs';
const root=resolve(process.env.H3_RUNTIME_ROOT || '/app');
const tools=createRequire(join(process.env.H3_QUOTA_TOOLS || '/tmp/h3-quota-runtime-tools','package.json'));
const { Miniflare }=tools('miniflare');const { build }=tools('esbuild');
const reset=process.env.H3_TEST_RESET_TOKEN;
assert(reset && /^h3_final_uat_/.test(process.env.MOCK_DB_NAME || ''),'isolated local UAT required');
const hmac=process.env.MOCK_QUOTA_HMAC_KEY;assert(hmac && hmac.length>=32);
function portFromEnv(name,fallback){
  const value=Number(process.env[name]||fallback);
  assert(Number.isInteger(value)&&value>=1024&&value<=65535,`${name} must be a valid local TCP port`);
  return value;
}
const runtimePort=portFromEnv('H3_LOCAL_RUNTIME_PORT',3330);
const mockProxyPort=portFromEnv('H3_LOCAL_MOCK_PROXY_PORT',3331);
const mockUpstreamPort=portFromEnv('H3_LOCAL_MOCK_UPSTREAM_PORT',3332);
const perimeterPort=portFromEnv('H3_LOCAL_PERIMETER_PORT',3333);
function safeErrorCode(error){
  const candidate=error && typeof error==='object'
    ? (error.code || error.cause?.code || error.name)
    : 'UNKNOWN';
  return typeof candidate==='string' && /^[A-Za-z][A-Za-z0-9_]{0,63}$/.test(candidate)
    ? candidate.toUpperCase().replace(/[^A-Z0-9_]/g,'_')
    : 'UNKNOWN';
}
const hopByHopHeaders=new Set(['connection','keep-alive','proxy-authenticate','proxy-authorization','te','trailer','transfer-encoding','upgrade','host','content-length']);
function forwardedHeaders(input,bodyLength){
  const excluded=new Set(hopByHopHeaders);
  for(const name of String(input.connection||'').split(',')){
    const token=name.trim().toLowerCase();
    if(/^[a-z0-9!#$%&'*+.^_`|~-]+$/.test(token)) excluded.add(token);
  }
  const output={};
  for(const [name,value] of Object.entries(input)) if(!excluded.has(name.toLowerCase()) && value!==undefined) output[name]=value;
  output['content-length']=String(bodyLength);
  return output;
}
function requestMock(req,body){
  return new Promise((resolve,reject)=>{
    const path=req.url;
    if(typeof path!=='string' || !path.startsWith('/') || path.startsWith('//') || /[\r\n]/.test(path)){
      reject(Object.assign(new Error('invalid local fixture path'),{code:'INVALID_LOCAL_PATH'}));return;
    }
    const upstream=httpRequest({hostname:'127.0.0.1',port:mockUpstreamPort,path,method:req.method,headers:forwardedHeaders(req.headers,body.length)},response=>{
      const chunks=[];
      response.on('data',chunk=>chunks.push(chunk));
      response.on('error',reject);
      response.on('aborted',()=>reject(Object.assign(new Error('local mock response aborted'),{code:'LOCAL_MOCK_RESPONSE_ABORTED'})));
      response.on('end',()=>{
        const responseBody=Buffer.concat(chunks);
        const headers=forwardedHeaders(response.headers,responseBody.length);
        if(response.statusCode===204 || response.statusCode===304) delete headers['content-length'];
        resolve({status:response.statusCode||502,headers,body:responseBody});
      });
    });
    upstream.setTimeout(10000,()=>upstream.destroy(Object.assign(new Error('local mock timeout'),{code:'LOCAL_MOCK_TIMEOUT'})));
    upstream.on('error',reject);
    if(body.length) upstream.write(body);
    upstream.end();
  });
}
const assetRoot=resolve(process.env.H3_STATIC_ROOT || join(root,'web/out'));let epoch=0;let mf;
const bridge=await build({stdin:{contents:"import {onRequest} from './web/functions/_middleware.ts'; export default {fetch(request,env){return onRequest({request,env,next:()=>env.ASSETS.fetch(request)})}};",
  resolveDir:root,sourcefile:'local-runtime-bridge.ts'},bundle:true,write:false,format:'esm',platform:'browser',target:'es2022'});
const quota=await build({entryPoints:[join(root,'workers/admin-quota/index.ts')],bundle:true,write:false,format:'esm',platform:'browser',target:'es2022'});
const persistent=await mkdtemp(join(tmpdir(),'h3-final-uat-runtime-'));
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.woff2':'font/woff2','.ico':'image/x-icon'};
async function assets(request) {
  try {
    const path=decodeURIComponent(new URL(request.url).pathname);
    let file=resolve(assetRoot,`.${path}`);
    if(!file.startsWith(`${assetRoot}/`) && file!==assetRoot) return new Response('Not found',{status:404});
    if((await stat(file)).isDirectory()) file=join(file,'index.html');
    return new Response(await readFile(file),{headers:{'Content-Type':mime[extname(file)] || 'application/octet-stream'}});
  } catch {return new Response('Not found',{status:404});}
}
const bindings={SUPABASE_URL:`http://127.0.0.1:${mockProxyPort}`,NEXT_SUPABASE_PUBLISHABLE_KEY:['sb','publishable','localmock'].join('_'),
  ADMIN_BFF_ALLOW_LOCALHOST:'true',ADMIN_BFF_ALLOW_LOCAL_AUTH_MOCK:'true',ADMIN_ALLOWED_HOSTS:'localhost,127.0.0.1',
  ADMIN_SESSION_ACTIVITY_HMAC_KEY:'local-only-runtime-admin-activity-fixture-key-32-bytes',
  ADMIN_QUOTA_HMAC_KEY:hmac,ADMIN_RPC_GATEWAY_HMAC_KEY:'local-only-runtime-rpc-gateway-fixture-key-32-bytes',
  ADMIN_RPC_GATEWAY_KEY_ID:'local-runtime-k1'};
mf=new Miniflare({port:runtimePort,host:'127.0.0.1',durableObjectsPersist:persistent,workers:[
  {name:'pages',modules:[{type:'ESModule',path:'pages.mjs',contents:bridge.outputFiles[0].text}],compatibilityDate:'2026-07-30',compatibilityFlags:['nodejs_compat'],
    bindings,serviceBindings:{ASSETS:assets,ADMIN_QUOTA:async request=>{
      const body=await request.json();
      // Each test owns a distinct local namespace; quotas remain active inside it.
      body.counters=isolateQuotaCounters(body.counters,epoch);
      return (await mf.getWorker('quota')).fetch('https://admin-quota.internal/check',{method:'POST',body:JSON.stringify(body)});
    }}},
  {name:'quota',script:quota.outputFiles[0].text,modules:true,compatibilityDate:'2026-07-30',
    durableObjects:{ADMIN_QUOTA_COUNTER:{className:'AdminQuotaCounter',useSQLite:true}}},
]});
const proxy=createServer(async(req,res)=>{
  let proxyPhase='read-request';
  let resetEpoch=null;
  try {
    const chunks=[];for await(const chunk of req) chunks.push(chunk);
    const body=Buffer.concat(chunks);
    if(req.url==='/__test/reset' && req.method==='POST' && req.headers['x-h3-test-token']===reset) {
      epoch++;
      resetEpoch=epoch;
    }
    proxyPhase='mock-http';
    const response=await requestMock(req,body);
    proxyPhase='write-response';
    res.writeHead(response.status,{
      ...response.headers,
      ...(resetEpoch!==null?{'x-h3-quota-fixture-epoch':String(resetEpoch)}:{}),
    });res.end(response.body);
  } catch (error) {console.error(`local-fixture-proxy|phase=${proxyPhase}|error_code=${safeErrorCode(error)}`);res.writeHead(502);res.end('Local fixture unavailable');}
});
const perimeter=createServer(async(req,res)=>{
  try {
    const host=req.headers.host==='localhost'?'localhost':'studiamatch.com';
    const url=new URL(req.url,`http://${host}`);
    const response=await (await mf.getWorker('pages')).fetch(url.href,{method:req.method,headers:req.headers});
    res.writeHead(response.status,Object.fromEntries(response.headers));res.end(Buffer.from(await response.arrayBuffer()));
  } catch (error) {console.error(`local-perimeter-proxy|error_code=${safeErrorCode(error)}`);res.writeHead(502);res.end('Local perimeter fixture unavailable');}
});
await Promise.all([mf.ready,new Promise(done=>proxy.listen(mockProxyPort,'127.0.0.1',done)),new Promise(done=>perimeter.listen(perimeterPort,'127.0.0.1',done))]);
console.log(JSON.stringify({ready:true,base:`http://localhost:${runtimePort}`,mock:`http://localhost:${mockProxyPort}`,perimeter:`http://localhost:${perimeterPort}`,persistent}));
process.on('SIGTERM',async()=>{proxy.close();perimeter.close();await mf.dispose();await rm(persistent,{recursive:true,force:true});process.exit(0);});
