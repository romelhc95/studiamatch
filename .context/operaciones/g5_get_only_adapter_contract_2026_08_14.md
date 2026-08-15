# F10.9 G5 - Contrato Offline GET-Only V2.2

| Campo | Valor |
|---|---|
| Subfase | `F10.9` |
| Estado | `REMEDIATED_REPOSITORY_ONLY_V2_2_TRUST_STOP` |
| Contrato | `f10.9-g5-get-only-adapter-contract.v2.2` |
| Schema | `f10.9-g5-get-only-adapter-schema.v2.2` |
| Algoritmo | `f10.9-g5-get-only-adapter-v2.2` |
| Fuente protegida | `desarrollo@c998b0293b364b1c59d9c52824178927977f0b56` |
| Tree protegido | `d93843d4e08dfd9c45571b72040994926dffc221` |
| Gate G5 | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Resultado repository-only | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| Connected mode | `STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED` |
| Conexiones/probes | `ZERO_NOT_IMPLEMENTED` |

## Reconciliacion PR 381

PR #381 fue aprobado, fusionado y verificado sobre:

```text
merge = c998b0293b364b1c59d9c52824178927977f0b56
tree = d93843d4e08dfd9c45571b72040994926dffc221
parent_1 = c7783af918c4e434d31b80e9a65247329c0b3595
parent_2 = 51c24af3664a5d03ad16e16fa8793862cdb7fec1
security_audit_post_merge = 31852148318=PASS
f9_7_post_merge = 31852148322=PASS
result = MERGED_POST_MERGE_CI_PASS_REMEDIATION_REQUIRED
```

El contrato v2.1 queda congelado como
`HISTORICAL_ANTECEDENT_NOT_FIT_FOR_CONNECTED_MODE`. No puede reinterpretarse
silenciosamente. Todo sucesor debe usar versiones de contrato, schema y algoritmo
v2.2 o posteriores y una autorizacion separada. V2 y v1 permanecen congelados por la
reconciliacion anterior y no se reabre.

## Modelo De Confianza

`AuthorizationRequest` contiene solo dataclasses congeladas y tuples con datos ya
materializados. Cada fila usa `FrozenRow`: una tuple exacta y ordenada de pares
exactos `(str, immutable_value)`, donde `immutable_value` solo puede ser un builtin
exacto `None`, `str`, `bool`, `int` o una tuple recursiva con las mismas reglas. No
se aceptan `Mapping`, dicts, listas, subclasses, propiedades ni objetos arbitrarios
en evidencia de autorizacion. No contiene provider, `Protocol`, callback, factory, transport,
gate, credential, nonce ni objeto ejecutable aportado por caller. La autorizacion:

- nunca ejecuta providers o callbacks;
- nunca inspecciona propiedades arbitrarias;
- no usa `runtime_checkable` ni checks `isinstance` contra `Protocol`;
- valida identidad e independencia declaradas mediante
  `ManifestBuilderEvidenceReceipt` y `AnchorProviderEvidenceReceipt` exactos;
- trata hashes y receipts sin firma solo como evidencia de estructura e
  integridad, nunca como aprobacion, autoridad, disponibilidad o consumo.

No se modelan `GateAttestation`, `CredentialAvailabilityAttestation` ni nonce como
evidencia confiable. Este candidate no puede establecer autoridad. Tras completar
todos los controles puros retorna obligatoriamente:

```text
decision = STOP
next_step = STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED
reason = STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED
authorization_complete = false
transport_created = false
```

Un sucesor separado debera implementar, sin que este documento lo conceda:

- verificador de autoridad confiable;
- consumo atomico single-use del gate;
- ledger de replay de nonce;
- identidad de environment y run;
- firma o proof no forjable.

## Orden Estructural

Los controles se ejecutan antes del STOP de confianza y en este orden:

1. SHA/tree protegidos;
2. workflow/environment;
3. target binding;
4. capability exacta;
5. paginacion y doble snapshot;
6. observaciones de fuente y cobertura de perfiles elegibles;
7. evidencia lifecycle ligada a todas las filas `processing`;
8. manifest, anchor y receipts;
9. cohorte FG3 y provenance historica;
10. trust verification no implementado.

La ventana temporal vinculante es exactamente:

```text
target.issued_at <= manifest.issued_at <= anchor.issued_at
                 < snapshot_1_started_at
                 <= evaluated_at < target.expires_at
```

La causalidad FG3 completa agrega:

```text
target.issued_at <= max(historical_observations.observed_at)
                 <= manifest.issued_at
                 <= anchor.issued_at
                 < snapshot_1_started_at
```

