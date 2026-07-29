# ADR-0005 - Corte De Seguridad Funcionalidad Y Estabilidad De Hito 1

| Campo | Valor |
|---|---|
| ID | `ADR-0005` |
| Estado | `ACCEPTED` |
| Decision humana | Congelar el perfil publico de Hito 1 sin captura publica de leads ni email automatico |
| Contexto relacionado | [PLAN-H1-CORTE-SFE-001](../operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md), [PLAN-F9.7-CIERRE-001](../operaciones/cierre_definitivo_f9_7.md), [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [ADR-0004](./ADR-0004_simplificacion_contractual_hito1.md) |

## Contexto

Hito 1 conserva como destino la produccion completa, pero su perfil habilitado no necesita captura publica de PII ni envio automatico de correo para entregar catalogo, busqueda, detalle y comparacion. El candidate v3 de F9.7 retira la ruta de trigger/email, pero no es suficiente como estado final seguro porque conserva `INSERT` publico limitado en `leads`.

## Decision

1. Hito 1 mantiene exclusivamente `H1-CA1`, `H1-CA2P` y `H1-CA7P`.
2. El producto publico conserva catalogo, busqueda, detalle y comparacion.
3. El harvester canonico y el Golden Pipeline conservan funcionalidad completa.
4. Leads y envio automatico de correo quedan fuera del perfil funcional habilitado de Hito 1.
5. La captura publica de PII queda deshabilitada en codigo local.
6. La arquitectura integral de realtime, proveedor de correo y flujo comercial queda `DEFERRED_NO_IMPLEMENTATION`.
7. La reactivacion exige un nuevo ciclo `INTAKE -> EST -> REQ -> TASK` aceptado.
8. La reactivacion no puede ocurrir mediante variable de entorno, grant manual o edicion de ledger.
9. Free y Pro deben contenerse por gates, bindings, backups y aprobaciones independientes.
10. El candidate v3 de PR #257 se conserva byte-identico como predecessor tecnico requerido, pero no puede aplicarse solo porque permite `INSERT` publico limitado.
11. El estado final seguro exige un package terminal separado de security hold.
12. El puente editorial futuro de F9.8/F9.9 permanece limitado a `publication_status`.
13. Esta decision no demuestra deployment, contencion, certificacion ni release remoto.
14. [ADR-0004](./ADR-0004_simplificacion_contractual_hito1.md) conserva su historia y decisiones F9.4-F9.6; esta ADR modifica solo el camino futuro de seguridad de leads/email y preservacion funcional.
15. [ADR-0003](./ADR-0003_taxonomia_macrofases_subfases.md) y la taxonomia decimal permanecen vigentes.
16. `anon`, `authenticated`, `authenticator` y `service_role` quedan sin acceso a `leads` y `email_log`; las filas legacy se preservan bajo autoridad exclusiva del owner `postgres`.
17. El cierre local se ejecuta mediante `WP-F9.7-01` a `WP-F9.7-06`, que son work packages internos de F9.7 y no subfases, subtareas ni criterios nuevos.
18. La publishable key historica retirada fue rotada; la atestacion humana se registra sin valor, identificador ni referencia sensible.
19. `public.exec_sql(text)` se conserva temporalmente como control-plane administrativo restringido a `service_role`; no es ruta data-plane y su sustitucion queda diferida en [BK-F9.5-07](../backlog_tareas/req_est_001_sprint_1/backlog_exec_sql_control_plane.md).

## Consecuencias

- El frontend soportado por el corte no tiene ruta de habilitacion de leads por configuracion.
- La Edge Function historica queda tombstoneada solo en Git; runtime Free y Pro siguen `UNKNOWN_NOT_ATTESTED`.
- El package terminal `F9.7-LEADS-EMAIL-SECURITY-HOLD-20260729` queda local, bloqueado y posterior a v3.
- El verifier terminal detecta drift administrativo ordinario sobre grants, ACL, RLS, policies, views, routines, publications, triggers, rules y membresias; no promete neutralizar a un owner/superuser ni probar SQL dinamico arbitrariamente ofuscado.
- El security hold no conserva lectura de aplicacion sobre las tablas retenidas; cualquier inspeccion futura requiere una operacion owner separada y autorizada.
- `service_role` no conserva acceso data-plane a `leads`/`email_log`; el contrato exacto de `exec_sql(text)` es residual aceptado para el PR local y cualquier executor adicional, overload o ACL distinta bloquea el GO del hold.
- [PLAN-F9.7-CIERRE-001](../operaciones/cierre_definitivo_f9_7.md) congela invariantes, clasificacion de hallazgos, checkpoints y criterios GO diferenciados para evitar ampliacion de alcance durante auditorias.
- F9, F9.7, F10, F11 y `TASK-H1-001` permanecen abiertos.
