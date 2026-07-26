# Preflight Free Dirigido F9.5

## Estado Y Autoridad

- Subfase: `F9.5`.
- Capability: `REMOTE_READ_FREE_DIRECTED`.
- Estado: `DEFINED_PENDING_REAUTHORIZATION`.
- Target: Free unicamente.
- Autorizacion vigente: ninguna; la autorizacion de remediacion local/documental se consume exclusivamente con el merge de esta reconciliacion y no autoriza acceso remoto.
- Resultado remoto vigente: pendiente de repeticion; el `FREE_PREFLIGHT_FAIL` anterior permanece como evidencia historica y no certifica Free.

Esta nota y [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) definen el siguiente trabajo autorizable. No heredan el adapter, OpenAPI, advisors, bindings, nonce o attestations de la [F9.4 sustituida](./preflight_free_f9_4.md).

## Candidate Cerrado

F9.5 contrasta exclusivamente `F8-HITO1-FUNCTIONAL-20260725` y sus cuatro migrations enumeradas en `db/manifests/fase08_candidate.json`. No edita migrations, manifest, ledger ni codigo.

Objetos dirigidos:

- Tablas: `courses`, `leads`, `email_log`, `ratings`, `reviews`, `institution_site_profiles` y las tablas intermedias afectadas por el package. `email_log` se limita al conteo H-00.
- Catalogos: columnas, constraints, indices, RLS, policies, ACL, owners y RPC afectadas por las cuatro migrations.
- Datos: solo conteos agregados para conflictos previos a constraints/indices y H-00; ninguna fila o valor PII.

## Allowlist De Herramientas

Solo se permiten tools project-scoped del servidor `supabase-free`:

1. `get_project_url`, solo para comprobar que la sesion corresponde al target Free; el valor no se registra.
2. `list_migrations`, para reconciliar nombres/checksums del package.
3. `execute_sql`, solo para sentencias `SELECT` o `WITH ... SELECT` dirigidas a los objetos anteriores y necesarias para catalogos/conteos no cubiertos por las otras tools.

`execute_sql` no puede contener multiples sentencias, comentarios ejecutables, DDL, DML, `CALL`, `DO`, `COPY`, `SET`, `RESET`, `LOCK`, funciones RPC de aplicacion ni inventarios globales. Los predicados deben limitar cada consulta a los objetos dirigidos dentro de `pg_catalog`, `information_schema`, `public.supabase_migrations` y `public`. Cada SQL debe mostrarse en el registro de sesion antes de invocarlo y fallar cerrado si no empieza y termina como lectura unica. No se permiten `get_publishable_keys`, logs, advisors, Edge Functions, branches, `apply_migration` ni tools Pro.

## Checklist Dirigido

1. Verificar sesion Free y package local exacto.
2. Comparar ledger completo con los cuatro nombres/checksums esperados.
3. Inspeccionar solo columnas, constraints e indices afectados.
4. Inspeccionar RLS, policies y ACL por rol en `courses`, `leads`, `ratings`, `reviews` e `institution_site_profiles`; `email_log` se limita al conteo H-00.
5. Inspeccionar owner, modo, `search_path` y grants de RPC modificadas por el package, sin invocarlas ni leer bodies.
6. Obtener solo conteos de conflictos que bloquearian constraints, foreign keys o indices.
7. Confirmar factibilidad de backup y pausa de writers como gates pendientes, sin ejecutar acciones.
8. Evaluar el contrato H-00 DB-only con cutoff exacto `2026-07-19T00:00:00Z`. PostgreSQL deriva la cohorte completa; no se aceptan UUIDs, listas de IDs ni identidad individual. La evidencia contiene solo `leads_total`, `leads_pre_cutoff`, `leads_post_cutoff` y `email_log_total`.
9. Reducir resultados a PASS/FAIL, conteos, nombres de checks y digests sanitizados.

## Contrato H-00 Counts-Only

