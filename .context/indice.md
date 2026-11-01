# StudIAMatch — índice de transferencia

> Corte H3REQ1 2026-11-01, posterior a PR #521: Desarrollo `64c23fd8a9694f50a2728399bf8e35771bf56fad`, Certification `605a6ecca29e20ade8cac3874d380758d18e6a11`, main `70d0f4fee885be0f6780e5d14f466b2a6c897961`. PR #521 está integrado y el deployment normal de Certification `ac707175-75a9-4c5a-9c6b-0786a6a0d517` terminó SUCCESS. DB Sync run #91 (`41338753002`) verificó H2 `h2-expand-compat` para C=605a6ecc: dispatch real `verify`, Apply NO-OP y migraciones a Pro SKIPPED. El JSON canónico es idéntico al miembro autenticado del artefacto `13096761150` (SHA-256 `563de170bbce697408413a212f39d8592238749856a0c6652e0bea4ce8051195`; ZIP `f7e3ac3a735013f2b3959b668b72913526e51c24dde063ee4c714613d69a5895`). `operation=apply` es la etiqueta histórica del JSON, no una aplicación ejecutada. H3 no está instalado en Pro. Se reutilizan E1–E6 local 6/6, Development R1–R4 4/4 y smoke Certification 1/1, sin repetirlos. El [checkpoint de scope y evidencia H2](evidencia/h3req1_protected_path_scope_fix_2026-10-31.md) conserva run 89 como historia y añade run 91. No autoriza commit, PR, SQL, dispatch, configuración, merge ni deploy.

Esta es la única entrada principal de Obsidian. El [estado del proyecto](estado_del_proyecto.md) es la única autoridad operativa para el corte vigente, resultados, pendientes y siguiente paso. Las reglas de ejecución están en [AGENTS.md](../AGENTS.md).

## Recorrido por el sistema

| Orden | Dominio | Alcance |
|---:|---|---|
| 1 | [Arquitectura](arquitectura.md) | Límites, flujos, runtimes, fallos y recuperación. |
| 2 | [Tecnologías](tecnologias.md) | Dependencias, versiones acreditadas, locks y excepciones. |
| 3 | [Frontend](frontend.md) | Rutas públicas/Admin, estado, filtros, edición, publicación y export. |
| 4 | [Backend](backend.md) | BFF, RPC, Edge Functions, Workers, cuotas, auth y errores HTTP. |
| 5 | [Base de datos](database.md) | Diccionario, tablas, vistas, funciones, grants, RLS, migrations y límites del baseline. |
| 6 | [Pipeline](componentes/pipeline.md) | Discovery, estaciones, estados, deduplicación, writers y schedules. |
| 7 | [Seguridad](seguridad.md) | Fronteras de confianza, credenciales, cookies, permisos, scanner y riesgos. |
| 8 | [Pruebas](pruebas.md) | Suite, criterios, entornos, resultados fechados y límites probatorios. |
| 9 | [Operación](operacion.md) | Ambientes, configuración por nombres, Docker, recuperación y observabilidad. |
| 10 | [CI/CD](ci_cd.md) | Workflows locales, triggers definidos, permisos y transición por ambiente. |

## Módulos y responsabilidades

