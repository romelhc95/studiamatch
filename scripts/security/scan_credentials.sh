#!/usr/bin/env bash
# Scans repository files, staged blobs, explicit files, or a git diff for credential-like values.

set -eu

PATTERNS="eyJhbG[A-Za-z0-9_-]{10,}|sb_publishable_[A-Za-z0-9_-]{20,}|sb_secret_[A-Za-z0-9_-]{10,}|sbp_[A-Za-z0-9_-]{10,}|sk-(proj-)?[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16}|ghs_[A-Za-z0-9]{20,}|opencode_[A-Za-z0-9_-]{20,}|oc_[A-Za-z0-9_-]{30,}|(CF_API_TOKEN|SUPABASE_ACCESS_TOKEN|RESEND_API_KEY|NEXT_SUPABASE_SECRET_KEY|FREE_NEXT_SUPABASE_SECRET_KEY|PRO_NEXT_SUPABASE_SECRET_KEY)[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9_./+=-]{20,}|OPENCODE_API_KEY[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9_-]{20,}"
SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
TMP_ROOT=${TMPDIR:-/tmp}
tmp_dir=''

fail() {
    printf '%s\n' "credential scan failed: $1" >&2 || true
    return 2
}

cleanup() {
    status=$?
    trap - EXIT
    if [ -n "$tmp_dir" ]; then
        if [ ! -d "$tmp_dir" ] || [ -L "$tmp_dir" ] \
            || ! rm -f -- "$tmp_dir/list" "$tmp_dir/changed" "$tmp_dir/staged" "$tmp_dir/path" "$tmp_dir/worktree" \
            || ! rmdir -- "$tmp_dir" 2>/dev/null; then
            printf '%s\n' 'credential scan failed: private temporary cleanup failed' >&2 || true
            [ "$status" -ne 0 ] || status=2
        fi
    fi
    exit "$status"
}

umask 077
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
if ! tmp_dir=$(mktemp -d "$TMP_ROOT/studiamatch-credential-scan.XXXXXXXX" 2>/dev/null); then
    fail 'cannot create private temporary directory'
    exit 2
fi
case "$tmp_dir" in
    "$TMP_ROOT"/studiamatch-credential-scan.*) ;;
    *) fail 'temporary directory path is unexpected'; exit 2 ;;
esac
  if [ ! -d "$tmp_dir" ] || [ -L "$tmp_dir" ]; then
    fail 'private temporary directory is invalid'
    exit 2
  fi

scan_matches() {
    input=$1
    if LC_ALL=C grep -aE "$PATTERNS" -- "$input" >/dev/null 2>/dev/null; then
        return 0
    else
        status=$?
        if [ "$status" -eq 1 ]; then
            return 1
        fi
        fail 'grep could not read or scan an input'
        return 2
    fi
}

scan_stream() {
    input=$1
    display_path=$2
    safe_display=$(printf '%s' "$display_path" | LC_ALL=C sed -E "s/($PATTERNS)/[REDACTED]/g") \
        || { fail 'could not sanitize an input path'; return 2; }
    safe_display=$(printf '%s' "$safe_display" | LC_ALL=C tr '\001-\037\177' '?') \
        || { fail 'could not normalize an input path'; return 2; }
    if scan_matches "$input"; then
        if ! printf '%s: [REDACTED credential-like value]\n' "$safe_display" >&2; then
            fail 'could not write redacted findings'
            return 2
        fi
        return 1
    else
        status=$?
        [ "$status" -eq 1 ] && return 0
        return 2
    fi
}

scan_file() {
    file=$1
    if [ ! -f "$file" ] || [ -L "$file" ] || [ ! -r "$file" ]; then
        fail 'input file is missing or unreadable'
        return 2
    fi
    if ! printf '%s' "$file" >"$tmp_dir/path"; then
        fail 'could not prepare a private path input'
        return 2
    fi
    if scan_stream "$tmp_dir/path" "$file"; then
        :
    else
        return $?
    fi
    scan_stream "$file" "$file"
}

scan_worktree_file() {
    file=$1
    if ! python3 "$SCRIPT_DIR/scan_worktree_file.py" "$worktree_root" "$file" \
        >"$tmp_dir/worktree" 2>/dev/null; then
        fail 'could not securely read a tracked worktree path'
        return 2
    fi
    scan_stream "$tmp_dir/worktree" "$file"
}

scan_tree() {
    if ! worktree_root=$(git rev-parse --show-toplevel 2>/dev/null); then
        fail 'git could not resolve the worktree root'
        return 2
    fi
    if ! git ls-files -z >"$tmp_dir/list" 2>/dev/null; then
        fail 'git could not enumerate tracked files'
        return 2
    fi
    while :; do
        file=''
        if IFS= read -r -d '' file; then
            [ -n "$file" ] || { fail 'git returned an empty tracked path'; return 2; }
        else
            [ -z "$file" ] && break
            fail 'git returned a malformed tracked path list'
            return 2
        fi
        if ! printf '%s' "$file" >"$tmp_dir/path"; then
            fail 'could not prepare a private path input'
            return 2
        fi
        if scan_stream "$tmp_dir/path" "$file"; then :; else return $?; fi
        if scan_worktree_file "$file"; then :; else return $?; fi
        if ! git show ":$file" >"$tmp_dir/staged" 2>/dev/null; then
            fail 'git could not read a tracked index blob'
            return 2
        fi
        if scan_stream "$tmp_dir/staged" "$file"; then :; else return $?; fi
    done <"$tmp_dir/list"
    return 0
}

