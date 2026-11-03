# JIT — rebuild selectivo y cutover reversible del runtime candidato

Fecha: 2026-10-09. Estado: preparado; **requiere aprobación humana agrupada antes de mutar Docker**.

## Objetivo

Construir una sola imagen con los manifests del candidato actual y habilitar ese checkout
como el contenedor habitual `studiamatch-dev`. El contenedor homónimo actual pertenece al
checkout `/home/romel/src/studiamatch`; se conserva como rollback y se renombra solo después
de validar la imagen nueva. No se sustituye el runtime fijado de C03 por `studiamatch-dev`.
El JIT no ejecuta suites H3 ni usa el contenedor habitual como entorno de prueba aislada.

## Evidencia que justifica la reparación

El `studiamatch-dev` actual (`115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`)
está `restarting`, usa `studiamatch-dev:local` / imagen
`sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0` y monta el checkout
original. La imagen staged conserva hashes antiguos distintos tanto del checkout original
como del candidato. El guard en `init-container.sh` compara esos hashes y termina ante el
desfase; el usuario ya observó esas líneas de error. La causa demostrada es ese rechazo de
manifests para el init descrito; no se afirma que explique cada reinicio dinámico.

La imagen base `node:20-bookworm` ya está presente como
`sha256:8f693eaa7e0a8e71560c9a82b55fd54c2ae920a2ba5d2cde28bac7d1c01c9ba5`. No se hará pull.
El tag nuevo `studiamatch-h3req1:20261009-v1`, el volumen
`studiamatch_h3req1_node_modules` y `studiamatch-h3req1-node-deps` no existían al preparar
este JIT; se revalidan inmediatamente antes de ejecutar y cualquier colisión detiene.

## Ficha de impacto y recursos exactos

| Recurso/archivo | Efecto permitido bajo este JIT |
|---|---|
| Imagen | Crear solo `studiamatch-h3req1:20261009-v1`; no modificar tag ni bytes de `studiamatch-dev:local`. Base local Node 20 Bookworm, pin/ID arriba. |
| Contexto de build | Temporal propio en `/tmp`, copias allowlisted de `Dockerfile`, `init-container.sh`, `requirements-pipeline.txt`, `web/package.json`, `web/package-lock.json`. Nunca enviar el checkout completo, `.env*`, `.git`, secretos o WIP de pruebas. Retirar solo ese contexto temporal tras guardar los hashes/exit sanitizados. |
| Contenedor anterior | Identidad exacta `115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`; cambiar restart policy a `no`, detener y renombrar a `studiamatch-original-dev-20261009`. Se preservan imagen y contenedor para rollback. No borrar. |
| Contenedor candidato habitual | `studiamatch-dev`, servicio `app`; bind únicamente al candidato `/home/romel/src/studiamatch-h3req1-sync-20261002:/app`; publicar `127.0.0.1:3000:3000`; comprobar healthcheck de `/admin/login/`. |
| Provisionador único | `studiamatch-h3req1-node-deps`, servicio `node-deps`, solo env UID/GID, binds read-only de `web/package.json` y lock más el volumen node_modules; no monta el checkout completo ni `.env.local`. Retirar el contenedor one-shot tras conservar resultado. |
| Volúmenes | Crear/usar solo `studiamatch_h3req1_node_modules`; preservar intacto `studiamatch_node_modules`. No borrar ningún volumen. |
| Red | Crear solo la red Compose `studiamatch-h3req1_default`, necesaria para el proyecto candidato; no conectar otros proyectos. |
| Checkout original | Se mantiene íntegro y montado en el contenedor renombrado de rollback hasta cierre. No modificar fuentes. |

La configuración Compose se validó sin resolver valores de entorno con Compose 5.5.1. El
servicio habitual `app` toma `.env.local` conforme al Compose existente; esta ejecución solo
arranca el entorno de desarrollo ordinario y no imprime variables. **No usar sus credenciales
reales en pruebas aisladas:** C03, Edge, PG17, PostgREST y runners de aceptación conservarán
contenedores/red/fixtures separados con valores sintéticos. Esos servicios no forman parte de
este JIT.

## Inputs fijados

La invocación recalcula estos hashes y se detiene ante cualquier delta:

