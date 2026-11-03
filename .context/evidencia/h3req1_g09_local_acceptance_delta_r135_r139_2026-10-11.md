# G09 delta R135–R139 — cuota integrada y refresh concurrente — 2026-10-11

## Candidato y ejecución

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- El runner actual `tests/h3_local_uat.mjs` tiene SHA-256
  `9382b45c79e2d0a7a9f546ce58a09fbefd4b79b533ba0e17dae7a4c83b1e06f4`;
  WSL, `studiamatch-dev` y el runtime UAT R12 devolvieron el mismo digest.
- Servidor: Pages/workerd R12 `h3req1-g09-uat-app-20261010-r12`, imagen
  `studiamatch-h3req1:20261009-v3`, integrado con Auth/PostgREST mock y PG17.11
  sintético R12. Chromium 1228 ejecutó Playwright headless en Docker; no abrió
  ventana. El fixture fue local y no usó cuentas/correo reales ni egress cloud.

## R135 — límite de cuota BFF

H3-UAT-070 corrió una vez por viewport y pasó 3/3 ejecuciones, 8/8 aserciones
por viewport (24/24), tres capturas, 0 errores de consola/requests y 0 retries.
Treinta writes sintéticos firmados fueron rechazados antes de mutación y
contaron contra el límite integrado; la solicitud 31 devolvió `429`
`rate_limited` con `Retry-After: 60`. El estado editorial, overrides, versión y
auditoría quedaron iguales; la sesión HttpOnly/AAL2 siguió activa.

Una ejecución inicial R134 terminó 0/3 porque el oráculo esperaba el código
interno `quota_rate_limited`, aunque la respuesta de contrato BFF era
`rate_limited`; también clasificaba el 429 esperado como error. Se conservó y
se corrigió únicamente el oráculo del runner. R135 es la revalidación. No hubo
cambio de producto.

- Matriz SHA-256: `6eb67bc8b179617051e45edf047c8ef9d2d90c3b5389ae4db9a1c9b0ae519bb3`.
- Ejecuciones SHA-256: `7f67cde306388893312bf39311ad10a21a5132c62d86836fefc4036711a966ec`.
- Hashes de artefactos SHA-256: `c5c979fc5c3e92b219162ead540a7bf5c64db67c58f8d2ba2ac0ac2d3e1b4077`.
- Manifiesto SHA-256: `9543147a40620090398c5a3e1e6aeeb76487f8095036d01a77458b0ab1479824`.
- Artefactos: `uat-integrated-quota-r135/`.

## R136–R139 — concurrencia y rotación Auth sintéticas

R136/R137 son fallos preservados del oráculo: Playwright no expuso
`Set-Cookie` en el mapa normalizado de headers, y el endpoint BFF no expone el
`sessionId` interno en su resumen público. Ambos comportamientos son
intencionales; no se cambió producto. El test ahora observa la expiración
renovada mediante la sesión pública y exige que no se filtre el identificador.

R139 añadió una comprobación de cobertura a H3-UAT-034: la cookie HttpOnly
sintética se coloca en la ventana de refresh; tres lecturas BFF simultáneas
deben seguir autenticadas con AAL2. El test calcula SHA-256 de los tokens solo
en memoria y emite únicamente booleanos. El par access/refresh cambia, el
vencimiento avanza y la cookie mantiene HttpOnly/Secure. Después, el reloj Auth
del mock avanza 3601 segundos: tres lecturas rechazan la sesión, limpian cookies
Auth/actividad y un RPC protegido devuelve 401.

R139 pasó 3/3 viewports y 14/14 aserciones por viewport (42/42), tres capturas,
un vídeo desktop, 0 errores de consola/requests y 0 retries. La prueba es de
integración local con Auth mock; no representa una llamada a Supabase remoto ni
una garantía del comportamiento del proveedor fuera de este fixture.

- Preflight en R12: `node --check` y `H3_VALIDATE_ONLY=1` PASS; 1 caso / 3
  viewports / 0 retries. Scanner focal PASS en `studiamatch-dev`.
- El primer intento de `H3_VALIDATE_ONLY` en `studiamatch-dev` falló antes de
  validar la estructura porque allí no está instalado Playwright; se ejecutó
  el preflight correcto en R12, que sí es el runtime fijado. La fuente montada
  coincidió por SHA. No se instaló nada.
- Matriz SHA-256: `e69932e78190ef13bc4212687d42c2017c2b31210bae5ed4cf3034755572616c`.
- Ejecuciones SHA-256: `2dec923c3b16c0679c8b72ed3b43e918021f58d6f8d0cb0934b780bbcfb1720f`.
- Hashes de artefactos SHA-256: `b2a7e9abebc679fade7d87378c7db40fc09df7ae07a77b3a63e10c88e7609066`.
- Manifiesto SHA-256: `ca89bd1be3293d5c3ccaf8c5f3006e9b7eca17604a1d9c1b2a95222a4bbb99d0`.
- Capturas: [desktop](h3req1_g09_uat_2026-10-10_r4/uat-auth-refresh-r139/H3-UAT-034-desktop.png),
  [tablet](h3req1_g09_uat_2026-10-10_r4/uat-auth-refresh-r139/H3-UAT-034-tablet.png),
  [mobile](h3req1_g09_uat_2026-10-10_r4/uat-auth-refresh-r139/H3-UAT-034-mobile.png).
- Vídeo: [refresh Auth desktop](h3req1_g09_uat_2026-10-10_r4/uat-auth-refresh-r139/H3-UAT-034-desktop.webm).
- Artefactos estructurados: `uat-auth-refresh-r139/`.

## Conciliación por área

- LOCAL-09: el subcaso pendiente de refresh concurrente ahora pasa en el Auth
  mock con rotación observable del par de tokens, AAL2 y expiración posterior.
  Se puede cerrar para el contrato sintético local; no implica validación Auth
  remota.
- LOCAL-17: el límite de cuota integrado ahora está probado con estado/auditoría
  intactos. Seguridad local cubierta por G08 + R51 + R135; la revisión final del
  candidato se sigue registrando en LOCAL-23.
- LOCAL-19: refresh, expiración, limpieza de cookies, RPC denegado y rechazo de
  cuota preservando datos se acreditan; siguen parciales los fallos adicionales
  de Auth/DB/Edge, respuestas malformed y recuperación integrada por etapa.
- INV-008: no se repitió. La causa y corrección del ciclo `password_pending` y
  el onboarding R8 10/10 siguen vigentes; ver
  [evidencia R8](h3req1_g09_onboarding_r8_inv008_topology_2026-10-11.md).

## Recursos y límites

R12, PG17 sintético R12 y `studiamatch-dev` se preservaron. Solo hubo cambios
al runner UAT y a esta evidencia; no cambiaron funciones de producto. No se
hicieron commits, push, PR, merge, deploy, writes remotos, uso de secretos o
cuentas reales, limpieza de recursos ni repetición de suites intactas.

`git diff --check` debe volver a verificarse después de este delta documental.
G08 permanece completo por evidencia previa compatible y las verificaciones
focales del runner. G09 sigue parcial por LOCAL-01/03/07/08/16/19/23; los
resultados de R135/R139 no cambian por sí solos el porcentaje de gates.
