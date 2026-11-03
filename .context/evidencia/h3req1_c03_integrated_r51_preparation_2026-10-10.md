# G07 C03 integrado local R51 — ejecución y resultado

Fecha: 2026-10-10. Estado: **PASS local integrado; sin GO remoto**.

## Candidato e impacto

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD baseline: `feat/h3req1-sync-20261002` /
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- R51 renovó la fixture integrada de C03 para los inputs actuales de Pages/workerd,
  BFF, Edge, cuota, gateway y sesión ligada a `session_id`.
- Se preservó el checkout original y `studiamatch-dev`; no se cargó `.env*`, no
  hubo destino cloud, Git de escritura, push/PR/merge, ni despliegue.
- R50 permanece como intento histórico FAIL por helper de arranque omitido del
  snapshot; su resultado no se convierte en PASS.

## Inputs fijados y revisión

- Runner `tests/h3req1_c03_integrated_drill_r51.sh`, SHA-256
  `e6e934aed0d8d68ead7e3e107ebeaf2197ddbe243e3fa2650ff00f1f25bd896f`.
- Contrato `tests/h3req1_c03_integrated_drill_r51_contract.test.mjs`, SHA-256
  `be249bc6ae5a5255783d924db2c20e94f33ff0ec9fb19dff31d54418dc1655dc`.
- Manifiesto `tests/h3req1-c03-integrated-r51.sha256`, SHA-256
  `912ce9ccc2d42bbe8ee0ca7b4dcb69991a924e5f788e0914b33c4a2ba4650277`,
  128 rutas verificadas; helper
  `tests/h3req1_c03_startup_healthz_probe.mjs` incluido.
- Revisión estática independiente: PASS, sin bloqueantes. Verificó snapshot,
  aislamiento, pins, nombres R51 y cleanup acotado; R50 no fue objeto de cleanup.
- Preflight Docker: endpoint/engine, imágenes, capacidad e identidad de recursos
  R51 PASS. Imágenes locales fijadas; sin pull/build/install.

## Ejecución y evidencia

- Comando ejecutado una vez:
  `bash tests/h3req1_c03_integrated_drill_r51.sh --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R51 --manifest-sha256 912ce9ccc2d42bbe8ee0ca7b4dcb69991a924e5f788e0914b33c4a2ba4650277`.
- Exit 0. Log sanitizado:
  `h3req1_c03_integrated_run_2026-10-10_r51.txt`, SHA-256
  `777a9f240943e34687a18c7ed6aec4161312eb6a13cceacd7387c1247d46c2fc`.
- PostgreSQL 17.11, migraciones H2→H3, PostgREST y cuotas/gateway locales
  sintéticos: PASS.
- Pages/workerd healthz, login AAL2, reserva antes de retención, suspensión
  segura persistente de Pages/Edge, dispatcher firmado, rechazo de nonce,
  invariantes ACL/datos/cuota/auditoría, finalizador in-flight de efecto único,
  resume en conexión nueva, replay idempotente y smoke final: PASS.
- El resultado Edge en suspensión fue HTTP 503 `maintenance_mode`; el dispatcher
  fue rechazado con 403/`42501` sin consumir nonce; el finalizador completó una
  vez mientras SQL estaba suspendido. Reanudación y lectura recuperada pasaron.
- Cleanup final retiró por ID exacto solo contenedores y redes internos R51.
  Snapshot, TLS y caches R4 read-only fueron preservados; PG17 usó tmpfs. Sin
  cambios de imagen ni archivos del checkout por el runner.

## Gate

G07 queda completo para el alcance local C03 integrado del candidato identificado.
Esto no cierra G08/G09, no demuestra el recorrido público/pipeline/Admin de la
matriz de 23 áreas y no acredita GO_LOCAL_PR ni GO_DEVELOPMENT_REAL.
