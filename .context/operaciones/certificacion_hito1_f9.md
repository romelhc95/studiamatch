# Certificacion Hito 1 - Macrofase F9

> Rebaseline vigente: la adenda CA1-only/CA2-a-Hito-2 esta
> `APPROVED_EFFECTIVE`. F9 queda `COMPLETED_READINESS_F10`; F10.6 quedo
> completada como control-plane y F10.7 quedo registrada como entrega tecnica
> post-main despues de PR #291, boundary final y Cloudflare Pages `SUCCESS`.
> F9.8 quedo cerrada por replay post-merge del
> candidate local CA1-only. La ruta schema/backfill/free_certified queda
> `SUPERSEDED_FOR_HITO_1` y se conserva como antecedente CA2 de Hito 2. Ver
> [ADR-0006](../decisiones/ADR-0006_incorporacion_adenda_sprint_1.md).

Esta nota es la autoridad operativa de la macrofase F9 del plan `main -> Hito 1`.
F9 comienza con preparacion local y, para la ruta CA1-only, termina en readiness
para F10 despues de certificacion final y `USER_PERSONAL_UAT`. No incluye
Production ni cierre final.

La taxonomia y los alias historicos se fijan en [ADR-0003](../decisiones/ADR-0003_taxonomia_macrofases_subfases.md). La informacion vigente del antecedente temporal se preservo en [Preservacion F9.4](./preservacion_plan_temporal_f9_4.md) antes de retirarlo.

## Estado

- Macrofase F9: `COMPLETED_READINESS_F10`.
- Base funcional contractual: F6-F8.
- Estado de certificacion: F9.7 cerrada por rebaseline; F9.8 cerrada por replay post-merge; F9.9 PR #277 fusionado, desviacion `DEVIATION_ACCEPTED_FAIL_CLOSED`, controles pre-main PR #280 mergeados en desarrollo, PR #282 mergeado en `certificacion@bc227629b8df1fcabca47ea7be3ea1d5b4c7667b` y QA independiente `PASS`; PR #283/#284 mergeados en `desarrollo`; PR #285 aprobado/fusionado en `certificacion@5cd27c6f6c35808865b7084673a83f9f690d3760` / tree `419b25f69e4eef4d7277a7439ca45efc1eaac242`; CI post-merge `30865604732=PASS`; run `30865604729=cancelled` con cero pasos; boundary final 32 objetos digest `34f3789d597bf4012378d6e509a03ee6e9ef37edaee95713023421538cab1aa5`; `USER_PERSONAL_UAT=PASS`; Free/Pro permanecen `UNCHANGED_NOT_ATTESTED`; no hubo DDL/DML, backfill, Production ni schedules.
- Subfase tecnica registrada: F10.7 `COMPLETED_TECHNICAL_DELIVERY`; [PLAN-H1-CA1-ONLY-001](./plan_cierre_hito1_ca1_only.md) fija la frontera CA1-only y la desviacion aceptada por HTTP 403 observado desde GitHub-hosted runners.
- Subfase completada por el cierre F10.6: solo control-plane, cancelacion autorizada de runs antiguos con cero pasos, environments fail-closed y activacion documental de F10.7. La entrega tecnica F10.7 no habilita Supabase, schema/RLS, writers remotos, schedules ni canary Production.
- Ultima subfase cerrada: F9.10 `COMPLETED_READINESS_F10`.
- Siguiente accion: F10.8 canary Production y F10.9 schedules/observacion siguen bloqueadas hasta autorizacion decimal exacta.

Base documental post-main: `desarrollo@4c214a789251b5c708186dd5645a01f07714c272` / tree `1496933c636eafa7601a062d2352a490a706585e`. Candidate CA1-only replay-validado: `desarrollo@5b282461149b7319685cf090534e28051e5eb32c`.

## Subfases