| Input | SHA-256 |
|---|---|
| `Dockerfile` | `34dc73ac9e5548b7c794e0987b8b2681ce26458a61b7d372f1146a4613f2f1c4` |
| `init-container.sh` | `8dd14ad53e9b23b6741786f1b2716707b2577d78d2e2791a68f1f95deaa173ca` |
| `requirements-pipeline.txt` | `922db6ec7a6cf13978ab9e3f27ecc4e82b3e1d8807c0b519cea0ab7608ba1bf0` |
| `web/package.json` | `4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a` |
| `web/package-lock.json` | `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc` |
| `docker-compose.yml` | `70ecf0a27054cec54151eee1b01957450f70abf6be6a6019e35104d7bb681575` |
| Override candidate | `32997839538f071219fe6174f3d20f2a0481ecb25b25e1cc3816f53d19fd48c0` |

El hash de `requirements-pipeline.txt` se verificó con `sha256sum` y tiene 64 hexadecimales.

## Egress, límites y validación

- Sin `--pull`; si la imagen base local falta o su ID difiere, detenerse y pedir autorización
  nueva. Una sola construcción para el tag único. No `docker compose build` sobre el checkout
  completo.
- Egress solo durante build, a repos Debian/apt, índice y artefactos PyPI usados por
  `pip --require-hashes`, `registry.npmjs.org` para `npm ci`, y CDN de Playwright para Chromium.
  No se inicia un navegador contra sitio externo. La imagen usa Node 20, Python 3.11 y Chromium
  conforme al Dockerfile/requirements. No se puede fijar una allowlist estable de mirror/CDN
  por este Dockerfile; residual explícito del build.
- Timeout máximo del build: 1800 s; si excede, fallo consumido. No hay retry. El Docker build
  no tiene cgroup CPU/mem límite propio en Compose; el alcance se limita a una imagen, un
  build y ausencia de pull/prune, pero el uso total del daemon queda como residual MEDIUM.
- Verificar en un contenedor efímero de la imagen nueva, con `--pull=never --network=none`,
  rootfs read-only, sin mounts/env/secretos, los dos hashes staged, Node/npm, Python/pip y
  disponibilidad del paquete Playwright. Registrar solo valores allowlisted y exits.
- Tras validar imagen: actualizar restart policy del contenedor antiguo a `no`, stop 10 s,
  renombrarlo, y ejecutar Compose `-p studiamatch-h3req1` con el override y `--no-build` para
  provisionar volumen, iniciar el app y verificar healthcheck. El puerto solo queda en loopback.
- Retirar con `docker compose rm -f node-deps` únicamente el one-shot propio ya completado.
  Mantener imagen, candidato, red, volumen nuevo, contenedor rollback, volumen original y
  `studiamatch-dev:local`. Sin prune ni rm de históricos fuera de la lista exacta y condicionada
  que sigue; sin eliminación de volumen, fuente o DB.
- Evidencia: exit por fase, ID/tag/digest de imagen, hashes staged, versión de herramientas,
  container ID/nombre/health, volumen/red exactos, transición de nombre del contenedor rollback
  y salida de los checksums. No capturar Env, logs crudos, valores de `.env.local` ni inspect
  completos.

## Orden, fallos y recuperación

1. Revalidar rama/HEAD/WIP, 7 hashes, imagen base, identidad del contenedor original, restart
   policy, puerto 3000 y ausencia de colisiones en todos los nombres candidatos. Cualquier drift
   detiene antes de mutar.
2. Crear contexto allowlisted temporal y construir/verificar imagen. Si build o verificación
   falla, no detener/renombrar el original, no arrancar Compose y no reintentar. Preservar el
   exit sanitizado y el tag generado para decisión posterior.
3. Solo tras PASS de imagen: cambiar policy del original a no, stop y rename exactos; luego
   `docker compose ... up -d --no-build node-deps app` y esperar salud hasta 180 s. No continuar
   si el healthcheck falla.
4. Si el cutover falla, detener el candidato si está activo, renombrarlo
   `studiamatch-h3req1-failed-20261009`, renombrar el original a `studiamatch-dev`, restaurar
   policy `unless-stopped` y arrancarlo. Preservar imagen y volumen candidato para inspección;
   no borrar recursos ni reintentar.
5. Si PASS, retirar solo el one-shot `node-deps` creado por esta invocación, dejar `studiamatch-dev`
   saludable para trabajo habitual y conservar el original detenido como rollback hasta aceptación.
   Cualquier limpieza del contenedor/volumen original queda para un JIT exacto posterior.

### Limpieza histórica agrupada para simplificar el mismo entorno Docker

Tras PASS del app candidato y solo si existen los documentos históricos citados en la
[evidencia de inventario](../evidencia/h3req1_v15_docker_sql_ci_reconciliation_2026-10-09.md),
este mismo objetivo puede retirar los siguientes objetos exactos. Todos se observaron
`exited`, sin volúmenes persistentes; PG17 usó tmpfs y runners solo binds read-only. Se
preservan sus imágenes y los archivos de resultados.

