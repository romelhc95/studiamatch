# F10.10 M3 - Alcance Por Ambiente Y Target Fisico

| Campo | Valor |
|---|---|
| Gate | `F10.10/M3` |
| Estado | `M3_COLLECTOR_CANDIDATE_PENDING_PROTECTED_MERGE` |
| Base | `desarrollo@c3108b499f0c8b02332404d45843c572707796ef` |
| Base tree | `42020a765ef21114754454cf8f928f3a0a12bf7b` |
| Ejecuta acceso remoto | `NO` |
| Autoriza M4 | `NO` |

Esta definicion concreta M3 del
[plan F10.10](./plan_remediacion_metadata_f10_10.md). El estado y la tarea viva
permanecen en [Estado del proyecto](../estado_del_proyecto.md) y
[TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).

La aprobacion de este documento autoriza el alcance, los aliases, query-set,
orden y criterios de salida. No autoriza una llamada remota: cada target conserva
un gate humano separado y el canal debe demostrar enforcement read-only antes de
leer.

## Objetivo Acotado

M3 solo puede contener y diagnosticar el estado vigente de:

```text
public.courses.id
public.courses.is_active
public.courses.syllabus
public.courses.objectives
```

Tambien puede inspeccionar metadata de catalogo estrictamente necesaria para
esas cuatro columnas: tipos/nullability/defaults, PK/constraints relevantes,
RLS/grants SELECT y triggers/funciones que reaccionen a syllabus/objectives.

No produce candidates editoriales, no llama providers y no modifica datos.

## Ambientes Y Orden Obligatorio

| Gate | Ambiente logico | Alias target | Accion remota | Prerrequisito |
|---|---|---|---|---|
| `M3-DEV-FREE` | Development | `FREE_DB` | Unica adquisicion fisica Free | `APPROVE_M3_FREE_READONLY` |
| `M3-CERT-FREE` | Certification | `FREE_DB` | Replay del binding/artifact; cero nueva lectura por defecto | `M3-DEV-FREE=PASS` + `APPROVE_M3_CERTIFICATION_REPLAY` |
| `M3-PRO` | Production | `PRO_DB` | Adquisicion fisica Pro separada | `M3-CERT-FREE=PASS` + tres approvals Pro exactos |

Development y Certification comparten Free como target fisico segun la topologia
vigente. Si sus configuraciones locales no resuelven al mismo binding, terminar
`STOP_TARGET_MISMATCH`; no crear dos cohortes ni escoger una silenciosamente.

Certification revalida el paquete Free. Una segunda lectura Free termina
`STOP_REAPPROVAL_REQUIRED` y exige una nueva instancia de
`APPROVE_M3_FREE_READONLY`, con nuevo approval ID y payload completo; nunca es
continuidad automatica ni usa un token alternativo implicito.

Pro no puede ser el primer target. Un HOLD/STOP en Free o Certification bloquea
Pro.

## Binding Privado Del Target

Antes de cualquier lectura, resolver URL y project ref desde configuracion local
gitignored del ambiente. Nunca imprimirlos ni versionarlos.

Normalizacion host `f10.10-m3-host-v1`:

1. exigir HTTPS;
2. lowercase e IDNA ASCII;
3. eliminar punto final;
4. rechazar userinfo, query, fragment, redirects y puerto distinto de 443;
5. comprobar que el project ref local corresponde al host resuelto.

```text
host_fingerprint = sha256("f10.10-m3-host-v1\0" || normalized_host)
physical_target = (local_project_ref, host_fingerprint)
api_binding_digest = domain_separated_sha256(physical_target)
```

El artifact privado conserva el tuple. La evidencia Git conserva solo:

```text
target_alias
target_binding_digest
host_normalization_version
approval_id
```

No publicar project ref, URL, hostname, IP, UUID de fila ni componentes que
permitan reconstruirlos.

## Canal Read-Only Autoritativo

Free y Pro exigen un colector local ejecutado dentro de `studiamatch-dev` sobre
una identidad SQL preexistente, full-population y read-only. El colector mantiene
una sola conexion TLS durante cada snapshot y escribe el artifact privado solo en
una ruta gitignored aprobada.

