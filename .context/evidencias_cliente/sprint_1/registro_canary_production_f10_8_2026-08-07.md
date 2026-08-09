# Registro Production Canary F10.8 - 2026-08-07

| Campo | Valor |
|---|---|
| ID | `EVID-H1-CANARY-F10.8-001` |
| Subfase | `F10.8` |
| Runs | `31157736479`, `31223623363`, `31236936740`, `31269277219`, `31272290614` |
| Estado | `PRODUCTION_CANARY_PASS` |
| Evidencia contractual | `EVID-H1-010=VERIFIED` |

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
slug solo en `discovery_institutions.py --source-slug`. En ese corte, antes de
declarar `EVID-H1-010=VERIFIED` se requeria promover esa correccion a `main`,
confirmar el secret FG1 sin exponer su valor, y obtener un Production Canary
completo con `run_fg1=true`, `run_fg2=true`, `run_fg3=true`,
`mutable_authorized=true`, limites `5/5/3/3/3`, snapshot privado, restore exacto
y segundo restore NOOP. Ese requisito quedo cumplido posteriormente por PR #325 y
Production Canary `31272290614=PASS`.

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

- DDL remoto ejecutado solo en Free/Desarrollo para
  `20260808_fase10_8_atomic_cleansing_provenance` bajo autorizacion separada.
- No se ejecuto DDL/DML en Pro.
- No se ejecuto otro Production Canary.
- No se habilitaron schedules ni writers programados.
- No hubo backfill ni cambios de secrets/environments.

## DDL Free/Desarrollo - 2026-08-08

| Campo | Valor |
|---|---|
| Migracion | `20260808_fase10_8_atomic_cleansing_provenance` |
| Ambiente | Free/Desarrollo |
| Estado | `APPLIED_AND_READONLY_VERIFIED` |
| Alcance | `DDL_ONLY_FUNCTION_REPLACE_AND_ACL` |

Verificacion read-only post-DDL:

- Registro tecnico presente en `supabase_migrations.schema_migrations`.
- `public.atomic_cleansing_promote(uuid[], jsonb)` quedo `SECURITY DEFINER`.
- `search_path=pg_catalog` confirmado.
- Merge de metadata historica y entrante confirmado en la definicion.
- Transicion `staging_raw.status IN ('pending','processing')` confirmada.
- `anon` y `authenticated` sin `EXECUTE`.
- `service_role` con `EXECUTE`.
- Advisors de seguridad/performance solo reportaron notices informativos
  preexistentes/no atribuibles a esta remediacion.

Limites preservados:

- No hubo DML operativo, backfill ni procesamiento de programas.
- No hubo Pro, Production Canary, schedules ni cambios de secrets/environments.
- En ese corte, `EVID-H1-010` permanecia `PENDING` hasta canary completo PASS.

## Verify-Only Y Retry Completo - 2026-08-08

| Campo | Valor |
|---|---|
| PR verify-only | `#323` -> `main@5c7efaf417eba7f45bed45994a6249d03f609fc2` |
| PR FG2 deferred verify | `#324` -> `main@675ade43f41a2f5d04f05a40f9837b514a8705ce` |
| Tree | `90868898778a1039006e45b870fbc03e6e65291b` |
| DB Sync verify | `31268229878=PASS` |
| Pending migrations | `0` |
| Apply | `SKIPPED` |
| Target schema | `PASS` |
| FG2 deferred | `PASS` |
| UAT | `USER_PERSONAL_UAT=PASS` para SHA/tree indicado |

## Resultado Sanitizado - Run `31269277219`

El Production Canary completo fue autorizado con aprobacion separada del
`main@675ade43f41a2f5d04f05a40f9837b514a8705ce` con limites `5/5/3/3/3` y
`mutable_authorized=true`.

Resultado:

- Target, candidate y limites: PASS.
- Source-access preflight: PASS.
- Snapshot privado: PASS.
- FG1 one-source inventory: PASS.
- FG2 harvest, cleansing, enrichment y sync: PASS.
- FG3 integrity: PASS.
- Restore exacto: PASS.
- Segundo restore `--expect-noop`: FAIL por JSON truncado durante atestacion
  no-cohorte.
- Manifest after-cleanup: FAIL secundario con HTTP 521.
- Artifact sanitizado parcial: 4/6 manifests; artifact ID `9025228257`.

Diagnostico sanitizado:

La atestacion no-cohorte leia filas completas con `select=*` usando paginas de
1000 filas. En `staging_raw`, las filas no-cohorte contienen payloads grandes y
una respuesta alcanzo aproximadamente 8.1 MB, llegando truncada dentro de un
string JSON. El run falla correctamente en modo fail-closed y no acredita
`EVID-H1-010`. No se documentan URLs, cohorte, UUIDs, hosts Supabase, secrets ni
datos operativos.

Remediacion acotada:

- Paginar solo la atestacion no-cohorte con paginas pequenas.
- Conservar `columns="*"`, `order="id.asc"`, grupos `neq`/`is.null`, digest
  actual y snapshot schema.
- Mantener fail-closed ante JSON invalido, HTTP no exitoso o manifests
  incompletos.
- No ejecutar DDL/DML, backfill, schedules, writers ni cambios de
  secrets/environments.

`EVID-H1-010` permanecia `PENDING` hasta un nuevo Production Canary completo PASS
sobre un SHA/tree promovido y autorizado separadamente.

## Resultado Sanitizado - Run `31272290614`

| Campo | Valor |
|---|---|
| Run | `31272290614` |
| Candidate | `main@859d2f7d83f83950d10858fe27bd035febba7f68` |
| Tree | `ba7f6e74e88b2153aef1f4582bb3faa999c01a98` |
| Estado | `PASS` |
| Artifact | `9026139906` (`f10-production-canary-manifests`) |
| Artifact digest | `sha256:1a1a0fe3df7bbd03b74217be188fd58014257a5b2a5045ce63863260b73ec6ce` |
| Artifact expires | `2026-09-07T18:49:37Z` |
| Evidencia contractual | `EVID-H1-010=VERIFIED` |

El Production Canary completo fue autorizado con aprobacion separada del
environment `Production`, `mutable_stages=fg2_fg3`, `mutable_authorized=true` y
limites `5/5/3/3/3`.

Resultado:

- Target, candidate y limites: PASS.
- Production Supabase target guard: PASS.
- Source-access preflight: PASS.
- Snapshot privado: PASS.
- FG1 one-source inventory: PASS.
- FG2 harvest, cleansing, enrichment y sync: PASS.
- FG3 integrity: PASS.
- Restore exacto: PASS.
- Segundo restore `--expect-noop`: PASS.
- Manifest after-cleanup: PASS.
- Verificacion de manifests sanitizados: PASS.
- Artifact sanitizado completo: 6/6 manifests, artifact ID `9026139906`.

Atestacion sanitizada:

- `pre` y `after-cleanup` coinciden en counts, gates, contrato y limites.
- `restore_idempotent` reporta `expect_noop=true`, `after_matches_snapshot=true`,
  `non_cohort_attestations_match=true` y cero filas restauradas o eliminadas.
- Revision focalizada del artifact no encontro patrones comunes de secrets, URLs
  Supabase, URLs HTTP ni UUIDs.

No se documentan URLs, cohorte, UUIDs operativos, hosts Supabase, secrets ni datos
operativos. Este run acredita `EVID-H1-010=VERIFIED`; no acredita schedules ni
conformidad cliente.
