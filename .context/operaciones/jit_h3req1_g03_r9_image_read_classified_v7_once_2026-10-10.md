# H3REQ1 G03 — r9 con clasificación de lectura Docker V7 (one-shot)

Fecha: 2026-10-10. Estado: preparado; requiere aprobación humana nueva.

## Motivo y resultado previo

El JIT G03 r9 V6 aprobado (`7592aaa6d29a3aa70513780087ecb2ae65b89076c772afe8667fdca3ebf17e95`)
se ejecutó una vez con TTY Ubuntu WSL, como usuario no-root. Resultado persistido:

```text
phase=r9-reused-web-inputs|error_code=HASHES_MATCH
phase=r9-context|error_code=IMAGE_READ_FAILED
exit=1
```

El endpoint Docker por contexto `default` pasó su comparación antes del error. El runner V6
descartó stderr del `docker image inspect`; por ello no está demostrado si falló el acceso al
daemon, el tag o la lectura API. La autorización V6 está consumida y no se repite.

## Solicitud agrupada

Se solicita una invocación de `H3REQ1-G03-R9-IMAGE-READ-CLASSIFIED-CONTINUATION-V7-ONCE-20261010-V1`.
La ejecución será una terminal TTY de Ubuntu WSL, usuario `romel` no-root y sin `sudo`, con
`sandbox_permissions=require_escalated` para el acceso local al socket Docker Desktop. La elevación
es del sandbox de Codex; no eleva el EUID del host. La aprobación no cubre ninguna otra invocación.

El runner V7 conserva el flujo del runner V6, actualiza su pin de WIP tras guardar la evidencia
V6, y agrega cuatro casos sintéticos del clasificador antes de la lectura real. Clasifica en
memoria el stderr de esa única lectura. Si falla, emite solo uno de `DOCKER_PERMISSION_DENIED`,
`DOCKER_ENDPOINT_UNAVAILABLE`, `IMAGE_NOT_FOUND` o `DOCKER_API_READ_FAILED` y detiene. Si pasa y
el digest coincide, continúa una vez con el r9 ya
aprobado en alcance: revalida `studiamatch-dev`/volumen, crea un contenedor efímero
`--pull=never --network=none --read-only`, reutiliza actionlint únicamente con hashes idénticos y
ejecuta los checks restantes en orden. Cualquier mismatch/FAIL/timeout detiene las etapas
posteriores. Timeout total: 180 segundos; cero retries.

## Inputs, límites y evidencia

- Rama `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`, WIP
  `55/282/0` al guardar este paquete.
- Imagen local `studiamatch-h3req1:20261009-v3`, digest
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- Contenedor `studiamatch-dev`, ID
  `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`; volumen
  `studiamatch_h3req1_node_modules` montado solo lectura.
- Runner `/tmp/h3req1-g03-r9-v7-image-read-classified-runner-20261010.sh`, SHA-256
  `a388d9264e68579161e7631002933ce5e6e0615fba12106c02ae098a0ed68614`.
- El runner verifica manifiestos, 68 fuentes, actionlint, web inputs y fuente del candidato antes
  del contenedor. Emite fases/códigos y, únicamente para ShellCheck, ruta allowlisted, línea,
  columna y regla. No emite stdout/stderr crudo.
- El wrapper conserva salida sanitizada y exit en
  `.context/evidencia/h3req1_g03_r9_v7_execution_2026-10-10.txt`; límite capturado 8192 bytes.
- Sin pull/build/install, egress, lectura F1, SQL/DB, secretos/`.env`, escrituras de volúmenes,
  recursos Docker persistentes, cleanup de otros recursos, Git remoto, CI remoto, push/PR/merge o
  deploy. El único contenedor nuevo es efímero y `--rm`.
- Un fallo de preflight no llama Docker. Un fallo de lectura o check consume la nueva invocación;
  no se repite ni se avanza a F1, snapshot, startup o integración.

## Comando único

Ejecutar literalmente una vez mediante la terminal TTY aprobada. En Codex, la llamada debe usar
`sandbox_permissions=require_escalated`; conservar `EUID != 0` y no usar `sudo`.

```bash
set -u -o pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER='/tmp/h3req1-g03-r9-v7-image-read-classified-runner-20261010.sh'
readonly RUNNER_SHA256='a388d9264e68579161e7631002933ce5e6e0615fba12106c02ae098a0ed68614'
readonly CAPTURE='/tmp/h3req1-g03-r9-v7-output-20261010.partial'
readonly SANITIZED='/tmp/h3req1-g03-r9-v7-output-20261010.sanitized'
readonly EVIDENCE='/home/romel/src/studiamatch-h3req1-sync-20261002/.context/evidencia/h3req1_g03_r9_v7_execution_2026-10-10.txt'
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
if [[ "$wip_counts" != 55/282/0 ]]; then fail WIP_MISMATCH; fi
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

La invocación se considera consumida al iniciar el bloque. No reejecutar, incluso si falla el
preflight o no se recupera la salida. Este JIT no acredita GO por sí solo.
