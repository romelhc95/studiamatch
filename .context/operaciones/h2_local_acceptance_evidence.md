# H2 Local Acceptance Evidence

Snapshot: `H2-LOCAL-VALIDATED-2026-08-25`.

## Alcance Validado Localmente

- Capa editorial separada: `course_editorial_state`, `editorial_field_definitions`, `course_editorial_audit` y `courses_public_effective`.
- Forward-fix local: `db/migrations/20260826_h2_editorial_layer_forward_fix.sql`.
- Contrato determinista: valores efectivos, `missing_fields`, `quality_status`, `field_sources` y timestamps por campo.
- Pipeline tolerante: incompletos no se publican por flags legacy y calidad se recomputa por RPC acotada.
- Backfill: `--dry-run` por defecto, `--apply` explicito, keyset por UUID, batches maximos 1000 y segundo run `NOOP` cubierto por tests.
- Leads: frontend sin `POST /leads`; DDL local revoca INSERT y elimina policies legacy conocidas.
- Publicacion publica: frontend usa `courses_public_effective`; SELECT directo a `courses` queda revocado para roles publicos en forward-fix.

## Commits Locales H2

```text
5bfb231 feat(h2): add editorial layer ddl baseline
c31c43e feat(h2): add editorial quality contract
f492638 feat(h2): harden editorial layer contract
9c20a32 test(h2): add postgres 17 editorial harness
a703d4c feat(h2): make pipeline editorial-gated
662f1e0 feat(h2): add editorial state backfill
5710658 feat(h2): close lead capture surfaces
fe07a9d test(h2): register editorial backfill security inventory
19a383b fix(h2): harden editorial publication safeguards
8806456 fix(h2): route public frontend through editorial view
c91160a ci(h2): enforce editorial safeguards
4bd9439 fix(h2): close legacy public course bypass
eb92e1f fix(h2): drop legacy public courses policy
d356fa8 fix(h2): require editorial view for public course reads
```

## Validaciones Locales

```text
docker exec studiamatch-dev pytest tests/test_h2_writer_scan.py tests/test_h2_pipeline_contract.py tests/test_h2_backfill_editorial_state.py tests/test_editorial_contract.py tests/test_h2_editorial_migration.py tests/test_security_flow.py tests/test_supabase_credentials_contract.py
Resultado: 79 passed

docker exec studiamatch-dev python3 -m py_compile scripts/maintenance/h2_scan_unauthorized_writers.py scripts/maintenance/h2_backfill_editorial_state.py scripts/shared/editorial_contract.py scripts/core/cleansing_worker.py scripts/core/enrichment_worker.py scripts/core/sync_vector_worker.py
Resultado: PASS

PostgreSQL 17 efimero con tests/sql/h2_pg17_harness.sql
Resultado: h2_pg17_harness_ok

docker exec studiamatch-dev sh -lc "cd /app/web && npm run lint"
Resultado: PASS con 10 warnings preexistentes

docker exec studiamatch-dev sh -lc "cd /app/web && npx tsc --noEmit"
Resultado: PASS

docker exec -e NEXT_PUBLIC_SUPABASE_URL=https://aqrldlmlszjtgpqiegaa.supabase.co -e NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_build_placeholder studiamatch-dev sh -lc "cd /app/web && npm run build"
Resultado: PASS
```

## Validaciones No Verdes Globales

```text
docker exec studiamatch-dev pytest
Resultado: FAIL por recoleccion de local/worktrees historicos y tests superseded fuera de alcance.

docker exec studiamatch-dev pytest tests
Resultado: 17 failed, 134 passed, 4 skipped por tests F9/F10 historicos superseded y falta de bs4 en el contenedor.
```

## Seguridad

- Hooks locales de commit: `credential scan passed` en todos los commits H2.
- `security-auditor` final sobre `HEAD d356fa8`: 0 criticos, 0 altos.
- GitHub Advanced Security MCP no disponible en este repo; no sustituye hooks/CI.

## Forward-Fix Free Aplicado

