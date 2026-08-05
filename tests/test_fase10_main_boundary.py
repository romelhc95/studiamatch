from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _extract_f10_boundary_script() -> str:
    workflow = source(".github/workflows/security-audit.yml")
    block = workflow.split("# F10_BOUNDARY_OBJECT_GATE_START", 1)[1].split(
        "# F10_BOUNDARY_OBJECT_GATE_END", 1
    )[0]
    lines = []
    for line in block.splitlines():
        if line.startswith("          "):
            lines.append(line[10:])
        else:
            lines.append(line)
    return "\n".join(lines).strip() + "\n"


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if repo != ROOT:
        env.pop("GIT_DIR", None)
        env.pop("GIT_WORK_TREE", None)
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
        check=check,
        capture_output=True,
        text=True,
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _init_repo(repo: Path) -> None:
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "ci@example.invalid")
    _git(repo, "config", "user.name", "CI")
    _git(repo, "config", "core.filemode", "true")


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _mark_certificacion_tip(repo: Path, sha: str) -> None:
    _git(repo, "update-ref", "refs/remotes/origin/certificacion", sha)


def _run_f10_boundary(repo: Path, **env: str) -> subprocess.CompletedProcess:
    run_env = os.environ.copy()
    if repo != ROOT:
        run_env.pop("GIT_DIR", None)
        run_env.pop("GIT_WORK_TREE", None)
    run_env.update(env)
    return subprocess.run(
        [sys.executable, "-c", _extract_f10_boundary_script()],
        cwd=repo,
        env=run_env,
        capture_output=True,
        text=True,
        check=False,
    )


def _extract_allowed_exact_paths() -> set[str]:
    workflow = source(".github/workflows/security-audit.yml")
    block = workflow.split("ALLOWED_EXACT_PATHS = {", 1)[1].split("          }", 1)[0]
    return {
        line.strip().rstrip(",").strip('"')
        for line in block.splitlines()
        if line.strip().startswith('"')
    }


def _parse_name_status(raw: str) -> list[tuple[str, str | None, str]]:
    fields = raw.split("\0")
    index = 0
    rows = []
    while index < len(fields) and fields[index]:
        status = fields[index]
        status_code = status[:1]
        index += 1
        old_path = None
        if status_code in {"R", "C"}:
            old_path = fields[index]
            index += 1
        path = fields[index]
        index += 1
        rows.append((status, old_path, path))
    return rows


def _tree_entry(repo: Path, commit: str, path: str) -> tuple[str, str, str] | None:
    result = _git(repo, "ls-tree", commit, "--", path)
    if not result.stdout:
        return None
    metadata, actual_path = result.stdout.rstrip("\n").split("\t", 1)
    mode, kind, blob = metadata.split(" ")
    assert actual_path == path
    return mode, kind, blob


def _is_ancestor(base: str, head: str) -> bool:
    return (
        _git(ROOT, "merge-base", "--is-ancestor", base, head, check=False).returncode
        == 0
    )


def _commit_parents(commit: str) -> list[str]:
    raw = _git(ROOT, "show", "-s", "--format=%P", commit).stdout.strip()
    return raw.split() if raw else []


def _commit_tree(commit: str) -> str:
    return _git(ROOT, "rev-parse", f"{commit}^{{tree}}").stdout.strip()


def _base_env(
    base: str,
    head: str,
    *,
    base_ref: str = "main",
    head_ref: str = "certificacion",
    repository: str = "studiamatch/studiamatch",
    base_repo: str = "studiamatch/studiamatch",
    head_repo: str = "studiamatch/studiamatch",
) -> dict[str, str]:
    return {
        "F10_EVENT_NAME": "pull_request",
        "F10_REF_NAME": base_ref,
        "F10_BASE_REF": base_ref,
        "F10_HEAD_REF": head_ref,
        "F10_BASE_SHA": base,
        "F10_HEAD_SHA": head,
        "F10_REPOSITORY": repository,
        "F10_BASE_REPO": base_repo,
        "F10_HEAD_REPO": head_repo,
    }


