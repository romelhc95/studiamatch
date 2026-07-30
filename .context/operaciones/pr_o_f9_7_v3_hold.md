# PR-O F9.7 - Contrato Combinado V3 + Security Hold

| Campo | Valor |
|---|---|
| ID | `PR-O-F9.7-V3-HOLD-001` |
| Estado | `DEFINED_LOCAL_NOT_AUTHORIZED` |
| Subfase | `F9.7` |
| Ambiente permitido futuro | `Free` solamente |
| Ambientes bloqueados | `Pro`, `Production`, `Certification` |
| application_authorized | `false` |
| capabilities | `[]` |
| Base Git | `desarrollo@e2721a0ec4581e422246dfabfa2048297f537025` / tree `0bc0d4b806117fb1b6a2a9fc4d618daa367829ee` |

Esta nota define localmente el contrato sucesor PR-O que combina el package v3 `F9.7-PUBLIC-ACCESS-TRIGGER-RETIREMENT-V3-20260728` y el security hold terminal `F9.7-LEADS-EMAIL-SECURITY-HOLD-20260729`. No implementa transporte, no aplica SQL, no crea runner, no modifica manifests, no cambia `application_authorized=false` y no concede `GO_FOR_FREE`.

## Alcance

PR-O solo puede existir como gate Free-only posterior al merge local de F9.7. Su objetivo futuro es aplicar en Free, bajo una autorizacion separada, el paquete exacto v3 seguido inmediatamente por el hold terminal en una unica unidad atomica. Esta definicion excluye Pro, H-00, backfill, datos operativos, reactivacion de leads/email, canary persistente, deploy Edge/Cloudflare, writers remotos y cualquier aplicacion parcial.

## Artefactos Protegidos

Los siete SQL y los dos manifests siguientes quedan byte-identicos. PR-O los referencia por path y digest canonico existente; no los reescribe ni agrega entradas nuevas:

| Orden | Path | SHA-256 canonico |
|---|---|---|
| 1 | `db/migrations/20260724_fase06_g1b_reconciliation.sql` | `d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df` |
| 2 | `db/migrations/20260724_fase06_hito1_editorial_contract.sql` | `b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a` |
| 3 | `db/migrations/20260725_fase07_g1b_closure.sql` | `9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120` |
| 4 | `db/migrations/20260725_fase08_hito1_functional_closure.sql` | `7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527` |
| 5 | `db/migrations/20260727_fase09_7_public_access_closure.sql` | `040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b` |
| 6 | `db/migrations/20260728_fase09_7_notify_new_lead_retirement_v3.sql` | `f1fd6e618bd16ff4216f46587ce897756e465ada92ee9bc398335cd9239fe188` |
| 7 | `db/migrations/20260729_fase09_7_leads_email_security_hold.sql` | `29082d96cbfd746753324aef0330a7af6f34b0e8bcfa2db0841ac0a8af90134e` |

| Manifest | Uso |
|---|---|
| `db/manifests/fase09_7_free_schema_rls_v3.json` | Predecessor exacto de seis entradas; manifest canonico `33c3b262dd1754d2fd8e7c8684e50601043654010c41b2d7b97c7386645a180c` |
| `db/manifests/fase09_7_leads_email_security_hold.json` | Hold terminal local bloqueado; `application_authorized=false`, `blocked_targets=[free,pro]` |

## Boundaries Permitidos

PR-O acepta exactamente los boundaries de ledger `0`, `3`, `4`, `5`, `6` y `7`:

| Boundary | Estado esperado | Accion futura permitida |
|---|---|---|
| `0` | Ledger vacio del package Hito 1 | Aplicar entradas 1-7 en orden exacto |
| `3` | F6/F7 aplicados, F8+F9.7 pendientes | Aplicar entradas 4-7 en orden exacto |
| `4` | F6-F8 aplicados, F9.7 pendiente | Aplicar entradas 5-7 en orden exacto |
| `5` | Closure F9.7 aplicada, retiro trigger y hold pendientes | Aplicar entradas 6-7 en orden exacto |
| `6` | v3 completo, hold pendiente | Aplicar solo entrada 7 |
| `7` | v3 + hold completos | Replay read-only de postcondiciones; cero DDL/DML |

Cualquier boundary distinto, gap, stem inesperado, colision de version, entrada F9.5, entrada H-00, mutation de ledger, manifest v2, hold sin v3 exacto, v3 standalone o aplicacion parcial debe fallar cerrado antes de abrir una transaccion de escritura.

## Target Binding Privado

El binding Free futuro debe resolverse desde configuracion privada local o gestor de secretos autorizado, nunca desde esta nota. La evidencia publica solo puede registrar `target_binding=BOUND_MATCHED` o `BOUND_MISMATCH_STOPPED`, el nombre del gate, timestamp y hash no reversible del descriptor privado. Queda prohibido registrar project refs, URLs, hostnames, tokens, database passwords, connection strings, anon keys, publishable keys, secret keys o screenshots del dashboard.

