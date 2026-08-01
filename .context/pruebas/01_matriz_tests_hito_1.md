# Matriz De Tests Hito 1

Plan subordinado a [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
La adenda CA1-only sigue pendiente; esta matriz no cambia el mapa contractual
original ni autoriza ejecucion remota.

| Test ID | CA | Requisito verificable | Clasificacion | Precondicion | Procedimiento | Resultado esperado | Ambiente | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|---|
| `T-H1-CA1-001` | `CA1 / H1-CA1` | FG2 y FG3 tienen schedules y dispatch declarados | `CONTRACTUAL_CA` | Candidate YAML | Inspeccionar triggers y refs | Cadencias y ramas coinciden con contrato | Local | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-002` | `CA1 / H1-CA1` | Gates, circuit breaker y freshness preceden el limite | `CONTRACTUAL_CA` | Fixtures de instituciones | Ejecutar casos deshabilitado, circuito abierto, fresco y elegible | Solo elegibles consumen limite | Local | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-002B` | `CA1 / H1-CA1` | Reactivar pipeline no pierde URLs descubiertas | `REGRESSION_REQUIRED` | Primera corrida discovery-only | Habilitar pipeline y repetir con la misma URL | La URL se extrae antes de `pending`; no llega vacia a cleansing ni se descarta falsamente | Local | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-003` | `CA1 / H1-CA1` | Fallo parcial o estado no demostrable no produce falso verde | `REGRESSION_REQUIRED` | Fallos controlados | Inyectar timeout y fallos internos de fetch/persistencia en harvester y HEAD/PATCH en FG3 | Salida no cero, freshness no oculta el parcial y trabajo persistido se conserva | Local | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-004` | `CA1 / H1-CA1` | FG2 y FG3 no se cancelan entre si | `OPERABILITY_REQUIRED` | Workflow parseable | Validar concurrency group y `cancel-in-progress` | Serializacion por ref sin cancelar ejecucion activa | Local | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-005` | `CA1 / H1-CA1` | Secrets existen solo en CI/backend autorizado | `SECURITY_REQUIRED` | Candidate completo | Escanear tree y revisar bindings de environment | Cero secretos en Git/browser; identidad correcta | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-006` | `CA1 / H1-CA1` | Ejecucion efectiva FG2/FG3 por ambiente | `OPERABILITY_REQUIRED` | Adenda aprobada y candidate autorizado | Canary y smoke con cohorte acotada | Gates respetados y resultado observable sin falso verde | Certification / Production | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA1-007` | `CA1 / H1-CA1` | Candidate CA1-only no modifica CA2 ni otras superficies | `REGRESSION_REQUIRED` | Adenda aprobada y baseline productivo | Comparar object IDs y diff cerrado | Cero cambios DB, frontend, leads/email, backfill y artifacts CA2 | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA2P-001` | `CA2 / H1-CA2P` | El alcance original permanece trazable mientras la adenda sea draft | `CONTRACTUAL_CA` | Adenda no aprobada | Contrastar REQ, TASK y candidate | CA2P no se declara cerrado ni se promueve con CA1-only | Documental | Vacia hasta candidate | `PLANNED` |
| `T-H1-CA7P-001` | `CA7 / H1-CA7P` | Preparacion documental original permanece trazable | `CONTRACTUAL_CA` | Adenda no aprobada | Revisar enlaces y anexo por ambiente | No se crea CA nuevo ni se reabre estado completado | Documental | Vacia hasta candidate | `PLANNED` |
| `T-H1-OOS-001` | `CA1` | FG1 no se convierte en CA adicional | `OUT_OF_SCOPE` | Candidate CA1 | Revisar evidencia y matriz cliente | FG1 figura solo como soporte operativo | Documental | Vacia hasta candidate | `PLANNED` |

## Gate De Salida

La TASK decide el cierre. Esta matriz solo puede aportar evidencia nueva contra
el candidate y ambientes autorizados; no sustituye aprobacion cliente, QA,
canary, smoke ni observacion productiva.
