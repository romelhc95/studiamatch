# H3REQ1 C03 integrado R9 — diagnóstico de PostgREST acotado

## Tareas, gates y candidato

- Ciclo activo: G07, integración local Pages/workerd + PostgreSQL 17 + PostgREST + Edge + C03.
- Checkout candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`; HEAD baseline: `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP al preparar R9: 55 rutas tracked modificadas, 4399 archivos untracked, 0 staged. Incluye WIP anterior; no se interpreta HEAD como inventario del candidato. El checkout original se conserva sin modificación.
- La autorización humana del 2026-10-10 comprende operaciones locales de H3 G01–G09 y los fixtures Docker/PG17 aislados, sin JIT documental adicional. No incluye secretos, servicios o datos operativos, operaciones remotas, Git de promoción, deploy ni cambios al engine.

## R8 consumido: resultado real

R8 terminó con exit 1 en `isolated-postgrest`. Antes del FAIL pasaron el snapshot/cache, imagen PostgreSQL 17.11, Pages/workerd `healthz`, bootstrap H2→Pro→H3, setup integrado y fixture sintético. El probe obtuvo `HTTP_503` en los 60 sondeos y no conservaba el código JSON del servidor. Failure-stop detuvo los tres servicios de ese run; Edge no se inició. Los estados post-stop fueron runtime 143, PG17 0 y PostgREST 255, OOM false; esos valores posteriores no explican la respuesta HTTP.

No se atribuye la causa a PostgREST, SQL, runtime ni Docker. Log sanitizado: [R8](h3req1_c03_integrated_run_2026-10-10_r8.log). Se preservaron los bytes del probe R8 (`h3req1_c03_postgrest_probe_r8_consumed.mjs`, SHA-256 `a3a6bacb4788a179653e6cb980856f4c8bde2be52d2431f62a4d0af0d7004206`) y su manifiesto consumido (`h3req1_c03_integrated_manifest_r8_consumed.sha256`, SHA-256 `a8ed50ca7d75c3d75a4e9667639c3fdfeb82d0026cd7f344bd48ef8a6fb41ad1`). R5–R8 runners, contratos, logs y recursos permanecen preservados.

## Reproducción y corrección focal

RED: la suite R9 se ejecutó antes del cambio del probe en el contenedor Node fijado, `network=none`, rootfs y mount del checkout read-only. Falló la nueva aserción: esperado `HTTP_503_PGRST000`, recibido `HTTP_503`; 10/11 subtests pasaron, exit 1. Esto reprodujo exactamente la pérdida de código del error que impedía clasificar R8.

GREEN: el probe usa `getReader({mode:'byob'})`, y cada lectura pide como máximo los bytes restantes hasta 8192. Al alcanzar el cap cancela y deja `HTTP_<status>` genérico; no realiza una lectura adicional para averiguar si el body excede el límite. Decodifica JSON estricto solo si el cuerpo termina antes del cap y emite únicamente `code` si coincide `PGRST[0-9]{3}` o SQLSTATE `[A-Z0-9]{5}`. Mensaje, detalles, hint, headers y cuerpo no se acceden ni se imprimen; cualquier stream no BYOB, código privado o JSON inválido queda en `HTTP_<status>`. Timeout existente de 2 s se conserva. El runner admite únicamente esas dos formas de sufijo en su regex cerrada; respuestas crudas o códigos privados producen `OUTPUT_REJECTED`.

Cobertura sintética: PGRST válido, SQLSTATE válido, código no permitido, JSON inválido, body de 8193 bytes del que se consumen como máximo 8192 y cancelación, stream Fetch `Response` real de Node y fallo de transporte. El resultado devuelto contiene solo fase/código y prueba que mensaje/details no aparecen.

La primera revisión independiente encontró un LOW: el lector default recibía un chunk completo >8192 antes de validar su longitud. Se corrigió con BYOB y prueba de consumo estricto; se pidió revisión estática final del nuevo digest antes del runtime.

## Validación local R9

