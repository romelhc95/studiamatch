# G08 R174 — regresión de secretos en historia Git — 2026-10-11

## Alcance e impacto

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`. La identidad del candidato
  incluye el WIP; HEAD no lo representa.
- Componentes: `scripts/security/scan_credentials.sh`,
  `.githooks/pre-push` y `tests/test_scan_credentials.sh`, además del contrato
  estático `tests/test_security_flow.py`.
- Consumidores: pre-push local y job Credential Scan de
  `.github/workflows/security-audit.yml`. El job/workflow no se ejecutó ni se
  configuró en remoto.
- Contrato preservado: el scanner falla cerrado, redacciona rutas/hallazgos,
  mantiene `--tree`, `--staged` y `--files`; no imprime valores. El cambio solo
  amplía la cobertura de `--diff` a los blobs de cada commit nuevo.

## Hallazgo y reproducción

La revisión independiente del código encontró que `--diff base head` comparaba
solo los nombres del delta neto y leía el blob de HEAD. Un archivo o valor
secreto añadido en un commit y borrado/saneado antes de HEAD seguía dentro de la
historia que se enviaría, pero no estaba en el árbol final y pasaba el scanner.
El hook pre-push y CI consumían ese modo. Severidad asignada por la revisión:
HIGH.

Se añadió primero una regresión sintética con valor construido en runtime
(`sb_secret_` + caracteres `a`), nunca con una credencial real. En Docker,
antes del cambio del scanner, la prueba salió exit 1 con
`scanner regression failed: credential-like value in a transient commit passed diff scan`.
La salida no incluyó el valor sintético. Esto reprodujo el hueco del control.

## Corrección

- `--diff` valida que HEAD sea un commit y enumera en orden los commits
  `base..head`. Si base es un árbol (por ejemplo, rama remota nueva), recorre
  toda la historia alcanzable desde HEAD. Cualquier error al resolver
  referencias, enumerar commits/rutas, leer blobs o escanear hace fallar la
  operación.
- Para cada commit se enumeran cambios contra sus padres, incluida raíz y
  merges; se escanean el path y el blob de ese commit, no solo el contenido de
  HEAD. Así se detectan blobs transitorios aunque luego se eliminen o saneen.
- En primer push el hook ahora materializa el árbol vacío con
  `git hash-object -t tree -w /dev/null`, requerido por el recorrido por
  historia. No escribe fuera del repositorio local ni contacta al remoto.
- No se alteraron reglas de patrones, exclusiones, checkout original, secretos,
  credenciales, recursos Docker persistentes, producto ni configuración
  remota.

## Validación ejecutada

| Prueba | Comando/entorno | Resultado |
|---|---|---|
| Regresión scanner | `docker exec studiamatch-dev ... bash tests/test_scan_credentials.sh` | **PASS**, exit 0: `history=5`; cubre blob transitorio lineal eliminado, base árbol vacío, secreto solo en root seguido de saneamiento, secreto introducido únicamente en resolución de merge y saneado después, y pre-push con OID remoto nulo. También conserva texto/binario, NUL/newline paths, salida redaccionada, errores I/O y concurrencia. |
| Sintaxis shell | `bash -n scripts/security/scan_credentials.sh tests/test_scan_credentials.sh`; `sh -n .githooks/pre-push`, en `studiamatch-dev` | **PASS**, exit 0. |
| Contratos Python relacionados | `env -i ... /opt/venv/bin/python -m pytest -q -p no:cacheprovider tests/test_security_flow.py tests/test_supabase_credentials_contract.py tests/test_protected_workflow_review.py`, en Docker | **PASS**, 70 passed, exit 0. El primer intento con `/usr/bin/python3` terminó exit 1 porque esa instalación no tiene pytest; se corrigió al intérprete de pruebas presente en el contenedor, sin instalar paquetes. |
| ShellCheck | ShellCheck v0.11.0 local, contenedor `--network none`, fuentes exactas montadas read-only | **PASS**, exit 0, scanner, pre-push y prueba shell. Un warning SC1007 preexistente en la asignación CDPATH del test se corrigió antes del pase final. |
| Scanner de inputs cambiados | `bash scripts/security/scan_credentials.sh scripts/security/scan_credentials.sh tests/test_scan_credentials.sh .githooks/pre-push tests/test_security_flow.py`, en Docker | **PASS**, exit 0, sin valores en salida. |

Intentos conservados y límites: `--tree` sobre `/app` en `studiamatch-dev`
terminó exit 2 antes del scan porque el archivo `.git` del worktree apunta al
directorio administrativo del checkout original, no montado dentro del
contenedor (`not a git repository`). No se cambió Git config ni se montó el
checkout original. La suite R174 sí ejercita `--tree` y `--staged` sobre un
repositorio Git sintético aislado. La implementación de esos dos modos no
cambió; el scan del árbol candidato anterior R159 se conserva con su hash y
alcance originales, no se presenta como una nueva ejecución R174.

## Revisión independiente y límite operativo

El revisor volvió a examinar la corrección y confirmó que raíz, merges, commits
lineales, árbol base, rutas y blobs se procesan fail-closed. Los dos hallazgos
LOW de cobertura quedaron cubiertos por las regresiones ejecutadas; el revisor
no encontró HIGH/MEDIUM en el delta corregido.

Si la primera publicación de una rama no tiene OID remoto base, el scan recorre
toda la historia alcanzable. Ese costo es inherente a revisar cada commit y
blob que se puede enviar; no se introdujo límite que permita omitir commits.
La duración de un primer push completo no se midió y no se afirma un SLA. Ante
interrupción, fallo de Git o scan error, el push sigue bloqueado. No se
optimiza por `HEAD`, primer padre ni refs remotas locales potencialmente
obsoletas.

G08 continúa completo para el alcance local aplicable tras renovar el scanner
y sus contratos. G09/LOCAL-23 continúa pendiente de conciliación y revisión
independiente del paquete completo actualizado; R174 no cierra ese gate por sí
solo. G10 remoto sigue NO-EJECUTADO.
