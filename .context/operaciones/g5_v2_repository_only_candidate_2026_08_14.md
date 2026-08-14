# F10.9 G5 V2 - Atribucion Repository-Only

| Campo | Valor |
|---|---|
| Subfase | `F10.9` |
| Estado | `COMPLETED_POST_MERGE_VERIFIED` |
| Schema | `f10.9-g5-production-readonly-projection.v2` |
| Algoritmo | `f10.9-g5-production-readonly-v2` |
| Gate conectado | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Modo conectado | `STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED` |
| Base protegida | `desarrollo@30f77b88778372de112c6a8fb51a1344155db025` |
| Tree base | `b25fca6fc4e37db5b1e2c0e048748ee0ec3d839c` |

## Promocion Post-Merge

PR #377 fue aprobado y fusionado mediante el candidate
`2c211cf58ed0917e3e5e1255c189dcd6ca8ef976`. La identidad protegida verificada
es:

```text
merge = 4bb7f6d93a269879a3d73f39a5c71919ac2ea7d5
tree = 1daedcbe9651667201214eb4388e00024fa59bf3
parent_1 = 30f77b88778372de112c6a8fb51a1344155db025
parent_2 = 2c211cf58ed0917e3e5e1255c189dcd6ca8ef976
candidate_tree = 1daedcbe9651667201214eb4388e00024fa59bf3
security_audit_post_merge = 31820665170=PASS
f9_7_post_merge = 31820665257=PASS
```

Candidate y merge tienen contenido identico. El run F9.7 termino `success` sobre
el merge; G5 v2 queda `COMPLETED_POST_MERGE_VERIFIED`. Esta atestacion no crea,
aprueba ni consume el gate, no desbloquea connected mode y no acredita lecturas
de Production.

PR #378 congelo esta atestacion mediante candidate
`9dbf6171a340fc0ca3905369f73d99e1056ffee9` y merge protegido
`bfdeb34c82d3e2fc4545b36f384436ff96ef1cb3`, tree
`dabf61ced4012419c4cd9f688506b4fe77e613dd`, con parents
`4bb7f6d93a269879a3d73f39a5c71919ac2ea7d5` y candidate. Security Audit
`31824928169=PASS` y F9.7 `31824928240=PASS` verificaron el merge; candidate y
merge tienen tree identico. G5 v2 conserva el mismo estado, gate y STOP.

## Reconciliacion

El [candidate G5 v1](./g5_production_readonly_candidate_2026_08_14.md) queda
`COMPLETED_POST_MERGE_VERIFIED`: PR #376 integro candidate
`520b0fc3f039d279faadb102fa0f13f3725a58ee` mediante merge protegido
`30f77b88778372de112c6a8fb51a1344155db025`, tree
`b25fca6fc4e37db5b1e2c0e048748ee0ec3d839c`. Security Audit
`31771823387=PASS` y F9.7 `31771823386=PASS` verifican el merge. No hubo drift
entre el tree del candidate y el tree integrado.

V1 permanece inmutable. V2 corrige exclusivamente atribucion y contrato privado;
no conecta ambientes, no crea transport, workflow, environment, gate ni adapter.

## Contrato Privado Atribuible

Cada inventario y fuente conserva privadamente fingerprints de perfil, fuente,
run y cohorte; etapa; reason code terminal; secuencia `HEAD`/`GET`; intentos; y
timestamp UTC. El vocabulario distingue `INVENTORY_QUERY_FAILED`,
`INVENTORY_INCOMPLETE`, `SOURCE_GET_403`, `SOURCE_TIMEOUT`,
`SOURCE_DNS_FAILURE`, `SOURCE_TLS_FAILURE` y `SOURCE_TRANSPORT_FAILURE`.
La unidad de atribucion es el fingerprint exacto de perfil, no la institucion;
dos perfiles habilitados de una misma institucion permanecen independientes.

Cada fila `processing` debe tener timestamp usado, origen, edad calculada y una
clasificacion exacta: `STALE`, `NOT_STALE`, `AGE_UNKNOWN` o
`FUTURE_TIMESTAMP`. El schema actual no posee un timestamp autoritativo de
entrada a `processing`; v2 declara `last_harvested_at` y luego `created_at` como
proxies. Nunca los presenta como autoritativos. Ausencia o valor inutilizable se
publica en `processing_age_unknown` y bloquea `PASS`.

