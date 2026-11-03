# JIT — smoke del template Docker F1 V6 + una lectura F1/r9 condicional

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-SMOKE-V6-R9-ONCE-20261009-V1`
Estado: preparado; requiere aprobación explícita; una invocación.
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Motivo

El JIT V5 nil-safe (`72d1c46aaa5c615d23308e605e8ad95edd8f8c39b2b0796ef171c355c7c8b316`) pasó
el endpoint previamente acreditado, imagen sintética, 11/11 casos, imagen F1; la única lectura
F1 de contenedor volvió a `INSPECT_TEMPLATE_EVALUATION_ERROR`. La salida no identifica campo ni
causa. V6 prepara una ejecución real del mismo formato Go sobre metadata sintética presente y
ausente y clasifica solo errores de expresiones allowlisted. No atribuye aún el error a una
expresión o a Docker.

## Límite de una invocación

Ejecutor: `romel`, Ubuntu WSL interactiva, no-root, TTY, sin `sudo`, con
`sandbox_permissions=require_escalated`.

1. Preflight fijo de rama/HEAD, overrides, runtime, hashes, endpoint previamente acreditado,
   paquetes r9 y pines, incluyendo la suite base V4 y las suites V5/V6 asociadas a sus digests.
   No reabre socket, no consulta `docker context` ni repite identidad.
2. Lee una vez el ID de la imagen sintética fijada y su `Config.Volumes`; si hay volúmenes
   declarados, detiene antes de crear contenedores. Ejecuta los 15 casos sintéticos en un
   contenedor temporal `--rm --pull=never`, red apagada, rootfs read-only, usuario 1001,
   capabilities removidas, límites fijos y bind de tests read-only.
3. Ejecuta dos smoke runs temporales de máximo 45 s, ambos `--rm --pull=never`, red apagada,
   rootfs read-only, usuario 1001, capabilities removidas, `no-new-privileges` y recursos
   limitados. No arrancan producto: solo ejecutan `python3 -B` en espera acotada para que el
   Engine inspeccione el contenedor. Uno contiene las tres labels allowlisted y tmpfs
   controlado; el otro no declara labels ni tmpfs. El código inspecciona ambos con el formato
   exacto V5/V6, valida 25 campos, labels/tmpfs del caso presente y campos vacíos del caso
   ausente, y confirma que el parser estricto no acepta el fixture incompleto. Los IDs, nombres
   y salida del Engine permanecen solo en memoria; se detienen tras el inspect y `--rm` los
   elimina. Si se interrumpe el ejecutor, los runs terminan solos en 45 s y también se eliminan.
4. Solo si sintéticos y smoke pasan, lee una vez la imagen F1 allowlisted y una vez los 25
   campos allowlisted del contenedor F1 usando el formato nil-safe. El clasificador procesa
   stderr acotado solo en memoria y devuelve códigos cerrados por expresión/causa; nunca emite
   texto del Engine.
5. Solo si la secuencia completa de diagnóstico y el predicado F1 son exactamente `OK`,
   revalida manifests r9 y ejecuta r9 una vez con el runner/imagen existentes. stdout/stderr de
   r9 se descartan.

Cualquier fallo, salida inesperada, cleanup incompleto o timeout detiene etapas posteriores y
consume esta aprobación. Sin retry. No se ejecutan `sudo`, `/proc`, pull/build/install, cambios
de daemon/configuración/imágenes, ni inspect/modificación de `studiamatch-dev`. No se altera el
recurso F1, secretos, SQL, ramas, remoto, Cloudflare, cuenta Auth, copia de fuentes ni producto.
Las únicas operaciones son preflights read-only, inspect de imagen sintética, un contenedor
pytest efímero, inspect de volúmenes de esa imagen, dos smoke runs efímeros con inspect/stop,
inspect read-only de imagen y contenedor F1 y —solo tras PASS completo— el preflight de r9 y su
contenedor efímero. La ejecución combinada está limitada a 450 s; cada subcomando tiene su
timeout local.

## Salida sanitaria

La secuencia completa antes de r9 debe ser exactamente:

```text
phase=prior-desktop-wsl-endpoint-attestation|error_code=OK
phase=classifier-synthetic-image-volumes-read|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-unit-tests|error_code=OK
phase=f1-template-synthetic-check|error_code=OK
phase=classifier-synthetic-tests|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=OK
```

El cierre total añade `phase=r9|error_code=OK`. Fallos solo pueden imprimir fases y códigos
cerrados por el wrapper; `exit=<n>` aparece solo ante fallo r9. No se muestran IDs, nombres,
labels, valores de metadata, paths internos, mounts ni salida cruda Docker/pytest/r9.

## Pines

- Runner combinado V6: `ba57b3bd613bafdd05ffe7d31377b6468ca1c4a7a74cbbcf39c86130034df080`.
- Clasificador V6: `b17266a33559b16b28cdf1b619f9b5d7dae666203f6d9a357b046ed7ae809128`.
- Runner sintético V6: `baf6d4873d6229b40db994c65305be527f61f310306e6ae904c1b8cd3b76380d`.
- Pruebas V6: `a5921c5291a207178f368c64184b7b4869ceeb010b006bb2618038c3cb8516c4`.
- Helper V5 nil-safe fijado: `2f47ebed1977d360df8aa5905a3a1cf3fa0a813f606e1c3aa583c56d26330c51`.
- V5 synthetic runner/test preservados: `48a46e03602064f04ea78e7e60cc64bba814aadcb66d9d0365d10cd0ac5b6764` y
  `f8880ccb9d6bf2324e5f7982712ce08f6508d09df68b3c087b91b3753e51219f`.
- V4 test preservado: `369382daa3445999704d85278a482edf78648a61a8e1ef3703ace37a2b923199`.
- V2 helper y V1 helper: `5ae493c50559b588ac9e40f49f54376da82c50af73b1bacf2e4133611136c90f` y
  `b84e46250823a0a7f3c73bf0bbd3359147585dea7d1c4b8ef322d87a1c12d4fc`.
- Proyección/parser F1: `794b49ce5560c8cacebbd403c05b4cdbe78fd0c0062d30b6690b901838831463`.
- Atestación previa: `8e6360143d15e47c819beb540edd69bd2a08634ac85b9267d03fd61c5c5ac33a`.
- Runner r9, manifest y tool manifest: `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`,
  `b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866` y
  `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.

No ejecutar si rama, HEAD, atestación, imagen, runner o cualquier hash no coincide.

## Comando único — terminal Ubuntu WSL interactiva

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_classifier_v6_then_r9_once.sh'
readonly RUNNER_SHA256='ba57b3bd613bafdd05ffe7d31377b6468ca1c4a7a74cbbcf39c86130034df080'
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
if ! hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)"; then
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
fi
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 450s /bin/bash "$RUNNER" 2>/dev/null
runner_status=$?
IFS= read -r -p 'Copia solo fases/códigos sanitizados y exit; presiona Enter para cerrar: ' _ || true
exit "$runner_status"
)
```

Esta aprobación cubre únicamente esta invocación agrupada, con F1 una vez y r9 solo bajo PASS
completo. Los JIT V4-FIX y V5 ya están consumidos; no se reutilizan.
