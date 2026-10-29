# H3REQ1 — auditoría npm V3 con captura JSON corregida

Estado: requiere autorización humana nueva. La invocación del JIT anterior
`H3REQ1-CANDIDATE-V3-NPM-AUDIT-CLASSIFIER-V2-ONCE-20261009-V1` quedó consumida en
`phase=capture-synthetic-tests|error_code=SUMMARY_CASE_INVALID`; no alcanzó Docker ni npm.
Este JIT corrige únicamente el predicado Bash de inicio del resumen JSON y solicita una
invocación nueva. No hereda ni reutiliza la autorización consumida.

## Ejecución solicitada

Una ejecución como `romel` no-root en una terminal interactiva Ubuntu WSL, sin `sudo`:

```bash
set -Eeuo pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/v3_npm_audit_classifier_v2/run_candidate_npm_audit_classifier_v2_once.sh'
readonly RUNNER_SHA256='0c48f12b818c8611c1187fa402f92bb502ed6ea45cb17cc13270db28a51a58f5'
if (( EUID == 0 )); then
  printf 'phase=jit-preflight|error_code=RUN_AS_WSL_USER\n'
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
exec /usr/bin/timeout --foreground --signal=TERM --kill-after=2s 180s /bin/bash "$RUNNER"
```

Falla, rechazo, discrepancia, resultado npm no clasificable o timeout consume la ejecución.
No hay reintento dentro de la invocación.

## Secuencia condicionada

1. Seis casos sintéticos del parser Bash de fases/resumen.
2. Solo tras `capture-synthetic-tests=OK`, inspección de solo lectura del tag local para
   comprobar el digest fijado.
3. Solo tras coincidencia, un contenedor efímero read-only ejecuta 14 casos sintéticos del
   clasificador Python.
4. Solo tras `synthetic-tests=OK`, una única llamada `npm audit --json` al registry público
   `https://registry.npmjs.org/` con `--fetch-retries=0`; captura stdout/stderr con límites,
   clasifica a un resumen saneado y no descarga tarballs ni cambia dependencias.

Un fallo detiene la secuencia. Ninguna fase posterior se ejecuta tras FAIL.

## Recursos, efectos y límites

- Candidato: rama `feat/h3req1-sync-20261002`, HEAD
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Imagen local `studiamatch-h3req1:20261009-v3`, digest
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`; no pull/build.
- Inputs npm: `web/package.json` SHA-256
  `4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a` y
  `web/package-lock.json` SHA-256
  `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc`.
- Clasificador Python SHA-256
  `9fa67714f441b262b4ff20b62177b95eed738198d5bb76fe75699abc912e33ba`;
  sintéticos SHA-256
  `802c3e3f72af3370a5cc7d9c15e4c25d4eda2a4145385725f5f233d46a7e263f`.
- Runner corregido SHA-256
  `0c48f12b818c8611c1187fa402f92bb502ed6ea45cb17cc13270db28a51a58f5`.
- Docker usa bridge predeterminada; registry público como egress conocido. Contenedor:
  `--pull=never`, filesystem read-only, UID/GID 1000, capacidades retiradas,
  `no-new-privileges`, 64 PIDs, 512 MiB, 0.5 CPU y `/tmp` tmpfs 64 MiB. Bind mounts
  read-only de solo los tres archivos fijados del clasificador. El directorio de config Docker
  temporal se limita al prefijo exacto del runner y se elimina por trap.
- Captura total máxima 8 KiB; runner 180 s; Docker 150 s; npm 120 s; fetch retries cero.
- No lee F1, r9 ni `studiamatch-dev`; no lee secretos/`.env*`; no hace pull, build, instalación,
  cambio de dependencias, cutover, limpieza externa, SQL, push/PR/merge, configuración remota
  ni despliegue.

## Recuperación / resultado

No cambia fuentes de producto, lockfile, imagen ni contenedores persistentes. Un FAIL conserva
solo fase/código sanitizado y no habilita otra ejecución. La evidencia runtime no acredita G03
ni GO; no se modifica la métrica de cierre por esta solicitud.
