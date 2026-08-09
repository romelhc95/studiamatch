# Seguimiento Detallado De Hito 1

## Proposito Y Autoridad

- ID de seguimiento: `TRACK-H1-001`.
- Tarea canonica: [TASK-H1-001](./tarea_001_hito_1.md).
- Requerimiento: [REQ-EST-001](./_index.md).
- Hito: [HITO-001](../../hitos/hito_001.md).
- Estado de esta nota: `TRACKING_ONLY`.
- Baseline documental al crear esta vista: `desarrollo@fab984049d2e0fa718c0277cf62d29382b81256d`.
- Baseline integrado por PR #248 y reconciliado despues con el cierre documental F9.6; el estado vivo permanece en las fuentes canonicas.

Esta nota recupera la granularidad de seguimiento del backlog historico sin crear subtareas, criterios, alcance ni estado vivo. Las filas `TR-H1-*` son referencias no ejecutables; toda situacion contractual u operativa se consulta exclusivamente en la tarea canonica y en el [Estado del proyecto](../../estado_del_proyecto.md).

## Plazos De Referencia

| Hito temporal | Fecha |
|---|---|
| Inicio historico comprometido | 2026-07-11 |
| Limite historico de construccion | 2026-07-25 |
| Despliegue contractual objetivo | 2026-07-27 09:00 PET |

Las fechas registran el compromiso original. No prueban cumplimiento ni sustituyen una reprogramacion acordada con el cliente.

## Fuentes

- Requerimiento privado `SRC-REQ-001`, sanitizado en [REQ-EST-001](./_index.md).
- [EST-001](../../estimaciones/est_001.md), Paquete 1.
- Backlog historico preservado fuera del workspace actual.
- [Plan simplificado](../../operaciones/plan_simplificado_hito1.md).
- Macrofase F9.
- [Plan de corte seguridad/funcionalidad/estabilidad](../../operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md).
- [Matriz de adopcion DB](../../operaciones/matriz_adopcion_db.md).
- [PR-O F9.7 executor privado](../../operaciones/pr_o_f9_7_successor_private_executor.md), definido pero todavia no implementado tras PR #262.
- [Adenda CA1/CA2 aprobada](./adenda_cliente_001_sanitizada.md), efectiva por
  rebaseline F9.7.
- [Plan CA1-only](../../operaciones/plan_cierre_hito1_ca1_only.md), vigente para
  F9.9 pero no ejecutable sin frase decimal exacta.
- Git, migrations, PR y evidencia enlazada desde las notas operativas.

## Mapa De Criterios Canonicos

