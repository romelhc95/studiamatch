from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS_ROOT = ROOT / "tests" / "e2e" / "ca1"


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_ca1_harness_manifest_lists_trusted_files() -> None:
    manifest = json.loads((HARNESS_ROOT / "harness_manifest_paths.json").read_text(encoding="utf-8"))
    paths = manifest["paths"]

    assert manifest["schema"] == "studiamatch.ca1_harness_paths.v1"
    assert "tests/e2e/ca1/ca1_functional_gate.py" in paths
    assert "tests/test_fase09_9_ca1_reactivation.py" in paths
    assert all(not path.startswith(("scripts/core/", "scripts/shared/", "db/", "supabase/", "web/")) for path in paths)
    for path in paths:
        assert (ROOT / path).exists(), path


def test_ca1_harness_has_dual_expected_decision_contract() -> None:
    harness = source("tests/e2e/ca1/ca1_functional_gate.py")

    assert "GO_TO_PREPARE_CERTIFICATION_PR" in harness
    assert "NO_GO_KNOWN_T_H1_CA1_002B" in harness
    assert "--expected-decision" in harness
    assert "--runtime-manifest-file" in harness
    assert "--harness-manifest-file" in harness
    assert "--runtime-manifest-b64" in harness
    assert "--harness-manifest-b64" in harness
    assert "CA1_MODE_LENIENT" in harness
    assert "CA1_CONTENT_LENIENT" in harness
    assert "classify_known_defect" in harness
    assert "expected pending" in harness
    assert "got discovered" in harness


def test_ca1_harness_generates_required_artifacts_and_sanitizes_secrets() -> None:
    harness = source("tests/e2e/ca1/ca1_functional_gate.py")

    assert "summary.json" in harness
    assert "junit.xml" in harness
    assert "redacted-logs.json" in harness
    assert "[SYNTHETIC_SECRET]" in harness
    assert "[SYNTHETIC_PUBLISHABLE]" in harness
    assert "egress_attempts" in harness
    assert "SYNTHETIC_SECRET_KEY" not in harness
    assert "sb_secret_" not in harness


def test_ca1_harness_exercises_fg1_fg2_cleansing_partial_paths() -> None:
    harness = source("tests/e2e/ca1/ca1_functional_gate.py")

    assert "scripts/core/discovery_institutions.py" in harness
    assert "scripts/core/universal_harvester.py" in harness
    assert "scripts/core/cleansing_worker.py" in harness
    assert "run_three_pass_case" in harness
    assert "run_partial_case" in harness
    assert "freshness changed after partial run" in harness
    assert "third run fetched a protected pending URL" in harness


def test_security_audit_contains_target_aware_f99_bootstrap_gate() -> None:
    workflow = source(".github/workflows/security-audit.yml")

    assert "fase09-9-ca1-reactivation:" in workflow
    assert "F9.9 CA1 Reactivation Functional Gate" in workflow
    assert "github.event.pull_request.base.sha" in workflow
    assert "github.event.before" in workflow
    assert "tests/e2e/ca1/ca1_functional_gate.py" in workflow
    assert "scripts/core/cleansing_worker.py" in workflow
    assert "NO_GO_KNOWN_T_H1_CA1_002B" in workflow
    assert "GO_TO_PREPARE_CERTIFICATION_PR" in workflow
    assert "F99_EVIDENCE_SAFE=true" in workflow
    assert "env.F99_EVIDENCE_SAFE == 'true'" in workflow
    assert "candidate_secret_rc" in workflow
    assert "evidence_secret_rc" in workflow
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow
    assert "needs.fase09-9-ca1-reactivation.result" in workflow
    assert "F99: ${{ needs.fase09-9-ca1-reactivation.result }}" in workflow


def test_security_audit_blocks_runtime_and_harness_in_same_pr_after_bootstrap() -> None:
    workflow = source(".github/workflows/security-audit.yml")

    assert "F99_RUNTIME_CHANGED" in workflow
    assert "F99_HARNESS_CHANGED" in workflow
    assert "F99_BASE_HAS_HARNESS" in workflow
    assert "Runtime and harness changed together after bootstrap" in workflow
    assert "base lacks trusted harness" in workflow


def test_bootstrap_does_not_modify_runtime_paths() -> None:
    harness = source("tests/e2e/ca1/ca1_functional_gate.py")

    assert "scripts/core/universal_harvester.py" in harness
    assert "config_path.write_text" in harness
    assert "scripts/core/universal_harvester.py\", \"w" not in harness
    assert "scripts/shared/db_client.py\", \"w" not in harness
    assert "open(\"scripts/core" not in harness
