# JIT — smoke del template Docker F1 clasificado V7 + F1/r9 condicional

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-SMOKE-CLASSIFIED-V7-R9-ONCE-20261009-V1`
Estado: preparado; requiere aprobación explícita; una invocación.
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Motivo y predicado

El JIT V6 aprobado y consumido, SHA-256
`c84491eee2e23bba26be38985e4658ffe280947c43c953f232eb23699d915277`, llegó a un inspect
sintético y devolvió `SYNTHETIC_TEMPLATE_RENDER_FAILED`. La salida V6 descartó stderr y no
clasificó la causa. Los 15 casos V4/V5/V6 habían pasado; el smoke con labels y tmpfs falló y se
limpió. No se alcanzaron el caso sin mapas, F1 ni r9. Esta evidencia no demuestra un defecto de
Docker ni identifica una expresión.

V7 conserva los clasificadores previos fijados, comprueba sus digests y ejecuta solo cuatro
pruebas nuevas enfocadas. Una prueba recorre el stderr sintético de Go-template por el clasificador
V6 y la allowlist V7; las restantes cubren códigos por campo, fallback cerrado y errores de
captura acotados. No vuelve a ejecutar las 15 pruebas anteriores. Si el digest de la evidencia o
de cualquier fuente fijada cambió, se detiene antes de operar Docker.

## Una invocación y límites

Ejecutor: `romel`, como usuario no-root, en una terminal interactiva de Ubuntu WSL integrada con
Docker Desktop. Sin `sudo`.

1. Comprueba candidato, rama/HEAD, TTY, overrides Docker, digest del runner, atestación
   previa de endpoint, evidencia V6, helpers V4–V6 y el paquete r9. La identidad de endpoint
   previa se reutiliza; no repite el diagnóstico de socket ni requiere `/proc` del Engine.
2. Lee la imagen sintética fijada y su declaración de volúmenes. Si tiene volúmenes declarados,
   detiene la secuencia.
3. En un contenedor temporal `--rm --pull=never` ejecuta solo las cuatro pruebas nuevas. La
   imagen de prueba se lee antes y no se descarga ni construye. El contenedor tiene red apagada,
   rootfs read-only, usuario 1001, capabilities removidas, límites de memoria/CPU/PIDs y un bind
   read-only de los tests.
4. Corre dos smokes temporales de máximo 45 s con la misma imagen fijada y el formato exacto
   Go-template: uno con las tres labels allowlisted y tmpfs controlado; otro sin labels ni tmpfs.
   Ambos usan `--rm --pull=never`, red apagada, rootfs read-only, usuario 1001, capabilities
   removidas, `no-new-privileges` y límites fijos. Captura stderr acotado solo en memoria y
   clasifica expresiones allowlisted; errores desconocidos reciben un código genérico. Valida los
   25 campos y que la política estricta rechace el caso incompleto. Limpia ambos contenedores.
5. Solo con pruebas y ambos smokes PASS, lee una vez la imagen F1 allowlisted y los campos
   allowlisted del contenedor F1. Si la metadata o la política no pasan, se detiene sin r9.
6. Solo con la secuencia exacta de PASS, revalida los manifests r9 y ejecuta r9 una vez. La salida
   cruda de pytest, Docker y r9 no se imprime.

Cualquier fallo, timeout, salida inesperada o cleanup incompleto consume la autorización y detiene
las etapas posteriores. Sin retry. No hace pull/build/install, no cambia Docker, daemon, contexto,
configuración ni imágenes, y no consulta, arranca, detiene, inspecciona ni modifica
`studiamatch-dev`. No accede a `/proc` del motor, secretos, SQL, Supabase, ramas, remoto,
Cloudflare, cuenta Auth ni producto. F1 y r9 solo son accesibles bajo sus predicados PASS.

## Salida sanitaria exigida

El éxito diagnóstico previo a r9 debe ser exactamente:

```text
phase=prior-desktop-wsl-endpoint-attestation|error_code=OK
phase=classifier-synthetic-image-volumes-read|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-v7-focused-tests|error_code=OK
phase=f1-template-synthetic-check|error_code=OK
phase=classifier-synthetic-tests|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=OK
```

El cierre completo agrega `phase=r9|error_code=OK`. Ante fallo se imprime solo fase y código
cerrado; `exit=<n>` se imprime solo si r9 falla. No se emiten stderr, mensajes de Docker,
tracebacks, IDs, nombres, labels, valores de metadata, paths internos ni contenido del contenedor.

## Digests fijados

- JIT V6 consumido: `c84491eee2e23bba26be38985e4658ffe280947c43c953f232eb23699d915277`.
- Evidencia de salida V6: `906d01943b566190ed4045dbcb2e510f28907b4a6591627dee3f91125dbd9c92`.
- Atestación previa del endpoint: `8e6360143d15e47c819beb540edd69bd2a08634ac85b9267d03fd61c5c5ac33a`.
- Helper V6 clasificador: `b17266a33559b16b28cdf1b619f9b5d7dae666203f6d9a357b046ed7ae809128`.
- Suite V4: `369382daa3445999704d85278a482edf78648a61a8e1ef3703ace37a2b923199`.
- Suite V5: `f8880ccb9d6bf2324e5f7982712ce08f6508d09df68b3c087b91b3753e51219f`.
- Suite y runner V6: `a5921c5291a207178f368c64184b7b4869ceeb010b006bb2618038c3cb8516c4` y
  `baf6d4873d6229b40db994c65305be527f61f310306e6ae904c1b8cd3b76380d`.
- Clasificador V7: `432295368a96b7ba8329e3a83aede3bfbba872400331b19127c334d06ca3d58d`.
- Pruebas focales V7 (4 casos): `548d65701def7cb7450cea1761063d992d39f2edac66d86269101cd431f52fa7`.
- Runner sintético V7: `99d1da50ead767f0fcbe2877db6df99589f64b2f8aaf7ed1ee85652174c6ede2`.
- Helper V7: `5b5341f7775b38350197976fe3d0246702e1158ae1578a2957717f97b5f9d0c1`.
- Wrapper combinado V7: `dee832ef729287205b56bfb6e3be3f889121b9b5464166ef6b7443e97b210e96`.
- R9 runner, manifest y tool manifest: `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`,
  `b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866` y
  `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.

Si candidato, JIT, evidencia, fuente, imagen o manifest no coincide, no ejecutar.

## Comando único — terminal Ubuntu WSL interactiva

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_template_smoke_v7_then_r9_once.sh'
readonly RUNNER_SHA256='dee832ef729287205b56bfb6e3be3f889121b9b5464166ef6b7443e97b210e96'
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
IFS= read -r -p 'Copia solo fases/codigos sanitizados y exit; presiona Enter para cerrar: ' _ || true
exit "$runner_status"
)
```

La aprobación, si se concede, cubre únicamente esta invocación agrupada. No reutiliza los JIT
consumidos V4, V5 ni V6.
