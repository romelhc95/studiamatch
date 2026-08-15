# F10.9 G5 - Contrato Offline GET-Only V2.3

| Campo | Valor |
|---|---|
| Subfase | `F10.9` |
| Estado | `REPOSITORY_ONLY_TRUST_PLANE_PR_A_STOP` |
| Contrato | `f10.9-g5-get-only-adapter-contract.v2.3` |
| Schema | `f10.9-g5-get-only-adapter-schema.v2.3` |
| Algoritmo | `f10.9-g5-get-only-adapter-v2.3` |
| Fuente protegida | `desarrollo@9045c90ac78634f17a66cb3e30e723a2431cb6b4` |
| Tree protegido | `3d8455a29b63a38906a67343ee4ba6dd15b366d7` |
| Gate G5 | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Resultado repository-only | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| Connected mode | `STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED` |
| Conexiones/probes | `ZERO_NOT_IMPLEMENTED` |

## Reconciliacion PR 382 Y PR 383

PR #382 integro repository-only v2.2 y fue verificado sobre:

```text
candidate = 8a6724a5850792383456763a119c925c53961f2a
merge = 58e0a0b37f7a3795e9487ab01aa558b5ecaa6ae3
tree = 13eb0465233c9e870995763630ee9e6541a45add
security_audit_post_merge = 31861308128=PASS
f9_7_post_merge = 31861308133=PASS
focused = 94955078030=159 PASS
result = MERGED_POST_MERGE_CI_PASS_ROUTING_REMEDIATION_REQUIRED
```

El contrato v2.2 queda congelado como
`HISTORICAL_ANTECEDENT_NOT_FIT_FOR_CONNECTED_MODE`. No puede reinterpretarse
silenciosamente. Todo sucesor debe usar versiones de contrato, schema y algoritmo
v2.3 o posteriores y una autorizacion separada. V2.1, v2 y v1 permanecen congelados por la
reconciliacion anterior y no se reabre.

PR #383 promovio el sucesor repository-only v2.3 y quedo verificado sobre:

```text
candidate = b921ee90d3ea4966602c3ca4b12a740d3721baa7
merge = 9045c90ac78634f17a66cb3e30e723a2431cb6b4
tree = 3d8455a29b63a38906a67343ee4ba6dd15b366d7
security_audit_post_merge = 31896356316=PASS
f9_7_post_merge = 31896356280=PASS
focused_v2_3_post_merge = 95040164691=PASS
result = MERGED_POST_MERGE_VERIFIED
```

V2.3 queda congelado en `desarrollo@9045c90ac78634f17a66cb3e30e723a2431cb6b4`
/ tree `3d8455a29b63a38906a67343ee4ba6dd15b366d7`. Este PR A agrega solo el
control-plane de confianza repository-only. No acredita connected mode,
Production, transporte, autoridad operacional, approval remoto, gate consumido ni
lectura remota.

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

## Trust-Plane G5 PR A Repository-Only

El trust-plane futuro queda modelado por [ADR-0012](../decisiones/ADR-0012_trust_plane_g5_repository_only.md)
sin ejecutarse. `AuthorizationRequest` y cualquier payload caller-facing no pueden
contener autoridad, approval, credential, gate status, nonce consumido, proof,
`run_id`, `deployment_id`, SHA o digests aislados como autoridad. Esos valores se
aceptan solo como evidencias inmutables ligadas entre si y validadas offline.

Estructuras inmutables nuevas:

- `GateIntent`.
- `GitHubOidcClaims`.
- `WorkflowRunEvidence`.
- `EnvironmentEvidence`.
- `ApprovalEvidence`.
- `DeploymentEvidence`.
- `GateConsumptionReceipt`.

Bindings obligatorios futuros:

- `repository_id` y `owner_id` numericos.
- ref exacta `refs/heads/main` y ref protegida.
- candidate SHA/tree congelados.
- workflow path/ref/SHA/blob.
- `run_id`, `run_attempt=1`, check run y job identity.
- environment `Production` por nombre e ID.
- `deployment_id` ligado al mismo SHA/ref/environment.
- `actor` y `triggering_actor` numericos.
- approver numeric ID distinto del iniciador; login por si solo no es autoridad.
- digests de contrato, schema, algoritmo y capability.
- `issued_at/expires_at` y `nonce_digest` dentro de ventana valida.

