# Preflight Free Read-Only F9.4

Esta nota define la subfase F9.4 de la [macrofase F9](./certificacion_hito1_f9.md). Canonicaliza el paso de validacion Free del plan temporal sin convertir ese antecedente en autoridad ejecutable.

## Estado De La Definicion

- Subfase: `F9.4`.
- Capability exclusiva: `REMOTE_READ_FREE`.
- Estado de fase: `PENDING`.
- Estado de definicion: `DEFINED_BLOCKED`.
- Target remoto permitido: Free unicamente.
- Subfase autorizada: ninguna.
- Resultado remoto futuro: `FREE_PREFLIGHT_PASS` o `FREE_PREFLIGHT_FAIL`.
- Estado del package: `reconciled_not_certified`, sin cambios.
- Free y Pro: schema apply bloqueado.
- T01 y attestations: cero.

Esta definicion no autoriza implementar el adapter, cargar secretos, usar Supabase MCP de proyecto, conectar a Free/Pro ni producir evidencia remota. Mientras exista un blocker abierto, la frase de ejecucion F9.4 no concede capacidad local ni remota.

## Reconciliacion Del Alcance Solicitado

| # | Requisito | Contrato F9.4 |
|---:|---|---|
| 1 | F9.3 byte-identical | Descriptor, catalogos, schemas y validators F9.3 permanecen inmutables. |
| 2 | Adapter minimo | Se crea separado; no agrega modo remoto al runner F9.3 ni primitives genericas. |
| 3 | Identidad Free | Se revalida localmente antes del primer socket y se rechaza toda ambiguedad. |
| 4 | Ledger paginado | Usa `migration_ledger` exacto, keyset, pagina 100 y terminal corta. |
| 5 | Schema/constraints/indices | Usa solo los query IDs congelados correspondientes. |
| 6 | Funciones/triggers | Usa `catalog_routines`, grants y `catalog_triggers`; no invoca funciones. |
| 7 | RLS/policies/ACL | Usa relations, policies y los cuatro inventarios ACL congelados. |
| 8 | Owners/security/search_path | Clasifica owners, `SECURITY DEFINER`, view security options y `proconfig`. |
| 9 | `exec_sql` | Inspecciona metadata y grants; queda prohibida toda invocacion/RPC. |
| 10 | PostgREST | Ejecuta unicamente el GET congelado si el blocker de compatibilidad se resuelve. |
| 11 | Advisors | Invoca solo `supabase-free.get_advisors` security/performance. |
| 12 | Backup/restore | Registra factibilidad pendiente y gate humano; no lista, crea, descarga ni restaura backups. |
| 13 | Writers | Evalua inventario/gates; no pausa, cancela, despacha ni reanuda writers. |
| 14 | Rollback/forward-fix | Evalua el contrato local; no ejecuta restore, migration ni SQL de recuperacion. |
| 15 | PASS/FAIL | Produce el envelope exacto F9.3 cuando una ejecucion remota valida comienza. |
| 16 | T01 | No crea T01. |
| 17 | Estado | No cambia status del package, tarea, criterio ni ambiente. |
| 18 | Schema | No desbloquea ni aplica schema en Free o Pro. |

## Binding Inmutable F9.3

La referencia canonica remota es el merge aprobado de PR #240: `desarrollo@2a7353a390359437a894ce3440d04cca56b6bffc`, tree `79278a6d1e4d48f608b120c682cf6717490bf5d0`, reconstruida con historia completa en un clon Linux limpio dentro de Docker. Gate D vuelve a exigir `git cat-file`/tree/blob sobre esa historia; un checkout local stale no sustituye la referencia remota.

| Path | Git blob SHA-1 | SHA-256 LF | Regla |
|---|---|---|---|
| `db/manifests/f9_3_free_preflight_contract.json` | `9797070a5df5dd52499c367afbfbbd5195bfade6` | `82562465a60541e4735c5bb8a4101baf1833277cb7a010eef310bf6c5b28f354` | Byte-identical |
| `scripts/maintenance/free_preflight.py` | `0b7e0ff11ea89b26b8f893d998f5e2289c6af088` | `543cff44e46f84326ae774009a58ccf4fb7d0525ff0797cd5cca561706e45a00` | Byte-identical |
| `tests/test_fase09_free_preflight.py` | `835d6ea7884d83db73c66a3ea58c25cc0d0a4c63` | `9642f9c9de0635f81f4d2769aa62558735a82155d7b18c988985f180a1269d33` | No modificar; agregar pruebas F9.4 separadas |

