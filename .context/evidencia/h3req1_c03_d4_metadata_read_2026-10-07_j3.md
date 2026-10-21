# Resultado J3 — metadata allowlisted del contenedor D4

Fecha: 2026-10-07. Candidato rama `feat/h3req1-sync-20261002`, HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Permiso y lectura ejecutada

- JIT J3 aprobado/consumido una sola vez, SHA-256
  `1ce8f345b4b8c92559228d5cc6d5b46ae198d2febbef486efb1f9111a61676f1`.
- Inputs D4, evidencia, branch/HEAD y hashes se verificaron antes del launcher.
- Una sola consulta read-only `docker inspect --type container --format` al ID exacto
  `d52d606bdc809eb7bfd13c6e16c4e0a7bc29db2bf3e71e7941b75a84de868650`, con stdout capado
  a 8 KiB; salida cruda descartada. No se consultaron logs ni otro recurso.

## Salida sanitaria

```text
metadata-result=control-mismatch
mismatch-fields=mounts
container-state=exited
container-exit=0
container-oom=false
mounts-observed=none
diag-tmpfs-observed=rw,noexec,nosuid,nodev,size=16m,uid=1001,gid=1001,mode=0700
logging-observed=local|max-size=1m|max-file=1|compress=false
```

La comparación de metadata allowlisted encontró que **solo** `mounts` difería; identidad,
labels, estado/exit/OOM, red, rootfs, usuario, capabilities, seguridad, límites CPU/RAM/PIDs,
restart, tmpfs de `/diag`, logging, puertos y shm coincidieron con el JIT D4. La lista
`.Mounts` vino vacía, mientras `HostConfig.Tmpfs[/diag]` contiene exactamente las opciones
esperadas y no hay mounts persistentes. Docker no representa ese tmpfs de `/diag` en la
lista `.Mounts` consultada.

## Causa y resultado separado

La causa del NO-GO del **runner D4** es una verificación incorrecta: esperaba que el tmpfs
de `/diag` apareciera como elemento de `.Mounts`; al recibir la lista vacía, su parser
desalineó campos y rechazó la metadata, aunque `HostConfig.Tmpfs` confirmó la configuración
efectiva requerida. No hubo una discrepancia real en los demás controles inspeccionados.

`docker wait` reportó exit 0. El payload sintético solo devuelve 0 desde la rama final que
confirma productor tar=0, restauración `--same-owner` denegada por ownership,
`--no-same-owner`=0 y validaciones de paths/symlinks/permisos/hashes. Por eso el fixture
sintético confirma el mecanismo de ownership bajo sus condiciones. El runner D4 conserva
su resultado factual exit 1/NO-GO por su falso negativo; no se reescribe su evidencia ni se
declara D4 runner PASS.

Esto no prueba que ownership causara el fallo S1: el fixture es sintético y el snapshot
completo de los 13 inputs S1 no se ha ejecutado con `--no-same-owner`. No hubo logs, exec,
start, stop, cleanup, retry ni acceso a otros IDs. El contenedor D4 permanece `exited` y
preservado; los manifiestos D4/J3 consumidos permanecen intactos.

## Siguiente gate

F1 ya está preparado con runner/sidecar/JIT nuevos para los 13 inputs del source manifest
S1 más el manifiesto. Sintaxis y pins pasan; la auditoría estática final encontró cero
HIGH/LOW y un MEDIUM de bypass de autorización same-user, declarado en el JIT como waiver
NO aprobado. No hay ejecución Docker autorizada hasta que se acepte explícitamente ese
residual y se apruebe F1 bajo su hash exacto. No repetir S1/D4 ni reusar permisos. Solo tras
PASS del snapshot podrá prepararse un smoke Pages/workerd actualizado bajo otro JIT.