def test_f10_main_boundary_gate_is_present_in_security_audit() -> None:
    workflow = source(".github/workflows/security-audit.yml")

    assert "f10-main-boundary:" in workflow
    assert "F10 Main Boundary And Production Canary" in workflow
    assert "tests/test_fase10_main_boundary.py tests/test_fase10_production_canary.py" in workflow
    assert "needs.f10-main-boundary.result" in workflow
    assert "F10_MAIN: ${{ needs.f10-main-boundary.result }}" in workflow
    assert "F10_BOUNDARY_OBJECT_GATE_START" in workflow
    assert "--name-status" in workflow
    assert "--find-renames" in workflow
    assert "--find-copies" in workflow
    assert "PRs to main must come only from certificacion" in workflow
    assert "PRs to main must originate from certificacion in the same repository" in workflow
    assert "PRs to main must use the protected certificacion branch tip" in workflow
    for path in {
        "requirements-db-migrate.txt",
        "scripts/core/certification_canary_state.py",
        "scripts/shared/roi_engine.py",
        "tests/test_fase09_9_certification_canary.py",
    }:
        assert f'"{path}"' in workflow
    f10_job = workflow.split("  f10-main-boundary:", 1)[1].split("\n  security-audit:", 1)[0]
    assert "fetch-depth: 0" in f10_job
    assert "Resolve object-based F10 main boundary" in f10_job
    assert "f10-main-boundary-object-gate" in f10_job
    assert "tests/test_fase09_10_pre_main_controls.py" in f10_job


def test_f10_main_boundary_accepts_certificacion_to_main_ca1_objects(tmp_path: Path) -> None:
    repo = tmp_path / "f10-pass"
    _init_repo(repo)
    _write(repo / ".github/workflows/security-audit.yml", "base\n")
    base = _commit(repo, "base")
    _write(repo / ".github/workflows/security-audit.yml", "head\n")
    _write(repo / "scripts/core/production_canary_manifest.py", "print('ok')\n")
    head = _commit(repo, "head")
    _mark_certificacion_tip(repo, head)

    result = _run_f10_boundary(repo, **_base_env(base, head))

    assert result.returncode == 0, result.stderr + result.stdout
    assert "F10_MAIN_BOUNDARY_PASS paths=2" in result.stdout


def test_f10_main_boundary_accepts_historical_certification_ca1_objects(tmp_path: Path) -> None:
    repo = tmp_path / "f10-historical-ca1-pass"
    _init_repo(repo)
    _write(repo / ".github/workflows/security-audit.yml", "base\n")
    _write(repo / "scripts/shared/roi_engine.py", "def lookup_market_salary():\n    return None\n")
    base = _commit(repo, "base")
    _write(repo / "requirements-db-migrate.txt", "requests==2.34.2 --hash=sha256:test\n")
    _write(repo / "scripts/core/certification_canary_state.py", "STATE_SCHEMA = 'f9.9'\n")
    _write(
        repo / "scripts/shared/roi_engine.py",
        "def lookup_market_salary_service():\n    return None\n",
    )
    _write(repo / "tests/test_fase09_9_certification_canary.py", "def test_contract():\n    pass\n")
    head = _commit(repo, "head")
    _mark_certificacion_tip(repo, head)

    result = _run_f10_boundary(repo, **_base_env(base, head))

    assert result.returncode == 0, result.stderr + result.stdout
    assert "F10_MAIN_BOUNDARY_PASS paths=4" in result.stdout


def test_f10_main_boundary_accepts_gitattributes_and_preserved_100755_mode(tmp_path: Path) -> None:
    repo = tmp_path / "f10-mode-preserved-pass"
    _init_repo(repo)
    workflow = repo / ".github/workflows/security-audit.yml"
    _write(workflow, "base\n")
    workflow.chmod(0o755)
    _write(repo / ".gitattributes", "base text eol=lf\n")
    base = _commit(repo, "base")
    _write(workflow, "head\n")
    workflow.chmod(0o755)
    _write(repo / ".gitattributes", "base text eol=lf\nnew text eol=lf\n")
    head = _commit(repo, "head")
    _mark_certificacion_tip(repo, head)

    result = _run_f10_boundary(repo, **_base_env(base, head))

    assert result.returncode == 0, result.stderr + result.stdout
    assert "F10_MAIN_BOUNDARY_PASS paths=2" in result.stdout


