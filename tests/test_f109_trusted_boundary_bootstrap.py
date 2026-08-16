from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from scripts.security.f109_trusted_boundary_bootstrap import (
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


def _event(base: str, head: str, *, head_repo: str = "romelhc95/studiamatch") -> dict[str, object]:
    return {
        "pull_request": {
            "base": {
                "ref": "desarrollo",
                "sha": base,
                "repo": {"full_name": "romelhc95/studiamatch", "fork": False},
            },
            "head": {
                "ref": PR_N_LINK_HARDENING_HEAD_REF,
                "sha": head,
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
    }
    values.update(overrides)
    return validate_trusted_boundary(repo, event, **values)


def test_trusted_boundary_accepts_one_direct_exact_same_repo_candidate() -> None:
    repo, base, head, temp = _build_repo()
    with temp:
        assert _validate(repo, base, head, _event(base, head)) == "PR_N_LINK_HARDENING_CLOSURE"


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
