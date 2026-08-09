# PLAN-H1-CORTE-SFE-001 - Corte Seguridad Funcionalidad Estabilidad Hito 1

> La adenda CA1-only aprobada conserva este corte como evidencia local CA2 y
> evita promoverlo parcialmente. Produccion mantiene su comportamiento actual
> durante Hito 1; cualquier cambio de frontend, Edge o DB leads/email pasa a
> Hito 2 solo despues de aprobacion cliente y gates propios.

Estado documental: `SUPERSEDED_FOR_HITO_1_BY_ADR_0006`; [ADR-0005](../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md) permanece como decision historica de seguridad y no autoriza aplicacion CA2/Free/Pro.

## Estado Y Autoridad

El corte pertenecio historicamente a F9.7 y a [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md). No cierra F9, Hito 1, F10 ni F11. La autoridad de estado vivo sigue en [Estado del proyecto](../estado_del_proyecto.md) y la tarea canonica.

## Objetivo Del Corte

Crear un corte local de seguridad, funcionalidad y estabilidad que retire la captura publica de leads y el email automatico del perfil habilitado, conserve el producto publico y preserve el Golden Pipeline.

## Decisiones Humanas Fijadas

Antes de la adenda, Hito 1 conservaba tres criterios, producto publico, harvester completo y ruta a produccion. El alcance vigente de Hito 1 es CA1-only; leads/email quedan diferidos y solo pueden reactivarse con nuevo ciclo formal. Los roles `anon`, `authenticated`, `authenticator` y `service_role` quedaron sin acceso a `leads`/`email_log` en el package local historico; las filas legacy se preservan bajo autoridad owner. El cierre se organizo mediante el plan definitivo de work packages, sin crear subfases ni subtareas.

## Semantica De Estados

`lead_email_architecture=DEFERRED_NO_IMPLEMENTATION`, `public_lead_capture=LOCAL_CODE_REMOVED_REMOTE_UNKNOWN`, `email_egress=LOCAL_TOMBSTONE_REMOTE_UNKNOWN`, `security_hold=LOCAL_CANDIDATE_BLOCKED`, `Free=UNCHANGED_NOT_ATTESTED` y `Pro=UNCHANGED_NOT_ATTESTED` describen el corte local, no un estado remoto.

## Baseline Git Y Disposicion De Artifacts

F6-F8 permanecen como baseline contractual. Los artifacts F9.5 permanecen `HISTORICAL_NON_PROMOTABLE`. El manifest v3 y sus seis migrations de PR #257 permanecen byte-identicos. V3 no se autoriza por si solo porque permite `INSERT` publico limitado en `leads`; solo podra usarse como dependencia previa de un hold sucesor. La Edge Function tombstone en Git no demuestra deployment remoto.

## Perimetro Funcional

El frontend sin leads es el unico perfil web soportado por el corte. Se preservan catalogo, busqueda, filtros, detalle, comparacion, soporte estatico, privacidad y terminos.

## Perimetro De Seguridad

El corte retira transporte publico de PII en frontend, deja la Edge Function como `410 Gone` local y define un hold DB-as-Code que revoca privilegios publicos sobre `leads` y `email_log` cuando un gate futuro lo autorice.

El hold cierra rutas ordinarias de aplicacion, incluido `service_role`, y hace fallar el verifier ante grants, policies, views, routines, publications, triggers, rules, membresias o ACL drift. Un owner `postgres` o superuser sigue siendo autoridad administrativa fuera del threat model y no puede neutralizarse absolutamente mediante una migration; SQL dinamico arbitrariamente ofuscado tampoco puede probarse por completo con inspeccion estatica.

## Perimetro De Estabilidad

No modifica schedules, protected paths, tablas del pipeline, RPCs de estaciones, gates institucionales, timeouts, concurrencia ni credenciales de workflows FG.

## Preservacion Completa Del Harvester

Se preservan `universal_harvester.py`, `master_orchestrator.py`, sitemap discovery, crawl/BFS, catalog-link discovery, HTTP extraction, browser/Playwright cuando aplique, persistencia `discovered/pending` en `staging_raw`, deduplicacion, hashing, `allowed_url_patterns`, `exclusion_patterns`, `discovery_enabled`, `pipeline_enabled`, fallback `pipeline_ready`, `production_enabled`, circuit breaker, cooldown, freshness, timeouts y persistencia parcial.

## Separacion Respecto De Leads Y Email

Leads/email no son una estacion del Golden Pipeline. Su arquitectura completa queda en [BK-F9.5-05](../backlog_tareas/req_est_001_sprint_1/backlog_seguridad_leads_email.md).

## Bloqueo Publico Permanente

La captura publica no puede reactivarse por flag, grant manual ni edicion de ledger. Cualquier reactivacion exige requerimiento aceptado y migration forward-only propia.

## Package Historico De Security Hold

