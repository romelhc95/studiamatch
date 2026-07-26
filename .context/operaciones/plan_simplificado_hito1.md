# Plan Simplificado De Hito 1

## Estado Y Autoridad

- ID documental: `PLAN-H1-SIMPLIFICADO-001`.
- Estado: `VIGENTE` mediante la reconciliacion F9.4 y [ADR-0004](../decisiones/ADR-0004_simplificacion_contractual_hito1.md).
- Decision humana: conservar F8, no restaurar F7 y simplificar F9.
- Fecha de decision: 2026-07-26.
- Alcance de esta nota: contractual y documental; no autoriza codigo, red, DDL, DML, secrets, migrations, backfill ni release.
- Entrada en vigor: al fusionar el PR documental F9.4 que actualiza [Estado del proyecto](../estado_del_proyecto.md), [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), la [macrofase F9](./certificacion_hito1_f9.md) y el [flujo de release](./flujo_release_minimo.md).

La definicion staged [Preflight Free F9.4](./preflight_free_f9_4.md) queda `SUPERSEDED_NON_AUTHORIZABLE`. F9.5 asume un preflight dirigido bajo otra autorizacion; esta nota no concede esa ejecucion.

## Dictamen

F1-F4 y F6 prepararon la ruta `main -> Hito 1`; `H1-CA7P` se completo documentalmente, F7 completo `H1-CA1` y F8 aporto trabajo funcional valido a `H1-CA2P`.

La auditoria fija los siguientes hechos:

- El cierre real de F7 es `5b56aa1`, PR #227.
- F8 contiene trabajo contractual valido de `H1-CA2P`.
- Restaurar completamente a F7 perderia cierres necesarios de schema, ACL y persistencia.
- Despues de F8 se agregaron aproximadamente 9300 lineas de infraestructura de certificacion.
- F9.3 y la definicion staged F9.4 incorporaron attestations, bindings cross-plane, OpenAPI, advisors y un adapter remoto que no corresponden a un criterio contractual de Hito 1.
- Esa complejidad adicional alargo el critical path y mantiene bloqueado el release.

Decision: conservar F8 y las correcciones posteriores validas, no restaurar F7 y reemplazar la ruta F9 bloqueada por una certificacion minima dirigida al contrato.

## Decisiones Fijadas

- Baseline: conservar F8 y las correcciones posteriores validas.
- Fecha contractual: 2026-07-27 a las 09:00 PET.
- H-00: eliminar definitivamente la PII historica solo si el preflight confirma exactamente las tres filas esperadas y existe autorizacion DML separada.
- Plan temporal: retirar `TEMP_PLAN_RECONSTRUCCION_MAIN_HITO1.md` durante F9.4, despues de reconciliar en el vault toda informacion vigente y bajo autorizacion exacta.
- Alcance Hito 1: exclusivamente `H1-CA1`, `H1-CA2P` y `H1-CA7P`.
- Esfuerzo: `EST-001` conserva una estimacion tecnica original de 72h. No constituye una obligacion contractual ni acredita por si sola el saldo real despues del avance registrado; el contrato es precio cerrado por entregable y fecha.
- Evidencia historica: sirve como fuente de reconstruccion, no como evidencia vigente de cumplimiento.

## Alcance Contractual

| Criterio | Alcance exigible | Exclusiones principales |
|---|---|---|
| `H1-CA1` | Schedules FG2/FG3, gates, circuit breakers y controles por ambiente | Redisenar scraping o ampliar pipeline |
| `H1-CA2P` | Schema editorial/calidad, fuentes, faltantes, timestamp manual, patrocinio/leads base y RLS | Deteccion automatica completa, panel admin, UI funcional nueva y entrega de leads en tiempo real; se conserva solo compatibilidad publica minima |
| `H1-CA7P` | Documentacion de campos, RLS, operacion FG2/FG3 y contrato para hitos posteriores | Documentacion historica completa del Sprint |

Ningun gate interno, manifest, attestation, adapter o framework de pruebas crea un criterio contractual adicional.

## Plan Corregido

| Subfase | Alcance minimo | Resultado requerido |
|---|---|---|
| `F9.4` | Reconciliacion contractual local | Simplificar F9, retirar el diseno bloqueado, consolidar CA y eliminar el plan temporal |
| `F9.5` | Preflight Free read-only | Identidad, ledger, compatibilidad DB, H-00, backup y writers; sin adapter nuevo; T01 solo tras PASS y aceptacion local |
| `F9.6` | Remediacion H-00 | Aprobar respaldo H-00 y eliminar exactamente la PII confirmada en Free, sin tocar Pro |
| `F9.7` | Schema/RLS Free | Versionar un descriptor de promocion nuevo ligado al overlay sucesor exacto de cinco migrations y aplicarlo, sin H-00 ni backfill; el descriptor F10/F9.2 historico no autoriza esta ejecucion |
| `F9.8` | Aprobar backfill editorial | Cohorte, predicado, conteos, idempotencia y rollback |
| `F9.9` | Ejecutar backfill Free | Aplicacion separada, segunda ejecucion en cero y smoke FG2/FG3 |
| `F9.10` | Certificacion Free | QA, RLS por rol, PostgREST, canary y PR `desarrollo -> certificacion` |
| `F10.1` | Preflight Pro | Backup, pausa de writers, drift y package exacto |
| `F10.2` | Aplicacion Pro | Mismo package certificado; nunca H-00 |
| `F10.3` | Backfill Pro-local | Sin copiar datos ni UUID desde Free |
| `F10.4` | Validacion productiva | RLS, canary, smoke, advisors y reanudacion aprobada |
| `F10.5` | Release | PR `certificacion -> main`, despliegue y observacion |
| `F11` | Cierre | Evidencia cliente, estado final y limpieza de ramas temporales |

