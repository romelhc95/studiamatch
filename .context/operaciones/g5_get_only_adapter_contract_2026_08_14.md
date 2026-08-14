# F10.9 G5 - Contrato Offline Del Futuro Adapter GET-Only

| Campo | Valor |
|---|---|
| Subfase | `F10.9` |
| Estado | `PREPARED_REPOSITORY_ONLY_REVIEW_PENDING` |
| Contrato | `f10.9-g5-get-only-adapter-contract.v1` |
| Schema | `f10.9-g5-get-only-adapter-schema.v1` |
| Algoritmo | `f10.9-g5-get-only-adapter-v1` |
| Fuente protegida | `desarrollo@bfdeb34c82d3e2fc4545b36f384436ff96ef1cb3` |
| Tree protegido | `dabf61ced4012419c4cd9f688506b4fe77e613dd` |
| Gate G5 | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Connected mode | `STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED` |
| Conexiones/probes | `ZERO_NOT_IMPLEMENTED` |

## Base Reconciliada

PR #378 congelo G5 v2 como `COMPLETED_POST_MERGE_VERIFIED`. El candidate
`9dbf6171a340fc0ca3905369f73d99e1056ffee9` fue integrado mediante merge
protegido:

```text
merge = bfdeb34c82d3e2fc4545b36f384436ff96ef1cb3
tree = dabf61ced4012419c4cd9f688506b4fe77e613dd
parent_1 = 4bb7f6d93a269879a3d73f39a5c71919ac2ea7d5
parent_2 = 9dbf6171a340fc0ca3905369f73d99e1056ffee9
security_audit_post_merge = 31824928169=PASS
f9_7_post_merge = 31824928240=PASS
```

Candidate y merge tienen tree identico. Esta identidad es la unica fuente
protegida permitida por el contrato offline. No crea target real, payload
privado, workflow, environment, gate, secret, transport ni acceso Production.

## Trust Model Y Target Binding

El futuro target binding privado debe contener y ligar como una sola identidad:

- environment exacto esperado `Production`;
- protected source SHA y tree exactos;
- versiones de contrato, schema y algoritmo;
- workflow exacto futuro;
- run ID opaco;
- `issued_at` y `expires_at` UTC;
- `snapshot_pair_id`;
- payload digest;
- manifest digest;
- historical anchor digest.

Todos los IDs de integridad son `sha256:<64 hex>`. Los fingerprints demuestran
integridad y atribucion, no anonimato. El target binding se calcula sobre el
objeto canonico completo. No se versiona ningun binding real ni material privado
en este candidate.

La autorizacion futura es fail-closed y conserva este orden exacto:

1. gate exacto `APPROVED_NOT_CONSUMED`, ligado a authority, target, run, nonce,
   issued/expires, estado no consumido y digest recalculado;
2. ejecucion desde SHA/tree protegidos;
3. workflow y environment permitidos;
4. target binding valido;
5. payload, manifest y anchor digests coincidentes;
6. ventana UTC no expirada;
7. capability exacta GET-only;
8. atestacion opaca de disponibilidad de credencial, ligada a authority,
   target/run y ventana, sin leer valores;
9. creacion del transporte al final.

El paso 9 no existe en este candidate. La salida offline conserva
`authorization_complete=false`, `independent_execution_verification_required=true`,
`transport_created=false` y `next_step=STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED`.
Una atestacion sintetica valida el orden, pero nunca equivale a autorizacion
operativa ni puede alimentar un transporte.
La autorizacion consume obligatoriamente el envelope de doble snapshot, el
manifest builder y el anchor provider como objetos runtime distintos; no acepta
un anchor construido fuera de ese binder independiente.
La funcion de autorizacion no acepta factory, transport, environment reader,
secret value ni credential object. Por ello no puede inspeccionarlos antes de
completar los controles puros. La atestacion de disponibilidad solo declara un
booleano y prohibe inspeccion de valores secretos.

## Capability Contract

La capability exacta contiene unicamente `select` y `count`. Rechaza cualquier
capacidad adicional, especialmente `insert`, `update`, `upsert`, `patch`,
`delete`, `rpc`, `execute` y `mutate`.

