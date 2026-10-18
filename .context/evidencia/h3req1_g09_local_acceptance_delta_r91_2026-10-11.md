# G09 delta R91 — conflicto concurrente de edición — 2026-10-11

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Runner actual `tests/h3_local_uat.mjs`, SHA-256
  `d90e641ed662475c52fa1e369f475dddad4d2bd7c1e3ed3ba1e172a7455bd14f`, igual
  al archivo montado en R12 antes de ejecutar.
- App/runtime: Pages/workerd R12 + mock Auth/PostgREST + PG17.11 sintético;
  Chromium 1228 headless en Docker, sin ventana. Datos sintéticos, sin egress
  de prueba, sin acceso a cloud/secretos/recursos remotos.
- Ejecución: `H3-UAT-023` con retry 0; desktop, tablet y móvil pasan 8/8
  aserciones cada uno (24/24 total). Cero fallos y la rutina restaura el
  override original en el fixture tras cada viewport.
- Predicados PASS: las dos escrituras con la misma versión producen un único
  ganador y un conflicto de versión; sobreviven valor efectivo y procedencia
  tras reload; base del pipeline/fecha fuente visibles; cleanup verifica
  valor, override y fuente original.
- Capturas:
  - Desktop `h3req1_g09_uat_2026-10-10_r4/uat-editorial-editor-conflict-r91/H3-UAT-023-desktop.png`, SHA-256 `da151be6b73f51f41d2dbade8435cc35f68b885c2b9ab65856f443c15dfc8fd3`.
  - Tablet `h3req1_g09_uat_2026-10-10_r4/uat-editorial-editor-conflict-r91/H3-UAT-023-tablet.png`, SHA-256 `9fe27677c11b0a51cf3e753d1e7899a435591476dee05d5bca80773e073fb21b`.
  - Móvil `h3req1_g09_uat_2026-10-10_r4/uat-editorial-editor-conflict-r91/H3-UAT-023-mobile.png`, SHA-256 `3ec4bf38b5d6318df43b2d427ad5c84400796bf62cde95e6a461f52bf6d8907d`.
  - JSON de ejecución y manifest en el mismo directorio.
- Alcance: cierra conflicto optimista y restauración de procedencia para el
  registro sintético probado. No cierra la matriz de tipos de campo ni toda
  LOCAL-13; G09 continúa parcial y las métricas no cambian.

