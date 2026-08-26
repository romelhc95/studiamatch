# DDL-H2-SECURITY-ADVISOR-REMEDIATION-FREE

Status: `APPLIED_AND_READONLY_VERIFIED`
Environment: Development / Supabase Free
Target project ref: `aqrldlmlszjtgpqiegaa`
Requested branch: `feat/h2-editorial-model`
Requested scope: H2 Security Advisor remediation only
Payload: `db/migrations/20260826_h2_security_advisor_remediation.sql`

## Alcance Preparado

- Remediar `security_definer_view` en `public.courses_public_effective` sin abrir lectura publica directa a `courses` ni `course_editorial_state`.
- Remediar `function_search_path_mutable` en `public.prevent_course_editorial_audit_mutation`.
- Cerrar privilegios publicos residuales de `courses`, `course_editorial_state`, `leads` e `increment_view_count`.
- Reemplazar recomputacion de calidad por RPC publico invoker y funciones privadas acotadas con idempotencia atomica `request_id` + `payload_hash`.
- Agregar RPC batch maximo 1000 items para backfill futuro, sin ejecutar DML en esta autorizacion.

## Exclusiones

Esta autorizacion no aprueba ni autoriza:

- DML, seed o backfill.
- Supabase Pro.
- Writers remotos, schedules, canaries o deploys.
- Push, PR, merge o commit.
- Limpieza de archivos EOL/legacy registrada en backlog.

## Evidencia Local Disponible

- `pytest` H2 ampliado: `88 passed`.
- `py_compile` H2: `PASS`.
- PostgreSQL 17 harness: `h2_pg17_harness_ok` con remediacion aplicada dos veces.
- Frontend lint: `PASS` con 10 warnings preexistentes.
- TypeScript: `PASS`.
- Static build: `PASS`.
- Credential scan: `PASS`.
- Security auditor final: sin bloqueantes para dejar listo payload JIT DDL Free.

## Intento Remoto 2026-08-26

- Proyecto verificado: `https://aqrldlmlszjtgpqiegaa.supabase.co`.
- Payload autorizado: `db/migrations/20260826_h2_security_advisor_remediation.sql`.
- Resultado: `FAILED`, sin ledger remoto creado.
- Error PostgreSQL: `42P16: cannot change data type of view column "slug" from character varying to text`.
- Diagnostico read-only posterior: `private` schema ausente, `private.h2_public_courses_effective()` ausente, `public.h2_update_course_quality(uuid,text[],jsonb,jsonb,text,text)` ausente y `public.h2_update_course_quality_batch(jsonb)` ausente.
- Causa tecnica: la vista remota existente expone `slug` como `varchar`; el payload preparado declaraba `slug TEXT` en la funcion tabular privada que alimenta `CREATE OR REPLACE VIEW`.
- Accion: no se aplico payload modificado bajo esta autorizacion; requiere correccion local y nueva aprobacion JIT DDL Free.

## Correccion Local Post 42P16

- `private.h2_public_courses_effective()` declara `slug VARCHAR` y `seniority_level VARCHAR` para respetar tipos reales observados en Free.
- El payload ahora ejecuta `DROP VIEW IF EXISTS public.courses_public_effective` antes de recrearla, evitando fallos por tipo previo (`TEXT` vs `VARCHAR`) en replay local o remoto.
- El diseno de seguridad se conserva: tablas base sin grants publicos directos, vista publica `security_invoker=true` sobre lector privado acotado, RPC publico invoker y funciones privadas con grants minimos.
- Validaciones post-fix: `pytest tests/test_h2_editorial_migration.py` `18 passed`, suite H2 ampliada `88 passed`, `py_compile` PASS, PostgreSQL 17 harness `h2_pg17_harness_ok`, credential scan PASS y security-auditor sin bloqueantes.
- Riesgo residual no bloqueante: `DROP VIEW` podria fallar si existen dependencias remotas no previstas; el siguiente JIT debe incluir preflight read-only de dependencias antes de aplicar.

## Intento Remoto Corregido 2026-08-26

- Proyecto verificado: `https://aqrldlmlszjtgpqiegaa.supabase.co`.
- Preflight dependencias `public.courses_public_effective`: sin dependencias bloqueantes.
- Resultado: `SUCCESS`.
- Ledger remoto: `20260826010206/20260826_h2_security_advisor_remediation`.
- Objetos verificados read-only: schema `private`, `private.h2_public_courses_effective()`, `public.h2_update_course_quality(uuid,text[],jsonb,jsonb,text,text)`, `public.h2_update_course_quality_batch(jsonb)` y `public.courses_public_effective` presentes.
- Conteo `courses_public_effective`: `0`, esperado sin seed/backfill/publicacion masiva.
- Grants verificados: `anon` y `authenticated` sin `SELECT` directo sobre `courses` ni `course_editorial_state`, sin `INSERT` sobre `leads`, sin `EXECUTE` sobre `increment_view_count` ni RPCs H2; `service_role` con `EXECUTE` sobre RPCs H2 nuevos.
- Tipos de vista verificados: `slug varchar`, `seniority_level varchar`.
- Advisors seguridad: sin hallazgos H2 `security_definer_view` ni `function_search_path_mutable`; solo persisten `INFO rls_enabled_no_policy` legacy en `_view_count_dedup`, `schema_repair_audit` y `supabase_migrations`.
- Advisors performance: solo `INFO` legacy/uso reciente, incluyendo indices H2 aun no usados por falta de trafico/backfill; no bloquea JIT DML Free.

## Frase De Aprobacion Esperada

```text
Apruebo JIT DDL Free para DDL-H2-SECURITY-ADVISOR-REMEDIATION-FREE sobre Supabase Free proyecto ref aqrldlmlszjtgpqiegaa, exclusivamente para aplicar el payload exacto db/migrations/20260826_h2_security_advisor_remediation.sql y ejecutar verificacion read-only posterior.

No apruebo DML, seed, backfill, Supabase Pro, writers, schedules, canaries, deploys, push, PR, merge ni commit.
```
