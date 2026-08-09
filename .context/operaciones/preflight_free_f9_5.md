# Registro Historico F9.5

## Estado Y Autoridad

- Subfase: `F9.5`.
- Capability: `HISTORICAL_NON_PROMOTABLE`.
- Estado: `COMPLETED_WITH_KNOWN_FINDINGS`.
- Target actual: ninguno.
- Autorizacion vigente: ninguna; F9.5 no admite otra lectura Free bajo esta nota.
- Resultado: los FAIL y las remediaciones locales permanecen como evidencia historica y no certifican Free/Pro.

Esta nota preserva la historia de F9.5. No define trabajo autorizable, no permite tools ni hereda adapter, OpenAPI, advisors, bindings, nonce o attestations de la [F9.4 sustituida](./preflight_free_f9_4.md). La definicion pendiente de ejecucion es exclusivamente F9.6 en la macrofase F9.

## Artifacts Historicos Preservados

F6-F8 permanecen como base funcional contractual. Las migrations, manifests, reducers, runners, pruebas y CI F9.5 introducidos por PR #245 y PR #247 permanecen byte-identicos como historia `HISTORICAL_NON_PROMOTABLE`. No son candidate, package contractual, replay aplicable ni insumo para F9.7; no se eliminan en este cierre.

Objetos dirigidos:

- Tablas: `institutions`, `courses`, `leads`, `email_log`, `ratings`, `reviews`, `institution_site_profiles` y las tablas intermedias afectadas por el package. `email_log` se limita al conteo H-00.
- Catalogos: columnas, constraints, indices, RLS, policies, ACL, owners y RPC afectadas por las seis migrations.
- Datos: solo conteos agregados para conflictos previos a constraints/indices y H-00; ninguna fila o valor PII.

## Allowlist Historica No Ejecutable

Ninguna tool esta permitida por esta nota. La siguiente allowlist describe solamente el registro historico de F9.5:

1. `get_project_url`, solo para comprobar que la sesion corresponde al target Free; el valor no se registra.
2. `list_migrations`, para reconciliar nombres/checksums del package.
3. `execute_sql`, solo para sentencias `SELECT` o `WITH ... SELECT` dirigidas a los objetos anteriores y necesarias para catalogos/conteos no cubiertos por las otras tools.

`execute_sql` no puede contener multiples sentencias, comentarios ejecutables, DDL, DML, `CALL`, `DO`, `COPY`, `SET`, `RESET`, `LOCK`, funciones RPC de aplicacion ni inventarios globales. Los predicados deben limitar cada consulta a los objetos dirigidos dentro de `pg_catalog`, `information_schema`, `public.supabase_migrations` y `public`. Cada SQL debe mostrarse en el registro de sesion antes de invocarlo y fallar cerrado si no empieza y termina como lectura unica. No se permiten `get_publishable_keys`, logs, advisors, Edge Functions, branches, `apply_migration` ni tools Pro.

## Checklist Historico No Ejecutable

Los pasos siguientes se conservan como antecedente y no habilitan ejecucion:

1. Verificar sesion Free y package local exacto.
2. Proyectar el ledger completo sobre los seis nombres/checksums esperados y aceptar solo un prefijo continuo exacto, preservando historia ajena no colisionante.
3. Inspeccionar solo columnas, constraints e indices afectados.
4. Inspeccionar RLS, policies y ACL por rol en `institutions`, `courses`, `leads`, `ratings`, `reviews` e `institution_site_profiles`; `email_log` se limita al conteo H-00.
5. Inspeccionar owner, modo, `search_path` y grants de RPC modificadas por el package, sin invocarlas ni leer bodies.
6. Obtener solo conteos de conflictos que bloquearian constraints, foreign keys o indices.
7. Confirmar factibilidad de backup y pausa de writers como gates pendientes, sin ejecutar acciones.
8. Evaluar el contrato H-00 DB-only con cutoff exacto `2026-07-19T00:00:00Z`. PostgreSQL deriva la cohorte completa; no se aceptan UUIDs, listas de IDs ni identidad individual. La evidencia contiene solo `leads_total`, `leads_pre_cutoff`, `leads_post_cutoff` y `email_log_total`.
9. Reducir resultados a PASS/FAIL, conteos, nombres de checks y digests sanitizados.