El binding debe rechazar cualquier variable generica, alias ambiguo, reuso de Pro, target distinto de Free o configuracion sin owner humano. Si el target privado no coincide en comparacion constant-time contra el fingerprint esperado, PR-O termina `NO_GO_TARGET_BINDING`.

## Snapshot Read-Only

El snapshot previo a una autorizacion futura debe ser read-only, catalog-only y sin filas de negocio. Su alcance maximo son schemas, ledger de migrations, privileges, policies, RLS/FORCE RLS, owners, memberships, views/materialized views, routines/overloads, triggers, rules, publications, constraints y fingerprints de los objetos requeridos por v3 + hold. No lee `leads`, `email_log` ni payloads de `pg_net`; el drenaje `pg_net` sigue counts-only.

El snapshot debe ejecutarse en transaccion `READ ONLY` o mecanismo equivalente y cerrar antes de cualquier decision de aplicacion. Si aparece grant heredado no reparado, policy no administrada, ACL desconocida, owner inesperado, overload, trigger adicional, view/rule/routine indirecta, publication no cubierta, ledger drift o diferencia frente a los digests esperados, el resultado es `NO_GO_SNAPSHOT_DRIFT`.

## Call Budget Y Freshness

Esta definicion tiene call budget remoto `0`. Un gate futuro, si se autoriza explicitamente, debe declarar y respetar como maximo:

| Bloque | Maximo | Tipo | Resultado permitido |
|---|---:|---|---|
| Target binding privado | `1` | lectura local privada, no Git | `BOUND_MATCHED` o stop |
| Snapshot catalog-only Free | `1` | read-only | `SNAPSHOT_READY` o stop |
| Verificacion restore | `1` | evidencia de runbook, no backup nuevo por esta nota | `RESTORE_PROVEN` o stop |
| Pausa/drain writers | `1` | evidencia de runbook, no pausa por esta nota | `HELD` o stop |
| Aplicacion atomica | `1` | unica transaccion futura autorizada | `COMMITTED` o stop |
| Revalidacion post-commit | `1` | read-only | `POSTCONDITIONS_PASS` o stop |

El snapshot y las aprobaciones deben estar dentro de la misma maintenance window. Freshness maxima antes de iniciar la transaccion futura: `30 minutes`; si se excede, se repite solo con nueva autorizacion. La revalidacion post-commit debe iniciar inmediatamente tras commit y dentro de `10 minutes`. Cualquier timeout, red intermitente, respuesta incompleta o ambigua consume el call budget correspondiente y activa no-retry.

## Aprobaciones Pendientes

Los controles operativos quedan definidos pero `PENDING`:

| Control | Estado | Evidencia requerida futura |
|---|---|---|
| Backup | `PENDING` | Backup Free creado fuera de Git, custodia privada, hash no reversible y owner humano |
| Restore | `PENDING` | Restore probado en destino aislado, integridad atestada y recovery owner nombrado |
| Writer pause | `PENDING` | Aprobacion humana separada, FG1/FG2/FG3/manual/external writers pausados |
| Drain | `PENDING` | Jobs en vuelo drenados; `pg_net` counts-only sin payloads |
| Maintenance window | `PENDING` | Ventana temporal aprobada, owner on-call, rollback/recovery preparado |
| Resume writers | `PENDING_F9.10` | No pertenece a PR-O salvo decision humana posterior a postcondiciones |

Ninguno de estos controles se ejecuta por esta definicion. Backup/restore, pausa, drenaje, aplicacion y reanudacion requieren aprobaciones independientes y no transitivas.

## Aplicacion Atomica Futura

Si un gate posterior concede `GO_FOR_FREE`, PR-O debe aplicar todo en una unica transaccion sobre Free:

1. Validar target binding y snapshot freshness antes de abrir escritura.
2. Iniciar una sola transaccion con timeouts fijados.
3. Revalidar boundary permitido y ledger sin cambio concurrente.
4. Aplicar entradas pendientes de v3 y luego el hold terminal, sin invertir ni omitir orden.
5. Ejecutar verificadores y postcondiciones dentro de la transaccion antes del append de ledger final.
6. Append-only ledger solo despues de postcondiciones internas PASS.
7. Commit unico.
8. Revalidacion read-only externa y evidencia sanitizada.

No se permite aplicar v3 sin hold, hold sin v3 exacto, dividir PR-O en varias transacciones, usar `CASCADE` no previsto, editar ledger manualmente, improvisar SQL, aplicar Pro, incluir H-00 o mezclar backfill.

## Politica No-Retry

