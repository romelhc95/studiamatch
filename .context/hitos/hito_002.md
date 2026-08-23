# HITO-002 - Modelo Editorial Y Calidad

| Campo | Valor |
|---|---|
| Lifecycle stage | `ACTIVE` |
| Gate status | `APPROVED_R1` |
| Implementation status | `BLOCKED_PENDING_OBSIDIAN_MAIN` |
| Acceptance status | `NOT_STARTED` |
| Work package | `WP-H2-001` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Criteria status | `H2-CA2=NOT_STARTED`, `H2-CA3=NOT_STARTED` |
| Gate | `WP-H2-001` activo hasta R1; `F12.1` bloqueado hasta cierre Obsidian efectivo en main. |

## Enlaces Canonicos

- Estado vivo: [Estado Del Proyecto](../estado_del_proyecto.md)
- Plan Maestro: [Plan Maestro Sprint 1 H2-H5](../operaciones/plan_maestro_sprint1_h2_h5.md)
- TASK: [TASK-H2-001](../backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md)
- Matriz: [Matriz Hito 002](../matrices/matriz_hito_002.md)
- Evidencia: [Evidencia Hito 002](../evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md)
- Work package: [WP-H2-001](../work_packages/WP-H2-001.json)

## Alcance

Hito 2 implementara CA2 completo antes de integrar CA3: schema editorial/calidad, estados, faltantes, fuentes por campo, timestamps manuales, auditoria append-only, RLS/grants, pipeline tolerante y backfill idempotente. `WP-H2-001` esta activo solo hasta R1; `F12.1` queda bloqueada hasta que la documentacion Obsidian canonica exista en main, se homologue y el checkout ordinario la consuma.

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

`F12.1` queda como traza futura de implementacion local H2-CA2 R1. No inicia H2-CA2 ni H2-CA3 hasta cierre efectivo de Etapa 1 en main y nueva/rebasada aprobacion WP. R2 y cualquier R3 requieren aprobaciones posteriores separadas.
