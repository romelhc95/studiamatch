# Preflight y revisión estática F1 — snapshot de fuente H3REQ1

Fecha: 2026-10-07. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Alcance del ciclo

Corregir el runner nuevo de snapshot F1 y sus pins/JIT a partir de una auditoría estática.
Solo se modificaron artefactos de diagnóstico/documentación; no hay cambios funcionales de
producto, SQL/DB, Auth, CI, workflows, secretos o servicios remotos. No se ejecutaron Docker,
el runner F1, npm, workerd ni Pages. La autorización humana `continua` permitió estas
correcciones locales, no la ejecución del JIT.

## Artefactos fijados

| Artefacto | SHA-256 |
|---|---|
| `tests/h3req1_c03_source_snapshot_f1.sh` | `3249cdfed8043dfd751074ec0d844d6a9a88f14328b144f10d93c41cbbb446e0` |
| `tests/h3req1-c03-source-snapshot-f1.sha256` | `23d676776ce7fb95001576315d39913425756ea388809eed199dab4c0260af40` |
| `.context/operaciones/manifiesto_jit_h3_close03_source_snapshot_2026-10-07_f1.md` | `e4a651f47322cec8a9d7551a93b40186d2c25089215aa1b7b8c87a4263c2547f` |
| `tests/h3req1-c03-startup-source-s1.sha256` | `ae335c8e197d2c380bc877abbd53aa9f52a30f2b00e3310865bccb64ecb17c5d` |

## Correcciones verificadas

- Se eliminó la definición duplicada de `stop_new_container`; la única implementación
  permite un stop acotado solo tras CID propio, controles/identidad completos pre-start y
  `START_ATTEMPTED`. Ya no depende de un estado cacheado que quedara `created` tras comenzar
  el proceso.
- F1 divide la operación en `create` (sin proceso), inspección completa pre-start, un único
  `start --attach --interactive`, e inspección final. Si no se verifica el recurso antes de
  start, no se inicia. Un fallo/señal después de start permite una sola petición de stop al
  ID propio pre-verificado; no hay retry/remove.
- La lectura del CID consume como máximo 66 bytes antes de validar ID hexadecimal y LF
  opcional. No hay `wc`/`cat` del CID sin límite.
- Operaciones locales individuales llevan timeout; manifest/source tienen límites de bytes,
  tar está acotado y el launcher envuelve preflight y ejecución con TERM a 270 s/KILL tras
  30 s. El runner reserva tiempo de stop.
- El stderr de Docker se descarta en la frontera común y en call sites; salida del proceso
  pasa por filtro allowlisted de una sola línea. `.Mounts` no se usa para validar tmpfs:
  `/snapshot` se comprueba mediante `HostConfig.Tmpfs`.
- Sidecar, launcher y tabla del JIT se actualizaron a los pins indicados arriba.

## Validaciones ejecutadas

- `bash -n tests/h3req1_c03_source_snapshot_f1.sh`: PASS.
- `sh -n` del payload sintético extraído del runner: PASS.
- `bash -n` del bloque exacto del launcher F1 extraído del JIT: PASS.
- `sha256sum --check tests/h3req1-c03-source-snapshot-f1.sha256`: PASS.
- `sha256sum --check tests/h3req1-c03-startup-source-s1.sha256`: PASS (13/13 inputs).
- Comprobación de una sola definición de cleanup, branch/HEAD, ausencia de placeholders y
  `git diff --check`: PASS.
- Docker y F1: **NO ejecutados**.

## Revisión de seguridad independiente y residual

La primera auditoría de esta iteración encontró pins obsoletos, un cleanup no confiable por
duplicación/estado stale, bounds incompletos, un CID leído sin cap y falta de timeout global.
Se corrigieron antes de la revisión final. Segunda auditoría estática independiente sobre
runner/sidecar/JIT: **0 HIGH, 0 LOW; un MEDIUM de autorización**. Confirmó que el cleanup
duplicado/estado stale, el stderr raw y el timeout que no cubría el preflight quedaron
remediados.

Residual MEDIUM: la misma cuenta local con acceso al daemon Docker puede invocar el runner
directamente y fijar argumentos/variables `H3_SNAPSHOT_VERIFIED_*`; un script local no puede
hacer de frontera criptográfica frente al dueño del proceso/daemon. El launcher verifica
integridad, pero la aprobación JIT sigue siendo procedimental. El [JIT F1](../operaciones/manifiesto_jit_h3_close03_source_snapshot_2026-10-07_f1.md)
describe causa/evidencia estática reproducible, riesgo, mitigación, owner `Romel` y expiración
tras una invocación o cancelación. **Waiver NO aprobado; F1 sigue NO-GO.** La aceptación del
waiver y la aprobación humana de una única ejecución F1 son gates pendientes e independientes
de esta revisión. No se debe consultar ni crear Docker antes de ambos.

## Resultado

Preflight estático completo para solicitar revisión/aprobación, pero no GO de ejecución:
F1 permanece **NO-GO** por el residual MEDIUM no aprobado. Snapshot completo S1, smoke
Pages/workerd, C03 integrado, `GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL` permanecen NO-GO.
El smoke Pages/workerd requiere su propio runner/JIT posterior, solo después de un F1 PASS.
