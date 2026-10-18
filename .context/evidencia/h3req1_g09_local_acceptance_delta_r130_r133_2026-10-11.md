# G09 delta R130–R133 — expiración Auth sintética en navegador

Fecha: 2026-10-11, America/Lima. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El runner modificado es WIP del candidato; no se identifica el candidato solo por HEAD.

## Entorno y alcance

- Se reutilizó Pages/workerd R12 (`h3req1-g09-uat-app-20261010-r12`, imagen `studiamatch-h3req1:20261009-v3`), mock Auth/PostgREST local y PG17 sintético existentes. No se recreó ni reinició el runtime o la base.
- URL de Pages/workerd desde el contenedor: `http://localhost:3330`; proxy del mock local: `http://localhost:3331`; perímetro local: `http://localhost:3333`.
- Chromium 1228 de Playwright ejecutó headless dentro de Docker; no se abrió ventana. La evidencia está en `h3req1_g09_uat_2026-10-10_r4/uat-r12/uat-auth-expiry-r133/`.
- Solo cambió `tests/h3_local_uat.mjs`; SHA-256 actual y montado en R12: `10029b7a1727c724d7aa460be61693ab148f14ef152f63f2800ca7a84efe6932`. No cambió BFF ni contrato de producto.
- El fixture es completamente sintético. Cada viewport inicia con reset del mock local; cero retries. No se usó Auth real, correo, cuentas reales, credenciales operativas, cloud, escrituras remotas ni despliegues.

## R130–R132 — resultados rojos preservados

| Ensayo | Resultado | Evidencia / observación |
|---|---|---|
| R130 | FAIL, 0/3 viewports, 3 capturas, 0 retries | El caso avanzó el reloj y luego abrió `/admin/`; las solicitudes protegidas de la página emitieron 401, que el runner contabilizó como consola. El predicado funcional de expiración sí llegó al final. Matrix SHA `d121c1b3ce33b2c758308d380c1c1dfa947f57bfb6d22d4cb872146304cd6a99`; executions SHA `e862f82aaa246a6028711c619af81a4016118d66bc0bb20f2cd3b6eee1e7815c`. |
| R131 | FAIL, 0/3 viewports, 3 capturas, 0 retries | Se quitó la navegación posterior, pero la cola Admin siguió montada: hubo 401 esperados y 502 en llamadas `POST /api/admin/rpc`. Matrix SHA `6d99b06d8407d1317c3b93c2b59c1b049617b2ff5c576b8e16bbe85607b83778`; executions SHA `33140c65a1bdc190ddd2fc9aea1f5a9201a93bfa38f8c87d732b5715d8cebfa9`. |
| R132 | FAIL, 0/3 viewports, 3 capturas, 0 retries | El runner añadió observabilidad allowlisted. Se vieron `rpc_failed` 502 en lecturas de la cola y 401 de autenticación en solicitudes protegidas; los 502 se registraron como iniciados antes del marcador del vencimiento, mientras la página Admin seguía activa. En móvil falló además el predicado de limpieza de cookies. Matrix SHA `17969803769c31e76150c2a75ce1861f8ac5abc0e53f1edb7ccc228b52afe97a`; executions SHA `8dea1ade38b06f115557f3949bc1c90e35ff84cb08b493284829ea109d2c39ee`. |

R130–R132 se conservan como ensayos fallidos del runner. La evidencia acota el error 502 al tráfico RPC de la cola Admin durante el caso combinado; no demuestra un defecto de Auth/BFF ni permite atribuir su causa interna. La suite vigente de cola R128 permanece PASS en sus inputs aplicables. La corrección fue aislar el probe de expiración fuera de esa superficie, no suprimir los errores ni cambiar timeouts.

## R133 — expiración de Auth mock aislada en browser

El caso existente `H3-UAT-034` ahora inicia sesión Admin sintética con MFA, navega a la ruta pública Privacidad para desmontar la cola Admin, adelanta 3.601 segundos en el reloj exclusivo del mock, y realiza tres lecturas simultáneas de `/api/admin/session`. Las tres observan `authenticated=false`; el contexto de Chromium confirma que no quedan cookies Auth/activity HttpOnly; una llamada RPC protegida devuelve 401 `unauthenticated`; no reaparecen tokens en storage/DOM.

Resultado: exit 0, **3/3 viewports PASS, 9/9 aserciones por viewport (27/27), 3 capturas, 1 vídeo desktop, cero retries, cero errores de consola y cero solicitudes fallidas**. No se modifica ni se prueba Auth remoto; el test acredita expiración del mock y fail-closed del BFF local. Una observación de RPC 200 no pudo ser decodificada por el capturador sanitizado en desktop; no afectó la respuesta ni las aserciones. No hubo 5xx iniciado después del límite de expiración.

Hashes:

- Runner `tests/h3_local_uat.mjs`: `10029b7a1727c724d7aa460be61693ab148f14ef152f63f2800ca7a84efe6932`.
- Matrix: `98d73a070aa362d8d8c565277eb8165540cc95ac951ed61e3ab53842cfec236d`.
- Executions: `b1f5a07326fd78798a2425269a817db5cf271862c02d17ed7a5698b82b1275b0`.
- Manifest: `ca89bd1be3293d5c3ccaf8c5f3006e9b7eca17604a1d9c1b2a95222a4bbb99d0`.
- PNG desktop/tablet/mobile: `e774936a2f8c544044ad319002d4092d01fd33a7878593bc63d9f2b281666877`, `5f3cecaece8ffe56b762d667db9860fd990479b6e2218a171072a6d484b029ab`, `f50d4fd64bbcfb98d5302be571d63e4b004615731d8d8dd64362c4d92752e105`.
- Vídeo desktop: `621a3690573b4c7c0b23cc725eca43597ffc00ba0295963a234cc22423cf65ba`.

La captura muestra la página pública usada para mantener el experimento separado de la cola Admin:

![H3-UAT-034 R133 desktop](/home/romel/src/studiamatch-h3req1-sync-20261002/.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-r12/uat-auth-expiry-r133/H3-UAT-034-desktop.png)

## Actualización del criterio

INV-008 continúa resuelto por causa reproducida del ciclo de rutas `password_pending`; R8 conserva onboarding 10/10, sin repetirlo. LOCAL-09 gana evidencia de expiración Auth local y limpieza HttpOnly. Sigue pendiente probar refresh concurrente end-to-end con Auth local sintético; por ello LOCAL-09/G09 permanecen parciales y el porcentaje no cambia.
