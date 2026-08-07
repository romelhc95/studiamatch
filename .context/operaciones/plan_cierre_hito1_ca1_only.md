# PLAN-H1-CA1-ONLY-001 - Cierre Productivo De Hito 1

| Campo | Valor |
|---|---|
| ID | `PLAN-H1-CA1-ONLY-001` |
| Estado | `F10_8_DB_SYNC_FAIL_CLOSED_REMEDIATION_REQUIRED` |
| Requerimiento | `REQ-EST-001` |
| Hito | `HITO-001` |
| Criterio | `H1-CA1` |
| Autoridad habilitante | [ADENDA-REQ-EST-001-001](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md) |

Este plan queda vigente por adenda aprobada y rebaseline del Context Graph. No
ejecuta por si mismo: F9.8 quedo cerrada por replay post-merge; F9.9 documento
PR #277, una desviacion Certification fail-closed, controles pre-main PR #280 y
QA independiente `PASS`. F9.10 quedo cerrada con PR #285, boundary final y
`USER_PERSONAL_UAT=PASS`; F10.6 quedo completada como control-plane. F10.7 quedo
registrada como entrega tecnica post-main por PR #291. F10.8 promovio por PR #297
la remediacion de Production Canary a `main@260900a268ab8eb194140ea7311aec2a170b6e17`
y obtuvo Certification Canary `31140933096=PASS`, pero el workflow
`DB Sync to Production` fallo fail-closed antes de Supabase en el push post-merge
porque no omitio la ruta DB en un candidate sin cambios `db/**`. Schedules,
Production Canary acreditable y fases posteriores permanecen bloqueados hasta
autorizaciones separadas.

## Objetivo

Cerrar Hito 1 en produccion con CA1 exclusivamente: schedules y operacion
segura del pipeline sin omitir gates, circuit breakers ni controles de
ambiente. Los avances CA2 se documentan y permanecen fuera del candidate.

## Criterio Contractual Sanitizado

- Schedules del harvester/pipeline quedan definidos o reactivados.
- Gates y circuit breakers no se omiten.
- Secrets existen solo en CI y nunca en browser.

FG1 se valida como soporte operacional de inventario, sin crear un criterio
contractual adicional.

## Gates Internos De Ingenieria

La promocion por PR, SSRF, clasificacion HTTP, paginacion, mutaciones
confirmadas, kill switch y las 16 evidencias son controles internos de calidad,
seguridad y release. No amplian el CA1 cliente ni crean entregables comerciales
adicionales.

La discrepancia historica sobre el estado de FG3 se resuelve como verificacion
interna necesaria para reactivar el schedule, no como criterio cliente nuevo.

## Frontera CA1-Only

### Permitido

- FG1 como soporte operativo.
- FG2 y FG3 como alcance CA1.
- Workflows FG1/FG2/FG3 y sus lockfiles CA1.
- Orquestacion, gates, circuit breaker, limites y timeouts.
- Seguridad operacional: refs, environments, actions SHA y permisos minimos.
- Manejo fail-closed, SSRF, paginacion y evidencia sanitizada necesaria para
  ejecutar CA1 responsablemente.
- Tests y CI que prueben exclusivamente esta frontera.

### Prohibido

- `db/**`, `supabase/**` y `web/**`.
- Schema, migrations, RLS, RPC, grants y backfill CA2.
- Campos editoriales, calidad, faltantes, fuentes, sponsorship o leads.
- Leads/email, Edge y artifacts terminales F9.7.
- Admin, Home, Resultados, cards, filtros y campos CA2.
- Tooling capaz de aplicar packages DB.

## Estrategia De Candidate Selectivo

`desarrollo` contiene cambios mixtos y no puede promoverse completo. El release
usa una frontera por patch:

1. F9.8 implementa y valida localmente CA1 en una rama limpia.
2. Congela diff, patch-id, commit/tree y hashes CA1 aprobados.
3. F9.9 reconstruye solo ese patch sobre el baseline de Certification.
4. F9.9 prueba equivalencia, ausencia CA2, canary y QA.
5. F9.9 cierra QA independiente y controles pre-main de repositorio antes de readiness.
6. F9.10 realiza certificacion final, `USER_PERSONAL_UAT` y readiness para F10.
7. F10.7 ejecuta PR a `main` y registra entrega tecnica post-merge.
8. F10.8 ejecuta canary Production con schedules apagados.
9. F10.9 habilita schedules gradualmente y observa la operacion.

Nunca se mezcla `desarrollo` dentro del candidate. Un conflicto que requiera
copiar CA2 invalida el candidate y obliga a reconstruirlo.

## Desviacion Certification F9.9 Aceptada

La decision [ADR-0007](../decisiones/ADR-0007_desviacion_canary_certification_f9_9.md)
registra `EVID-H1-008=DEVIATION_ACCEPTED_FAIL_CLOSED`. Esta desviacion acepta la
evidencia de comportamiento fail-closed ante HTTP 403 observado desde egress
compartido de GitHub-hosted runners, pero prohibe declarar un resultado positivo de Certification.

Evidencia sanitizada:

| Run | Resultado |
|---|---|
| `30777088545` | Cancelado esperando aprobacion; sin ejecucion ni secretos. |
| `30781870451` | FAIL por duplicado normalizado en inventario; cleanup e idempotencia exitosos. |
| `30782109395` | FAIL por source slug no configurado; cleanup e idempotencia exitosos. |
| `30782242009` | FG1 PASS; FG2 FAIL por HTTP 403; cleanup e idempotencia exitosos. |
| `30782360475` | FG1 PASS; FG2 FAIL por HTTP 403; cleanup e idempotencia exitosos. |

Condiciones de la desviacion:

- Solo cubre egress observado en Certification; no cubre credenciales, RLS, target Supabase, secretos, CA2, cleanup fallido ni mutaciones fuera de alcance.
- La ventana mutable quedo restaurada a `false` y no se ejecuta Production en esta documentacion.
- Los stages FG2 downstream y FG3 siguen sin validacion positiva.
- La validacion positiva se desplaza a F10: canary Production acotado y observacion programada posterior, ambos sujetos a controles pre-main.
- La desviacion expira al completar la observacion Production en F10 o ante el primer fallo que demuestre que el problema no era exclusivo del egress observado en Certification.

La definicion QA obligatoria para `EVID-H1-015` vive en [QA-F9.9-DEVIATION-001](./qa_desviacion_f9_9.md). Su resultado sanitizado [QA-F9.9-DEVIATION-001-RESULT](./qa_desviacion_f9_9_resultado.md) queda en `PASS`; no declara Certification PASS ni autoriza Production, schedules, F9.10/F10, Supabase, Cloudflare o DDL/DML.

## Controles Pre-Main F9.9

Este paquete implementa controles de repositorio para que F10 no pueda iniciar con
writers productivos ambiguos:

- `.github/workflows/db-sync-to-pro.yml` ejecuta report/dry-run en `push` a
  `main`; el apply queda limitado a `workflow_dispatch` con `operation=apply`,
  `apply_authorized=true`, `backup_pitr_verified=true`, autorizacion `DDL-*`,
  aprobacion del environment `Production`, candidate SHA igual a `origin/main`,
  registro versionado `.context/operaciones/ddl_authorizations/<DDL-ID>.md` y
  preflight `PRODUCTION_WRITERS_PAUSED`.
- `.github/scripts/production_control_preflight.sh` centraliza el gate fail-closed
  de `AUTOMATION_ENABLED` y `PRODUCTION_WRITERS_PAUSED`, sin leer secretos ni red.
- `fg1_inventory.yml`, `production_pipeline.yml` y `fg3_integrity.yml` resuelven
  el gate en un job con environment asociado y usan outputs explicitos; los jobs
  mutantes revalidan el preflight inmediatamente antes del writer.
