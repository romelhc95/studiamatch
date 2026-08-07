# Registro Production Canary F10.8 - 2026-08-07

| Campo | Valor |
|---|---|
| ID | `EVID-H1-CANARY-F10.8-001` |
| Subfase | `F10.8` |
| Runs | `31157736479`, `31223623363` |
| Estado | `SECOND_CANARY_FAIL_CLOSED_FG1_EXIT1_RESTORE_NOOP` |
| Evidencia contractual | `EVID-H1-010=PENDING` |

## Resultado Sanitizado - Run `31157736479`

El Production Canary fue autorizado con aprobacion separada del environment
`Production` y se ejecuto sobre `main@529ca111f1fef40efb15676ad6f07d002a54ae92`.
FG1, el manifest pre-canary y el snapshot privado quedaron completados. FG2
harvest fallo de forma fail-closed por respuestas HTTP `403` de la fuente
externa; cleansing, enrichment, sync y FG3 quedaron `skipped`.

La identidad de la cohorte, URLs, dominios, UUIDs, hosts Supabase, secrets y
datos operativos no se documentan en esta evidencia.

## Recuperacion - Run `31157736479`

- Snapshot privado creado en el runner.
- Restore exacto completado.
- Segundo restore `--expect-noop` completado.
- Manifest `after-cleanup` equivalente al estado pre-canary.
- Environments Production y Production-Scheduled-FG1/2/3 conservaron
  `AUTOMATION_ENABLED=false` y `PRODUCTION_WRITERS_PAUSED=true`.

## Hallazgo De Observabilidad - Run `31157736479`

La verificacion posterior detecto URLs operativas en logs del run. No se
detectaron credenciales, hosts Supabase ni UUIDs en artifacts sanitizados, pero
la presencia de URLs en logs impide usar el run como evidencia positiva y exige
remediacion antes de cualquier retry.

## Resultado Sanitizado - Run `31223623363`

El segundo Production Canary fue autorizado de forma separada y se ejecuto sobre
`main@32526efadc21b734c58e47ff00f3a5be5b042f24` despues de promover la
remediacion de sanitizacion/source-access preflight. El workflow valido target
Production, candidate exacto, limites canonicos `5/5/3/3/3`, manifest pre-canary,
source-access preflight y snapshot privado. FG1 fallo fail-closed con exit code
`1` bajo runner redacted; FG2 harvest, cleansing, enrichment, sync y FG3 quedaron
`skipped`.

La identidad de la cohorte, URLs, dominios, UUIDs, hosts Supabase, secrets y
datos operativos no se documentan en esta evidencia.

## Recuperacion - Run `31223623363`

- Snapshot privado creado en el runner.
- Manifest pre/post/after-cleanup con conteos estables: `staging_total=5`,
  `staging_discovered=5`, `courses_active=3`, `cleansed_pending=0`,
  `enriched_pending=0`.
- Restore exacto completado con `after_matches_snapshot=true`.
- Segundo restore `--expect-noop` completado con `after_matches_snapshot=true`.
- Atestaciones non-cohort completadas con `non_cohort_attestations_match=true`.
- Upload de artifacts sanitizados completado.

## Accion Pendiente

El segundo canary no es evidencia positiva porque no completo FG1/FG2/FG3. El
diagnostico local identifico que FG1 usaba el slug de cohorte mutable en vez de
un source slug FG1 dedicado. La correccion local separa
`F10_PRODUCTION_CANARY_FG1_SOURCE_SLUG` de
`F10_PRODUCTION_CANARY_INSTITUTION_SLUG`, valida/maskea ambos y usa el source
slug solo en `discovery_institutions.py --source-slug`. Antes de declarar
`EVID-H1-010=VERIFIED` se requiere promover esa correccion a `main`, confirmar el
secret FG1 sin exponer su valor, y obtener un Production Canary completo con
`run_fg1=true`, `run_fg2=true`, `run_fg3=true`, `mutable_authorized=true`,
limites `5/5/3/3/3`, snapshot privado, restore exacto y segundo restore NOOP.
