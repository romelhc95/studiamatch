# H3REQ1 G03 — inventario sanitizado de configuración TypeScript (V1 one-shot)

Estado: preparado; requiere aprobación independiente. No ejecutado.

## Propósito

El r9 TSC V1 terminó con NODE_HEAP_LIMIT, exit 134, bajo el límite existente de 512 MiB. No atribuyó el problema a un tipo o archivo. Este diagnóstico diferente no repite el typecheck: consulta una vez tsc --showConfig sobre el snapshot fijado y emite solo cantidades agregadas de raíces por categoría, rutas repetidas e includes duplicados. El JSON y las rutas permanecen en memoria; no se imprimen ni se guardan. Esto comprobará si el include repetido de .next/types se convierte en raíces duplicadas o si existe una categoría raíz inesperada.

## Alcance

- Ubuntu WSL interactiva, romel no-root, TTY, una invocación, cero retries, timeout exterior de 90 s.
- Rama feat/h3req1-sync-20261002, HEAD 4eb4d877a50b012bb630a129bd0c74482c33be9c, WIP antes de ejecutar 55/286/0.
- Snapshot sanitizado de r9 V1: /tmp/h3req1-g03-validation-29d8fff9-r6. Verifica sus dos manifiestos y coteja 68 inputs con el candidato. Los tres archivos exclusivos del paquete se omiten de esa comparación, pero se verifican con su manifiesto interno.
- Imagen local studiamatch-h3req1:20261009-v3, digest sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63.
- Identidad/health de studiamatch-dev y volumen studiamatch_h3req1_node_modules se consultan read-only. No se lee Env, mounts ni secretos.
- Un contenedor temporal --rm --pull=never --network=none --read-only, UID 1001, sin capabilities, 512 MiB memoria/swap, 1 CPU, 64 PIDs. Snapshot y volumen de dependencias read-only; tmpfs de 16 MiB. No se monta el checkout original ni .env*; el proceso recibe entorno vacío.
- Ejecuta primero sintéticos del filtro y luego una consulta tsc --showConfig. No corre typecheck, typegen, ESLint, suites, F1, DB/SQL, instalación, pull/build, egress, cambios Docker persistentes, CI remoto ni deploy.
- Evidencia sanitizada: .context/evidencia/h3req1_g03_r9_tsc_project_config_v1_execution_2026-10-10.txt.
- Si se aprueba y ejecuta, Codex guardará únicamente las líneas sanitizadas del filtro y el exit code en esa ruta de evidencia.
- Drift, FAIL, salida fuera del contrato o timeout detiene el ciclo. --rm retira el contenedor temporal. No se edita tsconfig por analogía.

Filtro: tests/h3req1_docker_peer_substep_diag/r9_tsc_config_filter_v1.js
SHA-256: 0350da4e60b5866244f0068d93394dd6fdbce7badfdd90d9a98f42a885dd2f31

## Comando único

Ejecutar exactamente una vez desde Ubuntu WSL interactiva como romel no-root, con TTY y sandbox_permissions=require_escalated para el endpoint Docker Desktop. La aprobación debe fijar el SHA-256 de este JIT.