- Proyecto verificado: `https://aqrldlmlszjtgpqiegaa.supabase.co`.
- Payload aplicado bajo JIT DDL Free: `db/migrations/20260826_h2_editorial_layer_forward_fix.sql`.
- Ledger remoto: `20260825234738/20260826_h2_editorial_layer_forward_fix`.
- Preflight read-only: PostgreSQL `17.6`, objetos H2 existentes y `has_duplicate_slugs=false`.
- Verificacion estructural: columnas, constraints, indices, triggers y RPC H2 presentes.
- Verificacion permisos: `anon` y `authenticated` sin `SELECT` directo sobre `courses`, sin `INSERT` sobre `leads`, sin `EXECUTE` sobre `h2_update_course_quality` ni `increment_view_count`; `service_role` conserva `EXECUTE` sobre `h2_update_course_quality`.
- Vista efectiva: `courses_public_effective` con grants `SELECT` para `anon`, `authenticated` y `service_role`; conteo actual `0`, esperado sin backfill ni publicacion masiva.
- Policies legacy publicas de `courses` y `leads`: ausentes.
- Policy H2 `course_editorial_state_public_effective_select`: presente.

## Security Advisor Post Forward-Fix

- `ERROR security_definer_view`: `public.courses_public_effective` queda como security definer view. Remediacion: https://supabase.com/docs/guides/database/database-linter?lint=0010_security_definer_view
- `WARN function_search_path_mutable`: `public.prevent_course_editorial_audit_mutation` no fija `search_path`. Remediacion: https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable
- `INFO rls_enabled_no_policy`: hallazgos legacy preexistentes en `_view_count_dedup`, `schema_repair_audit` y `supabase_migrations`. Remediacion: https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy
- Resultado: el gate DML Free de seed/backfill queda bloqueado hasta aplicar y verificar `20260826_h2_security_advisor_remediation.sql` bajo JIT DDL Free o waiver humano explicito.

## Remediacion Local De Pilares

- Payload local preparado: `db/migrations/20260826_h2_security_advisor_remediation.sql`.
- Seguridad: `courses_public_effective` pasa a `security_invoker=true` sobre lector acotado en schema `private`; tablas base `courses`, `course_editorial_state` y `leads` quedan sin acceso publico directo; RPC publico de calidad queda invoker y delega a implementacion privada; `prevent_course_editorial_audit_mutation` fija `search_path`.
- Calidad: servidor valida `missing_fields`; placeholders `consultar`, `a consultar` y `sin confirmar` cuentan como faltantes en campos obligatorios; idempotencia usa `request_id` + hash canonico del payload; repeticion con hash distinto falla sin mutar.
- Mantenimiento: `CONTRACT_VERSION=h2-quality-v2` centraliza el contrato Python; sync y backfill consumen el mismo hash/contrato; la migracion final queda incorporada al harness PG17 y al allowlist CI.
- Escalabilidad: backfill aplicado usa RPC batch maximo 1000 items y lecturas de estados fragmentadas para evitar URLs grandes; pruebas cubren 1001 y 10000 filas.
- Rendimiento: indices H2 agregados para gate publico y patrocinio; `EXPLAIN` local sobre `courses_public_effective` compila con `Function Scan` sobre lector privado acotado. Riesgo residual aceptado para JIT Free: menor pushdown potencial de filtros hasta medir con datos reales.
- Validacion final focalizada: `pytest` H2 ampliado `88 passed`, `py_compile` PASS, PostgreSQL 17 harness `h2_pg17_harness_ok`, lint PASS con 10 warnings preexistentes, TypeScript PASS, static build PASS y credential scan PASS.
- Security-auditor local final: sin hallazgos bloqueantes para dejar listo payload JIT DDL Free; riesgos residuales no bloqueantes documentados.

## Intento JIT DDL Free Remediacion

- Proyecto verificado: `https://aqrldlmlszjtgpqiegaa.supabase.co`.
- Payload autorizado: `db/migrations/20260826_h2_security_advisor_remediation.sql`.
- Resultado remoto: `FAILED`.
- Error: `42P16: cannot change data type of view column "slug" from character varying to text`.
- Verificacion read-only posterior: la migracion no aparece en ledger, `private` schema no existe y no existen los nuevos RPCs `h2_update_course_quality(..., p_payload_hash)` ni `h2_update_course_quality_batch(jsonb)`.
- Diagnostico: drift/tipo real de la vista remota; `slug` y `seniority_level` permanecen como `varchar` en `courses_public_effective`, mientras el payload los declaraba como `TEXT`.
- Accion tomada: se detuvo la aplicacion remota y no se modifico el payload bajo la JIT consumida. Requiere correccion local y nueva aprobacion JIT DDL Free.

