## Resumen

Sucesor local de H3REQ1 para integrar en `desarrollo` bajo PR protegido. Incluye el alcance funcional R8, la selección documental R13 reconciliada por R14 y los deltas R19 autorizados. Conserva R8/R9/R12/R13 y sus evidencias; R18 permanece histórico e intacto. No incluye WIP ajeno ni reabre la reorganización Obsidian. El veredicto actual es **NO-GO Development**: todavía no hay SHA nuevo, deployment R19 ni aceptación remota.

- Repositorio: [romelhc95/studiamatch](https://github.com/romelhc95/studiamatch), PR [#501](https://github.com/romelhc95/studiamatch/pull/501), destino `desarrollo`.
- Rama: `feat/h3req1-sync-20261018-r19`; HEAD local y remoto actual: `074583d9f6ea1b5686dc58c9669111f589cb8e7a`; baseline `desarrollo`: `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Las correcciones locales de workflow, guard, scanner, consumidores y el input directo del gate PostgreSQL siguen sin commit. La identidad exacta del paquete es el [manifiesto R19](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencia/h3req1_pr_scope_manifest_2026-10-18_r19_reconciled.json), que registra 1.179 rutas y seis artefactos de paquete adicionales.
- Evidencia vinculante: [estado vigente](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/estado_del_proyecto.md), [atestación cliente sanitizada](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md), [reporte remoto](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencia/h3req1_g10_remote_preparation_2026-10-18_r19.md), [paquete Development](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencia/h3req1_development_integration_package_2026-10-18_r19.md), [validaciones](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencia/h3req1_remote_preparation_checks_2026-10-18_r19.txt), [revisión independiente](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencia/h3req1_remote_preparation_independent_review_2026-10-18_r19.txt) y [tratamiento visual](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencia/h3req1_visual_evidence_redaction_2026-10-18_r19.md). El documento privado del cliente no se incluye.

## Evidencia De Este PR

- Docker aislado `studiamatch-dev:r19-20261018`: PostgreSQL 17.11/PostgREST 13.0.7 y las 11 invocaciones Node directas de Static Build pasan en el snapshot R19, incluidos el build mock H2 y los UAT runtime con Node 22.22.0. El flujo Python completo definido por `security-audit` también pasó con dependencias instaladas desde `requirements-pipeline.txt` bajo hashes: `py_compile`, escaneo H2, scanner regresiones/árbol, guard/negativos, pytest primario 250 passed + 10 subtests y segunda invocación 41 passed. Se corrigieron tres expectativas obsoletas; sus consumidores afectados y los 34 tests de seguridad/H2 ahora pasan. actionlint 1.7.7, ShellCheck 0.11.0 y `bash -n` pasan sobre inputs focales. Guard: 1.185 rutas (1.179 scope + 6 artefactos), 13 catálogos/1.173 referencias; negativos ordinary=3, newline=1, controls=1, malformed=3, unmanifested H3=2. Ningún PASS local es resultado de GitHub ni aceptación Development.
- El cambio tooling saca la comparación de 86 KB del bloque `run:` del workflow y la invoca mediante `scripts/security/protected_path_scope_guard.sh --compare-candidate`. La allowlist y sus límites se conservan; las pruebas leen ahora el helper como fuente. Dos expresiones SC2015 del scanner se expresan con condiciones explícitas equivalentes.
- Una invocación documental sin manifiesto en la copia sparse reportó rutas WIP registradas pero excluidas del paquete. La invocación exacta de CI con manifiesto candidato pasó; también pasó el self-test global del checkout de origen. No se añadieron esos WIP al paquete.
- La lectura de GitHub del 2026-10-19 10:57 UTC confirma que el SHA remoto sigue en `074583d9f6ea1b5686dc58c9669111f589cb8e7a`; el cuerpo remoto aún refleja el snapshot previo. El run [39228507399](https://github.com/romelhc95/studiamatch/actions/runs/39228507399) permanece `in_progress` en actionlint; ShellCheck sigue pendiente. Python Compile And Tests, Static Build y PostgreSQL fallaron en ese checkout anterior por dependencias/configuración ausentes: el log registra `tests/test_h3req1_c03_docker_daemon_identity_f2d.py`, `tests/h3_admin_auth_error_uat.mjs` y `tests/h3_admin_quota_postgrest.mjs`. La entrada PostgreSQL recuperada coincide byte por byte con el checkout fuente (SHA-256 `e11034070050212bffe961f87467cc727b0c16053a3319515acb477f63d28e95`); el paquete local actual contiene los inputs y sus validaciones Docker pasan. Estos resultados no reemplazan los checks remotos del sucesor.
- En ese run pasaron Documentation Source Registry, TypeScript, ESLint, Credential Scan y Protected Path Integrity; H2 Main Production Expand Gate quedó `skipped` fuera de alcance. CodeQL había terminado en success para `074583d9` según [39228503767](https://github.com/romelhc95/studiamatch/actions/runs/39228503767), pero no hay lectura individual de las alertas ni análisis del delta local. Cloudflare Pages sirvió Preview para el SHA viejo; no es aceptación Development. El job actionlint sigue en curso y ShellCheck pendiente; actionlint 1.7.7 y ShellCheck 0.11.0 pasan localmente sobre inputs que no cambiaron.
- Protected Workflow Integrity falló porque el checkout confiable `desarrollo` usado por el job no contiene `scripts/security/protected_workflow_review.py`; añadirlo al head de este PR no lo hace visible durante la misma comprobación protegida. Las ejecuciones visibles son [117980575050](https://github.com/romelhc95/studiamatch/actions/runs/39228507363/job/117980575050) y [117980944207](https://github.com/romelhc95/studiamatch/actions/runs/39228629396/job/117980944207). Una ruta viable sin modificar `main` ni debilitar checks es el verificador externo con GitHub App mínima descrita en el paquete JIT `/tmp/h3req1_pwi_external_check_app_jit_package_20261019.md`; su instalación sigue sin aprobación y no se ejecutará por inferencia.
- Los cuatro hallazgos CodeQL del PR y las alertas históricas de `main` son inventarios separados. Las alertas individuales no son legibles por el conector: ni el éxito del run CodeQL ni las correcciones locales permiten declararlas cerradas. El aprobador anterior figura `DISMISSED`; no aprueba ningún SHA futuro.

### Cuatro hallazgos CodeQL reportados para PR 501

Los siguientes avisos se reportaron en el commit analizado `d5220185cbb8d1975ebb901a5d6e8e77636b8b02`; las rutas/líneas son sus ubicaciones originales en esa versión. Su disposición por alerta no fue verificable. El CodeQL del SHA posterior `074583d9f6ea1b5686dc58c9669111f589cb8e7a` terminó en success, pero hace falta un análisis del nuevo SHA y lectura de alertas para afirmar cierre individual.

| Regla/severidad | Archivo y ubicación analizada | Corrección local incluida | Estado verificable |
|---|---|---|---|
| Inefficient regular expression — High | `scripts/core/universal_harvester.py:316` | Detector estructural lineal, patrón acotado y timeout con rechazo cerrado. | Regresión local previa PASS; alerta individual pendiente de lectura CodeQL sobre SHA nuevo. |
| Incomplete multi-character sanitization — High | `scripts/maintenance/h3req1_documentation_integrity.mjs:53` | Parser de tags con estado y casos de atributos/markup incompleto. | Self-test local con manifiesto PASS; alerta individual pendiente de lectura CodeQL sobre SHA nuevo. |
| Server-side request forgery — Critical | `tests/h3req1_c03_integrated_runtime.mjs:317` | Destino PostgREST desde allowlist local exacta; se rechaza antes de `fetch`. | Self-test local de destinos proxy PASS; alerta individual pendiente de lectura CodeQL sobre SHA nuevo. |
| Server-side request forgery — Critical | `tests/h3req1_c03_integrated_runtime.mjs:348` | Origen Edge fijo, ruta `/admin-invite` fija y query de caller descartada. | Self-test local de destinos proxy PASS; alerta individual pendiente de lectura CodeQL sobre SHA nuevo. |

### Alertas históricas Code Scanning observadas en main

El responsable compartió la vista de `main` con estas cuatro alertas abiertas. Las correcciones correspondientes están en este candidato, pero `main` no se modifica ni promueve en este ciclo. El conector no permite releer su estado actual; la misma ruta regular de PR decidirá su cierre al llegar a `main`.

| Alerta y regla | Archivo/línea en la vista compartida | Estado/alcance |
|---|---|---|
| #15 — Clear-text storage of sensitive information — High | `scripts/maintenance/taxonomy_roi_audit.py:86` | Observada abierta en `main`; corrección local conserva agregados y evita persistir detalle por fila. |
| #16 — Inefficient regular expression — High | `scripts/core/universal_harvester.py:316` | Observada abierta en `main`; ruta distinta del hallazgo del PR hasta promoción normal. |
| #17 — Incomplete URL substring sanitization — High | `scripts/shared/site_diagnostics.py:94` | Observada abierta en `main`; validación local compara hostname exacto/sufijo permitido, no subcadena. |
| #18 — Information exposure through a stack trace — Medium | `supabase/functions/send-lead-emails/index.ts:156` | Observada abierta en `main`; respuesta externa queda genérica y la regresión local cubre el handler. |
- La aprobación humana previa está `DISMISSED` y no cubre el SHA futuro. Tras los checks, el aprobador designado u otro colaborador autorizado —distinto de autora y publicadora— debe revisar y aprobar el SHA exacto vigente. No se autoaprueba ni se usa bypass.

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| H3REQ1 funcional | Conserva el alcance R8 seleccionado y los deltas de seguridad/administración del paquete. | Admin BFF, Edge, Worker/DO, Pages, migraciones y contratos escogidos. | Manifiesto y pruebas locales previas; no equivale a aceptación remota. |
| Seguridad CodeQL | Remedia cuatro diagnósticos del PR y cuatro alertas históricas de `main` en sus rutas respectivas. | Harvester, checker documental, harness de runtime, ROI, diagnóstico de host y handler de correo. | Revisión de seguridad del código en el paquete anterior y regresiones focales; CodeQL debe analizar un SHA nuevo. |
| Workflow y scope guard | Checkout de PR usa `head.sha`; la comparación protegida se ejecuta desde el helper corto sin ampliar rutas. | Checks Python, Static Build, PostgreSQL, PWI y workflow lint. | Actionlint, ShellCheck, guard, negativos y contratos pasan localmente en Docker. |
| Evidencia visual | Incluye solo derivados PNG neutros; excluye dos WEBM. | El PR no revela las imágenes originales. | Reconciliación R19; el PNG rechazado no se volvió a cargar. |
| B — configuración previa | Conserva el key ID Text confirmado por el responsable, HMAC existente y Worker v2 bajo excepción temporal. | Preview comparte ajustes con Certification; permanece fuera de pruebas de aceptación. | Confirmación humana separada de lectura del conector. B sigue incompleto hasta deployment/smoke compatible. |

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | `PENDIENTE` | Las pruebas locales anteriores cubren los contratos seleccionados; no hay aceptación Development. |
| Escalabilidad | `PENDIENTE` | Sin carga remota; límites de cuotas permanecen según el paquete D aprobado. |
| Seguridad | `PENDIENTE` | Scanner limpio y lint local; PWI no tiene fuente confiable y los checks del nuevo SHA no existen aún. |
| Mantenimiento | `PASS local documental` | 723/723 fuentes asignadas; 113/113 documentos activos alcanzables; 433/433 históricos catalogados y enlazados. |
| Calidad | `PENDIENTE` | Linters, guard y 17 contratos focales pasan; checks remotos y aprobación del SHA final pendientes. |
| Rendimiento | `PENDIENTE` | No se ha medido un deployment Development. |

## Transicion Transparente

| Fase | Alcance/resultado real | Evidencia / autorización cuando aplique |
|---|---|---|
| expand | A migration 3 se consumió en Free bajo su aprobación. | No repetir A ni modificar Pro. |
| compatibilidad | Worker/DO, binding, Edge v14 y Preview se identificaron; el responsable aceptó Worker v2 temporalmente hasta 2026-10-25 23:59 UTC. | B aprobado; su gate final de Preview/runtimes aún no pasa. Preview comparte configuración con Certification, preservada. |
| deploy | No hay deployment del nuevo SHA. | El push autorizado genera Preview automáticamente después de validación local/revisión; no se hará despliegue manual adicional. |
| contract | No iniciado; depende de estabilidad y aceptación. | No activar el pre-request antes del BFF compatible. |
| Rollback/recuperación | No ejercido para este SHA. | Conservar versión anterior; cualquier operación adicional protegida requiere paquete/permiso aplicable. |
| No degradacion funcional | No acreditada remotamente. | D01–D14 y regresión adicional siguen 0/14 y 0/11. |

## Evidencia Para Cliente

La [atestación sanitizada de Sprint 1](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md) enlaza la fuente privada sin adjuntarla. No se declara cierre contractual ni GO Development. D01–D14 y los 11 bloques de regresión adicional: 0/14 y 0/11 en remoto. El último administrador requiere escenario remoto aislado; Gmail y su configuración permanecen intactas.

## Validaciones

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS; regresiones y escaneo completo sin hallazgos. | Docker aislado sobre el candidato local. | `credential scan passed`; no demuestra el nuevo check remoto. Owner Codex. |
| Python tests | PASS; flujo exacto del job: 250 pruebas + 10 subtests y segunda invocación 41 pruebas; consumidores afectados 34 pruebas. | Docker aislado con lock de hashes. | No equivale al job remoto; el nuevo SHA debe ejecutar CI. |
| Python compile | PASS en todos los scripts del candidato. | Docker. | El job remoto del SHA anterior falló por checkout incompleto; el sucesor debe ejecutar su propio check. |
| PostgreSQL DB Change Gate | FAIL remoto en `074583d9` por falta de `tests/h3_admin_quota_postgrest.mjs`; PASS local en Docker con la dependencia restaurada y todo el fixture PG17/PostgREST. | GitHub Actions antiguo y Docker PG17/PostgREST desechable. | No hubo writes cloud. Nuevo SHA aún debe obtener su check remoto. Owner Codex. |
| ESLint | PASS en el SHA remoto anterior y en la validación local previa; frontend sin cambios en este delta. | GitHub Actions `074583d9` y Docker previo. | Nuevo SHA debe obtener check propio. |
| TypeScript | PASS en `074583d9`; frontend sin cambios en este delta. | GitHub Actions. | Nuevo SHA debe obtener check propio. |
| Static build | FAIL remoto en `074583d9` por input ausente; PASS local en Docker: las 11 invocaciones Node, `h2_web_mock_smoke.sh` y build exportado esperado. | GitHub Actions antiguo y fixture local Docker. | El build local no es Preview; nuevo SHA aún debe obtener su check remoto. |
| actionlint / ShellCheck | PASS local: actionlint 1.7.7 para tres workflows; ShellCheck 0.11.0 sobre siete scripts focales; `bash -n` PASS. | Contenedores Docker de herramientas, candidato de solo lectura. | El check remoto viejo sigue `in_progress` en actionlint; el nuevo SHA debe obtener resultado remoto. |
| UAT/runtime/integración | No ejecutado en Development. | Sin URL del candidato nuevo. | D01–D14: 0/14; regresión remota: 0/11. |
| security-audit / CI independiente efectivo | Run remoto 39228507399 seguía `in_progress` a las 10:57 UTC; Python, Static Build y PostgreSQL fallaron en el checkout anterior. Los gates locales del paquete exacto pasan en Docker. | SHA viejo `074583d9`; PWI 39228629396 falló por helper ausente en la base confiable. | PWI necesita la decisión JIT App descrita en el paquete preparado. No se elimina ni debilita el control. |
| CodeQL si aplica | PASS en el análisis remoto del SHA anterior `074583d9`; pendiente para el sucesor. | GitHub CodeQL. | No hay lectura de estado por alerta; no se declaran cerradas individualmente. |
| Cloudflare Pages / smoke preview | Preview anterior terminó success para `074583d9`; no hay Preview del nuevo SHA. | Cloudflare Preview, compartido con Certification. | No es Development; smoke/aceptación del sucesor no ejecutados. |
| Browser snapshot si aplica | No ejecutado para este candidato. | Sin host Development nuevo. | Requiere deployment identificado. |
| security-auditor | El bloque `independent_review` del manifiesto conserva estado, digest y veredicto de la revisión local exacta; debe ser PASS para publicar. | Revisión local read-only; distinta de la revisión remota del SHA. | La revisión humana de GitHub debe ser de persona distinta de autora/publicadora y del SHA final. |
| Documentación / trazabilidad / fuente cliente | 723/723 fuentes asignadas, 113/113 activos, 433/433 históricos y 13 catálogos; manifiesto: 1.179 rutas y 1.173 referencias. Self-test exacto y guard/manifiesto ya pasaron en Docker. | `--candidate-manifest`; el checkout de origen también pasa el modo global. | El pin final se recalcula tras esta actualización; revisar digest exacto antes de publicar. No se incorporó WIP. |

| `git diff --check` | PASS en el delta local R19; WARN al cotejar el paquete baseline→snapshot: 107 espacios finales y 18 líneas vacías al EOF. | Docker, snapshot exacto. | Avisos en documentos/evidencia histórica ya seleccionados; no reformatados porque no son un defecto funcional ni parte del delta R19. |

## Seguridad Y Datos

- [x] El scanner y sus regresiones pasan sobre el árbol candidato; no se guardan secretos ni PII en la evidencia nueva.
- [x] No se leyó ningún valor secreto; las confirmaciones humanas de Preview/Vault no se convierten en lectura del conector. Gmail conserva identidad, rol, contraseña, MFA, sesiones e historial.
- [ ] Checks del nuevo SHA y aprobación humana vigentes: pendientes; no se declara cero findings remoto ni GO.
- [x] Sin DDL/DML, reset de cuenta, invitación, workflow dispatch, cambio de secret, merge o deploy manual en esta actualización local.

## Alcance Y Limites

- [x] Candidato basado en PR 501 y `desarrollo`; el manifest fija el conjunto exacto, seis artefactos adicionales y exclusiones.
- [x] R8/R9/R12/R13 y sus evidencias, R14–R18, originales y ramas ajenas preservados.
- [x] WIP no manifestado, datos operativos, Certification, `main` y Production fuera del paquete.
- [ ] PWI, nuevos checks remotos y aprobación humana del SHA final pendientes. No se autoriza promoción por este body.

## Checklist Tecnico

- [x] Validaciones locales afectadas ejecutadas en Docker; resultados registrados como locales, no remotos.
- [ ] Publicar solo cuando el manifiesto registre PASS de la revisión del digest exacto y exista ruta PWI confiable; no se amplían carpetas de allowlist.
- [x] Seis pilares, criterio cliente y transición/rollback documentados con su estado real.
- [ ] PWI requiere proveedor de check confiable. Paquete JIT preparado en `/tmp/h3req1_pwi_external_check_app_jit_package_20261019.md`; ninguna App se instaló ni regla se cambió.
- [ ] Obtener resultados CI para el nuevo SHA y revisión humana independiente vigente. Solo entonces evaluar merge a `desarrollo`; no incluye Certification, `main` ni Production.