Este documento no implementa ni autoriza ese colector. Antes de consumir
`APPROVE_M3_FREE_READONLY` debe existir, revisarse y promoverse por PR protegido:

```text
scripts/maintenance/f10_10_m3_readonly_collector.py
tests/test_f10_10_m3_readonly_collector.py
```

El PR fija version, checksum, manifest del query-set, invocacion Docker,
allowlist de sentencias estaticas, zero-write tests y artifact path gitignored.
Tooling ad hoc, consola SQL y queries copiadas manualmente terminan
`STOP_COLLECTOR_NOT_PROMOTED`.

No se crea rol, grant, policy ni funcion para M3. Si la identidad no existe o no
cumple Q0, terminar `STOP_NEEDS_READONLY_CHANNEL`.

Antes de aprobar, la configuracion privada aporta el binding SQL esperado: host,
puerto, database, CA bundle, atributos TLS soportados y `server_version_num`
exacto esperados.
El host SQL usa
`f10.10-m3-sql-host-v1`: IDNA A-label ASCII lowercase, sin punto terminal,
userinfo, query ni fragment; el puerto es entero explicito. La conexion exige
TLS con validacion CA y hostname equivalente a `sslmode=verify-full`.

La misma conexion PostgreSQL, no un probe separado, observa host, puerto,
`current_database`, `server_version_num`, `ssl_in_use`, protocolo, cipher y
library TLS mediante la API publica libpq. El artifact
conserva binding esperado y observado; cualquier mismatch entre API alias,
configuracion local y conexion real termina `STOP_TARGET_MISMATCH`. La aprobacion
cita el digest esperado; el manifest PASS publica tambien el digest observado.

### MCP Free Opcional Y No Autoritativo

Supabase MCP puede usarse solo como sanity-check secundario de Q0-Q3 en Free:

```text
project_ref=<FREE_LOCAL_REF>
read_only=true
features=database
```

La aprobacion manual por llamada es un ajuste obligatorio del cliente MCP, no un
parametro del servidor. Cada tool call puede contener exactamente una sentencia.
Project scope debe deshabilitar account-management y `features=database` reducir
la superficie.

MCP no ejecuta snapshots, no recibe textos/filas `courses` y no acredita
poblacion, cohorte ni cero metadata. La publishable key/RLS tambien queda limitada
a replay publico secundario: ambos canales pueden producir un falso cero.

### Pro

Supabase MCP queda prohibido para `PRO_DB`: la recomendacion oficial es no
conectarlo a produccion. Pro usa exclusivamente el colector local y una identidad
SQL preexistente que pase Q0.

La conexion Pro se liga al target aprobado mediante un binding privado que agrega
al binding API:

```text
normalized_sql_dsn_host
sql_port
ca_certificate_sha256
tls_protocol
tls_cipher
tls_library
current_database
```

Solo el digest sale del artifact privado. Un mismatch de DSN, TLS, database o
asociacion local con el alias aprobado termina `STOP_TARGET_MISMATCH`.

No usar service/secret key, password postgres owner ni superuser. Toda transaccion
del colector comienza explicitamente `REPEATABLE READ READ ONLY`, ejecuta Q0 como
primera sentencia y comprueba `transaction_read_only=on`; no se confia solo en el
default del rol. La conexion fija `search_path=pg_catalog` antes de abrir la
transaccion y Q0 atesta `search_path=pg_catalog` y `client_encoding=UTF8`,
estabilizando toda renderizacion catalogo. Privilegio DML directo o transporte
sin esos enforcements termina `STOP_NEEDS_READONLY_CHANNEL`.

### Adenda De Implementacion Aprobada

La API publica de alto nivel elegida (`ConnectionInfo`/`PQsslAttribute`) no expone
el certificado leaf DER de la misma conexion. M3 no usa internals nativos,
`PQsslStruct` ni un probe separado: el binding exige
`sslmode=verify-full`, pin SHA-256 del CA file aprobado, hostname verification y
atributos TLS soportados. Cualquier atributo ausente o distinto termina
`STOP_TLS_CONTRACT` o `STOP_TARGET_MISMATCH`.

El CA aprobado se copia a un `memfd` collector-owned sellado contra write/grow/
shrink antes de entregarlo a libpq. Q1-Q3b usan named server-side cursors con
fetch acotado; Q0, BEGIN/COMMIT y cada pagina Q4 conservan cursor regular.