| ID | Alcance | Estado | Evidencia o condicion |
|---|---|---|---|
| `F9.1` | Precertificacion local/offline | `COMPLETED` | Alias historico `FASE-09`; PR #231/#232 y cierre #233 |
| `F9.2` | Reparacion local del contrato de promocion | `COMPLETED` | Alias historico `FASE-10`; PR #235/#236 |
| `F9.3` | Freeze local del contrato de preflight | `COMPLETED` | PR #238/#239; replay post-merge Docker sobre checkout Linux limpio |
| `F9.4` | Reconciliacion contractual local/documental | `COMPLETED` | Plan simplificado adoptado; definicion remota sustituida; antecedente temporal retirado |
| `F9.5` | Cierre contractual/documental | `COMPLETED_WITH_KNOWN_FINDINGS` | PR #245/#247 y sus artifacts son `HISTORICAL_NON_PROMOTABLE`; no queda repeticion Free pendiente |
| `F9.6` | P0 H-00 Free-only | `COMPLETED` | `H00_ALREADY_REMEDIATED_NO_DML`; PII directa remediada en la cohorte pseudonimizada; Gate B DELETE `SUPERSEDED_NON_AUTHORIZABLE`; nunca Pro |
| `F9.7` | Rebaseline documental de adenda y cierre CA1-only | `COMPLETED_BY_CONTRACT_REBASELINE` | `EVID-H1-001` verificada de forma sanitizada; PR #268 mergeado en `desarrollo@f8b8987` / tree `3d044210`; no hubo aplicacion remota, DDL/DML, backfill, Certification ni Production |
| `F9.8` | Implementacion y validacion local del candidate CA1-only | `COMPLETED_VERIFIED_POST_MERGE` | PR #270/#271; replay post-merge Docker/Linux sobre `5b28246`: 53 focused PASS, focused FG1/FG2/FG3 y jobs CI PASS, F9.7 congelado 226+7 PASS, runners PG17 PASS, actionlint/ShellCheck 0 issues, LF y credential scan PASS; `EVID-H1-002..005` `VERIFIED` |
| `F9.9` | Candidate selectivo, Certification, canary, QA y controles pre-main | `COMPLETED_QA_VERIFIED` | PR #277 fusionado en `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17`; `EVID-H1-006/007=VERIFIED`; `EVID-H1-008=DEVIATION_ACCEPTED_FAIL_CLOSED`; PR #280 fusionado en `desarrollo@ac7d46e7a09213a10616297323e2d411b8d10954`; QA independiente `PASS`; `EVID-H1-015=VERIFIED` |
| `F9.10` | Certificacion final, `USER_PERSONAL_UAT` y readiness F10 | `COMPLETED_READINESS_F10` | PR #285 fusionado en `certificacion@5cd27c6`; CI `30865604732=PASS`; run `30865604729` cancelado con cero pasos; boundary 32 objetos digest `34f3789d597bf4012378d6e509a03ee6e9ef37edaee95713023421538cab1aa5`; `USER_PERSONAL_UAT=PASS`; F10.6 activa |

La [definicion remota F9.4 anterior](./preflight_free_f9_4.md), el [registro F9.5](./preflight_free_f9_5.md) y la ruta schema/backfill/free_certified son historia no autorizable para Hito 1. Cada subfase pendiente conserva alcance, stop conditions, PR/review y autorizacion exacta propios.

## Cierre Contractual F9.5

F9.5 concluye sin repetir la lectura Free del overlay v2 y sin declarar `FREE_PREFLIGHT_PASS`. Los findings de los intentos historicos permanecen conocidos; no certifican Free/Pro ni se transforman en un package aplicable.

- Los artifacts de PR #245 y PR #247, incluidos migrations, manifests, reducers, runners, pruebas y cambios CI asociados a F9.5, son `HISTORICAL_NON_PROMOTABLE`.
- Se conservan fisicamente y no se incluyen en la base funcional contractual, en un package de F9.7 ni en un candidate de aplicacion. La base contractual sigue siendo F6-F8.
- `T01_CONDITIONAL_ACCEPTED` se acepto como cierre documental sin crear una attestation ni cambiar la maquina de promocion. Habilito solo la definicion entonces futura de F9.6.
- T01 nunca autorizo schema, migrations, F9.7, writers, backfill, Pro ni produccion. La definicion inicial de F9.6 contemplaba backup previo a DELETE; [el cierre posterior](./cierre_h00_f9_6.md) sustituyo esa rama al verificar la remediacion existente y cerrar sin DML.

## Cierre Exclusivo F9.6

