# Frontend público y portal Admin

## Componentes principales

- [Web público](componentes/web_publico.md#fuentes-y-relaciones) posee sus rutas, el estado de catálogo/comparación, assets y cliente SDK que consultan datos publicados.
- [Portal Admin](componentes/admin_portal.md#fuentes-y-relaciones) posee cola editorial, edición/vista previa, membresías y onboarding. El contrato server-side vive en [runtime Admin](componentes/admin_runtime.md#fuentes-y-relaciones).
- [Presentación web compartida](componentes/presentacion_web_compartida.md#fuentes-y-relaciones) separa primitives UI, renderer de cursos (detalle público y preview Admin) y helper `cn`; sus consumidores se revisan en ambas superficies.
- [Transporte Supabase](componentes/supabase_transport.md#fuentes-y-relaciones) comparte la política `apikey`/JWT entre el SDK público y el BFF, con allowlists diferentes por runtime.

Al modificar una pantalla, el [registro fuente-componente](trazabilidad/registro_fuentes_componentes.md) señala la fuente y sección exacta; desde ahí se siguen el contrato, consumidores, datos, suites y permisos. Cambiar una propiedad compartida requiere revisar todos los callers enumerados, no solo la ruta que originó el cambio.

## Rutas

| Ruta | Responsabilidad | Evidencia de fuente |
|---|---|---|
| / | catálogo y filtros | web/src/app/page.tsx, HomeContent.tsx. |
| /courses/ | fallback/ruta de catálogo | web/src/app/courses/page.tsx. |
| /courses/[institution]/[slug]/ | detalle estático y renderer público | web/src/app/courses/[institution]/[slug]/page.tsx, CourseDetailClient.tsx, CoursePublicRenderer.tsx. |
| /compare/ | comparación por IDs | web/src/app/compare/page.tsx, CompareContent.tsx. |
| /privacidad/, /terminos/ | documentos públicos legales | web/src/app/privacidad/page.tsx, terminos/page.tsx. |
| /admin/ | tablero/cola editorial | web/src/app/admin/page.tsx, AdminCourseQueue.tsx. |
| /admin/login/ | autenticación | web/src/app/admin/login/page.tsx. |
| /admin/auth/callback/ | callback de Auth | web/src/app/admin/auth/callback/page.tsx. |
| /admin/accept-invite/ | aceptar invitación | web/src/app/admin/accept-invite/page.tsx. |
| /admin/setup-password/, /admin/reset-password/ | onboarding y recuperación | rutas correspondientes bajo web/src/app/admin/. |
| /admin/edit/ | editor, preview y publicación | web/src/app/admin/edit/page.tsx, componentes web/src/components/admin/. |
| /admin/users/ | administración de membresías | web/src/app/admin/users/page.tsx. |

El middleware reconoce también /admin/auth/callback, /api/admin/* y la normalización de slash. La ruta callback aparece bajo la protección general Admin y el BFF expone el callback correspondiente; no asumir que una ruta Next es backend.

## Catálogo, búsqueda y comparación

HomeContent mantiene estado de búsqueda/filtros sincronizado con query params y caché local del catálogo. Busca por nombre de curso e institución; calcula facetas contextuales para categoría, tipo, institución y modalidad; permite límites de precio, rangos de duración y objetivos de carrera. Los rangos de precio en el código son accesible ≤ S/ 1.500, estándar > S/ 1.500–5.000, premium > S/ 5.000–15.000 y ejecutivo > S/ 15.000. Ordena por popularidad, precio, ROI, reciente y precio ascendente/descendente. La paginación muestra 12 elementos por página.

La lista para comparar se persiste en localStorage bajo StudIAMatch_compare_list, con máximo de tres programas. La ruta de comparación valida IDs UUID y obtiene los campos desde el contrato público efectivo.

El detalle usa generateStaticParams desde datos consultados al build y entrega metadatos/JSON-LD. Por el export estático, un curso nuevo no adquiere necesariamente una ruta HTML hasta reconstruir; los 404/redirects y la purga remota de caché no se verifican en este corte. Los datos de fallback/mock de build se clasifican como fixture, no como catálogo real.

## Asesoría, estados y accesibilidad

El CTA “Solicitar asesoría” presenta el modal que declara asesoría temporalmente deshabilitada. No hay flujo actual de captura de PII ni motor activo de recomendaciones por ese CTA. La atestación sanitizada conserva esta limitación editorial.

La UI contiene estados de carga, vacío, error y retry/cache en los módulos públicos/Admin; los criterios concretos están en HomeContent.tsx, CoursePublicRenderer.tsx y componentes Admin. Hay etiquetas, semántica, focus y clases responsive en rutas observadas. La evidencia R178 cubre los casos y viewports declarados, no constituye auditoría WCAG completa ni SLA de accesibilidad.

## Admin: sesión y edición

El cliente llama únicamente rutas same-origin /api/admin/*; no persiste el JWT en JS. La sesión se conserva en cookie HttpOnly administrada por Pages Functions. `AdminSessionGuard` restringe las áreas Admin protegidas, consulta la sesión Auth y aplica timeout/inactividad con refresco de actividad; no resuelve el rol. `currentAdminRole()` obtiene el rol mediante `admin_current_user_role()`, y las páginas/BFF/RPC aplican sus gates. MFA ofrece configuración/reinicio/desafío TOTP; las operaciones sensibles validan AAL2 server-side.

La cola muestra filtros/facetas/estados; el editor ofrece vista previa viva, edición por campos con procedencia, control de versión optimista y conflicto visible, guardar, publicar/despublicar, archivar, calidad, disponibilidad respaldada por evidencia HTTPS y auditoría de solo lectura. La verificación manual de disponibilidad vence como máximo a 90 días y al caducar regresa al estado calculado. La cuenta Admin puede invitar y administrar rol/actividad sin desactivar al último administrador activo.

Onboarding distingue invitación, aceptación, creación de contraseña, MFA y acceso listo. Reenvíos conservan el encadenamiento de invitaciones e idempotencia por request ID; retry debe reutilizar el identificador para evitar emisiones duplicadas.

## Datos y pruebas

La fuente pública es courses_public_effective; Admin opera por RPC allowlisted a través del BFF. Los datos sintéticos locales nunca se promueven como catálogo productivo.

| Área | Pruebas/evidencia | Criterio/límite |
|---|---|---|
| Catálogo, filtros, detalle y comparación | suites en tests/, Playwright/capturas locales en .context/evidencia/h3req1_g09_* | R178 documenta casos y viewports seleccionados; no acredita adopción remota. |
| Admin/editorial/MFA/onboarding | tests/h3_local_uat.mjs, tests/h3_invitation_uat.mjs, contracts test_h3_*, MFA/password tests y harnesses SQL | R178 contiene los resultados locales y los skips/warnings declarados. |
| Render público tras publicación | tests/h3_local_uat.mjs, tests/test_h3_admin_queue_ux_contract.py, harnesses de DB | Static export requiere rebuild para páginas estáticas; el reflejo remoto no se verificó. |

## Fuentes

web/src/app/, web/src/components/, web/src/lib/admin-auth.ts, web/src/lib/supabase.ts, web/src/components/courses/CoursePublicRenderer.tsx; [atestación cliente sanitizada](evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md); [R178](evidencia/h3req1_g09_local_close_r178_2026-10-11.md).

## Navegación relacionada

[Público](componentes/web_publico.md) · [Admin](componentes/admin_portal.md) · [Presentación compartida](componentes/presentacion_web_compartida.md) · [Transporte Supabase](componentes/supabase_transport.md) · [BFF runtime](componentes/admin_runtime.md) · [Backend](backend.md) · [Database](database.md) · [Seguridad](seguridad.md) · [Pruebas](pruebas.md) · [Criterios sanitizados](requerimientos/README.md) · [Hitos](hitos/README.md) · [Evidencia R178](evidencia/h3req1_g09_local_close_r178_2026-10-11.md) · [Índice](indice.md)

Registro por fuente: [frontend público](trazabilidad/registro_fuentes_componentes.md#frontend-publico) · [portal Admin](trazabilidad/registro_fuentes_componentes.md#portal-admin).
