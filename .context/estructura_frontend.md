# Estructura Frontend

## Stack

- Next.js `16.2.3` con App Router.
- React y React DOM `19.2.4`.
- TypeScript 5 y Tailwind CSS 4.
- Export estatico con `output: 'export'`, `trailingSlash: true` e imagenes no optimizadas.
- `ignoreBuildErrors: true` permanece configurado; typecheck separado sigue siendo un gate necesario.
- Fuentes de sistema mediante variables CSS locales; no usar `next/font/google` en gates hermeticos sin red.

## Rutas

| Ruta | Funcion |
|---|---|
| `/` | Busqueda, filtros y listado de programas. |
| `/courses/` | Catalogo publico de programas, equivalente navegable del listado principal. |
| `/courses/[institution]/[slug]/` | Detalle estatico y carga cliente del programa. |
| `/compare/` | Comparacion de hasta tres programas. |
| `/privacidad/` | Politica de privacidad. |
| `/terminos/` | Terminos del servicio. |

La ruta de detalle genera parametros estaticos y usa el formato canonico `/courses/{institution}/{slug}/`.

## Datos Publicos

El frontend consulta la Data API de Supabase con publishable key publica y campos permitidos. Las consultas visibles filtran `is_active=true` e `is_verified=true`; el contrato Hito 1 debe mantener compatibilidad con superficies revocadas y con el estado editorial que defina [Supabase](sistema_db_supabase.md).

No se deben incluir secret keys, service-role credentials ni mutaciones administrativas en el bundle del navegador. `NEXT_PUBLIC_SUPABASE_URL` debe normalizar a un origen limpio `https://*.supabase.co`; loopback `http://127.0.0.1:<port>` solo se permite con el placeholder corto `sb_publishable_ci_test` para gates locales.

## Captura De Leads

Desde [ADR-0005](decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md), el perfil frontend habilitado no incluye captura publica de leads ni transporte automatico de PII. No existe flag soportado para reactivar formularios, no se exportan marcadores `data-lead-capture-*`, no hay POST a `leads` y las CTAs publicas navegan a catalogo, detalle o comparacion.

La comparativa persiste solo `{id, name}` en `localStorage`, valida UUIDs, deduplica y limita a tres elementos. No persiste registros completos del API ni PII.

Los enlaces `mailto` de soporte en footer, privacidad o terminos no pertenecen al pipeline automatico de leads/email. La reactivacion de formularios publicos exige [BK-F9.5-05](backlog_tareas/req_est_001_sprint_1/backlog_seguridad_leads_email.md), nuevo requerimiento y migration forward-only propia.

## Gates De Cambio

Ejecutar en el contenedor: lint, typecheck, un unico build estatico con configuracion hostil, `assertPublicExport.mjs` y Playwright publico hermetico. Playwright debe interceptar la Data API publica esperada, bloquear `leads`, validar cero egress no esperado, cero errores de consola/hidratacion, rutas Home/courses/detalle/compare, teclado, `aria-pressed`, viewport 375x667 y zoom 200% sin overflow horizontal. Los cambios de frontend ligados a G1b deben tolerar que ratings/reviews y view count legacy permanezcan apagados.

Ver [Arquitectura del pipeline](arquitectura_pipeline.md) y [Tarea Hito 1](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
