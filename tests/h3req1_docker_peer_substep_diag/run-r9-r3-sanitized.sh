#!/usr/bin/env bash
set -u -o pipefail

readonly PACKAGE='/tmp/h3req1-g03-validation-29d8fff9-r3'
readonly TOOLS='/tmp/h3req1-g03-validation-29d8fff9-r2.tools'
readonly IMAGE='sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0'
readonly MAX_OUTPUT_BYTES=2048

fail() {
  local phase="$1" code="$2" status="${3:-1}"
  printf 'phase=%s|error_code=%s\nexit=%s\n' "$phase" "$code" "$status"
  exit "$status"
}

verify_hash() {
  local file="$1" expected="$2" hash_line
  [[ -f "$file" && ! -L "$file" ]] || return 1
  hash_line="$(/usr/bin/sha256sum -- "$file" 2>/dev/null)" || return 1
  [[ "${hash_line%% *}" == "$expected" ]]
}

[[ -d "$PACKAGE" && ! -L "$PACKAGE" && -d "$TOOLS" && ! -L "$TOOLS" ]] || fail 'r9-preflight' 'PACKAGE_UNAVAILABLE'
[[ "$(/usr/bin/stat -c '%a' "$PACKAGE" 2>/dev/null)" == '755' ]] || fail 'r9-preflight' 'PACKAGE_MODE_MISMATCH'
verify_hash "$PACKAGE/r3-package.sha256" '688e81efaae70a841a64cd4c0a074ae3c76c355f5ef9bc77756cff9ad607fc02' || fail 'r9-preflight' 'PACKAGE_HASH_MISMATCH'
verify_hash "$PACKAGE/inputs.sha256" '6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee' || fail 'r9-preflight' 'INPUT_MANIFEST_MISMATCH'
verify_hash "$TOOLS/tools.sha256" '4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa' || fail 'r9-preflight' 'TOOLS_MANIFEST_MISMATCH'
(cd "$PACKAGE" && /usr/bin/sha256sum -c r3-package.sha256 >/dev/null 2>&1) || fail 'r9-preflight' 'PACKAGE_HASH_MISMATCH'
(cd "$PACKAGE" && /usr/bin/sha256sum -c inputs.sha256 >/dev/null 2>&1) || fail 'r9-preflight' 'INPUT_MANIFEST_MISMATCH'
(cd "$TOOLS" && /usr/bin/sha256sum -c tools.sha256 >/dev/null 2>&1) || fail 'r9-preflight' 'TOOLS_MANIFEST_MISMATCH'

if ! endpoint="$(/usr/bin/docker --context default context inspect default --format '{{ .Endpoints.docker.Host }}' 2>/dev/null)"; then
  fail 'r9-context' 'CHECK_FAILED'
fi
[[ "$endpoint" == 'unix:///var/run/docker.sock' ]] || fail 'r9-context' 'ENDPOINT_MISMATCH'
printf 'phase=r9-context|error_code=OK\n'

if container_output="$(/usr/bin/docker --context default run --rm --pull=never --network=none --read-only \
  --user 1001:1001 --cap-drop=ALL --security-opt=no-new-privileges \
  --memory=512m --memory-swap=512m --cpus=1 --pids-limit=64 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m,uid=1001,gid=1001,mode=0700 \
  --tmpfs /lint-tools:rw,exec,nosuid,nodev,size=32m,uid=1001,gid=1001,mode=0700 \
  --tmpfs /scanner-fixture:rw,exec,nosuid,nodev,size=2m,uid=1001,gid=1001,mode=0700 \
  --mount "type=bind,src=$PACKAGE,dst=/validation,readonly" \
  --mount "type=bind,src=$TOOLS,dst=/validation-tools,readonly" \
  --workdir /validation --env PYTHONDONTWRITEBYTECODE=1 --env SCANNER_TEST_EXEC_ROOT=/scanner-fixture \
  --entrypoint bash "$IMAGE" -euc 'bash run-in-container-r3.sh' 2>/dev/null)"; then
  container_status=0
