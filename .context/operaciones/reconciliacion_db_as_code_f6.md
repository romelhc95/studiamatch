# Reconciliacion DB-as-Code F6

Esta nota registra el candidate forward-only de `FASE-06`. No autoriza ni afirma una aplicacion remota. La adopcion efectiva sigue determinada por [Sistema DB](../sistema_db_supabase.md), la [Matriz DB](./matriz_adopcion_db.md) y el [flujo de release](./flujo_release_minimo.md).

## Evidencia usada

- `[REMOTE]` Catalogos, tipos, constraints, indices, RLS, ACL, funciones, triggers, advisors y ledgers de Free y Pro observados en modo read-only.
- `[GIT]` Baseline vigente y migrations historicas versionadas.
- `[PRESERVED]` Bundles G1b y Hito 1 verificados por checksum fuera del workspace operativo.
- `[DERIVED]` Comparacion independiente de fuente, ledger y postcondicion.

Los detalles de objetos sensibles, identificadores de ambiente y diferencias explotables permanecen en el artifact privado ignorado. Esta nota no contiene credenciales ni filas operativas.

## Matriz por postcondicion

| Componente | Free observado | Pro observado | Fuente | Decision F6 |
|---|---|---|---|---|
| Cuatro estaciones y gates | Efectivo | Efectivo con drift | Baseline Git parcial | Conservar; nunca copiar filas operativas. |
| G1b `H-01` a `H-07` y `H-10` | Efectivo | Divergente | Consolidado preservado; drafts originales `source_unavailable` | Nueva reconciliacion forward-only, sin replay. |
| Contrato editorial y calidad Hito 1 | Efectivo | Ausente | Artifact preservado posterior a la aplicacion original | Nueva migration de schema/RLS, sin DML. |
| Moderacion ratings/reviews | Efectiva | Ausente | Postcondicion remota sin fuente historica exacta | Incorporada desde la postcondicion verificable. |
| Canary scoped | Efectivo en ambos con guard divergente | Efectivo en ambos con guard divergente | Blobs preservados verificables; ledger no atribuible | `observed_effective_unledgered`; registrar, no replayar. |
| `H-00` | Historia Free-only | No aplicable | Artifact operativo preservado | `historical_free_only`; exclusion mecanica de Pro. |
| `H-08`, `H-09` y redisenos diferidos | No adoptados por F6 | No adoptados por F6 | `source_unavailable` o fuera de alcance | Excluidos del candidate. |
| Snapshots completos historicos | Contradicen el remoto | Contradicen el remoto | Disponibles | `superseded`; prohibido replayar. |

## Candidate promocionable

El manifest cerrado `db/manifests/fase06_promotable.json` enumera exactamente:

1. `db/migrations/20260724_fase06_g1b_reconciliation.sql`.
2. `db/migrations/20260724_fase06_hito1_editorial_contract.sql`.
3. `db/migrations/20260725_fase07_g1b_closure.sql`.

Cada entrada exige provenance `new_forward_only`, target explicito y SHA-256 exacto sobre la representacion canonica LF del SQL. El validador del manifest y el marcador de ledger normalizan exclusivamente CRLF a LF antes del hash, por lo que un bind mount desde Windows conserva la misma identidad que CI Linux sin aceptar drift de contenido. El status permanece `reconciled_not_certified`: el runner rechaza aplicarlo tanto en Free como en Pro. Los prerrequisitos universales de este manifest v1 se conservan como evidencia historica, pero no gobiernan la promocion futura; F10 define requisitos separados por transicion. Pro rechaza cualquier status anterior a `free_certified`.

El workflow Production es manual, exige commit inmutable y aprobacion explicita, y nunca se dispara por push. El guard rechaza `H-00`, fuentes `historical_free_only`, `source_unavailable` o `superseded`, stems ajenos al package F6/F7, paths fuera de migrations, checksum drift y DML ejecutado durante instalacion.

Canary no aparece en el manifest porque sus postcondiciones ya se observaron en ambos ambientes y no existe atribucion de ledger suficiente para replay. Los ledgers permanecen append-only.

## Backfill separado

La estrategia vive en `db/operations/editorial/README.md`. No existe SQL ejecutable de backfill en este candidate. Cualquier operacion requiere autorizacion humana separada, Free-first, writers pausados, predicado acotado e idempotente, evidencia counts-only y aislamiento estricto de ambientes.

La migration editorial agrega defaults seguros. Schema/RLS debe aplicarse y certificarse en Free antes de ejecutar el backfill que promueva cursos existentes de borrador a publicado. Compatibilidad frontend, aplicacion schema, backfill y certificacion final son gates separados; ninguna aprobacion sustituye a la siguiente.

## Estado de adopcion

- Candidate Git: PR #223 y forward-fix PR #224 aprobados y fusionados en `desarrollo` mediante merge commits.
- Validacion post-merge: `desarrollo@e00052a`, tree exacto del forward-fix, 74 pruebas deterministas incluida regresion LF/CRLF desde Docker sobre Windows; Context Graph y sintaxis Python en PASS.
- Supabase Free: sin DDL/DML de F6 aplicado por esta fase.
- Supabase Pro: sin DDL/DML de F6 aplicado por esta fase.
- Estado F6: `COMPLETED`. El package sigue bloqueado para Free y Pro como `reconciled_not_certified`.
- Gate historico al cerrar F6: F7. Estado vigente: F7-F9 estan cerradas y F10 define el contrato local de promocion antes de cualquier preflight Free.

Ver [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) y [Release minimo](./flujo_release_minimo.md).