- `security-audit.yml` agrega el job bloqueante `F9.9 Pre-Main Repository Controls`
  con `tests/test_fase09_9_pre_main_controls.py` y
  `tests/test_fase10_main_boundary.py`.

No se ejecutan workflows remotos, no se configuran environments reales, no se
habilitan schedules, no se abre PR a `main`, no hay DDL/DML y no se accede a
Supabase ni Cloudflare en este paquete.

### Cierre Controles Pre-Main Y QA - 2026-08-03

- PR #280 aprobado/fusionado en `desarrollo@ac7d46e7a09213a10616297323e2d411b8d10954` / tree `695f5a358979a81c380641e8f800ca3ab62c9f6a`.
- CI post-merge sobre `desarrollo@ac7d46e7a09213a10616297323e2d411b8d10954`: `Security Audit Gate` run `30813990225` PASS y `F9.7 Local Contract` run `30813989772` PASS.
- QA independiente de la desviacion: [resultado sanitizado](./qa_desviacion_f9_9_resultado.md) `PASS`; `EVID-H1-015=VERIFIED`.
- `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17` aun no contiene los controles pre-main de PR #280; F9.10 debe reconstruirlos selectivamente antes de cualquier readiness F10.

### Readiness F9.10 En Ejecucion - 2026-08-03

- PR #282 reconstruyo selectivamente los controles pre-main sobre `certificacion` y quedo aprobado/fusionado en `certificacion@bc227629b8df1fcabca47ea7be3ea1d5b4c7667b` / tree `b2edda7c538b7e74abe0bcaf59715e9d3f4b9327`.
- CI post-merge `Security Audit Gate` run `30824041279` PASS sobre `bc227629b8df1fcabca47ea7be3ea1d5b4c7667b`.
- `F9.9 - Certification Canary` run `30824041542` PASS se acepta solo como evidencia read-only/sanitizada: FG1 uso `--no-insert`, FG2/FG3 quedaron skipped, no hubo DML, y los conteos pre/post/after-cleanup no cambiaron. Artifact sanitizado `f9-9-certification-canary-manifests-30824041542-1`, digest `sha256:ff6f4caeb20df0afa3e1778dd363f3e3f2f7a01ecfb4362a098401a868f88f4b`.
- Esta evidencia no sustituye `USER_PERSONAL_UAT`, no cambia `EVID-H1-008=DEVIATION_ACCEPTED_FAIL_CLOSED`, no valida Production y no habilita schedules.
- F9.10 agrega controles de repositorio previos a F10: gate CI dedicado para boundary `main`, canary Production manual SHA-bound con snapshot privado/restore idempotente, preflight `PRODUCTION-CANARY` con automation off + writers paused, correccion `DB-SYNC` vs writers y rollback documentado.
- El gate `f10-main-boundary` conserva una allowlist exacta para objetos CA1 historicos ya presentes en `certificacion` que deben poder promoverse a `main`: `requirements-db-migrate.txt` como dependencia operativa hash-locked, `scripts/core/certification_canary_state.py` y `tests/test_fase09_9_certification_canary.py` como controles/evidencia F9.9, y `scripts/shared/roi_engine.py` solo como separacion de identidad backend requerida por `sync_vector_worker.py`. Esta clasificacion no permite CA2, prefijos amplios ni nuevos cambios fuera de allowlist.
- `USER_PERSONAL_UAT` fue ejecutado despues del merge selectivo F9.10 en `certificacion`, ligado al SHA/tree final congelado. Checklist sanitizado completado: paquete CA1-only confirmado; `EVID-H1-008` sigue como `DEVIATION_ACCEPTED_FAIL_CLOSED` y no como PASS; Production, schedules y F10 seguian bloqueados al momento del hold; `USER_PERSONAL_UAT=PASS` aceptado explicitamente para ese SHA/tree sin registrar PII, secretos, slugs de cohortes ni identificadores internos.
- El canary Production que podra acreditar `EVID-H1-010` debe ejecutarse en F10.8 con `run_fg1=true`, `run_fg2=true`, `run_fg3=true`, `mutable_authorized=true` y limites `5/5/3/3/3`. Runs FG2-only o FG3-only son diagnosticos y no acreditan `EVID-H1-010`. `EVID-H1-013` exige FG1 manual equivalente PASS y cron mensual activo; un waiver requiere decision humana separada con responsable y fecha.

### Correccion F9.10 Posterior A PR #283 - 2026-08-03

- PR #283 quedo aprobado/fusionado en `desarrollo@5cfd93f626b3362c5c148b1d680ae948ce0218ea` / tree `8e6ab8a39de9b9ce1c3a9faf4d0d42e2c5c9c163`; head final `9b4f5e3f06a31b630cc644c54e63ce26d0f96ffb`, mergeado por `romelhc95-approver`.
- CI del PR #283: `security-audit`, `F10 Main Boundary And Production Canary`, `F9.9 Pre-Main Repository Controls`, credential scan, lint, typecheck, frontend build, Python check y contratos F6-F10 en `success`.
- CI post-merge de `desarrollo@5cfd93f626b3362c5c148b1d680ae948ce0218ea`: `Security Audit Gate` run `30856264196` PASS y `F9.7 Public Access, Trigger Retirement, and Security Hold PostgreSQL 17 Contract` run `30856264217` PASS.
- Refs revalidadas antes de esta correccion: `desarrollo@5cfd93f626b3362c5c148b1d680ae948ce0218ea` / tree `8e6ab8a39de9b9ce1c3a9faf4d0d42e2c5c9c163`, `certificacion@bc227629b8df1fcabca47ea7be3ea1d5b4c7667b` / tree `b2edda7c538b7e74abe0bcaf59715e9d3f4b9327`, `main@d8f1ea0b210f2a1cf95e73751621cf8b4fcf0f93` / tree `0c7d31a392612001b786e2ef680cc0be3d1b4c18`.
- Este paquete correctivo no abre PR a `certificacion` ni `main`. Tampoco ejecuta workflow dispatch, canary, Supabase, Cloudflare, DDL/DML, backup/restore real, writers, schedules, environments/secrets ni aprobacion de runs antiguos.

La proyeccion selectiva calculada desde `certificacion@bc227629b8df1fcabca47ea7be3ea1d5b4c7667b` hacia los blobs de `desarrollo@5cfd93f626b3362c5c148b1d680ae948ce0218ea` contiene exactamente 23 paths. El digest de control `projection_digest_sha256` es `2459cedda5542c81eb5bafca460148ebb6b65551c865fdcbe174ccee02edfb36`, calculado sobre JSON ordenado por `path` con claves `blob`, `kind`, `mode`, `path`, `status`, `sort_keys=true` y separadores compactos. Este digest congela PR #283 como fuente, pero no sustituye el re-freeze obligatorio despues del merge de este PR correctivo.

