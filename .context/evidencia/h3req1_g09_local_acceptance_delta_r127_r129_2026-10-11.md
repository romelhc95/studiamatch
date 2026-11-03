# G09 delta R127–R129 — accesibilidad de cola y membresías

Fecha: 2026-10-11, America/Lima. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El resultado identifica también el WIP; HEAD no representa por sí solo el candidato.

## Entorno y cambios

- Se reutilizó Pages/workerd R12 en `http://127.0.0.1:3370`, mock local `:3371` y PG17 sintético R12 existente. No se reinició ni recreó servicio o base.
- Chromium 1228 de Playwright corrió headless dentro de Docker; no se abrió ventana.
- Solo cambió el runner `tests/h3_local_uat.mjs`. No cambió código de producto ni se guardó estado de membresías. El archivo quedó montado igual en el contenedor; SHA-256 `23f3b23e9ed877c6b4b60a2db021dec22317fc667d477034b29a59fb8efd1f50`.
- Cada ejecución usó `H3_QUOTA_TEST_ISOLATION=true`; el runner restableció el fixture sintético por viewport. Cero llamadas externas observadas y cero errores de consola/requests en los PASS.

## R127 — fallo conservado del runner

H3-UAT-017 falló en desktop/tablet/móvil, exit 1, 0/3 PASS, cero retries. Los checks previos de etiqueta, foco, apertura del selector y diálogo por teclado pasaron. El predicado que falló exigía que la opción `Todos los estados` dejara de existir en el DOM después de Escape (`count() === 0`). La captura muestra el menú cerrado y el valor `Todos los estados` intacto; no se capturaron los operandos internos de la aserción, así que no se afirma si el nodo seguía en el DOM ni se atribuye un defecto de producto. Se corrigió el oráculo para esperar estado `hidden`, comprobar el valor seleccionado y dejar diagnosticado ese valor si falla.

Evidencia roja preservada en `h3req1_g09_uat_2026-10-10_r4/uat-queue-keyboard-r127/`:

- Matrix SHA-256 `c38b04f84a00cff47780819d6c93f515bce688c6fb664707224ef6bb5a78b323`.
- Executions SHA-256 `0aaafda28a4961c4e156d1e92d22ca6960c464079dc2cc4654e5de023f5bcede`.
- Captura desktop SHA-256 `7a83c1a4a60ff52f3e19026cabe908e0e62ce630cf21b1f961e0b9f5dec2cded`.

## R128 — cola Admin por teclado

`H3-UAT-017` se revalidó después de corregir el predicado del test. Exit 0; 3/3 viewports PASS, 26/26 assertions por viewport (78/78), tres PNG y un vídeo desktop; cero retries, errores de consola y requests fallidos. Se verificaron nombre accesible y foco del filtro editorial, apertura del menú por Enter, cierre por Escape manteniendo `Todos los estados`, foco del control Siguiente y cambio de página con Enter. El resto de la prueba renovó conteo, páginas sin solape, filtro compuesto y reset.

Artifacts en `h3req1_g09_uat_2026-10-10_r4/uat-queue-keyboard-r128/`:

- Matrix SHA-256 `9772b21e1a7a921a05dab28c6e0c0ff3f6599d63b827dac713cd697ac8360798`.
- Executions SHA-256 `14ccc42276ba2aadc8762d25938831887e43c3ee2c2d43700ad9758925f0ee90`.
- Capturas desktop/tablet/mobile: `50643ab0fb4b10383d5152adb7a8dd5f150a32f257b26d5c4c91bab7b6863043`, `443aae098ce2593aca4a622f7918a0d6e8d4acbd20ced23bc3e35b8819ad58e1`, `cb793d9603e1880b4b6b9775456310b1991bef8bc260dd2ef37463b05003c1f7`.
- Vídeo desktop SHA-256 `0cbbe3a85e05d907f47c2a2cc88e107fe98a41a8544164b1d1fb845701ca72c4`.

## R129 — confirmaciones, feedback y contraste

`H3-UAT-068` se revalidó tras cambiar los dos disparadores de confirmación a teclado. Exit 0; 3/3 viewports PASS, 15/15 assertions por viewport (45/45), tres PNG y un vídeo desktop; cero retries, errores de consola y requests fallidos. Enter enfoca y activa las acciones de estado/rol, sus confirmaciones identifican la cuenta sintética y, al descartarlas, no se emite RPC. El caso conserva feedback accesible para invitación local inválida, labels, tabla y muestras de contraste. Se midieron seis pares de texto/fondo por viewport, todos ≥4.5:1; el mínimo informado previamente es 4.76:1. Es muestreo de la pantalla de membresías, no auditoría WCAG global.

Artifacts en `h3req1_g09_uat_2026-10-10_r4/uat-membership-a11y-r129/`:

- Matrix SHA-256 `db8176de87f1431c2554c7b7508b2f60f89dbeaa94ddf05210218fd75f6d60c2`.
- Executions SHA-256 `4e89817b1759dcc8eb16ad233b10430cd340260f01ecd11753b2621fb70cccf2`.
- Capturas desktop/tablet/mobile: `2ca7b3a5652db3d06a82015744ee73fbb09549ea6525aa19eb342f86a667f251`, `c5fb57c1d5adb4c5079972ca293f6e353efec57f6cc6fc73a26dfcd3d65efe02`, `3ae893e1a3ef2bcfd55014cfadd6030f4095f05fb18d8dd64362c4d92752e105`.
- Vídeo desktop SHA-256 `0df4dd076b010736aeb10e06bb897699f4488b847f4f058ed734a03d200fee03`.

## Gate y siguientes dependencias

LOCAL-20 queda completa para las superficies actuales de la matriz al combinar R41 (tabla de membresías), R83/R128 (cola y filtros/paginación), R113 (editor), R126 (comparador) y R129 (acciones, confirmaciones, feedback y muestras de contraste). No se afirma cobertura de WCAG global. No cambia el estado ni los porcentajes de gates: G08 continúa completo; G09 continúa parcial por LOCAL-01/03/07/08/09/16/17/19/23 y revisión final. INV-008 ya quedó resuelto en R8 10/10, sin repetición. No hubo SQL nuevo, cambio de producto, commit, push, PR, merge, deploy ni operación remota.
