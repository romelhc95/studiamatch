# Flujo De Release Minimo Legacy

> `SUPERSEDED_HISTORY`: las lineas legacy de esta seccion conservan antecedente
> tecnico de Hito 1, pero no son autoridad viva. F10.9, F11.1, schedules y
> observacion productiva no quedan pendientes como gate actual; fueron sustituidos
> por F10.11, O0-O5, ADR-0026, ADR-0027 y ADR-0028.

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
8. F9.10 realizo certificacion final: `certificacion@5cd27c6f6c35808865b7084673a83f9f690d3760` / tree `419b25f69e4eef4d7277a7439ca45efc1eaac242`, CI post-merge `30865604732=PASS`, run `30865604729` cancelado con cero pasos, boundary 32 objetos digest `34f3789d597bf4012378d6e509a03ee6e9ef37edaee95713023421538cab1aa5` y `USER_PERSONAL_UAT=PASS`; la referencia historica `ADR-0008` queda superseded por [ADR-0026](../decisiones/ADR-0026_cutoff_h1_y_baseline_sprint1.md) para F10.11.
9. F9.10 declara readiness para F10 con candidate commit/tree inmutable, CI, review humano y sin blockers pendientes para F10.6.
10. F10.6 ejecuto control-plane: environments programados, variables fail-closed, runs antiguos resueltos/cancelados con autorizacion y branch policy verificada.
11. F10.6 cierra documentalmente y activa F10.7 antes de cualquier PR a `main`.
12. F10.7 documento rebaseline, reconstruyo controles, promovio por PR #291 a `main@64e4ed895d43121c5683e26a355993f18e528a5c` y registro boundary post-merge 32 objetos digest `8fafc74e415d6875315e8584eb17705e24c40777675996cde9bf4ff0ccf7ddff`.
13. F10.8 promovio por PR #297 la remediacion de Production Canary, remedio DB Sync por PR #304/#305/#306/#307 hasta `main@529ca111f1fef40efb15676ad6f07d002a54ae92`, y promovio la remediacion cleansing provenance por PR #319/#320 hasta `main@1885806f0d9f189600d410d353fcf13fb8dd4676`; `DB Sync to Production` run `31243797695=SUCCESS_REPORT_ONLY` detecto exactamente una migracion Pro pendiente y no aplico DDL.
14. F10.8 aplico Pro una sola vez mediante `DB Sync to Production` run `31263024890`, bajo registro `DDL-F10_8_ATOMIC_CLEANSING_PROVENANCE_PRO`, `candidate_sha` exacto igual a `origin/main`, dispatch manual, approval `Production`, Backup/RPO runtime aceptado y writers pausados; DB Sync verify `31268229878=PASS` confirmo pending `0`, apply skipped, target schema PASS y FG2 deferred PASS.
15. F10.8 ejecuto Production Canary manual con schedules apagados sobre `main@859d2f7d83f83950d10858fe27bd035febba7f68`, snapshot privado, restore always, segundo restore NOOP y artifacts sanitizados; run `31272290614=PASS`, artifact `9026139906`, `EVID-H1-010=VERIFIED`.
16. F10.9 habilita schedules gradualmente y observa FG2/FG3; las 72h empiezan con el primer FG2 automatico valido sobre el nuevo SHA de `main`, y el cierre requiere al menos tres pares FG2 -> FG3 consecutivos completos.
17. F11.1 cierra documentalmente el Hito 1 y la evidencia final.

## Stop Conditions

- Secretos o credenciales en archivos, logs o diffs.
- Tree, ancestry, package o checksum no verificables.
- Mismo stem SQL con contenido distinto o intento de editar ledger.
- H-00, schema/RLS, backfill o CA2 incluidos en el candidate CA1-only.
- Artifact F9.5 de PR #245 o PR #247 tratado como candidate, package contractual o insumo de aplicacion.
- Mutacion no acotada, environment ambiguo o writer/schedule activo fuera del canary aprobado.
- Fallo de test, Context Graph, canary o smoke.
- Diferencia no explicada entre la matriz DB canonica vigente, frontera CA1-only y ambiente real.
- Reutilizar el freeze F9.10 de 32 objetos como autoridad F10.7 sin nuevo digest, variables aprobadas y UAT nuevo.
- Tener un deployment Cloudflare Pages de `main` no observado, no documentado o usado como sustituto de canary Production.

