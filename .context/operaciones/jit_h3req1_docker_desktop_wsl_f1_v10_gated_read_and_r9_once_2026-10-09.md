# JIT — lectura F1 acotada y r9 local una vez

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-V10-GATED-READ-AND-R9-ONCE-20261009-V1`  
Estado: preparado; **requiere aprobación humana; una invocación**.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Motivo y evidencia previa

La aprobación V10 se consumió con PASS de identidad previa, 17 pruebas sintéticas, lectura
aislada de imagen, 25 probes de campos y cleanup. V10 excluyó la lectura F1 y r9. Las
autorizaciones anteriores de F1/r9 se consumieron durante fallos previos y no se reutilizan.

Esta invocación reutiliza la identidad de Docker Desktop WSL ya acreditada por V3 y el resultado
V10 fijado por hash. No repite los probes V10 ni el diagnóstico del socket. Antes de ejecutar,
comprueba que el ID fijado de F1 no coincide con el hash del ID que el usuario identificó como
`studiamatch-dev`; si coincide, detiene el ciclo sin leerlo.

## Alcance exacto y orden stop-on-failure

Ejecutor: Codex en Ubuntu WSL, usuario `romel` no-root, terminal interactiva y
`sandbox_permissions=require_escalated`; sin `sudo`.

1. Validar rama/HEAD, contexto `default`, identidad V3, JIT/evidencia V10, pins V6/V7, runner,
   paquete r3, paquete de herramientas y 68 entradas fuente del candidato. Tres entradas del
   manifiesto r9 son auxiliares internos del paquete; se comprueba que no haya drift en las 68
   entradas del candidato.
2. Reusar el clasificador V7 fijado y hacer un smoke Go-template con dos contenedores
   sintéticos temporales: labels y tmpfs presentes, luego ausentes. Se usa exclusivamente la
   imagen sintética fijada; `--pull=never`, red desactivada, rootfs read-only, UID 1001, sin
   capabilities y recursos acotados. Se inspecciona la proyección allowlisted de 25 campos y se
   detienen los contenedores por sus IDs. El resultado esperado es
   `phase=f1-template-synthetic-check|error_code=OK`.
3. Solo si el smoke pasa, leer una vez la imagen F1 allowlisted y una vez el contenedor F1
   allowlisted. La lectura compara los campos requeridos en memoria y emite solo fase/código;
   no guarda ni imprime metadata, ID o stderr. No enumera contenedores ni inspecciona
   `studiamatch-dev`.
4. Solo si las fases anteriores están en `OK` y la política F1 coincide, ejecutar r9 una vez
   en un contenedor efímero offline. Se usa la imagen local fijada con `--pull=never`; paquete y
   herramientas van montados read-only. La raíz del contenedor es read-only, con usuario 1001,
   red desactivada, capabilities retiradas, `no-new-privileges`, 512 MiB, 1 CPU y 64 PIDs.
   El runner copia de forma aislada los 68 inputs del candidato y valida dependencias, actionlint,
   ShellCheck, ESLint, TypeScript, workflow review, credential scan y protected-path guard.

Cualquier diferencia, FAIL, código no permitido o timeout detiene las etapas posteriores y
consume la autorización. No hay retry ni aumento de límites. La duración total queda acotada a
600 segundos; F1 y r9 conservan además sus timeouts internos fijados.

## Datos y operaciones excluidos

No accede a `studiamatch-dev`, no cambia ni reconstruye imágenes/contendores preexistentes, no
hace pull/build/install, no modifica Docker, no toca base de datos/SQL/Supabase/Auth/correo,
secretos, ramas protegidas, GitHub, Cloudflare, publicación, PR, merge o despliegue. El resultado
no autoriza snapshot completo, startup Pages/workerd, integración Edge/PG17/PostgREST ni C03.
F1/r9 PASS solo habilitaría considerar el siguiente gate local bajo las autorizaciones vigentes.

## Salida permitida

Solo registros `phase=…|error_code=…` de los allowlists fijados; ante fallo de r9 puede aparecer
`exit=<código>` decimal. stderr, metadata, imágenes, IDs, nombres y mensajes de herramientas se
descartan. Un resultado ausente no significa PASS.

## Comando único — invocación en terminal Ubuntu WSL

El bloque es para una sola ejecución. No copiarlo a una sesión root. La pausa conserva las líneas
sintéticas para que se puedan comprobar antes de cerrar el terminal.

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v11_then_r9_once.sh'
readonly RUNNER_SHA256='fbd5f3da45c0a5b1f50c6f7f158745f2b0c886c4eac1fb1e579e54e8ac63f4dd'
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
/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 600s /bin/bash "$RUNNER" 2>/dev/null
)
```

Una respuesta `OK` de endpoint o una lectura exitosa por sí sola no cierra un gate. Registrar la
salida permitida y el exit code inmediatamente al terminar. Esta autorización no se reutiliza.
