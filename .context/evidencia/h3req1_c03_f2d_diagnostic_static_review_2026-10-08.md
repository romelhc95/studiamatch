# Revisión estática F2d — peer SO_PEERCRED y metadata de F1

Fecha: 2026-10-08. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Resultado

F2c fue consumido con aprobación expresa y terminó NO-GO antes de Docker API. Verificó un
socket Unix local canónico, pero el reporte conserva solo `daemon-identity-not-proven`; no
permite distinguir `/proc` incompleto, listener ambiguo, proxy u otro fallo del helper. No
hubo imagen ni inspect F1. La causa del rechazo pre-start F1 sigue desconocida.

F2d es la alternativa local **preparada y no ejecutada**, con JIT propio y aprobación fresca
pendiente. Usa una conexión Unix y `SO_PEERCRED` para recibir del kernel el PID/UID/GID del
peer directo; no envía bytes de aplicación. Valida el PID/executable/namespaces y socket
antes de la metadata, y conserva fallos con códigos allowlisted. Si el peer no es `dockerd`
local, no visible o cambia, termina antes de Docker API. Solo tras pasar puede leer una vez
el ID local de imagen fijada e inspeccionar una vez el ID F1 exacto.

## Revisión del paquete

- No modifica F2b/F2c ni sus reportes consumidos. F2d es un método distinto y no hereda
  permisos ni aceptación de residuales.
- Las lecturas del contexto son locales. Requiere socket Unix canónico, prueba directa del
  peer con `SO_PEERCRED`, mismo PID namespace y ejecutable `dockerd` root-owned/no escribible
  por grupo u otros. El helper no enumera los file descriptors de todos los procesos.
- Si la identidad falla, no exporta `DOCKER_HOST`; el runner registra el código sanitizado
  y cero llamadas Docker API. Si pasa, queda limitado a la imagen por digest y al contenedor
  F1 exacto; no modifica ni limpia recursos.
- El parser compartido conserva campos estructurados: tmpfs desde `HostConfig.Tmpfs`, mounts
  persistentes de `HostConfig.Mounts`/`.Mounts` e imagen por ID local inmutable. Solo emite
  nombres de controles discrepantes.
- Requiere aceptación expresa nueva de MEDIUM por objeto inspect completo transitorio en
  Docker CLI y bypass procedimental del mismo usuario local.

## Validación efectuada y límites

- `bash -n tests/h3req1_c03_f1_diagnostic_f2d.sh`: PASS.
- Sidecar F2d y los 17 inputs fijados por su manifiesto: `sha256sum --check` PASS.
- `git diff --check`: PASS para paths rastreados en el corte; no cubre los archivos F2d
  untracked. No se ejecutó Python, parser regression, ShellCheck, actionlint, Docker, SQL,
  imagen ni F1. No hay PASS runtime.
- La revisión no contactó el contexto/socket. El helper Python requiere validación dentro
  del Docker H3 autorizado antes de considerar F2d listo para ejecución. El F2d JIT exige
  pins nuevos si cambia cualquier input.

## Pins presentados

| Artefacto | SHA-256 |
|---|---|
| JIT F2d | `f662d26783c9bb09d6cef2688da6bbf55e725dcc7fc77b92472ba0dc83a6c02e` |
| Runner F2d | `23f860e5582f1fefd96b2ccc4cf1b70e782e0d1a70ab72b630115fdf36c7964c` |
| Sidecar F2d | `5dab2330f306941d3d058ee88c3399501db06045c8573257f6e9829c122cbc27` |
| Manifiesto de inputs F2d | `0335b2e16c2363c81faf536d0f21499356ea1cfd070bd463f1a8b7090a715a31` |
| Helper SO_PEERCRED | `f117a1c4d6f769d161c1401daa78de166746729ad84a2e1431ca26967aa5612d` |
| Proyección compartida | `f75222f388b7a0e2fa3a87c6e051fc6473f027e1edadd663530f401d627757aa` |