## Correccion Local Post 42P16

- Payload corregido: `db/migrations/20260826_h2_security_advisor_remediation.sql`.
- Cambios: `slug VARCHAR`, `seniority_level VARCHAR` y `DROP VIEW IF EXISTS public.courses_public_effective` antes de recrear la vista.
- Seguridad: se conserva el diseno validado; no se reabren grants publicos directos a tablas base.
- Validaciones: `pytest tests/test_h2_editorial_migration.py` `18 passed`, suite H2 ampliada `88 passed`, `py_compile` PASS, PostgreSQL 17 harness `h2_pg17_harness_ok`, credential scan PASS y security-auditor sin bloqueantes.
- Preflight obligatorio para siguiente JIT: verificar dependencias remotas de `public.courses_public_effective` antes de `DROP VIEW`.

## JIT DDL Free Remediacion Aplicada

- Proyecto verificado: `https://aqrldlmlszjtgpqiegaa.supabase.co`.
- Preflight dependencias de `public.courses_public_effective`: sin dependencias bloqueantes.
- Payload aplicado: `db/migrations/20260826_h2_security_advisor_remediation.sql`.
- Ledger remoto: `20260826010206/20260826_h2_security_advisor_remediation`.
- Objetos presentes: schema `private`, lector privado, RPC unitario H2 con `p_payload_hash`, RPC batch H2 y vista efectiva.
- Acceso publico directo: `anon` y `authenticated` sin `SELECT` sobre `courses`, sin privilegios por columna sobre `courses`, sin `SELECT` sobre `course_editorial_state`, sin `INSERT` sobre `leads`, sin `EXECUTE` sobre `increment_view_count` ni RPCs H2.
- `service_role`: conserva `EXECUTE` sobre `h2_update_course_quality(uuid,text[],jsonb,jsonb,text,text)` y `h2_update_course_quality_batch(jsonb)`.
- Vista efectiva: usa `private.h2_public_courses_effective()`, conserva `slug varchar` y `seniority_level varchar`, conteo actual `0` sin backfill.
- Idempotencia RPC validada read-only por definicion: implementacion privada contiene `pg_advisory_xact_lock`, rechazo por `request_id` reutilizado con hash distinto y validacion server-side de `missing_fields`.
- Security Advisor: hallazgos H2 `security_definer_view` y `function_search_path_mutable` resueltos; persisten solo `INFO rls_enabled_no_policy` legacy no-H2.
- Performance Advisor: solo `INFO` legacy/uso reciente; indices H2 nuevos figuran sin uso hasta que haya trafico/backfill, no bloqueante para DML Free.

## Intento JIT DML Free Backfill

- Proyecto MCP verificado: `https://aqrldlmlszjtgpqiegaa.supabase.co`.
- Ledger H2 verificado: migraciones H2 requeridas presentes, incluyendo `20260826_h2_security_advisor_remediation`.
- Security Advisor pre-DML: sin hallazgos H2 criticos/warn; solo `INFO rls_enabled_no_policy` legacy no-H2.
- Conteos pre-DML read-only: `courses=350`, `course_editorial_state=0`, `courses_public_effective=0`, RPC batch presente.
- Dry-run por script: `FAILED_BEFORE_WRITE`.
- Error: `Service operations require a configured Supabase secret key`.
- Diagnostico: `studiamatch-dev` no tiene variables Supabase exportadas y `/app/.env.local` no provee una secret key valida para el script.
- Accion tomada: no se ejecuto DML, seed, backfill, segundo `NOOP`, Pro, writers, schedules, deploys, push, PR, merge ni commit. Se detiene hasta corregir configuracion de credenciales local/CI sin exponer secretos.

## JIT DML Free Backfill Ejecutado

