# Plan Simplificado De Hito 1

## Estado Y Autoridad

- ID documental: `PLAN-H1-SIMPLIFICADO-001`.
- Estado: `VIGENTE` mediante la reconciliacion F9.4 y [ADR-0004](../decisiones/ADR-0004_simplificacion_contractual_hito1.md).
- Decision humana: conservar F8, no restaurar F7 y simplificar F9.
- Fecha de decision: 2026-07-26.
- Alcance de esta nota: contractual y documental; no autoriza codigo, red, DDL, DML, secrets, migrations, backfill ni release.
- Entrada en vigor: adoptado en F9.4 y reconciliado por los cierres documentales F9.5/F9.6 en [Estado del proyecto](../estado_del_proyecto.md), [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), la [macrofase F9](./certificacion_hito1_f9.md) y el [flujo de release](./flujo_release_minimo.md).

La definicion staged [Preflight Free F9.4](./preflight_free_f9_4.md) queda `SUPERSEDED_NON_AUTHORIZABLE`. F9.5 queda cerrada `COMPLETED_WITH_KNOWN_FINDINGS`. F9.6 queda cerrada `H00_ALREADY_REMEDIATED_NO_DML`; Gate B DELETE es `SUPERSEDED_NON_AUTHORIZABLE` y F9.7 queda activa sin autorizacion.

## Dictamen

F1-F4 y F6 prepararon la ruta `main -> Hito 1`. F6-F8 son la base funcional contractual: F7 implemento `H1-CA1`, F8 aporto el schema local de `H1-CA2P` y `H1-CA7P` se completo documentalmente.

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
- H-00: P0 Free-only separado, obligatorio antes de `FREE_CERTIFIED` pero no criterio contractual. [F9.6](./cierre_h00_f9_6.md) verifico la cohorte con PII directa remediada, conservada como pseudonimizada, y cerro sin DML; el data owner acepta el riesgo residual de vinculabilidad en Free.
- Plan temporal: retirar `TEMP_PLAN_RECONSTRUCCION_MAIN_HITO1.md` durante F9.4, despues de reconciliar en el vault toda informacion vigente y bajo autorizacion exacta.
- Alcance Hito 1: exclusivamente `H1-CA1`, `H1-CA2P` y `H1-CA7P`.
- Esfuerzo: `EST-001` conserva una estimacion tecnica original de 72h. No constituye una obligacion contractual ni acredita por si sola el saldo real despues del avance registrado; el contrato es precio cerrado por entregable y fecha.
- Evidencia historica: sirve como fuente de reconstruccion, no como evidencia vigente de cumplimiento. Los artifacts F9.5 de PR #245 y PR #247 son `HISTORICAL_NON_PROMOTABLE` y no entran al package contractual.

## Alcance Contractual

| Criterio | Estado | Alcance exigible | Pendiente de certificacion |
|---|---|---|---|
| `H1-CA1` | `IMPLEMENTED` | Schedules FG2/FG3, gates, circuit breakers y controles por ambiente | Compatibilidad backend y ejecucion efectiva por ambiente |
| `H1-CA2P` | `IN_PROGRESS` | Schema editorial/calidad, fuentes, faltantes, timestamp manual, inicio, patrocinio/leads base y RLS | Aplicacion Free/Pro, identidad backend de servicio, backfill editorial y pruebas por rol |
| `H1-CA7P` | `COMPLETED` | Documentacion de campos, RLS, operacion FG2/FG3 y contrato para hitos posteriores | Anexo final por ambiente; no crea un criterio adicional |

Ningun gate interno, manifest, attestation, adapter o framework de pruebas crea un criterio contractual adicional.

Para `H1-CA2P` se aceptan `missing_fields` JSONB, `field_sources` JSONB, `manual_updated_at` y `start_date` como equivalencias semanticas. Esta aceptacion no acredita adopcion remota ni evita las pruebas por rol.

## Plan Corregido

