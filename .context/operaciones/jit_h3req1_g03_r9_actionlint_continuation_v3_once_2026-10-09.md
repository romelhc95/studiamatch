# JIT — diagnóstico actionlint sanitizado y continuación r9 — V3 — 2026-10-09

**ID:** `H3REQ1-G03-R9-ACTIONLINT-DIAGNOSTIC-AND-CONTINUATION-V3-ONCE-20261009-V1`  
**Estado:** preparado; requiere aprobación humana para una invocación.

## Reconciliación

El r9 original (`d0a99744…`) pasó hasta Next typegen y consumió su invocación en
`r9-actionlint|CHECK_FAILED`; el wrapper entonces perdió el diagnóstico. La continuación V1 fue
aprobada, pero se detuvo antes del runner/Docker por un SHA del helper interior inconsistente en
su ficha; no se consumió. La continuación V2 (`a5fa34d31015440fcf3f3c0f164f6491702764c33f4a494a253c230a904c06e8`)
fue aprobada y ejecutada una vez. Preflight, extracción, copia y sintéticos pasaron; se detuvo en
`r9-actionlint-diagnostic|OUTPUT_UNCLASSIFIED`, exit 1. La salida cruda fue descartada. V2 está
consumido; no se repite.

El defecto demostrado en la herramienta es que su clasificador/serializador dejó la salida real
sin una clasificación recuperable. V3 limita el cambio al parser diagnóstico: tolera prefijo de
ruta, coordenadas de hasta seis dígitos incluido cero y un token de regla desconocido que se
normaliza a `unknown`; no captura el mensaje textual. Distingue salida vacía, formato no
reconocido, exceso, mismatch de exit y resultado interno desconocido. Nueve aserciones sintéticas
cubren relativo/absoluto/prefijado, regla ausente o no segura, ruta no permitida, salida vacía,
límite, mismatch y ausencia de texto crudo.

No se atribuye el fallo al producto ni a un workflow concreto. No se amplía cobertura más allá
de los tres workflows; no incluye F1, `studiamatch-dev` mutations, build/pull/install, npm audit,
SQL/DB, cuentas, Auth, secretos, `.env*`, checkout writable, socket Docker en el contenedor,
publicación, Git remoto, PR, merge, GitHub/Cloudflare configuration ni deploy. Cualquier FAIL o
timeout consume esta autorización; sin retry.

## Candidato e inputs fijados

- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP esperado: `55/274/0` (tracked/untracked/staged).
- Paquete r4: `/tmp/h3req1-g03-validation-29d8fff9-r4`, 71 inputs; package manifest
  `ca30a43c990e45e634412219c9a28d964b410068671c499048e80f2ff8c9068b`; inputs manifest
  `b57603e8e75eb456a71e10ca45326c13e281ecb9e99b056ed163757c2292e2be`.
- Tools: `/tmp/h3req1-g03-validation-29d8fff9-r2.tools`, manifest
  `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.
- Imagen local `studiamatch-h3req1:20261009-v3`, ID
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- Candidato `studiamatch-dev`: ID
  `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`, `running/healthy`;
  volumen de dependencias `studiamatch_h3req1_node_modules`, read-only.
- Runner host:
  `tests/h3req1_docker_peer_substep_diag/run-r9-actionlint-continuation-v3.sh`, SHA-256
  `64ec3666e944b8a88e79542dadd964eced42a4c40439662d32de6956f5fc83a4`.
- Helper interior:
  `tests/h3req1_docker_peer_substep_diag/run-r9-actionlint-inner-v2.sh`, SHA-256
  `eaacd68e4a7d5ec9ec66f36f730f8c6ab0a308aa5962f1282ddaaf21506ae8cb`.

El runner fija los 68 hashes fuente y tres helpers `package-only` del manifest, endpoint Docker
default, imagen, ID/health/labels del contenedor y volumen. Revalida WIP e inputs antes de
Docker. Ejecuta un solo contenedor `--rm --pull=never --network=none --read-only`, UID 1001,
cap-drop, no-new-privileges y límites fijados; mounts del paquete/tools/helpers y del volumen
`node_modules` son read-only.

## Ejecución condicionada

Como `romel` no-root en Ubuntu WSL interactiva, sin sudo; timeout total 180 s:

1. Verificar identidad del candidato, WIP, SHA de helpers, manifests, 68/71 fuentes y runtime.
2. Ejecutar sintéticos del clasificador en contenedor efímero. Ante FAIL, detener.
3. Ejecutar una vez `actionlint -oneline` sobre `.github/workflows/security-audit.yml`,
   `.github/workflows/protected-workflow-integrity.yml` y `.github/workflows/db-sync-to-pro.yml`.
4. Si actionlint falla, emitir únicamente `workflow`, `line`, `column` y `rule` sanitizados,
   o un código de parser allowlisted; no emitir texto crudo. Detener en FAIL.
5. Solo con actionlint PASS, continuar en orden con ShellCheck de siete scripts/hooks,
   `npm run lint`, `tsc --noEmit`, `tests/test_protected_workflow_review.py`,
   `tests/test_scan_credentials.sh` y `tests/test_protected_path_scope_guard.sh`.

El stop-on-failure conserva todos los pasos no alcanzados como pendientes. `docker run --rm`
retira solo su contenedor; si timeout impide cleanup, no se inspecciona ni elimina ningún recurso
sin autorización separada.

## Comando único

```bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/run-r9-actionlint-continuation-v3.sh"
readonly RUNNER_SHA256='64ec3666e944b8a88e79542dadd964eced42a4c40439662d32de6956f5fc83a4'
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

Solo `ALL_REMAINING_CHECKS_OK` seguido de revisión sin hallazgos cierra G03. Este JIT no
autoriza F1, copia completa, Pages/workerd, Edge/PG17/PostgREST/C03 integrado, UAT, publicación,
PR, configuración remota, merge ni despliegues.
