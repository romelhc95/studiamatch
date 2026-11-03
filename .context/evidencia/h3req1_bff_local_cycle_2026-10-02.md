# Evidencia del ciclo local H3REQ1 BFF/HttpOnly

**Objetivo actualizado por el responsable:** GO integral para PR y pruebas
Development, no entregas por hallazgo. Los PASS y cierres focalizados siguientes
son evidencia interna; no constituyen GO del candidato. Pendientes y secuencia
consolidados en el plan y estado canónicos. Readiness para iniciar pruebas no
equivale a su resultado remoto; JIT por operación sigue obligatorio. Esta actualización
documental no ejecuta ni autoriza por sí sola operaciones remotas.

**Ejecuciones UTC:** 2026-10-02 (UAT visual `r14`; PG17/test gates actualizados)  
**Estado:** `NO-GO_H3REQ1_DEVELOPMENT_FREE`  
**Alcance:** checkout y contenedores locales; sin commit, push, PR, merge, deploy,
workflow_dispatch ni operaciones Supabase remotas. La atestación sanitizada que
gobierna el requerimiento se mantiene en
[`atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md`](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md).

El candidato es el worktree aislado `feat/h3req1-sync-20261002`, con `HEAD` en el
baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c` y cambios locales sin commit.
El manifiesto del árbol actual está en
`C:\Users\Romel\AppData\Local\Temp\opencode\h3req1-uat-20261002-r14\candidate-current-manifest.txt`;
su `working_tree_sha256` identifica 701 rutas versionadas/no ignoradas en este corte.
`HEAD` por sí solo no identifica los bytes del candidato.

La UAT visual Pages local `r14` pasó **48/48 casos, 144/144 ejecuciones y 144
capturas**, sin reintentos, sobre un build estático aislado servido por Wrangler y
mock local. El caso `H3-UAT-038` registra 502 + `invitation_failed`; el perímetro
sirve el hostname Admin permitido y devuelve 404 para `studiamatch.com`. La UAT de
invitaciones/onboarding pasó **10/10**. Artefactos y hashes:
`h3req1-uat-20261002-r14.tar.gz` SHA-256
`12163e7f33b5fb49b671410a9f2766da39b359b28d611ae891e991f9dfc418f1`, matriz JSON
SHA-256 `b211a7e9cf1ce4da20ebf2742f77ac76adaada2c828b16b3b70002e66b701a28`.

Después del hallazgo LOW de autorización por estado de membresía, `admin_update_course`
ahora exige editor activo y `account_status='ready'`. PG17 comprueba rechazo tanto
para un registro `invited` activo como para `password_pending` activo. La suite de
contratos se actualizó para exigir ese control.

La reauditoría read-only disponible se realizó antes de ese último delta SQL: registró
1 HIGH de integridad CI, 1 MEDIUM de rate limiting y 2 LOW (estado de membresía y
alcance del JWT). El primero sigue sin acreditación independiente remota; rate
limiting fue diferido sin waiver. El LOW de membresía quedó remediado localmente y
probado; falta reauditar el árbol exacto. El LOW del transporte sigue abierto: la
aprobación versionada limita JWT Bearer a RPCs allowlisted, mientras el runtime BFF
también usa Supabase Auth/MFA y la Edge Function `admin-invite`. El helper genérico
no valida ruta/método ni forma JWT, y la UAT SDK existente aún usa un token sintético
en una lectura de tabla. La pregunta de alcance para Auth/Edge quedó sin respuesta;
no se amplió la excepción ni se alteró ese transporte.

No existe rollback SQL compensatorio ejecutable ni drill de restauración de las
funciones/vistas previas. No hubo aplicación de DDL remota; cualquier deploy queda
bloqueado hasta definir y probar rollback separado. El estado local y remoto es
**NO-GO**.

## Corte vigente — remediación local tras aprobación del baseline

### Cierre focalizado posterior a `Continúa`

Dos hallazgos remediados: método `delivery_method` persistido por servidor en
reserva, antes de Auth; replay completado compara toda respuesta, incluido recovery.
Registros legacy sin metadata conservan false (compatibilidad explícita).
Drill ampliado crea reservas reales antes de suspender y llama completion/failure/
reconciliation bajo service_role después; comprueba rechazo de nuevas reservas,
estado persistido, auditoría y conservación de metadata. No modifica SQL productivo.

Validación Docker sobre fuentes actuales: Edge UAT **PASS**, typecheck semántico
SDK2.109.0 **PASS**, pytest **282 passed/4 skipped**, drills
`h3_current_pro_confirmed` y `h3_future_contracted_confirmed` **PASS**;
`git diff --check` **PASS**. Solo bases desechables PG17 locales; no DDL/DML remoto.
Reauditoría `ses_f01f31258ffeIQxqU1tGp9N4xX`: **ambos hallazgos cerrados**, sin
nuevas vulnerabilidades comprobadas. Auditor reejecutó Edge; SQL revisado estáticamente,
drills/typecheck/pytest ejecutados por sesión principal.

Criterios frente a atestación sanitizada H3-CA4: identidad/RBAC y auditoría conservados,
sin ampliación de Auth/MFA ni writes remotos. Pilares focalizados: funcionalidad
(replay consistente), seguridad (método server-side y permisos reales), mantenimiento/
calidad (regresiones reproducibles), rendimiento/escalabilidad (sin consulta extra
en replay ni infraestructura nueva). No equivale a prueba de carga ni GO global.
Expand metadata -> compatibilidad legacy probada -> deploy JIT pendiente -> contract
tras estabilización pendiente. Rollback: suspensión acotada, no downgrade Edge.
Fuentes cambiaron después del snapshot build anterior; no declarar ese snapshot
como artefacto final de este ciclo. NO-GO integral permanece.

La decisión humana permite modelar Pro actual con cohorte presente sin modificar
Pro. Dos bases nuevas del servidor Docker `h3req1-pg17-chain-build-20261002`
ejecutaron la cadena H2 -> H3 sin reset intermedio: `h3_current_pro_confirmed`
y `h3_future_contracted_confirmed`, ambas **PASS**. El segundo modo ensaya una
contracción futura; no describe Pro actual. Fixture reducido con campos acreditados,
no equivalencia exhaustiva con schema remoto.

Edge: scope de `reserved` corregido; tres escenarios de éxito y sus replay pasan
con HTTP 200 y sin segundo envío/reconciliation. Typecheck semántico `createProgram`
strict contra SDK instalado **2.109.0 PASS**, distinto de transpile-only.
SDK interceptado **26 PASS**, BFF **52 PASS**, Auth error **7 PASS**.
Suite Docker: **282 passed, 4 skipped**, warning histórico PyPDF2.

Snapshot Docker `/tmp/h3req1-ci-approved-pro-20261002` en
`studiamatch-h3req1-build`: `npm ci`, cinco scripts JS (incluido typecheck semántico)
y `h2_web_mock_smoke.sh` **PASS**. Build con fixture propio, sin sobrescribir
`web/out`. No acredita CI remoto ni ejecución integral de todos los jobs workflow.

`db/rollback/h3req1_safe_suspend.sql` y
`tests/sql/h3_safe_suspend_harness.sql`: drills **PASS** en ambas bases encadenadas.
Revoca iniciadores de mutaciones; conserva completion/failure/reconciliation en
curso, lectores endurecidos, datos/columnas/cohortes y auditoría append-only.
Drill verifica doble aplicación, hashes, permisos y unavailable vigente oculto.
Resume usa permisos guardados SOLO en prueba; no es receta remota aprobada.
Es suspensión segura deliberadamente limitada, no restauración funcional completa
ni rollback de artefacto desplegado. Cualquier uso remoto requiere JIT separado.

Inventario JWT identidad/origen/proveedor/ruta/método y tests Request/init ampliados;
allowlists CI reconciliadas. Reauditoría READ-ONLY solicitada a
`ses_f01fa8673ffeytyjgOYvnMSYta`, completada: HIGH Edge cerrado; dos hallazgos nuevos
abiertos (LOW respuesta replay recovery inconsistente, MEDIUM cobertura in-flight
incompleta del drill). Auditor reejecutó tres pruebas interceptadas con cinco fuentes
relevantes cotejadas por SHA-256; no reejecutó build ni SQL.
De 26 escenarios transporte, tres usan SDK real y los demás helper directo.
El typecheck local no acredita Deno ni versión final resuelta por npm SDK @2.
No restaurar Edge de HEAD como rollback seguro: envía Auth antes de reservar y puede
producir efectos externos antes de fallar con reserva revocada.
No declarar hallazgos cerrados por
intención ni extrapolar PASS interceptados a Auth/Supabase remoto.

**NO-GO**: cuotas, UAT final, manifiesto congelado, revisión y enforcement CI remoto
pendientes. Manifiesto r14 es histórico/stale, no identifica bytes actuales.
La única lectura remota de este ciclo sigue siendo metadata Pro previamente aprobada.

## Corte anterior de reauditoría — histórico, supersedido por el corte vigente

Revisión READ-ONLY `ses_f02149ccbffeOndfPb8FmeEHoT` del delta aprobado: no encontró
bypass del transporte JWT por origen/ruta/método/redirect; Supabase sigue verificando
identidad. API key Bearer eliminado; browser sin policy JWT. Faltan matriz explícita
de inventario y tests Request/init contradictorios. No afirmar Auth remoto probado.

**HIGH Edge reproducido:** éxito Auth + persistencia completion devuelve 409 falsa
reconciliación porque `reserved` sale de su scope en respuesta exitosa. El UAT Edge
previo no cubría ese happy path. Remediación y typecheck semántico Edge pendientes.
**MEDIUM CI:** harness encadenado, ESLint config y sistema_db_supabase no están en
allowlist aplicable; reconcile por rutas exactas. HIGH CI externo y MEDIUM cuotas
siguen abiertos. LOW documentación se corrige consolidando este corte; no descartar
históricos/artefactos para aparentar GO.

Pytest parcial nuevo 282+4, SDK 23, BFF 52, Edge y TS PASS no cierran esos hallazgos.
Harness encadenado FAIL provider_used; build CI completo/UAT visual final/rollback
pendientes. Documentación y credenciales tuvieron 17 contratos PASS antes de JWT;
un test inventario posterior detectó workflow que ya no consume Supabase directo
tras retirar URL placeholder, y se eliminó esa entrada obsoleta; revalidación pendiente.
Ciclo detenido ante baseline drift; no nuevas operaciones remotas ni schema ad hoc.

### Pro read-only posterior — autorizado, no promoción

El humano autorizó lectura acotada schema/tipos/grants/constraints/ledger de
`xwhtiqmboljkshrtviyw`. URL confirmada antes de consultar metadata. Resultado:
`courses.provider_used` existe (text nullable default mock); is_mock_data bool
nullable default true y seniority_level varchar nullable default Mid. La cohorte
`private.h2_legacy_public_course_cohort` **existe** actualmente en Pro.

Conclusión: provider_used faltante es defecto del fixture, no prueba de columna
ausente en Pro. Retiro de cohorte en el harness H2 Pro es escenario de contracción,
no baseline remoto actual. El ledger nativo leído no representa necesariamente SQL
aplicado por otras vías. No se consultaron filas operativas ni valores secretos.
No hubo writes, Auth, deploy, GitHub ni Git remoto.

El gate de baseline sigue NO-GO hasta decisión de modelar Pro actual (cohorte
presente) y mantener ensayo futuro contraído como prueba distinta. No modificar Pro
para acomodarlo al fixture. No hubo remediación de schema tras ese hallazgo.

Revalidación local posterior de inventario: pytest completo **282 passed/4 skipped**,
credential scan y git diff --check PASS; esos checks no cubren el HIGH Edge success
ni la discrepancia de baseline. Build CI/UAT final/rollback siguen pendientes.

## Cambios y regresiones cubiertas — histórico previo al corte vigente

- `admin-invite` clasifica 408/5xx y errores de red/Auth ambiguos como entrega
  desconocida antes de aplicar texto de rate limit; 429 mantiene su clase explícita.
- La reserva serializa por email y request ID; un mismo request ID no crea una
  segunda invitación, incluso si se cambia el payload.
- `admin_invitation_complete` repara idempotentemente el caso en que el destinatario
  acepta antes de terminar la persistencia de entrega. Solo completa el marcador y
  la auditoría cuando Auth user, usuario aceptante, membresía, rol, última invitación
  y estado `password_pending`/`ready` coinciden.
- Las rutas SQL de fallo, expiración, completion y reconciliación siguen el orden de
  locks por email y miembro antes de invitación. Hay harness concurrente para reserva,
  aceptación/reenvío y lectura de onboarding/completion.
- El agregador del workflow espera la ejecución confiable `pull_request_target` o
  `pull_request_review` correspondiente a PR + head SHA + evento. Los timestamps de
  reviews `submitted` y `dismissed` se seleccionan por acción; un timestamp faltante
  falla cerrado. Se conserva el job name estable `Protected Workflow Integrity`.
- El CORS no refleja Origin inválido/opaco/no autorizado; el request ID validado se
  propaga y conserva para soporte/reintento.

## Validaciones ejecutadas — histórico r14 previo al transporte nuevo

| Gate local | Resultado |
|---|---|
| Build estático aislado | **PASS** — `npm run build`; no sobrescribió `web/out` del checkout |
| UAT visual Pages local `r14` | **PASS** — 48/48 casos, 144/144 ejecuciones, 144 capturas, 0 retries; perímetro validado |
| UAT invitaciones/onboarding | **PASS** — 10/10 casos |
| UAT BFF `h3_admin_bff_mock_uat.mjs` | **PASS** — 52 checks |
| UAT errores cliente `h3_admin_auth_error_uat.mjs` | **PASS** — 7 checks |
| UAT SDK headers `h3_supabase_sdk_headers_uat.mjs` | **PASS reportado** — 15 checks interceptados; **no cierra** el hallazgo de ruta/JWT: usa token fixture y una lectura de tabla |
| UAT Edge `h3_admin_invite_edge_uat.mjs` | **PASS** — 6 CORS, 7 clasificaciones, 10 ambigüedad, 4 replay, 1 replay concurrente y 1 expiración |
| `pytest tests -q` completo | **PASS** — 281 passed, 4 skipped; 1 warning de deprecación `PyPDF2` |
| PG17 `h3_pg17_harness.sql` | **PASS** — modo Free con cohorte y modo Pro sin cohorte; incluye rechazo de edición con membresías `invited` y `password_pending` activas |
| H2 Pro PG17 baseline | **PASS** — cohorte `private.h2_legacy_public_course_cohort` ausente; H3 no la recrea |
| `h3_invitation_reservation_concurrency.sh` | **PASS** — `h3_invitation_reservation_concurrency_ok` |
| TypeScript `npx tsc --noEmit` | **PASS** |
| ESLint | **PASS** — 0 errores, 9 warnings ya presentes en `HomeContent.tsx` |
| `npm audit --include=dev` | **PASS** — 0 vulnerabilidades |
| Credential scan del árbol | **PASS** |
| `actionlint` workflows modificados | **PASS** |
| `shellcheck` hooks/scripts | **PASS** |
| `git diff --check` | **PASS** |
| Revisión read-only de seguridad | **NO-GO** — el informe precede al último delta SQL; hallazgo de estado mitigado localmente, reauditoría exacta pendiente; siguen CI HIGH, rate-limit MEDIUM y transporte JWT LOW |

El build y Wrangler Pages corrieron aislados en Docker (`Node 20.20.2`, Wrangler
`4.86.0`, compatibility date `2026-05-03`). El UAT apuntó solo a mocks locales; no
usó URL/key ni Auth de Supabase remoto. Los fallos de entorno de `r12` y `r13` se
preservaron; `r14` se ejecutó con puertos y procesos verificados. El artefacto actual
está en `C:\Users\Romel\AppData\Local\Temp\opencode\h3req1-uat-20261002-r14`.

## Hallazgos y gates pendientes — histórico previo a aprobación JWT

- **HIGH — integridad de CI:** `security-audit` es modificable junto con el PR. No
  se acreditó en remoto un workflow mantenedor independiente ni que
  `Protected Workflow Integrity` sea un check requerido. No se consultó GitHub en
  esta continuación; el HIGH bloquea GO.
- **MEDIUM — rate limiting:** faltan cuotas propias por actor/IP para login, RPCs e
  invitaciones. El responsable lo incluyó en el cierre actual: se retira el
  diferimiento, sin waiver. Arquitectura y cuotas pendientes de aprobación/pruebas.
- **LOW — autorización editorial:** corregido localmente para exigir miembro activo
  `ready`; las dos variantes PG17 rechazan `invited`/`password_pending` activos. La
  revisión read-only previa al cambio aún debe repetirse sobre el árbol exacto.
- **LOW — transporte JWT:** la regla aprobada autoriza JWT Bearer solo a RPCs
  allowlisted. El BFF runtime también realiza llamadas Auth/MFA y `admin-invite`;
  el helper actual no restringe destinos ni exige forma JWT. No se amplió el alcance
  porque no se recibió decisión para esos destinos; UAT de headers actual no prueba
  la política requerida.
- **Rollback DB:** no se aportó rollback SQL compensatorio ejecutable ni drill. No
  desplegar ni aplicar migraciones; antes del JIT se debe definir restauración de
  funciones/vistas y preservación de columnas/auditoría nuevas.

No hubo consulta/escritura Supabase, consulta a GitHub, push, PR, merge, deploy,
workflow dispatch, reset de cuentas, ni cambios de ramas protegidas. Local y remoto
siguen **NO-GO**.

### Inicio de continuación Build — actualización documental, no PASS nuevo

Se actualizaron estado/plan/evidencia con tareas y gates del plan acordado. El
trabajo local solicitado incluye corregir build CI, demostrar H2 Pro -> H3 en una
misma base PG17 y preparar rollback compensatorio; esas tres tareas aún no se han
ejecutado en esta continuación y no reciben PASS por los harnesses/build previos.
Se mantiene Auth/MFA/invitaciones y dos colaboradores (uno aprueba y otro mergea).

JWT: propuesta acotada de proyecto/ruta/método para RPC, Auth/MFA y `admin-invite`,
pendiente de aprobación antes de cambiar transporte o atestación. Cuotas: servicio
interno Cloudflare/Durable Objects por binding propuesto, no aprobado/desplegado.
No hubo operaciones remotas, cambios funcionales ni modificación del WIP original
en esta actualización. El manifiesto anterior ya no identifica los bytes de estos
documentos; conservarlo histórico y regenerar manifest de fuentes al congelar el
próximo candidato. NO-GO sigue vigente.

Validaciones de esta actualización documental en Docker: `17 passed` en
`test_obsidian_context_state.py` y `test_requirement_client_source_validation.py`;
credential scan del árbol y `git diff --check` PASS. No acreditan los cambios
funcionales pendientes ni amplían autorizaciones remotas.

### Resultado parcial posterior a aprobación JWT — no cierre de ciclo

- Aprobación humana `Aprobar cierre` recibida para los destinos exactos presentados.
  Atestación/contrato/inventario actualizados antes de implementación local.
- Transporte de sesión limitado a proyecto/ruta/método y redirects rechazados.
  Navegador sin excepción Bearer; BFF RPC/Auth/MFA/Edge autorizados; Edge solo
  GET Auth user para identidad del solicitante. Supabase valida el JWT, no el regex.
- Docker: SDK interceptado **23 escenarios PASS**, BFF **52 PASS**, Edge PASS,
  TypeScript PASS, pytest **282 passed/4 skipped**. UAT visual final pendiente y
  reauditoría requerida; resultados r14 preceden al nuevo transporte.
- CI: build previo `example.invalid` retirado y smoke con readiness de fixture
  local. actionlint/shellcheck PASS; build/job completo modificado **PENDIENTE**.
- H2 Pro -> H3 en servidor PG17 limpio: **FAIL**, vista Admin requiere
  `courses.provider_used` que no existe en el fixture H2 Pro. La migración de tracking
  de proveedor está versionada, pero no se verificó schema/ledger Pro remoto. No
  completar fixture con columnas por suposición ni declarar compatibilidad.
- Primer intento en servidor PG17 compartido se detuvo al DROP de roles usados por
  otras bases; ninguna base previa se eliminó. Segundo intento en nuevo servidor
  aislado ejecutó baseline H2 y reprodujo el FAIL H3 real descrito.

Se detiene ante drift de baseline para decisión humana. SQL compensatorio y cuotas
siguen pendientes; NO-GO. No hubo operaciones remotas ni modificación del WIP.

### Corrección documental del plan de sincronización

La revisión humana pidió incorporar las correcciones al plan: respaldo recuperable
verificado (no solo inventario), selección de deltas con comparación de tres versiones
en aislamiento, revisión de todos los cambios y no solo los 24 solapamientos,
baseline Pro read-only/migraciones, bootstrap del control CI externo sin circularidad,
hash de fuentes/artefacto servido y gates sobre el candidato sincronizado final.
Se exige reauditoría, aceptación cliente y veredictos local/remoto separados. El HIGH
no se cierra ni reclasifica automáticamente; el MEDIUM diferido no es waiver.

Resultado del preflight: respaldo verificable creado; después, con aprobación
humana exacta, se creó un worktree aislado desde el baseline remoto. **NO-GO
preservado**: no se sincronizaron fuentes ni se ejecutaron actionlint/shellcheck,
PG17 o UAT nueva.

### Preservación verificable del checkout — 2026-10-02

Primer preflight, antes del respaldo `verified2`: `HEAD=7650093b05a820e8e6faf9ec711e12fab8b50398`,
`origin/desarrollo=4eb4d877a50b012bb630a129bd0c74482c33be9c`, merge-base
`97168646b2a6bbd8e59f6d704446759303e11e64`, divergencia `27/5`, 1.706 entradas
en Git status y 0 staged. Pasaron credential scan del árbol versionado y de 1.652
archivos nuevos candidatos (15 configuraciones locales quedaron fuera, intactas en el
checkout) y `git diff --check`.

El respaldo externo más reciente está en
`C:\Users\Romel\AppData\Local\Temp\opencode\studiamatch-h3req1-sync-backup-20261002-verified5`.
Incluye patch binario, tar de fuentes nuevas y evidencia, hashes por archivo, estado,
rutas excluidas y referencias Git. Se verificaron 38 hashes de archivos tracked
presentes, 1.652 archivos nuevos y la integridad de patch/tar/manifiestos; `SHA256SUMS`
permite revalidarlo. El snapshot `verified2` tenía 15 rutas locales excluidas; después
apareció `.obsidian/workspace.json`, que permanece intacto y excluido. El snapshot
final `verified5` registra 1.707 entradas de estado y 16 rutas locales/configuradas
excluidas. No se copió, eliminó ni modificó código.

La inspección read-only de `git worktree list` encontró cinco entradas stale/prunable
con gitdir ausente. No se ejecutó prune ni cleanup. Tras aprobación se creó
`/home/romel/src/studiamatch-h3req1-sync-20261002` en branch
`feat/h3req1-sync-20261002`, exactamente en `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
En ese corte de creación el worktree estaba limpio; después recibió los deltas
registrados y probados en las secciones actuales anteriores.

