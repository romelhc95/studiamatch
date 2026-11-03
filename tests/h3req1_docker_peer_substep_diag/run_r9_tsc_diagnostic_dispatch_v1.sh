set -u -o pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_r9_tsc_diagnostic_host_v1.sh'
readonly RUNNER_SHA256='462f97186f13780fafeeb4e10095370746098ea0629e9b0d66476b77ad6c3694'
readonly CAPTURE='/tmp/h3req1-g03-r9-tsc-v1-output-20261010.partial'
readonly SANITIZED='/tmp/h3req1-g03-r9-tsc-v1-output-20261010.sanitized'
readonly EVIDENCE='/home/romel/src/studiamatch-h3req1-sync-20261002/.context/evidencia/h3req1_g03_r9_tsc_v1_execution_2026-10-10.txt'
readonly SAFE_PHASE_RE='^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$'
readonly SAFE_EXIT_RE='^exit=[0-9]{1,3}$'
readonly SAFE_DIAGNOSTIC_RE='^(diagnostic=script=(\.githooks/(pre-commit|pre-push)|scripts/security/(h2_web_mock_smoke|protected_path_scope_guard|scan_credentials)[.]sh|tests/sql/h3_invitation_reservation_concurrency[.]sh|tests/test_protected_path_scope_guard[.]sh)\|line=[0-9]{1,6}\|column=[0-9]{1,6}\|rule=SC[0-9]{4}|diagnostic=path=web/(src|test|tests|types)/[A-Za-z0-9_./-]{1,160}\|line=[0-9]{1,6}\|column=[0-9]{1,6}\|code=TS[0-9]{4,6})$'

fail() {
  printf 'phase=dispatch-preflight|error_code=%s\nexit=1\n' "$1"
  exit 1
}

if (( EUID == 0 )); then fail RUN_AS_WSL_USER; fi
if [[ ! -t 0 ]]; then fail INTERACTIVE_TTY_REQUIRED; fi
if [[ "$(uname -s 2>/dev/null)" != Linux || "$(uname -r 2>/dev/null | tr '[:upper:]' '[:lower:]')" != *microsoft* ]]; then fail WSL_REQUIRED; fi
if [[ "$(git -C "$ROOT" branch --show-current 2>/dev/null)" != feat/h3req1-sync-20261002 || "$(git -C "$ROOT" rev-parse HEAD 2>/dev/null)" != 4eb4d877a50b012bb630a129bd0c74482c33be9c ]]; then fail CANDIDATE_IDENTITY_MISMATCH; fi
wip_counts="$(git -C "$ROOT" status --porcelain=v1 2>/dev/null | awk 'BEGIN{m=0;u=0;s=0} substr($0,1,2)=="??"{u++;next} {m++;if(substr($0,1,1)!=" ")s++} END{printf "%d/%d/%d",m,u,s}')" || fail WIP_READ_FAILED
if [[ "$wip_counts" != 55/284/0 ]]; then fail WIP_MISMATCH; fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout || ! -x /usr/bin/stat || ! -x /usr/bin/mv || ! -x /bin/bash ]]; then fail RUNTIME_UNAVAILABLE; fi
if [[ ! -f "$RUNNER" || -L "$RUNNER" ]]; then fail RUNNER_UNAVAILABLE; fi
runner_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || fail RUNNER_HASH_FAILED
if [[ "${runner_line%% *}" != "$RUNNER_SHA256" ]]; then fail RUNNER_HASH_MISMATCH; fi
if [[ -e "$CAPTURE" || -e "$SANITIZED" || -e "$EVIDENCE" ]]; then fail OUTPUT_PATH_EXISTS; fi

if /usr/bin/timeout --foreground --signal=INT --kill-after=5s 180s /bin/bash "$RUNNER" >"$CAPTURE" 2>/dev/null; then
  runner_status=0
else
  runner_status=$?
fi

capture_bytes="$(/usr/bin/stat -c '%s' -- "$CAPTURE" 2>/dev/null)" || {
  printf 'phase=output-capture|error_code=CAPTURE_READ_FAILED\nexit=1\n' > "$CAPTURE"
  runner_status=1
  capture_bytes=0
}
if [[ ! "$capture_bytes" =~ ^[0-9]+$ ]] || (( capture_bytes > 8192 )); then
  printf 'phase=output-capture|error_code=OUTPUT_TOO_LARGE\n' > "$CAPTURE"
  runner_status=1
fi

output_invalid=0
sanitized_lines=0
if ! : > "$SANITIZED"; then
  printf 'phase=output-capture|error_code=SANITIZED_FILE_UNAVAILABLE\nexit=1\n'
  exit 1
fi
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ "$line" =~ $SAFE_PHASE_RE || "$line" =~ $SAFE_DIAGNOSTIC_RE ]]; then
    printf '%s\n' "$line" >> "$SANITIZED"
    sanitized_lines=$((sanitized_lines + 1))
  elif [[ "$line" =~ $SAFE_EXIT_RE ]]; then
    :
  else
    output_invalid=1
    break
  fi
done < "$CAPTURE"
if (( output_invalid )); then
  printf 'phase=output-capture|error_code=OUTPUT_REJECTED\n' > "$SANITIZED"
  runner_status=1
  sanitized_lines=1
elif (( sanitized_lines == 0 )); then
  printf 'phase=output-capture|error_code=NO_SANITIZED_OUTPUT\n' > "$SANITIZED"
  runner_status=1
fi
printf 'exit=%s\n' "$runner_status" >> "$SANITIZED"
if ! /usr/bin/mv -- "$SANITIZED" "$EVIDENCE" 2>/dev/null; then
  printf 'phase=output-persistence|error_code=WRITE_FAILED\nexit=1\n'
  exit 1
fi
/bin/cat -- "$EVIDENCE"
exit "$runner_status"
