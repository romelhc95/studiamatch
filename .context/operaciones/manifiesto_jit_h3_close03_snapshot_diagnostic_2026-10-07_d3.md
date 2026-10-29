# JIT D3 — diagnóstico mínimo del source snapshot H3-CLOSE-03

Estado: **propuesto, NO aprobado, NO ejecutado**. D2 y S1 siguen consumidos. Este documento no concede permiso por sí solo; el `continua` del ciclo no sustituye esta aprobación JIT.

## Pregunta que permite resolver

La lectura estática de `tests/h3req1_c03_startup_smoke_s1.sh` muestra que el snapshot del S1 conecta `tar -C "$ROOT" ... -cf -` con el receptor Docker `tar -xf - -C /snapshot`. `pipefail` entrega un único estado agregado, el runner no registra por separado el estado del productor/receptor y redirige a `/dev/null` la salida del contenedor. El NO-GO de S1 en `create-new-source-snapshot` exit 2 no identifica cuál etapa falló.

La hipótesis de ownership 1000:1000 con `--cap-drop=ALL` **no está demostrada**. D3 crea solo un fixture sintético, genera cabeceras tar con UID/GID numéricos `1000:1000` sin hacer `chown`, compara extracción explícita `--same-owner` con `--no-same-owner` bajo UID/GID receptor `1001:1001` y los mismos controles sin privilegios. Así se reproduce la solicitud de restaurar owner sin ejecutar como root; no pretende modelar el UID implícito exacto de S1. Registra los códigos del productor y ambos receptores por separado. La prueba puede confirmar o descartar este mecanismo reproducible; **no puede atribuir con certeza la causa histórica de S1**, cuya salida no se conserva.

## Inputs y hashes cerrados

| Input | SHA-256 | Uso |
|---|---|---|
| `tests/h3req1_c03_snapshot_diagnostic_d3.sh` | `a64fa5743372d5ff39fb9a009d89beb68a9afec756b32455066db06f84c41796` | Payload del runner; se ejecuta desde bytes ya verificados en memoria |
| `tests/h3req1-c03-snapshot-diagnostic-d3.sha256` | `560ea87e661acd95406ea749358b060d0132dcc97300682db1b101ef1f4ca0e1` | Manifiesto de un input: fija el runner anterior |

El fixture sintético se define por el runner: `owner.txt`, `nested/data.json` y `SHA256SUMS`; modos 0640/0600/0644, directorio 0750, rutas allowlisted, sin symlinks. El productor crea un tar de máximo 1 MiB con metadata UID/GID 1000:1000. El receptor comprueba las rutas, propietarios, modos, espacio disponible y hashes; la corrección comparativa no cambia controles de contenedor. No se empaquetan archivos de producto.

Imagen local fijada, sin pull: `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`, plataforma `linux/amd64`.

## Recurso, comandos y límites incluidos

Único recurso Docker nuevo: contenedor `h3req1-c03-snapshot-diagnostic-d3-20261007`, etiquetado con JIT, manifiesto y nonce de ejecución. Se usa `docker run --detach`; el sanitizador lee únicamente su `stdout` (el `stderr` se descarta), espera EOF tras la única línea ID esperada y exige exactamente un ID completo válido antes de continuar. Si aparece stdout extra/duplicado, aborta la lectura de inmediato y falla cerrado. En interrupción, el primer ID exacto emitido por esa invocación puede usarse solo para inspección por ID; nombre fijo y etiquetas/nonce deben coincidir antes de una parada. No se crean volúmenes ni redes Docker y no se listan contenedores preexistentes. Una colisión del nombre fijo falla sin devolver ID y no causa inspección histórica. Si Docker no devuelve un ID verificable (por ejemplo, timeout antes de responder), no se consulta por nombre ni se inspecciona otro recurso; se deja constancia NO-GO para intervención posterior con autorización nueva.

