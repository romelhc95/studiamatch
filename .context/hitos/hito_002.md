# HITO-002 - Modelo Editorial Y Calidad

| Campo | Valor |
|---|---|
| Lifecycle stage | `AWAITING_DIGEST` |
| Gate status | `READY_FOR_DIGEST_APPROVAL` |
| Implementation status | `PLANNED_NOT_ACTIVE` |
| Acceptance status | `NOT_STARTED` |
| Work package | `WP-H2-001` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Criteria status | `H2-CA2=NOT_STARTED`, `H2-CA3=NOT_STARTED` |
| Gate | O5, checkout limpio y aprobacion digest+commit de `WP-H2-001` |

## Alcance

Hito 2 implementa CA2 completo antes de integrar CA3: schema editorial/calidad, estados, faltantes, fuentes por campo, timestamps manuales, auditoria append-only, RLS/grants, pipeline tolerante y backfill idempotente. No hay ejecucion activa en F10.11.

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

No inicia hasta completar O5, tener checkout limpio homologado y aprobar `WP-H2-001` por digest y commit candidate verificables. La primera aprobacion solo puede autorizar R1; R2 y cualquier R3 requieren aprobaciones posteriores separadas.
