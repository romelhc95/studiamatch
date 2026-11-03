# JIT — corrección de expectativa V4 + una lectura F1/r9 condicional

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V4-FIX-AND-R9-ONCE-20261009-V1`  
Estado: preparado; requiere aprobación explícita; una sola invocación.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Causa acotada del último FAIL y cierre del reporter V4

El JIT V3 anterior quedó consumido con el endpoint acreditado y
`classifier-synthetic-tests/V2_MAIN_EXIT_ASSERT_FAILED`, exit 1. No llegó a F1 ni r9.
Revisión estática localizó que el reporter anterior buscaba tokens dentro de la representación
completa de pytest. El código de fase emitido no permite distinguir de forma segura qué
aserción falló. No se altera el clasificador F1 de producto ni se persiste el traceback.

V4 divide ese test en tres casos nombrados y el reporter obtiene el código únicamente del
nombre allowlisted del caso fallido. La revisión independiente encontró además que el reporter
debía fallar cerrado ante tests omitidos/skipped y que el wrapper no debía imprimir líneas
solo por ajustarse a una regex general. V4 exige un call report `PASS` para cada caso esperado,
rechaza cualquier `skip`/resultado ausente y valida pares fase/código con una allowlist cerrada
antes de imprimirlos. La descripción de F1 se ajustó a la lectura real del helper. El reporter
no recibe ni lee el traceback. El detalle de revisión y correcciones está en
[evidencia del ciclo](../evidencia/h3req1_c03_classifier_v4_review_and_prep_2026-10-09.md); la
matriz de aceptación original está en
[evidencia del ciclo](../evidencia/h3req1_c03_socket_classifier_v3_assertion_reporter_failure_2026-10-09.md).

Después, el JIT V4 de SHA-256
`d6e28031197cf6a2c34ed205ead389d0f7dc514ae745678aa505570a7bfe7648` se consumió con
`classifier-synthetic-tests/V2_MAIN_OUTPUT_ASSERT_FAILED`, exit 1. F1/r9 no se alcanzaron. La
causa estática precisa es que `test_v2_main_failure_emits_exact_sanitized_sequence` omitía
`classifier-synthetic-tests|OK`, que el `main()` V2 sí emite antes de leer F1. La expectativa se
corrigió en una sola línea. Evidencia: [resultado V4](../evidencia/h3req1_c03_classifier_v4_synthetic_output_mismatch_2026-10-09.md).

La revisión independiente final del delta no encontró hallazgos, confirmó que la secuencia
esperada coincide con el orden de `main()` y verificó los pins del test, clasificador y runner
combinado. Fue read-only; no ejecutó Docker, pytest ni Python de proyecto. Evidencia:
[reconciliación V4](../evidencia/h3req1_c03_classifier_v4_synthetic_output_mismatch_2026-10-09.md).
No se ha ejecutado la prueba sintética corregida.

## Evidencia de endpoint reutilizada

La última invocación JIT V3 acreditó como `OK` socket path, creación, conexión, lectura HTTP,
identidad Linux del Engine y endpoint. Esta ejecución **no vuelve a hacer** `lstat`, socket
create/connect ni `GET /version`. Reutiliza el artefacto sanitario fijado por SHA-256
`8e6360143d15e47c819beb540edd69bd2a08634ac85b9267d03fd61c5c5ac33a` y exige que contenga las
seis fases de atestación exactas en `OK`. No acredita PID/UID/ejecutable del daemon. El residual
es que la atestación corresponde a la conexión anterior; las nuevas consultas siguen limitadas
al endpoint fijo `unix:///var/run/docker.sock`.

## Alcance de una invocación

Ejecutor: `romel`, Ubuntu WSL interactiva, usuario no-root, TTY, sin `sudo`, bajo
`sandbox_permissions=require_escalated`.

1. Verifica usuario/TTY, rama y HEAD del candidato, SHA del runner, helper V4, tests V4, runner
   sintético V4, evidencia previa y paquete r9. Rechaza overrides Docker; no modifica el WIP.
