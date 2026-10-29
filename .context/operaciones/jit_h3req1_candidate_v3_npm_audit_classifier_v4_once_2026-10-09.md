# JIT — npm audit classifier V4: rutas de fixture corregidas — 2026-10-09

Estado: requiere aprobación humana nueva. El JIT V3 fue aprobado y consumido antes de npm:
`capture-synthetic-tests=OK`, `image-preflight=OK`, `synthetic-tests=TESTS_FAILED`. El cambio
mínimo de este paquete corrige las dos rutas de Python ejecutadas dentro del contenedor.

## Objetivo y alcance

Ejecutar los sintéticos del clasificador en la imagen candidata y, solo si pasan, solicitar una
vez `npm audit --json` al registry público. La respuesta se sanitiza a un resumen limitado o a
fase/código cerrado. No se guarda ni imprime stderr crudo.

## Candidato e inputs fijados

| Elemento | Valor |
|---|---|
| Checkout / rama / HEAD | `/home/romel/src/studiamatch-h3req1-sync-20261002` / `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| Imagen candidata | `studiamatch-h3req1:20261009-v3`, digest `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63` |
| Package manifest | `web/package.json`, SHA-256 `4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a` |
| Lockfile | `web/package-lock.json`, SHA-256 `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc` |
| Clasificador | `tests/h3req1_docker_peer_substep_diag/v3_npm_audit_classifier_v3/audit_candidate_v3_v3.py`, SHA-256 `d821152adfde8fe1b9b58c51b2b04c344581211e3318521c1709636d650dd7e1` |
| Pruebas sintéticas | `tests/h3req1_docker_peer_substep_diag/v3_npm_audit_classifier_v3/test_audit_candidate_v3_v3.py`, SHA-256 `46ae18fa6edc33c9625d6256ac0933fcd4dfedad4ce3d61fb177817d31ee5cfe` |
| Runner corregido | `tests/h3req1_docker_peer_substep_diag/v3_npm_audit_classifier_v3/run_candidate_npm_audit_classifier_v3_once.sh`, SHA-256 `2df6da2fe4617e87bc10a93f1ceb6ffd3c80b54bac918b6092aa5eac3beaa27a` |

## Comando único

Ejecutar una sola vez como `romel` no-root en una terminal interactiva Ubuntu WSL:

```bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/v3_npm_audit_classifier_v3/run_candidate_npm_audit_classifier_v3_once.sh"
readonly RUNNER_SHA256='2df6da2fe4617e87bc10a93f1ceb6ffd3c80b54bac918b6092aa5eac3beaa27a'
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

## Secuencia y límites

1. Fija rama/HEAD, package/lock, clasificador, pruebas, lista exacta de tres archivos e imagen
   local. No lee configuración ni `.env*`.
2. Ejecuta seis pruebas del parser Bash y 16 sintéticos en un contenedor efímero de la imagen
   fijada. El contenedor monta el directorio de prueba solo lectura. Las rutas corregidas son
   exactamente `test_audit_candidate_v3_v3.py` y `audit_candidate_v3_v3.py`.
3. Únicamente con PASS ejecuta una llamada `npm audit --json` con timeout y retries cero contra
   `https://registry.npmjs.org/`. La metadata del árbol de dependencias se envía a ese registry;
   no se descargan tarballs ni dependencias, y no se ejecutan lifecycle scripts.
4. Se conserva solo código allowlisted o resumen sanitizado. stderr crudo permanece temporal en
   memoria, con límite acotado, y nunca se imprime ni persiste. Error, resultado no clasificable
   o timeout consume esta invocación y detiene la etapa; sin retry.

El contenedor usa `--rm`, `--pull=never`, filesystem read-only, usuario 1000, capacidades
retiradas, `no-new-privileges`, cache temporal y Docker bridge para el request público. No hay
regla de firewall por hostname. No instala ni modifica paquetes; no toca manifests, lockfile,
imagen, Docker config, `studiamatch-dev`, SQL, DB, secretos, F1/r9, push/PR/merge/deploy o
cutover.

Este gate acredita únicamente la clasificación/auditoría fijada. No cierra G03 ni GO_LOCAL_PR por
sí solo.
