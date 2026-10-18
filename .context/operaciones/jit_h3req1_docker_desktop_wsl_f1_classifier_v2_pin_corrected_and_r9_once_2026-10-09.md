# JIT — classifier V2 con pin corregido, una lectura F1 y r9 condicional

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-PIN-FIX-AND-R9-ONCE-20261009-V1`  
Estado: **preparado; requiere aprobación exacta; no ejecutado**.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Motivo

La invocación aprobada de `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-FIX-AND-R9-ONCE-20261009-V1`,
SHA-256 `1cb4ad0dbf3f3928c88a62441c2806c8eff2358ff3970c1f07d5a787d8fd29b5`, se consumió una vez
y terminó `phase=classifier-v2-r9-preflight|error_code=DIAGNOSTIC_RUNNER_HASH_MISMATCH`, exit 1.
No ejecutó el diagnóstico interior, pruebas sintéticas, lectura F1 ni r9.

La causa quedó aislada por comparación estática: el runner combinado esperaba el SHA
`1fe0f175e6164e31e1562bac7c85604cc8e0711c7a2f47a6fdd476aa7f870a9b` para el runner diagnóstico;
el archivo fijado por el propio paquete/JIT tiene SHA
`97b5e9e0e3493594bad68022be40035880d01d12d6947104f0eadf22445d5452`. Se corrigió únicamente ese
pin. No se alteró lógica de Docker, helper, clasificador, test, F1, ni r9.

El usuario también reportó que `studiamatch-dev` muestra divergencia de hashes de
`web/package.json`/`web/package-lock.json` entre fuentes y la imagen staged. Esta invocación no
consulta, inicia, reconstruye ni modifica ese contenedor; el reporte queda como dependencia
separada, sin atribuirlo a la discrepancia del pin ni a la identidad Docker.

## Alcance de una invocación

Ejecutor: `romel` en Ubuntu WSL interactiva con TTY, sin `sudo`.

1. Comprueba checkout, rama, HEAD, hashes de diagnóstico y manifiestos r9, y ausencia de
   overrides Docker.
2. Atestigua el endpoint Docker Desktop WSL y que el Engine reporta Linux.
3. Ejecuta los casos sintéticos V2 en un contenedor efímero de la imagen fijada
   `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`, con `--pull=never`,
   sin red, rootfs read-only, UID 1001, capacidades removidas, límites de recursos, `/tmp`
   efímero y solo `/diag` montado read-only.
4. Solo tras synthetic `OK`, lee la imagen F1 allowlisted y ejecuta un único inspect del
   contenedor F1 fijado. No conserva ni imprime stdout, stderr ni metadata cruda.
5. Solo si endpoint, sintéticos, imagen y contenedor emiten exactamente `OK` y los controles
   F1 coinciden con la allowlist, ejecuta r9 una vez con imagen, tools y manifiestos fijados.

Cualquier fallo consume la autorización e impide la siguiente fase; no hay retry. No repite
F2d ni diagnósticos consumidos, no usa `/proc`, no hace pull/rebuild/instalación, no toca
`studiamatch-dev`, no crea recursos persistentes ni modifica SQL, secretos, settings, workflow,
ramas, GitHub, Pages o despliegues. Este JIT no autoriza copia completa, arranque
Pages/workerd, C03 integrado, UAT final, publicación, PR, merge ni configuración remota; las
etapas locales posteriores siguen sujetas a las autorizaciones ya vigentes y a sus propios
predicados.

## Pines

- Runner combinado corregido: SHA-256
  `d76fb2a8486baddbe04652a3f0e3bf08ce678e889c34607ed686b926820f0a53`.
- Runner diagnóstico: SHA-256
  `97b5e9e0e3493594bad68022be40035880d01d12d6947104f0eadf22445d5452`.
- Helper V2: SHA-256
  `018f179ffca763b0c328c6ee973f0cbc6ef3370bb5895860970e416c2a5a6408`.
- Pruebas sintéticas: SHA-256
  `67ac4da3ab79dbce7b6a09d1b34597c2f070ba5abb89c72058b7b74cd8930487`.
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

El SHA-256 de este JIT se comunica para aprobarlo y no se embebe en el propio archivo. El
comando externo y el runner verifican sus pins antes de continuar.

## Comando único — Ubuntu WSL interactiva

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_classifier_v2_then_r9_once.sh'
readonly RUNNER_SHA256='d76fb2a8486baddbe04652a3f0e3bf08ce678e889c34607ed686b926820f0a53'

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
IFS= read -r -p 'Copia las fases sanitizadas y el exit; presiona Enter para cerrar: ' _ || true
exit "$runner_status"
)
```

Compartir solo las líneas `phase=…|error_code=…` y el exit. No copiar stderr, metadata Docker,
stdout de pytest/r9, rutas privadas ni valores de entorno. Si hay fallo, conservar esa fase,
exit y evidencia del predicado sin reintentar.