| Status | Mode | Blob | Path |
|---|---|---|---|
| `A` | `100644` | `15c7b1ce5a2c0f00a05d85f2d3766769c66aaa55` | `.context/arquitectura/05_despliegue_ambientes.md` |
| `A` | `100644` | `145a3965a96d1791a09a42b14cc6e440175a7144` | `.context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md` |
| `A` | `100644` | `a68f68ca54f4489fa25d6ed947f06459bb037271` | `.context/estado_del_proyecto.md` |
| `M` | `100644` | `4544abfbd04ed73f3efac7311b9eceec8c8f3294` | `.context/evidencias_cliente/sprint_1/paquete_hito_001.md` |
| `A` | `100644` | `d7b8629650444ffd18cfa87c6d109c88b5a623f7` | `.context/operaciones/certificacion_hito1_f9.md` |
| `A` | `100644` | `b67c290a81bcda6a8292bdbea0c88d20c6463324` | `.context/operaciones/flujo_release_minimo.md` |
| `M` | `100644` | `8d8a73a4b1d1eaf9db7b3c234c0ecdca2ab177b7` | `.context/operaciones/plan_cierre_hito1_ca1_only.md` |
| `A` | `100644` | `b81652d02e0fdaccd2eeb8b273f23db7ca4b5611` | `.gitattributes` |
| `M` | `100644` | `b4ad7e59b66e60cb1a64bc8d68c812611c75be32` | `.github/scripts/production_control_preflight.sh` |
| `A` | `100644` | `d4a3ea305081e789b86a04370736d810e93f4480` | `.github/workflows/f9-7-contract.yml` |
| `A` | `100644` | `8959c4b8f90afe0d75f23bb6e0f99d51321f1c45` | `.github/workflows/production_canary.yml` |
| `M` | `100755` | `8435c79855d7f3dc05eb5f6174d2ae82f0c477e4` | `.github/workflows/security-audit.yml` |
| `M` | `100644` | `44cc4dbb925f94b67ad343ea2d8bb09f7bd3f7c0` | `scripts/core/cleansing_worker.py` |
| `M` | `100644` | `85d94e148e65263d7314fc3e57ac8e1da41265dc` | `scripts/core/enrichment_worker.py` |
| `A` | `100644` | `12e42b91b8d2a9d71611d8d175ae22c76a858fd1` | `scripts/core/production_canary_manifest.py` |
| `A` | `100644` | `2a48f77f613098f626b709d7c795b24da7a3f86c` | `scripts/core/production_canary_state.py` |
| `M` | `100644` | `95179835ef7c9dffadd8c697ed395f02f0398c3e` | `scripts/core/sync_vector_worker.py` |
| `M` | `100644` | `3bf3a6f03fcfa245469e8603e80e49f6c679601f` | `scripts/core/universal_harvester.py` |
| `M` | `100644` | `29cc1616b18a0c079017449b754f599280199d11` | `tests/test_fase09_10_pre_main_controls.py` |
| `A` | `100644` | `bd960428eb987ab28d5cfe38c19a34a15616b548` | `tests/test_fase09_7_release_gates.py` |
| `M` | `100644` | `741d44cefea8578831c8d4705ba73c1617474cbc` | `tests/test_fase10_main_boundary.py` |
| `A` | `100644` | `9e43a19aa8b62d270b5f5cbc72edb978331349c3` | `tests/test_fase10_production_canary.py` |
| `M` | `100644` | `4f43932220f3e1c5045a1bed82b585deb777ae46` | `tests/test_supabase_credentials_contract.py` |

La proyeccion virtual `main@d8f1ea0b210f2a1cf95e73751621cf8b4fcf0f93 -> certificacion` despues de aplicar exactamente los 23 objetos anteriores sobre `bc227629b8df1fcabca47ea7be3ea1d5b4c7667b` contiene 40 blobs y digest `future_main_boundary_digest_sha256=479e55e90f5cdf341b565335d088dc07bc7e65bc95ea9dc5b784fd9b1daa8a47`. Este valor es referencia de sanity-check, no autorizacion F10.7: debe recalcularse con el SHA/tree final de `certificacion` despues del replay selectivo y antes del PR `certificacion -> main`.

Blockers resueltos por esta definicion:

- CI: `certificacion@bc227629b8df1fcabca47ea7be3ea1d5b4c7667b` es el baseline exacto; cualquier drift de base invalida la segunda F9.10 y exige nuevo rebaseline.
- Seguridad: la proyeccion aprobada es por paths exactos, status, mode y blob; no acepta prefijos amplios, `db/**`, `supabase/**`, `web/**`, `.env*`, datos operativos ni CA2.
- Canary: `EVID-H1-010` queda reservado a F10.8 con FG1+FG2+FG3, `mutable_authorized=true`, limites `5/5/3/3/3`, host Pro allowlisted, snapshot privado, restore y segundo restore NOOP; runs parciales no acreditan cierre.
- Rollback: un canary con perdida de snapshot privado, restore fallido, runner perdido o artifacts no sanitizados falla y deja schedules apagados hasta autorizacion nueva.

Blockers de esta definicion: `SUPERSEDED_BY_F9_10_FINAL_FREEZE_2026_08_04`.
La proyeccion de 23 paths queda historica porque PR #285 aplico una
reconstruccion target-aware de 15 paths sobre `certificacion` y produjo el
boundary final `main -> certificacion` de 32 objetos documentado abajo.

### Cierre F9.10 Y Readiness F10 - 2026-08-04

- PR #285 quedo aprobado por `romelhc95-approver` y fusionado en
  `certificacion@5cd27c6f6c35808865b7084673a83f9f690d3760` / tree
  `419b25f69e4eef4d7277a7439ca45efc1eaac242`.
- CI post-merge `Security Audit Gate` run `30865604732` termino `PASS`.
- Run automatico `F9.9 - Certification Canary` `30865604729` quedo
  `cancelled` con job `Certification Canary` sin pasos ejecutados (`steps=[]`);
  no hubo aprobacion de environment, retry, Production, schedules ni DML.
- `USER_PERSONAL_UAT=PASS` fue emitido por el usuario para el SHA/tree final,
  confirmando paquete CA1-only, `EVID-H1-008=DEVIATION_ACCEPTED_FAIL_CLOSED` y
  Production/schedules/F10 bloqueados al momento del hold.
- Boundary final `main@d8f1ea0b210f2a1cf95e73751621cf8b4fcf0f93` / tree
  `0c7d31a392612001b786e2ef680cc0be3d1b4c18` hacia `certificacion` contiene
  32 objetos y `main_boundary_digest_sha256=34f3789d597bf4012378d6e509a03ee6e9ef37edaee95713023421538cab1aa5`.
- Filtro de rutas prohibidas y busqueda CA2 no encontraron implementacion en
  `db/**`, `supabase/**`, `web/**`, `scripts/maintenance/**`, `.env*`,
  leads/email, Edge, backfill o superficies CA2; los terminos CA2 restantes son
  exclusiones documentales/gates.