## Contrato H-00 Counts-Only Historico

La evidencia recuperada del backup local en cuarentena confirma que el contrato historico valido era DB-only, no un manifest privado de identidades. Sus artifacts y digests se preservan solo en evidencia privada ignorada; no se copiaron scripts ni SQL al candidate.

- Selector unico aceptado: cohorte completa de `public.leads` evaluada dentro de PostgreSQL con `created_at < '2026-07-19T00:00:00Z'`.
- Limite: `created_at = cutoff` pertenece a post-cutoff. Un timestamp nulo o una particion donde pre-cutoff + post-cutoff no iguale el total falla cerrado.
- Identidad: no existe identidad individual en la evidencia recuperada ni como input autorizado. Se prohiben UUID, lead ID, email, nombre, manifest, lista o evidencia por fila.
- Evidencia autorizada: exactamente cuatro conteos agregados, sin campos adicionales.
- PASS: los cuatro conteos coinciden con el shape agregado aprobado, cuyos valores se conservan solo en evidencia privada.
- Cualquier valor, campo, cutoff o shape diferente produce `FREE_PREFLIGHT_FAIL`.
- Un resultado inicial vacio puede describir un no-op, pero no demuestra la precondicion aprobada y no es PASS F9.5.

DB-only significa que la base deriva la cohorte desde el cutoff sin identidades aportadas por el cliente. Este antecedente no ejecuto F9.6 y conserva solo la definicion entonces prevista; el cierre posterior F9.6 sustituyo la rama de eliminacion al verificar la remediacion historica y cerrar sin DML.

## Registro De Evidencia Y Stop Conditions

La evidencia privada se mantiene fuera de Git. El cierre publico solo puede registrar commit, tree, package, checks y resultado sanitizado, sin valores de conteos H-00. Nunca publica project URL/ref, SQL response raw, filas, UUIDs, PII, policies completas, DSN, keys o findings explotables.

Target ambiguo, PII o identidad individual, tool no permitida o cualquier escritura detienen inmediatamente la ejecucion. Los mismatches tecnicos restantes, incluidos package/checksum, ledger, catalogos, ACL, RPC, conflictos, H-00, backup y writers, se registran de forma sanitizada y no impiden completar los demas checks read-only seguros. La ejecucion emite exactamente un resultado consolidado `FREE_PREFLIGHT_PASS` o `FREE_PREFLIGHT_FAIL`; nunca emite resultados intermedios ni respuestas raw.

Los resultados historicos no cambian estado DB. `T01_CONDITIONAL_ACCEPTED` del cierre documental habilita solo la definicion de F9.6; no autoriza schema, migrations, F9.7 ni ejecucion DML.

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
- Se adopto el cutoff exacto y el shape PASS agregado preservado solo en evidencia privada.
- No se accedio a Free/Pro, no se cargaron secrets y no se ejecuto SQL, DDL, DML, migration, H-00, backup, pausa de writers o backfill.
- La remediacion quedo registrada como antecedente despues de CI, review y merge del PR documental; el cierre actual no la mantiene vigente ni promocionable.

## Segundo Intento Read-Only 2026-07-26

- Binding project-scoped Free: PASS.
- Candidate local y checksums: 4/4 conformes.
- Entradas exactas del package en los ledgers dirigidos: 0/4, sin colision.
- Columnas: 13/13 compatibles.
- Constraints: 11/11 compatibles.
- Indices: 9/9 compatibles.
- RLS habilitado: 5/5 tablas.
- Policies esperadas: 7/7 presentes, 6/7 compatibles.
- Policies publicas adicionales: 3.
- Policies `service_role`: 4/4 compatibles.
- Resultado: `FREE_PREFLIGHT_FAIL`.

El package recrearia la policy esperada incompatible, pero no elimina las tres policies publicas adicionales. Su verificador F8 rechaza ese estado, de modo que el candidate exacto no puede satisfacer su propia postcondicion. La ejecucion se detuvo antes de inspeccionar ACL, RPC, conflictos de datos, H-00, backup o writers. En ese intento no se creo T01; el cierre actual solo deja F9.6 definida y sin autorizacion.

