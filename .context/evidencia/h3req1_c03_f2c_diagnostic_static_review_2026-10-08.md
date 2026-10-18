# Revisión estática F2c — daemon local y metadata de F1

Fecha: 2026-10-08. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Resultado

F2c fue aprobado para una invocación con aceptación expresa de ambos residuales MEDIUM y
quedó consumido. Terminó **NO-GO**, exit 1 en `daemon-identity-proof`: el reporte confirmó
socket Unix local y ruta canónica, pero el helper no probó identidad de peer. El runner
descartó stdout/stderr del helper al fallar, así que no se conserva submotivo; no se infiere
proxy ni proceso concreto. No hubo Docker API, lectura de imagen ni inspect de F1. El
reporte F2c permanece íntegro y F1 sigue sin discrepancia identificada.

## Corrección revisada

- F2b sigue intacto para que su SHA siga identificando la única ejecución consumida.
- F2c resuelve el endpoint Unix con `realpath -e`, comprueba que la ruta elegida y la
  canónica reporten el mismo objeto socket con `stat -L`, y fija el CLI a la ruta canónica.
- El helper F2c solo acepta la ruta canónica y la ruta seleccionada ya comparadas como el
  mismo socket. Busca una única entrada listener en `/proc/net/unix`, mapea su inode a FD
  de proceso, exige visibilidad completa, proceso `dockerd`, PID namespace local y binario
  root-owned no escribible por grupo/otros. No registra ningún path.
- Falla antes de daemon API si el endpoint no es Unix local, el socket cambia, la visibilidad
  de `/proc` es incompleta o la identidad del listener no se prueba. Tras el peer proof
  revalida socket/PID antes de una lectura local del ID de imagen fijada y un inspect
  allowlisted del ID F1 exacto.
- La proyección compara campos estructurados; tmpfs se toma de `HostConfig.Tmpfs`, mounts
  persistentes de `HostConfig.Mounts`/`.Mounts` y `.Image` del ID inmutable local. Reporta
  nombres de controles discrepantes, no sus valores.
- Los dos residuales MEDIUM fueron aceptados específicamente para F2c; no se heredan a
  otras invocaciones.

## Límites de esta revisión

- El gate F2b permite afirmar que su path seleccionado no igualó su forma canónica; el valor
  fue descartado. No permite afirmar symlink, proxy, daemon distinto ni causa F1.
- `bash -n` pasó para runner F2b/F2c, helper de proyección y regresiones shell; `sh -n` pasó
  para scanner canónico y regresiones. `sha256sum --check` pasó para sidecar/manifiesto F2c.
  Son comprobaciones estáticas, no pruebas del parser ni identidad runtime.
- `git diff --check` pasó para cambios rastreados en el corte anterior; no valida untracked
  ni sustituye la revisión del diff final.
- F2c no generó PASS runtime. Faltan ejecución del parser con formatos observados/negativos,
  pruebas del scanner y `actionlint`/`shellcheck` dentro del Docker H3 aprobado.

## Pins del paquete presentado

| Artefacto | SHA-256 |
|---|---|
| JIT F2c | `1046650f911fd91181ea79ef10bd630b065e98ab182b04ebf500a2c79cad45e7` |
| Runner F2c | `5f2b5eb429318538ea30d32834895148dc48aea189465923cb7b8ddcb26d4923` |
| Sidecar F2c | `ec10e73952405a2b53d83076b400721e919c3fd634f6fe4e4286909e4bc43971` |
| Manifiesto F2c | `3aba8447c7015cc342551fe5f3b56ff205b9df3be139fd2ce7e3ed6a30c6ffbf` |
| Helper de identidad F2c | `093b4cdbd4fc197949bd4442826a6e97f185cc1695cfb36f0d5e412dcf81addc` |
| Proyección/verificador | `f75222f388b7a0e2fa3a87c6e051fc6473f027e1edadd663530f401d627757aa` |
| Regresiones de proyección | `8a98a8d2c50e330e28c1694e8893aa67575a9915f9a2cf8954b53e38a73b036c` |

El diagnóstico siguiente está en [F2d](../operaciones/manifiesto_jit_h3_close03_f1_diagnostic_f2d_2026-10-08.md):
usa `SO_PEERCRED` para identificar el peer directo y requiere aprobación nueva. F2c no se
repite.

Fuente de estado: [resultado F2b](h3req1_c03_f1_daemon_diagnostic_f2b_2026-10-08.md),
[JIT F2c](../operaciones/manifiesto_jit_h3_close03_f1_diagnostic_f2c_2026-10-08.md) y
[estado vivo](../estado_del_proyecto.md). No constituye aprobación ni autoriza la ejecución.