### Reconciliación de deltas — preflight histórico solo lectura

Se repitió fetch read-only sin cambio de refs: WIP `7650093b05a820e8e6faf9ec711e12fab8b50398`,
`origin/desarrollo=4eb4d877a50b012bb630a129bd0c74482c33be9c`, merge-base
`97168646b2a6bbd8e59f6d704446759303e11e64`, divergencia `27/5`; `git cherry`
confirma tres patches equivalentes y dos commits no equivalentes. El diff del árbol
completo local respecto al remoto abarca 43 rutas tracked, además del inventario de
1.652 archivos nuevos preservados en el respaldo, 1.488 de ellos evidencia histórica/visual.

En las 24 rutas solapadas se hizo preview textual de merge de 3 vías, sin aplicar
cambios: 19 integran sin conflicto textual; cuatro son altas independientes
posteriores al merge-base que requieren decisión semántica. No incluye una revisión
de comportamiento ni reemplaza la revisión manual. Se preservó la versión remota
de `STUDIAMATCH-H3-UAT-MOCK-02-REPORT.md` y de
`.context/evidencia/h3req1_development_validation_2026-09-24.md`, pues las elimina el
candidato local sin decisión de borrado. El PR template del WIP está prellenado para
otro alcance y no se portará. En aquel corte, las cuatro migraciones nuevas seguían
pendientes de comparación con baseline Pro. Durante el port se eliminó el fallback de hostname
Preview compilado de `admin-invite`; callback y CORS requieren variables de ambiente
explícitas y fallan cerrado. Después se ejecutaron los UAT y harnesses locales
registrados arriba.

