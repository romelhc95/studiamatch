# H3REQ1 — resultado de captura V8 y auditoría npm V3

Fecha: 2026-10-09. Candidato: `feat/h3req1-sync-20261002`, HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## V8 Tmpfs: autorización recibida, ejecución sin resultado observable

El usuario aprobó una invocación de V8, JIT SHA-256
`f286b7c916fb434d7f55afa6d8bb0104df4d9bd52d382e061fe2570f1438477d`.
Codex emitió el runner fijado mediante una ejecución PTY. La respuesta de la herramienta quedó
truncada sin entregar phase ni exit. Una lectura posterior del terminal de la aplicación no
devolvió salida; una consulta de procesos no encontró el runner activo. No se puede determinar
si el proceso alcanzó las pruebas sintéticas, el daemon o Docker.

La autorización se considera consumida administrativamente para evitar duplicar una acción
one-shot. No se repite V8. No se acredita PASS ni FAIL; no se afirma que se leyó F1 o se ejecutó
r9. No hay resultado Docker verificable para agregar a los gates.

## Auditoría de advisories de la imagen V3 — invocación consumida

El dispatcher V3 informó durante `npm ci` dos advisories, uno `high` y otro `critical`, pero no
conservó su detalle. La consulta read-only aprobada se ejecutó una vez y no produjo un resumen.

| Insumo | SHA-256 / valor fijado |
|---|---|
| JIT `.context/operaciones/jit_h3req1_candidate_v3_npm_audit_once_2026-10-09.md` | `d14b4f8c6bec307c401b0ddda4fa73e249fc6d7e3058178a10525dc2ca4293fd` |
| Runner Bash | `d2dfb357c7584451727b73898f565ca363a9e5c81f0d77b477035948ef562c2f` |
| Auditor Python dentro del contenedor | `4ca41e19643192abec6f0547efd665e996be575e7ed39416940a2d840d34d2d6` |
| Pruebas sintéticas | `48036a07f1754335e2c503f248d68cdc07d353a0756fcd0afcb4d234c11c0c64` |
| `web/package.json` | `4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a` |
| `web/package-lock.json` | `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc` |
| Imagen/tag V3 | `studiamatch-h3req1:20261009-v3` → `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63` |
| JIT ejecutado | `d14b4f8c6bec307c401b0ddda4fa73e249fc6d7e3058178a10525dc2ca4293fd` |

Validación de preparación: `bash -n` del runner pasó; hashes package/lock coinciden con los
pins; el runner fija rama/HEAD, prueba los tres archivos del directorio allowlisted, verifica
el tag por ID, usa `--pull=never` y contiene límites de tiempo/salida. Los seis tests se
ejecutan con `/opt/venv/bin/python` **dentro** de la imagen V3; no se corrieron comandos
Python en el host.

Autorización recibida para una sola invocación del JIT SHA-256
`d14b4f8c6bec307c401b0ddda4fa73e249fc6d7e3058178a10525dc2ca4293fd`. Se ejecutó una vez en
PTY como `romel` no-root, sin sudo. Resultado sanitizado, exit 1:

```text
phase=image-preflight|error_code=OK
phase=npm-audit|error_code=REPORT_INVALID
```

El runner llega a la fase `npm-audit` solo después de verificar el marcador literal
`V3_NPM_AUDIT_SYNTHETIC_PASS:6/6`; los seis casos sintéticos pasaron dentro de la imagen y la
consulta alcanzó la decodificación del stdout de `npm audit`. El código `REPORT_INVALID` se
emite al fallar `json.loads` sobre ese stdout. La salida cruda se descarta tanto dentro del
runner como en el límite del contenedor, así que no es posible distinguir si npm emitió texto
no JSON, un cuerpo de error de red u otra respuesta. No se obtuvo un resumen de advisories ni
una causa más específica. La autorización quedó consumida: no se repite la llamada ni se
modifican dependencias.

## Gates y métrica

- G03/G04 siguen abiertos; la salida V8 no es verificable.
- El auditor V3 pasó 6/6 sintéticos, pero la única consulta npm concluyó
  `REPORT_INVALID`/exit 1 y no generó el resumen de advisories. No se corrigen ni promueven
  dependencias con base en el conteo agregado solamente.
- Se preparó una solicitud nueva e independiente que clasifica forma/tipo de stdout y
  presencia de stderr sin imprimir datos crudos: JIT
  `.context/operaciones/jit_h3req1_candidate_v3_npm_audit_classifier_v2_once_2026-10-09.md`,
  SHA-256 `1a70db5a61e9fdf63660b296404c8ec188014b0d1b08bb8f9148975e6902ac2e`. El runner
  `bash -n` pasó y todos los pins locales se fijaron; seis casos sintéticos del parser de fases
  Bash y 14 aserciones dentro de la imagen V3 aún no se ejecutaron. La consulta requiere
  aprobación nueva.
- Total H3REQ1: 10% de controles de cierre completos; delta 0. Esta documentación y la
  preparación del paquete no suman puntos.