Tambien permanecen inmutables los source entries, package binding, 15 queries, operacion HTTP, dos tool operations, tres capacidades locales, ACL policy, schemas de traces y evidence schema contenidos en el descriptor. La representacion canonica es LF/Git blob; un checkout Windows no es evidencia.

## Adapter Minimo Separado

El adapter futuro se limita a cuatro componentes cerrados:

1. `preflight coordinator`: valida contrato, Git, autorizacion, ventana, target y policy antes de red.
2. `postgres catalog transport`: ejecuta solo queries producidas por `prepare_catalog_query()` dentro de una transaccion `REPEATABLE READ READ ONLY`.
3. `postgrest probe`: ejecuta solo la operacion HTTP congelada, sin redirects, body, Bearer ni fallback.
4. `advisor bridge`: determinista y sin interpretacion LLM; invoca exactamente los dos tools congelados desde una sesion MCP project-scoped/read-only y reduce respuestas en memoria a los traces F9.3.

El reducer local valida observaciones con `free_preflight.py`, construye traces/evidencia exactos y persiste solo artefactos sanitizados. No se permiten interfaces `execute_sql`, `rpc`, `request`, URL, method, schema, project ref o query arbitrarios.

## Transportes Y Credenciales

| Plano | Operacion permitida | Identidad minima | Restriccion |
|---|---|---|---|
| PostgreSQL | 15 SELECT exactos en una transaccion | `FREE_SUPABASE_READ_ONLY_DSN`, rol preexistente y probado como read-only | TLS hostname/CA; sin fallback a `postgres` o credencial privilegiada |
| Data API | Un GET exacto `/rest/v1/` | `FREE_NEXT_SUPABASE_PUBLISHABLE_KEY` solo en `apikey` | Sin `Authorization`, secret key, redirect ni otra ruta |
| Advisors | Dos lecturas exactas | MCP project-scoped/read-only `supabase-free.get_advisors` con identidad de sesion atestada y feature/tool allowlist de advisors si el servidor lo soporta | Sin Management API sustituta, tool adicional ni transformacion LLM; si no puede restringirse o probarse, B03 sigue abierto |
| Anti-confusion Pro | Validacion local de separacion | URL/publishable Pro requeridos por target binding F9.3 | Cero DNS, socket, HTTP, SQL o tool hacia Pro |

Las credenciales se inyectan desde el gestor de secretos autorizado, nunca desde archivos versionados, argumentos CLI, logs o evidencia. El adapter no imprime origins, refs, DSN, keys, filas, OpenAPI ni findings.

## Revalidacion De Target Antes De Red

1. Verificar descriptor, source bindings, runner y adapter policy desde Git limpio en Docker/Linux.
2. Reconstruir commit/tree/blob con `validate_git_binding()`.
3. Cargar exactamente los cuatro nombres F9.3 de Free/Pro y rechazar nombres genericos.
4. Cargar desde `.context/artifacts/private/f9_4/target_identity.json` el artifact revisado que cumple la policy F9.3; el path esta gitignored.
5. Ejecutar `build_target_validation()` y comparar en tiempo constante.
6. Ligar mediante un artifact cross-plane de schema cerrado el host/rol SQL, origin Data API, sesion MCP y target artifact al mismo digest Free revisado; persistir solo sus digests.
7. Validar rol SQL efectivo, TLS, adapter policy hash, commit/tree aprobado, nonce, ventana UTC e intento unico.
8. Solo despues abrir el primer socket Free.

La ausencia o ambiguedad de cualquier input aborta antes de red. Pro solo participa en la prueba local anti-confusion.

## Secuencia Remota Cerrada

