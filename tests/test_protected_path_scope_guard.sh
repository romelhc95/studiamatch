#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$ROOT/scripts/security/protected_path_scope_guard.sh"

test_root=$(mktemp -d "${TMPDIR:-/tmp}/studiamatch-path-scope-test.XXXXXXXX")
cleanup() {
  rm -f -- "$test_root/ordinary.nul" "$test_root/newline.nul" "$test_root/control.nul" \
    "$test_root/empty.nul" "$test_root/unterminated" "$test_root/result" "$test_root/error"
  rmdir -- "$test_root" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

fail() {
  printf 'protected path scope regression failed: %s\n' "$1" >&2
  exit 1
}

printf 'README.md\0.env.example\0scripts/security/scan_credentials.sh\0' \
  >"$test_root/ordinary.nul"
result=$(protected_path_scope_capture "$test_root/ordinary.nul") \
  || fail 'ordinary NUL-delimited paths were rejected'
[[ "$result" == $'README.md\n.env.example\nscripts/security/scan_credentials.sh' ]] \
  || fail 'ordinary paths changed while converting separators'

newline_path=$(printf 'README.md\n.env.example')
printf '%s\0' "$newline_path" >"$test_root/newline.nul"
if protected_path_scope_capture "$test_root/newline.nul" \
  >"$test_root/result" 2>"$test_root/error"; then
  fail 'newline path was split into two allowlist records'
fi
[[ ! -s "$test_root/result" ]] || fail 'rejected newline path leaked into the normalized list'
grep -Fq 'unsupported control character' "$test_root/error" \
  || fail 'newline path did not fail with a sanitized reason'

printf 'README.md\r\n.env.example\0' >"$test_root/control.nul"
if protected_path_scope_capture "$test_root/control.nul" \
  >"$test_root/result" 2>"$test_root/error"; then
  fail 'control-character path was accepted'
fi

printf '\0' >"$test_root/empty.nul"
if protected_path_scope_capture "$test_root/empty.nul" \
  >"$test_root/result" 2>"$test_root/error"; then
  fail 'empty path record was accepted'
fi

printf 'README.md' >"$test_root/unterminated"
if protected_path_scope_capture "$test_root/unterminated" \
  >"$test_root/result" 2>"$test_root/error"; then
  fail 'unterminated path record was accepted'
fi

if protected_path_scope_capture "$test_root/missing.nul" \
  >"$test_root/result" 2>"$test_root/error"; then
  fail 'missing path list was accepted'
fi

python3 - "$ROOT/scripts/security/protected_path_scope_guard.sh" \
  "$ROOT/.context/evidencia/h3req1_pr_scope_manifest_2026-10-19_r19_pwi_r3_reconciled.json" \
  "$ROOT" <<'PY'
import hashlib
import json
import posixpath
import re
import subprocess
import sys
from urllib.parse import unquote
from pathlib import Path

guard_path, manifest_path, root = map(Path, sys.argv[1:])
guard = guard_path.read_text(encoding="utf-8")

def workflow_regex(name):
    match = re.search(rf"(?m)^\s*{re.escape(name)}='([^']*)'\s*$", guard)
    if not match:
        raise SystemExit(f"protected path integration test: missing {name} matcher")
    return match.group(1)

local_match = re.search(
    r"<<'H3_LOCAL_PATHS'\s*\n(?P<body>.*?)\n\s*H3_LOCAL_PATHS",
    guard,
    re.DOTALL,
)
if not local_match:
    raise SystemExit("protected path integration test: missing exact local allowlist")

patterns = [workflow_regex("allowed_h3"), workflow_regex("allowed_h3_extra")]
local_paths = {line.strip() for line in local_match.group("body").splitlines() if line.strip()}
pwi_worker_paths = {
    "scripts/security/pwi_worker/README.md",
    "scripts/security/pwi_worker/github.mjs",
    "scripts/security/pwi_worker/index.mjs",
    "scripts/security/pwi_worker/package.json",
    "scripts/security/pwi_worker/package-lock.json",
    "scripts/security/pwi_worker/policy.mjs",
    "scripts/security/pwi_worker/test/pwi_worker.test.mjs",
    "scripts/security/pwi_worker/runtime-test/pwi_worker.runtime.test.mjs",
    "scripts/security/pwi_worker/vitest.config.mjs",
    "scripts/security/pwi_worker/wrangler.jsonc",
}
for path in pwi_worker_paths:
    if not any(re.search(pattern, path) for pattern in patterns):
        raise SystemExit(f"protected path integration test: approved PWI path is not explicitly allowed: {path}")
for unreviewed_pwi in (
    "scripts/security/pwi_worker/unreviewed.mjs",
    "scripts/security/pwi_worker/runtime-test/unreviewed.mjs",
    "scripts/security/pwi_worker/extra/unreviewed.mjs",
):
    if unreviewed_pwi in local_paths or any(re.search(pattern, unreviewed_pwi) for pattern in patterns):
        raise SystemExit(
            "protected path integration test: unreviewed PWI path is accepted: "
            f"{unreviewed_pwi}"
        )
for unmanifested_h3 in (
    ".context/evidencia/h3req1-unreviewed-forbidden.md",
    ".context/evidencia/h3_unreviewed-forbidden.md",
):
    if unmanifested_h3 in local_paths or any(re.search(pattern, unmanifested_h3) for pattern in patterns):
        raise SystemExit(
            "protected path integration test: unmanifested H3 markdown is accepted: "
            f"{unmanifested_h3}"
        )
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
entries = manifest.get("scope", {}).get("entries")
if not isinstance(entries, list):
    raise SystemExit("protected path integration test: manifest has no scope entries")
scope_by_path = {entry["path"]: entry for entry in entries}
ignored_scope_paths = sorted(
    path for path, entry in scope_by_path.items() if entry.get("ignored_by_porcelain") is True
)
package_actions = manifest.get("package_actions", {})
force_add_paths = package_actions.get("force_add_ignored_paths")
if not isinstance(force_add_paths, list) or force_add_paths != ignored_scope_paths:
    raise SystemExit(
        "protected path integration test: ignored selected paths must be listed exactly for force-add"
    )
if not package_actions.get("force_add_reason"):
    raise SystemExit("protected path integration test: force-add selection has no documented reason")
for path in force_add_paths:
    entry = scope_by_path[path]
    if not any(
        selection in {"R8_preserved_selected_evidence", "R14_catalog_reference_closure"}
        for selection in entry.get("selections", [])
    ):
        raise SystemExit(
            "protected path integration test: ignored file lacks an R8 or catalog-closure selection"
        )

scope_changed = [
    entry["path"]
    for entry in entries
    if entry.get("status") in {"modified", "untracked", "deleted"}
]
if len(scope_changed) != len(set(scope_changed)):
    raise SystemExit("protected path integration test: scope contains duplicate paths")
changed = list(scope_changed)
package_artifacts = manifest.get("package_artifacts", {})
changed.extend(
    artifact["path"]
    for artifact in package_artifacts.values()
    if isinstance(artifact, dict) and artifact.get("included") and artifact.get("path")
)
changed = list(dict.fromkeys(changed))
if not changed:
    raise SystemExit("protected path integration test: scope paths are empty")

closure = manifest.get("catalog_reference_closure", {})
catalogs = closure.get("catalogs")
references = closure.get("entries")
if not isinstance(catalogs, list) or len(catalogs) != 13:
    raise SystemExit("protected path integration test: expected 13 historical catalogs")
expected_reference_count = closure.get("reference_count")
if expected_reference_count != 1173 or not isinstance(references, list) or len(references) != 1173:
    raise SystemExit("protected path integration test: expected 1173 direct catalog targets in the successor manifest")
reference_paths = [entry.get("path") for entry in references if isinstance(entry, dict)]
if len(reference_paths) != expected_reference_count or len(reference_paths) != len(set(reference_paths)):
    raise SystemExit("protected path integration test: catalog target paths are missing or duplicated")

# The selected R19 manifest is immutable evidence for PR #501. Validate its
# historical target set and candidate hashes against the integrated tree; the
# successor worktree is checked separately by --compare-candidate.
historical_candidate_commit = "8ac174d81cf6ce23658bff132236a78935ace1ad"
historical_paths = sorted(
    set(reference_paths)
    | {
        catalog["path"]
        for catalog in catalogs
        if isinstance(catalog, dict) and catalog.get("path")
    }
)
historical_result = subprocess.run(
    ["git", "cat-file", "--batch"],
    cwd=root,
    input="".join(f"{historical_candidate_commit}:{path}\n" for path in historical_paths).encode(),
    capture_output=True,
    check=False,
)
if historical_result.returncode != 0:
    raise SystemExit("protected path integration test: historical candidate tree is unavailable")
historical_data = historical_result.stdout
historical_blobs = {}
cursor = 0
for path in historical_paths:
    header_end = historical_data.find(b"\n", cursor)
    if header_end < 0:
        raise SystemExit("protected path integration test: historical candidate response is malformed")
    header = historical_data[cursor:header_end].decode("ascii", errors="replace")
    cursor = header_end + 1
    if header.endswith(" missing"):
        raise SystemExit(f"protected path integration test: historical target is unavailable: {path}")
    parts = header.split()
    if len(parts) != 3 or parts[1] != "blob":
        raise SystemExit(f"protected path integration test: historical target is not a blob: {path}")
    blob_size = int(parts[2])
    blob = historical_data[cursor : cursor + blob_size]
    if len(blob) != blob_size or historical_data[cursor + blob_size : cursor + blob_size + 1] != b"\n":
        raise SystemExit("protected path integration test: historical candidate response is truncated")
    historical_blobs[path] = blob
    cursor += blob_size + 1

for catalog in catalogs:
    catalog_path = catalog.get("path") if isinstance(catalog, dict) else None
    if not catalog_path or catalog_path not in historical_blobs:
        raise SystemExit(f"protected path integration test: catalog is unavailable: {catalog_path}")

actual_reference_paths = set()
for catalog in catalogs:
    catalog_path = catalog["path"]
    markdown = historical_blobs[catalog_path].decode("utf-8")
    links = [match.group(1) for match in re.finditer(r"!?\[[^\]]*\]\(([^)]*)\)", markdown)]
    links.extend(match.group(1).split("|", 1)[0].strip() for match in re.finditer(r"\[\[([^\]]+)\]\]", markdown))
    for raw in links:
        target = raw.strip()
        if target.startswith("<") and ">" in target:
            target = target[1 : target.index(">")]
        target = re.sub(r"\\([()])", r"\1", target)
        if not target or re.match(r"^(?:[a-z][a-z0-9+.-]*:|//)", target, re.IGNORECASE):
            continue
        target = unquote(target)
        file_part = target.split("#", 1)[0].split(None, 1)[0]
        relative = (
            posixpath.normpath(posixpath.join(posixpath.dirname(catalog_path), file_part.lstrip("/")))
            if file_part
            else catalog_path
        )
        if relative == ".." or relative.startswith("../"):
            raise SystemExit(f"protected path integration test: catalog target escapes checkout: {raw}")
        actual_reference_paths.add(relative)
if actual_reference_paths != set(reference_paths):
    missing_from_manifest = sorted(actual_reference_paths - set(reference_paths))
    stale_manifest_entries = sorted(set(reference_paths) - actual_reference_paths)
    raise SystemExit(
        "protected path integration test: catalog target set differs from manifest; "
        f"missing={missing_from_manifest[:8]} stale={stale_manifest_entries[:8]}"
    )

ignored_catalog_targets = {
    reference["path"]
    for reference in references
    if reference.get("availability") == "candidate_change"
    and reference["path"] in set(force_add_paths)
}
for reference in references:
    path = reference["path"]
    if path not in historical_blobs:
        raise SystemExit(f"protected path integration test: referenced target is unavailable: {path}")
    availability = reference.get("availability")
    if availability == "candidate_change":
        expected_hash = reference.get("sha256")
        if not expected_hash or hashlib.sha256(historical_blobs[path]).hexdigest() != expected_hash:
            raise SystemExit(f"protected path integration test: referenced target hash differs: {path}")
        scope_entry = scope_by_path.get(path)
        if path not in changed or not scope_entry or scope_entry.get("status") == "deleted":
            raise SystemExit(f"protected path integration test: candidate target is absent from scope: {path}")
        if scope_entry.get("sha256") != expected_hash:
            raise SystemExit(f"protected path integration test: candidate target pin differs: {path}")
        if scope_entry.get("ignored_by_porcelain") and path not in force_add_paths:
            raise SystemExit(
                f"protected path integration test: ignored catalog target is not force-added: {path}"
            )
    elif availability != "baseline":
        raise SystemExit(f"protected path integration test: invalid target availability: {path}")
    elif reference.get("baseline_tracked") is not True:
        raise SystemExit(f"protected path integration test: baseline target is not tracked: {path}")

if closure.get("reference_count") != len(references):
    raise SystemExit("protected path integration test: catalog reference count does not reconcile")

missing = [
    path
    for path in changed
    if path not in local_paths and not any(re.search(pattern, path) for pattern in patterns)
]
if missing:
    print(
        f"protected path integration failed: {len(missing)} manifest candidate paths are not accepted",
        file=sys.stderr,
    )
    for path in missing:
        print(path, file=sys.stderr)
    raise SystemExit(1)

print(
    "protected-path-manifest-integration=PASS"
    f"|candidate_paths={len(changed)}|catalogs={len(catalogs)}"
    f"|catalog_targets={len(references)}|force_add_ignored={len(force_add_paths)}"
    f"|ignored_catalog_targets={len(ignored_catalog_targets)}"
)
PY

printf '%s\n' 'protected-path-scope-regressions=PASS|ordinary=3|newline=1|controls=1|malformed=3|unmanifested_h3=2'
