# JIT H3-CLOSE-03 — diagnóstico F1/F2c con resolución canónica del socket local

Estado: **paquete concreto pendiente de aprobación; no ejecutado**. No reutiliza el
permiso F2b, que se consumió en una ejecución NO-GO antes de contactar el daemon. La
aprobación anterior de los residuales MEDIUM fue exclusiva de F2b; este paquete solicita
aceptación nueva para una sola ejecución.

## Objetivo y gate

Resolver la ruta del endpoint Unix del contexto Docker seleccionado a su destino canónico,
demostrar que ese socket tiene como único listener un `dockerd` local y, solo si ambos gates
pasan, comparar la metadata allowlisted del contenedor F1 exacto. Esto busca registrar los
nombres de controles discrepantes que faltaron en F1. No permite atribuir la causa de F1 si
la inspección no llega a ejecutarse.

Gates condicionados:

1. Candidato, rama, HEAD, runner, sidecar, manifiesto de inputs y hashes históricos coinciden.
2. El contexto seleccionado referencia un endpoint `unix://` local existente. `realpath`
   resuelve el endpoint; `stat` de la ruta seleccionada y la canónica coincide; el destino
   es un socket. Los symlinks de componentes padres se resuelven y no se registra el path.
3. `/proc` identifica un único listener para la ruta canónica o el alias seleccionado,
   previamente comprobados como el mismo socket, propiedad de un proceso
   `dockerd` local cuyo ejecutable es root-owned, ejecutable y no escribible por grupo/otros;
   la lectura de descriptores tiene visibilidad completa y el PID namespace coincide con el
   host.
4. Si cualquier gate previo falla, no se realiza una petición API al daemon. Si pasan, se
   resuelve el ID de la imagen local ya fijada sin pull y se ejecuta una inspección allowlisted
   del ID F1 exacto. Luego termina la invocación.

La canonización corrige el gate que hizo fallar F2b. Ese resultado no demuestra que el path
rechazado fuese un symlink, que hubiese un proxy ni que el listener fuese otro engine: la
ruta se descartó y no se observó `/proc`.

## Candidato, recursos e inputs fijados

- Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Único contenedor permitido: ID
  `54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9`, nombre
  `h3req1-c03-source-snapshot-f1-20261007`, nonce `552890-0-28538`.
- Única imagen: `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`.
- Reporte nuevo, inicialmente ausente:
  `.context/evidencia/h3req1_c03_f1_daemon_diagnostic_f2c_2026-10-08.md`.
- Hashes de paquete:

| Input | SHA-256 |
|---|---|
| Runner F2c | `5f2b5eb429318538ea30d32834895148dc48aea189465923cb7b8ddcb26d4923` |
| Sidecar F2c | `ec10e73952405a2b53d83076b400721e919c3fd634f6fe4e4286909e4bc43971` |
| Manifiesto F2c | `3aba8447c7015cc342551fe5f3b56ff205b9df3be139fd2ce7e3ed6a30c6ffbf` |
| Helper de identidad F2c | `093b4cdbd4fc197949bd4442826a6e97f185cc1695cfb36f0d5e412dcf81addc` |
| Proyección estructurada | `f75222f388b7a0e2fa3a87c6e051fc6473f027e1edadd663530f401d627757aa` |
| Regresiones de parser | `8a98a8d2c50e330e28c1694e8893aa67575a9915f9a2cf8954b53e38a73b036c` |
| Resultado F2b preservado | `e59f5f94bec2fb8ed7911f9fab9a6eb29a9fbde6c61ef1c127f29da9b7bae247` |

El manifiesto F2c fija estos artefactos y la evidencia F1/F2a/F2b con SHA-256. El JIT tiene
su SHA-256 independiente, que se confirma junto a esta solicitud; el runner imprime el hash
que leyó del JIT y compara sus propios hashes, sidecar y manifiesto antes de cualquier
lectura de contexto.

## Operación exacta

Tras aprobar este JIT y aceptar expresamente los dos residuales MEDIUM de abajo, se permite
una sola invocación desde el candidato:

```bash
cd /home/romel/src/studiamatch-h3req1-sync-20261002
/usr/bin/env -i \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="${HOME:?HOME debe seleccionar el contexto local autorizado}" LANG=C LC_ALL=C \
  /usr/bin/timeout --foreground --signal=TERM --kill-after=10s 120s \
  /bin/bash tests/h3req1_c03_f1_diagnostic_f2c.sh \
    --jit H3-CLOSE-03-F1-DAEMON-METADATA-DIAGNOSTIC-2026-10-08-F2C \
    --runner-sha256 5f2b5eb429318538ea30d32834895148dc48aea189465923cb7b8ddcb26d4923 \
    --sidecar-sha256 ec10e73952405a2b53d83076b400721e919c3fd634f6fe4e4286909e4bc43971 \
    --manifest-sha256 3aba8447c7015cc342551fe5f3b56ff205b9df3be139fd2ce7e3ed6a30c6ffbf
```

`docker context show` and `docker context inspect --format` read the selected context; they
do not send a request to its endpoint. Before any daemon API call, the runner requires local
Unix scheme, resolves the path with `realpath -e`, and compares followed `stat` identity for
the selected and canonical paths. The helper accepts only those two equivalent paths when
matching `/proc/net/unix`, since the kernel may retain the bind spelling. The
Docker CLI is then pinned to that canonical local socket, and peer identity is rechecked
before each API call. No socket is mounted into a container.

## Límites, egress, fallos y recuperación

- Tiempo total 120 s; context ≤5 s por lectura, `realpath`/`stat` ≤2 s por operación,
  `/proc` ≤10 s, cada lectura del daemon ≤10 s. Cero retries.
- `/proc` solo lee tabla Unix, descriptores, `comm`, `exe`, `status`, PID namespace y tiempo
  de inicio. No lee `cmdline`, `environ`, memoria ni configuración del daemon.
- Operaciones permitidas: mostrar e inspeccionar configuración local del contexto; resolver y
  verificar el socket; demostrar el proceso listener; una lectura del ID inmutable de la
  imagen local fijada; una lectura Docker inspect `--format` del contenedor F1 exacto.
- Proyección allowlisted: 27 campos con comparación estructurada; tmpfs desde
  `HostConfig.Tmpfs`; `.Mounts` y `HostConfig.Mounts` para mounts persistentes; `.Image`
  comparado al ID de imagen local. Captura: máximo 8 KiB para contenedor y 128 bytes para el
  ID de imagen. Reporte privado escribe solo estado, nombres de controles discrepantes,
  contadores y metadatos de hashes; no almacena el path del socket ni valores inspect.
- Egress: ninguno. Si el contexto no es Unix local o no se demuestra `dockerd`, no se contacta
  endpoint alguno. No se cambia contexto, no se prueba otro socket y no se descarga imagen.
- Sin `create`, `start`, `wait`, `stop`, `rm`, logs, exec, pull, filesystem, cleanup, SQL/DB,
  Auth/Supabase, npm/workerd/Pages, cambios de configuración, push/PR/merge/deploy.
- Si hay timeout, input/hash diferente, ruta inválida, lectura incompleta, proxy/peer
  desconocido, salida excesiva o parser inválido, se registra NO-GO sanitizado y el permiso
  queda consumido. No se repite F2c. Se preservan el reporte y F1. Si no se demuestra el
  peer, la alternativa de iniciar un `dockerd` desechable requiere un JIT nuevo y un plan
  separado de recursos/data-root, imagen local o bootstrap, egress, límites y cleanup; no hay
  fallback implícito en este paquete.

## Waivers que requieren aceptación expresa para F2c

1. **MEDIUM — procesamiento transitorio del objeto inspect completo por Docker CLI.** Docker
   CLI recibe el objeto antes de aplicar el formato Go; la proyección limita lo que procesa y
   conserva este runner, pero no lo que el cliente recibió. Mitigación: un ID fijado, un solo
   recurso, formato allowlisted, cap 8 KiB, stderr descartado y no persistir valores. Owner:
   Romel. Riesgo residual: metadata no seleccionada vive brevemente en memoria del cliente.
   Vence tras esta invocación o cancelación.
2. **MEDIUM — bypass same-user del gate procedimental local.** El usuario local que controla
   el runner también puede invocar Docker CLI directamente. Mitigación: hashes fijados, un
   recurso, runner fail-closed y aprobación nueva; el procedimiento no es una frontera
   contra el dueño del proceso. Owner: Romel. Riesgo residual: una invocación manual puede
   salir del alcance. Vence tras esta invocación o cancelación.

La aprobación debe autorizar una invocación con este JIT exacto y aceptar ambos residuales.
No hay otros waivers solicitados.
