#!/bin/sh
# Scans repository files, staged blobs, explicit files, or a git diff for credential-like values.

set -eu

PATTERNS="eyJhbG[A-Za-z0-9_-]{10,}|sb_publishable_[A-Za-z0-9_-]{20,}|sb_secret_[A-Za-z0-9_-]{10,}|sbp_[A-Za-z0-9_-]{10,}|sk-(proj-)?[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16}|ghs_[A-Za-z0-9]{20,}|opencode_[A-Za-z0-9_-]{20,}|oc_[A-Za-z0-9_-]{30,}|OPENCODE_API_KEY[[:space:]]*[:=][[:space:]]*['\"]?[A-Za-z0-9_-]{20,}"
SKIP='\.(png|jpg|jpeg|gif|bmp|ico|svg|woff|woff2|ttf|eot|mp4|avi|mov|pdf|zip|tar|gz|lock)$'

scan_file() {
    file="$1"
    base=$(basename "$file")
    [ -f "$file" ] || return 0
    printf '%s\n' "$file" | grep -Eq "$SKIP" && return 0
    printf '%s\n' "$file" | grep -Eq '(^|/)(\.git|node_modules|\.next|out|__pycache__)(/|$)' && return 0
    if LC_ALL=C grep -InE "$PATTERNS" "$file" >/tmp/studiamatch_credential_findings 2>/dev/null; then
        awk -F: '{ print $1 ":" $2 ": [REDACTED credential-like value]" }' /tmp/studiamatch_credential_findings >&2
        return 1
    fi
    return 0
}

scan_tree() {
    git ls-files | while IFS= read -r file; do
        scan_file "$file" || exit 1
    done
}

scan_diff() {
    base="$1"
    head="$2"
    if git diff --unified=0 "$base" "$head" -- | grep -E '^\+' | grep -vE '^\+\+\+' | LC_ALL=C grep -nE "$PATTERNS" >/tmp/studiamatch_credential_findings 2>/dev/null; then
        awk -F: '{ print "diff:" $1 ": [REDACTED credential-like value]" }' /tmp/studiamatch_credential_findings >&2
        return 1
    fi
    return 0
}

scan_staged() {
    git diff --cached --name-only --diff-filter=ACM | while IFS= read -r file; do
        printf '%s\n' "$file" | grep -Eq "$SKIP" && continue
        printf '%s\n' "$file" | grep -Eq '(^|/)(\.git|node_modules|\.next|out|__pycache__)(/|$)' && continue
        if git show ":$file" | LC_ALL=C grep -nE "$PATTERNS" >/tmp/studiamatch_credential_findings 2>/dev/null; then
            awk -v file="$file" -F: '{ print file ":" $1 ": [REDACTED credential-like value]" }' /tmp/studiamatch_credential_findings >&2
            return 1
        fi
    done
}

mode="files"
if [ "${1:-}" = "--tree" ]; then
    mode="tree"
    shift
elif [ "${1:-}" = "--staged" ]; then
    mode="staged"
    shift
elif [ "${1:-}" = "--diff" ]; then
    mode="diff"
    shift
fi

case "$mode" in
    tree)
        scan_tree
        ;;
    diff)
        scan_diff "${1:?base required}" "${2:-HEAD}"
        ;;
    staged)
        scan_staged
        ;;
    files)
        if [ "$#" -gt 0 ]; then
            for file in "$@"; do
                scan_file "$file"
            done
        else
            while IFS= read -r file; do
                scan_file "$file"
            done
        fi
        ;;
esac

echo "credential scan passed"
