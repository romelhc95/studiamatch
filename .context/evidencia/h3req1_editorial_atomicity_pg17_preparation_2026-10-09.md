# Preparación de atomicidad de auditoría editorial PG17 — 2026-10-09

Estado: cobertura añadida al harness y revisión estática PASS; ejecución PG17 pendiente de JIT.

## Candidato y ficha de impacto

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP antes del ciclo: 55 tracked modificados, 243 untracked, 0 staged; checkout original
  `/home/romel/src/studiamatch` sin cambios de este ciclo (39 tracked modificados, 39
  untracked, 0 staged). Se preserva el WIP de ambos.
- Criterio cliente: la edición editorial debe conservar actor/fecha/antes/después y su
  registro de auditoría protegido debe ser atómico con la mutación.
- Archivos/dominios: solo se añadió cobertura en `tests/sql/h3_pg17_harness.sql`; se creó
  un manifest transitivo de 36 SQL inputs y un runner de una sola ejecución. No se cambió
  ninguna migración/product SQL, BFF, UI, workflow, secreto o configuración Docker.
- Consumidores: el harness PostgreSQL 17 aplica las migraciones H2/H3 del fixture y luego
  integra tres harnesses de invitación/onboarding. La migración editorial probada es
  `db/migrations/20261001_h3_course_editorial_audit_availability.sql`.
- Transición/rollback: no hay cambio de contrato de producto ni schema de producto. El
  constraint de inyección es temporal dentro del harness y se elimina antes de la ruta
  positiva existente. El fixture completo usa un único contenedor PG17 con red `none`,
  bind mounts read-only y directorio de datos tmpfs; el paquete solicita retirada del
  contenedor exacto después de preservar la salida sanitizada.
- Permisos: la edición local de cobertura sigue el `continua` humano. La ejecución del
  harness SQL/DDL/DML y la creación/eliminación del PG17 local no se han ejecutado y
  requieren aprobación JIT nueva porque cambió el hash del harness.

## Brecha demostrada y corrección mínima

El harness ya validaba actualización exitosa, conflicto de versión, evento con actor,
fecha, valores previos/nuevos, reset del override y falta de lectura directa por el rol
`authenticated`. No contenía una ruta que forzara el fallo del `INSERT` de auditoría y
demostrara que el cambio editorial anterior no persiste.

Se añadió un `CHECK ... NOT VALID` de nombre exclusivo que rechaza únicamente eventos
`action='update'`. El bloque de excepción requiere que PostgreSQL identifique ese nombre
de constraint, no cualquier `check_violation`. Después compara el registro completo de
`course_editorial_state` serializado a JSONB y el conteo de eventos con los snapshots
previos. Si no hubo el error esperado, cambió cualquier estado editorial o apareció un
evento, el harness falla. Luego retira el constraint antes de continuar las pruebas
positivas existentes.

La migración realiza el `UPDATE` de estado antes del `INSERT` de auditoría. PostgreSQL debe
revertir ambos en la subtransacción cuando el `INSERT` falla; esta es la propiedad que se
va a probar. No se afirma defecto de producto ni resultado runtime hasta ejecutar PG17.

## Revisión y validación local

- Revisión estática del flujo: PASS. El constraint se elimina antes del camino positivo;
  la captura usa `GET STACKED DIAGNOSTICS ... CONSTRAINT_NAME`, y el predicado final exige
  `atomicity_caught IS DISTINCT FROM true`, igualdad del registro completo y conteo de
  auditoría sin delta.
- `bash -n` del runner JIT: PASS.
- `sha256sum --check --strict` del manifest SQL: 36/36 inputs coinciden.
- `git diff --check` del harness tracked y whitespace check de los archivos nuevos: PASS.
- No se ejecutó psql, SQL, Docker, PG17 ni una suite de producto. Resultado funcional:
  pendiente, no PASS.

## Hashes y gates

- Harness `tests/sql/h3_pg17_harness.sql`:
  `24868250cf598a42412394c9cc714e6826096865846d0e8c3a73cb2a02f8e355`.
- Manifest SQL transitivo de 36 archivos:
  `0ed63a7b439275121caa9255ea033030f20e363fdb71eb202a47a94792ab2bc5`.
- Runner JIT `tests/h3req1_c03_atomicity_pg17/run_editorial_atomicity_once.sh`:
  `3465f73650d283f2731bfb10d28c8b01f66d81d8102dc539baf5b91f76e1aded`.
- Paquete JIT `operaciones/jit_h3req1_editorial_atomicity_pg17_once_2026-10-09.md`:
  `a795528ec0376ac64a88344a03380644eed5122da9f52ffd44cf19cd3b923ef7`; aprobación
  requerida antes de ejecución.
- G01/G09 permanecen incompletos; no se aumenta el total de cierre por una prueba añadida
  o por documentación. G02 conserva su evidencia C03 safe-suspend v3 41/41, cuyo manifest
  no incluye este harness editorial; esa evidencia no acredita la nueva propiedad atómica.
- La autorización npm anterior `d14b4f8…` ya está consumida con
  `REPORT_INVALID`; no se reutiliza. El clasificador V2 es un JIT distinto y sigue
  pendiente de una autorización nueva.
