#!/usr/bin/env bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly JIT='H3REQ1-C03-EDGE-USER-WORKER-TRANSPORT-R23-20261010'
readonly NETWORK='h3req1-c03-edge-transport-r23-20261010'
readonly TLS_VOLUME='h3req1-c03-edge-transport-tls-r23-20261010'
readonly GATEWAY='h3req1-c03-edge-transport-gateway-r23-20261010'
readonly PROBE='h3req1-c03-edge-transport-probe-r23-20261010'
readonly NODE_IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly EDGE_IMAGE='supabase/edge-runtime:v1.74.3_amd64@sha256:cc355c3d0e9c063a351cad56d1c4c52a3c4d85aff4e1fad9d91688e75f9aad09'
readonly RESULT='.context/evidencia/h3req1_c03_edge_transport_probe_r23_2026-10-10.txt'
readonly CA_ARCHIVE='.context/evidencia/h3req1_c03_edge_transport_ca_r23_2026-10-10.pem'
phase='preflight'
exec 3>&1
emit() { printf '%s\n' "$1" >> "$RESULT"; printf '%s\n' "$1" >&3; }
cd "$ROOT"
[[ "$(git branch --show-current)" == "$BRANCH" ]]
[[ "$(git rev-parse HEAD)" == "$HEAD" ]]
[[ ! -e "$RESULT" && ! -L "$RESULT" && ! -e "$CA_ARCHIVE" && ! -L "$CA_ARCHIVE" ]]
docker image inspect "$NODE_IMAGE" >/dev/null 2>&1
docker image inspect "$EDGE_IMAGE" >/dev/null 2>&1
exec >"$RESULT" 2>&1
emit "candidate=$ROOT branch=$BRANCH head=$HEAD"
emit "source_sha256=$(sha256sum tests/h3req1_c03_edge_transport_gateway_r20.mjs tests/h3req1_c03_edge_transport_main_r20.ts tests/h3req1_c03_edge_transport_worker_r20.ts .context/evidencia/h3req1_c03_edge_auth_transport_probe_v2_2026-10-10.ts | awk '{printf "%s:%s ", $2, $1}')"
phase='create-internal-network-and-volume'
network_id="$(docker network create --internal --label "com.studiamatch.h3.c03.jit=$JIT" "$NETWORK")"
[[ "$network_id" =~ ^[a-f0-9]{64}$ ]]
[[ "$(docker volume create --label "com.studiamatch.h3.c03.jit=$JIT" "$TLS_VOLUME")" == "$TLS_VOLUME" ]]
docker run --pull=never --platform linux/amd64 --log-driver none -d --name "$GATEWAY" --label "com.studiamatch.h3.c03.jit=$JIT" \
  --network "$NETWORK" --network-alias local.supabase.co --read-only --memory=256m --memory-swap=256m --cpus=1 --pids-limit=128 \
  --tmpfs /diagnostic:rw,noexec,nosuid,size=16m --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --mount "type=volume,src=$TLS_VOLUME,dst=/certs" --env CERTS_ROOT=/certs --entrypoint sh "$NODE_IMAGE" -lc 'sleep 180' >/dev/null
gateway_id="$(docker inspect -f '{{.Id}}' "$GATEWAY")"
docker exec -i "$gateway_id" sh -c 'cat > /diagnostic/gateway.mjs' < tests/h3req1_c03_edge_transport_gateway_r20.mjs
docker exec -d "$gateway_id" node /diagnostic/gateway.mjs
gateway_ready=0
for _ in {1..20}; do
  if docker exec "$gateway_id" node -e 'fetch("http://127.0.0.1:5544/healthz",{signal:AbortSignal.timeout(1000)}).then(async r=>{const j=await r.json();if(r.status===200&&j.ready===true)process.exit(0);process.exit(1)}).catch(()=>process.exit(1))' >/dev/null 2>&1; then gateway_ready=1; break; fi
  sleep 1
done
[[ "$gateway_ready" == 1 ]]
emit 'phase=tls-gateway|error_code=READY'
docker cp "$gateway_id:/certs/ca.pem" "$CA_ARCHIVE" >/dev/null
ca_sha="$(sha256sum "$CA_ARCHIVE" | cut -d' ' -f1)"
[[ -s "$CA_ARCHIVE" && ! -L "$CA_ARCHIVE" && "$ca_sha" =~ ^[a-f0-9]{64}$ ]]
emit "phase=synthetic-ca|error_code=ARCHIVED|sha256=$ca_sha"

phase='start-edge-user-worker'
docker run --pull=never --platform linux/amd64 --log-driver none -d --name "$PROBE" --label "com.studiamatch.h3.c03.jit=$JIT" \
  --network "$NETWORK" --network-alias h3req1-c03-edge-transport-probe-r23 --read-only --memory=512m --memory-swap=512m --cpus=1 --pids-limit=128 \
  --tmpfs /diagnostic-main:rw,noexec,nosuid,size=16m --tmpfs /diagnostic-worker:rw,noexec,nosuid,size=16m --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --mount "type=volume,src=$TLS_VOLUME,dst=/run/c03-certs,readonly" \
  --env DENO_CERT=/run/c03-certs/ca.pem --env DENO_TLS_CA_STORE=mozilla,system \
  --entrypoint sh "$EDGE_IMAGE" -lc 'sleep 180' >/dev/null
