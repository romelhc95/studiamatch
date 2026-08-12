# F10.10 M3 - Scope Reader V2 Free-Only

| Campo | Valor |
|---|---|
| Gate | `F10.10/M3` |
| Estado | `M3_DDL_NULLABILITY_REMEDIATION_PENDING` |
| Target unico | `FREE_DB` |
| Collector | `f10.10-m3-readonly-collector-v2` |
| Canonical | `f10.10-m3-canonical-v2` |
| Ejecuta acceso remoto | `NO` |
| Gates consumidos | Preflight una vez PASS; DDL v1 una vez FAIL+rollback |
| Autoriza Certification / Pro / M4 | `NO / NO / NO` |

Este documento es el scope autoritativo M3 reader v2. Sustituye todas las
secciones ejecutables v1 del scope anterior. La
[evidencia M3 de PR #350](./m3_f10_10_post_merge_evidence_2026_08_11.md)
permanece antecedente historico del collector v1: no autoriza ejecucion v2, no
acredita este candidate y no consume gates.

Enlaces de autoridad: [rebaseline enfocado](./m3_reader_f10_10_rebaseline.md),
[plan F10.10](./plan_remediacion_metadata_f10_10.md),
[estado](../estado_del_proyecto.md) y
[TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).

## Frontera Free-Only

El collector v2 acepta exclusivamente `--target-alias FREE_DB`. `PRO_DB`, otro
alias o cualquier intento de continuar hacia Certification/Pro termina STOP.
Certification no ejecuta collector, replay ni nueva red dentro de este rebaseline.
No existe ruta M3 Pro autorizable desde este documento.

M3 diagnostica exclusivamente:

```text
public.courses.id
public.courses.is_active
public.courses.syllabus
public.courses.objectives
```

Puede inventariar catalogo estrictamente necesario para probar tipos,
nullability, PK, RLS, grants y superficies de trigger/rutina relacionadas, sin
otorgar al reader acceso ejecutable a esas rutinas. No genera contenido, no llama
providers, no modifica datos y no habilita M4.

## Package Free-Only

Provision:

```text
db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql
```

Compensacion exacta:

```text
db/rollbacks/20260811_fase10_10_m3_free_reader_compensating.sql
```

`db-sync-to-pro` debe excluir mecanicamente el path exacto
`db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql` y el path exacto
`db/rollbacks/20260811_fase10_10_m3_free_reader_compensating.sql` de toda
deteccion automatica de cambios Pro-relevant. El migrador Pro descubre solo
`db/migrations/*.sql`. Copiar, reflejar, detectar como Pro-relevant o aplicar
cualquiera de los dos paths Free-only en Pro termina STOP.

Para `apply_migration`, el SQL enviado no puede ser el blob canonico sin
transformar: su `COMMIT` cerraria el envelope transaccional que debe incluir el
ledger. La unica representacion admisible es
`f10.10-m3-apply-projection-v1`, generada localmente por
`scripts/maintenance/f10_10_m3_apply_projection.py`. Esta valida el package,
elimina solo sus wrappers externos, liga `current_user=session_user` al
fingerprint aprobado del provisioner y fija un `applied_query_digest` separado sin
imprimir ni versionar el nombre. Fingerprint y digest son bindings publicos no
secretos; el nombre literal no se serializa. Package, query-set y compensacion
quedan byte-identicos.

`apply_migration` se invoca como maximo una vez con migration name e identidad de
idempotencia fijados por el payload DDL. Timeout, 5xx, respuesta ambigua, mismatch
de digest/executor/target o ausencia de garantia rollback+ledger terminan STOP;
no se permite fallback a `execute_sql`, cambio de nombre ni retry automatico.
El [payload DDL Free](./m3_reader_f10_10_ddl_free_payload_2026_08_12.json)
congela `fase10_10_m3_free_reader_free_ddl_v1` como migration name e identidad de
idempotencia unica. Historicamente fue promovido como `PROPOSED_NOT_EXECUTED`;
su unica llamada posterior termino rollback y ahora queda
`CONSUMED_FAILED_SUPERSEDED`. No consumio Q0, lectura ni teardown.
Tras el merge protegido de PR #361, su binding `target-binding-v2` se renueva
exclusivamente offline; candidate/tree pasan al merge post-PR #361 sin cambiar
la identidad de migration, los digests del package/proyeccion ni las capacidades.

La unica ejecucion v1 termino `STOP_COURSES_COLUMN_CONTRACT_DRIFT` y rollback.
El diagnostico DB-as-Code identifica una precondicion obsoleta: `is_active` es
`boolean DEFAULT true` nullable, no `NOT NULL`. La remediacion corrige package,
collector y fixture, reserva `fase10_10_m3_free_reader_free_ddl_v2` y no genera
binding ni capacidad ejecutable. La identidad v1 no puede reutilizarse.

## Provisioner PostgreSQL 17

La provision usa el edge administrado minimo de PostgreSQL 17. El provisioner
aprobado se identifica privadamente mediante `F10_10_M3_PROVISIONER` y debe ser
exactamente el unico member del reader en `pg_auth_members`: `roleid=reader` y
`member=provisioner`. Ese unico edge debe tener:

```text
admin_option = true
inherit_option = false
set_option = false
```

No se acepta un segundo edge `roleid=reader`, una opcion distinta, `SET ROLE`,
session authorization, owner/superuser alternativo ni reparacion silenciosa. El
reader `studiamatch_m3_reader` es member de cero roles (`member=reader` no existe).
El unico edge inverso permitido es el provisioner aprobado como member/admin del
reader (`roleid=reader`) con las opciones exactas anteriores. Cualquier otro edge
termina STOP. El fingerprint domain-separated del provisioner aprobado forma
parte de `target-binding-v2`; el nombre permanece solo en evidencia privada.

## Estado Del Reader

La provision inicial crea exactamente:

```text
role = studiamatch_m3_reader
LOGIN = false
PASSWORD = NULL
rolvaliduntil = NULL
BYPASSRLS = true
SUPERUSER = false
CREATEDB = false
CREATEROLE = false
REPLICATION = false
INHERIT = false
CONNECTION LIMIT = 1
```

`BYPASSRLS=true` es obligatorio siempre: en provision, activacion, Q0 y collect.
No se acepta RLS policy como equivalente de visibilidad full-population.

El reader recibe `CONNECT` solo al database aprobado, `USAGE` solo en `public` y
SELECT de columna exactamente sobre `courses.id`, `courses.is_active`,
`courses.syllabus` y `courses.objectives`. Debe conservar cero SELECT sobre otra
columna/relacion, cero privilegio mutante, cero ownership, cero edges con
`member=reader`, exactamente el edge provisioner permitido con `roleid=reader`, y
cero acceso efectivo a rutinas no-sistema `SECURITY DEFINER`.

## Activacion Privada Q0

La provision DDL no activa el login. Bajo
`APPROVE_F10_10_M3_READER_Q0_FREE`, la activacion privada debe:

1. verificar de nuevo package, target y provisioner binding;
2. fijar `LOGIN` y un `VALID UNTIL` exacto, finito y futuro igual a
   `F10_10_M3_VALID_UNTIL`;
3. establecer el password exclusivamente con `psql` interactivo mediante
   `\password studiamatch_m3_reader`;
4. ejecutar `q0-only` dentro de la misma ventana;
5. no ejecutar Q1-Q4.

El password nunca aparece en SQL literal, argumento CLI, documentacion, Git,
logs, artifacts o transcript. El collector puede recibirlo solo por el canal
privado aprobado durante la ventana; esta documentacion no registra el valor.

Q0 exige exactamente `session_user=current_user=studiamatch_m3_reader`,
`BYPASSRLS=true`, `LOGIN=true`, `rolvaliduntil` igual al epoch exacto aprobado y
aun futuro, read-only on, `search_path=pg_catalog`, `client_encoding=UTF8`, cero
edges `member=reader`, exactamente un edge `roleid=reader` para el provisioner
aprobado con `admin=true/inherit=false/set=false`, y el contrato cerrado de
grants. Cualquier diferencia termina STOP.

## Binding V2 Offline

`target-binding-v2` se calcula sin red. Su payload privado incluye:

```text
schema = f10.10-m3-target-binding-v2
target_alias = FREE_DB
API host/project-ref fingerprints
SQL host/port/database/user fingerprints
provisioner fingerprint
F10_10_M3_VALID_UNTIL exact epoch
sslmode = verify-full
approved CA sha256
```

No incluye valores exactos esperados de protocolo TLS negociado, cipher, library
TLS ni `server_version_num`. Esas variables de entorno quedan eliminadas. Las
entradas privadas requeridas incluyen `F10_10_M3_PROVISIONER` y
`F10_10_M3_VALID_UNTIL`, ademas del binding Free, reader y CA aprobados.
El modo offline `target-binding-digest` no consume ni requiere
`F10_10_M3_PASSWORD`; `q0-only` y `collect` la exigen y detienen la ejecucion antes
de importar el driver o abrir una conexion si falta.

El CA se valida por digest, se copia a un `memfd` sellado y el mismo descriptor
aprobado se entrega a libpq con `sslmode=verify-full`. No se usa probe separado,
pooler ni conexion indirecta.

## Observed Transport V2

`observed-transport-v2` se produce solo despues de abrir la conexion aprobada. La
API publica libpq observa, desde esa misma conexion:

```text
host
port
database
user
ssl_in_use
protocol
cipher
library
server_version_num
```

Exige TLS activo, protocolo permitido y coincidencia de host/port/database/user
con el binding offline. Protocolo, cipher, library y servidor son observaciones,
no expected env vars.

`target_binding_digest` y `observed_transport_digest` usan dominios y payloads
distintos. Deben existir ambos y **NO deben ser iguales**. Igualdad termina
`STOP_DIGEST_DOMAIN_COLLISION`; ausencia o mezcla de payloads termina
`STOP_BINDING_CONTRACT`.

## Canonical Manifest V2 Y Content Digests

El collector, la serializacion/envelope del manifest canonical, el target
binding, el observed transport y el contrato predecessor son v2. El JSON del
manifest canonical v2 usa UTF-8, `ensure_ascii=true`, keys ordenadas y separadores
compactos.

La implementacion conserva intencionalmente los dominios content digest
domain-separated existentes:

```text
query-set-v1
schema-v1
constraints-v1
triggers-v1
snapshot-raw-v1
snapshot-normalized-v1
cohort-v1
```

Esos content digests v1 son validos dentro del manifest v2 y no implican aceptar
un manifest o binding v1. Los artifacts/manifests canonical v1 y
`target-binding-v1` historicos permanecen rechazados. No existe un dominio
`q0-attestation-v2`; Q0 se acredita mediante el manifest canonical v2, su modo,
decision, transcript sanitizado, binding, query-set y counters.

La normalizacion editorial sigue `f10.9-metadata-v2`. La referencia historica
`104/224` nunca es expected count ni allowlist.

## Predecessor Mecanico Q0

`collect` requiere mecanicamente un manifest predecessor `q0-only` canonical v2
con decision PASS. No basta una afirmacion humana ni un artifact privado suelto.
El predecessor debe:

- existir bajo la ruta privada aprobada y no ser symlink/overwrite;
- tener schema/modo `q0-only` v2 y decision `PASS`;
- corresponder a `FREE_DB` y al approval Q0 aprobado;
- probar mediante decision PASS y transcript sanitizado que Q0 valido
  internamente BYPASSRLS, login, expiracion y edges de membresia;
- tener `query_set_digest` igual al query-set runtime;
- tener `target_binding_digest` igual al binding offline runtime;
- conservar `observed_transport_digest` distinto de target binding;
- contener los counters sanitizados esperados para modo Q0;
- pasar verificacion de su digest canonical completo.

El manifest sanitizado predecessor no contiene valores raw de `BYPASSRLS`,
`rolvaliduntil`, password, nombres privados ni edges sin fingerprint. La prueba
publicable es PASS/transcript/binding/query-set/counters; los valores crudos
permanecen en la validacion interna y evidencia privada.

`collect` recibe tanto el path como el digest esperado del predecessor. Ausencia,
STOP/HOLD, expiracion, mismatch, canonical v1 o digest distinto termina
`STOP_Q0_PREDECESSOR_REQUIRED` antes de Q1-Q4.

## Invocacion V2 Ordenada

Siempre dentro de `studiamatch-dev`; los placeholders se resuelven solo desde el
payload privado aprobado:

```text
docker exec studiamatch-dev /tmp/f10_10_m3_venv/bin/python /app/scripts/maintenance/f10_10_m3_readonly_collector.py --mode query-set-digest
docker exec studiamatch-dev /tmp/f10_10_m3_venv/bin/python /app/scripts/maintenance/f10_10_m3_readonly_collector.py --mode target-binding-digest --target-alias FREE_DB --approval-id <Q0_APPROVAL>
docker exec studiamatch-dev /tmp/f10_10_m3_venv/bin/python /app/scripts/maintenance/f10_10_m3_readonly_collector.py --mode q0-only --target-alias FREE_DB --approval-id <Q0_APPROVAL> --expected-query-set-digest <QUERY_DIGEST> --expected-target-binding-digest <TARGET_DIGEST> --private-artifact local/f10_10/m3/<Q0_PRIVATE>.json --sanitized-manifest local/f10_10/m3/<Q0_MANIFEST>.json
docker exec studiamatch-dev /tmp/f10_10_m3_venv/bin/python /app/scripts/maintenance/f10_10_m3_readonly_collector.py --mode collect --target-alias FREE_DB --approval-id <READ_APPROVAL> --expected-query-set-digest <QUERY_DIGEST> --expected-target-binding-digest <TARGET_DIGEST> --q0-predecessor-manifest local/f10_10/m3/<Q0_MANIFEST>.json --expected-q0-predecessor-digest <Q0_MANIFEST_DIGEST> --private-artifact local/f10_10/m3/<COLLECT_PRIVATE>.json --sanitized-manifest local/f10_10/m3/<COLLECT_MANIFEST>.json
```

`q0-only` debe terminar PASS antes de invocar collect. No se permite `PRO_DB`,
omitir predecessor, reutilizar approval IDs ni derivar continuidad automatica.

## Teardown Fail-Closed

El teardown acepta como entrada tanto el estado inicial inactivo como un estado
activado con `LOGIN`, password no nulo y `VALID UNTIL` finito, sea aun futuro o ya
expirado. No exige volver manual y previamente al estado inicial.

La primera transaccion siempre cuarentena el rol:

```text
NOLOGIN
NOBYPASSRLS
PASSWORD NULL
```

Las sesiones del reader deben terminarse explicitamente bajo el gate de teardown
antes de intentar el drop. Despues se revocan los grants y settings creados por el
package. Solo al final ejecuta `DROP ROLE` si no hay sesiones, ownership ni
dependencias bloqueantes. Grants/dependencias ajenos al package pueden permanecer,
bloquear el DROP y exigir remediacion separada; no se describen como revocados por
este package. Un fallo posterior conserva el rol cuarentenado con los
grants/settings del package revocados, pero pueden persistir grants/dependencias
ajenos al package; nunca revierte la cuarentena para restaurar el estado activo.

## CI Local PostgreSQL 17

La imagen PostgreSQL 17 debe estar pinneada por digest. CI la descarga antes de
activar el firewall de egress. Despues del firewall, el runner inicia la prueba
con `--pull never --network none`; cualquier pull tardio o red distinta termina
STOP. La suite valida provision, edge del provisioner, estado NOLOGIN inicial,
activacion/Q0, BYPASSRLS obligatorio, cuatro columnas exactas, predecessor
mecanico, aislamiento Pro y teardown desde estado activo/inactivo.

La validacion final del candidate quedo acreditada por PR #353, merge protegido
`2cf614a4a44ffabc5e06ba08dc20707807db274f` y checks post-merge PASS. Esa
evidencia no autoriza Free ni consume gates.

## Credencial Canary Local

La [atestacion sanitizada de rotacion](./m3_reader_f10_10_rotation_attestation_2026_08_11.md)
confirma `FREE_DB_DATABASE_PASSWORD_ROTATED` y `OLD_CREDENTIAL_REVOKED`. El valor
no se registro ni inspecciono. `ROTATION_REQUIRED_OUT_OF_BAND` queda cerrado para
esa identidad, que permanece prohibida para provision, Q0, collect, teardown u
otro ambiente.

## Ledger De Gates

```text
APPROVE_F10_10_M3_READER_PREFLIGHT_FREE = CONSUMED_ONCE_PASS
APPROVE_F10_10_M3_READER_DDL_FREE = CONSUMED_ONCE_FAILED_ROLLBACK_SUPERSEDED
APPROVE_F10_10_M3_READER_Q0_FREE = NOT_CONSUMED
APPROVE_M3_FREE_READONLY = NOT_CONSUMED
APPROVE_F10_10_M3_READER_TEARDOWN_FREE = NOT_CONSUMED
```

El gate preflight fue consumido una vez y produjo [PASS sanitizado](./m3_reader_f10_10_preflight_evidence_2026_08_11.md).
DDL v1 fue consumido una vez y termino rollback; no puede reutilizarse. Q0 Free,
lectura y teardown siguen no consumidos/no ejecutables. Ningun gate concede el
siguiente.

El [payload exacto de preflight](./m3_reader_f10_10_preflight_payload_2026_08_11.json)
congela candidate, digests, binding offline, roles, CA y ventana de cuatro horas.
Su ejecucion no uso red ni password y termino PASS. No autoriza el gate DDL.
La ventana del preflight no se reutiliza para DDL. El payload DDL separado exige
el candidate de proyeccion promovido y un binding offline nuevamente vigente.
Certification, Pro, M4-M10, F10.9/G4, schedules, observacion y F11.1 permanecen
bloqueados. En este corte no hubo red, Supabase, DDL/DML remoto ni password; solo
se consumio el gate preflight local passwordless.
