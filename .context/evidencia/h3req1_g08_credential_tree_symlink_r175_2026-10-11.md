# G08 R175 — lectura segura de `--tree` — 2026-10-11

## Candidato y hallazgo

Candidato local: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`; el WIP forma parte de la
identidad y el checkout original sigue intacto.

La revisión independiente del cambio R174 encontró que el nuevo recorrido de
`--tree` detectaba symlink en el componente final, pero comprobaba una ruta
anidada mediante `-f`/`grep`. Si un directorio padre rastreado se sustituía por
un symlink, el scanner podía leer un archivo fuera del checkout. El chequeo y
la lectura también tenían una ventana TOCTOU. Severidad: MEDIUM; se detuvo el
cierre de G08/G09 antes de promover el estado.

## Corrección y regresión

`scripts/security/scan_worktree_file.py` abre el root y cada directorio padre
por descriptor con `O_DIRECTORY|O_NOFOLLOW`; abre el archivo final con
`O_NOFOLLOW|O_NONBLOCK`, valida con `fstat` que sea regular y lee desde el mismo
descriptor. Así no hay resolución posterior del path que permita escapar por
un symlink ni cambio de destino entre validar y leer. Un symlink final se
representa solo por el texto literal de su destino; no se abre. Componentes
inseguros, errores de permisos y tipos no regulares hacen fallar cerrado con
un código genérico sin ruta ni contenido.

La suite ahora comprueba cuatro escenarios `--tree`: ruta con newline, secreto
solo en el worktree, secreto solo en el índice y una ruta anidada con directorio
padre reemplazado por symlink a un fixture externo. El último caso exige el
código sanitizado de rechazo seguro y confirma que el valor sintético externo
no aparece en salida. Los escenarios de historia de R174 permanecen.

## Validación ejecutada

| Fase | Entorno / comando | Resultado |
|---|---|---|
| Scanner y sintaxis | `docker exec studiamatch-dev ... bash -n ...; python3 -m py_compile scripts/security/scan_worktree_file.py; bash tests/test_scan_credentials.sh` | **PASS**, exit 0; `tree=4`, `history=5`, errores de I/O 4, concurrencia 2 y redacción PASS. |
| Contratos relacionados | `docker exec studiamatch-dev ... /opt/venv/bin/python -m pytest -q tests/test_security_flow.py tests/test_supabase_credentials_contract.py tests/test_protected_workflow_review.py` | **PASS**, 70 passed, exit 0. |
| ShellCheck | `koalaman/shellcheck:v0.11.0`, `--pull=never --network none --read-only`, scanner/pre-push/test montados read-only | **PASS**, exit 0. La primera llamada incluía incorrectamente el nombre del ejecutable bajo la imagen con entrypoint ShellCheck y no llegó a analizar archivos (exit 2); la llamada corregida pasó. |
| Árbol tracked actual | Lista `git ls-files -z` del checkout candidato enviada al scanner en `studiamatch-dev` | **PASS**, 679 paths, exit 0 (`credential scan passed`). |
| Scope propuesto + evidencia | 88 paths propuestos + 138 evidencias del R4 histórico + helper y esta nota R175; scanner de archivos en Docker | **PASS**, 228 paths únicos, exit 0. R4 es solo la base del conteo y será sustituido por R5 con el helper incluido. |

Los cuatro inputs Shell/Docker tuvieron los mismos SHA-256 en el checkout y en
`studiamatch-dev`: scanner `9f32223c…`, helper `99d00912…`, suite
`46bd8379…` y pre-push `4be32e10…`. El contenedor observado fue
`studiamatch-dev`, imagen `studiamatch-h3req1:20261009-v3`, ID
`500931b0f086…`, estado running/healthy. No se leyó `.env*`, no se accedió a
secretos o servicios remotos, no se cambió Docker y no se siguió el symlink del
fixture. La prueba usa solo una cadena sintética construida en tiempo de
ejecución. `--tree` sobre `/app` del
contenedor de desarrollo continúa limitado por el enlace `.git` fuera del
mount; por eso esta validación ejecuta los casos `--tree` en repos sintéticos.
El scan completo del scope candidato se registra por separado en el corte G08.

R175 renueva un control dentro de G08; no agrega un punto a la métrica histórica.
El helper Python es un nuevo input del candidato y debe incluirse en el
manifest final. G09/LOCAL-23 permanece pendiente hasta revisar el scope completo
actual, actualizar manifiesto/borrador del PR y pasar revisión independiente.
G10 remoto permanece sin ejecutar.
