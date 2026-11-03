# Activity cookie ligada a sesión Auth — 2026-10-10

## Defecto reproducido

La cookie `__Host-studiamatch-admin-activity` tenía una HMAC válida sobre la hora,
pero no sobre la sesión Supabase que la acompañaba. Una actividad emitida para la
sesión A podía renovarse junto con una cookie Auth de la sesión B.

La prueba focal se ejecutó primero contra el código anterior dentro de Docker con
checkout y dependencias montados read-only, `--network=none`, usuario no-root y
sin credenciales. Resultado RED: exit 1; assertion
`an activity cookie issued for a different Auth session must not renew this session`,
actual `true`, esperado `false`.

## Corrección

El BFF valida primero el usuario mediante `auth.getUser()`, confirma que el usuario
coincide con la sesión del cliente y extrae del JWT ya validado el claim
`session_id`. La HMAC ahora firma dominio, `session_id` y timestamp; la cookie sigue
exponiendo únicamente `timestamp.signature`. La lectura falla cerrada si falta el
claim o no tiene formato UUID. El callback, login, lectura de sesión y rutas
protegidas usan la misma vinculación. El ID no se devuelve al navegador.

El mock Auth emite un ID sintético por sesión y conserva el mismo ID durante refresh.
Los fixtures integrados incorporan el claim sin cambiar identidad/rol. No se cambió
el flujo BFF/HttpOnly, gateway, cuotas, MFA ni cookies Auth.

## Validación posterior

Runner focal: `tests/h3_admin_bff_mock_uat.mjs`, en imagen local
`studiamatch-h3req1:20261009-v3`, contenedor efímero read-only, red deshabilitada,
fuentes/dependencias read-only, usuario no-root. Exit 0:

```text
{"result":"PASS","checks":87,"quotaCases":10,"activityCookieRejectCases":6,"sessionOriginRejectCases":4,"signingKeyConfigRejectCases":4}
```

La suite cubre cookie cruda, timestamp/firma inválidos, expiración/futuro,
reuso entre sesiones, CSRF de lectura, colisiones/configuración de llaves y
no exposición de JWT, refresh token, llave o `session_id`.

Esta prueba focal no sustituye typecheck, lint, snapshot, healthz, C03 integrado,
revisión independiente ni aceptación final. R46 y pruebas visuales previas quedan
históricas para los inputs BFF alterados y deben renovarse por impacto antes del
cierre local. El checkout original, recursos operativos y servicios remotos no se
usaron.

## Revalidación posterior del cambio de sesión — 2026-10-10

La revisión independiente identificó una condición adicional: la respuesta MFA
podía rotar el `session_id` de Auth. El callback ahora vuelve a autenticar la
sesión resultante, firma la actividad para ese ID y reemplaza cualquier cookie de
actividad anterior en la respuesta. El mock preserva el ID durante refresh y MFA
de nivel AAL2. La revisión independiente posterior confirmó ese ajuste y no
reportó bloqueantes estáticos; el alcance fue estático, sin runtime adicional.

La última revisión de implementación también serializó `getUser()` y
`getSession()` para evitar que dos llamadas concurrentes compitieran por una
renovación de sesión. Con los inputs actuales, en Docker read-only, sin red ni
credenciales:

- `tests/h3_admin_bff_mock_uat.mjs`: PASS, 90 checks, 10 casos de cuota, 6 rechazos
  de cookie de actividad, 1 rebind MFA y 4 casos de origen de sesión.
- `tests/test_h3_admin_queue_ux_contract.py`: 13/13 PASS.
- `mock-server/server.js`, `tests/h3req1_c03_integrated_runtime.mjs` y
  `tests/h3_admin_bff_mock_uat.mjs`: `node --check` PASS, exit 0.
- `npm run lint`: exit 0, cero errores y nueve warnings preexistentes en
  `HomeContent.tsx` (7 dependencias de `useMemo`, 2 variables `_e`).
- `next typegen`: PASS.
- TypeScript `tsc --noEmit --incremental false`: PASS, contenedor limitado a 4 GiB,
  `NODE_OPTIONS=--max-old-space-size=3072`, heap separado del repo y sin `.env*`.
- `git diff --check`: PASS.

Las tres suites G03 de workflow protegido, scanner y scope guard siguen siendo
reutilizables: su contenido e inputs no cambiaron y el resultado anterior fue
13 passed más dos regresiones shell PASS. ShellCheck y actionlint también se
reutilizan solo con sus listas de inputs y hashes coincidentes.

El resultado de autenticación 90/90 es local y sintético; no acredita bindings
remotos ni cambia la aceptación de sesión existente. Al cambiar BFF y sus
fixtures, S14/R46 y UAT visual anterior no representan el candidato actual.
Quedan por renovar snapshot completo, Pages/workerd `healthz`, C03 integrado,
checks finales afectados y UAT visual de 144 casos; onboarding sintético 10/10
permanece preservable mientras se confirme que sus inputs no cambiaron. La
rotación local de la firma hace que cookies de actividad anteriores fallen
cerradas y requieran reautenticación durante compatibilidad; no se ejecutó
deploy/contracción remota. El rollback local es volver al snapshot/candidato
anterior preservado, sin eliminar R46 ni recursos remotos.
