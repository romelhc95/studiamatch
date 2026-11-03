#!/usr/bin/env bash
set -Eeuo pipefail

readonly JIT='H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D2'
readonly MANIFEST='tests/h3req1-c03-integrated-diagnostic-r4-d2.sha256'
[[ "${1:-}" == '--jit' && "${2:-}" == "$JIT" && "${3:-}" == '--manifest-sha256' && $# -eq 4 ]] || {
  echo "Refusing to run: exact JIT $JIT and approved manifest SHA-256 required." >&2
  exit 77
}
readonly APPROVED_MANIFEST_SHA256="${4:-}"
[[ "$APPROVED_MANIFEST_SHA256" =~ ^[a-f0-9]{64}$ ]] || {
  echo 'Refusing to run: invalid manifest SHA-256.' >&2
  exit 77
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
exec 3>&1

readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly INTEGRATED_MANIFEST='tests/h3req1-c03-integrated.sha256'
readonly INTEGRATED_MANIFEST_SHA256='e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7'
readonly INTEGRATED_RUNNER='tests/h3req1_c03_integrated_drill.sh'
readonly INTEGRATED_RUNNER_SHA256='28c417bee4bd0f3c0d9d1e576397c8be1af9e7d0309b81a58c1fcc4f3639f474'
readonly R4_LOG='.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log'
readonly D1_LOG='.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d1.log'
readonly RUNTIME='h3req1-c03-integrated-runtime-20261006-r4'
readonly RESULT_LOG='.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d2.log'

phase='preflight'
on_error() {
  local status=$?
  printf 'Diagnostic halted phase=%s exit=%s; read-only scope, no cleanup/resume.\n' "$phase" "$status" >&2
  printf 'C03 R4 runtime diagnostic D2 halted in phase=%s (exit=%s); no cleanup/resume.\n' "$phase" "$status" >&3
}
on_signal() {
  local signal=$1 status
  case "$signal" in
    HUP) status=129 ;;
    INT) status=130 ;;
    TERM) status=143 ;;
    *) status=1 ;;
  esac
  printf 'Diagnostic interrupted phase=%s signal=%s exit=%s; no cleanup/resume.\n' "$phase" "$signal" "$status" >&2
  printf 'C03 R4 runtime diagnostic D2 interrupted in phase=%s (signal=%s); no cleanup/resume.\n' "$phase" "$signal" >&3
  trap - ERR HUP INT TERM
  exit "$status"
}
trap on_error ERR
trap 'on_signal HUP' HUP
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM
fail() { printf 'NO-GO: %s\n' "$1" >&2; return 1; }

[[ -d "$ROOT/tests" && ! -L "$ROOT/tests" ]] || fail 'tests directory missing or symlinked'
for input in "$MANIFEST" "$INTEGRATED_MANIFEST" "$INTEGRATED_RUNNER" "$R4_LOG" "$D1_LOG" 'tests/h3req1_c03_integrated_runtime_diag_d2.sh'; do
  [[ -f "$ROOT/$input" && ! -L "$ROOT/$input" ]] || fail "diagnostic input missing or symlinked: $input"
done
[[ -d "$ROOT/.context/evidencia" && ! -L "$ROOT/.context" && ! -L "$ROOT/.context/evidencia" ]] || fail 'evidence directory missing or symlinked'
[[ ! -e "$ROOT/$RESULT_LOG" && ! -L "$ROOT/$RESULT_LOG" ]] || fail "diagnostic result path already exists: $RESULT_LOG"
if ! ACTUAL_MANIFEST_SHA256="$(sha256sum "$MANIFEST" | cut -d' ' -f1)"; then
  fail 'unable to hash diagnostic manifest'
fi
[[ "$ACTUAL_MANIFEST_SHA256" == "$APPROVED_MANIFEST_SHA256" ]] || fail 'diagnostic manifest differs from approved digest'
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'candidate branch changed'
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail 'candidate HEAD changed'

set -o noclobber
exec >"$ROOT/$RESULT_LOG" 2>&1
set +o noclobber

sha256sum -c "$MANIFEST" || fail 'diagnostic input manifest mismatch'
[[ "$(sha256sum "$INTEGRATED_MANIFEST" | cut -d' ' -f1)" == "$INTEGRATED_MANIFEST_SHA256" ]] || fail 'R4 integrated manifest digest changed'
[[ "$(sha256sum "$INTEGRATED_RUNNER" | cut -d' ' -f1)" == "$INTEGRATED_RUNNER_SHA256" ]] || fail 'R4 integrated runner hash changed'
grep -Fqx 'NO-GO: runtime state timeout: healthz' "$R4_LOG" || fail 'R4 evidence does not contain the expected healthz timeout'
grep -Fqx 'NO-GO: R4 runtime image does not match the pinned digest' "$D1_LOG" || fail 'D1 evidence does not contain the expected sanitized image guard result'

phase='read-only-inspect-exact-r4-runtime-state'
if ! metadata="$(docker inspect --format '{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{.HostConfig.LogConfig.Type}}' "$RUNTIME" 2>/dev/null)"; then
  fail 'the exact R4 runtime container is unavailable; Docker output suppressed'
fi
IFS='|' read -r name state exit_code oom_killed log_driver <<< "$metadata"
[[ "$name" == "/$RUNTIME" ]] || fail 'Docker inspect returned an unexpected container name'
[[ "$state" =~ ^(created|running|paused|restarting|removing|exited|dead)$ ]] || fail 'runtime state is outside the safe output schema'
[[ "$exit_code" =~ ^[0-9]+$ ]] || fail 'runtime exit code is outside the safe output schema'
[[ "$oom_killed" == 'true' || "$oom_killed" == 'false' ]] || fail 'OOM state is outside the safe output schema'
[[ "$log_driver" == 'none' ]] || fail 'runtime logging driver differs from the R4 expected value'

printf 'runtime-container=%s\n' "$RUNTIME"
printf 'runtime-image-metadata=not-queried; R4 runner/manifest hashes are pinned\n'
printf 'runtime-state=%s\n' "$state"
printf 'runtime-exit-code=%s\n' "$exit_code"
printf 'runtime-oom-killed=%s\n' "$oom_killed"
printf 'runtime-log-driver=none\n'
printf '%s\n' 'runtime-log-availability=disabled-by-docker-log-driver'
printf 'D1 image field was intentionally excluded; no image identity is inferred by D2.\n'
printf 'No docker logs/exec, network or volume inspection, cleanup, stop, restart, or resume was performed.\n'
