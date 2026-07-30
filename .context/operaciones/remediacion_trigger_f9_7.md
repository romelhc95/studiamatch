# Remediacion Local Del Trigger F9.7

## Resultado

`v3_local_predecessor_preserved`.

El draft de atestacion remota de predicates/trigger no fue confirmado ni ejecutado y fue reemplazado por una remediacion local forward-only v3. PR-R reconstruye historicamente offline las variantes revisadas, incorpora el mismatch sanitizado ya conocido y no afirma ningun diagnostico remoto nuevo. No hubo lectura Free/Pro, transporte, DDL/DML remoto, migration remota, backup/restore, control de writers, aplicacion del package, backfill, F9.8, certificacion ni produccion.

## Package Sucesor

- Package: `F9.7-PUBLIC-ACCESS-TRIGGER-RETIREMENT-V3-20260728`.
- Manifest: `db/manifests/fase09_7_free_schema_rls_v3.json`.
- Manifest canonico: `33c3b262dd1754d2fd8e7c8684e50601043654010c41b2d7b97c7386645a180c`.
- Sexta migration: `db/migrations/20260728_fase09_7_notify_new_lead_retirement_v3.sql`.
- Sexta migration SHA-256 LF: `f1fd6e618bd16ff4216f46587ce897756e465ada92ee9bc398335cd9239fe188`.
- Boundaries aceptados: `0`, `3`, `4`, `5` y `6`.
- Targets declarados pero bloqueados: Free y Pro.
- Estado operativo historico PR-R: `application_authorized=false`, T02 `NOT_EXECUTED`, backup `PLANNED`, writers `INVENTORIED`, Free/Pro bloqueados. El corte posterior se registra en [ADR-0005](../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md).

El manifest historico `F9.7-PUBLIC-ACCESS-CLOSURE-20260727`, v2 y la evidencia Gate B/ACL permanecen intactos. V2 es antecedente historico no promocionable; v3 es el unico candidate local. Las cinco migrations previas conservan sus digests LF:

| Entrada | SHA-256 LF |
|---|---|
| `20260724_fase06_g1b_reconciliation.sql` | `d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df` |
| `20260724_fase06_hito1_editorial_contract.sql` | `b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a` |
| `20260725_fase07_g1b_closure.sql` | `9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120` |
| `20260725_fase08_hito1_functional_closure.sql` | `7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527` |
| `20260727_fase09_7_public_access_closure.sql` | `040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b` |

## Semantica Fail-Closed

La sexta migration fija `lock_timeout` y `statement_timeout` antes de cualquier lock, adquiere `ACCESS EXCLUSIVE` solo sobre `public.leads` y aborta antes de cualquier `DROP` salvo que:

1. PostgreSQL sea 17 y el verifier de la quinta entrada pase.
2. Exista una sola rutina `public.notify_new_lead`, sin overloads ni otro tipo de rutina.
3. Metadata, owner, ACL, configuracion, cuerpo, definicion y dependencias coincidan con los fingerprints revisados; CRLF/LF se canoniza antes de comparar sin relajar otros bytes.
4. Exista un solo trigger no interno en `public.leads`, llamado `trg_notify_new_lead`, ligado a esa funcion y con evento, timing, nivel, estado, argumentos, `WHEN`, transition tables y dependencias exactos.
5. No exista colision global por nombre, trigger adicional sobre `leads` ni reutilizacion de la funcion.

Solo despues ejecuta, sin `IF EXISTS` y sin `CASCADE`:

```sql
DROP TRIGGER trg_notify_new_lead ON public.leads;
DROP FUNCTION public.notify_new_lead();
```

El verifier `public.verify_fase09_7_notify_new_lead_retirement()` exige que el contrato de acceso anterior siga vigente y que no exista ninguna rutina `public.notify_new_lead`, trigger no interno en `public.leads` ni trigger global `trg_notify_new_lead`. Una postcondicion externa liga ademas su owner, metadata, ACL, configuracion, cuerpo y dependencias para impedir que el verifier se autoapruebe tras drift.

## Camino Manifest-Only

