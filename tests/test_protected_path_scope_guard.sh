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

# The duration/mobile successor PR adds only the exact local paths rejected
# by the current guard, plus the parser test and R20 selection manifest. R19
# remains the immutable historical manifest validated below.
candidate_scope_path = root / ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-pr-scope-2026-10-24.json"
candidate_scope = json.loads(candidate_scope_path.read_text(encoding="utf-8"))
remediation = candidate_scope.get("protectedPathRemediation", {})
exact_additions = remediation.get("exactAdditionalAllowedH3LocalPaths")
expected_exact_additions = {
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-acceptance-cycle-2026-10-24.md",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-pr-body-2026-10-24.md",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-pr-scope-2026-10-24.json",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-scope-manifest.json",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/canonical-runner.stdout",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/functional-catalog-seed-corrected.stdout",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/h3-expanded/H3-UAT-058-desktop.png",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/h3-expanded/H3-UAT-058-mobile.png",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/h3-expanded/H3-UAT-058-tablet.png",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/h3-expanded/H3-UAT-059-desktop.png",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/h3-expanded/H3-UAT-059-mobile.png",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/h3-expanded/H3-UAT-059-tablet.png",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/h3-expanded/h3-expanded-uat-artifact-hashes.json",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/h3-expanded/h3-expanded-uat-executions.json",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/h3-expanded/h3-expanded-uat-manifest.json",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/h3-expanded/h3-expanded-uat-matrix.json",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-duration-parser-green/output.jsonl",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-duration-parser-red/actual-result.jsonl",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-duration-parser-red/output.jsonl",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-filter-overflow-red/observed.json",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-final-docker-checks-2026-10-24/eslint.stdout",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-final-docker-checks-2026-10-24/static-build-artifact.sha256",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-final-docker-checks-2026-10-24/static-build.stdout",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-final-docker-checks-2026-10-24/typescript.stdout",
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-final-docker-checks-2026-10-24/uat-helper-unit-tests.stdout",
    "tests/h3_uat_http_diagnostics.mjs",
    "tests/h3_uat_sanitizer.mjs",
    "tests/h3_duration_parser.test.mjs",
    "web/src/components/Footer.tsx",
}
if (
    candidate_scope.get("target", {}).get("baseBranch") != "desarrollo"
    or remediation.get("currentPrChangedPathCount") != 37
    or remediation.get("currentlyRejectedByGuardCount") != 27
    or remediation.get("exactAdditionalAllowlistPathCount") != 29
    or not isinstance(exact_additions, list)
    or len(exact_additions) != 29
    or len(exact_additions) != len(set(exact_additions))
    or set(exact_additions) != expected_exact_additions
):
    raise SystemExit("protected path integration test: candidate remediation manifest differs from the reviewed exact scope")
included_candidate_paths = set(candidate_scope.get("includedPaths", []))
if not set(exact_additions).issubset(included_candidate_paths):
    raise SystemExit("protected path integration test: exact allowlist additions are not all selected in the candidate package")
if not set(exact_additions).issubset(local_paths):
    raise SystemExit("protected path integration test: a reviewed exact candidate path is not allowlisted")
if "web/src/components/Footer.tsx" not in exact_additions:
    raise SystemExit("protected path integration test: responsive footer correction is absent from the exact candidate scope")
if "tests/test_protected_path_scope_guard.sh" not in local_paths:
    raise SystemExit("protected path integration test: the guard regression itself is not allowlisted")
for unreviewed_candidate in (
    ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/run-canonical-058-059-footer-20261024/unlisted-output.json",
    "tests/h3_duration_parser_extra.test.mjs",
    "web/src/components/FooterExtra.tsx",
):
    if unreviewed_candidate in local_paths or any(
        re.search(pattern, unreviewed_candidate) for pattern in patterns
    ):
        raise SystemExit(
            "protected path integration test: unreviewed candidate sibling is accepted: "
            f"{unreviewed_candidate}"
        )

