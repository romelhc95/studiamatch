# Flujo De Release Minimo

## Principio

El release es manual, secuencial y fail-closed. Un estado documental no sustituye una verificacion Git, DB, CI o runtime.

## Candidate CA1-Only Vigente

La [adenda aprobada](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md)
fija una ruta selectiva para Hito 1 CA1-only:

1. PR CA1 a `desarrollo` sin mezclar el worktree terminal F9.7.
2. Congelar patch-id, commit/tree y allowlist CA1.
3. Reconstruir el patch sobre baseline productivo sin mergear `desarrollo`.
4. Demostrar cero cambios `db/**`, `supabase/**`, `web/**` y CA2.
5. PR CA1-only a `certificacion`, canary y QA.
6. F9.10 ya declaro readiness despues de controles `main`, canary Production definido, rollback, validaciones y `USER_PERSONAL_UAT=PASS`; F10.6 completo control-plane y F10.7 promovio tecnicamente a `main` antes del canary Production y la habilitacion gradual de schedules.

El flujo schema/backfill/free_certified anterior queda `SUPERSEDED_FOR_HITO_1` y
se conserva solo como antecedente CA2 de Hito 2.

## Secuencia

1. F9.8 crea una rama `feat/*` desde `desarrollo` verificado.
2. F9.8 implementa solo CA1 dentro de la frontera permitida y valida localmente en contenedor.
3. F9.8 ejecuta auditorias y congela diff, patch-id, commit/tree y hashes CA1.
4. F9.9 reconstruye el candidate selectivo sobre el baseline de `certificacion`, sin mezclar `desarrollo` completo.
5. F9.9 demuestra equivalencia y cero cambios `db/**`, `supabase/**`, `web/**`, leads/email, Edge, backfill y superficies CA2.
6. F9.9 abre PR a `certificacion`, ejecuta canary, define/cierra QA independiente e implementa controles pre-main de repositorio.
7. F9.10 registro PR #283/#284 en `desarrollo`, reconstruyo target-aware sobre `certificacion` mediante PR #285 y congelo el boundary final por path/status/mode/blob/digest.
8. F9.10 realizo certificacion final: `certificacion@5cd27c6f6c35808865b7084673a83f9f690d3760` / tree `419b25f69e4eef4d7277a7439ca45efc1eaac242`, CI post-merge `30865604732=PASS`, run `30865604729` cancelado con cero pasos, boundary 32 objetos digest `34f3789d597bf4012378d6e509a03ee6e9ef37edaee95713023421538cab1aa5` y `USER_PERSONAL_UAT=PASS`; [ADR-0008](../decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md) preserva esta evidencia como historica pero superseded para autoridad de promocion F10.7.
9. F9.10 declara readiness para F10 con candidate commit/tree inmutable, CI, review humano y sin blockers pendientes para F10.6.
10. F10.6 ejecuto control-plane: environments programados, variables fail-closed, runs antiguos resueltos/cancelados con autorizacion y branch policy verificada.
11. F10.6 cierra documentalmente y activa F10.7 antes de cualquier PR a `main`.
12. F10.7 documento rebaseline, reconstruyo controles, promovio por PR #291 a `main@64e4ed895d43121c5683e26a355993f18e528a5c` y registro boundary post-merge 32 objetos digest `8fafc74e415d6875315e8584eb17705e24c40777675996cde9bf4ff0ccf7ddff`.
13. F10.8 ejecuta canary Production manual con schedules apagados, `candidate_sha` exacto, snapshot privado, restore always, segundo restore NOOP y artifacts sanitizados.
14. F10.9 habilita schedules gradualmente y observa FG2/FG3; las 72h empiezan con el primer FG2 automatico valido sobre el nuevo SHA de `main`, y el cierre requiere al menos tres pares FG2 -> FG3 consecutivos completos.
15. F11.1 cierra documentalmente el Hito 1 y la evidencia final.

## Stop Conditions

- Secretos o credenciales en archivos, logs o diffs.
- Tree, ancestry, package o checksum no verificables.
- Mismo stem SQL con contenido distinto o intento de editar ledger.
- H-00, schema/RLS, backfill o CA2 incluidos en el candidate CA1-only.
- Artifact F9.5 de PR #245 o PR #247 tratado como candidate, package contractual o insumo de aplicacion.
- Mutacion no acotada, environment ambiguo o writer/schedule activo fuera del canary aprobado.
- Fallo de test, Context Graph, canary o smoke.
- Diferencia no explicada entre [Matriz DB](matriz_adopcion_db.md), frontera CA1-only y ambiente real.
- Reutilizar el freeze F9.10 de 32 objetos como autoridad F10.7 sin nuevo digest, variables aprobadas y UAT nuevo.
- Tener un deployment Cloudflare Pages de `main` no observado, no documentado o usado como sustituto de canary Production.

## Schedules

FG1, FG2 y FG3 conservan cadencia automatica declarada en YAML. Hito 1 exige que toda ejecucion automatica respete gates, circuit breakers, controles de ambiente y las stop conditions de este flujo. Ver [Pipeline](../arquitectura_pipeline.md).

## Separacion Dentro De La Macrofase F9

