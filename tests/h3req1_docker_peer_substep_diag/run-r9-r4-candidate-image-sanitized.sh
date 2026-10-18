#!/usr/bin/env bash
set -u -o pipefail

readonly PACKAGE='/tmp/h3req1-g03-validation-29d8fff9-r4'
readonly TOOLS='/tmp/h3req1-g03-validation-29d8fff9-r2.tools'
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly EXPECTED_WIP='55/270/0'
readonly IMAGE='sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63'
readonly IMAGE_TAG='studiamatch-h3req1:20261009-v3'
readonly CANDIDATE_ID='500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049'
readonly NODE_VOLUME='studiamatch_h3req1_node_modules'
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

[[ -d "$PACKAGE" && ! -L "$PACKAGE" && -d "$TOOLS" && ! -L "$TOOLS" ]] || fail r9-preflight PACKAGE_UNAVAILABLE
[[ "$(/usr/bin/stat -c '%a' "$PACKAGE" 2>/dev/null)" == 755 ]] || fail r9-preflight PACKAGE_MODE_MISMATCH
verify_hash "$PACKAGE/r4-package.sha256" 'ca30a43c990e45e634412219c9a28d964b410068671c499048e80f2ff8c9068b' || fail r9-preflight PACKAGE_HASH_MISMATCH
verify_hash "$PACKAGE/inputs.sha256" 'b57603e8e75eb456a71e10ca45326c13e281ecb9e99b056ed163757c2292e2be' || fail r9-preflight INPUT_MANIFEST_MISMATCH
verify_hash "$TOOLS/tools.sha256" '4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa' || fail r9-preflight TOOLS_MANIFEST_MISMATCH
(cd "$PACKAGE" && /usr/bin/sha256sum -c r4-package.sha256 >/dev/null 2>&1) || fail r9-preflight PACKAGE_HASH_MISMATCH
(cd "$PACKAGE" && /usr/bin/sha256sum -c inputs.sha256 >/dev/null 2>&1) || fail r9-preflight INPUT_MANIFEST_MISMATCH
(cd "$TOOLS" && /usr/bin/sha256sum -c tools.sha256 >/dev/null 2>&1) || fail r9-preflight TOOLS_MANIFEST_MISMATCH
printf 'phase=r9-preflight|error_code=OK\n'

if [[ "$(git -C "$ROOT" branch --show-current 2>/dev/null)" != "$EXPECTED_BRANCH" ||
      "$(git -C "$ROOT" rev-parse HEAD 2>/dev/null)" != "$EXPECTED_HEAD" ]]; then
  fail r9-candidate-identity MISMATCH
fi
wip_counts="$(python3 - "$ROOT" 2>/dev/null <<'PYWIP'
import subprocess
import sys

raw = subprocess.check_output(['git', '-C', sys.argv[1], 'status', '--porcelain=v1'])
entries = [entry for entry in raw.splitlines() if entry]
tracked = sum(entry[:2] != b'??' for entry in entries)
untracked = sum(entry[:2] == b'??' for entry in entries)
staged = sum(entry[:1] not in (b' ', b'?') for entry in entries)
print(f'{tracked}/{untracked}/{staged}')
PYWIP
)" || fail r9-candidate-identity WIP_READ_FAILED
[[ "$wip_counts" == "$EXPECTED_WIP" ]] || fail r9-candidate-identity WIP_MISMATCH

if ! python3 - "$ROOT" "$PACKAGE/inputs.sha256" 2>/dev/null <<'PYSOURCE'
import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = Path(sys.argv[2])
package_only = {'fetch-linters.sh', 'run-in-container.sh', 'run-r8.sh'}
rows = manifest.read_text(encoding='utf-8').splitlines()
if len(rows) != 71:
    raise SystemExit(1)
missing = set()
checked = 0
for row in rows:
    digest, relative = row.split('  ', 1)
    if not relative.startswith('./'):
        raise SystemExit(1)
    relative = relative[2:]
    path = root / relative
    if not path.is_file() or path.is_symlink():
        if relative in package_only and not path.exists():
            missing.add(relative)
            continue
        raise SystemExit(1)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise SystemExit(1)
    checked += 1
if checked != 68 or missing != package_only:
    raise SystemExit(1)
PYSOURCE
then
  fail r9-candidate-source SOURCE_DRIFT
fi
printf 'phase=r9-candidate-source|error_code=OK\n'

if ! endpoint="$(/usr/bin/docker --context default context inspect default --format '{{ .Endpoints.docker.Host }}' 2>/dev/null)"; then
  fail r9-context CHECK_FAILED
fi
[[ "$endpoint" == 'unix:///var/run/docker.sock' ]] || fail r9-context ENDPOINT_MISMATCH
if ! image_id="$(/usr/bin/docker --context default image inspect --format '{{.Id}}' "$IMAGE_TAG" 2>/dev/null)"; then
  fail r9-context IMAGE_READ_FAILED