| Subfase | Alcance minimo | Resultado requerido |
|---|---|---|
| `F9.4` | Reconciliacion contractual local | Simplificar F9, retirar el diseno bloqueado, consolidar CA y eliminar el plan temporal |
| `F9.5` | Cierre contractual/documental | `COMPLETED_WITH_KNOWN_FINDINGS`; PR #245/#247 y sus artifacts son `HISTORICAL_NON_PROMOTABLE`, sin nueva lectura Free ni package aplicable |
| `F9.6` | P0 H-00 Free-only | `H00_ALREADY_REMEDIATED_NO_DML`; PII directa historicamente remediada y cohorte pseudonimizada, Gate B DELETE sustituido y Pro prohibido |
| `F9.7` | Schema/RLS Free | Candidate implementado; Gate B consumido y origen ACL atestado; predicates/trigger, resguardo/restore, pausa y aplicacion conservan gates separados; sin H-00 ni backfill |
| `F9.8` | Aprobar backfill editorial | Dependencia `H1-CA2P` para evitar catalogo invisible: cohorte, predicado, conteos, idempotencia y rollback |
| `F9.9` | Ejecutar backfill Free | Dependencia `H1-CA2P` separada: aplicacion, segunda ejecucion en cero y smoke FG2/FG3 |
| `F9.10` | Certificacion Free | QA, RLS por rol, PostgREST, canary y PR `desarrollo -> certificacion` |
| `F10.1` | Preflight Pro | Backup, pausa de writers, drift y package exacto |
| `F10.2` | Aplicacion Pro | Mismo package certificado; nunca H-00 |
| `F10.3` | Backfill Pro-local | Sin copiar datos ni UUID desde Free |
| `F10.4` | Validacion productiva | RLS, canary, smoke, advisors y reanudacion aprobada |
| `F10.5` | Release | PR `certificacion -> main`, despliegue y observacion |
| `F11` | Cierre | Evidencia cliente, estado final y limpieza de ramas temporales |

Cada subfase decimal conserva autorizacion exacta, allowlist, stop conditions, revision y evidencia propias. La simplificacion elimina trabajo no contractual, no los controles humanos para red, datos, PII, backups, writers, migrations o releases.

## Simplificacion De F9

F9.4 no implementa el borrador staged. F9.5 se cierra documentalmente sin repetir su preflight: los findings y artifacts de PR #245/#247 permanecen historicos no promocionables. F6-F8 conservan el unico package funcional contractual. F9.6 cierra H-00 con PII directa ya remediada y cohorte pseudonimizada; F9.7 queda definida separadamente para schema/RLS Free.

Quedan fuera del critical path:

- OpenAPI root.
- Advisor bridge criptograficamente ligado.
- Cross-plane binding.
- Nonce one-shot.
- Inventarios globales de `auth` y `storage`.
- Nuevos frameworks de attestations.
- Mas runners sinteticos o maquinas de estado.

Los archivos F9.5 ya creados se conservan como historia tecnica, pero no gobiernan el release, no se amplian y no ingresan a un package contractual. Su retiro fisico queda en F11 y requiere una tarea posterior explicita.

## Secuencia Minima De Certificacion

1. Mantener F6-F8 congelada como base funcional contractual y evitar cambios no ligados a un CA.
2. Conservar F9.5 y sus artifacts como historia `HISTORICAL_NON_PROMOTABLE`, sin repetir la lectura Free ni crear un package sucesor.
3. Conservar `T01_CONDITIONAL_ACCEPTED` como antecedente documental de F9.6; no habilita schema ni nuevas operaciones.
4. Registrar F9.6 `H00_ALREADY_REMEDIATED_NO_DML`: PII directa remediada en la cohorte pseudonimizada, Gate B DELETE sustituido, cero DML y Pro sin acceso.
5. En F9.7, resolver bajo autorizacion propia resguardo/restore, pausa de writers, identidad backend, lecturas publicas, columnas de `leads` y comportamiento semantico RLS antes de aplicar schema/T02.
6. Aprobar y ejecutar el backfill editorial de `H1-CA2P` como operacion DML separada e idempotente para evitar catalogo invisible.
7. Validar RLS por rol, PostgREST, FG2/FG3, canary, cleanup y QA independiente.
8. Promover `desarrollo -> certificacion` solo con Free certificada.
9. Aplicar en Pro el mismo package certificado, ejecutar backfill Pro-local, smoke y observacion; nunca H-00.
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