F9.6 fue exclusivamente el P0 H-00 de la ruta Free-only sustituida; ya no es prerrequisito del Hito 1 CA1-only y no es criterio contractual. La evidencia sanitizada [EVID-F9.6-H00-001](./cierre_h00_f9_6.md) verifico la cohorte con remediacion completa de PII directa y sin coincidencias parciales o invalidas. Se conserva pseudonimizada por su riesgo residual de vinculabilidad. El resultado es `H00_ALREADY_REMEDIATED_NO_DML`.

- Gate B DELETE queda `SUPERSEDED_NON_AUTHORIZABLE`.
- Los fixtures conservan UUID y metadatos pseudonimizados; el data owner acepta ese riesgo residual en Free restringido y prohibe correlacionarlos o copiarlos a Pro. F9.7 debe verificar ausencia de lectura publica y F11 revaluar retencion.
- DELETE, UPDATE, INSERT, backup valido, acceso Pro, schema, migrations, writers y backfill fueron cero.
- Seguridad y calidad de datos aprobaron la evidencia agregada. Este cierre no certifica Free ni autoriza F9.7.

## Candidate Local Contractual F9.7

El candidate local F9.7 conserva byte-identicas las cuatro migrations F6-F8 y agrega una unica closure forward-only. `db/manifests/fase09_7_free_schema_rls.json` es el descriptor schema v2 de cinco entradas exactas, `reconciled_not_certified` y bloqueado para Free/Pro. Los artifacts F9.5 no son entradas ni insumos. Las pruebas locales cubren PostgreSQL 17, identidad backend, RLS/ACL semantico, rollback, replay, checksums, credenciales y frontend publico.

La [remediacion local del trigger](./remediacion_trigger_f9_7.md) preserva el descriptor v2 como antecedente historico no promocionable y agrega `db/manifests/fase09_7_free_schema_rls_v3.json`, sucesor exacto de seis entradas y unico camino manifest-only local. La sexta migration fija timeouts antes de locks, no bloquea `pg_catalog`, exige el verifier de acceso y fingerprints exactos antes de retirar el trigger y la funcion sin `CASCADE`; la Edge Function historica queda tombstoneada y el [drenaje pg_net](./pg_net_queue_drain_f9_7.md) queda counts-only. El draft remoto de predicates/trigger no fue ejecutado ni conserva capacidad.

[ADR-0005](../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md) agrega el corte local: la arquitectura leads/email queda diferida, el frontend soportado no incluye captura publica y la Edge Function queda tombstoneada solo en Git. El hold actual ya no es terminal promocionable; la ruta futura exige hold sucesor mediante executor privado, y antes del cierre debe demostrar `REMOTE_ABSENT`, `REMOTE_TOMBSTONE_410` o `DISABLEMENT_SEPARATE_AUTHORIZED`. No hay aplicacion remota autorizada.

## Gate B Pre-DDL/Read-Only F9.7

Gate B es exclusivamente pre-DDL y read-only: liga Free; congela commit/tree, package, allowlist y stop conditions; verifica identidad backend y estado de acceso; identifica responsables; y somete resguardo/restore y pausa de writers a aprobaciones humanas separadas. No pausa writers ni aplica schema/migrations.

Un gate F9.7 posterior, todavia no definido ni autorizado, podra aplicar schema/RLS/T02 solo despues de esas aprobaciones. Debera demostrar semanticamente que `leads` y `email_log` no son accesibles por `anon`, `authenticated`, `authenticator` ni `service_role`; el acceso owner queda fuera de la aplicacion. F9.7 no incluye H-00, backfill, Pro ni produccion.

### Resultado Gate B

[EVID-F9.7-GATE-B-001](./gate_b_f9_7.md) ejecuto una unica consulta agregada mediante `supabase-free` y registro `FREE_GATE_B_FAIL_STOPPED_READ_ONLY`. El ledger candidate quedo en un boundary vacio permitido sin colisiones ni entradas F9.5, y la postura de roles/service no mostro faltantes. Sin embargo, el acceso de superficies protegidas no cumplio el estado exigido; el gate se detuvo antes del runner HTTP, de aprobaciones de resguardo/pausa, writers o DDL. La autorizacion se consumio y no es reutilizable.

### Definicion De Remediacion

La [definicion local](./remediacion_gate_b_f9_7.md) congela el package existente sin modificar migrations. PostgreSQL 17 demuestra convergencia para las tres clases directas reducidas y rollback atomico ante policy desconocida o ACL heredada. La atestacion posterior resolvio la atribucion del snapshot, no la convergencia ni los predicates/trigger. Los runbooks de restore y pausa son datos no ejecutables, sin approvals concedidas.

