#!/usr/bin/env bash
set -Eeuo pipefail

sanitize_runtime_line() {
  local line=${1-} key_pattern validation_pattern
  key_pattern='(durableObjectsPersist|workers|name|modules|compatibilityDate|compatibilityFlags|bindings|serviceBindings|durableObjects|log|ADMIN_ALLOWED_HOSTS|ADMIN_BFF_ALLOW_LOCAL_AUTH_MOCK|ADMIN_BFF_SAFE_SUSPEND|ADMIN_SESSION_ACTIVITY_HMAC_KEY|ADMIN_RPC_GATEWAY_HMAC_KEY|ADMIN_RPC_GATEWAY_KEY_ID|ADMIN_QUOTA_HMAC_KEY|SUPABASE_URL|NEXT_SUPABASE_PUBLISHABLE_KEY|ASSETS|ADMIN_QUOTA|ADMIN_QUOTA_COUNTER|AdminQuotaCounter|type|path|contents|other)'
  validation_pattern="^runtime-validation-issue=(scope:shared\\|index:na|scope:worker\\|index:[0-2])\\|path:(root|${key_pattern}(\\.${key_pattern}){0,7})\\|code:(unrecognized_keys|invalid_type|invalid_value|invalid_union|too_small|too_big|invalid_format|custom|other)\\|keys:(none|${key_pattern}(,${key_pattern})*)$"
  case "$line" in
    'phase=runtime-diagnostic-synthetic|error_code=PASS' \
      |'runtime-stage=dependency-roots-present' \
      |'runtime-stage=miniflare-constructor-validation' \
      |'runtime-stage=runtime-uncaught-error' \
      |'runtime-stage=runtime-ready' \
      |'runtime-dependency-digests=PASS|groups=2' \
      |'runtime-last-stage=runtime-process-start' \
      |'runtime-last-stage=dependency-roots-present' \
      |'runtime-last-stage=miniflare-constructor-validation' \
      |'runtime-last-stage=runtime-uncaught-error' \
      |'runtime-last-stage=runtime-ready' \
      |'runtime-stop=grace-period-expired; signal=SIGKILL' \
      |'smoke=PASS workerd-pages-healthz=true pages-worker=root-asset edge-runtime=not-started database=not-started' \
      |'smoke=NO-GO reason=runtime-exit-not-clean')
      printf '%s\n' "$line"
      return 0
      ;;
  esac

  if [[ "$line" =~ ^healthz=PASS\ workerd=true\ pages-worker=root-asset\ attempts=[0-9]{1,2}$ \
    || "$line" =~ ^healthz=NO-GO\ reason=runtime-not-ready\ attempts=[0-9]{1,2}$ ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ ^runtime-error-class=(PERMISSION|MODULE_RESOLUTION|ADDRESS_IN_USE|RESOURCE_EXHAUSTION|TLS|WORKERD|ASSERTION|MISSING_FILE|ERROR|ASSERTIONERROR|TYPEERROR|REFERENCEERROR|SYNTAXERROR|RANGEERROR|SENSITIVE_REDACTED|MINIFLARECOREERROR|MINIFLAREERROR|OTHER_ERROR|UNCLASSIFIED)$ ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ ^runtime-spawn-error=(EACCES|EADDRINUSE|EAGAIN|EMFILE|ENFILE|ENOENT|ENOMEM|ENOSPC|EPERM|ETIMEDOUT|ERR_MODULE_NOT_FOUND|ERR_PACKAGE_PATH_NOT_EXPORTED|ERR_WORKER_INIT|UNCLASSIFIED)$ ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ ^runtime-project-frame=line:[0-9]{1,5}:column:[0-9]{1,5}$ ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ ^runtime-miniflare-frame=line:[0-9]{1,5}:column:[0-9]{1,5}$ ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ ^runtime-missing-module=(package-id:p[0-9]{6}|unlisted-package|node-builtin|relative-module|unclassified)\|from=(tools|web-deps|candidate-tests|candidate-web|other)$ ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ ^runtime-missing-module-shape=(message-empty|package-import|package-no-importer|module-import|module-no-importer|other-message)$ ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ $validation_pattern ]]; then
    printf '%s\n' "$line"
  elif [[ "$line" =~ ^runtime-error-code=(EACCES|EADDRINUSE|EAGAIN|EMFILE|ENFILE|ENOENT|ENOMEM|ENOSPC|EPERM|ETIMEDOUT|ERR_ADDRESS_IN_USE|ERR_CYCLIC|ERR_DEAD_LETTER_QUEUE_CYCLE|ERR_DIFFERENT_PREVENT_EVICTION|ERR_DIFFERENT_S3_CREDENTIALS|ERR_DIFFERENT_STORAGE_BACKEND|ERR_DIFFERENT_UNIQUE_KEYS|ERR_DISPOSED|ERR_DUPLICATE_NAME|ERR_FUTURE_COMPATIBILITY_DATE|ERR_INFIX_WILDCARD|ERR_INVALID_WRAPPED|ERR_MISSING_EXPLORER_UI|ERR_MISSING_INSPECTOR_PROXY_PORT|ERR_MODULE_DYNAMIC_SPEC|ERR_MODULE_NOT_FOUND|ERR_MODULE_PARSE|ERR_MODULE_RULE|ERR_MODULE_STRING_SCRIPT|ERR_MULTIPLE_CONSUMERS|ERR_MULTIPLE_OUTBOUNDS|ERR_NO_WORKERS|ERR_PACKAGE_PATH_NOT_EXPORTED|ERR_PERSIST_UNSUPPORTED|ERR_PLUGIN_LOADING_FAILED|ERR_QUERY_STRING|ERR_RUNTIME_FAILURE|ERR_VALIDATION|ERR_WORKER_INIT|UNCLASSIFIED)$ ]]; then
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
  local actual expected class_capture shape_capture
  actual="$(printf '%s\n' \
    'runtime-project-frame=line:800:column:3' \
    'runtime-miniflare-frame=line:142:column:7' \
    'runtime-miniflare-frame=line:142:column:7 token=synthetic-secret' \
    'runtime-stage=miniflare-constructor-validation' \
    'runtime-validation-issue=scope:worker|index:0|path:serviceBindings|code:unrecognized_keys|keys:serviceBindings' \
    'runtime-validation-issue=scope:worker|index:0|path:bindings|code:unrecognized_keys|keys:ADMIN_SESSION_ACTIVITY_HMAC_KEY' \
    'runtime-validation-issue=scope:worker|index:0|path:bindings|code:unrecognized_keys|keys:ADMIN_SESSION_ACTIVITY_HMAC_KEY=synthetic-secret' \
    'runtime-validation-issue=scope:worker|index:0|path:serviceBindings|code:unrecognized_keys|keys:token=synthetic-secret' \
    'runtime-validation-issue=scope:worker|index:0|path:serviceBindings|code:unrecognized_keys|keys:SUPABASE_SECRET_KEY' \
    'runtime-error-code=ERR_RUNTIME_FAILURE' \
    'runtime-error-code=API_SECRET_ABC' \
    'runtime-project-frame=line:800:column:3 token=synthetic-secret' \
    'runtime-error-class=OTHER_ERROR' \
    'runtime-error-class=OTHER_ERROR token=synthetic-secret' \
    'runtime-missing-module=package-id:p000125|from=tools' \
    'runtime-missing-module=package-id:p000125|from=tools token=synthetic-secret' \
    'runtime-probe-error=type:MINIFLARECOREERROR|code:UNCLASSIFIED' \
    'runtime-probe-error=type:MINIFLAREERROR|code:ERR_WORKER_INIT' \
    'runtime-probe-error=type:MINIFLARECOREERROR|code:ERR_WORKER_INIT token=synthetic-secret' \
    'runtime-probe-error=type:ERROR|code:API_SECRET_ABC' \
    'runtime-spawn-error=ENOENT' \
    'runtime-spawn-error=SUPABASE_SECRET_KEY' \
    'runtime-dependency-digests=PASS|groups=2' \
    'runtime-dependency-digests=PASS|groups=2 token=synthetic-secret' \
    'healthz=PASS workerd=true pages-worker=root-asset attempts=3' \
    'healthz=PASS workerd=true pages-worker=root-asset attempts=3 token=synthetic-secret' \
    | sanitize_runtime_output)"
  expected=$'runtime-project-frame=line:800:column:3\nruntime-miniflare-frame=line:142:column:7\nruntime-output-class=unclassified-line-suppressed\nruntime-stage=miniflare-constructor-validation\nruntime-validation-issue=scope:worker|index:0|path:serviceBindings|code:unrecognized_keys|keys:serviceBindings\nruntime-validation-issue=scope:worker|index:0|path:bindings|code:unrecognized_keys|keys:ADMIN_SESSION_ACTIVITY_HMAC_KEY\nruntime-output-class=unclassified-line-suppressed\nruntime-output-class=unclassified-line-suppressed\nruntime-output-class=unclassified-line-suppressed\nruntime-error-code=ERR_RUNTIME_FAILURE\nruntime-output-class=unclassified-line-suppressed\nruntime-output-class=unclassified-line-suppressed\nruntime-error-class=OTHER_ERROR\nruntime-output-class=unclassified-line-suppressed\nruntime-missing-module=package-id:p000125|from=tools\nruntime-output-class=unclassified-line-suppressed\nruntime-probe-error=type:MINIFLARECOREERROR|code:UNCLASSIFIED\nruntime-probe-error=type:MINIFLAREERROR|code:ERR_WORKER_INIT\nruntime-output-class=unclassified-line-suppressed\nruntime-output-class=unclassified-line-suppressed\nruntime-spawn-error=ENOENT\nruntime-output-class=unclassified-line-suppressed\nruntime-dependency-digests=PASS|groups=2\nruntime-output-class=unclassified-line-suppressed\nhealthz=PASS workerd=true pages-worker=root-asset attempts=3\nruntime-output-class=unclassified-line-suppressed\nruntime-output-sanitization=allowlisted-events-only'
  if [[ "$actual" != "$expected" ]]; then
    diff -u <(printf '%s\n' "$expected") <(printf '%s\n' "$actual") || true
    return 1
  fi
  class_capture="$(printf '%s\n' \
    'runtime-error-class=UNCLASSIFIED' \
    'runtime-error-class=UNCLASSIFIED token=synthetic-secret' \
    | sanitize_runtime_output)"
  [[ "$class_capture" == $'runtime-error-class=UNCLASSIFIED\nruntime-output-class=unclassified-line-suppressed\nruntime-output-sanitization=allowlisted-events-only' ]] || return 1
  shape_capture="$(printf '%s\n' \
    'runtime-missing-module-shape=package-no-importer' \
    'runtime-missing-module-shape=package-no-importer token=synthetic-secret' \
    | sanitize_runtime_output)"
  [[ "$shape_capture" == $'runtime-missing-module-shape=package-no-importer\nruntime-output-class=unclassified-line-suppressed\nruntime-output-sanitization=allowlisted-events-only' ]] || return 1
  printf 'phase=runtime-output-filter-synthetic|error_code=PASS\n'
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  case "${1:-}" in
    --self-test) [[ $# -eq 1 ]] || exit 64; self_test ;;
    --sanitize) [[ $# -eq 1 ]] || exit 64; sanitize_runtime_output ;;
    *) exit 64 ;;
  esac
fi
