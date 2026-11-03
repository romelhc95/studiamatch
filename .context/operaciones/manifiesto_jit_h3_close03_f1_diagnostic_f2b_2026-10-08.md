# JIT H3-CLOSE-03 — diagnóstico F1/F2b de daemon local e identidad pre-start

Estado: **solicitud concreta, no aprobada, no ejecutada**. Este permiso es nuevo; no
reutiliza F1, F2, F2a, D3, D4 ni J3, ni sus aprobaciones/waivers.

## Objetivo y gates

Identificar con evidencia el listener Docker seleccionado y, únicamente si se demuestra
que es el proceso `dockerd` local, leer la metadata allowlisted del contenedor F1 exacto
para registrar los nombres reales de los controles discrepantes. El resultado permite
explicar el NO-GO pre-start de F1 sin atribuirlo por analogía a D4, ownership, mounts o
imagen.

Gate condicionado:

1. Branch/HEAD, runner, sidecar, manifiesto de inputs y evidencia histórica coinciden.
2. Contexto local Unix y socket canónico coinciden; `/proc` identifica un único listener
   `dockerd` con ejecutable root-owned no escribible por grupo/otros y PID namespace local.
3. Si el gate 2 falla, **no se invoca ninguna API Docker**. Se registra NO-GO y F1 queda
   intacto.
4. Tras gate 2, se resuelve el ID de la imagen ya presente localmente, sin pull.
5. Se hace una sola llamada `docker inspect --type container --format` al ID F1 exacto y se
   comparan los campos estructurados. La ejecución termina tras esa lectura.

## Candidato, recursos e inputs fijados

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD esperados: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Único contenedor: `54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9`, nombre
  `h3req1-c03-source-snapshot-f1-20261007`, nonce `552890-0-28538`, labels vinculados al
  JIT F1 y al sidecar indicado abajo.
- Única imagen consultable: `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`.
- Reporte nuevo, inicialmente ausente: `.context/evidencia/h3req1_c03_f1_daemon_diagnostic_f2b_2026-10-08.md`.

| Input | SHA-256 |
|---|---|
| JIT F1 consumido | `e4a651f47322cec8a9d7551a93b40186d2c25089215aa1b7b8c87a4263c2547f` |
| Runner F1 preservado | `3249cdfed8043dfd751074ec0d844d6a9a88f14328b144f10d93c41cbbb446e0` |
| Sidecar F1 | `23d676776ce7fb95001576315d39913425756ea388809eed199dab4c0260af40` |
| Source manifest S1 | `ae335c8e197d2c380bc877abbd53aa9f52a30f2b00e3310865bccb64ecb17c5d` |
| Evidencia F1 preservada | `c28338c811b305428126ea7bea9fa5d4f9f9e3cfd09e8a26aeb370f032a41913` |
| Atestación F1 preservada | `9f0027bb3b6ec85347349f3dace69952719d2931f10de5b47f76e753828e9626` |
| Propuesta F2a, solo referencia | `9bc0fa74d7ad3c3f468c9e49f817c2e28aff4d2e753b6e6ca77ff16f5ccf072e` |
| Verificador local del peer | `0aed7908eee2bab5e11e8574bebe3f677c058fd54c1e9ba523474bea3bd5bd1e` |
| Proyección/verificador estructurado | `f75222f388b7a0e2fa3a87c6e051fc6473f027e1edadd663530f401d627757aa` |
| Regresiones del parser | `8a98a8d2c50e330e28c1694e8893aa67575a9915f9a2cf8954b53e38a73b036c` |
| Runner F2b | `69ce78f0e597f069f5ffcc5138af18dc0718ad1aa7824628519a3ed343210379` |
| Sidecar F2b | `10e5a797a1a06c86b364eb8f4d8c53034d2477142fc517e3812106aaa997a939` |
| Manifiesto de inputs F2b | `4d2a20555d8d5a861f8fdc19512553bcd391832cf1340b4bf85ee1cfb15a4cdd` |

El SHA-256 de este JIT se comunica junto con la solicitud de aprobación; el runner y sus
dependencias se fijan con los hashes anteriores y se exigen como argumentos exactos.

## Operación exacta

Después de la aprobación humana de este JIT y de los dos residuales detallados abajo, una
sola invocación desde el candidato:

```bash
cd /home/romel/src/studiamatch-h3req1-sync-20261002
/usr/bin/env -i \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="${HOME:?HOME debe seleccionar el contexto local autorizado}" LANG=C LC_ALL=C \
  /usr/bin/timeout --foreground --signal=TERM --kill-after=10s 120s \
  /bin/bash tests/h3req1_c03_f1_diagnostic_f2b.sh \
    --jit H3-CLOSE-03-F1-DAEMON-METADATA-DIAGNOSTIC-2026-10-08-F2B \
    --runner-sha256 69ce78f0e597f069f5ffcc5138af18dc0718ad1aa7824628519a3ed343210379 \
    --sidecar-sha256 10e5a797a1a06c86b364eb8f4d8c53034d2477142fc517e3812106aaa997a939 \
    --manifest-sha256 4d2a20555d8d5a861f8fdc19512553bcd391832cf1340b4bf85ee1cfb15a4cdd
```

