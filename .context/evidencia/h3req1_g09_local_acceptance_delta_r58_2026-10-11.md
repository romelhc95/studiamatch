# H3REQ1 G09 — delta de aceptación R57/R58 — 2026-10-11

## Candidato y ejecución

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD base: `feat/h3req1-sync-20261002` /
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`; se probaron los archivos WIP
  montados del checkout, no solo el commit base.
- `tests/h3_local_uat.mjs` SHA-256 en R58:
  `473f12a808d40681450d6a87562ce93c5883d12624fd9d83760e5d233ae60840`.
- App: `h3req1-g09-uat-app-20261010-r12`, imagen
  `studiamatch-h3req1:20261009-v3`; Pages/workerd y mock Auth/BFF.
- Base: `h3req1-g09-uat-pg17-20261010-r12`, PostgreSQL 17.11 con fixture
  sintético; reset aislado por caso/viewport mediante PostgREST mock. No se
  usaron cuentas, correo, datos ni servicios remotos.
- Playwright Chromium 1228, **headless, sin ventana interactiva**; viewports
  desktop 1440×900, tablet 768×1024 y móvil 390×844.
- Catálogo solicitado: H3-UAT-050 y H3-UAT-055. Cero retries.

## Diagnóstico conservado

R57 fue exit 1: 2/6 ejecuciones PASS y 4/6 FAIL; se preservan su matriz,
trazas y seis capturas en
`h3req1_g09_uat_2026-10-10_r4/uat-functional-focused-r57-audit-compare/`.

1. H3-UAT-055 consultó el lector público con `id=eq.<uuid>`. La ruta mock
   permite filtrar UUID mediante `id=in.(...)`; con el filtro ausente la
   consulta devolvió filas del catálogo. Esto demuestra un defecto del nuevo
   test, no una filtración ni un defecto del producto. La consulta se corrigió
   a `id=in.(...)` y se añadió forma/status/row-count sanitizado.
2. H3-UAT-050 pasó desktop y tablet, pero en móvil su primera lectura editorial
   recibió HTTP 403; el runner anterior no conservó el código de error del BFF.
   No se atribuye a producto, sincronización o entorno. R58 añadió telemetría
   limitada a status, error code allowlisted y cantidad de filas. En R58 no se
   reprodujo el 403. Se conserva como resultado aislado no explicado de R57.
3. INV-008 tiene diagnóstico separado: el ciclo de rutas de una sesión
   `password_pending` fue reproducido como defecto de login/guard, corregido y
   validado por R8 con 10/10, cero retries, diez capturas y un vídeo. R57 no
   cambia esa clasificación.

## Resultado R58

R58 terminó exit 0: **2/2 casos, 6/6 ejecuciones PASS, seis capturas, cero
retries**. La matriz y las ejecuciones por viewport están en
`h3req1_g09_uat_2026-10-10_r4/uat-functional-focused-r58-audit-compare-diagnostic/`.

- H3-UAT-050: user puede leer el curso para su tarea, pero el servidor deniega
  mutación de un campo completo; versión y valor efectivo quedan iguales; el
  endpoint de auditoría no entrega eventos a user. PASS en los tres viewports.
- H3-UAT-055: lector efectivo devuelve cero filas para un UUID sintético no
  elegible; deep link de comparación muestra cero programas y ninguna tarjeta
  ajena. PASS en los tres viewports.
- Captura desktop de comparación:
  `uat-functional-focused-r58-audit-compare-diagnostic/H3-UAT-055-desktop.png`.
- SHA-256 de esa captura:
  `ecb1b9662b580e9929502755b318daf3d8bbcc164576e84c13bcea3d050fe647`.
- SHA-256 de la captura Admin/user desktop:
  `c1a63b2ac03063c6af0ebc72430de4cd3f317676b3390e88b9a1fd7ca5bc4ffa`.

No se añadió código de producto. Estas dos áreas amplían LOCAL-05 y LOCAL-13;
no bastan para cerrar G09 ni las otras áreas parciales.

## G08: deltas de test de candidato

- Añadí a `tests/test_h3req1_local_pipeline_walk.py` pruebas sintéticas de
  reanudación para `paginated_catalog` y `catalog_link_extraction`. Ambas
  conservan `discovered`, no reprocesan `pending`, descubren una URL nueva y
  preservan el estado almacenado. SHA-256 del archivo:
  `88bc8ca11f2feaee0184da4082865677eaaa92b54e5d9d6e48d93ea6d29ec993`.
- Runner focal en `studiamatch-dev`:
  `docker exec -e PYTHONPATH=/app:/app/scripts/core:/app/scripts/maintenance studiamatch-dev pytest -q /app/tests/test_h3req1_local_pipeline_walk.py -k 'paginated_discovery_resumes or catalog_link_discovery_resumes'`
  — exit 0, 2 passed, 8 deselected, warning PyPDF2 conocido.
- Suite G08 del proyecto, siguiendo el glob vigente `tests/test_*.py` en
  `studiamatch-dev`:
  `docker exec -w /app -e PYTHONPATH=/app/scripts/core studiamatch-dev /bin/bash -c '/opt/venv/bin/python -m pytest -q -p no:cacheprovider tests/test_*.py'`
  — exit 0, **333 passed, 4 skipped**, un warning PyPDF2. Los skips siguen sin
  contarse como PASS.
- Una invocación exploratoria `pytest /app/tests` falló en colección (exit 2)
  por `test_diagnostic_once.py` duplicado en dos carpetas JIT históricas. No
  ejecutó pruebas. Se preserva como error de colección del selector; el glob
  prescrito del proyecto terminó PASS.
- `node --check` de `tests/h3_local_uat.mjs` pasó en `studiamatch-dev` y R12;
  `scan_credentials.sh` sobre ambos runners modificados pasó en Docker. Build,
  ESLint, TypeScript, auditorías y workflows no cambiaron inputs funcionales y
  se reutilizan conforme a la matriz G08.

## Próximas acciones G09

La matriz LOCAL-01..23 se reconcilia en
`h3req1_g09_local_acceptance_matrix_reconciliation_2026-10-11.md`. Siguen
parciales, entre otras, estratificación del fixture, rutas/estados públicos,
coherencia entre export estático y fixture PG17, colas y filtros combinados,
campos editoriales/ownership por tipo, concurrencia de membresías, estados de
error adicionales de pipeline/runtime, accesibilidad fuera de las regiones ya
probadas, y medición repetible de rendimiento.

La URL Windows de solo loopback del mismo runtime y fixture es
`http://localhost:3336/`; el contenedor de proxy R47 fija el destino a R12 y
solo acepta GET/HEAD. La GUI de Windows no fue usada. El vídeo disponible del
recorrido principal es el de R49; R58 capturó pantallas, no vídeo, porque sus
casos no son el recorrido integrado largo.
