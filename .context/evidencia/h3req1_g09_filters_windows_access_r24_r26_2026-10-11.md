# Filtros públicos y acceso Windows — R23/R24 y diagnósticos D24–D26 — 2026-10-11

## Candidato y recursos preservados

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`; el estado completo incluye WIP.
- Acceso desde Windows: `http://127.0.0.1:3333/`. El proxy existente
  `h3req1-g09-localhost-proxy-r12` publica solo en `127.0.0.1:3333` y enruta
  al Pages/workerd que ya escucha en el contenedor
  `h3req1-g09-uat-app-20261010-r12`, puerto interno 3330. La ruta directa
  `/courses/ulima/analitica-aplicada-60000000/` entrega el mismo fixture.
- PostgreSQL sintético activo: `h3req1-g09-uat-pg17-20261010-r12`, base
  `h3_final_uat_g09_20261010_r12`. La vista pública muestra 16 programas y 5
  instituciones; curso `Analítica Aplicada`, ID
  `70000000-0000-0000-0000-000000000091`, slug
  `analitica-aplicada-60000000`.
- No se reiniciaron ni recrearon contenedores; las pruebas de filtros son GET
  y cambios locales del estado del navegador, sin writes PG17. El proxy no
  recibió `.env`, credenciales ni secretos. La verificación HTTP Windows
  PowerShell 200 está preservada en
  [acceso Windows anterior](h3req1_g09_uat_2026-10-10_r4/windows-local-access-r1.md).

## Resultado por ejecución

| Ejecución | Caso / viewport | Resultado | Observación |
|---|---|---|---|
| R23 | H3-UAT-059 desktop | FAIL histórico | 23,148 ms; timeout esperando `Analítica Aplicada` después de limpiar `q`. El screenshot final conserva el estado vacío y texto de búsqueda. Cero errores de consola y requests fallidos. |
| R23 | H3-UAT-059 tablet | FAIL histórico | 7,622 ms; aserción de restauración falsa después de quitar `q`. Cero errores de consola y requests fallidos. |
| R23 | H3-UAT-059 mobile | PASS | Búsqueda, empty state y reset pasaron. |
| R23 | H3-UAT-062 desktop/tablet/mobile | PASS | Comparador 3/3, selección única, límite, deep link, remover y limpiar. |
| R24 canónico | H3-UAT-059 + H3-UAT-060, tres viewports | PASS 6/6 | Primer resultado posterior a R23: filtros/búsqueda/reset 3/3 y bandas de precio/límites 3/3. Seis capturas, cero retries. Matriz generada `2026-10-11T04:19:50Z`. |
| R28 | H3-UAT-052/053/059/060/061/062, tres viewports | PASS 18/18 | La corrida completa fue 180/189 y falló solo en 007/032/042; los seis casos de filtros, bandas, orden/paginación y comparación pasaron. Las 189 capturas y el resultado global rojo permanecen preservados. |
| D24 | reset de búsqueda desktop/tablet/mobile | Diagnóstico | Tras limpiar, desktop/móvil mostraron 12 tarjetas en la primera lectura. Tablet tuvo 0 tarjetas a 0/50 ms y 12 tarjetas más el curso visible a 350/1200 ms; sin `pageerror`. Esta medición fue posterior y aislada; no reemplaza la corrida canónica R24. |
| D25 | reproducción focal H3-UAT-059, tres viewports | PASS 3/3 | Diagnóstico suplementario: 16 aserciones por viewport para filtros, búsqueda, URL, estado vacío y reset. Cero retries. No suma una corrida canónica. |
| D26 | reproducción con esperas canónicas, desktop/tablet | PASS 2/2 | Conservó la secuencia y las esperas de sincronización URL/`networkidle` del runner. Tras quitar `q`, el curso y las 12 tarjetas estuvieron listos en 98 ms desktop y 33 ms tablet. Cero retries. Diagnóstico suplementario. |