El lector local `/proc` corre en el host que posee el socket: ejecutarlo dentro de
`studiamatch-dev` observaría otro namespace. No se monta el socket en ningún contenedor.
Contexto y endpoint se leen sin petición al daemon. El runner rechaza overrides de Docker,
endpoint no Unix, symlinks y socket no canónico. Luego compara el listener del socket en
`/proc/net/unix` con todos los `/proc/<pid>/fd`; exige visibilidad completa, un único PID,
`comm= dockerd`, ejecutable `dockerd` root-owned, no escribible por grupo/otros y PID
namespace local. Repite la comprobación antes de cada llamada Docker, fijando el socket
canónico y el mismo PID/inode.

Si el peer no se demuestra, el runner registra NO-GO antes de `docker image inspect` o
`docker inspect`; no prueba otro contexto, host ni daemon. La alternativa local requiere
otro JIT: iniciar un daemon desechable directo con `dockerd` ya instalado, socket y data-root
propios, bridge/iptables/ip-masq desactivados, sin instalar ni reconfigurar el engine
existente; cargar la imagen fijada desde una fuente local verificada o pedir un bootstrap
de descarga separado y acotado. Ese paquete deberá fijar binario, imagen/sha256, paths,
recursos, egress, tiempos y limpieza exacta antes de ejecutar.

## Límites de ejecución y datos

- Tiempo global 120 s, TERM y 10 s de gracia; configuración Docker ≤5 s, stat/realpath ≤2 s,
  lectura `/proc` ≤10 s y cada llamada al daemon ≤10 s. Cero retries.
- `/proc` solo lee tabla Unix, descriptores, `comm`, `exe`, `status`, PID namespace y tiempo
  de inicio. No lee `cmdline`, `environ`, memoria del proceso ni configuración del daemon.
- API permitida, solo tras demostrar el listener: una lectura
  `docker image inspect --format '{{json .Id}}'` de la imagen digest fijada y una lectura
  `docker inspect --type container --format` del ID F1 exacto. La primera no descarga.
- La proyección contiene únicamente identidad, estado/exit/OOM, tres labels F1, red, rootfs,
  usuario, capabilities, security options, límites, restart, `HostConfig.Tmpfs`, logging,
  puertos, shm, Binds, `HostConfig.Mounts`, `.Mounts` e `.Image`. Cap 8 KiB para contenedor y
  128 bytes para ID de imagen. El reporte escribe solo nombres de campos discrepantes, nunca
  valores inspeccionados, Env, comando, credenciales, `.State.Error`, paths de mounts o
  objeto Docker completo. Stderr Docker/Python se descarta.
- Egress: ninguno. El único transporte de API, si se supera el gate, es el socket Unix local
  atribuido a `dockerd`; ningún TCP/SSH/TLS/context remoto ni registry.
- Sin `create`, `start`, `wait`, `stop`, `rm`, logs, exec, filesystem, limpieza, SQL/DB,
  Auth/Supabase, npm/workerd/Pages, cambios de configuración, push/PR/merge/deploy.
- El reporte privado se crea con `umask 077` y `noclobber`. Cualquier error, timeout,
  discrepancia de branch/HEAD/hash, lectura incompleta de `/proc`, peer proxy/desconocido,
  salida excesiva o error de parser produce NO-GO y consume el permiso. No se reintenta ni se
  altera F1. La evidencia fallida se conserva; recuperación: inspección del reporte y nuevo
  JIT antes de cualquier acción.

## Waivers que requieren aceptación expresa dentro de esta aprobación

1. **MEDIUM — procesamiento transitorio del objeto inspect completo por Docker CLI.** Causa
   reproducible: `docker inspect` recibe el objeto de respuesta antes de aplicar el formato
   Go; la proyección restringe lo que el runner procesa/persiste pero no lo que el cliente
   Docker recibió. Mitigación: una llamada al ID literal, proyección allowlisted, cap 8 KiB,
   stderr descartado, valores nunca impresos ni persistidos. Owner: Romel. Riesgo residual:
   metadata no seleccionada puede estar brevemente en memoria del cliente Docker. Vence tras
   esta única invocación o cancelación.
2. **MEDIUM — bypass same-user del gate procedimental local.** Causa reproducible: el mismo
   usuario que controla el runner posee acceso local al engine/contexto y puede invocar el
   CLI directamente. Mitigación: hashes fijados, un único recurso, runner fail-closed y
   aprobación nueva; esto no es una frontera contra el dueño del proceso. Owner: Romel.
   Riesgo residual: una invocación manual por el mismo usuario puede salir del alcance. Vence
   tras esta única invocación o cancelación.

La aprobación debe aceptar ambos residuales enumerados y autorizar una sola invocación con
este JIT exacto. No hay otros waivers solicitados.
