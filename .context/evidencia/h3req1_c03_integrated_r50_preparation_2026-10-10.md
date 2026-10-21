# G07 C03 integrado local R50 — preparación

Fecha: 2026-10-10. Revalidación focal del candidato actual tras R49 PASS con dos
inputs de sesión posteriores. R49 y su manifiesto histórico permanecen intactos.

## Candidato e impacto

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD baseline: `feat/h3req1-sync-20261002` /
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Consumidores: Pages/workerd y BFF, Edge `admin-invite`, PostgreSQL 17.11 y
  PostgREST; contratos de cookie Auth ligada a `session_id`, MFA/AAL2, gateway,
  cuota, suspensión, finalizador único, replay e invariantes SQL.
- Evidencia preservable: 125/127 hashes R49 iguales, SQL/editorial PG17 vigente,
  S18 snapshot completo y S16 healthz real. R49 demuestra integración local para
  sus bytes y permanece histórico.
- Evidencia a renovar: snapshot integrado de 127 inputs, contrato R50, runtime
  Pages/workerd conectado a Edge/PostgREST/PG17 con la fixture de sesión actual y
  aserciones C03 integradas. Motivo: dos cambios de código que afectan identidad
  de sesión y su fixture.
- Contrato/alcance: sin cambio de reglas de negocio, esquema SQL o ambiente remoto.
  Se preservan compatibilidad legacy, BFF HttpOnly, MFA, roles, gateway firmado,
  cuotas y datos/auditoría/publicación/último admin durante suspensión y recovery.
- Recuperación: stop-on-failure; no retries. PG en tmpfs; redes internas; secretos
  sintéticos derivados dentro del runner; mounts de caches read-only. Cleanup solo
  de contenedores/redes R50 etiquetados y verificados por IDs; snapshot/TLS/caches
  permanecen. Sin tocar `studiamatch-dev`, `.env*`, checkout original o remotos.

## Paquete y revisión previa

- Runner: `tests/h3req1_c03_integrated_drill_r50.sh`, SHA-256
  `21ce77a9cc2fa9492b97481cb1de2b4944eef06cbba9ae1f4ddeff58d750578c`.
- Contrato: `tests/h3req1_c03_integrated_drill_r50_contract.test.mjs`, SHA-256
  `9e55793338511cbf8f730c99a7bde19f148bc98de7b83e03b28d3ac7cdf5c189`.
- Manifiesto: 127 rutas exactas, SHA-256
  `ece1d3ea73dc3914308b0ef029fbb21c5f98d46b49a1c2ccd695f00eeca0ad62`.
- El manifiesto conserva los mismos 127 paths de R49 salvo el nombre de los dos
  artefactos versionados R49→R50; actualiza únicamente los hashes del runtime, BFF,
  runner R50 y contrato R50. Los 123 inputs restantes conservan sus digests.
- PostgreSQL 17.11, PostgREST, Node y Edge Runtime usan los mismos digests locales
  fijados por R49. No se hace pull/build/install/egress.
- Nombres R50 nuevos de contenedores, redes y volúmenes verificados libres. El
  preflight del runner vuelve a verificar Docker target, capacidad, hashes, caches
  fijadas, nombres, montajes y estado antes de crear recursos.
- Timeout exterior 2400 segundos, retries cero, stop-on-failure. El runner registra
  fases/exits sanitizados en `.context/evidencia/h3req1_c03_integrated_run_2026-10-10_r50.txt`.
- Validación previa en contenedores locales fijados: `bash -n` PASS,
  `node --check` PASS, ShellCheck 0.11.0 PASS, manifest 127/127 PASS,
  `git diff --check` PASS y contract suite 36/36 PASS. El contract suite se
  ejecutó en Node con `network=none`, filesystem read-only y snapshot temporal
  de los 127 inputs.
- Revisión independiente estática: PASS para invocar R50; no encontró bloqueo
  de seguridad/aislamiento. LOW no bloqueante: el runtime no llama
  `admin_list_members` ni `admin_list_members_onboarding`, por lo que el drill
  no acredita esa clasificación de cuota. Se cubrirá como caso focal de G08;
  no se atribuye ese resultado a R50.

La preparación no afirma runtime PASS ni cierra G07. Revisión estática y
validaciones locales previas terminaron PASS; R50 sigue pendiente de ejecución.

## Resultado posterior preservado — R50 consumido, R51 PASS

El resultado real de R50 quedó registrado en
`h3req1_c03_integrated_run_2026-10-10_r50.txt` (SHA-256
`bafb8a80f5b49e2d7dab7ad4ca718ee64827a5179d7b040eae0dc58d700bedef`).
R50 terminó con exit 1 en `isolated-workerd-bootstrap`: un import estático del
runtime requería `h3req1_c03_startup_healthz_probe.mjs`, ausente del snapshot de
127 rutas. No se atribuye a Docker ni a la aplicación. Se conservan sus recursos
y evidencia histórica; R51 los dejó intactos.

R51 añadió únicamente ese helper al snapshot y una aserción contractual que
comprueba la dependencia. Su manifiesto actual de 128 entradas y el drill
integrado terminaron PASS, según
`h3req1_c03_integrated_r51_preparation_2026-10-10.md` y
`h3req1_c03_integrated_run_2026-10-10_r51.txt`. R50 sigue siendo FAIL histórico;
R51 es el resultado vigente para G07. No se reutiliza R50 como PASS.