# D04 is a separate candidate. R20/#503 remains unchanged and is checked above.
d04_scope_path = root / ".context/evidencia/h3req1_d04_candidate_pr_scope_2026-10-25.json"
d04_scope = json.loads(d04_scope_path.read_text(encoding="utf-8"))
d04_expected_paths = {
    ".context/componentes/admin_runtime.md",
    ".context/componentes/database_migrations.md",
    ".context/componentes/pruebas_evidencia.md",
    ".context/componentes/seguridad_tooling.md",
    ".context/evidencia/h3req1_d04_candidate_docs_scope_2026-10-25.json",
    ".context/evidencia/h3req1_d04_candidate_pr_scope_2026-10-25.json",
    ".context/evidencia/h3req1_d04_onboarding_forbidden_2026-10-25.md",
    ".context/indice.md",
    ".context/trazabilidad/registro_fuentes_componentes.json",
    ".context/trazabilidad/registro_fuentes_componentes.md",
    ".github/workflows/security-audit.yml",
    "db/migrations/20261025_h3_admin_members_onboarding_forbidden_status.sql",
    "scripts/security/protected_path_scope_guard.sh",
    "tests/h3_admin_bff_mock_uat.mjs",
    "tests/sql/h3_admin_quota_harness.sql",
    "tests/test_h3_admin_onboarding_denial_contract.py",
    "tests/test_protected_path_scope_guard.sh",
    "tests/test_security_flow.py",
    "web/functions/_lib/admin-bff.ts",
}
d04_included = d04_scope.get("includedPaths")
if not isinstance(d04_included, list) or len(d04_included) != len(set(d04_included)) or set(d04_included) != d04_expected_paths:
    raise SystemExit("protected path integration test: D04 exact candidate path manifest differs from reviewed scope")
d04_excluded = {entry.get("path") for entry in d04_scope.get("excludedPaths", []) if isinstance(entry, dict)}
if d04_excluded != {
    "tests/h3_admin_quota_postgrest.mjs",
    "tests/sql/h3_quota_postgrest_fixture.sql",
}:
    raise SystemExit("protected path integration test: D04 preserved WIP exclusions differ from reviewed scope")
if not d04_expected_paths.issubset(local_paths | {path for path in d04_expected_paths if any(re.search(pattern, path) for pattern in patterns)}):
    raise SystemExit("protected path integration test: D04 exact candidate contains a path outside the guarded allowlist")