Riesgo residual explícito: si Docker crea el contenedor pero el timeout/interrupción ocurre antes de que el CLI entregue el ID, podría quedar un contenedor nuevo ejecutándose. Si el stdout de create produce IDs duplicados, el filtro falla cerrado y, por ambigüedad, no inspecciona ni detiene ninguno. El runner no buscará por nombre ni detendrá a ciegas. Owner de la decisión: responsable humano del JIT; identificar/parar cualquiera de esos casos requiere nueva aprobación dirigida. La autorización D3 es de una sola invocación y queda invalidada si cambia HEAD, runner, manifiesto, imagen, comando o recurso.

Riesgos de entorno residual: los dos comandos iniciales `docker context show/inspect` solo leen la configuración local con timeout para descubrir el endpoint. El endpoint se obtiene como JSON, se rechaza cualquier path fuera del schema Unix local permitido, y la identidad del socket antes y después de `realpath` debe coincidir. Después Docker usa exactamente la ruta canónica, cuya identidad (device/inode/uid/gid/mode) se revalida antes de cada operación del daemon. Esto detecta sustitución persistente, pero no autentica criptográficamente el peer ni elimina la carrera entre `stat` y conexión; la propuesta presupone un Docker local confiable y no debe ejecutarse en un host bajo control de otro proceso/usuario. Los `stdout` de contexto, image inspect, inspect y stop usados como campos estructurados tienen timeout, pero no un límite de bytes explícito; un daemon local malformado/hostil podría causar crecimiento de memoria hasta el timeout. Owner de aceptación: responsable humano de este JIT; el riesgo se limita a esta invocación y cualquier repetición requiere aprobación nueva. Una respuesta anómala de `docker wait` queda acotada a 5 bytes; la captura falla cerrada si excede el formato exacto `0`–`255` más EOF.

Comando exacto, solo después de aprobación humana explícita:

```bash
/usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="${HOME:?HOME is required for the selected local Docker context}" LANG=C LC_ALL=C \
  /bin/bash -Eeuo pipefail <<'H3_C03_D3_LAUNCHER'
set -Eeuo pipefail
root="$(git rev-parse --show-toplevel)"
[[ "$root" == "$(pwd -P)" ]] || { printf 'NO-GO: run from candidate root\n' >&2; exit 1; }
runner='tests/h3req1_c03_snapshot_diagnostic_d3.sh'
manifest='tests/h3req1-c03-snapshot-diagnostic-d3.sha256'
expected_runner='a64fa5743372d5ff39fb9a009d89beb68a9afec756b32455066db06f84c41796'
expected_manifest='560ea87e661acd95406ea749358b060d0132dcc97300682db1b101ef1f4ca0e1'
[[ -f "$runner" && ! -L "$runner" && -f "$manifest" && ! -L "$manifest" ]] \
  || { printf 'NO-GO: runner/manifest unavailable or symlinked\n' >&2; exit 1; }
runner_b64="$(base64 -w0 -- "$runner" 2>/dev/null)" \
  || { printf 'NO-GO: runner capture failed\n' >&2; exit 1; }
manifest_b64="$(base64 -w0 -- "$manifest" 2>/dev/null)" \
  || { printf 'NO-GO: manifest capture failed\n' >&2; exit 1; }
actual_runner="$(printf '%s' "$runner_b64" | base64 --decode | sha256sum | awk '{print $1}')"
actual_manifest="$(printf '%s' "$manifest_b64" | base64 --decode | sha256sum | awk '{print $1}')"
[[ "$actual_runner" == "$expected_runner" && "$actual_manifest" == "$expected_manifest" ]] \
  || { printf 'NO-GO: approved input digest mismatch\n' >&2; exit 1; }
manifest_text="$(printf '%s' "$manifest_b64" | base64 --decode)"
[[ "$manifest_text" == "$expected_runner  $runner" ]] \
  || { printf 'NO-GO: manifest does not pin the runner\n' >&2; exit 1; }
printf '%s' "$runner_b64" | base64 --decode | \
  /usr/bin/env -i \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="$HOME" LANG=C LC_ALL=C \
  H3_DIAG_ROOT="$root" \
  H3_DIAG_VERIFIED_RUNNER_SHA256="$actual_runner" \
  H3_DIAG_VERIFIED_MANIFEST_SHA256="$actual_manifest" \
  /bin/bash -s -- \
    --jit H3-CLOSE-03-SNAPSHOT-CAUSE-DIAGNOSTIC-2026-10-07-D3 \
    --runner-sha256 "$actual_runner" \
    --manifest-sha256 "$actual_manifest"
H3_C03_D3_LAUNCHER
```

