# Plan Maestro Sprint 1 H2-H5

> Esta nota no crea alcance ni autoriza ejecucion. La autoridad viva esta en
> [`estado_del_proyecto.md`](../estado_del_proyecto.md). [`REDEFINICION.md`](../../REDEFINICION.md)
> se conserva como soporte temporal sin autoridad independiente.

## Estado

```text
FASE = F10.11
ESTADO = SIMPLE_FLOW_DEPLOYED_PENDING_CLIENT_GO
H2-H5 = PLANNED_NOT_ACTIVE
active_work_package = NONE_SUPERSEDED
next_gate = CLIENT_GO_FOR_NEXT_SCOPE
DB = BLOCKED_NO_DDL_DML_WITHOUT_JIT
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

- H2-H5 no inician durante F10.11.
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
| H2 | `PLANNED_NOT_ACTIVE` | Nuevo pedido explicito y aprobacion JIT para DB si aplica. |
| H3 | `PENDING` | H2 aceptado y nuevo pedido explicito. |
| H4 | `PENDING` | Nuevo pedido explicito. |
| H5 | `PENDING` | Nuevo pedido explicito. |

## Stop Conditions

- Aparece un secreto o valor credential-like.
- Cambia una ruta protegida sin aprobacion separada.
- Se intenta ejecutar DB Sync, DDL/DML o writer productivo.
- Se intenta iniciar nuevo alcance sin GO del cliente.
