# HITO-001 - Automatizacion Segura CA1

`HITO-001` historico queda preservado por decision humana O0-B con waivers. Para el nuevo pedido, H1 se redefine como automatizacion segura y reactivacion gradual de FG1/FG2/FG3 despues de H2 y H3 aceptados. Esta nota no autoriza ejecucion remota.

## Resultado

| Campo | Valor |
|---|---|
| Estado | `REDEFINED_ACTIVE_AFTER_H2_H3` |
| Criterio activo | `H1-CA1` |
| Cutoff contractual | PR #291 / `64e4ed895d43121c5683e26a355993f18e528a5c` |
| Baseline tecnico posterior | PR #327 / `main@ad89e8ab9575b37476502d6062e22c044ad6447b` |
| Waivers historicos | `EVID-H1-011`, `EVID-H1-012`, `EVID-H1-013`, `EVID-H1-016`; no cierran CA1 nuevo |

## Alcance Nuevo

- Readiness de FG1, FG2 y FG3.
- Preflight distingue `blocked`, `preflight-only` y ejecucion funcional.
- Corridas con estaciones skipped no cierran evidencia funcional.
- Validacion con `actionlint`, frecuencia documentada y concurrency group corregido.
- Confirmacion de `pipeline_ready`, limites, entornos y rollback.
- Activacion JIT secuencial: FG1, observar, repausar/evaluar; FG2, observar, repausar/evaluar; FG3, observar, repausar/evaluar; schedules ordinarios.

## Transferencias

- `H1-CA2P` pasa a `H2-CA2` y requiere evidencia nueva.
- `H1-CA7P` pasa a `H4-CA7` y requiere evidencia nueva.
- F10.9/WP2B y F10.10/M3 son historia no promocionable.
- Waivers historicos de H1 no pueden reutilizarse para cerrar CA1 del nuevo pedido.

## Trazabilidad

- [Acta de cierre contractual](../evidencias_cliente/sprint_1/acta_cierre_contractual_hito_001.md)
- [ADR-0026](../decisiones/ADR-0026_cutoff_h1_y_baseline_sprint1.md)
- [Plan Maestro H2-H5](../operaciones/plan_maestro_sprint1_h2_h5.md)
