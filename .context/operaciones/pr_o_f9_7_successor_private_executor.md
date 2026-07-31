# PR-O F9.7 - Sucesor Executor Privado

| Campo | Valor |
|---|---|
| ID | `PR-O-F9.7-PRIVATE-EXECUTOR-002` |
| Estado | `GO_WP_LOCAL` |
| Subfase | `F9.7` |
| Base Git | Definicion creada desde `desarrollo@ee0e320d55b70dedd72c5a09429ed84a34bf7543` / tree `218bfcc7e99bdef3569fc730bba21228dee53540`; PR #263 verificado en `778267948fc3461987a41dc9184b151c9ff19243` / tree `4e6609926ea6f4a3342cac43e71307fd5cd24aba` |
| PR-O v1 | `SUPERSEDED_NON_PROMOTABLE` |
| Hold actual | `F9.7-LEADS-EMAIL-SECURITY-HOLD-20260729=SUPERSEDED_NON_PROMOTABLE_FOR_FUTURE_ROUTE` |
| application_authorized | `false` |
| capabilities | `[]` |
| Ambiente permitido futuro | DB `Free` solamente, con aprobacion separada |
| Ambientes bloqueados | DB `Pro`, `Production` y `Certification` como rama/release |

Este contrato corrige local y documentalmente PR-O despues del merge `ee0e320d55b70dedd72c5a09429ed84a34bf7543` y queda integrado por PR #262 en `desarrollo@c0b6c5efaaaca25f7946e114cc53f63f3a5daa66`. La implementacion local posterior crea artifacts sinteticos del executor privado y su matriz de pruebas, pero no escribe SQL remoto, no accede a Free/Pro y no concede `GO_FOR_FREE`.

Free es el ambiente DB de desarrollo/certificacion para una aplicacion futura autorizada; `certificacion` como rama/release permanece bloqueada hasta F9.10. Este contrato no cambia ese bloqueo.

## Supersesion

PR-O v1 queda preservado en [PR-O F9.7 v1 superseded](./pr_o_f9_7_v3_hold.md). La ruta futura no puede usar v1 ni el hold actual como paquete terminal promocionable porque el estado final seguro debe eliminar `public.exec_sql(text)` y probar estado Edge remoto. Los artifacts actuales permanecen byte-identicos para trazabilidad y pruebas locales, no como ruta final.

## Executor Privado Requerido

La implementacion local reemplaza cualquier primitive generica `public.exec_sql(text)` del estado final esperado por un executor privado con estas propiedades:

- No vive en `public` ni en ningun schema expuesto por Data API.
- No es invocable por `PUBLIC`, `anon`, `authenticated`, `authenticator` ni por endpoints PostgREST/RPC.
- No acepta SQL arbitrario ni texto SQL ad hoc; solo acepta un descriptor cerrado por digest.
- Es `digest-bound`: candidato, manifests, SQL, runbooks y payloads deben coincidir byte a byte con los SHA-256 aprobados.
- Es `target-bound`: solo opera si el fingerprint privado de Free coincide en comparacion constant-time.
- Es `single-use`: cada aprobacion se consume una vez, queda invalidada por exito, fallo, timeout o respuesta ambigua, y no puede reutilizarse.
- Es `window-bound`: exige ventana, expiracion y owner de recuperacion autorizados fuera de Git.
- Es fail-closed ante drift de schema, ledger, grants, policies, owner, routine, trigger, view, rule, publication, extension o payload.

La evidencia publica solo puede registrar estados agregados, timestamps, digests y verdicts. No registra project refs, URLs, hostnames, tokens, connection strings, secrets, filas, PII, UUIDs operativos ni detalles explotables.

## Digests Vinculantes

### Base Git

| Artifact | SHA |
|---|---|
| Commit base | `ee0e320d55b70dedd72c5a09429ed84a34bf7543` |
| Tree base | `218bfcc7e99bdef3569fc730bba21228dee53540` |

### SQL Protegidos

| Orden | Path | SHA-256 |
|---|---|---|
| 1 | `db/migrations/20260724_fase06_g1b_reconciliation.sql` | `d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df` |
| 2 | `db/migrations/20260724_fase06_hito1_editorial_contract.sql` | `b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a` |
| 3 | `db/migrations/20260725_fase07_g1b_closure.sql` | `9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120` |
| 4 | `db/migrations/20260725_fase08_hito1_functional_closure.sql` | `7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527` |
| 5 | `db/migrations/20260727_fase09_7_public_access_closure.sql` | `040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b` |
| 6 | `db/migrations/20260728_fase09_7_notify_new_lead_retirement_v3.sql` | `f1fd6e618bd16ff4216f46587ce897756e465ada92ee9bc398335cd9239fe188` |
| 7 | `db/migrations/20260729_fase09_7_leads_email_security_hold.sql` | `29082d96cbfd746753324aef0330a7af6f34b0e8bcfa2db0841ac0a8af90134e` |