def test_f10_main_boundary_rejects_main_pr_from_unsupported_source(tmp_path: Path) -> None:
    repo = tmp_path / "f10-source-fail"
    _init_repo(repo)
    _write(repo / ".github/workflows/security-audit.yml", "base\n")
    base = _commit(repo, "base")
    _write(repo / ".github/workflows/security-audit.yml", "head\n")
    head = _commit(repo, "head")

    result = _run_f10_boundary(repo, **_base_env(base, head, head_ref="feat/f10"))

    assert result.returncode != 0
    assert "PRs to main must come only from certificacion" in result.stdout + result.stderr


def test_f10_main_boundary_rejects_main_pr_from_fork_or_other_repo(tmp_path: Path) -> None:
    repo = tmp_path / "f10-repo-fail"
    _init_repo(repo)
    _write(repo / ".github/workflows/security-audit.yml", "base\n")
    base = _commit(repo, "base")
    _write(repo / ".github/workflows/security-audit.yml", "head\n")
    head = _commit(repo, "head")

    result = _run_f10_boundary(repo, **_base_env(base, head, head_repo="attacker/studiamatch"))

    assert result.returncode != 0
    assert "PRs to main must originate from certificacion in the same repository" in result.stdout + result.stderr


def test_f10_main_boundary_rejects_certificacion_name_not_branch_tip(tmp_path: Path) -> None:
    repo = tmp_path / "f10-tip-fail"
    _init_repo(repo)
    _write(repo / ".github/workflows/security-audit.yml", "base\n")
    base = _commit(repo, "base")
    _write(repo / ".github/workflows/security-audit.yml", "head\n")
    head = _commit(repo, "head")
    _mark_certificacion_tip(repo, base)

    result = _run_f10_boundary(repo, **_base_env(base, head))

    assert result.returncode != 0
    assert "PRs to main must use the protected certificacion branch tip" in result.stdout + result.stderr


def test_f10_main_boundary_rejects_zero_or_same_baseline(tmp_path: Path) -> None:
    repo = tmp_path / "f10-baseline-fail"
    _init_repo(repo)
    _write(repo / ".github/workflows/security-audit.yml", "base\n")
    base = _commit(repo, "base")
    _write(repo / ".github/workflows/security-audit.yml", "head\n")
    head = _commit(repo, "head")

    zero_result = _run_f10_boundary(repo, **_base_env("0" * 40, head))
    same_result = _run_f10_boundary(repo, **_base_env(base, base))

    assert zero_result.returncode != 0
    assert "F10_BASE_SHA is not a supported commit SHA" in zero_result.stdout + zero_result.stderr
    assert same_result.returncode != 0
    assert "requires distinct base and head" in same_result.stdout + same_result.stderr


def test_f10_main_boundary_rejects_denied_ca2_paths(tmp_path: Path) -> None:
    repo = tmp_path / "f10-path-fail"
    _init_repo(repo)
    _write(repo / ".github/workflows/security-audit.yml", "base\n")
    base = _commit(repo, "base")
    _write(repo / "web/src/app/page.tsx", "export default function Page() { return null }\n")
    head = _commit(repo, "head")
    _mark_certificacion_tip(repo, head)

    result = _run_f10_boundary(repo, **_base_env(base, head))

    assert result.returncode != 0
    assert "denied F10 boundary path: web/src/app/page.tsx" in result.stdout + result.stderr


def test_f10_main_boundary_rejects_mode_drift_on_allowed_paths(tmp_path: Path) -> None:
    repo = tmp_path / "f10-mode-fail"
    _init_repo(repo)
    workflow = repo / ".github/workflows/security-audit.yml"
    _write(workflow, "base\n")
    base = _commit(repo, "base")
    _write(workflow, "head\n")
    workflow.chmod(0o755)
    head = _commit(repo, "head")
    _mark_certificacion_tip(repo, head)

    result = _run_f10_boundary(repo, **_base_env(base, head))

    assert result.returncode != 0
    assert "mode drift is not allowed" in result.stdout + result.stderr


