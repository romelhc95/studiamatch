# JIT — H3REQ1 G03 r9 output capture V6

Identificador: `H3REQ1-G03-R9-OUTPUT-CAPTURE-V6-ONCE-20261010-V1`  
Estado: requiere aprobación humana nueva; una invocación.  
Ejecutor: `romel`, no-root, terminal interactiva de Ubuntu WSL conectada a Docker Desktop.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.  
Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.  
WIP fijado para este paquete: `55/280/0` después de añadir este documento; no tolera drift.

## Motivo y relación con V5

V5, SHA aprobado `0cdd62518f924693c0c05b45a69ecaf8a2bf4b4b0d96001f1bde75a39f403eb6`, se
despachó una vez y se consumió. La salida no es recuperable y no permite afirmar qué fases
terminaron. Este paquete requiere aprobación nueva; no reutiliza la autorización V5.

V6 repite exclusivamente el r9 G03 que V5 intentó validar porque falta evidencia verificable.
No lee F1 ni ejecuta copia, runtime, SQL/DB, C03 integrado, UAT, onboarding o acciones remotas.
Conserva las mismas siete entradas de ShellCheck y los checks no alcanzados de V5. No repite
actionlint: el helper conserva los tres hashes del PASS anterior y se detiene si alguno cambió.

La única diferencia operativa del dispatcher es persistir la salida ya sanitizada del runner
en el archivo de evidencia fijado abajo. El runner de `/tmp` deriva del host V5 y cambia solo
el WIP esperado a `55/280/0`; SHA-256:
`53c26148369460e8232b4925d131a12e7b2da1626459235644832b1b9b5177e6`.

## Recursos e inputs fijados

| Recurso | Identidad |
|---|---|
| Runner host V6 en `/tmp` | `/tmp/h3req1-g03-r9-v6-output-capture-runner-20261010.sh`, SHA-256 `53c26148369460e8232b4925d131a12e7b2da1626459235644832b1b9b5177e6` |
| Runner interior | `tests/h3req1_docker_peer_substep_diag/run-r9-shellcheck-continuation-inner-v3.sh`, SHA-256 `b4835a286ef036ca733efe6a49be9cc37b19d16bb5ddbfb4a6ea90065461ab71` |
| ShellCheck json1 classifier V2 | `tests/h3req1_docker_peer_substep_diag/shellcheck_json1_classifier_v2.py`, SHA-256 `07a8401aa6a89275362e2456655ad79ec00ff6d3629da5059e851a2520cc38a4` |
| Snapshot de validación existente | `/tmp/h3req1-g03-validation-29d8fff9-r6`, `r4-package.sha256=d10cc19b87adfff36f8092c97b59dc8fb4a247166c0dcbf8f0653dd9f2db6186`, `inputs.sha256=c53e3321190646a2449e28b935711fc6f7b8425d1b19289f2374f4488eaff4c8` |
| Herramientas locales existentes | `/tmp/h3req1-g03-validation-29d8fff9-r2.tools`, `tools.sha256=4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa` |
| Imagen local | `studiamatch-h3req1:20261009-v3`, ID `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63` |
| Contenedor activo requerido | `studiamatch-dev`, ID `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`, `running|healthy` |
| Volumen de dependencias | `studiamatch_h3req1_node_modules`, montaje solo lectura en `/app/web/node_modules` |
| Evidencia final nueva | `.context/evidencia/h3req1_g03_r9_v6_execution_2026-10-10.txt`; debe no existir al iniciar |
| Captura temporal | `/tmp/h3req1-g03-r9-v6-output-20261010.partial`; debe no existir al iniciar |
| Salida sanitizada temporal | `/tmp/h3req1-g03-r9-v6-output-20261010.sanitized`; debe no existir al iniciar |

El runner valida además branch/HEAD/WIP, 68 fuentes del manifiesto, manifests, classifier,
workflows, `web/package.json`, lockfile, `tsconfig`, `next-env.d.ts`, `next.config.js`, imagen,
contenedor y volumen antes de iniciar el único contenedor de validación.