Ante timeout, desconexion, HTTP 5xx, respuesta truncada, resultado sin ledger verificable o duda sobre si hubo commit, queda prohibido reintentar automaticamente la aplicacion. El estado pasa a `AMBIGUOUS_STOP_NO_RETRY`, los writers permanecen `HELD`, se bloquea toda mutacion adicional y el recovery owner ejecuta solo diagnostico read-only autorizado para clasificar `COMMITTED_VERIFIED`, `ROLLED_BACK_VERIFIED` o `UNKNOWN_REQUIRES_INCIDENT`.

Si el estado sigue ambiguo, las unicas salidas son incidente humano con restore desde backup probado o forward-fix nuevo; ambas requieren autorizacion exacta separada. Nunca se hace segundo apply ciego.

## Rollback Y Recovery Owner

Antes del commit, cualquier falla de guard, checksum, boundary, snapshot, verifier, postcondicion o ledger revierte la transaccion completa. Despues del commit no existe down migration automatica: el recovery owner humano debe decidir entre forward-fix o restore, usando el backup `RESTORE_PROVEN` y evidencia read-only.

El recovery owner futuro debe estar nombrado fuera de Git en el plan privado de ventana. La evidencia publica solo registra `recovery_owner_present=true` y estado de aprobacion; no registra nombres, correos, telefonos ni canales privados.

## Evidencia Sanitizada

La evidencia publica de PR-O solo puede contener:

- Commit/tree del contrato y de la ejecucion futura autorizada.
- Hashes SHA-256 de manifests y SQL ya versionados.
- Boundary inicial y final.
- Estados agregados de target binding, snapshot, backup/restore, writers, maintenance window, apply y postcondiciones.
- Conteos agregados de objetos de catalogo y resultados PASS/FAIL.
- Timestamps, duraciones, versiones de herramientas y `call_budget_used` sin endpoints.
- Verdicts de auditores y `BLOCKING_IN_SCOPE`.

Debe excluir secrets, URLs, project refs, hostnames, connection strings, JWTs, payloads, filas de negocio, PII, UUIDs operativos, SQL completo generado fuera de Git y detalles explotables de grants o policies no reparados.

## Stop Conditions

- `application_authorized` distinto de `false` en esta definicion local.
- Cualquier cambio a los siete SQL o manifests v3/hold existentes.
- Target Free no ligado o binding ambiguo.
- Pro, backfill, H-00 o F9.5 aparece en el package.
- Boundary distinto de `0`, `3`, `4`, `5`, `6` o `7`.
- Snapshot ausente, stale o no read-only.
- Backup/restore distinto de `RESTORE_PROVEN`.
- Writers/drain distinto de `HELD`.
- Maintenance window no aprobada.
- Call budget excedido o respuesta ambigua.
- Grant, policy, view, rule, trigger, routine, publication, owner, membership o ACL drift no cubierto.
- Error de Context Graph, CI, auditoria, review humana o credential scan.

## GO_FOR_FREE Requerido

Esta definicion no emite `GO_FOR_FREE`. Un gate futuro solo podra proponerlo si existe evidencia de:

1. PR-O definido y mergeado en `desarrollo` con CI y auditorias `GO`.
2. Aprobacion humana explicita para Free, separada de esta definicion.
3. Target binding privado `BOUND_MATCHED`.
4. Snapshot catalog-only fresco y read-only `SNAPSHOT_READY`.
5. Boundary permitido y package exacto v3 + hold.
6. Backup `CREATED`, integridad atestada y restore `RESTORE_PROVEN`.
7. Writers `HELD`, drain confirmado y maintenance window aprobada.
8. Recovery owner presente y no publicado.
9. Evidencia sanitizada compatible con este contrato.

## GO_F9.7_COMPLETE Requerido

`GO_F9.7_COMPLETE` solo puede existir despues de un `GO_FOR_FREE` futuro y de una ejecucion Free exitosa. Debe demostrar ledger final boundary `7`, postcondiciones internas y externas PASS, acceso cero de `anon`, `authenticated`, `authenticator` y `service_role` a `leads`/`email_log`, ausencia de rutas indirectas dentro del threat model, PostgREST negativo publico sin bodies, identidad service positiva solo para superficies autorizadas, Edge tombstone sin deploy nuevo, writers aun `HELD`, evidencia sanitizada aprobada, CI/review en verde y decision humana de cierre F9.7.

Completar F9.7 no autoriza backfill, Pro ni produccion; solo habilita la transicion hacia F9.8 conforme a la macrofase F9.

## Referencias

- [Estado del proyecto](../estado_del_proyecto.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- [Plan de corte Hito 1](./plan_corte_seguridad_funcionalidad_estabilidad_hito1.md)
- [Cierre definitivo F9.7](./cierre_definitivo_f9_7.md)
- [Macrofase F9](./certificacion_hito1_f9.md)
- [Remediacion local del trigger F9.7](./remediacion_trigger_f9_7.md)
- [Definicion de remediacion Gate B F9.7](./remediacion_gate_b_f9_7.md)
- [Matriz de adopcion DB](./matriz_adopcion_db.md)
- [Flujo de release minimo](./flujo_release_minimo.md)