### Atestacion De Origen ACL

[EVID-F9.7-ACL-SOURCE-001](./atestacion_origen_acl_f9_7.md) consumio una unica consulta Free catalog-only y sanitizada. No observo grants heredados/SET, owners publicos, elevacion, ACL desconocida, policy no administrada, view/rule/definer desconocido, publication o particion; `package_source_coverage=complete`. La closure actual sigue incompleta; el mismatch y el trigger conocido mantienen `fail_closed=true`, mientras los predicates no atestados bloquean aplicacion de forma independiente. No hubo filas de negocio, HTTP, DDL/DML remoto en Free/Pro, backup/restore, writers ni Pro.

La definicion local posterior no reutilizo esa lectura. PostgreSQL 17 demuestra que el package sucesor v3 aplica la closure y retira atomicamente la ruta de egress, o revierte schema y ledger completos ante overloads, triggers adicionales, drift de owner/ACL/body/config/timing/evento/nivel/args/WHEN/transition table, mismatch o falla posterior a los drops, al verifier o al append de ledger. Esto no demuestra el snapshot remoto ni habilita ejecucion.

## Dependencias Posteriores

El [contrato PR-O F9.7 executor privado](./pr_o_f9_7_successor_private_executor.md) queda certificado localmente como `CERTIFIED_LOCAL_PR_O_SUCCESSOR` y `SUPERSEDED_FOR_HITO_1`: PR-O v1 y hold actual `SUPERSEDED_NON_PROMOTABLE`, executor privado digest-bound/target-bound/single-use/no Data API y boundary `7` estrictamente read-only se preservan como historia. No habilita preflight remoto, backup/restore, writer pause, `GO_FOR_FREE` ni aplicacion final en Hito 1 CA1-only.

Supabase Free/Pro permanecen `UNCHANGED_NOT_ATTESTED` en este rebaseline; `certificacion` es la rama/release para canary y QA de F9.9. En F9.10, despues de canary, validaciones tecnicas Certification y QA, debe cumplirse `USER_PERSONAL_UAT`: candidate commit/tree inmutable y `PASS` personal explicito del usuario antes de readiness F10. Este hold no agrega criterio contractual, subfase ni transicion nueva.

El backfill editorial queda trasladado a `H2-CA2`; para Hito 1 CA1-only no se planifica, ejecuta ni certifica.

## Cierre F9.8 - Candidate Local CA1-Only

F9.8 termina `COMPLETED_VERIFIED_POST_MERGE`. El candidate CA1-only implementado
por PR #270 y PR #271 fue fusionado en `desarrollo@5b282461149b7319685cf090534e28051e5eb32c`
(merge M, tree `d1fe60a403aa213e8a1beb51d49af12aba727cfd`) y replay-validado en
Docker/Linux dentro de `studiamatch-dev` sobre un checkout limpio.

- Diff `638c51c..M` = exactamente 2 paths de CI (`.github/workflows/f9-7-contract.yml`,
  `tests/test_fase09_8_ca1_candidate.py`), cero paths CA2.