probe_id="$(docker inspect -f '{{.Id}}' "$PROBE")"
docker exec -i "$probe_id" sh -c 'cat > /diagnostic-main/index.ts' < tests/h3req1_c03_edge_transport_main_r20.ts
docker exec -i "$probe_id" sh -c 'cat > /diagnostic-worker/index.ts' < tests/h3req1_c03_edge_transport_worker_r20.ts
probe_ca_sha="$(docker exec "$probe_id" sh -c 'sha256sum /run/c03-certs/ca.pem 2>/dev/null | cut -d" " -f1')"
[[ "$probe_ca_sha" == "$ca_sha" ]]
emit 'phase=edge-ca-mount|error_code=CONTENT_MATCH'
docker exec -d "$probe_id" edge-runtime start --main-service /diagnostic-main -p 9000
phase='edge-user-worker-readiness'
probe_ready=0
for _ in {1..20}; do
  if docker exec "$gateway_id" node -e 'fetch("http://h3req1-c03-edge-transport-probe-r23:9000/healthz",{signal:AbortSignal.timeout(1000)}).then(async r=>{const j=await r.json();if(r.status===200&&j.phase==="edge-main"&&j.code==="READY")process.exit(0);process.exit(1)}).catch(()=>process.exit(1))' >/dev/null 2>&1; then probe_ready=1; break; fi
  sleep 1
done
[[ "$probe_ready" == 1 ]]
emit 'phase=edge-user-worker-readiness|error_code=READY'

phase='one-edge-user-worker-auth-transport-request'
probe_result="$(docker exec "$gateway_id" node -e 'fetch("http://h3req1-c03-edge-transport-probe-r23:9000/probe",{signal:AbortSignal.timeout(10000)}).then(async r=>{let j;try{j=await r.json()}catch{console.log("phase=edge-user-worker-auth|error_code=INVALID_RESPONSE");process.exitCode=1;return}const a=new Set(["HTTP_401","HTTP_200","TLS_UNKNOWN_ISSUER","TLS_CERTIFICATE_ERROR","DNS_FAILURE","CONNECT_REFUSED","CONNECT_RESET","CONNECT_TIMEOUT","TIMEOUT","FETCH_FAILED","WORKER_START_FAILED"]);if(j.phase!=="edge-user-worker"||!a.has(j.code)){console.log("phase=edge-user-worker-auth|error_code=OUTPUT_REJECTED");process.exitCode=1;return}console.log("phase=edge-user-worker-auth|error_code="+j.code)}).catch(()=>{console.log("phase=edge-user-worker-auth|error_code=PROBE_CLIENT_FAILED");process.exitCode=1})' 2>/dev/null)"
[[ "$probe_result" =~ ^phase=edge-user-worker-auth\|error_code=(HTTP_401|HTTP_200|TLS_UNKNOWN_ISSUER|TLS_CERTIFICATE_ERROR|DNS_FAILURE|CONNECT_REFUSED|CONNECT_RESET|CONNECT_TIMEOUT|TIMEOUT|FETCH_FAILED|WORKER_START_FAILED|INVALID_RESPONSE|OUTPUT_REJECTED|PROBE_CLIENT_FAILED)$ ]]
emit "$probe_result"
counters="$(docker exec "$gateway_id" node -e 'fetch("http://127.0.0.1:5544/counters").then(async r=>{const j=await r.json();if(r.status!==200||!Number.isInteger(j.authUserGet)||!Number.isInteger(j.otherRequests)){console.log("phase=gateway-observation|error_code=INVALID_COUNTERS");process.exitCode=1;return}console.log("phase=gateway-observation|auth_user_get="+j.authUserGet+"|other_requests="+j.otherRequests)})' 2>/dev/null)"
[[ "$counters" =~ ^phase=gateway-observation\|auth_user_get=[0-9]+\|other_requests=[0-9]+$ ]]
emit "$counters"
[[ "$counters" == 'phase=gateway-observation|auth_user_get=1|other_requests=0' ]]

phase='archive-ca-and-clean-exact-fixtures'
for name in "$PROBE" "$GATEWAY"; do
  metadata="$(docker inspect -f '{{.Id}}|{{.Name}}|{{index .Config.Labels "com.studiamatch.h3.c03.jit"}}' "$name")"
  [[ "$metadata" =~ ^[a-f0-9]{64}\|/$name\|$JIT$ ]]
  docker stop --time 3 "$name" >/dev/null
  docker rm "$name" >/dev/null
done
[[ -z "$(docker ps --filter "network=$NETWORK" --format '{{.ID}}')" ]]
network_state="$(docker network inspect -f '{{.Id}}|{{.Internal}}|{{len .Containers}}|{{index .Labels "com.studiamatch.h3.c03.jit"}}' "$network_id")"
[[ "$network_state" == "$network_id|true|0|$JIT" ]]
docker network rm "$network_id" >/dev/null
volume_state="$(docker volume inspect -f '{{.Driver}}|{{index .Labels "com.studiamatch.h3.c03.jit"}}' "$TLS_VOLUME")"
[[ "$volume_state" == "local|$JIT" ]]
[[ -z "$(docker ps --filter "volume=$TLS_VOLUME" --format '{{.ID}}')" ]]
docker volume rm "$TLS_VOLUME" >/dev/null
emit 'phase=fixture-cleanup|error_code=EXACT_RESOURCES_REMOVED'
emit 'phase=edge-user-worker-transport|error_code=COMPLETE'
trap - ERR
