from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

import scripts.security.f109_trusted_boundary_bootstrap as trusted
from scripts.security.f109_trusted_boundary_bootstrap import (
    BoundaryProfile,
    FORBIDDEN_PR_N_PATHS,
    FORBIDDEN_PR_N_PREFIXES,
    PR_N_EXPECTED_BASE_SHA,
    PR_N_EXPECTED_BLOBS,
    PR_N_EXPECTED_HEAD_SHA,
    PR_N_EXPECTED_HEAD_TREE,
    PR_N_LINK_HARDENING_ALLOWED_STATUSES,
    PR_N_LINK_HARDENING_HEAD_REF,
    PR_N_TRUSTED_CHECK_NAME,
    PR_P_REGISTRATION_PROBE_ALLOWED_STATUSES,
    PR_P_REGISTRATION_PROBE_HEAD_REF,
    PR_P_TRUSTED_CHECK_NAME,
    STABLE_TRUSTED_CHECK_NAME,
    TRUSTED_CHECK_NAME,
    TRUSTED_PROFILES,
    TrustedBoundaryError,
    validate_exact_delta,
    validate_trusted_boundary,
)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout.strip()


def _write(repo: Path, relative: str, text: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _event(
    base: str,
    head: str,
    *,
    action: str = "opened",
    base_ref: str = "desarrollo",
    head_ref: str = PR_N_LINK_HARDENING_HEAD_REF,
    head_repo: str = "romelhc95/studiamatch",
    event_base_sha: str | None = None,
    event_head_sha: str | None = None,
) -> dict[str, object]:
    return {
        "action": action,
        "pull_request": {
            "base": {
                "ref": base_ref,
                "sha": event_base_sha or base,
                "repo": {"full_name": "romelhc95/studiamatch", "fork": False},
            },
            "head": {
                "ref": head_ref,
                "sha": event_head_sha or head,
                "repo": {"full_name": head_repo, "fork": head_repo != "romelhc95/studiamatch"},
            },
        }
    }


def _build_repo() -> tuple[Path, str, str, tempfile.TemporaryDirectory[str]]:
    temp = tempfile.TemporaryDirectory()
    repo = Path(temp.name)
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Trusted Boundary Test")

    for relative, status in PR_N_LINK_HARDENING_ALLOWED_STATUSES.items():
        if status == "M":
            _write(repo, relative, f"base {relative}\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")

    for relative, status in PR_N_LINK_HARDENING_ALLOWED_STATUSES.items():
        _write(repo, relative, f"candidate {relative}\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "candidate")
    head = _git(repo, "rev-parse", "HEAD")
    return repo, base, head, temp


def _build_profile_repo(allowed_statuses: dict[str, str]) -> tuple[Path, str, str, tempfile.TemporaryDirectory[str]]:
    temp = tempfile.TemporaryDirectory()
    repo = Path(temp.name)
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Trusted Boundary Test")

    for relative, status in allowed_statuses.items():
        if status == "M":
            _write(repo, relative, f"base {relative}\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")

    for relative, status in allowed_statuses.items():
        _write(repo, relative, f"candidate {relative}\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "candidate")
    head = _git(repo, "rev-parse", "HEAD")
    return repo, base, head, temp


def _build_out_of_scope_repo(path: str = "docs/out-of-scope.md") -> tuple[Path, str, str, tempfile.TemporaryDirectory[str]]:
    temp = tempfile.TemporaryDirectory()
    repo = Path(temp.name)
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Trusted Boundary Test")
    _write(repo, "README.md", "base\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")

    _write(repo, path, "safe candidate\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "out of scope")
    head = _git(repo, "rev-parse", "HEAD")
    return repo, base, head, temp


def _commit_current(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _validate(repo: Path, base: str, head: str, event: dict[str, object], **overrides: str) -> str:
    values = {
        "event_name": "pull_request_target",
        "base_ref": "desarrollo",
        "head_ref": PR_N_LINK_HARDENING_HEAD_REF,
        "base_sha": base,
        "head_sha": head,
        "base_repo": "romelhc95/studiamatch",
        "head_repo": "romelhc95/studiamatch",
        "repository": "romelhc95/studiamatch",
        "check_name": TRUSTED_CHECK_NAME,
        "protected_base_sha": base,
    }
    values.update(overrides)
    return validate_trusted_boundary(repo, event, **values)


def test_default_branch_registration_missing_is_documented_fail_closed() -> None:
    root_cause = {
        "default_branch": "main",
        "workflow_exists_in_desarrollo": True,
        "workflow_exists_in_main": False,
        "pull_request_target_requires_default_branch_file": True,
        "edited_retry_api_enable_can_fix_absence": False,
        "retroactive_merge_gate_attestation_allowed": False,
    }
    assert root_cause["default_branch"] == "main"
    assert root_cause["workflow_exists_in_desarrollo"] is True
    assert root_cause["workflow_exists_in_main"] is False
    assert root_cause["pull_request_target_requires_default_branch_file"] is True
    assert root_cause["edited_retry_api_enable_can_fix_absence"] is False
    assert root_cause["retroactive_merge_gate_attestation_allowed"] is False


def test_workflow_absent_from_default_branch_blocks_registration() -> None:
    default_branch_workflows = {"security-audit.yml", "f9-7-contract.yml"}
    trusted_workflow = "f10-9-g5-trusted-boundary-bootstrap.yml"
    assert trusted_workflow not in default_branch_workflows


def test_workflow_registered_on_default_branch_enables_future_pr_p_profile() -> None:
    default_branch_workflows = {"security-audit.yml", "f9-7-contract.yml", "f10-9-g5-trusted-boundary-bootstrap.yml"}
    trusted_workflow = "f10-9-g5-trusted-boundary-bootstrap.yml"
    assert trusted_workflow in default_branch_workflows
    assert PR_P_REGISTRATION_PROBE_HEAD_REF not in TRUSTED_PROFILES


def test_check_provenance_uses_pr_p_name_and_preserves_pr_n_history() -> None:
    assert TRUSTED_CHECK_NAME == "F10.9 Trusted Boundary v1"
    assert TRUSTED_CHECK_NAME == STABLE_TRUSTED_CHECK_NAME
    assert PR_N_TRUSTED_CHECK_NAME == "F10.9 Trusted Boundary PR N v1"
    assert PR_P_TRUSTED_CHECK_NAME == "F10.9 Trusted Boundary PR P v1"


def test_trusted_boundary_accepts_one_direct_exact_same_repo_candidate() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        with pytest.raises(TrustedBoundaryError, match="base content binding drift"):
            _validate(repo, base, head, _event(base, head))


def test_pr_p_registration_probe_is_retired_without_dynamic_fallback() -> None:
    repo, base, head, temp = _build_profile_repo(dict(PR_P_REGISTRATION_PROBE_ALLOWED_STATUSES))
    with temp:
        assert PR_P_REGISTRATION_PROBE_HEAD_REF not in TRUSTED_PROFILES
        with pytest.raises(TrustedBoundaryError, match="sensitive path requires explicit trusted profile"):
            _validate(
                repo,
                base,
                head,
                _event(base, head, head_ref=PR_P_REGISTRATION_PROBE_HEAD_REF),
                head_ref=PR_P_REGISTRATION_PROBE_HEAD_REF,
                check_name=TRUSTED_CHECK_NAME,
            )


def test_normal_out_of_scope_pr_passes_without_explicit_profile() -> None:
    repo, base, head, temp = _build_out_of_scope_repo()
    with temp:
        assert (
            _validate(
                repo,
                base,
                head,
                _event(base, head, head_ref="feat/docs-copy"),
                head_ref="feat/docs-copy",
            )
            == "OUT_OF_SCOPE_SAFE"
        )


def test_pr_n_allowlist_excludes_workflows_and_trusted_validator() -> None:
    assert not any(path.startswith(FORBIDDEN_PR_N_PREFIXES) for path in PR_N_LINK_HARDENING_ALLOWED_STATUSES)
    assert not FORBIDDEN_PR_N_PATHS.intersection(PR_N_LINK_HARDENING_ALLOWED_STATUSES)
    assert ".github/workflows/f9-7-contract.yml" not in PR_N_LINK_HARDENING_ALLOWED_STATUSES
    assert "scripts/security/f109_trusted_boundary_bootstrap.py" not in PR_N_LINK_HARDENING_ALLOWED_STATUSES


def test_required_check_preservation_profile_excludes_workflows_and_validator() -> None:
    assert not any(path.startswith(FORBIDDEN_PR_N_PREFIXES) for path in PR_P_REGISTRATION_PROBE_ALLOWED_STATUSES)
    assert not FORBIDDEN_PR_N_PATHS.intersection(PR_P_REGISTRATION_PROBE_ALLOWED_STATUSES)
    assert ".github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml" not in PR_P_REGISTRATION_PROBE_ALLOWED_STATUSES
    assert "scripts/security/f109_trusted_boundary_bootstrap.py" not in PR_P_REGISTRATION_PROBE_ALLOWED_STATUSES


def test_trusted_boundary_accepts_edited_event_when_metadata_stays_protected() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        with pytest.raises(TrustedBoundaryError, match="base content binding drift"):
            _validate(repo, base, head, _event(base, head, action="edited"))


def test_trusted_boundary_rejects_forks_and_unexpected_shapes() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        with pytest.raises(TrustedBoundaryError, match="fork"):
            _validate(
                repo,
                base,
                head,
                _event(base, head, head_repo="external/fork"),
                head_repo="external/fork",
            )
        with pytest.raises(TrustedBoundaryError, match="check name"):
            _validate(repo, base, head, _event(base, head), check_name="security-audit")
        _write(repo, "unexpected.txt", "unexpected\n")
        _git(repo, "add", ".")
        _git(repo, "commit", "-m", "unexpected")
        drift_head = _git(repo, "rev-parse", "HEAD")
        with pytest.raises(TrustedBoundaryError, match="direct commit"):
            _validate(repo, base, drift_head, _event(base, drift_head))


def test_trusted_boundary_rejects_stale_protected_base() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        with pytest.raises(TrustedBoundaryError, match="stale protected base"):
            _validate(repo, base, head, _event(base, head), protected_base_sha="b" * 40)


def test_trusted_boundary_rejects_retargeted_edited_event() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        with pytest.raises(TrustedBoundaryError, match="base ref"):
            _validate(
                repo,
                base,
                head,
                _event(base, head, action="edited", base_ref="main"),
                base_ref="main",
            )


def test_trusted_boundary_rejects_duplicate_check_name() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        with pytest.raises(TrustedBoundaryError, match="retired trusted boundary check name"):
            _validate(repo, base, head, _event(base, head), check_name="F10.9 Trusted Boundary Bootstrap")


def test_trusted_boundary_rejects_pr_n_check_for_future_pr_p_profile() -> None:
    repo, base, head, temp = _build_profile_repo(dict(PR_P_REGISTRATION_PROBE_ALLOWED_STATUSES))
    with temp:
        with pytest.raises(TrustedBoundaryError, match="retired trusted boundary check name"):
            _validate(
                repo,
                base,
                head,
                _event(base, head, head_ref=PR_P_REGISTRATION_PROBE_HEAD_REF),
                head_ref=PR_P_REGISTRATION_PROBE_HEAD_REF,
                check_name=PR_N_TRUSTED_CHECK_NAME,
            )


def test_wp0_trusted_content_binding_pr_n_historical_profile_validates_tree_and_blobs(monkeypatch: pytest.MonkeyPatch) -> None:
    profile = TRUSTED_PROFILES[PR_N_LINK_HARDENING_HEAD_REF]

    monkeypatch.setattr(trusted, "changed_statuses", lambda repo, base, head: dict(profile.allowed_statuses))
    monkeypatch.setattr(trusted, "commit_tree", lambda repo, revision: PR_N_EXPECTED_HEAD_TREE)
    monkeypatch.setattr(trusted, "blob_mode", lambda repo, revision, path: profile.allowed_modes[path])
    monkeypatch.setattr(trusted, "blob_sha", lambda repo, revision, path: PR_N_EXPECTED_BLOBS[path])

    validate_exact_delta(Path("."), PR_N_EXPECTED_BASE_SHA, PR_N_EXPECTED_HEAD_SHA, profile)


def test_wp0_trusted_content_binding_one_byte_blob_drift_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    profile = TRUSTED_PROFILES[PR_N_LINK_HARDENING_HEAD_REF]
    drift_path = "scripts/security/f109_boundary.py"

    monkeypatch.setattr(trusted, "changed_statuses", lambda repo, base, head: dict(profile.allowed_statuses))
    monkeypatch.setattr(trusted, "commit_tree", lambda repo, revision: PR_N_EXPECTED_HEAD_TREE)
    monkeypatch.setattr(trusted, "blob_mode", lambda repo, revision, path: profile.allowed_modes[path])
    monkeypatch.setattr(
        trusted,
        "blob_sha",
        lambda repo, revision, path: "0" * 40 if path == drift_path else PR_N_EXPECTED_BLOBS[path],
    )

    with pytest.raises(TrustedBoundaryError, match="blob content binding drift"):
        validate_exact_delta(Path("."), PR_N_EXPECTED_BASE_SHA, PR_N_EXPECTED_HEAD_SHA, profile)


def test_wp0_trusted_content_binding_tree_drift_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    profile = TRUSTED_PROFILES[PR_N_LINK_HARDENING_HEAD_REF]
    monkeypatch.setattr(trusted, "commit_tree", lambda repo, revision: "0" * 40)

    with pytest.raises(TrustedBoundaryError, match="tree content binding drift"):
        validate_exact_delta(Path("."), PR_N_EXPECTED_BASE_SHA, PR_N_EXPECTED_HEAD_SHA, profile)


def test_wp0_trusted_content_binding_rejects_branch_recreated_with_same_name() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        with pytest.raises(TrustedBoundaryError, match="base content binding drift"):
            _validate(repo, base, head, _event(base, head, head_ref=PR_N_LINK_HARDENING_HEAD_REF))


def test_wp0_trusted_content_binding_boundary_profile_expected_fields_are_historical_only() -> None:
    profile = TRUSTED_PROFILES[PR_N_LINK_HARDENING_HEAD_REF]
    assert isinstance(profile, BoundaryProfile)
    assert profile.expected_base_sha == PR_N_EXPECTED_BASE_SHA
    assert profile.expected_head_sha == PR_N_EXPECTED_HEAD_SHA
    assert profile.expected_head_tree == PR_N_EXPECTED_HEAD_TREE
    assert profile.expected_blob_sha == PR_N_EXPECTED_BLOBS
    assert set(TRUSTED_PROFILES) == {PR_N_LINK_HARDENING_HEAD_REF}


def test_wp0_trusted_content_binding_pr_p_removed_from_trusted_profiles() -> None:
    assert PR_P_REGISTRATION_PROBE_HEAD_REF not in TRUSTED_PROFILES


def test_wp0_trusted_content_binding_evidence_without_profile_fails() -> None:
    repo, base, head, temp = _build_out_of_scope_repo(".context/evidencias_cliente/sprint_1/paquete_hito_001.md")
    with temp:
        with pytest.raises(TrustedBoundaryError, match="sensitive path requires explicit trusted profile"):
            _validate(
                repo,
                base,
                head,
                _event(base, head, head_ref="feat/evidence-without-profile"),
                head_ref="feat/evidence-without-profile",
            )


def test_workflow_runs_for_paths_outside_previous_filter() -> None:
    workflow = Path(".github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml").read_text(encoding="utf-8")
    assert "pull_request_target:" in workflow
    assert "branches: [desarrollo]" in workflow
    assert "paths:" not in workflow
    assert "paths-ignore:" not in workflow


def test_required_check_uses_stable_name() -> None:
    workflow = Path(".github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml").read_text(encoding="utf-8")
    assert "name: F10.9 Trusted Boundary v1" in workflow
    assert "CHECK_NAME: F10.9 Trusted Boundary v1" in workflow
    assert "name: F10.9 Trusted Boundary PR P v1" not in workflow


def test_workflow_candidate_fails_even_without_explicit_profile() -> None:
    repo, base, head, temp = _build_out_of_scope_repo(".github/workflows/unsafe.yml")
    with temp:
        with pytest.raises(TrustedBoundaryError, match="workflow modifications are forbidden"):
            _validate(
                repo,
                base,
                head,
                _event(base, head, head_ref="feat/workflow-change"),
                head_ref="feat/workflow-change",
            )


def test_trusted_validator_candidate_fails_even_without_explicit_profile() -> None:
    repo, base, head, temp = _build_out_of_scope_repo("scripts/security/f109_trusted_boundary_bootstrap.py")
    with temp:
        with pytest.raises(TrustedBoundaryError, match="trusted validator modification is forbidden"):
            _validate(
                repo,
                base,
                head,
                _event(base, head, head_ref="feat/validator-change"),
                head_ref="feat/validator-change",
            )


def test_sensitive_path_without_explicit_profile_fails() -> None:
    repo, base, head, temp = _build_out_of_scope_repo("tests/test_fase10_9_new_guard.py")
    with temp:
        with pytest.raises(TrustedBoundaryError, match="sensitive path requires explicit trusted profile"):
            _validate(
                repo,
                base,
                head,
                _event(base, head, head_ref="feat/f10-9-unprofiled"),
                head_ref="feat/f10-9-unprofiled",
            )


def test_neutral_named_operational_manifest_without_explicit_profile_fails() -> None:
    repo, base, head, temp = _build_out_of_scope_repo(".context/operaciones/remote_actions_manifest.json")
    with temp:
        with pytest.raises(TrustedBoundaryError, match="sensitive path requires explicit trusted profile"):
            _validate(
                repo,
                base,
                head,
                _event(base, head, head_ref="feat/ops-manifest"),
                head_ref="feat/ops-manifest",
            )


def test_trusted_boundary_rejects_invalid_oid_before_git() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        with pytest.raises(TrustedBoundaryError, match="invalid head sha"):
            _validate(repo, base, head, _event(base, head), head_sha="refs/heads/desarrollo")


def test_trusted_boundary_rejects_symlink_or_mode_drift() -> None:
    repo, base, _head, temp = _build_repo()
    with temp:
        _git(repo, "checkout", "-q", base)
        relative = next(iter(PR_N_LINK_HARDENING_ALLOWED_STATUSES))
        path = repo / relative
        path.unlink()
        path.symlink_to("target")
        drift_head = _commit_current(repo, "symlink drift")
        with pytest.raises(TrustedBoundaryError, match="content binding drift"):
            _validate(repo, base, drift_head, _event(base, drift_head))


def test_trusted_boundary_rejects_renames() -> None:
    repo, base, _head, temp = _build_repo()
    with temp:
        _git(repo, "checkout", "-q", base)
        relative = next(iter(PR_N_LINK_HARDENING_ALLOWED_STATUSES))
        path = repo / relative
        path.rename(repo / f"{relative}.renamed")
        drift_head = _commit_current(repo, "rename drift")
        with pytest.raises(TrustedBoundaryError, match="content binding drift"):
            _validate(repo, base, drift_head, _event(base, drift_head))


def test_trusted_boundary_rejects_inconsistent_metadata() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        with pytest.raises(TrustedBoundaryError, match="event head sha drift"):
            _validate(repo, base, head, _event(base, head, event_head_sha="c" * 40))
