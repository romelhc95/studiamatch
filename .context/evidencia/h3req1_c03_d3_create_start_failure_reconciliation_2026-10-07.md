# Reconciliación factual del resultado D3 — H3REQ1

Fecha: 2026-10-07. Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`,
rama `feat/h3req1-sync-20261002`, baseline HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Resultado comprobado

- JIT aprobado y consumido una sola vez:
  `H3-CLOSE-03-SNAPSHOT-CAUSE-DIAGNOSTIC-2026-10-07-D3`, SHA-256
  `cd90d783b7ec5a65a5ccc4e57fe6f737681d7aa4f8ed46a4d9c7e8c786f3ae7c`.
- Runner SHA-256: `a64fa5743372d5ff39fb9a009d89beb68a9afec756b32455066db06f84c41796`.
- Manifiesto runner SHA-256: `560ea87e661acd95406ea749358b060d0132dcc97300682db1b101ef1f4ca0e1`.
- El daemon devolvió el ID completo
  `81c57f0e70538d7430e46a61d745a3b6296fb943980342f2caeead19c0658ebf` para
  `h3req1-c03-snapshot-diagnostic-d3-20261007`; nonce del informe:
  `509355-1791394106958035732-20366`.
- Resultado: `NO-GO`, exit 1, fase `one-new-offline-synthetic-diagnostic-container`.
  La lectura acotada de identidad/estado usada por el propio runner registró `created`;
  `bounded-stop=not-needed`, `resource-preserved=true`. No se paró ni eliminó.

## Límite diagnóstico

El runner no llegó a ejecutar el proceso sintético dentro del contenedor: no se ejecutó
tar productor/receptor, no se validó el snapshot y no se alcanzaron npm ni Pages/workerd.
El `stderr` del comando Docker se descartó y no se consultó `.State.Error`. El resultado
solo establece que el comando `docker run --detach` terminó en fallo después de devolver
un ID y que el contenedor quedó `created`; **no demuestra por qué falló**, ni demuestra
ni descarta el mecanismo de restauración de ownership 1000:1000. Tampoco atribuye la
causa histórica del fallo S1.

La ejecución anterior del launcher que terminó por quoting (`unexpected EOF`) no produjo
archivo de evidencia D3; no consultó Docker. Hubo una sola invocación D3 con el JIT
aprobado.

## Preservación y estado documental

El reporte original D3 permanece intacto, SHA-256
`76e4c7c4182bcb30156f7a12eea87376aa68f6667c21a203ef8a7ddcc9f43a23`. El manifiesto D3
aprobado permanece intacto, SHA-256
`cd90d783b7ec5a65a5ccc4e57fe6f737681d7aa4f8ed46a4d9c7e8c786f3ae7c`; su línea inicial
“propuesto, NO aprobado, NO ejecutado” es el estado del corte de preparación, no un
registro mutable de la ejecución posterior. Esta nota y el estado vivo reconcilian el
resultado sin cambiar ni reemplazar ese artefacto consumido.

C02 v4 y C03 SQL v3 se conservan por inputs/alcance aplicables y no se repiten. D2, S1 y
D3 están consumidos. No hubo cambios de producto, SQL, Auth, red, npm, workerd, Pages,
Edge ni remoto. El smoke y C03 integrado siguen NO-GO.

## Siguiente gate, no autorizado todavía

El primer JIT de lectura [`D3 create/start error inspect`](../operaciones/manifiesto_jit_h3_close03_d3_create_failure_inspect_2026-10-07.md), SHA-256
`1ec96b5a1820e519625bce113777e99fb1e2e693c8317f27625358ec08b241f1`, fue aprobado y
consumido en una única consulta. El `docker inspect` devolvió exit 0 y salida bajo el límite;
el parser/sanitizador falló cerrado en identidad/schema/sanitización. Solo se emitió
`NO-GO: identity/schema/sanitizer failed; raw output discarded`; no se expuso ni persistió
el JSON crudo y no se recuperó causa. No hubo `start`, retry, `exec`, logs, stop, remove,
cleanup ni otra inspección; el último estado evidenciado del contenedor sigue siendo
`created` y el recurso no fue modificado por la lectura.

J2 [`D3 State.Error only`](../operaciones/manifiesto_jit_h3_close03_d3_state_error_read_2026-10-07_j2.md), SHA-256
`47d6c7f0d4edf0a574871582accbc1fda4ca2929e4fad03ea724a2f11e8d2267`, fue aprobado y
consumido una sola vez. Recuperó el texto sanitizado `failed to create task for container:
failed to initialize logging driver: compression cannot be enabled when max file count is 1`.
La causa de D3 es la incompatibilidad de configuración del logging local; D3 no alcanzó
tar. Este resultado no explica S1 ni demuestra ownership. Ver [evidencia J2](h3req1_c03_snapshot_d3_state_error_read_2026-10-07_j2.md).

El siguiente cambio de tooling fue únicamente añadir `--log-opt compress=false` a un runner
diagnóstico nuevo, manteniendo `max-size=1m`, `max-file=1` y todos los demás controles.
D4 está preparado con runner SHA-256
`785908597840def21e394c11181114d34a349746226a3c058a8bb3426f2f6107`, sidecar
`84b06ba5dcaa3795e1267397d13d57f12aa0b2b5d83b4beca14a9b8fb49b3e4c` y JIT SHA-256
`fcec517023f4a85e1381ad4b1b2be949fba933596e469293fed28315397a4fba`. No modifica D3 ni
accede al recurso preservado. Sintaxis y hashes locales pasaron; la auditoría independiente
solo revisó el delta por falta de acceso al checkout. La ejecución queda pendiente de
aprobación JIT separada.

Transición documental solamente: `expand` añade esta reconciliación; compatibilidad
conserva el comportamiento y la historia; deploy/contract no aplican. No hay GO local
ni autorización de push/PR/merge/deploy.

## Actualización posterior D4 — 2026-10-07

D4, preparado en el corte anterior, fue aprobado/consumido una vez y terminó NO-GO al
fallar la verificación de metadata/controles; el proceso sintético devolvió exit 0. Su
evidencia sanitaria, preservación del recurso y siguiente JIT read-only están en la
[reconciliación D4](h3req1_c03_d4_metadata_mismatch_reconciliation_2026-10-07.md).
No cambia la causa D3 demostrada ni aporta causa de S1.
