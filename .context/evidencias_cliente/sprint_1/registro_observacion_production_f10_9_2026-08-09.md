# Registro De Observacion Production F10.9 - 2026-08-09

| Campo | Valor |
|---|---|
| ID | `EVID-H1-OBS-F10.9-001` |
| Estado | `OBSERVATION_RESET_ZERO_ACCEPTED_PAIRS` |
| Subfase | `F10.9` |
| Base observada | `main@38314170197a907ac5c4c815a9bb18b3d5f29b06` / tree `741627eda4b4fbcf76503b8e353abb08ac0eb1c4` |
| Evidencias | `EVID-H1-011`, `EVID-H1-012`, `EVID-H1-013` |

## Ledger Append-Only

| Run | Evento | Intento | Flujo | Resultado | Cuenta | Motivo sanitizado |
|---|---|---:|---|---|---|---|
| `31297402286` | `schedule` | 1 | FG2 | `FAIL_CLOSED_AUTH_401` | No | Credenciales scheduled aun no reconciliadas. |
| `31311174311` | `schedule` | 1 | FG3 | `SUCCESS_PREFLIGHT_ONLY` | No | Integrity skipped por automation disabled. |
| `31318589218` | `workflow_dispatch` | 1 | FG2 | `FAIL_CLOSED_PRODUCTION_PAUSED` | No | Environment manual `Production`; no prueba scheduled. |
| `31318468550` | `workflow_dispatch` | 1 | FG3 | `FAIL_CLOSED_PRODUCTION_PAUSED` | No | Environment manual `Production`; no prueba scheduled. |
| `31297402286` | `schedule` rerun | 2 | FG2 | `FAIL_CLOSED_FG2_PARTIAL` | No | Credenciales validas; harvesting global incompleto. |
| `31311174311` | `schedule` rerun | 2 | FG3 | `FAIL_CLOSED_FG3_INCONCLUSIVE` | No | Credenciales validas; resultados HTTP inconclusos. |

## Estado De Observacion

| Metrica | Estado |
|---|---|
| Pares FG2 -> FG3 aceptados | `0` |
| Runs naturales aceptados | `0` |
| Inicio ventana 72h | `NOT_STARTED` |
| Secuencia consecutiva | `RESET_REQUIRED` |
| `EVID-H1-011` | `PENDING` |
| `EVID-H1-012` | `PENDING` |
| `EVID-H1-013` | `PENDING` |

## Regla De Conteo

Solo cuentan runs naturales `event=schedule` que completen todas las estaciones
aplicables sobre el candidate congelado. No cuentan reruns, workflow_dispatch,
skipped, cancelled, timeout, parcial, false-green, `401/403/429/5xx`, error de
red, TimeGuard o mutacion no demostrada.

La salida requiere tres pares FG2 -> FG3 consecutivos y al menos 72 horas desde
el inicio del primer FG2 aceptado hasta el cierre del tercer FG3 aceptado. Cero
dispatches, reruns o ejecuciones manuales pueden completar ese intervalo.

Cada nuevo par aceptable debe registrar run IDs, SHA/tree, environment,
conclusion, conteos sanitizados, mutaciones/NOOP demostrados y ausencia de drift.

## Impacto

Los runs documentados prueban controles fail-closed y validan posteriormente el
contrato de credenciales, pero no acreditan `EVID-H1-011/012`. La observacion se
reinicia despues de promover y autorizar
[PLAN-REM-F10.9-001](../../operaciones/plan_remediacion_f10_9_fg2_fg3.md).

`EVID-H1-010=VERIFIED` permanece preservada por el Production Canary F10.8.

## Sanitizacion

Este ledger no contiene URLs, dominios, instituciones de cohorte, UUID, hosts
Supabase, valores de secrets ni datos operativos. La evidencia privada permanece
fuera de Git.