else
  container_status=$?
fi

if (( ${#container_output} > MAX_OUTPUT_BYTES )); then
  fail 'r9-output' 'OUTPUT_REJECTED'
fi

safe_output=''
invalid_output=0
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  case "$line" in
    'phase=r9-input-hashes|error_code=OK'|'phase=r9-input-hashes|error_code=CHECK_FAILED'|\
    'phase=r9-tool-hashes|error_code=OK'|'phase=r9-tool-hashes|error_code=CHECK_FAILED'|\
    'phase=r9-tool-extraction|error_code=OK'|'phase=r9-tool-extraction|error_code=CHECK_FAILED'|\
    'phase=r9-tool-versions|error_code=OK'|'phase=r9-tool-versions|error_code=CHECK_FAILED'|\
    'phase=r9-candidate-copy|error_code=OK'|'phase=r9-candidate-copy|error_code=CHECK_FAILED'|\
    'phase=r9-npm-dependency-manifest|error_code=OK'|'phase=r9-npm-dependency-manifest|error_code=CHECK_FAILED'|\
    'phase=r9-node-and-typescript-versions|error_code=OK'|'phase=r9-node-and-typescript-versions|error_code=CHECK_FAILED'|\
    'phase=r9-actionlint|error_code=OK'|'phase=r9-actionlint|error_code=CHECK_FAILED'|\
    'phase=r9-shellcheck|error_code=OK'|'phase=r9-shellcheck|error_code=CHECK_FAILED'|\
    'phase=r9-eslint|error_code=OK'|'phase=r9-eslint|error_code=CHECK_FAILED'|\
    'phase=r9-typescript|error_code=OK'|'phase=r9-typescript|error_code=CHECK_FAILED'|\
    'phase=r9-protected-workflow-tests|error_code=OK'|'phase=r9-protected-workflow-tests|error_code=CHECK_FAILED'|\
    'phase=r9-credential-scan|error_code=OK'|'phase=r9-credential-scan|error_code=CHECK_FAILED'|\
    'phase=r9-protected-path-guard|error_code=OK'|'phase=r9-protected-path-guard|error_code=CHECK_FAILED'|\
    exit=[0-9]|exit=[0-9][0-9]|exit=[0-9][0-9][0-9])
      safe_output+="${line}"$'\n'
      ;;
    *) invalid_output=1; break ;;
  esac
done <<< "$container_output"

if (( invalid_output )); then
  fail 'r9-output' 'OUTPUT_REJECTED'
fi

expected_success=$'phase=r9-input-hashes|error_code=OK\nphase=r9-tool-hashes|error_code=OK\nphase=r9-tool-extraction|error_code=OK\nphase=r9-tool-versions|error_code=OK\nphase=r9-candidate-copy|error_code=OK\nphase=r9-npm-dependency-manifest|error_code=OK\nphase=r9-node-and-typescript-versions|error_code=OK\nphase=r9-actionlint|error_code=OK\nphase=r9-shellcheck|error_code=OK\nphase=r9-eslint|error_code=OK\nphase=r9-typescript|error_code=OK\nphase=r9-protected-workflow-tests|error_code=OK\nphase=r9-credential-scan|error_code=OK\nphase=r9-protected-path-guard|error_code=OK'
expected_success+=$'\n'

if (( container_status == 0 )); then
  if [[ "$safe_output" == "$expected_success" ]]; then
    printf '%s' "$safe_output"
    printf 'phase=r9-summary|error_code=ALL_CHECKS_OK\n'
    exit 0
  fi
  [[ -n "$safe_output" ]] && printf '%s' "$safe_output"
  fail 'r9-summary' 'OUTPUT_MISMATCH'
fi

if [[ -n "$safe_output" ]]; then
  printf '%s' "$safe_output"
else
  printf 'phase=r9-container-launch|error_code=CHECK_FAILED\n'
fi
if [[ "$safe_output" != *$'exit='* ]]; then
  printf 'exit=%s\n' "$container_status"
fi
exit "${container_status:-1}"