1. `BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY`.
2. Aplicar los tres `SET LOCAL` congelados: statement 5000 ms, lock 1000 ms e idle 10000 ms.
3. Ejecutar los 15 query IDs en el orden del descriptor, con paginacion y terminal page exactas.
4. Ejecutar `ROLLBACK` en `finally`; no existe `COMMIT`.
5. Validar SQL trace sin filas raw.
6. Ejecutar el unico GET PostgREST y validar HTTP trace sin body raw.
7. Invocar advisors security/performance y validar dos tool traces sin responses raw.
8. Registrar las tres clasificaciones locales requeridas.
9. Validar el envelope final F9.3 y emitir su etiqueta externa PASS/FAIL.

No hay retries, fallback de transporte, segunda credencial ni correccion en caliente. Un segundo intento requiere otra autorizacion remota exacta.

## Limites Del Adapter

- Timeout de conexion/TLS: 5000 ms por transporte.
- Deadline wall-clock total: 900000 ms.
- SQL: maximo 1001 paginas y 100000 filas por query, 1 MiB serializado por fila, 8 MiB por pagina, 64 MiB agregados por query y 256 MiB SQL por ejecucion.
- HTTP OpenAPI: maximo 16 MiB.
- Advisor response: maximo 4 MiB y 10000 items por tool.
- Bytes remotos de payload SQL + HTTP + advisors: maximo 280 MiB por ejecucion.
- Memoria de proceso: maximo 256 MiB, digest incremental y cero spill de filas/bodies/findings a disco.
- Mapping cerrado: deadline/timeout -> `TIMEOUT`; limite SQL/local -> `CATALOG_POLICY_VIOLATION`; HTTP size -> `HTTP_TRACE_INVALID`; advisor size/items -> `TOOL_TRACE_INVALID`. No se inventa `LIMIT_EXCEEDED` ni se eleva un limite durante la ejecucion.

## Cobertura De Inspeccion

- Ledger: completo, paginado y clasificado como package ausente o prefijo exacto; PASS no afirma por si solo que el package este aplicado.
- Schema: relations/columns de `public`, `auth` y `storage` segun visibilidad del rol.
- Constraints: definicion y `convalidated`.
- Indices: inventario determinista.
- RLS/policies: flags y expresiones, sin publicar detalle raw.
- ACL: schemas, tablas, columnas, secuencias y routines para roles congelados.
- Owners: schemas, relations, views y routines cubiertos por queries F9.3.
- Security mode: `SECURITY DEFINER`, runtime settings/search path y view security options.
- Functions/triggers: metadata de routines public y triggers public no internos.
- `exec_sql`: firma, overloads, owner, lenguaje, retorno, security mode, search path y EXECUTE grants; nunca body ni llamada.
- PostgREST/advisors: solo proyecciones, conteos y digests.

## Evaluaciones Sin Ejecucion

- Backup/restore: `BACKUP_APPROVAL_REQUIRED_NOT_EXECUTED`. Solo registra factibilidad pendiente. En Free no se presume backup administrado; alcance del dump y restore drill pertenecen a F9.6 y exigen aprobacion.
- Writers: `SEPARATE_PAUSE_RESUME_APPROVAL_REQUIRED`. F9.4 no modifica schedules, workflows, runs o containers.
- Rollback: `ROLLBACK_ONLY_NO_REMOTE_EXECUTION`. Solo verifica que el plan forward-fix/restore conserva gates; no ejecuta recovery.

## Evidencia Y Resultados

Los SQL/HTTP/tool traces y el envelope usan exactamente los schemas F9.3. Pueden existir solo sanitizados bajo `.context/artifacts/private/f9_4/<run-id>/`; filas, bodies y findings raw viven unicamente en memoria y nunca se escriben. Si `item_count > 0`, un sidecar privado obligatorio conserva IDs, niveles y URLs de remediacion sanitizados, ligado por hash pero fuera del envelope; PASS valida transporte/shape y no acepta ni cierra findings.

`FREE_PREFLIGHT_PASS` significa exclusivamente que target, contrato, 15 queries, ledger/paginacion, rollback, GET, advisors, clasificaciones locales y evidencia pasaron el contrato F9.3. No significa `ready_for_free`, advisors limpios, backup aprobado, writers pausados, schema aplicado ni Free certificada.

