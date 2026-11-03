# H3REQ1 G09 delta R113–R116 — accesibilidad editorial y estados del catálogo — 2026-10-11

## Identidad y recursos

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Runner vigente después de R116: `tests/h3_local_uat.mjs`, SHA-256
  `5c52820b21a32428de59cd1581b51a79bdea1469ffdc154a1c28691fc5c51542`.
- Se reutilizó el runtime Pages/workerd activo
  `h3req1-g09-uat-app-20261010-r12`, escuchando dentro del contenedor en
  `127.0.0.1:3330`; reset proxy local `127.0.0.1:3331`; proxy de lectura
  Windows `127.0.0.1:3333`. No se recrearon app, PG17, red ni volúmenes.
- Playwright Chromium 1228 corrió headless dentro de Docker, sin ventana. R113
  y R116 usan fixtures/respuestas REST sintéticas con `page.route`; no usan Auth,
  datos reales ni escrituras PG17. El egress externo del navegador quedó
  interceptado y ambos casos comprobaron cero orígenes externos.
- El acceso Windows preexistente `http://127.0.0.1:3333/` sigue separado de los
  casos automatizados. No se abrieron secretos ni `.env*`.

## Fallos preservados y causas

| Corrida | Resultado | Causa / clasificación |
|---|---|---|
| R109 | FAIL de preflight, 0 viewports | El wrapper de fixture intentó restablecer el mock en el endpoint heredado incorrecto; no se ejecutó el caso. |
| R110 | FAIL, 0/3 PASS | Se usó `localhost:3000`, puerto que no es el listener Pages/workerd de R12; 3 capturas preservadas y conexión rechazada. |
| R111 | FAIL, 0/3 PASS | El oráculo de asociación accesible contó 12/13 porque el locator no encontró Modalidad; no se observó error de aplicación. |
| R112 | FAIL, 0/3 PASS | El nombre accesible del combobox incluye la selección y no coincidía con el nombre exacto; el mock MFA llegó a 429 porque el caso no restablecía fixture entre viewport. |
| R113 | PASS, ver detalle | Se corrigieron solo locators con prefijo y se usó reset sintético por viewport. |
| R114 | FAIL, 0/3 PASS | Tras la primera respuesta 200, HomeContent reutilizó su caché local no vacía por TTL de cinco minutos; el reload del estado vacío no emitió otra petición y venció `waitForResponse` a 10 s. No hubo incremento de timeout ni defecto de producto. |
| R115 | FAIL del runner, 0/3 PASS | Los cinco predicados funcionales pasaron en cada viewport, pero Next prefetch pidió `/courses/uat-sintetica/curso-uat-estados-publicos/`, ausente del export estático, generando 404 de consola. Era un slug de fixture inválido para este build. |
| R116 | PASS, ver detalle | Se invalida explícitamente la caché sintética entre estados y el slug reutiliza una ruta del export existente. Sin errores de consola/requests. |

Los artefactos de cada corrida permanecen en
`h3req1_g09_uat_2026-10-10_r4/uat-editor-accessibility-r109..r113/` y
`uat-catalog-states-r114..r116/`; no se reemplazaron salidas fallidas.

## R113 — H3-UAT-066, accesibilidad de edición

- Comando dentro de R12:

  ```text
  docker exec -w /app -e H3_BASE_URL=http://127.0.0.1:3330 \
    -e H3_MOCK_URL=http://127.0.0.1:3331 \
    -e H3_EVIDENCE_DIR=/evidence/uat-editor-accessibility-r113 \
    -e H3_REPO_ROOT=/app -e H3_UAT_CASES=H3-UAT-066 \
    -e H3_QUOTA_TEST_ISOLATION=false h3req1-g09-uat-app-20261010-r12 \
    /usr/bin/timeout --foreground --signal=TERM --kill-after=2s 180s \
    node /app/tests/h3_local_uat.mjs
  ```

- Exit 0: 1/1 caso, 3/3 viewports, 9/9 assertions, 3 PNG, 1 vídeo, cero
  retries, errores de consola o solicitudes fallidas.
- Aserciones por vista: 13 campos con nombre accesible; Tab avanza al siguiente
  control visible; Shift+Tab retorna al campo inicial. No se guardó ni mutó el
  fixture.
- Evidencia matriz SHA-256 `bb9fb063b33cc868d8852ea8a7ab16acb1f0c5627cb3794067f5b9f4c1b627d3`;
  ejecuciones SHA-256 `96b72c87075d92843fa68b997fd61965bcdbb642da03ffa9b33d4e30cb7b82e0`.
- Capturas desktop/tablet/mobile: `9fbb0450…94eb6e`,
  `1f87743a…9539724`, `6f6b8323…f3c80d8`; vídeo desktop SHA-256
  `50b5f48ac591b406b8cb9352c61f0db067d9e9b2f41cc0a023ec8f27060975ae`.

R113 fue ejecutado con el hash de runner
`65e0c6ef9e11ce8be86f429a11c8b80dcd9ae6756e932088b533479cdae8e79f`. Los
cambios posteriores se limitaron al nuevo caso H3-UAT-067 y a habilitar vídeo
para ese caso; la implementación/assertions de H3-UAT-066 no cambió. Por ello
R113 sigue aplicando a su caso, no a una supuesta corrida completa del archivo.

