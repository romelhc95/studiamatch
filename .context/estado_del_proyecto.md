# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-08-01-F9.7-ADENDA-DRAFT-CA1-ONLY`.

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases. El estado vivo de la tarea activa pertenece a la propia tarea.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `F0` | Preservacion | `COMPLETED` | Preservacion verificada. |
| `F1` | Main a certificacion | `COMPLETED` | Convergencia verificada. |
| `F2` | Certificacion a desarrollo | `COMPLETED` | Convergencia verificada. |
| `F3` | Higiene remota | `COMPLETED` | Higiene terminada. |
| `F4` | Bootstrap local | `COMPLETED` | Entorno local verificado. |
| `F5` | Obsidian minimo | `COMPLETED` | Gobierno documental, PR #221 y `SRC-REQ-001` reconciliada. |
| `F6` | Reconciliacion DB-as-Code | `COMPLETED` | Base funcional contractual Hito 1, forward-only y validada localmente; ningun cambio remoto aplicado. |
| `F7` | G1b minimo | `COMPLETED` | Base funcional contractual Hito 1; gates y postcondiciones locales validados. |
| `F8` | Hito 1 funcional | `COMPLETED` | Base funcional contractual Hito 1 y PostgreSQL 17 validados; sin aplicacion DB remota. |
| `F9` | Certificacion Hito 1 en Free | `IN_PROGRESS` | Corte local F9.7 fusionado; PR #263 remediado en `778267948fc3461987a41dc9184b151c9ff19243` / tree `4e6609926ea6f4a3342cac43e71307fd5cd24aba`; PR-O v1 y hold actual quedan `SUPERSEDED_NON_PROMOTABLE`; sucesor con executor privado certificado localmente como `CERTIFIED_LOCAL_PR_O_SUCCESSOR` en `771b8b1366e302eae52e4263577e0f6967679d7b` / tree `99f315c6820966e94213665df43cd21f9f4ef730`; Free sigue sin certificar. |
| `F10` | Pro y produccion | `PENDING` | Bloqueada hasta que F9 termine en `free_certified`; incluye canary, `main`, smoke y observacion. |
| `F11` | Cierre final | `PENDING` | Bloqueada hasta completar produccion observada; incluye limpieza fisica autorizada de artifacts historicos. |

## Subfases F9

| ID | Estado | Identidad vigente |
|---|---|---|
| `F9.1` | `COMPLETED` | Precertificacion local; alias historico `FASE-09`, PR #231/#232 y cierre #233 |
| `F9.2` | `COMPLETED` | Contrato local de promocion; alias historico `FASE-10`, PR #235/#236 |
| `F9.3` | `COMPLETED` | Freeze local; PR #238, remediacion CRLF #239 y replay post-merge Docker sobre checkout Linux limpio |
| `F9.4` | `COMPLETED` | Reconciliacion contractual local; plan simplificado adoptado, definicion remota sustituida y antecedente temporal retirado |
| `F9.5` | `COMPLETED_WITH_KNOWN_FINDINGS` | Cierre contractual/documental; artifacts de PR #245 y PR #247 son `HISTORICAL_NON_PROMOTABLE`; no queda lectura Free pendiente |
| `F9.6` | `COMPLETED` | `H00_ALREADY_REMEDIATED_NO_DML`: cohorte con PII directa remediada, conservada como pseudonimizada; Gate B DELETE `SUPERSEDED_NON_AUTHORIZABLE`; Pro prohibido |
| `F9.7` | `IN_PROGRESS` | `security_cutoff_local_candidate` local cerrado y fusionado por PR #258; PR #261 fue mergeado por humano en `ee0e320d55b70dedd72c5a09429ed84a34bf7543`; PR #262 fue mergeado por humano en `c0b6c5efaaaca25f7946e114cc53f63f3a5daa66` / tree `3e5537f01ebf4bec94ada99b274415fc13a2f039`; PR #263 fue remediado en `778267948fc3461987a41dc9184b151c9ff19243` / tree `4e6609926ea6f4a3342cac43e71307fd5cd24aba`; [PR-O v1](operaciones/pr_o_f9_7_v3_hold.md) y hold actual quedan `SUPERSEDED_NON_PROMOTABLE`; [PR-O executor privado](operaciones/pr_o_f9_7_successor_private_executor.md) queda `CERTIFIED_LOCAL_PR_O_SUCCESSOR` en `771b8b1366e302eae52e4263577e0f6967679d7b` / tree `99f315c6820966e94213665df43cd21f9f4ef730`, `application_authorized=false`, `capabilities=[]`, sin capacidad remota ejecutable; F9.7 permanece `IN_PROGRESS` hasta `GO_F9.7_COMPLETE` en Free; Free/Pro `UNCHANGED_NOT_ATTESTED`, `GO_FOR_FREE` bloqueado, Supabase previews skipped y sin Cloudflare manual |
| `F9.8` a `F9.10` | `PENDING` | Plan/ejecucion backfill/T03 y certificacion/T04; gates separados; `USER_PERSONAL_UAT` es hold operativo de F9.10 despues de validaciones tecnicas Free y antes de T04, writer resume o cualquier PR/merge `desarrollo -> certificacion` |