Este resultado permanece historico. La remediacion forward-only local descrita abajo se conserva solo como antecedente; el cierre F9.5 sustituye cualquier repeticion y no autoriza una nueva lectura Free.

## Remediacion Forward-Only Local 2026-07-26

- Migration sucesora: `20260726_fase09_5_rls_canary_reconciliation.sql`, checksum canonico `4959b3f1ad60e2fe3a6e9a23161dd0467cfc549e10c1262ba8a0bb2aaf4c9a01`.
- Manifest overlay: `F9.5-RLS-CANARY-RECONCILIATION-20260726`, cinco entradas, digest canonico completo `27af06a3411f65786d5dfbda19814c24b187f13a055a0fa4733698843f1d3353`, `reconciled_not_certified`, Free/Pro bloqueados.
- Binding del manifest: el objeto JSON completo, claves unicas, status, bloqueos, exclusiones, entradas y checksums estan ligados por digest canonico; una copia promocionable o un package sustituto falla cerrado.
- Inmutabilidad: cuatro migrations F6-F8 y `fase08_candidate.json` conservaron sus hashes LF exactos.
- Guards versionados: policies restrictivas canary exactas y transitivas de `institutions`, `institution_site_profiles` y `courses`.
- Profiles: `profiles_select_public` cubre exactamente `anon` y `authenticated` antes de retirar `profiles_select_authenticated`.
- Verificadores: F8 conserva todos sus checks, exige owner `postgres` y RLS en las seis tablas, roles publicos sin superuser/BYPASS ni membresias privilegiadas, y `service_role` con BYPASSRLS pero sin superuser ni membresias privilegiadas adicionales. Cierra columnas publicas de `institutions`, ACL incluido `PUBLIC`, volatilidad del RPC mutante e inventarios totales de policies; F9.5 encadena la postcondicion y verifica su propia metadata.
- Leads: `anon` y `authenticated` reciben `INSERT` solo sobre `first_name`, `last_name`, `email`, `whatsapp`, `source_page`, `type`, `course_id`, `area_interest`, `budget`, `modality`, `description` e `is_late_enrollment_request`. `id`, `status`, timestamps, `lead_source_type` y cualquier otra columna administrada permanecen denegados.
- Planner: el planner de `db_migrate.py` consulta el ledger PostgreSQL real y valida end-to-end 0/5, 3/5 y 4/5 antes de construir cada suffix aprobado; gaps, checksum drift, replay 5/5 y rollback tambien fallan o convergen segun contrato.
- PostgreSQL 17: una reconstruccion sintetica del baseline observado prueba efectos representativos F8 presentes, ledger vacio y drift RLS historico antes del overlay. Luego valida RLS por rol, membresias privilegiadas negativas, aislamiento canary separado por URL, profile e institucion, rollback atomico, replay semantico y segundo plan en cero.
- CI: el contrato exige PostgreSQL 17 con `--network none` y socket Unix, y comprueba ese modo antes de ejecutar. El proceso de pruebas corre sin secrets ni acceso al socket Docker, sin capabilities y con `no-new-privs`; reglas IPv4/IPv6 cierran OUTPUT y un intento IPv4 externo debe incrementar su contador `REJECT` dedicado.
- Registro historico de promocion: el descriptor F10/F9.2 de cuatro entradas permanece historico e inmutable. La referencia entonces prevista a F9.7 fue sustituida por las dependencias semanticas vigentes; ningun artifact F9.5 autoriza aplicacion alguna.
- Acceso Free/Pro, secrets, SQL remoto, DDL/DML remoto, migrations remotas, H-00, backup, writers, backfill y produccion: ninguno.

La remediacion queda preservada como historia con CI, revision independiente y merge. No crea una attestation, no cambia estado DB y no autoriza F9.6.

## Tercer Intento Read-Only 2026-07-26

