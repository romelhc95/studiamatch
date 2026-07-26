# Preflight Free Dirigido F9.5

## Estado Y Autoridad

- Subfase: `F9.5`.
- Capability: `REMOTE_READ_FREE_DIRECTED`.
- Estado: `DEFINED_PENDING_AUTHORIZATION`.
- Target: Free unicamente.
- Autorizacion vigente: ninguna.
- Resultado: `FREE_PREFLIGHT_PASS` o `FREE_PREFLIGHT_FAIL`; no certifica Free.

Esta nota y [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) definen el siguiente trabajo autorizable. No heredan el adapter, OpenAPI, advisors, bindings, nonce o attestations de la [F9.4 sustituida](./preflight_free_f9_4.md).

## Candidate Cerrado

F9.5 contrasta exclusivamente `F8-HITO1-FUNCTIONAL-20260725` y sus cuatro migrations enumeradas en `db/manifests/fase08_candidate.json`. No edita migrations, manifest, ledger ni codigo.

Objetos dirigidos:

- Tablas: `courses`, `leads`, `ratings`, `reviews`, `institution_site_profiles` y las tablas intermedias afectadas por el package.
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
4. Inspeccionar RLS, policies y ACL por rol en las cinco tablas dirigidas.
5. Inspeccionar owner, modo, `search_path` y grants de RPC modificadas por el package, sin invocarlas ni leer bodies.
6. Obtener solo conteos de conflictos que bloquearian constraints, foreign keys o indices.
7. Confirmar factibilidad de backup y pausa de writers como gates pendientes, sin ejecutar acciones.
8. Usar el predicado H-00 privado aprobado para obtener solo el conteo; no mostrar ni persistir PII. PASS exige exactamente tres filas esperadas.
9. Reducir resultados a PASS/FAIL, conteos, nombres de checks y digests sanitizados.

## Evidencia Y Stop Conditions

La evidencia privada se mantiene bajo `.context/artifacts/private/f9_5/` y no se versiona. El cierre publico solo puede registrar commit, tree, package, conteos agregados, checks y resultado. Nunca publica project URL/ref, SQL response raw, filas, UUIDs, PII, policies completas, DSN, keys o findings explotables.

Se detiene antes de continuar ante target ambiguo, package/checksum distinto, tool no permitida, SQL no read-only, predicado H-00 privado ausente/no aprobado, resultado raw que no pueda sanitizarse, conteo H-00 distinto de tres, conflicto de datos, backup/writer gate no demostrable o cualquier necesidad de Pro/escritura.

`FREE_PREFLIGHT_PASS` permite revisar localmente T01; no crea por si solo T01, no cambia status, no autoriza F9.6 y no desbloquea schema. `FREE_PREFLIGHT_FAIL` mantiene todo bloqueado y requiere remediacion/otra autorizacion.

## Autorizacion Exacta

Solo despues del merge F9.4 puede solicitarse:

```text
Ejecuta las tareas pendientes de la Fase F9.5
```