~~~bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly SNAPSHOT='/tmp/h3req1-g03-validation-29d8fff9-r6'
readonly FILTER="$ROOT/tests/h3req1_docker_peer_substep_diag/r9_tsc_config_filter_v1.js"
readonly FILTER_SHA='0350da4e60b5866244f0068d93394dd6fdbce7badfdd90d9a98f42a885dd2f31'
readonly IMAGE_TAG='studiamatch-h3req1:20261009-v3'
readonly IMAGE='sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63'
readonly CANDIDATE_ID='500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049'
readonly NODE_VOLUME='studiamatch_h3req1_node_modules'
readonly EVIDENCE="$ROOT/.context/evidencia/h3req1_g03_r9_tsc_project_config_v1_execution_2026-10-10.txt"
readonly PARTIAL="$EVIDENCE.partial"
fail() { printf 'phase=%s|error_code=%s\nexit=1\n' "$1" "$2"; exit 1; }
verify_hash() {
  local file="$1" expected="$2" line actual
  [[ -f "$file" && ! -L "$file" ]] || return 1
  line="$(/usr/bin/sha256sum -- "$file" 2>/dev/null)" || return 1
  actual="$(cut -d' ' -f1 <<< "$line")"
  [[ "$actual" == "$expected" ]]
}
(( EUID != 0 )) || fail preflight RUN_AS_WSL_USER
[[ -t 0 ]] || fail preflight INTERACTIVE_TTY_REQUIRED
[[ "$(uname -s)" == Linux && "$(uname -r | tr '[:upper:]' '[:lower:]')" == *microsoft* ]] || fail preflight WSL_REQUIRED
[[ "$(git -C "$ROOT" branch --show-current)" == feat/h3req1-sync-20261002 ]] || fail preflight BRANCH_MISMATCH
[[ "$(git -C "$ROOT" rev-parse HEAD)" == 4eb4d877a50b012bb630a129bd0c74482c33be9c ]] || fail preflight HEAD_MISMATCH
wip="$(git -C "$ROOT" status --porcelain=v1 | awk 'BEGIN{m=0;u=0;s=0} substr($0,1,2)=="??"{u++;next} {m++;if(substr($0,1,1)!=" ")s++} END{printf "%d/%d/%d",m,u,s}')"
[[ "$wip" == 55/286/0 ]] || fail preflight WIP_MISMATCH
verify_hash "$FILTER" "$FILTER_SHA" || fail preflight FILTER_HASH_MISMATCH
[[ -d "$SNAPSHOT" && ! -L "$SNAPSHOT" && ! -e "$EVIDENCE" && ! -e "$PARTIAL" ]] || fail preflight SNAPSHOT_OR_OUTPUT_PATH
verify_hash "$SNAPSHOT/r4-package.sha256" d10cc19b87adfff36f8092c97b59dc8fb4a247166c0dcbf8f0653dd9f2db6186 || fail preflight PACKAGE_MANIFEST_MISMATCH
verify_hash "$SNAPSHOT/inputs.sha256" c53e3321190646a2449e28b935711fc6f7b8425d1b19289f2374f4488eaff4c8 || fail preflight INPUT_MANIFEST_MISMATCH
(cd "$SNAPSHOT" && /usr/bin/sha256sum -c r4-package.sha256 >/dev/null 2>&1 && /usr/bin/sha256sum -c inputs.sha256 >/dev/null 2>&1) || fail preflight SNAPSHOT_MANIFEST_INVALID
checked=0
while read -r expected relative; do
  [[ -n "$expected" && -n "$relative" ]] || continue
  case "$relative" in ./fetch-linters.sh|./run-in-container.sh|./run-r8.sh) continue ;; esac
  verify_hash "$ROOT/$relative" "$expected" || fail preflight CANDIDATE_SOURCE_DRIFT
  checked=$((checked + 1))
