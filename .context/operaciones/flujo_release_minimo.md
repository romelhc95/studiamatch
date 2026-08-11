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
13. F10.8 promovio por PR #297 la remediacion de Production Canary, remedio DB Sync por PR #304/#305/#306/#307 hasta `main@529ca111f1fef40efb15676ad6f07d002a54ae92`, y promovio la remediacion cleansing provenance por PR #319/#320 hasta `main@1885806f0d9f189600d410d353fcf13fb8dd4676`; `DB Sync to Production` run `31243797695=SUCCESS_REPORT_ONLY` detecto exactamente una migracion Pro pendiente y no aplico DDL.
14. F10.8 aplico Pro una sola vez mediante `DB Sync to Production` run `31263024890`, bajo registro `DDL-F10_8_ATOMIC_CLEANSING_PROVENANCE_PRO`, `candidate_sha` exacto igual a `origin/main`, dispatch manual, approval `Production`, Backup/RPO runtime aceptado y writers pausados; DB Sync verify `31268229878=PASS` confirmo pending `0`, apply skipped, target schema PASS y FG2 deferred PASS.
15. F10.8 ejecuto Production Canary manual con schedules apagados sobre `main@859d2f7d83f83950d10858fe27bd035febba7f68`, snapshot privado, restore always, segundo restore NOOP y artifacts sanitizados; run `31272290614=PASS`, artifact `9026139906`, `EVID-H1-010=VERIFIED`.
16. F10.9 planificaba habilitar schedules y observar FG2/FG3, pero G4=`STOP_REQUIRES_REBASELINE` suspendio G5-G13.
17. F10.10 ejecuta, por gates separados, remediacion metadata fill-only por etapas Free -> Certification -> Pro y devuelve evidencia a F10.9/G4; las cohortes son independientes por target fisico, no por alias de environment, y no habilita schedules.
18. F11.1 cierra documentalmente el Hito 1 y la evidencia final solo tras los gates productivos aplicables.

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
- La macrofase F10 Produccion inicio en F10.6; F10.7 queda registrada como entrega tecnica post-main segun [ADR-0008](../decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md) y [ADR-0009](../decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md); F10.8 queda completada como `COMPLETED_PRODUCTION_CANARY_VERIFIED` con Pro DDL aplicada una sola vez, DB Sync verify `31268229878=PASS`, PR #325 en `main@859d2f7d83f83950d10858fe27bd035febba7f68`, Production Canary `31272290614=PASS`, artifact `9026139906` y `EVID-H1-010=VERIFIED`; F10.9 queda `STOP_REQUIRES_REBASELINE` en G4 y ninguna autorizacion decimal F10.9 habilita G5-G13 sin decision superior.

## Subfases F10 CA1-Only

| ID | Estado | Alcance |
|---|---|---|
| `F10.1`-`F10.5` | `SUPERSEDED_HISTORY` | Historia sustituida; no autoriza ejecucion. |
| `F10.6` | `COMPLETED_CONTROL_PLANE` | Control-plane y limpieza de runs antiguos antes de promover a `main`: environments programados fail-closed, branch policy `main`, reviewer humano y runs `30681941694`, `29678093566`, `29677885934` cancelados con cero pasos. |
| `F10.7` | `COMPLETED_TECHNICAL_DELIVERY` | PR #291 aprobado/fusionado a `main`, boundary post-merge 32 objetos, Security Audit PASS, Cloudflare Pages `SUCCESS` y DB Sync cancelado cero-pasos. |
| `F10.8` | `COMPLETED_PRODUCTION_CANARY_VERIFIED` | Remediacion Production Canary promovida por PR #297 a `main@260900a268ab8eb194140ea7311aec2a170b6e17`; Certification Canary `31140933096=PASS`; DB Sync historico `31142826000` fallo fail-closed antes de Supabase; remediacion DB Sync promovida por PR #304/#305/#306/#307 a `main@529ca111f1fef40efb15676ad6f07d002a54ae92`; remediacion cleansing provenance promovida por PR #319/#320 a `main@1885806f0d9f189600d410d353fcf13fb8dd4676`; Pro DDL aplicada una sola vez por `31263024890`; DB Sync verify `31268229878=PASS`; PR #325 promovio paginacion no-cohorte a `main@859d2f7d83f83950d10858fe27bd035febba7f68`; Production Canary `31272290614=PASS`, artifact `9026139906`, `EVID-H1-010=VERIFIED`. |
| `F10.9` | `STOP_REQUIRES_REBASELINE` | G3/P5 cerrado; G4 detiene P7, promociones, schedules y observacion hasta decision de autoridad superior. |
| `F10.10` | `M3_SCOPE_APPROVED_TARGET_AUTHORIZATIONS_PENDING` | M1/M2 integrados por PR #345/#346; [evidencia M2](./m2_f10_10_post_merge_evidence_2026_08_10.md) y [scope M3](./m3_f10_10_scope_por_ambiente_target.md) fijan colector promovido -> Free -> Certification replay -> Pro. Ninguna capacidad remota se concede antes del colector ni sin el gate exacto del target. |
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
- F10 conserva el significado de produccion de [ADR-0003](../decisiones/ADR-0003_taxonomia_macrofases_subfases.md); para CA1-only se limita a PR a `main`, Pro DDL acotado cuando exista autorizacion separada, canary Production, schedules y observacion, sin backfill ni cambios CA2.
- Forward-fix o restauracion requieren un incidente documentado y una autorizacion de emergencia exacta separada; esta regla no autoriza ninguna de esas operaciones.

## Politica De Resguardo

Los respaldos preservados se conservan fuera del repositorio, sin mover, editar o compactar hasta desplegar Hito 1 y completar observacion. Sus rutas locales no se versionan.

Ver [Estado](../estado_del_proyecto.md) y [Tarea 001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