- `EVID-H1-002` (diff CA1-only cero CA2), `EVID-H1-003` (validacion local PASS),
  `EVID-H1-004` (secret scan sin blockers) y `EVID-H1-005` (PR #271 Approved/Merged)
  quedan `VERIFIED`. `EVID-H1-006..016` permanecen `PLANNED` hasta F9.9/F9.10/F10.
- Replay post-merge: 53 pruebas focused F9.8 PASS; focused FG1/FG2/FG3 y jobs CI
  (fase06, fase07-g1b, fase08, fase09) PASS; F9.7 congelado candidate `258ef3a`
  226 passed/5 skipped + attestation ACL 7 passed; runners `run_fase09_7_postgres.sh`
  y `run_fase09_7_leads_email_security_hold_postgres.sh` PASS (exit 0); actionlint
  1.7.7 + ShellCheck 0.9.0 0 issues; LF enforcement y credential scan PASS;
  Context Graph `PASS (85 files, 730 links)`.
- No hubo red remota, DDL/DML, backfill, Certification, canaries, schedules
  observados ni Production. Free/Pro permanecen `UNCHANGED_NOT_ATTESTED`.
- F9.9 queda como subfase activa y requiere la frase exacta
  `Ejecuta las tareas pendientes de la Fase F9.9`; este PR documental no la ejecuta.

## Desviacion F9.9 - Certification Fail-Closed

La decision [ADR-0007](../decisiones/ADR-0007_desviacion_canary_certification_f9_9.md)
formaliza la desviacion `DEVIATION_ACCEPTED_FAIL_CLOSED`:

- PR #277 quedo aprobado y fusionado en `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17`.
- `security-audit`, credential scan, typecheck, lint, Python check y gate `F9.9 Certification Selective Candidate` terminaron en PASS.
- Run `30777088545`: cancelado esperando aprobacion, sin ejecucion ni secretos.
- Run `30781870451`: fail-closed por duplicado normalizado en inventario; cleanup e idempotencia exitosos.
- Run `30782109395`: fail-closed por source slug no configurado; cleanup e idempotencia exitosos.
- Run `30782242009`: FG1 PASS; FG2 fail-closed por HTTP 403; cleanup e idempotencia exitosos.
- Run `30782360475`: FG1 PASS; FG2 fail-closed por HTTP 403; cleanup e idempotencia exitosos.
- La ventana mutable quedo restaurada a `false`; las cohortes intentadas quedaron documentadas como sin markers F9.9 residuales; los artifacts disponibles reportaron conteos no-cohorte sin cambio y QA independiente verifico el aislamiento al nivel demostrado.

Esta evidencia no es un resultado positivo de Certification, no valida FG2 downstream ni FG3, y no habilita F10. La validacion positiva queda desplazada a F10 mediante canary Production acotado y observacion programada posterior, con controles pre-main obligatorios.

La revision independiente de la desviacion queda definida en [QA-F9.9-DEVIATION-001](./qa_desviacion_f9_9.md) y su resultado sanitizado [QA-F9.9-DEVIATION-001-RESULT](./qa_desviacion_f9_9_resultado.md) es `PASS`; `EVID-H1-015=VERIFIED` sin reclasificar Certification como PASS.

## Controles Pre-Main F9.9

El paquete pre-main implementa controles de repositorio antes de cualquier ruta F10:

- `db-sync-to-pro.yml` queda report-only/dry-run para `push` a `main`; el apply
  automatico no existe y el apply manual exige `operation=apply`, autorizacion DDL
  versionada bajo `.context/operaciones/ddl_authorizations/`, candidate SHA igual
  a `origin/main`, backup/PITR verificado, environment `Production` y preflight de writers.
- `fg1_inventory.yml`, `production_pipeline.yml` y `fg3_integrity.yml` reemplazan
  el uso ambiguo de `vars.AUTOMATION_ENABLED` en `job.if` por un preflight con
  environment asociado y outputs explicitos.
- Cada estacion mutante FG1/FG2/FG3 revalida
  `.github/scripts/production_control_preflight.sh` inmediatamente antes de escribir.
- `security-audit.yml` agrega tests bloqueantes de controles pre-main y boundary F10.
- `f9-7-contract.yml` conserva el candidate F9.7 congelado y solo amplia el gate de
  transicion para reconocer la modificacion autorizada de `db-sync-to-pro.yml`.

Este paquete no ejecuta Production, schedules, canaries, Supabase, Cloudflare,
DDL/DML, backup/restore, writers remotos ni PR a `main`. F9.10 permanece sin
autorizacion ejecutable hasta una frase decimal exacta y F10 sigue bloqueada hasta
readiness inequivoca.

PR #280 quedo aprobado/fusionado en `desarrollo@ac7d46e7a09213a10616297323e2d411b8d10954` / tree `695f5a358979a81c380641e8f800ca3ab62c9f6a`; los runs post-merge `30813990225` (`Security Audit Gate`) y `30813989772` (`F9.7 Local Contract`) terminaron `PASS`. Estos controles aun deben reconstruirse selectivamente sobre `certificacion` dentro de F9.10 antes de cualquier readiness F10.

## Readiness F9.10 En Ejecucion

PR #282 reconstruyo selectivamente los controles pre-main sobre `certificacion` y quedo aprobado/fusionado en `certificacion@bc227629b8df1fcabca47ea7be3ea1d5b4c7667b`. CI post-merge `Security Audit Gate` run `30824041279` termino `PASS`. El run `30824041542` de `F9.9 - Certification Canary` termino `PASS` en modalidad read-only/sanitizada: FG1 `--no-insert`, FG2/FG3 skipped y conteos sin cambios; no reemplaza `USER_PERSONAL_UAT` ni reclasifica `EVID-H1-008`.

La ejecucion F9.10 agrego controles antes de F10: `f10-main-boundary` en CI,
canary Production manual `workflow_dispatch` main-only con `candidate_sha`,
preflight `PRODUCTION-CANARY` (automation off + writers paused), snapshot
privado/restore idempotente, artifacts sin slug/SHA/run/digest privado,
`DB-SYNC` permitido solo con writers pausados y subfases F10.6-F10.9/F11.1.
PR #283 quedo fusionado en `desarrollo@5cfd93f626b3362c5c148b1d680ae948ce0218ea`
/ tree `8e6ab8a39de9b9ce1c3a9faf4d0d42e2c5c9c163`, con `Security Audit Gate`
run `30856264196` PASS y F9.7 contract run `30856264217` PASS post-merge. La
proyeccion F9.10 inicial sobre `certificacion@bc227629b8df1fcabca47ea7be3ea1d5b4c7667b`
queda como antecedente superado por PR #285. El cierre final F9.10 congela
`certificacion@5cd27c6f6c35808865b7084673a83f9f690d3760` / tree
`419b25f69e4eef4d7277a7439ca45efc1eaac242`, boundary `main -> certificacion`
de 32 objetos digest `34f3789d597bf4012378d6e509a03ee6e9ef37edaee95713023421538cab1aa5`,
run `30865604729` cancelado con cero pasos y `USER_PERSONAL_UAT=PASS`. No
ejecuta Production, schedules, Supabase, Cloudflare, DDL/DML ni PR a `main`.
La investigacion posterior de F10.7 documentada en
[ADR-0008](../decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md)
verifico que el final de `certificacion` carece de `f10-main-boundary`; por eso
el freeze F9.10 queda como evidencia historica y debe regenerarse para promocion
F10.7.

## Identidades Historicas

- [Precertificacion local F9](./precertificacion_hito1_f9.md) conserva la identidad ejecutable cerrada `FASE-09` y se mapea a F9.1.
- [Contrato local F10](./promocion_hito1_f10.md) conserva descriptor, package y jobs `FASE-10` y se mapea a F9.2.
- El evidence type congelado `f9_completion` significa cierre del package historico `FASE-09`/F9.1, no cierre de la macrofase F9.
- Los nombres historicos no autorizan nuevas operaciones y no se renombran en codigo, manifests, tests o CI.

## Definicion De F9.3

Esta seccion conserva el contrato historico F9.3. Toda referencia futura a F9.4 registra el diseno vigente al cerrar F9.3 y fue sustituida por ADR-0004; no define ni autoriza capacidades actuales.

F9.3 tuvo capability exclusiva `LOCAL_FREE_PREFLIGHT_CONTRACT`. Congelo y probo localmente el contrato que entonces se preveia ejecutar en una F9.4 remota. F9.3 no cargo configuracion de ambiente, no conecto y no produjo `FREE_PREFLIGHT_PASS/FAIL`.

### Entregables F9.3

1. Descriptor inmutable del preflight con package/manifest/commit/tree, inventory y algoritmo de digest exactos.
2. Catalogo cerrado de consultas read-only, parametros, cardinalidad, paginacion, timeouts y shape esperado; cualquier consulta no enumerada falla antes de transporte.
3. Target binding Free por fingerprint no reversible, comparacion constant-time y rechazo de variables genericas/Pro/reutilizadas, sin loggear componentes.
4. Enforcement mecanico de solo lectura: metodos HTTP permitidos cerrados y consultas catalogo dentro de transaccion `READ ONLY`; no se expone primitive SQL/RPC generica.
5. Schema de evidencia sanitizada limitado a PASS/FAIL, conteos agregados y digests; prohibe URLs, refs, keys, filas, UUIDs y detalles explotables.
6. Runner de replay sintetico sin red que demuestre fail-closed ante escritura, query drift, target ambiguo, ledger incompleto, paginacion defectuosa, timeout o evidencia extra.
7. Job CI sin environment/secrets que ejecute solo el contrato local con egress bloqueado.

### Allowlist F9.3

- Nuevo descriptor `db/manifests/f9_3_free_preflight_contract.json`.
- Nuevo runner `scripts/maintenance/free_preflight.py`, sin modo remoto ejecutable en F9.3.
- Nuevas pruebas `tests/test_fase09_free_preflight.py` y fixtures sinteticos locales estrictamente necesarios.
- `.github/workflows/security-audit.yml` solo para un job local sin environment/secrets.
- Esta nota, `estado_del_proyecto.md`, `TASK-H1-001`, changelog y documentacion de cierre F9.3.

Todo path no enumerado queda excluido. F9.3 no modifica manifests/migrations F6-F10, workers, frontend, workflows de aplicacion ni artifacts historicos.

### Prohibiciones F9.3

- Cualquier red remota, Supabase MCP, advisor remoto, PostgREST real o carga de `.env*`/secrets.
- DDL, DML, RPC, `exec_sql`, backups, writers, H-00, backfill, migrations, workflow dispatch o cambios de status.
- Crear attestations, evidencia Free o presentar tests sinteticos como readiness.
- Implementar un flag, funcion o primitive que permitiera transporte dentro de F9.3.

### Gates F9.3

1. Esta reconciliacion y definicion deben pasar Context Graph, auditorias, CI, review y merge.
2. Despues del merge se requiere la frase exacta `Ejecuta las tareas pendientes de la Fase F9.3`.
3. La implementacion F9.3 no puede conectar; solo congela consultas, evidencia, target binding y enforcement con pruebas sinteticas.
4. El candidate F9.3 debe recibir auditorias, CI, review, merge, replay post-merge y PR documental de cierre.
5. El gate historico exigio cerrar F9.3 antes de la F9.4 remota entonces prevista y conservar sus artifacts; ADR-0004 sustituyo despues esa ruta sin reescribir la evidencia.

### Evidencia De Cierre F9.3

- Autorizacion exacta recibida: `Ejecuta las tareas pendientes de la Fase F9.3`.
- Descriptor/runner local: `LOCAL_VALID`, con `git_proof=EXTERNAL_REQUIRED`; no afirma readiness ni produce PASS/FAIL remoto.
- Suite focused: 55 pruebas PASS. Regresion F6-F10/credenciales: 253 pruebas PASS y un warning heredado de PyPDF2; total scoped 308.
- Replay sintetico determinista: 22 checks PASS. `py_compile`, `git diff --check` y Context Graph 30 archivos/232 enlaces: PASS.
- SHA-256 fijado del runner: `543cff44e46f84326ae774009a58ccf4fb7d0525ff0797cd5cca561706e45a00`.
- PR #238: CI verde, aprobacion de `romelhc95-approver` y merge humano en `desarrollo@4e712b0`.
- El primer replay post-merge encontro que el fixture temporal construia un blob CRLF desde el bind mount Windows aunque el validador comparaba correctamente identidad LF. PR #239 limito la remediacion al fixture, agrego la regresion CRLF, recibio CI/auditorias/review en GO y fue fusionado.
- Replay definitivo: `desarrollo@4e77fe0`, tree `efdf3f4edb53a384ee5f2a6251131696ccfb1865`, checkout limpio `i/lf w/lf` en el filesystem Linux interno de `studiamatch-dev`, sin ejecutar Python sobre el bind mount Windows. Pasaron 55 pruebas focused, 253 de regresion, 22 checks sinteticos, `py_compile` y Context Graph 30/232.
- Auditorias finales security y QA: GO, cero hallazgos bloqueantes. CI ejecuto el job F9.3 bajo `unshare --net`; el contenedor local carece deliberadamente de `CAP_SYS_ADMIN`, por lo que el replay local mantuvo ambiente vacio, runner sin transporte y bloqueo de sockets en pruebas. Los gaps de adapter, target identity artifact y traces fueron asignados entonces a una F9.4 remota, luego sustituida.
- Acceso Free/Pro, Supabase MCP, secrets, `.env*`, DDL/DML/RPC remoto, attestations y transiciones de estado: cero.
- El PR documental que contiene esta evidencia completa F9.3 al fusionarse. No define, autoriza ni ejecuta F9.4.

## Definicion Sustituida De F9.4

La anterior [definicion F9.4](./preflight_free_f9_4.md) queda `SUPERSEDED_NON_AUTHORIZABLE`. F9.4 fue redefinida y completada como reconciliacion contractual local/documental; nunca implemento adapter ni accedio a Free/Pro. Los artifacts F9.3 permanecen historicos y byte-identicos, pero no gobiernan F9.5 ni crean criterios adicionales.

## Preservacion De La Secuencia Original F9

| Paso original | Asignacion canonica obligatoria |
|---|---|
| Validacion Free del package exacto | `SUPERSEDED_FOR_HITO_1`; antecedente CA2 de Hito 2 |
| H-00 Free-only counts-only | F9.6 |
| ACL negativas `anon`/`authenticated` | Antecedente CA2; no cierre Hito 1 CA1-only |
| ACL negativa `service_role` sobre `leads`/`email_log`; identidad de servicio se conserva para superficies autorizadas | Antecedente historico; no cierre Hito 1 CA1-only |
| Smoke FG2 sin fallback de persistencia | F9.9/F9.10 segun candidate CA1-only |
| Cleanup idempotente | F9.9/F9.10 segun candidate CA1-only |
| Hold operativo `USER_PERSONAL_UAT` con candidate commit/tree inmutable y PASS personal del usuario | F9.10, despues de canary, validaciones tecnicas Certification y QA |
| PR a `desarrollo` si el candidate nace temporal | Cada subfase aplicable; comprobacion final F9.10 |
| Promocion nueva a `certificacion` | F9.10 con review/CI |
| Canary Certification desde candidate exacto | F9.9/F9.10 |
| QA independiente | F9.9/F9.10: definicion y revision de desviacion en F9.9; confirmacion final de readiness en F9.10 |
| Readiness F10 | F9.10 completada; sustituye `FREE_CERTIFIED` para Hito 1 CA1-only |

## Gates Humanos Preservados Y Sustituidos

- F9.6 cerro H-00 con PII directa ya remediada y la cohorte conservada como pseudonimizada, sin DML; Gate B DELETE fue sustituido y no puede reabrirse desde esta macrofase.
- La ruta de migration Free y backup/restore de F9.7 queda `SUPERSEDED_FOR_HITO_1`; cualquier operacion equivalente futura requiere hito, subfase decimal y aprobacion propios.
- La pausa/reanudacion de writers de la ruta F9.7 queda `SUPERSEDED_FOR_HITO_1`; F9.10 CA1-only no reanuda writers Free.
- Plan y ejecucion de backfill quedan fuera de Hito 1 y se trasladan a Hito 2.
- `USER_PERSONAL_UAT` en F9.10 requiere candidate commit/tree inmutable y `PASS` personal del usuario despues de canary, validaciones tecnicas Certification y QA.
- Cada merge a `desarrollo` y el merge a `certificacion` requieren aprobacion humana y CI en la subfase aplicable/F9.10.
- T04 y `free_final_certification_approval` quedan sustituidos para Hito 1; F9.10 CA1-only certifica candidate, canary, QA, `USER_PERSONAL_UAT` y readiness F10.
- Cualquier promocion Supabase Pro de la ruta CA2 queda fuera de Hito 1; F10 CA1-only conserva aprobaciones separadas para Production sin adoptar Free/Pro schema/backfill.
- Eliminar ramas remotas pertenece a F11 y requiere aprobacion propia; el antecedente temporal ya fue retirado documentalmente en F9.4.

## Criterio De Salida De La Macrofase F9

F9 termino para Hito 1 CA1-only con candidate selectivo inmutable,
`EVID-H1-008=DEVIATION_ACCEPTED_FAIL_CLOSED`, QA independiente, controles
pre-main, certificacion final, boundary `main -> certificacion` y
`USER_PERSONAL_UAT=PASS`. F10.6 cerro control-plane y F10.7 registro entrega
tecnica post-main; canary Production, schedules y conformidad siguen bloqueados
hasta sus autorizaciones F10.8/F10.9/F11.1.

Ver [Estado](../estado_del_proyecto.md), [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Release minimo](./flujo_release_minimo.md) y [Matriz DB](./matriz_adopcion_db.md).
