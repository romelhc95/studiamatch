# JIT — clasificar una lectura fallida de F1 en Docker Desktop WSL

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-READ-ERROR-CLASSIFICATION-ONCE-20261008-V1`  
Estado: **preparado; requiere aprobación exacta; no ejecutado**.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Hecho que motiva el diagnóstico

El usuario aportó estas líneas como resultado de su ejecución en Ubuntu WSL:

```text
phase=desktop-wsl-endpoint-attested|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=DOCKER_READ_FAILED
```

La lectura se conserva como salida sanitizada reportada por el usuario. El mensaje no
aprobó ese JIT y no se usa para acreditar un gate. La salida sí delimita la fase reportada:
el `docker inspect` fijo de F1 devolvió un código no cero. El wrapper de Docker abstrae el
exit numérico del CLI; el runner diagnóstico termina en exit 1 por cualquier fase/code que
no sea `OK`. El proyector actual descarta `stderr`, por lo que no distingue contenedor ausente,
denegación de acceso, error de Engine ni error del template. La causa queda desconocida.

No está probado que F1 falte o esté corrupto. No recrear, iniciar, parar, borrar, restaurar,
reconstruir ni descargar recursos para inferir una causa.

## Objeto de autorización solicitado

Autorizar una sola invocación del runner nuevo y, únicamente si devuelve las tres líneas
`error_code=OK` indicadas abajo, reanudar r9 y las etapas locales aún no consumidas dentro de
la autorización consolidada existente. No requiere permisos por cada archivo, helper, hash
o comando cubierto por esos paquetes. El usuario `romel` ejecuta el bloque exacto en una
terminal interactiva Ubuntu WSL del host Windows, sin `sudo`.

El runner vuelve a comprobar branch/HEAD, contexto Docker Desktop, que el Engine responda como
Linux, y la política allowlisted de imagen F1; luego ejecuta **una vez** el `docker inspect`
del ID F1 fijado. Esa lectura repetida está justificada porque la corrida reportada no
distinguió la causa y el código del proyector que la produjo se corrigió para clasificarla.
El comando conserva límite de salida y timeout. No usa `/proc` ni depende de la distro interna
del Engine. No ejecuta `docker info`, logs, `ps`, pull, build, create, run, start, exec, wait,
stop, rm, limpieza, cambios de contexto/configuración ni writes remotos.

El residual **MEDIUM** de la atestación Docker Desktop WSL se mantiene: contexto local,
respuesta Linux y F1 allowlisted no prueban PID/UID/ejecutable/namespace del daemon. Esta
invocación no vuelve a usar la aprobación consumida del output-capture JIT anterior.

## Condiciones de parada

- Un único intento; sin retry.
- Timeout, preflight distinto, línea inválida, salida vacía o cualquier error consume esta
  autorización y detiene G03/G04 y r9.
- `CONTAINER_NOT_FOUND` no autoriza crear o recrear F1. Se presenta evidencia y se prepara
  decisión nueva por objetivo.
- `DOCKER_ACCESS_DENIED`, `DOCKER_ENGINE_UNAVAILABLE`, `INSPECT_TEMPLATE_ERROR`,
  `DOCKER_READ_FAILED`, mismatch, error de salida o timeout detienen la etapa. No tocar Docker
  antes de identificar el predicado y acordar una corrección revisable.
- Solo las tres fases exactas con `OK` habilitan continuar las operaciones runtime ya
  autorizadas. Una lectura correcta de F1 por sí sola no declara G04 cerrado; deben compararse
  sus controles contra la allowlist vigente.

## Runner y pin

- Runner: `tests/h3req1_docker_peer_substep_diag/run_wsl_f1_read_classification_once.sh`
- SHA-256 runner: `3e9adabdb3fdb2ed6f067e297975613047589cf4714acc8ec213cce89694dcd0`
- Helper: `tests/h3req1_docker_peer_substep_diag/f1_read_failure_classification_once.py`
- SHA-256 helper: `b84e46250823a0a7f3c73bf0bbd3359147585dea7d1c4b8ef322d87a1c12d4fc`
- Attestation helper existente, sin modificación: SHA-256
  `c25aa3d3d91bb0cadc160b090c49c4bc61362baefaf3415d046ce7a9cabea4cb`.
- Proyector allowlisted existente, sin modificación: SHA-256
  `794b49ce5560c8cacebbd403c05b4cdbe78fd0c0062d30b6690b901838831463`.

El helper mantiene el texto de error solo en memoria, hasta 4096 bytes, y lo traduce a una
lista cerrada de códigos. No registra ni imprime `stderr`, stdout crudo, ID, ruta, labels,
variables de entorno ni metadata. La prueba sintética cubre patrones conocidos, fallback y
ausencia de salida cruda. Está preparada, no ejecutada.

## Comando único para terminal interactiva Ubuntu WSL

Pegar el bloque completo una sola vez, como usuario `romel` y sin `sudo`:

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_read_classification_once.sh'
readonly RUNNER_SHA256='3e9adabdb3fdb2ed6f067e297975613047589cf4714acc8ec213cce89694dcd0'
readonly SAFE_LINE_RE='^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$'
readonly EXPECTED_OK=$'phase=desktop-wsl-endpoint-attested|error_code=OK\nphase=f1-image-read|error_code=OK\nphase=f1-container-read|error_code=OK'

if (( EUID == 0 )); then
  printf 'phase=capture-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -t 0 ]]; then
  printf 'phase=capture-preflight|error_code=INTERACTIVE_TTY_REQUIRED\n'
  exit 1
fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout ]]; then
  printf 'phase=capture-preflight|error_code=RUNTIME_UNAVAILABLE\n'
  exit 1
fi
if ! hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)"; then
  printf 'phase=capture-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
fi
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=capture-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi

runner_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=1s 55s \
  /bin/bash "$RUNNER" 2>/dev/null)"
runner_status=$?

safe_output=''
invalid_output=0
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ "$line" =~ $SAFE_LINE_RE ]]; then
    safe_output+="${line}"$'\n'
  else
    invalid_output=1
    break
  fi
done <<< "$runner_output"

if (( invalid_output )); then
  printf 'phase=output-capture|error_code=OUTPUT_REJECTED\n'
elif [[ -z "$safe_output" ]]; then
  printf 'phase=output-capture|error_code=NO_SANITIZED_OUTPUT\n'
elif (( runner_status == 0 )) && [[ "$runner_output" == "$EXPECTED_OK" ]]; then
  printf '%s' "$safe_output"
elif (( runner_status == 0 )) || [[ "$runner_output" == "$EXPECTED_OK" ]]; then
  printf '%s' "$safe_output"
  printf 'phase=output-capture|error_code=INCOMPLETE_RESULT\n'
else
  printf '%s' "$safe_output"
fi

IFS= read -r -p 'Copia solo las lineas phase/error_code; presiona Enter cuando las tengas: ' _ || true
)
```

Copiar únicamente las líneas `phase=…|error_code=…` antes de presionar Enter. Si la pausa no
queda abierta, detenerse; no ejecutar otra vez.

## Revisión y límite

Revisión estática de alcance: solo invoca el ID F1 con el formato de campos ya allowlisted;
los bytes de error se limitan, clasifican y descartan. Timeout total externo 55 s y timeout
interno del comando preservado. No se ejecutaron runner, Docker ni pruebas sintéticas para
preparar este paquete. Sin aprobación exacta y resultado, no se invoca.