| Status | Mode | Blob | Path |
|---|---|---|---|
| `A` | `100644` | `fb9b14ec04301fdafa35544d2984aa0aac045222` | `.context/evidencias_cliente/sprint_1/paquete_hito_001.md` |
| `A` | `100644` | `c6433840c6966b5275f9ca23a5a8fd8e709db338` | `.context/operaciones/plan_cierre_hito1_ca1_only.md` |
| `A` | `100644` | `430babc1a17c02f2d86e6451a4991ef2cd10c46d` | `.gitattributes` |
| `A` | `100644` | `b4ad7e59b66e60cb1a64bc8d68c812611c75be32` | `.github/scripts/production_control_preflight.sh` |
| `M` | `100644` | `3f6e39c8d24492f83b30b12b7b268af3a2b6b33d` | `.github/workflows/db-sync-to-pro.yml` |
| `A` | `100644` | `147b19537bc52416adb9931cdb7ec9b66976a6a5` | `.github/workflows/f9_9_certification_canary.yml` |
| `M` | `100644` | `7700a9923a28503f2d45d0e8266bb307023b8f42` | `.github/workflows/fg1_inventory.yml` |
| `M` | `100644` | `1191404cfd9aad537eda3846797192c36df565cf` | `.github/workflows/fg3_integrity.yml` |
| `A` | `100644` | `8959c4b8f90afe0d75f23bb6e0f99d51321f1c45` | `.github/workflows/production_canary.yml` |
| `M` | `100644` | `b8fffaec1244797d2e27ff69bb2012d27f689e6a` | `.github/workflows/production_pipeline.yml` |
| `M` | `100755` | `3fefa46857960841873dbd735de3c53a4d415a0e` | `.github/workflows/security-audit.yml` |
| `A` | `100644` | `310875d24631062e8cd8e92d8342366de87cc260` | `requirements-db-migrate.txt` |
| `A` | `100644` | `01508b0cc631180cda560f0f4c6ba77d5359d296` | `requirements-fg1.txt` |
| `A` | `100644` | `7704ae22a36d20d5c39af234808273c18c4194f2` | `requirements-fg3.txt` |
| `A` | `100644` | `38bbc3f369b949602b1dd668d2e6f16805cdb586` | `requirements-pipeline.txt` |
| `A` | `100644` | `5ce27cd6d8458178dcbc8438d3ab2132f90c1f51` | `scripts/core/certification_canary_manifest.py` |
| `A` | `100644` | `430083ee8f393fcb7e81220019ba20d2aa125754` | `scripts/core/certification_canary_state.py` |
| `M` | `100644` | `c7dc5bae98faed54a0d67282fd0eee95744147bd` | `scripts/core/cleansing_worker.py` |
| `M` | `100644` | `95d76e6dd25bf0f8f68fc470524ab0735a05ecde` | `scripts/core/discovery_institutions.py` |
| `M` | `100644` | `1217cbb777a8740e922c632c2fe439174026ec28` | `scripts/core/enrichment_worker.py` |
| `M` | `100644` | `337bfddc0b3d32f06e00e6d054de151b95e02032` | `scripts/core/integrity_ping.py` |
| `M` | `100644` | `699a40ec809e67516be7763a3911e9f2a2e96348` | `scripts/core/master_orchestrator.py` |
| `A` | `100644` | `12e42b91b8d2a9d71611d8d175ae22c76a858fd1` | `scripts/core/production_canary_manifest.py` |
| `A` | `100644` | `2a48f77f613098f626b709d7c795b24da7a3f86c` | `scripts/core/production_canary_state.py` |
| `M` | `100644` | `e4cd7b0b3d7796369b3c126b0c9e240e4487509e` | `scripts/core/sync_vector_worker.py` |
| `M` | `100644` | `3507bb0bd254bc0d705f301b8858a93f119ac0be` | `scripts/core/universal_harvester.py` |
| `M` | `100644` | `b9e939cdf787458304d9056e65a3d0971d725d35` | `scripts/shared/db_client.py` |
| `M` | `100644` | `7acac703f5f8aa710db516d4a2eabd773d0bd2cd` | `scripts/shared/roi_engine.py` |
| `A` | `100644` | `a9612d33c6e03db07a83afc1c1da7319e8726774` | `tests/test_fase09_10_pre_main_controls.py` |
| `A` | `100644` | `b4b368cf5aa8cb98e6c02c3b5f8c1290ca380183` | `tests/test_fase09_9_certification_canary.py` |
| `A` | `100644` | `7cc10e90b426429403ad494bb766fbf99bc222ea` | `tests/test_fase10_main_boundary.py` |
| `A` | `100644` | `3c9c1e140db81f2bce697100aa98e4530b31f09e` | `tests/test_fase10_production_canary.py` |

Con este freeze F9.10 termino como `COMPLETED_READINESS_F10`; F10.6 quedo
`COMPLETED_CONTROL_PLANE` despues de verificar environments fail-closed y
cancelar runs legacy con cero pasos. El siguiente paso requiere la frase exacta
`Ejecuta las tareas pendientes de la Fase F10.7` y no concede por si mismo
canary Production, schedules ni cambios remotos fuera del PR autorizado.

### Rebaseline F10.7 Cycle 1 - 2026-08-04

La investigacion read-only de F10.7 verifico que el estado final de
`certificacion@5cd27c6f6c35808865b7084673a83f9f690d3760` no contiene
`.github/workflows/f9-7-contract.yml` ni el job bloqueante `f10-main-boundary`.
El PR directo `certificacion -> main` queda bloqueado porque el gate main/F10
documentado en F9.10 no estaria presente en la rama candidata.

La decision [ADR-0008](../decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md)
reclasifica el freeze de 32 objetos y `USER_PERSONAL_UAT=PASS` como
`SUPERSEDED_FOR_F10_7_PROMOTION`. Siguen siendo evidencia historica de F9.10,
pero F10.7 Cycle 2 debe producir una nueva autoridad de promocion.

El plan definido para Cycle 2, condicionado a nueva autorizacion decimal exacta,
fue:

- reconstruir en `desarrollo` y luego selectivamente en `certificacion` solo
  `.github/workflows/security-audit.yml`, `.github/workflows/opencode.yml` y
  `tests/test_fase10_main_boundary.py`;
- no promover `.github/workflows/f9-7-contract.yml`;
- agregar `f10-main-boundary` como gate bloqueante y agregado por
  `security-audit` para PR `certificacion -> main`;
- endurecer `opencode.yml` o deshabilitar el workflow secret-bearing si no puede
  pinnearse con SHA confiable;
- prevenir y verificar que Cloudflare Pages no despliegue automaticamente al
  recibir un push en `main`;
- cancelar con cero pasos el run automatico `F9.9 - Certification Canary` tras
  reconstruir `certificacion`;
- recalcular el boundary `main -> certificacion`; bajo el alcance de tres paths
  el conteo esperado es 33 por la entrada nueva `.github/workflows/opencode.yml`;
- registrar variables no secretas aprobadas de SHA, tree, count y digest del
  freeze, obtener `USER_PERSONAL_UAT=PASS` nuevo y solo entonces abrir el PR a
  `main`;
- cancelar `DB Sync to Production` tras el merge a `main` antes de aprobacion o
  pasos, verificando `steps=[]` y cero pending deployments.

Cycle 1 no autorizo PR a `certificacion`, PR a `main`, workflow dispatch,
aprobacion de environments, Supabase, Cloudflare deployment, DDL/DML,
backup/restore, writers, schedules ni canary Production. La ejecucion posterior
de F10.7 queda registrada en la seccion siguiente.

### Entrega Tecnica F10.7 Post-Main - 2026-08-04

F10.7 queda registrada como entrega tecnica post-main, no como cierre contractual
completo del Hito 1.

- PR #288 remediado y mergeado a `desarrollo`; commit `989cc05` y CI run
  `30944457900=PASS`.
- PR #289 abierto y mergeado a `certificacion`; CI PR run `30964692610=PASS` y
  post-merge `Security Audit Gate` `30964892097=PASS`.
- PR #290 cerrado como superseded por proteccion `require_last_push_approval`.
- PR #291 creado por `RELEASE_AUTHOR_RECORDED_PRIVATELY`, aprobado por
  `APPROVING_REVIEWER_RECORDED_PRIVATELY` y mergeado a
  `main@64e4ed895d43121c5683e26a355993f18e528a5c` / tree
  `7d43590c19ca15171d468bf8c823a5e93b47d8cc`.
- Boundary post-merge `main@d8f1ea0b210f2a1cf95e73751621cf8b4fcf0f93 -> main@64e4ed895d43121c5683e26a355993f18e528a5c`: 32 objetos,
  digest `8fafc74e415d6875315e8584eb17705e24c40777675996cde9bf4ff0ccf7ddff`.
- Security Audit post-main run `30969158679=PASS`; job `F10 Main Boundary`
  `92189531095=PASS`.
- Cloudflare Pages termino `SUCCESS` para el commit de `main`; se acepta como
  publicacion tecnica del arbol promovido, no como canary Production.
- `DB Sync to Production` run `30969158711=CANCELLED_ZERO_STEPS`; jobs `Report
  pending migrations`, `Apply pending migrations`, `Verify target schema` y `FG2
  deferred to scheduled production window` con `steps=[]`.
- Sin runs `waiting` ni `in_progress` al cierre de verificacion.