Post-merge preflight binding: `desarrollo@416ee19e3eea2cd61d4ae42d1455ff579c60f262` / tree `f6173cf7d8fcd2a0ca95cfaf38e9e2914501d85c` (head `82fdfcf7aacb7b9ce9c1793189b6b88303c1f474`).

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase activa: F9.7; [ADR-0005](decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md), [PLAN-H1-CORTE-SFE-001](operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md), [PLAN-F9.7-CIERRE-001](operaciones/cierre_definitivo_f9_7.md), [PR-O v1 superseded](operaciones/pr_o_f9_7_v3_hold.md) y [PR-O executor privado](operaciones/pr_o_f9_7_successor_private_executor.md) fijan el corte local y la definicion operacional sucesora: PR #258 cerro `WP-F9.7-04..06`, PR #259 reconcilio el replay, PR #260 documento post-merge, PR #261 fue mergeado por humano en `desarrollo@ee0e320d55b70dedd72c5a09429ed84a34bf7543` / tree `218bfcc7e99bdef3569fc730bba21228dee53540`, PR #262 fue mergeado por humano en `desarrollo@c0b6c5efaaaca25f7946e114cc53f63f3a5daa66` / tree `3e5537f01ebf4bec94ada99b274415fc13a2f039`, PR #263 quedo en `778267948fc3461987a41dc9184b151c9ff19243` / tree `4e6609926ea6f4a3342cac43e71307fd5cd24aba`, y el PR-O executor privado fue certificado localmente en `771b8b1366e302eae52e4263577e0f6967679d7b` / tree `99f315c6820966e94213665df43cd21f9f4ef730`.
- Subfase autorizada: `CERTIFICACION_LOCAL_PR_O_SUCCESSOR` queda `CONSUMED_PASS` como `CERTIFIED_LOCAL_PR_O_SUCCESSOR`; no autoriza preflight remoto, Supabase Free/Pro, DDL/DML remoto en Free/Pro, backup/restore, writers, backfill, Edge, Cloudflare manual, aplicacion PR-O, push directo a ramas permanentes, merge automatico ni `GO_FOR_FREE`.
- Autorizacion documental anterior: `DOCUMENTAR_ADENDA_Y_PLAN_CINCO_HITOS_REQ_EST_001`, completada y fusionada por PR #267 en `0dfa5dbc9c23aa0eaa487a9e113580dc0041f485`.
- Gate decimal recibido para este paquete: `Ejecuta las tareas pendientes de la Fase F9.7`; su alcance especifico `DOCUMENTAR_ARQUITECTURA_Y_MATRICES_TEST_CA_SPRINT1` crea vistas derivadas y matrices `PLANNED`, sin codigo, DB ni operaciones remotas. El token de alcance no sustituye el gate decimal ni autoriza trabajo posterior.
- Siguiente accion: validar y fusionar el PR documental independiente de arquitectura/pruebas, y obtener aprobacion cliente de la adenda. Mientras falte esa aprobacion, `PREFLIGHT_READ_ONLY_FREE` no se reanuda, el mapa CA1-only no entra en vigor y F9.7 sigue `IN_PROGRESS`.

## Alcance Inmediato

La [macrofase F9](operaciones/certificacion_hito1_f9.md) conserva su historia y no ejecuta operaciones remotas. La adenda propuesta plantea separar el cierre CA1 productivo del alcance CA2 pendiente, pero no cambia el contrato hasta aprobacion cliente. F6-F8, v3 y los artifacts F9.7 permanecen inmutables; Free/Pro siguen `UNCHANGED_NOT_ATTESTED`; `GO_FOR_FREE` continua bloqueado. Los artifacts terminales no comprometidos son WIP CA2 no promocionable y no forman parte de este PR documental. Hitos 2 a 5 estan documentados como `PENDING`, sin subfase ejecutable.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