Las tablas y columnas privadas son las mismas seis proyecciones cerradas de G5
v2: `institutions`, `institution_site_profiles`, `staging_raw`,
`cleansed_programs`, `enriched_programs` y `courses`. Cada query declara:

- columnas exactas allowlisted;
- filtros vacios explicitos para el inventario completo;
- keyset pagination estable `id.asc`, con `id` como cursor y desempate unico;
- page size maximo `1000`;
- maximo `50000` filas y `50` paginas por tabla;
- maximo `32000000` bytes por snapshot;
- timeout maximo `15` segundos;
- retry budget maximo `2`.

No hay implementacion de SELECT/count ni cliente que pueda ejecutarlos. El
contrato valida evidencia sintetica ya materializada.

## Paginacion Y Count

Cada lectura futura requiere count inicial, paginas y count final, con timing para
los counts. Cada pagina liga `after_id`, limit, page digest, filas privadas,
cursores ordenados, fingerprints de fila y timing real. Row digest, page digest e
inventory digest se recalculan desde material canonico y target/pair. El validador
offline exige:

- continuidad keyset desde `after_id=null` al ultimo ID de la pagina anterior;
- orden estable y desempate sin colisiones;
- page digests no repetidos;
- fingerprints de fila unicos entre todas las paginas;
- total materializado igual al count inicial;
- count inicial igual al final;
- limites de filas, paginas y page size respetados;
- cero paginas para count cero;
- ninguna pagina vacia antes de completar el inventario.
- bytes canonicos acumulados bajo el limite del snapshot.

Pagina repetida, fila duplicada, hueco, truncamiento o total incompleto termina
`STOP_G5_PAGINATION_INCOMPLETE`. Drift de count termina `STOP_G5_COUNT_DRIFT`.
Nunca se acepta truncamiento silencioso ni se publica un inventario parcial.

Un envelope superior exige exactamente las seis tablas en `snapshot_1` y
`snapshot_2`, valida cada inventario, suma bytes a nivel snapshot, exige igualdad
exacta de fingerprints por tabla y recalcula un payload digest global. Ese digest
debe ser el del target. Count estable sin doble inventario identico no acredita
estabilidad. Todos los timings del primer snapshot deben terminar estrictamente
antes del inicio de cualquier timing del segundo, tanto en UTC como monotonic;
reutilizar el mismo read evidence para ambos lados termina STOP.

## Clock Y Timing

Cada count y pagina captura timestamp inmediatamente antes e inmediatamente despues.
La fuente declarada es `SYSTEM_UTC_PLUS_MONOTONIC`: wall clock timezone-aware
UTC para evidencia y clock monotonic para orden/duracion. Cada timing liga el
`snapshot_pair_id` y exige:

```text
IMMEDIATELY_BEFORE_READ < IMMEDIATELY_AFTER_READ
monotonic_started_ns < monotonic_ended_ns
```

Naive datetimes, offsets no UTC, igualdad/inversion temporal, operaciones
solapadas/desordenadas, timeout excedido, clock source distinto o pair mismatch
terminan `STOP_G5_CLOCK_TIMING_INVALID`.

## HistoricalFG3AnchorProvider

`HistoricalFG3AnchorProvider` es una interfaz offline independiente del manifest
suministrado por el collector. Su atestacion debe ligar provenance
`INDEPENDENT_HISTORICAL_FG3_SOURCE`, candidate SHA/tree, run ID, manifest digest,
provider identity/instance, issued_at UTC y anchor digest recalculable.

El manifest declara separadamente builder identity/instance, candidate/run,
issued_at, digest recalculable, inventario exacto de observation fingerprints,
categoria por observacion, totales por categoria y `complete=true`. Builder y
provider no pueden compartir identity, instance ni objeto runtime. El provider
interface es consumido por un binder offline que rechaza el mismo objeto antes de
invocarlo. Un mismo objeto/actor declarado no puede construir el manifest y
acreditarlo como fuente independiente. Self-attestation termina
`STOP_G5_HISTORICAL_ANCHOR_NOT_INDEPENDENT`; desacuerdo de manifest, candidate,
run, provenance, timestamps o digest termina
`STOP_G5_MANIFEST_ANCHOR_MISMATCH`.

