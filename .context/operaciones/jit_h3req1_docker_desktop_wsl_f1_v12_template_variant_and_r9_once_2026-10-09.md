# JIT — diagnóstico V12 de template, lectura F1 y r9 una vez

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-V12-TEMPLATE-VARIANT-DIAGNOSTIC-AND-R9-ONCE-20261009-V1`  
Estado: preparado; requiere aprobación humana para **una invocación**.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Motivo y evidencia

V11 ya fue aprobado y consumido. Su salida fue `f1-template-synthetic-inspect / INSPECT_TEMPLATE_EVALUATION_ERROR`, exit 1; detuvo el ciclo antes de F1 y r9. La evidencia no distingue las variantes sintéticas con labels/tmpfs presentes y ausentes. V10 había probado los 25 campos individualmente en otro fixture, así que no resuelve esta discrepancia.

V12 registra qué variante falla. Antes de crear fixtures, comprueba que la imagen sintética no tenga labels heredados. La variante `absent` no pasa ningún label; la propiedad del fixture temporal se verifica mediante un marcador aleatorio en `Config.Env`, sin alterar `.Config.Labels`. Ante cualquier error Go-template allowlisted (`INSPECT_TEMPLATE_*`), ejecuta hasta 25 lecturas allowlisted de campos individuales contra ese mismo fixture. No emite valores, stderr ni metadata. Cualquier fallo detiene F1 y r9.

## Ejecutor y alcance exactos

Ejecutor: `romel`, no-root, en terminal interactiva de Ubuntu WSL integrada con Docker Desktop; `sandbox_permissions=require_escalated`, sin `sudo`. Una sola invocación. El runner comprueba rama/HEAD, ausencia de overrides Docker, hashes, evidencia previa y 68 inputs del candidato; el manifiesto contiene además tres auxiliares internos del paquete r9. No lee `.env*` ni imprime secretos.

Orden stop-on-failure:

1. Revalidar V11 consumido, evidencia V10 y endpoint atestado previamente; comprobar pins del smoke, proyección, herramientas y paquete r9. No vuelve a diagnosticar el socket ni repite los probes V10.
2. Leer de forma allowlisted el mapa de labels de la imagen sintética y exigirlo vacío. Crear como máximo dos contenedores temporales desde esa imagen local fijada, con `--pull=never`, red desactivada, filesystem read-only, UID no-root y límites de recursos. Probar el formato combinado primero con labels/tmpfs y luego sin ningún label ni tmpfs. Si una variante falla con cualquier error Go-template allowlisted, probar sus 25 expresiones fijas en el mismo contenedor. La limpieza selecciona el nombre aleatorio y verifica un marcador aleatorio de propiedad con un template que solo puede emitir `OWNED`; solo entonces detiene el ID validado. Ante incertidumbre o fallo de cleanup, no crea la variante siguiente.
3. Solo si ambas variantes pasan, leer una vez la imagen F1 allowlisted y una vez la proyección allowlisted del contenedor F1. El ID fijado se compara con el hash del ID que el usuario identificó como `studiamatch-dev`; una coincidencia detiene el acceso.
4. Solo si el smoke y ambos controles F1 pasan, ejecutar r9 una vez en su contenedor efímero offline: copia aislada, manifiestos, dependencias, Node/TypeScript, actionlint, ShellCheck, ESLint, typecheck, pruebas del workflow protegido, scanner de credenciales y scope guard. Requiere 68/68 inputs del candidato sin drift.

Límites: máximo 900 s para el wrapper, 360 s para V12 y 240 s para r9, además de los timeouts internos fijados. Cualquier error, salida no permitida o timeout consume la autorización y detiene las etapas posteriores. No hay retry, `pull`, `build`, `install`, limpieza de recursos preexistentes ni cambios de Docker. No accede a `studiamatch-dev`, DB, SQL, Supabase, Auth, correo, secretos, Git remoto, GitHub, Cloudflare, ramas protegidas, PR, merge o despliegue. Los contenedores del fixture y r9 son efímeros y de alcance fijo. La salida permitida es solo `phase=…|error_code=…` y, ante fallo, `exit=<decimal>`.

## Evidencia de salida esperada

El resultado diagnóstico PASS debe emitir, en este orden:

```text
phase=prior-v11-failure|error_code=OK
phase=prior-v10-evidence|error_code=OK
phase=prior-endpoint-attestation|error_code=OK
phase=f1-template-synthetic-label-map|error_code=OK
phase=f1-template-present-inspect|error_code=OK
phase=f1-template-absent-inspect|error_code=OK
phase=f1-template-synthetic-check|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=OK
```

Después, r9 debe emitir sus 14 checks en `OK` y `phase=r9-summary|error_code=ALL_CHECKS_OK`. Solo entonces se puede acreditar G03/G04 según su evidencia requerida. Un PASS sintético por sí solo no cierra un gate.

## Comando único

Pegar una sola vez en la terminal Ubuntu WSL como `romel`; conservar la ventana y devolver únicamente las líneas sanitizadas antes de cerrar. No correr como root.

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v12_then_r9_once.sh'
readonly RUNNER_SHA256='a02b200efcf377da64bc13caa62136167811f31ac4fa4cf54ed81a4c7338f783'
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
/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 900s /bin/bash "$RUNNER" 2>/dev/null
)
```

Ni esta solicitud ni una salida incompleta se reutilizan para otra invocación. Un error requiere preservar el resultado, corregir la fase demostrada y presentar JIT nuevo por objetivo.