## Una ejecución y límites

Timeout total: 180 segundos; cero retries; stop-on-failure. Se ejecuta un contenedor nuevo con
`--rm --pull=never --network=none --read-only`, no-root, límites de 512 MiB/1 CPU/64 PIDs,
capabilities descartadas y sin privilegios nuevos. El snapshot y las herramientas son read-only;
el volumen `node_modules` es read-only. Los tmpfs son efímeros. No se lee `.env*`, `Env`, secretos,
contenido de volúmenes ni se hace `docker exec` al servicio habitual.

Orden: reutilizar actionlint solo con sus tres hashes exactos; extraer ShellCheck local fijado;
ShellCheck sobre siete scripts; copia temporal; comparar manifests y versiones Node/TypeScript;
`next typegen`; ESLint; `tsc --noEmit`; `test_protected_workflow_review.py`;
`test_scan_credentials.sh`; `test_protected_path_scope_guard.sh`. Un fallo detiene el resto.
No hay pull, build, install, egress, F1, mutaciones persistentes, SQL/DB, cleanup de otros
recursos, push, PR, merge, deploy ni configuración remota.

La captura host acepta únicamente `phase=…|error_code=…`, `exit=…` y el diagnóstico ShellCheck
allowlisted `script|line|column|SC####`. Si la salida supera 8192 bytes o no pasa el filtro, la
evidencia contiene solo un código sanitizado. El archivo se mueve de `/tmp` al destino fijado y
se vuelve a mostrar tras validación. Si ocurre timeout, se conserva el resultado parcial; no se
reintenta ni se inspecciona/retira ningún recurso temporal Docker aparte del `--rm` declarado.

## Comando único

Pegar el bloque completo una sola vez desde Ubuntu WSL interactiva, como `romel`, sin `sudo`.
La aprobación solo será válida para los bytes de este documento y los pins anteriores.

