# F10.9 G5 - Contrato Offline GET-Only V2.1

| Campo | Valor |
|---|---|
| Subfase | `F10.9` |
| Estado | `REMEDIATED_REPOSITORY_ONLY_V2_1_TRUST_STOP` |
| Contrato | `f10.9-g5-get-only-adapter-contract.v2.1` |
| Schema | `f10.9-g5-get-only-adapter-schema.v2.1` |
| Algoritmo | `f10.9-g5-get-only-adapter-v2.1` |
| Fuente protegida | `desarrollo@c7783af918c4e434d31b80e9a65247329c0b3595` |
| Tree protegido | `37d4ab05738355436169188d2613f860c6b35148` |
| Gate G5 | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Resultado repository-only | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| Connected mode | `STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED` |
| Conexiones/probes | `ZERO_NOT_IMPLEMENTED` |

## Reconciliacion PR 380

PR #380 fue aprobado, fusionado y verificado sobre:

```text
merge = c7783af918c4e434d31b80e9a65247329c0b3595
tree = 37d4ab05738355436169188d2613f860c6b35148
parent_1 = c28e5b86e6be29bbb2444bedd9b9407d1e7b0974
parent_2 = 6ff5e2b2e402a82842d51b5b3ec5b7c69b7713e3
security_audit_post_merge = 31848341499=PASS
f9_7_post_merge = 31848341110=PASS
result = MERGED_POST_MERGE_CI_PASS_REMEDIATION_REQUIRED
```

El contrato v2 queda congelado como
`HISTORICAL_ANTECEDENT_NOT_FIT_FOR_CONNECTED_MODE`. No puede reinterpretarse
silenciosamente. Todo sucesor debe usar versiones de contrato, schema y algoritmo
v2.1 o posteriores y una autorizacion separada. V1 permanece congelado por la
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
                 <= evaluated_at < target.expires_at
```

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

`SourceObservationEvidence.observed_at` se conserva solo como alias verificable:
debe coincidir exactamente con `ended_at_utc` del ultimo intento. No sustituye la
evidencia de inicio/fin ni puede ocultar un intento fuera de intervalo. Ademas,
`evaluated_at` debe ser posterior o igual al cierre completo mas tardio de
`snapshot_2`, no solo a su inicio. El request se valida por
tipo exacto antes de leer `method_sequence`; un tipo incorrecto produce
`G5AdapterContractError(STOP_G5_TARGET_BINDING_INVALID)`, nunca un error incidental.

La unidad de cada source observation es el par profile/source. No se asocia
artificialmente a un course: un profile elegible puede tener su fuente observada
sin crear identidad de curso. Este candidate exige exactamente un par
profile/source por perfil elegible; un segundo source para el mismo perfil no se
agrega ni se confunde con otro curso, sino que detiene el contrato para exigir un
schema sucesor explicito. La cobertura se deriva mecanicamente de las filas exactas de
`institution_site_profiles`: son elegibles solo perfiles con
`discovery_enabled=true`, `pipeline_enabled=true`, `pipeline_ready=true` y
`circuit_open=false`. Debe existir exactamente un bundle por fingerprint de perfil
elegible; duplicados, faltantes o extras terminan fail-closed sin ejecutar probes.

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
actuales. La cohorte primaria contiene
todos los cursos activos en `snapshot_1`; un inactivo solo entra con antecedente
exact-one atribuible.

Cada `FG3HistoricalObservationEvidence` liga target, snapshot pair, curso, run,
categoria, estado activo, `observed_at` UTC y fingerprint recomputable. Debe estar
dentro del target y antes del inicio de `snapshot_1`. El antecedente de un curso
inactivo incluye `antecedent_observed_at`, mutation kind y mutation fingerprint
recomputable; tambien debe preceder `snapshot_1`. Todo fallo de orden temporal usa
`STOP_G5_CLOCK_TIMING_INVALID`.

Antes de comparar cualquier fila `courses`, v2.1 exige
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

La proyeccion publica cerrada contiene solo version, decision, reason code y flags
falsos. Excluye URLs, hosts, UUID, institution IDs, payload/rows, project ref,
response bodies y secretos. Metadata/H2-CA2, syllabus/objectives, providers
editoriales, backfill y re-enrichment siguen excluidos.

`collect_g5_connected` permanece byte-intacto y termina antes de inspeccionar sus
argumentos con `STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED`. Este contrato no crea
workflow, environment, gate, secret, adapter o transporte, y no accede a
Production, Free, Pro o Certification.
