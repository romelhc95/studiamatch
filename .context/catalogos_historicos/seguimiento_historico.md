# Seguimiento y handoffs históricos

> Catálogo de navegación histórica. Sus entradas preservan cortes y resultados; no crean autoridad operativa ni trasladan un resultado al estado actual.

## Propósito y alcance

Cortes previos de seguimiento, retrospectiva y navegación; no reemplazan el estado operativo vigente.

Documentos preservados en este catálogo: 7. La asignación se mantiene en el registro JSON canónico. Cada vínculo conduce al archivo histórico sin modificar sus bytes.

## Componentes relacionados

- [Frontend público](../componentes/web_publico.md#navegacion-historica-local)
- [Portal Admin](../componentes/admin_portal.md#navegacion-historica-local)
- [Runtime Admin](../componentes/admin_runtime.md#navegacion-historica-local)
- [Base de datos](../componentes/database_migrations.md#navegacion-historica-local)
- [Infraestructura y release](../componentes/infra_release.md#navegacion-historica-local)
- [Seguridad y tooling](../componentes/seguridad_tooling.md#navegacion-historica-local)
- [Pruebas y evidencia](../componentes/pruebas_evidencia.md#navegacion-historica-local)
- [Legacy y deprecated](../componentes/legacy.md#navegacion-historica-local)
- [Transporte Supabase cliente/BFF](../componentes/supabase_transport.md#navegacion-historica-local)

## Documentos preservados

La relación anterior/posterior se muestra solo cuando una fuente local la declara. El número de revisión por sí solo no demuestra una secuencia.

### [H3REQ1 — avance comprobado, PR y pruebas remotas](../seguimiento/h3req1_estado_pr_y_remoto_2026-10-05.md)

- **Path:** `.context/seguimiento/h3req1_estado_pr_y_remoto_2026-10-05.md` · **Estado:** histórico — Registro preservado de un corte anterior; no prueba por sí solo el comportamiento vigente ni crea una autorización actual.
- **Propósito documentado:** H3REQ1 — avance comprobado, PR y pruebas remotas _(Resumen tomado del H1 del documento; no acredita por sí solo aceptación ni ejecución.)_
- **Componente(s):** [Infraestructura y release](../componentes/infra_release.md#fuentes-y-relaciones); [Pruebas y evidencia](../componentes/pruebas_evidencia.md#fuentes-y-relaciones). Base: Las rutas de fuente citadas se asignaron con el registro canónico; título/ruta añade solo contexto. No afirma que el componente consuma esta evidencia.
- **Requerimiento(s):** H3REQ1. Código explícito en título o ruta; no valida aceptación.
- **Fuente(s):** referencia identificada localmente; [.github/pull_request_template.md](../../.github/pull_request_template.md); Ruta exacta obtenida de enlaces/rutas citadas en el documento o de una coincidencia de cohorte local explícita.
- **Runner:** referencia identificada localmente; [tests/h3req1_c03_integrated_drill.sh](../../tests/h3req1_c03_integrated_drill.sh); Ruta exacta obtenida de enlaces/rutas citadas en el documento o de una coincidencia de cohorte local explícita.
- **Test(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Manifiesto(s):** referencia identificada localmente; [tests/h3req1-c03-integrated.sha256](../../tests/h3req1-c03-integrated.sha256); Ruta exacta obtenida de enlaces/rutas citadas en el documento o de una coincidencia de cohorte local explícita.
- **Resultado(s):** referencia identificada localmente; [.context/evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md](../evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md), [.context/evidencia/h3req1_h3_close03_integrated_preflight_2026-10-05.md](../evidencia/h3req1_h3_close03_integrated_preflight_2026-10-05.md); Ruta exacta obtenida de enlaces/rutas citadas en el documento o de una coincidencia de cohorte local explícita.
- **Anterior/posterior:** no se atribuye secuencia con la evidencia local revisada. No se atribuye secuencia por numeración solamente; se revisaron referencias y nombres de cohorte local.
- **Preservación/alcance:** Notas de traspaso y seguimiento fechadas; el estado vivo actual prevalece y la evidencia histórica se conserva. _(Se escaneó Markdown y referencias de ruta locales; el archivo histórico no se editó.)_.

### [H3REQ1 — avance actual y traspaso ejecutable del próximo ciclo](../seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md)

- **Path:** `.context/seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md` · **Estado:** histórico — Registro preservado de un corte anterior; no prueba por sí solo el comportamiento vigente ni crea una autorización actual.
- **Propósito documentado:** H3REQ1 — avance actual y traspaso ejecutable del próximo ciclo _(Resumen tomado del H1 del documento; no acredita por sí solo aceptación ni ejecución.)_
- **Componente(s):** [Base de datos](../componentes/database_migrations.md#fuentes-y-relaciones); [Pruebas y evidencia](../componentes/pruebas_evidencia.md#fuentes-y-relaciones); [Transporte Supabase cliente/BFF](../componentes/supabase_transport.md#fuentes-y-relaciones). Base: Las rutas de fuente citadas se asignaron con el registro canónico; título/ruta añade solo contexto. No afirma que el componente consuma esta evidencia.
- **Requerimiento(s):** H3REQ1. Código explícito en título o ruta; no valida aceptación.
- **Fuente(s):** referencia identificada localmente; [db/migrations/20260927_h3_admin_queue_facets_filter.sql](../../db/migrations/20260927_h3_admin_queue_facets_filter.sql), [db/migrations/20261004_h3_admin_queue_first_null_guard.sql](../../db/migrations/20261004_h3_admin_queue_first_null_guard.sql), [db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql](../../db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql), [db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql](../../db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql), [db/rollback/h3req1_safe_suspend.sql](../../db/rollback/h3req1_safe_suspend.sql), [web/src/lib/supabase-transport.ts](../../web/src/lib/supabase-transport.ts); Ruta exacta obtenida de enlaces/rutas citadas en el documento o de una coincidencia de cohorte local explícita.
- **Runner:** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Test(s):** referencia identificada localmente; [tests/sql/h3_admin_quota_harness.sql](../../tests/sql/h3_admin_quota_harness.sql), [tests/sql/h3_admin_rpc_signed_gateway_harness.sql](../../tests/sql/h3_admin_rpc_signed_gateway_harness.sql), [tests/sql/h3_from_h2_pro_pg17_harness.sql](../../tests/sql/h3_from_h2_pro_pg17_harness.sql), [tests/sql/h3_quota_postgrest_assert.sql](../../tests/sql/h3_quota_postgrest_assert.sql), [tests/sql/h3_quota_postgrest_fixture.sql](../../tests/sql/h3_quota_postgrest_fixture.sql), [tests/sql/h3_safe_suspend_harness.sql](../../tests/sql/h3_safe_suspend_harness.sql); Ruta exacta obtenida de enlaces/rutas citadas en el documento o de una coincidencia de cohorte local explícita.
- **Manifiesto(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Resultado(s):** referencia identificada localmente; [.context/evidencia/h3req1_h3_close03_integrated_preflight_2026-10-05.md](../evidencia/h3req1_h3_close03_integrated_preflight_2026-10-05.md); Ruta exacta obtenida de enlaces/rutas citadas en el documento o de una coincidencia de cohorte local explícita.
- **Anterior/posterior:** no se atribuye secuencia con la evidencia local revisada. No se atribuye secuencia por numeración solamente; se revisaron referencias y nombres de cohorte local.
- **Preservación/alcance:** Notas de traspaso y seguimiento fechadas; el estado vivo actual prevalece y la evidencia histórica se conserva. _(Se escaneó Markdown y referencias de ruta locales; el archivo histórico no se editó.)_.

### [Mapa documental histórico Obsidian — corte 2026-10-04](../seguimiento/mapa_documental_obsidian_2026-10-04.md)

- **Path:** `.context/seguimiento/mapa_documental_obsidian_2026-10-04.md` · **Estado:** sustituido — Mapa de navegación fechado en 2026-10-04; la estructura vigente está en .context/indice.md y los catálogos actuales.
- **Propósito documentado:** Mapa documental histórico Obsidian — corte 2026-10-04 _(Resumen tomado del H1 del documento; no acredita por sí solo aceptación ni ejecución.)_
- **Componente(s):** [Seguridad y tooling](../componentes/seguridad_tooling.md#fuentes-y-relaciones). Base: Las rutas de fuente citadas se asignaron con el registro canónico; título/ruta añade solo contexto. No afirma que el componente consuma esta evidencia.
- **Requerimiento(s):** sin código explícito en título/ruta. Sin código en título/ruta; no se infiere requerimiento.
- **Fuente(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Runner:** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Test(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Manifiesto(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Resultado(s):** referencia identificada localmente; [.context/evidencia/h3req1_h3_close03_integrated_preflight_2026-10-05.md](../evidencia/h3req1_h3_close03_integrated_preflight_2026-10-05.md); Ruta exacta obtenida de enlaces/rutas citadas en el documento o de una coincidencia de cohorte local explícita.
- **Anterior/posterior:** posterior: [.context/indice.md](../indice.md). El índice vigente lo clasifica expresamente como mapa histórico sin autoridad.
- **Preservación/alcance:** Notas de traspaso y seguimiento fechadas; el estado vivo actual prevalece y la evidencia histórica se conserva. _(Se escaneó Markdown y referencias de ruta locales; el archivo histórico no se editó.)_.

### [plantilla pr historica 2026 09 24](../seguimiento/plantilla_pr_historica_2026-09-24.md)

- **Path:** `.context/seguimiento/plantilla_pr_historica_2026-09-24.md` · **Estado:** histórico — Registro preservado de un corte anterior; no prueba por sí solo el comportamiento vigente ni crea una autorización actual.
- **Propósito documentado:** Archivo sin H1; propósito nominal preservado por el nombre: plantilla pr historica 2026 09 24. _(Resumen tomado del nombre del archivo; no se encontró un H1 que describa propósito.)_
- **Componente(s):** [Frontend público](../componentes/web_publico.md#fuentes-y-relaciones); [Infraestructura y release](../componentes/infra_release.md#fuentes-y-relaciones); [Portal Admin](../componentes/admin_portal.md#fuentes-y-relaciones); [Runtime Admin](../componentes/admin_runtime.md#fuentes-y-relaciones). Base: Las rutas de fuente citadas se asignaron con el registro canónico; título/ruta añade solo contexto. No afirma que el componente consuma esta evidencia.
- **Requerimiento(s):** sin código explícito en título/ruta. Sin código en título/ruta; no se infiere requerimiento.
- **Fuente(s):** referencia identificada localmente; [.github/pull_request_template.md](../../.github/pull_request_template.md), [supabase/functions/admin-invite/index.ts](../../supabase/functions/admin-invite/index.ts), [web/src/lib/admin-auth.ts](../../web/src/lib/admin-auth.ts), [web/src/lib/supabase.ts](../../web/src/lib/supabase.ts); Ruta exacta obtenida de enlaces/rutas citadas en el documento o de una coincidencia de cohorte local explícita.
- **Runner:** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Test(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Manifiesto(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Resultado(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Anterior/posterior:** no se atribuye secuencia con la evidencia local revisada. No se atribuye secuencia por numeración solamente; se revisaron referencias y nombres de cohorte local.
- **Preservación/alcance:** Notas de traspaso y seguimiento fechadas; el estado vivo actual prevalece y la evidencia histórica se conserva. _(Se escaneó Markdown y referencias de ruta locales; el archivo histórico no se editó.)_.

### [Plantilla Tracker Reutilizable](../seguimiento/plantilla_tracker_reutilizable.md)

- **Path:** `.context/seguimiento/plantilla_tracker_reutilizable.md` · **Estado:** histórico — Registro preservado de un corte anterior; no prueba por sí solo el comportamiento vigente ni crea una autorización actual.
- **Propósito documentado:** Plantilla Tracker Reutilizable _(Resumen tomado del H1 del documento; no acredita por sí solo aceptación ni ejecución.)_
- **Componente(s):** [Infraestructura y release](../componentes/infra_release.md#fuentes-y-relaciones); [Legacy y deprecated](../componentes/legacy.md#fuentes-y-relaciones); [Pruebas y evidencia](../componentes/pruebas_evidencia.md#fuentes-y-relaciones). Base: Clasificación por título/ruta para navegación histórica; no afirma consumidor de producto.
- **Requerimiento(s):** sin código explícito en título/ruta. Sin código en título/ruta; no se infiere requerimiento.
- **Fuente(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Runner:** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Test(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Manifiesto(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Resultado(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Anterior/posterior:** no se atribuye secuencia con la evidencia local revisada. No se atribuye secuencia por numeración solamente; se revisaron referencias y nombres de cohorte local.
- **Preservación/alcance:** Notas de traspaso y seguimiento fechadas; el estado vivo actual prevalece y la evidencia histórica se conserva. _(Se escaneó Markdown y referencias de ruta locales; el archivo histórico no se editó.)_.

### [Retrospectiva Hito 1](../seguimiento/retrospectiva_hito_001.md)

- **Path:** `.context/seguimiento/retrospectiva_hito_001.md` · **Estado:** histórico — Registro preservado de un corte anterior; no prueba por sí solo el comportamiento vigente ni crea una autorización actual.
- **Propósito documentado:** Retrospectiva Hito 1 _(Resumen tomado del H1 del documento; no acredita por sí solo aceptación ni ejecución.)_
- **Componente(s):** [Infraestructura y release](../componentes/infra_release.md#fuentes-y-relaciones); [Legacy y deprecated](../componentes/legacy.md#fuentes-y-relaciones); [Pruebas y evidencia](../componentes/pruebas_evidencia.md#fuentes-y-relaciones). Base: Clasificación por título/ruta para navegación histórica; no afirma consumidor de producto.
- **Requerimiento(s):** sin código explícito en título/ruta. Sin código en título/ruta; no se infiere requerimiento.
- **Fuente(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Runner:** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Test(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Manifiesto(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Resultado(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Anterior/posterior:** no se atribuye secuencia con la evidencia local revisada. No se atribuye secuencia por numeración solamente; se revisaron referencias y nombres de cohorte local.
- **Preservación/alcance:** Notas de traspaso y seguimiento fechadas; el estado vivo actual prevalece y la evidencia histórica se conserva. _(Se escaneó Markdown y referencias de ruta locales; el archivo histórico no se editó.)_.

### [RF-01 Build Report - GIT and RELEASE GOVERNANCE](../seguimiento/rf01_build_report.md)

- **Path:** `.context/seguimiento/rf01_build_report.md` · **Estado:** histórico — Registro preservado de un corte anterior; no prueba por sí solo el comportamiento vigente ni crea una autorización actual.
- **Propósito documentado:** RF-01 Build Report - GIT and RELEASE GOVERNANCE _(Resumen tomado del H1 del documento; no acredita por sí solo aceptación ni ejecución.)_
- **Componente(s):** [Infraestructura y release](../componentes/infra_release.md#fuentes-y-relaciones). Base: Clasificación por título/ruta para navegación histórica; no afirma consumidor de producto.
- **Requerimiento(s):** sin código explícito en título/ruta. Sin código en título/ruta; no se infiere requerimiento.
- **Fuente(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Runner:** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Test(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Manifiesto(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Resultado(s):** no identificada en la búsqueda local declarada; no demuestra que nunca existió; Se escaneó el cuerpo Markdown completo buscando rutas locales y enlaces, y nombres de archivos de la misma revisión cuando existían; no se encontró esta relación en ese alcance. Esto no demuestra que el artefacto nunca existiera.
- **Anterior/posterior:** no se atribuye secuencia con la evidencia local revisada. No se atribuye secuencia por numeración solamente; se revisaron referencias y nombres de cohorte local.
- **Preservación/alcance:** Notas de traspaso y seguimiento fechadas; el estado vivo actual prevalece y la evidencia histórica se conserva. _(Se escaneó Markdown y referencias de ruta locales; el archivo histórico no se editó.)_.

---

[Índice principal](../indice.md) · [Estado operativo](../estado_del_proyecto.md)
