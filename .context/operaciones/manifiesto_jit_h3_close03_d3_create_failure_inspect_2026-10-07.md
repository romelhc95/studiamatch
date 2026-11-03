# Solicitud JIT — lectura acotada del fallo create/start de D3

Estado: **propuesto, NO aprobado, NO ejecutado**. Este manifiesto pide una única lectura
de metadata del recurso D3 ya creado. No autoriza crear o iniciar recursos.

## Pregunta y decisión permitida

Determinar si Docker conservó en `.State.Error` el motivo de que el comando D3
`docker run --detach` terminara con exit 1 y dejara el contenedor en estado `created`.
La lectura puede orientar una corrección o establecer que hace falta una reproducción
mínima nueva. No puede demostrar la causa histórica S1 ni atribuirla a ownership.

## Recurso único

- Tipo: contenedor Docker local existente.
- ID exacto permitido:
  `81c57f0e70538d7430e46a61d745a3b6296fb943980342f2caeead19c0658ebf`.
- Nombre esperado: `/h3req1-c03-snapshot-diagnostic-d3-20261007`.
- JIT/manifest/nonce esperados: `H3-CLOSE-03-SNAPSHOT-CAUSE-DIAGNOSTIC-2026-10-07-D3`,
  `560ea87e661acd95406ea749358b060d0132dcc97300682db1b101ef1f4ca0e1`,
  `509355-1791394106958035732-20366`.
- Fuente identificadora: reporte D3 original, que permanece intacto.

## Operación y campos permitidos

Una sola consulta read-only `docker inspect --type container` por el ID completo
anterior, contra un contexto Docker que el preflight confirme como socket Unix local.
No consultar por nombre. El formato solicitará exclusivamente:

`Id`, `Name`, `Created`, `State.Status`, `State.Error`, `State.ExitCode`,
`State.OOMKilled`, `State.Dead`, `State.Paused`, `State.Restarting`,
`State.StartedAt`, `State.FinishedAt` y tres labels exactos de identidad
(`com.studiamatch.h3.snapshot.jit`, `.manifest`, `.run`). No se lee `.Config.Env`,
el resto de `.Config`, `.HostConfig`, mounts, redes, procesos, logs ni filesystem.

`.State.Error` se mantiene solo en memoria durante el sanitizado; nunca se imprime ni
persiste en crudo. Un parser local de JSON debe verificar schema/ID/nombre/labels y
producir un resumen acotado: categoría allowlisted, texto de error con paths, tokens,
JWT, claves, IDs hexadecimales y controles redactados, máximo 512 caracteres. La salida
completa de `inspect` tiene límite de 8 KiB; cualquier parseo, identidad, sanitización,
I/O o límite fallido termina en NO-GO y no amplía la consulta. Solo se registra la salida
sanitizada.

## Preflight local y comando exacto propuesto

El siguiente launcher es la única invocación solicitada. Su entorno vacío impide
overrides Docker heredados. `docker context show/inspect` consulta solo configuración
local del cliente; no lista ni consulta recursos del daemon. El único acceso al daemon
es el `inspect` por ID completo mostrado en el script. Si cualquier preflight falla,
el script termina antes de ese acceso. No imprime el endpoint ni el contenido crudo.

