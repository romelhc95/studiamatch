# Certificacion Local Hito 1 F8

Esta nota registra el candidate Git de `FASE-08`. No afirma adopcion remota, no autoriza aplicar migrations y no completa `H1-CA2P`. El package permanece `reconciled_not_certified` hasta una certificacion posterior en Free.

## Alcance funcional

- La migration forward-only F8 preserva `metadata` y `brochure_url` en la promocion atomica de enrichment.
- El acceso publico a `view_count` y `comparison_count` queda retirado del contrato de cursos.
- `verify_fase08_hito1_contract()` valida RLS, policies, columnas, defaults, constraints, indices, ACL y funciones sobre PostgreSQL 17.
- Cleansing y enrichment fallan cerrado si no pueden demostrar persistencia; los conteos reflejan solo escrituras confirmadas.
- Sync impide que datos mock sobrescriban un curso editorialmente publicado.
- El runner valida offline sin credenciales y aplica un eventual sufijo pendiente del manifest en una sola transaccion privilegiada.
- La paridad futura exige nombres, checksums y el verificador F8; no compara ledgers completos entre ambientes.

## Candidate

- Manifest: `db/manifests/fase08_candidate.json`.
- Estado: `reconciled_not_certified`.
- Targets bloqueados: Free y Pro.
- Orden cerrado: F6 G1b, F6 Hito 1, F7 closure y F8 functional closure.
- Las migrations y el manifest F6/F7 permanecen inmutables.
- `H-00`, canary sin atribucion y snapshots historicos permanecen excluidos.

## Evidencia local requerida

- 121 pruebas Python F6/F7/F8 y contrato de credenciales en PASS.
- PostgreSQL 17 efimero con baseline sintetico, roles `anon`, `authenticated` y `service_role` en PASS.
- Positivos y negativos RLS/ACL, policy heredada, persistencia RPC, identidad, deteccion de drift y replay del overlay F8 en PASS.
- Python compile y Context Graph con 26 archivos/190 enlaces en PASS.
- Lint sin errores, typecheck y build estatico en PASS; se conservan 10 warnings frontend preexistentes.
- Auditorias finales de seguridad y QA en GO, sin bloqueadores.

## Riesgos residuales aceptados

- La atomicidad construida del package requiere una prueba posterior mediante el RPC real `exec_sql` antes de cualquier promocion remota.
- Las definiciones exactas de policies se certifican sobre PostgreSQL 17 y fallan cerrado ante diferencias de formato.
- El loop de enrichment opera fail-fast; la nomenclatura legacy de tres intentos se reconciliara fuera de F8.
- La lectura de ledger en parity conserva el limite actual de 1000 filas y debe paginarse antes de excederlo.

## Gates restantes

- PR #228 recibio CI verde, aprobacion y merge humano mediante merge commit.
- `desarrollo@dbda29e` conserva el tree exacto del candidate; 121 pruebas, Python compile, Context Graph y PostgreSQL 17 repiten PASS post-merge.
- Estado F8: `COMPLETED` como certificacion local, sin afirmar adopcion remota.
- Free-first en una fase y autorizacion separadas, con preflight, writers pausados y evidencia counts-only.
- Backfill editorial acotado y certificado antes de publicar filas existentes.
- Pro permanece prohibido hasta obtener un manifest `free_certified` y aprobacion Production.
- `TASK-H1-001` y `H1-CA2P` permanecen `IN_PROGRESS`.
- Gate historico al cerrar F8: el package despues llamado `FASE-09`, ahora F9.1, no era ejecutable hasta definir su alcance. Estado vigente: F9.1/F9.2 cerradas y macrofase F9 en progreso.

Ver [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](./matriz_adopcion_db.md), [Reconciliacion F6](./reconciliacion_db_as_code_f6.md) y [Release minimo](./flujo_release_minimo.md).