| Objeto exacto | Imagen/version | ID esperado | Acción única |
|---|---|---|---|
| `h3req1-node22-jit-20261005` | Node 22 `sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | `8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c` | `docker rm 8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c` |
| `h3req1-node22-jit-v2-20261005` | Node 22 `sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | `544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02` | `docker rm 544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02` |
| `h3req1-pg17-jit-v3-20261005` | PostgreSQL 17 `sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f` | `51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a` | `docker rm 51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a` |
| `h3req1-pg17-jit-v4-20261005` | PostgreSQL 17 `sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f` | `4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27` | `docker rm 4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27` |
| `h3req1-postgrest-jit-20261005` | PostgREST v13.0.7 `sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228` | `4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6` | `docker rm 4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6` |
| `h3req1-c03-safe-suspend-pg17-20261005` | PostgreSQL 17 `sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f` | `88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d` | `docker rm 88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d` |

El PG v2 histórico no existe y no se recrea. Revalidar cada ID, nombre, `exited`, restart
count, imagen y ausencia de volúmenes inmediatamente antes; una divergencia detiene el
cleanup completo. Después de retirar contenedores, quitar únicamente estas redes si siguen
`Internal=true` y vacías:

| Red exacta | ID esperado | Acción única |
|---|---|---|
| `h3req1-jit-internal-20261005` | `f54379669c125d32f02120b0c0f74d07b56cf3df8c973a3ae6c869e0cf8646b9` | `docker network rm h3req1-jit-internal-20261005` |
| `h3req1-jit-internal-v3-20261005` | `da6a40654b6cc5af86a38b9df73fe873814a0b249f1ded6d03ed5426ca4ddbe7` | `docker network rm h3req1-jit-internal-v3-20261005` |
| `h3req1-jit-internal-v4-20261005` | `f8851397653ad3eb5f013331de5bb947a6b74f338ba813c3fb233855a73daa3c` | `docker network rm h3req1-jit-internal-v4-20261005` |

### Residuales exactos del C03 integrado R4

La consulta read-only de los nombres fijados en `tests/h3req1_c03_integrated_drill.sh`
encontró cinco auxiliares `exited/0` y un runtime fallido `exited/1`. El log que conserva el
FAIL de healthz existe en `.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log`,
SHA-256 `208e42cb55cd7de5d74a9960655ac3cdec6accbeab1fc5f00a7a3e8eb047eb34`. El bootstrap
PG17/PostgREST/Edge no se alcanzó. El candidato de runtime fallido se **preserva** porque el
log no identifica causa raíz y puede contener diagnóstico recuperable; el JIT no lee sus
logs ni su Env.