La evidencia recuperada del backup local en cuarentena confirma que el contrato historico valido era DB-only, no un manifest privado de identidades. Sus artifacts y digests se preservan solo en evidencia privada ignorada; no se copiaron scripts ni SQL al candidate.

- Selector unico aceptado: cohorte completa de `public.leads` evaluada dentro de PostgreSQL con `created_at < '2026-07-19T00:00:00Z'`.
- Limite: `created_at = cutoff` pertenece a post-cutoff. Un timestamp nulo o una particion donde pre-cutoff + post-cutoff no iguale el total falla cerrado.
- Identidad: no existe identidad individual en la evidencia recuperada ni como input autorizado. Se prohiben UUID, lead ID, email, nombre, manifest, lista o evidencia por fila.
- Evidencia autorizada: exactamente cuatro conteos agregados, sin campos adicionales.
- PASS: `leads_total = 3`, `leads_pre_cutoff = 3`, `leads_post_cutoff = 0` y `email_log_total = 0`.
- Cualquier valor, campo, cutoff o shape diferente produce `FREE_PREFLIGHT_FAIL`.
- Un resultado inicial `already_absent`/`0/0/0/0` puede describir un no-op, pero no demuestra la precondicion aprobada y no es PASS F9.5.

DB-only significa que la base deriva la cohorte desde el cutoff sin identidades aportadas por el cliente. F9.5 sigue siendo read-only: no instala RPC, no ejecuta el runner recuperado y no realiza DDL/DML.

## Evidencia Y Stop Conditions

La evidencia privada se mantiene bajo `.context/artifacts/private/f9_5/` y no se versiona. El cierre publico solo puede registrar commit, tree, package, los cuatro conteos H-00, checks y resultado. Nunca publica project URL/ref, SQL response raw, filas, UUIDs, PII, policies completas, DSN, keys o findings explotables.

Se detiene antes de continuar ante target ambiguo, package/checksum distinto, tool no permitida, SQL no read-only, cutoff H-00 distinto, selector que no sea la cohorte completa DB-only, identidad individual, shape distinto de los cuatro conteos autorizados, resultado raw que no pueda sanitizarse, conteos H-00 distintos de `3/3/0/0`, conflicto de datos, backup/writer gate no demostrable o cualquier necesidad de Pro/escritura.

`FREE_PREFLIGHT_PASS` permite revisar localmente T01; no crea por si solo T01, no cambia status, no autoriza F9.6 y no desbloquea schema. `FREE_PREFLIGHT_FAIL` mantiene todo bloqueado y requiere remediacion/otra autorizacion.

## Evidencia Historica Del Intento 2026-07-26

- Autorizacion exacta: recibida.
- Candidate local: package y cuatro checksums de blobs Git conformes con el manifest.
- Stop condition observada entonces: predicado H-00 privado aprobado ausente bajo el contrato previo.
- Resultado: `FREE_PREFLIGHT_FAIL`.
- Acceso Free, tools Supabase y SQL ejecutado: ninguno.
- T01, F9.6, schema, H-00, backup y writers: no autorizados y bloqueados.

La evidencia detallada se conserva exclusivamente en el artifact privado ignorado de F9.5. La reconciliacion local posterior sustituye el requisito de identidades privadas por el contrato DB-only counts-only, sin alterar este resultado historico.

## Remediacion Local 2026-07-26

- Se reconciliaron read-only los artifacts H-00 recuperados del backup local autorizado.
- Se preservaron provenance y digests en un artifact privado nuevo; el FAIL anterior no fue editado.
- Se retiro el requisito de manifest/predicado privado con UUID o identidad individual.
- Se adopto el cutoff exacto y el PASS agregado `3/3/0/0` definidos arriba.
- No se accedio a Free/Pro, no se cargaron secrets y no se ejecuto SQL, DDL, DML, migration, H-00, backup, pausa de writers o backfill.
- La remediacion solo queda vigente despues de CI, review y merge del PR documental.

## Autorizacion Exacta

Solo despues del merge de la remediacion documental puede volver a solicitarse:

```text
Ejecuta las tareas pendientes de la Fase F9.5
```
