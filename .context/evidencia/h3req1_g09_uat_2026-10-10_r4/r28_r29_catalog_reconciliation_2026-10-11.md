# Conciliación catálogo visual R28 + R29 + R30 — 2026-10-11

## Resultado

El catálogo vigente de 63 casos en tres viewports queda cubierto con un PASS
por cada una de las 189 ejecuciones, conciliando dos corridas preservadas:

- R28 ejecutó 189 veces sin retries: 180 PASS y 9 FAIL; conserva sus 189
  capturas en [`uat-functional-full-r28`](uat-functional-full-r28/). Matriz
  SHA-256 `0dbc69650ae5f70ca4e62cd6e506128dc98796fb8f701a25d94ff6fa2d06ca9f`;
  manifiesto SHA-256 `9e5e0c2a9161988dfdfcad39d100f091742c72f319964056590b273a3b0e32f5`.
- R29 reejecutó solo los IDs afectados (007, 032 y 042 × tres viewports): 9/9
  PASS, cero retries y nueve capturas. Matriz SHA-256
  `3364d62a6264070dd8da86c52929932aad8ea6e0da1899703fcfa6403f239d44`;
  manifiesto SHA-256
  `2da359a355fe8d3a0f6808eef32b7d29d29068a5f351eee11aee2755f3effdc1`.
- R30 reejecutó H3-UAT-049 (tres viewports) tras añadir una assertion que
  comprueba el enlace “Solicitar Info” en comparación. Resultado 3/3 PASS, cero
  retries, tres PNG y vídeo. Matriz SHA-256
  `38c71b38a837742c6adad2df7bbbb230c55d081044f92fe35ce4f3bb7a36f71a`;
  manifiesto de artefactos SHA-256
  `2ef7191a8d16b65c94c21032a2548d10f20a74fcc8136b83fc82f8c37c49caeb`.
- Conciliación actual: se retienen 177 PASS de R28 que no corresponden a
  007/032/042/049; se usan los nueve PASS de R29 para 007/032/042 y los tres
  PASS de R30 para 049 con la assertion añadida. Son 189 resultados PASS
  seleccionados entre tres corridas, no una sola ejecución de 189 PASS. R28
  conserva sus nueve FAIL originales; no se cuentan como retries.

## Causas y cambios del ensayo

| Caso | Causa demostrada en R28 | Ajuste y resultado R29 |
|---|---|---|
| H3-UAT-007 | El selector eligió un curso sintético publicado con `missing_fields` vacío, así que el editor no ofrecía campos al usuario. | El runner ahora selecciona una fila con campos faltantes y exige que cada control editable pertenezca a ese conjunto. 3/3 PASS; solo cambió el runner. |
| H3-UAT-032 | El caso se ejecutó bajo el host `127.0.0.1`, distinto del host canónico del ensayo de cookie. | R29 usó `localhost`; el flujo de sesión AAL2/HttpOnly pasó en los tres viewports. No se reprodujo falla del producto. |
| H3-UAT-042 | La URL del perímetro apuntaba a `3332`, que sirve PostgREST, en vez del proxy de runtime. | R29 fijó el perímetro en `localhost:3333`; la ruta Admin del host público devolvió el 404 esperado en los tres viewports. No cambió el producto. |

El runner `tests/h3_local_uat.mjs` actual tiene SHA-256
`d6718f0883a47e1141a74401e080e2ccd2d43364591156adb5e604947c8f60b7`.
No se alteró código funcional del producto entre estas corridas; los cambios
son selección/inputs del ensayo y una assertion local de navegación. R29 y R30
no registran errores de consola ni requests fallidos.

## Aplicación, navegador y capturas

- App Pages/workerd: contenedor existente `h3req1-g09-uat-app-20261010-r12`,
  imagen `studiamatch-h3req1:20261009-v3`.
- Windows: [`http://127.0.0.1:3333/`](http://127.0.0.1:3333/), loopback por
  `h3req1-g09-localhost-proxy-r12`. Windows PowerShell recibió HTTP 200. El
  mismo proxy llega a la app y la PostgreSQL 17 sintética existentes; no se
  reiniciaron ni recrearon app o base.
- Servicios internos: Pages/workerd 3330; Auth mock 3331; PostgREST 3332;
  proxy/perímetro 3333. Chromium de Playwright corre headless dentro del
  contenedor app, sin ventana visible.
- Fixture: “Analítica Aplicada”, UUID
  `70000000-0000-0000-0000-000000000091`. El proxy no recibió secretos.
- [Captura R29 de edición de usuario en desktop](uat-functional-targeted-r29/H3-UAT-007-desktop.png).
  Las ocho capturas restantes están en el mismo directorio. [Captura R30 del
  comparador](uat-functional-targeted-r30/H3-UAT-049-desktop.png) y [vídeo R30
  del recorrido](uat-functional-targeted-r30/H3-UAT-049-desktop.webm) muestran el
  mismo curso y el nuevo chequeo del CTA interno. R28 también preserva [el vídeo
  anterior](uat-functional-full-r28/H3-UAT-049-desktop.webm) y sus 189 PNG;
  R28/R29/R30 preservan 201 PNG crudos.
- Se verificó HTTP desde Windows, no se abrió navegador Windows con GUI.
  Usa `127.0.0.1`: `localhost` resolvió a `::1`, que no tiene binding.

## Límite

La conciliación cubre el catálogo visual 63×3; **G09 sigue parcial** mientras
no se concilien y ejecuten las coberturas necesarias de las 23 áreas
`LOCAL-01..LOCAL-23`, incluido el recorrido real del pipeline. No suma puntos
G01–G10 ni declara GO.
