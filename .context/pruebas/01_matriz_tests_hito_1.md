# Matriz De Tests Hito 1

Plan subordinado a [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
La adenda CA1-only esta aprobada; esta matriz conserva runtime CA1 como
`PLANNED` y reconvierte `H1-CA2P`/`H1-CA7P` en verificaciones documentales de
traslado y preservacion historica. No autoriza ejecucion remota.

| Test ID | CA | Requisito verificable | Clasificacion | Precondicion | Procedimiento | Resultado esperado | Ambiente | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|---|
| `T-H1-CA1-001` | `CA1 / H1-CA1` | FG2 y FG3 tienen schedules y dispatch declarados | `CONTRACTUAL_CA` | Candidate YAML | Inspeccionar triggers y refs | Cadencias y ramas coinciden con contrato | Local | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-002` | `CA1 / H1-CA1` | Gates, circuit breaker y freshness preceden el limite | `CONTRACTUAL_CA` | Fixtures de instituciones | Ejecutar casos deshabilitado, circuito abierto, fresco y elegible | Solo elegibles consumen limite | Local | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-002B` | `CA1 / H1-CA1` | Reactivar pipeline no pierde URLs descubiertas | `REGRESSION_REQUIRED` | Primera corrida discovery-only | Habilitar pipeline y repetir con la misma URL | La URL se extrae antes de `pending`; no llega vacia a cleansing ni se descarta falsamente | Local | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-003A` | `CA1 / H1-CA1` | Fallo parcial FG2 o estado no demostrable no produce falso verde | `REGRESSION_REQUIRED` | Fallos controlados | Revisar runs F9.9 y ejecutar/analizar casos de fetch/persistencia en harvester | Salida no cero, stages downstream omitidos y trabajo persistido se conserva o se restaura | Local / Certification | Runs F9.9 `30781870451`, `30782109395`, `30782242009`, `30782360475`: fail-closed observado; QA independiente `PASS` segun `QA-F9.9-DEVIATION-001-RESULT` | `QA_VERIFIED_FAIL_CLOSED` |
| `T-H1-CA1-003B` | `CA1 / H1-CA1` | Fallo parcial FG3 no produce falso verde ni mutacion no confirmada | `REGRESSION_REQUIRED` | Fallos controlados FG3 | Inyectar timeout, HTTP indeterminado y fallo PATCH en FG3 | Salida no cero; no se limpia estado ante indeterminado; PATCH confirma una fila | Local / Production futura | FG3 no tuvo validacion positiva en Certification | `PLANNED` |
| `T-H1-CA1-004` | `CA1 / H1-CA1` | FG2 y FG3 no se cancelan entre si | `OPERABILITY_REQUIRED` | Workflow parseable | Validar concurrency group y `cancel-in-progress` | Serializacion por ref sin cancelar ejecucion activa | Local | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-005` | `CA1 / H1-CA1` | Secrets existen solo en CI/backend autorizado | `SECURITY_REQUIRED` | Candidate completo | Escanear tree y revisar bindings de environment | Cero secretos en Git/browser; identidad correcta | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-006` | `CA1 / H1-CA1` | Ejecucion efectiva FG2/FG3 por ambiente | `OPERABILITY_REQUIRED` | Adenda aprobada y candidate autorizado | Canary y smoke con cohorte acotada | Gates respetados y resultado observable sin falso verde | Certification / Production | Certification queda `DEVIATION_ACCEPTED_FAIL_CLOSED`; success path positivo se desplaza a F10 | `PLANNED` |
| `T-H1-CA1-007` | `CA1 / H1-CA1` | Candidate CA1-only no modifica CA2 ni otras superficies | `REGRESSION_REQUIRED` | Adenda aprobada y baseline productivo | Comparar object IDs y diff cerrado | Cero cambios DB, frontend, leads/email, backfill y artifacts CA2 | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-008` | `CA1 / H1-CA1` | Controles pre-main bloquean writers productivos ambiguos | `OPERABILITY_REQUIRED` | F9.9 autorizada | Ejecutar tests estaticos de workflows y preflight | `db-sync-to-pro` report-only en push, apply manual DDL-gated, FG1/FG2/FG3 environment-bound y pause fail-closed | Local / CI | PR #280, `tests/test_fase09_9_pre_main_controls.py` y `tests/test_fase10_main_boundary.py`; CI post-merge PASS | `VERIFIED_PRE_MAIN_CONTROLS` |
| `T-H1-CA2P-001` | `CA2 / H1-CA2P -> H2-CA2` | El alcance CA2P queda preservado como antecedente y trasladado a Hito 2 | `CONTRACTUAL_CA` | Adenda aprobada | Contrastar REQ, TASK, Hito 2 y candidate CA1-only | CA2P no se declara cerrado, no se promueve con CA1-only y exige evidencia nueva en Hito 2 | Documental | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA7P-001` | `CA7 / H1-CA7P -> H4-CA7` | Preparacion documental original queda preservada como antecedente historico | `CONTRACTUAL_CA` | Adenda aprobada | Revisar enlaces, TASK H4 y paquete de evidencia | No se crea CA nuevo, no se reabre cierre historico y H4 requiere evidencia nueva | Documental | Vacia hasta candidate | `PLANNED` |
| `T-H1-OOS-001` | `CA1` | FG1 no se convierte en CA adicional | `OUT_OF_SCOPE` | Candidate CA1 | Revisar evidencia y matriz cliente | FG1 figura solo como soporte operativo | Documental | Vacia hasta candidate | `PLANNED` |

## Gate De Salida

La TASK decide el cierre. Esta matriz solo puede aportar evidencia nueva contra
el candidate y ambientes autorizados; no sustituye aprobacion cliente, QA,
canary, smoke ni observacion productiva.

## Interpretacion F9.9

- `T-H1-CA1-003A` queda `QA_VERIFIED_FAIL_CLOSED`: los runs F9.9 muestran fallo cerrado, ausencia de falso verde y QA independiente `PASS` sobre el bundle primario disponible.
- `T-H1-CA1-003B` queda `PLANNED`: FG3 no tuvo validacion positiva en Certification.
- `T-H1-CA1-006` no queda verificado: FG2 downstream, FG3 y success path siguen pendientes.
- La desviacion `DEVIATION_ACCEPTED_FAIL_CLOSED` no equivale a `PASS`; QA independiente solo verifica fail-closed y no valida success path ni Production.
- `T-H1-CA1-008` cubre solo controles de repositorio; no ejecuta Production, schedules, Supabase, Cloudflare ni writers remotos.