```bash
set -u -o pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER='/tmp/h3req1-g03-r9-v6-output-capture-runner-20261010.sh'
readonly RUNNER_SHA256='53c26148369460e8232b4925d131a12e7b2da1626459235644832b1b9b5177e6'
readonly CAPTURE='/tmp/h3req1-g03-r9-v6-output-20261010.partial'
readonly SANITIZED='/tmp/h3req1-g03-r9-v6-output-20261010.sanitized'
readonly EVIDENCE='/home/romel/src/studiamatch-h3req1-sync-20261002/.context/evidencia/h3req1_g03_r9_v6_execution_2026-10-10.txt'
readonly SAFE_PHASE_RE='^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$'
readonly SAFE_EXIT_RE='^exit=[0-9]{1,3}$'
readonly SAFE_DIAGNOSTIC_RE='^diagnostic=script=(\.githooks/(pre-commit|pre-push)|scripts/security/(h2_web_mock_smoke|protected_path_scope_guard|scan_credentials)[.]sh|tests/sql/h3_invitation_reservation_concurrency[.]sh|tests/test_protected_path_scope_guard[.]sh)\|line=[0-9]{1,6}\|column=[0-9]{1,6}\|rule=SC[0-9]{4}$'

fail() {
  printf 'phase=dispatch-preflight|error_code=%s\nexit=1\n' "$1"
  exit 1
}

if (( EUID == 0 )); then fail RUN_AS_WSL_USER; fi
if [[ ! -t 0 ]]; then fail INTERACTIVE_TTY_REQUIRED; fi
if [[ "$(uname -s 2>/dev/null)" != Linux || "$(uname -r 2>/dev/null | tr '[:upper:]' '[:lower:]')" != *microsoft* ]]; then fail WSL_REQUIRED; fi
if [[ "$(git -C "$ROOT" branch --show-current 2>/dev/null)" != feat/h3req1-sync-20261002 || "$(git -C "$ROOT" rev-parse HEAD 2>/dev/null)" != 4eb4d877a50b012bb630a129bd0c74482c33be9c ]]; then fail CANDIDATE_IDENTITY_MISMATCH; fi
wip_counts="$(git -C "$ROOT" status --porcelain=v1 2>/dev/null | awk 'BEGIN{m=0;u=0;s=0} substr($0,1,2)=="??"{u++;next} {m++;if(substr($0,1,1)!=" ")s++} END{printf "%d/%d/%d",m,u,s}')" || fail WIP_READ_FAILED
if [[ "$wip_counts" != 55/280/0 ]]; then fail WIP_MISMATCH; fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout || ! -x /usr/bin/stat || ! -x /usr/bin/mv || ! -x /bin/bash ]]; then fail RUNTIME_UNAVAILABLE; fi
if [[ ! -f "$RUNNER" || -L "$RUNNER" ]]; then fail RUNNER_UNAVAILABLE; fi
runner_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || fail RUNNER_HASH_FAILED
if [[ "${runner_line%% *}" != "$RUNNER_SHA256" ]]; then fail RUNNER_HASH_MISMATCH; fi
if [[ -e "$CAPTURE" || -e "$SANITIZED" || -e "$EVIDENCE" ]]; then fail OUTPUT_PATH_EXISTS; fi

if /usr/bin/timeout --foreground --signal=INT --kill-after=5s 180s /bin/bash "$RUNNER" >"$CAPTURE" 2>/dev/null; then
  runner_status=0
else
  runner_status=$?
fi

capture_bytes="$(/usr/bin/stat -c '%s' -- "$CAPTURE" 2>/dev/null)" || {
  printf 'phase=output-capture|error_code=CAPTURE_READ_FAILED\nexit=1\n' > "$CAPTURE"
  runner_status=1
  capture_bytes=0
}
if [[ ! "$capture_bytes" =~ ^[0-9]+$ ]] || (( capture_bytes > 8192 )); then
  printf 'phase=output-capture|error_code=OUTPUT_TOO_LARGE\n' > "$CAPTURE"
  runner_status=1
fi

output_invalid=0
sanitized_lines=0
if ! : > "$SANITIZED"; then
  printf 'phase=output-capture|error_code=SANITIZED_FILE_UNAVAILABLE\nexit=1\n'
  exit 1
fi
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ "$line" =~ $SAFE_PHASE_RE || "$line" =~ $SAFE_DIAGNOSTIC_RE ]]; then
    printf '%s\n' "$line" >> "$SANITIZED"
    sanitized_lines=$((sanitized_lines + 1))
  elif [[ "$line" =~ $SAFE_EXIT_RE ]]; then
    :
  else
    output_invalid=1
    break
  fi
done < "$CAPTURE"
if (( output_invalid )); then
  printf 'phase=output-capture|error_code=OUTPUT_REJECTED\n' > "$SANITIZED"
  runner_status=1
  sanitized_lines=1
elif (( sanitized_lines == 0 )); then
  printf 'phase=output-capture|error_code=NO_SANITIZED_OUTPUT\n' > "$SANITIZED"
  runner_status=1
fi
printf 'exit=%s\n' "$runner_status" >> "$SANITIZED"
if ! /usr/bin/mv -- "$SANITIZED" "$EVIDENCE" 2>/dev/null; then
  printf 'phase=output-persistence|error_code=WRITE_FAILED\nexit=1\n'
  exit 1
fi
/bin/cat -- "$EVIDENCE"
exit "$runner_status"
```

## Resultado esperado y recuperación

La evidencia es el archivo indicado, incluso si el runner se detiene después de emitir una fase.
Se reporta su contenido sanitizado y el exit real. Ante preflight drift no se inicia Docker. Ante
fallo de Docker o un check no se ejecutan etapas posteriores. No repetir esta invocación; preparar
corrección mínima y una autorización nueva si el siguiente intento requiere ejecución protegida.

Este JIT no cierra por sí solo G03 si algún check falla, ni acredita F1, G01/G04–G10, GO_LOCAL_PR
o GO_DEVELOPMENT_REAL.
