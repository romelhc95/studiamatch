# DDL-H2-PUBLIC-EFFECTIVE-VIEW-FIELDS-FIX-FREE

Status: `APPLIED_AND_READONLY_VERIFIED`
Environment: Development / Supabase Free
Target project ref: `aqrldlmlszjtgpqiegaa`
Requested branch: `feat/h2-editorial-model`
Requested scope: H2 public effective view field exposure fix only
Payload: `db/migrations/20260826_h2_public_effective_view_public_fields_fix.sql`

## Alcance Autorizado

- Aplicar solo el fix de superficie publica de `public.courses_public_effective`.
- Quitar campos privados/editoriales de la vista publica efectiva.
- Recrear `private.h2_public_courses_effective()` con firma publica reducida.
- Mantener `security_invoker=true` en la vista publica y grants explicitos sobre funcion/vista.
- Ejecutar preflight read-only de dependencias y verificacion read-only post-apply.

## Exclusiones

Esta autorizacion no aprueba ni autoriza:

- DML, seed o backfill adicional.
- Supabase Pro.
- Writers remotos, schedules, canaries o deploys.
- Push, PR, merge o commit.
- Limpieza de archivos EOL/legacy registrada en backlog.

## Evidencia Local Disponible

- Suite H2 focalizada: `91 passed`.
- PostgreSQL 17 harness: `h2_pg17_harness_ok`.
- `py_compile` H2: `PASS`.
- Frontend lint: `PASS` con 10 warnings preexistentes.
- TypeScript: `PASS`.
- Static build: `PASS`.
- Credential scan: `PASS`.
- Security-auditor: `GO` para solicitar JIT DDL Free; `NO GO` para PR hasta verificar remoto y limpiar diff legacy.

## Aplicacion Remota 2026-08-26

- Proyecto verificado: `https://aqrldlmlszjtgpqiegaa.supabase.co`.
- Preflight dependencias `public.courses_public_effective`: sin dependencias bloqueantes.
- Preflight vista: `39` columnas, incluyendo campos privados/editoriales que debian retirarse.
- Resultado: `SUCCESS`.
- Ledger remoto: `20260826020441/h2_public_effective_view_public_fields_fix`.

## Verificacion Read-Only Post-Apply

- Columnas de `public.courses_public_effective`: `28`.
- Campos privados/editoriales expuestos: `0`.
- `slug`: `varchar`; `seniority_level`: `varchar`.
- `security_invoker`: `true`.
- Funcion privada: `PUBLIC` sin `EXECUTE`; `anon`, `authenticated` y `service_role` con `EXECUTE` explicito.
- Vista publica: `anon`, `authenticated` y `service_role` con `SELECT`.
- Consulta como `anon`: `courses_public_effective=0`, esperado por gate editorial sin publicacion efectiva.
- Security Advisor: sin hallazgos H2 criticos/warn; persisten solo `INFO rls_enabled_no_policy` legacy no-H2.
- Performance Advisor: solo `INFO` legacy/uso reciente, incluyendo indices H2 aun sin uso; no bloquea el cierre Free.
