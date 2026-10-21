# Solicitud JIT F1 — validación completa del snapshot de fuente S1

Estado: **propuesto, NO aprobado, NO ejecutado**. S1/D2/D3/D4/J1/J2/J3 están consumidos;
F1 usa runner, recurso y permiso nuevos, y no los repite.

## Propósito

Validar únicamente el snapshot completo del source manifest S1 (13 archivos fijados más
el propio manifiesto), usando el correctivo comprobado en fixture sintético:
`tar --no-same-owner`. No inicia npm, Pages, workerd ni runtime. Un F1 PASS solo acredita
la transferencia/extracción/hash de esos archivos en el contenedor nuevo; no es smoke ni
C03 integrado y no prueba retrospectivamente la causa S1.

## Inputs fijados

| Input | SHA-256 | Uso |
|---|---|---|
| Runner `tests/h3req1_c03_source_snapshot_f1.sh` | `3249cdfed8043dfd751074ec0d844d6a9a88f14328b144f10d93c41cbbb446e0` | Ejecuta únicamente la validación de snapshot |
| Sidecar `tests/h3req1-c03-source-snapshot-f1.sha256` | `23d676776ce7fb95001576315d39913425756ea388809eed199dab4c0260af40` | Fija el runner |
| Source manifest `tests/h3req1-c03-startup-source-s1.sha256` | `ae335c8e197d2c380bc877abbd53aa9f52a30f2b00e3310865bccb64ecb17c5d` | 13 inputs; se incluye también como 14.º archivo del snapshot |

Rama `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
Imagen exclusivamente local, sin pull: `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`, `linux/amd64`.

## Operaciones autorizables

- Checks locales de branch/HEAD, hashes, source manifest 13/13 y paths allowlisted.
- Docker context show/inspect solo para exigir endpoint Unix local; `stat`/`realpath` para
  identidad del socket. `docker image inspect` solo sobre la imagen fijada, sin pull, para
  rechazar imágenes que declaren volúmenes.
- Una única operación `docker create --cidfile` para el contenedor nuevo
  `h3req1-c03-source-snapshot-f1-20261007`, sin iniciar proceso. ID leído desde un máximo
  de 66 bytes. Una inspección completa pre-start valida ID/nombre/labels/nonce y todos los
  controles; si algo difiere, el contenedor permanece `created` y nunca arranca.
- Solo tras PASS pre-start, una única `docker start --attach --interactive` sobre el ID
  literal verificado, que recibe por stdin un tar de los 14 paths fijados. El receptor extrae
  con `tar --no-same-owner`, valida set exacto, no-symlinks, SHA del manifiesto y 13/13.
- Una inspección completa final del mismo ID valida estado `exited`, exit 0 y los controles.
  `/snapshot` se valida por `HostConfig.Tmpfs`, nunca esperando que figure en `.Mounts`.
- Ante señal/fallo antes de verificar identidad, no se para nada y el contenedor permanece
  solo `created`: el runner nunca lo inicia antes de que ID/nombre/labels/nonce/red/controles
  pasen la inspección pre-start.
- Después de PASS pre-start y desde que comienza el único `start`, se permite como máximo
  una llamada `docker stop --time 5` al mismo ID literal pre-verificado para contener un
  fallo/señal. No se hace una consulta adicional para decidir el stop; está limitado al ID
  propio. Si el daemon no responde, se registra fallo y el recurso queda preservado.
- Se preservan contenedor, cidfile y reporte; no hay `rm`/remove, retry, logs, exec, start
  adicional ni consulta por nombre. Si el daemon no responde al stop, el proceso puede
  continuar; se registra el fallo y no se reintenta.

Controles: `--network none`, `--pull=never`, sin puertos ni binds/volúmenes, rootfs read-only,
UID/GID 1001:1001, `--cap-drop=ALL`, `no-new-privileges`, 0.5 CPU, 128 MiB RAM/swap,
64 PIDs, `/dev/shm` 16 MiB, `/snapshot` tmpfs 96 MiB `noexec,nosuid,nodev`, restart
deshabilitado y `log-driver none`. Se preserva el recurso al finalizar.

El reporte de contenedor está allowlisted a una sola línea fija; tar/inspect/errors raw no se
imprimen. El stdout del `inspect` se limita a 8 KiB; CID se lee mediante un stream de máximo
66 bytes. Inputs locales:
source manifest máximo 16 KiB; cada source file máximo 4 MiB y conjunto máximo 8 MiB;
paths máximos 100 bytes; stream tar truncado/fallido sobre 16 MiB+1; checksum máximo 20 s.
Runner/sidecar se limitan a 256 KiB/512 bytes antes de hash/captura; base64 en el launcher
usa timeout 5 s y cota de salida. Toda operación local individual tiene timeout ≤5 s más
1 s de kill grace (checksum ≤20 s más 1 s); presupuesto de trabajo del runner 180 s más 10 s
reservados para stop, tar y `docker start` máximo 60 s, `docker create` 15 s, cada inspect
15 s, stop 5 s (cada uno con hasta 1 s de kill grace). La comprobación del socket conserva una carrera local
stat/connect y no autentica criptográficamente al peer; daemon local confiable es supuesto
residual.

## Criterio

PASS solo si el contenedor pasa controles pre-start, productor tar=0, `docker start`=0, el
reporte fijo se valida, el proceso sale 0, inspección final confirma todos los controles,
se extraen exactamente 14 archivos sin
symlinks y el manifiesto fuente confirma sus 13/13 hashes. Cualquier fallo, timeout, salida
excesiva o discrepancia es NO-GO; no retry. No declarar smoke Pages/workerd, C03 integrado,
GO_LOCAL_PR o GO_DEVELOPMENT_REAL. El smoke actualizado requiere su propio runner y JIT.

## Exclusiones

No modificar ni reusar S1/D2/D3/D4/J1/J2/J3, manifiestos/evidencia consumidos o recursos
anteriores. No leer `.env*`, credenciales, Auth/MFA, SQL/DB, fixtures, datos operativos,
logs/exec/filesystem de otros recursos, caches/npm, workerd/Pages, Edge/PostgREST/Supabase,
Cloudflare, red externa, CI/remoto, push/PR/merge/deploy, schedules, `rm`/remove, cleanup
de artefactos, rollback o resume, fuera del stop acotado al ID pre-verificado descrito arriba.

## Comando exacto — solo tras aprobación humana

```bash
/usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="${HOME:?HOME is required for the selected local Docker context}" LANG=C LC_ALL=C \
  /usr/bin/timeout --signal=TERM --kill-after=30s 270s \
  /bin/bash -Eeuo pipefail <<'H3_C03_SOURCE_SNAPSHOT_F1_LAUNCHER'