| Nombre exacto | ID exacto | Imagen fijada | Estado/restart | Montajes y acción |
|---|---|---|---|---|
| `h3req1-c03-bootstrap-miniflare-20261006-r4` | `dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36` | `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | `exited/0`, restart 0 | Dos named volumes R4 → `/out`, `/source`; retirar contenedor con `docker rm ID` sin `-v`. |
| `h3req1-c03-bootstrap-pages-deps-20261006-r4` | `8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb` | `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | `exited/0`, restart 0 | Dos named volumes R4 → `/out`, `/source`; retirar contenedor con `docker rm ID` sin `-v`. |
| `h3req1-c03-bootstrap-edge-deps-20261006-r5` | `d6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929` | `denoland/deno:2.1.4@sha256:bc48369c9b1810da957cabcac234094a691f94cb6cd0e88d533ccac89f2f0cb9` | `exited/0`, restart 0 | Tres named volumes R4/R5 → `/deno-cache`, `/source`, `/source/supabase/functions/admin-invite/node_modules`; retirar contenedor sin `-v`. |
| `h3req1-c03-dependency-cache-verify-20261006-r4` | `94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4` | `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | `exited/0`, restart 0 | Cinco named volumes R4/R5 de solo lectura; retirar contenedor sin `-v`. |
| `h3req1-c03-source-snapshot-20261006-r4` | `e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4` | `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | `exited/0`, restart 0 | Named volume `h3req1-c03-integrated-source-snapshot-20261006-r4` → `/snapshot`; retirar contenedor sin `-v`. |
| `h3req1-c03-integrated-runtime-20261006-r4` | `b8aff87745e80a82265be0019be5530e9173fc621ab3ff47754f85e933a1508f` | `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | `exited/1`, restart 0 | Seis named volumes R4/R5; **preservar contenedor y montajes** por diagnóstico healthz no resuelto. |

Las redes R4 `h3req1-c03-integrated-edge-20261006-r4` (ID
`b1f633b40c7b11bdce27eed62eecade67609b66fc327ffd6e92d413788cd78dc`) y
`h3req1-c03-integrated-data-20261006-r4` (ID
`da562797a7a6323bde4094cf08905f4f8f7f20cbdc4f498eb34425b07219ca75`) se observaron
`Internal=true`, 0 endpoints; retirar sus nombres exactos solo tras revalidar ID,
`Internal=true` y cero endpoints. Los seis volúmenes R4/R5 nombrados arriba se conservan;
no `docker volume rm`, no `docker rm -v`, no limpieza por prefijo. El PG17, PostgREST y los
dos Edge R4 active/suspended estaban ausentes. No se amplía inventario a recursos no citados
por ese runner.

No se elimina la red `bridge`, images/pins, tags, `studiamatch_node_modules`, el contenedor
rollback, ninguna fuente ni otros contenedores. Si falla una eliminación o la red presenta
un endpoint, parar y conservar el resto; no ampliar el selector.

### Comandos exactos del rebuild y cutover

Antes de mutar Docker, desde el root del candidato, comprobar los siete pins, base local y
colisiones exactas. Todo `HASH_MISMATCH`, tag/volumen/red/contenedor candidato preexistente,
imagen base distinta, checkout/ID/policy/mount del contenedor anterior distinto, o puerto
3000 ocupado por otro ID detiene el paquete sin mutación:

```bash
set -Eeuo pipefail
readonly CANDIDATE='/home/romel/src/studiamatch-h3req1-sync-20261002'
cd "$CANDIDATE"
[[ "$(git branch --show-current)" == 'feat/h3req1-sync-20261002' ]]
[[ "$(git rev-parse HEAD)" == '4eb4d877a50b012bb630a129bd0c74482c33be9c' ]]
python3 - <<'PY'
import subprocess
raw=subprocess.check_output(['git','status','--porcelain=v1','-z'])
entries=[e for e in raw.split(b'\0') if e]
tracked=sum(e[:2] != b'??' for e in entries)
untracked=sum(e[:2] == b'??' for e in entries)
staged=sum(e[:1] not in (b' ',b'?') for e in entries)
if (tracked,untracked,staged) != (54,232,0):
    print('phase=candidate-wip|error_code=STATUS_DRIFT')
    raise SystemExit(1)
print('phase=candidate-wip|error_code=OK')
PY
sha256sum -c <(cat <<'HASHES'
34dc73ac9e5548b7c794e0987b8b2681ce26458a61b7d372f1146a4613f2f1c4  Dockerfile
8dd14ad53e9b23b6741786f1b2716707b2577d78d2e2791a68f1f95deaa173ca  init-container.sh
922db6ec7a6cf13978ab9e3f27ecc4e82b3e1d8807c0b519cea0ab7608ba1bf0  requirements-pipeline.txt
4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a  web/package.json
8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc  web/package-lock.json
70ecf0a27054cec54151eee1b01957450f70abf6be6a6019e35104d7bb681575  docker-compose.yml
32997839538f071219fe6174f3d20f2a0481ecb25b25e1cc3816f53d19fd48c0  .context/operaciones/h3req1_docker_candidate_override_2026-10-09.yml
HASHES
)
[[ "$(docker image inspect --format '{{.Id}}' node:20-bookworm)" == \
  'sha256:8f693eaa7e0a8e71560c9a82b55fd54c2ae920a2ba5d2cde28bac7d1c01c9ba5' ]]
if docker image inspect studiamatch-h3req1:20261009-v1 >/dev/null 2>&1; then exit 1; fi
if docker volume inspect studiamatch_h3req1_node_modules >/dev/null 2>&1; then exit 1; fi
if docker network inspect studiamatch-h3req1_default >/dev/null 2>&1; then exit 1; fi
for name in studiamatch-h3req1-node-deps studiamatch-original-dev-20261009 \
  studiamatch-h3req1-failed-20261009; do
  if docker inspect "$name" >/dev/null 2>&1; then exit 1; fi
done
readonly OLD_ID='115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a'
[[ "$(docker inspect --format '{{.Id}}|{{.Config.Image}}|{{.HostConfig.RestartPolicy.Name}}' studiamatch-dev)" == \
  "$OLD_ID|studiamatch-dev:local|unless-stopped" ]]
