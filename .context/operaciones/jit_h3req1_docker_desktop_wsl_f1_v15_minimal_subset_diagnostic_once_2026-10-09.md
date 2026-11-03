# JIT V15 — aislar el conjunto mínimo por eliminación acotada

Fecha: 2026-10-09. Estado: preparado; **requiere aprobación humana para una invocación**.

## Bloqueo demostrado y propósito

V14 probó cada una de las 25 expresiones allowlisted por separado en el fixture `present`:
las 25 dieron `OK`. El formato combinado dio `INSPECT_TEMPLATE_EVALUATION_ERROR` y el resumen
`FIELD_INTERACTION_ERROR`; por eso V14 no leyó F1 ni ejecutó r9. Este JIT no vuelve a ejecutar
solo el formato completo: en un mismo fixture sintético valida una vez que reproduce exactamente
el error V14 y, únicamente entonces, reduce el formato por eliminación de un campo por prueba.

El resultado será un conjunto **1-minimal por eliminación**: quitar cualquiera de sus campos
debe despejar el error exacto. El método no afirma mínimo cardinal global. Si el error exacto no
se reproduce, aparece otro error, se alcanza el límite o no se puede demostrar la minimalidad,
se detiene sin proponer una causa.

## Ficha de impacto

| Campo | Valor |
|---|---|
| Checkout / rama / HEAD | `/home/romel/src/studiamatch-h3req1-sync-20261002` / `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| Archivos propios | `f1_template_minimal_failure_v15_once.py`, `test_f1_template_minimum_reducer_v15.py`, `run_wsl_f1_v15_minimal_subset_diagnostic_once.sh` |
| Consumidores | Clasificador sintético C03 V15; no cambia rutas de producto, SQL, wire, BFF, Auth, roles, MFA, gateway o cuotas |
| Pruebas/evidencia preservadas | Resultado V14 y sus 25 probes aislados, fixtures V13, entradas C03 y evidencia histórica; no se reescriben ni invalidan |
| Persistencia | Un contenedor temporal con `--rm`, sin bind mounts ni volúmenes; no se lee ni escribe el volumen `studiamatch_node_modules` |
| Gates vigentes antes de esta invocación | G01=0/10 (harness C02 editorial pendiente); G02=10/10 (C03 SQL v3 exacto); G03–G10=0/10; total=10%; D01–D14=0/14. Esta invocación por sí sola no cierra un gate |
| Recuperación | Cleanup ownership-checked al fallar creación y `docker stop` del ID validado en `finally`; si cleanup falla, detenerse y preservar el recurso para inspección separada |

## Operaciones autorizables en esta invocación

1. Preflight no-root/TTY, checkout, rama, HEAD, ausencia de overrides Docker y verificación de
   pins/evidencia previa. La salida del runner se acepta solo como líneas sanitizadas
   `phase=…|error_code=…`, hasta 8192 bytes.
2. Reutilizar los fixtures puros ya fijados, validar la evidencia previa de atestación del
   endpoint Docker Desktop/WSL y usar el socket fijado por esa atestación; no se vuelve a
   identificar el daemon en vivo. Revisar read-only el prefijo V12. Si existe un residual,
   detenerse sin inspect, stop o rm.
3. Leer los labels de la imagen sintética fijada y exigir la condición allowlisted antes de crear
   el fixture. La imagen `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`
   tiene el mismo ID que `studiamatch-dev:local`. El JIT **sí reutiliza esa imagen compartida**;
   no inspecciona, monta, inicia, detiene, renombra ni cambia el contenedor existente
   `studiamatch-dev`, su volumen, tag o configuración.
4. Crear como máximo un container `h3req1-v12-template-<token>-present` desde esa imagen con
   `--pull=never`, `--network=none`, rootfs read-only, UID:GID `1001:1001`, capabilities retiradas,
   `no-new-privileges`, memoria/swap de 128 MiB, CPU 0.5, 64 PIDs y un tmpfs efímero de 96 MiB en
   `/snapshot`. No hereda Env del host, no monta archivos/secretos ni conecta servicios.
5. En ese mismo container, una lectura de baseline con el formato combinado fijado. Si termina
   correctamente o presenta otro código de evaluación de template, emitir solo
   `BASELINE_FAILURE_NOT_REPRODUCED` y detenerse. Los errores de transporte/daemon se informan
   con su fase y código sanitizados y también detienen el ciclo.
6. Solo tras el baseline exacto, efectuar como máximo 52 probes read-only de subconjuntos únicos
   (cada inspect con timeout de 5 s). El reductor cachea resultados, limita tanto las probes como
   las líneas de traza a 52, y el wrapper verifica el campo/lista allowlisted, el resumen, la
   cardinalidad y que cada campo incluido tuvo una eliminación que despejó el baseline.
7. Detener y retirar el único temporal por su ID validado. Fallo/timeout/cleanup fallido consume
   el JIT y detiene la operación; no hay retry.

El máximo de 52 probes más el baseline es un límite duro, no una meta. Con hasta 5 s por inspect,
timeout externo de 600 s y output de 8192 bytes. El único egress previsto es la API local de
Docker Desktop/WSL para lecturas y crear/retirar ese fixture; no hay pull, build, apt, pip, npm,
Playwright, red del contenedor, Git remoto, Cloudflare o Supabase.

## Fuera de alcance y gates posteriores

No prueba el mapa ausente, no lee F1, no ejecuta r9, no inicia Pages/workerd, Edge, PG17 o
PostgREST, no corre los 144 UAT ni onboarding 10/10, no limpia recursos históricos y no modifica
Docker/Compose, imágenes, pins, volúmenes, archivos de producto, SQL, secretos o servicios
remotos. El resultado por sí solo no arregla el formato combinado ni acredita runtime. Después
de obtener la combinación se preparará/revisará el cambio mínimo y un paquete JIT agrupado para
validar present/absent, negativos, F1 y r9; el run de r9 y las etapas siguientes quedan
condicionados a PASS exacto y autorización vigente.

## Revisión estática y pins

La revisión independiente detectó y se corrigió antes de esta solicitud: faltaba confirmar el
baseline exacto en el mismo fixture antes de reducir; se añadió esa condición y un test negativo
para códigos distintos. También se repineó el helper en el wrapper. La revisión final del paquete
actual y sus pruebas locales están registradas en la evidencia V15 enlazada abajo.

| Recurso | SHA-256 |
|---|---|
| Helper V15 | `05947152fcfb356c1ea8bc0a283eda3c3aad0c94f31e9844083fac2678a0f764` |
| Tests sintéticos V15 | `460a18aef0f391e1a479fbb4ce1cf41f387ea9266c5938e09087904741ddecf4` |
| Wrapper V15 | `765d1abefe11afad133bd7a2b4497c3f084e3cff3cdb7bea06b69b0551e6662d` |
| V14 JIT consumido | `60ba16f2b29919ef89869625360416cb87470a7e4ad374f7c1d4b763d9686f48` |
| V14 resultado consumido | `abf6be735583098f5a196b6d5284438aefcb8329adbd9601a73a6ed728c80940` |

## Solicitud concreta

Se solicita aprobar **una invocación única** de
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-V15-MINIMAL-SUBSET-DIAGNOSTIC-ONCE-20261009-V1`, con el
SHA-256 de este JIT indicado en la aprobación humana. Se ejecutará como `romel` no-root en una
terminal interactiva Ubuntu WSL, con `require_escalated` y sin `sudo`.

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v15_minimal_subset_diagnostic_once.sh'
readonly RUNNER_SHA256='765d1abefe11afad133bd7a2b4497c3f084e3cff3cdb7bea06b69b0551e6662d'
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
/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 600s /bin/bash "$RUNNER" 2>/dev/null
)
```