| CA | Resumen de consulta | Fuente autorizada | Evidencia final prevista |
|---|---|---|---|
| `H1-CA1` | Orquestacion FG2/FG3, gates y circuit breakers | [TASK-H1-001](./tarea_001_hito_1.md#criterios-y-entregables) | Anexo CA1 por ambiente |
| `H1-CA2P` | Schema editorial/calidad y seguridad base | [TASK-H1-001](./tarea_001_hito_1.md#criterios-y-entregables) | Anexo CA2P por ambiente |
| `H1-CA7P` | Contrato tecnico para hitos posteriores | [TASK-H1-001](./tarea_001_hito_1.md#criterios-y-entregables) | Anexo final de certificacion |

Las equivalencias de `H1-CA2P` se consultan en la [tarea canonica](./tarea_001_hito_1.md#equivalencias-aceptadas-de-h1-ca2p); esta vista no las redefine.

## Matriz De Verificacion Referencial

| Ref | Verificacion | CA | Autoridad del resultado | Gate previsto |
|---|---|---|---|---|
| `CHK-H1-01` | Cadencia FG2/FG3 con gates y secrets por ambiente | `H1-CA1` | Git, workflows y TASK-H1-001 | F9.10/F10 |
| `CHK-H1-02` | Gates y circuit breakers previos al procesamiento | `H1-CA1` | Git y TASK-H1-001 | F9.7/F9.10 |
| `CHK-H1-03` | Campos editoriales, calidad, faltantes, fuentes, actualizacion manual e inicio | `H1-CA2P` | Package F6-F8 y matriz DB | F9.7/F10 |
| `CHK-H1-04` | Patrocinio/leads base sin entrega real-time | `H1-CA2P` | Package F6-F8 y pruebas por rol | F9.7/F10 |
| `CHK-H1-05` | Estado editorial separado de estados ETL | `H1-CA2P` | Verificadores y matriz DB | F9.7/F10 |
| `CHK-H1-06` | Publico sin lectura PII ni escritura administrada | `H1-CA2P` | Pruebas RLS/ACL por rol | F9.7/F9.10 |
| `CHK-H1-07` | Catalogo visible despues del cambio editorial | `H1-CA2P` | Backfill y smoke autorizados | F9.8-F9.10 |
| `CHK-H1-08` | SQL versionado, revisado y aplicado primero en Free | `H1-CA2P` | Git, ledger y postcondiciones | F9.7 |
| `CHK-H1-09` | Contrato consumible por hitos posteriores | `H1-CA7P` | Context Graph y anexos | F9.10/F11 |
| `CHK-H1-10` | Matriz CA -> cambio -> prueba -> ambiente -> resultado | `H1-CA7P` | Evidencia final aprobada | F11 |

Los identificadores `CHK-H1-*` son referencias de verificacion, no criterios de aceptacion nuevos.

## Filas De Seguimiento No Ejecutables

| ID         | Tema observado                                                                 | Relacion                     | Fuente de autoridad                                            | Gate relacionado |
| ---------- | ------------------------------------------------------------------------------ | ---------------------------- | -------------------------------------------------------------- | ---------------- |
| `TR-H1-01` | Workflows FG2/FG3                                                              | `H1-CA1`                     | Git y TASK-H1-001                                              | F7/F9.10         |
| `TR-H1-02` | Modalidad FG3                                                                  | `H1-CA1`, `H1-CA7P`          | Git y TASK-H1-001                                              | F7/F11           |
| `TR-H1-03` | Gates, limites y circuit breakers                                              | `H1-CA1`                     | Git y TASK-H1-001                                              | F7/F9.10         |
| `TR-H1-04` | Campos editoriales/calidad                                                     | `H1-CA2P`                    | Package F6-F8                                                  | F6-F8/F9.7       |
| `TR-H1-05` | Migration contractual                                                          | `H1-CA2P`                    | Package F6-F8 y matriz DB                                      | F6-F8/F9.7       |
| `TR-H1-06` | Patrocinio y leads base; captura publica y email quedan diferidos por ADR-0005 | `H1-CA2P`                    | Package F6-F8 y [BK-F9.5-05](backlog_seguridad_leads_email.md) | F6-F8/F9.7       |
| `TR-H1-07` | RLS, RPC y ACL                                                                 | `H1-CA2P`                    | TASK-H1-001 y matriz DB                                        | F9.7/F9.10       |
| `TR-H1-08` | Contrato para hitos siguientes                                                 | `H1-CA7P`                    | Context Graph                                                  | F11              |
| `TR-H1-09` | H-00 Free-only                                                                 | `P0_PRIVACY`, no CA          | Cierre H-00 F9.6       | F9.6             |
| `TR-H1-10` | Identidad backend de servicio                                                  | Dependencia `H1-CA1/H1-CA2P` | TASK-H1-001                                                    | F9.7             |
| `TR-H1-11` | Schema/RLS contractual en Free                                                 | `H1-CA2P`                    | TASK-H1-001 y matriz DB                                        | F9.7             |
| `TR-H1-12` | Candidate local CA1-only                                                       | `H1-CA1`                     | Macrofase F9                                                   | F9.8             |
| `TR-H1-13` | Candidate selectivo, Certification, canary y QA                                 | `H1-CA1`                     | Macrofase F9                                                   | F9.9             |
| `TR-H1-14` | Certificacion final y readiness F10                                             | `H1-CA1`                     | Macrofase F9                                                   | F9.10            |
| `TR-H1-17` | Hold operativo `USER_PERSONAL_UAT` despues de canary, validaciones y QA         | Hold operativo, no CA        | Macrofase F9 y flujo release                                   | F9.10            |
| `TR-H1-15` | Promocion certificada a Pro                                                    | `H1-CA2P`, release           | Estado y flujo de release                                      | F10              |
| `TR-H1-16` | Evidencia cliente                                                              | `H1-CA7P`                    | TASK-H1-001 y estado                                           | F11              |

## Referencia De Cierre H-00

F9.6 cerro como `H00_ALREADY_REMEDIATED_NO_DML`: EVID-F9.6-H00-001 registra la cohorte con PII directa remediada, conservada como pseudonimizada, Gate B DELETE sustituido y riesgo residual aceptado por el data owner en Free. Esta vista no conserva la evidencia privada y no autoriza F9.7.

## Correspondencia Con El Backlog Historico

| Subtarea historica | Seguimiento vigente |
|---|---|
| ST-01 Auditoria workflows | `TR-H1-01` |
| ST-02 Estrategia FG3 | `TR-H1-02` |
| ST-03 Gates/orquestacion | `TR-H1-03`, `TR-H1-10` |
| ST-04 Campos editoriales/calidad | `TR-H1-04` |
| ST-05 Migration idempotente | `TR-H1-05`, `TR-H1-11` |
| ST-06 Patrocinio/leads | `TR-H1-06` |
| ST-07 RLS/RPC/permisos | `TR-H1-07`, `TR-H1-11`, `TR-H1-14` |
| ST-08 Documentacion | `TR-H1-08`, `TR-H1-16` |
| ST-09 RLS publico/backfill | `TR-H1-11` a `TR-H1-13` |
| ST-10 Anti-spoofing leads | `TR-H1-07`, `TR-H1-14` |
| ST-11 Evidencia reconciliada | `TR-H1-16` |
| ST-12 Orden de gates/limit | `TR-H1-03` |
| Hold personal de usuario | `TR-H1-17` |

Los checks historicos no se heredan como evidencia vigente. Cada estado anterior fue reclasificado contra Git, las migrations actuales y la adopcion real por ambiente.

## Consulta Por Fase

| Fase | Proposito asociado al Hito | Fuente autorizada |
|---|---|---|
| F6-F8 | Base funcional contractual local | Notas operativas F6-F8 y Git |
| F9.1-F9.5 | Historia y cierre contractual/documental | Macrofase F9 y TASK-H1-001 |
| F9.6 | H-00 Free-only | Cierre H-00 F9.6 |
| F9.7-F9.10 | Rebaseline, candidate local CA1-only, Certification/QA, UAT y readiness | Macrofase F9 y [Estado](../../estado_del_proyecto.md) |
| F10 | Pro y produccion | Estado y flujo de release |
| F11 | Cierre contractual | Estado y TASK-H1-001 |

Esta tabla no conserva estados. La fase vigente se lee siempre desde el [Estado del proyecto](../../estado_del_proyecto.md).

## Consulta De Adopcion

La adopcion local, Free y Pro no se duplica en esta vista. Se consulta exclusivamente en la [Matriz de adopcion DB](../../operaciones/matriz_adopcion_db.md), contrastada con ledger y postcondiciones segun el [flujo de release](../../operaciones/flujo_release_minimo.md).

## Evidencia Requerida Para Cliente

1. Informe ejecutivo de Hito 1.
2. Matriz `CA -> cambio -> prueba -> ambiente -> resultado`.
3. Anexo CA1 con schedules FG2/FG3, gates y ejecucion efectiva.
4. Anexo CA2P con diccionario de campos, constraints, indices, RLS y resultados Free/Pro.
5. Acta QA con commit, tree, package, checksums, exclusiones y aprobacion independiente.

No se incluyen artifacts privados, project refs, endpoints, PII, filas, credentials ni hallazgos explotables.

## Desviaciones Y Backlog

- H-00 es un P0 de privacidad separado; no agrega un CA.
- H-00 cerro en F9.6 sin DML; Gate B DELETE es `SUPERSEDED_NON_AUTHORIZABLE` y F9.7 conserva autorizacion separada.
- Los artifacts PR #245/#247 son `HISTORICAL_NON_PROMOTABLE`.
- El corte F9.7 deja v3 byte-identico como predecessor; el hold actual queda `SUPERSEDED_NON_PROMOTABLE` y la ruta futura exige PR-O sucesor con executor privado. PLAN-F9.7-CIERRE-001 organiza seis work packages internos con acceso cero de roles de aplicacion; captura publica `LOCAL_CODE_REMOVED_REMOTE_UNKNOWN`, email egress `LOCAL_TOMBSTONE_REMOTE_UNKNOWN`, T02 `NOT_EXECUTED`, backup `PLANNED`, writers `INVENTORIED` y Free/Pro `UNCHANGED_NOT_ATTESTED`.
- PR #262 quedo mergeado en `desarrollo@c0b6c5efaaaca25f7946e114cc53f63f3a5daa66` / tree `3e5537f01ebf4bec94ada99b274415fc13a2f039`; el PR-O sucesor fue certificado localmente despues, pero queda `SUPERSEDED_FOR_HITO_1` por la rebaseline CA1-only. Free/Pro siguen `UNCHANGED_NOT_ATTESTED`.
- Free es el ambiente DB de desarrollo/certificacion del contrato; `certificacion` como rama/release permanece bloqueada.
- `USER_PERSONAL_UAT` es hold operativo F9.10 de tracking, no criterio, subtarea, subfase ni transicion. Debe ocurrir despues de canary, validaciones tecnicas Certification y QA, y antes de readiness F10; exige candidate commit/tree inmutable y `PASS` personal explicito del usuario.
- PR #248 fija el baseline de cierre F9.5 y definicion F9.6 usado por esta vista; no se modifica aqui.
- Los hallazgos no contractuales se consultan en el [Backlog F9.5](./backlog_f9_5_known_findings.md).
- El detalle de migrations/policies internas no se presenta como criterio cliente.

## Regla De Actualizacion

Esta vista se actualiza solo para mantener referencias, correspondencias y fuentes. No registra transiciones propias: estados, ambientes observados, pruebas, bloqueos y siguientes gates permanecen en la tarea, el estado, la matriz DB o la nota operativa que los gobierna.

Ninguna fila `TR-H1-*` puede autorizar trabajo, completar criterios o sustituir evidencia local/remota.
