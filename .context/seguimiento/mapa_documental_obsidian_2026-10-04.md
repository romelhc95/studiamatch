# Mapa documental histórico Obsidian — corte 2026-10-04

Esta nota conserva el mapa y los resultados de conectividad del corte 2026-10-04.
No es una navegación vigente ni una autoridad: comenzar por el [índice único](../indice.md)
y consultar el [estado operativo](../estado_del_proyecto.md). Los destinos y reglas que
siguen aplicando se mantienen en las fichas, el [protocolo constructor](../trazabilidad/protocolo_constructor.md)
y el [registro de fuentes](../trazabilidad/registro_fuentes_componentes.md).

## Auditoría y regla de amarre

En el análisis de aquel corte había 92 notas Markdown en `.context` (excluyendo configuración `.obsidian`),
52 alcanzables desde el índice de entonces, 40 no alcanzables y nueve destinos rotos. Estas
cifras son exclusivamente históricas; no describen el grafo actual. Alcanzable significaba
seguir enlaces internos Markdown/wiki desde el índice, sin contar menciones en código como
enlaces. No era el Context Graph histórico de permisos.

Este documento registra cómo se agregaron caminos a las notas que no eran alcanzables
en el corte histórico, con su motivo de conservación. El mapa ya no completa ni duplica
la navegación actual. Los documentos operativos H3 conservan enlaces semánticos entre
estado, hito, tarea, plan, evidencia y seguimiento; sus asignaciones vigentes están en el
registro canónico.

## Arquitectura y DB — referencia técnica, no garantía de ambiente remoto

- [Sistema DB Supabase](../sistema_db_supabase.md): contratos, drift y enlace al baseline.
- [Matriz adopción DB](../operaciones/matriz_adopcion_db.md): historia de adopción por ambiente.
- [H2 Development legacy compat](../operaciones/h2_development_legacy_compat_evidence.md): evidencia de compatibilidad H2 necesaria para cadena H3.
- [DDL H2 public view fields](../operaciones/ddl_authorizations/DDL-H2-PUBLIC-EFFECTIVE-VIEW-FIELDS-FIX-FREE.md): alcance autorizado histórico, no permiso nuevo.
- [DDL F10.8 cleansing provenance Pro](../operaciones/ddl_authorizations/DDL-F10_8_ATOMIC_CLEANSING_PROVENANCE_PRO.md): trazabilidad histórica de DDL, no reutilizar JIT.
- [DDL H2 Pro expand compat](../operaciones/ddl_authorizations/DDL-H2-PRO-EXPAND-COMPAT-20260827.md): baseline/transición histórica.
- [DDL H2 Pro legacy cohort RLS](../operaciones/ddl_authorizations/DDL-H2-PRO-ENABLE-LEGACY-COHORT-RLS-20260827.md): seguridad/cohorte histórica, no prueba de contract actual.

## Fuente cliente y matrices — aceptación sanitizada, no fuente privada

- [Evidencia H2 Sprint 1](../evidencias_cliente/sprint_1/evidencia_hito_002.md).
- [Evidencia H3 Sprint 1](../evidencias_cliente/sprint_1/evidencia_hito_003.md).
- [Evidencia H4 Sprint 1](../evidencias_cliente/sprint_1/evidencia_hito_004.md).
- [Evidencia H5 Sprint 1](../evidencias_cliente/sprint_1/evidencia_hito_005.md).
- [Evidencia H2 intake anterior](../evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md).
- [Matriz H2](../matrices/matriz_hito_002.md).
- [Matriz H3](../matrices/matriz_hito_003.md).
- [Matriz H4](../matrices/matriz_hito_004.md).
- [Matriz H5](../matrices/matriz_hito_005.md).

Se conservan porque trazan criterios/aceptación y fases distintas. En H3 el corte
actual está en estado/plan/traspaso; porcentajes o PASS de estas matrices no son GO
del nuevo candidato. H4/H5 permanecen dependientes de sus gates; enlazarlos no los activa.

## H3 — implementación y evidencia histórica contextualizadas

