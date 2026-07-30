from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
F97_BASELINE_COMMIT = "8ab1cdf9173b8093781e75ba32c2fea9ae931b14"

PROTECTED_PATHS = (
    ".github/workflows/fg1_inventory.yml",
    ".github/workflows/production_pipeline.yml",
    ".github/workflows/fg3_integrity.yml",
    ".github/workflows/db-sync-to-pro.yml",
    "scripts/core",
    "scripts/shared",
    "config",
    "requirements-fg1.txt",
    "requirements-pipeline.txt",
    "requirements-fg3.txt",
    "requirements-db-migrate.txt",
    "db/manifests/fase09_7_free_schema_rls_v3.json",
    "db/migrations/20260724_fase06_g1b_reconciliation.sql",
    "db/migrations/20260724_fase06_hito1_editorial_contract.sql",
    "db/migrations/20260725_fase07_g1b_closure.sql",
    "db/migrations/20260725_fase08_hito1_functional_closure.sql",
    "db/migrations/20260727_fase09_7_public_access_closure.sql",
    "db/migrations/20260728_fase09_7_notify_new_lead_retirement_v3.sql",
    "scripts/maintenance/category_coverage_audit.py",
    "scripts/maintenance/quality_assurance_audit.py",
    "scripts/maintenance/taxonomy_roi_audit.py",
)