- Commit sincronizado: `2e5be1719dffc8a867f4c40e4e8081b51ef56fb7`.
- Binding project-scoped Free: PASS; el identificador no se registro.
- Overlay: `F9.5-RLS-CANARY-RECONCILIATION-20260726`, cinco entradas, package y digest local conformes.
- Ledger dirigido: prefijo `0/5`, sin colision de nombres.
- Columnas: `13/13` compatibles.
- Constraints: `11/11` compatibles.
- Indices: `9/9` compatibles.
- RLS: `6/6` tablas dirigidas habilitadas; seguridad de roles `3/3` compatible.
- Inventario de policies: FAIL; el overlay exacto no converge al inventario cerrado.
- Resultado: `FREE_PREFLIGHT_FAIL`.

Las cinco migrations no retiran todo el drift observado y `verify_fase08_hito1_contract()` rechaza cualquier policy fuera de su inventario cerrado. La ejecucion se detuvo antes de ACL, RPC, conflictos de datos, H-00, backup o writers. En ese intento no se preparo T01. No hubo acceso Pro, DDL, DML, aplicacion de migrations, H-00, backup, pausa de writers ni backfill. El detalle permanece solo en evidencia privada ignorada.

## Remediacion Forward-Only V2 Local 2026-07-26

- Baseline: `desarrollo@1428d310747969af6818ece10cb1a31613f8069a`.
- Inmutabilidad: las cuatro migrations F8, la quinta migration F9.5 y sus manifests historicos permanecen byte-identicos.
- Sexta migration: `20260726_fase09_5_policy_inventory_reconciliation.sql`, checksum canonico `76a7c06bcf1b46a513801d0b1843ac081948a34f552e0371136c6ac2ac097822`.
- Overlay v2: `F9.5-POLICY-INVENTORY-RECONCILIATION-V2-20260726`, seis entradas, digest canonico `575f2e21f747b6445911a050c9951ad93372bcb616282b275838ea21e7cf5795`, `reconciled_not_certified`, Free/Pro bloqueados.
- Inventario: exactamente 21 policies; versiona las tres policies SELECT historicas del runner canary y `profiles_service_role`, con roles, comandos, modo, predicados, owner de tablas, postura del rol y grants cerrados.
- Verificadores: F8 y F9.5 aceptan solo el inventario final de 21; cualquier policy, grant, owner, rol o metadata distinta falla cerrado. La postcondicion v2 encadena ambos contratos y cierra su propia metadata/ACL.
- Planner: acepta exclusivamente prefijos exactos `0/6`, `3/6`, `4/6`, `5/6` y `6/6`; los dos prefijos predecesores incompatibles solo difieren postcondiciones cuando el suffix v2 exacto esta pendiente.
- PostgreSQL 17: reconstruye el baseline observado, prueba convergencia desde todos los prefijos aceptados, replay, rollback atomico desde `0/6` y `5/6`, y rechazo de drift desconocido.
- Preflight: las consultas cerradas devuelven exclusivamente conteos y digests agregados; incluyen roles/memberships, ACL de schema/tablas/columnas/funciones y firmas/grants RPC. El reducer deriva PASS/FAIL contra conteos y digests esperados, liga el target a un digest privado y obtiene los cuatro conteos H-00 en una sola consulta. Los mismatches tecnicos se agregan hasta un unico resultado; target ambiguo, PII, tool prohibida o escritura siguen siendo stop inmediato.
- No hubo acceso Free/Pro, secrets, SQL remoto, DDL/DML remoto, aplicacion de migrations, H-00, backup, writers, backfill ni F9.6.

## Autorizaciones Historicas No Reutilizables

Las autorizaciones F9.5 anteriores estan consumidas. No pueden reutilizarse para leer Free, aplicar artifacts, crear package, habilitar T01 adicional ni definir F9.7. El unico efecto documental de T01 en este cierre es mantener definida F9.6; toda ejecucion posterior requiere su propia autorizacion decimal exacta y no hereda capacidad de F9.5.

## Gate Historico Consumido

El bloque siguiente se conserva textualmente como evidencia del gate historico y para su contrato de regresion. Esta marcado como consumido, no es una autorizacion vigente y no habilita ningun acceso o accion:

```text
Ejecuta las tareas pendientes de la Fase F9.5

HISTORICAL_GATE_CONSUMED
```
