# JIT — aislar expresiones del template Docker F1 sintético V8

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-FIELD-ISOLATION-V8-ONCE-20261009-V1`
Estado: preparado, pendiente de autorización explícita; una invocación.
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Predicado y motivo

V7 fue consumido con salida
`phase=f1-template-synthetic-inspect|error_code=INSPECT_TEMPLATE_EVALUATION_ERROR`. Sus cuatro
pruebas focales pasaron, pero el clasificador no reconoció una expresión concreta. V8 prepara
pruebas aisladas de las 25 columnas del formato allowlisted actual. No repite V7 ni reejecuta el
formato completo. Solo las fases/códigos sanitizados salen del runner.

## Una invocación agrupada y límites

Ejecutor: `romel` no-root en terminal Ubuntu WSL interactiva, con `require_escalated`, sin
`sudo`.

1. Comprueba checkout, rama/HEAD, WSL, endpoint ya atestiguado, digests de evidencia V7 y fuentes
   de diagnóstico. No repite conexión de socket, HTTP ni identidad del Engine.
2. Lee una vez la imagen sintética fijada por digest y comprueba que no declare volúmenes.
3. Corre cinco pruebas enfocadas en un contenedor temporal del mismo digest, sin red, rootfs
   read-only, usuario 1001, capabilities removidas y límites fijos. Monta el directorio de
   diagnósticos solo read-only.
4. Solo con PASS de las cinco pruebas, crea un contenedor temporal read-only, sin red, con
   labels allowlisted y tmpfs controlado. Ejecuta una lectura `docker inspect --format` por cada
   una de las 25 expresiones/columnas del formato fijado. El stdout del inspect se captura en
   memoria y se descarta; stderr queda acotado y se convierte en código cerrado. Se emite una
   fase allowlisted por campo con `OK` o código sanitizado. Los fallos de template se registran
   para las columnas restantes; un error de transporte detiene las lecturas. El contenedor se
   detiene y elimina con `--rm`.

Timeout exterior: 450 s; el wrapper interno limita el runner a 420 s, cada inspect usa el límite
del helper fijado y el contenedor temporal termina por sí mismo en 45 s si se interrumpe el
proceso. Cualquier FAIL/timeout consume la invocación y detiene la etapa. Sin retry, pull,
build, install, cambios de imagen/configuración/daemon, acceso a `studiamatch-dev`, lectura F1,
r9, copia, Pages/workerd, SQL, Supabase, remoto, Cloudflare, Auth o datos operativos. Este JIT no
autoriza F1 ni r9.

## Evidencia de salida

Solo líneas `phase=…|error_code=…` con fases predefinidas y valores cerrados. No se imprime
stdout de metadata, stderr, ID/nombre del contenedor, labels, valores del Engine, traceback ni
secretos. Si todos los campos aislados pasan, eso no declara PASS del template agregado; se
registra únicamente `probe-summary|ALL_FIELDS_OK` para orientar el siguiente diagnóstico.

## Digests fijados

- Resultado V7: `80332dca12db2c0a38692cc833d7cabd3a0feb47abf614e3aa7fdda7e6fce72d`.
- Atestación previa endpoint/socket: `8e6360143d15e47c819beb540edd69bd2a08634ac85b9267d03fd61c5c5ac33a`.
- Template V5 fuente: `2f47ebed1977d360df8aa5905a3a1cf3fa0a813f606e1c3aa583c56d26330c51`.
- Helper V1 de inspect acotado: `b84e46250823a0a7f3c73bf0bbd3359147585dea7d1c4b8ef322d87a1c12d4fc`.
- Helper Desktop WSL: `c25aa3d3d91bb0cadc160b090c49c4bc61362baefaf3415d046ce7a9cabea4cb`.
- Clasificador V8: `ef7d8bf086335b07374186043dfe74964536ca9194df773d889cd7df5f23ab72`.
- Pruebas V8: `555b9557c6969d414412cdf4a7a68a68105c956a876eda15fe5feb72cac57ff0`.
- Runner sintético V8: `e06d0490320e9a86df1a086f17040d7880a5253defeda88d25f88892cdd76c83`.
- Helper V8: `498bb484854bd86d3b67d1ed3586d391cf7690b822aec7caac84c184299a9c24`.
- Wrapper WSL: `a82fc9102a465103f4c509288980a86ef0b294a2dcbfca8d9acd3bae15aaf9b7`.

Si candidato, fuente, evidencia o digest no coincide, no ejecutar.

## Comando único — terminal Ubuntu WSL interactiva

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_template_expression_probe_v8_once.sh'
readonly RUNNER_SHA256='a82fc9102a465103f4c509288980a86ef0b294a2dcbfca8d9acd3bae15aaf9b7'
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
/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 450s /bin/bash "$RUNNER" 2>/dev/null
runner_status=$?
IFS= read -r -p 'Conserva solo fases y códigos sanitizados; presiona Enter para cerrar: ' _ || true
exit "$runner_status"
)
```

La aprobación cubre exclusivamente esta invocación agrupada y no autoriza operaciones
condicionales adicionales.