- Suite contractual en imagen Node local fijada `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`, `network=none`, rootfs/mount read-only: 11/11 PASS, exit 0.
- `bash -n tests/h3req1_c03_integrated_drill_r9.sh`: PASS en contenedor aislado.
- ShellCheck oficial `koalaman/shellcheck:v0.11.0`, `-S warning`, contenedor aislado: PASS, exit 0.
- Los 63 inputs no modificados del manifiesto R8 verificaron 63/63 antes de transportar sus pins. Manifiesto R9 canonical, 64 entradas, verifica 64/64.
- Un intento del agregador local de manifest/sintaxis/tests terminó exit 1 por expansión de `$2` en el awk del propio comando de verificación; no alcanzó los checks posteriores. Se corrigió el agregador sin tocar fuentes; ejecución siguiente: manifest 64/64, bash syntax PASS y contrato 11/11. No es un hallazgo de producto ni se ocultó como PASS.
- Revisión independiente final de seguridad y de protocolo/SQL: ambas PASS sin blockers tras el cambio BYOB. La revisión de protocolo había señalado LOW por chunk mayor al límite con lector default; el código se corrigió, los bytes consumidos quedaron cubiertos por prueba y la revisión final confirmó el bound y fallback.

Pins R9:

- runner `tests/h3req1_c03_integrated_drill_r9.sh`: `905398c9964b2182726d97ffca0788b176198b3ecdce3ca0492d948f82084840`.
- contrato `tests/h3req1_c03_integrated_drill_r9_contract.test.mjs`: `8d8e5c9fa26731479a05fcacb2d2cc4f632a7ee8a261ca95de03e501aed34ba7`.
- probe `tests/h3req1_c03_postgrest_probe.mjs`: `92d419157a8669b889edf5cf78a5d54e31040076788d8a39ddf4123b501f69d7`.
- manifiesto canonical, 64 rutas: `6b0a469325b466a59211b3f6e50f16bce49910d78cad994068daa51caba13de9`.

## Entorno y recursos

- `studiamatch-dev` permanece `healthy`, imagen local `studiamatch-h3req1:20261009-v3`; no se usa como servicio de credenciales/prueba integrada.
- R8 conservó su source snapshot y volumen TLS sintético; redes internas `h3req1-c03-integrated-edge-20261010-r8` y `h3req1-c03-integrated-data-20261010-r8`; caches R4 son read-only. Sus contenedores están detenidos. Los recursos R8 no se reutilizan.
- R9 tendrá nombres/nonce/labels nuevos, imágenes locales fijadas con `--pull=never`, redes internas, PGDATA temporal, credenciales sintéticas, deadline 1800 s y stop-on-failure. Ningún `.env*`, cuenta, correo, DB cloud, egress de runtime o recurso ajeno participa.
- Recuperación: ante FAIL, stop solo de contenedores con JIT+manifest+nonce de R9; se preserva snapshot/TLS/cache y el log sanitizado. El siguiente ciclo usará la fase/código observado para una corrección mínima, sin aumentar sondeos ni reusar R8.

## Ejecución integrada R9 lista; runtime pendiente

```bash
/usr/bin/timeout --foreground --signal=INT --kill-after=60s 1800s \
  /bin/bash tests/h3req1_c03_integrated_drill_r9.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R9 \
  --manifest-sha256 6b0a469325b466a59211b3f6e50f16bce49910d78cad994068daa51caba13de9
```

La suite local y la revisión independiente final terminaron sin bloqueantes. R9 se ejecutó una vez con el comando fijado, timeout 1800 s, y terminó exit 1 en `isolated-postgrest`: los 60 sondeos devolvieron `HTTP_503_PGRST002`. El stop por ownership exacto terminó runtime 143, PG17 0 y PostgREST 255 (después del stop), OOM false; no se inició Edge. Resultado conservado en [log R9](h3req1_c03_integrated_run_2026-10-10_r9.log).

La documentación oficial PostgREST 13 describe PGRST002 como HTTP 503 durante consulta/construcción de schema cache cuando PostgreSQL no está disponible ([errores PostgREST 13](https://docs.postgrest.org/en/v13/references/errors.html#group-0-connection)). El código HTTP no contiene el SQLSTATE subyacente. R9 comprobó `pg_isready` local y ejecutó harness/fixtures con `psql` local antes de iniciar PostgREST, pero no comprobó conectividad TCP/autenticación desde la red integrada después del fallo; por tanto la causa concreta sigue desconocida y no se atribuye a PostgreSQL, SQL, PostgREST o Docker.

Siguiente paso: diagnóstico R10 focalizado al mismo predicado, con un test sintético del clasificador de logs, validación TCP/autenticación a PG usando credencial sintética y captura PostgREST limitada a log temporal de 1 MiB. Un filtro solo emitirá un SQLSTATE allowlisted de la línea schema-cache, nunca texto, JSON, query o mensaje; el recurso temporal se retirará tras guardar la evidencia sanitizada. No iniciar Edge ni alterar esquemas/contratos para obtener PASS. G07 sigue parcial; métricas sin cambio: 60% histórico y 6/9 local.
