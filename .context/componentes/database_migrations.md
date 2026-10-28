# Ledger de migrations SQL locales

> Generado el 2026-10-12 desde nombres presentes en el checkout candidato. El orden lexicográfico coincide con el prefijo de fecha, no certifica orden de aplicación en ningún ambiente. Los cuerpos y comentarios de cada migration definen el cambio. No se ejecutó SQL.


## 202604

- [20260412_dynamic_categories.sql](../../db/migrations/20260412_dynamic_categories.sql)
- [20260413_social_proof.sql](../../db/migrations/20260413_social_proof.sql)
- [20260414_fase18_saneamiento.sql](../../db/migrations/20260414_fase18_saneamiento.sql)
- [20260414_optimize_search.sql](../../db/migrations/20260414_optimize_search.sql)
- [20260415_market_salaries.sql](../../db/migrations/20260415_market_salaries.sql)
- [20260416_seniority_roi_update.sql](../../db/migrations/20260416_seniority_roi_update.sql)
- [20260428_rls_intermediate_tables.sql](../../db/migrations/20260428_rls_intermediate_tables.sql)
- [20260429_discard_null_offnames.sql](../../db/migrations/20260429_discard_null_offnames.sql)
- [20260429_fix_p0003_duplicate_rows.sql](../../db/migrations/20260429_fix_p0003_duplicate_rows.sql)
- [20260429_rpc_ambiguous_fix.sql](../../db/migrations/20260429_rpc_ambiguous_fix.sql)
- [20260430_fix_search_path_mutable.sql](../../db/migrations/20260430_fix_search_path_mutable.sql)
- [20260430_intermediate_tables_ddl.sql](../../db/migrations/20260430_intermediate_tables_ddl.sql)
- [20260430_move_extensions_to_schema.sql](../../db/migrations/20260430_move_extensions_to_schema.sql)
- [20260430_rls_hardening.sql](../../db/migrations/20260430_rls_hardening.sql)

## 202605

- [20260501_fix_cleansing_loop.sql](../../db/migrations/20260501_fix_cleansing_loop.sql)
- [20260501_institution_site_profiles.sql](../../db/migrations/20260501_institution_site_profiles.sql)
- [20260501_production_full_replace.sql](../../db/migrations/20260501_production_full_replace.sql)
- [20260503_FASE74_drop_crawler_exclusions.sql](../../db/migrations/20260503_FASE74_drop_crawler_exclusions.sql)
- [20260503_FASE74_seed_pro_profiles.sql](../../db/migrations/20260503_FASE74_seed_pro_profiles.sql)
- [20260503_fase73_start_date.sql](../../db/migrations/20260503_fase73_start_date.sql)
- [20260504_fase62_sync_pro.sql](../../db/migrations/20260504_fase62_sync_pro.sql)
- [20260504_fase75_pipeline_ready.sql](../../db/migrations/20260504_fase75_pipeline_ready.sql)
- [20260504_fase75_requeue_skipped.sql](../../db/migrations/20260504_fase75_requeue_skipped.sql)
- [20260505_add_provider_tracking.sql](../../db/migrations/20260505_add_provider_tracking.sql)
- [20260505_fase79bd_circuitbreaker_guardrails.sql](../../db/migrations/20260505_fase79bd_circuitbreaker_guardrails.sql)
- [20260505_fase79c_noise_patterns.sql](../../db/migrations/20260505_fase79c_noise_patterns.sql)
- [20260505_fase80_rls_hardening.sql](../../db/migrations/20260505_fase80_rls_hardening.sql)
- [20260505_fase82_view_count.sql](../../db/migrations/20260505_fase82_view_count.sql)
- [20260506_fase90_dmc_profile_fix.sql](../../db/migrations/20260506_fase90_dmc_profile_fix.sql)
- [20260507_fase93_dmc_profile_config.sql](../../db/migrations/20260507_fase93_dmc_profile_config.sql)
- [20260507_fase94_dmc_woocommerce_metadata.sql](../../db/migrations/20260507_fase94_dmc_woocommerce_metadata.sql)
- [20260509_ulima_pipeline_ready.sql](../../db/migrations/20260509_ulima_pipeline_ready.sql)
- [20260510_pro_schema_sync.sql](../../db/migrations/20260510_pro_schema_sync.sql)
- [20260512_fix_lock_staging_records_plpgsql.sql](../../db/migrations/20260512_fix_lock_staging_records_plpgsql.sql)
- [20260512_normalize_syllabus_text.sql](../../db/migrations/20260512_normalize_syllabus_text.sql)
- [20260524_fase100_institution_gates.sql](../../db/migrations/20260524_fase100_institution_gates.sql)
- [20260524_fase100_production_gate_enforcement.sql](../../db/migrations/20260524_fase100_production_gate_enforcement.sql)
- [20260525_fase112_pro_fk_courses_category.sql](../../db/migrations/20260525_fase112_pro_fk_courses_category.sql)
- [20260525_fase113_pro_rls_and_rpc_sync.sql](../../db/migrations/20260525_fase113_pro_rls_and_rpc_sync.sql)
- [20260525_fase114_security_contract_hardening.sql](../../db/migrations/20260525_fase114_security_contract_hardening.sql)
- [20260525_fase115_authenticated_profile_hardening.sql](../../db/migrations/20260525_fase115_authenticated_profile_hardening.sql)
- [20260525_fase116_public_grant_defense_in_depth.sql](../../db/migrations/20260525_fase116_public_grant_defense_in_depth.sql)
- [20260526_fase117_fix_category_trigger.sql](../../db/migrations/20260526_fase117_fix_category_trigger.sql)
- [20260526_fase119_extensible_categories.sql](../../db/migrations/20260526_fase119_extensible_categories.sql)
- [20260526_fase120_category_coverage_keywords.sql](../../db/migrations/20260526_fase120_category_coverage_keywords.sql)
- [20260526_fase121_category_catalog_parity.sql](../../db/migrations/20260526_fase121_category_catalog_parity.sql)
- [20260526_ulima_pipeline_activation.sql](../../db/migrations/20260526_ulima_pipeline_activation.sql)
- [20260531_fase121_auto_generated.sql](../../db/migrations/20260531_fase121_auto_generated.sql)
- [20260531_fase67b_email_infrastructure.sql](../../db/migrations/20260531_fase67b_email_infrastructure.sql)
- [20260531_fase67b_secure_trigger.sql](../../db/migrations/20260531_fase67b_secure_trigger.sql)
- [20260531_fix_pro_leads_columns.sql](../../db/migrations/20260531_fix_pro_leads_columns.sql)

## 202606

- [20260602_fase121_profile_pillar_extractors.sql](../../db/migrations/20260602_fase121_profile_pillar_extractors.sql)

## 202608

- [20260808_fase10_8_atomic_cleansing_provenance.sql](../../db/migrations/20260808_fase10_8_atomic_cleansing_provenance.sql)
- [20260825_h2_editorial_layer.sql](../../db/migrations/20260825_h2_editorial_layer.sql)
- [20260825_h2_editorial_layer_allowlist_fix.sql](../../db/migrations/20260825_h2_editorial_layer_allowlist_fix.sql)
- [20260825_h2_editorial_layer_grants_fix.sql](../../db/migrations/20260825_h2_editorial_layer_grants_fix.sql)
- [20260825_h2_editorial_layer_start_date_view_fix.sql](../../db/migrations/20260825_h2_editorial_layer_start_date_view_fix.sql)
- [20260826_h2_development_legacy_public_compat.sql](../../db/migrations/20260826_h2_development_legacy_public_compat.sql)
- [20260826_h2_editorial_layer_forward_fix.sql](../../db/migrations/20260826_h2_editorial_layer_forward_fix.sql)
- [20260826_h2_public_effective_view_public_fields_fix.sql](../../db/migrations/20260826_h2_public_effective_view_public_fields_fix.sql)
- [20260826_h2_security_advisor_remediation.sql](../../db/migrations/20260826_h2_security_advisor_remediation.sql)
- [20260826_h2_seed_editorial_field_definitions.sql](../../db/migrations/20260826_h2_seed_editorial_field_definitions.sql)
- [20260827_h2_pro_backfill_editorial_state.sql](../../db/migrations/20260827_h2_pro_backfill_editorial_state.sql)
- [20260827_h2_pro_capture_legacy_cohort.sql](../../db/migrations/20260827_h2_pro_capture_legacy_cohort.sql)
- [20260827_h2_pro_contract_legacy_cohort.sql](../../db/migrations/20260827_h2_pro_contract_legacy_cohort.sql)
- [20260827_h2_pro_contract_public_reader.sql](../../db/migrations/20260827_h2_pro_contract_public_reader.sql)
- [20260827_h2_pro_enable_legacy_cohort_rls.sql](../../db/migrations/20260827_h2_pro_enable_legacy_cohort_rls.sql)
- [20260827_h2_pro_expand_schema_compat.sql](../../db/migrations/20260827_h2_pro_expand_schema_compat.sql)
- [20260827_h2_pro_rollback_public_reader_contract.sql](../../db/migrations/20260827_h2_pro_rollback_public_reader_contract.sql)
- [20260827_h2_pro_seed_editorial_field_definitions.sql](../../db/migrations/20260827_h2_pro_seed_editorial_field_definitions.sql)
- [20260828_h3_admin_auth.sql](../../db/migrations/20260828_h3_admin_auth.sql)
- [20260828_h3_admin_course_queue_view.sql](../../db/migrations/20260828_h3_admin_course_queue_view.sql)
- [20260828_h3_admin_editorial_reader_rpc.sql](../../db/migrations/20260828_h3_admin_editorial_reader_rpc.sql)
- [20260828_h3_admin_editorial_rpc.sql](../../db/migrations/20260828_h3_admin_editorial_rpc.sql)
- [20260828_h3_admin_queue_rpc.sql](../../db/migrations/20260828_h3_admin_queue_rpc.sql)
- [20260829_h3_rbac_users.sql](../../db/migrations/20260829_h3_rbac_users.sql)
- [20260830_h3_expanded_contract.sql](../../db/migrations/20260830_h3_expanded_contract.sql)

## 202609

- [20260902_h3_pr_contract.sql](../../db/migrations/20260902_h3_pr_contract.sql)
- [20260903_h3_rbac_contract_fix.sql](../../db/migrations/20260903_h3_rbac_contract_fix.sql)
- [20260918_h3_invitation_flow_persistence.sql](../../db/migrations/20260918_h3_invitation_flow_persistence.sql)
- [20260919_h3_invitation_auth_token_delta.sql](../../db/migrations/20260919_h3_invitation_auth_token_delta.sql)
- [20260920_h3_invitation_edge_runtime.sql](../../db/migrations/20260920_h3_invitation_edge_runtime.sql)
- [20260921_h3_invitation_onboarding_rpc.sql](../../db/migrations/20260921_h3_invitation_onboarding_rpc.sql)
- [20260924_h3_onboarding_rbac_hardening.sql](../../db/migrations/20260924_h3_onboarding_rbac_hardening.sql)
- [20260924_h3_onboarding_rbac_hardening_fix.sql](../../db/migrations/20260924_h3_onboarding_rbac_hardening_fix.sql)
- [20260925_h3_admin_members_onboarding_reader.sql](../../db/migrations/20260925_h3_admin_members_onboarding_reader.sql)
- [20260925_h3_legacy_member_creation_guard.sql](../../db/migrations/20260925_h3_legacy_member_creation_guard.sql)
- [20260927_h3_admin_queue_facets_filter.sql](../../db/migrations/20260927_h3_admin_queue_facets_filter.sql)
- [20260927_h3_publication_visibility_contract.sql](../../db/migrations/20260927_h3_publication_visibility_contract.sql)
- [20260928_h3_invitation_accept_email_regex_fix.sql](../../db/migrations/20260928_h3_invitation_accept_email_regex_fix.sql)

