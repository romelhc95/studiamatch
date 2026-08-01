# Matriz De Tests Hito 2

Plan subordinado a [TASK-H2-001](../backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md).
Hito 2 permanece `PENDING`, sin subfase ejecutable.

| Test ID | CA | Requisito verificable | Clasificacion | Precondicion | Procedimiento | Resultado esperado | Ambiente | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|---|
| `T-H2-CA2-001` | `CA2 / H2-CA2` | Schema soporta calidad, faltantes, fuentes, actualizacion manual e inicio | `CONTRACTUAL_CA` | Candidate DB forward-only | Aplicar en DB efimera e inspeccionar contrato | Tipos, defaults y constraints coinciden con REQ/TASK | Local PostgreSQL | Vacia hasta candidate | `PLANNED` |
| `T-H2-CA2-001B` | `CA2 / H2-CA2` | Schema soporta flags base de patrocinio/leads sin entrega real-time | `CONTRACTUAL_CA` | Candidate DB forward-only | Aplicar fixtures patrocinado, organico y lead base | Campos/flags persisten con defaults y restricciones acordados, sin egress | Local PostgreSQL | Vacia hasta candidate | `PLANNED` |
| `T-H2-CA2-002` | `CA2 / H2-CA2` | Estado ETL y editorial permanecen separados | `CONTRACTUAL_CA` | Fixtures de pipeline y edicion | Procesar y editar el mismo registro | Pipeline no sobrescribe procedencia manual protegida | Local | Vacia hasta candidate | `PLANNED` |
| `T-H2-CA2-002B` | `CA2 / H2-CA2` | Mock o pendiente no se publica como verificado | `SECURITY_REQUIRED` | Matriz calidad/editorial | Cruzar `is_mock_data`, estado pendiente, `production_enabled`, `is_active` e `is_verified` | Solo registros que cumplen contrato editorial pueden quedar activos/verificados | Local / Free | Vacia hasta candidate | `PLANNED` |
| `T-H2-CA2-003` | `CA2 / H2-CA2` | RLS, grants y RPC aplican minimo privilegio | `SECURITY_REQUIRED` | Matriz de roles | Ejecutar positivos y negativos anon, authenticated, pipeline y admin | Solo operaciones explicitamente autorizadas pasan | Local / Free | Vacia hasta candidate | `PLANNED` |
| `T-H2-CA2-004` | `CA2 / H2-CA2` | Candidate es reproducible e idempotente | `OPERABILITY_REQUIRED` | Manifest y checksums cerrados | Apply/replay en DB efimera; probar rollback transaccional y recovery del runbook | Postcondicion estable sin down migration, edicion de ledger ni replay remoto improvisado | Local / Free | Vacia hasta candidate | `PLANNED` |
| `T-H2-CA2-005` | `CA2 / H2-CA2` | Backfill separado evita catalogo invisible | `REGRESSION_REQUIRED` | Schema certificado y backfill aprobado | Ejecutar y repetir una cohorte ligada separadamente a cada ambiente | Catalogo visible, segunda corrida sin cambios y cero copia de filas Free a Pro | Free / Pro | Vacia hasta candidate | `PLANNED` |
| `T-H2-CA3-001` | `CA3 / H2-CA3` | Campos vacios no detienen el pipeline | `CONTRACTUAL_CA` | Fixtures completos e incompletos | Recorrer cuatro estaciones | Incompletos se conservan y lote continua | Local | Vacia hasta candidate | `PLANNED` |
| `T-H2-CA3-002` | `CA3 / H2-CA3` | Pendiente y completo se calculan de forma determinista | `CONTRACTUAL_CA` | Reglas CA2 certificadas | Procesar fixtures limite | Cada registro obtiene estado y faltantes esperados | Local | Vacia hasta candidate | `PLANNED` |
| `T-H2-CA3-003` | `CA3 / H2-CA3` | Reintentos no duplican ni pierden procedencia | `REGRESSION_REQUIRED` | Fallo parcial controlado | Reejecutar desde estado recuperable | Mismo resultado sin duplicados ni perdida | Local / Free | Vacia hasta candidate | `PLANNED` |
| `T-H2-CA3-004` | `CA3 / H2-CA3` | Cohortes mayores al limite se recorren completamente | `OPERABILITY_REQUIRED` | Dataset paginado | Ejecutar todas las paginas/batches | Todos los IDs visitados segun contrato | Local / Free | Vacia hasta candidate | `PLANNED` |
| `T-H2-OOS-001` | `CA2` | Leads base no implica email/webhook real-time | `OUT_OF_SCOPE` | Candidate H2 | Inspeccionar diff, egress y evidencia | Cero entrega comercial real-time agregada | Local / CI | Vacia hasta candidate | `PLANNED` |

## Gate De Salida

CA2 debe certificarse como unidad antes de integrar CA3. Schema/RLS y backfill
usan gates separados; ninguna prueba de esta matriz autoriza operaciones
remotas por si misma.
