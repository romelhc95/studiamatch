# JIT H3REQ1 — cutover reversible a `studiamatch-dev` y limpieza selectiva (V5 dispatch)

Fecha: 2026-10-09. Estado: requiere aprobación humana nueva para una invocación. El JIT Docker
V4 anterior fue aprobado y consumido antes de cualquier comando Docker: el archivo `.log` que
creó está excluido por Git, por lo que el conteo quedó 55/267/0 mientras el ejecutor esperaba
55/268/0. Este paquete corrige solo la precondición de WIP y usa un log V5 nuevo. No reutiliza
aquella aprobación ni cambia la imagen, el override, los recursos o la secuencia autorizada.

ID: `H3REQ1-DOCKER-CANDIDATE-CUTOVER-V5-ONCE-20261009-V1`.

## Objetivo y candidato

Usar como runtime habitual el candidato local ya construido si supera identidad y health check.
Mantener el checkout original como rollback. Después de registrar evidencia sanitizada y health
PASS, retirar contenedores históricos y redes vacías exactos. El runtime R4 fallido y sus dos
redes se conservan para recuperación.

| Elemento | Identidad fijada |
|---|---|
| Checkout / rama / HEAD | `/home/romel/src/studiamatch-h3req1-sync-20261002` / `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| WIP | 55 rutas tracked modificadas, 268 entradas untracked (incluye este JIT; el log `*.log` está ignorado), 0 staged |
| Runtime anterior | ID `115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`; `studiamatch-dev:local`; bind `/home/romel/src/studiamatch:/app`; volumen `studiamatch_node_modules`; estado read-only observado `restarting`, política `unless-stopped` |
| Imagen del candidato | `studiamatch-h3req1:20261009-v3`, ID `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`; se reutiliza localmente |
| Imagen original | `studiamatch-dev:local`, preservada para rollback; no se modifica ni elimina |
| Contenedor node-deps original | `studiamatch-node-deps`, ID `20f9f5a75ebce7fb7f890f50577a00edb8fb29f0c15b928bffd3f08414c21e16`; `exited`, imagen `studiamatch-dev:local`; se conserva |
| Provisionador del candidato | `studiamatch-h3req1-node-deps`, servicio Compose `node-deps`, imagen V3 fijada; debe finalizar `exited/0` |
| Volumen candidato | crear `studiamatch_h3req1_node_modules` solo si está ausente; provisionar desde `/opt/node-staging` de la imagen, sin npm install |
| Red del proyecto candidato | crear `studiamatch-h3req1_default` si está ausente; bridge Compose normal |
| Log de salida | crear una vez `.context/evidencia/h3req1_docker_candidate_cutover_v5_once_2026-10-09.log`; solo fases/códigos y exit |

## Inputs y configuración

El runner verifica estos SHA-256 antes de mutar:

| Input | SHA-256 |
|---|---|
| `Dockerfile` | `241b149f521c8133fc2bed5f40eac16c6eaa16e63a2fbee7c81382f6c39d9012` |
| `init-container.sh` | `8dd14ad53e9b23b6741786f1b2716707b2577d78d2e2791a68f1f95deaa173ca` |
| `requirements-pipeline.txt` | `922db6ec7a6cf13978ab9e3f27ecc4e82b3e1d8807c0b519cea0ab7608ba1bf0` |
| `web/package.json` | `4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a` |
| `web/package-lock.json` | `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc` |
| `docker-compose.yml` | `70ecf0a27054cec54151eee1b01957450f70abf6be6a6019e35104d7bb681575` |
| Compose override V4 | `b05df1ada0dae130284e9f97ddb1c9c4780276140e1d7d0dafe31bf0931e8290` |
| Runner | `a36a06f976c835a38796fb68e165e24ede3ed2de583443ad79d0f1644d775ba0` |

El override cambia solo el tag del servicio a la imagen fijada, da nombre distinto al
provisionador, mapea el volumen de dependencias a `studiamatch_h3req1_node_modules`, liga el
puerto a `127.0.0.1:3000` y reemplaza `env_file` del `app` por la ruta existente
`/home/romel/src/studiamatch/.env.local`. El `node-deps` recibe únicamente package/lock
read-only y el volumen; no recibe env_file. El candidato no tiene `.env.local`. El runner comprueba
lectura de la fuente y `docker compose config --quiet`; no imprime ni guarda valores. El contenedor
`app` candidato sí cargará el env_file normal del desarrollo. Codex no leerá ni expondrá sus
valores.

No se ejecuta build, pull, npm install, apt, PyPI ni descarga de Chromium. `docker compose up`
usa `--no-build --pull never`; `init-container.sh` copia dependencias ya staged a un volumen
nuevo. El runtime y el provisionador usan el bridge Compose normal, que permite egress; el JIT
no instala un firewall. No se solicita egress ni se llama a servicios remotos: el healthcheck
único de `/admin/login/` es local. La app podrá hacer llamadas externas si se invocan sus rutas
después; esos flujos no están en esta autorización.

## Secuencia, recursos y recuperación

Una invocación única, como `romel` no-root en Ubuntu WSL interactiva, `timeout` total de 600 s
más 120 s para terminar rollback. El ejecutable fijado es
`tests/h3req1_docker_peer_substep_diag/docker_candidate_cutover_v5.sh`.

1. Comprueba rama, HEAD, WIP `55/268/0`, hashes, digest de imagen, ausencia de los nombres/
   volumen/red candidatos, identidad/montajes del contenedor original, fuente de env_file y
   `docker compose config --quiet`. Cualquier discrepancia termina sin cutover ni cleanup.
2. Cambia restart policy del ID anterior a `no`, lo detiene y renombra a
   `studiamatch-original-dev-20261009`.
3. Ejecuta solo `docker compose up -d --no-build --pull never node-deps app` con el checkout
   candidato. El provisionador copia módulos del staging de la imagen al volumen nuevo. El app
   publica solo en loopback.
4. Espera hasta 300 s por health `healthy` y valida digest, tag, labels de proyecto/servicio,
   bind candidato, volumen nuevo y `node-deps` exited/0. Antes del cleanup, el runner persiste
   esas fases en el archivo sanitizado.
5. Si falla antes de health PASS, el trap inspecciona identidad y montajes: detiene y renombra un
   candidato propio a `studiamatch-h3req1-failed-20261009-v3`, devuelve el nombre
   `studiamatch-dev` al ID original, restaura `unless-stopped` y lo inicia si estaba detenido.
   Conserva el candidato fallido y volumen para evidencia. Si la identidad es ambigua, no mueve
   el recurso y emite `RECOVERY_INCOMPLETE`.
6. Solo después del health PASS, del hash existente del log R4 y de la validación exacta, puede
   retirar estos 11 contenedores históricos, sin `-v`:

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

   It may also remove only the three empty internal networks after verifying their exact IDs,
   `Internal=true`, and zero attachments:

   ```text
   h3req1-jit-internal-20261005         f54379669c125d32f02120b0c0f74d07b56cf3df8c973a3ae6c869e0cf8646b9
   h3req1-jit-internal-v3-20261005      da6a40654b6cc5af86a38b9df73fe873814a0b249f1ded6d03ed5426ca4ddbe7
   h3req1-jit-internal-v4-20261005      f8851397653ad3eb5f013331de5bb947a6b74f338ba813c3fb233855a73daa3c
   ```

The failed R4 runtime `b8aff87745e80a82265be0019be5530e9173fc621ab3ff47754f85e933a1508f`, its
six named volumes, and `h3req1-c03-integrated-edge-20261006-r4` plus
`h3req1-c03-integrated-data-20261006-r4` remain untouched. `studiamatch_node_modules`, the
candidate image, original image, all other images, and every volume remain. No global prune,
`docker rm -v`, volume deletion, SQL, suite H3/r9, remote Git, PR/merge, CI setting, or deploy.

## Comando único

```bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/docker_candidate_cutover_v5.sh"
readonly RUNNER_SHA256='a36a06f976c835a38796fb68e165e24ede3ed2de583443ad79d0f1644d775ba0'
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
exec /usr/bin/timeout --foreground --signal=TERM --kill-after=120s 600s /bin/bash "$RUNNER"
```

Un FAIL, timeout, hash/preflight mismatch o rollback incompleto consume la invocación. No hay
retry. El log de salida contiene únicamente `phase=...|error_code=...` y el código de salida.
