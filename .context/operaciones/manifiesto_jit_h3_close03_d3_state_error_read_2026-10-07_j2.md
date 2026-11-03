# Solicitud JIT J2 — lectura únicamente de `.State.Error` del recurso D3

Estado: **propuesto, NO aprobado, NO ejecutado**. J1 está consumido y no se repite. Este
JIT solicita una lectura nueva, más pequeña, para recuperar el único campo que puede
explicar el fallo de create/start. No crea ni inicia recursos.

## Alcance y recurso

- Único recurso: contenedor Docker local ya creado por D3.
- Único ID permitido:
  `81c57f0e70538d7430e46a61d745a3b6296fb943980342f2caeead19c0658ebf`.
- Nombre esperado: `/h3req1-c03-snapshot-diagnostic-d3-20261007`.
- El intento J1 (SHA-256
  `1ec96b5a1820e519625bce113777e99fb1e2e693c8317f27625358ec08b241f1`) completó el
  `inspect`, pero su parser/sanitizador falló cerrado y descartó la salida. J2 no vuelve
  a ejecutar D3 ni hereda permisos.

## Única operación Docker y campos

Tras un preflight local que valida el checkout y un socket Unix local, una única llamada
al daemon por ID completo. Lee solo `Id`, `Name` y `.State.Error`; no consulta por nombre.
El campo de error JSON se sanitiza en memoria, nunca se imprime ni persiste en crudo.

## Comando exacto