mounts="$(docker inspect --format '{{range .Mounts}}{{.Type}}|{{.Source}}|{{.Destination}};{{end}}' "$OLD_ID")"
[[ "$mounts" == *'bind|/home/romel/src/studiamatch|/app;'* ]]
[[ "$mounts" == *'volume|/var/lib/docker/volumes/studiamatch_node_modules/_data|/app/web/node_modules;'* ]]
published="$(docker ps --no-trunc --filter publish=3000 --format '{{.ID}}' | sort -u)"
[[ -z "$published" || "$published" == "$OLD_ID" ]]
```

La identidad del contenedor anterior, el bind `/home/romel/src/studiamatch:/app`, el volumen
`studiamatch_node_modules` y el puerto se comparan con los valores de este JIT; el nombre
`studiamatch-dev` debe resolver únicamente al ID anterior. El nombre de red
`studiamatch-h3req1_default` también debe estar libre.

Con esos checks PASS, formar el contexto temporal allowlisted con solo los cinco archivos de
build y conservar en evidencia los checksums:

```bash
set -Eeuo pipefail
readonly CANDIDATE='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BUILD_CONTEXT="$(mktemp -d /tmp/h3req1-docker-build-v1.XXXXXX)"
readonly INPUT_MANIFEST="${BUILD_CONTEXT}.inputs.sha256"
mkdir -p "$BUILD_CONTEXT/web"
cp -- "$CANDIDATE/Dockerfile" "$CANDIDATE/init-container.sh" \
  "$CANDIDATE/requirements-pipeline.txt" "$BUILD_CONTEXT/"
cp -- "$CANDIDATE/web/package.json" "$CANDIDATE/web/package-lock.json" \
  "$BUILD_CONTEXT/web/"
(
  cd "$CANDIDATE"
  sha256sum -c <(cat <<'HASHES'
34dc73ac9e5548b7c794e0987b8b2681ce26458a61b7d372f1146a4613f2f1c4  Dockerfile
8dd14ad53e9b23b6741786f1b2716707b2577d78d2e2791a68f1f95deaa173ca  init-container.sh
922db6ec7a6cf13978ab9e3f27ecc4e82b3e1d8807c0b519cea0ab7608ba1bf0  requirements-pipeline.txt
4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a  web/package.json
8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc  web/package-lock.json
HASHES
  )
)
(
  cd "$BUILD_CONTEXT"
  sha256sum -c <(cat <<'HASHES'
34dc73ac9e5548b7c794e0987b8b2681ce26458a61b7d372f1146a4613f2f1c4  Dockerfile
8dd14ad53e9b23b6741786f1b2716707b2577d78d2e2791a68f1f95deaa173ca  init-container.sh
922db6ec7a6cf13978ab9e3f27ecc4e82b3e1d8807c0b519cea0ab7608ba1bf0  requirements-pipeline.txt
4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a  web/package.json
8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc  web/package-lock.json
HASHES
  )
  sha256sum Dockerfile init-container.sh requirements-pipeline.txt \
    web/package.json web/package-lock.json > "$INPUT_MANIFEST"
  sha256sum -c "$INPUT_MANIFEST"
)
```

Con esos checksums PASS, ejecutar una sola vez:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=10s 1800s \
  docker build --pull=false --build-arg STUDIAMATCH_UID=1000 --build-arg STUDIAMATCH_GID=1000 \
  --tag studiamatch-h3req1:20261009-v1 "$BUILD_CONTEXT"
```

Validar el tag nuevo offline sin montar fuentes ni pasar variables:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 60s \
  docker run --rm --pull=never --network=none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m --user 1000:1000 \
  --entrypoint /bin/bash studiamatch-h3req1:20261009-v1 -lc \
  'cd /opt/node-staging/web && printf "%s  %s\n%s  %s\n" 7f42e397a859d7d5108f1f17a613e8722493ecfb368c25dd4a12b0e414e7e7bb package.json a6f707e516fbb0d4dc3067b809573b9ac64d8543c54dfe28998cd13901bf4ccf package-lock.json | sha256sum -c - && node --version && npm --version && /opt/venv/bin/python --version && /opt/venv/bin/python -m playwright --version'
```

Solo con todos los resultados esperados, renombrar el contenedor viejo bajo su ID verificado
y luego arrancar el proyecto candidato sin rebuild:

```bash
docker update --restart=no 115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a
docker stop --time 10 115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a
docker rename 115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a studiamatch-original-dev-20261009
STUDIAMATCH_UID=1000 STUDIAMATCH_GID=1000 docker compose --env-file /dev/null \
  -p studiamatch-h3req1 -f docker-compose.yml \
  -f .context/operaciones/h3req1_docker_candidate_override_2026-10-09.yml \
  up -d --no-build node-deps app
