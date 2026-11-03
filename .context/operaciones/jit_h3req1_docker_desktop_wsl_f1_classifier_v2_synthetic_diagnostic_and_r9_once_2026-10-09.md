# JIT — diagnóstico sintético V2 con códigos cerrados, F1 y r9 condicional

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-SYNTHETIC-DIAGNOSTIC-AND-R9-ONCE-20261009-V1`  
Estado: **preparado; requiere aprobación exacta; no ejecutado**.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Motivo

El JIT de pin corregido
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-PIN-FIX-AND-R9-ONCE-20261009-V1`, SHA-256
`dbc58ec3dcc3ce7cacc83d84ec6689a16f1564ae40c0776607fba5e35371e79d`, se aprobó y consumió una
vez. Resultado: endpoint `OK`, `classifier-synthetic-tests/SYNTHETIC_TESTS_FAILED`, exit 1;
F1/r9 no alcanzados.

La revisión mostró que el wrapper anterior agrupaba como `SYNTHETIC_TESTS_FAILED` tanto un
fallo al crear el contenedor como pytest/colección/aserciones. Además, descartaba la identidad
del digest local antes de intentar ejecutarlo. No se preservó la salida cruda y no se conoce la
causa exacta. La revisión estática de los casos actuales no demuestra una aserción defectuosa.
Se preparó una salida diagnóstica cerrada por estado y caso; no se ejecutó.

## Alcance de una invocación

Ejecutor: `romel` en Ubuntu WSL interactiva con TTY, sin `sudo`.

1. Comprueba checkout, rama, HEAD, pins, manifiestos r9 y ausencia de overrides Docker.
2. Atestigua el endpoint Docker Desktop WSL y Engine Linux.
3. Lee solo `.Id` de la imagen sintética fijada
   `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`, sin pull. Si no
   está disponible o el ID no coincide, se detiene antes de lanzar contenedores.
4. Ejecuta los cinco casos sintéticos V2 en un contenedor efímero con `--pull=never`, sin red,
   rootfs read-only, UID 1001, capacidades removidas, límites de recursos y solo `/diag` read-only.
   Un helper captura pytest solo en memoria efímera y emite códigos cerrados allowlisted para
   pytest ausente/import, colección, fase de test o cada caso V2; stdout/stderr raw, rutas y
   valores de test no se imprimen ni persisten.
5. Solo si endpoint, digest sintético y casos devuelven exactamente `OK`, lee una vez la imagen
   F1 allowlisted y realiza un inspect del contenedor F1 fijado.
6. Solo si endpoint, imagen sintética, sintéticos, imagen F1 y contenedor F1 son `OK` y los
   controles F1 pasan, ejecuta r9 una vez con sus hashes y límites fijados.

Cualquier fallo consume este permiso e impide la etapa posterior; no hay retry. No repite F2d ni
otra invocación consumida, no hace pull/rebuild/instalación, no usa `/proc`, no accede ni modifica
`studiamatch-dev`, y no cambia SQL, secretos, workflows, settings, ramas, GitHub, Pages o
despliegues. No autoriza copia completa, Pages/workerd, C03 integrado, UAT final, publicación,
PR, merge ni configuración remota. Las etapas locales posteriores solo siguen con sus
autorizaciones vigentes y predicados satisfechos.

## Fases de éxito esperadas

```text
phase=desktop-wsl-endpoint-attested|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-tests|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=OK
phase=r9|error_code=OK
```

Si falla una prueba, el runner puede emitir también líneas
`phase=classifier-synthetic-test-case|error_code=<código cerrado>` antes del código final de
fase. Un fallo detiene el ciclo; no habrá F1 ni r9 tras error sintético. Los códigos cerrados
previstos incluyen `PYTEST_UNAVAILABLE`, `PYTEST_IMPORT_FAILED`, `PYTEST_RUNNER_FAILED`,
`V2_TEST_COLLECTION_FAILED`, `V2_TEST_PHASE_FAILED`, `V2_PARSE_CASE_FAILED`,
`V2_EVALUATION_CASE_FAILED`, `V2_AMBIGUOUS_CASE_FAILED`, `V2_MAIN_SANITIZATION_FAILED`,
`V2_FAILURE_CODE_CLASSIFIER_FAILED`, `V2_TEST_FAILURE_UNCLASSIFIED`,
`SYNTHETIC_CONTAINER_RUN_FAILED`, `SYNTHETIC_IMAGE_UNAVAILABLE` e
`SYNTHETIC_IMAGE_ID_MISMATCH`.

## Pines

- Runner combinado: SHA-256
  `d7e64ac2125bcaa703479e4f6eb83e449fcc309e56b559795235a64006e416f9`.
- Runner diagnóstico: SHA-256
  `781750a9e839eaa81fa3e17287fba970e9c5535d9c097f3caa88df05f42b8c8a`.
- Helper diagnóstico V2: SHA-256
  `d7ae28af55d3f45d41588fc8b2d3f5ed5b56710d0d91d5e7d49618d7e1cca5bf`.
- Pruebas sintéticas: SHA-256
  `231a6d04ad00ac0cbc4574378109ffd39dde5cfe897b83e692fe55ac35113574`.
- Clasificador de salida sintética: SHA-256
  `45ad0f6849a0c4a96becb25df54c7df7ddd94716bdeddba3e0ae1a2400d44bdf`.
- Helper de endpoint: SHA-256
  `c25aa3d3d91bb0cadc160b090c49c4bc61362baefaf3415d046ce7a9cabea4cb`.
- Proyector Docker: SHA-256
  `794b49ce5560c8cacebbd403c05b4cdbe78fd0c0062d30b6690b901838831463`.
- Helper F1 V1 fijado: SHA-256
  `b84e46250823a0a7f3c73bf0bbd3359147585dea7d1c4b8ef322d87a1c12d4fc`.
- Runner r9: SHA-256
  `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`.
- Manifiesto r9: SHA-256
  `b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866`.
- Manifiesto tools: SHA-256
  `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.

El SHA-256 de este documento se comunica para aprobación y no se embebe en el propio archivo.
El comando y los runners vuelven a validar sus pins antes de continuar.

## Comando único — Ubuntu WSL interactiva

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_classifier_v2_then_r9_once.sh'
readonly RUNNER_SHA256='d7e64ac2125bcaa703479e4f6eb83e449fcc309e56b559795235a64006e416f9'

if (( EUID == 0 )); then
  printf 'phase=jit-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -t 0 ]]; then
  printf 'phase=jit-preflight|error_code=INTERACTIVE_TTY_REQUIRED\n'
  exit 1
fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout ]]; then
  printf 'phase=jit-preflight|error_code=RUNTIME_UNAVAILABLE\n'
  exit 1
fi
if ! hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)"; then
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
fi
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi

/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 300s /bin/bash "$RUNNER"
runner_status=$?
IFS= read -r -p 'Copia solo las fases sanitizadas y el exit; presiona Enter para cerrar: ' _ || true
exit "$runner_status"
)
```

Compartir solo las fases/códigos sanitizados y el exit. No copiar stderr, metadata Docker,
salida de pytest, rutas privadas ni valores de entorno. Si hay fallo, conservar fase, código,
predicado y exit; no reintentar.