El collector usa `psycopg2-binary==2.9.12` ya fijado con hashes en
`requirements-pipeline.txt`; el import es lazy y la invocacion runtime instala
ese lock dentro de `studiamatch-dev`. No se agrega un segundo driver.

Solo se acepta conexion directa `db.<project_ref>.supabase.co:5432`; session y
transaction poolers terminan `STOP_TARGET_MISMATCH`. Asi el host liga fisicamente
el project ref y Q0 compara el rol efectivo exacto, sin confundir login pooler con
`current_user`.

Query-set `f10.10-m3-query-set-v1` incluye exactamente, ordenados por path:

```text
scripts/maintenance/f10_10_m3_readonly_collector.py
tests/test_f10_10_m3_readonly_collector.py
```

El digest se calcula runtime sobre texto UTF-8 normalizado; no se incrusta en los
archivos que hashea. Limites fail-closed: pagina `500`, poblacion `10000`, string
`32768` chars, presupuesto remoto acumulado `16 MiB`, cada resultado catalogo
`50000` filas, artifact `64 MiB`, connect timeout `10s` y
statement/lock/idle-in-transaction timeout `60s`. Artifacts solo bajo
`local/f10_10/m3/`, ruta ya gitignored; symlink, traversal u overwrite terminan
STOP.

Invocacion reproducible, siempre dentro del contenedor:

```text
docker exec studiamatch-dev python3 -m venv /tmp/f10_10_m3_venv
docker exec studiamatch-dev /tmp/f10_10_m3_venv/bin/pip install --require-hashes -r /app/requirements-pipeline.txt
docker exec studiamatch-dev /tmp/f10_10_m3_venv/bin/python /app/scripts/maintenance/f10_10_m3_readonly_collector.py --mode query-set-digest
docker exec studiamatch-dev /tmp/f10_10_m3_venv/bin/python /app/scripts/maintenance/f10_10_m3_readonly_collector.py --mode target-binding-digest --target-alias <ALIAS> --approval-id <APPROVAL_ID>
docker exec studiamatch-dev /tmp/f10_10_m3_venv/bin/python /app/scripts/maintenance/f10_10_m3_readonly_collector.py --mode collect --target-alias <ALIAS> --approval-id <APPROVAL_ID> --expected-query-set-digest <DIGEST> --expected-target-binding-digest <DIGEST> --private-artifact local/f10_10/m3/<PRIVATE>.json --sanitized-manifest local/f10_10/m3/<MANIFEST>.json
```

La instalacion o ejecucion no ocurre hasta consumir el gate remoto exacto. El
manifest sanitizado se publica ultimo como commit marker; un private artifact sin
manifest se considera adquisicion incompleta y nunca PASS. El canal publico usa
`approval_fingerprint`, no el approval ID crudo.

Referencias Supabase consultadas al definir este contrato:

- https://supabase.com/docs/guides/ai-tools/mcp
- https://supabase.com/docs/guides/api/securing-your-api
- https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically

## Query-Set Exacto

Cada sentencia es estatica y se aprueba antes de ejecucion. No se permiten
queries ad hoc. Q0 ocurre antes de cualquier catalogo o fila.

### Q0 - Canal, Rol Y Visibilidad Completa

```sql
select
  session_user,
  current_user,
  current_database(),
  current_setting('transaction_read_only') as transaction_read_only,
  current_setting('default_transaction_read_only') as default_transaction_read_only,
  current_setting('search_path') as effective_search_path,
  current_setting('client_encoding') as client_encoding,
  r.rolsuper,
  r.rolbypassrls,
  r.rolcreaterole,
  r.rolcreatedb,
  exists (
    select 1 from pg_catalog.pg_auth_members as m where m.member = r.oid
  ) as has_role_memberships,
  c.relrowsecurity,
  c.relforcerowsecurity,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'SELECT') as can_select,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'INSERT') as can_insert,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'UPDATE') as can_update,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'DELETE') as can_delete,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'TRUNCATE') as can_truncate,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'REFERENCES') as can_reference,
  pg_catalog.has_table_privilege(current_user, 'public.courses', 'TRIGGER') as can_trigger,
  exists (
    select 1
    from pg_catalog.pg_attribute as a
    where a.attrelid = 'public.courses'::regclass
      and a.attnum > 0
      and not a.attisdropped
      and (
        pg_catalog.has_column_privilege(current_user, a.attrelid, a.attnum, 'INSERT')
        or pg_catalog.has_column_privilege(current_user, a.attrelid, a.attnum, 'UPDATE')
        or pg_catalog.has_column_privilege(current_user, a.attrelid, a.attnum, 'REFERENCES')
      )
  ) as has_mutating_column_privilege
from pg_catalog.pg_roles as r
join pg_catalog.pg_class as c on c.oid = 'public.courses'::regclass
where r.rolname = current_user;
```