- Proyecto MCP verificado: `https://aqrldlmlszjtgpqiegaa.supabase.co`.
- Secret key Free: presente en `/app/.env.local`; no se imprimio valor.
- URL Free: inyectada explicitamente al proceso como `NEXT_PUBLIC_SUPABASE_URL=https://aqrldlmlszjtgpqiegaa.supabase.co` porque no estaba exportada en el contenedor.
- Ledger H2: migraciones requeridas presentes, incluyendo `20260826_h2_security_advisor_remediation`.
- Security Advisor pre-DML: sin hallazgos H2 criticos/warn; solo `INFO rls_enabled_no_policy` legacy no-H2.
- Conteos pre-DML: `courses=350`, `course_editorial_state=0`, `courses_public_effective=0`, RPC batch presente.
- Dry-run: `DRY_RUN scanned=350 inserted=350 updated=0 deleted=0 noop=0`.
- Apply: `APPLY scanned=350 inserted=350 updated=0 deleted=0 noop=0`.
- Segundo run: `APPLY scanned=350 inserted=0 updated=0 deleted=0 noop=350`.
- Conteos post-DML: `courses=350`, `course_editorial_state=350`, `courses_public_effective=0`, `quality_audit_count=350`, `editorial_field_definitions=0`.
- Distribucion calidad: `complete=131`, `pending=219`.
- Faltantes detectados: `duration=219`.
- Integridad de metadata editorial: `field_sources` y `field_timestamps` son objetos en 350/350 estados; `manual_overrides=0`, por lo que no habia timestamps manuales existentes que preservar en Free.
- Security Advisor post-DML: sin hallazgos H2 criticos/warn; persisten solo `INFO rls_enabled_no_policy` legacy no-H2.
- Performance Advisor post-DML: solo `INFO` legacy/uso reciente; no bloquea el cierre de backfill Free.
- Seed de `editorial_field_definitions`: no ejecutado porque no existe payload/script H2 de seed versionado en el repo; queda como decision separada antes de cerrar H2 si se requiere diccionario poblado.

## Payload Seed Editorial Field Definitions

- Payload local preparado: `db/migrations/20260826_h2_seed_editorial_field_definitions.sql`.
- Alcance: seed DML idempotente de 41 definiciones para `editorial_field_definitions`.
- Estrategia: `INSERT ... ON CONFLICT (field_key) DO UPDATE`, sin `DELETE`, `TRUNCATE`, DDL, secrets ni writes a otras tablas.
- Cobertura: campos requeridos del contrato H2 (`name`, `institution`, `url`, `slug`, `category`, `mode`, `duration`), defaults/display, campos computados, sponsorship, publication gates y auditoria manual privada.
- Seguridad: campos privados/editoriales quedan con `is_public=false`; no se exponen `manual_overrides`, `manual_updated_by`, `published_at`, sponsorship ni estados internos como publicos.
- Validaciones: seed count local `41`, `pytest tests/test_h2_editorial_migration.py` `19 passed`, suite H2 ampliada `89 passed`, PostgreSQL 17 harness `h2_pg17_harness_ok`, `py_compile` PASS y credential scan PASS.
- Security-auditor: sin hallazgos bloqueantes. Riesgo residual: `ON CONFLICT DO UPDATE` sobrescribe definiciones remotas si ya fueron editadas manualmente; el JIT debe hacer preflight read-only de drift antes de aplicar.
- Estado: listo para revision/aprobacion JIT DML Free separada; no aplicado remotamente.

## JIT DML Free Seed Ejecutado

- Proyecto verificado: `https://aqrldlmlszjtgpqiegaa.supabase.co`.
- Preflight H2: DDL H2 requerida en ledger, backfill Free ya aplicado, Security Advisor sin hallazgos H2 criticos/warn.
- Preflight diccionario: `editorial_field_definitions=0`, sin claves existentes ni drift manual.
- Payload aplicado: `db/migrations/20260826_h2_seed_editorial_field_definitions.sql`.
- Conteo post-seed: `41` definiciones.
- Distribucion post-seed: `12` required, `25` publicas, `16` privadas.
- Campos privados expuestos: `0`.
- Roles publicos: `anon` y `authenticated` tienen `SELECT`, no `INSERT`; RLS policy `editorial_field_definitions_public_select` filtra `is_public = true`.
- Visibilidad efectiva por rol: `anon=25`, `authenticated=25`.
- Security Advisor post-seed: sin hallazgos H2 criticos/warn; persisten solo `INFO rls_enabled_no_policy` legacy no-H2.
- Performance Advisor post-seed: solo `INFO` legacy/uso reciente, incluyendo indices aun sin uso; no bloquea cierre Free.
- No se ejecuto Pro, backfill adicional, writers, schedules, canaries, deploys, push, PR, merge ni commit.

