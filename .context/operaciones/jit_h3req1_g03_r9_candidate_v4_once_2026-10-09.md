# JIT — r9 tooling del candidato en imagen Docker fijada — 2026-10-09

**ID:** `H3REQ1-G03-R9-CANDIDATE-V4-ONCE-20261009-V1`  
**Estado:** preparado; requiere aprobación humana para una invocación.

## Propósito y límite

Ejecutar una sola vez los checks locales de tooling afectados por el WIP H3REQ1, usando el
paquete r4 y la imagen candidata ya construida. Esto no instala ni activa el workflow PWI en
GitHub, no publica el patch de controles y no cambia ramas protegidas.

No incluye F1, limpieza Docker, build/pull/install, SQL, DB, cuentas, Auth, correo, push, PR,
merge, configuración GitHub/Cloudflare, despliegues ni suites de aceptación. No monta el
checkout ni `.env*`, no lee ni pasa secretos y no monta el socket Docker dentro del contenedor.

## Identidad e inputs fijados

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP preflight esperado: `55/270/0`; además, el wrapper compara hashes de las 68 rutas fuente
  existentes contra `inputs.sha256` y permite exactamente tres rutas auxiliares solo del paquete.
- Paquete aislado: `/tmp/h3req1-g03-validation-29d8fff9-r4`, 71 entradas; manifiestos
  `r4-package.sha256` SHA-256 `ca30a43c990e45e634412219c9a28d964b410068671c499048e80f2ff8c9068b` y
  `inputs.sha256` SHA-256 `b57603e8e75eb456a71e10ca45326c13e281ecb9e99b056ed163757c2292e2be`.
- Tools ya descargados y fijados, sin red en esta etapa:
  `/tmp/h3req1-g03-validation-29d8fff9-r2.tools/tools.sha256`, SHA-256
  `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.
- Runner: `tests/h3req1_docker_peer_substep_diag/run-r9-r4-candidate-image-sanitized.sh`,
  SHA-256 `5197e0f8be7583394903fbac629bee94ff55cd084130d8f1a8c78c0c958721ba`.
- Imagen local: `studiamatch-h3req1:20261009-v3`, image ID
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- Runtime precondicionado: `studiamatch-dev`, ID
  `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`, healthy; dependency
  volume `studiamatch_h3req1_node_modules`, montado solo lectura en el contenedor de prueba.
  El runner verifica ID/imagen/health/servicio antes de crear el contenedor efímero.

## Checks en orden, stop-on-failure

El wrapper verifica integridad de manifests/tools; rama, HEAD y WIP; y la igualdad de hashes de
las 68 rutas fuente actuales (68/71, cero drift; las tres auxiliares package-only permitidas son
`fetch-linters.sh`, `run-in-container.sh` y `run-r8.sh`). Comprueba endpoint Unix del contexto
`default`, imagen, candidato healthy y volumen de dependencias. Después crea un único contenedor
anónimo con `--rm --pull=never --network=none --read-only`, usuario 1001, capacidades retiradas,
`no-new-privileges`, 512 MiB, 1 CPU, 64 PIDs y tmpfs limitados. Inputs y tools se montan read-only;
la dependencia npm candidata también se monta read-only. No hay egress desde el contenedor.

En el scratch efímero dentro de ese contenedor se ejecutan, en secuencia:

1. Hashes de los 71 inputs y tools; extracción de actionlint 1.7.7/ShellCheck 0.11.0 en tmpfs.
2. Node `v20.20.2`, TypeScript `5.9.3`, manifiesto de dependencias y `next typegen` sobre la
   copia temporal antes de `tsc`.
3. actionlint para `security-audit.yml`, `protected-workflow-integrity.yml` y `db-sync-to-pro.yml`.
4. ShellCheck sobre los siete scripts fijados; `npm run lint`; `tsc --noEmit`.
5. pytest focal `tests/test_protected_workflow_review.py`,
   `tests/test_scan_credentials.sh` y `tests/test_protected_path_scope_guard.sh`.

El wrapper limita la salida a 2048 bytes y permite solo fases/códigos enumerados. stderr de los
checks no se conserva. La salida no contiene metadata Docker cruda ni valores de entorno.

## Ejecutor y comando único

Ejecutor: `romel`, no-root, en una terminal interactiva Ubuntu WSL del host Docker Desktop, sin
`sudo`. Timeout total 180 s. Un fallo, drift, salida no clasificada o timeout consume la
invocación y detiene el ciclo; no retry ni aumento de límites. `docker run --rm` retira el único
contenedor cuando termina; no se limpia ningún recurso preexistente. Si el timeout impidiera la
retirada automática, detenerse y pedir un JIT separado para inspeccionar/retirar solo el recurso
efímero de esta invocación.

```bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/run-r9-r4-candidate-image-sanitized.sh"
readonly RUNNER_SHA256='5197e0f8be7583394903fbac629bee94ff55cd084130d8f1a8c78c0c958721ba'
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
exec /usr/bin/timeout --foreground --signal=INT --kill-after=5s 180s /bin/bash "$RUNNER"
```

Esta aprobación no autoriza una segunda invocación ni el cambio/publicación/configuración del
control CI. Preservar fase, código sanitizado y exit real; sumar G03 solo si el conjunto completo
termina `ALL_CHECKS_OK` y la revisión del resultado no encuentra hallazgos.