## 202610

- [20261001_h3_course_editorial_audit_availability.sql](../../db/migrations/20261001_h3_course_editorial_audit_availability.sql)
- [20261001_h3_invitation_reservation_compensation.sql](../../db/migrations/20261001_h3_invitation_reservation_compensation.sql)
- [20261002_h3_admin_quota_expand.sql](../../db/migrations/20261002_h3_admin_quota_expand.sql)
- [20261002_h3_admin_quotas.sql](../../db/migrations/20261002_h3_admin_quotas.sql)
- [20261004_h3_admin_queue_first_null_guard.sql](../../db/migrations/20261004_h3_admin_queue_first_null_guard.sql)
- [20261004_h3_admin_rpc_signed_gateway_expand.sql](../../db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql)
- [20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql](../../db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql)
- [20261010_h3_admin_members_service_select.sql](../../db/migrations/20261010_h3_admin_members_service_select.sql)
- [20261025_h3_admin_members_onboarding_forbidden_status.sql](../../db/migrations/20261025_h3_admin_members_onboarding_forbidden_status.sql)
- [20261028_h3_editorial_publication_snapshot.sql](../../db/migrations/20261028_h3_editorial_publication_snapshot.sql)
- [20261028_h3_public_price_projection_empty_price_guard.sql](../../db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql)

### Migration 20261028 — H3 editorial publication snapshot

`20261028_h3_editorial_publication_snapshot.sql` es un delta forward-only local:
añade columnas nullable para la instantánea publicada, conserva firmas y gates de
autorización, y no rellena masivamente cursos operativos. Los rows existentes sin
snapshot mantienen fallback legacy; en la primera corrección se captura su valor
público previo antes de cambiar el borrador. La edición `user` usa la allowlist
completa; solo Admin actualiza la instantánea al publicar. Los grants de lectura
pública se limitan a la vista efectiva. Ejecutada dos veces sobre PG17 sintético en
Docker; ninguna base Supabase recibió DDL. Ver [checkpoint CA4](../evidencia/h3req1_editorial_contract_2026-10-28.md).

### Migration 20261028 — H3 public price projection empty-price guard

`20261028_h3_public_price_projection_empty_price_guard.sql` es un fix
forward-only de `private.h2_public_courses_effective()`: reemplaza el único cast
conocido de `published_editorial_values.price_pen` por una conversión condicionada
a un formato decimal acotado (hasta 63 dígitos enteros y 63 fraccionarios). Un valor
vacío, inválido o sobredimensionado se proyecta como SQL `NULL`
para que un dato de precio no invalide el catálogo público completo. Si la definición
remota no contiene exactamente el fragmento esperado, la migración falla cerrada.
Reafirma los grants de lectura existentes y no altera datos de cursos ni snapshots.

El harness sintético PG17 ejecuta la migración dos veces y comprueba precios vacíos,
inválidos, JSON null, decimal en el límite, overflow y fallback sin snapshot, además de ACL,
`SECURITY DEFINER` y `search_path`. El SQL queda preparado para una JIT futura:
no se aplicó a Supabase. Al no cambiar columnas ni callers, el fix puede aplicarse
antes de revalidar el deployment compatible; no requiere rebuild ni deploy manual.
Rollback: preparar y aprobar un fix forward que restaure la lectura previa solo tras
confirmar que ya no hay snapshots incompatibles; no borrar datos ni auditoría. Ver
[checkpoint R1–R4 y fix](../evidencia/h3req1_editorial_contract_2026-10-28.md).

## Fichas exactas y relaciones por migration