```bash
/usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="${HOME:?HOME is required for the selected local Docker context}" LANG=C LC_ALL=C \
  /bin/bash -Eeuo pipefail <<'H3_D3_CREATE_FAILURE_INSPECT'
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly ID='81c57f0e70538d7430e46a61d745a3b6296fb943980342f2caeead19c0658ebf'
readonly NAME='/h3req1-c03-snapshot-diagnostic-d3-20261007'
readonly JIT='H3-CLOSE-03-SNAPSHOT-CAUSE-DIAGNOSTIC-2026-10-07-D3'
readonly MANIFEST_SHA='560ea87e661acd95406ea749358b060d0132dcc97300682db1b101ef1f4ca0e1'
readonly NONCE='509355-1791394106958035732-20366'
readonly REPORT='.context/evidencia/h3req1_c03_snapshot_diagnostic_2026-10-07_d3.md'
readonly REPORT_SHA='76e4c7c4182bcb30156f7a12eea87376aa68f6667c21a203ef8a7ddcc9f43a23'
readonly D3_JIT='.context/operaciones/manifiesto_jit_h3_close03_snapshot_diagnostic_2026-10-07_d3.md'
readonly D3_JIT_SHA='cd90d783b7ec5a65a5ccc4e57fe6f737681d7aa4f8ed46a4d9c7e8c786f3ae7c'
readonly RUNNER='tests/h3req1_c03_snapshot_diagnostic_d3.sh'
readonly RUNNER_SHA='a64fa5743372d5ff39fb9a009d89beb68a9afec756b32455066db06f84c41796'
readonly MANIFEST='tests/h3req1-c03-snapshot-diagnostic-d3.sha256'
readonly OUTPUT_LIMIT=8192

stop() { printf 'NO-GO: %s\n' "$1" >&2; exit 1; }
hash_of() { local line; line="$(sha256sum -- "$1")" || return 1; printf '%s\n' "${line%% *}"; }
[[ "$(pwd -P)" == "$ROOT" ]] || stop 'wrong checkout root'
[[ "$(git rev-parse --show-toplevel)" == "$ROOT" ]] || stop 'wrong git root'
[[ "$(git branch --show-current)" == 'feat/h3req1-sync-20261002' ]] || stop 'candidate branch changed'
[[ "$(git rev-parse HEAD)" == '4eb4d877a50b012bb630a129bd0c74482c33be9c' ]] || stop 'candidate HEAD changed'
[[ "$(hash_of "$REPORT")" == "$REPORT_SHA" ]] || stop 'D3 report hash changed'
[[ "$(hash_of "$D3_JIT")" == "$D3_JIT_SHA" ]] || stop 'approved D3 JIT snapshot changed'
[[ "$(hash_of "$RUNNER")" == "$RUNNER_SHA" ]] || stop 'D3 runner hash changed'
[[ "$(hash_of "$MANIFEST")" == "$MANIFEST_SHA" ]] || stop 'D3 manifest hash changed'
sha256sum --check "$MANIFEST" >/dev/null 2>&1 || stop 'D3 manifest no longer pins its runner'
command -v perl >/dev/null 2>&1 || stop 'Perl sanitizer unavailable; no daemon query made'
perl -MJSON::PP -MEncode=encode -e 'exit 0' >/dev/null 2>&1 || stop 'JSON sanitizer unavailable; no daemon query made'
[[ -z "${DOCKER_HOST:-}${DOCKER_CONTEXT:-}${DOCKER_TLS_VERIFY:-}${DOCKER_CERT_PATH:-}" ]] \
  || stop 'Docker endpoint override present'

context="$(timeout --foreground --signal=TERM --kill-after=1s 5s docker context show 2>/dev/null)" \
  || stop 'cannot read current local context name'
[[ "$context" =~ ^[A-Za-z0-9_.-]{1,64}$ ]] || stop 'context name outside safe schema'
endpoint_json="$(timeout --foreground --signal=TERM --kill-after=1s 5s \
  docker context inspect --format '{{json (index .Endpoints "docker").Host}}' "$context" 2>/dev/null)" \
  || stop 'cannot read local context endpoint'
[[ "$endpoint_json" =~ ^\"unix:///[A-Za-z0-9_./-]+\"$ ]] || stop 'context is not a local Unix socket'
endpoint="${endpoint_json:1:${#endpoint_json}-2}"
socket="${endpoint#unix://}"
socket_identity() {
  timeout --foreground --signal=TERM --kill-after=0.2s 1s stat -Lc '%F|%d:%i:%u:%g:%a' -- "$1" 2>/dev/null
}
initial_identity="$(socket_identity "$socket")" || stop 'cannot verify local socket'
[[ "$initial_identity" =~ ^socket\|[0-9]+:[0-9]+:[0-9]+:[0-9]+:[0-7]{3,4}$ ]] || stop 'endpoint is not a local socket'
canonical="$(timeout --foreground --signal=TERM --kill-after=0.2s 1s realpath -e -- "$socket" 2>/dev/null)" \
  || stop 'cannot canonicalize local socket'
[[ "$canonical" == /* && "$canonical" != *$'\n'* && "$canonical" != *$'\r'* ]] || stop 'invalid canonical socket path'
canonical_identity="$(socket_identity "$canonical")" || stop 'cannot verify canonical socket'
[[ "$canonical_identity" == "$initial_identity" ]] || stop 'socket identity changed during preflight'
verified_endpoint="unix://$canonical"

set +e
inspect_json="$(timeout --foreground --signal=TERM --kill-after=2s 10s \
  docker --host "$verified_endpoint" inspect --type container \
  --format '{"id":{{json .Id}},"name":{{json .Name}},"created":{{json .Created}},"status":{{json .State.Status}},"state_error":{{json .State.Error}},"exit_code":{{json (printf "%d" .State.ExitCode)}},"oom_killed":{{json (printf "%t" .State.OOMKilled)}},"dead":{{json (printf "%t" .State.Dead)}},"paused":{{json (printf "%t" .State.Paused)}},"restarting":{{json (printf "%t" .State.Restarting)}},"started_at":{{json .State.StartedAt}},"finished_at":{{json .State.FinishedAt}},"jit":{{json (index .Config.Labels "com.studiamatch.h3.snapshot.jit")}},"manifest":{{json (index .Config.Labels "com.studiamatch.h3.snapshot.manifest")}},"run":{{json (index .Config.Labels "com.studiamatch.h3.snapshot.run")}}}' \
  "$ID" 2>/dev/null | head -c "$((OUTPUT_LIMIT + 1))")"
inspect_status=$?
set -e
[[ "$inspect_status" -eq 0 ]] || stop 'single inspect failed or timed out; no retry/fallback'
(( ${#inspect_json} <= OUTPUT_LIMIT )) || stop 'inspect output exceeded 8 KiB; discarded'
final_identity="$(socket_identity "$canonical")" || stop 'cannot reverify local socket after query'
[[ "$final_identity" == "$canonical_identity" ]] || stop 'socket identity changed; query output discarded'

sanitized="$(printf '%s' "$inspect_json" | perl -MJSON::PP -MEncode=encode -e '
use strict; use warnings;
local $/;
my $raw = <STDIN>;
die unless defined($raw) && length($raw) <= 8192;
my $o = decode_json($raw);
die unless ref($o) eq "HASH";
my @keys = qw(id name created status state_error exit_code oom_killed dead paused restarting started_at finished_at jit manifest run);
my %allowed = map { $_ => 1 } @keys;
die if grep { !exists $o->{$_} || ref($o->{$_}) } @keys;
die if grep { !$allowed{$_} } keys %$o;
my %expected = (
  id => "81c57f0e70538d7430e46a61d745a3b6296fb943980342f2caeead19c0658ebf",
  name => "/h3req1-c03-snapshot-diagnostic-d3-20261007",
  jit => "H3-CLOSE-03-SNAPSHOT-CAUSE-DIAGNOSTIC-2026-10-07-D3",
  manifest => "560ea87e661acd95406ea749358b060d0132dcc97300682db1b101ef1f4ca0e1",
  run => "509355-1791394106958035732-20366",
);
die if grep { $o->{$_} ne $expected{$_} } keys %expected;
die unless $o->{status} =~ /\A(?:created|running|paused|restarting|removing|exited|dead)\z/;
die unless $o->{exit_code} =~ /\A[0-9]{1,3}\z/;
for my $key (qw(oom_killed dead paused restarting)) { die unless $o->{$key} =~ /\A(?:true|false)\z/; }
for my $key (qw(created started_at finished_at)) { die unless $o->{$key} =~ /\A[0-9TZ:.+\-]+\z/; }
my $e = $o->{state_error};
die if length(encode("UTF-8", $e)) > 4096;
my $lc = lc($e);
my $class = $e eq "" ? "empty" :
  $lc =~ /no space left|disk quota|resource temporarily unavailable/ ? "resource-exhaustion" :
  $lc =~ /permission denied|operation not permitted/ ? "permission-denied" :
  $lc =~ /mount|read-only file system/ ? "mount-or-filesystem" :
  $lc =~ /oci runtime|runc|container init|failed to start|shim task/ ? "runtime-create-start" :
  $lc =~ /no such file|executable.*not found|exec format/ ? "entrypoint-or-file" :
  "unclassified-nonempty";
my $safe = $e;
$safe =~ s/[\x00-\x1f\x7f]/ /g;
$safe =~ s/\s+/ /g;
$safe =~ s{https?://\S+}{[URL]}ig;
$safe =~ s/\bBearer\s+\S+/Bearer [REDACTED]/ig;
$safe =~ s/\beyJ[A-Za-z0-9_.-]{8,}\b/[JWT_REDACTED]/g;
$safe =~ s/\bsb_(?:publishable|secret)_[A-Za-z0-9_-]+/[API_KEY_REDACTED]/ig;
$safe =~ s/\b(token|secret|password|authorization|api[_ -]?key)\s*[:=]\s*[^\s,;]+/$1=[REDACTED]/ig;
$safe =~ s{https?://\S+}{[URL]}ig;
$safe =~ s{(?:[A-Za-z]:\\)[^\s,;]+}{[PATH]}g;
$safe =~ s{(?:/[A-Za-z0-9._+@%=-]+)+/?}{[PATH]}g;
$safe =~ s/\b[A-Za-z0-9_-]{48,}\b/[LONG_VALUE_REDACTED]/g;
$safe =~ s/\b[a-f0-9]{32,}\b/[HEX_ID_REDACTED]/ig;
$safe = substr($safe, 0, 512);
$safe = "[empty]" if $safe eq "";
print "id=$o->{id}\nname=$o->{name}\ncreated=$o->{created}\nstatus=$o->{status}\n";
print "exit_code=$o->{exit_code}\noom_killed=$o->{oom_killed}\ndead=$o->{dead}\npaused=$o->{paused}\nrestarting=$o->{restarting}\n";
print "started_at=$o->{started_at}\nfinished_at=$o->{finished_at}\nstate_error_class=$class\nstate_error_sanitized=$safe\n";
' 2>/dev/null)" || stop 'identity/schema/sanitizer failed; raw output discarded'
unset inspect_json
printf '%s\n' "$sanitized"
H3_D3_CREATE_FAILURE_INSPECT
```