## Bloqueos Vigentes

- Backfill remoto Free ejecutado y segundo `NOOP` validado.
- Seed de `editorial_field_definitions` aplicado y verificado en Free.
- Fix `db/migrations/20260826_h2_public_effective_view_public_fields_fix.sql` aplicado y verificado en Supabase Free; `courses_public_effective` remoto expone `0` campos privados.
- No se ejecuto Pro, certificacion, schedules, writers remotos, canaries, deploys, push ni PR.
- El ruido ajeno CRLF/whitespace en `scripts/**`, `scripts/shared/utils.py` y `tests/test_harvester.py` fue verificado sin diff funcional mediante `git diff --ignore-space-at-eol` y restaurado a HEAD para no contaminar H2.

## Correccion Local Superficie Publica H2

- Hallazgo corregido localmente: `courses_public_effective` y `COURSE_PUBLIC_FIELDS` no deben exponer campos privados/editoriales (`editorial_status`, `quality_status`, `missing_fields`, `field_sources`, `field_timestamps`, sponsorship, availability ni auditoria manual).
- Payload local: `db/migrations/20260826_h2_public_effective_view_public_fields_fix.sql`.
- Forward-only: hace `DROP VIEW IF EXISTS public.courses_public_effective` y `DROP FUNCTION IF EXISTS private.h2_public_courses_effective()` antes de recrear la funcion con firma publica reducida.
- Grants: revoca `EXECUTE` de la funcion privada a `PUBLIC`, `anon`, `authenticated` y `service_role`; luego concede solo `EXECUTE` explicito a `anon`, `authenticated` y `service_role`; la vista conserva `security_invoker=true` y `SELECT` acotado.
- Harness CI: `tests/sql/h2_pg17_harness.sql` usa `\ir ../../db/migrations/...` para rutas relativas al archivo y compatible con `psql -f tests/sql/h2_pg17_harness.sql` desde repo root.
- Validaciones post-fix: suite H2 focalizada `91 passed`; PostgreSQL 17 harness `h2_pg17_harness_ok`; `py_compile` PASS; lint PASS con 10 warnings preexistentes; TypeScript PASS; static build PASS; credential scan PASS.
- Security-auditor post-fix: sin bloqueantes tecnicos H2 restantes tras agregar grants explicitos. El bloqueo operativo por ruido legacy fue retirado al restaurar esos archivos a HEAD tras confirmar que no tenian diff funcional.

## JIT DDL Free Fix Superficie Publica Aplicado

- Proyecto verificado: `https://aqrldlmlszjtgpqiegaa.supabase.co`.
- Preflight dependencias `public.courses_public_effective`: sin dependencias bloqueantes.
- Preflight vista: `39` columnas, incluyendo campos privados/editoriales que debian retirarse.
- Payload aplicado: `db/migrations/20260826_h2_public_effective_view_public_fields_fix.sql`.
- Ledger remoto: `20260826020441/h2_public_effective_view_public_fields_fix`.
- Columnas post-apply: `28`.
- Campos privados/editoriales expuestos: `0`.
- `security_invoker`: `true`.
- Funcion privada: `PUBLIC` sin `EXECUTE`; `anon`, `authenticated` y `service_role` con `EXECUTE` explicito.
- Vista publica: `anon`, `authenticated` y `service_role` con `SELECT`.
- Consulta como `anon`: `courses_public_effective=0`, esperado por gate editorial sin publicacion efectiva.
- Security Advisor post-fix: sin hallazgos H2 criticos/warn; persisten solo `INFO rls_enabled_no_policy` legacy no-H2.
- Performance Advisor post-fix: solo `INFO` legacy/uso reciente; no bloquea cierre Free.
- No se ejecuto Pro, DML/backfill/seed adicional, writers, schedules, canaries, deploys, push, PR, merge ni commit.