scan_diff() {
    base=$1
    head=$2
    if ! git rev-parse --verify "$head^{commit}" >/dev/null 2>&1; then
        fail 'git could not resolve the diff head commit'
        return 2
    fi

    if git rev-parse --verify "$base^{commit}" >/dev/null 2>&1; then
        if ! git rev-list --reverse "$base..$head" >"$tmp_dir/list" 2>/dev/null; then
            fail 'git could not enumerate commits after the diff base'
            return 2
        fi
    elif git rev-parse --verify "$base^{tree}" >/dev/null 2>&1; then
        if ! git rev-list --reverse "$head" >"$tmp_dir/list" 2>/dev/null; then
            fail 'git could not enumerate commits from the tree diff base'
            return 2
        fi
    else
        fail 'git could not resolve the diff base as a commit or tree'
        return 2
    fi

    while :; do
        commit=''
        if IFS= read -r commit; then
            [ -n "$commit" ] || { fail 'git returned an empty commit id'; return 2; }
        else
            [ -z "$commit" ] && break
            fail 'git returned a malformed commit list'
            return 2
        fi

        if ! git diff-tree --root -m --no-commit-id --name-only --diff-filter=ACMRT -r -z \
            "$commit" >"$tmp_dir/changed" 2>/dev/null; then
            fail 'git could not enumerate changed paths in a commit'
            return 2
        fi

        while :; do
            file=''
            if IFS= read -r -d '' file; then
                [ -n "$file" ] || { fail 'git returned an empty changed path'; return 2; }
            else
                [ -z "$file" ] && break
                fail 'git returned a malformed changed path list'
                return 2
            fi
            if ! printf '%s' "$file" >"$tmp_dir/path"; then
                fail 'could not prepare a private path input'
                return 2
            fi
            if scan_stream "$tmp_dir/path" "$file"; then :; else return $?; fi
            if ! git show "$commit:$file" >"$tmp_dir/staged" 2>/dev/null; then
                fail 'git could not read a changed commit blob'
                return 2
            fi
            if scan_stream "$tmp_dir/staged" "$file"; then :; else return $?; fi
        done <"$tmp_dir/changed"
    done <"$tmp_dir/list"
    return 0
}

scan_staged() {
    if ! git diff --cached --name-only --diff-filter=ACMRT -z >"$tmp_dir/list" 2>/dev/null; then
        fail 'git could not enumerate staged files'
        return 2
    fi
    while :; do
        file=''
        if IFS= read -r -d '' file; then
            [ -n "$file" ] || { fail 'git returned an empty staged path'; return 2; }
        else
            [ -z "$file" ] && break
            fail 'git returned a malformed staged path list'
            return 2
        fi
        if ! printf '%s' "$file" >"$tmp_dir/path"; then
            fail 'could not prepare a private path input'
            return 2
        fi
        if scan_stream "$tmp_dir/path" "$file"; then :; else return $?; fi
        if ! git show ":$file" >"$tmp_dir/staged" 2>/dev/null; then
            fail 'git could not read a staged blob'
            return 2
        fi
        if scan_stream "$tmp_dir/staged" "$file"; then
            :
        else
            status=$?
            return "$status"
        fi
    done <"$tmp_dir/list"
    return 0
}

mode=files
if [ "${1:-}" = "--tree" ]; then
    mode=tree
    shift
elif [ "${1:-}" = "--staged" ]; then
    mode=staged
    shift
elif [ "${1:-}" = "--diff" ]; then
    mode="diff"
    shift
fi

case "$mode" in
    tree)
        [ "$#" -eq 0 ] || { fail '--tree takes no file arguments'; exit 2; }
        if scan_tree; then :; else exit $?; fi
        ;;
    diff)
        if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
          fail '--diff requires a base and optional head'
          exit 2
        fi
        if scan_diff "$1" "${2:-HEAD}"; then :; else exit $?; fi
        ;;
    staged)
        [ "$#" -eq 0 ] || { fail '--staged takes no file arguments'; exit 2; }
        if scan_staged; then :; else exit $?; fi
        ;;
    files)
        if [ "$#" -gt 0 ]; then
            for file do
                if scan_file "$file"; then :; else exit $?; fi
            done
        else
            while IFS= read -r file || [ -n "$file" ]; do
                if scan_file "$file"; then :; else exit $?; fi
            done
        fi
        ;;
esac

printf '%s\n' 'credential scan passed'
