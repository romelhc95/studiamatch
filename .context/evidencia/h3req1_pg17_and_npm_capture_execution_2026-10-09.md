# H3REQ1 — resultado PG17 editorial y clasificador npm V2

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Tareas, gates y ficha de impacto

| Tarea | Gate | Resultado y siguiente acción |
|---|---|---|
| Probar atomicidad del append de auditoría editorial en PG17 | G01/G09, harness editorial | JIT aprobado y consumido. `preflight=OK`, `pg17-start=OK`, `pg17-version=VERSION_MISMATCH`, `container-cleanup=OK`, exit 1. Detener; no retry. La versión observada exacta no se emite, por lo que queda sin determinar. |
| Clasificar una vez el reporte de auditoría npm de la imagen V3 | G03 | JIT V2 aprobado y consumido antes de Docker. `capture-synthetic-tests=SUMMARY_CASE_INVALID`, exit 1. No se inspeccionó la imagen, no se creó contenedor y no hubo tráfico npm. |
| Corregir el parser del wrapper | G03 | Hallazgo localizado al patrón JSON: omitía las comillas de las claves `auditCommandExit`/`counts`. Corrección mínima en el runner. `bash -n` y `git diff --check` pasan; no se ejecutó suite sintética en host. El JIT nuevo está preparado y requiere aprobación separada. |

### Evidencia PG17

- Permiso: una invocación de `H3REQ1-EDITORIAL-ATOMICITY-PG17-ONCE-20261009-V1`, SHA-256
  `a795528ec0376ac64a88344a03380644eed5122da9f52ffd44cf19cd3b923ef7`.
- Runner fijado `tests/h3req1_c03_atomicity_pg17/run_editorial_atomicity_once.sh`, SHA-256
  `3465f73650d283f2731bfb10d28c8b01f66d81d8102dc539baf5b91f76e1aded`; manifest de 36 inputs
  SHA-256 `0ed63a7b439275121caa9255ea033030f20e363fdb71eb202a47a94792ab2bc5`.
- Resultado sanitizado preservado en
  `evidencia/h3req1_editorial_atomicity_pg17_once_2026-10-09.md`. La limpieza retiró el
  contenedor efímero exacto. No se reporta el harness SQL como PASS y no se copia 41/41 a esta
  cobertura; G01 queda abierto. El runner no expone el valor de versión real, así que la causa
  posterior a la discrepancia del predicado queda desconocida y no se atribuye a Docker.
- Para resolver únicamente esa incógnita sin repetir SQL se preparó una lectura única del
  `postgres --version` de la misma imagen fijada, sin mounts, datos ni red:
  `operaciones/jit_h3req1_pg17_pinned_image_version_once_2026-10-09.md`, SHA-256
  `a7787182737186ae43cb4e82f6f88a4fb7a71bdf52e2de7e1f9967672c2835b1`. No está aprobada ni
  ejecutada. Su runner pasó revisión estática `bash -n`; no realizó Docker.

### Evidencia npm V2

- Permiso: una invocación de `H3REQ1-CANDIDATE-V3-NPM-AUDIT-CLASSIFIER-V2-ONCE-20261009-V1`,
  JIT SHA-256 `1a70db5a61e9fdf63660b296404c8ec188014b0d1b08bb8f9148975e6902ac2e`.
- Pines de JIT, runner inicial (`4a867f32759f88618325b969f4c89668a6ec25146414a75d33a78c999049ca78`),
  clasificador, sintéticos, `package.json`, `package-lock.json`, rama y HEAD coincidieron antes
  de ejecutar. Se ejecutó una vez en PTY como UID 1000; exit 1 en el parser de captura, antes
  de cualquier llamada Docker.
- El fallo era del wrapper de salida, no de producto ni de `package-lock`: el patrón Bash
  buscaba `{auditCommandExit:`/`{counts:` sin la comilla JSON después de `{`, mientras el
  fixture válido empieza `{"auditCommandExit":...`.
- El runner original se conserva en
  `evidencia/h3req1_npm_audit_capture_runner_v2_pre_fix_2026-10-09.sh`, con hash verificado
  `4a867f32759f88618325b969f4c89668a6ec25146414a75d33a78c999049ca78`. El runner actualizado
  cambia únicamente ese predicado; SHA-256 nuevo
  `0c48f12b818c8611c1187fa402f92bb502ed6ea45cb17cc13270db28a51a58f5`.
- Revisión local: `bash -n` PASS y escaneo de whitespace sin coincidencias. No se ejecutaron
  los seis casos de captura ni los 14 sintéticos fuera del JIT. Paquete para una invocación nueva:
  `operaciones/jit_h3req1_candidate_v3_npm_audit_classifier_v2_fixed_capture_once_2026-10-09.md`.
  SHA-256 `f06d497bfcc26cd321b6a2b96ebc8c2d2bc8fedfecf187df9eb00cdd601c9aea`. No hay aprobación
  para repetir hasta recibirla.

## Impacto, evidencia y estado de gates

- Cambia únicamente tooling de test/auditoría y evidencia; no cambia código funcional,
  SQL/migraciones, workflow, imagen ni manifiestos npm.
- Integridad preservada: checkout original y secretos no leídos; no se ejecutó F1, r9, copia,
  Pages/workerd, Edge/PostgREST ni C03 integrado. No hubo operación remota.
- G01 sigue 0/10 por `VERSION_MISMATCH`; G02 conserva 10/10 por el manifest separado C03 SQL
  v3 41/41; G03 sigue 0/10; G04–G10 siguen sin cierre. Total **10%**, delta **0 puntos**.
- El PASS de limpieza, hashes y sintaxis son parciales; no suman puntos ni acreditan candidate
  readiness. Las siguientes acciones requieren autorización para los dos JIT preparados:
  lectura PG17 SHA `a7787182737186ae43cb4e82f6f88a4fb7a71bdf52e2de7e1f9967672c2835b1` y npm con
  captura corregida SHA `f06d497bfcc26cd321b6a2b96ebc8c2d2bc8fedfecf187df9eb00cdd601c9aea`.
  Ambas invocaciones anteriores se consumieron y no autorizan replay.
