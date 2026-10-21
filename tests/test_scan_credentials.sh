#!/bin/sh
set -eu

ROOT=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd -P)
SCANNER="$ROOT/scripts/security/scan_credentials.sh"
cd "$ROOT"
umask 077
credential_like=sb_secret_
while [ "${#credential_like}" -lt 32 ]; do
    credential_like=${credential_like}a
done
test_root=$(mktemp -d "${TMPDIR:-/tmp}/studiamatch-scanner-test.XXXXXXXX")
exec_fixture_root=${SCANNER_TEST_EXEC_ROOT:-$test_root}
case "$exec_fixture_root" in
    "$test_root"|/exec-fixture) ;;
    *)
        rmdir -- "$test_root" 2>/dev/null || true
        printf '%s\n' 'scanner regression failed: unexpected executable fixture root' >&2
        exit 1
        ;;
esac
fakebin="$exec_fixture_root/fakebin"
cleanup() {
    rm -f -- "$test_root/clean.txt" "$test_root/hit.txt" "$test_root/missing-output" \
        "$test_root/hit-output" "$test_root/hit-error" "$test_root/clean-error" \
        "$test_root/write-error" "$test_root/write-output" "$test_root/read-error" "$test_root/grep-error" \
        "$test_root/named-credentials.txt" "$test_root/named-output" "$test_root/named-error" \
        "$test_root/leaf-symlink-output" "$test_root/leaf-symlink-error" \
        "$test_root/leaf-target-output" "$test_root/leaf-target-error" \
        "$test_root/concurrent-clean" "$test_root/concurrent-hit" \
        "$test_root/newline-tree-output" "$test_root/newline-tree-error" \
        "$test_root/newline-staged-output" "$test_root/newline-staged-error" \
        "$test_root/newline-diff-output" "$test_root/newline-diff-error" \
        "$test_root/binary.bin" "$test_root/binary-output" "$test_root/binary-error" \
        "$test_root/fixture.lock" "$test_root/lock-output" "$test_root/lock-error" \
        "$test_root/plus-diff-output" "$test_root/plus-diff-error" \
        "$test_root/binary-diff-output" "$test_root/binary-diff-error" \
        "$test_root/history-diff-output" "$test_root/history-diff-error" \
        "$test_root/nested-symlink-output" "$test_root/nested-symlink-error" \
        "$test_root/grep-invocations" \
        "$test_root/$credential_like.txt" "$test_root/path-hit-output" "$test_root/path-hit-error" \
        "$fakebin/grep" "$test_root/tmp/studiamatch-credential-scan."*
    rm -rf -- "$test_root/newline-repo" "$test_root/root-repo" "$test_root/merge-repo" \
        "$test_root/external-parent" \
        "$test_root/hook-repo" 2>/dev/null || true
    rmdir -- "$fakebin" "$test_root/tmp" "$test_root" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

fail() {
    printf '%s\n' "scanner regression failed: $1" >&2
    exit 1
}

assert_no_sensitive_output() {
    candidate=$1
    output_file=$2
    if grep -Fq -- "$candidate" "$output_file"; then
        fail 'credential-like value appeared in scanner output'
    fi
}

mkdir "$test_root/tmp" "$fakebin"
printf '%s\n' 'ordinary public text' >"$test_root/clean.txt"
clean_output=$(TMPDIR="$test_root/tmp" "$SCANNER" "$test_root/clean.txt" 2>&1) \
    || fail 'clean file did not pass'
[ "$clean_output" = 'credential scan passed' ] || fail 'clean file output changed'

printf '%s\n' "$credential_like" >"$test_root/hit.txt"
if TMPDIR="$test_root/tmp" "$SCANNER" "$test_root/hit.txt" \
    >"$test_root/hit-output" 2>"$test_root/hit-error"; then
    fail 'credential-like value was not rejected'
fi
grep -Fq '[REDACTED credential-like value]' "$test_root/hit-error" || fail 'finding was not redacted'
assert_no_sensitive_output "$credential_like" "$test_root/hit-output"
assert_no_sensitive_output "$credential_like" "$test_root/hit-error"

printf '%s\n' 'ordinary public filename content' >"$test_root/$credential_like.txt"
if TMPDIR="$test_root/tmp" "$SCANNER" "$test_root/$credential_like.txt" \
    >"$test_root/path-hit-output" 2>"$test_root/path-hit-error"; then
    fail 'credential-like path hit was accepted'
fi
grep -Fq '[REDACTED]' "$test_root/path-hit-error" || fail 'credential-like path was not redacted'
assert_no_sensitive_output "$credential_like" "$test_root/path-hit-output"
assert_no_sensitive_output "$credential_like" "$test_root/path-hit-error"

printf 'binary-prefix\000%s\n' "$credential_like" >"$test_root/binary.bin"
if TMPDIR="$test_root/tmp" "$SCANNER" "$test_root/binary.bin" \
    >"$test_root/binary-output" 2>"$test_root/binary-error"; then
    fail 'credential-like value in a binary file was not rejected'
fi
grep -Fq '[REDACTED credential-like value]' "$test_root/binary-error" \
    || fail 'binary-file finding was not redacted'
assert_no_sensitive_output "$credential_like" "$test_root/binary-output"
assert_no_sensitive_output "$credential_like" "$test_root/binary-error"

printf '%s\n' "$credential_like" >"$test_root/fixture.lock"
if TMPDIR="$test_root/tmp" "$SCANNER" "$test_root/fixture.lock" \
    >"$test_root/lock-output" 2>"$test_root/lock-error"; then
    fail 'credential-like value in a lock file was not rejected'
fi
assert_no_sensitive_output "$credential_like" "$test_root/lock-output"
assert_no_sensitive_output "$credential_like" "$test_root/lock-error"

opaque_value=OpaqueToken_
while [ "${#opaque_value}" -lt 40 ]; do
    opaque_value=${opaque_value}a
done
printf "CF_API_TOKEN='%s'\nSUPABASE_ACCESS_TOKEN: \"%s\"\nRESEND_API_KEY=%s\nNEXT_SUPABASE_SECRET_KEY=%s\n" \
    "$opaque_value" "$opaque_value" "$opaque_value" "$opaque_value" \
    >"$test_root/named-credentials.txt"
if TMPDIR="$test_root/tmp" "$SCANNER" "$test_root/named-credentials.txt" \
    >"$test_root/named-output" 2>"$test_root/named-error"; then
    fail 'opaque named credential assignments were not rejected'
fi
grep -Fq '[REDACTED credential-like value]' "$test_root/named-error" \
    || fail 'named credential finding was not redacted'
assert_no_sensitive_output "$opaque_value" "$test_root/named-output"
assert_no_sensitive_output "$opaque_value" "$test_root/named-error"

# Git permits newline characters in paths. NUL-delimited enumeration must still
# scan the tracked worktree file and index blob in tree mode, even when split path parts exist.
# Diff mode scans changed blobs so binary and patch-marker-shaped lines are covered.
newline_repo="$test_root/newline-repo"
mkdir "$newline_repo"
git -C "$newline_repo" init -q
git -C "$newline_repo" config user.email scanner-test@example.invalid
git -C "$newline_repo" config user.name scanner-test
printf '%s\n' 'harmless first path fragment' >"$newline_repo/split"
printf '%s\n' 'harmless second path fragment' >"$newline_repo/payload"
git -C "$newline_repo" add -- split payload
git -C "$newline_repo" commit -qm baseline
base_sha=$(git -C "$newline_repo" rev-parse HEAD)
newline_file=$(printf 'split\npayload')
printf '%s\n' "$credential_like" >"$newline_repo/$newline_file"
git -C "$newline_repo" add -- "$newline_file"
if (cd "$newline_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --tree) \
    >"$test_root/newline-tree-output" 2>"$test_root/newline-tree-error"; then
    fail 'credential in newline-named tracked file passed tree scan'
fi
assert_no_sensitive_output "$credential_like" "$test_root/newline-tree-output"
assert_no_sensitive_output "$credential_like" "$test_root/newline-tree-error"
if (cd "$newline_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --staged) \
    >"$test_root/newline-staged-output" 2>"$test_root/newline-staged-error"; then
    fail 'credential in newline-named staged file passed staged scan'
fi
assert_no_sensitive_output "$credential_like" "$test_root/newline-staged-output"
assert_no_sensitive_output "$credential_like" "$test_root/newline-staged-error"
git -C "$newline_repo" commit -qm 'add newline-named fixture'
git -C "$newline_repo" rm -q -- "$newline_file"
git -C "$newline_repo" commit -qm 'remove newline-named fixture'
# Tree mode must scan both tracked worktree content and staged blobs. An
# unstaged edit must not be hidden by an unchanged index, and a staged blob
# must not be hidden by a sanitized worktree file.
worktree_file="$newline_repo/worktree-only.txt"
printf '%s\n' 'harmless committed worktree fixture' >"$worktree_file"
git -C "$newline_repo" add -- worktree-only.txt
git -C "$newline_repo" commit -qm 'add clean worktree fixture'
printf '%s\n' "$credential_like" >"$worktree_file"
if (cd "$newline_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --tree) \
    >"$test_root/newline-tree-output" 2>"$test_root/newline-tree-error"; then
    fail 'credential in an unstaged tracked worktree file passed tree scan'
fi
assert_no_sensitive_output "$credential_like" "$test_root/newline-tree-output"
assert_no_sensitive_output "$credential_like" "$test_root/newline-tree-error"
printf '%s\n' 'harmless index fixture' >"$worktree_file"
git -C "$newline_repo" add -- worktree-only.txt
git -C "$newline_repo" commit -qm 'refresh clean worktree fixture'
printf '%s\n' "$credential_like" >"$worktree_file"
git -C "$newline_repo" add -- worktree-only.txt
printf '%s\n' 'sanitized worktree fixture' >"$worktree_file"
if (cd "$newline_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --tree) \
    >"$test_root/newline-tree-output" 2>"$test_root/newline-tree-error"; then
    fail 'credential in a staged tracked blob passed tree scan'
fi
assert_no_sensitive_output "$credential_like" "$test_root/newline-tree-output"
assert_no_sensitive_output "$credential_like" "$test_root/newline-tree-error"
# Restore the worktree and index before subsequent symlink probes so those
# probes fail or pass only on their own path condition.
printf '%s\n' 'sanitized staged fixture' >"$worktree_file"
git -C "$newline_repo" add -- worktree-only.txt
# A tracked nested path must fail closed if a parent directory is replaced by
# a symlink. The scanner must not follow the link into data outside the repo.
mkdir "$newline_repo/nested" "$test_root/external-parent"
printf '%s\n' 'clean nested baseline' >"$newline_repo/nested/fixture.txt"
git -C "$newline_repo" add -- nested/fixture.txt
git -C "$newline_repo" commit -qm 'add clean nested path fixture'
printf '%s\n' "$credential_like" >"$test_root/external-parent/fixture.txt"
rm -f -- "$newline_repo/nested/fixture.txt"
rmdir -- "$newline_repo/nested"
ln -s "$test_root/external-parent" "$newline_repo/nested"
if (cd "$newline_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --tree) \
    >"$test_root/nested-symlink-output" 2>"$test_root/nested-symlink-error"; then
    fail 'tracked path through a symlinked parent passed tree scan'
fi
grep -Fq 'credential scan failed: could not securely read a tracked worktree path' \
    "$test_root/nested-symlink-error" \
    || fail 'symlinked parent was not rejected before reading its target'
assert_no_sensitive_output "$credential_like" "$test_root/nested-symlink-output"
assert_no_sensitive_output "$credential_like" "$test_root/nested-symlink-error"
rm -- "$newline_repo/nested"
mkdir "$newline_repo/nested"
printf '%s\n' 'clean nested baseline' >"$newline_repo/nested/fixture.txt"
# A leaf symlink is scanned as link text, never followed to its target.
printf '%s\n' "$credential_like" >"$test_root/external-parent/leaf-target.txt"
ln -s "$test_root/external-parent/leaf-target.txt" "$newline_repo/external-leaf.txt"
git -C "$newline_repo" add -- external-leaf.txt
git -C "$newline_repo" commit -qm 'add external leaf symlink fixture'
if (cd "$newline_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --tree) \
    >"$test_root/leaf-target-output" 2>"$test_root/leaf-target-error"; then
    :
else
    fail 'scanner followed the target of a final symlink'
fi
[ "$(cat "$test_root/leaf-target-output")" = 'credential scan passed' ] \
    || fail 'external leaf target changed the scan result'
assert_no_sensitive_output "$credential_like" "$test_root/leaf-target-output"
assert_no_sensitive_output "$credential_like" "$test_root/leaf-target-error"
ln -s "$credential_like" "$newline_repo/credential-link"
git -C "$newline_repo" add -- credential-link
if (cd "$newline_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --tree) \
    >"$test_root/leaf-symlink-output" 2>"$test_root/leaf-symlink-error"; then
    fail 'credential-like final symlink target text passed tree scan'
fi
assert_no_sensitive_output "$credential_like" "$test_root/leaf-symlink-output"
assert_no_sensitive_output "$credential_like" "$test_root/leaf-symlink-error"
head_sha=$(git -C "$newline_repo" rev-parse HEAD)
if (cd "$newline_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --diff "$base_sha" "$head_sha") \
    >"$test_root/newline-diff-output" 2>"$test_root/newline-diff-error"; then
    fail 'credential in newline-named diff passed diff scan'
fi
assert_no_sensitive_output "$credential_like" "$test_root/newline-diff-output"
assert_no_sensitive_output "$credential_like" "$test_root/newline-diff-error"

plus_base_sha=$head_sha
printf '+++%s\n' "$credential_like" >"$newline_repo/plus-content.txt"
git -C "$newline_repo" add -- plus-content.txt
git -C "$newline_repo" commit -qm 'add plus-prefixed fixture'
plus_head_sha=$(git -C "$newline_repo" rev-parse HEAD)
if (cd "$newline_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --diff "$plus_base_sha" "$plus_head_sha") \
    >"$test_root/plus-diff-output" 2>"$test_root/plus-diff-error"; then
    fail 'credential-like value on a plus-prefixed added line passed diff scan'
fi
assert_no_sensitive_output "$credential_like" "$test_root/plus-diff-output"
assert_no_sensitive_output "$credential_like" "$test_root/plus-diff-error"

binary_base_sha=$plus_head_sha
printf 'binary-prefix\000%s\n' "$credential_like" >"$newline_repo/binary-diff.bin"
git -C "$newline_repo" add -- binary-diff.bin
git -C "$newline_repo" commit -qm 'add binary fixture'
binary_head_sha=$(git -C "$newline_repo" rev-parse HEAD)
if (cd "$newline_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --diff "$binary_base_sha" "$binary_head_sha") \
    >"$test_root/binary-diff-output" 2>"$test_root/binary-diff-error"; then
    fail 'credential-like value in a changed binary blob passed diff scan'
fi
assert_no_sensitive_output "$credential_like" "$test_root/binary-diff-output"
assert_no_sensitive_output "$credential_like" "$test_root/binary-diff-error"

# A push still carries every commit after the remote base. A credential-like
# blob must be rejected even when a later commit deletes the file before HEAD.
history_base_sha=$binary_head_sha
printf '%s\n' "$credential_like" >"$newline_repo/transient.txt"
git -C "$newline_repo" add -- transient.txt
git -C "$newline_repo" commit -qm 'add transient credential fixture'
git -C "$newline_repo" rm -q -- transient.txt
git -C "$newline_repo" commit -qm 'remove transient credential fixture'
history_head_sha=$(git -C "$newline_repo" rev-parse HEAD)
if (cd "$newline_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --diff "$history_base_sha" "$history_head_sha") \
    >"$test_root/history-diff-output" 2>"$test_root/history-diff-error"; then
    fail 'credential-like value in a transient commit passed diff scan'
fi
assert_no_sensitive_output "$credential_like" "$test_root/history-diff-output"
assert_no_sensitive_output "$credential_like" "$test_root/history-diff-error"

empty_tree_sha=$(git -C "$newline_repo" hash-object -t tree -w /dev/null)
if (cd "$newline_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --diff "$empty_tree_sha" "$history_head_sha") \
    >"$test_root/history-diff-output" 2>"$test_root/history-diff-error"; then
    fail 'credential-like value in history passed empty-tree diff scan'
fi
assert_no_sensitive_output "$credential_like" "$test_root/history-diff-output"
assert_no_sensitive_output "$credential_like" "$test_root/history-diff-error"

root_repo="$test_root/root-repo"
mkdir "$root_repo"
git -C "$root_repo" init -q
git -C "$root_repo" config user.email scanner-test@example.invalid
git -C "$root_repo" config user.name scanner-test
printf '%s\n' "$credential_like" >"$root_repo/root-transient.txt"
git -C "$root_repo" add -- root-transient.txt
git -C "$root_repo" commit -qm 'synthetic root credential fixture'
printf '%s\n' 'sanitized root fixture' >"$root_repo/root-transient.txt"
git -C "$root_repo" add -- root-transient.txt
git -C "$root_repo" commit -qm 'sanitize root credential fixture'
root_head_sha=$(git -C "$root_repo" rev-parse HEAD)
if (cd "$root_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --diff "$empty_tree_sha" "$root_head_sha") \
    >"$test_root/history-diff-output" 2>"$test_root/history-diff-error"; then
    fail 'credential-like value in a root commit passed diff scan'
fi
assert_no_sensitive_output "$credential_like" "$test_root/history-diff-output"
assert_no_sensitive_output "$credential_like" "$test_root/history-diff-error"

merge_repo="$test_root/merge-repo"
mkdir "$merge_repo"
git -C "$merge_repo" init -q
git -C "$merge_repo" config user.email scanner-test@example.invalid
git -C "$merge_repo" config user.name scanner-test
printf '%s\n' 'merge base' >"$merge_repo/merge.txt"
git -C "$merge_repo" add -- merge.txt
git -C "$merge_repo" commit -qm 'merge scanner base'
merge_base_sha=$(git -C "$merge_repo" rev-parse HEAD)
merge_main_branch=$(git -C "$merge_repo" symbolic-ref --short HEAD)
git -C "$merge_repo" checkout -qb scanner-side
printf '%s\n' 'side branch version' >"$merge_repo/merge.txt"
git -C "$merge_repo" commit -qam 'side branch change'
git -C "$merge_repo" checkout -q "$merge_main_branch"
printf '%s\n' 'main branch version' >"$merge_repo/merge.txt"
git -C "$merge_repo" commit -qam 'main branch change'
set +e
git -C "$merge_repo" merge --no-commit scanner-side >/dev/null 2>&1
merge_status=$?
set -e
[ "$merge_status" -ne 0 ] || fail 'merge conflict fixture did not conflict'
printf '%s\n' "$credential_like" >"$merge_repo/merge.txt"
git -C "$merge_repo" add -- merge.txt
git -C "$merge_repo" commit -qm 'synthetic merge resolution fixture'
printf '%s\n' 'sanitized merge fixture' >"$merge_repo/merge.txt"
git -C "$merge_repo" commit -qam 'sanitize merge resolution fixture'
merge_head_sha=$(git -C "$merge_repo" rev-parse HEAD)
if (cd "$merge_repo" && TMPDIR="$test_root/tmp" "$SCANNER" --diff "$merge_base_sha" "$merge_head_sha") \
    >"$test_root/history-diff-output" 2>"$test_root/history-diff-error"; then
    fail 'credential-like value in a merge resolution passed diff scan'
fi
assert_no_sensitive_output "$credential_like" "$test_root/history-diff-output"
assert_no_sensitive_output "$credential_like" "$test_root/history-diff-error"

hook_repo="$test_root/hook-repo"
mkdir -p "$hook_repo/.githooks" "$hook_repo/scripts/security"
cp "$ROOT/.githooks/pre-push" "$hook_repo/.githooks/pre-push"
cp "$SCANNER" "$hook_repo/scripts/security/scan_credentials.sh"
git -C "$hook_repo" init -q
git -C "$hook_repo" config user.email scanner-test@example.invalid
git -C "$hook_repo" config user.name scanner-test
git -C "$hook_repo" add -- .githooks/pre-push scripts/security/scan_credentials.sh
git -C "$hook_repo" commit -qm 'scanner hook fixture baseline'
printf '%s\n' "$credential_like" >"$hook_repo/hook-transient.txt"
git -C "$hook_repo" add -- hook-transient.txt
git -C "$hook_repo" commit -qm 'add transient hook credential fixture'
git -C "$hook_repo" rm -q -- hook-transient.txt
git -C "$hook_repo" commit -qm 'remove transient hook credential fixture'
hook_head_sha=$(git -C "$hook_repo" rev-parse HEAD)
set +e
printf 'refs/heads/test %s refs/heads/test %040d\n' "$hook_head_sha" 0 \
    | (cd "$hook_repo" && .githooks/pre-push) \
        >"$test_root/history-diff-output" 2>"$test_root/history-diff-error"
hook_status=$?
set -e
[ "$hook_status" -ne 0 ] || fail 'pre-push accepted a transient credential on a new branch'
assert_no_sensitive_output "$credential_like" "$test_root/history-diff-output"
assert_no_sensitive_output "$credential_like" "$test_root/history-diff-error"

if TMPDIR="$test_root/clean.txt" "$SCANNER" "$test_root/clean.txt" \
    >"$test_root/write-error" 2>&1; then
    fail 'temporary-directory write failure was accepted'
fi
set +e
TMPDIR="$test_root/tmp" "$SCANNER" "$test_root/hit.txt" \
    >"$test_root/write-output" 2>/dev/full
write_status=$?
set -e
[ "$write_status" -eq 2 ] || fail 'redacted finding output failure was accepted'
if "$SCANNER" "$test_root/does-not-exist" >"$test_root/read-error" 2>&1; then
    fail 'missing input was accepted'
fi

cat >"$fakebin/grep" <<'EOF'
#!/bin/sh
printf '%s\n' invoked >>"${SCANNER_TEST_GREP_MARKER:?}"
exit 2
EOF
chmod 700 "$fakebin/grep"
set +e
/usr/bin/env -i PATH="$fakebin:/usr/bin:/bin" LC_ALL=C \
    TMPDIR="$test_root/tmp" SCANNER_TEST_GREP_MARKER="$test_root/grep-invocations" \
    SCANNER_TEST_EXEC_ROOT="$exec_fixture_root" \
    /usr/bin/bash "$SCANNER" "$test_root/clean.txt" \
    >"$test_root/grep-error" 2>&1
grep_status=$?
set -e
[ -s "$test_root/grep-invocations" ] || fail 'grep I/O failure fixture was not invoked'
[ "$grep_status" -eq 2 ] || fail 'grep I/O failure was not returned as an operational error'
if grep -Fq 'credential scan failed: grep could not read or scan an input' "$test_root/grep-error"; then
    :
else
    fail 'grep I/O failure was accepted'
fi

set +e
TMPDIR="$test_root/tmp" "$SCANNER" "$test_root/clean.txt" \
    >"$test_root/concurrent-clean" 2>&1 &
clean_pid=$!
TMPDIR="$test_root/tmp" "$SCANNER" "$test_root/hit.txt" \
    >"$test_root/concurrent-hit" 2>&1 &
hit_pid=$!
wait "$clean_pid"
clean_status=$?
wait "$hit_pid"
hit_status=$?
set -e
[ "$clean_status" -eq 0 ] || fail 'concurrent clean scan failed'
[ "$hit_status" -eq 1 ] || fail 'concurrent hit scan did not fail closed'
assert_no_sensitive_output "$credential_like" "$test_root/concurrent-hit"

remaining=$(find "$test_root/tmp" -mindepth 1 -maxdepth 1 -print -quit)
[ -z "$remaining" ] || fail 'scanner left its private temporary directory behind'
printf '%s\n' 'scanner-regressions=PASS|clean=1|text=1|named-credentials=4|binary=2|lockfile=1|plus-prefixed=1|newline-paths=3|tree=6|history=5|io-failures=4|concurrent=2|redaction=PASS'