El launcher se inicia con entorno vacío (incluyendo sin `BASH_ENV`, funciones exportadas ni overrides Docker), captura como base64 ambos archivos, calcula los hashes sobre los bytes capturados y pasa exactamente esos mismos bytes verificados al intérprete por stdin. No reabre el payload después de validar el digest, eliminando el TOCTOU de hash-seguido-de-lectura del runner. El literal de aprobación sigue siendo una decisión humana: los hashes y el launcher no son por sí mismos autorización.

El runner permite únicamente:

1. Verificar el contexto Docker local por socket Unix y disponibilidad de la imagen fijada; no listar recursos Docker existentes.
2. Antes de crear el recurso, exigir que la imagen fijada no declare volúmenes. Ejecutar una vez `docker run --detach` con `--network none`, sin puertos, `--pull=never`, driver de logs local con máximo 1 MiB/1 archivo, `--restart=no`, rootfs read-only, `/diag` tmpfs de 16 MiB (`noexec,nosuid,nodev,mode=0700`, asignado a 1001:1001), `/dev/shm` de 16 MiB, 0.5 CPU, 128 MiB RAM/swap, 64 procesos, UID/GID 1001:1001, `--cap-drop=ALL` y `no-new-privileges`. No se ejecuta como root ni se añade ninguna capacidad.
3. Capturar desde el `stdout` de `docker run --detach` (sin mezclar `stderr`) un único ID; solo con exactamente una línea ID válida inspeccionar ese ID en una sola consulta: identidad/estado/exit/OOM/etiquetas, red/rootfs, user UID:GID, CapDrop, SecurityOpt, memoria/swap, NanoCPUs, PIDs, tmpfs `/diag`, `ShmSize`, restart, driver de logs, mounts y port bindings. Se exige como único mount `tmpfs` en `/diag` y ningún port binding. El runner exige que todos los valores coincidan con este JIT.
4. Si vence el límite o se interrumpe la ejecución, detener únicamente ese contenedor si sigue running y solo después de verificar su ID completo y etiquetas. El stop tiene límite de 5 s y no elimina el recurso.

Los comandos iniciales `docker context show/inspect` son lecturas locales de configuración, con timeout, para resolver el endpoint antes de disponer de una identidad de socket. El endpoint se captura como JSON con schema estricto, sin escapes ni caracteres de control; identidad pre/post socket y resolución `realpath` tienen cada una límite de 1 s más 0.2 s de gracia, y ambas identidades deben coincidir. Después Docker usa exactamente la ruta canónica mediante `DOCKER_HOST`; antes de cada operación del daemon, incluidas image inspect, create, wait, inspect, logs y stop, se revalida el path contra device/inode/uid/gid/mode registrados con el mismo límite. Persiste la carrera local entre comprobación y conexión. El create/start detached se limita a 20 s más 1 s de gracia; una salida create inesperada detiene pronto la lectura y causa NO-GO; `docker wait` a un máximo de 60 s más 1 s de gracia. Su respuesta se lee por un filtro byte-safe con `dd` limitado a cinco bytes y conversión hexadecimal acotada (solo se captura texto hex de tamaño fijo, no el stream crudo); solo acepta `0`–`255` seguido de LF y EOF, y falla cerrado ante NUL o bytes adicionales. Inspección, logs y stop se limitan a 20 s más 1 s por llamada. El runner usa un presupuesto nominal de 180 s y reserva 100 s después del wait para la única inspección agregada, lectura de logs y, en fallo, inspección/parada acotada. Estos caminos quedan por debajo de la reserva; `SECONDS` y la gracia de timeout hacen que el total sea presupuestado, no un watchdog duro externo. El tmpfs `/diag` y `/dev/shm` son de 16 MiB cada uno; el log local del único contenedor nuevo está limitado a 1 MiB/1 archivo. Al concluir, el contenedor queda `exited` y se preserva; no se hace cleanup, retry, resume ni rollback. No hay límite global de cgroup del daemon, pero el contenedor tiene los límites anteriores.