- [Implementation report H3](../hitos/h3req1_implementation_report.md): corte anterior a remediaciones BFF/gateway.
- [Remediation plan 2026-09-24](../evidencia/planes_historicos/h3req1_remediation_plan_2026-09-24.md): decisiones previas; archivado como historia y reemplazado por el plan único de cierre.
- [JIT Auth/Access/MFA](../operaciones/jit_supabase_auth_cloudflare_access_mfa.md): propuesta/operaciones históricas, permisos no persistentes.
- [Evidencia JIT A Free/Auth](../operaciones/evidencia_jit_a_supabase_auth_free.md): resultados históricos acotados.
- [Evidencia JIT B Access/DNS](../operaciones/evidencia_jit_b_cloudflare_access_dns.md): resultados/perímetro históricos acotados.
- [Waiver static export](../waivers/waiver_h3_static_export.md): waiver supersedido; no excepción activa ni permiso de saltar build.
- [Remediation final 2026-09-23](../evidencia/h3req1_remediation_final_2026-09-23.md).
- [Read-only remote 2026-09-24](../evidencia/h3_remote_validation_readonly_2026-09-24.md).
- [UAT matrix local 2026-09-23](../evidencia/h3req1_uat_matrix_local_2026-09-23.md).
- [Remediation report 2026-09-23](../evidencia/h3req1_remediation_report_2026-09-23.md).
- [Remote validation progress](../evidencia/H3REQ1_REMOTE_VALIDATION_PROGRESS.md).
- [Read-only remote cycle 2](../evidencia/h3req1_remote_validation_readonly_2026-09-24_cycle2.md).
- [Development validation 2026-09-24](../evidencia/h3req1_development_validation_2026-09-24.md).
- [Development cycle 2026-09-24](../evidencia/h3req1_development_cycle_2026-09-24.md).
- [Pro/Free/local matrix 2026-08-30](../evidencia/h3_pro_free_local_matrix_2026-08-30.md).
- [Migration classification 2026-08-30](../evidencia/h3_migration_classification_2026-08-30.md).
- [Remediation baseline 2026-09-23](../evidencia/h3req1_remediation_baseline_2026-09-23.md).
- [Invitation mock UAT 2026-09-23](../evidencia/h3-invitation-flow/evidencia_h3_uat_mock_2026-09-23.md).
- [Invitation remediation 2026-09-23](../evidencia/h3-invitation-flow/evidencia_h3_invitation_flow_remediation_local_2026-09-23.md).
- [Invitation frontend/Auth 2026-09-22](../evidencia/h3-invitation-flow/evidencia_h3_invitation_flow_frontend_auth_local_2026-09-22.md).

Estos reportes se conectan para conservar procedencia, fallos y decisiones. No
normalizar sus resultados históricos como estado vigente ni reutilizar su JIT.
La evidencia de esta ruta continúa en [estado vivo](../estado_del_proyecto.md),
[ruta EXEC-01–06 histórica a GO PR/Development](../evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md),
[propuesta JIT S1 Pages/workerd](../operaciones/manifiesto_jit_h3_close03_startup_smoke_2026-10-06_s1.md),
[preflight F1 snapshot](../evidencia/h3req1_c03_source_snapshot_f1_static_review_2026-10-07.md),
[reconciliación F1 pre-start](../evidencia/h3req1_c03_source_snapshot_f1_prestart_failure_reconciliation_2026-10-07.md),
[atestación aprobación F1](../evidencia/h3req1_c03_source_snapshot_f1_approval_2026-10-07.md),
[revisión estática F2](../evidencia/h3req1_c03_source_snapshot_f2_static_review_2026-10-07.md),
[propuesta JIT F2 metadata](../operaciones/manifiesto_jit_h3_close03_source_snapshot_f1_metadata_read_2026-10-07_f2.md),
[propuesta JIT F1 snapshot](../operaciones/manifiesto_jit_h3_close03_source_snapshot_2026-10-07_f1.md),
[preflight integrado C03](../evidencia/h3req1_h3_close03_integrated_preflight_2026-10-05.md),
[propuesta JIT v3 safe-resume](../operaciones/manifiesto_jit_h3_close03_safe_resume_pg17_2026-10-05_v3.md) y
[candidato 2026-10-04](../evidencia/h3req1_development_candidate_cycle_2026-10-04.md).

