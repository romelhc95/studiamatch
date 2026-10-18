# Evidencia del ciclo local — identidad visible en encabezado Admin

**Fecha:** 2026-10-01  
**Estado:** `NO-GO_LOCAL_VISUAL_UAT_PENDING`  
**Atestación:** [Aceptación sanitizada del plan y del encabezado](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md)

## Criterio aceptado

El encabezado del panel Admin muestra el correo Auth de la sesión autenticada en
lugar del distintivo `Admin`/`User`. El rol sigue gobernando permisos, navegación
y la cola editorial; no se solicita ni agrega un username.

## Comprobación remota read-only — Supabase Free

Se contrastó solo el estado de la cuenta indicada por el responsable, sin devolver
ni registrar correo, UUID, hash de contraseña, factor, token o contenido de correo.
La consulta SELECT confirmó:

| Comprobación | Resultado |
|---|---|
| Cuenta Auth única | **PASS** |
| Correo confirmado y contraseña configurada | **PASS** |
| Cuenta creada en la fecha UTC de esta comprobación | **PASS** |
| Inicio de sesión registrado | **PASS** |
| Membresía `admin`, activa y `ready` | **PASS** |
| Factor TOTP verificado | **PASS** |
| Invitación aceptada | **PASS** |

El responsable reportó que recibió la invitación, definió contraseña, configuró y
verificó MFA y pudo iniciar sesión. Los valores persistidos concuerdan con ese
reporte. Esta consulta no verifica entrega del correo ni reproduce el flujo visual.
No se ejecutaron DDL, DML, Auth mutations, invitaciones, writes ni cleanup remoto.

## Implementación local y validaciones

- `web/src/lib/admin-auth.ts` obtiene el email con `auth.getUser()`; ante error o
  ausencia del correo, devuelve `null` sin registrar PII.
- `web/src/app/admin/page.tsx` lo presenta como texto truncable con `title`; el rol
  validado se establece primero y continúa controlando accesos. Si el email no está
  disponible, el encabezado indica `Usuario autenticado`.
- Se agregó contrato de regresión para identidad, orden de autorización, fallback y
  conservación de gates de rol.
- TypeScript: **PASS** (`npx tsc --noEmit`, Docker).
- ESLint: **PASS**, 0 errores y 9 warnings preexistentes en `HomeContent.tsx`.
- Contratos H3 enfocados: **11 PASS**, ejecutados directamente dentro de Docker;
  `pytest` no está instalado en el contenedor.
- Credential scan: **PASS**.
- `git diff --check`: **PASS**.
- Revisión `@security-auditor` del ciclo inicial: sin hallazgos restantes de ese
  delta; la nueva auditoría de dependencias indicada abajo mantiene el NO-GO global.

## NO-GO visual y transición

En la comprobación inicial el contenedor `studiamatch-dev` estaba `unhealthy` y
`/admin/` respondió HTTP 500 por manifests ausentes en `.next/dev`. Con aprobaciones
locales puntuales se reinició el contenedor, se actualizó Next y luego se reconstruyó
la imagen/reaprovisionó `studiamatch_node_modules` tras el gate de manifests. Estado
actual: `running/healthy`, reinicios 0; Next `16.3.8`, shadcn `4.21.1`; `/admin/login/`
y `/admin/` responden HTTP 200. La vista pública de login se inspeccionó en navegador
aislado a 1440×900 y 390×844: sin errores de consola ni overflow horizontal. No se
inició sesión, no se probó el header autenticado ni el editor con MFA. El build
estático local se ejecutó con aprobación separada; el detalle y su fallback quedan
registrados abajo.

La auditoría inicial de este ciclo reportó 49 hallazgos (13 HIGH, 28 moderate, 8 low,
0 critical); `npm audit --omit=dev` reportó 33 (13 HIGH, 12 moderate, 8 low,
0 critical). Esa lectura quedó supersedida por la remediación local documentada al
final de esta evidencia: los manifests y el contenedor Docker se actualizaron con
aprobación puntual, sin ejecutar `npm audit fix`.