`protected-workflow-integrity.yml` no existía en ese baseline y no se acreditó su
enforcement remoto; el HIGH de CI continúa abierto. En ese corte no se hizo
cherry-pick, rebase, copy/apply, DDL/DML/Auth, push/PR/deploy ni validación funcional
del candidato aislado. Las validaciones posteriores están en la sección actual.

## UAT visual y archivos de evidencia

- `r8`: configuración inicial inválida del runner; 0/144. Se conserva para
  trazabilidad, no cuenta como gate.
- `r9`: 30/144 ejecuciones PASS, 10/48 casos lógicos PASS y 144 capturas. Las
  fallas del BFF fueron 404 del servidor Next dev sin runtime Pages Functions.
- `r10`: **FAIL**, 141/144 ejecuciones PASS y 47/48 casos lógicos PASS, 144
  capturas, 0 retries. `H3-UAT-038` falla en desktop/tablet/mobile porque recibe
  `duplicate_ready`/409 en vez de `invitation_failed`/502. Se conserva como
  evidencia del hallazgo y su remediación.
- `r11`: **PASS**, 144/144 ejecuciones y 48/48 casos lógicos PASS, 144 capturas,
  0 retries (`generatedAt` `2026-10-02T03:02:51.231Z`). La traza de `H3-UAT-038`
  registra POST `/api/admin/invitations` → 502. Esta ejecución fue anterior a la
  aserción explícita de status agregada al runner y al hardening adicional de errores
  RPC.