done < "$SNAPSHOT/inputs.sha256"
[[ "$checked" == 68 ]] || fail preflight INPUT_COUNT_MISMATCH
endpoint="$(/usr/bin/docker --context default context inspect default --format '{{ .Endpoints.docker.Host }}' 2>/dev/null)" || fail docker-context CHECK_FAILED
[[ "$endpoint" == unix:///var/run/docker.sock ]] || fail docker-context ENDPOINT_MISMATCH
image_id="$(/usr/bin/docker --context default image inspect --format '{{.Id}}' "$IMAGE_TAG" 2>/dev/null)" || fail docker-context IMAGE_READ_FAILED
[[ "$image_id" == "$IMAGE" ]] || fail docker-context IMAGE_MISMATCH
candidate="$(/usr/bin/docker --context default inspect --format '{{.Id}}|{{.Image}}|{{.Config.Image}}|{{.State.Status}}|{{.State.Health.Status}}|{{index .Config.Labels "com.docker.compose.project"}}|{{index .Config.Labels "com.docker.compose.service"}}' studiamatch-dev 2>/dev/null)" || fail docker-context CANDIDATE_READ_FAILED
[[ "$candidate" == "$CANDIDATE_ID|$IMAGE|$IMAGE_TAG|running|healthy|studiamatch-h3req1|app" ]] || fail docker-context CANDIDATE_MISMATCH
/usr/bin/docker --context default volume inspect "$NODE_VOLUME" >/dev/null 2>&1 || fail docker-context VOLUME_UNAVAILABLE
if output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 90s /usr/bin/docker --context default run --rm --pull=never --network=none --read-only --user 1001:1001 --cap-drop=ALL --security-opt=no-new-privileges --memory=512m --memory-swap=512m --cpus=1 --pids-limit=64 --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m,uid=1001,gid=1001,mode=0700 --mount "type=bind,src=$SNAPSHOT,dst=/validation,readonly" --mount "type=bind,src=$FILTER,dst=/tsc-config-filter.js,readonly" --mount "type=volume,src=$NODE_VOLUME,dst=/app/web/node_modules,readonly" --workdir /validation/web --entrypoint /usr/bin/env "$IMAGE_TAG" -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/tmp /bin/bash -euo pipefail -c 'node /tsc-config-filter.js --self-test && /usr/bin/timeout --foreground --signal=TERM --kill-after=3s 70s /bin/bash -euo pipefail -c "/app/web/node_modules/.bin/tsc --showConfig --project /validation/web/tsconfig.json --pretty false 2>/dev/null | node /tsc-config-filter.js"' 2>/dev/null)"; then
  run_status=0
else
  run_status=$?
fi
if [[ -z "$output" ]]; then
  if (( run_status == 124 || run_status == 137 )); then
    output='phase=docker-run|error_code=TIMEOUT'
  else
    output='phase=docker-run|error_code=CHECK_FAILED'
  fi
fi
[[ "$(wc -c <<< "$output")" -le 8192 ]] || fail output OUTPUT_TOO_LARGE
readonly METRICS_RE='^metrics=files=[0-9]+\|unique_files=[0-9]+\|duplicate_paths=[0-9]+\|include_count=[0-9]+\|duplicate_includes=[0-9]+\|web_source=[0-9]+\|next_generated=[0-9]+\|functions=[0-9]+\|app=[0-9]+\|other=[0-9]+$'
safe=''
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  case "$line" in
    'phase=tsc-config-synthetics|error_code=OK'|'phase=tsc-config|error_code=OK'|'phase=tsc-config|error_code=OUTPUT_LIMIT'|'phase=tsc-config|error_code=CONFIG_OUTPUT_INVALID'|'phase=tsc-config|error_code=CONFIG_SHAPE_INVALID'|'phase=tsc-config|error_code=PROCESS_START_FAILED'|'phase=tsc-config|error_code=TSC_CONFIG_FAILED'|'phase=docker-run|error_code=TIMEOUT'|'phase=docker-run|error_code=CHECK_FAILED')
      safe+="$line"$'\n'
      ;;
    *)
      [[ "$line" =~ $METRICS_RE ]] || fail output OUTPUT_REJECTED
      safe+="$line"$'\n'
      ;;
  esac
done <<< "$output"
[[ -n "$safe" ]] || fail output NO_SANITIZED_OUTPUT
printf '%s' "$safe" > "$PARTIAL"
printf 'exit=%s\n' "$run_status" >> "$PARTIAL"
/usr/bin/mv -- "$PARTIAL" "$EVIDENCE" 2>/dev/null || fail output EVIDENCE_WRITE_FAILED
/bin/cat -- "$EVIDENCE"
exit "$run_status"
~~~

El paquete se consume al comenzar el bloque. Cualquier drift, FAIL o timeout detiene este diagnóstico y no habilita typecheck, F1, suites restantes ni otra etapa.