La salida del script es el único material que puede copiarse a evidencia. No persiste
el JSON ni `.State.Error` crudo. Presupuesto máximo: contexto show/inspect 5 s cada uno,
stat/realpath 1 s cada uno, daemon inspect 10 s + 2 s de gracia; suma máxima nominal
menor a 30 s. No usar root, `sudo`, capacidades, cambios de permisos o configuración.

## Errores, resultado y límites

- Si el contexto no es local Unix, el ID no existe en ese daemon, falla el timeout,
  output supera 8 KiB, el error de Docker/JSON no pasa el esquema o la identidad no
  coincide: registrar categoría sanitizada NO-GO y detenerse. No buscar por nombre ni
  cambiar de contexto para “encontrarlo”.
- Si `State.Error` está vacío o no permite determinar el motivo, conservar ese resultado
  y proponer reproducción sintética nueva con captura sanitizada desde el origen; requerirá
  otro JIT explícito. No leer `docker logs` como fallback.
- Si el estado resulta `running`, solo informar el hallazgo y preservar el recurso; no
  parar ni cambiar su estado bajo este permiso.
- Evidencia sanitaria propuesta: `.context/evidencia/h3req1_c03_snapshot_d3_create_failure_inspect_2026-10-07.md`.

Prohibido: `start`, restart/retry, `exec`, `logs`, `attach`, `wait`, `stop`, `kill`,
`rm`, cleanup, rollback/resume, `ps`/list, inspect de otro ID, imágenes, redes, volúmenes,
mounts o caches; acceso a `.env*`, secretos, credenciales, Auth, SQL, PG17/PostgREST,
Edge, Pages/workerd, Supabase/Cloudflare, red externa, Git remoto, push/PR/merge/deploy,
schedules y workflow_dispatch. No eleva privilegios ni toca ramas protegidas.

Este JIT se consume solo si se invoca la única consulta de daemon; el fallo de un
preflight detiene la operación sin fallback. No autoriza snapshot completo, smoke,
C03 integrado ni los ciclos siguientes. Owner de aprobación: responsable humano.
