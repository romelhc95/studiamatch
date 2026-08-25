# Plan Maestro Sprint 1 H2-H5

> Esta nota no crea alcance ni autoriza ejecucion. La autoridad viva esta en
> [`estado_del_proyecto.md`](../estado_del_proyecto.md) y, durante la
> transicion, en [`REDEFINICION.md`](../../REDEFINICION.md).

## Estado

```text
FASE = F10.11
ESTADO = SIMPLE_FLOW_LOCAL_VALIDATION
H2-H5 = PLANNED_NOT_ACTIVE
active_work_package = NONE_SUPERSEDED
next_gate = REMOTE_ACTIONS_REQUIRE_SEPARATE_AUTHORIZATION
DB = BLOCKED_NO_DDL_DML
PRODUCTION = BLOCKED
```

## Flujo Vigente

```text
feat/* o docs/* desde desarrollo
-> PR protegido a desarrollo
-> PR protegido desarrollo a certificacion
-> PR protegido certificacion a main
```

## Reglas

- H2-H5 no inician durante F10.11.
- Work Packages, grants R3, digests documentales, Context Graph y promotion gates historicos quedan superseded y no autorizan ejecucion.
- Cambios DB, DDL/DML, Supabase, writers, schedules, deploys, produccion, backups y acciones destructivas requieren aprobacion JIT separada.
- `security-audit` permanece como check requerido.
- DB Sync permanece manual-only.

## Bases De Transicion

| Rama | Commit | Estado |
|---|---|---|
| `main` | `9b486146962bd2a092acfd649fdcf716e922de89` | Baseline de redefinicion. |
| `desarrollo` | `8ed8e36259af53a16e1f473ad906b5beadd5b09c` | PR #451 mergeado con flujo simple. |
| `certificacion` | `df2cde3626c75fa4733bf1624fb105d8ee08c076` | Base para reconciliacion unica. |

## Hitos Pendientes

| Hito | Estado | Gate futuro |
|---|---|---|
| H2 | `PLANNED_NOT_ACTIVE` | Nuevo pedido explicito y aprobacion JIT para DB si aplica. |
| H3 | `PENDING` | H2 aceptado y nuevo pedido explicito. |
| H4 | `PENDING` | Nuevo pedido explicito. |
| H5 | `PENDING` | Nuevo pedido explicito. |

## Stop Conditions

- Aparece un secreto o valor credential-like.
- Cambia una ruta protegida sin aprobacion separada.
- Se intenta ejecutar DB Sync, DDL/DML o writer productivo.
- Se intenta avanzar a `main` sin checkpoint separado.