Cada subfase decimal conserva autorizacion exacta, allowlist, stop conditions, revision y evidencia propias. La simplificacion elimina trabajo no contractual, no los controles humanos para red, datos, PII, backups, writers, migrations o releases.

## Simplificacion De F9

F9.4 no implementa el borrador staged. Reconcilia y deja definido para F9.5 un preflight dirigido que inspecciona unicamente:

- El overlay vigente de cinco migrations: las cuatro entradas F8 byte-identicas mas la reconciliacion RLS canary forward-only.
- Columnas, constraints e indices afectados.
- Policies y ACL de `institutions`, `courses`, `leads`, `ratings`, `reviews` e `institution_site_profiles`.
- Owner, `search_path`, modo y grants de las RPC afectadas.
- Conflictos de datos previos a indices y foreign keys.
- Identidad inequivoca del ambiente Free.
- Capacidad de backup y pausa de writers.
- Existencia exacta de las filas H-00 sin mostrar PII.

Quedan fuera del critical path:

- OpenAPI root.
- Advisor bridge criptograficamente ligado.
- Cross-plane binding.
- Nonce one-shot.
- Inventarios globales de `auth` y `storage`.
- Nuevos frameworks de attestations.
- Mas runners sinteticos o maquinas de estado.

Los archivos ya creados pueden conservarse como historia tecnica, pero no deben gobernar el release ni ampliarse. Su retiro fisico, si se decide, queda fuera del critical path y requiere una tarea posterior explicita.

## Secuencia Minima De Certificacion

1. Reconciliar este plan en el Context Graph mediante PR exclusivamente documental.
2. Congelar el candidate F6-F8 y evitar cambios funcionales no ligados a un CA.
3. Ejecutar preflight Free read-only dirigido y emitir solo evidencia sanitizada.
4. Si H-00 coincide exactamente, aprobar/verificar su respaldo y despues ejecutar la eliminacion transaccional aprobada y verificar `3 -> 0`; Pro permanece sin cambios.
5. Con backup y writers pausados, aplicar schema/RLS Free sin mezclar H-00 ni backfill.
6. Aprobar y ejecutar el backfill editorial como operacion DML separada e idempotente.
7. Validar RLS por rol, PostgREST, FG2/FG3, canary, cleanup y QA independiente.
8. Promover `desarrollo -> certificacion` solo con Free certificada.
9. Aplicar en Pro el mismo package, ejecutar backfill Pro-local, smoke y observacion.
10. Promover `certificacion -> main` y cerrar con evidencia aprobada.

## Evidencia Para El Cliente

La entrega final contiene cinco elementos sanitizados:

1. Informe ejecutivo de Hito 1.
2. Matriz `CA -> cambio -> prueba -> ambiente -> resultado`.
3. Anexo CA1 con schedules FG2/FG3, gates y una ejecucion efectiva.
4. Anexo CA2P con diccionario de campos, constraints, indices, RLS y resultados Free/Pro.
5. Acta QA con commit, tree, package, checksums, exclusiones y aprobacion independiente.

No se entregan artifacts privados, identificadores operativos, filas, PII, endpoints, credenciales ni findings explotables.

## Fecha Contractual Y Estado De Release

La fecha contractual es 2026-07-27 a las 09:00 PET. El estado observado al aprobar este plan es `NO-GO` porque Free no esta certificada, H-00 sigue pendiente, schema/backfill no fueron ejecutados bajo el candidate vigente, `certificacion`/`main` no contienen F7-F9 y quedan CI/reviews/aprobaciones humanas.

No se debe afirmar ni garantizar cumplimiento sin evidencia de todos los gates. Si la fecha no puede cumplirse, corresponde entregar un informe de avance y acordar por escrito una reprogramacion; Hito 1 no puede presentarse como completado antes del release productivo y su evidencia.

## Gates De Adopcion

1. El mapeo coincide con [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md), [HITO-001](../hitos/hito_001.md) y [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
2. Estado, tarea, macrofase F9, release minimo, indice y changelog quedan reconciliados sin trabajo operativo.
3. La definicion staged F9.4 queda sustituida y no autorizable.
4. La informacion vigente del plan temporal queda preservada en [Preservacion F9.4](./preservacion_plan_temporal_f9_4.md) antes de retirarlo.
5. La adopcion se completa solo con Context Graph, auditorias, CI, aprobacion humana y merge del PR exclusivamente documental.

El prompt exacto para continuar con la siguiente subfase, despues del merge F9.4, sera:

```text
Ejecuta las tareas pendientes de la Fase F9.5
```

## Referencias

- [Estado del proyecto](../estado_del_proyecto.md)
- [EST-001](../estimaciones/est_001.md)
- [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md)
- [HITO-001](../hitos/hito_001.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- [Certificacion local F8](./certificacion_hito1_f8.md)
- [Macrofase F9 vigente](./certificacion_hito1_f9.md)
- [Flujo de release minimo](./flujo_release_minimo.md)
