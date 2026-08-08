# Registro Production Canary F10.8 - 2026-08-07

| Campo | Valor |
|---|---|
| ID | `EVID-H1-CANARY-F10.8-001` |
| Subfase | `F10.8` |
| Run | `31157736479` |
| Estado | `FAIL_CLOSED_HTTP_403_RESTORE_NOOP` |
| Evidencia contractual | `EVID-H1-010=PENDING` |

## Resultado Sanitizado

El Production Canary fue autorizado con aprobacion separada del environment
`Production` y se ejecuto sobre `main@529ca111f1fef40efb15676ad6f07d002a54ae92`.
FG1, el manifest pre-canary y el snapshot privado quedaron completados. FG2
harvest fallo de forma fail-closed por respuestas HTTP `403` de la fuente
externa; cleansing, enrichment, sync y FG3 quedaron `skipped`.

La identidad de la cohorte, URLs, dominios, UUIDs, hosts Supabase, secrets y
datos operativos no se documentan en esta evidencia.

## Recuperacion

- Snapshot privado creado en el runner.
- Restore exacto completado.
- Segundo restore `--expect-noop` completado.
- Manifest `after-cleanup` equivalente al estado pre-canary.
- Environments Production y Production-Scheduled-FG1/2/3 conservaron
  `AUTOMATION_ENABLED=false` y `PRODUCTION_WRITERS_PAUSED=true`.

## Hallazgo De Observabilidad

La verificacion posterior detecto URLs operativas en logs del run. No se
detectaron credenciales, hosts Supabase ni UUIDs en artifacts sanitizados, pero
la presencia de URLs en logs impide usar el run como evidencia positiva y exige
remediacion antes de cualquier retry.

## Accion Pendiente

Antes de un segundo Production Canary F10.8 se requiere promover a `main` una
remediacion que:

- elimine URLs, slugs, nombres, UUIDs y JSON de institucion de logs del canary;
- agregue source-access preflight read-only antes del snapshot;
- endurezca el manifest pre-canary con gates y perfil completos;
- mantenga artifacts exclusivamente sanitizados;
- preserve `EVID-H1-010=PENDING` hasta un canary completo PASS.

## Retry Completo - 2026-08-08

| Campo | Valor |
|---|---|
| Run | `31236936740` |
| Candidate | `main@705624a8ffa2f4fae0ffd7a958baa6205a6ae088` |
| Estado | `FAIL_CLOSED_FG2_CLEANSING_PROVENANCE_RESTORE_NOOP` |
| Evidencia contractual | `EVID-H1-010=PENDING` |

Resultado sanitizado:

- Target, candidate y limites `5/5/3/3/3`: PASS.
- Source-access preflight: PASS.
- Snapshot privado: PASS.
- FG1 one-source inventory: PASS.
- FG2 bounded harvest: PASS.
- FG2 bounded cleansing: FAIL con salida redactada y exit `1`.
- FG2 enrichment, FG2 sync y FG3: `skipped` por fail-closed previo.
- Restore exacto: PASS.
- Segundo restore `--expect-noop`: PASS.
- Manifest `after-cleanup` equivalente al estado pre-canary: PASS.

Diagnostico sanitizado:

La etapa FG2 harvest paso, pero cleansing fallo despues de promover tres filas
existentes. La causa localmente reproducida es que `atomic_cleansing_promote`
reencola filas por conflicto de URL sin fusionar `cleansed_programs.metadata`,
por lo que la verificacion de procedencia no encuentra
`f10_production_canary_run_id` en filas preexistentes. No se documentan URLs,
cohorte, UUIDs, hosts Supabase, secrets ni datos operativos.

Remediacion local validada:

- Migration forward-only `20260808_fase10_8_atomic_cleansing_provenance.sql`.
- Merge de metadata historica con metadata entrante durante `ON CONFLICT`.
- Transicion de `staging_raw` desde `pending` o `processing` a `processed`.
- `SECURITY DEFINER`, `SET search_path = pg_catalog` y execute solo para
  `service_role`.
- `restore_full_schema.sql` sincronizado con la definicion canonica.
- `db-sync-to-pro.yml` limitado a la migracion F10.8 con `--only`, sin
  `--manifest` ni `--validate-only`.
- Pruebas locales Docker/Linux y PostgreSQL 17 PASS.

Restricciones vigentes:

- No se ejecuto DDL/DML remoto en Free ni Pro.
- No se ejecuto otro Production Canary.
- No se habilitaron schedules ni writers programados.
- No hubo backfill ni cambios de secrets/environments.
