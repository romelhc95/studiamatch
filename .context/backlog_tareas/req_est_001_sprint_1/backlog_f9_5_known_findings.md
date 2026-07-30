# Backlog F9.5 - Hallazgos Diferidos

Estado: `DEFERRED_NO_IMPLEMENTATION`.

Este backlog registra hallazgos del cierre documental F9.5 sin crear una subtarea, criterio, candidate, package, autorizacion ni compromiso de implementacion. `TASK-H1-001` sigue siendo la unica tarea de Hito 1 y conserva su estado vivo.

## Items Diferidos

| ID | Hallazgo o trabajo futuro | Limite de esta nota |
|---|---|---|
| `BK-F9.5-01` | Policies y rol canary interno | Requiere definicion y autorizacion propias; no reutiliza artifacts F9.5. |
| `BK-F9.5-02` | Redundancia de `profiles_service_role` | Requiere evaluacion semantica por rol; no autoriza cambiar policies. |
| `BK-F9.5-03` | Inventarios exactos, reducers, HMAC, digests y firewall CI | No autoriza crear infraestructura, attestation ni mecanismo de promocion. |
| `BK-F9.5-04` | `ratings`/`reviews` y sus contadores | Requiere alcance y pruebas propias; no forma parte de H-00. |
| `BK-F9.5-05` | [Arquitectura diferida de leads/email](backlog_seguridad_leads_email.md): email, rate limit, privacidad, outbox, provider, secretos, observabilidad y supply-chain hardening | Requiere evaluacion de seguridad, nuevo ciclo `INTAKE -> EST -> REQ -> TASK` y autorizacion separada. |
| `BK-F9.5-06` | Limpieza fisica de artifacts historicos | Reservada exclusivamente para F11, con aprobacion explicita. |
| `BK-F9.5-07` | [Exec SQL control-plane](backlog_exec_sql_control_plane.md): canal administrativo restringido `public.exec_sql(text)` | Residual aceptado para PR local; requiere sustitucion futura sin autorizar implementacion. |
| `BK-F9.5-08` | Hardening futuro fuera de alcance WP-F9.7-04: cadenas firewall legacy distintas de las tres F9.7, medicion/optimizacion de tiempo CI, escaneo de commit messages, verificacion remota de branch protection y expansion general de patrones de credenciales | `DEFERRED_NO_IMPLEMENTATION`; no crea tarea, criterio, fecha ni compromiso. |

## BK-F9.5-08 - Hardening Futuro Fuera De Alcance WP-F9.7-04

Estado: `DEFERRED_NO_IMPLEMENTATION`.

Riesgo: las superficies legacy y controles operativos externos pueden requerir endurecimiento futuro, pero no forman parte de los invariantes R01-R09 del release gate local F9.7.

Mitigaciones actuales: WP-F9.7-04 deja fail-closed actionlint, EOL changed-only, whitespace ranged, protected closure por objetos Git, hooks pre-commit/pre-push, credential scan de candidate tree, helper firewall con ownership para `F97_FRONTEND_EGRESS`, `FASE097_EGRESS` y `FASE097_AUDIT_EGRESS`, y aggregator bloqueante `security-audit`.

Por que no bloquea Hito 1: no hay ejecucion remota, no hay DDL/DML, no hay deploy, no hay cambio de branch protection remoto y las cadenas legacy distintas de esas tres no son recursos owned por WP-F9.7-04.

Criterio de activacion futura: abrir evaluacion separada si se autoriza hardening general de firewall CI, reduccion de tiempo total de pipelines, scanning de commit metadata, verificacion remota de branch protection o ampliacion transversal de patrones de credenciales.

Comunicacion al cliente: si se activa, comunicarlo como hardening posterior al corte local, no como defecto bloqueante del candidato Hito 1.

## Regla De Tratamiento

Los artifacts de PR #245 y PR #247 permanecen `HISTORICAL_NON_PROMOTABLE`. Ningun item de este backlog permite promoverlos, aplicarlos, borrarlos o incluirlos en el package contractual F6-F8.

Las dependencias minimas de F9.7 y el backfill editorial de F9.8/F9.9 viven en [TASK-H1-001](tarea_001_hito_1.md). La definicion P0 H-00 de F9.6 vive en la [macrofase F9](../../operaciones/certificacion_hito1_f9.md).