```bash
/usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="${HOME:?HOME is required for the selected local Docker context}" LANG=C LC_ALL=C \
  /bin/bash -Eeuo pipefail <<'H3_D3_STATE_ERROR_J2'
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly ID='81c57f0e70538d7430e46a61d745a3b6296fb943980342f2caeead19c0658ebf'
readonly NAME='/h3req1-c03-snapshot-diagnostic-d3-20261007'
readonly REPORT='.context/evidencia/h3req1_c03_snapshot_diagnostic_2026-10-07_d3.md'
readonly REPORT_SHA='76e4c7c4182bcb30156f7a12eea87376aa68f6667c21a203ef8a7ddcc9f43a23'
readonly D3_JIT='.context/operaciones/manifiesto_jit_h3_close03_snapshot_diagnostic_2026-10-07_d3.md'
readonly D3_JIT_SHA='cd90d783b7ec5a65a5ccc4e57fe6f737681d7aa4f8ed46a4d9c7e8c786f3ae7c'
readonly RUNNER='tests/h3req1_c03_snapshot_diagnostic_d3.sh'
readonly RUNNER_SHA='a64fa5743372d5ff39fb9a009d89beb68a9afec756b32455066db06f84c41796'
readonly MANIFEST='tests/h3req1-c03-snapshot-diagnostic-d3.sha256'
readonly MANIFEST_SHA='560ea87e661acd95406ea749358b060d0132dcc97300682db1b101ef1f4ca0e1'
readonly J1='.context/operaciones/manifiesto_jit_h3_close03_d3_create_failure_inspect_2026-10-07.md'
readonly J1_SHA='1ec96b5a1820e519625bce113777e99fb1e2e693c8317f27625358ec08b241f1'
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
[[ "$(hash_of "$MANIFEST")" == "$MANIFEST_SHA" ]] || stop 'D3 runner manifest hash changed'
[[ "$(hash_of "$J1")" == "$J1_SHA" ]] || stop 'consumed J1 request snapshot changed'
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
inspect_output="$(timeout --foreground --signal=TERM --kill-after=2s 10s \
  docker --host "$verified_endpoint" inspect --type container \
  --format '{{.Id}}|{{.Name}}|{{json .State.Error}}' "$ID" 2>/dev/null | head -c "$((OUTPUT_LIMIT + 1))")"
inspect_status=$?
set -e
[[ "$inspect_status" -eq 0 ]] || stop 'single inspect failed or timed out; no retry/fallback'
(( ${#inspect_output} <= OUTPUT_LIMIT )) || stop 'inspect output exceeded 8 KiB; discarded'
final_identity="$(socket_identity "$canonical")" || stop 'cannot reverify local socket after query'
[[ "$final_identity" == "$canonical_identity" ]] || stop 'socket identity changed; query output discarded'

sanitized="$(printf '%s' "$inspect_output" | perl -MJSON::PP -MEncode=encode -e '
use strict; use warnings;
local $/;
my $raw = <STDIN>;
die unless defined($raw) && length($raw) <= 8192;
$raw =~ s/\n\z//;
die if $raw =~ /[\r\n]/;
my ($id, $name, $error_json) = $raw =~ /\A([a-f0-9]{64})\|([^|]+)\|(.+)\z/s;
die unless defined($id) && defined($name) && defined($error_json);
die unless $id eq "81c57f0e70538d7430e46a61d745a3b6296fb943980342f2caeead19c0658ebf";
die unless $name eq "/h3req1-c03-snapshot-diagnostic-d3-20261007";
my $error = decode_json($error_json);
$error = "" unless defined $error;
die if ref($error);
die if length(encode("UTF-8", $error)) > 4096;
my $lc = lc($error);
my $class = $error eq "" ? "empty" :
  $lc =~ /no space left|disk quota|resource temporarily unavailable/ ? "resource-exhaustion" :
  $lc =~ /permission denied|operation not permitted/ ? "permission-denied" :
  $lc =~ /mount|read-only file system/ ? "mount-or-filesystem" :
  $lc =~ /oci runtime|runc|container init|failed to start|shim task/ ? "runtime-create-start" :
  $lc =~ /no such file|executable.*not found|exec format/ ? "entrypoint-or-file" :
  "unclassified-nonempty";
my $safe = $error;
$safe =~ s/[\x00-\x1f\x7f]/ /g;
$safe =~ s/\s+/ /g;
$safe =~ s{https?://\S+}{[URL]}ig;
$safe =~ s/\bBearer\s+\S+/Bearer [REDACTED]/ig;
$safe =~ s/\beyJ[A-Za-z0-9_.-]{8,}\b/[JWT_REDACTED]/g;
$safe =~ s/\bsb_(?:publishable|secret)_[A-Za-z0-9_-]+/[API_KEY_REDACTED]/ig;
$safe =~ s/\b(token|secret|password|authorization|api[_ -]?key)\s*[:=]\s*[^\s,;]+/$1=[REDACTED]/ig;
$safe =~ s{(?:[A-Za-z]:\\)[^\s,;]+}{[PATH]}g;
$safe =~ s{(?:/[A-Za-z0-9._+@%=-]+)+/?}{[PATH]}g;
$safe =~ s/\b[A-Za-z0-9_-]{48,}\b/[LONG_VALUE_REDACTED]/g;
$safe =~ s/\b[a-f0-9]{32,}\b/[HEX_ID_REDACTED]/ig;
$safe = substr($safe, 0, 512);
$safe = "[empty]" if $safe eq "";
print "id=$id\nname=$name\nstate_error_class=$class\nstate_error_sanitized=$safe\n";
' 2>/dev/null)" || stop 'ID/JSON/sanitizer failed; raw output discarded'
unset inspect_output
printf '%s\n' "$sanitized"
H3_D3_STATE_ERROR_J2
```

Ejecución: un solo `inspect`, timeout 10 s + TERM/gracia 2 s; contexto show/inspect
5 s cada uno y `stat`/`realpath` 1 s cada uno; presupuesto nominal total menor a 30 s.
Los errores Docker/JSON/I/O se descartan y solo generan NO-GO genérico. No hay retry ni
fallback. Si el campo está vacío o no permite determinar causa, se detiene y se propone
una reproducción mínima nueva, observable y bajo JIT independiente.

Prohibido: `create`, `start`, restart/retry, `exec`, `logs`, attach, wait, stop, kill, rm,
cleanup, rollback/resume, `ps`/list, inspect de otro ID, DB/SQL/PG17/PostgREST, Auth,
correo, Edge, Pages/workerd, red externa, Supabase/Cloudflare, secrets, Git remoto,
push/PR/merge/deploy, schedules o workflow_dispatch. Sin root, `sudo`, capacidades ni
cambios de permisos/configuración.

Este JIT no autoriza reproducción, snapshot completo, smoke ni C03 integrado. Evidencia
sanitaria, solo tras aprobación/ejecución: `.context/evidencia/h3req1_c03_snapshot_d3_state_error_read_2026-10-07_j2.md`.
Owner de aprobación: responsable humano.