La cohorte FG3 primaria contiene solo cursos activos en `snapshot_1`. Un curso
inactivo entra unicamente con antecedente privado exact-one atribuible. Los
inactivos historicos no relacionados quedan excluidos. Cada observacion liga
run/cohorte, estados `is_active` y `last_404_at` de ambos snapshots,
clasificacion `HEALTHY`, `GET_404`, `GET_410`, `GET_403`, `TIMEOUT`,
`DNS_FAILURE`, `TLS_FAILURE` o `TRANSPORT_FAILURE`, secuencia `HEAD`/`GET`,
intentos y, cuando existe,
mutation kind, apply outcome y verificacion exact-one del antecedente.
El antecedente liga ademas run fingerprint, timestamp previo al primer snapshot y
mutation fingerprint recalculado. Un manifest privado completo enumera los
fingerprints de observaciones historicas esperadas y liga esa lista con su propio
fingerprint; un booleano aislado no acredita completitud ni mutacion.
El manifest no se acepta por si solo: una ancla privada separada debe declarar su
fingerprint esperado y quedar ligada al base/candidate SHA y tree. Ausencia o
desacuerdo termina en `STOP_G5_FG3_HISTORICAL_EVIDENCE_ANCHOR_MISSING`.
Si la evidencia historica necesaria para atribuir los casos FG3 no esta completa,
el collector termina con `STOP_G5_FG3_HISTORICAL_EVIDENCE_MISSING` antes de
publicar conteos 24/2/1; nunca los infiere desde el estado actual.

## Proyeccion Sanitizada

Los agregados FG2 preservan `duplicate_groups`, `duplicate_excess_rows`,
`conflicting_hash_groups` y `downstream_reference_conflicts`. Lifecycle publica
por separado stale, no stale, edad desconocida y timestamp futuro. FG3 publica:

```text
fg3_evaluated_courses
fg3_active_before
fg3_active_after
fg3_inconclusive_total
fg3_inconclusive_by_reason
first_get_404_observations
first_get_410_observations
deactivations_persistent_gone
recoveries_required
prior_mutations_revalidated
```

Cada aggregate y reason code publicado declara unidad y denominador constantes.
`denominator_values` publica las cantidades agregadas necesarias para auditar
esas definiciones. La cohorte primaria activa y la cohorte inactiva con mutacion
previa se publican por separado, y su suma debe coincidir con cursos evaluados.
La proyeccion contiene solo conteos, definiciones, fingerprints opacos, tiempos
del par, SHA/tree, decision y digests. Quedan fuera URLs, hosts, UUID e
institution IDs, filas, project ref, resultados por curso o institucion,
response bodies y secretos.

## Doble Lectura

El orden obligatorio es `snapshot_1 -> observations -> snapshot_2`. El par liga
`snapshot_pair_id`, inicio/fin UTC de cada bloque, fingerprint por tabla y global,
y count inicial/final. Ambos snapshots completos deben ser identicos. Esta doble
lectura demuestra estabilidad del intervalo, no una unica transaccion PostgreSQL:
`DOUBLE_READ_STABILITY_NOT_SINGLE_POSTGRES_TRANSACTION`.

## Frontera

Permanecen completamente excluidos syllabus/objectives, metadata, providers,
lineage editorial, H2-CA2, SQL, DDL/DML/RPC, workers, schedules, mutaciones y
planes de mutacion. `collect_g5_connected` termina antes de usar una factory o
red. Este candidate no accede a Production, Free o Pro y no usa secrets ni
environments.

La autoridad permanece en el [plan F10.9](./plan_remediacion_f10_9_fg2_fg3.md) y
el [estado vivo](../estado_del_proyecto.md). El siguiente candidate se limita al
[contrato offline del futuro adapter GET-only](./g5_get_only_adapter_contract_2026_08_14.md).
Implementar transporte, conectarlo o ejecutarlo requiere alcance y autorizacion
separados; este documento no los concede.