La fecha contractual es 2026-07-27 a las 09:00 PET. El estado sigue `NO-GO` porque Free no esta certificada: H-00 cerro sin DML, pero schema/backfill no fueron ejecutados bajo el candidate vigente, `certificacion`/`main` no contienen F7-F9 y quedan CI/reviews/aprobaciones humanas.

No se debe afirmar ni garantizar cumplimiento sin evidencia de todos los gates. Si la fecha no puede cumplirse, corresponde entregar un informe de avance y acordar por escrito una reprogramacion; Hito 1 no puede presentarse como completado antes del release productivo y su evidencia.

## Gates De Adopcion

1. El mapeo coincide con [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md), [HITO-001](../hitos/hito_001.md) y [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
2. Estado, tarea, macrofase F9, release minimo, matriz DB, indice y changelog quedan reconciliados sin trabajo operativo.
3. La definicion staged F9.4 y el registro F9.5 quedan historicos y no autorizables; PR #245/#247 quedan `HISTORICAL_NON_PROMOTABLE`.
4. La informacion vigente del plan temporal queda preservada en [Preservacion F9.4](./preservacion_plan_temporal_f9_4.md) antes de retirarlo.
5. La adopcion se completa solo con Context Graph, auditorias, CI, aprobacion humana y merge del PR exclusivamente documental.

El prompt historico que solicito Gate B pre-DDL/read-only de F9.7 despues del merge y validacion post-merge del candidate local fue:

```text
Ejecuta las tareas pendientes de la Fase F9.7

Alcance exclusivo: ejecutar el Gate B pre-DDL y read-only de F9.7 unicamente en Free. Ligar el target Free; congelar package/commit/tree, allowlist positiva y stop conditions; verificar identidad backend de servicio, ausencia de lectura publica en leads/email_log, columnas permitidas de INSERT leads y drift semantico; identificar responsables de resguardo/restore y pausa de writers; y someter ambos mecanismos a aprobaciones humanas separadas. Registrar solo evidencia agregada y detenerse antes de pausar writers o aplicar DDL.

No autoriza Pro, DDL, DML, schema, migrations, pausa/reanudacion de writers, H-00, backfill, F9.8, ramas de certificacion/main ni produccion.
```

La autorizacion fue recibida y consumida por [EVID-F9.7-GATE-B-001](./gate_b_f9_7.md). Gate B termino `FREE_GATE_B_FAIL_STOPPED_READ_ONLY`; este prompt queda como evidencia historica y no puede reutilizarse para una nueva lectura o remediacion.

La [definicion de remediacion](./remediacion_gate_b_f9_7.md) congela package, allowlist logica, rollback, postcondiciones y runbooks sin capacidad remota. La [atestacion ACL posterior](./atestacion_origen_acl_f9_7.md) observo unicamente fuentes reparables por el package; el mismatch de closure y el trigger mantienen fail-closed, mientras predicates no atestados bloquean aplicacion independientemente. No autoriza repetir lecturas ni aplicar schema.

## Referencias

- [Estado del proyecto](../estado_del_proyecto.md)
- [EST-001](../estimaciones/est_001.md)
- [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md)
- [HITO-001](../hitos/hito_001.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- [Certificacion local F8](./certificacion_hito1_f8.md)
- [Macrofase F9 vigente](./certificacion_hito1_f9.md)
- [Flujo de release minimo](./flujo_release_minimo.md)