El contenedor solo emite categorías allowlisted. Los errores tar se clasifican con stderr sintético de hasta 4 KiB; no se imprime stderr crudo. El stream se lee en segmentos de hasta 513 caracteres, con máximo 64 líneas sanitizadas emitidas. El create acepta solo una línea ID en `stdout`, descarta `stderr` y aborta ante una línea inesperada/duplicada; los logs se limitan a 64 líneas y 1 MiB persistido. El stderr de comandos de control Docker se descarta y sus fallos se representan por fase, sin propagar texto del daemon. Errores de I/O/grep, categorías desconocidas, archivos/rutas inesperados, hash, permisos o espacio fallan cerrados. Los códigos quedan diferenciados como `producer-tar-exit`, `receiver-same-owner-tar-exit`, `receiver-no-same-owner-tar-exit`, estado de wait y exit inspeccionado del contenedor. Un resumen de salida enumera cada stage como código numérico o `not-run`, incluso ante NO-GO temprano/clasificador fallido.

El cuerpo del runner exige el entorno del launcher verificador, los dos argumentos de digest y el checkout candidato esperado. El hash se valida antes de invocar el cuerpo y los bytes validados son los mismos que `bash -s` recibe. Esto es una comprobación de integridad, **no una autorización** ni una prueba criptográfica de aprobación humana: solo se ejecutará tras que el responsable apruebe este JIT, comando y ambos digests exactos.

## Criterio y límites de decisión

El runner solo termina PASS si el productor pasa, `--same-owner` falla con clase `ownership-restore-denied`, `--no-same-owner` termina exit 0 y todos los checks de ruta/symlink, permisos, espacio y hash pasan. Cualquier otro resultado es NO-GO y conserva el diagnóstico; no hay retry implícito.

PASS demostraría el mecanismo en el fixture con la imagen y controles fijados; no convertiría S1 en smoke PASS, no probaría el snapshot completo y no acreditaría C03 integrado. La validación del snapshot fuente completo y cualquier corrección posterior necesitan alcance/JIT separado. El smoke Pages/workerd y C03 integrado permanecen bloqueados hasta sus propios gates.

Exclusiones: fuentes del candidato, `.env*`, credenciales, Auth real/mock, email, npm, workerd, Pages runtime, Edge, SQL/PG17/PostgREST, Supabase/Cloudflare, red externa, logs/exec/mounts/inspect de recursos históricos, cleanup, retries, rollback/resume, Git/CI remoto, push/PR/merge/deploy y cambios a scope guard.

## Scope guard e inclusión futura

La allowlist vigente de `Protected Path Integrity` no incluye el runner D3, su manifiesto `.sha256` ni este JIT bajo `.context/operaciones/`. Por tanto, estos artefactos no pueden incluirse en un PR protegido sin que una persona revise y autorice por separado el ajuste de scope guard. Este JIT solo autoriza (si se aprueba) una invocación diagnóstica local; no modifica workflows ni concede aprobación para cambiar allowlists o abrir PR.

Tooling diagnóstico únicamente: `expand` incorpora runner/manifiesto/evidencia sanitaria; compatibilidad de producto no cambia; deploy/contract no aplican. Rollback: detener el ciclo, preservar runner, reporte y recurso nuevo; no limpiar ni reanudar.
