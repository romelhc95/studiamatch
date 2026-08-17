#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


PROTECTED_BASE_REF = "desarrollo"
PR_N_TRUSTED_CHECK_NAME = "F10.9 Trusted Boundary PR N v1"
TRUSTED_CHECK_NAME = PR_N_TRUSTED_CHECK_NAME
RETIRED_TRUSTED_CHECK_NAMES = {"F10.9 Trusted Boundary Bootstrap"}
PR_N_LINK_HARDENING_HEAD_REF = "feat/f10-9-pr-n-link-hardening-closure"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_ACTIONS = {"opened", "synchronize", "reopened", "ready_for_review", "edited"}
FORBIDDEN_PR_N_PATHS = {"scripts/security/f109_trusted_boundary_bootstrap.py"}
FORBIDDEN_PR_N_PREFIXES = (".github/workflows/",)
GIT_CONFIG_ARGS = (
    "-c",
    "core.hooksPath=/dev/null",
    "-c",
    "protocol.file.allow=never",
)

PR_N_LINK_HARDENING_ALLOWED_STATUSES = {
    ".context/00_INDICE.md": "M",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/decisiones/ADR-0024_g5_link_header_hardening_closure.md": "A",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
    ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
    "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
    "workers/g5-trust-broker/src/index.mjs": "M",
    "workers/g5-trust-broker/test/trust-broker.test.mjs": "M",
}
PR_N_LINK_HARDENING_ALLOWED_MODES = {
    path: "100644" for path in PR_N_LINK_HARDENING_ALLOWED_STATUSES
}


class TrustedBoundaryError(RuntimeError):
    pass


@dataclass(frozen=True)
class BoundaryProfile:
    name: str
    head_ref: str
    allowed_statuses: Mapping[str, str]
    allowed_modes: Mapping[str, str]


TRUSTED_PROFILES = {
    PR_N_LINK_HARDENING_HEAD_REF: BoundaryProfile(
        name="PR_N_LINK_HARDENING_CLOSURE",
        head_ref=PR_N_LINK_HARDENING_HEAD_REF,
        allowed_statuses=PR_N_LINK_HARDENING_ALLOWED_STATUSES,
        allowed_modes=PR_N_LINK_HARDENING_ALLOWED_MODES,
    )
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TrustedBoundaryError(message)


def validate_sha(value: str, label: str) -> None:
    require(bool(SHA_RE.fullmatch(value)), f"invalid {label} sha")


def isolated_git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *GIT_CONFIG_ARGS, "-c", f"safe.directory={repo.resolve()}", *args],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=isolated_git_env(),
    )
    return result.stdout.strip()