El build estático aislado reportó compilación exitosa, generó 17/17 páginas y
finalizó la optimización. Como se usaron placeholders públicos y
`NEXT_PUBLIC_SUPABASE_URL=https://example.invalid`, `generateStaticParams` registró
`ENOTFOUND` y usó el fallback existente `/courses/pucp/estudios-generales`; no es
evidencia del catálogo real de Free. Se produjeron 124 archivos (2,371,859 bytes).
`web/out` previo fue restaurado y verificado idéntico (180 archivos, 2,461,143
bytes; SHA-256 de árbol
`0dab4eef13500534ba07c7ccae0eb475bf08a548574f6d45d8e83d60bbcbbe98`); la salida
del build se conservó en el directorio temporal aprobado, fuera del repo.

- **Expand:** obtener y mostrar el email de la sesión autenticada.
- **Compatibilidad:** no se altera `requireActiveAdmin`, RBAC, navegación de Admin,
  ni los permisos `admin`/`user`; el fallback evita dejar vacía la identidad.
- **Deploy:** no realizado. Requiere validación visual y autorización/deploy
  independientes.
- **Contract:** el distintivo de rol deja de ocupar el lugar de identidad en el
  encabezado; el rol permanece activo en los gates funcionales.
- **Rollback:** restaurar el distintivo `Admin`/`User` en el encabezado y retirar
  la lectura de email. No requiere revertir datos ni cambios de base de datos.

El cambio queda implementado localmente, pero no se declara GO de aceptación visual,
deploy ni cierre H3REQ1. La validación en Free confirma el estado de onboarding de
esta cuenta; no sustituye la UAT visual del editor nuevo ni los gates remotos
restantes de H3REQ1.

## Remediación local de dependencias — 2026-10-01

Se incorporaron 15 overrides transitivos acotados por rango/major en
`web/package.json` y `web/package-lock.json`. La matriz exacta quedó lockeada; las
versiones vulnerables previas de Babel, MCP SDK, Ajv 8, brace-expansion 5,
Browserslist, fast-uri, Hono, ip-address, js-yaml, update-browserslist-db,
`@hono/node-server`, `@humanfs/node`, `body-parser` y `qs` se reemplazaron por
resoluciones parcheadas compatibles con los rangos declarados. Ajv 6 y otras copias
de distinto major requeridas por ESLint se conservaron sin override global.

- `npm ci`: **PASS**, 625 paquetes instalados; 0 vulnerabilidades.
- `npm audit --include=dev`: **PASS**, 0 low/moderate/high/critical.
- `npm audit --omit=dev`: **PASS**, 0 low/moderate/high/critical.
- TypeScript: **PASS** (`tsc --noEmit --incremental false`, Docker).
- ESLint: **PASS**, 0 errores y 9 warnings preexistentes en `HomeContent.tsx`.
- Pruebas/contratos enfocados: **28 PASS**.
- Credential scan: **PASS**; `git diff --check`: **PASS**.
- Docker: `studiamatch-dev` `running/healthy`, reinicios 0; `/admin/login/` y
  `/admin/` HTTP 200; Next `16.3.8`, shadcn `4.21.1`.
- Marcador de dependencias: **PASS**, coincide con hashes de `package.json` y
  `package-lock.json`.
- `web/out`: **sin cambios**, 180 archivos, 2,461,143 bytes, SHA-256 del árbol
  `0dab4eef13500534ba07c7ccae0eb475bf08a548574f6d45d8e83d60bbcbbe98`.
- Seguridad: revisión read-only sin hallazgos confirmados con la evidencia disponible;
  queda riesgo de compatibilidad por overrides transitivos y ausencia de advisories
  no equivale a garantía absoluta de seguridad.

No se ejecutó build estático, ni hubo writes Supabase/Auth, cambios remotos, deploy,
push, PR, merge o promoción durante esta remediación. Se satisface el gate local de
auditoría de dependencias, pero el ciclo UI conserva `NO-GO` hasta probar el header
autenticado y el editor con MFA; H3REQ1 remoto sigue pendiente de sus gates y JIT
independientes.