- `r14`: **PASS**, 144/144 ejecuciones y 48/48 casos lógicos PASS, 144 capturas,
  0 retries (`generatedAt` `2026-10-02T14:37:37.866Z`). Corrió sobre export aislado
  actual de la web con perímetro hostname allowlisted; artefacto y checksums están
  documentados al inicio de esta evidencia.

Carpetas preservadas en el checkout ORIGINAL (no se copiaron al worktree candidato).
Las rutas relativas siguientes cruzan entre checkouts y se comprobaron presentes;
dependen de esa estructura local. Ver [mapa de assets externos](../seguimiento/mapa_documental_obsidian_2026-10-04.md)
y [traspaso actual](../seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md).

- [`r8` original](../../../studiamatch/.context/evidencia/h3-expanded-bff-2026-10-01-r8/)
- [`r9` original](../../../studiamatch/.context/evidencia/h3-expanded-bff-2026-10-01-r9/)
- [`r10` original](../../../studiamatch/.context/evidencia/h3-expanded-bff-2026-10-01-r10/)
- [`r11` original](../../../studiamatch/.context/evidencia/h3-expanded-bff-2026-10-01-r11/)
- `r14`: `C:\Users\Romel\AppData\Local\Temp\opencode\h3req1-uat-20261002-r14`