for unreviewed_d04 in (
    ".context/evidencia/h3req1_d04_candidate_pr_scope_2026-10-25-extra.json",
    "db/migrations/20261025_h3_admin_members_onboarding_forbidden_status_extra.sql",
    "tests/test_h3_admin_onboarding_denial_contract_extra.py",
):
    if unreviewed_d04 in local_paths or any(re.search(pattern, unreviewed_d04) for pattern in patterns):
        raise SystemExit(
            "protected path integration test: unreviewed D04 sibling is accepted: "
            f"{unreviewed_d04}"
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

python3 - "$ROOT/.context/evidencia/h3req1_public_admin_corrections_2026-10-26/candidate-pr-scope-2026-10-26.json" \
  "$ROOT/.context/evidencia/h3req1_public_admin_corrections_2026-10-26/candidate-scope-manifest-2026-10-26.json" \
  "$ROOT/scripts/security/protected_path_scope_guard.sh" "$ROOT/.github/workflows/security-audit.yml" "$ROOT" <<'PY'
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

scope_path, manifest_path, guard_path, workflow_path, root = map(Path, sys.argv[1:])
scope = json.loads(scope_path.read_text(encoding="utf-8"))
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
guard = guard_path.read_text(encoding="utf-8")
workflow = workflow_path.read_text(encoding="utf-8")

expected_paths = {
    ".github/workflows/security-audit.yml",
    "scripts/security/protected_path_scope_guard.sh",
    "tests/test_protected_path_scope_guard.sh",
    "scripts/maintenance/h3req1_documentation_integrity.mjs",
    "tests/h3_duration_parser.test.mjs",
    "tests/h3_local_uat.mjs",
    "web/src/app/HomeContent.tsx",
    "web/src/app/admin/page.tsx",
    "web/src/components/AdminCourseQueue.tsx",
    "web/src/lib/supabase.ts",
    "tests/admin_header_responsive.test.mjs",
    "tests/admin_queue_request_guard.test.mjs",
    "web/src/lib/admin-queue-request-guard.mjs",
    ".context/componentes/web_publico.md",
    ".context/componentes/admin_portal.md",
    ".context/componentes/pruebas_evidencia.md",
    ".context/indice.md",
    ".context/trazabilidad/registro_fuentes_componentes.json",
    ".context/trazabilidad/registro_fuentes_componentes.md",
    ".context/evidencia/h3req1_public_admin_corrections_2026-10-26/candidate-pr-scope-2026-10-26.json",
    ".context/evidencia/h3req1_public_admin_corrections_2026-10-26/candidate-scope-manifest-2026-10-26.json",
    ".context/evidencia/h3req1_public_admin_corrections_2026-10-26/candidate-pr-body-2026-10-26.md",
}
expected_additions = {
    "tests/admin_header_responsive.test.mjs",
    "tests/admin_queue_request_guard.test.mjs",
    "web/src/lib/admin-queue-request-guard.mjs",
    ".context/evidencia/h3req1_public_admin_corrections_2026-10-26/candidate-pr-scope-2026-10-26.json",
    ".context/evidencia/h3req1_public_admin_corrections_2026-10-26/candidate-scope-manifest-2026-10-26.json",
    ".context/evidencia/h3req1_public_admin_corrections_2026-10-26/candidate-pr-body-2026-10-26.md",
}
included = scope.get("includedPaths")
remediation = scope.get("protectedPathRemediation", {})
if (
    scope.get("target", {}).get("baseBranch") != "desarrollo"
    or not isinstance(included, list)
    or len(included) != 22
    or len(included) != len(set(included))
    or set(included) != expected_paths
    or remediation.get("currentPrChangedPathCount") != 22
    or remediation.get("currentlyRejectedByGuardCount") != 6
    or remediation.get("exactAdditionalAllowlistPathCount") != 6
    or set(remediation.get("exactAdditionalAllowedH3LocalPaths", [])) != expected_additions
):
    raise SystemExit("R21 scope regression: exact 22-path package or six-path guard delta changed")

local_match = re.search(r"<<'H3_LOCAL_PATHS'\s*\n(?P<body>.*?)\n\s*H3_LOCAL_PATHS", guard, re.DOTALL)
if not local_match:
    raise SystemExit("R21 scope regression: exact local allowlist missing")
local_paths = {line.strip() for line in local_match.group("body").splitlines() if line.strip()}
if not expected_additions.issubset(local_paths):
    raise SystemExit("R21 scope regression: an exact path is missing from the reviewed local allowlist")

manifest_paths = {
    entry["path"] for entry in manifest.get("scope", {}).get("entries", [])
    if isinstance(entry, dict) and entry.get("status") != "deleted" and isinstance(entry.get("path"), str)
}
manifest_paths.update(
    artifact["path"] for artifact in manifest.get("package_artifacts", {}).values()
    if isinstance(artifact, dict) and artifact.get("included") is True and isinstance(artifact.get("path"), str)
)
if manifest.get("manifest_id") != "R21-public-admin-corrections-2026-10-26":
    raise SystemExit("R21 scope regression: manifest identity changed")
if manifest.get("successor_of", {}).get("manifest") != ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-scope-manifest.json":
    raise SystemExit("R21 scope regression: R20 predecessor is not preserved")
historical_r20 = json.loads((root / ".context/evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-scope-manifest.json").read_text(encoding="utf-8"))
historical_r19_path = ".context/evidencia/h3req1_pr_scope_manifest_2026-10-19_r19_pwi_r3_reconciled.json"
if (
    historical_r20.get("successor_of", {}).get("manifest") != historical_r19_path
    or not (root / historical_r19_path).is_file()
):
    raise SystemExit("R21 scope regression: historical R19/R20 manifest chain is not preserved")
if not expected_paths.issubset(manifest_paths):
    raise SystemExit("R21 scope regression: PR paths are not selected by the candidate-aware manifest")
documentation_job = workflow.split("  documentation-integrity:", 1)[1].split("\n  python-check:", 1)[0]
if (
    "candidate-scope-manifest-2026-10-26.json" not in workflow
    or "h3req1_d04_candidate_docs_scope_2026-10-25.json" not in workflow
    or "fetch-depth: 0" not in documentation_job
    or "# h3req1-manifest-selector:start" not in documentation_job
    or "# h3req1-manifest-selector:end" not in documentation_job
):
    raise SystemExit("R21 scope regression: workflow must retain the trusted history and expose the tested manifest selector")
for test_path in ("admin_header_responsive.test.mjs", "admin_queue_request_guard.test.mjs"):
    if f"node ../tests/{test_path}" not in workflow:
        raise SystemExit(f"R21 scope regression: workflow omits {test_path}")

registry = json.loads((root / ".context/trazabilidad/registro_fuentes_componentes.json").read_text(encoding="utf-8"))
candidate_only = {path for group in registry["groups"] for path in group.get("candidate_only_paths", [])}
selected_candidate_only = manifest_paths & candidate_only & expected_paths
if len(selected_candidate_only) != 5:
    raise SystemExit(f"R21 scope regression: expected five candidate-only source/test paths in this exact PR, found {len(selected_candidate_only)}")

excluded = set(scope.get("excludedPaths", []))
for forbidden in (
    "db/migrations/20261025_h3_admin_members_onboarding_forbidden_status.sql",
    "tests/sql/h3_quota_postgrest_fixture.sql",
    ".context/evidencia/h3req1_editorial_fixtures_2026-10-26/seed_d07_d11_free.sql",
    "web/functions/_lib/admin-bff.ts",
):
    if forbidden in included or forbidden not in excluded:
        raise SystemExit(f"R21 scope regression: unrelated fixture/Admin WIP inclusion or exclusion drift: {forbidden}")

print("protected-path-R21-manifest-integration=PASS|candidate_paths=22|exact_additions=6|selected_candidate_only_source_and_test_paths=5|R20_preserved=1")

selector_lines = documentation_job.splitlines()
selector_start = selector_lines.index("          # h3req1-manifest-selector:start")
selector_end = selector_lines.index("          # h3req1-manifest-selector:end")
selector_script = "\n".join(
    line[10:] if line.startswith("          ") else line
    for line in selector_lines[selector_start + 1:selector_end]
)
if not selector_script.strip():
    raise SystemExit("R21 scope regression: tested selector block is empty")

def git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()

def write_manifest(repo, relative, manifest_id):
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "manifest_id": manifest_id,
        "manifest_role": "candidate-aware documentation integrity selection",
        "scope": {"entries": []},
        "package_artifacts": {},
    }), encoding="utf-8")

