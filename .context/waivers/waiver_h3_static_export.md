# H3REQ1 — Waiver Técnico: Static Export

**Fecha**: 2026-09-02
**Estado**: SUPERSEDED_BY_REVALIDATION
**Severidad**: MEDIUM
**Owner**: Build/DevOps
**Vencimiento**: 2026-12-31

## Causa Raíz

El static export (`output: 'export'`) de Next.js 16.2.3 con React 19.2.4 falla sistemáticamente durante la fase de prerender con error `Cannot read properties of null (reading 'useContext')` en `/_global-error` y otras rutas.

Este es un bug conocido upstream en el runtime SSR de Next.js 16 + React 19 cuando se combina con Turbopack y static export.

## Intentos de Remediación

Se probaron 14+ combinaciones de versiones:
- Next.js 16.2.3 + React 19.2.4: falla en `/_global-error`
- Next.js 15.1.4 + React 18.3.1: falla en `/404` con `<Html>` import error
- Next.js 14.2.18 + React 18.3.1: falla en todas las páginas con `useContext` null
- Next.js 14.2.18 + React 19.0.0: falla en todas las páginas con `useContext` null
- Next.js 16.x + React 18.3.1: falla con `useContext` null / fuentes Geist desconocidas

Todas las variantes fallan en la fase de generación de páginas estáticas. Se restauró la combinación original Next.js 16.2.3 + React 19.2.4 como versión vigente del repo.

## Decisión

**Ejecutar UAT H3 contra dev server de Next.js** (`npm run dev`) en lugar de static export, usando mock Auth backend y PostgreSQL 17 local, con el perímetro real `static-server.js` (puerto 3002) validando el bloqueo por hostname. Esto permite validar completamente la funcionalidad H3 (RBAC, AAL2, membresías, ownership) sin depender del static export bugueado.

## Riesgo Residual

- **LOCAL**: Ninguno — el dev server es adecuado para validación funcional; dos corridas UAT completas consecutivas PASS (47/47 y 141/141) en el ciclo de cierre
- **CERTIFICATION**: BAJO — el despliegue a Certification usará el build normal (no mock) contra Supabase Free; el waiver no cambia el mecanismo de despliegue
- **PRODUCTION**: BAJO — el despliegue a Production usa el build normal contra Supabase Pro

El static export solo se necesita para el entorno mock aislado; los ambientes reales (Development/Certification/Production) usan los endpoints Supabase correspondientes y no requieren mock. El build normal de producción (`npm run build`) no fue re-verificado en este ciclo y se validará en el PR/JIT de despliegue.

## Plan de Resolución

1. **Corto plazo** (H3): revalidación ejecutada; build normal/mock PASS el 2026-09-02.
2. **Mediano plazo**: mantener el required check `static-build` activo en CI.
3. **Reapertura**: crear un waiver nuevo solo si el fallo reaparece con evidencia reproducible.

## Supersesión

El 2026-09-02 se reejecutaron `npm run build` y `npm run build:mock` dentro de
`studiamatch-dev`; ambos compilaron correctamente y el export contiene
`admin/index.html`, `admin/login/index.html`, `admin/edit/index.html` y
`admin/users/index.html`. Por ello este waiver deja de aplicar al candidato actual
y no puede usarse para omitir el required check `static-build` del PR.

Si el fallo reaparece, debe abrirse un waiver nuevo con evidencia reproducible,
owner, riesgo residual, vencimiento y aprobación humana explícita.

**Aprobado por**: No aplica; waiver no aprobado y superseded por revalidación  
**Revisión siguiente**: Solo si reaparece el fallo
