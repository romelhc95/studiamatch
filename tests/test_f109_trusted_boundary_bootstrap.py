from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from scripts.security.f109_trusted_boundary_bootstrap import (
    FORBIDDEN_PR_N_PATHS,
    FORBIDDEN_PR_N_PREFIXES,
    PR_N_LINK_HARDENING_ALLOWED_STATUSES,
    PR_N_LINK_HARDENING_HEAD_REF,
    TRUSTED_CHECK_NAME,
    TrustedBoundaryError,
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


def test_trusted_boundary_accepts_one_direct_exact_same_repo_candidate() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        assert _validate(repo, base, head, _event(base, head)) == "PR_N_LINK_HARDENING_CLOSURE"


def test_pr_n_allowlist_excludes_workflows_and_trusted_validator() -> None:
    assert not any(path.startswith(FORBIDDEN_PR_N_PREFIXES) for path in PR_N_LINK_HARDENING_ALLOWED_STATUSES)
    assert not FORBIDDEN_PR_N_PATHS.intersection(PR_N_LINK_HARDENING_ALLOWED_STATUSES)
    assert ".github/workflows/f9-7-contract.yml" not in PR_N_LINK_HARDENING_ALLOWED_STATUSES
    assert "scripts/security/f109_trusted_boundary_bootstrap.py" not in PR_N_LINK_HARDENING_ALLOWED_STATUSES


def test_trusted_boundary_accepts_edited_event_when_metadata_stays_protected() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        assert _validate(repo, base, head, _event(base, head, action="edited")) == "PR_N_LINK_HARDENING_CLOSURE"


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
        with pytest.raises(TrustedBoundaryError, match="duplicate trusted boundary check name"):
            _validate(repo, base, head, _event(base, head), check_name="F10.9 Trusted Boundary Bootstrap")


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
        with pytest.raises(TrustedBoundaryError, match="file mode drift"):
            _validate(repo, base, drift_head, _event(base, drift_head))


def test_trusted_boundary_rejects_renames() -> None:
    repo, base, _head, temp = _build_repo()
    with temp:
        _git(repo, "checkout", "-q", base)
        relative = next(iter(PR_N_LINK_HARDENING_ALLOWED_STATUSES))
        path = repo / relative
        path.rename(repo / f"{relative}.renamed")
        drift_head = _commit_current(repo, "rename drift")
        with pytest.raises(TrustedBoundaryError, match="renames/copies"):
            _validate(repo, base, drift_head, _event(base, drift_head))


def test_trusted_boundary_rejects_inconsistent_metadata() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        with pytest.raises(TrustedBoundaryError, match="event head sha drift"):
            _validate(repo, base, head, _event(base, head, event_head_sha="c" * 40))