## Transición, rollback y límites

- **Expand:** BFF same-origin/HttpOnly, funciones Pages y RPCs/migración local
  idempotente se validan como candidato, conservando Auth/MFA/RBAC y la UI existente.
- **Compatibilidad:** UAT mock visual r14 completa bajo Wrangler Pages local pasa.
  Las cuentas existentes deben limpiar la sesión legacy y reautenticar la misma
  cuenta con MFA; no se canjean tokens legacy, crean cuentas ni repiten onboarding.
  La transición real de cuentas en producción aún no se ejecutó.
- **Deploy:** no ejecutado. Cada gate remoto, Free/Preview/Auth, DDL, workflow o
  publicación requiere aprobación JIT separada.
- **Contract:** retirar rutas/session storage legacy solo tras estabilidad de
  producción acreditada; no ejecutado ni autorizado en este ciclo.
- **Rollback:** antes de cualquier promoción, deshabilitar el candidato y volver al
  SHA Pages previamente aprobado; no degradar a tokens JS ni limpiar datos. La
  estrategia SQL compensatoria para funciones/vistas, preservación de columnas y
  auditoría nuevas, y compatibilidad con el SHA anterior aún deben especificarse y
  probarse antes de JIT/deploy. No hay script de rollback ejecutable ni drill.

