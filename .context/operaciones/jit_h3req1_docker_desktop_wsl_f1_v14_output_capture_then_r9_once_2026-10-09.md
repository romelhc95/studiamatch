# JIT V14 — captura de fases, auditoría de temporales y F1/r9 condicional

Fecha: 2026-10-09. Estado: preparación estática completa; revisión independiente final sin hallazgos; requiere aprobación humana para una invocación nueva.

## Motivo demostrado

V13 fue aprobado una vez y terminó con `f1-v11-output/OUTPUT_REJECTED`, exit 1. El wrapper no guardó la salida interna. Ese código combina dos causas posibles: límite de 2048 bytes o línea no permitida. No se sabe si el proceso llegó a leer F1; r9 no se alcanzó porque el wrapper exige la secuencia completa antes de iniciarlo. V14 sube el máximo acotado a 8192 bytes, mantiene la validación estricta y emite solo las fases sanitizadas anteriores al primer output no permitido. Cualquier mismatch, incluso con status 0, devuelve exit no-cero.

V13 pudo haber iniciado hasta dos contenedores `h3req1-v12-template-*`; su runner intentó detenerlos, pero el output rechazado impide acreditar el resultado. Antes de crear nuevos temporales, V14 consulta una sola vez `docker container ls` filtrado por ese prefijo. Solo evalúa si el resultado está vacío; no imprime ni conserva IDs. Si encuentra uno, informa presencia sanitizada y se detiene sin inspeccionarlo ni limpiarlo.

## Candidato, impacto y gates

