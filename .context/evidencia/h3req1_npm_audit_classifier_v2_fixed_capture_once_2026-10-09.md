# H3REQ1 — resultado de auditoría npm con captura corregida

Fecha: 2026-10-09. Candidato: rama `feat/h3req1-sync-20261002`, HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Resultado

- JIT aprobado: `H3REQ1-CANDIDATE-V3-NPM-AUDIT-CLASSIFIER-V2-FIXED-CAPTURE-ONCE-20261009-V1`,
  SHA-256 `f06d497bfcc26cd321b6a2b96ebc8c2d2bc8fedfecf187df9eb00cdd601c9aea`.
- JIT y pins de runner, clasificador, sintéticos, manifests npm, rama y HEAD coincidieron antes
  de la invocación. Ejecutado una sola vez como UID 1000 en PTY; exit 1.
- Fases sanitizadas, en orden:

```text
phase=capture-synthetic-tests|error_code=OK
phase=image-preflight|error_code=OK
phase=synthetic-tests|error_code=OK
phase=npm-audit|error_code=EMPTY_STDOUT_STDERR_PRESENT
```

El parser Bash corregido pasó sus seis casos, el digest local de la imagen fijada coincidió y
los 14 sintéticos Python pasaron. La auditoría alcanzó npm; su stdout quedó vacío y stderr
estuvo presente, por lo que el clasificador emitió solo el código cerrado. El contenido crudo
de stderr no se preservó ni se imprime. No se atribuye causa de red o registry sin código
sanitizado que la demuestre.

## Efectos y gates

- El contenedor de auditoría fue lanzado con `--rm`; el runner elimina su directorio temporal de
  configuración al salir. No se modificaron dependencias, lockfile ni imagen. El reporte no
  contiene una fase de cleanup independiente.
- La invocación está consumida. No hay retry. G03 sigue abierto; este resultado no acredita
  audit PASS ni cierra candidato.
- Ninguna lectura F1, r9, `studiamatch-dev`, SQL, escritura remota, push, PR, merge o deploy.
- G01 editorial sigue pendiente de la versión PG17. G02 mantiene su evidencia separada 41/41.
  Total de cierre: 10%, delta 0.

La próxima corrección mínima del clasificador, si se aprueba, debe identificar en stderr solo
códigos npm de allowlist y devolver `UNCLASSIFIED` cuando no pueda hacerlo, sin emitir metadata
cruda ni repetir la solicitud automáticamente.