Exigir exactamente una fila y:

```text
session_user = current_user
transaction_read_only = on
default_transaction_read_only = on
effective_search_path = pg_catalog
client_encoding = UTF8
rolsuper = false
rolcreaterole = false
rolcreatedb = false
has_role_memberships = false
can_select = true
can_insert = false
can_update = false
can_delete = false
can_truncate = false
can_reference = false
can_trigger = false
has_mutating_column_privilege = false
full_population_visibility = (relrowsecurity = false OR rolbypassrls = true)
```

Si RLS esta activo, solo se acepta un rol no-superuser con `rolbypassrls=true`,
sin DML y read-only forzado. No se interpretan policies como prueba equivalente
de visibilidad completa. Role/database names permanecen privados.

### Q1 - Columnas

```sql
select
  a.attname as column_name,
  pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type,
  a.attnotnull as not_null,
  pg_catalog.pg_get_expr(d.adbin, d.adrelid) as default_expression
from pg_catalog.pg_attribute as a
left join pg_catalog.pg_attrdef as d
  on d.adrelid = a.attrelid and d.adnum = a.attnum
where a.attrelid = 'public.courses'::regclass
  and a.attnum > 0
  and not a.attisdropped
  and a.attname in ('id', 'is_active', 'syllabus', 'objectives')
order by a.attnum;
```

Exigir exactamente cuatro filas: `id=uuid NOT NULL`, `is_active=boolean NOT
NULL`, `syllabus=text NULL` y `objectives=text NULL`. Un `is_active=NULL` o
cualquier drift termina `STOP_SCHEMA_DRIFT`.

### Q2 - Constraints Relevantes

```sql
select
  c.conname,
  c.contype,
  pg_catalog.pg_get_constraintdef(c.oid, true) as constraint_definition,
  case when c.contype = 'p' then k.ordinality::integer else null end as key_ordinality,
  case when c.contype = 'p' then a.attname else null end as key_column_name
from pg_catalog.pg_constraint as c
left join lateral unnest(c.conkey) with ordinality as k(attnum, ordinality) on true
left join pg_catalog.pg_attribute as a
  on a.attrelid = c.conrelid and a.attnum = k.attnum
where c.conrelid = 'public.courses'::regclass
  and (
    c.contype = 'p'
    or pg_catalog.pg_get_constraintdef(c.oid, true) ~* '(syllabus|objectives)'
  )
order by c.conname, k.ordinality nulls first;
```

Q2 demuestra estructuralmente que existe exactamente una PK de una columna `id`;
cualquier PK
compuesta, ausencia de PK o unicidad/nullability ambigua termina
`STOP_UNSTABLE_KEYSET`.

### Q3 - Triggers Completos

```sql
select
  t.oid as trigger_oid,
  t.tgname,
  pg_catalog.pg_get_triggerdef(t.oid, true),
  p.oid as function_oid,
  p.proname,
  pg_catalog.pg_get_functiondef(p.oid)
from pg_catalog.pg_trigger as t
join pg_catalog.pg_proc as p on p.oid = t.tgfoid
where t.tgrelid = 'public.courses'::regclass
order by t.tgname, p.proname, t.oid;
```

Inventariar todos los triggers, incluidos internos, no solo coincidencias
textuales.

`pg_depend` no demuestra llamadas semanticas dentro de PL/pgSQL o SQL dinamico.
Q3b no hace esa afirmacion: captura la superficie completa de rutinas no-sistema
y extensiones del target, de modo que cualquier helper local, incluso invocado
dinamicamente, cambie el fingerprint:

```sql
select
  n.nspname,
  p.proname,
  p.prokind,
  l.lanname,
  pg_catalog.pg_get_function_identity_arguments(p.oid) as identity_arguments,
  pg_catalog.pg_get_functiondef(p.oid) as function_definition
from pg_catalog.pg_proc as p
join pg_catalog.pg_namespace as n on n.oid = p.pronamespace
join pg_catalog.pg_language as l on l.oid = p.prolang
where n.nspname not in ('pg_catalog', 'information_schema')
  and n.nspname !~ '^pg_toast'
  and p.prokind in ('f', 'p', 'w')
order by n.nspname, p.proname,
         pg_catalog.pg_get_function_identity_arguments(p.oid);

select e.extname, e.extversion, n.nspname
from pg_catalog.pg_extension as e
join pg_catalog.pg_namespace as n on n.oid = e.extnamespace
order by e.extname;

select
  n.nspname,
  p.proname,
  pg_catalog.pg_get_function_identity_arguments(p.oid) as identity_arguments,
  pg_catalog.pg_get_function_result(p.oid) as result_type,
  a.aggkind,
  a.aggnumdirectargs,
  a.aggtransfn::regprocedure::text as transition_function,
  a.aggfinalfn::regprocedure::text as final_function,
  a.aggcombinefn::regprocedure::text as combine_function,
  a.aggserialfn::regprocedure::text as serial_function,
  a.aggdeserialfn::regprocedure::text as deserial_function,
  pg_catalog.format_type(a.aggtranstype, null) as transition_type,
  a.aggtransspace,
  a.aggmtransfn::regprocedure::text as moving_transition_function,
  a.aggminvtransfn::regprocedure::text as moving_inverse_function,
  a.aggmfinalfn::regprocedure::text as moving_final_function,
  pg_catalog.format_type(a.aggmtranstype, null) as moving_transition_type,
  a.aggmtransspace,
  a.aggfinalextra,
  a.aggmfinalextra,
  a.aggfinalmodify,
  a.aggmfinalmodify,
  a.agginitval,
  a.aggminitval,
  onsp.nspname as sort_operator_schema,
  o.oprname as sort_operator_name,
  olnsp.nspname as sort_operator_left_type_schema,
  olt.typname as sort_operator_left_type_name,
  ornsp.nspname as sort_operator_right_type_schema,
  ort.typname as sort_operator_right_type_name
from pg_catalog.pg_aggregate as a
join pg_catalog.pg_proc as p on p.oid = a.aggfnoid
join pg_catalog.pg_namespace as n on n.oid = p.pronamespace
left join pg_catalog.pg_operator as o on o.oid = a.aggsortop
left join pg_catalog.pg_namespace as onsp on onsp.oid = o.oprnamespace
left join pg_catalog.pg_type as olt on olt.oid = o.oprleft
left join pg_catalog.pg_namespace as olnsp on olnsp.oid = olt.typnamespace
left join pg_catalog.pg_type as ort on ort.oid = o.oprright
left join pg_catalog.pg_namespace as ornsp on ornsp.oid = ort.typnamespace
where n.nspname not in ('pg_catalog', 'information_schema')
  and n.nspname !~ '^pg_toast'
order by n.nspname, p.proname,
         pg_catalog.pg_get_function_identity_arguments(p.oid);

select
  e.extname,
  d.classid::regclass::text as class_name,
  d.objid,
  d.objsubid
from pg_catalog.pg_depend as d
join pg_catalog.pg_extension as e on e.oid = d.refobjid
where d.refclassid = 'pg_catalog.pg_extension'::regclass
  and d.deptype = 'e'
order by e.extname, d.classid::regclass::text, d.objid, d.objsubid;
```

Definiciones permanecen privadas; el artifact clasifica relevancia por separado.
Una rutina/agregado cuya definicion no pueda obtenerse, una language no
inventariable o drift en cualquier rutina, agregado, extension o membresia
termina `STOP_OPAQUE_ROUTINE_SURFACE`. Q2/Q3/Q3b solo publican conteos y
fingerprints.

### Q4 - Dos Snapshots Completos