### Manifests Y Runbooks Actuales

| Path | Estado futuro | SHA-256 |
|---|---|---|
| `db/manifests/fase09_7_free_schema_rls_v3.json` | Predecessor byte-identico | `835b9103f10a8c03b930d4474f9007d99a8715b9bcbc438f144c5bd14d80ea07` |
| `db/manifests/fase09_7_leads_email_security_hold.json` | `SUPERSEDED_NON_PROMOTABLE_FOR_FUTURE_ROUTE` | `f38aa354a4eaddd2a01265529d835843c96994d29d19dcbd7b152259c85c1439` |
| `db/runbooks/fase09_7_backup_restore.json` | `PENDING_NOT_AUTHORIZED` | `254eb387c425675a399d5a2d03411a572ee1bb50061a73158cfb828835e267cf` |
| `db/runbooks/fase09_7_writer_pause.json` | `PENDING_NOT_AUTHORIZED` | `005648e6fd176f03ab7a488319b437d9c1b28bb8f734fc4a878b7ac6a4909444` |
| `db/runbooks/fase09_7_leads_email_security_hold.json` | `SUPERSEDED_NON_PROMOTABLE_FOR_FUTURE_ROUTE` | `7d2c6dca75f7119c649535456ff8ed31ebecffbba43a245c0c2f28139d6a5168` |
| `db/manifests/fase09_7_private_executor.json` | `GO_WP_LOCAL` | `1374903e3a2f696649c44f291425d48c86fef4e382396fa4e436b177c34f3229` |
| `db/runbooks/fase09_7_private_executor.json` | `GO_WP_LOCAL` | `8246675f588afc85f360c9b18dac667069615885a104ab41624da35c0e177cda` |
| `tests/sql/fase09_7_private_executor_boundary7.sql` | `GO_WP_LOCAL_BOUNDARY7_READ_ONLY` | `d54581979ee3d7faff14e90677081f158ab1923badf4ba341c5b7efd8182b781` |

### Payloads Locales Historicos

| Path | Uso | SHA-256 |
|---|---|---|
| `scripts/maintenance/fase09_7_candidate.py` | Generator v3 historico | `f872aa796537b215fd717ed76e0d0a4129c96e5bd201f56a4b1874993b0dc17f` |
| `scripts/maintenance/fase09_7_leads_email_security_hold_candidate.py` | Generator hold actual no promocionable | `f53c321cff2018d7a11208ad36cfc8c97caad10b11d7c5e15b7d7b20a4ec1bc3` |
| `tests/sql/fase09_7_leads_email_security_hold_test.sql` | Test SQL hold actual | `1143bf0214896eb9e73c32a698df778cb74287621c90a0235fde018d1d28b96c` |
| `tests/sql/run_fase09_7_leads_email_security_hold_postgres.sh` | Runner local hold actual | `7030d0eb5ae26ae6c74c541500735389c3498ed119c9aa0d253291394281aad6` |
| `tests/test_fase09_7_leads_email_security_hold.py` | Pytest hold actual | `7fbdc3703ab31d57af5b247d2cec3a67c5cbf0c81ba891a60f22788cb0fc2764` |
| `scripts/maintenance/fase09_7_private_executor.py` | Planner/validador sucesor local | `384625282393ab8f851d2332287534dd48e260c24822b113baeaf9aa4a81a0e6` |
| `tests/test_fase09_7_private_executor.py` | Pytest sucesor local | `51a505534df82d46a93db4174f911ccb86c68653e831321bb6e275ef154a080a` |
| `PR-O-F9.7-PRIVATE-EXECUTOR-002-PAYLOAD` | Payload sintetico manifest-bound | `f86c3062ca1d394e809e0e2e85d5173754779dcd9e6d66fe8f0d69f46afdba49` |

El payload sucesor tiene digest propio y no reutiliza los payloads del hold actual como finales.

## Secuencia Atomica Futura

Si un ciclo posterior llega a una aplicacion Free autorizada, el unico orden valido dentro de una transaccion es:

1. `pending v3`.
2. `postcondiciones v3`.
3. `ledger v3`.
4. `hold sucesor`.
5. `verificador terminal`.
6. `ledger hold`.
7. `verificacion final`.
8. `commit unico`.

No se permite `ledger hold` antes del verificador terminal, v3 sin hold sucesor, hold sucesor sin v3 exacto, aplicar el hold actual, dividir transacciones, usar `CASCADE` no previsto, editar ledger manualmente, improvisar SQL, reintentar a ciegas ni mezclar H-00, backfill, Pro o produccion.

## Boundary 7

Boundary `7` significa v3 y hold sucesor completos en ledger y postcondiciones. Su replay es estrictamente `READ ONLY`:

