# PLAN-H1-CA1-ONLY-001 - Cierre Productivo De Hito 1

| Campo | Valor |
|---|---|
| ID | `PLAN-H1-CA1-ONLY-001` |
| Estado | `F9_9_QA_VERIFIED_F9_10_PENDING` |
| Requerimiento | `REQ-EST-001` |
| Hito | `HITO-001` |
| Criterio | `H1-CA1` |
| Autoridad habilitante | [ADENDA-REQ-EST-001-001](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md) |

Este plan queda vigente por adenda aprobada y rebaseline del Context Graph. No
ejecuta por si mismo: F9.8 quedo cerrada por replay post-merge; F9.9 documento
PR #277, una desviacion Certification fail-closed, controles pre-main PR #280 y
QA independiente `PASS`. Production, schedules y F10 permanecen bloqueados hasta
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
7. F10 ejecuta PR a `main`, canary Production con schedules apagados.
8. F10 habilita schedules gradualmente y observa la operacion.

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
  - Gate main/F10 con boundary CA1-only, cero CA2, credential scan, workflows validos, tests obligatorios, candidate commit/tree/digest inmutables, review humano y aprobacion SDLC.
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

## Kill Switch Y Rollback

- `AUTOMATION_ENABLED=false` detiene nuevas ejecuciones.
- Workflows afectados pueden deshabilitarse sin tocar DB.
- Revert por PR forward-only; nunca reset/force-push.
- Mutaciones canary usan manifest/evidencia acotada para restauracion.
- Un incidente mantiene schedules apagados hasta nueva aprobacion.

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
| `EVID-H1-009` | PR main | Approved/Merged | `PLANNED` |
| `EVID-H1-010` | Canary Production | PASS | `PLANNED` |
| `EVID-H1-011` | FG2 automatico | SUCCESS/NOOP completo | `PLANNED` |
| `EVID-H1-012` | FG3 automatico | SUCCESS/NOOP completo | `PLANNED` |
| `EVID-H1-013` | FG1 soporte | Canary PASS y cron activo | `PLANNED` |
| `EVID-H1-014` | Cero cambios CA2 | Object/digest closure PASS | `PENDING_REVERIFY_MAIN_CANDIDATE` |
| `EVID-H1-015` | QA independiente | PASS | `VERIFIED` |
| `EVID-H1-016` | Conformidad cliente | APPROVED | `PLANNED` |

## Stop Conditions

- Path/hunk CA2 en el candidate.
- Dependencia de columna/RPC no presente en produccion.
- Target/environment ambiguo.
- Secret o dato sensible en diff/log.
- SSRF, mock publicado, mutacion no probada o salida parcial verde.
- CI, QA, canary positivo, smoke o schedule fallido, salvo la desviacion F9.9 registrada explicitamente como `DEVIATION_ACCEPTED_FAIL_CLOSED`.
- PR a `main`, Production o schedules antes de cerrar los controles pre-main.

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

## Criterio De Salida

`H1-CA1=COMPLETED_PRODUCTION` y `HITO-001=COMPLETED_PRODUCTION_CA1_ONLY`
solo despues de que `EVID-H1-008` conserve su desviacion aceptada y
`EVID-H1-009..016` queden verificadas segun sus umbrales futuros. CA2 queda
`DEFERRED_TO_HITO_2` sin cambio funcional productivo.