Estados resultantes: `EVID-H1-009=VERIFIED`,
`EVID-H1-014=VERIFIED_POST_MERGE_BOUNDARY`, `EVID-H1-010..013=PENDING` y
`EVID-H1-016=CLIENT_CONFORMITY_PENDING`.

### Readiness Pre-Canary F10.8 - 2026-08-05

PR #292 quedo aprobado/fusionado en
`desarrollo@a5eea3ae970e895bd8cde3da694284d7a720f81f` / tree
`968d25851c802eee5a082b8cffca2eda33f7e77e`. Sus validaciones post-merge fueron
`Security Audit Gate` `31022879108=PASS` y `F9.7 Local Contract`
`31022879169=PASS`. Esta reconciliacion no modifica `main`, no ejecuta workflow
dispatch, no accede a Supabase y no habilita schedules.

En ese corte, F10.8 quedo registrada como remediacion requerida de Production
Canary con autoridad de canary congelada:

| Campo | Valor |
|---|---|
| `candidate_sha` | `64e4ed895d43121c5683e26a355993f18e528a5c` |
| `candidate_tree` | `7d43590c19ca15171d468bf8c823a5e93b47d8cc` |
| Workflow | `.github/workflows/production_canary.yml` |
| Workflow blob en `main` | `8959c4b8f90afe0d75f23bb6e0f99d51321f1c45` |
| Cohorte | `institution_slug` seleccionado privadamente; no registrar en Git |
| UAT | `USER_PERSONAL_UAT=PASS` nuevo contra este SHA/tree antes del GO operativo |
| Environment | `Production`, aprobacion humana separada durante el workflow |

El `USER_PERSONAL_UAT=PASS` nuevo queda registrado contra el SHA/tree congelado.
Los intentos F10.8 realizados no acreditan `EVID-H1-010`:

| Run | Estado | Resultado |
|---|---|---|
| `31058586387` | `FAIL_CLOSED_INVALID_SLUG_ZERO_MUTATIONS` | Actor separado y environment `Production` aprobado; guard fallo por slug invalido; FG1/FG2/FG3 skipped; sin Supabase, snapshot, mutacion ni artifacts. |
| `31061221460` | `FAIL_CLOSED_MISSING_PRODUCTION_HOST_ZERO_MUTATIONS` | Actor separado y environment `Production` aprobado; guard fallo por variable `F10_PRODUCTION_CANARY_SUPABASE_HOST` ausente; FG1/FG2/FG3 skipped; sin Supabase, snapshot, mutacion ni artifacts. |
| `31068745673` | `FAIL_CLOSED_TARGET_ALLOWLIST_MISMATCH_ZERO_MUTATIONS` | Actor separado y environment `Production` aprobado; guard PASS; fallo en manifest pre-canary antes de crear cliente DB; sin Supabase, snapshot, FG1/FG2/FG3, mutacion, artifacts ni pending deployments. Logs mostraron identificadores operativos privados; no se detectaron credenciales. |

La remediacion pendiente autorizable dentro de F10.8 es corregir el workflow para
que el host allowlist y la cohorte privada sean secrets de environment, no inputs
o variables visibles; enmascarar identificadores operativos antes de propagarlos;
validar el target antes de instalar dependencias o crear cliente DB; y evitar
cascadas de manifests, restore y artifacts cuando no exista snapshot. El retry de
canary queda consumido: no hay nuevo `workflow_dispatch` hasta promover esta
remediacion a `main`, congelar nuevo SHA/tree, registrar UAT nuevo y emitir una
autorizacion decimal separada.

Stop conditions especificas antes o durante F10.8:

- `candidate_sha` distinto de `origin/main` o tree no verificable.
- `institution_slug` no seleccionado privadamente, no elegible, no
  `pipeline_ready`/`production_enabled` o expuesto en Git/logs/artifacts.
- `USER_PERSONAL_UAT=PASS` nuevo ausente para `main@64e4ed895d43121c5683e26a355993f18e528a5c`.
- Host Supabase Production no allowlisted, environment ambiguo, secrets faltantes
  por nombre o secretos impresos.
- Snapshot privado ausente, permisos no restrictivos, restore fallido o segundo
  restore no-NOOP.
- Mutacion fuera de cohorte, limite excedido, salida parcial verde, timeout,
  cancelacion, artifacts no sanitizados o run no aprobado por `Production`.
- Cualquier intento de habilitar schedules, ejecutar DDL/DML, backfill, Edge,
  cambios CA2, ramas protegidas o workflow distinto del canary aprobado.
- Cualquier intento de repetir F10.8 canary antes de cerrar la remediacion y
  promover un nuevo SHA/tree a `main`.

Ante cualquier stop condition, F10.8 queda bloqueada, no se reintenta
automaticamente, `AUTOMATION_ENABLED=false` y `PRODUCTION_WRITERS_PAUSED=true`
permanecen vigentes, `EVID-H1-010=PENDING` y F10.9 no puede iniciar.

### Reconciliacion Post-Main F10.8 - 2026-08-07

La promocion tecnica F10.8 quedo fusionada por PR #297 en
`main@260900a268ab8eb194140ea7311aec2a170b6e17`.

- `security-audit`, `F10 Main Boundary`, Cloudflare Pages, Credential Scan,
  Python, ESLint y TypeScript: PASS.
- Certification Canary `31140933096=PASS` sobre
  `certificacion@94026de77fe9c1a01c66eae78bea8b09858daf96`; artifact
  `f9-9-certification-canary-manifests-31140933096-1` sanitizado, con cohortes
  `redacted`, sin `institution_id`, hosts Supabase ni UUIDs en artifacts, y
  conteos/gates `pre == post == after_cleanup`.
- `DB Sync to Production` run `31142826000=FAIL_CLOSED_PRE_SUPABASE`: el step
  report invoco `db_migrate.py --manifest` en una version de `main` incompatible
  antes de contactar Supabase. `Apply pending migrations`, `Verify target schema`
  y `FG2 deferred to scheduled production window` quedaron skipped. No hubo
  DDL/DML, migrations, acceso Supabase, writer ni mutacion DB.

El estado resultante es `TECHNICALLY_DELIVERED_FORMAL_CLOSURE_PENDING`. La
remediacion siguiente dentro de F10.8 no es repetir el run historico
`31142826000`, sino corregir `DB Sync to Production` para que un push a `main`
sin cambios `db/**` termine en success con los jobs DB omitidos.

## Work Packages Internos

Los IDs siguientes organizan trabajo; no son tareas, subfases, criterios ni
autorizaciones.

| WP | Objetivo | Salida |
|---|---|---|
| `WP-H1-CA1-01` | Contrato/diff CA1-only | Allowlist, denylist y baseline |
| `WP-H1-CA1-02` | Soporte operacional FG1 | Inventario idempotente y fail-closed |
| `WP-H1-CA1-03` | Hardening FG2 | Gates, breaker, persistencia y no mock publico |
| `WP-H1-CA1-04` | Hardening FG3 | SSRF, estados HTTP y mutaciones verificadas |
| `WP-H1-CA1-05` | CI y environments | Schedules main-only y kill switch |
| `WP-H1-CA1-06` | F9.8 local/desarrollo | PR, validacion y candidate patch |
| `WP-H1-CA1-07` | F9.9/F9.10 Certification | Candidate selectivo, canary, QA, certificacion final y UAT |
| `WP-H1-CA1-08` | F10/F11 Production y evidencia | Canary, schedules, observacion, matriz y conformidad |

## Requisitos Operativos

### FG1

- Config versionado obligatorio; fallback legacy no puede ocultar errores.
- Inserts/upserts confirmados e idempotentes.
- Instituciones nuevas permanecen con gates cerrados hasta revision.
- Error de lectura/escritura produce salida no cero.

### FG2

