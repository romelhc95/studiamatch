# H3REQ1 aceptación local — delta R107–R108 — 2026-10-11

## Candidato y entorno

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD baseline: `feat/h3req1-sync-20261002` /
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP al comienzo y cierre: 60 entradas tracked modificadas, 812 entradas
  untracked visibles y 0 staged. Se conservaron ambos checkouts y el WIP.
- R107 usó `tests/h3_local_uat.mjs` SHA-256
  `db58514da658c269b9e3c8efab174e51f00f60beffe01221e1848459b0035d97`.
  R108 usó SHA-256
  `51c5d7da79d444b2692c6e2664fa411a15ccfc014daabd769a4297b69934fcfd`;
  checkout y bind mount `/app/tests/h3_local_uat.mjs` coincidieron.
- Servidor: Pages/workerd local R47/R12 en `http://localhost:38750/`, mock
  PostgREST/Auth en `http://localhost:38751/` y PostgreSQL 17 sintético R12.
  App `h3req1-g09-uat-app-20261010-r12`, imagen
  `studiamatch-h3req1:20261009-v3`. Se reutilizó el entorno activo.
- Navegador: Chromium 1228, Playwright headless en Docker, sin ventana visible;
  service workers bloqueados. Escrituras limitadas al curso sintético y
  restauración verificada por el `finally` del caso.

## R107 — fallo preservado y diagnóstico

- Comando: ejecución de `tests/h3_local_uat.mjs` con
  `H3_UAT_CASES=H3-UAT-049`, BASE/MOCK fijados a endpoints locales y salida en
  `uat-editorial-field-matrix-r107`.
- Exit 1; 0/3 viewports PASS, 0 retries, cero errores de consola y cero
  requests fallidos. Se preservan matriz y capturas.
- Desktop: el input quedó vacío, pero la aserción requería el id temporal
  `#preview-impact-start_date_text`, que solo existe mientras el campo conserva
  el resaltado. R106 ya había mostrado el fallback visible en 3/3; causa de
  harness/predicado transitorio, no defecto de producto.
- Tablet/móvil: las capturas muestran los valores editados; la aserción comparó
  duración sin normalizar, aunque CSS la presenta en mayúsculas. Causa de
  sensibilidad a capitalización en el test, no falta de propagación.
- Ejecuciones JSON SHA-256
  `66f24d5fdff44c9e4986d42f02a80287effb723ba1d5aec9d6e26b773870062f`.
  Capturas desktop/tablet/móvil SHA-256 `c20df7874941a7fcb1b22d17f9716ac7586f18d07565265ea6a74d229c3f2d4e`,
  `30e38a627ae9034bbfe68c3df678a6871a94e776f62ae5f67d64897ea328f990`,
  `e11093cff859a7643e5ce13545b3f5e4faeae7fc2406070ceedaaffad6bee43e`.
  R107 no se borra ni reemplaza.

## Corrección y R108

El cambio quedó limitado al runner UAT. Se comprobó el fallback mediante el
contenido visible estable de `data-preview-field`, sin ampliar el timeout de
2 s, y se normalizó el texto antes de comparar. H3-UAT-049 guarda los trece
campos editables en una sola interacción Admin, verifica valores
efectivos/overrides, conserva valores y fuentes del pipeline, coteja
actor/fecha/antes/después de auditoría y relee el mismo curso en lector
efectivo, listado, detalle y comparador tras reload.

| Viewport | Resultado | Aserciones | Consola / requests | Captura |
|---|---:|---:|---|---|
| Desktop 1440×900 | PASS | 43/43 | 0 / 0 | [PNG](h3req1_g09_uat_2026-10-10_r4/uat-editorial-field-matrix-r108/H3-UAT-049-desktop.png), SHA-256 `cc814eb943edae7f7bb51b7a5b22610a1ca54bc5fc16b4f2b7396ebafed059ff` |
| Tablet 768×1024 | PASS | 43/43 | 0 / 0 | [PNG](h3req1_g09_uat_2026-10-10_r4/uat-editorial-field-matrix-r108/H3-UAT-049-tablet.png), SHA-256 `47c44f4e5cea7f299670bf68341f2b292a88113db5e1470c4b8af0a06fdb06e0` |
| Móvil 390×844 | PASS | 43/43 | 0 / 0 | [PNG](h3req1_g09_uat_2026-10-10_r4/uat-editorial-field-matrix-r108/H3-UAT-049-mobile.png), SHA-256 `28b95f08405064d8e439418557900e00327afa3f0fdc02d6b15ef13764fe7f4a` |

- Exit 0, 3/3 viewports, 129/129 aserciones y cero retries.
- Vídeo desktop WebM SHA-256
  `3d43833eae32d8ad390a40e4fa11e3969817cede5508d3afb738c9c975cea7af`.
- Ejecuciones JSON SHA-256
  `e3b1a016a95298bfaf79397eff4948bdf5ecbb67fd18dfc3f6ea1a1c8bf97379`;
  manifest SHA-256
  `a4bc4e6b6bc807ff80dd4b2d0d8810e0288883c7f23428855c402e450d7eba89`.
- `node --check` dentro de Docker, `git diff --check` y scanner focal
  `env -i PATH=/usr/bin:/bin /bin/bash /app/scripts/security/scan_credentials.sh
  /app/tests/h3_local_uat.mjs` pasaron. Sin secretos en el test. No cambiaron
  fuentes de producto, SQL, manifests de dependencias ni workflows.

## Impacto en G09 y G08

- LOCAL-13/G09-T08 queda **completo en el fixture sintético**: trece controles,
  persistencia, procedencia, auditoría; R91 cubre conflicto de versión, R58
  ownership y R7 atomicidad PG17.
- LOCAL-16 avanza pero sigue **parcial**: el cambio se refleja en lector,
  listing, detalle y comparador tras recarga. No se afirma rebuild del
  artefacto ni se cubren todos los estados/assets.
- G08 continúa completo. Por el cambio exclusivo de runner JS se renovaron
  sintaxis y scan de credenciales; los demás checks conservan inputs
  compatibles. Histórico 8/10=80%; cierre local 8/9=88,89%, sin delta.
- INV-008 continúa resuelto por R8 (onboarding sintético 10/10); no se repitió.
- No se ejecutaron APIs live, CI remoto, promociones ni deploys. R12 y
  servicios sintéticos permanecen activos.

Los artefactos completos se preservan en
`h3req1_g09_uat_2026-10-10_r4/uat-editorial-field-matrix-r107/` y
`h3req1_g09_uat_2026-10-10_r4/uat-editorial-field-matrix-r108/`.