2. No repite parse/evaluation/ambiguous: esos casos fueron parte del JIT V3 y no reportaron
   fallo. Corre dentro del contenedor fijado los siete casos sintéticos, incluida la expectativa
   corregida de secuencia exacta y las tres pruebas del reporter. Requiere colección exacta y
   PASS de cada caso. Corre con
   imagen existente, `--pull=never`, red deshabilitada, rootfs read-only, UID 1001, capabilities
   removidas y límites ya fijados.
3. Si todos los casos pasan, lee una vez el ID de la imagen sintética y verifica que la imagen
   F1 allowlisted no declare volúmenes (`.Config.Volumes`); no lee su digest. Después lee/valida
   una vez el contenedor F1. El helper compara todos los campos allowlisted de la política;
   leer campos no equivale a PASS si hay discrepancia.
4. Solo con el resultado exacto sintético y F1 en `OK`, revalida los manifiestos y ejecuta r9
   una vez, con timeout del runner. Descarta todo stdout/stderr de r9; solo expone
   `phase=r9|error_code=OK` o `phase=r9|error_code=CHECK_FAILED` y su código numérico de salida.

Cualquier error, resultado inesperado o timeout detiene las fases restantes y consume la
aprobación. No hay retry. No ejecuta `docker context inspect` ni repite consultas de la
atestación; r9 incluye su propio preflight previsto. No usa `/proc`, no llama `sudo`, no lee ni
modifica `studiamatch-dev`, no hace pull/build/instalación/cambio/cleanup de Docker, no toca
secretos, SQL, ramas o recursos externos. No autoriza copia, Pages/workerd, C03 integrado,
publicación, PR, merge, Settings o despliegues.

## Salida sanitaria exacta requerida

```text
phase=prior-desktop-wsl-endpoint-attestation|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-tests|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=OK
phase=r9|error_code=OK
```

La salida parcial solo puede contener pares fase/código de la allowlist cerrada del runner y
`exit=<n>`. Un par desconocido se sustituye por `phase=output-capture|error_code=OUTPUT_REJECTED`;
no se imprime stdout/stderr de los diagnósticos, de r9 o metadata cruda.

## Pines

- JIT: verificar SHA-256 del archivo antes de solicitar/aplicar aprobación.
- Runner combinado V4: `771f7e58d5981c81c8b0d861eb3df9b7636c665e6941f47295644d2ed97936c0`.
- Clasificador V4: `ebbc1aedf4120d053d0336a45e2e11daef2b7d97417ce90276d24b4238777292`.
- Runner sintético V4: `378f353e47192e1f7564091d56e59a101d0cee7063cd7fdb26e648ccfb7d21a9`.
- Test sintético acotado: `369382daa3445999704d85278a482edf78648a61a8e1ef3703ace37a2b923199`.
- Helper V2 allowlisted: `5ae493c50559b588ac9e40f49f54376da82c50af73b1bacf2e4133611136c90f`.
- Testimonio V3 endpoint/identidad: `8e6360143d15e47c819beb540edd69bd2a08634ac85b9267d03fd61c5c5ac33a`.
- Runner r9: `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`.
- Manifiestos r9/tools: `b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866` y
  `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.

Los pines de este bloque son estables una vez aprobado. No ejecutar si rama, HEAD, ID de imagen
sintética, paquete o cualquiera de los hashes no coincide.

## Comando único — terminal Ubuntu WSL interactiva

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_classifier_v4_then_r9_once.sh'
readonly RUNNER_SHA256='771f7e58d5981c81c8b0d861eb3df9b7636c665e6941f47295644d2ed97936c0'
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
IFS= read -r -p 'Copia solo fases/códigos sanitizados y exit; presiona Enter para cerrar: ' _ || true
exit "$runner_status"
)
```

La aprobación de este JIT cubre solo la invocación indicada y sus etapas condicionales. No
reutilizar aprobaciones de F2d, diagnósticos anteriores ni del JIT V3/V4 ya consumidos.