- Solo perfiles habilitados atraviesan gates antes de limites.
- Circuit breaker mide errores consecutivos y persiste su estado.
- Harvester diferencia `NOOP` de fallo sin persistencia.
- Cleansing aplica exclusiones por institucion.
- Enrichment no publica datos mock en produccion.
- Sync demuestra mutaciones, pagina/drena su cohorte y no oculta parciales.
- FG2 no consume columnas CA2 ausentes del baseline productivo.

### FG3

- Solo HTTPS y destinos publicos/institucionales permitidos.
- Destino inicial y redirects bloquean IPs privadas/reservadas.
- `2xx` saludable; `404/410` ausente; `405/501` usa fallback acotado;
  `401/403/429/5xx/timeout` queda indeterminado sin limpiar estado.
- PATCH confirma una fila; fallo o TimeGuard produce salida no cero.
- Cohortes completas usan paginacion estable.
- FG2 no reactiva automaticamente una desactivacion confirmada por FG3.

## Environments Y Schedules

Las ejecuciones manuales conservan environments humanos. Las programadas usan
environments dedicados, main-only y secrets minimos:

- `Production-Scheduled-FG1`.
- `Production-Scheduled-FG2`.
- `Production-Scheduled-FG3`.

Cada environment empieza con `AUTOMATION_ENABLED=false`. Despues del canary
Production se habilita de forma controlada. `Production` mantiene reviewer para
operaciones manuales.

Cadencias:

- FG2 y FG3 siguen la cadencia CA1 definida en los workflows aprobados.
- FG3 se serializa despues de FG2 mediante concurrency compartida.
- FG1 mensual es soporte operacional interno y no un criterio cliente.

## Validacion Local

Todo comando de desarrollo corre dentro de `studiamatch-dev`:

- py_compile de scripts CA1.
- pytest focused FG1/FG2/FG3.
- gates, breaker, mock, SSRF, HTTP, paginacion y partial exits.
- workflow parse/actionlint y ShellCheck.
- requirements `--require-hashes` con Python 3.11.
- credential scan y secret scan.
- Context Graph y diff CA2 cerrado.

### F9.8 Local Candidate - 2026-08-01

- `python3 -m py_compile` en contenedor Linux para scripts CA1: `PASS`.
- Assertions focused `tests/test_fase09_8_ca1_candidate.py` ejecutadas en
  contenedor Linux via import directo porque la imagen local no tenia `pytest`:
  `7 focused CA1 assertions passed`.
