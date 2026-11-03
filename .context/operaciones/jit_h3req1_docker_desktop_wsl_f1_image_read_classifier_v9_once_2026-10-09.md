# JIT — clasificar lectura de imagen sintética y aislar template V9

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-IMAGE-READ-CLASSIFIER-V9-ONCE-20261009-V1`
Estado: preparado; requiere autorización explícita; una invocación.
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Predicado que motiva esta invocación

V8 fue aprobado y consumido. Su salida fue `prior-endpoint-attestation|OK` y
`synthetic-image-read|SYNTHETIC_IMAGE_UNAVAILABLE`, exit 1. La lectura usa el mismo digest
sintético que V7 había leído correctamente; esa salida previa no demuestra disponibilidad
actual. El código V8 convierte cualquier non-zero a un solo código y no conserva la causa.

V9 prepara clasificación acotada de stderr en memoria para una única lectura exacta de la misma
imagen: imagen no encontrada, acceso denegado, Engine no disponible, error de template o fallback
cerrado. No escribe el texto crudo ni lee metadata fuera del formato fijo.

## Alcance agrupado — una invocación

Ejecutor: `romel` no-root en terminal Ubuntu WSL interactiva con `require_escalated`, sin `sudo`.

1. Comprueba el checkout, la rama/HEAD, los hashes V7/V8 y todos los fuentes V8/V9.
2. Reutiliza la atestación anterior de endpoint/sock­et como evidencia, sin repetir esa conexión.
3. Ejecuta una sola vez `docker image inspect --format '{{.Id}}|{{json .Config.Volumes}}'`
   contra el digest sintético `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`.
   argv exacto, timeout 15 s, stdout máximo 256 bytes y stderr máximo 4096 bytes en memoria.
   Códigos cerrados; stderr se descarta tras clasificación.
4. Solo si ID y volumen-free coinciden, ejecuta catorce casos focales (cinco V8 ya preparados más
   nueve V9 de clasificación, argumentos exactos, límites stdout/stderr, timeout y cleanup) en un
   contenedor temporal del mismo digest, con `--pull=never`,
   sin red, rootfs read-only, UID 1001, capabilities removidas, recursos acotados y montaje
   de diagnósticos read-only.
5. Solo si pasan los catorce casos, hace el probe V8 ya preparado: un contenedor sintético
   temporal y hasta 25 expresiones allowlisted de `docker inspect`, stdout descartado y errores
   sanitizados. El contenedor se elimina por `--rm` y el runner lo detiene en su cleanup.

El wrapper acepta fases y códigos desde listas cerradas; rechaza códigos sintácticamente válidos
pero no enumerados. Cualquier FAIL o timeout consume la autorización y detiene la etapa. Sin retry, pull, build,
install, Docker config changes, lectura F1, r9, `studiamatch-dev`, copia, Pages/workerd, SQL,
Supabase, CI remoto, Auth, Cloudflare o datos operativos. Aun con `ALL_FIELDS_OK`, el resultado
solo localiza la falla anterior; no cierra F1 ni un gate H3REQ1.

## Evidencia permitida

Solo fases y códigos allowlisted, por ejemplo `IMAGE_NOT_FOUND`, `DOCKER_ACCESS_DENIED`,
`DOCKER_ENGINE_UNAVAILABLE` o `IMAGE_INSPECT_FAILED`; nunca texto Docker, valores del Engine,
IDs/nombres temporales ni metadata. El error no-cero del inspect se clasifica solo en memoria.

## Digests fijados

- Resultado V7: `80332dca12db2c0a38692cc833d7cabd3a0feb47abf614e3aa7fdda7e6fce72d`.
- Resultado V8: `461e1fb24dfc6eabe2ee9f5a680acf911365abfd4ebe3a278ccb081b487c748d`.
- JIT V8: `b63ad5cf046625af7f2fff26e65343b54068e40f1489d8f2df6c2f883bd005a5`.
- At­estación previa de endpoint: `8e6360143d15e47c819beb540edd69bd2a08634ac85b9267d03fd61c5c5ac33a`.
- Probe V8: `498bb484854bd86d3b67d1ed3586d391cf7690b822aec7caac84c184299a9c24`.
- Clasificador V9: `19189d5012290dc971fab501c37a01390af49fc89a549653ab8e3cd44826b9b8`.
- Tests V9: `d92f7d37bec04469f8be017be9dfff63f80dfcb810ccee052aa4eebf4a3796c1`.
- Runner de tests V9: `49d29b60dc66366d78b9022837abc1e525dcc9a42644f0e9a9f3ae71d343b88a`.
- Runner agrupado V9: `d8d01088cfc6207ab7a224829e4eb3804dd6fa536cd41d112d00bd3d4cc0edb1`.
- Wrapper WSL V9: `2f12d0afe106b49ed2dba68a5403783837b6883bfc329384112424a718a1e2b3`.

Si cualquier pin, preflight, código sintético o condición difiere, detenerse sin operación Docker.

## Comando único — terminal Ubuntu WSL interactiva

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_template_expression_probe_v9_once.sh'
readonly RUNNER_SHA256='2f12d0afe106b49ed2dba68a5403783837b6883bfc329384112424a718a1e2b3'
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
hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || {
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
}
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
exec /usr/bin/timeout --foreground --signal=TERM --kill-after=5s 450s /bin/bash "$RUNNER" 2>/dev/null
)
```

La autorización cubre exclusivamente esta invocación. No habilita una lectura F1 ni r9.