set -Eeuo pipefail
launcher_local() {
  local limit=$1
  shift
  timeout --foreground --signal=TERM --kill-after=1s "${limit}s" "$@"
}
root="$(launcher_local 5 git rev-parse --show-toplevel)"
[[ "$root" == "$(pwd -P)" && "$root" == '/home/romel/src/studiamatch-h3req1-sync-20261002' ]] \
  || { printf 'NO-GO: unexpected candidate root\n' >&2; exit 1; }
[[ "$(launcher_local 5 git branch --show-current)" == 'feat/h3req1-sync-20261002' ]] \
  || { printf 'NO-GO: candidate branch changed\n' >&2; exit 1; }
[[ "$(launcher_local 5 git rev-parse HEAD)" == '4eb4d877a50b012bb630a129bd0c74482c33be9c' ]] \
  || { printf 'NO-GO: candidate HEAD changed\n' >&2; exit 1; }
runner='tests/h3req1_c03_source_snapshot_f1.sh'
sidecar='tests/h3req1-c03-source-snapshot-f1.sha256'
source_manifest='tests/h3req1-c03-startup-source-s1.sha256'
expected_runner='3249cdfed8043dfd751074ec0d844d6a9a88f14328b144f10d93c41cbbb446e0'
expected_sidecar='23d676776ce7fb95001576315d39913425756ea388809eed199dab4c0260af40'
expected_source='ae335c8e197d2c380bc877abbd53aa9f52a30f2b00e3310865bccb64ecb17c5d'
[[ -f "$runner" && ! -L "$runner" && -f "$sidecar" && ! -L "$sidecar" \
  && -f "$source_manifest" && ! -L "$source_manifest" ]] \
  || { printf 'NO-GO: fixed source inputs missing or symlinked\n' >&2; exit 1; }
runner_bytes="$(launcher_local 5 stat -Lc '%s' -- "$runner" 2>/dev/null)" \
  || { printf 'NO-GO: runner size unavailable\n' >&2; exit 1; }
sidecar_bytes="$(launcher_local 5 stat -Lc '%s' -- "$sidecar" 2>/dev/null)" \
  || { printf 'NO-GO: sidecar size unavailable\n' >&2; exit 1; }
source_bytes="$(launcher_local 5 stat -Lc '%s' -- "$source_manifest" 2>/dev/null)" \
  || { printf 'NO-GO: source manifest size unavailable\n' >&2; exit 1; }
