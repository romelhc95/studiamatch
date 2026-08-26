# Plan Maestro Sprint 1 H2-H5

> Esta nota no crea alcance ni autoriza ejecucion. La autoridad viva esta en
> [`estado_del_proyecto.md`](../estado_del_proyecto.md) y el nuevo plan activo
> esta en [Plan Vinculante Nuevo Pedido](plan_vinculante_nuevo_pedido_2026_08_25.md).

## Estado

```text
FASE = F11
ESTADO = H2_MERGED_TO_DESARROLLO_CI_GREEN
H2-H5 = REDEFINED_ACTIVE_SEQUENCE
active_work_package = NONE_SUPERSEDED
next_gate = PROMOTE_DESARROLLO_TO_CERTIFICACION_FOR_H2
DB = FREE_H2_VALIDATED_BLOCKED_FOR_NEW_DDL_DML_WITHOUT_JIT
PRODUCTION_MUTATIONS = BLOCKED_WITHOUT_JIT
```

## Flujo Vigente

```text
feat/* o docs/* desde desarrollo
-> PR protegido a desarrollo
-> PR protegido desarrollo a certificacion
-> PR protegido certificacion a main
```

## Reglas

- H2-H5 quedan redefinidos por el nuevo plan vinculante; H2 fue mergeado a `desarrollo` mediante PR #458 y queda pendiente de promocion protegida a `certificacion`.
- Work Packages, grants R3, digests documentales, Context Graph y promotion gates historicos quedan superseded y no autorizan ejecucion.
- Cambios DB, DDL/DML, Supabase, writers, schedules, deploys, produccion, backups y acciones destructivas requieren aprobacion JIT separada.
- `security-audit` permanece como check requerido.
- DB Sync permanece manual-only.

## Bases De Transicion

| Rama | Commit | Estado |
|---|---|---|
| `desarrollo` | `8ed8e36259af53a16e1f473ad906b5beadd5b09c` | PR #451 mergeado con flujo simple. |
| `certificacion` | `8b843ac3714866dbce7b44958362fe7243ae06b9` | PR #452 mergeado con reconciliacion. |
| `main` | `6128e5861ade426840a650335f7f859c803e5431` | PR #453 mergeado; Cloudflare Pages automatico exitoso. |

## Hitos Pendientes

| Hito | Estado | Gate futuro |
|---|---|---|
| H2 | `NEXT_ACTIVE_SCOPE_PENDING_PR_AND_JIT_DB` | PR H2 separado y aprobacion JIT para DB. |
| H3 | `PLANNED_AFTER_H2_ACCEPTED` | H2 aceptado. |
| H4 | `PLANNED_AFTER_H2_CONTRACT_STABLE` | Contrato H2 estable. |
| H5 | `PLANNED_AFTER_H2_CONTRACT_STABLE` | Contrato H2 estable. |

## Stop Conditions

- Aparece un secreto o valor credential-like.
- Cambia una ruta protegida sin aprobacion separada.
- Se intenta ejecutar DB Sync, DDL/DML o writer productivo.
- Se intenta iniciar H2 con DDL/DML, Supabase o backfill sin aprobacion JIT separada.