def test_real_main_to_certificacion_manifest_is_within_f10_boundary() -> None:
    allowed_exact = _extract_allowed_exact_paths()
    allowed_prefixes = (".context/", "config/", "tests/e2e/ca1/")
    denied_prefixes = ("db/", "supabase/", "web/", "scripts/maintenance/")
    main = _git(
        ROOT, "rev-parse", "--verify", "refs/remotes/origin/main^{commit}"
    ).stdout.strip()
    certificacion = _git(
        ROOT, "rev-parse", "--verify", "refs/remotes/origin/certificacion^{commit}"
    ).stdout.strip()
    if _is_ancestor(main, certificacion):
        base = main
        head = certificacion
    else:
        assert _is_ancestor(certificacion, main)
        assert _commit_tree(main) == _commit_tree(certificacion)
        parents = _commit_parents(main)
        assert parents, main
        assert certificacion in parents or any(
            _is_ancestor(certificacion, parent) for parent in parents
        )
        base = parents[0]
        head = main
    raw = _git(
        ROOT,
        "diff",
        "--name-status",
        "-z",
        "--find-renames",
        "--find-copies",
        base,
        head,
        "--",
    ).stdout
    manifest = []
    missing = []
    for status, old_path, path in _parse_name_status(raw):
        status_code = status[:1]
        assert status_code in {"A", "M"}, (status, path)
        for item in [item for item in (old_path, path) if item]:
            assert not item.startswith(denied_prefixes), item
            if item not in allowed_exact and not item.startswith(allowed_prefixes):
                missing.append(item)
        head_entry = _tree_entry(ROOT, head, path)
        base_entry = _tree_entry(ROOT, base, path)
        assert head_entry is not None, path
        head_mode, head_kind, head_blob = head_entry
        assert head_kind == "blob", path
        if status_code == "A":
            assert base_entry is None, path
            assert head_mode == "100644", path
        else:
            assert base_entry is not None, path
            base_mode, base_kind, _base_blob = base_entry
            assert base_kind == "blob", path
            assert base_mode == head_mode and head_mode in {"100644", "100755"}, path
        manifest.append({"path": path, "mode": head_mode, "blob": head_blob})
    assert missing == []
    assert len(manifest) == 32
    assert any(item["path"] == "scripts/core/certification_canary_state.py" for item in manifest)


def test_main_promotion_cannot_auto_apply_database_changes() -> None:
    workflow = source(".github/workflows/db-sync-to-pro.yml")

    assert "push:" in workflow
    assert "Report pending migrations dry-run" in workflow
    assert "Confirm report-only mode" in workflow
    assert "operation == 'apply'" in workflow
    assert "backup_pitr_verified" in workflow
    assert "ddl_authorization_id" in workflow

    apply_section = workflow.split("  apply:", 1)[1].split("  verify:", 1)[0]
    assert "github.event_name == 'workflow_dispatch'" in apply_section
    assert "inputs.operation == 'apply'" in apply_section
    assert "inputs.apply_authorized" in apply_section
    assert "inputs.backup_pitr_verified" in apply_section
    assert "inputs.ddl_authorization_id != ''" in apply_section
    assert "fromJSON(needs.report.outputs.pending_count) > 0" in apply_section
    assert ".context/operaciones/ddl_authorizations/${DDL_AUTHORIZATION_ID}.md" in apply_section
    assert "APPROVED_FOR_PRODUCTION_DDL" in apply_section
    assert "Verify production controls before migrations" in apply_section


def test_main_scheduled_writers_start_paused_until_environment_controls_allow_them() -> None:
    workflows = [
        source(".github/workflows/fg1_inventory.yml"),
        source(".github/workflows/production_pipeline.yml"),
        source(".github/workflows/fg3_integrity.yml"),
    ]

    for workflow in workflows:
        assert "Production-Scheduled-" in workflow
        assert "PRODUCTION_WRITERS_PAUSED: ${{ vars.PRODUCTION_WRITERS_PAUSED }}" in workflow
        assert "needs.production_control_preflight.outputs.allow_writer == 'true'" in workflow
        assert "production_control_preflight.sh" in workflow
        assert "github.ref_name == 'main' && vars.AUTOMATION_ENABLED == 'true'" not in workflow


def test_pre_main_controls_do_not_touch_denied_runtime_surfaces() -> None:
    plan = source(".context/operaciones/plan_cierre_hito1_ca1_only.md")

    assert "Allowlist De Controles Pre-Main F9.10" in plan
    assert "`db/**`, `supabase/**`, `web/**`" in plan
    assert "Production o schedules antes de cerrar los controles pre-main" in plan
