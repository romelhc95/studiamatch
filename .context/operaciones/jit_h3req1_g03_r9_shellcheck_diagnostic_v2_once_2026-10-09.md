# JIT — diagnóstico sanitizado ShellCheck r9 V2 — 2026-10-09

**ID:** `H3REQ1-G03-R9-SHELLCHECK-DIAGNOSTIC-V2-ONCE-20261009-V1`  
**Estado:** preparado; requiere aprobación humana para una invocación.

## Hecho precedente y corrección

El JIT ShellCheck diagnóstico V1, SHA-256
`138629c2b2a94bbd5207c764909a2a5909749e0965a5ac5a0b5169cab7ded8b2`, recibió aprobación y
se consumió una vez. El contexto, sintéticos y extracción de herramienta pasaron; la ejecución
ShellCheck terminó `OUTPUT_INVALID`, exit 1. V1 descartó la forma de la respuesta real y no
conservó diagnósticos, por lo que no se atribuye un código/archivo específico ni se repite.

La especificación oficial confirma que `json1` es un objeto con propiedad `comments`; el arreglo
es el formato legado `json` ([manual oficial](https://github.com/koalaman/shellcheck/blob/master/shellcheck.1.md)).
V1 esperaba un arreglo y su sintético trataba el objeto `json1` válido como inválido. Esto ofrece
una causa compatible con `OUTPUT_INVALID`, pero la salida real de V1 no se guardó para verificar
directamente esa forma. V2 corrige el parser y sus casos sintéticos para el objeto `json1`.

## Candidato e inputs fijados

- Rama/HEAD/WIP al preparar: `feat/h3req1-sync-20261002` /
  `4eb4d877a50b012bb630a129bd0c74482c33be9c` / `55/277/0`.
- Package r5: `/tmp/h3req1-g03-validation-29d8fff9-r5`; manifiesto
  `5363610a5fd28558f3e2168dd926aaf1c26037d01b2645de815da7201c00b0ae`; inputs
  `290905c8c88f56ce8c17aaf112e6536185068ea644008c685f299beeaeb1c57b`.
- Tools manifest: `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.
- Imagen local: `studiamatch-h3req1:20261009-v3`, ID
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- Runner SHA-256: `af9a9293248822778b69195f70c42db72fb919080e8cc8cd5e6e6345db0b7557`.
- Contenido interior SHA-256: `6392599b1271ee47ce89ed3c79dfc44522d31f98a41b0d844ae78b0d89ac2c32`.
- Clasificador `json1` SHA-256: `07a8401aa6a89275362e2456655ad79ec00ff6d3629da5059e851a2520cc38a4`.

El runner fija rama/HEAD/WIP, revalida los 68 archivos fuente y 3 archivos package-only, ambos
manifiestos, el endpoint Docker Desktop actual y el digest de imagen. Cualquier drift detiene la
invocación antes del contenedor.

## Una invocación y sus límites

Ejecutor: `romel`, usuario no-root, terminal interactiva Ubuntu WSL, timeout 120 s.

1. Extraer ShellCheck 0.11.0 del archivo local fijado en un contenedor aislado.
2. Ejecutar 34 pruebas sintéticas del clasificador: objeto `json1`, arreglo legado, raíz,
   comments, allowlist de rutas, coordenadas/códigos, límites, exit code y descarte de mensajes.
3. Si los sintéticos pasan, ejecutar ShellCheck una vez con `--format=json1` sobre los siete
   scripts allowlisted fijados en V1.
4. Clasificar sin retener ni emitir mensajes, texto crudo o contenido de archivos. La salida
   puede contener solo `phase`, `error_code`, ruta allowlisted, línea, columna, `SC####` y exit.

El contenedor usa la imagen y tool archive locales, `--pull=never --network=none --read-only`,
usuario 1001, capabilities eliminadas, no-new-privileges, límites CPU/memoria/PIDs y tmpfs de
tamaño fijado. Package, inputs, helper y clasificador van montados read-only. La copia de trabajo
y salida JSON existen únicamente en el contenedor efímero `--rm` y se destruyen al terminar.

No incluye `studiamatch-dev`, F1, r9 posterior, ESLint, TypeScript, suites, datos/SQL, secretos,
`.env*`, volúmenes, pull/build/install, egress, retry, cambios Docker persistentes, producto,
GitHub, Cloudflare, push/PR/merge, settings o deploy. No corrige automáticamente findings.
Si clasifica warnings, la invocación termina con exit 1 y evidencia sanitaria suficiente para
corregir solo los scripts/rules demostrados; se requerirá luego una validación r9 protegida por
un JIT propio si el ciclo no queda cubierto por otra autorización vigente.

**Cualquier fallo o timeout consume esta autorización; no hay reintento.**

## Comando único

```bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/run-r9-shellcheck-diagnostic-v2.sh"
readonly RUNNER_SHA256='af9a9293248822778b69195f70c42db72fb919080e8cc8cd5e6e6345db0b7557'
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
exec /usr/bin/timeout --foreground --signal=INT --kill-after=5s 120s /bin/bash "$RUNNER"
```
