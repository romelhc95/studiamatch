#!/usr/bin/env bash
set -Eeuo pipefail

sanitize_runtime_line() {
  local line=${1-}
  case "$line" in
    'phase=runtime-diagnostic-synthetic|error_code=PASS' \
      |'runtime-stage=dependency-roots-present' \
      |'runtime-stage=runtime-ready' \
      |'runtime-last-stage=runtime-process-start' \
      |'runtime-last-stage=dependency-roots-present' \
      |'runtime-last-stage=runtime-ready' \
      |'runtime-stop=grace-period-expired; signal=SIGKILL' \
      |'smoke=PASS workerd-pages-healthz=true edge-runtime=not-started database=not-started' \
      |'smoke=NO-GO reason=runtime-exit-not-clean')
      printf '%s\n' "$line"
      return 0
      ;;
  esac

  if [[ "$line" =~ ^healthz=PASS\ workerd=true\ attempts=[0-9]{1,2}$ \
    || "$line" =~ ^healthz=NO-GO\ reason=runtime-not-ready\ attempts=[0-9]{1,2}$ ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ ^runtime-error-class=(PERMISSION|MODULE_RESOLUTION|ADDRESS_IN_USE|RESOURCE_EXHAUSTION|TLS|WORKERD|ASSERTION|MISSING_FILE|ERROR|ASSERTIONERROR|TYPEERROR|REFERENCEERROR|SYNTAXERROR|RANGEERROR|SENSITIVE_REDACTED|MINIFLARECOREERROR|MINIFLAREERROR|OTHER_ERROR)$ ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ ^runtime-spawn-error=(EACCES|EADDRINUSE|EAGAIN|EMFILE|ENFILE|ENOENT|ENOMEM|ENOSPC|EPERM|ETIMEDOUT|ERR_MODULE_NOT_FOUND|ERR_PACKAGE_PATH_NOT_EXPORTED|ERR_WORKER_INIT|UNCLASSIFIED)$ ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ ^runtime-project-frame=line:[0-9]{1,5}:column:[0-9]{1,5}$ ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ ^runtime-exit=code:[0-9]{1,3}\ signal:none$ \
    || "$line" =~ ^runtime-exit=code:null\ signal:SIG[A-Z0-9]+$ ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ ^runtime-probe-error=type:(ERROR|ASSERTIONERROR|TYPEERROR|REFERENCEERROR|SYNTAXERROR|RANGEERROR|MINIFLARECOREERROR|MINIFLAREERROR|UNCLASSIFIED)\|code:(EACCES|EADDRINUSE|EAGAIN|EMFILE|ENFILE|ENOENT|ENOMEM|ENOSPC|EPERM|ETIMEDOUT|ERR_MODULE_NOT_FOUND|ERR_PACKAGE_PATH_NOT_EXPORTED|ERR_WORKER_INIT|UNCLASSIFIED)$ ]]; then
    printf '%s\n' "$line"
  else
    printf 'runtime-output-class=unclassified-line-suppressed\n'
  fi
}

sanitize_runtime_output() {
  local line
  while IFS= read -r line || [[ -n "$line" ]]; do
    sanitize_runtime_line "$line"
  done
  printf 'runtime-output-sanitization=allowlisted-events-only\n'
}

self_test() {
  local actual expected
  actual="$(printf '%s\n' \
    'runtime-project-frame=line:800:column:3' \
    'runtime-project-frame=line:800:column:3 token=synthetic-secret' \
    'runtime-error-class=OTHER_ERROR' \
    'runtime-error-class=OTHER_ERROR token=synthetic-secret' \
    'runtime-probe-error=type:MINIFLARECOREERROR|code:UNCLASSIFIED' \
    'runtime-probe-error=type:MINIFLAREERROR|code:ERR_WORKER_INIT' \
    'runtime-probe-error=type:MINIFLARECOREERROR|code:ERR_WORKER_INIT token=synthetic-secret' \
    'runtime-probe-error=type:ERROR|code:API_SECRET_ABC' \
    'runtime-spawn-error=ENOENT' \
    'runtime-spawn-error=SUPABASE_SECRET_KEY' \
    'healthz=PASS workerd=true attempts=3' \
    'healthz=PASS workerd=true attempts=3 token=synthetic-secret' \
    | sanitize_runtime_output)"
  expected=$'runtime-project-frame=line:800:column:3\nruntime-output-class=unclassified-line-suppressed\nruntime-error-class=OTHER_ERROR\nruntime-output-class=unclassified-line-suppressed\nruntime-probe-error=type:MINIFLARECOREERROR|code:UNCLASSIFIED\nruntime-probe-error=type:MINIFLAREERROR|code:ERR_WORKER_INIT\nruntime-output-class=unclassified-line-suppressed\nruntime-output-class=unclassified-line-suppressed\nruntime-spawn-error=ENOENT\nruntime-output-class=unclassified-line-suppressed\nhealthz=PASS workerd=true attempts=3\nruntime-output-class=unclassified-line-suppressed\nruntime-output-sanitization=allowlisted-events-only'
  [[ "$actual" == "$expected" ]] || return 1
  printf 'phase=runtime-output-filter-synthetic|error_code=PASS\n'
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  [[ "${1:-}" == '--self-test' && $# -eq 1 ]] || exit 64
  self_test
fi
