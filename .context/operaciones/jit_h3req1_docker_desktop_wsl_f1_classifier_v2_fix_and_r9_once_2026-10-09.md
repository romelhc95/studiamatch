# JIT — classifier V2 corregido, una lectura F1 y r9 condicional

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-FIX-AND-R9-ONCE-20261009-V1`  
Estado: **preparado; requiere aprobación exacta; no ejecutado**.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Motivo de esta solicitud

El JIT previo `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-AND-R9-ONCE-20261008-V1`,
SHA-256 `c2f9414cea67402af76727b3c240982d1c264252569ab94aea9dedc47c687a66`, fue aprobado y
consumido una vez. Endpoint pasó; las pruebas sintéticas fallaron; F1 y r9 no se alcanzaron.
Su resultado se conserva en
[la evidencia del corte](../evidencia/h3req1_c03_f1_classifier_v2_synthetic_failure_2026-10-09.md).

La revisión del test reveló que la prueba unitaria de `main()` dejaba activa la orquestación
`run_synthetic_tests()`, que intenta lanzar Docker anidado desde el contenedor pytest sin socket
montado. Se corrigió únicamente el fixture para sustituir esa orquestación por no-op dentro de
esa prueba. El runner exterior sigue ejecutando los casos V2 en el contenedor efímero fijado.
No se ejecutaron las pruebas después del cambio y el fallo no se presume resuelto hasta que el
nuevo runtime lo demuestre.

## Alcance de una invocación

Ejecutor: `romel` en terminal interactiva Ubuntu WSL, sin `sudo`.

1. Comprueba checkout, rama, HEAD, hashes fijados y ausencia de overrides Docker.
2. Atestigua el endpoint Docker Desktop WSL y que el Engine reporta Linux.
3. Ejecuta los casos `v2` del clasificador en un contenedor efímero de la imagen existente
   `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`, con
   `--pull=never`, sin red, rootfs read-only, UID 1001, capacidades removidas, límites de
   recursos, `/tmp` efímero y solo `/diag` montado read-only. No se monta socket Docker en ese
   contenedor. Su salida se suprime y el wrapper emite fase/código.
4. Solo si los sintéticos pasan, lee la imagen F1 allowlisted y hace un único inspect del
   contenedor F1 fijado. No guarda ni imprime stdout, stderr ni metadata cruda.
5. Solo si endpoint, sintéticos, imagen y contenedor emiten exactamente `OK` y los controles F1
   coinciden con la allowlist, ejecuta una vez r9 con sus manifiestos, imagen y límites fijados.

Cualquier error consume esta autorización e impide la siguiente fase; no hay retry. No ejecuta
F2d ni un inspect con formato alternativo; no consulta `/proc`, rebuild/pull/instala Docker, no
toca `studiamatch-dev`, no crea recursos persistentes, no cambia SQL, secretos, settings,
workflow, ramas, GitHub, Pages o despliegues. El contenedor sintético y el contenedor de r9 son
efímeros (`--rm`). Este JIT no autoriza copia completa, arranque Pages/workerd, C03 integrado,
UAT final, publicación, PR, merge ni configuración remota.

## Pines

- Runner combinado:
  `tests/h3req1_docker_peer_substep_diag/run_wsl_f1_classifier_v2_then_r9_once.sh`  
  SHA-256 `3212b44753d26bf5f52da1835adc88d872e7e63fa630549a9bd00683ebd8c362`.
- Runner diagnóstico:
  `tests/h3req1_docker_peer_substep_diag/run_wsl_f1_read_classification_v2_once.sh`  
  SHA-256 `97b5e9e0e3493594bad68022be40035880d01d12d6947104f0eadf22445d5452`.
- Helper V2: SHA-256 `018f179ffca763b0c328c6ee973f0cbc6ef3370bb5895860970e416c2a5a6408`.
- Pruebas sintéticas: SHA-256 `67ac4da3ab79dbce7b6a09d1b34597c2f070ba5abb89c72058b7b74cd8930487`.
- Desktop helper: SHA-256 `c25aa3d3d91bb0cadc160b090c49c4bc61362baefaf3415d046ce7a9cabea4cb`.
- Proyector F1: SHA-256 `794b49ce5560c8cacebbd403c05b4cdbe78fd0c0062d30b6690b901838831463`.
- Helper V1 fijado: SHA-256 `b84e46250823a0a7f3c73bf0bbd3359147585dea7d1c4b8ef322d87a1c12d4fc`.
- r9 runner: SHA-256 `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`.
- r9 package manifest: SHA-256 `b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866`.
- tools manifest: SHA-256 `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.

El SHA-256 de este documento se entrega para la aprobación y no se embebe en el propio archivo.
El wrapper vuelve a comprobar los pins antes de ejecutar.

## Comando único — Ubuntu WSL interactiva

Ejecutar una vez después de aprobar este JIT. La shell conserva el TTY, aplica el timeout total
y hace pausa visible para copiar únicamente fases/códigos y el estado r9.

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_classifier_v2_then_r9_once.sh'
readonly RUNNER_SHA256='3212b44753d26bf5f52da1835adc88d872e7e63fa630549a9bd00683ebd8c362'

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
IFS= read -r -p 'Copia las fases sanitizadas y el resumen r9; presiona Enter para cerrar: ' _ || true
exit "$runner_status"
)
```

Compartir solo `phase=…|error_code=…`, exit del wrapper y resumen de r9. No copiar stderr,
metadata Docker, output de tests, rutas privadas ni valores de entorno. Un fallo consume este
JIT; no ejecutar el bloque nuevamente.
