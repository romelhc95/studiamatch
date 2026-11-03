# H3REQ1 G09 delta R75 — conciliación de subcasos de sesión/MFA — 2026-10-11

## Candidato e inputs

- Checkout `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- El runner actual `tests/h3_admin_bff_mock_uat.mjs` tiene SHA-256
  `378f753d0de940ad5e023123d735d35429678e73498c458a5270b75da05dd3f6`, igual
  al valor del `source-inputs-r4.sha256` de G08.
- La evidencia primaria es
  `evidencia/h3req1_activity_cookie_session_binding_2026-10-10.md`: ejecución
  registrada en Docker local sobre imagen `studiamatch-h3req1:20261009-v3`,
  Node/Auth mock, contenedor efímero read-only, red disabled y sin credenciales.
  El resultado es 90 checks, con 6 rechazos de actividad, 1 rebind MFA, 4
  rechazos de origen y 4 rechazos de configuración de firma. La suite no se
  repitió porque el input coincide.

## Subcasos acreditados

- Actividad firmada para sesión A se rechaza con sesión Auth B; no renueva B.
- Actividad raw, timestamp alterado, firma inválida, edad >30 minutos y tiempo
  futuro se rechazan y limpian la cookie de actividad.
- La cookie de Auth lleva `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/` y
  `Max-Age=1800`; JWT, refresh token y `session_id` no se devuelven al cliente.
- Tras MFA, la cookie de actividad se vuelve a firmar para el `session_id` que
  Auth devuelve después de la rotación.
- Logout limpia la cookie Auth `.0`; esto no demuestra lectura/limpieza de una
  cadena con varios chunks.

## Límite y efecto

El test no abre navegador ni usa Auth real. No acredita expiración real de Auth
en browser, expiración/refresh concurrente extremo a extremo ni cookies Auth
multi-chunk. Por ello LOCAL-09 y G09-T05 siguen parciales. No cambió código ni
se ejecutó una nueva prueba; se corrige el mapeo de cobertura de la matriz y el
borrador PR, sin sumar porcentaje de gate.
