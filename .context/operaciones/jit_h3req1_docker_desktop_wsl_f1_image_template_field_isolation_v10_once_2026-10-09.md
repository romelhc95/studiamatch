# JIT — aislar los campos del template de imagen y reanudar probes V10

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-IMAGE-TEMPLATE-FIELD-ISOLATION-V10-ONCE-20261009-V1`
Estado: preparado; requiere autorización explícita; una invocación.
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Resultado previo que motiva el cambio

El JIT V9 Bash corregido (`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-IMAGE-READ-CLASSIFIER-V9-BASH-DISPATCH-ONCE-20261009-V1`,
SHA `a1b28cb9b3a2bc40bc9d4150dc2ffd8d90371e78672920ba75028c064abf8c43`) ejecutó una lectura del
template combinado `{{.Id}}|{{json .Config.Volumes}}`. El clasificador respondió
`IMAGE_INSPECT_TEMPLATE_ERROR`, exit 1. Se detuvo antes de tests, contenedores/probes, F1 o r9.
La salida está en [evidencia V9](../evidencia/h3req1_c03_v9_image_template_error_2026-10-09.md).

V10 no repite el template combinado. Ejecuta por separado las expresiones fijadas
`{{.Id}}` y `{{json .Config.Volumes}}` para localizar el campo que falla.

## Alcance agrupado — una invocación

Ejecutor: `romel` no-root en terminal Ubuntu WSL interactiva, con `require_escalated` del entorno,
sin `sudo`.

1. Comprueba el checkout, pins V8/V9/V10 y las evidencias/JIT históricos declarados abajo.
   Reutiliza la atestación previa del endpoint aceptada por V9; no repite diagnóstico de socket.
2. Ejecuta una sola lectura read-only de `docker image inspect --format '{{.Id}}'` contra la imagen
   sintética fijada. argv exacto; timeout 15 s; stdout 256 bytes y stderr 4096 bytes máximo en
   memoria. Solo emite fase/código y valida el ID contra el digest fijado.
3. Solo si el ID pasa, ejecuta 17 pruebas focales (cinco V8, nueve V9 y tres V10) en un contenedor
   efímero del mismo digest. `--pull=never`, sin red, rootfs read-only, usuario 1001, capacidades
   removidas, recursos acotados y fuentes montadas read-only.
4. Solo si las 17 pruebas pasan, ejecuta una lectura separada
   `docker image inspect --format '{{json .Config.Volumes}}'` sobre el mismo digest, con los mismos
   límites y clasificación. Solo se aceptan valores sin volúmenes (``, `null`, `{}`).
5. Solo si esta segunda expresión pasa, inicia un contenedor sintético temporal y ejecuta hasta 25
   probes read-only del template de contenedor V8. stdout se descarta, stderr se clasifica con
   códigos cerrados y cleanup permanece fail-closed.

Cualquier FAIL o timeout consume la autorización y detiene la etapa. No se repite el template
combinado ni se reintenta ninguna llamada. No lee F1, no corre r9, no accede a `studiamatch-dev`,
no hace pull/build/install ni cambios de configuración Docker. No hay SQL, Supabase, Auth,
Cloudflare, secretos, ramas protegidas o datos operativos. Aun con `ALL_FIELDS_OK`, el resultado
es diagnóstico sintético; no cierra F1 ni gates H3REQ1.

## Salida permitida

Solo `phase=…|error_code=…` desde allowlists cerradas. Fases nuevas: `image-id-isolated` y
`image-volumes-isolated`. Nunca emitir texto Docker, stderr, IDs de contenedor temporal, valores de
metadata ni digests distintos del valor estático de la solicitud.

## Pines

- JIT V8: `b63ad5cf046625af7f2fff26e65343b54068e40f1489d8f2df6c2f883bd005a5`.
- Resultado V8: `461e1fb24dfc6eabe2ee9f5a680acf911365abfd4ebe3a278ccb081b487c748d`.
- JIT V9 base: `f2d19ea84397c66ab6ba2755e38b840448a8f40def796ac7895904029805d86c`.
- Resultado V9: `98422e3529506e8214973f4212e83fa867b69a4645db4ced5ef454c62ea4244b`.
- JIT V9 Bash dispatch consumido: `a1b28cb9b3a2bc40bc9d4150dc2ffd8d90371e78672920ba75028c064abf8c43`.
- Helper V9: `19189d5012290dc971fab501c37a01390af49fc89a549653ab8e3cd44826b9b8`.
- Tests V9: `d92f7d37bec04469f8be017be9dfff63f80dfcb810ccee052aa4eebf4a3796c1`.
- Helper parser V10: `3459f0c70f3c464fb241275a6b2e0c8907ac1ef0b5efc417c06e3e8be25377e3`.
- Tests parser V10: `8d00c2357f6d00dfaf8bc621cb5a4770639a8ae81a726e543813afa0b5ffd4e8`.
- Runner sintético V10: `aa341f65167f3fd7aabce5a144ed7abd5928255acbe6dc007362cf23ba8f4545`.
- Orquestador V10: `3721861d4506ed778d2166fda952d6bfffc08072158c8d1ea1050ac030eb23d4`.
- Wrapper WSL V10: `6360d53eccc4fbea89a60259587ab600a8f5cc78d3ce20eb37163669e2023ce6`.

Si el preflight, un hash o un predicado difiere, detenerse sin continuar a la siguiente etapa.
La autorización no habilita F1, r9 ni otra operación posterior.

## Comando único — terminal Ubuntu WSL interactiva

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_template_expression_probe_v10_once.sh'
readonly RUNNER_SHA256='6360d53eccc4fbea89a60259587ab600a8f5cc78d3ce20eb37163669e2023ce6'
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

La aprobación cubre este bloque una vez y solo estos predicados. No aumentar timeouts, hacer retry
ni reinterpretar una salida ausente como PASS.