OIDC futuro requiere issuer GitHub, audience dedicada, firma/JWKS verificados,
claims exactos, `jti` no reutilizado e intervalo temporal vigente. Rerun, partial
rerun o `run_attempt != 1` terminan STOP.

State machine del gate:

```text
READY -> CONSUMED
```

El consumo valido exige compare-and-set exacto para una sola identidad derivada de
`repository_id/run_id/run_attempt/check_run_id`. Cero, multiples, timeout o resultado
ambiguo terminan `STOP_G5_CONSUMPTION_AMBIGUOUS`. Un gate consumido permanece
consumido aunque el diagnostico posterior falle. Replay de nonce o `jti` termina
`STOP_G5_REPLAY_DETECTED`. Gate expirado termina `STOP_G5_GATE_EXPIRED`.

La interfaz cerrada de ledger queda limitada a `read_gate_intent`,
`compare_and_set_ready_to_consumed`, `record_jti_once`, `record_nonce_once` y
`return_consumption_receipt`. No hay proveedor ni implementacion remota en este PR.
Si GitHub deployment/approval no demuestra atomicidad single-use, el contrato termina
`STOP_G5_ATOMIC_LEDGER_REQUIRED`; `deployment_id` o environment approval por si solos
no son ledger atomico. PR A no acepta un booleano, proof o provider caller-supplied
para saltar ese STOP.

El `workflow_ref` futuro usa formato OIDC repo-qualified: `romelhc95/studiamatch/.github/workflows/f9-7-contract.yml@refs/heads/main`.
`workflow_sha` y `workflow_blob_sha` quedan congelados como constantes esperadas en
el modelo repository-only, no como SHA arbitrarios aportados por caller. Los digests
de contrato, schema, algoritmo y capability se recomputan desde constantes del
repositorio. Approval queda ligado a `run_id`, `check_run_id`, `deployment_id`, SHA
y `workflow_sha`. Approval y receipt no pueden estar en el futuro respecto de
`evaluated_at`; timeout se representa como resultado no consumido y termina
`STOP_G5_CONSUMPTION_AMBIGUOUS`.

Reason codes separados del trust-plane:

- `STOP_G5_AUTHORITY_INVALID`.
- `STOP_G5_APPROVAL_INVALID`.
- `STOP_G5_BINDING_DRIFT`.
- `STOP_G5_REPLAY_DETECTED`.
- `STOP_G5_GATE_EXPIRED`.
- `STOP_G5_CONSUMPTION_AMBIGUOUS`.
- `STOP_G5_ATOMIC_LEDGER_REQUIRED`.
- `STOP_G5_PROOF_INVALID`.

Permisos futuros minimos: `contents:read`, `actions:read`, `deployments:read` e
`id-token:write`. Todo permiso `write` restante queda prohibido. El workflow futuro
sera manual-only, main-only y environment `Production`; no se crea en este PR.

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

Cada metodo de `method_sequence` exige exactamente un `SourceAttemptResult`
inmutable con metodo, inicio/fin UTC e inicio/fin monotonic. Los intentos deben
aparecer en el mismo orden, ser secuenciales y no solaparse. Cada operacion
completa empieza despues del cierre UTC y monotonic global de `snapshot_1`,
termina antes del inicio UTC y monotonic global de `snapshot_2`, queda dentro de
`target.issued_at/expires_at` y termina antes o en `evaluated_at`.

Duraciones UTC y monotonic deben ser positivas. Cada intento source, HEAD o GET,
tiene el mismo presupuesto fijo exacto de 15 segundos; la secuencia HEAD-GET no
convierte ese limite en 30 segundos para un intento individual. Deben diferir como maximo
`CLOCK_DURATION_TOLERANCE_NS=250000000`. Cualquier cruce, overlap, desorden,
duracion cero/negativa/excesiva, cantidad distinta de timings o incoherencia usa
exclusivamente `STOP_G5_CLOCK_TIMING_INVALID`.

