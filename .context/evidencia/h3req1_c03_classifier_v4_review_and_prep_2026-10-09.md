# H3REQ1 C03 — revisión del reporter V4 y JIT preparado

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Tareas y gates

| Tarea | Resultado | Gate |
|---|---|---|
| Corregir el reporter sintético ambiguo | V4 mapea fallos por caso allowlisted; no inspecciona traceback | Validación Docker pendiente de JIT nuevo |
| Cerrar `skip` y resultados incompletos | V4 exige PASS de cada caso y falla ante skip/resultado ausente | Prueba sintética añadida, aún sin ejecutar |
| Cerrar emisión sanitaria del wrapper | Solo imprime pares fase/código allowlisted; línea desconocida produce `OUTPUT_REJECTED` | Revisión independiente final pendiente |
| Preparar F1 y r9 condicionales | El JIT lee `.Config.Volumes` de la imagen F1 y política allowlisted del contenedor; r9 depende de esos PASS | Requiere aprobación exacta nueva |

## Discrepancia previa

El JIT V3 aprobado y consumido acreditó socket path/create/connect, lectura HTTP e identidad
Linux del Engine. También obtuvo `OK` al leer el ID de la imagen sintética. El runner emitió
`phase=classifier-synthetic-tests|error_code=V2_MAIN_EXIT_ASSERT_FAILED`, exit 1. Stop-on-failure
detuvo antes de F1 y r9. No se reintentó ni se consultó, construyó o cambió
`studiamatch-dev`/Docker.

La causa de atribución estaba en el reporter: buscaba un marker por subcadena dentro de la
representación completa del fallo de pytest. La salida no distinguía cuál assertion falló; no
demuestra un defecto del clasificador funcional ni de Docker. El contexto detallado y la matriz
de aceptación de cuatro ajustes quedan en
[la evidencia V3 preservada](h3req1_c03_socket_classifier_v3_assertion_reporter_failure_2026-10-09.md).

## Hallazgos de la primera revisión independiente y correcciones

| Hallazgo | Corrección en V4 | Evidencia estática |
|---|---|---|
| Reporter podía dar PASS si un test se omitía con skip | Registra call reports `passed`, `skipped` y `failed`; requiere que todo caso esperado tenga PASS; skip produce `V2_TEST_SKIPPED` y ausencia produce `V2_TEST_RESULT_INCOMPLETE` | Se añadieron tres pruebas sintéticas del reporter: pase completo, skip y resultado incompleto |
| Wrapper imprimía cualquier línea con regex amplia antes de validar el transcript exacto | `is_allowed_diagnostic_line` aplica allowlist cerrada de fases/códigos antes de guardar/imprimir; desconocidos se reemplazan por `phase=output-capture|error_code=OUTPUT_REJECTED` | `bash -n` PASS; salida exacta esperada sigue siendo condición para F1/r9 |
| El JIT describía una lectura del digest de imagen F1 | Texto corregido: se lee/verifica `.Config.Volumes`; el ID de imagen sintética se verifica en su paso separado | Revisión directa del helper invocado; no se ejecutó Docker |
| Runner r9 emitía directamente salida de suites bajo el contrato sanitario | El wrapper descarta stdout/stderr de r9 y conserva solo `phase=r9|error_code=...` y el exit numérico ante fallo | Revisión del wrapper y del JIT detectó la ruta; nueva revisión independiente pendiente |

La segunda revisión independiente de los cuatro archivos V4 no encontró hallazgos concretos.
En una revisión integral final detecté que r9 transmitía stdout/stderr; el wrapper ahora descarta
ambos canales y conserva solo `phase=r9|error_code=OK` al pasar, o `CHECK_FAILED` más `exit=<n>`
al fallar. La revisión independiente final de los cuatro archivos confirmó que no quedan
hallazgos concretos y verificó los pines actuales, incluidos el shell runner, helper V4,
synthetic runner, tests, helper V2, evidencia endpoint y manifiestos r9. No ejecutó Docker,
pytest ni Python de proyecto y no modificó archivos.

## JIT preparado

[JIT V4 reporter + F1/r9 condicional](../operaciones/jit_h3req1_docker_desktop_wsl_f1_classifier_v4_and_r9_once_2026-10-09.md).
SHA-256: `d6e28031197cf6a2c34ed205ead389d0f7dc514ae745678aa505570a7bfe7648`.
Ejecutor indicado: `romel`, Ubuntu WSL interactiva, sin `sudo`, una invocación con
`sandbox_permissions=require_escalated`. Reutiliza la atestación socket/Engine anterior y no
repite socket/connect/HTTP. El runner ejecuta primero sintéticos en imagen existente con
`--pull=never`, red deshabilitada, rootfs read-only, usuario 1001, capabilities removidas y
límites fijados; después lee F1 una vez y ejecuta r9 solo si todos los predicados previos pasan.
Fallo/timeout consume la autorización; no hay retry ni cambio de Docker.

## Validación disponible antes del JIT

- `bash -n tests/h3req1_docker_peer_substep_diag/run_wsl_f1_classifier_v4_then_r9_once.sh`: PASS.
- `git diff --check`: PASS.
- No se ejecutaron pytest, código Python de proyecto ni comandos Docker; esperan el JIT nuevo.
- La salida de r9 se descarta por completo; al pasar reporta `phase=r9|error_code=OK`, y al
  fallar reporta `phase=r9|error_code=CHECK_FAILED` con su exit numérico.
- SHA-256 actuales del paquete: runner combinado
  `6238cd2c276919a173654219497b2f0096ebad2c23e60aabe8cd477af1c61577`; helper V4
  `d95a9450302e58f6ee220c5c0ae115b8bd37f83f267b7842aca453099231c877`; runner sintético
  `378f353e47192e1f7564091d56e59a101d0cee7063cd7fdb26e648ccfb7d21a9`; tests sintéticos
  `97a5d186e463e65e96933fd42066a370180ef57d59972e6f8007c754184a883e`.

La herramienta de Codex Security rechazó la revisión diff con target repositorio + scope de
subdirectorio porque exige `scope='.'`; rechaza también tratar el subdirectorio como raíz Git.
No creó `scanId` ni inició un scan amplio, respetando el límite de no repetir scans completos.
La revisión acotada se mantiene con el auditor independiente del cambio V4.

## Gates y estado

G01=10/10, G02=10/10; G03–G10=0/10; total 20%, delta 0. La lectura de endpoint y la
documentación del reporter no suman puntos. F1, r9, copia íntegra aislada, Pages/workerd,
integración Edge/PG17/PostgREST, C03 integrado, los cuatro ajustes del WIP, UAT vigente,
onboarding separado, aceptación final y CI efectivo siguen abiertos. No hay
`GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
