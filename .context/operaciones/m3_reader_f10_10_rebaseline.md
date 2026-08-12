# F10.10 M3 Reader - Rebaseline De Preparacion Local

| Campo | Valor |
|---|---|
| Subfase | `F10.10` |
| Estado | `M3_PUBLIC_DB_ACL_DIAGNOSTIC_V3_PAYLOAD_PENDING_HUMAN_APPROVAL` |
| Autoridad de ejecucion recibida | `Ejecuta las tareas pendientes de la Fase F10.10` |
| Alcance consumido | Preparacion local y documentacion del candidate `studiamatch_m3_reader` |
| Acceso remoto / DDL remoto | `Una llamada v1 y una v2, ambas fallidas con rollback / NO capacidad vigente` |
| Gates consumidos | Preflight una vez PASS; DDL v1 y v2 una vez cada una FAIL+rollback |
| Autoriza M4, F10.9/G4, schedules o F11.1 | `NO` |
| Query-set content digest `query-set-v1` candidate v2 | `sha256:d3bc8fddf7d0d8b39497e4f184c7669bec3cbc4537dde7aeb3757d4afe53957a` |
| Package rebaselined offline, no identity v3 | `sha256:53dfeb7e67e7699d7314dd174e923418e49a5230acd5ae858697c410d95875e3` |
| Compensacion candidate | `sha256:609a5b22202021de44ff1fa484ddb1a35fbb7bb15f495bc9afe304542d288fe0` |
| Proyeccion local `apply_migration` v2 ligada al provisioner aprobado | `sha256:a13e0e814185f756d612d8b092561a5baa71442a2cff2e83db081eb32ddd2f3f` |

Esta nota es la autoridad enfocada del rebaseline M3 reader y sustituye las
partes operativas del scope M3 anterior que asumian
una identidad SQL preexistente y un unico gate de lectura. La
[evidencia post-merge M3](./m3_f10_10_post_merge_evidence_2026_08_11.md) de PR
#350 permanece inmutable como antecedente del collector v1 promovido; no acredita
el candidate v2, no registra ejecucion remota y no consume aprobaciones.

## Decision

La preparacion local se rebaselina sobre un collector v2 exclusivamente
`FREE_DB` y un paquete Free-only
para una identidad efimera dedicada llamada exactamente
`studiamatch_m3_reader`. PR #353 promovio el candidate completo mediante merge
protegido `2cf614a4a44ffabc5e06ba08dc20707807db274f` / tree
`7b9e9cfd9d74749416cfab098da116ecbe239c04`; CI post-merge termino PASS. La
[evidencia post-merge](./m3_reader_f10_10_post_merge_evidence_2026_08_11.md)
acredita el candidate, pero no autoriza una operacion remota ni consume gates.

La autorizacion decimal recibida permite esta preparacion local. No permite
Supabase, red remota, DDL remoto, manejo de passwords, activacion privada ni el
consumo de `APPROVE_M3_FREE_READONLY`. En esta preparacion no ocurrio acceso
remoto, conexion Supabase, DDL/DML remoto, cambio de password ni consumo de gate.

## Contrato Del Collector V2

El collector v2 separa dos evidencias que no deben confundirse:

1. **Binding aprobado offline**: se calcula sin red desde alias, project-ref
   fingerprint, host API/SQL normalizado, puerto, database/user fingerprints,
   `sslmode=verify-full`, digest del CA aprobado y expiracion privada del rol.
2. **Atestacion observada en la misma conexion**: despues de conectar, la API
   publica libpq observa host, puerto, database, user, TLS activo, protocolo,
   cipher, library y `server_version_num` de esa misma conexion PostgreSQL.

El binding offline no incorpora valores negociados esperados de protocolo,
cipher, library TLS ni version exacta del servidor. Se eliminan como entradas de
entorno los valores TLS negociados exactos. La atestacion observada sigue siendo
obligatoria y fail-closed: exige TLS activo, `verify-full`, protocolo permitido y
coincidencia de host/puerto/database/user con el binding; publica solo su digest
sanitizado. No se usa un probe TLS separado ni se convierte una observacion
negociada en configuracion preaprobada ficticia.