Q0-Q3b corren primero en una transaccion propia. Cada traversal Q4 corre despues
en su propia transaccion y conexion estable; Q0 es la primera sentencia de las
tres transacciones:

```sql
begin transaction isolation level repeatable read read only;
```

Primera pagina:

```sql
select id, is_active, syllabus, objectives
from public.courses
order by id asc
limit 500;
```

Paginas siguientes:

```sql
select id, is_active, syllabus, objectives
from public.courses
where id > %s
order by id asc
limit 500;
```

Continuar hasta una pagina menor a 500 filas y luego `commit`. Abrir una segunda
transaccion repeatable-read/read-only y repetir Q4 desde cero. Prohibido
`OFFSET`, `select=*`, joins, views o filtros de cohorte. El unico parametro `%s`
recibe `last_private_id` como UUID privado mediante binding DB-API.

La pagina terminal menor a 500 cuenta en `page_count`, incluida una pagina vacia
solo cuando la poblacion es multiplo exacto de 500. Antes de conservar la fila
10.001, terminar `STOP_POPULATION_LIMIT`.

## Conteos Y Digests

Por snapshot:

```text
page_count
total_count
total_ids_digest
active_count
active_ids_digest
missing_syllabus
missing_objectives
missing_both
incomplete_active_courses
incomplete_slots
full_snapshot_raw_digest
full_snapshot_normalized_digest
cohort_fingerprint
schema_fingerprint
constraint_fingerprint
trigger_fingerprint
query_set_digest
target_binding_digest
```

Todos los conteos missing usan exclusivamente filas `is_active=true`.
`missing_both` cuenta cursos activos con ambos campos missing;
`incomplete_active_courses` cuenta la union; `incomplete_slots` cuenta campos.

Serializacion `f10.10-m3-canonical-v1`:

```text
canonical_json = UTF-8, ensure_ascii=true, sort_keys=true, separators=(",", ":")
null = ["null"]
string = ["string", value]
boolean = ["boolean", true|false]
integer = ["integer", decimal_ascii]
digest(domain, value) = SHA256(
  "f10.10-m3:" || domain || "\n" || uint64_be(len(canonical_json)) || canonical_json
)
```

Todo preimage es exactamente
`{"domain":<domain>,"version":1,"payload":<payload>}` bajo canonical JSON. No
se omiten keys; SQL usa bytes UTF-8 con BOM prohibido y CRLF/CR normalizado a LF,
incluido un unico LF final. Payloads exactos:

```text
total-ids-v1 / active-ids-v1 = [[typed_id], ...]
snapshot-raw-v1 = [[typed_id, ["boolean",is_active], typed_syllabus, typed_objectives], ...]
snapshot-normalized-v1 = misma matriz con strings normalizados y missing como ["null"]
cohort-v1 = [[typed_id, ["boolean",missing_syllabus], ["boolean",missing_objectives]], ...]
schema-v1 = filas Q1 como arrays en el orden exacto del SELECT
constraints-v1 = filas Q2 como arrays en el orden exacto del SELECT
triggers-v1 = {"triggers":filas_Q3,"routines":filas_Q3b,"extensions":filas_extensiones,"aggregates":filas_agregados,"extension_members":filas_membresias}
query-set-v1 = {"collector_version":string,"files":[[relative_path,sha256_hex,normalized_utf8_text],...]}
target-binding-v1 = {"alias":string,"api":[host_normalization_version,project_ref_fingerprint,host_fingerprint],"sql":[sql_host_normalization_version,sql_host_fingerprint,port,database_fingerprint,tls_mode,ca_sha256,[ssl_in_use,tls_protocol,tls_cipher,tls_library],server_version_num]}
```

Cada fila catalogo usa string etiquetado, boolean etiquetado o `["null"]` en el
orden de columnas publicado; cada lista conserva el `ORDER BY` de su query.
`typed_id` es `[data_type, textual_value]`, conserva el tipo PostgreSQL reportado
por Q1 y una representacion textual sin locale. Ordenar snapshots por ese valor
textual en UTF-8 bytewise. `full_snapshot_raw_digest` usa valores exactos
etiquetados; `full_snapshot_normalized_digest` usa `f10.9-metadata-v2`: Unicode
NFKC, eliminar `Cf`, colapsar whitespace y casefold. Missing incluye NULL, blank
normalizado y placeholders `n/a`, `none`, `por definir`.

