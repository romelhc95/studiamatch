#!/usr/bin/env bash
set -u -o pipefail

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/f1_template_expression_probe_v10_once.py"
readonly RUNNER_SHA256='3721861d4506ed778d2166fda952d6bfffc08072158c8d1ea1050ac030eb23d4'
readonly SAFE_LINE_RE='^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$'

fail() {
  printf 'phase=jit-preflight|error_code=%s\n' "$1"
  exit 1
}

if (( EUID == 0 )); then
  fail 'RUN_AS_WSL_USER'
fi
if [[ ! -t 0 ]]; then
  fail 'INTERACTIVE_TTY_REQUIRED'
fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout || ! -x /usr/bin/python3 ]]; then
  fail 'RUNTIME_UNAVAILABLE'
fi

hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || fail 'RUNNER_HASH_FAILED'
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  fail 'RUNNER_HASH_MISMATCH'
fi

runner_output=''
if runner_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 420s \
  /usr/bin/env -i HOME=/home/romel PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 \
  /usr/bin/python3 -B "$RUNNER" 2>/dev/null)"; then
  runner_status=0
else
  runner_status=$?
fi

safe_output=''
invalid_output=0
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ ! "$line" =~ $SAFE_LINE_RE ]]; then
    invalid_output=1
    break
  fi
  phase="${line#phase=}"
  phase="${phase%%|*}"
  code="${line#*|error_code=}"
  case "$phase" in
    jit-preflight|preflight|prior-endpoint-attestation|image-id-isolated|image-volumes-isolated|synthetic-image-read|classifier-v8-focused-tests|probe-container-start|probe-container-cleanup|probe-summary|\
    template-probe-id|template-probe-name|template-probe-state-status|template-probe-state-exit-code|template-probe-state-oom-killed|\
    template-probe-label-jit|template-probe-label-manifest|template-probe-label-run|template-probe-network-mode|template-probe-readonly-rootfs|\
    template-probe-user|template-probe-cap-drop|template-probe-security-opt|template-probe-memory|template-probe-memory-swap|\
    template-probe-nano-cpus|template-probe-pids-limit|template-probe-restart-policy|template-probe-tmpfs-snapshot|\
    template-probe-tmpfs-count|template-probe-log-config|template-probe-port-bindings|template-probe-shm-size|\
    template-probe-binds|template-probe-mounts)
      ;;
    *)
      invalid_output=1
      break
      ;;
  esac
  case "$code" in
    OK|RUN_AS_WSL_USER|INTERACTIVE_TTY_REQUIRED|RUNTIME_UNAVAILABLE|RUNNER_HASH_FAILED|RUNNER_HASH_MISMATCH|\
    SOURCE_OR_EVIDENCE_MISMATCH|CLASSIFIER_LOAD_FAILED|ENDPOINT_MISMATCH|DESKTOP_HELPER_LOAD_FAILED|DIAGNOSTIC_FAILED|\
    IMAGE_NOT_FOUND|DOCKER_ACCESS_DENIED|DOCKER_ENGINE_UNAVAILABLE|IMAGE_INSPECT_TEMPLATE_ERROR|IMAGE_INSPECT_FAILED|\
    IMAGE_INSPECT_OUTPUT_LIMIT|IMAGE_ERROR_OUTPUT_LIMIT|IMAGE_METADATA_INVALID|IMAGE_DIGEST_MISMATCH|\
    SYNTHETIC_IMAGE_UNAVAILABLE|SYNTHETIC_IMAGE_VOLUMES_PRESENT|V8_TEST_CONTAINER_FAILED|V8_TEST_RESULT_INVALID|\
    SYNTHETIC_CONTAINER_START_FAILED|SYNTHETIC_CONTAINER_ID_INVALID|TEMPORARY_CONTAINER_STOP_FAILED|\
    TEMPLATE_SHAPE_INVALID|FIELDS_FAILED|ALL_FIELDS_OK|INSPECT_TEMPLATE_ERROR|INSPECT_TEMPLATE_PARSE_ERROR|\
    INSPECT_TEMPLATE_EVALUATION_ERROR|CONTAINER_NOT_FOUND|DOCKER_READ_FAILED|OUTPUT_LIMIT|ERROR_OUTPUT_LIMIT|\
    COMMAND_START_FAILED|ETIMEDOUT|EACCES|EAGAIN|EBUSY|ECONNABORTED|ECONNREFUSED|ECONNRESET|EEXIST|EFAULT|\
    EINTR|EINVAL|EIO|EISDIR|EMFILE|EMLINK|ENAMETOOLONG|ENFILE|ENOBUFS|ENODEV|ENOENT|ENOMEM|ENOSPC|ENOSYS|\
    ENOTDIR|ENOTSOCK|ENXIO|EOPNOTSUPP|EPIPE|EPERM|EROFS|ESPIPE|ETXTBSY|EOTHER)
      ;;
    *)
      invalid_output=1
      break
      ;;
  esac
  safe_output+="${line}"$'\n'
done <<< "$runner_output"

if (( invalid_output )); then
  printf 'phase=output-capture|error_code=OUTPUT_REJECTED\n'
  runner_status=1
elif [[ -z "$safe_output" ]]; then
  printf 'phase=output-capture|error_code=NO_SANITIZED_OUTPUT\n'
  runner_status=1
else
  printf '%s' "$safe_output"
fi

IFS= read -r -p 'Conserva solo las fases y códigos; presiona Enter para cerrar: ' _ || true
exit "$runner_status"