`q0-only` es un modo y gate independiente. Solo atesta transporte, identidad,
expiracion, read-only y privilegios; exige `BYPASSRLS=true`, no ejecuta Q1-Q4, no
lee filas de `courses` y no concede la lectura full-population. `collect` exige
mecanicamente un manifest predecessor canonical v2 `q0-only=PASS`, cuyo digest,
query-set y target binding deben coincidir con runtime.

## Rol Free Dedicado

El paquete local propone exactamente este estado inicial:

- rol efimero `studiamatch_m3_reader` con `NOLOGIN`, `PASSWORD NULL`,
  `VALID UNTIL NULL`, `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`,
  `NOREPLICATION`, `NOINHERIT`, connection limit 1 y `BYPASSRLS` aceptado para
  visibilidad full-population bajo RLS;
- defaults por rol/database: `default_transaction_read_only=on`,
  `search_path=pg_catalog` y `client_encoding=UTF8`;
- `CONNECT` solo al database aprobado y `USAGE` solo sobre `public`;
- `SELECT` de columna exactamente sobre `public.courses.id`,
  `public.courses.is_active`, `public.courses.syllabus` y
  `public.courses.objectives`;
- cero `SELECT` sobre otras columnas o relaciones, cero privilegio mutante,
  cero ownership, cero edges `member=reader`, exactamente un edge
  `roleid=reader` para el provisioner aprobado, y cero acceso efectivo a rutinas
  no-sistema `SECURITY DEFINER`.

`BYPASSRLS=true` es obligatorio en todos los estados admitidos y no concede
escritura. Se acepta unicamente junto con el cierre de
privilegios anterior, transacciones `REPEATABLE READ READ ONLY`, Q0 separado y
caducidad finita. Cualquier grant heredado, `PUBLIC` amplio, colision de rol,
edge distinto del provisioner permitido, ownership, acceso a otra
relacion/columna, capacidad mutante o `SECURITY DEFINER` termina STOP.

El contrato de provision, si una nueva identidad y aprobacion separadas se
promueven despues del rebaseline requerido, debe dejar `NOLOGIN`, `PASSWORD NULL`
y `rolvaliduntil=NULL`. Solo durante una activacion privada bajo el gate Q0 se fija `LOGIN` y un `VALID
UNTIL` exacto, finito y futuro igual a `F10_10_M3_VALID_UNTIL`. El password
se establece exclusivamente mediante `psql` interactivo con `\password
studiamatch_m3_reader`; nunca mediante SQL literal, argumento CLI, variable
versionada, log, artifact, transcript o esta documentacion. La activacion y la
lectura deben terminar antes de la expiracion.

El edge administrado PostgreSQL 17 admite exactamente al provisioner aprobado por
`F10_10_M3_PROVISIONER` como member/admin del reader: `roleid=reader`,
`member=provisioner`, `admin=true/inherit=false/set=false`. El reader es member de
cero roles (`member=reader`). Cualquier otro edge termina STOP. El fingerprint
del provisioner forma parte del binding offline `target-binding-v2`.

## Package Y Aislamiento Pro

El package de provision vive bajo:

```text
db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql
```

La compensacion vive separada bajo:

```text
db/rollbacks/20260811_fase10_10_m3_free_reader_compensating.sql
```

`scripts/maintenance/db_migrate.py` descubre mecanicamente solo
`db/migrations/*.sql`; por ubicacion, el package Free-only queda fuera de ese glob
Pro. Ademas, DB Sync Pro excluye de su deteccion automatica Pro-relevant el patron
exacto `db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql` y el path exacto de compensacion anterior. No
deben copiarse, enlazarse ni reflejarse bajo `db/migrations/`. Cualquier deteccion
o aplicacion por la ruta Pro termina STOP.

La compensacion acepta el estado inicial inactivo o el estado activo con
LOGIN/password/expiracion finita futura o expirada. Es deliberadamente
fail-closed y multi-etapa:
primero pone el rol
en cuarentena con `NOLOGIN NOBYPASSRLS PASSWORD NULL`; despues termina sesiones
bajo el gate de teardown y revoca los grants/settings creados por el package;
finalmente lo elimina solo si no hay ownership ni dependencias bloqueantes. Grants
o dependencias ajenos al package pueden permanecer y bloquear `DROP ROLE`. Si el
drop no es seguro, la identidad queda cuarentenada con grants/settings del package
revocados, mientras grants/dependencias ajenos pueden persistir; nunca se reactiva
por rollback.

## Validacion Local Requerida

