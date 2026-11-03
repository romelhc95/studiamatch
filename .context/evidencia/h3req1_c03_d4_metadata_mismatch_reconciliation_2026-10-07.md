# Reconciliación del NO-GO D4 — H3REQ1

Fecha: 2026-10-07. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Ejecución autorizada

- JIT D4 aprobado/consumido una vez, SHA-256
  `fcec517023f4a85e1381ad4b1b2be949fba933596e469293fed28315397a4fba`.
- Runner SHA-256 `785908597840def21e394c11181114d34a349746226a3c058a8bb3426f2f6107`;
  sidecar SHA-256 `84b06ba5dcaa3795e1267397d13d57f12aa0b2b5d83b4beca14a9b8fb49b3e4c`.
- Antes de invocar, rama/HEAD y los tres hashes se verificaron; coincidieron con la
  aprobación. Se ejecutó una sola vez el launcher literal del manifiesto.
- Evidencia generada por el runner y preservada sin editar:
  [reporte D4](h3req1_c03_snapshot_diagnostic_2026-10-07_d4.md), SHA-256
  `022edaab6a693cb7d1261595aefd1588f89904c03b8a741d296b85f5cd2a5efe`.

## Resultado

El Docker local creó únicamente el contenedor D4
`d52d606bdc809eb7bfd13c6e16c4e0a7bc29db2bf3e71e7941b75a84de868650` con el nombre y nonce
fijados. `docker run --detach` terminó 0; `docker wait` reportó el exit code del proceso
contenedor como 0. Luego `verify_new_container` rechazó la metadata con
`new diagnostic container identity, state, or controls differed from this JIT`.
El runner entró en el manejo de fallo e hizo la lectura de identidad permitida por JIT;
confirmó `state=exited`, por lo que `bounded-stop=not-needed`. No se detuvo ni eliminó.

El payload sintético solo devuelve 0 en su rama final de confirmación: productor tar=0,
`--same-owner` clasificado como `ownership-restore-denied`, `--no-same-owner`=0 y paths,
symlinks, permisos y hashes esperados. Por tanto, el proceso reportó PASS interno de ese
fixture sintético. **El ensayo D4 completo permanece NO-GO** porque la verificación de
identidad/controles de Docker falló; no se leyeron los logs ni se aceptan esos controles
como verificados. El campo exacto discrepante no se guardó en la evidencia y no se infiere.

El recurso permanece preservado en el último estado observado `exited`. No hubo logs, exec,
stop, cleanup, retry, segundo run, ni acceso a D3/S1/R1–R4, fuentes del producto, npm,
workerd, Pages, DB, Auth o remoto fuera de lo expresamente autorizado por D4.

## Estado y siguiente gate

NO-GO de D4, snapshot completo, smoke Pages/workerd, C03 integrado, `GO_LOCAL_PR` y
`GO_DEVELOPMENT_REAL`. D4 no prueba la causa histórica de S1 ni convierte el fixture PASS
interno en GO integrado.

J3 fue aprobado/consumido una sola vez, SHA-256
`1ce8f345b4b8c92559228d5cc6d5b46ae198d2febbef486efb1f9111a61676f1`. Confirmó que solo
fallaba la expectativa `.Mounts`; `HostConfig.Tmpfs[/diag]` coincidió y los demás campos
allowlisted pasaron. Ver [evidencia J3](h3req1_c03_d4_metadata_read_2026-10-07_j3.md).
La causa del NO-GO D4 fue ese falso negativo del runner. `docker wait=0` y la rama de salida
del payload confirman el mecanismo sintético; esto no atribuye el fallo histórico S1. El
contenedor sigue exited/preservado; J3 no ejecutó logs, exec, stop, cleanup ni retry.

F1 ya está preparado para el snapshot completo S1 con runner/sidecar/JIT nuevos. La
auditoría estática final encontró cero HIGH/LOW y un MEDIUM de bypass same-user documentado
como waiver NO aprobado; F1 no se ejecutará hasta aceptación explícita del residual y JIT
exacto. No reusar D4/S1 ni modificar sus evidencias/manifiestos consumidos. Si snapshot
pasa, smoke Pages/workerd actualizado queda para otro JIT.
