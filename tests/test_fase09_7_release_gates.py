from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

import tests.test_fase09_7_pipeline_no_regression as pipeline_contract
from tests.test_fase09_7_pipeline_no_regression import (
    F97_BASELINE_COMMIT,
    PROTECTED_PATHS,
    protected_closure_findings,
    resolve_candidate_tree,
)


ROOT = Path(__file__).resolve().parents[1]
ACTIONLINT_VERSION = "1.7.7"
SHELLCHECK_VERSION = "0.9.0"
SHELLCHECK_SHA256 = "700324c6dd0ebea0117591c6cc9d7350d9c7c5c287acbad7630fa17b1d4d9e2f"
ACTIONLINT_ASSET = f"actionlint_{ACTIONLINT_VERSION}_linux_amd64.tar.gz"
ACTIONLINT_SHA256 = "023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757"
ACTIONLINT_CONFIG = """paths:
  .github/workflows/db-sync-to-pro.yml:
    ignore:
      - '^shellcheck reported issue in this script: SC2086:info:3:24: Double quote to prevent globbing and word splitting$'
  .github/workflows/production_pipeline.yml:
    ignore:
      - '^shellcheck reported issue in this script: SC2086:info:1:38: Double quote to prevent globbing and word splitting$'
"""
WORKFLOW_PATHS = (
    ".github/workflows/db-sync-to-pro.yml",
    ".github/workflows/f9-7-contract.yml",
    ".github/workflows/fg1_inventory.yml",
    ".github/workflows/fg3_integrity.yml",
    ".github/workflows/opencode.yml",
    ".github/workflows/production_pipeline.yml",
    ".github/workflows/security-audit.yml",
)
LEGACY_ACTIONLINT_IGNORES = (
    (
        ".github/workflows/db-sync-to-pro.yml",
        "^shellcheck reported issue in this script: SC2086:info:3:24: Double quote to prevent globbing and word splitting$",
    ),
    (
        ".github/workflows/production_pipeline.yml",
        "^shellcheck reported issue in this script: SC2086:info:1:38: Double quote to prevent globbing and word splitting$",
    ),
)
ALLOWED_FIREWALL_CHAINS = (
    "F97_FRONTEND_EGRESS",
    "FASE097_EGRESS",
    "FASE097_AUDIT_EGRESS",
)
ZERO_SHA = "0" * 40


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _git(args: list[str], cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


def _git_bytes(args: list[str], cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True)


def _init_repo(path: Path) -> None:
    _git(["init", "-q"], cwd=path)
    _git(["config", "user.email", "ci@example.invalid"], cwd=path)
    _git(["config", "user.name", "CI"], cwd=path)


def _commit(path: Path, message: str) -> str:
    _git(["add", "-A"], cwd=path)
    _git(["commit", "-q", "-m", message], cwd=path)
    return _git(["rev-parse", "HEAD"], cwd=path).stdout.strip()


def _write(path: Path, data: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")


def _synthetic_token() -> str:
    return "sb_" + "publishable_" + ("x" * 20)


def _extract_hook_pattern(relative: str) -> str:
    prefix = 'F97_CREDENTIAL_PATTERN="'
    line = next(item for item in _source(relative).splitlines() if item.startswith(prefix))
    value = []
    escaped = False
    for char in line[len(prefix):]:
        if escaped:
            value.append("\\" + char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            break
        value.append(char)
    return "".join(value).replace('\\"', '"')


def _extract_workflow_pattern() -> str:
    workflow = _source(".github/workflows/security-audit.yml")
    match = re.search(r"F97_CREDENTIAL_PATTERN:\s*>-\n\s+(.+)", workflow)
    assert match
    return match.group(1).strip().replace('\\"', '"')


def _credential_scan_tree(repo: Path, treeish: str, pattern: str | None = None) -> int:
    pattern = pattern or _extract_hook_pattern(".githooks/pre-commit")
    completed = subprocess.run(
        ["git", "grep", "-a", "-q", "-E", pattern, treeish, "--", "."],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return completed.returncode


def _first_actionlint_version_line(output: str) -> str:
    return output.split("\n", 1)[0]


def _changed_eol_findings(repo: Path, baseline: str, candidate: str) -> list[str]:
    raw = _git_bytes(
        [
            "diff",
            "--name-status",
            "-z",
            "--find-renames",
            "--find-copies",
            "--diff-filter=ACMR",
            baseline,
            candidate,
            "--",
        ],
        cwd=repo,
    ).stdout
    fields = raw.split(b"\0")
    findings: list[str] = []
    index = 0
    while index < len(fields) and fields[index]:
        status = fields[index].decode("ascii")
        index += 1
        if status.startswith(("R", "C")):
            index += 1
        path = fields[index].decode("utf-8", "surrogateescape")
        index += 1
        blob = _git_bytes(["cat-file", "blob", f"{candidate}:{path}"], cwd=repo).stdout
        if b"\0" in blob:
            continue
        if b"\r\n" in blob:
            findings.append(path.encode("unicode_escape").decode("ascii"))
    return findings


def _index_lf_attribute_findings(repo: Path) -> list[str]:
    raw_index = _git_bytes(["ls-files", "-s", "-z"], cwd=repo).stdout
    paths: list[bytes] = []
    oid_by_path: dict[bytes, str] = {}
    for record in raw_index.split(b"\0"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        _mode, oid, stage = meta.decode("ascii").split(" ")
        if stage != "0":
            raise AssertionError("unmerged index entries are not valid for F9.7 release gates")
        paths.append(path)
        oid_by_path[path] = oid

    if not paths:
        return []

    attrs = subprocess.run(
        ["git", "check-attr", "-z", "--stdin", "eol"],
        cwd=repo,
        input=b"\0".join(paths) + b"\0",
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")

    findings: list[str] = []
    for index in range(0, len(attrs) - 1, 3):
        path, _attribute, value = attrs[index : index + 3]
        if value != b"lf":
            continue
        blob = _git_bytes(["cat-file", "blob", oid_by_path[path]], cwd=repo).stdout
        if b"\r" in blob:
            findings.append(path.decode("utf-8", "surrogateescape"))
    return findings


def _resolve_candidate_tree_branches() -> tuple[str, str]:
    source = _source("tests/test_fase09_7_pipeline_no_regression.py")
    commit_branch = source.split('if mode == "commit":', 1)[1].split(
        'if mode == "index":', 1
    )[0]
    index_branch = source.split('if mode == "index":', 1)[1].split(
        'raise AssertionError("F97_CANDIDATE_MODE', 1
    )[0]
    return commit_branch, index_branch


def _validate_resolve_candidate_tree_source(source: str) -> None:
    commit_branch = source.split('if mode == "commit":', 1)[1].split('if mode == "index":', 1)[0]
    index_branch = source.split('if mode == "index":', 1)[1].split(
        'raise AssertionError("F97_CANDIDATE_MODE', 1
    )[0]
    assert "write-tree" not in commit_branch
    assert '["rev-parse", f"{candidate}^{{tree}}"]' in commit_branch
    assert "write-tree" in index_branch


def _prepare_candidate_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    repo = tmp_path / "candidate-repo"
    repo.mkdir()
    _init_repo(repo)
    _write(repo / "tracked.txt", "baseline\n")
    baseline = _commit(repo, "baseline")
    monkeypatch.setattr(pipeline_contract, "F97_BASELINE_COMMIT", baseline)
    monkeypatch.setenv("F97_BASELINE_COMMIT", baseline)
    return repo, baseline


def test_candidate_identity_uses_mode_aware_tree_resolution_and_preserves_index():
    before = _git_bytes(["ls-files", "--stage", "-z"]).stdout
    assert not (ROOT / ".git" / "index.lock").exists()
    candidate, candidate_tree = resolve_candidate_tree()
    if os.environ["F97_CANDIDATE_MODE"] == "commit":
        assert candidate == os.environ["F97_CANDIDATE_COMMIT"]
        assert _git(["rev-parse", f"{candidate}^{{tree}}"]).stdout.strip() == candidate_tree
    else:
        assert candidate == "index"
        assert candidate_tree == os.environ["F97_CANDIDATE_TREE"]
        assert _git(["write-tree"]).stdout.strip() == candidate_tree
    after = _git_bytes(["ls-files", "--stage", "-z"]).stdout
    assert after == before
    assert not (ROOT / ".git" / "index.lock").exists()


def test_resolve_candidate_tree_commit_mode_does_not_call_write_tree(tmp_path: Path, monkeypatch):
    repo, _baseline = _prepare_candidate_repo(tmp_path, monkeypatch)
    _write(repo / "tracked.txt", "candidate\n")
    candidate_commit = _commit(repo, "candidate")
    candidate_tree = _git(["rev-parse", f"{candidate_commit}^{{tree}}"], cwd=repo).stdout.strip()
    real_git = shutil.which("git")
    assert real_git
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_path = tmp_path / "git-write-tree.log"
    fake_git = bin_dir / "git"
    fake_git.write_text(
        f'''#!/bin/sh
if [ "$1" = "write-tree" ]; then
  printf '%s\n' "$1" >> "{log_path}"
  exit 97
fi
exec "{real_git}" "$@"
''',
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.setenv("F97_CANDIDATE_MODE", "commit")
    monkeypatch.setenv("F97_CANDIDATE_COMMIT", candidate_commit)
    monkeypatch.setenv("F97_CANDIDATE_TREE", candidate_tree)
    before = _git_bytes(["ls-files", "--stage", "-z"], cwd=repo).stdout

    resolved_candidate, resolved_tree = pipeline_contract.resolve_candidate_tree(repo)

    assert resolved_candidate == candidate_commit
    assert resolved_tree == candidate_tree
    assert _git_bytes(["ls-files", "--stage", "-z"], cwd=repo).stdout == before
    assert not log_path.exists()
    assert not (repo / ".git" / "index.lock").exists()


def test_resolve_candidate_tree_index_mode_uses_write_tree_for_valid_and_modified_stage(
    tmp_path: Path, monkeypatch
):
    repo, _baseline = _prepare_candidate_repo(tmp_path, monkeypatch)
    monkeypatch.setenv("F97_CANDIDATE_MODE", "index")
    candidate_tree = _git(["write-tree"], cwd=repo).stdout.strip()
    monkeypatch.setenv("F97_CANDIDATE_TREE", candidate_tree)
    assert pipeline_contract.resolve_candidate_tree(repo) == ("index", candidate_tree)

    _write(repo / "staged.txt", "staged\n")
    _git(["add", "staged.txt"], cwd=repo)
    modified_tree = _git(["write-tree"], cwd=repo).stdout.strip()
    monkeypatch.setenv("F97_CANDIDATE_TREE", modified_tree)
    assert pipeline_contract.resolve_candidate_tree(repo) == ("index", modified_tree)

    monkeypatch.setenv("F97_CANDIDATE_TREE", candidate_tree)
    with pytest.raises(AssertionError, match="staged index tree changed"):
        pipeline_contract.resolve_candidate_tree(repo)
    assert not (repo / ".git" / "index.lock").exists()


def test_resolve_candidate_tree_index_mode_fails_for_unmerged_index(tmp_path: Path, monkeypatch):
    repo, _baseline = _prepare_candidate_repo(tmp_path, monkeypatch)
    branch = _git(["branch", "--show-current"], cwd=repo).stdout.strip()
    _git(["checkout", "-q", "-b", "other"], cwd=repo)
    _write(repo / "tracked.txt", "other\n")
    _commit(repo, "other")
    _git(["checkout", "-q", branch], cwd=repo)
    _write(repo / "tracked.txt", "main\n")
    _commit(repo, "main")
    assert _git(["merge", "other"], cwd=repo, check=False).returncode != 0
    assert _git(["ls-files", "-u"], cwd=repo).stdout.strip()
    monkeypatch.setenv("F97_CANDIDATE_MODE", "index")
    monkeypatch.setenv("F97_CANDIDATE_TREE", _git(["rev-parse", "HEAD^{tree}"], cwd=repo).stdout.strip())
    with pytest.raises(subprocess.CalledProcessError):
        pipeline_contract.resolve_candidate_tree(repo)


def test_resolve_candidate_tree_source_keeps_commit_read_only_and_index_write_tree():
    _validate_resolve_candidate_tree_source(_source("tests/test_fase09_7_pipeline_no_regression.py"))


def test_resolve_candidate_tree_source_rejects_write_tree_reintroduced_in_commit_mode():
    source = _source("tests/test_fase09_7_pipeline_no_regression.py")
    mutated = source.replace(
        'return candidate, _git(["rev-parse", f"{candidate}^{{tree}}"], cwd=repo).strip()',
        'return candidate, _git(["write-tree"], cwd=repo).strip()',
    )
    with pytest.raises(AssertionError):
        _validate_resolve_candidate_tree_source(mutated)


def test_ci_boundary_pytest_runs_as_nobody_with_limited_safe_directory():
    required = {
        "F97_BASELINE_COMMIT",
        "F97_CANDIDATE_MODE",
        "F97_CANDIDATE_COMMIT",
        "F97_CANDIDATE_TREE",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_KEY_0",
        "GIT_CONFIG_VALUE_0",
    }
    if os.environ.get("CI") != "true" or not required <= set(os.environ):
        pytest.skip("requires the F9.7 setpriv/env-i CI boundary")
    assert os.geteuid() == 65534
    assert os.getegid() == 65534
    assert ROOT.stat().st_uid != os.geteuid()
    assert os.environ["GIT_CONFIG_COUNT"] == "1"
    assert os.environ["GIT_CONFIG_KEY_0"] == "safe.directory"
    assert os.environ["GIT_CONFIG_VALUE_0"] == str(ROOT)
    assert os.environ["GIT_CONFIG_VALUE_0"] != "*"
    assert not os.access(ROOT, os.W_OK)
    assert not os.access(ROOT / ".git", os.W_OK)
    before = _git_bytes(["ls-files", "--stage", "-z"]).stdout
    probe = ROOT / ".f97-read-only-probe"
    with pytest.raises(OSError):
        probe.write_text("blocked\n", encoding="utf-8")
    assert not probe.exists()
    assert _git_bytes(["ls-files", "--stage", "-z"]).stdout == before
    assert not (ROOT / ".git" / "index.lock").exists()


def _validate_actionlint_contract(source: str) -> None:
    assert f"ACTIONLINT_VERSION: '{ACTIONLINT_VERSION}'" in source
    assert f"SHELLCHECK_VERSION: '{SHELLCHECK_VERSION}'" in source
    assert f"SHELLCHECK_SHA256: {SHELLCHECK_SHA256}" in source
    assert f"ACTIONLINT_ASSET: {ACTIONLINT_ASSET}" in source
    assert "linux_x86_64" not in source
    assert "linux_386" not in source
    assert "linux_arm64" not in source
    assert ACTIONLINT_SHA256 in source
    assert "sha256sum -c -" in source
    assert "koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}" in source
    assert "shellcheck-v${SHELLCHECK_VERSION}.linux.x86_64.tar.xz" in source
    assert 'printf \'%s  %s\\n\' "$SHELLCHECK_SHA256" "$shellcheck_archive" | sha256sum -c -' in source
    assert "command -v shellcheck" in source
    assert "reported_shellcheck_version=\"$(shellcheck --version | awk -F': ' '$1 == \"version\" { print $2 }')\"" in source
    assert "test \"$reported_shellcheck_version\" = \"$SHELLCHECK_VERSION\"" in source
    assert 'reported_actionlint_output="$("$actionlint_dir/actionlint" -version)"' in source
    assert "reported_actionlint_release=\"${reported_actionlint_output%%$'\\n'*}\"" in source
    assert "test \"$reported_actionlint_release\" = \"$ACTIONLINT_VERSION\"" in source
    assert 'actionlint_version="$($actionlint_dir/actionlint -version)"' not in source
    assert 'actionlint_version_output="$($actionlint_dir/actionlint -version)"' not in source
    assert "test \"$actionlint_version_output\" = \"$ACTIONLINT_VERSION\"" not in source
    assert "actionlint_version_output" not in source
    assert "actionlint_version=\"" not in source
    assert "test \"$actionlint_version\"" not in source
    assert "find .github/workflows" in source
    assert "-name '*.yml'" in source
    assert "-name '*.yaml'" in source
    assert "-print0" in source
    assert "xargs -0" in source
    assert "-config-file .github/actionlint.yaml" in source
    assert "test -s \"$workflow_list\"" in source
    assert "RUNNER_TEMP" in source
    assert "$GITHUB_WORKSPACE/actionlint" not in source
    assert "curl -fsSLo actionlint.tar.gz" not in source
    assert "# shellcheck disable" not in source
    assert "-shellcheck=" not in source
    assert "SHELLCHECK_OPTS" not in source
    assert " -ignore " not in source
    assert "continue-on-error" not in source
    assert "! -path" not in source
    assert "git diff --name-only" not in source


@pytest.mark.parametrize(
    "relative",
    [".github/workflows/security-audit.yml", ".github/workflows/f9-7-contract.yml"],
)
def test_actionlint_tuple_is_immutable_and_nul_safe(relative: str):
    _validate_actionlint_contract(_source(relative))


def test_actionlint_version_parser_accepts_official_multiline_output():
    official_like = f"{ACTIONLINT_VERSION}\nbuilt with go1.24.0 for linux/amd64"
    assert _first_actionlint_version_line(official_like) == ACTIONLINT_VERSION
    assert _first_actionlint_version_line(f"{ACTIONLINT_VERSION}.1\nextra") != ACTIONLINT_VERSION


def _validate_actionlint_config(source: str) -> None:
    assert source == ACTIONLINT_CONFIG
    assert source.count("SC2086") == 2
    assert source.count("SC2153") == 0
    assert "\nignore:" not in source
    assert ".*" not in source
    assert ".+" not in source
    assert "|" not in source
    assert "SC2086$" not in source
    for path, finding in LEGACY_ACTIONLINT_IGNORES:
        assert f"  {path}:" in source
        assert f"      - '{finding}'" in source


def test_actionlint_config_is_byte_exact_and_limited_to_two_legacy_sc2086_findings():
    assert (ROOT / ".github/actionlint.yaml").read_bytes() == ACTIONLINT_CONFIG.encode("utf-8")
    _validate_actionlint_config(_source(".github/actionlint.yaml"))


@pytest.mark.parametrize(
    "mutator",
    [
        lambda s: s + "ignore:\n  - '.*'\n",
        lambda s: s.replace("db-sync-to-pro.yml", "fg1_inventory.yml"),
        lambda s: s.replace("SC2086:info:3:24", "SC2086:info:3:25"),
        lambda s: s.replace("SC2086:info:3:24", "SC2153:info:3:24"),
        lambda s: s.replace("^shellcheck", "shellcheck"),
        lambda s: s.replace("word splitting$", "word splitting"),
        lambda s: s.replace("word splitting$'", "word splitting.*'"),
        lambda s: s.replace("production_pipeline.yml", "*.yml"),
        lambda s: s.replace("SC2086:info:1:38", "SC2086"),
        lambda s: s + "  .github/workflows/opencode.yml:\n    ignore:\n      - '^x$'\n",
    ],
)
def test_actionlint_config_mutations_are_rejected(mutator):
    with pytest.raises(AssertionError):
        _validate_actionlint_config(mutator(ACTIONLINT_CONFIG))


def test_actionlint_workflow_inventory_is_exactly_seven_tracked_files():
    observed = tuple(
        sorted(
            subprocess.check_output(
                ["git", "ls-files", ".github/workflows/*.yml", ".github/workflows/*.yaml"],
                cwd=ROOT,
                text=True,
            ).splitlines()
        )
    )
    assert observed == WORKFLOW_PATHS


def test_actionlint_legacy_sc2086_workflow_blobs_remain_at_baseline():
    for path, _finding in LEGACY_ACTIONLINT_IGNORES:
        baseline_blob = _git_bytes(["cat-file", "blob", f"{F97_BASELINE_COMMIT}:{path}"]).stdout
        candidate_blob = _git_bytes(["cat-file", "blob", f"HEAD:{path}"]).stdout
        assert candidate_blob == baseline_blob


@pytest.mark.parametrize(
    "mutator",
    [
        lambda s: s.replace("linux_amd64", "linux_x86_64"),
        lambda s: s.replace("linux_amd64", "linux_386"),
        lambda s: s.replace("linux_amd64", "linux_arm64"),
        lambda s: s.replace("linux_amd64", "linux_ppc64le"),
        lambda s: s.replace(ACTIONLINT_SHA256, "0" * 64),
        lambda s: s.replace(SHELLCHECK_SHA256, "0" * 64),
        lambda s: s.replace(ACTIONLINT_VERSION, "1.7.8", 1),
        lambda s: s.replace(SHELLCHECK_VERSION, "0.10.0", 1),
        lambda s: s.replace("command -v shellcheck\n", ""),
        lambda s: s.replace('reported_actionlint_release="${reported_actionlint_output%%$\'\\n\'*}"', 'actionlint_version="${actionlint_version_output%%$\'\\n\'*}"'),
        lambda s: s.replace('test "$reported_actionlint_release" = "$ACTIONLINT_VERSION"', 'test "$reported_actionlint_output" = "$ACTIONLINT_VERSION"'),
        lambda s: s.replace('test "$reported_actionlint_release" = "$ACTIONLINT_VERSION"', "true"),
        lambda s: s.replace('test "$reported_shellcheck_version" = "$SHELLCHECK_VERSION"', "true"),
        lambda s: s.replace("-name '*.yaml'", "-name '*.yml'"),
        lambda s: s.replace("$RUNNER_TEMP/actionlint", "$GITHUB_WORKSPACE/actionlint"),
        lambda s: s.replace("-config-file .github/actionlint.yaml", ""),
    ],
)
def test_actionlint_contract_mutations_are_rejected(mutator):
    with pytest.raises(AssertionError):
        _validate_actionlint_contract(mutator(_source(".github/workflows/security-audit.yml")))


def test_changed_only_eol_accepts_lf_special_paths_rename_deletes_and_binary(tmp_path: Path):
    repo = tmp_path / "eol-pass"
    repo.mkdir()
    _init_repo(repo)
    _write(repo / "legacy.txt", b"legacy\r\n")
    _write(repo / "deleted.txt", b"delete\r\n")
    _write(repo / "rename-old.txt", "old\n")
    baseline = _commit(repo, "baseline")

    (repo / "deleted.txt").unlink()
    _write(repo / "changed_lf.txt", "ok\n")
    _write(repo / "binary.bin", b"not text\0with\r\n")
    _write(repo / "path with space.txt", "ok\n")
    _write(repo / "path\nwith-newline.txt", "ok\n")
    _write(repo / ".gitattributes", "*.txt text eol=lf\n")
    _write(repo / ".githooks/pre-commit", "#!/bin/sh\nexit 0\n")
    _git(["mv", "rename-old.txt", "rename-new.txt"], cwd=repo)
    candidate = _commit(repo, "candidate")

    assert _changed_eol_findings(repo, baseline, candidate) == []


def test_changed_only_eol_blocks_only_changed_crlf_and_sanitizes_paths(tmp_path: Path):
    repo = tmp_path / "eol-fail"
    repo.mkdir()
    _init_repo(repo)
    _write(repo / "legacy.txt", b"legacy\r\n")
    baseline = _commit(repo, "baseline")
    _write(repo / "bad\npath.txt", b"bad\r\n")
    candidate = _commit(repo, "candidate")

    assert _changed_eol_findings(repo, baseline, candidate) == ["bad\\npath.txt"]


def test_gitattributes_lf_scope_is_explicit_and_index_blobs_are_lf():
    source = _source(".gitattributes")
    required = {
        ".gitattributes text eol=lf",
        ".env.example text eol=lf",
        "AGENTS.md text eol=lf",
        ".githooks/* text eol=lf",
        "*.sh text eol=lf",
        ".github/workflows/security-audit.yml text eol=lf",
        ".github/workflows/f9-7-contract.yml text eol=lf",
        ".github/actionlint.yaml text eol=lf",
        "db/migrations/20260727_fase09_7_*.sql text eol=lf",
        "db/migrations/20260728_fase09_7_*.sql text eol=lf",
        "db/migrations/20260729_fase09_7_*.sql text eol=lf",
        "tests/sql/fase09_7_*.sql text eol=lf",
        "tests/test_fase09_7_*.py text eol=lf",
        "web/src/app/compare/CompareContent.tsx text eol=lf",
    }
    lines = set(source.splitlines())
    assert required <= lines
    for forbidden in (
        "*.css text eol=lf",
        "*.html text eol=lf",
        "*.js text eol=lf",
        "*.json text eol=lf",
        "*.md text eol=lf",
        "*.mjs text eol=lf",
        "*.py text eol=lf",
        "*.sql text eol=lf",
        "*.ts text eol=lf",
        "*.tsx text eol=lf",
        "*.txt text eol=lf",
        "*.yaml text eol=lf",
        "*.yml text eol=lf",
    ):
        assert forbidden not in lines
    assert _index_lf_attribute_findings(ROOT) == []


def test_changed_only_eol_fails_for_invalid_git_objects(tmp_path: Path):
    repo = tmp_path / "eol-invalid"
    repo.mkdir()
    _init_repo(repo)
    _write(repo / "tracked.txt", "ok\n")
    baseline = _commit(repo, "baseline")

    with pytest.raises(subprocess.CalledProcessError):
        _changed_eol_findings(repo, baseline, ZERO_SHA)


def test_explicit_candidate_changed_blobs_are_lf_only():
    _, candidate_tree = resolve_candidate_tree()
    assert _changed_eol_findings(ROOT, F97_BASELINE_COMMIT, candidate_tree) == []


def test_ranged_whitespace_check_catches_clean_worktree_regression(tmp_path: Path):
    repo = tmp_path / "whitespace"
    repo.mkdir()
    _init_repo(repo)
    _write(repo / "file.txt", "clean\n")
    baseline = _commit(repo, "baseline")
    _write(repo / "file.txt", "bad trailing \n")
    candidate = _commit(repo, "candidate")
    _git(["checkout", "-q", candidate], cwd=repo)

    bare = _git(["diff", "--check"], cwd=repo, check=False)
    ranged = _git(["diff", "--check", baseline, candidate], cwd=repo, check=False)

    assert bare.returncode == 0
    assert ranged.returncode != 0


def test_protected_closure_gate_uses_same_explicit_candidate_tree():
    _, candidate_tree = resolve_candidate_tree()
    assert protected_closure_findings(ROOT, F97_BASELINE_COMMIT, candidate_tree) == []


def _run_hook(repo: Path, relative: str, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        ["sh", str(ROOT / relative)],
        cwd=repo,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def test_pre_commit_scans_index_not_worktree_and_handles_paths_and_nul(tmp_path: Path):
    token = _synthetic_token()

    empty = tmp_path / "empty"
    empty.mkdir()
    _init_repo(empty)
    assert _run_hook(empty, ".githooks/pre-commit").returncode == 0

    clean = tmp_path / "clean"
    clean.mkdir()
    _init_repo(clean)
    _write(clean / "space name.txt", "clean\n")
    _write(clean / "line\nname.txt", "clean\n")
    _git(["add", "-A"], cwd=clean)
    assert _run_hook(clean, ".githooks/pre-commit").returncode == 0
    _git(["commit", "-q", "-m", "base"], cwd=clean)
    _write(clean / "line\nname.txt", "clean modification\n")
    _git(["add", "line\nname.txt"], cwd=clean)
    _git(["mv", "space name.txt", "renamed space.txt"], cwd=clean)
    assert _run_hook(clean, ".githooks/pre-commit").returncode == 0

    index_secret = tmp_path / "index-secret"
    index_secret.mkdir()
    _init_repo(index_secret)
    _write(index_secret / "secret.bin", (token + "\0").encode())
    _git(["add", "secret.bin"], cwd=index_secret)
    _write(index_secret / "secret.bin", "clean worktree\n")
    blocked = _run_hook(index_secret, ".githooks/pre-commit")
    assert blocked.returncode != 0
    assert token not in blocked.stdout + blocked.stderr

    worktree_secret = tmp_path / "worktree-secret"
    worktree_secret.mkdir()
    _init_repo(worktree_secret)
    _write(worktree_secret / "file.txt", "clean\n")
    _git(["add", "file.txt"], cwd=worktree_secret)
    _write(worktree_secret / "file.txt", token + "\n")
    assert _run_hook(worktree_secret, ".githooks/pre-commit").returncode == 0

    not_repo = tmp_path / "not-repo"
    not_repo.mkdir()
    assert _run_hook(not_repo, ".githooks/pre-commit").returncode != 0


def test_pre_push_scans_every_outgoing_commit_tree(tmp_path: Path):
    token = _synthetic_token()
    hook = ".githooks/pre-push"

    repo = tmp_path / "pre-push"
    repo.mkdir()
    _init_repo(repo)
    _write(repo / "file.txt", "base\n")
    base = _commit(repo, "base")
    _git(["update-ref", "refs/remotes/origin/main", base], cwd=repo)

    _write(repo / "file.txt", "clean\n")
    clean = _commit(repo, "clean")
    line = f"refs/heads/main {clean} refs/heads/main {base}\n"
    assert _run_hook(repo, hook, line).returncode == 0

    _write(repo / "secret.txt", token + "\n")
    dirty = _commit(repo, "dirty")
    (repo / "secret.txt").unlink()
    removed = _commit(repo, "removed")
    line = f"refs/heads/main {removed} refs/heads/main {clean}\n"
    blocked = _run_hook(repo, hook, line)
    assert blocked.returncode != 0
    assert token not in blocked.stdout + blocked.stderr
    assert dirty

    _git(["checkout", "-q", "-b", "topic", base], cwd=repo)
    _write(repo / "topic.txt", token + "\n")
    _commit(repo, "topic dirty")
    (repo / "topic.txt").unlink()
    topic_clean = _commit(repo, "topic clean")
    line = f"refs/heads/topic {topic_clean} refs/heads/topic {ZERO_SHA}\n"
    assert _run_hook(repo, hook, line).returncode != 0

    deletion = f"refs/heads/topic {ZERO_SHA} refs/heads/topic {topic_clean}\n"
    assert _run_hook(repo, hook, deletion).returncode == 0

    invalid = f"refs/heads/main {ZERO_SHA[:-1]}1 refs/heads/main {base}\n"
    assert _run_hook(repo, hook, invalid).returncode != 0


def test_pre_push_handles_multiple_refs_force_push_and_old_remote_history(tmp_path: Path):
    token = _synthetic_token()
    hook = ".githooks/pre-push"
    repo = tmp_path / "pre-push-refs"
    repo.mkdir()
    _init_repo(repo)
    _write(repo / "file.txt", "base\n")
    base = _commit(repo, "base")
    _git(["update-ref", "refs/remotes/origin/main", base], cwd=repo)

    _write(repo / "old.txt", token + "\n")
    old_remote = _commit(repo, "old remote dirty")
    (repo / "old.txt").unlink()
    local_clean = _commit(repo, "old remote clean child")
    clean_line = f"refs/heads/main {local_clean} refs/heads/main {old_remote}\n"
    assert _run_hook(repo, hook, clean_line).returncode == 0

    _git(["checkout", "-q", "-B", "force", base], cwd=repo)
    _write(repo / "force.txt", token + "\n")
    force_dirty = _commit(repo, "force dirty")
    _git(["checkout", "-q", "-B", "other", base], cwd=repo)
    _write(repo / "other.txt", "clean\n")
    other_clean = _commit(repo, "other clean")
    stdin = (
        f"refs/heads/other {other_clean} refs/heads/other {base}\n"
        f"refs/heads/force {force_dirty} refs/heads/force {local_clean}\n"
    )
    assert _run_hook(repo, hook, stdin).returncode != 0


def test_candidate_credential_scan_is_tree_based_binary_safe_and_redacted(tmp_path: Path):
    token = _synthetic_token()
    repo = tmp_path / "credential-tree"
    repo.mkdir()
    _init_repo(repo)
    _write(repo / f"filename-{token}.txt", "clean\n")
    clean = _commit(repo, "clean")
    assert _credential_scan_tree(repo, f"{clean}^{{tree}}") == 1

    _write(repo / "space name.bin", ("prefix\0" + token).encode())
    dirty = _commit(repo, "dirty")
    assert _credential_scan_tree(repo, f"{dirty}^{{tree}}") == 0
    assert _credential_scan_tree(repo, ZERO_SHA) > 1


def test_credential_patterns_are_identical_across_ci_and_hooks():
    assert _extract_hook_pattern(".githooks/pre-commit") == _extract_hook_pattern(
        ".githooks/pre-push"
    )
    assert _extract_hook_pattern(".githooks/pre-commit") == _extract_workflow_pattern()


def _write_fake_firewall(directory: Path) -> None:
    fake = directory / "fake_firewall.py"
    fake.write_text(
        r'''#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

state_path = Path(os.environ["FAKE_FIREWALL_STATE"])
family = sys.argv[1]
args = sys.argv[2:]
state = json.loads(state_path.read_text() if state_path.exists() else "{}")
state.setdefault("ops", []).append(f"{family} {' '.join(args)}")
family_state = state.setdefault(family, {"chains": {}, "jumps": {}})
for name, rules in list(family_state["chains"].items()):
    if rules is True:
        family_state["chains"][name] = []
fail = {item for item in os.environ.get("FAKE_FIREWALL_FAIL", "").split(",") if item}

def save_exit(code):
    state_path.write_text(json.dumps(state, sort_keys=True))
    raise SystemExit(code)

def fails(op):
    return bool(fail & {f"{family}:{op}", f"all:{op}"})

def rule_key(rule):
    return "\0".join(rule)

def jump_target(rule):
    return rule[rule.index("-j") + 1] if "-j" in rule else ""

def append_op(rule):
    if rule == ["-o", "lo", "-j", "RETURN"]:
        return "append-loopback"
    if rule == ["-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "RETURN"]:
        return "append-conntrack"
    if rule == ["-j", "REJECT"]:
        return "append-reject"
    return "append"

if args[:3] == ["-w", "10", "-L"] and args[3] == "OUTPUT":
    save_exit(1 if fails("available") else 0)
if args[:3] == ["-w", "10", "-S"] and args[3] == "OUTPUT":
    if fails("show"):
        save_exit(2)
    print("-P OUTPUT ACCEPT")
    for chain, count in family_state["jumps"].items():
        for _ in range(count):
            print(f"-A OUTPUT -j {chain}")
    save_exit(0)
if args[:3] == ["-w", "10", "-nL"]:
    if fails("query"):
        save_exit(2)
    save_exit(0 if args[3] in family_state["chains"] else 1)
if args[:3] == ["-w", "10", "-C"]:
    if fails("query"):
        save_exit(2)
    chain = args[3]
    if chain == "OUTPUT":
        target = jump_target(args[4:])
        if target not in family_state["chains"]:
            save_exit(2)
        save_exit(0 if family_state["jumps"].get(target, 0) > 0 else 1)
    if chain not in family_state["chains"]:
        save_exit(1)
    save_exit(0 if rule_key(args[4:]) in family_state["chains"][chain] else 1)
if args[:3] == ["-w", "10", "-N"]:
    if fails("new"):
        save_exit(1)
    chain = args[3]
    if chain in family_state["chains"]:
        save_exit(1)
    family_state["chains"][chain] = []
    save_exit(0)
if args[:3] == ["-w", "10", "-A"]:
    rule = args[4:]
    if fails("append") or fails(append_op(rule)):
        save_exit(1)
    chain = args[3]
    if chain not in family_state["chains"]:
        save_exit(1)
    family_state["chains"][chain].append(rule_key(rule))
    save_exit(0)
if args[:3] == ["-w", "10", "-I"]:
    if fails("insert"):
        save_exit(1)
    chain = args[-1]
    if chain not in family_state["chains"]:
        save_exit(2)
    family_state["jumps"][chain] = family_state["jumps"].get(chain, 0) + 1
    save_exit(0)
if args[:3] == ["-w", "10", "-D"]:
    if fails("delete-jump"):
        save_exit(1)
    chain = args[-1]
    count = family_state["jumps"].get(chain, 0)
    if count <= 0:
        save_exit(1)
    family_state["jumps"][chain] = count - 1
    save_exit(0)
if args[:3] == ["-w", "10", "-F"]:
    if fails("flush"):
        save_exit(1)
    chain = args[3]
    if chain not in family_state["chains"]:
        save_exit(1)
    family_state["chains"][chain] = []
    save_exit(0)
if args[:3] == ["-w", "10", "-X"]:
    if fails("delete-chain"):
        save_exit(1)
    chain = args[3]
    if chain not in family_state["chains"] or family_state["jumps"].get(chain, 0):
        save_exit(1)
    if family_state["chains"][chain]:
        save_exit(1)
    del family_state["chains"][chain]
    save_exit(0)
save_exit(2)
''',
        encoding="utf-8",
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    for name in ("iptables", "ip6tables"):
        link = directory / name
        link.write_text(f"#!/bin/sh\nexec {fake} {name} \"$@\"\n", encoding="utf-8")
        link.chmod(link.stat().st_mode | stat.S_IXUSR)


def _fake_firewall_env(tmp_path: Path, fail: str = "") -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    if not (bin_dir / "iptables").exists():
        _write_fake_firewall(bin_dir)
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "F97_FIREWALL_SUDO": "",
            "FAKE_FIREWALL_STATE": str(tmp_path / "firewall-state.json"),
            "FAKE_FIREWALL_FAIL": fail,
        }
    )
    return env


def _run_firewall(tmp_path: Path, action: str, chain: str, state_dir: Path, fail: str = ""):
    env = _fake_firewall_env(tmp_path, fail)
    return subprocess.run(
        ["sh", str(ROOT / ".github/scripts/fase09_7_firewall_guard.sh"), action, chain, str(state_dir)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _firewall_state(tmp_path: Path) -> dict:
    path = tmp_path / "firewall-state.json"
    return {} if not path.exists() else __import__("json").loads(path.read_text())


def _assert_no_owned_firewall_residue(tmp_path: Path, chain: str) -> None:
    state = _firewall_state(tmp_path)
    for family in ("iptables", "ip6tables"):
        family_state = state.get(family, {"chains": {}, "jumps": {}})
        assert chain not in family_state.get("chains", {})
        assert family_state.get("jumps", {}).get(chain, 0) == 0


def test_fake_firewall_models_output_rules_and_missing_chain_checks(tmp_path: Path):
    env = _fake_firewall_env(tmp_path)
    state_file = tmp_path / "firewall-state.json"
    state_file.write_text(
        '{"iptables":{"chains":{"F97_FRONTEND_EGRESS":[]},"jumps":{"F97_FRONTEND_EGRESS":1}}}',
        encoding="utf-8",
    )
    listed = subprocess.run(
        ["iptables", "-w", "10", "-S", "OUTPUT"],
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert listed.returncode == 0
    assert "-A OUTPUT -j F97_FRONTEND_EGRESS" in listed.stdout.splitlines()
    missing = subprocess.run(
        ["iptables", "-w", "10", "-C", "OUTPUT", "-j", "NO_SUCH_CHAIN"],
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert missing.returncode == 2


def test_firewall_helper_setup_cleanup_and_partial_failures_are_fail_closed(tmp_path: Path):
    state_dir = tmp_path / "state"
    state_dir.mkdir(mode=0o700)
    assert _run_firewall(tmp_path, "setup", "F97_FRONTEND_EGRESS", state_dir).returncode == 0
    assert _run_firewall(tmp_path, "cleanup", "F97_FRONTEND_EGRESS", state_dir).returncode == 0
    _assert_no_owned_firewall_residue(tmp_path, "F97_FRONTEND_EGRESS")

    partial = tmp_path / "partial"
    partial.mkdir(mode=0o700)
    assert _run_firewall(tmp_path, "setup", "FASE097_EGRESS", partial, "iptables:insert").returncode != 0
    assert _run_firewall(tmp_path, "cleanup", "FASE097_EGRESS", partial).returncode == 0
    _assert_no_owned_firewall_residue(tmp_path, "FASE097_EGRESS")

    partial6 = tmp_path / "partial6"
    partial6.mkdir(mode=0o700)
    assert _run_firewall(tmp_path, "setup", "FASE097_AUDIT_EGRESS", partial6, "ip6tables:append").returncode != 0
    assert _run_firewall(tmp_path, "cleanup", "FASE097_AUDIT_EGRESS", partial6).returncode == 0
    _assert_no_owned_firewall_residue(tmp_path, "FASE097_AUDIT_EGRESS")


@pytest.mark.parametrize("chain", ALLOWED_FIREWALL_CHAINS)
def test_firewall_helper_setup_cleanup_repeated_for_all_owned_chains(tmp_path: Path, chain: str):
    state_dir = tmp_path / chain
    state_dir.mkdir(mode=0o700)
    assert _run_firewall(tmp_path, "setup", chain, state_dir).returncode == 0
    state = _firewall_state(tmp_path)
    for family in ("iptables", "ip6tables"):
        ops = state[family]["chains"][chain]
        assert "-o\0lo\0-j\0RETURN" in ops
        assert "-m\0conntrack\0--ctstate\0ESTABLISHED,RELATED\0-j\0RETURN" in ops
        assert "-j\0REJECT" in ops
        assert state[family]["jumps"][chain] == 1
    assert _run_firewall(tmp_path, "cleanup", chain, state_dir).returncode == 0
    assert _run_firewall(tmp_path, "cleanup", chain, state_dir).returncode == 0
    _assert_no_owned_firewall_residue(tmp_path, chain)


@pytest.mark.parametrize("family", ["iptables", "ip6tables"])
@pytest.mark.parametrize("append_failure", ["append-loopback", "append-conntrack", "append-reject"])
def test_firewall_helper_never_inserts_family_jump_after_append_failure(
    tmp_path: Path, family: str, append_failure: str
):
    chain = "FASE097_EGRESS"
    state_dir = tmp_path / f"{family}-{append_failure}"
    state_dir.mkdir(mode=0o700)
    failed = _run_firewall(tmp_path, "setup", chain, state_dir, f"{family}:{append_failure}")
    assert failed.returncode != 0
    assert _firewall_state(tmp_path)[family]["jumps"].get(chain, 0) == 0
    assert _run_firewall(tmp_path, "cleanup", chain, state_dir).returncode == 0
    _assert_no_owned_firewall_residue(tmp_path, chain)


@pytest.mark.parametrize("family", ["iptables", "ip6tables"])
@pytest.mark.parametrize("operation", ["insert", "delete-jump", "flush", "delete-chain"])
def test_firewall_helper_partial_failures_preserve_markers_until_recovered(
    tmp_path: Path, family: str, operation: str
):
    chain = "FASE097_AUDIT_EGRESS"
    state_dir = tmp_path / f"{family}-{operation}"
    state_dir.mkdir(mode=0o700)
    if operation == "insert":
        assert _run_firewall(tmp_path, "setup", chain, state_dir, f"{family}:insert").returncode != 0
        assert (state_dir / f"{'ipv4' if family == 'iptables' else 'ipv6'}-jump").exists()
    else:
        assert _run_firewall(tmp_path, "setup", chain, state_dir).returncode == 0
        assert _run_firewall(tmp_path, "cleanup", chain, state_dir, f"{family}:{operation}").returncode != 0
        assert (state_dir / f"{'ipv4' if family == 'iptables' else 'ipv6'}-chain").exists()
    assert _run_firewall(tmp_path, "cleanup", chain, state_dir).returncode == 0
    _assert_no_owned_firewall_residue(tmp_path, chain)


def test_firewall_helper_cleanup_before_prepare_empty_state_and_inconsistent_markers(tmp_path: Path):
    chain = "F97_FRONTEND_EGRESS"
    empty = tmp_path / "empty"
    empty.mkdir(mode=0o700)
    assert _run_firewall(tmp_path, "cleanup", chain, empty).returncode == 0
    _assert_no_owned_firewall_residue(tmp_path, chain)

    inconsistent = tmp_path / "inconsistent"
    inconsistent.mkdir(mode=0o700)
    (inconsistent / "ipv4-jump").write_text("", encoding="utf-8")
    (tmp_path / "firewall-state.json").write_text(
        '{"iptables":{"chains":{"F97_FRONTEND_EGRESS":[]},"jumps":{"F97_FRONTEND_EGRESS":1}},"ip6tables":{"chains":{},"jumps":{}}}',
        encoding="utf-8",
    )
    assert _run_firewall(tmp_path, "cleanup", chain, inconsistent).returncode == 0
    state = _firewall_state(tmp_path)
    assert state["iptables"]["jumps"].get(chain, 0) == 0
    assert chain in state["iptables"]["chains"]


def test_firewall_helper_preserves_unowned_resources_and_reports_cleanup_errors(tmp_path: Path):
    state_dir = tmp_path / "state"
    state_dir.mkdir(mode=0o700)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_fake_firewall(bin_dir)
    state_file = tmp_path / "firewall-state.json"
    state_file.write_text(
        '{"iptables":{"chains":{"F97_FRONTEND_EGRESS":true},"jumps":{}},"ip6tables":{"chains":{},"jumps":{}}}',
        encoding="utf-8",
    )
    preexisting = _run_firewall(tmp_path, "setup", "F97_FRONTEND_EGRESS", state_dir)
    assert preexisting.returncode != 0
    preserved = _run_firewall(tmp_path, "cleanup", "F97_FRONTEND_EGRESS", state_dir)
    assert preserved.returncode == 0
    assert "F97_FRONTEND_EGRESS" in _firewall_state(tmp_path)["iptables"]["chains"]

    owned = tmp_path / "owned"
    owned.mkdir(mode=0o700)
    state_file.write_text("{}", encoding="utf-8")
    assert _run_firewall(tmp_path, "setup", "FASE097_EGRESS", owned).returncode == 0
    assert _run_firewall(tmp_path, "cleanup", "FASE097_EGRESS", owned, "iptables:delete-jump").returncode != 0
    assert _run_firewall(tmp_path, "cleanup", "FASE097_EGRESS", owned).returncode == 0


def test_firewall_helper_blocks_query_errors_duplicates_and_unsupported_chains(tmp_path: Path):
    state_dir = tmp_path / "state"
    state_dir.mkdir(mode=0o700)
    assert _run_firewall(tmp_path, "setup", "F97_FRONTEND_EGRESS", state_dir, "iptables:query").returncode != 0
    unsupported = _run_firewall(tmp_path, "setup", "LEGACY_EGRESS", state_dir)
    assert unsupported.returncode == 2

    duplicated = tmp_path / "duplicated"
    duplicated.mkdir(mode=0o700)
    (duplicated / "ipv4-chain").write_text("", encoding="utf-8")
    (duplicated / "ipv4-jump").write_text("", encoding="utf-8")
    (tmp_path / "firewall-state.json").write_text(
        '{"iptables":{"chains":{"F97_FRONTEND_EGRESS":true},"jumps":{"F97_FRONTEND_EGRESS":2}},"ip6tables":{"chains":{},"jumps":{}}}',
        encoding="utf-8",
    )
    assert _run_firewall(tmp_path, "cleanup", "F97_FRONTEND_EGRESS", duplicated).returncode == 0
    assert _firewall_state(tmp_path)["iptables"]["chains"] == {}


def test_firewall_helper_contract_is_limited_to_f9_7_owned_chains():
    helper = _source(".github/scripts/fase09_7_firewall_guard.sh")
    for chain in ALLOWED_FIREWALL_CHAINS:
        assert chain in helper
    assert "LEGACY_EGRESS" not in helper
    assert "|| true" not in helper
    assert "-S OUTPUT" in helper
    assert "-C OUTPUT" not in helper
    assert 'grep -Fx -- "-A OUTPUT -j $CHAIN"' in helper
    assert "cleanup_family iptables ipv4" in helper
    assert "cleanup_family ip6tables ipv6" in helper


def _job_ids(workflow: str) -> set[str]:
    jobs = workflow.split("\njobs:\n", 1)[1]
    return set(re.findall(r"^  ([A-Za-z0-9_-]+):\n", jobs, flags=re.MULTILINE))


def _security_audit_job(workflow: str) -> str:
    return workflow.split("  security-audit:\n", 1)[1]


def test_security_audit_aggregator_is_blocking_for_all_required_jobs(tmp_path: Path):
    workflow = _source(".github/workflows/security-audit.yml")
    jobs = _job_ids(workflow)
    expected_needs = jobs - {"security-audit"}
    job = _security_audit_job(workflow)
    needs_match = re.search(r"needs: \[([^\]]+)\]", job)
    assert needs_match
    needs = {item.strip() for item in needs_match.group(1).split(",")}
    assert needs == expected_needs
    assert "if: always()" in job
    assert "continue-on-error" not in workflow

    env_map = dict(re.findall(r"\n\s+([A-Z0-9_]+): \$\{\{ needs\.([A-Za-z0-9_-]+)\.result \}\}", job))
    assert set(env_map.values()) == expected_needs
    run_block = job.split("run: |\n", 1)[1]
    for variable in env_map:
        assert f'if [ "${variable}" != "success" ]; then' in run_block

    script = "\n".join(line[10:] for line in run_block.splitlines() if line.startswith("          "))
    summary = tmp_path / "summary.md"
    env = os.environ.copy()
    env.update({variable: "success" for variable in env_map})
    env["GITHUB_STEP_SUMMARY"] = str(summary)
    assert subprocess.run(["sh", "-c", script], env=env, check=False).returncode == 0
    for bad_status in ("failure", "cancelled", "skipped"):
        env_bad = env.copy()
        env_bad[next(iter(env_map))] = bad_status
        assert subprocess.run(["sh", "-c", script], env=env_bad, check=False).returncode != 0


def test_f9_7_contract_workflow_triggers_cover_wp04_paths_and_protected_inventory():
    workflow = _source(".github/workflows/f9-7-contract.yml")
    for required in (
        ".env.example",
        ".githooks/**",
        ".github/scripts/fase09_7_firewall_guard.sh",
        ".github/actionlint.yaml",
        "tests/test_fase09_7_release_gates.py",
        "config/**",
        *PROTECTED_PATHS,
    ):
        assert f"'{required}'" in workflow


def test_f9_7_workflows_run_release_gate_tests_in_focused_jobs():
    security = _source(".github/workflows/security-audit.yml")
    contract = _source(".github/workflows/f9-7-contract.yml")
    assert "tests/test_fase09_7_release_gates.py" in security.split(
        "  fase09-7-remediation:\n", 1
    )[1].split("\n  security-audit:", 1)[0]
    assert "tests/test_fase09_7_release_gates.py" in contract.split(
        "Run local-only Python and PostgreSQL contracts", 1
    )[1]


def _validate_f9_7_setpriv_env_contract(source: str) -> None:
    for required in (
        "sudo chmod -R go+rX,go-w \"$GITHUB_WORKSPACE\"",
        "sudo setpriv --reuid=65534 --regid=65534 --clear-groups \\",
        "--bounding-set=-all --inh-caps=-all --ambient-caps=-all --no-new-privs \\",
        "env -i HOME=/tmp CI=true PATH=\"$PATH\" PYTHONPATH=\"$GITHUB_WORKSPACE\" \\",
        'F97_BASELINE_COMMIT="$F97_BASELINE_COMMIT"',
        'F97_CANDIDATE_MODE="$F97_CANDIDATE_MODE"',
        'F97_CANDIDATE_COMMIT="$F97_CANDIDATE_COMMIT"',
        'F97_CANDIDATE_TREE="$F97_CANDIDATE_TREE"',
        "GIT_CONFIG_COUNT=1",
        "GIT_CONFIG_KEY_0=safe.directory",
        'GIT_CONFIG_VALUE_0="$GITHUB_WORKSPACE"',
        "PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider",
    ):
        assert required in source
    assert "safe.directory=*" not in source
    assert "safe.directory *" not in source
    assert "git config --global --add safe.directory" not in source
    assert "F97_CANDIDATE_COMMIT:-" not in source
    assert "F97_CANDIDATE_TREE:-" not in source
    assert "chown" not in source
    assert "GIT_OPTIONAL_LOCKS" not in source


@pytest.mark.parametrize(
    "relative",
    [".github/workflows/security-audit.yml", ".github/workflows/f9-7-contract.yml"],
)
def test_f9_7_setpriv_env_boundary_passes_candidate_and_limited_safe_directory(relative: str):
    _validate_f9_7_setpriv_env_contract(_source(relative))


@pytest.mark.parametrize(
    "mutator",
    [
        lambda s: s.replace('F97_BASELINE_COMMIT="$F97_BASELINE_COMMIT" \\\n', ""),
        lambda s: s.replace('F97_CANDIDATE_MODE="$F97_CANDIDATE_MODE" \\\n', ""),
        lambda s: s.replace('F97_CANDIDATE_COMMIT="$F97_CANDIDATE_COMMIT" \\\n', ""),
        lambda s: s.replace('F97_CANDIDATE_TREE="$F97_CANDIDATE_TREE" \\\n', ""),
        lambda s: s.replace("GIT_CONFIG_COUNT=1 \\\n", ""),
        lambda s: s.replace("GIT_CONFIG_KEY_0=safe.directory \\\n", ""),
        lambda s: s.replace('GIT_CONFIG_VALUE_0="$GITHUB_WORKSPACE"', "GIT_CONFIG_VALUE_0=\"*\""),
    ],
)
def test_f9_7_setpriv_env_boundary_mutations_are_rejected(mutator):
    with pytest.raises(AssertionError):
        _validate_f9_7_setpriv_env_contract(mutator(_source(".github/workflows/security-audit.yml")))


def test_f9_7_workflow_cleanup_blocks_are_state_guarded_and_preserve_markers():
    cleanup_expectations = {
        ".github/workflows/security-audit.yml": (
            'state_dir="${F97_FRONTEND_FIREWALL_STATE:-}"',
            'firewall_state="${FASE097_AUDIT_FIREWALL_STATE:-}"',
            'audit_state="${FASE097_AUDIT_STATE:-}"',
        ),
        ".github/workflows/f9-7-contract.yml": (
            'state_dir="${F97_FRONTEND_FIREWALL_STATE:-}"',
            'firewall_state="${FASE097_FIREWALL_STATE:-}"',
            'state_dir="${FASE097_STATE:-}"',
        ),
    }
    for relative, expected_snippets in cleanup_expectations.items():
        workflow = _source(relative)
        for snippet in expected_snippets:
            assert snippet in workflow
        assert 'rm -rf -- "$F97_FRONTEND_FIREWALL_STATE"' not in workflow
        assert 'rm -rf -- "$FASE097_FIREWALL_STATE"' not in workflow
        assert 'rm -rf -- "$FASE097_AUDIT_FIREWALL_STATE"' not in workflow
        assert 'rm -rf -- "$FASE097_STATE"' not in workflow
        assert 'rm -rf -- "$FASE097_AUDIT_STATE"' not in workflow
        assert "state directory is missing" in workflow
        assert 'if [ "$cleanup_status" -eq 0 ]; then' in workflow


def test_wp04_executable_modes_are_tracked_as_100755():
    expected = {
        ".githooks/pre-commit": "100755",
        ".githooks/pre-push": "100755",
        ".github/scripts/fase09_7_firewall_guard.sh": "100755",
    }
    output = _git(["ls-files", "-s", *expected]).stdout.splitlines()
    observed = {line.split("\t", 1)[1]: line.split(" ", 1)[0] for line in output}
    assert observed == expected


def test_environment_example_uses_short_placeholders_and_no_scanner_hits():
    source = _source(".env.example")
    assert "LEAD_CAPTURE" not in source
    assert _credential_scan_tree(ROOT, os.environ["F97_CANDIDATE_TREE"]) == 1


def test_security_audit_uses_candidate_tree_scan_and_no_workspace_lists():
    workflow = _source(".github/workflows/security-audit.yml")
    assert "git grep -a -q -E \"$F97_CREDENTIAL_PATTERN\" \"$F97_CANDIDATE_TREE\"" in workflow
    credential_job = workflow.split("  credential-scan:\n", 1)[1].split("\n  release-gates:", 1)[0]
    assert "find ." not in credential_job
    assert "credential_files.list" not in credential_job
    assert "grep -I" not in credential_job
    assert "content redacted" in credential_job


def test_workflows_use_explicit_candidate_sha_and_index_clean_tree():
    for relative in (".github/workflows/security-audit.yml", ".github/workflows/f9-7-contract.yml"):
        workflow = _source(relative)
        assert "F97_BASELINE_COMMIT: 8ab1cdf9173b8093781e75ba32c2fea9ae931b14" in workflow
        assert "github.event.pull_request.head.sha" in workflow
        assert "github.sha" in workflow
        assert "ref: ${{ github.event_name == 'pull_request' && github.event.pull_request.head.sha || github.sha }}" in workflow
        assert "fetch-depth: 0" in workflow
        assert 'test "$(git rev-parse HEAD)" = "$F97_CANDIDATE_COMMIT"' in workflow
        assert "git merge-base --is-ancestor \"$F97_BASELINE_COMMIT\" \"$F97_CANDIDATE_COMMIT\"" in workflow
        assert "F97_CANDIDATE_TREE" in workflow
        assert 'test "$(git rev-parse "$F97_CANDIDATE_COMMIT^{tree}")" = "$F97_CANDIDATE_TREE"' in workflow
        assert 'git write-tree' not in workflow


def test_changed_only_eol_and_ranged_whitespace_are_used_by_release_gates():
    for relative in (".github/workflows/security-audit.yml", ".github/workflows/f9-7-contract.yml"):
        workflow = _source(relative)
        assert "'git', 'diff', '--name-status', '-z', '--find-renames', '--find-copies', '--diff-filter=ACMR'" in workflow
        assert "'git', 'cat-file', 'blob'" in workflow
        assert "b'\\r\\n'" in workflow
        assert "git diff --check \"$F97_BASELINE_COMMIT\" \"$F97_CANDIDATE_COMMIT\"" in workflow
        assert "git diff --check" in workflow


def test_firewall_helper_is_the_only_f9_7_chain_implementation_in_workflows():
    for relative in (".github/workflows/security-audit.yml", ".github/workflows/f9-7-contract.yml"):
        workflow = _source(relative)
        for chain in ALLOWED_FIREWALL_CHAINS:
            if chain in workflow:
                assert re.search(rf"fase09_7_firewall_guard\.sh\"? setup {chain}", workflow)
                assert re.search(rf"fase09_7_firewall_guard\.sh\"? cleanup {chain}", workflow)
                assert f"iptables -w 10 -N {chain}" not in workflow
                assert f"ip6tables -w 10 -N {chain}" not in workflow
