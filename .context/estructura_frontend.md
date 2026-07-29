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
| `/courses/` | Fallback para resolucion de cursos. |
| `/courses/[institution]/[slug]/` | Detalle estatico y carga cliente del programa. |
| `/compare/` | Comparacion de hasta tres programas. |
| `/privacidad/` | Politica de privacidad. |
| `/terminos/` | Terminos del servicio. |

La ruta de detalle genera parametros estaticos y usa el formato canonico `/courses/{institution}/{slug}/`.

## Datos Publicos

El frontend consulta la Data API de Supabase con publishable key publica y campos permitidos. Las consultas visibles filtran `is_active=true` e `is_verified=true`; el contrato Hito 1 debe mantener compatibilidad con superficies revocadas y con el estado editorial que defina [Supabase](sistema_db_supabase.md).

No se deben incluir secret keys, service-role credentials ni mutaciones administrativas en el bundle del navegador. `NEXT_PUBLIC_SUPABASE_URL` debe normalizar a un origen limpio `https://*.supabase.co`; loopback `http://127.0.0.1:<port>` solo se permite con el placeholder corto `sb_publishable_ci_test` para gates locales.

## Captura De Leads

`NEXT_PUBLIC_LEAD_CAPTURE_ENABLED` es un flag fail-closed de UX y defensa build-time. Solo el valor exacto `"true"` habilita formularios y transporte; unset, vacio, `false`, `1`, `TRUE` o cualquier otro valor deshabilita la captura y no renderiza controles PII. Como el sitio usa `output: 'export'`, cambiar el flag exige rebuild y redeploy para actualizar el HTML/JS generado.

El flag no es una barrera contra acceso directo a PostgREST. La proteccion real sigue siendo RLS/ACL, allowlist de columnas y gates DB. `web/src/lib/leadCaptureCore.ts` contiene la logica pura de flag, estado build-time `enabled|disabled|unset`, allowlist de columnas y transporte. `web/src/lib/leadCapture.ts` es el wrapper navegador que vincula `fetch` sin perder su `this`, usa `apikey` publishable y no envia `Authorization: Bearer`.

El export estatico debe emitir marcadores SSR `data-lead-capture-server-marker="home|course-detail"` con estado exacto `enabled`, `disabled` o `unset`. `disabled` y `unset` deben fallar cerrado: no HTML con `data-lead-capture-form` ni `data-pii-control`; el JS puede contener el codigo cliente pero no debe enviar POST. Los formularios activos deben exponer errores con `role="alert"`, asociar `aria-invalid`/`aria-describedby`, anunciar mantenimiento/exito con live regions y restaurar/fijar foco.

## Gates De Cambio

Ejecutar en el contenedor: lint, typecheck, tests Node del helper, Playwright local con route interception y builds estaticos `enabled`/`disabled`/`unset`. Playwright debe interceptar toda la Data API esperada, contestar CORS/OPTIONS de `leads`, abortar REST no reconocido, validar cero POST cuando falla cerrado, exactamente dos POST cuando esta enabled, errores HTTP/network accesibles, Escape/focus trap/foco restaurado, viewport 375x667 y zoom 200% sin overflow horizontal. Los cambios de frontend ligados a G1b deben tolerar que ratings/reviews y view count legacy permanezcan apagados.

Ver [Arquitectura del pipeline](arquitectura_pipeline.md) y [Tarea Hito 1](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