def commit_exists(repo: Path, sha: str) -> bool:
    validate_sha(sha, "commit")
    result = subprocess.run(
        ["git", *GIT_CONFIG_ARGS, "-c", f"safe.directory={repo.resolve()}", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=isolated_git_env(),
    )
    return result.returncode == 0


def commit_parents(repo: Path, sha: str) -> list[str]:
    line = git(repo, "rev-list", "--parents", "-n", "1", sha)
    parts = line.split()
    require(parts and parts[0] == sha, "commit identity drift")
    return parts[1:]


def changed_statuses(repo: Path, base: str, head: str) -> dict[str, str]:
    output = git(repo, "diff", "--name-status", "-M", base, head, "--")
    if not output:
        return {}
    statuses: dict[str, str] = {}
    for line in output.splitlines():
        parts = line.split("\t")
        status = parts[0] if parts else ""
        if status.startswith(("R", "C")):
            require(len(parts) == 3, f"unexpected rename/copy status shape: {line!r}")
            validate_no_forbidden_paths(parts[1:])
            raise TrustedBoundaryError("renames/copies are not allowed")
        require(len(parts) == 2, f"unexpected diff status shape: {line!r}")
        status, path = parts
        validate_no_forbidden_paths([path])
        if status == "T":
            raise TrustedBoundaryError(f"candidate file mode drift: {path}")
        require(status in {"A", "M", "D"}, f"unexpected diff status: {status!r}")
        require(path not in statuses, f"duplicate diff path: {path}")
        statuses[path] = status
    return statuses


def validate_no_forbidden_paths(paths: list[str] | tuple[str, ...]) -> None:
    for path in paths:
        require(path not in FORBIDDEN_PR_N_PATHS, "trusted validator modification is forbidden")
        require(
            not any(path.startswith(prefix) for prefix in FORBIDDEN_PR_N_PREFIXES),
            "workflow modifications are forbidden for PR N",
        )


def blob_mode(repo: Path, revision: str, path: str) -> str:
    metadata = git(repo, "ls-tree", revision, "--", path).split(None, 3)
    require(len(metadata) == 4 and metadata[1] == "blob" and metadata[3] == path, f"unexpected git object for {path}")
    return metadata[0]


def validate_exact_delta(repo: Path, base: str, head: str, profile: BoundaryProfile) -> None:
    actual = changed_statuses(repo, base, head)
    require(actual == dict(profile.allowed_statuses), "candidate path/status delta drift")
    for path, status in profile.allowed_statuses.items():
        if status == "D":
            continue
        mode = blob_mode(repo, head, path)
        require(mode == profile.allowed_modes[path], f"candidate file mode drift: {path}")


def load_event(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_event_shape(
    event: Mapping[str, Any],
    *,
    event_name: str,
    base_ref: str,
    head_ref: str,
    base_sha: str,
    head_sha: str,
    base_repo: str,
    head_repo: str,
    repository: str,
    check_name: str,
    protected_base_sha: str,
) -> BoundaryProfile:
    require(event_name == "pull_request_target", "trusted boundary must run only on pull_request_target")
    require(check_name not in RETIRED_TRUSTED_CHECK_NAMES, "duplicate trusted boundary check name")
    require(check_name == TRUSTED_CHECK_NAME, "trusted boundary check name drift")
    validate_sha(base_sha, "base")
    validate_sha(head_sha, "head")
    validate_sha(protected_base_sha, "protected base")
    require(base_ref == PROTECTED_BASE_REF, "trusted boundary base ref drift")
    require(base_repo == repository, "trusted boundary base repository drift")
    require(head_repo == repository, "fork or cross-repository candidate rejected")
    require(base_repo == head_repo, "base/head repository mismatch")
    require(base_sha != head_sha, "base and head must differ")
    require(protected_base_sha == base_sha, "stale protected base")

    pull_request = event.get("pull_request")
    require(isinstance(pull_request, Mapping), "missing pull_request event payload")
    action = event.get("action")
    require(action in ALLOWED_ACTIONS, "unexpected pull_request_target action")
    require(pull_request.get("base", {}).get("repo", {}).get("full_name") == repository, "event base repository drift")
    require(pull_request.get("head", {}).get("repo", {}).get("full_name") == repository, "event head repository drift")
    require(pull_request.get("head", {}).get("repo", {}).get("fork") is False, "fork candidate rejected")
    require(pull_request.get("base", {}).get("ref") == base_ref, "event base ref drift")
    require(pull_request.get("head", {}).get("ref") == head_ref, "event head ref drift")
    require(pull_request.get("base", {}).get("sha") == base_sha, "event base sha drift")
    require(pull_request.get("head", {}).get("sha") == head_sha, "event head sha drift")
    validate_sha(str(pull_request.get("base", {}).get("sha", "")), "event base")
    validate_sha(str(pull_request.get("head", {}).get("sha", "")), "event head")

    profile = TRUSTED_PROFILES.get(head_ref)
    require(profile is not None, "unexpected trusted boundary head ref")
    return profile


def validate_trusted_boundary(
    repo: Path,
    event: Mapping[str, Any],
    *,
    event_name: str,
    base_ref: str,
    head_ref: str,
    base_sha: str,
    head_sha: str,
    base_repo: str,
    head_repo: str,
    repository: str,
    check_name: str,
    protected_base_sha: str,
) -> str:
    profile = validate_event_shape(
        event,
        event_name=event_name,
        base_ref=base_ref,
        head_ref=head_ref,
        base_sha=base_sha,
        head_sha=head_sha,
        base_repo=base_repo,
        head_repo=head_repo,
        repository=repository,
        check_name=check_name,
        protected_base_sha=protected_base_sha,
    )
    require(commit_exists(repo, base_sha), "base commit object is unavailable")
    require(commit_exists(repo, head_sha), "candidate commit object is unavailable")
    require(commit_parents(repo, head_sha) == [base_sha], "candidate must be exactly one direct commit")
    subprocess.run(
        ["git", *GIT_CONFIG_ARGS, "-c", f"safe.directory={repo.resolve()}", "merge-base", "--is-ancestor", base_sha, head_sha],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=isolated_git_env(),
    )
    validate_exact_delta(repo, base_sha, head_sha, profile)
    return profile.name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--event-path", type=Path, required=True)
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--base-repo", required=True)
    parser.add_argument("--head-repo", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--check-name", required=True)
    parser.add_argument("--protected-base-sha", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        profile_name = validate_trusted_boundary(
            args.repo,
            load_event(args.event_path),
            event_name=args.event_name,
            base_ref=args.base_ref,
            head_ref=args.head_ref,
            base_sha=args.base_sha,
            head_sha=args.head_sha,
            base_repo=args.base_repo,
            head_repo=args.head_repo,
            repository=args.repository,
            check_name=args.check_name,
            protected_base_sha=args.protected_base_sha,
        )
    except (TrustedBoundaryError, subprocess.CalledProcessError) as exc:
        print(f"trusted boundary failed: {exc}", file=sys.stderr)
        return 1
    print(f"trusted boundary passed: profile={profile_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