Todos esos timestamps permanecen dentro del target binding. La igualdad
observacion/manifest y manifest/anchor es valida; el anchor nunca puede coincidir
con el inicio del primer snapshot.

Manifest o anchor futuros, expirados o fuera del binding terminan
`STOP_G5_CLOCK_TIMING_INVALID`.

## Doble Snapshot Y Observaciones

Las seis tablas pueden leerse en paralelo dentro de cada snapshot. La separacion
entre bloques es estricta:

```text
snapshot_1 completo -> observaciones -> snapshot_2 completo
```

Cada metodo de `method_sequence` exige exactamente un `SourceAttemptTiming`
inmutable con metodo, inicio/fin UTC e inicio/fin monotonic. Los intentos deben
aparecer en el mismo orden, ser secuenciales y no solaparse. Cada operacion
completa empieza despues del cierre UTC y monotonic global de `snapshot_1`,
termina antes del inicio UTC y monotonic global de `snapshot_2`, queda dentro de
`target.issued_at/expires_at` y termina antes o en `evaluated_at`.

Duraciones UTC y monotonic deben ser positivas, no exceder el presupuesto fijo de
15 segundos y diferir como maximo
`CLOCK_DURATION_TOLERANCE_NS=250000000`. Cualquier cruce, overlap, desorden,
duracion cero/negativa/excesiva, cantidad distinta de timings o incoherencia usa
exclusivamente `STOP_G5_CLOCK_TIMING_INVALID`.

La gramatica cerrada acepta solamente `HEAD, GET`, `HEAD, HEAD, GET` y
`HEAD, GET, GET`, con maximo tres intentos totales. El HEAD o GET repetido es un
retry. `GET` solo, `HEAD` solo, `GET -> HEAD`, alternancias posteriores, cuatro
intentos y cualquier otra secuencia se rechazan fail-closed.

`SourceObservationEvidence.observed_at` se conserva solo como alias verificable:
debe coincidir exactamente con `ended_at_utc` del ultimo intento. No sustituye la
evidencia de inicio/fin ni puede ocultar un intento fuera de intervalo. Ademas,
`evaluated_at` debe ser posterior o igual al cierre completo mas tardio de
`snapshot_2`, no solo a su inicio. El request se valida por
tipo exacto antes de leer `method_sequence`; un tipo incorrecto produce
`G5AdapterContractError(STOP_G5_TARGET_BINDING_INVALID)`, nunca un error incidental.

La unidad de cada source observation es el par profile/source. No se asocia
artificialmente a un course: un profile elegible puede tener su fuente observada
sin crear identidad de curso. V2.2 deriva mecanicamente cada source fingerprint
desde el fingerprint del perfil y su configuracion inmutable completa:
`discovery_mode`, `seed_urls`, `catalog_url_patterns` y `allowed_url_patterns`.
Cada entrada configurada produce un source distinto ligado a su tipo. El conjunto
observado debe ser exactamente el conjunto profile/source derivado; fuentes
arbitrarias, faltantes, duplicadas, extras o cruzadas entre perfiles terminan
fail-closed sin ejecutar probes.
La derivacion queda acotada a `64` fuentes por perfil y `50000` pares globales;
exceder cualquiera de esos limites termina `STOP_G5_TARGET_BINDING_INVALID`
antes de materializar el conjunto ampliado.

`pipeline_enabled` es el gate primario. Solo cuando es `None` se usa
`pipeline_ready` como fallback explicito. `pipeline_enabled=false` nunca cae a
`pipeline_ready=true`. `pipeline_enabled` admite exclusivamente `bool | None` y
`pipeline_ready` exclusivamente `bool`; enteros, strings y subclasses se
rechazan. Ademas se exige `discovery_enabled=true` y `circuit_open=false`.

Count inicial/final distinto produce `STOP_G5_COUNT_DRIFT`. Inventario truncado,
duplicado, desordenado o incompleto produce solo
`STOP_G5_PAGINATION_INCOMPLETE`. Contenido distinto entre snapshots con el mismo
count produce `STOP_G5_SNAPSHOT_CONTENT_DRIFT`.
Un count estable superior a la capacidad declarada es inventario incompleto y
produce `STOP_G5_PAGINATION_INCOMPLETE`, no `STOP_G5_COUNT_DRIFT`.

Todos los enteros rechazan `bool`: limites, retries, attempts, counts y valores
monotonic. La duracion UTC y monotonic debe diferir como maximo
`CLOCK_DURATION_TOLERANCE_NS=250000000` (250 ms); excederla produce
`STOP_G5_CLOCK_TIMING_INVALID`.

## Manifest Y Cohorte FG3

