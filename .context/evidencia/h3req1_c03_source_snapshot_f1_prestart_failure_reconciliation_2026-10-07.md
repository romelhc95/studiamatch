# Reconciliación del NO-GO pre-start F1 — H3REQ1

Fecha: 2026-10-07. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## JIT y ejecución consumidos

- JIT F1 aprobado/consumido una sola vez, SHA-256
  `e4a651f47322cec8a9d7551a93b40186d2c25089215aa1b7b8c87a4263c2547f`.
- Waiver del bypass same-user fue aceptado dentro de esa aprobación. Esa aceptación no
  amplía alcance ni permite reusar el JIT.
- Runner `3249cdfed8043dfd751074ec0d844d6a9a88f14328b144f10d93c41cbbb446e0`, sidecar
  `23d676776ce7fb95001576315d39913425756ea388809eed199dab4c0260af40`, source manifest
  `ae335c8e197d2c380bc877abbd53aa9f52a30f2b00e3310865bccb64ecb17c5d`. Branch/HEAD y pins
  se comprobaron antes de ejecutar.
- Se ejecutó una sola vez el launcher exacto del JIT. Evidencia del runner, preservada sin
  editar: [reporte F1](h3req1_c03_source_snapshot_2026-10-07_f1.md), SHA-256
  `c28338c811b305428126ea7bea9fa5d4f9f9e3cfd09e8a26aeb370f032a41913`.

## Resultado factual

- El Docker local informó contexto Unix local verificado.
- El único `docker create` terminó status 0 para
  `h3req1-c03-source-snapshot-f1-20261007`, ID
  `54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9`, nonce
  `552890-0-28538`.
- La validación de identidad/controles pre-start respondió NO-GO. El reporte no conserva el
  nombre del campo discrepante; no se infiere cuál fue.
- El runner no llamó a `docker start`; por diseño, la fase de extracción `tar`, la comparación
  de ownership y cualquier inspección final no ocurrieron. El runner registró
  `bounded-stop=not-needed|reason=container-never-started`; no hubo stop/remove/cleanup,
  logs/exec, retry ni segundo Docker command.
- El recurso creado se preserva. La última evidencia de lifecycle viene de la secuencia
  aprobada `create` exit 0 y de que el runner no ejecutó `start`; no hubo una consulta
  posterior independiente del estado. No volver a consultarlo bajo F1.

F1 es NO-GO, no PASS del snapshot. No demuestra causa de S1 ni ownership histórico.
El JIT está consumido aunque el contenedor no haya arrancado.

## Siguiente gate

F2 propone una única lectura read-only allowlisted de metadata del ID exacto para determinar
qué campo pre-start discrepó. No autoriza logs, `.State.Error`, Env/command, filesystem,
start, stop, remove, retry ni consulta por nombre. Su JIT es nuevo, propuesto y requiere
aprobación independiente. Ningún Docker posterior está autorizado por esta evidencia.

Snapshot completo, smoke Pages/workerd, C03 integrado, `GO_LOCAL_PR` y
`GO_DEVELOPMENT_REAL` permanecen NO-GO.