- F9.1 produce solo evidencia local/offline y conserva `reconciled_not_certified` con Free/Pro bloqueados; su identidad historica es `FASE-09`.
- F9.2 codifica localmente la maquina de promocion; su descriptor e identidad historica permanecen `FASE-10`.
- F9.3 conserva historia del contrato local. F9.4 reconcilia documentalmente el plan. F9.5 queda `COMPLETED_WITH_KNOWN_FINDINGS`; no se repite la lectura Free y sus artifacts no se promueven.
- T01 queda `CONDITIONAL_ACCEPTED` como antecedente de F9.6, sin attestation tecnica ni capacidad heredada.
- F9.6 cierra H-00 como `H00_ALREADY_REMEDIATED_NO_DML`; Gate B DELETE es `SUPERSEDED_NON_AUTHORIZABLE`.
- F9.7 queda cerrada por rebaseline contractual; v3, PR-O v1/hold actual y PR-O sucesor permanecen historia no ejecutable de Hito 1.
- F9.8 implementa y valida localmente el candidate CA1-only.
- F9.9 ejecuta candidate selectivo, Certification, canary, QA y controles pre-main de repositorio; F9.10 inicia solo cuando el Context Graph lo declare activo y requiere autorizacion decimal propia.
- F9.10 realizo correccion repository-only post PR #283, reconstruccion selectiva autorizada, certificacion final, controles `main`, rollback, `USER_PERSONAL_UAT` y readiness para F10.
- La macrofase F10 Produccion inicio en F10.6; F10.7 queda registrada como entrega tecnica post-main segun [ADR-0008](../decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md) y [ADR-0009](../decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md); F10.8 esta activa con remediacion DB Sync fail-closed despues de PR #297, Certification Canary PASS y DB Sync `31142826000=FAIL_CLOSED_PRE_SUPABASE`; F10.9 permanece bloqueada.

## Subfases F10 CA1-Only

| ID | Estado | Alcance |
|---|---|---|
| `F10.1`-`F10.5` | `SUPERSEDED_HISTORY` | Historia sustituida; no autoriza ejecucion. |
| `F10.6` | `COMPLETED_CONTROL_PLANE` | Control-plane y limpieza de runs antiguos antes de promover a `main`: environments programados fail-closed, branch policy `main`, reviewer humano y runs `30681941694`, `29678093566`, `29677885934` cancelados con cero pasos. |
| `F10.7` | `COMPLETED_TECHNICAL_DELIVERY` | PR #291 aprobado/fusionado a `main`, boundary post-merge 32 objetos, Security Audit PASS, Cloudflare Pages `SUCCESS` y DB Sync cancelado cero-pasos. |
| `F10.8` | `IN_PROGRESS_DB_SYNC_FAIL_CLOSED_REMEDIATION_REQUIRED` | Remediacion Production Canary promovida por PR #297 a `main@260900a268ab8eb194140ea7311aec2a170b6e17`; Certification Canary `31140933096=PASS`; DB Sync `31142826000` fallo fail-closed antes de Supabase por ejecutar report DB en push sin cambios `db/**`. Requiere remediar DB Sync antes de Production Canary, schedules u observacion. |
| `F10.9` | `PENDING` | Schedules graduales y observacion 72h + tres pares FG2 -> FG3 completos. |
| `F11.1` | `PENDING` | Cierre final y conformidad cliente. |

## Maquina De Promocion Hito 1

- El package historico `FASE-10`/F9.2 definio localmente `reconciled_not_certified -> ready_for_free -> free_schema_certified -> free_backfill_certified -> free_certified`; esa maquina queda `SUPERSEDED_FOR_HITO_1` y se conserva como antecedente CA2 de Hito 2.
- Cada transicion requiere attestation inmutable y aprobacion propia; no hay saltos ni continuidad automatica.
- F9.4 adopta el plan simplificado y no conecta. La anterior definicion remota F9.4 no es autorizable.
- F9.5 queda cerrada; su T01 condicionado es antecedente historico y no cambia ningun estado DB.
- La maquina de attestations del package historico `FASE-10` no gobierna el T01 documental actual: este no es una attestation ni una transicion de estado.
- F9.6 cerro P0 H-00 sin DML. F9.7 cierra por rebaseline documental; F9.8-F9.10 reemplazan la ruta schema/backfill/free_certified para Hito 1.
- `USER_PERSONAL_UAT` es hold operativo F9.10, no attestation de la maquina ni transicion nueva; se ubica despues de canary, validaciones tecnicas Certification y QA, y antes de readiness F10.
- La definicion F9.7 de identidad backend, hold y executor privado queda como historia `SUPERSEDED_FOR_HITO_1`; no habilita una ruta remota ni backfill en CA1-only.
- F10 conserva el significado de produccion de [ADR-0003](../decisiones/ADR-0003_taxonomia_macrofases_subfases.md); para CA1-only se limita a PR a `main`, canary Production, schedules y observacion, sin promover cambios DB Pro.
- Forward-fix o restauracion requieren un incidente documentado y una autorizacion de emergencia exacta separada; esta regla no autoriza ninguna de esas operaciones.

## Politica De Resguardo

Los respaldos preservados se conservan fuera del repositorio, sin mover, editar o compactar hasta desplegar Hito 1 y completar observacion. Sus rutas locales no se versionan.

Ver [Estado](../estado_del_proyecto.md) y [Tarea 001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
