# H3REQ1 — clasificador sanitizado para auditoría npm V3

Estado: requiere autorización humana nueva. El JIT anterior fue aprobado y consumido con
`REPORT_INVALID`; esta solicitud no reutiliza esa aprobación ni ejecuta automáticamente un
retry.

## Invocación y alcance

Autorizar **una ejecución** como `romel` no-root en Ubuntu WSL interactiva, sin `sudo`:

```bash
set -Eeuo pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/v3_npm_audit_classifier_v2/run_candidate_npm_audit_classifier_v2_once.sh'
readonly RUNNER_SHA256='4a867f32759f88618325b969f4c89668a6ec25146414a75d33a78c999049ca78'
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

Una falla, rechazo, discrepancia o timeout consume la invocación. No reintentar.

## Acción concreta

El runner fija rama `feat/h3req1-sync-20261002`, HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`, imagen local V3
`studiamatch-h3req1:20261009-v3` →
`sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`, y los manifests
de npm. Primero verifica seis contratos sintéticos de captura de fases en Bash; luego hace una
lectura `docker image inspect` del tag para comprobar el digest y una sola ejecución
`docker run --rm --pull=never` en un contenedor efímero, con root filesystem
read-only, usuario UID/GID 1000, capacidades retiradas, `no-new-privileges`, 64 PIDs, 512 MiB,
0.5 CPU y `/tmp` limitado. Monta read-only solo los tres archivos allowlisted del clasificador;
no monta el checkout ni archivos de entorno. El contenedor ejecuta 14 aserciones sintéticas y,
solo si pasan, un `npm audit --json` de la misma imagen y lockfile. Las fases de salida son
`capture-synthetic-tests`, `image-preflight`, `synthetic-tests` y `npm-audit` en orden.

El clasificador captura stdout y stderr en memoria con límites independientes de 64 KiB y
16 KiB. Emite únicamente fases/códigos cerrados (`NON_JSON_OUTPUT`, `NPM_TEXT_ERROR`,
`NON_JSON_MARKUP`, códigos npm de allowlist, etc.) o un resumen de advisories saneado. No
imprime texto crudo, cuerpos de red, stderr, env vars ni mensajes npm. Si el JSON es válido,
solo conserva nombres/versiones/rangos con allowlist, severidades, GHSA válidos y disponibilidad
de fix. Límite de auditoría: 120 s; Docker: 150 s; bloque total: 180 s; salida exterior: 8 KiB.

## Red y efectos

- `npm audit` envía el grafo de dependencias al registry público npm; esto es un egress externo
  conocido y forma parte de la acción solicitada.
- Docker usa la red bridge predeterminada; no hay allowlist por dominio a nivel de red. La
  configuración npm fija `https://registry.npmjs.org/`, desactiva retries y no descarga
  tarballs. No se instala ni modifica ningún paquete.
- Docker puede crear un contenedor temporal; `--rm` lo retira al terminar. El único directorio
  temporal de configuración en WSL se elimina por trap bajo el prefijo exacto del runner.
- No lee F1, no corre r9, no accede a `studiamatch-dev`, no reconstruye/cambia Docker, no hace
  cutover, no toca datos/volúmenes/SQL, no modifica fuentes y no realiza acciones GitHub,
  Cloudflare o Supabase.

## Pines verificados al preparar

| Recurso | SHA-256 / pin |
|---|---|
| Este paquete JIT | SHA adjunto por fuera del contenido: verificar antes de autorizar |
| Runner Bash | `4a867f32759f88618325b969f4c89668a6ec25146414a75d33a78c999049ca78` |
| Clasificador Python | `9fa67714f441b262b4ff20b62177b95eed738198d5bb76fe75699abc912e33ba` |
| Sintéticos | `802c3e3f72af3370a5cc7d9c15e4c25d4eda2a4145385725f5f233d46a7e263f` |
| `web/package.json` | `4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a` |
| `web/package-lock.json` | `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc` |
| Imagen candidata | `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63` |

Las pruebas del clasificador no se ejecutaron en el host. `bash -n` del runner pasó. El
resultado de este paquete no acredita por sí mismo G03 ni autoriza remediar dependencias o
hacer cutover.