La gramatica compatible con `safe_source_probe` acepta exclusivamente `HEAD` o
`HEAD, GET`. Un `HEAD` 2xx termina accesible; `403`, `405` o `501` exige el GET
acotado. `GET` solo, retries inventados, `GET -> HEAD`, mas de dos intentos y
cualquier otra secuencia se rechazan fail-closed. Este contrato describe los
resultados pre-materializados y no modifica `safe_source_probe`, preflight ni
workers.

`SourceObservationEvidence.observed_at` se conserva solo como alias verificable:
debe coincidir exactamente con `ended_at_utc` del ultimo intento. No sustituye la
evidencia de inicio/fin ni puede ocultar un intento fuera de intervalo. Ademas,
`evaluated_at` debe ser posterior o igual al cierre completo mas tardio de
`snapshot_2`, no solo a su inicio. El request se valida por
tipo exacto antes de leer `method_sequence`; un tipo incorrecto produce
`G5AdapterContractError(STOP_G5_TARGET_BINDING_INVALID)`, nunca un error incidental.

La decision de routing es causal respecto de las observaciones: cuando existen
bundles, `routing_observed_at` es `started_at_utc` del primer
`SourceAttemptResult` valido mas temprano, y el minimo UTC debe identificar el
mismo profile/source que el minimo monotonic. Si no existen bundles, usa el cierre
de `snapshot_1`; nunca usa por defecto ese cierre cuando ya existe un intento
source. Cualquier desacuerdo termina `STOP_G5_CLOCK_TIMING_INVALID`.

La unidad de cada source observation es el par profile/source. No se asocia
artificialmente a un course: un profile elegible puede tener su fuente observada
sin crear identidad de curso. V2.3 deriva `EffectiveProfileRouting` desde un join
exact-one profile/institution; profiles huerfanos, instituciones duplicadas,
profiles duplicados por institucion o cualquier cardinalidad distinta de uno
terminan `STOP_G5_PROFILE_ROUTING_INVALID`.

La elegibilidad exige `discovery_enabled=true`, gate de pipeline efectivo true y
un circuito no abierto de forma efectiva. La presencia de `pipeline_enabled` exige un bool exacto;
`null`, enteros, strings o subclasses son divergence blocker. Solo su ausencia
real permite fallback a `pipeline_ready`, tambien bool exacto. Esta distincion de
presencia/null forma parte del fingerprint y no cambia preflight ni workers.

La semantica de circuito replica el cooldown efectivo del harvester: con
`circuit_open=true`, `circuit_opened_at` UTC valido mantiene el circuito abierto
solo mientras su edad sea menor que 24 horas. Exactamente a 24h, y despues, queda
auto-closed y puede ser elegible; antes de 24h no produce probes. Timestamp
malformado o no UTC bloquea routing fail-closed.

Cuando `circuit_open=false`, `circuit_opened_at` queda dormido: se conserva
literalmente en el routing fingerprint, pero no se parsea, no altera elegibilidad
y no genera probes por si mismo. Solo `circuit_open=true` activa su interpretacion
temporal para el cooldown.

Los roles son cerrados: destinos efectivos `PROBE_TARGET`, templates
`TEMPLATE`, y allowed/exclusion patterns `FILTER`. Solo `PROBE_TARGET` produce
observaciones. La derivacion estatica por modo es:

- `hardcoded_urls`: seeds filtrados como `HARDCODED_DETAIL`;
- `paginated_catalog`: expansion `{page}` acotada como `CATALOG_PAGE`;
- `catalog_link_extraction`: seeds y website como `CATALOG_ROOT`;
- `sitemap_bfs`: website deriva `SITEMAP_ROOT` y `BFS_ROOT`;
- `WARMUP`: solo cuando browser, bypass y warmup configurado coinciden.

Website, sitemap roots, BFS roots y warmup son targets solo bajo esas reglas.
Configuracion dormida se incorpora al routing/source fingerprint, pero nunca se
convierte silenciosamente en target. Catalog links extraidos, nested sitemaps y
BFS children pertenecen al runtime dinamico FG2 y quedan fuera del scope
repository-only static-only de G5. La frontera no declara que esas fuentes
dinamicas sean inexistentes ni las sustituye por templates o filters.

