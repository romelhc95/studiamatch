# G09 UAT delta R123–R126 — membresías y comparador accesibles

Fecha: 2026-10-11, America/Lima. Candidato `feat/h3req1-sync-20261002`, HEAD
baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`; el estado del candidato
incluye el WIP completo, no solo HEAD.

## Entorno y alcance

- Pages/workerd Miniflare R121 sirvió el export normal R120-v5 desde el
  contenedor `h3req1-g09-uat-app-20261010-r12`, URL interna
  `http://127.0.0.1:3370/`; BFF/mock `:3371` y perímetro `:3373`.
- Playwright Chromium 1228 en modo headless, sin ventana. El runtime y PG17 R12
  se preservaron; las pruebas nuevas no escribieron DB.
- R124/R126 son casos UAT focales con una réplica de PostgREST en memoria para
  el ID sintético `70000000-0000-0000-0000-000000000091` (Analítica Aplicada),
  curso/institución/categoría fijados en el runner. El predicado registra cero
  orígenes externos. C03/R51 y R74 conservan la evidencia separada de integración
  con PG17/PostgREST real local.
- El manifest del export R120-v5 es
  `h3req1_g09_uat_2026-10-10_r4/a11y-build-r120/normal-out-r120-v5.sha256`,
  SHA-256 `04a580352a6620930a84ab542d7fdb1dd62dac13881334ba72488869288af9f9`.
  El producto no cambió durante R123–R126; solo evolucionó el runner UAT.

## Diagnósticos preservados

| Ejecución | Resultado | Evidencia y clasificación |
|---|---|---|
| R120/R121 | H3-UAT-068 previo; R121 falló al anunciar el error de invitación | Se conserva el fallo de selector genérico: encontró el route-announcer vacío además del mensaje. El selector se acotó a `main p[role=alert]`; no se atribuyó a producto. |
| R122 | H3-UAT-068, 3/3 y 9 assertions por viewport | PASS previo preservado, pero no incluye el medidor de contraste ni el segundo diálogo añadidos después. No se usa como resultado final del caso. |
| R123 | H3-UAT-068, 0/3, 0 retries | El medidor produjo ratio `0` para seis muestras. Chromium serializa los estilos de la app como CSS `lab(...)`; el parser del test aceptaba solo `rgb()/rgba()`. No hubo errores de consola ni requests fallidos. Es un defecto demostrado del parser de prueba, no de la interfaz. Evidencia en `uat-membership-a11y-r123/`. |
| R125 | H3-UAT-069, 0/3, 0 retries | El runtime apuntó al PostgREST sintético de build `127.0.0.1:3363`, que ya no estaba en ejecución (`ERR_CONNECTION_REFUSED`). Los tres requests de fixture fallaron antes de medir la pantalla; no se atribuye a producto. Se preserva en `uat-compare-a11y-r125/`. |

## Correcciones y resultados

- R124 corrigió el medidor para convertir CSS Color moderno a sRGB mediante
  Canvas y componer fondos alpha. Se añadieron probes de `lab(0 0 0)`,
  `lab(100 0 0)` y `rgb(0, 0, 0)`.
- R124 H3-UAT-068: PASS 3/3 viewports, 13/13 assertions cada uno, screenshots
  3/3, vídeo desktop 1/1, cero retries, cero errores de consola y requests.
  Verificó labels de correo/rol, autocompletado, siete encabezados, nombres de
  acciones con cuenta objetivo, texto de confirmación, ausencia de mutación al
  descartar dos confirmaciones, orden de teclado e invitación inválida anunciada.
  Contraste medido en seis muestras: 4.76:1 mínimo (encabezado de tabla),
  17.04:1 heading y 19.8:1 en las otras cuatro muestras. No es una auditoría
  WCAG global.
- R126 añadió una respuesta PostgREST sintética local por caso y bloqueó todo
  origen ajeno al runtime. H3-UAT-069: PASS 3/3 viewports, 6/6 assertions cada
  uno, screenshots 3/3, vídeo desktop 1/1, cero retries, cero errores y cero
  requests fallidos. Verificó heading/título del curso, nombre de acción,
  recorrido por Tab hasta el control, texto sin `null/undefined` y ausencia de
  overflow: desktop `1440/1440`, tablet `768/768`, móvil `390/390` (documento /
  viewport). El curso fue solo lectura y no se hizo click en retirar.

## Artefactos R124

- `h3req1_g09_uat_2026-10-10_r4/uat-membership-a11y-r124/H3-UAT-068-desktop.png`
  SHA-256 `d4a25f2e445bfc329c021ec9df4a671a20006a70a27af6550f2368b47177dcfc`.
- Tablet `46a8506b2a6b87a97e64ab62ad2e83f07705bbb1a852d7e81e6e37042ae54d2c`;
  móvil `46b2e811c7b9022cfcbbca59cda0e6856d7c4cf29014c46946cf6c386d5259a5`.
- Vídeo desktop SHA-256
  `8f1f88bb05e011f8914924d3f568623b322ef53d34de4da8c4401a72013ea4dd`.

## Artefactos R126

- `h3req1_g09_uat_2026-10-10_r4/uat-compare-a11y-r126/H3-UAT-069-desktop.png`
  SHA-256 `82c697dbaf2cddcd3bff464f00609250311b605d9e608468bd29e02a651b137a`.
- Tablet `108db30fdb4dc4f0fa2fb6147797a2809fe7d9a5a08e32779b92b0b2fd4b6b25`;
  móvil `48a201f727ba36fdcafbd330b480a3e3caa1198c6d7e4007fbfede276fae0b49`.
- Vídeo desktop SHA-256
  `6c5ea628328d35fd671295456d6ecf9109d488a57127363a0025424c960a581c`.

## G08 focal y límite del gate

Después del delta del runner, `node --check` y `H3_VALIDATE_ONLY=1` pasaron en
Docker; el catálogo valida 69 casos/207 ejecuciones posibles/0 retries. El
credential scanner y `git diff --check` pasaron. El catálogo completo no se
ejecutó como una sola corrida: el conciliado actual selecciona 207 ejecuciones
PASS compatibles entre corridas. G08 no gana otro punto; G09 sigue parcial por
LOCAL-01/03/07/08/09/16/17/19/20/23, revisión final, pilares y aceptación
integral pendientes.
