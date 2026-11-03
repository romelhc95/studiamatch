# JIT H3-CLOSE-03 — peer directo SO_PEERCRED para F1/F2d

Estado: **revisión r2 preparada tras PASS de helper en Docker; requiere aprobación fresca; no ejecutar todavía**.
F2b y F2c están consumidos. Esta propuesta cambia el método de identidad; no repite esas
invocaciones ni hereda sus aprobaciones. La revisión anterior de este JIT se preserva en
[la versión previa](manifiesto_jit_h3_close03_f1_diagnostic_f2d_2026-10-08_v1_pre_r4.md).

## Objetivo y gate

Intentar identificar el peer real del socket Docker Unix local con las credenciales que el
kernel entrega mediante `SO_PEERCRED`. Si el peer directo resulta ser el proceso local
`dockerd` y los checks de PID/executable/socket permanecen estables, obtener solo la
metadata allowlisted del contenedor F1 exacto y registrar los nombres de controles que
discrepan. El reporte F2c solo conserva `daemon-identity-not-proven`; no expone el submotivo
interno. F2d registra códigos de fallo del helper acotados, sin recuperar datos descartados.

F2c sí acreditó endpoint Unix local, socket existente y ruta canónica, pero no probó la
identidad del listener. El helper F2c dependía de enumerar `/proc/net/unix` y descriptores
de todos los procesos. F2d toma como alternativa `SO_PEERCRED` en una conexión Unix local
sin enviar bytes de aplicación, y valida el PID recibido contra `/proc/<pid>` y el socket.
Si el peer es proxy, socket-activation manager, proceso no visible, cambiante o distinto de
`dockerd`, el resultado queda NO-GO y **no se emite ninguna petición Docker API**.

## Candidato, recurso e inputs fijados

- Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Único contenedor permitido: ID
  `54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9`, nombre
  `h3req1-c03-source-snapshot-f1-20261007`, nonce `552890-0-28538`.
- Única imagen permitida: `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`.
- Reporte nuevo, inicialmente ausente:
  `.context/evidencia/h3req1_c03_f1_daemon_diagnostic_f2d_2026-10-08.md`.
- Pins del paquete:

| Input | SHA-256 |
|---|---|
| Runner F2d | `23f860e5582f1fefd96b2ccc4cf1b70e782e0d1a70ab72b630115fdf36c7964c` |
| Sidecar F2d | `5dab2330f306941d3d058ee88c3399501db06045c8573257f6e9829c122cbc27` |
| Manifiesto de inputs F2d, 17/17 vigentes | `18101dd492dd894d5c5692c204f1a47d3727fb609f75b83ffdbc854bcf0f657a` |
| Helper `SO_PEERCRED` F2d | `c0b3820d920015325b2d91ed8e50215f3a1ba967d79a1d3abda62c702b460ac0` |
| Proyección estructurada | `f75222f388b7a0e2fa3a87c6e051fc6473f027e1edadd663530f401d627757aa` |
| Resultado F2c | `070f01a76b585312a6e43b5b8608c786adf51bde7c77298d85011c034133e7ff` |
| Resultado F2b | `e59f5f94bec2fb8ed7911f9fab9a6eb29a9fbde6c61ef1c127f29da9b7bae247` |

El manifiesto de inputs fija además F1, sus approvals, runner/source manifest y los
resultados F2b/F2c. El SHA del propio JIT se comprueba antes de invocar y se registra en el
reporte; no se inserta dentro del JIT para evitar autociclo.

La prueba sintética del helper F2d se ejecutó dentro del Docker aislado r4 y estuvo entre
los 20 tests PASS. El manifiesto F2d anterior fallaba 1/17 porque mantenía el pin del helper
previo; los 17 pins renovados ahora coinciden. Ese PASS de fixture no prueba identidad del
daemon real ni permite leer F1.

## Operación exacta

Antes de invocar el runner, leer el SHA del manifiesto con este comando y compararlo con el
SHA incluido en la solicitud/aprobación humana. Si no coincide exactamente, detenerse sin
consultar Docker:

```bash
sha256sum -- .context/operaciones/manifiesto_jit_h3_close03_f1_diagnostic_f2d_2026-10-08.md
```

Solo después de aprobación expresa de este JIT y de los dos residuales MEDIUM, se permite
una invocación desde el candidato:

```bash
cd /home/romel/src/studiamatch-h3req1-sync-20261002
/usr/bin/env -i \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="${HOME:?HOME debe seleccionar el contexto local autorizado}" LANG=C LC_ALL=C \
  /usr/bin/timeout --foreground --signal=TERM --kill-after=10s 120s \
  /bin/bash tests/h3req1_c03_f1_diagnostic_f2d.sh \
    --jit H3-CLOSE-03-F1-DAEMON-METADATA-DIAGNOSTIC-2026-10-08-F2D \
    --runner-sha256 23f860e5582f1fefd96b2ccc4cf1b70e782e0d1a70ab72b630115fdf36c7964c \
    --sidecar-sha256 5dab2330f306941d3d058ee88c3399501db06045c8573257f6e9829c122cbc27 \
    --inputs-sha256 18101dd492dd894d5c5692c204f1a47d3727fb609f75b83ffdbc854bcf0f657a
```

