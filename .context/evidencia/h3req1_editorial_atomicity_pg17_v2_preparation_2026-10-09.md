# Preparación PG17 de atomicidad editorial — parser de versión V2

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Ficha de impacto

- **Objetivo:** ejecutar el harness editorial fijado solo con PostgreSQL 17.11 y acreditar
  rollback atómico del cambio junto con su append de auditoría.
- **Archivos/rutas:** runner de prueba PG17, manifest transitivo de 36 entradas y un JIT
  temporal. No cambia migraciones ni comportamiento del producto.
- **Consumidores:** JIT de aceptación editorial; el runner monta `tests/sql`, `db/migrations` y
  `db/seeds` solo lectura.
- **Contrato:** la primera consulta de versión no expuso el valor y emitió
  `VERSION_OUTPUT_INVALID`. Su runner aceptaba solamente el formato bare
  `postgres (PostgreSQL) 17.x`. La salida real no se conservó; por eso no se afirma que un
  sufijo de distribución fuera la causa observada. V2 acepta un sufijo seguro separado por un
  espacio ASCII y rechaza saltos de línea o caracteres ajenos.
- **Transición/rollback:** fixture aislado, `network none`, SQL read-only, PGDATA tmpfs; el trap
  elimina el ID exacto del contenedor. No hay cambios persistentes de producto que revertir.
- **Permiso:** el JIT anterior y la lectura de versión ya están consumidos. La ejecución V2
  requiere una aprobación nueva para una invocación; el harness corre únicamente si el parser
  clasifica exactamente `17.11`.

## Revisión y comprobaciones locales

- Revisión estática del parser: major/minor se extraen de grupos numéricos; el sufijo no puede
  contener newline, y los códigos emitidos no incluyen metadata del contenedor.
- `bash -n tests/h3req1_c03_atomicity_pg17/run_editorial_atomicity_v2_once.sh`: PASS.
- Revisión de whitespace del runner: sin coincidencias.
- `sha256sum --check --strict` del manifest: 36/36 inputs PASS.
- Los siete casos sintéticos y el SQL no se ejecutaron localmente; ambos quedan detrás del JIT
  aprobado y se ejecutan dentro del contenedor PG17 sin red.
- Runtime, versión observada, harness y cleanup del siguiente ciclo: pendientes; no son PASS por
  sintaxis o hashes.

## Gate

G01 permanece abierto, total H3REQ1 10%. La única siguiente operación de este hilo es la
invocación concreta descrita en
[`JIT PG17 V2`](../operaciones/jit_h3req1_editorial_atomicity_pg17_version_classifier_v2_once_2026-10-09.md);
su SHA-256 actual es `8b491649c945983e01df7b0ca8b3bee3e23cf5aad0438961ce73c1623d3f7b19`.