- Transaccion `READ ONLY` o mecanismo equivalente.
- Cero DDL, DML, RPC mutante, `LOCK`, `SELECT FOR UPDATE`, advisory locks, waits de escritura o cambios de settings persistentes.
- Solo catalogo, ledgers, privileges, policies, RLS/FORCE RLS, owners, memberships, views, routines, triggers, rules, publications, constraints, Edge-state evidence y fingerprints.
- No lee `leads`, `email_log` ni payloads de `pg_net`.
- Cualquier necesidad de lock o mutacion cambia el resultado a `NO_GO_BOUNDARY7_NOT_READ_ONLY`.

## Estado Edge Requerido

Antes de cerrar F9.7, la superficie Edge historica debe demostrar exactamente uno de estos estados con evidencia sanitizada:

| Estado | Condicion |
|---|---|
| `REMOTE_ABSENT` | La funcion remota no existe para el target Free ligado. |
| `REMOTE_TOMBSTONE_410` | La funcion remota responde semanticamente como tombstone 410 sin PII ni egress de email. |
| `DISABLEMENT_SEPARATE_AUTHORIZED` | Una deshabilitacion remota fue autorizada, ejecutada y auditada en un ciclo separado. |

El tombstone Git por si solo no satisface el cierre.

## Separacion De Autorizaciones

Estas autorizaciones son distintas, no transitivas y single-use:

| Autorizacion | Estado actual | Alcance maximo |
|---|---|---|
| `IMPLEMENTACION_LOCAL_PR_O_SUCCESSOR` | `CONSUMED_GO_WP_LOCAL` | Crear executor privado, hold sucesor, payloads y pruebas locales sin red. |
| `CERTIFICACION_LOCAL_PR_O_SUCCESSOR` | `PENDING_NEXT` | Validar digest binding, target binding sintetico, boundary y no-Data-API en local. |
| `PREFLIGHT_READ_ONLY_FREE` | `PENDING` | Snapshot catalog-only Free sin filas ni payloads. |
| `BACKUP_RESTORE_FREE` | `PENDING` | Backup privado y restore probado fuera de Git. |
| `WRITER_PAUSE_DRAIN_FREE` | `PENDING` | Pausa/drain de writers y `pg_net` counts-only. |
| `GO_FOR_FREE` | `PENDING` | Autorizar aplicacion Free del sucesor exacto. |
| `FINAL_APPLY_FREE` | `PENDING` | Ejecutar transaccion unica y revalidacion final. |

Cada approval debe estar ligado a target fingerprint, boundary inicial, candidate commit/tree, digests de payloads, ventana, expiracion, recovery owner y nonce privado. Al expirar, fallar, consumirse o encontrar respuesta ambigua, queda invalidado.

## Stop Conditions

- Intento de usar `PR-O-F9.7-V3-HOLD-001` como ruta aplicable.
- Intento de usar el hold actual como hold terminal final.
- `public.exec_sql(text)` presente en el estado final esperado.
- Executor en schema expuesto por Data API o con grants a roles de aplicacion.
- Target fingerprint ausente, ambiguo, no Free o no ligado al approval single-use.
- Boundary distinto de `0`, `3`, `4`, `5`, `6` o `7`.
- Boundary `7` que requiera locks de escritura o mutaciones.
- Edge sin `REMOTE_ABSENT`, `REMOTE_TOMBSTONE_410` o `DISABLEMENT_SEPARATE_AUTHORIZED` antes del cierre.
- Drift de digests en SQL, manifests, runbooks, commit/tree o payloads.
- Backup/restore, writers/drain, maintenance window o recovery owner no aprobados cuando correspondan.
- Respuesta ambigua, timeout o duda de commit; no retry automatico.
- Supabase Free/Pro, backup, restore, writers, Edge, Cloudflare, backfill, Pro o produccion invocados durante esta definicion documental.

## Siguiente Accion Canonica

La siguiente accion no es `GO_FOR_FREE`. La siguiente accion es `CERTIFICACION_LOCAL_PR_O_SUCCESSOR`, bajo autorizacion separada, sin red remota y con pruebas locales que demuestren executor privado no expuesto por Data API, eliminacion de `public.exec_sql(text)` del estado final esperado, digests actuales y approvals single-use.

## Referencias

- [PR-O F9.7 v1 superseded](./pr_o_f9_7_v3_hold.md)
- [Estado del proyecto](../estado_del_proyecto.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- [Plan de corte Hito 1](./plan_corte_seguridad_funcionalidad_estabilidad_hito1.md)
- [Cierre definitivo F9.7](./cierre_definitivo_f9_7.md)
- [Macrofase F9](./certificacion_hito1_f9.md)
- [Matriz de adopcion DB](./matriz_adopcion_db.md)
- [Sistema DB Supabase](../sistema_db_supabase.md)
- [Flujo de release minimo](./flujo_release_minimo.md)
