# H3REQ1 G09 — R41, membresías y recorrido por teclado — 2026-10-11

## Candidato y alcance

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama / baseline: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- El build normal R9 utilizó el conjunto allowlisted de 57 inputs, SHA-256
  `3894b6c5807677736c0c963b6ff8caed24dbda701489e5960dd2f9fc007293ab`; contiene
  el cambio Admin probado. El runner UAT fue validado por sintaxis y scanner
  acotado antes del ensayo. R10 renovó el build mock sobre el mismo conjunto.
- Alcance funcional: H3-UAT-040 en desktop, tablet y móvil. No se repitió el
  catálogo completo de 189 ejecuciones.

## Diagnóstico y corrección

R39 falló antes de probar la aplicación: el directorio de salida estática no
estaba dentro del montaje de evidencia que ve el contenedor, así que workerd
respondió 404. Se corrigió la ubicación del artefacto; este resultado se
conserva como fallo del arranque del ensayo, no como defecto de producto.

R40 sí llegó a la tabla de membresías y falló la aserción de desplazamiento
con teclado. La lectura instrumentada del mismo control mostró contenido
horizontal recortado (ancho de contenido 1327 px; área visible de 974/670/292
px en los viewports desktop/tablet/móvil) y `scrollLeft` no cambiaba con
ArrowRight aunque el contenedor tenía foco. Esto distinguió un defecto real de
la UI de un problema de sincronización o disponibilidad del servidor.

El ajuste mínimo en `web/src/app/admin/users/page.tsx` hace que la región
nombrada y enfocada desplace la tabla con ArrowLeft/ArrowRight, limitando el
movimiento al rango visible. La tabla declara encabezados por columna y mantiene
las celdas legibles sin ocultar los controles. No se alteraron roles, rutas,
MFA, BFF/HttpOnly ni el contrato SQL.

## Ejecución R41

- Resultado: exit 0; 1 caso lógico, 3/3 ejecuciones viewport PASS, 17/17
  assertions por ejecución (51 en total), cero retries.
- Browser: Playwright Chromium 1228 headless, dentro del contenedor de UAT.
  No se abrió una ventana interactiva. No se capturó video en esta pasada;
  hay captura PNG independiente para cada viewport.
- Runtime: Pages/workerd local en `http://localhost:3350`, BFF y mocks del
  contenedor UAT existente, conectado al PostgreSQL 17 sintético R12. El ensayo
  no usó cuentas reales, correo, secretos operativos ni servicios remotos.
- La aserción demostró que ArrowRight mueve `scrollLeft` de 0 a 353 px en
  desktop y ArrowLeft lo devuelve a 0; tablet y móvil pasaron las mismas
  comprobaciones con sus límites de viewport.
- El caso leyó el estado inicial del fixture, cambió el rol de un miembro
  sintético, desactivó y reactivó el miembro, probó el rechazo al intentar
  degradar al último admin activo, volvió a leer ambos miembros y comprobó que
  el intento rechazado no cambió sus valores. Su bloque `finally` restauró el
  rol/estado original del target sintético y una lectura posterior lo confirmó.
- Requests fallidos: 0. Errores de consola: 0. El log del runner termina con
  `PASS`, 3 viewport executions y 3 screenshots.

## Evidencia

- Resultado, conteos y hashes por viewport:
  `h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/`.
- Comando sanitizado:
  `h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41-command.log`.
- Exit final:
  `h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41-runner-exit.txt`.
- Verificación de 126/126 artefactos estáticos:
  `h3req1_g09_uat_2026-10-10_r4/site-out-r41-verify.log`.
- Capturas:
  - [desktop](h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/H3-UAT-040-desktop.png)
  - [tablet](h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/H3-UAT-040-tablet.png)
  - [móvil](h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/H3-UAT-040-mobile.png)

## Revisión y límites

La revisión del delta encontró que el manejador de teclado se limita a las dos
flechas horizontales, clampa en el rango de scroll y solo evita el
comportamiento por defecto cuando la tabla puede desplazarse. El test valida
movimiento observado, foco y retorno, no la mera presencia de un handler.
También cubre persistencia de cambios sintéticos y restauración en `finally`.
Las capturas finales son posteriores al recorrido y a la restauración.

R41 completa esta cobertura de teclado para la región de membresías y renueva
LOCAL-10 para rol/estado/último admin en su subalcance. No prueba carreras de
mutaciones de membresía ni completa el recorrido general de teclado,
diálogos/feedback o contraste. G09 sigue parcial.

## Acceso Windows al mismo runtime R41

Para revisar el mismo runtime/datos sin recrear la app ni PG17, se añadió un
forwarder interno y un sidecar HTTP acotado:

- URL: `http://localhost:3335/admin/login/` (Windows o WSL loopback). El
  contenedor sidecar `h3req1-g09-localhost-proxy-r41`, ID
  `2d579168976e07fe66799900b072b226ec72428e7dd6568f4c99835c3e2dd316`, publica
  únicamente `127.0.0.1:3335`. Imagen local
  `studiamatch-h3req1:20261009-v3`, sin pull; bind mount del script solo lectura,
  root filesystem read-only, sin capabilities y con 64 MiB/0.25 CPU.
- El sidecar usa las redes locales `h3req1-g09-localhost-access-r12` y
  `h3req1-g09-uat-20261010-r12`, y su único upstream es el forwarder interno
  del contenedor `h3req1-g09-uat-app-20261010-r12` en 3360. Ese proceso reenvía
  a R41 en `127.0.0.1:3350`; no cambia el bundle, el runtime o la base.
- App y datos: el mismo Pages/workerd R41 y el PostgreSQL 17 sintético
  `h3req1-g09-uat-pg17-20261010-r12`, imagen fijada por digest. H3-UAT-040
  usó 15 membresías sintéticas y exactamente dos admins activos. No se usaron
  datos/cuentas reales, `.env*`, correo ni secretos operativos.
- Pruebas por la publicación: `/`, `/admin/login/`, `/admin/users/` y el
  detalle estático de fixture `/courses/inst-a/curso-legacy-visible/` HTTP 200;
  lectura de origen cross-site HTTP 403 y escritura cross-site HTTP 403.
  El host está restringido a `localhost:3335`, el sidecar no reescribe Origin,
  y no permite métodos fuera de GET/HEAD/POST/PUT/PATCH/DELETE/OPTIONS.
- El detalle `/courses/ulima/analitica-aplicada-60000000/` devuelve 404 porque
  no está emitido en el snapshot R41; el build solo tiene el artefacto
  `/courses/inst-a/curso-legacy-visible/`. La lectura del output confirma que
  este es un desacople entre el fixture estático de R9 y el curso de PG17 R12,
  no un fallo del proxy. Por tanto, el acceso Windows acredita la superficie
  Admin/membresías y el catálogo estático del fixture del build, pero no prueba
  que el curso pipeline de PG17 esté en ese bundle. Esto permanece como gap de
  LOCAL-03/16 y no se arregló recreando el runtime. El endpoint antiguo
  `http://127.0.0.1:3333/` sigue en R12/puerto interno 3330; no fue reemplazado.
- Scripts sanitizados y revisables: `r41_windows_loopback_forwarder.mjs`
  (SHA-256 `629c57651484a06d8b74dbf4a1f9448dc7869a5001f6d16998d0f5127397b331`)
  y `r41_windows_loopback_sidecar.mjs` (SHA-256
  `4c04af718f70373108cf15e56d4b2111e83755c337f441154e2ed75d18f8448a`).
  El acceso vive mientras esos dos procesos/contenedores permanezcan activos;
  no se ejecutó limpieza de recursos previos.