## Reconciliación explícita con `AGENTS.md`

`AGENTS.md` exige que las pruebas y comandos de desarrollo de producto se ejecuten en
Docker, y prohíbe ejecutarlos en el host Windows. El helper Python F2d no es una prueba de
producto ni instala dependencias: es un diagnóstico de identidad del daemon Linux del
host. Debe conectarse directamente al socket Unix real y leer solo `/proc/<pid>` del peer
que el kernel entrega mediante `SO_PEERCRED`, dentro del mismo namespace PID. Ejecutarlo
en un contenedor sin socket no probaría el daemon; montarle el socket y `/proc` del host
ampliaría exposición y alcance. Por eso la operación exacta requiere correr el auxiliar
`/usr/bin/python3` en el host Linux, después de que sus fixtures sintéticos ya pasaron en
Docker r4. El runner no instala paquetes ni ejecuta suites de producto en el host. Esta
excepción estrecha requiere aprobación explícita del usuario junto con este JIT; si no se
aprueba, no se ejecutará el auxiliar ni se llamará Docker API.

## Alcance y límites

- Local reads: branch/HEAD, hashes, Docker `context show` y `context inspect --format` del
  contexto elegido, `realpath`, `stat`, y metadata de proceso de un peer identificado por
  el kernel. El context debe ser un socket Unix local canónico. La ruta no se conserva.
- Identidad: máximo tres conexiones Unix locales usando `SO_PEERCRED`; el helper no envía
  petición HTTP ni bytes de aplicación. Lee únicamente `/proc/<pid>/stat`, `comm`, `exe`,
  `status` y `ns/pid`, y vuelve a validar el socket. Exige PID de peer estable, proceso y
  ejecutable `dockerd`, namespace PID local y ejecutable root-owned, ejecutable y no
  escribible por grupo/otros.
- Si no pasa la prueba directa de peer, no se exporta endpoint para Docker CLI y se hacen
  cero llamadas Docker API. Si pasa: una lectura `docker image inspect` del digest fijado,
  sin pull; después una inspección `docker inspect --type container` del ID F1 exacto.
- Proyección: 27 campos allowlisted, stdout ≤128 bytes para ID de imagen y ≤8192 bytes para
  F1; `.Image` compara contra el ID inmutable de la imagen local; tmpfs compara
  `HostConfig.Tmpfs[/snapshot]`; mounts persistentes comparan `HostConfig.Mounts`/`.Mounts`.
  Reporta nombres de controles discrepantes, no valores de metadata. `stderr` y respuesta
  inspect no proyectada se descartan.
- Recursos: ningún container/network/volume nuevo; F1 y otros recursos se preservan. No
  `create`, `start`, `wait`, `stop`, `rm`, logs, exec, pull, archivos de contenedor, SQL/DB,
  Auth/Supabase, npm/workerd/Pages, cambios de configuración, push/PR/merge/deploy.
- Egress: ninguno. No se contacta un endpoint TCP/remoto. Si el contexto seleccionado no es
  Unix local o el peer no se prueba, el flujo se detiene antes de Docker API.
- Límites: 120 s totales; context reads ≤5 s, `realpath`/`stat` ≤2 s, cada peer proof ≤5 s,
  cada Docker API read ≤10 s, stdout acotado según arriba. Cero retries. El JIT se consume
  aunque haya timeout o NO-GO.
- Fallo y recuperación: registrar código sanitizado y fase; descartar metadata cruda; no
  repetir ni alterar/limpiar F1. Si el proceso peer cambia entre gates, cortar antes de la
  siguiente lectura. Un nuevo método o daemon requerirá un JIT separado. No hay stop/delete
  de recursos porque la operación no cambia su estado.

## Residuales que requieren aceptación expresa

1. **MEDIUM — procesamiento transitorio del objeto inspect completo por Docker CLI.** La
   CLI recibe el objeto antes de aplicar el formato Go. Mitigación: un ID exacto, campos
   allowlisted, límite de captura, stderr descartado y no persistir valores. Owner: Romel.
   Riesgo: metadata no seleccionada vive brevemente en memoria del cliente. Vence al terminar
   o cancelar esta invocación.
2. **MEDIUM — bypass procedimental del mismo usuario local.** Quien controla el usuario que
   corre el runner puede invocar Docker CLI fuera de este JIT. Mitigación: pins, runner
   fail-closed, peer proof y aprobación fresca. Owner: Romel. Riesgo: una invocación manual
   puede exceder el alcance. Vence al terminar o cancelar esta invocación.

La aprobación debe autorizar **una invocación** con el SHA de este JIT, aprobar el auxiliar
Python de host Linux descrito arriba y aceptar expresamente ambos residuales. La aceptación
F2c no se hereda. Ningún PASS de C02/C03 ni causa del F1 se infiere de preparar o ejecutar
este paquete.
