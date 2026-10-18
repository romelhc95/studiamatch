# JIT — continuar r9 desde actionlint con diagnóstico sanitizado — 2026-10-09 — V2

**ID:** `H3REQ1-G03-R9-ACTIONLINT-DIAGNOSTIC-AND-CONTINUATION-V2-ONCE-20261009-V1`  
**Estado:** preparado; requiere aprobación humana para una invocación.

## Reconciliación de V1

El JIT V1 SHA-256 `63c9cc7facec5233c46f9f7967847d851e56f7e1ba03f8ea74515ffd3f3185b1`
recibió aprobación, pero se detuvo antes de ejecutar el runner o Docker al detectar que su
ficha fijaba el helper interno con SHA `8c13d00a2ce5e58636b155e17bfcd09ecee0030e339507767f8580f2591acea5`,
mientras el helper presente y fijado por el runner aprobado tiene SHA
`65b5feae6661b868cb62ee8e23c28caaf862faa508f091cee3b2d81d6b109557`. V1 no se ejecutó ni
consumió su invocación; sus archivos se preservan. V2 corrige esa ficha, crea un runner separado
y fija el WIP resultante. No se alteró Docker ni se ejecutó actionlint.

## Motivo y límites

La invocación r9 anterior está consumida y terminó exit 1 en `r9-actionlint`. El wrapper
silenció stdout/stderr, por lo que no conservó archivo, línea o regla; no se atribuye el fallo a
un workflow ni se vuelve a correr el conjunto completo. Este JIT vuelve a ejecutar `actionlint`
una vez para los mismos tres workflows fijados y solo si pasa continúa con checks r9 que no se
alcanzaron: ShellCheck, ESLint, TypeScript y tres suites focales. Los pasos previos con PASS se
preservan; solo se repiten preflight de identidad, hashes, runtime y copia inmutable del
paquete como barreras de entrada.

No incluye F1, `studiamatch-dev` mutations, build/pull/install, npm audit, SQL/DB, cuentas,
Auth, secretos, `.env*`, socket Docker en el contenedor, publicación, Git remoto, PR, merge,
GitHub/Cloudflare configuration ni deploy. No corrige workflows por conjetura. Falla o timeout
consume esta autorización; no retry ni aumento de límites.

## Candidato e inputs fijados

- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP esperado al ejecutar: `55/273/0` (tracked/untracked/staged; incluye los JIT/runners V1 y V2,
  el patch pre-sync preservado y helpers ya preparados).
- Paquete r4: `/tmp/h3req1-g03-validation-29d8fff9-r4`, 71 inputs; package manifest
  `ca30a43c990e45e634412219c9a28d964b410068671c499048e80f2ff8c9068b`; inputs manifest
  `b57603e8e75eb456a71e10ca45326c13e281ecb9e99b056ed163757c2292e2be`.
- Tools: `/tmp/h3req1-g03-validation-29d8fff9-r2.tools`, manifest
  `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.
- Imagen local fijada: `studiamatch-h3req1:20261009-v3`, image ID
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- `studiamatch-dev`: ID
  `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`, servicio `app`,
  `running/healthy`; dependencia `studiamatch_h3req1_node_modules` montada solo lectura.
- Helper host:
  `tests/h3req1_docker_peer_substep_diag/run-r9-actionlint-continuation-v2.sh`, SHA-256 fijado
  por este JIT y validado abajo.
- Helper dentro del contenedor:
  `tests/h3req1_docker_peer_substep_diag/run-r9-actionlint-inner-v1.sh`, SHA-256
  `65b5feae6661b868cb62ee8e23c28caaf862faa508f091cee3b2d81d6b109557`.

El runner compara las 68 rutas fuente con el manifest y permite solo los tres helpers
package-only `fetch-linters.sh`, `run-in-container.sh` y `run-r8.sh`. Fija endpoint default Unix,
imagen, identidad/health del candidato y volumen antes de arrancar el contenedor.

## Ejecución condicionada

Como `romel` no-root en terminal Ubuntu WSL interactiva del host Docker Desktop, sin sudo,
timeout total 180 s:

1. Verificar branch/HEAD/WIP, SHA de ambos helpers, manifests, fuentes 68/71 y runtime fijado.
2. Ejecutar un solo contenedor efímero `--rm --pull=never --network=none --read-only`, usuario
   1001, cap-drop, no-new-privileges, límites fijados, mounts del paquete/tools/helper y volumen
   `node_modules` read-only. No se monta checkout writable, `.env*` ni el socket Docker.
3. Revalidar hashes de paquete/tools, hacer copia temporal y symlink read-only de dependencies.
4. Correr cinco sintéticos del clasificador de salida. Si fallan, detener.
5. Correr `actionlint -oneline` una vez en:
   `.github/workflows/security-audit.yml`,
   `.github/workflows/protected-workflow-integrity.yml` y
   `.github/workflows/db-sync-to-pro.yml`.
6. Si actionlint falla, emitir únicamente nombre de workflow, línea, columna y regla en lista
   allowlisted; no se expone texto crudo. Detener sin ejecutar los pasos restantes.
7. Si actionlint pasa, continuar sin repetir typegen ni pasos anteriores con ShellCheck sobre
   siete scripts/hooks, `npm run lint`, `tsc --noEmit`,
   `tests/test_protected_workflow_review.py`, `tests/test_scan_credentials.sh` y
   `tests/test_protected_path_scope_guard.sh`, en orden stop-on-failure.

stdout máximo 2048 bytes con fases/códigos allowlisted. stderr queda descartado. Un error de
captura, formato desconocido, drift, mismatch, timeout o resultado no allowlisted detiene el
ciclo. `docker run --rm` retira solo su contenedor; si timeout impidiera cleanup no se inspecciona
ni elimina recurso alguno sin JIT separado.

## Comando único

```bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/run-r9-actionlint-continuation-v2.sh"
readonly RUNNER_SHA256='a3171b16e29eddfade63b1369f11d5e924e08a490709d5f9277835a9dc58438f'
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

Solo un resultado completo `ALL_REMAINING_CHECKS_OK`, seguido de revisión sin hallazgos,
puede cerrar G03. Esta autorización no habilita F1, integración, UAT, publicación, PR,
configuración remota ni promoción.