def _git(args: list[str], cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _git_bytes(args: list[str], cwd: Path = ROOT) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _object_exists(repo: Path, revision: str) -> bool:
    return (
        subprocess.run(
            ["git", "cat-file", "-e", revision],
            cwd=repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def resolve_candidate_tree(repo: Path = ROOT) -> tuple[str, str]:
    baseline = os.environ.get("F97_BASELINE_COMMIT")
    mode = os.environ.get("F97_CANDIDATE_MODE")
    if not baseline:
        raise AssertionError("F97_BASELINE_COMMIT is required")
    if baseline != F97_BASELINE_COMMIT:
        raise AssertionError("F97_BASELINE_COMMIT does not match F9.7 baseline")
    if not _object_exists(repo, f"{baseline}^{{commit}}"):
        raise AssertionError("F97 baseline commit is missing")

    if mode == "commit":
        candidate = os.environ.get("F97_CANDIDATE_COMMIT")
        if not candidate:
            raise AssertionError("F97_CANDIDATE_COMMIT is required in commit mode")
        if not _object_exists(repo, f"{candidate}^{{commit}}"):
            raise AssertionError("F97 candidate commit is missing")
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", baseline, candidate],
            cwd=repo,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return candidate, _git(["rev-parse", f"{candidate}^{{tree}}"], cwd=repo).strip()

    if mode == "index":
        candidate_tree = os.environ.get("F97_CANDIDATE_TREE")
        if not candidate_tree:
            raise AssertionError("F97_CANDIDATE_TREE is required in index mode")
        actual_tree = _git(["write-tree"], cwd=repo).strip()
        if actual_tree != candidate_tree:
            raise AssertionError("staged index tree changed during F9.7 validation")
        if not _object_exists(repo, f"{candidate_tree}^{{tree}}"):
            raise AssertionError("F97 candidate tree is missing")
        return "index", candidate_tree

    raise AssertionError("F97_CANDIDATE_MODE must be explicit: commit or index")


def ls_tree(repo: Path, treeish: str, pathspecs: tuple[str, ...]) -> dict[str, tuple[str, str, str]]:
    raw = _git_bytes(["ls-tree", "-r", "-z", treeish, "--", *pathspecs], cwd=repo)
    result: dict[str, tuple[str, str, str]] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        mode, kind, oid = meta.decode("ascii").split(" ")
        result[path.decode("utf-8", "surrogateescape")] = (mode, kind, oid)
    return result


def protected_closure_findings(
    repo: Path,
    baseline: str,
    candidate_tree: str,
    pathspecs: tuple[str, ...] = PROTECTED_PATHS,
) -> list[str]:
    if not _object_exists(repo, f"{baseline}^{{commit}}"):
        raise AssertionError("invalid baseline commit")
    if not _object_exists(repo, f"{candidate_tree}^{{tree}}"):
        raise AssertionError("invalid candidate tree")
    baseline_objects = ls_tree(repo, baseline, pathspecs)
    candidate_objects = ls_tree(repo, candidate_tree, pathspecs)
    findings: list[str] = []
    for path in sorted(set(baseline_objects) | set(candidate_objects)):
        before = baseline_objects.get(path)
        after = candidate_objects.get(path)
        if before is None:
            findings.append(f"addition:{path}")
        elif after is None:
            findings.append(f"deletion:{path}")
        elif before != after:
            findings.append(f"drift:{path}")
    return findings


def _init_repo(path: Path) -> None:
    _git(["init", "-q"], cwd=path)
    _git(["config", "user.email", "ci@example.invalid"], cwd=path)
    _git(["config", "user.name", "CI"], cwd=path)


def _commit(path: Path, message: str) -> str:
    _git(["add", "-A"], cwd=path)
    _git(["commit", "-q", "-m", message], cwd=path)
    return _git(["rev-parse", "HEAD"], cwd=path).strip()


def test_protected_path_inventory_is_the_canonical_f9_7_closure_set():
    assert PROTECTED_PATHS == (
        ".github/workflows/fg1_inventory.yml",
        ".github/workflows/production_pipeline.yml",
        ".github/workflows/fg3_integrity.yml",
        ".github/workflows/db-sync-to-pro.yml",
        "scripts/core",
        "scripts/shared",
        "config",
        "requirements-fg1.txt",
        "requirements-pipeline.txt",
        "requirements-fg3.txt",
        "requirements-db-migrate.txt",
        "db/manifests/fase09_7_free_schema_rls_v3.json",
        "db/migrations/20260724_fase06_g1b_reconciliation.sql",
        "db/migrations/20260724_fase06_hito1_editorial_contract.sql",
        "db/migrations/20260725_fase07_g1b_closure.sql",
        "db/migrations/20260725_fase08_hito1_functional_closure.sql",
        "db/migrations/20260727_fase09_7_public_access_closure.sql",
        "db/migrations/20260728_fase09_7_notify_new_lead_retirement_v3.sql",
        "scripts/maintenance/category_coverage_audit.py",
        "scripts/maintenance/quality_assurance_audit.py",
        "scripts/maintenance/taxonomy_roi_audit.py",
    )
    baseline_objects = ls_tree(ROOT, F97_BASELINE_COMMIT, PROTECTED_PATHS)
    assert len(baseline_objects) == 32


def test_protected_paths_match_baseline_for_explicit_candidate():
    _, candidate_tree = resolve_candidate_tree()
    assert protected_closure_findings(ROOT, F97_BASELINE_COMMIT, candidate_tree) == []


@pytest.mark.parametrize(
    "mutation",
    ["addition", "modification", "deletion", "rename", "mode", "directory-addition"],
)
def test_protected_closure_detects_synthetic_git_object_drift(tmp_path: Path, mutation: str):
    repo = tmp_path / mutation
    repo.mkdir()
    _init_repo(repo)
    (repo / "scripts/core").mkdir(parents=True)
    (repo / "scripts/core/worker.py").write_text("print('ok')\n", encoding="utf-8")
    (repo / "config").mkdir()
    (repo / "config/institution_sources.json").write_text("{}\n", encoding="utf-8")
    baseline = _commit(repo, "baseline")

    if mutation == "addition":
        (repo / "requirements-pipeline.txt").write_text("pytest==0\n", encoding="utf-8")
    elif mutation == "modification":
        (repo / "scripts/core/worker.py").write_text("print('changed')\n", encoding="utf-8")
    elif mutation == "deletion":
        (repo / "scripts/core/worker.py").unlink()
    elif mutation == "rename":
        (repo / "scripts/core/renamed.py").write_text(
            (repo / "scripts/core/worker.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (repo / "scripts/core/worker.py").unlink()
    elif mutation == "mode":
        _git(["update-index", "--chmod=+x", "scripts/core/worker.py"], cwd=repo)
        _git(["commit", "-q", "-m", "mode"], cwd=repo)
        candidate_tree = _git(["rev-parse", "HEAD^{tree}"], cwd=repo).strip()
        assert protected_closure_findings(repo, baseline, candidate_tree, ("scripts/core",))
        return
    else:
        (repo / "config/new.json").write_text("{}\n", encoding="utf-8")

    candidate = _commit(repo, mutation)
    candidate_tree = _git(["rev-parse", f"{candidate}^{{tree}}"], cwd=repo).strip()
    assert protected_closure_findings(
        repo,
        baseline,
        candidate_tree,
        ("scripts/core", "config", "requirements-pipeline.txt"),
    )


def test_protected_closure_fails_closed_for_invalid_objects(tmp_path: Path):
    repo = tmp_path / "invalid"
    repo.mkdir()
    _init_repo(repo)
    (repo / "tracked.txt").write_text("ok\n", encoding="utf-8")
    baseline = _commit(repo, "baseline")
    tree = _git(["rev-parse", "HEAD^{tree}"], cwd=repo).strip()

    with pytest.raises(AssertionError, match="invalid baseline"):
        protected_closure_findings(repo, "0" * 40, tree, ("tracked.txt",))
    with pytest.raises(AssertionError, match="invalid candidate"):
        protected_closure_findings(repo, baseline, "0" * 40, ("tracked.txt",))


def test_candidate_resolution_requires_explicit_mode_baseline_and_candidate(monkeypatch):
    for name in ("F97_BASELINE_COMMIT", "F97_CANDIDATE_MODE", "F97_CANDIDATE_TREE", "F97_CANDIDATE_COMMIT"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(AssertionError, match="F97_BASELINE_COMMIT"):
        resolve_candidate_tree()

    monkeypatch.setenv("F97_BASELINE_COMMIT", F97_BASELINE_COMMIT)
    with pytest.raises(AssertionError, match="F97_CANDIDATE_MODE"):
        resolve_candidate_tree()

    monkeypatch.setenv("F97_CANDIDATE_MODE", "index")
    with pytest.raises(AssertionError, match="F97_CANDIDATE_TREE"):
        resolve_candidate_tree()