Todas las URLs activas pasan por la canonicalizacion compartida de identidad URL;
userinfo, identidades sin host o canonical URL y URNs se rechazan. Seeds
hardcoded se deduplican por URL canonica conservando orden, y el conjunto final se
deduplica por `(kind, canonical_url)`: dos kinds sobre la misma URL siguen siendo
targets distintos. Allowed/exclusion con rol `FILTER` usa el literal contra la URL
canonica completa, sin truncarla. Para `re:`, el texto de busqueda se acota a 2000
caracteres (exclusion sobre URL, allowed sobre path). El regex se limita a 200
caracteres y usa un subset lineal conservador: rechaza toda agrupacion,
alternancia o cuantificador no escapado antes de compilar. Un escape final
incompleto tambien se rechaza.
`localhost`, subdominios `.localhost` y literales IP no globales se rechazan antes
de crear targets.

Un profile no elegible conserva y fingerprinta su configuracion, estado efectivo
de circuito y tiempo observado, pero deriva cero `PROBE_TARGET` y produce cero
observaciones/probes. Configuracion insegura necesaria para fingerprint seguro,
como regex hostil, sigue bloqueando fail-closed aun cuando el profile no sea
elegible.

Cada source fingerprint liga el routing inmutable completo, rol, kind, URL e
indice. El conjunto observado debe ser exactamente el conjunto profile/source
derivado; fuentes arbitrarias, faltantes, duplicadas, extras o cruzadas entre
perfiles terminan fail-closed sin ejecutar probes.
La derivacion admite como maximo `64` fuentes por perfil y `50000` pares globales.
Los primeros valores fuera de cota, `65` y `50001`, terminan exactamente
`STOP_G5_TARGET_BINDING_INVALID` antes de materializar el conjunto ampliado.

`pipeline_enabled` es el gate primario. Solo cuando la columna esta ausente se
usa `pipeline_ready` como fallback explicito. Presente con `null` es divergence
blocker; `pipeline_enabled=false` nunca cae a `pipeline_ready=true`. Ambos gates
admiten exclusivamente bool exacto; enteros, strings y subclasses se rechazan.
El preflight FG2 existente, en cambio, trata `pipeline_enabled=NULL` como fallback
legacy a `pipeline_ready`; v2.3 registra deliberadamente esa divergencia y STOP,
no la armoniza silenciosamente. Sus otras reglas de configuracion preflight
tampoco sustituyen la derivacion del routing efectivo del harvester. Este candidate
no modifica preflight ni workers.

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

## Outcomes Source Recomputables

Cada terminal source se recalcula exclusivamente desde los intentos cerrados;
una declaracion del caller no puede sustituirlo. Los status `2xx`, `404`, `410`,
`403`, `405`, `501`, transitorios y restantes se traducen respectivamente segun
la secuencia HEAD/HEAD-GET a `SOURCE_ACCESSIBLE`, `SOURCE_HTTP_404`,
`SOURCE_HTTP_410`, `SOURCE_ACCESS_403`, `SOURCE_TIMEOUT` o
`SOURCE_INACCESSIBLE`. Los errores `TIMEOUT`, `DNS_FAILURE`, `TLS_FAILURE`,
`TRANSPORT_FAILURE` y `UNSAFE_TARGET` producen sus reason codes source exactos.
Solo `SOURCE_ACCESSIBLE` es compatible con GO; todo otro terminal produce
`STOP_G5_SOURCE_BLOCKERS_PRESENT` antes del STOP de confianza.

La clasificacion contractual de redirect queda cerrada exactamente como
`NO_REDIRECT_WITHOUT_DERIVATION_EVIDENCE`: cada intento pre-materializado debe
declarar `NO_REDIRECT`; `SAME_ORIGIN_PUBLIC`, `OTHER_PUBLIC` o cualquier redirect
sin evidencia derivable se rechaza como `STOP_G5_TARGET_BINDING_INVALID`. La
ausencia declarada de redirect es evidencia estructural, no prueba no forjable,
autoridad, trust, disponibilidad ni consumo de gate.

El blocker source y el blocker lifecycle son dominios separados. Un terminal
source valido pero no accesible nunca se reclasifica como problema lifecycle, y
una fila processing stale/unknown/futura nunca se oculta bajo source access.

