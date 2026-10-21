# JIT — revalidación actionlint y continuación r9 — V4 — 2026-10-09

**ID:** `H3REQ1-G03-R9-ACTIONLINT-DIAGNOSTIC-AND-CONTINUATION-V4-ONCE-20261009-V1`  
**Estado:** preparado; requiere aprobación humana para una invocación.

## Hallazgo y corrección local

La invocación V3 aprobada se ejecutó una vez y quedó consumida, exit 1. Preflight, extracción,
copia aislada y los nueve sintéticos del clasificador dieron `OK`. `actionlint` encontró un
error reproducible en `.github/workflows/security-audit.yml:330:0`, regla `syntax-check`. La
línea 330 era el terminador del heredoc `H3_LOCAL_PATHS` en columna cero dentro de un bloque
YAML `run: |`; la línea 331 (`)`) también estaba fuera del bloque. Ambas líneas se indentan diez
espacios para que YAML las mantenga dentro del literal y el shell reciba el terminador en columna
cero después de retirar la indentación común. Ninguna otra línea de workflow cambia en esta
corrección.

La comparación con el paquete V3 identifica exactamente esas dos líneas. `git diff --check` y
`bash -n` para el nuevo runner y el helper interior pasan. Esto es revisión estática; no declara
`actionlint` PASS. La lectura actionlint V3 ya está consumida y no se repite bajo esa autorización.

## Candidato e inputs fijados

- Rama/HEAD/WIP esperado después de agregar este JIT: `feat/h3req1-sync-20261002` /
  `4eb4d877a50b012bb630a129bd0c74482c33be9c` / `55/275/0`.
- Package: `/tmp/h3req1-g03-validation-29d8fff9-r5`; se deriva del r4 preservado y difiere en
  el único workflow corregido. El diff de ese archivo contiene solo la indentación del terminador
  del heredoc y el cierre de la sustitución.
- Package-manifest SHA-256:
  `5363610a5fd28558f3e2168dd926aaf1c26037d01b2645de815da7201c00b0ae`.
- Inputs-manifest SHA-256:
  `290905c8c88f56ce8c17aaf112e6536185068ea644008c685f299beeaeb1c57b`.
- Tools manifest SHA-256:
  `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.
- Candidate workflow SHA-256: `276641005c0bc1dc64b26e479b9ef197137a69b3dc4b08be8e56246fdb75df23`.
- Imagen local: `studiamatch-h3req1:20261009-v3`, ID
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- `studiamatch-dev`: ID
  `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`, `running/healthy`;
  volumen de dependencias `studiamatch_h3req1_node_modules`, solo lectura.
- Runner host:
  `tests/h3req1_docker_peer_substep_diag/run-r9-actionlint-continuation-v4.sh`, SHA-256
  `405f587a759fbc4f0d646c3b045db05949743cf3548d4dd33792a0a3dbf6d32a`.
- Helper interior sin cambios:
  `tests/h3req1_docker_peer_substep_diag/run-r9-actionlint-inner-v2.sh`, SHA-256
  `eaacd68e4a7d5ec9ec66f36f730f8c6ab0a308aa5962f1282ddaaf21506ae8cb`.

Los manifests del package r5 y inputs pasan `sha256sum -c`; los inputs mantienen 68 fuentes
presentes y tres auxiliares package-only. El runner revalida rama, HEAD, WIP, 68 hashes fuente,
manifests, imagen, estado/labels del contenedor y volumen antes de usar Docker.

## Una ejecución condicionada

Como `romel` no-root en terminal Ubuntu WSL interactiva, timeout total 180 s:

1. Verificar identidad, WIP, hashes y manifests fijados.
2. Ejecutar los nueve sintéticos del clasificador y una vez `actionlint -oneline` sobre los
   mismos tres workflows: `security-audit.yml`, `protected-workflow-integrity.yml` y
   `db-sync-to-pro.yml`.
3. Si actionlint falla, detener y conservar solo los campos sanitizados
   `workflow`, `line`, `column` y `rule`, o el código allowlisted del parser. No conservar ni
   mostrar la línea cruda.
4. Solo si actionlint pasa, continuar en orden con ShellCheck de siete scripts/hooks,
   `npm run lint`, `tsc --noEmit`, `tests/test_protected_workflow_review.py`,
   `tests/test_scan_credentials.sh` y `tests/test_protected_path_scope_guard.sh`.
5. Solo la secuencia completa `ALL_REMAINING_CHECKS_OK` seguida de revisión sin hallazgos puede
   cerrar G03. El runner no declara GO_LOCAL_PR.

Usa un único contenedor temporal `--rm --pull=never --network=none --read-only`, UID 1001,
cap-drop, no-new-privileges, límites de CPU/memoria/PIDs y mounts read-only del package, tools,
helper y volumen candidato. No lee `.env*`, secretos, DB, F1 ni checkout writable; no muta
`studiamatch-dev`, imágenes, volúmenes, redes, producto ni recursos remotos. Cada fallo/timeout
consume la autorización; sin retry. Si timeout impide retirar el contenedor efímero, no se
inspecciona ni limpia sin autorización separada.

## Comando único

```bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/run-r9-actionlint-continuation-v4.sh"
readonly RUNNER_SHA256='405f587a759fbc4f0d646c3b045db05949743cf3548d4dd33792a0a3dbf6d32a'
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

Este JIT no autoriza F1, copia completa, Pages/workerd, Edge/PG17/PostgREST/C03 integrado,
aceptación UAT, auditoría npm, publicación, PR, configuración remota, merge ni despliegues.
