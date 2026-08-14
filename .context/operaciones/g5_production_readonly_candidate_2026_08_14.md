# F10.9 G5 - Candidate Production Read-Only Repository-Only

| Campo | Valor |
|---|---|
| Subfase | `F10.9` |
| Estado | `COMPLETED_POST_MERGE_VERIFIED` |
| Gate conectado | `APPROVE_F10_9_G5_PRODUCTION_READONLY_DIAGNOSTIC_V1` |
| Estado del gate | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Acceso remoto | `BLOCKED_BEFORE_NETWORK` |
| Base protegida | `desarrollo@2c9d2438c5fc309d3692d1a1de1233e0fcc95afc` |
| Tree base | `161a8df69bf5e527c4ba863891504551ec5f7aa7` |

## Cierre Post-Merge ADR-0011

PR #375 queda `COMPLETED_POST_MERGE_VERIFIED`. El candidate
`bc8408cdd5c90d3906fafd33989e1d124441859a` fue integrado por merge protegido:

```text
merge = 2c9d2438c5fc309d3692d1a1de1233e0fcc95afc
tree = 161a8df69bf5e527c4ba863891504551ec5f7aa7
parent_1 = d8859a52254135561be996a706590f9a005fc7da
parent_2 = bc8408cdd5c90d3906fafd33989e1d124441859a
security_audit_post_merge = 31768101859=PASS
f9_7_contract_post_merge = 31768101887=PASS
```

La decision [ADR-0011](../decisiones/ADR-0011_rebaseline_superior_hito1_ca1_f10_10_a_h2.md)
queda integrada y verificada. F10.10 permanece
`SUPERSEDED_FOR_HITO_1_TRANSFERRED_TO_H2_CA2`; F10.9 permanece
`REBASELINED_FG2_FG3_OPERATIONAL_REMEDIATION` y
`G4=PASS_CA1_FG2_FG3_ONLY_METADATA_TRANSFERRED_TO_H2`.

## Cierre Post-Merge G5 V1

PR #376 queda `COMPLETED_POST_MERGE_VERIFIED`. El candidate
`520b0fc3f039d279faadb102fa0f13f3725a58ee` fue integrado por merge protegido:

```text
merge = 30f77b88778372de112c6a8fb51a1344155db025
tree = b25fca6fc4e37db5b1e2c0e048748ee0ec3d839c
parent_1 = 2c9d2438c5fc309d3692d1a1de1233e0fcc95afc
parent_2 = 520b0fc3f039d279faadb102fa0f13f3725a58ee
security_audit_post_merge = 31771823387=PASS
f9_7_contract_post_merge = 31771823386=PASS
```

El schema `f10.9-g5-production-readonly-projection.v1` y el algoritmo
`f10.9-g5-production-readonly-v1` quedan congelados como antecedente. El corte
v2 vive en `g5_v2_repository_only_candidate_2026_08_14.md`; no reinterpreta esta
evidencia ni habilita el adapter conectado.

## Candidate G5

Este candidate prepara exclusivamente codigo, pruebas, boundary y documentacion
repository-only. Reutiliza las capacidades promovidas P2/P3/P4 para
normalizacion URL, clasificacion FG2, paginacion estable y estados FG3, sin
invocar workers ni superficies mutantes.

La fachada G5 conserva mecanicamente solo `select` y `count` sobre dos snapshots
privados ya materializados. No conserva cliente DB, transporte ni callables
ligados al backend. No contiene
`insert`, `upsert`, `patch`, `update`, `delete`, `rpc`, SQL, DDL, providers ni
llamadas a workers. Dos snapshots completos, paginados y ordenados por `id.asc`,
deben ser identicos; cualquier diferencia termina `STOP_G5_SNAPSHOT_DRIFT`.

La proyeccion publicable contiene solo conteos, reason codes, fingerprints,
decision, digests, timestamps y SHA/tree. URLs, UUID, institution IDs, project
ref, host, filas y observaciones permanecen en payloads privados gitignored. No
se incorpora ningun artifact privado al candidate.

El alcance diagnostico CA1 queda limitado a duplicados URL normalizados, filas
excedentes, hashes conflictivos, referencias downstream, lifecycle stale o
desconocido, perfiles invalidos, inventarios no cargables, resultados de fuentes
403/timeout/fallo y estado FG3 inconcluso/404/410/desactivacion pendiente de
revalidacion. Quedan excluidos metadata, providers, lineage editorial,
re-enrichment, backfill y todo H2-CA2.

## Boundary Conectado

El entrypoint conectado valida todas estas condiciones antes de cualquier red:

1. merge protegido del candidate G5;
2. checks post-merge PASS;
3. payload privado ligado al merge SHA/tree;
4. target Production validado privadamente;
5. gate humano separado con estado `APPROVED_NOT_CONSUMED`.

El gate no se crea, aprueba ni consume en este candidate. Las credenciales
backend existentes del environment autorizado solo podran ser usadas por el
adaptador privado futuro, despues de todos los controles anteriores. Este
repositorio no crea roles, passwords, ACL, grants, migrations ni readers.
Incluso con todos los campos propuestos presentes, este candidate termina
`STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED` y nunca invoca una factory. La
materializacion conectada requiere una implementacion post-merge separada.

El payload privado futuro debe ligar al fingerprint del snapshot cada resultado
de fuente/FG3 y una atestacion `content_hash_valid` por fila
`pending`/`processing`/`processed`. La fachada rechaza columnas fuera de su
proyeccion exacta y el diagnostico verifica referencias hasta
`enriched_programs`; ninguna fila ni atestacion privada se publica.

## Autoridad Y Siguiente Paso

Este registro complementa el
[plan F10.9](./plan_remediacion_f10_9_fg2_fg3.md), la
[tarea Hito 1](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) y el
[estado vivo](../estado_del_proyecto.md). No autoriza Production, source probes,
SQL, DDL/DML/RPC, writers, remediaciones, schedules, Certification ni Main.

La salida de este corte se limita a aprobar y fusionar el PR protegido G5 a
`desarrollo` y verificarlo post-merge. Solo despues puede prepararse un payload
privado nuevo y solicitarse el gate conectado separado.