## Manifest Y Cohorte FG3

El manifest completo exige fingerprints unicos y conteos exactos `24/2/1`, sin
contar duplicados. No exige una observacion historica diferente por curso activo:
varias observaciones validas pueden ligarse al mismo curso activo cuando sus
fingerprints son unicos y el manifest las requiere. Esta multiplicidad pertenece
al manifest historico FG3 y no cambia la unidad profile/source de observaciones
actuales. La cohorte enumera todos los cursos de `snapshot_1`. Para cada curso
inactivo exige exactamente una `FG3PriorMutationEvidence`; exact-one se deriva
contando evidencia inmutable y no existe un booleano autocertificado.

Las formas y cardinalidades FG3 se acotan tempranamente: `category_counts` exige
exactamente `3` pares; `courses`, `prior_mutations` e `historical_observations`
admiten cada una como maximo `50000`. Manifest expected fingerprints y categories
quedan bajo la misma cota. Todo se valida por longitud antes de iterar, construir
sets o recalcular fingerprints; `50001` termina
`STOP_G5_MANIFEST_ANCHOR_MISMATCH` sin materializacion ampliada.

Cada `FG3HistoricalObservationEvidence` liga target, snapshot pair, curso, run,
categoria, estado activo, `observed_at` UTC y fingerprint recomputable. Debe estar
dentro del target y antes del inicio de `snapshot_1`. El antecedente de un curso
inactivo liga course fingerprint, antecedent run, antecedent timestamp,
`DEACTIVATION`, mutation fingerprint recomputable y una observacion historica
`DEACTIVATION` del mismo curso/run/timestamp. Mutaciones faltantes, duplicadas,
extras, de cursos activos, ajenos o no relacionadas terminan
`STOP_G5_MANIFEST_ANCHOR_MISMATCH`. Todo fallo temporal usa
`STOP_G5_CLOCK_TIMING_INVALID`.

Todas las observaciones historicas `DEACTIVATION` o `PRIOR_DEACTIVATION` quedan
sujetas a exact-one: cada una debe ser consumida por exactamente una prior mutation
del curso inactivo correspondiente, y cada curso inactivo requiere exactamente
una prior mutation. Observaciones deactivation no referenciadas, reutilizadas,
extras o ligadas a cursos activos bloquean el manifest.

Antes de comparar contenido entre snapshots, v2.3 exige
`type(is_active) is bool` en ambos snapshots. `0`, `1` y cualquier otro entero se
rechazan como `STOP_G5_MANIFEST_ANCHOR_MISMATCH`; nunca se interpretan como
`False` o `True`.

## Lifecycle Completo

Cada fila `staging_raw` cuyo status exacto es `processing` exige exactamente un
`LifecycleEvidence` ligado al fingerprint de fila y un proxy recomputable. No se
permiten duplicados, faltantes ni extras. Los campos crudos
`last_harvested_at`/`created_at` son exclusivamente `str | None`; no se coercionan
objetos. `last_harvested_at` es el primer proxy y `created_at` el fallback. El
limite stale es exactamente 24 horas: edad igual a 24h es `NOT_STALE` y 24h mas
un microsegundo es `STALE`. Se conservan `AGE_UNKNOWN`, `FUTURE_TIMESTAMP` y el
rechazo de PASS forjado. La salida compatible con GO exige que todas las filas
`processing` tengan evidencia exact-one recomputable y clasificacion
`NOT_STALE`; cualquier otra clasificacion produce
`STOP_G5_LIFECYCLE_BLOCKERS_PRESENT` por separado del source blocker.

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
pagina, 50000 filas, 50 paginas, 15 segundos y 32 MB por snapshot. El budget de
source es tambien 15 segundos por intento, pero es un dominio separado; la
gramatica source admite como maximo HEAD seguido de un unico GET, no dos retries.
No existe implementacion de lectura.

El check CI `F10.9 G5 GET-Only Trust Plane PR A` ejecuta la suite focused tanto en
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
Production, Free, Pro o Certification. Tampoco autoriza red, writers, schedules,
promocion a Certification/Main ni ninguna operacion en Main.