- Replay post-merge sobre `desarrollo@5b282461149b7319685cf090534e28051e5eb32c`
  (PR #271) en Docker/Linux:
  - `test_fase09_8_ca1_candidate.py` = 24 passed; `test_fase09_8_runtime_security.py` = 29 passed; juntos 53 passed.
  - Focused FG1/FG2/FG3 y jobs CI: `test_fase07_g1b.py` 23 passed;
    `test_fase06_db_as_code.py` + `test_supabase_credentials_contract.py` 75 passed;
    `test_fase08_db.py` + `test_fase08_workers.py` 24 passed;
    `test_fase09_db.py` + `test_fase09_workers.py` 25 passed.
  - F9.7 congelado (candidate `258ef3a`): 226 passed, 5 skipped; attestation ACL 7 passed.
  - Runners PostgreSQL 17: `run_fase09_7_postgres.sh` y
    `run_fase09_7_leads_email_security_hold_postgres.sh` PASS (exit 0).
  - actionlint 1.7.7 + ShellCheck 0.9.0 sobre 7 workflows: 0 issues.
  - LF enforcement y credential scan tree+rango `8ab1cdf..M`: PASS.
  - Context Graph `CONTEXT_GRAPH: PASS (85 files, 730 links)`.
- `EVID-H1-002` (diff `638c51c..M` = solo 2 paths CI), `EVID-H1-003` (validacion
  local PASS), `EVID-H1-004` (secret scan sin blockers) y `EVID-H1-005` (PR #271
  Approved/Merged) quedan `VERIFIED`.
- CI, canaries, schedules observados, Certification y Production siguen
  pendientes en F9.9/F9.10.
- Riesgos residuales aceptados: CI F9.9 no observado aun, DNS rebinding TOCTOU
  residual en FG3, y configuracion de environments/vars pendiente de atestacion
  en GitHub antes de habilitar Production.

## Gates De Promocion

### Desarrollo / F9.8

- PR CA1-only, CI y review independiente.
- Candidate patch congelado despues del merge.
- Ejecucion controlada contra Development solo con autorizacion.

### Certification / F9.9-F9.10

- Patch equivalente sobre baseline de certificacion.
- Cero paths CA2.
- `EVID-H1-006/007=VERIFIED` por PR #277 y CI; `EVID-H1-008=DEVIATION_ACCEPTED_FAIL_CLOSED`, nunca `PASS`.
- QA independiente debe revisar la desviacion antes de readiness.
- La revision QA debe seguir [QA-F9.9-DEVIATION-001](./qa_desviacion_f9_9.md) y puede terminar `PASS`, `FAIL` o `BLOCKED`.
- Evidencia de target sin exponer identificadores.
- `USER_PERSONAL_UAT` despues de canary, validaciones tecnicas Certification y QA.

### Production / F10

- Antes de cualquier PR a `main` deben cerrarse como checklist bloqueante:
  - `db-sync-to-pro.yml`: push a `main` solo dry-run/report-only; apply automatico prohibido; apply solo por `workflow_dispatch`, confirmacion explicita, aprobacion Production, backup/PITR verificado, autorizacion DDL separada, Actions pinneadas por SHA y dependencias hash-locked.
  - Environments `Production-Scheduled-FG1`, `Production-Scheduled-FG2` y `Production-Scheduled-FG3` con reviewer humano, branch policy `main`, secrets minimos separados y `AUTOMATION_ENABLED=false` inicial.
  - Gate de automatizacion con preflight asociado al environment programado, sin depender ambiguamente de variable de environment en job-level `if`, y output explicito por writer.
  - `PRODUCTION_WRITERS_PAUSED` efectivo y fail-closed antes de cada estacion mutante y tambien para migraciones.
  - Gate main/F10 reconstruido en `certificacion` con boundary CA1-only, cero CA2, credential scan, workflows validos, tests obligatorios, candidate commit/tree/count/digest inmutables, variables no secretas aprobadas, review humano y aprobacion SDLC.
  - `opencode.yml` endurecido o deshabilitado sin secreto accesible por comentario no confiable; cualquier ejecucion historica no confiable exige rotacion de la credencial antes de continuar.
  - Cloudflare Pages con auto-deploy de `main` prevenido y verificado antes del PR a `main`; si un deployment arranca, F10.7 se detiene como incidente.
  - Freeze F10.7 nuevo y UAT nuevo; el freeze F9.10 de 32 objetos no puede reutilizarse como autoridad de promocion.
  - Rollback con backup/restore ensayados, responsable, RTO/RPO, cancelacion de jobs, schedules off, rollback de datos, migracion compensatoria si existiera DDL y revert de codigo solo por PR forward-only.
- El primer gate operativo Production de F10 es el canary manual acotado; no es precondicion para cerrar F9.9 ni para iniciar F10.
- PR `certificacion -> main`.
- Candidate/tree inmutable y aprobacion humana.
- Backup/rollback operativo proporcionado por el ambiente vigente.
- Canary Production acotado, solo `workflow_dispatch`, SHA exacto de `main`, environment Production con aprobacion, host Pro allowlisted, una cohorte, limites acotados, snapshot privado, restore exacto, segundo restore NOOP y artifacts sanitizados.
- Cero mutaciones fuera de cohorte y cero cambios CA2.
- FG2/FG3 automaticos observados; FG1 manual equivalente con cron mensual
  activo y primera ventana natural como observacion post-cierre.

### Observacion Production

- No inicia antes de un canary Production PASS.
- FG2 programado a `05:00 UTC` y FG3 a `11:00 UTC`.
- Requiere tres pares consecutivos FG2 -> FG3, seis runs completos; puede exceder 72 horas.
- Un run skipped, cancelled, timeout, partial, `401/403/429/5xx` o false-green no cuenta.
- Ante cualquier fallo: `PRODUCTION_WRITERS_PAUSED=true`, automation false, cancelar jobs activos, preservar evidencia y reiniciar la secuencia despues de remediar.
- FG1 mensual no se considera observado en 72 horas; exige FG1 manual equivalente PASS y cron activo, o waiver explicita con responsable y fecha de primera ventana natural.

### Cierre Control-Plane F10.6

- `Production-Scheduled-FG1`, `Production-Scheduled-FG2` y `Production-Scheduled-FG3` existen con branch policy exacta `main`, reviewer humano autorizado y self-review bloqueado.
- `AUTOMATION_ENABLED=false` y `PRODUCTION_WRITERS_PAUSED=true` estan configuradas en `Production`, `Production-Scheduled-FG1`, `Production-Scheduled-FG2` y `Production-Scheduled-FG3`.
- Los secrets requeridos existen por nombre en cada environment programado; sus valores no se leyeron ni documentaron.
- Runs legacy schedule `30681941694`, `29678093566` y `29677885934` quedaron `cancelled`; todos sus jobs conservaron `steps=[]` y no quedaron pending deployments.
- No hubo aprobacion, retry, dispatch, schedule ejecutado, writer, Production canary, Supabase, Cloudflare, DDL/DML ni PR/merge a `main`.

## Kill Switch Y Rollback

- `AUTOMATION_ENABLED=false` detiene nuevas ejecuciones.
- Workflows afectados pueden deshabilitarse sin tocar DB.
- Revert por PR forward-only; nunca reset/force-push.
- Mutaciones canary usan manifest/evidencia acotada para restauracion.
- Un incidente mantiene schedules apagados hasta nueva aprobacion.

### Rollback F10 Requerido Antes De Produccion

- `PRODUCTION_WRITERS_PAUSED=true` antes de cualquier DDL manual y ante incidente de canary/schedule.
- `AUTOMATION_ENABLED=false` en `Production-Scheduled-FG1`, `Production-Scheduled-FG2` y `Production-Scheduled-FG3` hasta habilitacion gradual aprobada.
- Canary Production conserva snapshot privado en runner, restaura siempre, ejecuta segundo restore `--expect-noop` y sube solo resumen sanitizado sin slug de cohorte, SHA/run ID ni digest privado de filas.
- Ante fallo: cancelar jobs activos, preservar artifacts sanitizados, no reintentar automaticamente, documentar incidente y reabrir solo con autorizacion decimal futura.
- Revert de codigo solo por PR forward-only; DDL compensatorio o restore de datos requiere autorizacion separada y evidencia Backup/PITR.

## Evidencia De Salida

| ID | Evidencia | Umbral | Estado |
|---|---|---|---|
| `EVID-H1-001` | Adenda integral aprobada | Alcance, cronograma y detalle comercial verificados en privado | `VERIFIED` |
| `EVID-H1-002` | Diff CA1-only | Cero paths CA2 | `VERIFIED` |
| `EVID-H1-003` | Validacion local | PASS | `VERIFIED` |
| `EVID-H1-004` | Seguridad/secret scan | Sin blockers | `VERIFIED` |
| `EVID-H1-005` | PR desarrollo | Approved/Merged | `VERIFIED` |
| `EVID-H1-006` | Equivalencia patch | PR #277 CI/boundary PASS | `VERIFIED` |
| `EVID-H1-007` | PR certificacion | PR #277 Approved/Merged | `VERIFIED` |
| `EVID-H1-008` | Canary Certification | Fail-closed documentado, no PASS | `DEVIATION_ACCEPTED_FAIL_CLOSED` |
| `EVID-H1-009` | PR main | Approved/Merged | `VERIFIED` |
| `EVID-H1-010` | Canary Production | PASS | `PENDING` |
| `EVID-H1-011` | FG2 automatico | SUCCESS/NOOP completo | `PENDING` |
| `EVID-H1-012` | FG3 automatico | SUCCESS/NOOP completo | `PENDING` |
| `EVID-H1-013` | FG1 soporte | Canary PASS y cron activo | `PENDING` |
| `EVID-H1-014` | Cero cambios CA2 | Object/digest closure PASS | `VERIFIED_POST_MERGE_BOUNDARY` |
| `EVID-H1-015` | QA independiente | PASS | `VERIFIED` |
| `EVID-H1-016` | Conformidad cliente | APPROVED | `CLIENT_CONFORMITY_PENDING` |

## Stop Conditions

- Path/hunk CA2 en el candidate.
- Dependencia de columna/RPC no presente en produccion.
- Target/environment ambiguo.
- Secret o dato sensible en diff/log.
- SSRF, mock publicado, mutacion no probada o salida parcial verde.
- CI, QA, canary positivo, smoke o schedule fallido, salvo la desviacion F9.9 registrada explicitamente como `DEVIATION_ACCEPTED_FAIL_CLOSED`.
- Production o schedules antes de cerrar los controles pre-main, F10.8 y F10.9.
- Uso del freeze F9.10 de 32 objetos como autoridad F10.7 sin digest post-merge y evidencia nueva.
- Promocion no verificada de `.github/workflows/f9-7-contract.yml` a `certificacion -> main`.
- OpenCode secret-bearing sin pinning/allowlist o sin deshabilitacion segura.
- Cloudflare Pages de `main` no observado, no documentado o usado como sustituto de canary Production.

## Allowlist De Controles Pre-Main F9.9

Esta allowlist habilita este paquete de repositorio tras la frase decimal exacta `Ejecuta las tareas pendientes de la Fase F9.9`. No autoriza ejecucion remota, cambios de environments, secrets, Production, schedules, Supabase, Cloudflare, DDL/DML, backup/restore ni writers.

Paths permitidos para ese paquete posterior:

- `.github/workflows/db-sync-to-pro.yml` para separar reporte dry-run en push a `main` del apply manual.
- `.github/workflows/fg1_inventory.yml`, `.github/workflows/production_pipeline.yml` y `.github/workflows/fg3_integrity.yml` para preflight environment-bound, outputs explicitos y gate de `AUTOMATION_ENABLED`.
- `.github/workflows/security-audit.yml` para gate main/F10 object-based, boundary CA1-only y checks documentales.
- `.github/workflows/f9-7-contract.yml` solo para ampliar el gate de transicion y permitir la modificacion de `.github/workflows/db-sync-to-pro.yml` dentro de este paquete F9.9.
- `.github/workflows/opencode.yml` solo para pinning de Actions por SHA confiable si se resuelve externamente sin inventar SHAs.
- `.github/actionlint.yaml` solo para ajustar suppressions si los workflows dejan de necesitarlas.
- `.github/scripts/production_control_preflight.sh` como script local fail-closed sin secretos ni red.
- `tests/test_fase09_9_pre_main_controls.py` y `tests/test_fase10_main_boundary.py` para pruebas estaticas de controles.
- Ajustes minimos a tests existentes que congelan comportamiento antiguo, preservando evidencia historica F9.7/F9.8 por commit.
- `.context/**` enlazado para documentar resultados y mantener el Context Graph.

Paths y acciones excluidos para ese paquete posterior: `db/**`, `supabase/**`, `web/**`, `scripts/maintenance/db_migrate.py`, manifests DB, datos operativos, `.env*`, artifacts privados, cambios remotos GitHub, dispatches, canaries, schedules, PR a `main`, DDL/DML, backup/restore y cualquier cambio CA2.

## Allowlist De Controles Pre-Main F9.10

Esta allowlist habilita el paquete F9.10 tras la frase decimal exacta `Ejecuta las tareas pendientes de la Fase F9.10`. No autoriza ejecutar Production, Supabase, Cloudflare, DDL/DML, backup/restore real, schedules, PR a `main`, environments/secrets remotos ni canaries remotos.

Paths permitidos para este paquete:

- `.github/scripts/production_control_preflight.sh` para separar `DB-SYNC` manual con writers pausados de FG1/FG2/FG3 con writers activos.
- `.github/workflows/f9-7-contract.yml` solo para ampliar el gate de transicion y permitir exactamente las altas de `scripts/core/production_canary_manifest.py` y `scripts/core/production_canary_state.py` dentro de este paquete F9.10.
- `.github/workflows/security-audit.yml` para agregar el gate bloqueante `f10-main-boundary`.
- `.github/workflows/production_canary.yml` para definir el canary Production manual, main-only, SHA-bound, environment `Production`, preflight `PRODUCTION-CANARY`, snapshot privado, restore always y segundo restore NOOP.
- `.gitattributes` solo para fijar LF de los nuevos archivos F9.10 y evitar drift CRLF en el package.
- `scripts/core/production_canary_manifest.py` y `scripts/core/production_canary_state.py` para evidencia sanitizada y rollback acotado.
- `scripts/core/universal_harvester.py`, `scripts/core/cleansing_worker.py`, `scripts/core/enrichment_worker.py` y `scripts/core/sync_vector_worker.py` solo para marcadores env-gated de canary que permiten limpiar filas creadas durante FG2/FG3.
- `tests/test_fase09_10_pre_main_controls.py`, `tests/test_fase10_main_boundary.py` y `tests/test_fase10_production_canary.py` para pruebas estaticas y conductuales offline de los controles.
- `tests/test_supabase_credentials_contract.py` solo para inventariar los tres consumidores Supabase nuevos de F9.10.
- `tests/test_fase09_7_release_gates.py` solo para actualizar el inventario exacto de workflows de ocho a nueve por `production_canary.yml`.
- `.context/**` enlazado para registrar PR #282, run `30824041542`, rollback, subfases F10.x y blockers pendientes.

El allowlist exacto interno de `f10-main-boundary` tambien reconoce objetos CA1 historicos ya fusionados en `certificacion`: `requirements-db-migrate.txt`, `scripts/core/certification_canary_state.py`, `scripts/shared/roi_engine.py` y `tests/test_fase09_9_certification_canary.py`. Estos paths no amplian la allowlist de edicion F9.10; solo evitan un falso bloqueo al promover el manifest CA1 existente `certificacion -> main` en F10.7.

Paths y acciones excluidos para este paquete: `db/**`, `supabase/**`, `web/**`, `scripts/maintenance/db_migrate.py`, manifests DB, datos operativos fuera de snapshot privado efimero, `.env*`, cambios remotos GitHub, dispatches, canaries reales, schedules, PR a `main`, DDL/DML, backup/restore real y cualquier cambio CA2.

## Allowlist Historica De Rebaseline F10.7

Cycle 1 quedo limitado a `.context/**` y solo documento [ADR-0008](../decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md), el bloqueo de promocion directa, la invalidez del freeze F9.10 como autoridad F10.7 y los requisitos de Cycle 2.

Cycle 2, tras repetir la frase decimal exacta `Ejecuta las tareas pendientes de la Fase F10.7`, permitio un paquete de controles con alcance maximo:

- `.github/workflows/security-audit.yml` para reconstruir `f10-main-boundary`, hacerlo target-aware, agregarlo al agregador `security-audit` y validar SHA/tree/count/digest aprobados.
- `.github/workflows/opencode.yml` para pinning por SHA confiable, allowlist de actores o deshabilitacion segura del workflow con secreto.
- `tests/test_fase10_main_boundary.py` para pruebas offline de source branch, same-repo, branch-tip, path/status/mode/blob, variables aprobadas y regresiones de F10.
- `.context/**` solo para registrar la evidencia de Cycle 2, nuevo freeze, UAT nuevo, cancelaciones cero-pasos y cierre de `EVID-H1-009`.

Cycle 2 excluyo `db/**`, `supabase/**`, `web/**`, `scripts/maintenance/**`, requirements, runtime scripts, datos operativos, `.env*`, artifacts privados, workflow dispatch, canaries, schedules, DDL/DML, backup/restore y cualquier cambio CA2. Cloudflare Pages `SUCCESS` post-main se registra como side effect tecnico observado, no como canary Production.

## Subfases F10 Propuestas

| ID | Estado | Alcance |
|---|---|---|
| `F10.1`-`F10.5` | `SUPERSEDED_HISTORY` | Historia documental sustituida; no autorizable. |
| `F10.6` | `COMPLETED_CONTROL_PLANE` | Control-plane: environments programados, variables `AUTOMATION_ENABLED=false`, `PRODUCTION_WRITERS_PAUSED=true`, cancelacion/resolucion de runs antiguos y verificacion de branch policy. |
| `F10.7` | `COMPLETED_TECHNICAL_DELIVERY` | PR #291 aprobado/fusionado a `main`, boundary 32 objetos, Security Audit PASS, Cloudflare Pages `SUCCESS` y DB Sync cancelado cero-pasos. |
| `F10.8` | `IN_PROGRESS_DB_SYNC_FAIL_CLOSED_REMEDIATION_REQUIRED` | Remediacion Production Canary promovida por PR #297 a `main@260900a268ab8eb194140ea7311aec2a170b6e17`; Certification Canary final `31140933096=PASS`; DB Sync `31142826000` fallo fail-closed antes de Supabase por ejecutar report DB en push sin cambios `db/**`. Requiere remediar DB Sync antes de Production Canary, schedules u observacion. |
| `F10.9` | `PENDING` | Habilitacion gradual de schedules y observacion: al menos 72h y tres pares FG2 -> FG3 consecutivos completos. |
| `F11.1` | `PENDING` | Cierre documental final de Hito 1 CA1-only y conformidad cliente. |

## Criterio De Salida

`H1-CA1=COMPLETED_PRODUCTION` y `HITO-001=COMPLETED_PRODUCTION_CA1_ONLY`
solo despues de que `EVID-H1-008` conserve su desviacion aceptada,
`EVID-H1-009` y `EVID-H1-014` conserven la entrega tecnica verificada y
`EVID-H1-010..013/016` queden verificadas segun sus umbrales futuros. CA2 queda
`DEFERRED_TO_HITO_2` sin cambio funcional productivo.

## Allowlist De Remediacion DB Sync F10.8

Esta allowlist habilita unicamente la remediacion fail-closed de DB Sync tras la
frase decimal exacta `Ejecuta las tareas pendientes de la Fase F10.8`, una vez
fusionada la reconciliacion documental que la activa. No autoriza Supabase,
DDL/DML, Production Canary, schedules, writers, backfill ni CA2.

Paths permitidos:

- `.github/workflows/db-sync-to-pro.yml` para agregar detector sin secrets de
  cambios `db/**`, omitir report/apply/verify en push sin DB y conservar apply
  manual DDL-gated.
- Tests especificos del contrato DB Sync para push sin DB, push con DB,
  `workflow_dispatch` report y `workflow_dispatch` apply.
- `.github/workflows/security-audit.yml` solo si el gate minimo de promocion
  necesita aceptar exactamente este patch.

Paths y acciones excluidos: `db/**`, `supabase/**`, manifests, migrations,
`scripts/maintenance/db_migrate.py`, datos operativos, `.env*`, Supabase,
DDL/DML, backup/restore real, workflow dispatch operativo, Production Canary,
schedules, writers, backfill, Edge y cualquier cambio CA2.