El manifest completo exige fingerprints unicos y conteos exactos `24/2/1`, sin
contar duplicados. No exige una observacion historica diferente por curso activo:
varias observaciones validas pueden ligarse al mismo curso activo cuando sus
fingerprints son unicos y el manifest las requiere. Esta multiplicidad pertenece
al manifest historico FG3 y no cambia la unidad profile/source de observaciones
actuales. La cohorte enumera todos los cursos de `snapshot_1`. Para cada curso
inactivo exige exactamente una `FG3PriorMutationEvidence`; exact-one se deriva
contando evidencia inmutable y no existe un booleano autocertificado.

Cada `FG3HistoricalObservationEvidence` liga target, snapshot pair, curso, run,
categoria, estado activo, `observed_at` UTC y fingerprint recomputable. Debe estar
dentro del target y antes del inicio de `snapshot_1`. El antecedente de un curso
inactivo liga course fingerprint, antecedent run, antecedent timestamp,
`DEACTIVATION`, mutation fingerprint recomputable y una observacion historica
`DEACTIVATION` del mismo curso/run/timestamp. Mutaciones faltantes, duplicadas,
extras, de cursos activos, ajenos o no relacionadas terminan
`STOP_G5_MANIFEST_ANCHOR_MISMATCH`. Todo fallo temporal usa
`STOP_G5_CLOCK_TIMING_INVALID`.

Antes de comparar contenido entre snapshots, v2.2 exige
`type(is_active) is bool` en ambos snapshots. `0`, `1` y cualquier otro entero se
rechazan como `STOP_G5_MANIFEST_ANCHOR_MISMATCH`; nunca se interpretan como
`False` o `True`.

## Lifecycle Completo

Cada fila `staging_raw` cuyo status exacto es `processing` exige exactamente un
`LifecycleEvidence` ligado al fingerprint de fila y un proxy recomputable. No se
permiten duplicados, faltantes ni extras. Los campos crudos
`last_harvested_at`/`created_at` son exclusivamente `str | None`; no se coercionan
objetos. Se conserva el fallback, el limite stale de siete dias,
`AGE_UNKNOWN`, `FUTURE_TIMESTAMP` y el rechazo de PASS forjado.

## Errores Malformados

Todos los validators y digest helpers publicos validan primero tipos exactos y
estructuras anidadas. Inputs top-level o nested malformados producen un
`G5AdapterContractError` estable del dominio correspondiente, nunca
`TypeError`, `ValueError` o `AttributeError`. Esta prevencion por tipos inmutables
evita ejecutar metodos especiales de objetos hostiles; no se atrapan excepciones
de caller ni se usa un catch amplio para ocultarlas.

UTC exige el singleton `timezone.utc`; un `tzinfo` suministrado por caller se
rechaza sin invocarlo. Cada valor inmutable queda limitado a profundidad `8`,
`256` nodos, strings de `8192` bytes e integers signed de 64 bits antes de hashing
o serializacion. Exceder cualquier limite produce el reason code estable del
dominio y evita `RecursionError`, conversiones gigantes o ejecucion indirecta.
Una instancia de dataclass de clase exacta con cualquier campo ausente se rechaza
antes de leer atributos de negocio. El chequeo usa exclusivamente el estado
incorporado de clases exactas conocidas; no usa `getattr`, `hasattr`, `Protocol`,
callbacks, hooks ni propiedades aportadas por caller.

## Capability Y Privacidad

La capability cerrada permite exclusivamente `select` y `count` sobre las seis
proyecciones existentes, columnas exactas, keyset `id.asc`, maximo 1000 filas por
pagina, 50000 filas, 50 paginas, 15 segundos, dos retries y 32 MB por snapshot.
No existe implementacion de lectura.

El check CI `F10.9 G5 GET-Only Contract V2.2` ejecuta la suite focused tanto en
el candidate como en el push post-merge a `desarrollo`. El job F9.7 depende de
este resultado y solo despues cambia al checkout historico congelado F9.7. Antes
de importar codigo candidato instala dependencias desde el commit F9.7 congelado,
bloquea egress con el guard congelado y ejecuta como UID/GID sin privilegios,
capabilities ni environment heredado sobre un workspace read-only. El cleanup de
firewall es obligatorio incluso ante fallo.

La proyeccion publica cerrada contiene solo version, decision, reason code y flags
falsos. Excluye URLs, hosts, UUID, institution IDs, payload/rows, project ref,
response bodies y secretos. Metadata/H2-CA2, syllabus/objectives, providers
editoriales, backfill y re-enrichment siguen excluidos.

`collect_g5_connected` permanece byte-intacto y termina antes de inspeccionar sus
argumentos con `STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED`. Este contrato no crea
workflow, environment, gate, secret, adapter o transporte, y no accede a
Production, Free, Pro o Certification.