## Gobernanza release anterior — archivada, sin autoridad ejecutiva

- [RF01 release target](../operaciones/rf01_release_promotion_contract_target.md).
- [RF01 hotfix target](../operaciones/rf01_hotfix_reconciliation_contract_target.md).
- [ADR-0028 target governance](../decisiones/ADR-0028_target_release_governance.md).
- [RF01 build report](rf01_build_report.md).

Se preservan para explicar el cambio de gobernanza. Si contradicen el flujo protegido,
AGENTS/estado/plan vigente prevalecen. No revivir work packages, grants persistentes,
promotion gates o automatismos por haber conectado estas notas al grafo.

## Referencias retiradas y evidencia fuera del worktree

`ADR-0027_work_packages_y_convergencia.md` no existe en este candidato. Sus antiguos
enlaces se reemplazan por explicación de retiro y enlace al estado. No crear ADR
ficticio ni modificar aceptación cliente: cambia navegación/procedencia, no criterios.
`arquitectura_pipeline.md` tampoco existe; la referencia técnica disponible es
[AGENTS — arquitectura del pipeline](../../AGENTS.md#arquitectura-del-pipeline-4-estaciones--auditoría)
y [Sistema DB](../sistema_db_supabase.md). No crear una autoridad paralela para rellenar el hueco.

Las carpetas visuales r8/r9/r10/r11 no se copiaron al candidato: siguen en
`/home/romel/src/studiamatch/.context/evidencia/`, comprobadas presentes en lectura.
La [nota BFF](../evidencia/h3req1_bff_local_cycle_2026-10-02.md) enlaza ahora a la ubicación
original con ruta relativa entre checkouts. Son assets históricos fuera del vault,
NO notas aisladas de este grafo, NO evidencia del candidato actual. Esos enlaces
dependen de conservar la estructura local; para PR/traspaso a otra máquina inventariar
respaldo/hash y ubicación recuperable, no prometer portabilidad inexistente ni copiar
144 capturas por corrida sin necesidad. Artefactos en contenedores/temp también
requieren manifiesto recuperable antes de cualquier cleanup autorizado.

Excluidos de aquel grafo: configuración `.obsidian`, secretos `.env*`, fuente privada
cliente, código/SQL y assets no Markdown. La regla vigente es enlazar una nota nueva
desde su ficha dueña y desde el índice principal cuando corresponda; este mapa histórico
no es un consumidor de mantenimiento.

## Criterios de validación del grafo

Resultado de la revisión posterior a los enlaces: **94/94 notas alcanzables desde
el índice, 0 sin enlace entrante y 0 destinos locales rotos**. Los cuatro enlaces a
assets del checkout original se validaron como carpetas externas presentes, no como
notas del vault. La prueba de formato en Docker de 14 documentos terminó PASS;
detectó antes un fence faltante en un prompt histórico de seguimiento, que se corrigió
sin alterar su contenido. `git diff --check` PASS. No se validaron URLs remotas,
anchors ni la vista renderizada del grafo Obsidian. El alcance es el vault `.context`
del worktree sincronizado; no se reescribió el vault del checkout original.

- Enumerar todos los `.md` de `.context` salvo configuración `.obsidian`.
- Resolver Markdown relativos y wikilinks únicos, excluir URL externas/anchors puros
  y enlaces de ejemplo dentro de fences; validar destinos de assets por separado.
- Recorrer enlaces desde el índice principal vigente (`.context/indice.md`): exigir todas las notas alcanzables y ningún
  nodo sin entrada, salvo raíz si se explica (este mapa también enlaza a la raíz).
- No afirmar que se validó anchors, URLs externas o render visual de Obsidian por
  un chequeo de archivos; registrar límites del método y repetir tras nuevos documentos.
