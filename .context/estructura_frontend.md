# Estructura Frontend

## Stack

- Next.js `16.2.3` con App Router.
- React y React DOM `19.2.4`.
- TypeScript 5 y Tailwind CSS 4.
- Export estatico con `output: 'export'`, `trailingSlash: true` e imagenes no optimizadas.
- `ignoreBuildErrors: true` permanece configurado; typecheck separado sigue siendo un gate necesario.

## Rutas

| Ruta | Funcion |
|---|---|
| `/` | Busqueda, filtros y listado de programas. |
| `/courses/` | Fallback para resolucion de cursos. |
| `/courses/[institution]/[slug]/` | Detalle estatico y carga cliente del programa. |
| `/compare/` | Comparacion de hasta tres programas. |
| `/privacidad/` | Politica de privacidad. |
| `/terminos/` | Terminos del servicio. |

La ruta de detalle genera parametros estaticos y usa el formato canonico `/courses/{institution}/{slug}/`.

## Datos Publicos

El frontend consulta la Data API de Supabase con publishable key publica y campos permitidos. Las consultas visibles filtran `is_active=true` e `is_verified=true`; el contrato Hito 1 debe mantener compatibilidad con superficies revocadas y con el estado editorial que defina [Supabase](sistema_db_supabase.md).

No se deben incluir secret keys, service-role credentials ni mutaciones administrativas en el bundle del navegador.

## Gates De Cambio

Ejecutar en el contenedor: lint, typecheck y build estatico. Revisar rutas generadas, navegacion movil, detalle, filtros y comparador. Los cambios de frontend ligados a G1b deben tolerar que ratings/reviews y view count legacy permanezcan apagados.

Ver [Arquitectura del pipeline](arquitectura_pipeline.md) y [Tarea Hito 1](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
