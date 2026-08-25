# TASK-H1-001 - HITO-001

| Campo | Valor |
|---|---|
| ID | `TASK-H1-001` |
| Estado | `REDEFINED_ACTIVE_AFTER_H2_H3` |
| Requerimiento | `REQ-EST-001` |
| Hito | [HITO-001](../../hitos/hito_001.md) |
| Cutoff contractual | PR #291 / `64e4ed895d43121c5683e26a355993f18e528a5c` |
| Baseline tecnico | PR #327 / `main@ad89e8ab9575b37476502d6062e22c044ad6447b` |

## Disposicion

- `H1-CA1=ACCEPTED_WITH_WAIVERS`.
- `H1-CA1` del nuevo pedido requiere evidencia nueva y no puede cerrarse con waivers historicos.
- `EVID-H1-011=WAIVED_NOT_VERIFIED`.
- `EVID-H1-012=WAIVED_NOT_VERIFIED`.
- `EVID-H1-013=WAIVED_NOT_VERIFIED`.
- `EVID-H1-016=CLIENT_CONFORMITY_ACCEPTED_2026_08_19`.
- `F10.9/WP2B=SUPERSEDED`; PR #413 queda `CLOSED_NOT_MERGED_EXCLUDED`.
- `F10.10/M3=HISTORICAL_NON_PROMOTABLE`.

## Transferencia De Alcance

- `H1-CA2P` se transfiere a [TASK-H2-001](./tarea_002_hito_2.md) como `H2-CA2`.
- `H1-CA7P` se transfiere a [TASK-H4-001](./tarea_004_hito_4.md) como `H4-CA7`.

La historia contractual queda congelada. Para el nuevo pedido, H1 se ejecuta
despues de H2 y H3 aceptados, con autorizacion JIT separada para workflows,
writers, schedules o produccion.