| Campo | Valor |
|---|---|
| Checkout | `/home/romel/src/studiamatch-h3req1-sync-20261002` |
| Rama / HEAD | `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| WIP actual de preparación | 54 archivos tracked modificados, 226 entradas untracked de `git status --short`, 0 staged; checkout original preservado |
| Archivos propios | `tests/h3req1_docker_peer_substep_diag/f1_output_capture_classifier_v14_once.py`; `tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v14_output_capture_then_r9_once.sh` |
| Impacto | Diagnóstico read-only y contenedores temporales con `--rm`; sin cambio funcional, SQL, Docker config o estado remoto |
| G03/G04 / total | 0/10 y 0/10; G01/G02 10/10; G05–G10 0/10; total 20%, delta 0; D01–D14 0/14 |

## Secuencia única y stop-on-failure

1. Validar identidad no-root/TTY, candidato/rama/HEAD, variables de override Docker, pins V7/V10/V11/V12/V13 y manifiestos r9 con 68 inputs sin drift.
2. Verificar la evidencia V13 consumida y ejecutar siete fixtures puros antes de Docker. Ningún fallo de pin/fixture inicia Docker.
3. Confirmar endpoint/evidencia previa y consultar en modo read-only el prefijo exacto `h3req1-v12-template-`. Cualquier residual detiene, sin limpieza ni inspect. Si no hay residuales, leer el mapa de labels sintético y exigir que las tres claves snapshot H3 estén ausentes; labels ajenos se permiten y el JSON no se imprime.
4. Ejecutar los dos smokes temporales V13 con recursos limitados, sin red, read-only, UID no-root, `--pull=never` y limpieza ownership-checked. Cualquier error/cleanup fallido detiene F1 y r9.
5. Solo con smoke PASS, leer una vez imagen F1 y una vez la proyección del contenedor F1 allowlisted. La identidad objetivo se compara por hash; si coincide con `studiamatch-dev`, detener.
6. Solo tras F1 PASS exacto, ejecutar r9 una vez dentro de su contenedor efímero offline.

El wrapper captura stdout de la fuente Python fijada bajo timeout y luego verifica un máximo de 8192 bytes con `LC_ALL=C`; ese máximo se comprueba después de la captura en memoria, no durante el stream. La fuente y sus comandos Docker están fijados, con salidas individuales acotadas. El wrapper solo conserva líneas `phase=…|error_code=…`, imprime las fases sanitizadas anteriores a un rechazo y no muestra ni persiste salida cruda. Si excede el límite o contiene una línea ajena, se detiene antes de r9. Cualquier FAIL/timeout consume esta autorización. No hay retry, pull, build, install, limpieza de recursos preexistentes, cambios de Docker, DB/SQL/Supabase, secretos, Git remoto/GitHub/Cloudflare, push, PR, merge, ramas protegidas o deploy. No reejecuta F2d ni probes completos V10; no usa sudo ni `/proc` del motor.

El alcance incluye una lectura de `docker container ls` limitada al prefijo anterior, una lectura del mapa de labels sintético, como máximo dos smokes temporales, una lectura F1 de imagen, una de contenedor y r9 condicional. Debido a que V13 no conservó las fases previas a `OUTPUT_REJECTED`, la invocación nueva podría repetir ambas lecturas F1; esto queda explícito en esta autorización.

La salida diagnóstica completa que habilita r9 debe coincidir en orden:

```text
phase=prior-v13-output-capture|error_code=OK
phase=prior-v12-failure|error_code=OK
phase=classifier-v13-null|error_code=OK
phase=classifier-v13-empty-object|error_code=OK
phase=classifier-v13-unrelated-label|error_code=OK
phase=classifier-v13-target-label-1|error_code=OK
phase=classifier-v13-target-label-2|error_code=OK
phase=classifier-v13-target-label-3|error_code=OK
phase=classifier-v13-malformed-json|error_code=OK
phase=prior-v11-failure|error_code=OK
phase=prior-v10-evidence|error_code=OK
phase=prior-endpoint-attestation|error_code=OK
phase=prior-v13-container-audit|error_code=OK
phase=f1-template-synthetic-label-map|error_code=OK
phase=f1-template-present-inspect|error_code=OK
phase=f1-template-absent-inspect|error_code=OK
phase=f1-template-synthetic-check|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=OK
```

Después, r9 debe emitir sus checks completos `OK` y `phase=r9-summary|error_code=ALL_CHECKS_OK`.

## Evidencia del ciclo anterior

Resultado V13: [salida rechazada, sin r9](../evidencia/h3req1_c03_v13_output_rejected_2026-10-09.md), SHA-256 `d46d2774af0ca2f70f44445a183e8f073de2446bcb6bdab0d74ad2f17acada64`.

## Pines

| Recurso | SHA-256 |
|---|---|
| Helper V14 | `776d56c87101f5f4b632f7dd58fddc3405f591cfcd756343741ce4095a47ce29` |
| Wrapper V14 | `9b87fc79cfa93e5515fb0e0746bbcbe947df070961c32b1c47ef83ec619259aa` |
| Helper V13 fijado | `e2cb61472552dab4165014347f63232a3f8d1d888efa7b75aea918a02c71d073` |
| Wrapper V13 consumido | `59781a6607da28918536e57698e683051967e3407ec30e09a148692675d9ddb7` |
| JIT V13 consumido | `5019c8cd6aab75d18d3f4e369744470fee16ad91398855f6d3c18c781250aa25` |
| Evidencia V13 consumida | `d46d2774af0ca2f70f44445a183e8f073de2446bcb6bdab0d74ad2f17acada64` |
| Paquete r9 | `688e81efaae70a841a64cd4c0a074ae3c76c355f5ef9bc77756cff9ad607fc02` |
| Inputs r9 | `6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee` |
| Herramientas r9 | `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa` |

## Revisión independiente

Finalizada sin hallazgos en el helper y wrapper V14. Confirmó los pins V13, el listado read-only del prefijo residual sin inspect/stop/rm, salida sanitizada y el orden fail-closed hasta F1/r9. No ejecutó Docker ni pruebas. La limitación de captura posterior a memoria queda descrita arriba y en la evidencia de preparación.

## Solicitud concreta

Se solicita aprobar una invocación de `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-V14-OUTPUT-CAPTURE-AND-R9-ONCE-20261009-V1` con el SHA-256 de este JIT indicado en la solicitud humana. Se ejecuta una vez como `romel` no-root en Ubuntu WSL interactiva con `require_escalated`, sin sudo. El alcance es exactamente el anterior; fallo o timeout detiene sin retry.

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v14_output_capture_then_r9_once.sh'
readonly RUNNER_SHA256='9b87fc79cfa93e5515fb0e0746bbcbe947df070961c32b1c47ef83ec619259aa'
if (( EUID == 0 )); then
  printf 'phase=jit-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -t 0 ]]; then
  printf 'phase=jit-preflight|error_code=INTERACTIVE_TTY_REQUIRED\n'
  exit 1
fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout ]]; then
  printf 'phase=jit-preflight|error_code=RUNTIME_UNAVAILABLE\n'
  exit 1
fi
hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || {
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
}
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 900s /bin/bash "$RUNNER" 2>/dev/null
)
```