Los gates remotos H3-003/H3-004, hostnames/artefacto Pages de Development, aprobación
de branch protection, rollback remoto y UAT con Pages real continúan pendientes.
La reauditoría del árbol exacto y la decisión sobre los destinos JWT Auth/Edge siguen
pendientes; el ciclo permanece **NO-GO global**. No hubo escrituras Supabase remotas,
consulta remota a GitHub, workflow remoto ni promoción de ramas.

## Plan posterior y límites de esta evidencia

El [plan GO local y Development integral](../operaciones/plan_go_h3req1_local_development_2026-10-02.md)
registra etapas, gates, preguntas interactivas, inclusión condicionada de las
remediaciones en PR y reinicio Free acotado tras inventario. No acredita acciones
ejecutadas ni amplía autorizaciones. El siguiente cierre local requiere candidato
exacto, reauditoría, decisión explícita de transporte, rollback documentado y
validación de gates afectados. El cierre remoto se evalúa después y por separado con
JIT, integración protegida y evidencia real.
# Corte cuotas/runtime — evidencia local, NO-GO integral

Arquitectura local aprobada por el responsable mediante «Aprobar diseño local».
No operación remota posterior. Worktree y evidencias anteriores conservados.

| Evidencia | Resultado y límite |
|---|---|
| DO real | Miniflare4.20260730.0/workerd, Node22.22.0, SQLite persistente: 25 requests concurrentes, 10 admitidos, 15 rechazados, reinicio mantiene cuota. Último artefacto runtime `/tmp/h3-quota-runtime-R71A8i` en contenedor check. No runtime Cloudflare remoto. |
| PG17 r3 | `h3_quota_current_r3`, `h3_quota_future_r3`; logs `/tmp/h3-quota-sql-r3` en check: H2/H3 misma base, expand/reserva legacy/activación/finalizador, doble reaplicación, límites/ACL/suspensión PASS. No datos remotos. |
| Concurrencia SQL r2 | 35 conexiones al mismo scope, 30 admitidas/5 bloqueadas; `/tmp/h3-quota-concurrent.IOgBC8`. Scope privado sintético, no UAT Auth. |
| Wire local | PostgREST13.0.7 digest `sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228` + SDK: 403 MFA conserva admisión, lector legacy120 después429/Retry-After, service-only denegado. PGfixture TEST-only; no semejanza acreditada de versión/config Free. |
| Build CI snapshot | `/tmp/h3req1-ci-quota-20261002-r1` en build: npmci, JS, smoke/build, DO runtime PASS; ANTERIOR a último transporte/cookies/suspensión, no candidato final. |
| Build UAT r7 | `/tmp/h3req1-final-quota-20261002-r7`: npmci/buildmock PASS; artefacto mock Auth/PG17, no build production. |
| UAT r8 | `r7/evidence-r8`: FAIL, 26/48 lógicos y80/144 ejecuciones PASS,143capturas,0retries. Snapshot contratos faltantes, query editor perdida, sesiónAAL2 inestable. |
| UAT r10 | `/tmp/h3req1-final-quota-20261002-r10/.h3-expanded-44663-1790980391061.tmp`: sin resultado final. Se detuvo runner PID44663 propio tras >40min/dos timeouts, preservando staging/capturas. No retries ni matrizPASS inferida. |
| Revisión | `ses_f0118bf9cffeK47ubskTUvcYSB`: cero nuevosHIGH/MEDIUM focalizados; HIGH runtime requiere UAT final, riesgo PGRST/abort rollback de cuota no waived. |

HIGH runtime encontrado en workerd: `redirect:error` no soportado. Cambiado a
manual + rechazo3xx/opaqueredirect, sin seguirLocation ni ampliarJWT allowlists;
SDK26+7redirecttests y Edge interceptados PASS, smoke workerd loginPASS. Slash
preservaquery. Lecturas ya no reemiten Auth request cookie (riesgo de sobrescribir
AAL2 por respuesta AAL1 tardía); SDKsetAll permanece. Logout limpia SSRchunks y
verifier con CSRF, sin upstream/config/cuota ni nuevos destinosJWT. No afirmar
cierre runtime/AAL2 con contratos/smoke; UAT144/144 es gate bloqueante.

