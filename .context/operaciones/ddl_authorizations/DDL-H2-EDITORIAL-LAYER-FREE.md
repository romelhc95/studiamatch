# DDL-H2-EDITORIAL-LAYER-FREE

Status: CONSUMED_BY_FREE_DDL
Environment: Development / Supabase Free
Target project ref: `aqrldlmlszjtgpqiegaa`
Requested branch: `feat/h2-editorial-model`
Requested scope: H2 editorial layer DDL only
Authorized by: user conversation on 2026-08-25
Authorized migrations: `20260825_h2_editorial_layer.sql`, `20260825_h2_editorial_layer_grants_fix.sql`, `20260825_h2_editorial_layer_start_date_view_fix.sql`, `20260825_h2_editorial_layer_allowlist_fix.sql`
Consumed migrations ledger: `20260825205937/20260825_h2_editorial_layer`, `20260825210119/20260825_h2_editorial_layer_grants_fix`, `20260825210927/20260825_h2_editorial_layer_start_date_view_fix`, `20260825211309/20260825_h2_editorial_layer_allowlist_fix`

## Alcance Solicitado

Solicitud JIT para autorizar, en un PR H2 separado, la creacion de una migracion
forward-only que agregue la capa editorial:

- `public.editorial_field_definitions`.
- `public.course_editorial_state`.
- `public.course_editorial_audit`.
- Vista `public.courses_public_effective` con `security_invoker = true`.
- RLS, policies y grants explicitos para los objetos anteriores.
- Revocacion de captura publica de `leads` solo si se incluye en el mismo alcance H2 aprobado.
- Tests estaticos/offline de RLS, grants, vista efectiva, audit append-only y no-publicacion pipeline.

## Exclusiones

Esta autorizacion no aprueba ni autoriza:

- Ejecutar DDL o DML en Supabase Pro.
- Backfill de `course_editorial_state`.
- Cambios de Auth, creacion de usuarios admin o configuracion de signup.
- Activar writers, schedules, FG1, FG2, FG3, canaries o deploys.
- DB Sync a Pro.
- Publicacion masiva de cursos.
- Cambios frontend H4/H5 fuera del retiro de captura publica si se aprueba explicitamente.

## Evidencia Requerida Antes De Apply Free

1. PR H2 con migracion SQL versionada y tests offline verdes.
2. Revision `@security-auditor` sin hallazgos bloqueantes.
3. `security-audit` verde en PR a `desarrollo`.
4. Confirmacion humana explicita cambiando este registro a `APPROVED_FOR_FREE_DDL` o instruccion equivalente en conversacion.
5. Comando exacto o SQL exacto a ejecutar en Supabase Free.
6. Plan de rollback/forward-fix y verificacion read-only posterior.

## Frase De Aprobacion Esperada

```text
Apruebo JIT DDL Free para DDL-H2-EDITORIAL-LAYER-FREE sobre feat/h2-editorial-model, exclusivamente para la migracion H2 editorial layer y su verificacion read-only posterior. No apruebo Pro, backfill, writers, schedules, canaries ni deploys.
```

## Verificacion Read-Only Free

- Objetos creados: `editorial_field_definitions`, `course_editorial_state`, `course_editorial_audit`, `courses_public_effective`.
- RLS habilitado en las tres tablas nuevas.
- Vista `courses_public_effective` con `security_invoker=true`.
- `course_editorial_audit` efectivo para `service_role`: solo `SELECT` e `INSERT`.
- `course_editorial_state` efectivo para `service_role`: `SELECT`, `INSERT` y `UPDATE`; sin `DELETE` ni `TRUNCATE`.
- `course_editorial_state` para `anon/authenticated`: `SELECT` por columnas publicas y RLS con gates `published`, `complete`, `courses.is_active`, `courses.is_verified` y `production_enabled`.
- `courses_public_effective` filas actuales: `0`, esperado porque no hubo backfill ni publicacion masiva.
- Security advisor: sin hallazgos nuevos sobre los objetos H2; solo infos legacy preexistentes de tablas con RLS sin policy.
- Performance advisor: reporta indices H2 como `unused_index`, esperado inmediatamente despues de crear objetos sin carga/backfill.
- Forward-fix aplicado en Free: `20260825_h2_editorial_layer_start_date_view_fix.sql` elimina el cast inseguro de `manual_overrides.start_date` a `DATE`.
- Forward-fix aplicado en Free: `20260825_h2_editorial_layer_allowlist_fix.sql` retira `start_date` del allowlist mientras queda pipeline-owned.

## Estado Actual

Autorizacion consumida completamente en Supabase Free para las cuatro migraciones
indicadas y verificacion read-only posterior. No autoriza Pro, backfill, writers,
schedules, canaries ni deploys. Cualquier accion adicional requiere nueva JIT.
