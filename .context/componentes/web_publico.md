# Componente: frontend público

## Propósito y límites

Frontend Next App Router compilado a static export. Presenta catálogo, búsqueda/filtros, detalle, comparación y páginas legales. Lee datos efectivos publicados; no administra sesión Admin ni escribe leads desde el CTA de asesoría vigente.

## Fuentes y contratos

- Entradas: web/src/app/page.tsx y HomeContent.tsx; web/src/app/courses/*; web/src/app/compare/*; web/src/app/privacidad/ y terminos/.
- Cliente de datos público: `web/src/lib/supabase.ts` consume el transporte HTTP común; no depende de primitives ni del renderer. En la dirección inversa, `CoursePublicRenderer.tsx` importa solo `cleanSlug` desde este módulo. Cargarlo ejecuta sus comprobaciones de configuración e inicializa el cliente Supabase; ese import por sí solo no envía una petición de red. La dependencia cruzada y sus consecuencias se detallan en [presentación web compartida](presentacion_web_compartida.md).
- Datos: courses_public_effective; IDs UUID para compare; paths institucional/slug para detalle. Public keys via apikey.
- Contratos descritos con criterios en [frontend.md](../frontend.md) y schema en [database.md](../database.md).

## Consumidores, pruebas y operación

Los usuarios públicos consumen páginas estáticas; el build usa static params para detalle. Tests focales y UAT local están en tests y evidencia G09. Una ruta nueva puede requerir rebuild; caching/redirect remoto no se validó.

`parseDurationToMonths` es el contrato compartido de duración para filtros del catálogo, facetas y “Actualizarme”; normaliza unidades compuestas antes de categorizar el curso. “Más filtros” se posiciona desde la fila primaria y en móvil se centra dentro del viewport. El catálogo canónico asigna H3-UAT-058 a H3-CA4.11 (listado/detalle responsive) y H3-UAT-059 a H3-CA4.9 (filtros independientes y “Actualizarme”); ambos declaran cero resets. R12 validó el build estático local y ejecutó ambos casos juntos: 2/2 casos, 6/6 viewports, seis capturas, cero retries y cero resets. 058 comprobó el panel, listado, detalle y footer a 320 px; 059 pasó 39/39 aserciones por viewport (117/117) incluyendo todos los filtros y el consumidor “Actualizarme”. El fixture PG17 completo se reutilizó sin SQL ni limpieza; su postflight read-only confirmó 13 relaciones públicas, 31 cursos, 31 filas editoriales, 16 cursos efectivos y 26 filas de cola. El build usa el source base `6e1bd8f5ad623a44524b11391c1385c59b9a4b70` más el cambio local del rótulo; SHA-256 de `HomeContent.tsx` `84af11d225b18fd52e95fb54625c7014a06e6a1a31bb413d29a6a980f516ffd7` y runner `tests/h3_local_uat.mjs` `e9c2ed3a660d2c4982c7443fd4ffed0da4ab174d2e357284d5dac0026a5719bd`. Chrome Windows MCP observó la página local a 390 px; 320 px lo cubre el runner. R11 y R12 conservan evidencia separada; el resumen y límites están en el [ciclo de aceptación local](../evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-acceptance-cycle-2026-10-24.md). Estado: **VALIDADO LOCAL — PENDIENTE REMOTO**; repetir en Preview/Development solo después de publicar/integrar el candidato. Esto no valida D06/Admin ni cierra H3REQ1.

## Estado y fuentes

Implementación candidata en el worktree; validación local R178 con fixtures/casos enumerados; adopción remota del HTML/dataset/cache desconocida. Las fuentes propias son rutas públicas bajo `web/src/app/`, assets de `web/public/`, `Header`, `Footer`, `AnimatedCounter` y sus tests consumidores. El renderer, primitives y helper `cn` tienen asignación compartida separada; `supabase-transport.ts` pertenece a su ficha de contrato HTTP. Véase [R178](../evidencia/h3req1_g09_local_close_r178_2026-10-11.md).

## Navegación relacionada

[Frontend](../frontend.md#componentes-principales) · [Presentación web compartida](presentacion_web_compartida.md) · [Transporte Supabase](supabase_transport.md) · [Database](../database.md) · [Pruebas](../pruebas.md) · [HITO-004/005](../hitos/README.md) · [Criterios sanitizados](../requerimientos/README.md) · [Registro](../trazabilidad/registro_fuentes_componentes.md#frontend-publico) · [Índice](../indice.md)


## Mapa de fuentes, consumidores y suites

La tabla contiene una fila por path del componente y se deriva de la búsqueda estática local enlazada; los consumers de Next se marcan como convención y las ausencias quedan limitadas al alcance. No añade resultados de ejecución.

| Fuente | Consumidor/entrada | Suite con referencia o ausencia en scope |
|---|---|---|
| `web/public/_headers` | Cloudflare Pages static asset convention / Next public asset; direct importer: none expected | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/public/robots.txt` | Cloudflare Pages static asset convention / Next public asset; direct importer: none expected | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/app/HomeContent.tsx` | web/src/app/page.tsx | `tests/test_admin_invite_edge_contract.py`, `tests/test_h2_development_legacy_compat.py`, `tests/test_supabase_credentials_contract.py` |
| `web/src/app/compare/CompareContent.tsx` | web/src/app/compare/page.tsx | `tests/test_h2_development_legacy_compat.py`, `tests/test_supabase_credentials_contract.py` |
| `web/src/app/compare/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/app/courses/CoursesFallbackPage.tsx` | web/src/app/courses/page.tsx | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx` | web/src/app/courses/[institution]/[slug]/CourseDetailClientWrapper.tsx | `tests/test_h2_development_legacy_compat.py`, `tests/test_h3_admin_queue_ux_contract.py`, `tests/test_supabase_credentials_contract.py` |
| `web/src/app/courses/[institution]/[slug]/CourseDetailClientWrapper.tsx` | web/src/app/courses/CoursesFallbackPage.tsx, web/src/app/courses/[institution]/[slug]/page.tsx | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/app/courses/[institution]/[slug]/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | `tests/test_h2_development_legacy_compat.py`, `tests/test_supabase_credentials_contract.py` |
| `web/src/app/courses/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/app/favicon.ico` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/app/globals.css` | web/src/app/layout.tsx | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/app/layout.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/app/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | `tests/h3req1_docker_peer_substep_diag/r9_tsc_output_classifier_v1.py`, `tests/test_h2_development_legacy_compat.py`, `tests/test_h2_writer_scan.py`, `tests/test_supabase_credentials_contract.py` |
| `web/src/app/privacidad/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/app/terminos/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/components/AnimatedCounter.tsx` | no direct static import in graph scope | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/components/Footer.tsx` | web/src/app/layout.tsx | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/components/Header.tsx` | web/src/app/layout.tsx | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/lib/supabase.ts` | web/src/app/HomeContent.tsx, web/src/app/compare/CompareContent.tsx, web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx, web/src/app/courses/[institution]/[slug]/page.tsx, web/src/app/page.tsx, web/src/components/courses/CoursePublicRenderer.tsx | `tests/test_h2_pipeline_contract.py`, `tests/test_h3_admin_queue_ux_contract.py`, `tests/test_supabase_credentials_contract.py` |

## Fuentes y relaciones

El listado exacto de rutas públicas, assets, estilos y páginas de este módulo está en el [registro fuente-componente](../trazabilidad/registro_fuentes_componentes.md#frontend-publico). Las relaciones de primitives, renderer y `cn` están en [presentación web compartida](presentacion_web_compartida.md#fuentes-y-relaciones), y la política del cliente SDK en [Supabase transport](supabase_transport.md#fuentes-y-relaciones). Mantén las rutas especiales del framework y los contratos públicos sin renombrarlos.

## Navegación histórica local

Evidencia preservada por proceso; cada catálogo enlaza sus documentos históricos individualmente y no es una autoridad operativa.

- [C03 integrado: sesiones, invitación y recuperación](../catalogos_historicos/c03_integrado.md#documentos-preservados)
- [Admin, autenticación e historia editorial](../catalogos_historicos/admin_auth_editorial.md#documentos-preservados)
- [Frontend público y UAT](../catalogos_historicos/frontend_publico_uat.md#documentos-preservados)
- [Pipeline, datos y base de datos](../catalogos_historicos/pipeline_base_datos.md#documentos-preservados)
- [Infraestructura, seguridad y CI](../catalogos_historicos/infra_seguridad_ci.md#documentos-preservados)
- [Documentación, trazabilidad y transferencia](../catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados)
- [Registros operativos históricos y JIT](../catalogos_historicos/operacion_jit.md#documentos-preservados)
- [Seguimiento y handoffs históricos](../catalogos_historicos/seguimiento_historico.md#documentos-preservados)
- [C03 — diagnóstico de arranque de runtimes locales](../catalogos_historicos/c03_inicio_runtime.md#documentos-preservados)
- [C03 — diagnósticos Docker, F1 y clasificadores](../catalogos_historicos/c03_diagnosticos_runtime.md#documentos-preservados)
