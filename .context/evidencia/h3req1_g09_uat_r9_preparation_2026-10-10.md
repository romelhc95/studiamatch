# H3REQ1 G09 UAT R9 — preparación y resultado

Fecha: 2026-10-10. Candidato: `feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## R8 preservado y hallazgos

R8 ejecutó 48 casos, 144 viewports, cero retries; aprobaron 33/144 ejecuciones y
se guardaron 34/144 capturas. UAT-023 falló después de tres aserciones correctas
por `winnerName is not defined`: la variable se declaraba dentro del `try` y se
usaba después de ese bloque. UAT-035 cargó 31 respuestas HTTP 200, sin requests
fallidos ni errores de consola, y perdió el target del navegador mientras esperaba;
los casos restantes fallaron en cascada. El contenedor app terminó con exit 137
por el trap del runner; `OOMKilled=false`. La causa del cierre de Chromium aún no
está clasificada.

R8 permanece en `h3-expanded-r8`. Se preservaron 42 archivos entre capturas,
matriz, ejecuciones, manifest y logs; su manifiesto de integridad está en
`input-manifests/r8-preserved-evidence.sha256`, SHA-256
`5efdfa93c28738c88f99b76afba17195029b7dca038efe7804127870f7eccb07`.

## Cambio mínimo y diagnóstico

En `tests/h3_local_uat.mjs`, `winnerName` ahora vive en el scope que usa las
aserciones posteriores. El runner registra `page.crash` y desconexión inesperada
del browser como fase/caso/viewport/código, sin mensajes crudos. El evento
`browser.process()` no forma parte de la API disponible en el Playwright fijado;
se descartó esa instrumentación antes de ejecutar UAT. Un smoke de Chromium local
confirmó `isConnected()` y registro `disconnected`.

La suite conserva el catálogo 48×3, orden, cero retries y recursos 4 GiB/2 CPU,
512 PIDs y `/dev/shm` 128 MiB. R9 reutiliza el PG17 sintético interno fijado y
crea un contenedor app nuevo, con directorio de evidencia exclusivo; mantiene
read-only las fuentes y dependencias montadas. No usa `.env*`, cuentas,
credenciales ni servicios remotos.

## Evidencia previa a R9

- Rama/HEAD: esperados; WIP: 55 modificados, 649 untracked, 0 borrados.
- App R8: ID `63b1adc5c87d1d7fb5418e5144c5ef606c25ed14135d8ee554da86faaab8019f`,
  detenido, exit 137, no OOM, imagen `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- PG17: ID `ab792c23c9a6d4b32a5a2072e15f07714f1cfddc9e822db0a79851b39678ff5e`,
  corriendo, imagen `sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`.
- Red: `h3req1-g09-uat-20261010-r1`, `Internal=true`; DB sintética
  `h3_final_uat_g09_20261010_r1`: 15 membresías y 30 cursos.
- Runner R9: SHA-256 `c1129800feb44831291982c8dace0ac0fcb20929000416197030e6be1e150344`.
- Fuente UAT: SHA-256 `cf339c1f1c77e15b9e18477cb9acb731d641dbaa3b47e994f254bb944a859b42`.
- Bash syntax, Node syntax, ShellCheck 0.11.0 y `git diff --check` del cambio
  focal: PASS.

## Resultado R9

Pendiente de ejecución al crear esta nota. Añadir exit, resumen 48×3, capturas,
diagnóstico sanitizado del ciclo de vida del browser, hashes y recursos al terminar.