El candidate requiere PostgreSQL 17 local, aislado y networkless. La validacion
debe cubrir provision, estado inicial sin password/expiracion, visibilidad RLS por
`BYPASSRLS`, SELECT exacto de cuatro columnas, rechazo de otras columnas,
relaciones, DML y `SECURITY DEFINER`, colisiones/grants amplios fail-closed, y
compensacion cuarentena -> revocacion -> drop. Debe demostrar tambien que el
package Free-only no entra al glob `db/migrations/*.sql` de Pro.

CI descarga la imagen PostgreSQL 17 pinneada antes de activar el firewall de
egress; despues inicia la prueba con `--pull never --network none`. Un pull tardio
o cualquier red habilitada invalida la prueba.

PR #353 y las validaciones post-merge completaron PostgreSQL 17 networkless,
collector v2, boundary, credential scan y contratos del repositorio. Ese PASS
habilita unicamente revisar payloads futuros; no concede Free, DDL ni passwords.
La preparacion offline de `target-binding-digest` debe omitir
`F10_10_M3_PASSWORD`; solo `q0-only` y `collect`, bajo sus gates posteriores,
pueden requerirla y cualquier ausencia detiene antes de driver o conexion.

## Proyeccion DDL Para Apply Migration

La investigacion read-only del cliente MCP oficial confirmo que `apply_migration`
envia `name` y `query` a `POST /v1/projects/{ref}/database/migrations`. La
documentacion publica declara rollback si la migration falla; la implementacion
self-hosted publica construye `BEGIN; <query>; INSERT ledger; COMMIT;`.

El package canonico conserva `BEGIN/COMMIT` porque tambien debe ser atomico con
`psql`. Enviarlo sin transformar cerraria anticipadamente el envelope externo:
PostgreSQL 17 emite warning ante el `BEGIN` anidado y el `COMMIT` interno persiste
DDL antes del ledger. Un probe local reprodujo ese split. El package sin proyectar
queda prohibido para `apply_migration`.

`scripts/maintenance/f10_10_m3_apply_projection.py` implementa una proyeccion
local, determinista y sin red: valida el digest LF exacto, elimina solo los
statements externos `BEGIN;`/`COMMIT;`, rechaza otros controles transaccionales
top-level, liga `current_user=session_user` al fingerprint aprobado sin serializar
el nombre privado y produce artifacts `0600` bajo `local/f10_10/m3/`.

La remediacion v2 cambia package y `query-set-v1` para aceptar la nullability
canonica de `is_active`. Para el fingerprint del provisioner aprobado, la
proyeccion candidate v2 queda ligada a
`sha256:a13e0e814185f756d612d8b092561a5baa71442a2cff2e83db081eb32ddd2f3f`;
otro provisioner produce necesariamente otro digest y termina STOP.
PostgreSQL 17 local acredito rollback del reader ante fallo de ledger o executor
distinto, y commit conjunto de DDL+ledger en success path. No hubo Free ni gate.

El payload preflight anterior y su ventana terminada son evidencia historica. El
[payload DDL Free](./m3_reader_f10_10_ddl_free_payload_2026_08_12.json) usa el
merge/tree post-PR #361, binding offline renovado y la identidad unica
`fase10_10_m3_free_reader_free_ddl_v1`. Su unica ejecucion termino rollback por
`STOP_COURSES_COLUMN_CONTRACT_DRIFT`; v1 queda superseded y no reutilizable.
PR #363 fusiono la remediacion de `is_active` nullable. Sobre su merge protegido
`bc268f119e04791bc17439aaa096e9e06c8b5e8b` / tree
`fd08e8cee5cc7cc6d031fd59fbb5ed97e9f9ad68`, la preparacion offline genero un
binding fresco y la proyeccion privada v2. PR #364 promovio el payload sanitizado
y la unica llamada `fase10_10_m3_free_reader_free_ddl_v2` termino
`STOP_BROAD_PUBLIC_DATABASE_PRIVILEGES` antes de `CREATE ROLE`, con rollback,
cero retry y cero fallback. La identidad y el gate v2 quedan consumidos y no son
reutilizables.

La [atestacion sanitizada de rotacion](./m3_reader_f10_10_rotation_attestation_2026_08_11.md)
confirma que la contrasena SQL canary anterior fue rotada y revocada fuera de
banda. No se registro ni inspecciono su valor. La identidad anterior permanece
prohibida en provision, Q0, collect, teardown y cualquier otro ambiente.