El package `F9.7-LEADS-EMAIL-SECURITY-HOLD-20260729` es separado, forward-only, de una entrada, `application_authorized=false`, con Free/Pro bloqueados y se conserva byte-identico. Para la ruta futura queda `SUPERSEDED_NON_PROMOTABLE_FOR_FUTURE_ROUTE`: no es hold terminal aplicable porque el estado final sucesor debe eliminar `public.exec_sql(text)` y exigir executor privado no expuesto por Data API.

## PR-O Sucesor Con Executor Privado

[PR-O F9.7 executor privado](./pr_o_f9_7_successor_private_executor.md) queda certificado localmente como `CERTIFIED_LOCAL_PR_O_SUCCESSOR`. Mantiene `application_authorized=false`, `capabilities=[]`, Pro/backfill/H-00/aplicaciones parciales rechazados, boundaries permitidos `0`, `3`, `4`, `5`, `6` y `7`, cero capacidad remota ejecutable, approvals single-use y secuencia atomica `pending v3 -> postcondiciones v3 -> ledger v3 -> hold sucesor -> verificador terminal -> ledger hold -> verificacion final -> commit unico`.

## Gate Futuro De Contencion Free

La ruta historica Free requeria `PREFLIGHT_READ_ONLY_FREE` separado, binding privado, snapshot read-only fresco, backup/restore `RESTORE_PROVEN`, pausa/drain de writers `HELD`, boundary permitido por PR-O, evidencia sanitizada del target, estado Edge valido y aprobacion humana independiente antes de aplicar v3 + hold sucesor. Tras la rebaseline queda `SUPERSEDED_FOR_HITO_1`.

## Gate Futuro De Contencion Pro

Pro repite el proceso con cohorte, binding, backup/restore y evidencia propios. Nunca copia datos Free hacia Pro.

## Puente Minimo De Publication Status Historico

En la ruta historica sustituida, F9.8/F9.9 permanecian limitadas a cursos legacy anteriores a cutoff aprobado, `is_active=true`, `is_verified=true`, institucion `production_enabled=true`, `publication_status=borrador`, `manual_updated_at IS NULL` y unico cambio `publication_status -> publicado`. Tras la rebaseline, este puente queda `SUPERSEDED_FOR_HITO_1` y no autoriza backfill, Free ni Pro.

## Ruta Restante A Produccion

Merge humano del corte, replay local post-merge, definicion local de PR-O v1, supersesion local por PR-O executor privado, implementacion local `GO_WP_LOCAL` y certificacion local `CERTIFIED_LOCAL_PR_O_SUCCESSOR` quedan como historia local. `PREFLIGHT_READ_ONLY_FREE`, `GO_FOR_FREE`, gates Free, puente editorial y backfill quedan `SUPERSEDED_FOR_HITO_1`; la ruta vigente usa F9.8 candidate local CA1-only, F9.9 Certification/canary/QA, F9.10 certificacion final/`USER_PERSONAL_UAT`/readiness, F10 Production y F11 cierre final.

## Plan De Cierre Definitivo

PLAN-F9.7-CIERRE-001 divide el trabajo en `WP-F9.7-01` a `WP-F9.7-06`: gobierno, DB, frontend, release gates, candidate inmutable y auditoria/PR. Cada WP tiene alcance, owner de archivos, matriz enfocada, checkpoint y GO propio. Solo el ultimo WP puede producir `GO_FOR_LOCAL_PR`; los gates Free permanecen separados.

## Evidencia De Salida

La salida del corte exige validaciones Docker, PostgreSQL 17, frontend publico, Context Graph, actionlint, EOL, hashes v3, diff cero de protected paths, secret scan y auditorias `GO_FOR_LOCAL_PR` sobre un mismo tree. Los auditores aplican los invariantes y la clasificacion congelados en PLAN-F9.7-CIERRE-001; remote unknown y limites aceptados no amplian por si solos el alcance local.

## Stop Conditions

Detener ante drift de F9.7, cambios en los seis SQL v3, ruta frontend para habilitar leads, egress Edge, diff en protected paths, necesidad de Free/Pro, lectura `.env*`, secreto/PII, falla de tests, churn EOL o ampliacion del backfill.

## No Autorizaciones

No autoriza Supabase Free/Pro, Supabase MCP, DDL/DML remoto, deploy Edge/Cloudflare, backup/restore, pausa real, drenaje `pg_net`, backfill, dispatch, merge automatico ni push directo a ramas permanentes.

## Referencias

- [ADR-0005](../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md)
- Cierre definitivo F9.7
- Certificacion Hito 1 F9
- Remediacion local del trigger F9.7
- [Contrato PR-O F9.7 v1 superseded](./pr_o_f9_7_v3_hold.md)
- [Contrato PR-O F9.7 executor privado](./pr_o_f9_7_successor_private_executor.md)
- [Backlog leads/email](../backlog_tareas/req_est_001_sprint_1/backlog_seguridad_leads_email.md)
- [Arquitectura del pipeline](../arquitectura_pipeline.md)
- Estructura frontend