## Schedules

FG1, FG2 y FG3 conservan cadencia automatica declarada en YAML. Hito 1 exige que toda ejecucion automatica respete gates, circuit breakers, controles de ambiente y las stop conditions de este flujo. En F10.11 los schedules permanecen fail-closed hasta JIT R3 posterior a H2.

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
- La macrofase F10 Produccion inicio en F10.6; F10.7 y F10.8 quedan como historia tecnica preservada. Para F10.11, [ADR-0026](../decisiones/ADR-0026_cutoff_h1_y_baseline_sprint1.md) y [ADR-0027](../decisiones/ADR-0027_work_packages_y_convergencia.md) sustituyen referencias legacy como autoridad operativa.

## Subfases F10 CA1-Only

| ID | Estado | Alcance |
|---|---|---|
| `F10.1`-`F10.5` | `SUPERSEDED_HISTORY` | Historia sustituida; no autoriza ejecucion. |
| `F10.6` | `COMPLETED_CONTROL_PLANE` | Control-plane y limpieza de runs antiguos antes de promover a `main`: environments programados fail-closed, branch policy `main`, reviewer humano y runs `30681941694`, `29678093566`, `29677885934` cancelados con cero pasos. |
| `F10.7` | `COMPLETED_TECHNICAL_DELIVERY` | PR #291 aprobado/fusionado a `main`, boundary post-merge 32 objetos, Security Audit PASS, Cloudflare Pages `SUCCESS` y DB Sync cancelado cero-pasos. |
| `F10.8` | `COMPLETED_PRODUCTION_CANARY_VERIFIED` | Remediacion Production Canary promovida por PR #297 a `main@260900a268ab8eb194140ea7311aec2a170b6e17`; Certification Canary `31140933096=PASS`; DB Sync historico `31142826000` fallo fail-closed antes de Supabase; remediacion DB Sync promovida por PR #304/#305/#306/#307 a `main@529ca111f1fef40efb15676ad6f07d002a54ae92`; remediacion cleansing provenance promovida por PR #319/#320 a `main@1885806f0d9f189600d410d353fcf13fb8dd4676`; Pro DDL aplicada una sola vez por `31263024890`; DB Sync verify `31268229878=PASS`; PR #325 promovio paginacion no-cohorte a `main@859d2f7d83f83950d10858fe27bd035febba7f68`; Production Canary `31272290614=PASS`, artifact `9026139906`, `EVID-H1-010=VERIFIED`. |
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
- F10 conserva el significado de produccion definido por la taxonomia vigente; para F10.11 se limita a homologacion documental y no autoriza PR a `main`, Pro DDL, canary Production, schedules ni observacion sin prompt separado.
- Forward-fix o restauracion requieren un incidente documentado y una autorizacion de emergencia exacta separada; esta regla no autoriza ninguna de esas operaciones.

## Politica De Resguardo

Los respaldos preservados se conservan fuera del repositorio, sin mover, editar o compactar hasta desplegar Hito 1 y completar observacion. Sus rutas locales no se versionan.

