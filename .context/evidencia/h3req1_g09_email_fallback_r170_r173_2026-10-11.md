# UAT del encabezado autenticado y fallback — R170–R173 — 2026-10-11

Ruta canónica del informe R170–R173; se conserva el archivo anterior con
nombre R170–R171 como antecedente, sin alterar sus resultados.

## Alcance e identidad

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD base
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`; la fuente probada fue el WIP
  cuyo runner está fijado en `run-inputs-r171.sha256`.
- App conservada: `h3req1-g09-onboarding-app-20261011-r8`, contenedor
  `9921c96524bf6b97e567248a77198651caf1199b143d9af1ed2327b6032fab07`,
  imagen `studiamatch-h3req1:20261009-v3`, ID
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- Servidor: Pages/workerd normal del artefacto R146 mediante el helper fijado;
  puertos 3380/3381/3383 enlazados solo a `127.0.0.1`. Health de `/admin/login/`
  HTTP 200 antes de ambas corridas. No se recrearon app, PostgreSQL ni redes.
- Navegador: Playwright Chromium 1228, headless, sin ventana. Datos: usuarios
  sintéticos del fixture Auth/PostgREST y PostgreSQL 17.11 local. No se usaron
  cuentas, correos, tokens ni servicios operativos; no se guardaron valores de
  variables de entorno.

## R170 — fallo del runner preservado

Exit 1; seis viewports ejecutados, seis PNG conservados, cero retries. Las
aserciones de email autenticado y capacidades de rol pasaron; el timeout ocurre
al esperar `Usuario autenticado`. El diagnóstico sanitizado registra HTTP 403
en el GET local `/api/admin/session` inmediatamente después de instalar la
interceptación de Playwright. Por tanto, la evidencia no demuestra un fallo de
la UI: el test usó `route.fetch()` desde la interceptación de un endpoint BFF
autenticado y no obtuvo la sesión para construir la variante sintética.

Hipótesis comprobable: el transporte de la petición interceptada de Playwright
no preserva el contexto del GET BFF como lo hace `fetch` del propio navegador.
Se cambió únicamente el fixture del test: primero toma y valida la sesión
autenticada mediante el origen del navegador; luego responde localmente con la
misma sesión y `email: null`. No realiza un segundo GET BFF bajo interceptación.
El rojo completo se preserva en `run-r7/inputs-r170/failed-r170/`.

## R171 — revalidación tras la corrección

Resultado PASS, exit 0: H3-UAT-002 y H3-UAT-003, tres viewports cada uno,
6/6 ejecuciones, 30/30 assertions, 6/6 capturas, cero retries y cero errores
de captura de vídeo. Los dos casos verifican email autenticado y, luego, el
fallback sin email; el rol admin conserva el enlace de membresías y el rol user
continúa sin acceso a esa capacidad. Matrix, executions, manifest, hash list,
summary y capturas están en `run-r7/inputs-r170/r171/`.

La prueba confirma que el fallo R170 era de la sincronización/interceptación del
test. El runtime, contenedor, imagen, helper y fixture permanecieron iguales.
No se observó una causa ambiental ni un defecto de producto en este ensayo.

Comandos del delta: dentro de `studiamatch-dev`,
`/app/scripts/security/scan_credentials.sh /app/tests/h3_local_uat.mjs` y
`node --check /app/tests/h3_local_uat.mjs` (ambos PASS); desde WSL se ejecutó
una vez `bash .context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/inputs-r170/run_h3_uat002_003_r171.sh`
(exit 0). El runner fija contenedor, imagen, helper, artifact R146, puertos
loopback, selección de casos y timeout 240 s; no contiene retries.

Inputs SHA-256 (incluidos en `run-inputs-r171.sha256`):

- `tests/h3_local_uat.mjs`: `7690ea33b386f2b13c930f50ba31446dce792e8947619c05fb8d5c1dc7d20519`.
- Wrapper R171: `28697b1e0182d4b5fef323f319ee44aa1c219452eb00e75ebd8a665634e5fc49`.
- Helper Pages/workerd R146: `8a0f7c7cccb2fbbfd3e8e9eb6ff26840b88df0d4ff75493872944a9cc590ff66`.
- Manifest/hash list del artefacto R146 y verificaciones R162 de 201 archivos
  del build y 61 fuentes actuales, fijados por el archivo de inputs.

Resumen R171 SHA-256 `b6e49a4561e7d9a3a96d978c08bcade8f4b6d3480960d3cb66248377122c0aed`;
matriz SHA-256 `2cddf6ee6d180d7578ef1cfd061b9ddc213b60a224bf86860f60161c7880f576`;
lista de hashes de artefactos SHA-256
`d5a8f1dd078e313680189e348e0fe153237c82412d83170e4d87c4e6e12bf6c5`.

## R172/R173 — cierre de revisión del harness

R172 mantuvo el mismo resultado funcional: 2/2 casos, 6/6 viewports, 36/36
aserciones, seis capturas y cero retries. La revisión de seguridad confirmó el
aislamiento a loopback y encontró un LOW no bloqueante: el helper permitía una
query string en la ruta interceptada. R172 se conserva como evidencia previa,
pero no representa el código actual.

Se corrigió solo el guard del test para aceptar GET al origen loopback exacto,
path `/api/admin/session` y `search` vacío; otros métodos, orígenes, paths y
query strings se abortan. Sobre el nuevo hash, Docker credential scan y
`node --check` pasaron. R173 ejecutó una vez el mismo par de casos: exit 0,
2/2 casos, 6/6 viewports, 36/36 aserciones, seis capturas y cero retries.
No se cambió el runtime, el producto ni el fixture entre R172/R173.

R173 usa el Pages/workerd normal R146, puertos `127.0.0.1:3380/3381/3383`,
Chromium 1228 headless dentro del contenedor Docker fijado y el fixture local
Auth/PostgREST con PostgreSQL 17.11 desechable. La salida no contiene tokens ni
datos de cuentas reales. El wrapper, resumen, matriz, ejecuciones, seis PNG y
hashes están en `run-r7/inputs-r170/r173/`, `run-inputs-r173.sha256` y
`run-artifacts-r173.sha256`.

Revisión de seguridad del helper actualizado (SHA
`04d00dc068994cfc9836132d9e5b1d3ed0676a9ad5fb2404cbb5f425133dd60f`): LOW
resuelto, sin HIGH/MEDIUM ni otros hallazgos en este alcance. Dictamen y límites
en [revisión R173](h3req1_g09_security_review_r173_2026-10-11.md). R170 y R171
permanecen como antecedentes con su propio resultado; R170 no se cuenta como
PASS ni se reetiqueta como retry.

## INV-008

INV-008 es un defecto funcional distinto y ya está resuelto: una sesión de
invitación en `password_pending` quedaba atrapada entre el guard de Admin y el
redirect de login. R8 reprodujo y corrigió el ciclo, con onboarding sintético
10/10 y cero retries; R146 renovó el onboarding 10/10. La causa, cambio y
límites están en [diagnóstico R8](h3req1_g09_onboarding_r8_inv008_topology_2026-10-11.md).
R170 no fue una repetición de INV-008 ni cambia ese dictamen.

## Límites

El helper R146 sirve un artefacto normal ya verificado y enlaza a fixtures
sintéticos; esta prueba no acredita Auth/PostgREST cloud, proveedores de correo,
Production/Certification, CI remoto ni despliegue. El vídeo no se grabó en la
pasada R171; se conservan las seis capturas individuales y el onboarding R8
conserva vídeo del recorrido principal.
