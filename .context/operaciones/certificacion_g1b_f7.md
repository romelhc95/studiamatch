# Certificacion G1b F7

Esta nota registra el cierre Git de `FASE-07`. No afirma adopcion remota ni autoriza aplicar migrations. El package permanece `reconciled_not_certified` hasta certificar tambien backfill editorial y postcondiciones Free.

## Matriz de postcondiciones

| ID | Postcondicion Git | Metodo | Evidencia candidate |
|---|---|---|---|
| `H-01` | RPC ETL ejecutables solo por `service_role` | Verificadores SQL y contrato manifest | `verify_fase06_g1b_reconciliation()` + `tests/test_fase06_db_as_code.py` |
| `H-02` | Owner `postgres`, modo correcto, path vacio y referencias calificadas | Inspeccion de catalogo en verifier | Migration G1b F6 inmutable |
| `H-03` | `cleansed_programs` sin acceso publico | RLS, revoke total y verifier | Migration G1b F6 inmutable |
| `H-04` | Ratings/reviews sin mutacion publica y frontend read-only | ACL, ausencia de POST y selects explicitos | Migration F7 + `tests/test_fase07_g1b.py` |
| `H-05` | Helpers `test_%` ausentes y processing cerrado | Verifier fail-closed y ACL RPC | Migration G1b F6 inmutable |
| `H-06` | ACL social minima acoplada al selector publico | Grants por columna y regresion frontend | `20260725_fase07_g1b_closure.sql` |
| `H-07` | RPC legacy de view count ausente y UI desacoplada | Drops forward-only y ausencia estatica de llamadas/campos | Migration F7 + contrato frontend |
| `H-10` | Requeue usa `pipeline_gate=false`; trigger y orquestacion son seguros | Contrato de tres writers, gates pre-limit y tests de fallos/timeout | Workers, `master_orchestrator.py` y pruebas F7 |

## Cambios acotados

- El frontend conserva ratings/reviews solo en lectura y deja de exponer el contador legacy.
- Cleansing, enrichment y sync escriben la razon canonica que consume `requeue_pipeline_records`.
- Sync consulta el curso existente con identidad de servicio fail-closed, codifica filtros PostgREST, no reactiva cursos manualmente despublicados, preserva metadata y no sobrescribe `publication_status`.
- Los tres workers leen perfiles y colas en modo estricto; las instituciones deshabilitadas se materializan como `skipped` para que requeue pueda recuperarlas despues.
- El orquestador aplica discovery, exclusiones, circuit breaker y freshness antes del limite; una lectura no demostrable, timestamp invalido, fallo parcial o timeout produce salida no cero.
- FG1 mantiene cadencia mensual con timeout; FG3 se escalona y comparte el grupo de concurrencia de FG2. FG1/FG2/FG3 rechazan tags y ramas no permanentes antes de cargar environments con secretos.
- FG1 y FG3 instalan dependencias runtime fijadas por version y hash.
- CI hace bloqueantes lint, typecheck, build estatico y el contrato F7 con Node 22; el runner revalida postcondiciones incluso para migrations ya registradas.
- La migration F7 se agrega al manifest cerrado sin modificar las migrations F6 ni habilitar su aplicacion.

## Gates restantes

- Validacion local: 97 pruebas, Context Graph, Python, lint, typecheck y build estatico en PASS; auditoria independiente final en GO.
- Validacion post-merge: PR #226 fusionado; `desarrollo@982d879` conserva el tree exacto y repite 97 pruebas y Context Graph en PASS.
- Gate humano: el usuario ratifico `romelhc95` como owner y `romelhc95-approver` como reviewer/aprobador para el cierre F7.
- Supabase Free y Pro: ninguna migration F6/F7 aplicada por esta fase.
- Los negativos por rol y postcondiciones remotas se ejecutan solo cuando una fase posterior autorice Free.
- El backfill editorial sigue separado y sin SQL ejecutable en este candidate.
- `H-00`, `H-08`, `H-09` y los redisenos definitivos H-04/H-07 permanecen fuera de alcance.
- Estado F7: `COMPLETED`. F8 requiere una autorizacion humana nueva.

Ver [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Reconciliacion F6](./reconciliacion_db_as_code_f6.md) y [Matriz DB](./matriz_adopcion_db.md).