```

Esperar hasta 180 s al healthcheck con este bucle acotado; solo imprimir estado allowlisted:

```bash
deadline=$((SECONDS + 180))
while :; do
  health="$(docker inspect --format '{{.State.Health.Status}}' studiamatch-dev 2>/dev/null || true)"
  if [[ "$health" == healthy ]]; then
    printf 'phase=candidate-health|error_code=OK\n'
    break
  fi
  if [[ "$health" == unhealthy || "$health" == '' || $SECONDS -ge $deadline ]]; then
    printf 'phase=candidate-health|error_code=HEALTHCHECK_FAILED\n'
    exit 1
  fi
  sleep 5
done
```

Tras PASS, conservar hashes/exit en la evidencia y retirar el contexto temporal exacto y el
one-shot propio sin volumen:

```bash
[[ "$BUILD_CONTEXT" == /tmp/h3req1-docker-build-v1.* && -d "$BUILD_CONTEXT" ]] || exit 1
[[ "$INPUT_MANIFEST" == /tmp/h3req1-docker-build-v1.*.inputs.sha256 && -f "$INPUT_MANIFEST" ]] || exit 1
rm -rf -- "$BUILD_CONTEXT"
rm -f -- "$INPUT_MANIFEST"
STUDIAMATCH_UID=1000 STUDIAMATCH_GID=1000 docker compose --env-file /dev/null \
  -p studiamatch-h3req1 -f docker-compose.yml \
  -f .context/operaciones/h3req1_docker_candidate_override_2026-10-09.yml \
  rm -f node-deps
```

Solo después de `candidate-health/OK`, la limpieza histórica autorizada se limita a las
tablas anteriores. Revalidar primero el archivo R4 por SHA y cada contenedor mediante
`docker inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.RestartCount}}'`;
para los seis recursos antiguos, exigir también que el listado de mounts no contenga tipo
`volume`. Para los cinco auxiliares R4 y el runtime R4 fallido, comparar exactamente el
mapa volume/name/destination/RW fijado abajo. El runtime fallido se deja intacto. Validar
primero los 11 contenedores y las cinco redes; no empieza ningún `rm` hasta que todo el
preflight pase. Después retirar los 11 IDs de contenedor enumerados con `docker rm <ID exacto>`
**sin `-v`**, y solo después las cinco redes exactas. Ante cualquier mismatch o error, no
iniciar cleanup; ante error de una eliminación, detener la secuencia. No borrar los seis
volúmenes R4/R5 ni inspeccionar sus contenidos.