## Ledger De Gates

Ledger vigente:

| Gate | Capacidad maxima propuesta | Estado |
|---|---|---|
| `APPROVE_F10_10_M3_READER_PREFLIGHT_FREE` | Preflight sanitizado del target y package; sin DDL ni password | `CONSUMED_ONCE_PASS` |
| `APPROVE_F10_10_M3_READER_DDL_FREE` | Provision Free-only del rol `NOLOGIN/PASSWORD NULL/rolvaliduntil NULL` mediante el payload DDL promovido | `CONSUMED_ONCE_FAILED_ROLLBACK_SUPERSEDED` |
| `APPROVE_F10_10_M3_READER_DDL_FREE_V2` | Unica llamada Free-only v2 ya consumida; cero retry/fallback | `CONSUMED_ONCE_FAILED_ROLLBACK` |
| `APPROVE_F10_10_M3_PUBLIC_DB_ACL_DIAGNOSTIC_FREE` | Una lectura agregada de `pg_catalog.pg_database`; counts/flags-only | `CONSUMED_ONCE_STOP_CANDIDATE_BINDING_PENDING_ZERO_REMOTE_CALLS` |
| `APPROVE_F10_10_M3_PUBLIC_DB_ACL_DIAGNOSTIC_FREE_V2` | Envelope sin atestacion PostgreSQL 17 | `SUPERSEDED_NOT_EXECUTED` |
| `APPROVE_F10_10_M3_PUBLIC_DB_ACL_DIAGNOSTIC_FREE_V3` | Envelope con atestacion PostgreSQL 17, una llamada Free counts/flags-only | `PENDING_HUMAN_APPROVAL_NOT_EXECUTED` |
| `APPROVE_F10_10_M3_READER_Q0_FREE` | Activacion privada finita y ejecucion `q0-only`; sin Q1-Q4 | `PROPOSED_NOT_EXECUTABLE` |
| `APPROVE_M3_FREE_READONLY` | Lectura completa Q1-Q4 solo tras Q0 PASS | `EXISTING_NOT_CONSUMED` |
| `APPROVE_F10_10_M3_READER_TEARDOWN_FREE` | Cuarentena, revocacion y drop fail-closed | `PROPOSED_NOT_EXECUTABLE` |

El gate preflight fue aprobado/consumido una vez y termino PASS. Los gates DDL v1
y v2 fueron consumidos una vez cada uno y terminaron rollback; sus identidades no
son reutilizables. Q0, lectura y teardown siguen no consumidos y no ejecutables.
Cada aprobacion
humana posterior debe citar su payload exacto:
candidate SHA/tree, digests de package/compensacion/query-set, target binding
offline, clase de executor/reader, ventana, `VALID UNTIL`, artifacts privados,
stop conditions y plan de teardown. Ningun gate concede el siguiente y la frase
decimal F10.10 no los consume.

El [payload preflight](./m3_reader_f10_10_preflight_payload_2026_08_11.json) ya
congela esos campos en forma sanitizada. Su digest canonico es
`sha256:68fd845808dbe694984ffbdd087b44e19754b4c76c14da862d74dad232971613`.
La [ejecucion local passwordless](./m3_reader_f10_10_preflight_evidence_2026_08_11.md)
consumio exclusivamente el gate preflight y termino PASS. DDL v1 y v2 terminaron
rollback; Q0, lectura y teardown permanecen no consumidos.

## Bloqueos Preservados

Certification y Pro no reciben este rol ni este DDL Free-only. Certification
replay y toda ruta de collector/lectura/DDL Pro quedan superseded y bloqueadas en
este rebaseline. M4-M10, F10.9/G4, G5-G13, schedules,
observacion y F11.1 permanecen bloqueados. Un PASS operativo Free futuro tampoco
los habilitaria automaticamente; requieren sus autoridades y gates posteriores.

Enlaces: [Estado](../estado_del_proyecto.md) |
[TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) |
[Scope M3](./m3_f10_10_scope_por_ambiente_target.md) |
[Plan F10.10](./plan_remediacion_metadata_f10_10.md) |
[Flujo release](./flujo_release_minimo.md) |
[Plan cierre Hito 1](./plan_cierre_hito1_ca1_only.md)
