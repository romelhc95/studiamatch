# G07 R17 — Pages health y servicios listos; invitación rechazada antes de reserva

## Resultado

- Candidato: `feat/h3req1-sync-20261002` @ `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Runner R17 y manifiesto de 67 entradas pasaron sus pins; `sha256sum -c` 67/67.
- Docker Desktop local pasó identidad y capacidad; imágenes fijadas presentes; PostgreSQL 17.11,
  snapshot íntegro, contrato 18/18 y caches read-only pasaron.
- Pages/workerd `healthz` PASS; PG17/PostgREST iniciaron y la sonda real de PostgREST pasó.
- Login sintético PASS (`aal2`, cookies HttpOnly de auth y actividad presentes).
- Fase siguiente `real-edge-invite-held-after-reservation`: exit 1. El control recibió el código
  sanitizado `INVITE_EARLY_UNAUTHORIZED` en `/control/trigger-inflight`. El runner hizo
  stop-on-failure y detuvo exactamente runtime, PG17, PostgREST y Edge R17; ninguno quedó running.
- Log sanitizado: [R17 run](h3req1_c03_integrated_run_2026-10-10_r17.log), SHA-256
  `811ebc5d4c53336d0bf55ae7e5dab3ade6e094b609b7a13b9aa7df71ee78e576`.
- Manifiesto exacto de inputs R17 preservado:
  [R17 manifest](h3req1_c03_integrated_manifest_r17.sha256), SHA-256
  `6532388df6a09dd7dfd2359cc9979ad6666d1fec8b1f5c9dc1d2a567437f6105`.
- Runtime exacto usado: SHA-256 `828b93c2d9774884cd3cfa710b891bb84b8a85ac123445383fac30733a12ca38`;
  se archivará antes de instrumentar el siguiente ensayo.

## Clasificación e impacto

Se demostró que el fallo está en el flujo local de invitación: Edge devolvió el código
`unauthorized` durante su autorización o durante una dependencia que se transforma en ese
código. El log no demuestra por sí solo si Auth rechazó la sesión sintética o si la lectura
PostgREST de membresía falló. No es evidencia de un defecto de producto ni de Docker.

No se ejecutó la aserción SQL de reserva ni ninguna fase de suspensión, finalización in-flight,
reanudación o smoke de recuperación. G07 continúa parcial; métricas sin cambio.

El siguiente runner añadirá únicamente contadores sintéticos de etapa: solicitudes y resultado
del mock `/auth/v1/user`, entrada/aceptación de la llamada Edge, lectura PostgREST de
`admin_members` (status numérico) y RPCs de admisión/reserva. Las salidas quedan limitadas a
enteros/enum allowlisted; no se imprimen tokens, headers, cuerpos, errores crudos ni SQL. Esto
determinará el componente que origina `unauthorized` antes de considerar una corrección.
