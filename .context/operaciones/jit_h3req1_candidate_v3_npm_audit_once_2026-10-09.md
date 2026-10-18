# H3REQ1 — consulta npm audit de la imagen candidata V3

Estado: preparado; requiere autorización humana propia. No hereda permisos del diagnóstico V8 ni del rebuild V3 consumido.

## Objetivo y fallo demostrado

El build V3 logró instalar 627 paquetes y `npm ci` informó dos advisories, uno `high` y uno `critical`, sin conservar sus detalles. Antes de preparar otro cutover se necesita identificar el paquete, severidad, rango y disponibilidad de fix en esa imagen exacta. Esta operación no corrige dependencias ni ejecuta suites del producto.

## Solicitud concreta

Autorizar **una invocación**, ejecutada como `romel` no-root en una terminal interactiva de Ubuntu WSL, sin `sudo`:

```bash
set -Eeuo pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/v3_npm_audit/run_candidate_npm_audit_v3_once.sh'
readonly RUNNER_SHA256='d2dfb357c7584451727b73898f565ca363a9e5c81f0d77b477035948ef562c2f'
hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)"
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
exec /usr/bin/timeout --foreground --signal=TERM --kill-after=10s 180s /bin/bash "$RUNNER"
```

## Inputs fijados

- Rama `feat/h3req1-sync-20261002`; HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Imagen local `studiamatch-h3req1:20261009-v3`, ID requerido `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`; el preflight usa solo `docker image inspect --format '{{.Id}}'`.
- `web/package.json`: SHA-256 `4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a`.
- `web/package-lock.json`: SHA-256 `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc`.
- Auditor en Python SHA-256 `4ca41e19643192abec6f0547efd665e996be575e7ed39416940a2d840d34d2d6` y pruebas sintéticas SHA-256 `48036a07f1754335e2c503f248d68cdc07d353a0756fcd0afcb4d234c11c0c64`.
- Runner Bash SHA-256 se fija en el comando anterior y en su pin interno antes de solicitar aprobación.

## Ejecución, límites y egress

1. Preflight TTY, WSL, usuario no-root, rama/HEAD, hashes de package/lock y fuentes. Cualquier diferencia detiene antes de Docker.
2. Crea un directorio temporal nuevo `h3req1-npm-audit-config.*` con permisos `0700`, configura Docker por el socket fijo `/var/run/docker.sock` y usa `env -i`; el trap elimina exclusivamente ese directorio.
3. Lee una vez el ID de la etiqueta V3 y exige el digest fijado. No hace pull ni build.
4. Arranca un contenedor efímero único con `--rm --pull=never`, `--network=bridge`, rootfs read-only, UID/GID 1000, `cap-drop=ALL`, `no-new-privileges`, 512 MiB de RAM/swap, 0.5 CPU, 64 PIDs y `/tmp` tmpfs de 64 MiB. Monta como read-only el directorio dedicado con exactamente tres archivos fijados (runner Bash, auditor y prueba); no monta el checkout web, `.env*`, socket Docker, volúmenes persistentes ni configuración/credenciales.
5. Monta read-only el directorio diagnóstico dedicado con exactamente tres archivos allowlisted, y dentro de la imagen ejecuta seis pruebas sintéticas con `/opt/venv/bin/python` y luego un solo `npm audit --json`. La implementación del auditor se ejecuta dentro de la imagen V3, no en el host. Se fija el registry público `https://registry.npmjs.org/`, se deshabilitan retries de fetch (`--fetch-retries=0`) y las configs global/usuario (`/dev/null`). El comando no usa `npm audit fix` ni modifica manifests.
6. El contenedor solicita metadata al registry npm mediante bridge. El grafo de dependencias de los manifests staging se envía al registry para construir la auditoría. No se descargan tarballs ni imágenes en esta etapa. No hay allowlist de dominios en la capa de red; la aplicación fija el registry HTTPS esperado y la restricción de red permanece como riesgo explícito.
7. El output JSON crudo se limita a 65,536 bytes y stderr se descarta. El auditor emite solo nombres/rangos validados, severidad, fix disponible, GHSA y conteos; nunca imprime URLs completas ni metadata npm cruda. El resumen final se limita a 8,192 bytes. Cualquier resultado inválido, exceso, timeout o error se clasifica y detiene.

Límites: un `image inspect`, un `docker run`, seis pruebas sintéticas, un `npm audit`, 120 s de timeout interno y 180 s total. Sin retries operativos o npm, F1, r9, `studiamatch-dev`, rebuild, cutover, limpieza, DB/SQL, secretos, push/PR/merge, GitHub, Cloudflare o deploy.

## Predicados y evidencia

- PASS técnico de auditoría: test marker exacto `V3_NPM_AUDIT_SYNTHETIC_PASS:6/6`, imagen exacta, reporte JSON válido, exit de npm 0/1 y resumen sanitizado íntegro.
- `verdict=HIGH_CRITICAL_PRESENT` no autoriza promover ni cortar tráfico. Requiere analizar los paquetes y preparar un cambio/rebuild distinto con validaciones y JIT aplicable.
- La salida esperada contiene `phase=synthetic-tests|error_code=OK`, `phase=npm-audit|error_code=OK` y una línea `summary=` limitada. Se incorpora como evidencia del corte; no registra secretos.
- El contenedor temporal se retira automáticamente. El directorio temporal de configuración se elimina en el trap. Si falla cualquier predicado, no se reintenta y no hay recursos persistentes que recuperar.

Esta aprobación solo cubre la consulta descrita. No suma puntos G01–G10 ni habilita cutover, r9, suites, correcciones de dependencia u operaciones remotas.