## R116 — H3-UAT-067, estados públicos

Antes de ejecutar, `H3_VALIDATE_ONLY=1` confirmó 1 caso, 3 viewports y cero
retries. La fuente del candidato y `/app/tests/h3_local_uat.mjs` coincidían en
SHA; `node --check`, `git diff --check` y el scanner de credenciales en Docker
terminaron exit 0.

Comando del caso:

```text
docker exec -w /app -e H3_BASE_URL=http://127.0.0.1:3330 \
  -e H3_MOCK_URL=http://127.0.0.1:3331 \
  -e H3_EVIDENCE_DIR=/evidence/uat-catalog-states-r116 \
  -e H3_REPO_ROOT=/app -e H3_UAT_CASES=H3-UAT-067 \
  -e H3_QUOTA_TEST_ISOLATION=false h3req1-g09-uat-app-20261010-r12 \
  /usr/bin/timeout --foreground --signal=TERM --kill-after=2s 180s \
  node /app/tests/h3_local_uat.mjs
```

Exit 0: 1/1 caso, 3/3 viewports, 15/15 assertions, tres capturas, vídeo
desktop, cero retries, errores de consola o solicitudes fallidas. Cada viewport
vio respuestas sintéticas `200 populated`, `200 empty`, `503 unavailable`; la
vista vacía muestra “Sin resultados”, el error conserva el catálogo estático,
y no hubo egress externo. No se mutó la base.

- Matriz SHA-256 `9c14a121bb34f2e8776822f390e2f501b224754855ae67cd4433e8c71c27dec3`;
  ejecuciones SHA-256 `c3697562e3c46b8b47ff890b85bd3391d12713757156d2f895cebf6b8d33df14`.
- Capturas desktop/tablet/mobile SHA-256:
  `847818cc35f39241131f39e3e478f0ebb6e165e1eadc4273ceb9a0d15d03003b`,
  `aa90cbf134c0092201e4b98ecc3fa82e651c5750e0af0af1293ab7bebceb1e2a`,
  `139aa8869a83aa60f2d9732b5c80990f5bc587fbdb073c221d9eadae08c0e540`.
- Vídeo desktop SHA-256
  `1727b1b2c54753190f0e4b3d64470e6ad685b7650415ebcb4609f75cecf06c78`.

## Lectura agregada PG17 para LOCAL-01

Se ejecutó una consulta acotada `BEGIN READ ONLY ... ROLLBACK` en
`h3_final_uat_g09_20261010_r12`, contenedor
`h3req1-g09-uat-pg17-20261010-r12`; solo devolvió agregados sintéticos:

- Cursos: 31; sin estado editorial: 0; filas en `courses_public_effective`: 16.
- Precio: 27 positivo, 2 cero, 2 NULL.
- Evidencia de disponibilidad observada: 15 dentro de 0–90 días; 16 ausentes.
- Membresías por rol/estado/activo: 2 admin ready activos; resto agrupado en
  user invited/password_pending/ready/revoked. No se seleccionaron emails ni IDs.
- La base también conserva los conteos previos de cola/auditoría/invitación R83.

Es una conciliación de estratos, no un cotejo de cada ID a través de detalle,
listing y artefacto. LOCAL-01 sigue parcial. El HTML de R116 muestra el contador
del lector local, pero este caso usa REST sintético interceptado y no prueba que
la respuesta del navegador provenga de esta consulta PG17.

## Gates, cambios y límites

- G08 permanece completo: pytest 335/4 skips, TypeScript, ESLint, scanner,
  writer scan, auditorías y builds mantienen inputs de producto/dependencias
  compatibles. Para el runner UAT modificado se renovaron `node --check`,
  scanner Docker, `git diff --check`, source match y validación estructural.
  No se ejecutaron tests live/credenciales/cloud.
- G09 avanza sin nuevo punto: LOCAL-02 añade vacío/error/fallback; LOCAL-20
  añade teclado/nombres del formulario; LOCAL-01 añade agregados. LOCAL-01,
  LOCAL-02, LOCAL-03 y LOCAL-20 continúan parciales. LOCAL-07/08, LOCAL-09,
  LOCAL-16/17/19 y revisión final siguen pendientes por su evidencia específica.
- INV-008 no se repitió. R8 ya reprodujo el ciclo de redirects
  `password_pending`, corrigió el guard de login y pasó onboarding sintético
  10/10 con cero retries.
- Matriz visual: 67 casos × 3 viewports = 201 ejecuciones PASS seleccionadas
  entre corridas compatibles, no una sola ejecución global. R113/R116 agregan
  6/6 viewports y 24/24 assertions; los FAIL R109–R115 quedan preservados y no
  cuentan como PASS.
- Métricas sin cambio: histórico G01–G10 = 8/10 = 80%; local G01–G09 =
  8/9 = 88.89%. G09 no cierra. No hubo commit, push, PR, merge, deploy,
  ejecución remota, operación de cuenta real ni cambio al checkout original.
