# JIT H3REQ1 — limpieza selectiva tras cutover saludable (V6)

Fecha: 2026-10-09. Estado: paquete preparado; requiere una autorización humana para una
invocación. El JIT V5 quedó consumido con health PASS y cleanup bloqueado por una expectativa
incorrecta de montaje. Este V6 corrige solo el predicado demostrado y ejecuta únicamente la limpieza
histórica ya delimitada; no repite el cutover.

ID: `H3REQ1-DOCKER-CANDIDATE-CLEANUP-V6-ONCE-20261009-V1`.

## Resultado que habilita esta solicitud

La invocación V5 dejó `studiamatch-dev` healthy con el checkout candidato, imagen V3 fijada y el
provisionador exit 0. El original sigue preservado como `studiamatch-original-dev-20261009`.
El preflight se detuvo antes de borrar recursos porque para el contenedor histórico
`d6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929` se esperaba el mount del
snapshot `/source` con `RW=true`, pero Docker devuelve `RW=false`. Los otros mapas comprobados
coinciden. El montaje actual es read-only. V6 cambia únicamente ese valor esperado y valida otra
vez el runtime, el rollback y todos los recursos exactos antes de mutar.

## Candidato y pins

| Elemento | Valor fijado |
|---|---|
| Checkout / rama / HEAD | `/home/romel/src/studiamatch-h3req1-sync-20261002` / `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| WIP antes de ejecutar | 55 tracked, 269 untracked, 0 staged; el log `*.log` está ignorado |
| Runtime habitual | `studiamatch-dev`, ID `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`, healthy |
| Imagen local | `studiamatch-h3req1:20261009-v3`, ID `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63` |
| Checkout/volumen candidato | Bind del checkout candidato en `/app`; volumen `studiamatch_h3req1_node_modules` en `/app/web/node_modules` |
| Rollback | `studiamatch-original-dev-20261009`, ID `115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`; imagen `studiamatch-dev:local`, checkout original y volumen `studiamatch_node_modules` |
| Provisionador | `studiamatch-h3req1-node-deps`, ID `1e9d942bd3236b9a2cb860976d7254583ef4ede953529e87b5a61cb67422e3d9`, exited/0 |
| Evidencia C03 R4 usada como pin | `.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log`, SHA-256 `208e42cb55cd7de5d74a9960655ac3cdec6accbeab1fc5f00a7a3e8eb047eb34` |
| Ejecutable | `tests/h3req1_docker_peer_substep_diag/docker_candidate_cleanup_v6.sh`, SHA-256 `37386e4a640618356f7cea8ac630ae298e8537380680255e4a4105e127214e63` |

La revisión del candidato queda limitada a ID, image ID/tag, estado/health, labels Compose y mounts
permitidos. La revisión del rollback queda limitada a ID, image, estado, política de reinicio y
mounts. No se leen `Config.Env`, archivos `.env*`, credenciales ni metadata inspect completa.

## Alcance autorizado solicitado

Una invocación como `romel` no-root en terminal Ubuntu WSL interactiva. El ejecutor comprueba rama,
HEAD, WIP, contexto Docker `default`, digest local, runtime candidate healthy y mounts exactos,
provisionador exit 0, rollback preservado, hash R4 y los IDs, imágenes, estados, exits, mounts y
redes de la lista histórica. Toda esa etapa es read-only. No ejecuta pruebas H3, r9, SQL, npm,
rebuild, pull, instalación, llamadas remotas, publicación, PR, merge ni deploy.

Solo si todos los predicados pasan, el runner puede retirar con `docker rm` (sin `-v`) estos once
contenedores detenidos:

```text
8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c
544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02
51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a
4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27
4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6
88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d
dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36
8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb
d6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929
94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4
e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4
```

After every container is removed, it may remove only these three networks if their IDs still match,
`Internal=true` and attachment count is zero:

```text
h3req1-jit-internal-20261005     f54379669c125d32f02120b0c0f74d07b56cf3df8c973a3ae6c869e0cf8646b9
h3req1-jit-internal-v3-20261005  da6a40654b6cc5af86a38b9df73fe873814a0b249f1ded6d03ed5426ca4ddbe7
h3req1-jit-internal-v4-20261005  f8851397653ad3eb5f013331de5bb947a6b74f338ba813c3fb233855a73daa3c
```

All six R4 volumes, the candidate and original volumes, every image, candidate runtime, original
rollback and all other resources remain. No prune, `docker rm -v`, volume/image removal, force
removal or wildcard/prefix cleanup. The historical container configs and evidence remain available
in the recorded packages and mounts; recreating any removed test container would require a separate
review/approval if later needed.

## Failure and recovery

Any failed identity, health, WIP, hash, state or mount check stops before the first removal and
consumes the invocation. Cleanup removal failure stops at that exact item; earlier removals in the
same invocation are not retried or automatically recreated. The active candidate and rollback
container remain untouched, with all images and named volumes preserved. The log contains only
allowlisted `phase=...|error_code=...` lines and exit. A timeout or failure consumes this JIT; no
retry is included.

## Comando único

```bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/docker_candidate_cleanup_v6.sh"
readonly RUNNER_SHA256='37386e4a640618356f7cea8ac630ae298e8537380680255e4a4105e127214e63'
if (( EUID == 0 )); then
  printf 'phase=dispatch-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -t 0 ]]; then
  printf 'phase=dispatch-preflight|error_code=INTERACTIVE_TTY_REQUIRED\n'
  exit 1
fi
if [[ "$(uname -s 2>/dev/null)" != Linux || "$(uname -r 2>/dev/null | tr '[:upper:]' '[:lower:]')" != *microsoft* ]]; then
  printf 'phase=dispatch-preflight|error_code=WSL_REQUIRED\n'
  exit 1
fi
runner_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || {
  printf 'phase=dispatch-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
}
if [[ "${runner_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=dispatch-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
exec /usr/bin/timeout --foreground --signal=TERM --kill-after=60s 180s /bin/bash "$RUNNER"
```

No se ejecuta hasta recibir aprobación para este ID, hash y alcance agrupado. El JIT V5 permanece
consumido, sin retry. La preparación, revisión estática y hashes no suman puntos G01–G10.
