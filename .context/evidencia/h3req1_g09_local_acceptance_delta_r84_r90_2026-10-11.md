# G09 delta R84–R90 — preview y edición Admin — 2026-10-11

## Candidato y entorno

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`; WIP no staged preservado.
- Runtime Pages/workerd y runner: contenedor
  `h3req1-g09-uat-app-20261010-r12`, imagen local
  `studiamatch-h3req1:20261009-v3`; fixture PostgREST/Auth mock y PG17.11
  sintéticos R12 en red Docker interna.
- Chromium 1228 en Docker, headless y sin ventana visible. Sin datos/cuentas
  reales, sin egress de prueba y sin operaciones remotas.
- En R90, SHA-256 de `tests/h3_local_uat.mjs`:
  `d90e641ed662475c52fa1e369f475dddad4d2bd7c1e3ed3ba1e172a7455bd14f`;
  el archivo montado en R12 tuvo el mismo hash. Los tres fuentes funcionales
  de Admin/editor/renderer también coincidieron byte a byte entre el checkout
  y el contenedor; no hubo cambios de producto en este delta.

## Ejecuciones y diagnóstico

| Corte | Resultado | Hallazgo y tratamiento |
|---|---|---|
| R84 | H3-UAT-049, 3/3 viewports, 29 aserciones por viewport, PASS | Contenido de preview, fallback poblado y límites responsive. Capturas y vídeo desktop conservados. |
| R85 | 0/3, FAIL de test | `getByText('Inicio', exact:true)` coincidió con navegación y etiqueta de preview. Selector reemplazado por el ID del bloque. |
| R86 | 0/3, FAIL de test | Aserción no guardó input ni DOM observado. Rojo preservado. |
| R87 | 0/3, FAIL de test | Instrumentación confirmó input vacío y `textContent=InicioConsultar`; la lectura `innerText.includes` produjo el rojo. No se atribuye a producto. |
| R88 | 3/3, 31 aserciones por viewport, PASS | El fallback se consultó como texto exacto visible dentro del bloque. Capturas y vídeo desktop. |
| R89 | 0/3, FAIL de test | La aserción esperaba que el botón no existiera; implementación correcta lo deja presente y deshabilitado. Badge ausente y auditoría sin cambios. Rojo preservado. |
| R90 | 3/3, 32 aserciones por viewport, PASS | Aserción corregida: botón único presente/deshabilitado, sin badge, versión y auditoría sin cambios tras descartar el borrador. |

Las diferencias de R85/R86/R87/R89 son fallos del oráculo o sincronización del
test; la evidencia no demuestra defecto funcional del renderer ni del editor.
No se aumentaron reintentos: todos los cortes informan cero retries.

## Cobertura R90

El caso integrado H3-UAT-049 editó el curso sintético
`70000000-0000-0000-0000-000000000091`, comprobó procedencia de pipeline y
override, autor/fecha/antes/después en auditoría, rechazo de evidencia inválida
de disponibilidad, preview sin guardar con `Consultar` para fecha vacía,
ausencia de `null`/`undefined`, ajuste al viewport, descarte sin persistir y
botón de guardado deshabilitado; después guardó/publicó y leyó el mismo curso
en listado, detalle y comparación. Cada viewport pasó 32/32: 96 aserciones,
cero errores de consola, cero requests fallidos, tres capturas y un vídeo
desktop; no hubo retry.

Capturas de R90:

- Desktop: `h3req1_g09_uat_2026-10-10_r4/uat-editorial-preview-r90/H3-UAT-049-desktop.png`
  — SHA-256 `7450e29ad4906fc85de64632d1f3de1910b3e5e8d3502ac6dd04148c35d8e2c1`.
- Tablet: `h3req1_g09_uat_2026-10-10_r4/uat-editorial-preview-r90/H3-UAT-049-tablet.png`
  — SHA-256 `5d57f0949d9da89f2ca7696eec23c72ea10ffaf10f20638545c63947c0de6f50`.
- Móvil: `h3req1_g09_uat_2026-10-10_r4/uat-editorial-preview-r90/H3-UAT-049-mobile.png`
  — SHA-256 `48a952a824ce224678d310ee850af2c22cfca786cceb4e75e9a5f94ea304f9f3`.
- Vídeo desktop: `h3req1_g09_uat_2026-10-10_r4/uat-editorial-preview-r90/H3-UAT-049-desktop.webm`
  — SHA-256 `f4969163c91f99c2edc88fe4c28207130d41cc160f78c7aa2a4fb92c7d32cbe1`.
- Ejecuciones y manifest de captura: directorio R90, archivos
  `h3-expanded-uat-executions.json`, `h3-expanded-uat-manifest.json`,
  `h3-expanded-uat-matrix.json` y `h3-expanded-uat-artifact-hashes.json`.

## Efecto sobre G09

- G09-T09 / LOCAL-14: **completo** para preview Admin del caso sintético:
  campos poblados/parciales, fallback vacío, fit en tres viewports, descarte,
  save y recorrido público integrado.
- G09-T08 / LOCAL-13: avanza en descarte/no-op, procedencia y auditoría. Sigue
  **parcial** hasta cerrar la cobertura de tipos/campos y reconciliar los casos
  de conflicto/ownership sobre inputs actuales.
- No se cierra G09 ni cambian las métricas: tablero G01–G10 80% (8/10); cierre
  local G01–G09 88,89% (8/9). G10 remoto continúa separado.