`FREE_PREFLIGHT_FAIL` detiene F9.4, no reintenta, no crea attestation y no habilita F9.5. Un fallo anterior a target/Git/autorizacion es `ABORTED_BEFORE_REMOTE_EVIDENCE`, no se falsifica como envelope F9.3.

El cierre documental posterior registra solo etiqueta, conteos, digests, commit/tree, ventana UTC y hashes de artefactos privados. No publica componentes sensibles.

## Blockers Vigentes

| ID | Blocker | Consecuencia | Resolucion exigida |
|---|---|---|---|
| `F94-B01` | Desde 2026-04-08 OpenAPI root exige secret/service-role y PostgREST v14 expone Swagger 2 (`swagger`), mientras F9.3 exige publishable `apikey` y proyeccion `openapi` | El GET exacto no tiene ruta legitima a PASS | Aprobar contrato sucesor local sin reescribir F9.3, o cancelar/diferir F9.4; un FAIL diagnostico no resuelve el blocker |
| `F94-B02` | No existe identidad SQL read-only inventariada y F9.3 no consulta identidad, memberships, `rolsuper`, `rolbypassrls` o default read-only | No puede probarse minimo privilegio con el catalogo exacto | Contrato sucesor local debe probar rol efectivo; provisionar credencial, si hiciera falta, usa otro gate |
| `F94-B03` | El alias/tool trace no prueba la identidad real del servidor MCP ni existe bridge determinista congelado | Advisors podrian apuntar a otro proyecto o depender de interpretacion LLM | Atestar sesion project-scoped/read-only, feature/tool allowlist y bridge exacto; si no puede probarse sin tool adicional, F9.4 sigue bloqueada |
| `F94-B04` | `information_schema` filtra por privilegios y validators ACL aceptan subconjuntos/filas cero | Un inventario parcial o vacio podria pasar | Contrato sucesor debe usar inventario completo y exigir igualdad bidireccional/presencia de grants |
| `F94-B05` | F9.3 no liga conjuntamente SQL, MCP, target artifact, adapter policy y consumo one-shot | Riesgo de confusion cross-plane o replay de autorizacion | Artifact privado de schema cerrado, hashes en Gate R y marcador atomico single-use |

