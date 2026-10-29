# C03 integrado local R49 — preparación

Fecha: 2026-10-10. Continuación del PASS R48 con el delta SQL de `admin_update_course`
fijado. La migración editorial cambió después de R48, por lo que R48 se preserva como
histórico y no se atribuye al guard actual `p_version IS NULL OR ... IS DISTINCT FROM`.

## Candidato y ficha de impacto

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP pre-R49: 55 tracked modificados, 659 untracked, 0 staged; preservar checkout original.
- Consumidores: Pages/workerd runtime, Edge `admin-invite`, PostgreSQL 17/PostgREST,
  gateway firmado, cuotas, safe-suspend y recuperación C03.
- Delta funcional consumido: migración editorial actualizada; R48 manifestó un único
  mismatch de input, `db/migrations/20261001_h3_course_editorial_audit_availability.sql`.
- Evidencia preservada: R48 PASS con sus 127 inputs históricos; G01 PG17 V6 ejecuta
  de forma aislada la corrección de NULL-version y el gateway firmado. S14 conserva
  el snapshot completo 14/14 de sus 13 fuentes allowlisted más manifest, aún coincidentes.
- Pruebas a renovar: snapshot integrado exacto de 127 entradas; runner contract R49;
  arranque Pages/workerd healthz; PG17 H2→H3 actual, PostgREST y C03 integrado.
- Recuperación: on failure el runner detiene dependencias; conserva volúmenes snapshot/TLS
  y cachés fijadas; retira solo contenedores/redes etiquetados de R49 al completar. No toca
  `studiamatch-dev`, checkout original, volúmenes de datos ajenos, servicios remotos ni `.env*`.
- Transición: compatibilidad de RPC/estado legacy permanece; el guard de versión rechaza
  NULL/stale antes de mutación; ningún rollback remoto ni fase deploy/contract remota se ejecuta.

## Artefactos fijados

- Manifest R49: 127 rutas exactas; SHA-256
  `5238e20f4711ad033f0d8f3571f9445705c9a193f19905d866fc4ad694d0ac00`.
- Runner: `tests/h3req1_c03_integrated_drill_r49.sh`, SHA-256
  `91787049728f2fea39847b7e198a11565d57aae42980b6cb78ff71f230658991`.
- Contract: `tests/h3req1_c03_integrated_drill_r49_contract.test.mjs`, SHA-256
  `fc7b1734d6123053f869d417592749057e00a5ccb251e3d4e9acc498c2ebb51b`.
- Diferencia R48→R49 de manifest: mismo conjunto de 127 inputs; se renombraron runner y
  contract R48→R49 y se actualizó el hash de la migración editorial. Los demás inputs
  conservan sus bytes.
- Imágenes ya locales y fijadas en el runner: PostgreSQL 17.11,
  PostgREST SHA `0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228`,
  Node SHA `dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`,
  Edge Runtime `v1.74.3` SHA `cc355c3d0e9c063a351cad56d1c4c52a3c4d85aff4e1fad9d91688e75f9aad09`.
- Runtime Pages/Edge, PG y PostgREST se ejecutan en redes internas etiquetadas; secrets
  son fixtures sintéticos derivados en el runner, no se leen archivos `.env*`, secretos
  reales ni datos operativos. No hay egress, pull, build ni instalación.
- R4 tool/module caches se verifican por digest y se montan read-only. PG usa tmpfs.
- Comando exacto: `bash tests/h3req1_c03_integrated_drill_r49.sh --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R49 --manifest-sha256 5238e20f4711ad033f0d8f3571f9445705c9a193f19905d866fc4ad694d0ac00`.
- Timeout exterior 2400 s, cero retries, stop-on-failure. El runner contiene bounded timeouts
  por operación, emite log sanitizado y comprueba el PASS final después del cleanup.

## Revisión previa ejecutada

- Runner `bash -n` dentro de `studiamatch-dev`: PASS.
- Contract `node --check` dentro de `studiamatch-dev`: PASS.
- ShellCheck 0.11.0 en imagen local fijada, read-only/network-none: PASS.
- Manifest: 127/127 SHA-256 actuales; comparación R48→R49 limitada al delta indicado.
- `source-manifest` S14 mantiene 13/13 hashes actuales; S14 registra productor,
  receptor, verificador, symlinks, permisos y extracción PASS 14/14.
- No se encontraron nombres de recursos R49 previamente ocupados.

La invocación y el resultado, incluidos exits por fase y recursos exactos, se agregarán
en `.context/evidencia/h3req1_c03_integrated_run_2026-10-10_r49.txt`. Esta preparación
no afirma runtime PASS.