Driver preserva ahora backups/staging/progreso y timeoutcaptura10s, sin borrar
evidencia fallida. Cambio posterior a r10; suite actual aún no ejecutada completa.
Pytest282passed/4skipped/1warningPyPDF2, webtypecheck, Edge strictSDK2.109.0,
BFF52+6cuotas, SDK26+7redirect, Edge, cuotaunitaria y suspensiónmiddlewarePASS.
Actionlint/credentialscan/diffcheckPASS antes de esta actualización documental.
Plan vigente registra expand/compatibilidad/deploy/contract, suspensión segura,
variables por nombre y matriz JIT. No hashes finales congelados, GO ni remoto.

## Revalidación final local y triage — 2026-10-02

### UAT visual y capturas

Se conservaron rondas fallidas separadas en el contenedor Docker
`studiamatch-h3req1-check`:

| Ronda | Resultado | Diagnóstico |
|---|---|---|
| r13 | **FAIL**, 142/144 ejecuciones y 142 capturas | Export usado apuntaba a `example.invalid`; dos rutas públicas fallaron por recursos. No se contó como candidato final. |
| r14 | **FAIL**, 143/144 y 143 capturas | `build:mock` no generó rutas de cursos del mock y una captura móvil excedió 10 s. |
| r15 | **FAIL**, 142/144 y 142 capturas | Export reconstruido con PostgREST local; dos capturas de `/` excedieron 10 s. |
| r16 | **FAIL**, 142/144 y 142 capturas | Dos capturas de `/` (desktop/tablet) excedieron 20 s; cero errores de consola, requests fallidos o aserciones funcionales fallidas en esas ejecuciones. |

Diagnóstico puntual posterior a r16 reprodujo GET de las cinco rutas y screenshot
full-page sobre los mismos assets: desktop 1440×900 completó en 901 ms y tablet
820×1180 en 419 ms, sin errores. Es compatible con una falla intermitente/contención,
pero no sustituye capturas faltantes ni autoriza retries silenciosos. r17 corrió con
export PostgREST y sin carga concurrente: **PASS 48/48 casos lógicos, 144/144
ejecuciones, 144 capturas, cero retries**, `generatedAt=2026-10-03T02:15:53.295Z`.
Su matriz, ejecuciones, manifiesto, checksums y capturas están en
`/tmp/h3req1-go-candidate-20261002-r14/evidence-expanded-uat-r17` dentro del
contenedor `studiamatch-h3req1-check`. No se modifica ni sobrescribe r13–r16.

Las fuentes web copiadas al snapshot r14 coinciden con las del worktree en 61/62
archivos (la única diferencia fue `tsconfig.tsbuildinfo`, artefacto generado). Se
comprobó presencia de las rutas de cursos UTP/USIL y carga móvil sin errores al usar
el build PostgREST. El hash del manifiesto candidato sigue pendiente; r17 acredita
la matriz visual del snapshot local, no acepta por sí solo todos los gates del ciclo.

### Diagnóstico de onboarding paced — ejecución fallida y corrección de test

La primera ejecución separada de `tests/h3_invitation_uat.mjs` terminó en el primer
envío UI esperando respuesta 30 s. Antes de cualquier reintento, una lectura de la
base PG17 local confirmó cero filas `uat-user-*` en `admin_invitations` y cero
identidades Auth asociadas; no se había emitido una invitación.

El diagnóstico mostró que el helper `loginAdmin` esperaba solo el heading de la cola
tras MFA. A diferencia del helper de la suite visual, no esperaba una respuesta
server-side `/api/admin/session` con `authenticated=true` y `aal2`. El gate AAL2 no
estaba acreditado antes de navegar a gestión de usuarios. En un fixture local
reiniciado, al esperar explícitamente AAL2, assurance dio `aal2`,
`admin_list_members_onboarding` respondió HTTP 200 y el botón quedó habilitado; no se
envió ninguna invitación durante ese diagnóstico.

Se endureció el test local: espera confirmación AAL2; exige el botón habilitado antes
del click; usa matcher same-origin + pathname exacto, y empieza el timeout de respuesta
después del pacing (20.1 s; timeout 60 s). `node --check` y typecheck semántico Edge
PASS. La segunda ejecución paced cerró **PASS 10/10**: INV-013, INV-008, INV-001,
INV-002, INV-009, INV-007, INV-003, INV-004, INV-005 e INV-012. El resumen
sanitizado está en
`/tmp/h3req1-go-candidate-20261002-r14/evidence-onboarding-uat-r1/summary.json`
en el contenedor, SHA-256
`b258c833c3034326a734fa57c3026409c88b0d9ba321c7f3f6d4115261585d01`. La suite usa
emails sintéticos locales; no persiste en el resumen emails, mailbox ni tokens. Este
PASS es solo mock/PG17, no acredita entrega/aceptación Auth remota.

### Dependencias

`npm audit --include=dev` devuelve exit 1: **9 HIGH, 0 CRITICAL**. Aviso raíz
`GHSA-vfj7-8cjw-p6xm`, `braces <=3.0.3`, CVSS 7.5, sin versión corregida compatible;
cadena `micromatch@4.0.8` → `fast-glob` dentro de shadcn y ESLint Next. Tras clean
install/build/lint/typecheck aislados se reclasificó `shadcn@4.21.1` como
`devDependency`: `globals.css` importa `shadcn/tailwind.css` al compilar el static
export y no existe consumo de runtime. `npm audit --omit=dev` sobre el worktree da
**0 HIGH/0 CRITICAL**; el audit completo sigue en **9 HIGH/0 CRITICAL**. `npm audit
fix` y cambios mayores incompatibles se descartaron; sin waiver.

