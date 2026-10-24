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

`parseDurationToMonths` es el contrato compartido de duración para filtros del catálogo, facetas y objetivo “Actualizarme”; normaliza unidades compuestas antes de categorizar el curso. “Más filtros” se posiciona desde la fila primaria y en móvil se centra dentro del viewport. `tests/h3_local_uat.mjs` cubre geometría con `H3-UAT-058`/`H3-CA4.11` y filtros, duración compuesta, “Actualizarme”, reset y paginación con `H3-UAT-059`/`H3-CA4.9`. En Docker, ambos casos terminaron PASS en desktop/tablet/móvil (6/6 ejecuciones, cero reintentos). Chrome Windows sobre `http://localhost:3020/`, con ancho real de 320 CSS px, midió documento/body/footer en 320 px, footer x=0..320 con `scrollWidth=clientWidth=320` y panel x=16..304; el footer no se desborda. Una fila interna de filtros presenta `scrollWidth=280` frente a `clientWidth=272`, pero sus controles siguen dentro del viewport y la página mide 320 px de ancho. Evidencia: [ciclo de aceptación local 2026-10-24](../evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-acceptance-cycle-2026-10-24.md). Estado **VALIDADO LOCAL — PENDIENTE REMOTO**. Esto no valida Development ni D06/Admin.

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