fi
[[ "$image_id" == "$IMAGE" ]] || fail r9-context IMAGE_MISMATCH
if ! candidate="$(/usr/bin/docker --context default inspect --format '{{.Id}}|{{.Image}}|{{.Config.Image}}|{{.State.Status}}|{{.State.Health.Status}}|{{index .Config.Labels "com.docker.compose.project"}}|{{index .Config.Labels "com.docker.compose.service"}}' studiamatch-dev 2>/dev/null)"; then
  fail r9-context CANDIDATE_READ_FAILED
fi
[[ "$candidate" == "$CANDIDATE_ID|$IMAGE|$IMAGE_TAG|running|healthy|studiamatch-h3req1|app" ]] || fail r9-context CANDIDATE_MISMATCH
/usr/bin/docker --context default volume inspect "$NODE_VOLUME" >/dev/null 2>&1 || fail r9-context DEPENDENCY_VOLUME_UNAVAILABLE
printf 'phase=r9-context|error_code=OK\n'

if container_output="$(/usr/bin/docker --context default run --rm --pull=never --network=none --read-only \
  --user 1001:1001 --cap-drop=ALL --security-opt=no-new-privileges \
  --memory=512m --memory-swap=512m --cpus=1 --pids-limit=64 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m,uid=1001,gid=1001,mode=0700 \
  --tmpfs /lint-tools:rw,exec,nosuid,nodev,size=32m,uid=1001,gid=1001,mode=0700 \
  --tmpfs /scanner-fixture:rw,exec,nosuid,nodev,size=2m,uid=1001,gid=1001,mode=0700 \
  --mount "type=bind,src=$PACKAGE,dst=/validation,readonly" \
  --mount "type=bind,src=$TOOLS,dst=/validation-tools,readonly" \
  --mount "type=volume,src=$NODE_VOLUME,dst=/app/web/node_modules,readonly" \
  --workdir /validation --env PYTHONDONTWRITEBYTECODE=1 --env SCANNER_TEST_EXEC_ROOT=/scanner-fixture \
  --env HOME=/tmp --env NEXT_TELEMETRY_DISABLED=1 \
  --entrypoint bash "$IMAGE" -euc 'bash run-in-container-r4.sh' 2>/dev/null)"; then
  container_status=0
else
  container_status=$?
fi
if (( ${#container_output} > MAX_OUTPUT_BYTES )); then fail r9-output OUTPUT_REJECTED; fi

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
    'phase=r9-next-typegen|error_code=OK'|'phase=r9-next-typegen|error_code=CHECK_FAILED'|\
    'phase=r9-actionlint|error_code=OK'|'phase=r9-actionlint|error_code=CHECK_FAILED'|\
    'phase=r9-shellcheck|error_code=OK'|'phase=r9-shellcheck|error_code=CHECK_FAILED'|\
    'phase=r9-eslint|error_code=OK'|'phase=r9-eslint|error_code=CHECK_FAILED'|\
    'phase=r9-typescript|error_code=OK'|'phase=r9-typescript|error_code=CHECK_FAILED'|\
    'phase=r9-protected-workflow-tests|error_code=OK'|'phase=r9-protected-workflow-tests|error_code=CHECK_FAILED'|\
    'phase=r9-credential-scan|error_code=OK'|'phase=r9-credential-scan|error_code=CHECK_FAILED'|\
    'phase=r9-protected-path-guard|error_code=OK'|'phase=r9-protected-path-guard|error_code=CHECK_FAILED'|\
    exit=[0-9]|exit=[0-9][0-9]|exit=[0-9][0-9][0-9]) safe_output+="${line}"$'\n' ;;
    *) invalid_output=1; break ;;
  esac
done <<< "$container_output"
if (( invalid_output )); then fail r9-output OUTPUT_REJECTED; fi

expected_success=$'phase=r9-input-hashes|error_code=OK\nphase=r9-tool-hashes|error_code=OK\nphase=r9-tool-extraction|error_code=OK\nphase=r9-tool-versions|error_code=OK\nphase=r9-candidate-copy|error_code=OK\nphase=r9-npm-dependency-manifest|error_code=OK\nphase=r9-node-and-typescript-versions|error_code=OK\nphase=r9-next-typegen|error_code=OK\nphase=r9-actionlint|error_code=OK\nphase=r9-shellcheck|error_code=OK\nphase=r9-eslint|error_code=OK\nphase=r9-typescript|error_code=OK\nphase=r9-protected-workflow-tests|error_code=OK\nphase=r9-credential-scan|error_code=OK\nphase=r9-protected-path-guard|error_code=OK\n'
if (( container_status == 0 )); then
  if [[ "$safe_output" == "$expected_success" ]]; then
    printf '%s' "$safe_output"
    printf 'phase=r9-summary|error_code=ALL_CHECKS_OK\n'
    exit 0
  fi
  [[ -n "$safe_output" ]] && printf '%s' "$safe_output"
  fail r9-summary OUTPUT_MISMATCH
fi
if [[ -n "$safe_output" ]]; then printf '%s' "$safe_output"; else printf 'phase=r9-container-launch|error_code=CHECK_FAILED\n'; fi
[[ "$safe_output" == *$'exit='* ]] || printf 'exit=%s\n' "$container_status"
exit "$container_status"
