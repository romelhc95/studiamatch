# Sistema DB Supabase

Estado factual al 2026-07-24. Este documento separa evidencia observada en remoto, evidencia Git y conclusiones derivadas. No contiene keys ni datos operativos.

Enlaces: [Indice](./00_INDICE.md) | [Arquitectura pipeline](./arquitectura_pipeline.md) | [Estado del proyecto](./estado_del_proyecto.md) | [Tarea Hito 1](./backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) | [Flujo release](./operaciones/flujo_release_minimo.md) | [Matriz DB](./operaciones/matriz_adopcion_db.md)

## Leyenda de evidencia

- `[REMOTE]`: observado con Supabase MCP sobre catalogos, policies, ACL, funciones, triggers, advisors o ledgers.
- `[GIT]`: observado en el repositorio actual.
- `[DERIVED]`: comparacion de evidencia REMOTE y GIT.

## Proyectos y roles

| Ambiente | Project ref | Uso | Estado observado |
|---|---|---|---|
| Free | `aqrldlmlszjtgpqiegaa` | Development y Certification | `[REMOTE]` PostgreSQL 17.6 |
| Pro | `xwhtiqmboljkshrtviyw` | Production | `[REMOTE]` PostgreSQL 17.6 |

`[REMOTE]` Roles relevantes, iguales en ambos proyectos:

- `anon` y `authenticated`: `NOLOGIN`, sin `BYPASSRLS`.
- `service_role`: `NOLOGIN`, con `BYPASSRLS`; solo backend y CI.
- `authenticator`: `LOGIN`, `NOINHERIT`; puede asumir los roles API.
- `canary_runner`: `NOLOGIN`, `NOINHERIT`, sin `BYPASSRLS`; existe en ambos.
- La inspeccion MCP fue realizada como `postgres`. No se consultaron ni registraron keys.

`[GIT/REMOTE]` La documentacion historica que indica PostgreSQL 15 esta desactualizada: ambos remotos usan 17.6.

## Cuatro estaciones y esquema publico

```text
staging_raw -> cleansed_programs -> enriched_programs -> courses
```

`[REMOTE]` Ambos proyectos tienen las cuatro tablas, FK por institucion, RLS habilitado y los gates `pipeline_ready`, `discovery_enabled`, `pipeline_enabled` y `production_enabled`. Tambien comparten la configuracion F121 en `institution_site_profiles`: `field_selectors`, `label_selectors`, `url_type_rules`, `extraction_transforms` y `extraction_confidence`.

`[REMOTE]` Diferencias de tabla relevantes:

- Solo Free: `_view_count_dedup`.
- Solo Pro: `crawler_exclusions`.
- `vector` 0.8.0 esta instalada en ambos, pero `enriched_programs.embedding` es `text`, no `vector`.

### Acceso efectivo

- `[REMOTE Free]` Las RPC ETL principales solo tienen `EXECUTE` para owner y `service_role`. `cleansed_programs` no tiene grants para `anon` ni `authenticated`. Las otras tablas ETL quedan cerradas por RLS para esos roles. `canary_runner` solo tiene lectura acotada por policies canary.
- `[REMOTE Free]` La lectura publica de `courses` exige `is_active`, `is_verified`, `publication_status = 'publicado'` y `production_enabled`.
- `[REMOTE Pro]` Las RPC ETL tambien son service-role-only por ACL, pero varias conservan `SECURITY DEFINER` y `search_path` mutable. Las tablas ETL tienen grants de tabla amplios para roles API; el acceso ordinario depende de RLS para fallar cerrado.
- `[REMOTE Pro]` La lectura publica de `courses` exige `is_active`, `is_verified` y `production_enabled`; no puede filtrar por `publication_status` porque Hito 1 no esta instalado.

## Hito 1: Free frente a Pro

`[REMOTE Free]` Hito 1 esta materializado:

- `courses`: `publication_status`, `data_quality_status`, `missing_fields`, `field_sources`, `manual_updated_at`, `is_sponsored`, `sponsorship_priority`, `sponsorship_label`.
- `leads`: `lead_source_type`.
- `ratings` y `reviews`: `moderation_status`, `moderated_at` y FK a `courses`.
- La lectura publica de cursos exige publicacion editorial.
- Ratings y reviews publicos exigen moderacion aprobada y curso publicable; no hay mutacion publica.
- Leads publicos tienen validacion de formato, curso elegible y `lead_source_type = 'organic'`.
- Existe `increment_view_count_v2`; el RPC legacy no es ejecutable por roles publicos.