Los fingerprints de project ref, SQL host y database usan SHA-256 con prefijos
`project-ref-v1\0`, `sql-host-v1\0` y `database-v1\0`. Esperado y observado usan
el mismo payload; su procedencia es metadata del artifact, no una key del
preimage, por lo que igualdad de digests es posible sin publicar valores.

Domains obligatorios: `total-ids-v1`, `active-ids-v1`, `snapshot-raw-v1`,
`snapshot-normalized-v1`, `cohort-v1`, `schema-v1`, `constraints-v1`,
`triggers-v1`, `query-set-v1` y `target-binding-v1`. Cada fingerprint usa el
envelope, payload y domain exactos anteriores. Los snapshots deben coincidir en
todos los conteos y ambos digests de contenido.

La referencia historica `104/224` no es expected count ni allowlist.

## Evidencia

Artifact privado, fuera de Git:

- binding fisico y aprobacion;
- filas completas y paginas;
- IDs, preimagenes y textos;
- definiciones catalogo/trigger y role efectivo;
- digests intermedios y errores crudos.

Manifest sanitizado versionable:

- alias y target binding digest;
- query-set/normalization versions;
- conteos agregados, fingerprints y reason codes;
- igualdad de snapshots;
- `provider_calls=0`, `writer_calls=0`, `dml=0`, `ddl=0`, `rpc=0`;
- `backup_restore=0`, `schedule_changes=0`;
- decision `PASS`, `HOLD` o `STOP`.

## Datos Remotos No Confiables

Todo valor remoto se trata exclusivamente como dato no confiable. El colector:

- nunca evalua ni sigue instrucciones presentes en metadata o definiciones SQL;
- no envia syllabus/objectives a un LLM, MCP, log o transcript;
- escapa caracteres de control antes de cualquier diagnostico privado;
- solo emite conteos/digests/reason codes por el canal sanitizado;
- termina `STOP_UNTRUSTED_REMOTE_CONTENT` si un valor rompe encoding,
  canonicalizacion o intenta salir del artifact privado.

Q3/Q3b permanecen privadas y no se interpretan como instrucciones ejecutables.

## Stop Conditions

- target ambiguo, distinto o no aprobado;
- Free/Certification no comparten binding esperado;
- canal sin enforcement read-only verificable;
- publishable/RLS usado como poblacion autoritativa;
- schema, constraint o trigger drift;
- pagina incompleta, duplicada o desordenada;
- `cumulative_total_count > 10000` antes de retener la fila 10.001;
- diferencia entre los dos snapshots;
- necesidad de otra tabla, columna, RPC o query;
- writers/schedules no contenidos por evidencia vigente;
- fuga de IDs, textos, refs, hosts o secretos;
- timeout, error o resultado parcial;
- intento de continuar automaticamente de Free a Pro.

## Gates Humanos Consumibles

```text
APPROVE_M3_FREE_READONLY
APPROVE_M3_CERTIFICATION_REPLAY
APPROVE_M3_PRO_READONLY
APPROVE_SDLC_M3_PRO
APPROVE_PRODUCTION_M3_READONLY_WINDOW
```

Cada aprobacion debe citar alias, target binding digest esperado, query-set digest
del colector promovido, clase de credencial, artifact/digest predecesor y ventana.
No es reutilizable entre targets. El digest observado se produce dentro de esa
ventana y debe igualar al esperado para PASS.

`M3-CERT-FREE=PASS` exige igualdad exacta de target binding, artifact privado,
manifest digest, query-set, canonicalizacion, snapshot digests y decision Free;
no ejecuta red. Cualquier diferencia termina `STOP_CERTIFICATION_REPLAY_DRIFT`.

Para Pro, el orden obligatorio es: `APPROVE_SDLC_M3_PRO`, luego
`APPROVE_PRODUCTION_M3_READONLY_WINDOW`, y finalmente
`APPROVE_M3_PRO_READONLY`. Faltar uno bloquea la conexion.

La frase decimal F10.10 por si sola no consume estos gates. M3 PASS no concede
M4 ni reactiva F10.9/G4.