Las fichas siguientes asignan cada migration a su propio anchor. El objeto/identifier map procede de SQL local y del barrido léxico de tests; los nombres de tests localizan posibles aserciones, no son resultados de ejecución. Los archivos son DB-as-code. R15 leyó metadata y ledger de Pro, pero no obtuvo un diff exhaustivo del baseline ni metadata legible de Free; la aplicación de cada objeto remoto sigue pendiente. Ver [evidencia R15](../evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md#supabase).

### migration-20260412-dynamic-categories

**Path:** [`20260412_dynamic_categories.sql`](../../db/migrations/20260412_dynamic_categories.sql)

**Propósito/por qué:** ========================================== MIGRACIÓN: Catálogo Dinámico de Categorías Fecha: 2026-04-12 Descripción: Creación de tablas categories, category_rules y trigger de auto-asignación con Diseño Híbrido. Diseño Híbrido: Clasificació

**Contrato y datos:** table: categories, category_rules; alter: categories, category_rules, courses; function: fn_auto_assign_category; trigger: tr_auto_assign_category.  Targets DML observados: INSERT INTO categories, INSERT INTO category_rules, UPDATE courses. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_runtime.mjs`, `tests/h3_admin_quota_uat.mjs`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260413-social-proof

**Path:** [`20260413_social_proof.sql`](../../db/migrations/20260413_social_proof.sql)

**Propósito/por qué:** Migration: 20260413_social_proof.sql Description: Creates ratings and reviews tables for the Social Proof System with RLS policies

**Contrato y datos:** table: ratings, reviews; alter: ratings, reviews.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/test_h2_development_legacy_compat.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260414-fase18-saneamiento

**Path:** [`20260414_fase18_saneamiento.sql`](../../db/migrations/20260414_fase18_saneamiento.sql)

**Propósito/por qué:** ============================================================================== FASE 18: Saneamiento de Huérfanos y Actualizaciones de Arquitectura ==============================================================================

**Contrato y datos:** table: institutions; alter: courses.  Targets DML observados: INSERT INTO public.categories, INSERT INTO public.category_rules, UPDATE public.courses. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_runtime.mjs`, `tests/h3_admin_quota_uat.mjs`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260414-optimize-search

**Path:** [`20260414_optimize_search.sql`](../../db/migrations/20260414_optimize_search.sql)

**Propósito/por qué:** MIGRACIÓN: Optimización de Búsqueda FECHA: 2026-04-14 DESCRIPCIÓN: Habilita pg_trgm y crea un índice GIN en courses.name para búsqueda difusa (fuzzy search).

**Contrato y datos:** index: idx_courses_name_trgm.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/mobile_usability.spec.ts`, `tests/quality_audit.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260415-market-salaries

**Path:** [`20260415_market_salaries.sql`](../../db/migrations/20260415_market_salaries.sql)

**Propósito/por qué:** ========================================== MIGRACIÓN: Market Salaries Baseline Fecha: 2026-04-15 Descripción: Creación de la tabla market_salaries para el cálculo dinámico del ROI. Basado en investigación de mercado proyectada para Abril 20

**Contrato y datos:** table: market_salaries.  Targets DML observados: INSERT INTO public.market_salaries. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_runtime.mjs`, `tests/h3_admin_quota_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260416-seniority-roi-update

**Path:** [`20260416_seniority_roi_update.sql`](../../db/migrations/20260416_seniority_roi_update.sql)

**Propósito/por qué:** ========================================== MIGRACIÓN: Seniority Level & ROI Update Fecha: 2026-04-16 Descripción: Inferencia de Seniority y actualización masiva de expected_monthly_salary. ==========================================

**Contrato y datos:** alter: courses, market_salaries.  Targets DML observados: UPDATE public.market_salaries, UPDATE public.courses. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/mobile_usability.spec.ts`, `tests/quality_audit.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260428-rls-intermediate-tables

**Path:** [`20260428_rls_intermediate_tables.sql`](../../db/migrations/20260428_rls_intermediate_tables.sql)

**Propósito/por qué:** Migration: RLS Policies for Intermediate ETL Tables + RPC Functions Fase 53: Correcciones P0 (Seguridad e Integridad) Fecha: 2026-04-28 1. Habilita RLS en las 4 tablas intermedias que no tenían políticas 2. Crea políticas de seguridad: solo

**Contrato y datos:** alter: cleansed_programs, crawler_exclusions, enriched_programs, staging_raw; function: atomic_cleansing_promote, atomic_enrichment_promote, lock_cleansed_records, lock_staging_records, unlock_cleansed_record, unlock_staging_record.  Targets DML observados: UPDATE staging_raw, UPDATE cleansed_programs, INSERT INTO cleansed_programs, INSERT INTO enriched_programs. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_local_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_from_h2_pro_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260429-discard-null-offnames

**Path:** [`20260429_discard_null_offnames.sql`](../../db/migrations/20260429_discard_null_offnames.sql)

**Propósito/por qué:** ============================================================ FASE 59 P1-5: Descarte de enriched_programs sin official_name Contexto: 24 registros en enriched_programs tienen official_name=NULL. Sus cleansed_programs correspondientes tampoco

**Contrato y datos:** DML/DDL targets: UPDATE enriched_programs.  Targets DML observados: UPDATE enriched_programs. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** sin identificador de test localizado en el scope. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260429-fix-p0003-duplicate-rows

**Path:** [`20260429_fix_p0003_duplicate_rows.sql`](../../db/migrations/20260429_fix_p0003_duplicate_rows.sql)

**Propósito/por qué:** ============================================================ FASE 59 P1-6: Fix RPC P0003 "query returned more than one row" en atomic_cleansing_promote Bug: Si p_cleansed_data contiene 2+ items con la misma URL (ej: trailing-slash normaliza

**Contrato y datos:** function: atomic_cleansing_promote, atomic_enrichment_promote.  Targets DML observados: INSERT INTO cleansed_programs, UPDATE staging_raw, INSERT INTO enriched_programs, UPDATE cleansed_programs. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/h3_uat_functional_catalog_seed.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260429-rpc-ambiguous-fix

**Path:** [`20260429_rpc_ambiguous_fix.sql`](../../db/migrations/20260429_rpc_ambiguous_fix.sql)

**Propósito/por qué:** ============================================================ FASE 57: Pipeline RPC Fixes Corrige 3 bugs en funciones SQL del pipeline: 1. Columnas ambiguas en lock_staging_records y lock_cleansed_records 2. Cast float → INT en duration_mont

**Contrato y datos:** function: atomic_enrichment_promote, lock_cleansed_records, lock_staging_records.  Targets DML observados: UPDATE staging_raw, UPDATE cleansed_programs, INSERT INTO enriched_programs. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/h3_uat_functional_catalog_seed.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260430-fix-search-path-mutable

**Path:** [`20260430_fix_search_path_mutable.sql`](../../db/migrations/20260430_fix_search_path_mutable.sql)

**Propósito/por qué:** ============================================================ Migration: Fix function_search_path_mutable — Fase 32A (Prioridad 2) Project: StudIAMatch (Dev Free: YOUR_FREE_PROJECT_REF) Date: 2026-04-30 Description: Agrega SET search_path = 

**Contrato y datos:** function: atomic_cleansing_promote, atomic_enrichment_promote, fn_auto_assign_category, lock_cleansed_records, lock_staging_records, unlock_cleansed_record, unlock_staging_record, update_updated_at_column.  Targets DML observados: UPDATE staging_raw, UPDATE cleansed_programs, INSERT INTO cleansed_programs, INSERT INTO enriched_programs. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_invitation_reservation_concurrency.sh`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/h3_uat_functional_catalog_seed.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260430-intermediate-tables-ddl

**Path:** [`20260430_intermediate_tables_ddl.sql`](../../db/migrations/20260430_intermediate_tables_ddl.sql)

**Propósito/por qué:** ============================================================ FASE 51: Versionado de DDL — 4 Tablas Intermedias del Pipeline Estas tablas fueron creadas originalmente en Supabase Dashboard sin DDL versionado en el repositorio. Este archivo e

**Contrato y datos:** table: cleansed_programs, crawler_exclusions, enriched_programs, staging_raw; index: idx_cleansed_programs_staging, idx_cleansed_programs_status, idx_cleansed_programs_url, idx_crawler_exclusions_active, idx_crawler_exclusions_institution, idx_enriched_programs_cleansed, idx_enriched_programs_status, idx_enriched_programs_url, idx_staging_raw_institution_status, idx_staging_raw_status, idx_staging_raw_url.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_local_uat.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h3_invitation_edge_runtime_harness.sql`, `tests/sql/h3_invitation_onboarding_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_pg17_harness_local.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260430-move-extensions-to-schema

**Path:** [`20260430_move_extensions_to_schema.sql`](../../db/migrations/20260430_move_extensions_to_schema.sql)

**Propósito/por qué:** Migration: Move pg_trgm and vector to extensions schema Date: 2026-04-30 Description: Mueve extensiones pg_trgm y vector de schema public a extensions. El search_path por defecto de Supabase ya incluye extensions, por lo que no se requiere 

**Contrato y datos:** DML/DDL targets: ALTER EXTENSION pg_trgm SET SCHEMA extensions, ALTER EXTENSION vector SET SCHEMA extensions.  Targets DML observados: ALTER EXTENSION pg_trgm SET SCHEMA extensions, ALTER EXTENSION vector SET SCHEMA extensions. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** sin identificador de test localizado en el scope. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260430-rls-hardening

**Path:** [`20260430_rls_hardening.sql`](../../db/migrations/20260430_rls_hardening.sql)

**Propósito/por qué:** ============================================================ Migration: RLS Hardening — Fase 32A Project: StudIAMatch (Dev Free: YOUR_FREE_PROJECT_REF) Date: 2026-04-30 Description: Habilitar RLS en 8 tablas sin protección, crear policies d

**Contrato y datos:** alter: categories, category_rules, courses, institutions, leads, market_salaries, ratings, reviews.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260501-fix-cleansing-loop

**Path:** [`20260501_fix_cleansing_loop.sql`](../../db/migrations/20260501_fix_cleansing_loop.sql)

**Propósito/por qué:** Migration: 20260501_fix_cleansing_loop.sql Fase 66: Fix pipeline cleansing infinite loop Fix A: lock_staging_records ahora SETEA status='processing' atomically (antes era SELECT-only, requiriendo mark_records_processing() que nunca se llama

**Contrato y datos:** function: atomic_cleansing_promote, lock_staging_records.  Targets DML observados: UPDATE staging_raw, INSERT INTO cleansed_programs. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/h3_uat_functional_catalog_seed.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260501-institution-site-profiles

**Path:** [`20260501_institution_site_profiles.sql`](../../db/migrations/20260501_institution_site_profiles.sql)

**Propósito/por qué:** Migration: 20260501_institution_site_profiles.sql Fase 61: Site Profiles — consolidate exclusion + discovery + extraction config per institution Replaces crawler_exclusions with institution_site_profiles.exclusion_patterns (JSONB)

**Contrato y datos:** table: institution_site_profiles; alter: institution_site_profiles; function: update_updated_at; index: idx_profiles_institution; policy: profiles_select_authenticated, profiles_service_role; trigger: set_updated_at.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260501-production-full-replace

**Path:** [`20260501_production_full_replace.sql`](../../db/migrations/20260501_production_full_replace.sql)

**Propósito/por qué:** ============================================================ MIGRATION: Production Full Replace (Supabase Pro) Project: StudIAMatch Date: 2026-05-01 Target: zogdcvlqxanzqbvkkdar FULL REPLACE: Drops & recreates intermediate ETL tables + rati

**Contrato y datos:** table: cleansed_programs, crawler_exclusions, enriched_programs, ratings, reviews, staging_raw; alter: cleansed_programs, crawler_exclusions, enriched_programs, ratings, reviews, staging_raw; function: atomic_cleansing_promote, atomic_enrichment_promote, fn_auto_assign_category, lock_cleansed_records, lock_staging_records, unlock_cleansed_record, unlock_staging_record, update_updated_at_column; index: idx_cleansed_programs_staging, idx_cleansed_programs_status, idx_cleansed_programs_url, idx_courses_url_unique, idx_crawler_exclusions_active, idx_crawler_exclusions_institution, idx_crawler_exclusions_pattern_inst, idx_enriched_programs_cleansed, idx_enriched_programs_status, idx_enriched_programs_url, idx_enriched_programs_url_unique, idx_staging_raw_institution_status, idx_staging_raw_status, idx_staging_raw_url; trigger: tr_auto_assign_category, tr_enriched_programs_updated_at.  Targets DML observados: UPDATE staging_raw, UPDATE cleansed_programs, INSERT INTO cleansed_programs, INSERT INTO enriched_programs. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/mobile_usability.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260503-FASE74-drop-crawler-exclusions

**Path:** [`20260503_FASE74_drop_crawler_exclusions.sql`](../../db/migrations/20260503_FASE74_drop_crawler_exclusions.sql)

**Propósito/por qué:** Migration: Fase 74 — DROP crawler_exclusions (replaced by institution_site_profiles.exclusion_patterns) Run in Supabase Dashboard > SQL Editor on BOTH Free and Pro PREREQUISITE: institution_site_profiles must have exclusion_patterns populat

**Contrato y datos:** relation_targets: crawler_exclusions, institution_site_profiles.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/sql/h3req1_pipeline_postgrest_pg17_setup_r1.sql`, `tests/test_fase09_9_certification_canary.py`, `tests/test_fase10_production_canary.py`, `tests/test_h2_pro_migration_controls.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260503-FASE74-seed-pro-profiles

**Path:** [`20260503_FASE74_seed_pro_profiles.sql`](../../db/migrations/20260503_FASE74_seed_pro_profiles.sql)

**Propósito/por qué:** Migration: Fase 74 — Create + Seed institution_site_profiles in Pro PREREQUISITE: Run this in Supabase Dashboard > SQL Editor for the PRODUCTION project Includes: CREATE TABLE (if not exists) + RLS + indexes + 10 profile INSERTs

**Contrato y datos:** table: institution_site_profiles; alter: institution_site_profiles; function: update_updated_at; index: idx_profiles_institution; trigger: set_updated_at.  Targets DML observados: INSERT INTO public.institution_site_profiles. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_local_uat.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_invitation_edge_runtime_harness.sql`, `tests/sql/h3_invitation_onboarding_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260503-fase73-start-date

**Path:** [`20260503_fase73_start_date.sql`](../../db/migrations/20260503_fase73_start_date.sql)

**Propósito/por qué:** Fase 73: Filtrado por Fecha Expirada Agrega columna start_date DATE a courses para filtrado de programas expirados (>90d). También agrega start_date a enriched_programs como columna estructurada.

**Contrato y datos:** alter: courses, enriched_programs; index: idx_courses_start_date.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/mobile_usability.spec.ts`, `tests/quality_audit.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260504-fase62-sync-pro

**Path:** [`20260504_fase62_sync_pro.sql`](../../db/migrations/20260504_fase62_sync_pro.sql)

**Propósito/por qué:** Fase 62+75: Agregar columnas faltantes a Pro DB APLICADO via Supabase Dashboard 2026-05-03 SDLC: Aprobado @SDLC-Chief

**Contrato y datos:** alter: institution_site_profiles; index: idx_profiles_pipeline_ready.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/sql/h3req1_pipeline_postgrest_pg17_setup_r1.sql`, `tests/test_fase09_9_certification_canary.py`, `tests/test_fase10_production_canary.py`, `tests/test_h2_editorial_migration.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260504-fase75-pipeline-ready

**Path:** [`20260504_fase75_pipeline_ready.sql`](../../db/migrations/20260504_fase75_pipeline_ready.sql)

**Propósito/por qué:** Fase 75: Exclusion Gate + Noise Sentinel v2 Agrega pipeline_ready gate y allowed_url_patterns (whitelist positiva)

**Contrato y datos:** alter: institution_site_profiles; index: idx_profiles_pipeline_ready.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/sql/h3req1_pipeline_postgrest_pg17_setup_r1.sql`, `tests/test_fase09_9_certification_canary.py`, `tests/test_fase10_production_canary.py`, `tests/test_h2_editorial_migration.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260504-fase75-requeue-skipped

**Path:** [`20260504_fase75_requeue_skipped.sql`](../../db/migrations/20260504_fase75_requeue_skipped.sql)

**Propósito/por qué:** Fase 75: Re-queue records skipped by pipeline_ready gate Permite resetear registros marcados como 'skipped' cuando una institucion se habilita con pipeline_ready=true USO: 1. Setear pipeline_ready=true para la institucion 2. Ejecutar: SELEC

**Contrato y datos:** function: requeue_pipeline_records.  Targets DML observados: UPDATE staging_raw, UPDATE cleansed_programs, UPDATE enriched_programs. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_local_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_from_h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_pg17_harness_local.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260505-add-provider-tracking

**Path:** [`20260505_add_provider_tracking.sql`](../../db/migrations/20260505_add_provider_tracking.sql)

**Propósito/por qué:** Fase 79A: Add provider tracking columns to enriched_programs and courses Permite distinguir datos enriquecidos por LLM real vs smart mock

**Contrato y datos:** alter: courses, enriched_programs.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/mobile_usability.spec.ts`, `tests/quality_audit.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260505-fase79bd-circuitbreaker-guardrails

**Path:** [`20260505_fase79bd_circuitbreaker_guardrails.sql`](../../db/migrations/20260505_fase79bd_circuitbreaker_guardrails.sql)

**Propósito/por qué:** =================================================================== Fase 79B: Circuit Breaker por Institucion Agrega columnas para control de errores consecutivos por perfil. =================================================================

**Contrato y datos:** alter: institution_site_profiles; function: repair_jsonb_array, repair_jsonb_object, validate_institution_site_profiles_jsonb; trigger: trg_validate_institution_site_profiles_jsonb.  Targets DML observados: UPDATE institution_site_profiles. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/sql/h3req1_pipeline_postgrest_pg17_setup_r1.sql`, `tests/test_fase09_9_certification_canary.py`, `tests/test_fase10_production_canary.py`, `tests/test_h2_editorial_migration.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260505-fase79c-noise-patterns

**Path:** [`20260505_fase79c_noise_patterns.sql`](../../db/migrations/20260505_fase79c_noise_patterns.sql)

**Propósito/por qué:** Fase 79C: Noise Patterns Centralizados Mueve patrones de ruido hardcodeados a JSONB en institution_site_profiles Consolidando 3 fuentes: sync_vector_worker.py + cleansing_worker.py (HTML + name)

**Contrato y datos:** alter: institution_site_profiles.  Targets DML observados: UPDATE institution_site_profiles. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/sql/h3req1_pipeline_postgrest_pg17_setup_r1.sql`, `tests/test_fase09_9_certification_canary.py`, `tests/test_fase10_production_canary.py`, `tests/test_h2_pro_migration_controls.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260505-fase80-rls-hardening

**Path:** [`20260505_fase80_rls_hardening.sql`](../../db/migrations/20260505_fase80_rls_hardening.sql)

**Propósito/por qué:** Fase 80A: RLS Hardening + Column-Level Security + Validación Aplicado vía supabase_apply_migration en Free (aqrldlmlszjtgpqiegaa) y Pro (nglyqraaalxbincabbzw)

**Contrato y datos:** policy: courses_select_public, leads_insert_public.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/mobile_usability.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260505-fase82-view-count

**Path:** [`20260505_fase82_view_count.sql`](../../db/migrations/20260505_fase82_view_count.sql)

**Propósito/por qué:** Fase 82A: Schema Enhancement — View Counter + Comparison Count Apply on Free (desarrollo) → Certificacion → Pro (produccion)

**Contrato y datos:** alter: courses; function: increment_view_count.  Targets DML observados: UPDATE courses. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/mobile_usability.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260506-fase90-dmc-profile-fix

**Path:** [`20260506_fase90_dmc_profile_fix.sql`](../../db/migrations/20260506_fase90_dmc_profile_fix.sql)

**Propósito/por qué:** Fase 90: DMC Profile Fix — WooCommerce selectors + exclusiones Cambia catalog_link_selector de Elementor (0 resultados) a WooCommerce correcto. Agrega exclusiones para URLs transaccionales WooCommerce. Genérico: el mecanismo institution_sit

**Contrato y datos:** DML/DDL targets: UPDATE institution_site_profiles.  Targets DML observados: UPDATE institution_site_profiles. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** sin identificador de test localizado en el scope. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260507-fase93-dmc-profile-config

**Path:** [`20260507_fase93_dmc_profile_config.sql`](../../db/migrations/20260507_fase93_dmc_profile_config.sql)

**Propósito/por qué:** Fase 93: DMC Harvester — Section Keywords + H4 Extractor Configura section_keywords, field_defaults, seed_urls, price/duration regex, title_prefix_removals, y activa pipeline_ready para DMC. Basado en análisis real de https://dmc.pe/product

**Contrato y datos:** DML/DDL targets: UPDATE institution_site_profiles.  Targets DML observados: UPDATE institution_site_profiles. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** sin identificador de test localizado en el scope. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260507-fase94-dmc-woocommerce-metadata

**Path:** [`20260507_fase94_dmc_woocommerce_metadata.sql`](../../db/migrations/20260507_fase94_dmc_woocommerce_metadata.sql)

**Propósito/por qué:** Fase 94: DMC WooCommerce Structured Data Extraction for Pillar Enrichment Agrega campus por defecto al perfil DMC

**Contrato y datos:** DML/DDL targets: UPDATE institution_site_profiles.  Targets DML observados: UPDATE institution_site_profiles. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** sin identificador de test localizado en el scope. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260509-ulima-pipeline-ready

**Path:** [`20260509_ulima_pipeline_ready.sql`](../../db/migrations/20260509_ulima_pipeline_ready.sql)

**Propósito/por qué:** Migration: 20260509_ulima_pipeline_ready.sql Activa Universidad de Lima en el pipeline con extracción mejorada. Basado en análisis de URLs proporcionadas por el usuario (102 programas). ======================================================

**Contrato y datos:** DML/DDL targets: UPDATE institution_site_profiles, UPDATE staging_raw.  Targets DML observados: UPDATE institution_site_profiles, UPDATE staging_raw. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** sin identificador de test localizado en el scope. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260510-pro-schema-sync

**Path:** [`20260510_pro_schema_sync.sql`](../../db/migrations/20260510_pro_schema_sync.sql)

**Propósito/por qué:** =================================================================== Migration: 20260510_pro_schema_sync.sql Fase 95: Pro Schema Sync — corrige 8 diferencias estructurales entre Free y Pro para que FG2 pueda ejecutarse en producción. Incluye

**Contrato y datos:** alter: courses, institution_site_profiles; function: atomic_enrichment_promote, exec_sql, repair_jsonb_array, repair_jsonb_object, validate_institution_site_profiles_jsonb; index: idx_courses_start_date; trigger: trg_validate_institution_site_profiles_jsonb.  Targets DML observados: UPDATE institution_site_profiles, INSERT INTO enriched_programs, UPDATE cleansed_programs, ALTER EXTENSION vector SET SCHEMA extensions, ALTER EXTENSION pg_trgm SET SCHEMA extensions. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/mobile_usability.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260512-fix-lock-staging-records-plpgsql

**Path:** [`20260512_fix_lock_staging_records_plpgsql.sql`](../../db/migrations/20260512_fix_lock_staging_records_plpgsql.sql)

**Propósito/por qué:** Migration: 20260512_fix_lock_staging_records_plpgsql Fix RPC lock_staging_records: migrate to plpgsql and fully qualify columns.

**Contrato y datos:** function: lock_staging_records.  Targets DML observados: UPDATE staging_raw. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/test_fase09_9_certification_canary.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260512-normalize-syllabus-text

**Path:** [`20260512_normalize_syllabus_text.sql`](../../db/migrations/20260512_normalize_syllabus_text.sql)

**Propósito/por qué:** Migration: 20260512_normalize_syllabus_text Normalize existing JSON-like syllabus payloads into readable text. Handles object JSON ({...}) and array JSON ([...]) and then enforces CHECK.

**Contrato y datos:** alter: courses.  Targets DML observados: UPDATE courses. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/mobile_usability.spec.ts`, `tests/quality_audit.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260524-fase100-institution-gates

**Path:** [`20260524_fase100_institution_gates.sql`](../../db/migrations/20260524_fase100_institution_gates.sql)

**Propósito/por qué:** Fase 100: explicit institution gates for discovery, pipeline and production. `pipeline_ready` remains as a temporary compatibility fallback in code.

**Contrato y datos:** alter: institution_site_profiles.  Targets DML observados: UPDATE public.institution_site_profiles. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/sql/h3req1_pipeline_postgrest_pg17_setup_r1.sql`, `tests/test_fase09_9_certification_canary.py`, `tests/test_fase10_production_canary.py`, `tests/test_h2_editorial_migration.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260524-fase100-production-gate-enforcement

**Path:** [`20260524_fase100_production_gate_enforcement.sql`](../../db/migrations/20260524_fase100_production_gate_enforcement.sql)

**Propósito/por qué:** Fase 100: enforce production_enabled for public course visibility.

**Contrato y datos:** function: deactivate_courses_when_production_disabled; policy: courses_select_authenticated, courses_select_public; trigger: trg_deactivate_courses_when_production_disabled.  Targets DML observados: UPDATE public.courses. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260525-fase112-pro-fk-courses-category

**Path:** [`20260525_fase112_pro_fk_courses_category.sql`](../../db/migrations/20260525_fase112_pro_fk_courses_category.sql)

**Propósito/por qué:** Fase 112: FK courses_category_id_fkey for PostgREST embedded resources. PostgREST requires a declared FK to resolve categories(name) in course queries.

**Contrato y datos:** table: schema_repair_audit; alter: courses.  Targets DML observados: INSERT INTO public.schema_repair_audit, UPDATE public.courses. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/mobile_usability.spec.ts`, `tests/quality_audit.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260525-fase113-pro-rls-and-rpc-sync

**Path:** [`20260525_fase113_pro_rls_and_rpc_sync.sql`](../../db/migrations/20260525_fase113_pro_rls_and_rpc_sync.sql)

**Propósito/por qué:** Fase 113: Version RLS policy and sync atomic_enrichment_promote RPC. Closes production drift found after Fase 111.

**Contrato y datos:** function: atomic_enrichment_promote; policy: profiles_select_public.  Targets DML observados: INSERT INTO public.enriched_programs, UPDATE public.cleansed_programs. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_local_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_from_h2_pro_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260525-fase114-security-contract-hardening

**Path:** [`20260525_fase114_security_contract_hardening.sql`](../../db/migrations/20260525_fase114_security_contract_hardening.sql)

**Propósito/por qué:** Fase 114: Security hardening for Fases 112-113 contracts. Prevents public execution of SECURITY DEFINER RPCs and limits public profile exposure.

**Contrato y datos:** policy: profiles_select_public.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_typecheck.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_runtime_server.mjs`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260525-fase115-authenticated-profile-hardening

**Path:** [`20260525_fase115_authenticated_profile_hardening.sql`](../../db/migrations/20260525_fase115_authenticated_profile_hardening.sql)

**Propósito/por qué:** Fase 115: Restrict authenticated profile exposure. Keeps institution_site_profiles usable for production gates without exposing scraper config.

**Contrato y datos:** table: schema_repair_audit; policy: profiles_select_authenticated.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260525-fase116-public-grant-defense-in-depth

**Path:** [`20260525_fase116_public_grant_defense_in_depth.sql`](../../db/migrations/20260525_fase116_public_grant_defense_in_depth.sql)

**Propósito/por qué:** Fase 116: Defense-in-depth against accidental PUBLIC grants. Keeps future institution profile configuration private by default.

**Contrato y datos:** relation_targets: institution_site_profiles, schema_repair_audit.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/sql/h3req1_pipeline_postgrest_pg17_setup_r1.sql`, `tests/test_fase09_9_certification_canary.py`, `tests/test_fase10_production_canary.py`, `tests/test_h2_pro_migration_controls.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260526-fase117-fix-category-trigger

**Path:** [`20260526_fase117_fix_category_trigger.sql`](../../db/migrations/20260526_fase117_fix_category_trigger.sql)

**Propósito/por qué:** Fase 117: fix auto category trigger word-boundary regex and UPDATE firing.

**Contrato y datos:** function: fn_auto_assign_category; trigger: tr_auto_assign_category.  Targets DML observados: UPDATE public.courses. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/mobile_usability.spec.ts`, `tests/quality_audit.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260526-fase119-extensible-categories

**Path:** [`20260526_fase119_extensible_categories.sql`](../../db/migrations/20260526_fase119_extensible_categories.sql)

**Propósito/por qué:** Fase 119: extend category, keyword and salary catalogs without code changes.

**Contrato y datos:** relation_targets: CONFLICT, cat.  Targets DML observados: INSERT INTO public.categories, INSERT INTO public.category_rules, INSERT INTO public.market_salaries, UPDATE public.courses. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_invitation_reservation_concurrency.sh`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/h3_uat_functional_catalog_seed.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260526-fase120-category-coverage-keywords

**Path:** [`20260526_fase120_category_coverage_keywords.sql`](../../db/migrations/20260526_fase120_category_coverage_keywords.sql)

**Propósito/por qué:** Fase 120: close coverage gaps found by category_coverage_audit.

**Contrato y datos:** relation_targets: CONFLICT, cat.  Targets DML observados: INSERT INTO public.category_rules, UPDATE public.courses. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_invitation_reservation_concurrency.sh`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/h3_uat_functional_catalog_seed.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260526-fase121-category-catalog-parity

**Path:** [`20260526_fase121_category_catalog_parity.sql`](../../db/migrations/20260526_fase121_category_catalog_parity.sql)

**Propósito/por qué:** Fase 121: normalize category catalog names and restore missing base categories.

**Contrato y datos:** relation_targets: CONFLICT, cat.  Targets DML observados: UPDATE public.categories, UPDATE public.courses, UPDATE public.category_rules, DELETE FROM public.market_salaries, UPDATE public.market_salaries, DELETE FROM public.categories, INSERT INTO public.categories, INSERT INTO public.category_rules. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_invitation_reservation_concurrency.sh`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/h3_uat_functional_catalog_seed.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260526-ulima-pipeline-activation

**Path:** [`20260526_ulima_pipeline_activation.sql`](../../db/migrations/20260526_ulima_pipeline_activation.sql)

**Propósito/por qué:** Activate Universidad de Lima for the post-Fase-100 gated pipeline.

**Contrato y datos:** DML/DDL targets: UPDATE public.institution_site_profiles, UPDATE public.staging_raw.  Targets DML observados: UPDATE public.institution_site_profiles, UPDATE public.staging_raw. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** sin identificador de test localizado en el scope. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260531-fase121-auto-generated

**Path:** [`20260531_fase121_auto_generated.sql`](../../db/migrations/20260531_fase121_auto_generated.sql)

**Propósito/por qué:** Fase 121: Auto-Deteccion de Sitio en Harvester Agrega columna auto_generated para distinguir perfiles creados automaticamente de perfiles revisados por humanos.

**Contrato y datos:** alter: institution_site_profiles.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/sql/h3req1_pipeline_postgrest_pg17_setup_r1.sql`, `tests/test_fase09_9_certification_canary.py`, `tests/test_fase10_production_canary.py`, `tests/test_h2_editorial_migration.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260531-fase67b-email-infrastructure

**Path:** [`20260531_fase67b_email_infrastructure.sql`](../../db/migrations/20260531_fase67b_email_infrastructure.sql)

**Propósito/por qué:** Fase 67B: Email infrastructure — email_log, contact_email, trigger, pg_net Enables email notifications when a lead is created.

**Contrato y datos:** table: email_log; alter: email_log, institutions; function: notify_new_lead; index: idx_email_log_lead_id, idx_email_log_status; policy: email_log_select_authenticated, email_log_service_role; trigger: trg_notify_new_lead.  Targets DML observados: INSERT INTO public.email_log. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260531-fase67b-secure-trigger

**Path:** [`20260531_fase67b_secure_trigger.sql`](../../db/migrations/20260531_fase67b_secure_trigger.sql)

**Propósito/por qué:** Fase 67B v2: Secure trigger — zero hardcoded credentials Trigger queries course + institution data via SECURITY DEFINER, passes complete payload to Edge Function. No DB queries inside Edge Function.

**Contrato y datos:** function: notify_new_lead.  Targets DML observados: INSERT INTO public.email_log. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** sin identificador de test localizado en el scope. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260531-fix-pro-leads-columns

**Path:** [`20260531_fix_pro_leads_columns.sql`](../../db/migrations/20260531_fix_pro_leads_columns.sql)

**Propósito/por qué:** Fix: Pro leads table missing columns sent by frontend forms The CourseDetailClient.tsx and HomeContent.tsx send extra fields that didn't exist in Pro's leads table (only in Free).

**Contrato y datos:** alter: leads.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3req1_pipeline_postgrest_pg17_setup_r1.sql`, `tests/test_h2_editorial_migration.py`, `tests/test_h2_writer_scan.py`, `tests/test_requirement_client_source_validation.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260602-fase121-profile-pillar-extractors

**Path:** [`20260602_fase121_profile_pillar_extractors.sql`](../../db/migrations/20260602_fase121_profile_pillar_extractors.sql)

**Propósito/por qué:** Fase 121: Extraccion configurable de 14 pilares por institucion y segmento URL. DB-as-Code: agrega contrato JSONB para selectores, labels, overrides y confianza.

**Contrato y datos:** alter: institution_site_profiles.  Targets DML observados: UPDATE public.institution_site_profiles. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/sql/h3req1_pipeline_postgrest_pg17_setup_r1.sql`, `tests/test_fase09_9_certification_canary.py`, `tests/test_fase10_production_canary.py`, `tests/test_h2_editorial_migration.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260808-fase10-8-atomic-cleansing-provenance

**Path:** [`20260808_fase10_8_atomic_cleansing_provenance.sql`](../../db/migrations/20260808_fase10_8_atomic_cleansing_provenance.sql)

**Propósito/por qué:** F10.8: preserve cleansing canary provenance on URL conflicts. Production Canary run 31236936740 showed that atomic_cleansing_promote requeued existing cleansed_programs rows but kept their old metadata, so the post-RPC provenance check coul

**Contrato y datos:** function: atomic_cleansing_promote.  Targets DML observados: INSERT INTO public.cleansed_programs, UPDATE public.staging_raw. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_local_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_from_h2_pro_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260825-h2-editorial-layer

**Path:** [`20260825_h2_editorial_layer.sql`](../../db/migrations/20260825_h2_editorial_layer.sql)

**Propósito/por qué:** H2: Editorial layer for course publication and quality state. Scope: Free/Development DDL only under DDL-H2-EDITORIAL-LAYER-FREE. No backfill, Pro apply, writers, schedules, canaries, or deploys are authorized here.

**Contrato y datos:** table: course_editorial_audit, course_editorial_state, editorial_field_definitions; alter: course_editorial_audit, course_editorial_state, editorial_field_definitions; view: courses_public_effective; index: idx_course_editorial_audit_course_created, idx_course_editorial_state_sponsored, idx_course_editorial_state_status, idx_editorial_field_definitions_public; policy: course_editorial_audit_service_insert, course_editorial_audit_service_select, course_editorial_state_public_effective_select, course_editorial_state_service_all, editorial_field_definitions_public_select, editorial_field_definitions_service_all.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260825-h2-editorial-layer-allowlist-fix

**Path:** [`20260825_h2_editorial_layer_allowlist_fix.sql`](../../db/migrations/20260825_h2_editorial_layer_allowlist_fix.sql)

**Propósito/por qué:** H2: align manual_overrides allowlist with pipeline-owned start_date. Scope: Free/Development DDL only under DDL-H2-EDITORIAL-LAYER-FREE. This migration performs no DML/backfill.

**Contrato y datos:** alter: course_editorial_state.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_pg17_harness_local.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/h3_uat_functional_catalog_seed.sql`, `tests/sql/h3_uat_pipeline_course_seed.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260825-h2-editorial-layer-grants-fix

**Path:** [`20260825_h2_editorial_layer_grants_fix.sql`](../../db/migrations/20260825_h2_editorial_layer_grants_fix.sql)

**Propósito/por qué:** H2: tighten effective grants after editorial layer creation. Scope: Free/Development DDL only under DDL-H2-EDITORIAL-LAYER-FREE. This migration fixes effective service_role grants; it performs no DML/backfill.

**Contrato y datos:** relation_targets: course_editorial_audit, course_editorial_state, courses_public_effective, editorial_field_definitions, service_role.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_local_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_from_h2_pro_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260825-h2-editorial-layer-start-date-view-fix

**Path:** [`20260825_h2_editorial_layer_start_date_view_fix.sql`](../../db/migrations/20260825_h2_editorial_layer_start_date_view_fix.sql)

**Propósito/por qué:** H2: remove unsafe DATE cast from the public effective view. Scope: Free/Development DDL only under DDL-H2-EDITORIAL-LAYER-FREE. This migration performs no DML/backfill.

**Contrato y datos:** view: courses_public_effective.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_from_h2_pro_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260826-h2-development-legacy-public-compat

**Path:** [`20260826_h2_development_legacy_public_compat.sql`](../../db/migrations/20260826_h2_development_legacy_public_compat.sql)

**Propósito/por qué:** H2: development compatibility cohort for transparent public catalog transition. Scope: Free/Development compatibility DDL+DML only under explicit JIT. No Pro, production, schedules, canaries, deploys, or broad publication are authorized her

**Contrato y datos:** table: h2_legacy_public_course_cohort; view: courses_public_effective; function: h2_public_courses_effective.  Targets DML observados: INSERT INTO private.h2_legacy_public_course_cohort. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260826-h2-editorial-layer-forward-fix

**Path:** [`20260826_h2_editorial_layer_forward_fix.sql`](../../db/migrations/20260826_h2_editorial_layer_forward_fix.sql)

**Propósito/por qué:** H2: forward-only hardening for the editorial layer. Scope: local PR payload only. Remote apply requires a new JIT DDL approval. No backfill, Pro apply, schedules, canaries, deploys, or mass publication here.

**Contrato y datos:** alter: course_editorial_audit, course_editorial_state, courses; view: courses_public_effective; function: h2_update_course_quality, prevent_course_editorial_audit_mutation; index: idx_course_editorial_audit_request_id, idx_courses_slug_global_h2; policy: course_editorial_state_public_effective_select; trigger: prevent_course_editorial_audit_delete, prevent_course_editorial_audit_update.  Targets DML observados: INSERT INTO public.course_editorial_state, INSERT INTO public.course_editorial_audit. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260826-h2-public-effective-view-public-fields-fix

**Path:** [`20260826_h2_public_effective_view_public_fields_fix.sql`](../../db/migrations/20260826_h2_public_effective_view_public_fields_fix.sql)

**Propósito/por qué:** H2: remove private editorial fields from the public effective course surface. Scope: Free DDL remediation only. Remote apply requires explicit JIT DDL approval. No DML, seed, backfill, Pro, writers, schedules, canaries, deploys, push, PR, o

**Contrato y datos:** view: courses_public_effective; function: h2_public_courses_effective.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_from_h2_pro_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260826-h2-security-advisor-remediation

**Path:** [`20260826_h2_security_advisor_remediation.sql`](../../db/migrations/20260826_h2_security_advisor_remediation.sql)

**Propósito/por qué:** H2: forward-only remediation for Supabase Security Advisor findings. Scope: Free DDL remediation only. Remote apply requires explicit JIT approval. No DML, seed, backfill, Pro, writers, schedules, canaries, deploys, push, PR, or merge.

**Contrato y datos:** alter: course_editorial_audit; view: courses_public_effective; function: h2_public_courses_effective, h2_required_missing_fields, h2_update_course_quality, h2_update_course_quality_batch, h2_update_course_quality_batch_impl, h2_update_course_quality_impl, prevent_course_editorial_audit_mutation; index: idx_course_editorial_state_public_gate_h2, idx_course_editorial_state_sponsored_priority_h2.  Targets DML observados: INSERT INTO public.course_editorial_state, INSERT INTO public.course_editorial_audit. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260826-h2-seed-editorial-field-definitions

**Path:** [`20260826_h2_seed_editorial_field_definitions.sql`](../../db/migrations/20260826_h2_seed_editorial_field_definitions.sql)

**Propósito/por qué:** H2: seed editorial field definitions. Scope: DML seed only. Remote apply requires explicit JIT DML approval. No backfill, Pro apply, writers, schedules, canaries, deploys, push, PR, or merge.

**Contrato y datos:** relation_targets: CONFLICT.  Targets DML observados: INSERT INTO public.editorial_field_definitions. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/h3_uat_functional_catalog_seed.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/test_h2_development_legacy_compat.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260827-h2-pro-backfill-editorial-state

**Path:** [`20260827_h2_pro_backfill_editorial_state.sql`](../../db/migrations/20260827_h2_pro_backfill_editorial_state.sql)

**Propósito/por qué:** H2 Pro backfill: create non-published editorial states for existing courses. Scope: Production DML only after explicit JIT and h2-expand-compat manifest approval.

**Contrato y datos:** relation_targets: CONFLICT.  Targets DML observados: INSERT INTO public.course_editorial_state. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/h3_uat_functional_catalog_seed.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/test_h2_development_legacy_compat.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260827-h2-pro-capture-legacy-cohort

**Path:** [`20260827_h2_pro_capture_legacy_cohort.sql`](../../db/migrations/20260827_h2_pro_capture_legacy_cohort.sql)

**Propósito/por qué:** H2 Pro compatibility: freeze the production legacy-visible cohort. Scope: Production DML only after explicit JIT, h2-expand-compat and baseline approval.

**Contrato y datos:** relation_targets: CONFLICT.  Targets DML observados: INSERT INTO private.h2_legacy_public_course_cohort. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/h3_uat_functional_catalog_seed.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/test_h2_development_legacy_compat.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260827-h2-pro-contract-legacy-cohort

**Path:** [`20260827_h2_pro_contract_legacy_cohort.sql`](../../db/migrations/20260827_h2_pro_contract_legacy_cohort.sql)

**Propósito/por qué:** H2 Pro contract: retire the legacy compatibility cohort after strict H2 parity. Scope: Production DDL/DML only after explicit JIT and strict-H2 catalog parity approval.

**Contrato y datos:** view: courses_public_effective; function: h2_public_courses_effective.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_runtime.mjs`, `tests/h3_admin_quota_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260827-h2-pro-contract-public-reader

**Path:** [`20260827_h2_pro_contract_public_reader.sql`](../../db/migrations/20260827_h2_pro_contract_public_reader.sql)

**Propósito/por qué:** H2 Pro contract: retire direct public course reads after stable H2 frontend deploy. Scope: Production DDL only after explicit JIT and post-deploy smoke approval.

**Contrato y datos:** relation_targets: COLUMN, VIEW, courses.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/mobile_usability.spec.ts`, `tests/quality_audit.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260827-h2-pro-enable-legacy-cohort-rls

**Path:** [`20260827_h2_pro_enable_legacy_cohort_rls.sql`](../../db/migrations/20260827_h2_pro_enable_legacy_cohort_rls.sql)

**Propósito/por qué:** H2 Pro security remediation: protect the private compatibility cohort. Scope: Production DDL only after explicit JIT, backup/PITR and manifest approval. The table remains private and has no public grants or policies.

**Contrato y datos:** alter: h2_legacy_public_course_cohort.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_from_h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/test_h2_development_legacy_compat.py`, `tests/test_h2_editorial_migration.py`, `tests/test_h3_admin_queue_ux_contract.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260827-h2-pro-expand-schema-compat

**Path:** [`20260827_h2_pro_expand_schema_compat.sql`](../../db/migrations/20260827_h2_pro_expand_schema_compat.sql)

**Propósito/por qué:** H2 Pro expand: additive editorial schema and compatibility reader. Scope: Production DDL only after explicit JIT, backup/PITR and manifest approval. This migration must not revoke legacy public reads from public.courses. The legacy crawler 

**Contrato y datos:** table: course_editorial_audit, course_editorial_state, editorial_field_definitions, h2_legacy_public_course_cohort; alter: course_editorial_audit, course_editorial_state, editorial_field_definitions; view: courses_public_effective; function: h2_public_courses_effective, h2_required_missing_fields, h2_update_course_quality, h2_update_course_quality_batch, h2_update_course_quality_batch_impl, h2_update_course_quality_impl, h2_verify_expand_compat, h2_verify_expand_compat_impl, prevent_course_editorial_audit_mutation; index: idx_course_editorial_audit_course_created, idx_course_editorial_audit_request_id, idx_course_editorial_state_public_gate_h2, idx_course_editorial_state_sponsored_priority_h2, idx_course_editorial_state_status, idx_courses_institution_slug_h2, idx_editorial_field_definitions_public; policy: course_editorial_audit_service_insert, course_editorial_audit_service_select, course_editorial_state_service_all, editorial_field_definitions_public_select, editorial_field_definitions_service_all; trigger: prevent_course_editorial_audit_delete, prevent_course_editorial_audit_update.  Targets DML observados: INSERT INTO public.course_editorial_state, INSERT INTO public.course_editorial_audit. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_typecheck.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_invitation_uat.mjs`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260827-h2-pro-rollback-public-reader-contract

**Path:** [`20260827_h2_pro_rollback_public_reader_contract.sql`](../../db/migrations/20260827_h2_pro_rollback_public_reader_contract.sql)

**Propósito/por qué:** H2 Pro rollback: restore legacy public course reader after contract-public-reader. Scope: Production DDL only after explicit JIT rollback authorization. This forward-only rollback is valid only before retiring the legacy cohort.

**Contrato y datos:** policy: courses_exclude_release_canary, courses_select_authenticated, courses_select_public.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_admin_safe_suspend_uat.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_local_uat_sanitizer.test.mjs`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260827-h2-pro-seed-editorial-field-definitions

**Path:** [`20260827_h2_pro_seed_editorial_field_definitions.sql`](../../db/migrations/20260827_h2_pro_seed_editorial_field_definitions.sql)

**Propósito/por qué:** H2 Pro seed: editorial field dictionary. Scope: Production DML only after explicit JIT and h2-expand-compat manifest approval.

**Contrato y datos:** relation_targets: CONFLICT.  Targets DML observados: INSERT INTO public.editorial_field_definitions. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/h3_uat_functional_catalog_seed.sql`, `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql`, `tests/test_h2_development_legacy_compat.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260828-h3-admin-auth

**Path:** [`20260828_h3_admin_auth.sql`](../../db/migrations/20260828_h3_admin_auth.sql)

**Propósito/por qué:** H3: Admin authentication and authorization layer Scope: Free/Development DDL only under DDL-H3-ADMIN-AUTH-FREE No backfill, Pro apply, writers, schedules, canaries, or deploys are authorized here.

**Contrato y datos:** table: admin_members; alter: admin_members; function: admin_current_user_role, admin_is_active_admin, admin_is_active_editor, admin_user_can_edit_field, handle_updated_at; index: idx_admin_members_role_active, idx_admin_members_user; policy: admin_members_service_insert, admin_members_service_select, admin_members_service_update; trigger: admin_members_updated_at.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260828-h3-admin-course-queue-view

**Path:** [`20260828_h3_admin_course_queue_view.sql`](../../db/migrations/20260828_h3_admin_course_queue_view.sql)

**Propósito/por qué:** H3: Admin course queue view for cursor pagination Scope: Free/Development DDL only under DDL-H3-ADMIN-QUEUE-FREE No backfill, Pro apply, writers, schedules, canaries, or deploys are authorized here.

**Contrato y datos:** view: admin_course_queue.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_runtime.mjs`, `tests/h3_admin_quota_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260828-h3-admin-editorial-reader-rpc

**Path:** [`20260828_h3_admin_editorial_reader_rpc.sql`](../../db/migrations/20260828_h3_admin_editorial_reader_rpc.sql)

**Propósito/por qué:** 20260828 h3 admin editorial reader rpc

**Contrato y datos:** function: admin_get_course_editorial.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_uat_sanitizer.mjs`, `tests/mobile_usability.spec.ts`, `tests/quality_audit.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260828-h3-admin-editorial-rpc

**Path:** [`20260828_h3_admin_editorial_rpc.sql`](../../db/migrations/20260828_h3_admin_editorial_rpc.sql)

**Propósito/por qué:** H3: Admin editorial RPCs with optimistic locking and audit Scope: Free/Development DDL only under DDL-H3-ADMIN-RPC-FREE No backfill, Pro apply, writers, schedules, canaries, or deploys are authorized here.

**Contrato y datos:** function: admin_archive_course, admin_publish_course, admin_unpublish_course, admin_update_course, admin_update_quality_status.  Targets DML observados: UPDATE public.course_editorial_state, INSERT INTO public.course_editorial_audit. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260828-h3-admin-queue-rpc

**Path:** [`20260828_h3_admin_queue_rpc.sql`](../../db/migrations/20260828_h3_admin_queue_rpc.sql)

**Propósito/por qué:** H3: Admin course queue RPC with cursor pagination Scope: Free/Development DDL only under DDL-H3-ADMIN-QUEUE-RPC-FREE No backfill, Pro apply, writers, schedules, canaries, or deploys are authorized here.

**Contrato y datos:** function: admin_count_course_queue, admin_get_course_queue.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260829-h3-rbac-users

**Path:** [`20260829_h3_rbac_users.sql`](../../db/migrations/20260829_h3_rbac_users.sql)

**Propósito/por qué:** H3 RBAC: User management (admin-only) Scope: Free/Development DDL only under DDL-H3-RBAC-USERS-FREE No backfill, Pro apply, writers, schedules, canaries, or deploys are authorized here. NOTE: Creating auth.users requires the Supabase Admin 

**Contrato y datos:** function: admin_create_member, admin_is_active_editor, admin_list_members.  Targets DML observados: INSERT INTO public.admin_members, INSERT INTO public.admin_membership_audit. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260830-h3-expanded-contract

**Path:** [`20260830_h3_expanded_contract.sql`](../../db/migrations/20260830_h3_expanded_contract.sql)

**Propósito/por qué:** 20260830 h3 expanded contract

**Contrato y datos:** table: admin_membership_audit; alter: admin_membership_audit; function: admin_has_aal2, admin_require_aal2, admin_update_member, prevent_admin_membership_audit_mutation; trigger: prevent_admin_membership_audit_delete, prevent_admin_membership_audit_update.  Targets DML observados: UPDATE public.admin_members, INSERT INTO public.admin_membership_audit. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260902-h3-pr-contract

**Path:** [`20260902_h3_pr_contract.sql`](../../db/migrations/20260902_h3_pr_contract.sql)

**Propósito/por qué:** H3: PR contract delta — effective-value editorial reader and publish completeness gate Scope: Free/Development DDL only. CREATE OR REPLACE deltas are idempotent. No backfill, Pro apply, writers, schedules, canaries, or deploys are authorize

**Contrato y datos:** function: admin_get_course_editorial, admin_publish_course.  Targets DML observados: UPDATE public.course_editorial_state, INSERT INTO public.course_editorial_audit. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_uat_sanitizer.mjs`, `tests/mobile_usability.spec.ts`, `tests/quality_audit.spec.ts`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260903-h3-rbac-contract-fix

**Path:** [`20260903_h3_rbac_contract_fix.sql`](../../db/migrations/20260903_h3_rbac_contract_fix.sql)

**Propósito/por qué:** H3 RBAC contract fix: runtime bugs found by remote JIT-A matrix (2026-09-02) A6 -> 42804: admin_list_members returned auth.users.email (varchar(255)) into a TEXT OUT column. A13 -> 42702: admin_update_member referenced role/is_active/user_i

**Contrato y datos:** function: admin_list_members, admin_update_member.  Targets DML observados: UPDATE public.admin_members, INSERT INTO public.admin_membership_audit. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_local_uat.mjs`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_invitation_onboarding_harness.sql`, `tests/sql/h3_onboarding_rbac_hardening_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_pg17_harness_local.sql`, `tests/sql/h3_safe_suspend_harness.sql`, `tests/sql/run_h3req1_pipeline_postgrest_pg17_r1.sh`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260918-h3-invitation-flow-persistence

**Path:** [`20260918_h3_invitation_flow_persistence.sql`](../../db/migrations/20260918_h3_invitation_flow_persistence.sql)

**Propósito/por qué:** H3 Invitation Flow persistence layer (design: STUDIAMATCH-H3-INVITATION-DESIGN-01 / H3-DESIGN-DB-01) Scope: local SQL migration only. No frontend, no Edge Functions, no MFA removal, no remote apply. Compatibility contract: * `is_active`, `r

**Contrato y datos:** table: admin_invitations; alter: admin_invitations, admin_members, admin_membership_audit; function: guard_admin_invitations_identity, guard_admin_invitations_status_transition, guard_admin_members_status_insert, guard_admin_members_status_transition, prevent_admin_invitations_delete; index: idx_admin_invitations_email_created, idx_admin_invitations_member, idx_admin_invitations_pending_expiry, idx_admin_invitations_resend_chain, idx_admin_invitations_status, idx_admin_members_last_invitation, idx_admin_members_ready_admins, idx_admin_members_status_active_role, idx_admin_membership_audit_entity_action, idx_admin_membership_audit_invitation, uq_admin_invitations_one_pending_per_email, uq_admin_invitations_token_hash; trigger: admin_members_status_insert_guard, admin_members_status_transition_guard, guard_admin_invitations_identity, guard_admin_invitations_status, prevent_admin_invitations_delete.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260919-h3-invitation-auth-token-delta

**Path:** [`20260919_h3_invitation_auth_token_delta.sql`](../../db/migrations/20260919_h3_invitation_auth_token_delta.sql)

**Propósito/por qué:** H3 Invitation Flow Opcion A delta. Scope: expand-only local SQL migration. Supabase Auth owns the invitation token; StudIAMatch retains the business record, lifecycle and audit trail. This migration intentionally does not modify 20260918_h3

**Contrato y datos:** alter: admin_invitations, admin_membership_audit; function: guard_admin_invitations_status_transition.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_invitation_edge_runtime_harness.sql`, `tests/sql/h3_invitation_onboarding_harness.sql`, `tests/sql/h3_invitation_reservation_concurrency.sh`, `tests/sql/h3_onboarding_rbac_hardening_harness.sql`, `tests/sql/h3_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260920-h3-invitation-edge-runtime

**Path:** [`20260920_h3_invitation_edge_runtime.sql`](../../db/migrations/20260920_h3_invitation_edge_runtime.sql)

**Propósito/por qué:** H3-BUILD-03A-EDGE runtime support. The Edge Function uses these service-role-only RPCs to keep reservation, completion and failure transitions atomic within the database. Auth remains the authority for invitation tokens and delivery.

**Contrato y datos:** alter: admin_membership_audit; function: admin_invitation_complete, admin_invitation_fail, admin_invitation_record_failure, admin_invitation_reserve.  Targets DML observados: UPDATE public.admin_members, UPDATE public.admin_invitations, INSERT INTO public.admin_members, INSERT INTO public.admin_invitations, INSERT INTO public.admin_membership_audit. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260921-h3-invitation-onboarding-rpc

**Path:** [`20260921_h3_invitation_onboarding_rpc.sql`](../../db/migrations/20260921_h3_invitation_onboarding_rpc.sql)

**Propósito/por qué:** H3-BUILD-03B-DB-IMPLEMENTATION. Auth owns the invitation token. Postgres owns the business lifecycle. Expand-only delta: do not edit the historical 20260918/20260919/20260920 files. No password, token, secret, or frontend-supplied expiry is

**Contrato y datos:** alter: admin_invitations; function: admin_accept_current_invitation, admin_complete_password_setup, admin_get_onboarding_status, admin_invitation_record_failure, admin_invitation_reserve, guard_admin_members_status_transition.  Targets DML observados: UPDATE public.admin_members, UPDATE public.admin_invitations, INSERT INTO public.admin_membership_audit, INSERT INTO public.admin_members, INSERT INTO public.admin_invitations. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260924-h3-onboarding-rbac-hardening

**Path:** [`20260924_h3_onboarding_rbac_hardening.sql`](../../db/migrations/20260924_h3_onboarding_rbac_hardening.sql)

**Propósito/por qué:** H3REQ1 compatibility hardening for onboarding-aware RBAC. Expand-only: legacy rows default to account_status = ready and retain the existing admin/user workflow. New or incomplete onboarding states cannot be activated through the administra

**Contrato y datos:** function: admin_current_user_role, admin_is_active_admin, admin_is_active_editor, admin_update_member, admin_user_can_edit_field.  Targets DML observados: UPDATE public.admin_members, INSERT INTO public.admin_membership_audit. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260924-h3-onboarding-rbac-hardening-fix

**Path:** [`20260924_h3_onboarding_rbac_hardening_fix.sql`](../../db/migrations/20260924_h3_onboarding_rbac_hardening_fix.sql)

**Propósito/por qué:** Follow-up to 20260924_h3_onboarding_rbac_hardening. The local variable uses `cur_role` to avoid PostgreSQL's current-role identifier collision while preserving the same function signature and ACL.

**Contrato y datos:** function: admin_current_user_role.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260925-h3-admin-members-onboarding-reader

**Path:** [`20260925_h3_admin_members_onboarding_reader.sql`](../../db/migrations/20260925_h3_admin_members_onboarding_reader.sql)

**Propósito/por qué:** H3REQ1 compatibility reader for admin membership management. The legacy admin_list_members() signature remains unchanged. This additive RPC exposes onboarding state to the existing admin UI without changing the old contract or granting dire

**Contrato y datos:** function: admin_list_members_onboarding.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_auth_error_uat.mjs`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_typecheck.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_admin_quota_runtime.mjs`, `tests/h3_admin_quota_uat.mjs`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260925-h3-legacy-member-creation-guard

**Path:** [`20260925_h3_legacy_member_creation_guard.sql`](../../db/migrations/20260925_h3_legacy_member_creation_guard.sql)

**Propósito/por qué:** H3REQ1 legacy compatibility guard. The canonical invitation path is admin-invite -> Auth email -> callback/PKCE -> accept -> password setup. The old direct membership RPC remains callable for compatibility, but may no longer create a ready/

**Contrato y datos:** function: admin_create_member.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260927-h3-admin-queue-facets-filter

**Path:** [`20260927_h3_admin_queue_facets_filter.sql`](../../db/migrations/20260927_h3_admin_queue_facets_filter.sql)

**Propósito/por qué:** H3/UX: server-side queue facets and institution filtering for Development/Free. Scope: additive Free/Development DDL only. Legacy queue/count RPCs remain intact for compatibility and rollback. No data backfill, operational writes, Pro apply

**Contrato y datos:** function: admin_count_course_queue_filtered, admin_get_course_queue_facets, admin_get_course_queue_filtered.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260927-h3-publication-visibility-contract

**Path:** [`20260927_h3_publication_visibility_contract.sql`](../../db/migrations/20260927_h3_publication_visibility_contract.sql)

**Propósito/por qué:** H3: publication must satisfy the public availability gate. Scope: Free/Development DDL only. CREATE OR REPLACE is idempotent. No data backfill, Pro apply, writers, schedules, canaries, or deploys.

**Contrato y datos:** function: admin_publish_course.  Targets DML observados: UPDATE public.course_editorial_state, INSERT INTO public.course_editorial_audit. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_local_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_from_h2_pro_pg17_harness.sql`, `tests/sql/h3_pg17_harness.sql`, `tests/sql/h3_pg17_harness_local.sql`, `tests/sql/h3_quota_postgrest_fixture.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20260928-h3-invitation-accept-email-regex-fix

**Path:** [`20260928_h3_invitation_accept_email_regex_fix.sql`](../../db/migrations/20260928_h3_invitation_accept_email_regex_fix.sql)

**Propósito/por qué:** H3 invitation onboarding remediation. The Free/Development function definition drifted from the versioned contract: its email validation contained two backslashes before the dot, rejecting every normal email address before the invitation tr

**Contrato y datos:** function: admin_accept_current_invitation.  Targets DML observados: UPDATE public.admin_invitations, INSERT INTO public.admin_membership_audit, UPDATE public.admin_members. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_local_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_from_h2_pro_pg17_harness.sql`, `tests/sql/h3_invitation_edge_runtime_harness.sql`, `tests/sql/h3_invitation_onboarding_harness.sql`, `tests/sql/h3_invitation_reservation_concurrency.sh`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20261001-h3-course-editorial-audit-availability

**Path:** [`20261001_h3_course_editorial_audit_availability.sql`](../../db/migrations/20261001_h3_course_editorial_audit_availability.sql)

**Propósito/por qué:** H3: Admin-readable audit, evidence-backed availability override, and effective-value preservation for editorial corrections. Local Docker/PG17 validation only; Free DDL/writes and all deployments require separate JIT approval. No backfill, 

**Contrato y datos:** alter: course_editorial_state; view: courses_public_effective; function: admin_get_course_audit, admin_get_course_editorial, admin_publish_course, admin_set_course_availability, admin_update_course, h2_public_courses_effective; index: idx_course_editorial_state_availability_override_expiry.  Targets DML observados: UPDATE public.course_editorial_state, INSERT INTO public.course_editorial_audit. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_admin_quota_runtime.mjs`, `tests/h3_admin_quota_uat.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20261001-h3-invitation-reservation-compensation

**Path:** [`20261001_h3_invitation_reservation_compensation.sql`](../../db/migrations/20261001_h3_invitation_reservation_compensation.sql)

**Propósito/por qué:** Local H3 delta: reserve the invitation row before calling Auth, serialize failures with the same per-email advisory lock, restore a superseded invitation only on definitive rejection, and audit ambiguous delivery without invalidating a link

**Contrato y datos:** alter: admin_membership_audit; function: admin_accept_current_invitation, admin_invitation_complete, admin_invitation_expire, admin_invitation_fail, admin_invitation_mark_delivery_reconciliation, admin_invitation_reserve, guard_admin_invitations_status_transition.  Targets DML observados: UPDATE public.admin_invitations, INSERT INTO public.admin_membership_audit, UPDATE public.admin_members, INSERT INTO public.admin_members, INSERT INTO public.admin_invitations. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20261002-h3-admin-quota-expand

**Path:** [`20261002_h3_admin_quota_expand.sql`](../../db/migrations/20261002_h3_admin_quota_expand.sql)

**Propósito/por qué:** LOCAL approved additive EXPAND. Deploy this before the compatible Edge and BEFORE 20261002_h3_admin_quotas.sql wraps legacy RPCs. Remote JIT required.

**Contrato y datos:** table: h3_admin_quota_events; alter: h3_admin_quota_events; function: admin_invitation_request_admit, h3_raise_admin_quota, h3_take_admin_quota; index: h3_admin_quota_expiry.  Targets DML observados: INSERT INTO private.h3_admin_quota_events, UPDATE private.h3_admin_quota_events, DELETE FROM private.h3_admin_quota_events. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_local_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20261002-h3-admin-quotas

**Path:** [`20261002_h3_admin_quotas.sql`](../../db/migrations/20261002_h3_admin_quotas.sql)

**Propósito/por qué:** Approved LOCAL design. Remote DDL/deploy remains separately gated. Additive rolling-window quotas; originals retained privately, auth/RLS unchanged.

**Contrato y datos:** relation_targets: n.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_typecheck.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_runtime_server.mjs`, `tests/h3_local_uat.mjs`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### database-migration-20261025-h3-admin-members-onboarding-forbidden-status

**Path:** [`20261025_h3_admin_members_onboarding_forbidden_status.sql`](../../db/migrations/20261025_h3_admin_members_onboarding_forbidden_status.sql)

**Propósito/por qué:** delta local acotado para que el guard de Admin activo del lector de onboarding emita SQLSTATE `42501`, ya traducido por el wrapper de cuota a HTTP 403. Busca distinguir una denegación de rol de una falla del servicio; no atribuye ni resuelve por sí solo el 502 histórico observado sin correlación.

**Contrato y datos:** inspecciona las firmas fijas `private.h3_quota_base_admin_list_members_onboarding()` y `public.admin_list_members_onboarding()`, confirma el marcador y el mapeo existente `42501 -> 403`, y reemplaza solo el texto exacto del guard legacy. No toca filas, grants, firma pública, cuota ni auditoría. El preflight estricto pasó en la base PG17 desechable autorizada; la migration se aplicó allí únicamente para el harness sintético. No se aplicó en Free/Development ni otro servicio remoto.

**Consumidores y pruebas relacionadas:** `web/functions/_lib/admin-bff.ts` preserva el estado 403 y entrega código/mensaje sanitizados; `tests/h3_admin_bff_mock_uat.mjs` verifica rechazo user/Admin y errores desconocidos; `tests/test_h3_admin_onboarding_denial_contract.py` revisa el contrato; `tests/sql/h3_admin_quota_harness.sql` comprueba sintéticamente Admin permitido y user denegado. El mock BFF, el contrato Python y el harness/SQL corrieron en Docker; la ejecución PG17 se limita a dos bases sintéticas del paquete JIT registrado. No acredita PostgREST remoto.

**Operación y recuperación:** cambio de definición de función (DDL). Requiere autorización separada y prueba previa en PG17 desechable antes de cualquier despliegue remoto. Rollback: restaurar la definición anterior solo si la huella exacta/guard sigue coincidiendo, mediante una migration inversa revisada y autorización propia; no ejecutar durante este ciclo. Expand conserva wrapper y contrato; compatibilidad conserva firma/grants/cuota y deja fallos no clasificados sanitizados; deploy pendiente; contract no elimina rutas ni controles hasta observar estabilidad. Ver [evidencia D04](../evidencia/h3req1_d04_onboarding_forbidden_2026-10-25.md).

### migration-20261004-h3-admin-queue-first-null-guard

**Path:** [`20261004_h3_admin_queue_first_null_guard.sql`](../../db/migrations/20261004_h3_admin_queue_first_null_guard.sql)

**Propósito/por qué:** H3REQ1: forward-only guard for deployments where the original queue migration is already recorded as applied. Preserve a quota wrapper when one is installed by patching only its private original-function snapshot.

**Contrato y datos:** DO procedural block: inspects/replaces a guarded function definition; target statement is reviewed separately below..  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** sin identificador de test localizado en el scope. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20261004-h3-admin-rpc-signed-gateway-expand

**Path:** [`20261004_h3_admin_rpc_signed_gateway_expand.sql`](../../db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql)

**Propósito/por qué:** H3REQ1 signed Admin RPC gateway — additive EXPAND only. This file intentionally does NOT configure pgrst.db_pre_request or provision keys. Activate only after signed BFF consumers are deployed and a separate JIT approves the exact PostgREST

**Contrato y datos:** table: h3_admin_rpc_gateway_keys, h3_admin_rpc_gateway_nonces; alter: h3_admin_rpc_gateway_keys, h3_admin_rpc_gateway_nonces; function: h3_admin_rpc_gateway_hmac, h3_admin_rpc_signed_gateway_pre_request; index: h3_admin_rpc_gateway_nonce_expiry.  Targets DML observados: DELETE FROM private.h3_admin_rpc_gateway_nonces, INSERT INTO private.h3_admin_rpc_gateway_nonces. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_invite_edge_typecheck.mjs`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_admin_safe_suspend_runtime_uat.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_runtime_server.mjs`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20261004-h3-admin-rpc-signed-gateway-payload-bound-wrapper

**Path:** [`20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql`](../../db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql)

**Propósito/por qué:** H3REQ1: bind the Admin RPC gateway proof to the exact typed dispatch payload. Additive EXPAND only. Activation, key provisioning, and disposable PG17 execution each require their own JIT approval; this migration performs none of them.

**Contrato y datos:** function: admin_signed_rpc, h3_admin_rpc_args_match, h3_admin_rpc_gateway_fail, h3_admin_rpc_gateway_signature_matches, h3_admin_rpc_gateway_verify_payload, h3_admin_rpc_signed_gateway_pre_request.  Targets DML observados: DELETE FROM private.h3_admin_rpc_gateway_nonces, INSERT INTO private.h3_admin_rpc_gateway_nonces. Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/h3_admin_quota_postgrest.mjs`, `tests/h3_invitation_uat.mjs`, `tests/h3_local_uat.mjs`, `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DDL/schema/functión, DML/data, DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

### migration-20261010-h3-admin-members-service-select

**Path:** [`20261010_h3_admin_members_service_select.sql`](../../db/migrations/20261010_h3_admin_members_service_select.sql)

**Propósito/por qué:** The server-side admin-invite function resolves an existing membership with its service_role client. Keep this explicit so the contract does not depend on project-wide default privileges. No client role receives direct access.

**Contrato y datos:** relation_targets: admin_members, service_role.  Esta es una lectura del cuerpo local; no certifica que Pro tenga el objeto ni que la migration se aplicó.

**Consumidores y pruebas relacionadas:** `tests/fixtures/h3/admin_auth_local_mock.sql`, `tests/h3_admin_invite_edge_uat.mjs`, `tests/h3req1_pipeline_postgrest_pg17_integration.py`, `tests/sql/h2_pg17_harness.sql`, `tests/sql/h2_pro_pg17_harness.sql`, `tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, `tests/sql/h3_from_h2_pro_pg17_harness.sql`. `db_migrate.py` es un loader local por manifest/`--only`; el workflow DB sync solo acepta su lista H2 cerrada. Un identifier hit no es PASS ni confirma aplicación del archivo.

**Operación y recuperación:** DCL/grants. No ejecutar sin JIT y un plan expand → compatibilidad → deploy → contract; el rollback genérico no se infiere. Consultar el procedimiento por cambio y validar contra Pro en etapa separada.

**Historia y cambio seguro:** [fila de historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md), [mapa de objetos/tests](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Antes de editar, revisar todas las migrations posteriores que redefinen el mismo objeto, su consumidor SQL/RPC, harnesses citados y rollback; actualizar diccionario, fixtures y registro.

## Archivos SQL y operativos adyacentes

### Baselines y snapshots

Pro sigue siendo la autoridad del schema según `AGENTS.md`; estos archivos son snapshots locales y no demuestran aplicación remota. El registro separa cada artefacto porque su responsabilidad y riesgo son distintos.

| Path | Responsabilidad exacta | Referencias/consumidores locales | Evidencia y límite |
|---|---|---|---|
| `db/PRODUCTION_MASTER.sql` | Snapshot SQL de schema de producción usado como referencia histórica. | No se halló loader ejecutable. `20260428_rls_intermediate_tables.sql` y `20260501_production_full_replace.sql` lo mencionan en comentarios/contexto, sin cargarlo. | Se preserva el cuerpo e historia local; no acredita baseline aplicado. No se encontró suite ni replay fechado de este archivo. |
| `db/production_init.sql` | SQL histórico de inicialización del ambiente. | Sin loader/caller ejecutable identificado en los scopes locales. | No se encontró una suite ni replay fechado asociado. No usar como paso actual de bootstrap sin cotejo y autorización. |
| `db/production_seed.sql` | Snapshot histórico de seed de producción, distinto del seed H3 sintético de pruebas. | Sin loader/caller ejecutable identificado en los scopes locales. | No se encontró suite ni replay fechado asociado. No se usa para promover datos operativos. |
| `db/restore_full_schema.sql` | Snapshot SQL para restauración completa, distinto de migration incremental o backup verificado. | No se halló loader ejecutable. `20260504_fase75_pipeline_ready.sql` lo menciona en un comentario de compatibilidad; no lo carga. | No se encontró prueba/replay fechado. El nombre no acredita restore actual, integridad de backup ni convergencia con Pro. |

La búsqueda de cada path cubrió `.github/`, `scripts/`, `tests/`, `db/`, `web/`, `workers/`, `supabase/` y `config/` en ambos checkouts locales. Esta ausencia tiene ese alcance y no descarta uso manual o referencias externas. Antes de cambiar cualquiera, comparar el contenido con el baseline Pro en una etapa remota autorizada; no ejecutar estos snapshots para documentar ni alterar evidencia histórica. La asignación individual está en el [registro verificable](../trazabilidad/registro_fuentes_componentes.md#asignaciones-por-fuente).

### Helper de migración Pro

`db/migrations/apply_cleansing_fix_pro.py` no es una migration SQL ni un runner de pruebas. Lee `20260501_fix_cleansing_loop.sql`, elimina sus envolturas `BEGIN/COMMIT` y hace un POST a la Supabase Management API usando los nombres `SUPABASE_PRO_URL`, `SUPABASE_PRO_PROJECT_REF` y `SUPABASE_MGMT_TOKEN`. El SQL reemplaza `public.lock_staging_records` y `public.atomic_cleansing_promote` y elimina `public.mark_records_processing`; afecta el paso de `staging_raw` a `cleansed_programs`.

No se encontró un workflow que invoque el helper. `tests/test_supabase_credentials_contract.py` incluye su identidad/ruta para revisar el contrato de credenciales, pero no lo importa ni aplica el SQL. La búsqueda exacta en `tests/`, `.github/workflows/` y `scripts/` de ambos checkouts no encontró una prueba funcional propia ni resultado de aplicación. Impacto: falta evidencia aislada del helper; no debe inferirse seguridad/éxito por el inventario de credenciales. Es capaz de aplicar DDL contra Pro y requiere JIT DDL y revisión de baseline/rollback; no leer `.env` ni ejecutar el helper para resolver la relación.

### Seed H3 local

`db/seeds/h3_admin_seed_local.sql` se incluye con `\ir` desde `tests/sql/h3_pg17_harness.sql` y `tests/sql/h3_pg17_harness_local.sql`; ambos se encuentran en los dos checkouts. Crea identidades Auth sintéticas con `h3.test_password`, membresías admin/user/inactiva, instituciones y categorías locales. El gate `security-audit.yml` invoca el primer harness cuando hay cambios de DB; no se halló un runner automático del segundo ni se infiere que cada variante ejecutó el seed. Es fixture idempotente de test, no seed de Free/Pro ni catálogo de producción. Nunca correr contra Supabase.

### Rollbacks de suspensión y reanudación H3REQ1

`db/rollback/h3req1_safe_suspend.sql` captura ACLs/firmas de funciones y revoca grants en el contrato de suspensión; `h3req1_safe_resume.sql` verifica el snapshot y reconstituye los grants del target permitido. No son inversas generales de todas las migrations ni reemplazan rollback por ambiente. El harness `tests/sql/h3_safe_suspend_harness.sql` incluye ambos mediante `\ir`; las variantes C03 `tests/h3req1_c03_integrated_drill*.sh` invocan `run_sql` para suspensión y reanudación; `tests/test_admin_invite_edge_contract.py` lee el path de suspensión como contrato. Esto acredita enlaces estáticos, no que se haya ejecutado un rollback remoto. Los SQL tienen efectos DDL/DCL y necesitan JIT específico, backup/rollback revisado y aislamiento; no ejecutarlos en esta transferencia.

La asignación, los consumidores y la evidencia/ausencia por path están en las anclas [baselines](#baselines-y-snapshots), [helper](#helper-de-migracion-pro), [seed](#seed-h3-local) y [rollback](#rollbacks-de-suspension-y-reanudacion-h3req1). La evidencia de búsqueda local conserva el alcance y sus resultados; el cotejo remoto de Pro queda pendiente.

## Navegación relacionada

[Database/diccionario](../database.md) · [Datos y pipeline](datos_pipeline.md) · [Pruebas](../pruebas.md) · [Operación](../operacion.md) · [HITO-002/003](../hitos/README.md) · [Decisiones](../decisiones/README.md) · [Registro](../trazabilidad/registro_fuentes_componentes.md#base-de-datos)

## Fuentes y relaciones

El [registro fuente-componente](../trazabilidad/registro_fuentes_componentes.md#base-de-datos) asigna cada migration, seed, baseline, rollback y helper a esta ficha y al diccionario de [`database.md`](../database.md#diccionario). La secuencia local de migrations es evidencia de código; aplicación y diferencias actuales de Pro necesitan cotejo remoto separado.

## Navegación histórica local

Evidencia preservada por proceso; cada catálogo enlaza sus documentos históricos individualmente y no es una autoridad operativa.

- [C03 integrado: sesiones, invitación y recuperación](../catalogos_historicos/c03_integrado.md#documentos-preservados)
- [Admin, autenticación e historia editorial](../catalogos_historicos/admin_auth_editorial.md#documentos-preservados)
- [Frontend público y UAT](../catalogos_historicos/frontend_publico_uat.md#documentos-preservados)
- [Pipeline, datos y base de datos](../catalogos_historicos/pipeline_base_datos.md#documentos-preservados)
- [Infraestructura, seguridad y CI](../catalogos_historicos/infra_seguridad_ci.md#documentos-preservados)
- [Documentación, trazabilidad y transferencia](../catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados)
- [Registros operativos históricos y JIT](../catalogos_historicos/operacion_jit.md#documentos-preservados)
- [Evidencia histórica de requerimientos e hitos](../catalogos_historicos/requerimientos_hitos.md#documentos-preservados)
- [Seguimiento y handoffs históricos](../catalogos_historicos/seguimiento_historico.md#documentos-preservados)
- [Documentación DB sustituida](../catalogos_historicos/database_legacy.md#documentos-preservados)
