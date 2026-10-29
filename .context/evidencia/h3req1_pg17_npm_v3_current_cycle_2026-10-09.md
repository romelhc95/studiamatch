# Ciclo actual PG17 editorial y auditoría npm V3 — 2026-10-09

Snapshot candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Invocaciones aprobadas y consumidas

| Objetivo | Aprobación / ejecución | Resultado sanitizado | Gate |
|---|---|---|---|
| Leer una vez la versión de la imagen PostgreSQL fijada | `H3REQ1-PG17-PINNED-IMAGE-VERSION-ONCE-20261009-V1`, JIT SHA `a7787182737186ae43cb4e82f6f88a4fb7a71bdf52e2de7e1f9967672c2835b1`; runner SHA `fa2203dc1f034116bdf2251b04f165f7e617e5e2aa988f6d94fd94a98bf2fcf4`; exit 1 | `preflight=OK`, `container-create=OK`, `version-read=VERSION_OUTPUT_INVALID`, `container-cleanup=OK` | Consumido. El contenedor exacto se limpió. No se leyó SQL. El contenido de la versión no se guardó; no se atribuye la causa a la imagen. |
| Clasificar una vez la salida de `npm audit` | `H3REQ1-CANDIDATE-V3-NPM-AUDIT-CLASSIFIER-V2-FIXED-CAPTURE-ONCE-20261009-V1`, JIT SHA `f06d497bfcc26cd321b6a2b96ebc8c2d2bc8fedfecf187df9eb00cdd601c9aea`; runner SHA `0c48f12b818c8611c1187fa402f92bb502ed6ea45cb17cc13270db28a51a58f5`; exit 1 | `capture-synthetic-tests=OK`, `image-preflight=OK`, `synthetic-tests=OK`, `npm-audit=EMPTY_STDOUT_STDERR_PRESENT` | Consumido. npm fue alcanzado; no se conserva stderr crudo ni se demuestra su causa. No se modificaron dependencias o lockfile. Sin retry. |

## Corrección preparada y gates pendientes

- En PG17, la lectura read-only posterior falló porque su parser solo aceptaba la versión bare;
  el valor real no fue conservado. El runner editorial V2 permite un sufijo de distribución
  acotado por espacio ASCII, extrae solo major/minor y ejecuta sintéticos antes del contenedor.
  Si la versión no es `17.11`, el harness y SQL se omiten. El JIT actualizado es
  `operaciones/jit_h3req1_editorial_atomicity_pg17_version_classifier_v2_once_2026-10-09.md`,
  SHA-256 `8b491649c945983e01df7b0ca8b3bee3e23cf5aad0438961ce73c1623d3f7b19`.
- Para npm, V3 reconoce únicamente líneas exactas de código npm. Un código allowlisted puede
  aparecer sanitizado; uno desconocido o una línea ambigua produce `NPM_ERROR_REPORT`. Dos casos
  nuevos cubren `EAI_AGAIN` y un código desconocido. El nuevo JIT está en
  `operaciones/jit_h3req1_candidate_v3_npm_audit_classifier_v3_once_2026-10-09.md`, SHA-256
  `d1bacad0aa0281aabb3e8bd1c04598cc99330770aadf79eb86eaf3960e55d3db`.
- Ambos paquetes exigen aprobación nueva; los permisos consumidos no se reutilizan. Los cambios
  son tooling de aceptación y no tocan las fuentes de producto, SQL, secretos o Docker.
- Revisión local: Bash syntax PASS en ambos runners; whitespace limpio. Manifest editorial PG17
  36/36 inputs PASS. Hashes de package/lock npm coinciden con los valores fijados. Las pruebas
  sintéticas Python no se ejecutaron en host; el JIT V3 las ejecuta dentro de la imagen antes de
  su etapa condicionada.

## Métrica y límites

G01 continúa 0/10, G02 conserva 10/10 por su manifest separado C03 SQL v3 41/41, G03 continúa
0/10 y G04–G10 continúan 0/10 cada uno. Total **10%**, delta **0 puntos**. Ninguna preparación,
limpieza, sintaxis o coincidencia de hashes suma cierre. No hay GO_LOCAL_PR ni
GO_DEVELOPMENT_REAL. El candidato aún requiere los restantes gates locales, revisión
independiente y aceptación.

## Docker activo y simplificación dentro del ciclo

Lectura read-only acotada al contenedor conocido `studiamatch-dev` (sin inspect completo ni
scan global): ID `115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`, estado
`restarting`, exit 1, 71 reinicios; imagen `studiamatch-dev:local`, ID
`sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`. Compose usa
`/home/romel/src/studiamatch/docker-compose.yml`, servicio `app`, bind del checkout original a
`/app` y volumen persistente `studiamatch_node_modules:/app/web/node_modules`.

El último JIT de rebuild/cutover aprobado y consumido (V3) dejó una imagen candidato local
`studiamatch-h3req1:20261009-v3` (`sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`):
build y smoke PASS; cutover FAIL porque `.env.local` no está en el checkout candidato; rollback
PASS al `studiamatch-dev` original; cleanup histórico no alcanzado. La imagen permite el auditor
npm, pero el runtime de integración no está activo. La diferencia entre manifests fuente e
imagen está demostrada en la reconciliación previa; logs recientes no prueban que sea la causa
del reinicio. Se preservan el contenedor de rollback, el runtime R4 fallido, volúmenes y
evidencia; no se ha eliminado recurso. Otro cutover requiere paquete corregido y JIT nuevo.
