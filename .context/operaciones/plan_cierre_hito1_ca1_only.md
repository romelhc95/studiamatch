# PLAN-H1-CA1-ONLY-001 - Cierre Productivo De Hito 1

| Campo | Valor |
|---|---|
| ID | `PLAN-H1-CA1-ONLY-001` |
| Estado | `DRAFT_PENDING_CLIENT_APPROVAL` |
| Requerimiento | `REQ-EST-001` |
| Hito | `HITO-001` |
| Criterio | `H1-CA1` |
| Autoridad habilitante | [ADENDA-REQ-EST-001-001](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md) |

Este plan no autoriza ejecucion. Entra en vigor cuando la adenda sea aprobada,
el Context Graph adopte la rebaseline y exista una subfase decimal activa.

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
- Cambios funcionales de leads/email y Edge.
- Panel admin, Home, Resultados, cards, filtros o rutas.
- Tooling capaz de aplicar packages DB.
- Artifacts terminales locales F9.7.

## Estrategia De Candidate Selectivo

`desarrollo` contiene cambios mixtos y no puede promoverse completo. El release
usa una frontera por patch:

1. Implementar y revisar CA1 en una rama limpia con PR a `desarrollo`.
2. Congelar diff, patch-id, commit/tree y hashes CA1 aprobados.
3. Reconstruir solo ese patch sobre el baseline productivo vigente.
4. Probar equivalencia y ausencia CA2.
5. PR del candidate CA1-only a `certificacion`.
6. Canary/QA Certification.
7. PR `certificacion -> main` con tree funcional equivalente.
8. Canary Production con schedules apagados.
9. Habilitar schedules y observar la operacion.

Nunca se mezcla `desarrollo` dentro del candidate. Un conflicto que requiera
copiar CA2 invalida el candidate y obliga a reconstruirlo.

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
| `WP-H1-CA1-06` | Development/Certification | PRs, canary y QA |
| `WP-H1-CA1-07` | Production | Canary, schedule y observacion |
| `WP-H1-CA1-08` | Evidencia cliente | Matriz y conformidad |

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

## Gates De Promocion

### Desarrollo

- PR CA1-only, CI y review independiente.
- Candidate patch congelado despues del merge.
- Ejecucion controlada contra Development solo con autorizacion.

### Certificacion

- Patch equivalente sobre baseline de certificacion.
- Cero paths CA2.
- Canary FG1/FG2/FG3, cleanup y QA.
- Evidencia de target sin exponer identificadores.

### Produccion

- PR `certificacion -> main`.
- Candidate/tree inmutable y aprobacion humana.
- Backup/rollback operativo proporcionado por el ambiente vigente.
- Canary acotado antes de schedules.
- Cero mutaciones fuera de cohorte y cero cambios CA2.
- FG2/FG3 automaticos observados; FG1 manual equivalente con cron mensual
  activo y primera ventana natural como observacion post-cierre.

## Kill Switch Y Rollback

- `AUTOMATION_ENABLED=false` detiene nuevas ejecuciones.
- Workflows afectados pueden deshabilitarse sin tocar DB.
- Revert por PR forward-only; nunca reset/force-push.
- Mutaciones canary usan manifest/evidencia acotada para restauracion.
- Un incidente mantiene schedules apagados hasta nueva aprobacion.

## Evidencia De Salida

| ID | Evidencia | Umbral |
|---|---|---|
| `EVID-H1-001` | Adenda integral aprobada | Alcance, cronograma y detalle comercial verificados en privado |
| `EVID-H1-002` | Diff CA1-only | Cero paths CA2 |
| `EVID-H1-003` | Validacion local | PASS |
| `EVID-H1-004` | Seguridad/secret scan | Sin blockers |
| `EVID-H1-005` | PR desarrollo | Approved/Merged |
| `EVID-H1-006` | Equivalencia patch | PASS |
| `EVID-H1-007` | PR certificacion | Approved/Merged |
| `EVID-H1-008` | Canary Certification | PASS |
| `EVID-H1-009` | PR main | Approved/Merged |
| `EVID-H1-010` | Canary Production | PASS |
| `EVID-H1-011` | FG2 automatico | SUCCESS/NOOP completo |
| `EVID-H1-012` | FG3 automatico | SUCCESS/NOOP completo |
| `EVID-H1-013` | FG1 soporte | Canary PASS y cron activo |
| `EVID-H1-014` | Cero cambios CA2 | Object/digest closure PASS |
| `EVID-H1-015` | QA independiente | PASS |
| `EVID-H1-016` | Conformidad cliente | APPROVED |

## Stop Conditions

- Adenda no aprobada.
- Path/hunk CA2 en el candidate.
- Dependencia de columna/RPC no presente en produccion.
- Target/environment ambiguo.
- Secret o dato sensible en diff/log.
- SSRF, mock publicado, mutacion no probada o salida parcial verde.
- CI, QA, canary, smoke o schedule fallido.

## Criterio De Salida

`H1-CA1=COMPLETED_PRODUCTION` y `HITO-001=COMPLETED_PRODUCTION_CA1_ONLY`
solo despues de las 16 evidencias verificadas. CA2 queda
`DEFERRED_TO_HITO_2` sin cambio funcional productivo.