| Módulo | Ficha canónica | Dominio complementario |
|---|---|---|
| Frontend público | [Web público](componentes/web_publico.md) | [Frontend](frontend.md) |
| Portal Admin | [Portal Admin](componentes/admin_portal.md) | [Frontend](frontend.md) |
| Presentación compartida | [Primitives, renderer y utilidad `cn`](componentes/presentacion_web_compartida.md) | [Frontend](frontend.md#componentes-principales) |
| Transporte Supabase | [API key, sesión y gateway RPC](componentes/supabase_transport.md) | [Backend](backend.md#bff-y-contrato-de-error), [Seguridad](seguridad.md#modelo-de-confianza-y-permisos) |
| BFF, gateway, Edge y cuota | [Runtime Admin](componentes/admin_runtime.md) | [Backend](backend.md) |
| SQL y migrations | [Migrations de base de datos](componentes/database_migrations.md) | [Base de datos](database.md) |
| Pipeline y datos | [Pipeline](componentes/pipeline.md), [integración datos/pipeline](componentes/datos_pipeline.md) | [Base de datos](database.md) |
| Canarios | [Canarios](componentes/canarios.md) | [Operación](operacion.md) |
| Mantenimiento | [Herramientas de mantenimiento](componentes/mantenimiento.md) | [Operación](operacion.md) |
| Utilidades y ROI | [Utilidades compartidas](componentes/utilidades_compartidas.md) | [Backend](backend.md), [Base de datos](database.md) |
| Infraestructura y release | [Infra/release](componentes/infra_release.md) | [Tecnologías](tecnologias.md), [CI/CD](ci_cd.md) |
| Seguridad y tooling | [Seguridad/tooling](componentes/seguridad_tooling.md) | [Seguridad](seguridad.md) |
| Suites y evidencia | [Pruebas/evidencia](componentes/pruebas_evidencia.md) | [Pruebas](pruebas.md) |
| Código y documentos legacy | [Legacy/deprecated](componentes/legacy.md) | [Historia preservada](#historia-y-evidencia) |

Las fichas explican el módulo; el [registro verificable de fuentes](trazabilidad/registro_fuentes_componentes.md) es la fuente canónica de asignaciones path→componente→documento/anchor y relaciones por grupo. No hay un índice duplicado de componentes.

## Requerimientos, hitos y decisiones

- [Requerimientos sanitizados](requerimientos/README.md) enlaza criterios, atestación de aceptación y evidencias sin exponer el documento privado del cliente.
- [Hitos](hitos/README.md) enlaza estado, dependencias y resultado de cada hito.
- [Decisiones](decisiones/README.md) conserva decisiones y su vigencia demostrable.
- El [protocolo de mantenimiento y nomenclatura](trazabilidad/protocolo_constructor.md) define cómo actualizar registro, módulos y consumidores al crear, mover, eliminar o cambiar contratos; no crea otra autoridad operativa.
- [Backlog del Sprint 1](backlog_tareas/req_est_001_sprint_1/_index.md) es navegación subordinada para tareas; no crea otra autoridad operativa.
- El [plan vinculante del nuevo pedido](operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md) conserva su alcance aprobado; el estado operativo indica qué puede ejecutarse.
- El [estándar de prompts retroalimentados](operaciones/estandar_prompts_retroalimentados.md) describe el formato de trabajo; no crea un plan ni una autoridad operativa paralela.

## Recorridos para cambios comunes

Sigue los [recorridos de transferencia](transferencia.md) para cambiar: una regla de edición Admin, un filtro público, un campo de datos, discovery/procesamiento, invitaciones/cuota/sesión o un workflow/herramienta. Cada recorrido enlaza módulo, fuentes/símbolos, consumidores, datos, permisos y pruebas que revisar.

## Historia y evidencia

- [Contrato editorial H3REQ1 — cortes históricos de CA4 y preflight](evidencia/h3req1_editorial_contract_2026-10-28.md) conserva las aceptaciones E1–E6 local, R1–R4 Development y smoke Certification, además de los resultados y límites de cada corte. La actualidad de ramas, despliegues, H2 Pro y gates se lee en el estado operativo vigente.
- [Checkpoint de scope y evidencia H2 Pro — run 89 histórico y run 91 vigente](evidencia/h3req1_protected_path_scope_fix_2026-10-31.md) conserva la procedencia, digests, diferencia entre etiqueta histórica `operation=apply` y dispatch real `verify` con Apply NO-OP, además del paquete local en preparación. El run 91 acredita H2 `h2-expand-compat` para C; no demuestra H3 instalado en Pro.
- [D04: distinguir denegación de rol de fallo RPC](evidencia/h3req1_d04_onboarding_forbidden_2026-10-25.md) conserva el diagnóstico acotado del 502 histórico, el cambio local de SQLSTATE/BFF, pruebas focales Docker y los límites de SQL/runtime sin ejecutar.
- [Ciclo de aceptación local del candidato de duración compuesta y filtros móviles](evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-acceptance-cycle-2026-10-24.md) conserva R11 y añade R12: H3-UAT-058/H3-CA4.11 y H3-UAT-059/H3-CA4.9 pasan juntos en 6/6 viewports; 058 incluye la comprobación de footer/filtros a 320 px y 059 pasa 39/39 aserciones por viewport. Son resultados locales sintéticos; Preview, integración, deployment y aceptación remota siguen pendientes.
- [Revisión del candidato de correcciones públicas y Admin R21](evidencia/h3req1_public_admin_corrections_2026-10-26/candidate-pr-body-2026-10-26.md) agrupa el delta exacto, sus consumidores, validaciones Docker y escenarios remotos que deben renovarse. No autoriza publicación; no incorpora el WIP Admin/MFA/FG3 ajeno.
- [Registro verificable de fuentes y componentes](trazabilidad/registro_fuentes_componentes.md) muestra las asignaciones generadas desde el JSON canónico; los resultados y pendientes del corte solo viven en el estado operativo.
- [Consolidación de trazabilidad R11](evidencia/h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md) registra los mapas sustituidos, destinos, consumidores y backups verificados.
- [Mapa histórico de navegación 2026-10-04](seguimiento/mapa_documental_obsidian_2026-10-04.md) conserva los conteos y enlaces de ese corte; no es una entrada ni una autoridad vigente.
- [Changelog](changelog.md) resume cambios sustanciales con fecha y clasificación.
- [Checkpoint de reconciliación R19](evidencia/h3req1_g10_remote_preparation_2026-10-18_r19.md), [paquete Development](evidencia/h3req1_development_integration_package_2026-10-18_r19.md), [checks](evidencia/h3req1_remote_preparation_checks_2026-10-18_r19.txt), [revisión independiente](evidencia/h3req1_remote_preparation_independent_review_2026-10-18_r19.txt), [manifiesto reconciliado](evidencia/h3req1_pr_scope_manifest_2026-10-18_r19_reconciled.json), [cuerpo PR basado en plantilla](evidencia/h3req1_pr_body_draft_local_review_2026-10-18_r19.md) y [tratamiento visual sanitizado](evidencia/h3req1_visual_evidence_redaction_2026-10-18_r19.md) registran avances B y el snapshot sucesor. El checker documental pasa localmente con el manifiesto exacto; actionlint/ShellCheck esperan Docker. B está incompleto; no se publicó ni abrió PR. R18 y el WIP fuente permanecen preservados.
- [Checkpoint de preparación R18](evidencia/h3req1_g10_remote_preparation_2026-10-14_r18.md) registra A aplicado y los bloqueos actuales. El [paquete Development A–D](evidencia/h3req1_development_integration_package_2026-10-14_r18.md), [checks](evidencia/h3req1_remote_preparation_checks_2026-10-14_r18.txt), [revisión independiente](evidencia/h3req1_remote_preparation_independent_review_2026-10-14_r18.txt), [manifest reconciliado](evidencia/h3req1_pr_scope_manifest_2026-10-14_r18_reconciled.json) y [cuerpo PR basado en plantilla](evidencia/h3req1_pr_body_draft_local_review_2026-10-14_r18.md) conforman el paquete actual. R18 no acredita integración ni GO Development.
- [Preparación y reconciliación R17](evidencia/h3req1_g10_remote_preparation_2026-10-14_r17_public_sanitized_r18.md) y su paquete, checks, revisión, manifest y body quedan preservados como corte previo a la ejecución A; R18 los actualiza únicamente con resultados nuevos.
- [Corte histórico R16](evidencia/h3req1_g10_remote_preparation_2026-10-14_r16.md) y sus artefactos quedan preservados sin cambios; R17 sustituye únicamente la actualidad que releyó y declara los límites restantes.
- [Corte histórico R15 de preparación remota](evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md) y sus artefactos relacionados se conservan; R16/R17 sustituyen solo observaciones explícitamente releídas.
- [Historia Git local por path](evidencia/h3req1_historia_paths_local_2026-10-12.md) cubre ambos checkouts; un commit no demuestra test, despliegue ni vigencia.
- [Relaciones locales investigadas](evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md) precisa alcance de búsquedas y relaciones aún no acreditadas.
- [Relaciones semánticas C03](evidencia/h3req1_relaciones_semanticas_c03_2026-10-13.md) desglosa diagnósticos, runners, tests, locks y overrides con límites de evidencia/operación.
- [Reclasificación web R11](evidencia/h3req1_reclasificacion_componentes_web_2026-10-13_r11.md) documenta la separación de Admin, UI compartida y transporte Supabase con búsquedas de ambos checkouts e historia local.
- [Resolución local R11](evidencia/h3req1_sem_resolucion_relaciones_locales_2026-10-13_r11.md) conserva fuentes, búsquedas y límites que respaldan el cierre de relaciones locales. El [cierre documental local R12](evidencia/h3req1_documentacion_cierre_local_2026-10-13_r12.md) presenta el resultado corregido, la revisión independiente, los checks ejecutados y el traspaso a la etapa siguiente; R11 queda como corte provisional histórico.
- [Reanudación R10](evidencia/h3req1_documentacion_semantica_reanudacion_2026-10-13_r10.md) queda como corte histórico; sus conteos y tareas no describen el estado actual.
- [Relaciones locales de infra/release](evidencia/h3req1_relaciones_infra_local_2026-10-13.md) registra búsquedas literales, callers y sus límites en ambos checkouts.
- [Cierre funcional R178](evidencia/h3req1_g09_local_close_r178_2026-10-11.md) y [revisión R181/R182](evidencia/h3req1_g10_r8_review_corrections_r181_2026-10-12.md) permanecen como evidencia local de esos cortes; no se reescriben.
- [Navegación histórica R13](evidencia/h3req1_documentacion_navegacion_historica_2026-10-13_r13.md) documenta catálogos, enlaces individuales, R37 y sus límites. El [borrador del paquete documental R13](evidencia/h3req1_pr_body_draft_local_review_2026-10-13_r13_docs.md) no es un PR ejecutado.
- El [plan H3REQ1 de cierre del 2026-10-04](operaciones/plan_cierre_integral_h3req1_2026-10-04.md) se conserva como contrato histórico citado por tareas/pruebas; el estado vigente prevalece.
- [Estructura documental R10](evidencia/h3req1_documentacion_estructura_2026-10-13_r10.md) registra la navegación única, decisiones exactas de conservación/fusión/sustitución/retiro y copias externas verificadas.
- [Reorganización documental R9](evidencia/h3req1_documentacion_estructura_2026-10-12.md) conserva el corte y resultado anterior, incluida la propuesta de puente después retirada.
- [Planes H3REQ1 reemplazados](evidencia/planes_historicos/plan_go_h3req1_local_development_2026-10-02.md) y [remediación inicial archivada](evidencia/planes_historicos/h3req1_remediation_plan_2026-09-24.md) conservan historia; no son rutas activas de trabajo.
- La [ruta ejecutable del corte 2026-10-08](evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md) conserva su secuencia y límites NO-GO de ese momento; fue sustituida por el cierre local R178/R181/R182 y no dirige la continuación actual.
- [Historial previo del estado](evidencia/h3req1_estado_historico_2026-10-12_public_sanitized_r18.md) conserva los snapshots anteriores sin autoridad vigente.

<!-- h3req1:historical-catalog-index:start -->
### Catálogos subordinados de evidencia histórica

Estos catálogos dan navegación individual a documentos preservados. No convierten resultados históricos en estado vigente ni autoridad operativa. Los conteos se generan desde el registro canónico y el checker valida que el bloque visible coincida.

| Proceso/familia | Catálogo | Documentos catalogados |
|---|---|---:|
| C03 integrado: sesiones, invitación y recuperación | [C03 integrado: sesiones, invitación y recuperación](catalogos_historicos/c03_integrado.md#documentos-preservados) | 59 |
| Admin, autenticación e historia editorial | [Admin, autenticación e historia editorial](catalogos_historicos/admin_auth_editorial.md#documentos-preservados) | 14 |
| Frontend público y UAT | [Frontend público y UAT](catalogos_historicos/frontend_publico_uat.md#documentos-preservados) | 25 |
| Pipeline, datos y base de datos | [Pipeline, datos y base de datos](catalogos_historicos/pipeline_base_datos.md#documentos-preservados) | 15 |
| Infraestructura, seguridad y CI | [Infraestructura, seguridad y CI](catalogos_historicos/infra_seguridad_ci.md#documentos-preservados) | 78 |
| Documentación, trazabilidad y transferencia | [Documentación, trazabilidad y transferencia](catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados) | 14 |
| Registros operativos históricos y JIT | [Registros operativos históricos y JIT](catalogos_historicos/operacion_jit.md#documentos-preservados) | 110 |
| Evidencia histórica de requerimientos e hitos | [Evidencia histórica de requerimientos e hitos](catalogos_historicos/requerimientos_hitos.md#documentos-preservados) | 10 |
| Seguimiento y handoffs históricos | [Seguimiento y handoffs históricos](catalogos_historicos/seguimiento_historico.md#documentos-preservados) | 7 |
| Documentación DB sustituida | [Documentación DB sustituida](catalogos_historicos/database_legacy.md#documentos-preservados) | 1 |
| C03 — diagnóstico de arranque de runtimes locales | [C03 — diagnóstico de arranque de runtimes locales](catalogos_historicos/c03_inicio_runtime.md#documentos-preservados) | 35 |
| C03 — snapshots y preflight de fuentes | [C03 — snapshots y preflight de fuentes](catalogos_historicos/c03_snapshot_fuentes.md#documentos-preservados) | 19 |
| C03 — diagnósticos Docker, F1 y clasificadores | [C03 — diagnósticos Docker, F1 y clasificadores](catalogos_historicos/c03_diagnosticos_runtime.md#documentos-preservados) | 46 |
<!-- h3req1:historical-catalog-index:end -->

## Límites del corte

Las preferencias locales de `.context/.obsidian/` se preservan en el backup y no forman parte del paquete compartido. R15 ejecutó lecturas acotadas de GitHub, Supabase, Cloudflare y procedencia pública de braces; el reporte delimita errores de acceso, discrepancias y preguntas no resueltas. No se leyó información operativa, identidades, correo ni valores secretos; no hubo escrituras ni ejecución remota. Código/migrations/workflows locales no demuestran adopción del WIP, schema completo, protección efectiva, DNS global, runtime ni acceptance. La autoridad operativa y la próxima decisión están en [estado](estado_del_proyecto.md).
