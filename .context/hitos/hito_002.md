# HITO-002 - Modelo Editorial Y Calidad

| Campo | Valor |
|---|---|
| Estado | `H2_COMPAT_MERGED_TO_DESARROLLO_PENDING_CERTIFICATION` |
| Work package | `SUPERSEDED` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Gate | Promocion protegida desarrollo a certificacion y validacion de despliegue estable; Pro/writers/main requieren nueva JIT |

## Alcance

Hito 2 implementa CA2 completo antes de integrar CA3: schema editorial/calidad, estados, faltantes, fuentes por campo, timestamps manuales, auditoria append-only, RLS/grants, pipeline tolerante y backfill idempotente. La DDL Free inicial, el forward-fix, la remediacion Security Advisor, el backfill editorial, el seed versionado de `editorial_field_definitions` y el fix `20260826_h2_public_effective_view_public_fields_fix.sql` fueron aplicados/verificados en Supabase Free bajo JIT consumidas. PR #458 fue aprobado y mergeado a `desarrollo`; PR #459 agrego el gate documental post-merge; PR #460 promovio H2 a `certificacion`, todos con checks verdes.

## Validacion Contra Fuente Cliente

El cierre H2 valida `H2-CA2` y `H2-CA3` contra la fuente privada cliente `SRC-REQ-002` mediante la atestacion sanitizada versionada [ADENDA-REQ-EST-001-001](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md). La fuente privada no se versiona ni se expone en PRs.

## Contrato Editorial

El diseno debe clasificar cada campo como `pipeline_owned`, `manual_owned`, `computed` o `hybrid_manual_preferred`. Los valores manuales tienen precedencia sobre pipeline salvo autorizacion explicita y auditoria. El pipeline no puede publicar programas por si solo.

## Diccionario Minimo

| Campo conceptual | Ownership | Uso |
|---|---|---|
| Estado editorial | Manual/admin | Publicacion y cola admin. |
| Estado de calidad | Computed/pipeline | Identificar completos, pendientes y bloqueados. |
| `missing_fields` | Computed | Explicar por que un registro esta pendiente. |
| `field_sources` | Hybrid | Trazar fuente de cada campo. |
| Fecha de inicio | Hybrid manual preferred | Cards y filtros. |
| Patrocinio | Manual/admin | Orden y distincion visual. |
| Leads base | Manual/admin | Flags de CTA visual; sin captura ni egress. |

## Estados Y Transiciones

| Estado | Origen | Transiciones permitidas |
|---|---|---|
| `draft` | Backfill/admin | `pending_review`, `archived` |
| `pending_review` | Pipeline/admin | `published`, `draft`, `archived` |
| `published` | Admin solamente | `pending_review`, `archived` |
| `archived` | Admin/integrity | `draft` con auditoria |

## Restricciones Obligatorias

1. Migracion nueva forward-only.
2. Estados editorial/calidad explicitos.
3. `missing_fields` persistente o reproducible.
4. `field_sources` persistente o reproducible.
5. Timestamps manuales preservados.
6. Patrocinio/leads base sin egress.
7. Auditoria append-only.
8. Pipeline tolerante a parciales.
9. Valores manuales protegidos contra overwrite pipeline.
10. Pipeline incapaz de publicar por si solo.
11. Paginacion para mas de 1000 filas.
12. Backfill reanudable.
13. Segundo run `NOOP` obligatorio.

## Pruebas Requeridas

- RLS por rol anon, authenticated, admin y service/CI.
- Grants minimos sobre tablas/RPC.
- Backfill primer run y segundo run `NOOP`.
- Preservacion de campos manuales.
- Registros incompletos conservados como pendientes.
- Writer inventory sin rutas ocultas.

## Gate

DDL Free inicial, forward-fix `20260826_h2_editorial_layer_forward_fix.sql`, remediacion `20260826_h2_security_advisor_remediation.sql`, backfill H2, seed `20260826_h2_seed_editorial_field_definitions.sql`, fix `20260826_h2_public_effective_view_public_fields_fix.sql` y compatibilidad `20260826_h2_development_legacy_public_compat.sql` aplicados bajo JIT consumidas. Security Advisor H2 critico/warn resuelto. Segundo run `NOOP` validado. Vista publica efectiva verificada con `0` campos privados, grants explicitos y `security_invoker=true`; post-apply Free: `227` cursos legacy elegibles, `227` en cohorte, `227` en `courses_public_effective`, `0` faltantes y `0` inesperados. Limpieza de calidad para PR #466 elimina rewrites rotos de detalle, llamadas legacy `ratings`/`reviews` y defaults fabricados del comparador; preview Cloudflare final `af2ac376` valida Calidad `GO`. PR #458, PR #459 y PR #466 mergeados a `desarrollo`; PR #460 promovio H2 base a `certificacion`; QA read-only previa H2/H3 aprobada en [QA Read-Only Certificacion H2/H3](../operaciones/h2_h3_certification_readonly_qa.md). La compatibilidad H2 queda lista para PR protegido `desarrollo -> certificacion`. Pro, writers, schedules, canaries, deploys manuales, `main` o cualquier DML adicional requieren aprobacion separada.