Referencia oficial de `F94-B01`: [Removing access to OpenAPI spec via anon key](https://supabase.com/changelog/42949-breaking-change-removing-access-to-openapi-spec-via-the-anon-key). La alternativa Management API anunciada alli no satisface path, auth class ni transport F9.3 y no puede sustituirse silenciosamente. La aceptacion humana de un FAIL conocido solo podria autorizar un diagnostico separado; no habilita `ADAPTER_AUTHORIZABLE` ni completa F9.4.

## Gates Y Autorizaciones

### Gate D - Definicion

Esta nota, estado, tarea, changelog e indice deben pasar Context Graph, auditorias, CI, review y merge. Gate D reconstruye tambien commit/tree/blob F9.3 desde historia completa. El merge conserva `DEFINED_BLOCKED` y no autoriza ejecucion.

### Gate C - Compatibilidad Contractual

Resolver B01/B02/B04 exige una decision humana y un PR puramente documental que defina un contrato sucesor local sin reescribir F9.3. Gate C asigna ID y SHA-256 al sucesor, fija operaciones/conteos/traces/evidence aplicables y actualiza el template Gate R. Gate C no implementa adapter, no carga secrets y no conecta. Mientras ese PR no sea aprobado/fusionado y B03/B05 no tengan diseno verificable, F9.4 no puede pasar a `ADAPTER_AUTHORIZABLE`.

### Gate A - Adapter Local

Solo despues de resolver documentalmente `F94-B01` a `F94-B05` y cambiar la definicion a `ADAPTER_AUTHORIZABLE`, la frase exacta `Ejecuta las tareas pendientes de la Fase F9.4` puede autorizar el adapter/policy y pruebas sinteticas locales. Ese gate no autoriza red ni secrets.

### Gate R - Ejecucion Remota

Despues de CI, auditorias, review, merge y replay local del adapter se requiere otra autorizacion exacta F9.4 con binding operativo:

```text
Ejecuta las tareas pendientes de la Fase F9.4
authorization_nonce=<64-lower-hex>
target=free
capability=REMOTE_READ_FREE
package_id=F8-HITO1-FUNCTIONAL-20260725
base_contract_id=F9.3-FREE-PREFLIGHT-CONTRACT-20260725
effective_contract_id=<Gate-C-approved-id>
effective_contract_sha256=<64-hex>
candidate_commit=<40-hex>
candidate_tree=<40-hex>
adapter_policy_sha256=<64-hex>
target_identity_artifact_sha256=<64-hex>
cross_plane_binding_sha256=<64-hex>
sql_endpoint_identity_sha256=<64-hex>
mcp_project_identity_sha256=<64-hex>
window_start_utc=<ISO-8601>
window_end_utc=<ISO-8601>
attempts=1
```

`cross_plane_binding_sha256` cubre target artifact, adapter policy, SQL identity, MCP identity y nonce. `sql_endpoint_identity_sha256` cubre host, port, database, rol efectivo y digests de atributos/memberships/TLS, nunca DSN raw. `mcp_project_identity_sha256` cubre server/session attestation, `read_only`, feature/tool allowlist y target project digest, nunca token/ref raw.

Sin todos los campos exactos, o con ventana vencida, no se conecta. Gate A no puede reutilizarse como Gate R. Antes de cargar secrets o abrir sockets, el coordinator crea con `O_CREAT|O_EXCL`, modo `0600`, el marcador `.context/artifacts/private/f9_4/authorizations/<nonce>.consumed.json`, ligado al digest canonico de Gate R y sin secrets. Se retiene hasta F11; si existe, se pierde o no puede verificarse, el nonce se considera consumido permanentemente. Todo abort posterior al marker consume la autorizacion, aunque no haya comenzado red, y cambiar `run-id` no concede otro intento.

## Stop Conditions

Antes de red: blocker abierto; drift F9.3; Git sucio/incompleto; adapter no aprobado; target artifact ausente; variables faltantes/extras/genericas/reutilizadas; DSN no ligado o privilegiado; TLS no verificable; MCP binding ambiguo; ventana invalida; attempts distinto de uno; path de evidencia ya existente; secrets detectados.

Durante: query de catalogo distinta del SELECT congelado; statement de control fuera de los seis comandos exactos; metodo HTTP distinto de GET; RPC o invocacion de `exec_sql`; COMMIT; redirect; timeout; total/orden/cursor/offset inestable; truncamiento; pagina terminal ausente; shape/cardinality invalida; bytes agregados por query/transport/ejecucion o cualquier limite numerico excedido; log o persistencia raw; proyecto tool distinto; acceso Pro; rollback no confirmado.

Despues: trace/envelope invalido; digests/counts incongruentes; material raw persistido; attestation/T01/status/schema unlock; dispatch o mutacion. Cualquier stop produce abort o FAIL fail-closed y bloquea F9.5.

## Allowlist Futura De Implementacion

- `db/manifests/f9_4_remote_adapter_policy.json`: policy de transportes/limites/bindings; no duplica ni sobreescribe F9.3.
- `scripts/maintenance/free_preflight_remote.py`: adapter separado sin primitives genericas.
- `tests/test_fase09_4_remote_free.py`: pruebas sinteticas/adversariales sin secrets ni red.
- `.github/workflows/security-audit.yml`: job local aditivo; el job F9.3 permanece sin cambios funcionales.
- Dependencia de driver PostgreSQL solo si la revision demuestra que no existe una version fijada reutilizable.
- Esta nota, estado, tarea, indice, changelog y documentacion de cierre F9.4.

Todo otro path queda excluido. La evidencia privada futura no se versiona y los hashes sanitizados se registran solo durante el cierre autorizado.

Gate A debe probar en fixtures de frontera el marker single-use, digests incrementales, limites de memoria/bytes/paginas y mapping a failure codes, incluido abort limpio sin red.

## Criterio De Salida

F9.4 solo pasa a `COMPLETED` tras resolver blockers, fusionar/revisar adapter, ejecutar un unico preflight autorizado desde commit/tree aprobado, validar evidence/traces, obtener auditorias GO y fusionar el cierre documental. El package permanece `reconciled_not_certified`, Free/Pro siguen bloqueados y attestations permanecen en cero. F9.5 requiere definicion y autorizacion independientes.