[[ "$runner_bytes" =~ ^[0-9]+$ && "$runner_bytes" -le 262144 \
  && "$sidecar_bytes" =~ ^[0-9]+$ && "$sidecar_bytes" -le 512 \
  && "$source_bytes" =~ ^[0-9]+$ && "$source_bytes" -le 16384 ]] \
  || { printf 'NO-GO: launcher input exceeds its byte bound\n' >&2; exit 1; }
runner_b64="$(set -o pipefail; timeout --foreground --signal=TERM --kill-after=1s 5s base64 -w0 -- "$runner" 2>/dev/null | head -c 349529)" \
  || { printf 'NO-GO: runner capture failed\n' >&2; exit 1; }
sidecar_b64="$(set -o pipefail; timeout --foreground --signal=TERM --kill-after=1s 5s base64 -w0 -- "$sidecar" 2>/dev/null | head -c 685)" \
  || { printf 'NO-GO: sidecar capture failed\n' >&2; exit 1; }
runner_hash_line="$(printf '%s' "$runner_b64" | launcher_local 5 bash -o pipefail -c 'base64 --decode | sha256sum')"
sidecar_hash_line="$(printf '%s' "$sidecar_b64" | launcher_local 5 bash -o pipefail -c 'base64 --decode | sha256sum')"
runner_hash="${runner_hash_line%% *}"
sidecar_hash="${sidecar_hash_line%% *}"
[[ "$runner_hash" == "$expected_runner" && "$sidecar_hash" == "$expected_sidecar" ]] \
  || { printf 'NO-GO: approved runner/sidecar digest mismatch\n' >&2; exit 1; }
sidecar_text="$(printf '%s' "$sidecar_b64" | launcher_local 5 base64 --decode)"
[[ "$sidecar_text" == "$expected_runner  $runner" ]] \
  || { printf 'NO-GO: sidecar does not pin the approved runner\n' >&2; exit 1; }
source_hash_line="$(launcher_local 5 sha256sum "$source_manifest")"
[[ "${source_hash_line%% *}" == "$expected_source" ]] \
  || { printf 'NO-GO: S1 source manifest changed\n' >&2; exit 1; }
printf '%s' "$runner_b64" | launcher_local 5 base64 --decode | \
  /usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="$HOME" LANG=C LC_ALL=C \
  H3_SNAPSHOT_ROOT="$root" \
  H3_SNAPSHOT_VERIFIED_RUNNER_SHA256="$runner_hash" \
  H3_SNAPSHOT_VERIFIED_SIDECAR_SHA256="$sidecar_hash" \
  /bin/bash -s -- \
    --jit H3-CLOSE-03-SOURCE-SNAPSHOT-F1-2026-10-07 \
    --runner-sha256 "$runner_hash" \
    --sidecar-sha256 "$sidecar_hash"
H3_C03_SOURCE_SNAPSHOT_F1_LAUNCHER
```

El runner calcula tiempos individuales respecto de 180 s y reserva hasta 10 s para stop;
el launcher envuelve **preflight y ejecución** en timeout global: envía TERM al grupo de
procesos a los 270 s y KILL tras 30 s adicionales (techo absoluto 300 s). Preflight local se
limita a operaciones individuales ≤5 s; el checksum tiene ≤20 s.

El launcher verifica hashes y ejecuta los bytes capturados del runner. Esto protege la
integridad del comando aprobado, pero no es una barrera criptográfica contra invocación
manual por otro proceso del mismo usuario local: quien puede ejecutar el runner también
puede fijar sus argumentos/variables de entorno, y quien controla el daemon puede ejecutar
Docker directamente. **Waiver propuesto, NO aprobado:** causa y evidencia reproducible:
runner, guard de argumentos/entorno `H3_SNAPSHOT_VERIFIED_*` (líneas 166–170) acepta valores
provistos por el invocador; inspeccionar ese guard basta para reproducir la limitación y no
requiere ejecutar el runner ni Docker. Mitigación: en este ciclo el agente ejecutará solo el
launcher hash-bound tras aprobación humana y repetirá branch/HEAD/hashes. Owner: Romel,
responsable humano del proyecto y titular operativo del checkout/Docker local. Riesgo:
bypass local de la aprobación bajo la misma cuenta/daemon; limitado a permisos de esa cuenta,
sin vía remota ni secretos en alcance. Expiración: después de una única invocación F1 o al
cancelar este JIT, lo que ocurra primero. La aprobación JIT debe aceptar explícitamente este
residual o F1 no se ejecutará.

Runner, sidecar, source manifest, sintaxis y revisión de seguridad deben pasar el preflight
antes de solicitar aprobación. La aprobación, si se solicita, será para una invocación exacta
y queda consumida incluso con NO-GO. El smoke Pages/workerd permanece fuera del alcance.