Validación del snapshot `/tmp/h3req1-deps-triage-20261002-r2/web`: `npm ci` limpio,
TSC, ESLint y build estático contra PostgREST local PASS. Los 151 assets de `out/`
coinciden exactamente por SHA-256 con los del snapshot r14; las versiones,
resolutions e integridades de paquetes coinciden con el lockfile previo, y el cambio
solo añade marcas `dev` al árbol de dependencia. La reclasificación quedó aplicada a
`web/package.json` y `web/package-lock.json`. No se usaron secretos ni APIs/DB/Auth/
BFF de los ambientes del proyecto; solo metadata pública del registry NPM.

### Gates confirmados y bloqueos residuales

Continuación local autorizada: ratificado umbral Edge 120/min sin despliegue. Con JIT
específico para PG17 desechable `h3_final_uat_go_r14`, el preflight read-only verificó
versión 17.11, schema de invitaciones/auditoría/cuota y cero conexiones activas
ajenas; `psql -X -v ON_ERROR_STOP=1 -f tests/sql/h3_safe_suspend_harness.sql`
devolvió `h3_safe_suspend_harness_ok`. Se conserva log en
`/tmp/h3req1-go-candidate-20261002-r14/evidence-safe-suspend-pg17-r1/` del
contenedor. Harness SHA-256
`c1dcfef828b836e6627530127eb66a157db1df1437ad923a06f6c64e2c6782f1`;
rollback SQL SHA-256
`09fcd8f6a5b9590f2e8db20f00c0fd9244ffd6a4a8db714c3c2837f04c22369d`.
El test reanuda grants solo para verificar idempotencia/recuperación en fixture, no
proporciona una operación de resume remoto. Pages middleware fixture y workerd y
Edge fixture de suspensión pasan separadamente; **faltan** la ejecución integrada
Pages/Edge/cookies/bindings/SQL y recuperación operativa autorizada.

Inventario estático de 94 migraciones `2026*.sql`: solo los dos archivos H3 de cuota
levantan `PGRST`; los originales versionados no introducen esa excepción. Aun así,
el wrapper repropaga PGRST de cuota y un `ROLLBACK` exterior revierte las admisiones
SQL: no prometer conteo de todos los intentos ni afirmar baseline Pro verificado.
Análisis de mitigación sin cambios SQL: para contabilizar incluso transacciones
abortadas se requiere admisión fuera de esa transacción; BFF/DO ya cubre su propio
perímetro, pero el JWT permite RPC directa. Requeriría gateway firmado y
contracción de grants tras fase compatible, además de admisión durable Edge antes
de Auth y pruebas de identidad/RLS/AAL2/replay. No se implementó, ni hay JIT para
DB/infraestructura remota. En Docker, `braces`/`micromatch` latest y el plugin ESLint
Next latest conservan la cadena vulnerable; 9 HIGH son paquetes alcanzados por el
aviso raíz, no nueve fixes independientes. El audit full sigue FAIL.

Inventario GitHub read-only con autorización humana separada: en
`romelhc95/studiamatch`, `desarrollo` es protegida y permanece en
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. El árbol remoto de workflows
incluye `security-audit.yml` pero no `protected-workflow-integrity.yml`; el último
solo existe en WIP local. No hay PR abierto con base `desarrollo` al consultar.
Colaboradores visibles: owner `romelhc95` (admin) y
`romelhc95-approver` (write). No se pudo leer required checks/rulesets efectivos
con la herramienta GitHub disponible: la etiqueta `protected=true` no prueba
enforcement del check independiente, ni disponibilidad de aprobaciones en un futuro
PR. No se hizo ninguna escritura GitHub, push, PR, revisión ni merge.

- Docker pytest completo: **283 passed, 4 skipped**, los cuatro tests de integración
  Supabase requieren `RUN_SUPABASE_INTEGRATION_TESTS=1`; no se activaron ni se hicieron
  llamadas live. Warnings ESLint: cero errores y 9 existentes; warning Python de
  deprecación `PyPDF2`.
- TypeScript, `actionlint`, `shellcheck`, credential scan y `git diff --check`: PASS.
  BFF mock 52, Edge invite, SDK headers 26, middleware fixture y runtime
  workerd/Miniflare PASS; ocho aliases Admin rechazados sin fallback, tres rutas
  públicas preservadas.
- Workflow local: `workflow_dispatch` sin baseline confiable falla cerrado en gates
  de rutas/DB; push inicial transforma el SHA cero al empty tree. `actionlint` y
  contratos pasan; esto no prueba que el workflow/check esté protegido en GitHub.
- Probe PG17 sintético: una admisión SQL de RPC directa existe dentro de la transacción
  y desaparece tras `ROLLBACK`. Riesgo MEDIUM confirmado: transacciones abortadas o
  canceladas no quedan contabilizadas; no se presenta como cuota de todos los intentos
  y no existe waiver aprobado.
- Sigue NO-GO por 9 HIGH en el audit completo, riesgo de cuota SQL transaccional,
  CI independiente no acreditado remotamente, rollback
  Pages/Edge/cookies/bindings no ensayado integrado, aceptación/pilares y hashes
  congelados pendientes. No se consultó GitHub/Supabase/Cloudflare ni hubo push, PR,
  merge, deploy o write remoto en esta validación.