```bash
set -Eeuo pipefail
readonly R4_LOG='.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log'
readonly R4_LOG_SHA256='208e42cb55cd7de5d74a9960655ac3cdec6accbeab1fc5f00a7a3e8eb047eb34'
r4_log_hash="$(sha256sum "$R4_LOG" 2>/dev/null | cut -d' ' -f1)" || {
  printf 'phase=cleanup-preflight|error_code=R4_EVIDENCE_READ_FAILED\n'
  exit 1
}
[[ "$r4_log_hash" == "$R4_LOG_SHA256" ]] || {
  printf 'phase=cleanup-preflight|error_code=R4_EVIDENCE_HASH_MISMATCH\n'
  exit 1
}

verify_container() {
  local id="$1" expected="$2" actual
  if ! actual="$(docker inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.RestartCount}}' "$id" 2>/dev/null)"; then
    printf 'phase=cleanup-preflight|error_code=CONTAINER_READ_FAILED\n'
    return 1
  fi
  if [[ "$actual" != "$expected" ]]; then
    printf 'phase=cleanup-preflight|error_code=CONTAINER_MISMATCH\n'
    return 1
  fi
}
verify_no_named_volumes() {
  local id="$1" volumes
  if ! volumes="$(docker inspect --format '{{range .Mounts}}{{if eq .Type "volume"}}volume;{{end}}{{end}}' "$id" 2>/dev/null)"; then
    printf 'phase=cleanup-preflight|error_code=MOUNT_READ_FAILED\n'
    return 1
  fi
  if [[ -n "$volumes" ]]; then
    printf 'phase=cleanup-preflight|error_code=UNEXPECTED_VOLUME\n'
    return 1
  fi
}
verify_mount_map() {
  local id="$1" expected="$2" actual
  if ! actual="$(docker inspect --format '{{range .Mounts}}{{.Type}}|{{.Name}}|{{.Destination}}|{{.RW}};{{end}}' "$id" 2>/dev/null | tr ';' '\n' | sed '/^$/d' | sort)"; then
    printf 'phase=cleanup-preflight|error_code=MOUNT_READ_FAILED\n'
    return 1
  fi
  expected="$(printf '%s\n' "$expected" | sed '/^$/d' | sort)"
  if [[ "$actual" != "$expected" ]]; then
    printf 'phase=cleanup-preflight|error_code=VOLUME_MAP_MISMATCH\n'
    return 1
  fi
}
verify_network() {
  local name="$1" expected_id="$2" actual
  if ! actual="$(docker network inspect --format '{{.Id}}|{{.Internal}}|{{len .Containers}}' "$name" 2>/dev/null)"; then
    printf 'phase=cleanup-preflight|error_code=NETWORK_READ_FAILED\n'
    return 1
  fi
  if [[ "$actual" != "$expected_id|true|0" ]]; then
    printf 'phase=cleanup-preflight|error_code=NETWORK_MISMATCH\n'
    return 1
  fi
}

verify_container 8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c \
  '8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c|/h3req1-node22-jit-20261005|node:22@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|255|0'
verify_container 544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02 \
  '544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02|/h3req1-node22-jit-v2-20261005|node:22@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|255|0'
verify_container 51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a \
  '51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a|/h3req1-pg17-jit-v3-20261005|postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f|exited|255|0'
verify_container 4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27 \
  '4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27|/h3req1-pg17-jit-v4-20261005|postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f|exited|255|0'
verify_container 4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6 \
  '4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6|/h3req1-postgrest-jit-20261005|postgrest/postgrest:v13.0.7@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228|exited|255|0'
verify_container 88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d \
  '88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d|/h3req1-c03-safe-suspend-pg17-20261005|postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f|exited|255|0'
for id in 8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c \
  544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02 \
  51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a \
  4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27 \
  4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6 \
  88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d; do
  verify_no_named_volumes "$id"
done
verify_container dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36 \
  'dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36|/h3req1-c03-bootstrap-miniflare-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|0|0'
verify_mount_map dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36 $'volume|h3req1-c03-integrated-miniflare-node-modules-20261006-r4|/out|true\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/source|false'
verify_container 8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb \
  '8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb|/h3req1-c03-bootstrap-pages-deps-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|0|0'
verify_mount_map 8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb $'volume|h3req1-c03-integrated-pages-node-modules-20261006-r4|/out|true\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/source|false'
verify_container d6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929 \
  'd6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929|/h3req1-c03-bootstrap-edge-deps-20261006-r5|denoland/deno:2.1.4@sha256:bc48369c9b1810da957cabcac234094a691f94cb6cd0e88d533ccac89f2f0cb9|exited|0|0'
verify_mount_map d6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929 $'volume|h3req1-c03-integrated-edge-deno-cache-20261006-r5|/deno-cache|true\nvolume|h3req1-c03-integrated-edge-node-modules-20261006-r5|/source/supabase/functions/admin-invite/node_modules|true\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/source|true'
verify_container 94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4 \
  '94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4|/h3req1-c03-dependency-cache-verify-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|0|0'
verify_mount_map 94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4 $'volume|h3req1-c03-integrated-edge-deno-cache-20261006-r5|/deno-cache|false\nvolume|h3req1-c03-integrated-edge-node-modules-20261006-r5|/edge-node-modules|false\nvolume|h3req1-c03-integrated-miniflare-node-modules-20261006-r4|/tools|false\nvolume|h3req1-c03-integrated-pages-node-modules-20261006-r4|/web-deps|false\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/source|false'
verify_container e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4 \
  'e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4|/h3req1-c03-source-snapshot-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|0|0'
verify_mount_map e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4 $'volume|h3req1-c03-integrated-source-snapshot-20261006-r4|/snapshot|true'
verify_container b8aff87745e80a82265be0019be5530e9173fc621ab3ff47754f85e933a1508f \
  'b8aff87745e80a82265be0019be5530e9173fc621ab3ff47754f85e933a1508f|/h3req1-c03-integrated-runtime-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|1|0'
verify_mount_map b8aff87745e80a82265be0019be5530e9173fc621ab3ff47754f85e933a1508f $'volume|h3req1-c03-integrated-edge-deno-cache-20261006-r5|/deno-cache|false\nvolume|h3req1-c03-integrated-edge-node-modules-20261006-r5|/candidate/supabase/functions/admin-invite/node_modules|false\nvolume|h3req1-c03-integrated-miniflare-node-modules-20261006-r4|/tools|false\nvolume|h3req1-c03-integrated-pages-node-modules-20261006-r4|/web-deps|false\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/candidate|false\nvolume|h3req1-c03-integrated-tls-20261006-r4|/run/c03-certs|true'

verify_network h3req1-jit-internal-20261005 f54379669c125d32f02120b0c0f74d07b56cf3df8c973a3ae6c869e0cf8646b9
verify_network h3req1-jit-internal-v3-20261005 da6a40654b6cc5af86a38b9df73fe873814a0b249f1ded6d03ed5426ca4ddbe7
verify_network h3req1-jit-internal-v4-20261005 f8851397653ad3eb5f013331de5bb947a6b74f338ba813c3fb233855a73daa3c
verify_network h3req1-c03-integrated-edge-20261006-r4 b1f633b40c7b11bdce27eed62eecade67609b66fc327ffd6e92d413788cd78dc
verify_network h3req1-c03-integrated-data-20261006-r4 da562797a7a6323bde4094cf08905f4f8f7f20cbdc4f498eb34425b07219ca75
printf 'phase=cleanup-preflight|error_code=OK\n'

cleanup_container() {
  local id="$1" ordinal="$2"
  if docker rm "$id" >/dev/null 2>&1; then
    printf 'phase=cleanup-container-%02d|error_code=OK\n' "$ordinal"
  else
    printf 'phase=cleanup-container-%02d|error_code=REMOVE_FAILED\n' "$ordinal"
    return 1
  fi
}
ordinal=0
for id in \
  8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c \
  544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02 \
  51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a \
  4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27 \
  4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6 \
  88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d \
  dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36 \
  8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb \
  d6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929 \
  94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4 \
  e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4; do
  ordinal=$((ordinal + 1))
  cleanup_container "$id" "$ordinal"
done

cleanup_network() {
  local name="$1" ordinal="$2"
  if docker network rm "$name" >/dev/null 2>&1; then
    printf 'phase=cleanup-network-%02d|error_code=OK\n' "$ordinal"
  else
    printf 'phase=cleanup-network-%02d|error_code=REMOVE_FAILED\n' "$ordinal"
    return 1
  fi
}
ordinal=0
for network in \
  h3req1-jit-internal-20261005 \
  h3req1-jit-internal-v3-20261005 \
  h3req1-jit-internal-v4-20261005 \
  h3req1-c03-integrated-edge-20261006-r4 \
  h3req1-c03-integrated-data-20261006-r4; do
  ordinal=$((ordinal + 1))
  cleanup_network "$network" "$ordinal"
done
printf 'phase=cleanup|error_code=OK\n'
```