Ver [Estado](../estado_del_proyecto.md) y [Tarea 001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
# Flujo Release Minimo Vigente - Posterior A F10.11

> Esta nota no crea alcance ni autoriza ejecucion por si sola. La autoridad viva
> esta en `estado_del_proyecto.md`.

## Flujo Vigente Sprint 1

```text
F10.11 GOV-HOM candidate produce T_HOM
-> R2 separado para push/PR/merge a desarrollo
-> GOV-CI separa security-audit de review nativa
-> GOV-CI2 separa boundary incremental y boundary estructural de promociones
-> GOV-CI3 elimina bootstrap autorreferencial de grants
-> GOV-CI4 usa Environment Promotion dedicado para boundary
-> GOV-CI5 valida pushes post-merge de promociones fail-closed
-> GOV-CI6 publica promociones target-aware y congela F9.7 automatico
-> GOV-CI7 valida evidencia post-merge fail-closed y HOM-007
-> R3 re-O2 JIT desarrollo -> certificacion
-> R3 O3 JIT certificacion -> main
-> R3 O4 JIT main -> certificacion
-> R3 O5 JIT certificacion -> desarrollo
-> predicado externo de cierre F10.11
-> rebaseline WP-H2-001
F12.1 local H2-CA2 bajo WP/digest R1
-> R2 separado para push/PR a desarrollo
-> R3 JIT separado para Supabase Free, DDL/DML, RLS/grants y backfill
-> PR protegido desarrollo a certificacion solo con gate posterior
-> PR protegido certificacion a main solo con gate posterior
-> R3 Pro/produccion solo con grant single-use posterior
```

## Reglas

- `security-audit` permanece como required check.
- `security-audit` valida attestation, manifest, digest, `Base-SHA`, `Candidate-SHA`, paths y co-change.
- Para PR normales, `Canonical Path Boundary` sigue usando el diff incremental y el WP vigente.
- Para promociones O2-O5, `Canonical Path Boundary` usa `Promotion Attestation` y valida same-repo, operacion, `Grant-ID`, par, ancestry, tree, `D_FINAL`, `T_FINAL`, `Final-WP`, nivel R3 JIT, referencia de aprobacion y expiry.
- Para pushes post-merge de promociones O2-O5, `Canonical Path Boundary` clasifica `VERIFIED_PROMOTION`, `NOT_APPLICABLE` o `BLOCKED`; solo `NOT_APPLICABLE` puede volver al boundary incremental.
- Las solicitudes `.context/r3_grants/*.json` son `REQUESTED_JIT_SINGLE_USE` con bindings simbolicos; no contienen `candidate_sha`, `t_final`, approvals, expiry ni consumo falso.
- Cada PR requiere review humano por branch protection; la review no dispara CI y no necesita rerun manual.
- Push y PR requieren R2 separado.
- H2-H5 requieren work package aprobado por digest.
- H2-CA3 no inicia antes de cerrar H2-CA2 local.
- F10.11 no cierra por prosa: requiere trees iguales a `T_HOM`, ancestry `main -> certificacion -> desarrollo`, DB Sync sin cambios y checkout ordinario actualizado.
- Los grants `O2`, `O3`, `O4` y `O5` no se pueden agrupar; cada retry requiere grant nuevo.
- PR #428 fallo O2 y dejo `O2_CONSUMED_BY_FAILURE`; no autoriza retry ni nuevo O2 sin grant JIT separado posterior.
- PR #428 y PR #431 quedaron cerrados/fallidos sin merge; no autorizan retry ni nuevo O2 sin grant JIT separado posterior.
- PR #433 completo O2 y consumio `R3-GOV-HOM-004-O2-REQ1`, pero el push post-merge fallo; no autoriza O3 hasta publicar GOV-CI5 y ejecutar nuevo re-O2.
- PR #437 completo O2 y consumio `R3-GOV-HOM-006-O2-REQ1`, pero el push post-merge fallo; HOM-006 O3-O5 queda superseded y no autoriza O3 hasta publicar GOV-CI7 y ejecutar nuevo re-O2 HOM-007.
- Cualquier DB, Supabase, RLS/grants, backfill, writer, schedule, deploy,
  Certification, Main o produccion requiere R3 JIT separado.

## R3

Certification/Main, DB, deploys, schedules, writers, secrets o acciones
destructivas requieren aprobacion JIT separada.