`[REMOTE Pro]` Ninguna de las once columnas Hito 1 anteriores existe. Tampoco existen sus constraints, `_view_count_dedup` ni `increment_view_count_v2`. Ratings y reviews mantienen lectura e insercion `PUBLIC`; leads mantiene `WITH CHECK (true)`.

`[REMOTE Free]` Evidencia canonica Hito 1:

1. `hito1_editorial_quality_contract`
2. `hito1_st09_st10_rls_hardening`
3. `hito1_idempotency_check_conrelid`
4. `hito1_rls_versioned_idempotency`
5. `hito1_editorial_quality_authenticated_hardening`
6. `20260721_hito1_rls_reconciliation`

`[REMOTE Pro]` No hay entradas canonicas Hito 1.

## G1b: Free frente a Pro

`[REMOTE Free]` El ledger canonico contiene 13 entradas H00-H10 y correcciones:

- `20260718_h00_anonymize_leads_pii`
- `20260718_h01_secure_requeue_and_close_etl_rpcs`
- `20260718_h03_close_cleansed_programs_public_read`
- `20260718_h07_h04_contain_public_writes`
- `20260718_h02_harden_etl_functions_search_path`
- `20260718_h05_h06_remove_tests_revoke_triggers`
- `20260718_h10_updated_at_trigger_parity`
- `20260718_h04_w3_canonical_contract`
- `20260718_h08_drop_crawler_exclusions`
- `20260718_h07_w4_view_count_v2_secure`
- `20260718_correction_h01_h02_h10_lock_updated_at`
- `20260718_correction_h07_v2_dedup_h03_privileges`
- `20260718_wp05_ratings_reviews_grants_fix`

`[REMOTE Free]` Postcondiciones observables: RPC ETL service-role-only, funciones mutadoras con objetos calificados y `search_path = ''`, `unlock_*` y `mark_cleansed_processing` como invoker, requeue endurecido, `cleansed_programs` no publico, writes de ratings/reviews cerrados, view count legacy cerrado y `crawler_exclusions` ausente.

`[REMOTE Pro]` No hay entradas canonicas G1b. Persisten funciones ETL antiguas, view count legacy publico, writes publicos de ratings/reviews y `crawler_exclusions`.

## Ledgers y drift DB-as-Code

| Fuente | Free | Pro |
|---|---:|---:|
| `supabase_migrations.schema_migrations` canonico | 42 | 23 |
| `public.supabase_migrations` del proyecto | 41; todas `version=0` | 52; 15 `version=0` |
| `db/migrations/*.sql` en Git | 52 archivos | Los mismos 52 archivos |

`[GIT]` Los 52 SQL locales van de `20260412_dynamic_categories.sql` a `20260602_fase121_profile_pillar_extractors.sql`.

`[DERIVED]` El ledger de proyecto Pro contiene los 52 stems Git, pero esto no demuestra paridad: el ledger canonico solo tiene 23 entradas y Pro carece de Hito 1/G1b. El ledger de proyecto Free contiene 39 stems Git mas `20260723_pre_hito1_g1b_hardening` y `20260723_pre_hito1_g1b_ledger_reconciliation`.

`[GIT/REMOTE]` El SQL fuente de las migraciones canonicas Hito 1/G1b de julio no esta en el arbol Git actual. Sus entradas y postcondiciones remotas existen, pero la fuente debe considerarse `source_unavailable` hasta recuperar un artifact con checksum.

### Canary observado sin ledger demostrable

`[REMOTE]` Estas funciones scoped tienen el mismo SHA-256 en Free y Pro, pero no hay una entrada canonica canary identificable en Pro:

- `atomic_canary_sync`: `26ded2162905...`
- `atomic_cleansing_promote_scoped`: `a9c6be6ffab1...`
- `atomic_enrichment_promote_scoped`: `6fbdb01773fd...`
- `lock_staging_records_scoped`: `2789ae3ecbec...`

Se clasifican `observed_effective_unledgered`. `verify_release_canary_guards` diverge: Free `6a4a9ecbafd6...`; Pro `ad2aa03d99ac...`.

### Drift de RPC principal

`[REMOTE]` Definiciones SHA-256 y modo Free frente a Pro:

| Funcion | Free | Pro |
|---|---|---|
| `atomic_cleansing_promote` | `f2d7f26b7b87...`, path vacio | `edfcf5744dd2...`, path mutable |
| `atomic_enrichment_promote` | `799a3c70f138...` | `4f311bcc9155...` |
| `lock_staging_records` | `2c8638aa6884...`, path vacio | `4c734beb8ddf...`, path `public` |
| `lock_cleansed_records` | `2bdd0e2e0616...`, path vacio | `eeb44abdba55...`, path mutable |
| `mark_cleansed_processing` | `0f088d885430...`, invoker | `abaee58e6ef3...`, path mutable |
| `unlock_staging_record` | `cb5e1bb3ba17...`, invoker | `5bb48dccac88...`, definer/path mutable |
| `unlock_cleansed_record` | `38370aae7c54...`, invoker | `a9ff27652d3...`, definer/path mutable |
| `requeue_pipeline_records` | `c4f07f960704...`, path vacio | `9b1248ec11e9...`, path mutable |

## Snapshots Git obsoletos

`[GIT/REMOTE]` Estos archivos son snapshots historicos y no describen el estado Free actual:

- `db/restore_full_schema.sql`
- `db/production_init.sql`
- `db/PRODUCTION_MASTER.sql`

Contienen contratos pre-Hito/G1b, como `courses USING (true)`, writes de ratings/reviews y RPC sin hardening. Se consideran `superseded` como fuentes de restauracion y no deben reproducirse sobre ambientes actuales.

`[GIT/REMOTE]` La afirmacion historica de que `crawler_exclusions` fue eliminada en ambos ambientes es falsa para Pro: la tabla existe y tiene lectura para roles API.

## Caveats de seguridad y advisors

### Free

`[REMOTE Advisor]` Tres avisos informativos `rls_enabled_no_policy`: `_view_count_dedup`, `schema_repair_audit` y `supabase_migrations`. Los grants observados los mantienen cerrados para roles publicos.

- Remediation: [RLS enabled without policy](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy)

### Pro

`[REMOTE Advisor]` Caveats activos:

- Ocho funciones con `search_path` mutable: [function search path mutable](https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable).
- Leads con policies `WITH CHECK (true)`: [permissive RLS policy](https://supabase.com/docs/guides/database/database-linter?lint=0024_permissive_rls_policy).
- `increment_view_count` es `SECURITY DEFINER` y ejecutable por `anon` y `authenticated`: [anon executable](https://supabase.com/docs/guides/database/database-linter?lint=0028_anon_security_definer_function_executable) y [authenticated executable](https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable).
- `schema_repair_audit` y `supabase_migrations` tienen RLS sin policies: [RLS enabled without policy](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy).

`[REMOTE]` Caveats adicionales: mutacion publica efectiva de ratings/reviews, lectura sin moderacion, exposicion de `crawler_exclusions` y ACL de tabla mas amplias que el minimo.

### Ambos

- `exec_sql(text)` es `SECURITY DEFINER`, service-role-only y tiene la misma definicion en ambos. Es una superficie de alto impacto ante compromiso de la credencial backend.
- `service_role` omite RLS; nunca debe usarse en cliente.
- Varias tablas conservan grants mas amplios que sus policies. La seguridad depende de RLS y carece de defensa ACL minima.
- `canary_runner` no tiene login ni bypass, pero su rol DB no expira; el control temporal depende del JWT y de su emision.

## Requisitos forward-only para F6

1. Construir la adopcion por postcondicion y no por coincidencia de stems.
2. No editar, borrar ni reconstruir ledgers historicos; toda reconciliacion futura debe ser una migracion nueva.
3. Recuperar SQL Hito 1/G1b desde backups con checksum. Si no se demuestra la fuente, mantener `source_unavailable` y crear un reemplazo forward-only.
4. Mantener H00 como `historical_free_only` y excluirlo mecanicamente de todo manifest o glob Pro.
5. Separar schema/RLS/RPC del backfill editorial. Todo DML futuro debe ser acotado, idempotente y auditable.
6. No copiar entre ambientes `staging_raw`, `cleansed_programs`, `enriched_programs` ni `courses`. Pro genera sus propios datos operativos.
7. Consolidar G1b por postcondiciones: ACL service-role-only, owner/mode/search path, objetos calificados, cierre de ETL publico, requeue, `updated_at`, ratings/reviews y view count.
8. Clasificar H08/H09 de forma explicita: estan fuera de G1b minimo. La tabla legacy Pro no se elimina por replay implicito.
9. Versionar o clasificar la superficie canary existente sin copiar filas canary ni asumir paridad por hashes parciales.
10. No usar los snapshots Git obsoletos como baseline. Verificar PostgREST y frontend antes de exigir `publication_status` o revocar una superficie consumida.

La decision por artifact y ambiente se registra en la [matriz de adopcion DB](./operaciones/matriz_adopcion_db.md).
