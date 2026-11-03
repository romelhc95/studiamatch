# JIT — plantilla F1 nil-safe V5 + una lectura F1/r9 condicional

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-NIL-SAFE-V5-R9-ONCE-20261009-V1`
Estado: preparado; revisión independiente sin hallazgos; requiere aprobación explícita; una invocación.
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Causa y corrección acotadas

El JIT V4-FIX de SHA-256
`949748aa95a4bc3aa0ed6ecda4c95ed1157ba0840cf89dc2cbc4b5c11521878c` pasó los sintéticos,
la lectura de imagen F1 y llegó a `f1-container-read/INSPECT_TEMPLATE_EVALUATION_ERROR`; stop-on-
failure impidió r9. El resultado no conserva cuál mapa ni texto del Engine. La plantilla
allowlisted contiene cuatro `index` sobre mapas opcionales (`Config.Labels` y `HostConfig.Tmpfs`).

V5 aplica `with` a esos mapas. El orden de los 25 campos permanece igual y el parser vigente
conserva las mismas comparaciones estrictas. Si falta metadata, la plantilla produce un campo
vacío y el parser debe devolver `F1_POLICY_MISMATCH`; esto no puede dar PASS por omisión. Cuatro
pruebas sintéticas nuevas comprueban la guarda, su aplicación antes del inspect y que
labels/Tmpfs faltantes fallen cerrados, junto con los siete casos previos.
Solo se usa la salida sanitaria de fase/código.

## Alcance de una invocación

Ejecutor: `romel`, Ubuntu WSL interactiva, no-root, TTY, sin `sudo`, con
`sandbox_permissions=require_escalated`.

1. Preflight fijo de rama/HEAD, runtime, overrides Docker, hashes, evidencia de endpoint
   previamente acreditada y paquetes r9. El diagnóstico V5 no repite socket, `docker context`
   ni lectura de identidad.
2. Lee una vez el ID de la imagen sintética fijada con `docker image inspect --format {{.Id}}`;
   después corre un contenedor sintético con esa imagen, `--pull=never`, red deshabilitada,
   rootfs read-only, usuario 1001, capacidades removidas y límites existentes. Exige colección
   exacta y PASS de los once casos previstos. La prueba nueva se verifica por SHA dentro del
   runner.
3. Solo tras sintéticos PASS, lee una vez la imagen F1 allowlisted y una vez los 25 campos
   allowlisted del contenedor F1, con el formato nil-safe. Un campo ausente no coincide con la
   política y detiene el ciclo como `F1_POLICY_MISMATCH`.
4. Solo si la salida completa de diagnóstico y el predicado F1 son exactamente `OK`, revalida
   manifests y ejecuta r9 una vez. r9 conserva su propio `docker context inspect` de preflight y
   lanza un contenedor temporal `--rm` desde la imagen ya existente, con red apagada, rootfs
   read-only y binds read-only. stdout/stderr de r9 se descartan; solo se emite resultado
   sanitizado y, ante fallo, exit numérico.

Cualquier preflight FAIL, error, resultado inesperado o timeout detiene las etapas posteriores
y consume esta aprobación. Sin retry. No ejecuta `sudo`, `/proc`, pull/build/install ni cambia
daemon, configuración o imágenes. Las únicas operaciones Docker son el inspect read-only de la
imagen sintética, su contenedor temporal `--rm`, los inspect read-only de imagen y contenedor
F1, y —solo tras PASS completo— el preflight `docker context inspect default` y contenedor de
prueba r9 temporal `--rm`. No inspecciona/modifica `studiamatch-dev` ni altera el recurso F1,
secretos, SQL, ramas, remoto o Cloudflare. No hace copia, arranque Pages/workerd ni C03
integrado. r9 permanece condicionado al PASS real de F1.

## Salida sanitaria

Éxito previo a r9:

```text
phase=prior-desktop-wsl-endpoint-attestation|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-tests|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=OK
```

El éxito completo añade `phase=r9|error_code=OK`. Fallos solo pueden mostrar fases/códigos
allowlisted por el wrapper. `exit=<n>` se emite para un fallo de r9; fallos anteriores terminan
con estado no cero y no necesariamente imprimen ese campo. Nunca se imprime salida cruda de
Docker/pytest/r9, IDs, nombres, paths, labels, mounts ni metadata.

## Pines

- Paquete JIT: SHA-256 se calcula y comunica antes de solicitar autorización.
- Runner combinado V5: `6859af613d9e02da7b064a7312f9626b4a22c7066a433f78d7ce00200584c4d9`.
- Clasificador V5: `2f47ebed1977d360df8aa5905a3a1cf3fa0a813f606e1c3aa583c56d26330c51`.
- Runner sintético V5: `48a46e03602064f04ea78e7e60cc64bba814aadcb66d9d0365d10cd0ac5b6764`.
- Prueba nil-safe V5: `f8880ccb9d6bf2324e5f7982712ce08f6508d09df68b3c087b91b3753e51219f`.
- Prueba sintética V4 preservada: `369382daa3445999704d85278a482edf78648a61a8e1ef3703ace37a2b923199`.
- Helper clasificador V2: `5ae493c50559b588ac9e40f49f54376da82c50af73b1bacf2e4133611136c90f`.
- Helper legado V1: `b84e46250823a0a7f3c73bf0bbd3359147585dea7d1c4b8ef322d87a1c12d4fc`.
- Helper Desktop WSL: `c25aa3d3d91bb0cadc160b090c49c4bc61362baefaf3415d046ce7a9cabea4cb`.
- Proyección F1/parser estricto: `794b49ce5560c8cacebbd403c05b4cdbe78fd0c0062d30b6690b901838831463`.
- Atestación previa: `8e6360143d15e47c819beb540edd69bd2a08634ac85b9267d03fd61c5c5ac33a`.
- Runner r9: `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`.
- Manifest r9/tools: `b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866` y
  `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.

No ejecutar si rama, HEAD, paquete r9, atestación o algún hash no coincide.

## Comando único — terminal Ubuntu WSL interactiva

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_classifier_v5_then_r9_once.sh'
readonly RUNNER_SHA256='6859af613d9e02da7b064a7312f9626b4a22c7066a433f78d7ce00200584c4d9'
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
/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 300s /bin/bash "$RUNNER"
runner_status=$?
IFS= read -r -p 'Copia solo fases/códigos sanitizados y exit; presiona Enter para cerrar: ' _ || true
exit "$runner_status"
)
```

Esta aprobación cubre solo esta invocación, incluida la secuencia F1 y r9 condicional. No
reutilizar aprobaciones de F2d ni de los JIT V3/V4 anteriores ya consumidos.