La independencia es un requisito de trust, no un booleano decorativo. El digest
del manifest y el anchor se recalculan y deben coincidir con target/candidate/run.
El inventario historico completo sigue siendo obligatorio para 24/2/1. El
manifest conserva explicitamente `published_count_tuple=(24,2,1)` y rechaza otra
cardinalidad publicada, categorias desconocidas por su propio contrato o drift
entre fingerprints, categorias y totales.

## SourceObservationProvider

`SourceObservationProvider` queda definido solo como interfaz offline, sin
implementacion. Su request/evidence liga:

- secuencia `HEAD`/`GET`, terminada en `GET`;
- attempts entre uno y tres;
- terminal reason cerrado;
- observed_at UTC;
- profile, source, run, cohort y snapshot-pair fingerprints.

Este candidate no instancia providers ni ejecuta HEAD/GET. La interfaz preserva
la atribucion de G5 v2 para una implementacion futura separada.

## Lifecycle Y Cohorte FG3

`last_harvested_at` y luego `created_at` permanecen proxies explicitos. Nunca se
renombran ni presentan como `processing_started_at`. Las clasificaciones exactas
siguen siendo `STALE`, `NOT_STALE`, `AGE_UNKNOWN` y `FUTURE_TIMESTAMP`. Ausencia,
timestamp invalido/no UTC o edad futura nunca produce PASS; solo una evidencia
`NOT_STALE` valida puede hacerlo.

La cohorte FG3 v2 no cambia:

- primaria: cursos activos en `snapshot_1`;
- inactivos: solo con antecedente exact-one atribuible;
- manifest historico independiente obligatorio para 24/2/1;
- historicos no relacionados excluidos.

El validador deriva mecanicamente cohortes primaria e inactiva desde las filas
canonicas de `courses` del envelope de ambos snapshots, exige todos los activos,
exact-one y antecedent run distinto para cada inactivo, impide reutilizar una
observacion entre cursos, rechaza evidencia no relacionada y reconcilia tanto
antecedentes inactivos como observaciones inconclusas activas contra el inventario
completo del manifest. Cada observacion historica adicional es un objeto ligado a
course fingerprint activo, run, categoria y observation fingerprint; listas de
digests sin atribucion no son aceptadas. `is_active` debe ser booleano estricto.

## Reason Codes Fail-Closed

El contrato agrega el siguiente vocabulario terminal privado:

```text
STOP_G5_TARGET_BINDING_INVALID
STOP_G5_PROTECTED_SOURCE_SHA_TREE_INVALID
STOP_G5_GATE_ABSENT_OR_NOT_APPROVED
STOP_G5_PAYLOAD_EXPIRED
STOP_G5_ADAPTER_CAPABILITY_INVALID
STOP_G5_PAGINATION_INCOMPLETE
STOP_G5_COUNT_DRIFT
STOP_G5_CLOCK_TIMING_INVALID
STOP_G5_HISTORICAL_ANCHOR_NOT_INDEPENDENT
STOP_G5_MANIFEST_ANCHOR_MISMATCH
STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED
```

Los reason codes no publican valores privados.

## Privacidad Y Frontera

Permanecen fuera de toda proyeccion publica URL/host, UUID, institution IDs,
filas, project ref, payloads, resultados individuales, response bodies y
secretos. El modulo no importa ni usa Supabase, requests/httpx/urllib, socket,
subprocess, db_client, clientes SQL o gestores de secrets.

La unica proyeccion construida por este contrato posee schema cerrado con
version, decision `STOP`, reason code, target digest y flags falsos de
authorization/transport; no acepta campos aportados por callers.

`collect_g5_connected` permanece byte-intacto y bloqueado antes de inspeccionar
authorization, factory, observations, binding o credenciales. No se crea
workflow, environment, gate, secret ni adapter de red. No se modifica Production,
Free, Pro, Certification o Main y no se ejecutan probes.

El siguiente paso se limita a review humano, merge protegido a `desarrollo` y
checks post-merge. Implementar el transporte conectado requiere otro candidate,
gate y autorizacion separados despues de verificar este contrato post-merge.
