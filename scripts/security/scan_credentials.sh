#!/bin/sh
# scan_credentials.sh — Scans files for hardcoded credentials
# Usage: scan_credentials.sh [file1 file2 ...]
#   If no files given, reads from stdin (pipe delimited file paths).
# Returns 0 (clean) or 1 (credentials found), writes findings to stderr.

set -e

# Patterns that signal a hardcoded credential
PATTERNS="eyJhbG[A-Za-z0-9_-]\{10,\}|
sb_secret_[A-Za-z0-9_-]\{10,\}|
sbp_[A-Za-z0-9_-]\{10,\}|
sk-[A-Za-z0-9]\{20,\}|
ghp_[A-Za-z0-9]\{20,\}|
gho_[A-Za-z0-9]\{20,\}|
github_pat_[A-Za-z0-9_-]\{30,\}|
AKIA[0-9A-Z]\{16\}|
ghs_[A-Za-z0-9]\{20,\}"

# File patterns to always skip
skip_pattern="\.(png|jpg|jpeg|gif|bmp|ico|svg|woff|woff2|ttf|eot|mp4|avi|mov|pdf|zip|tar|gz|lock)$"

found=0
search_file() {
    f="$1"
    basename=$(basename "$f")
    # Skip binary / generated files
    echo "$f" | grep -qE "$skip_pattern" && return 0
    # Skip .env files (should be gitignored but safety check)
    echo "$basename" | grep -qE '^\.env' && return 0
    # Skip node_modules, .git
    echo "$f" | grep -qE '/(node_modules|\.git|\.next|out)/' && return 0
    # Skip files that don't exist or are binary
    [ ! -f "$f" ] && return 0
    # Check for credential patterns
    matches=$(grep -nE "$PATTERNS" "$f" 2>/dev/null || true)
    if [ -n "$matches" ]; then
        echo "⚠️  CREDENTIAL FOUND in $f:"
        echo "$matches" | while IFS= read -r line; do
            echo "   → $line"
        done
        found=1
    fi
    return 0
}

if [ $# -gt 0 ]; then
    for file in "$@"; do
        search_file "$file"
    done
else
    while IFS= read -r file; do
        search_file "$file"
    done
fi

if [ "$found" -eq 1 ]; then
    echo "❌ SECURITY BLOCKED: Hardcoded credentials detected. Remove them and use env vars instead." >&2
    exit 1
fi
exit 0