Las fallas R23 se conservan en `uat-functional-r23/`. La causa funcional quedó
identificada en el delta existente de `web/src/app/HomeContent.tsx`: el botón
“Limpiar todo” vaciaba `searchTerm`, pero dejaba `searchInput` intacto. El
efecto debounce de 300 ms toma `searchInput` como fuente y podía volver a
aplicar el término viejo mientras el URL ya se había limpiado. R23 registra
precisamente el candidato ausente y el texto anterior aún en el campo. El delta
posterior añadió `setSearchInput("")` al mismo handler; la modificación tiene
mtime 23:18 de Lima, después de R23 (23:16) y antes de R24 (23:19). R24 pasa
los seis viewports y su bundle cargó un chunk adicional. Es la corrección
demostrada; no se hizo otro cambio funcional en esta continuación. D25/D26
son corroboraciones posteriores, se preservan como diagnósticos y no se cuentan
como sustituto ni como gates adicionales.

## Servidor y navegador

- R24, R28, D25 y D26: Pages/workerd y fixture del mismo contenedor de app. Playwright
  Chromium 1228 se ejecutó headless desde el contenedor UAT, usando el binario
  local ya instalado `/ms-playwright/chromium-1228/chrome-linux64/chrome`.
  No hubo ventana visible.
- Dos probes previos no iniciaron navegador: el primer directorio de evidencia
  no existía dentro del contenedor; el segundo probe dejó que Playwright 1.63
  buscara Chromium 1243, pero el contenedor conserva el binario 1228 fijado por
  el runner canónico. Se corrigió ruta y ejecutó el diagnóstico; no hubo
  instalación ni cambio de imagen.
- La URL se dejó abierta en el panel browser de Codex (estado `queued` para el
  hilo) y sigue disponible para abrir manualmente desde el navegador Windows.
  `127.0.0.1` es necesario; `localhost` resuelve a `::1` y no tiene binding.

## Capturas, vídeo e integridad

- [R24 desktop](uat-functional-diagnostic-r24/H3-UAT-059-desktop.png),
  [tablet](uat-functional-diagnostic-r24/H3-UAT-059-tablet.png) y
  [móvil](uat-functional-diagnostic-r24/H3-UAT-059-mobile.png) muestran el
  catálogo restaurado después del reset.
- R25: [desktop](uat-functional-r25/H3-UAT-059-desktop.png),
  [tablet](uat-functional-r25/H3-UAT-059-tablet.png),
  [móvil](uat-functional-r25/H3-UAT-059-mobile.png) y
  [vídeo desktop del recorrido](uat-functional-r25/H3-UAT-059-desktop.webm).
- R24 canónico preserva su propio conjunto de seis capturas en
  `uat-functional-r24/` para H3-UAT-059 y H3-UAT-060.
- [R24 canónico H3-UAT-059 desktop](uat-functional-r24/H3-UAT-059-desktop.png),
  [tablet](uat-functional-r24/H3-UAT-059-tablet.png) y
  [móvil](uat-functional-r24/H3-UAT-059-mobile.png); H3-UAT-060 tiene un set
  separado de tres capturas en el mismo directorio.
- El vídeo y las capturas D25 cubren la navegación de filtros y el estado
  posterior al reset. R23 mantiene las seis capturas originales del caso 059
  y 062, incluidas las dos vistas rojas.

SHA-256 de capturas/vídeo R25:

| Artefacto | SHA-256 |
|---|---|
| `H3-UAT-059-desktop.png` | `82d2381cabaf09deb42386bbb240dd53336b950f3323726dc40c0d37b16da6d3` |
| `H3-UAT-059-tablet.png` | `57c491f3ec1e1fab0ded2fe5149f2c89434f7fdebdf9e1f83071d13829b40c0f` |
| `H3-UAT-059-mobile.png` | `0b7f1eb5352805687ae0d7cf6f1a13f62381d18a572a7127a123c036174f7790` |
| `H3-UAT-059-desktop.webm` | `51d55951a3aba9276491bc7d5c42a8d36a2af21a12ec6a80bc39033dbfc8e9f0` |

R33 revalidó el filtro combinado H3-UAT-053 sobre el mismo runtime disponible
desde Windows: tres viewports PASS, nueve aserciones, tres capturas y cero
retries. El acceso, R31/R32 previos y sus causas están en
`h3req1_g09_windows_access_combined_filters_r31_r33_2026-10-11.md`.

G09 continúa parcial: R24 acredita filtro/búsqueda/reset y bandas de precio en
sus seis ejecuciones; R28 pasa los filtros combinados, precio mínimo, orden,
paginación y comparación en sus 18 ejecuciones seleccionadas. Quedan las demás
coberturas de las 23 áreas. Los diagnósticos D25/D26 no cambian porcentajes.