def create_repo(root, name, include_r21=True):
    repo = root / name
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Manifest selector regression")
    git(repo, "config", "user.email", "selector-regression@example.invalid")
    if include_r21:
        write_manifest(repo, ".context/evidencia/r21.json", "R21")
        write_manifest(repo, ".context/evidencia/r20.json", "R20")
        write_manifest(repo, ".context/evidencia/r19.json", "R19")
    write_manifest(repo, ".context/evidencia/d04.json", "D04")
    (repo / "README.md").write_text("baseline\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "baseline")
    return repo, git(repo, "rev-parse", "HEAD")

def commit(repo, message):
    git(repo, "add", ".")
    git(repo, "commit", "-qm", message)

def run_selector(repo, base_sha, r21_path, d04_path):
    output = repo / "github-output.txt"
    output.unlink(missing_ok=True)
    env = os.environ.copy()
    env.update({
        "PROTECTED_BASELINE_SHA": base_sha,
        "R21_MANIFEST": r21_path,
        "D04_MANIFEST": d04_path,
        "GITHUB_OUTPUT": str(output),
    })
    result = subprocess.run(
        ["bash", "-e", "-c", selector_script], cwd=repo, env=env,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    selected = None
    if output.exists():
        for line in output.read_text(encoding="utf-8").splitlines():
            if line.startswith("path="):
                selected = line.removeprefix("path=")
    return result, selected

with tempfile.TemporaryDirectory(prefix="h3req1-manifest-selector-") as temp_dir:
    temp_root = Path(temp_dir)
    r21_path = ".context/evidencia/r21.json"
    d04_path = ".context/evidencia/d04.json"

    repo, base = create_repo(temp_root, "successor")
    write_manifest(repo, ".context/evidencia/r22.json", "R22")
    commit(repo, "add successor manifest")
    result, selected = run_selector(repo, base, r21_path, d04_path)
    if result.returncode != 0 or selected != ".context/evidencia/r22.json":
        raise SystemExit("R21 selector regression: successor manifest was not preferred over persistent R21")

    repo, base = create_repo(temp_root, "d04")
    write_manifest(repo, d04_path, "D04-successor")
    commit(repo, "update D04 candidate manifest")
    result, selected = run_selector(repo, base, r21_path, d04_path)
    if result.returncode != 0 or selected != d04_path:
        raise SystemExit("R21 selector regression: changed D04 candidate manifest was not selected")

    repo, base = create_repo(temp_root, "fallback")
    (repo / "README.md").write_text("ordinary code change\n", encoding="utf-8")
    commit(repo, "ordinary change")
    result, selected = run_selector(repo, base, r21_path, d04_path)
    if result.returncode != 0 or selected != r21_path:
        raise SystemExit("R21 selector regression: R21 fallback changed when no candidate manifest changed")

    repo, base = create_repo(temp_root, "d04-fallback", include_r21=False)
    (repo / "README.md").write_text("ordinary change\n", encoding="utf-8")
    commit(repo, "ordinary change")
    result, selected = run_selector(repo, base, r21_path, d04_path)
    if result.returncode != 0 or selected != d04_path:
        raise SystemExit("R21 selector regression: D04 fallback was not preserved without R21")

    repo, base = create_repo(temp_root, "ambiguous")
    write_manifest(repo, ".context/evidencia/r22.json", "R22")
    write_manifest(repo, d04_path, "D04-successor")
    commit(repo, "change two candidate manifests")
    result, selected = run_selector(repo, base, r21_path, d04_path)
    if result.returncode == 0 or selected is not None:
        raise SystemExit("R21 selector regression: ambiguous candidate manifests did not fail closed")

    repo, base = create_repo(temp_root, "deleted-successor")
    (repo / r21_path).unlink()
    commit(repo, "delete persistent R21 manifest")
    result, selected = run_selector(repo, base, r21_path, d04_path)
    if result.returncode == 0 or selected is not None:
        raise SystemExit("R21 selector regression: deleting a historical candidate manifest did not fail closed")

    repo, base = create_repo(temp_root, "renamed-successor")
    renamed = repo / ".context/archive/r21.json"
    renamed.parent.mkdir(parents=True, exist_ok=True)
    (repo / r21_path).rename(renamed)
    commit(repo, "move persistent candidate manifest out of evidence")
    result, selected = run_selector(repo, base, r21_path, d04_path)
    if result.returncode == 0 or selected is not None:
        raise SystemExit("R21 selector regression: moving a historical candidate manifest out of evidence did not fail closed")

    repo, base = create_repo(temp_root, "invalid")
    invalid = repo / ".context/evidencia/candidate-scope-manifest-r22.json"
    invalid.write_text("{invalid json", encoding="utf-8")
    commit(repo, "add invalid successor manifest")
    result, selected = run_selector(repo, base, r21_path, d04_path)
    if result.returncode == 0 or selected is not None:
        raise SystemExit("R21 selector regression: invalid candidate manifest did not fail closed")

    repo, base = create_repo(temp_root, "invalid-structure")
    invalid = repo / ".context/evidencia/candidate-scope-manifest-r22.json"
    invalid.write_text(json.dumps({
        "manifest_id": "R22",
        "manifest_role": "candidate-aware documentation integrity selection",
        "scope": {"entries": "not-an-array"},
        "package_artifacts": {},
    }), encoding="utf-8")
    commit(repo, "add malformed successor manifest")
    result, selected = run_selector(repo, base, r21_path, d04_path)
    if result.returncode == 0 or selected is not None:
        raise SystemExit("R21 selector regression: structurally invalid candidate did not fail closed")

    repo, base = create_repo(temp_root, "wrong-role")
    wrong_role = repo / ".context/evidencia/candidate-scope-manifest-r22.json"
    wrong_role.write_text(json.dumps({
        "manifest_id": "R22",
        "manifest_role": "unrelated documentation manifest",
        "scope": {"entries": []},
        "package_artifacts": {},
    }), encoding="utf-8")
    commit(repo, "add candidate manifest with unexpected role")
    result, selected = run_selector(repo, base, r21_path, d04_path)
    if result.returncode == 0 or selected is not None:
        raise SystemExit("R21 selector regression: candidate manifest with unexpected role fell back instead of failing closed")

    repo, base = create_repo(temp_root, "no-baseline")
    env = os.environ.copy()
    output = repo / "github-output.txt"
    env.update({"PROTECTED_BASELINE_SHA": "", "R21_MANIFEST": r21_path,
                "D04_MANIFEST": d04_path, "GITHUB_OUTPUT": str(output)})
    result = subprocess.run(
        ["bash", "-e", "-c", selector_script], cwd=repo, env=env,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode == 0 or output.exists():
        raise SystemExit("R21 selector regression: missing trusted baseline did not fail closed")

print("candidate-manifest-selector-regressions=PASS|successor=1|D04_changed=1|R21_fallback=1|D04_fallback=1|ambiguous=fail_closed|deleted_manifest=fail_closed|renamed_manifest=fail_closed|invalid_json=fail_closed|invalid_structure=fail_closed|wrong_role=fail_closed|baseline_missing=fail_closed")
PY