F9.7 v3 tiene un unico camino local PR-ready: `scripts/maintenance/fase09_7_candidate.py` carga `db/manifests/fase09_7_free_schema_rls_v3.json`, valida seis entradas exactas y emite un package atomico manifest-only. El planner separa clasificacion de ledger, generacion de SQL y append de ledger para que PR-O componga locks/hold/ledger sin modificar migrations. El modo legacy de `scripts/maintenance/db_migrate.py` rechaza mecanicamente `20260727_fase09_7_*` y `20260728_fase09_7_*` para impedir aplicacion por orden lexicografico. El package generado fija timeouts antes del lock de `public.supabase_migrations`, no usa locks explicitos sobre `pg_catalog.pg_proc`, `pg_catalog.pg_trigger` ni `pg_catalog.pg_depend`, y conserva las revalidaciones de prefijo antes de las entradas pendientes.

## Egress Residual

`supabase/functions/send-lead-emails/index.ts` queda tombstoneado en Git: responde `410`, no lee payloads, no deriva secretos, no invoca Resend, no construye `Authorization: Bearer`, no ejecuta `fetch()` y no procesa PII. La sexta migration retira la ruta DB `net.http_post`/`to_jsonb(NEW)` al eliminar el trigger y la funcion revisados. El runbook counts-only de drenaje pg_net queda documentado en [Pg Net queue drain F9.7](./pg_net_queue_drain_f9_7.md), sin ejecucion remota.

Esta nota conserva la identidad tecnica v3. [ADR-0005](../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md) modifica el camino futuro: el frontend soportado ya no conserva captura fail-closed por build, sino eliminacion local de la captura publica; v3 queda como predecessor byte-identico pero insuficiente por permitir `INSERT` publico limitado. El security hold terminal posterior se define en [PLAN-H1-CORTE-SFE-001](./plan_corte_seguridad_funcionalidad_estabilidad_hito1.md).

## PostgreSQL 17

El runner local networkless demuestra:

1. Convergencia desde boundaries `0`, `3`, `4` y `5` al ledger exacto de seis entradas cuando la superficie revisada lo permite.
2. Boundary `6` sin SQL pendiente.
3. Policies, RLS, ACL e inserts publicos funcionales despues del retiro del trigger.
4. Replay del package por ledger como no-op y replay SQL directo de la sexta entrada en fail-closed.
5. Rollback atomico de policy desconocida y ACL heredada desde boundary `4`.
6. Rollback sin drops ante drift de overload, firma incorrecta, trigger extra, trigger homonimo en otra tabla, reutilizacion de funcion, trigger deshabilitado, timing/evento/nivel/args/WHEN/transition table incorrectos, owner, ACL, cuerpo o configuracion desde boundary `5`.
7. Rollback posterior a ambos drops, posterior al verifier y durante append de ledger; funcion, trigger y boundary `5` quedan restaurados.
8. Ledger append-only solo despues de todas las postcondiciones.
9. Colision homonima del verifier rechazada antes de los drops y drift posterior de su cuerpo rechazado en boundary `6`.

## Limites

Esta definicion local no demuestra el snapshot remoto ni autoriza ejecucion. No existe aun gate operacional aprobado; el hold DB ACL sera definido en PR-O y el T02 historico F10 no sera reactivado. Los runbooks siguen `PLANNED` e `INVENTORIED`; restore no es `RESTORE_PROVEN`, writers no estan `HELD` y las decisiones humanas separadas no fueron concedidas. Cualquier aplicacion futura requiere un gate nuevo y no puede reutilizar la autorizacion de esta remediacion.

## Referencias

- [Estado del proyecto](../estado_del_proyecto.md)
- [Definicion Gate B](./remediacion_gate_b_f9_7.md)
- [Atestacion ACL consumida](./atestacion_origen_acl_f9_7.md)
- [Macrofase F9](./certificacion_hito1_f9.md)
- [Matriz DB](./matriz_adopcion_db.md)
- [Pg Net queue drain F9.7](./pg_net_queue_drain_f9_7.md)
- [Flujo de release](./flujo_release_minimo.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
