# JIT — clasificador npm V3 y una auditoría read-only — 2026-10-09

Estado: preparado; requiere una aprobación humana nueva. La invocación V2 aprobada está
consumida en `EMPTY_STDOUT_STDERR_PRESENT`. Este paquete no reutiliza ese permiso ni repite
automáticamente la solicitud.

## Objetivo y alcance

Identificar una sola vez un código de error npm presente en stderr mediante líneas exactas y
allowlist. Si el proceso devuelve un reporte JSON, emitir su resumen ya sanitizado. Si stderr no
permite una clasificación segura, devolver un código genérico cerrado. No se preserva ni imprime
stderr crudo.

## Candidato e inputs fijados

| Elemento | Valor |
|---|---|
| Checkout / rama / HEAD | `/home/romel/src/studiamatch-h3req1-sync-20261002` / `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| Imagen candidata | `studiamatch-h3req1:20261009-v3`, digest `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63` |
| Package manifest | `web/package.json`, SHA-256 `4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a` |
| Lockfile | `web/package-lock.json`, SHA-256 `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc` |
| Clasificador | `tests/h3req1_docker_peer_substep_diag/v3_npm_audit_classifier_v3/audit_candidate_v3_v3.py`, SHA-256 `d821152adfde8fe1b9b58c51b2b04c344581211e3318521c1709636d650dd7e1` |
| Pruebas sintéticas | `tests/h3req1_docker_peer_substep_diag/v3_npm_audit_classifier_v3/test_audit_candidate_v3_v3.py`, SHA-256 `46ae18fa6edc33c9625d6256ac0933fcd4dfedad4ce3d61fb177817d31ee5cfe` |
| Runner | `tests/h3req1_docker_peer_substep_diag/v3_npm_audit_classifier_v3/run_candidate_npm_audit_classifier_v3_once.sh`, SHA-256 `fbfca9919a41ee7eda8c5d8d2574cd94d21726544c682597193d32b01ab64aa4` |

## Comando único

Ejecutar una sola vez como `romel` no-root en una terminal interactiva de Ubuntu WSL:

```bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/v3_npm_audit_classifier_v3/run_candidate_npm_audit_classifier_v3_once.sh"
readonly RUNNER_SHA256='fbfca9919a41ee7eda8c5d8d2574cd94d21726544c682597193d32b01ab64aa4'
if (( EUID == 0 )); then
  printf 'phase=dispatch-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -t 0 ]]; then
  printf 'phase=dispatch-preflight|error_code=INTERACTIVE_TTY_REQUIRED\n'
  exit 1
fi
runner_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || {
  printf 'phase=dispatch-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
}
if [[ "${runner_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=dispatch-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
exec /usr/bin/timeout --foreground --signal=TERM --kill-after=10s 150s /bin/bash "$RUNNER"
```

## Secuencia condicionada

1. El runner vuelve a fijar rama/HEAD, paquete, lockfile, clasificador, pruebas, imagen local y
   lista exacta de archivos. Cualquier discrepancia detiene el ciclo antes de Docker.
2. Se ejecutan primero seis pruebas sintéticas del parser Bash y dieciséis casos del clasificador
   en el contenedor fijado. Las nuevas fixtures reconocen `EAI_AGAIN` solo desde la línea
   `npm error code EAI_AGAIN` y convierten un código desconocido a `NPM_ERROR_REPORT`.
3. Solo si los sintéticos pasan, se ejecuta una vez `npm audit --json` en `/opt/node-staging/web`,
   contra `https://registry.npmjs.org/`, con `--fetch-retries=0` y timeout interno 120 s. No se
   vuelve a solicitar si falla.
4. stdout solo puede producir un resumen sanitizado y de tamaño limitado, o una línea
   `phase=...|error_code=...`. stderr se mantiene en memoria, se limita a 16 KiB y nunca se
   imprime ni persiste. Un código solo se emite si es allowlisted; formatos desconocidos fallan
   cerrados.
5. El contenedor usa `--rm`, imagen `--pull=never`, filesystem read-only, usuario 1000, sin
   capacidades, sin secretos/`.env*`, cache temporal y sin volúmenes persistentes. El registry
   público recibe la solicitud de auditoría; no se envían credenciales ni se descargan
   tarballs/dependencias. La interfaz Docker usa `--network=bridge`; el comando fija
   `registry.npmjs.org` y no ejecuta lifecycle scripts, pero este JIT no instala una regla de
   firewall por hostname. La petición transmite la metadata del árbol de dependencias necesaria
   para la auditoría pública.

No modifica manifests, lockfile, imagen, Docker, `studiamatch-dev`, SQL, DB, datos remotos,
credenciales o configuración. No hace pull/build/install, F1, r9, cutover, push, PR, merge ni
deploy. Error o timeout consume la invocación y detiene esta etapa; sin retry.

## Resultado esperado y límite del gate

La evidencia admitida será únicamente la salida sanitizada del runner, agregada al archivo de
evidencia sin contenido npm crudo. `NPM_ERROR_<código>` demuestra solo el código de error
observado; no acredita una causa más amplia. Un resumen válido documenta los advisories del
lockfile, pero no cierra otros gates H3REQ1. G03 y GO_LOCAL_PR siguen abiertos hasta revisión
completa de los resultados y los prerrequisitos restantes.