El bloque de cleanup retira solo los once IDs auxiliares `exited` anteriores (seis de
históricos previos y cinco R4) y las cinco redes exactas; preserva el runtime R4 fallido,
las seis named volumes R4/R5, la imagen/tag, todos los otros volúmenes y cualquier recurso
fuera de estas listas. Ante cualquier mismatch o error de `rm`, detener la secuencia; no
continuar con más objetos ni ampliar el selector.

Si el cutover falla, validar la identidad del contenedor candidato y detenerlo; renombrarlo
`studiamatch-h3req1-failed-20261009`, renombrar el anterior al nombre `studiamatch-dev`,
restaurar policy `unless-stopped` y arrancar el ID anterior. Esto restaura el estado previo
conocido (que puede volver a `restarting` por el desfase ya demostrado), no declara saludable
el checkout original. No ejecutar cleanup histórico si el app candidato no llegó a health
PASS; no borrar la imagen, volumen ni contexto que se necesiten para analizar el fallo.

El paquete no ejecuta r9, copia completa, Pages/workerd, Edge, PG17/PostgREST, SQL, UAT,
onboarding, CI remoto ni operaciones Git/Cloudflare/Supabase. Esas fases mantienen sus propios
gates y aprobaciones; no se interpretará el healthcheck de login como cierre H3.

## Solicitud concreta

Se solicita una aprobación agrupada para **una invocación única de simplificación Docker**
descrita en este documento: rebuild selectivo con contexto allowlisted, cutover reversible
del contenedor exacto actual, creación del volumen/red candidatos, arranque del app y retiro
del one-shot propio, más retiro condicionado de los once contenedores históricos exactos y las
cinco redes internas exactas de las tablas. No autoriza borrar imágenes/tags, volúmenes persistentes, el
contenedor de rollback, `bridge`, fuentes o recursos fuera de esas listas, ni ejecutar pruebas
de producto.

Ejecutor: Codex en el candidato indicado mediante la herramienta Docker autorizada del entorno,
sin `sudo`; después de aprobación se repetirá el preflight íntegro. Un error o timeout consume
la invocación y detiene las etapas posteriores.
