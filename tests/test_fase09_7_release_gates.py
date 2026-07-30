from __future__ import annotations

import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

from tests.test_fase09_7_pipeline_no_regression import (
    F97_BASELINE_COMMIT,
    PROTECTED_PATHS,
    protected_closure_findings,
    resolve_candidate_tree,
)


ROOT = Path(__file__).resolve().parents[1]
ACTIONLINT_VERSION = "1.7.7"
ACTIONLINT_ASSET = f"actionlint_{ACTIONLINT_VERSION}_linux_amd64.tar.gz"
ACTIONLINT_SHA256 = "023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757"
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


def test_candidate_identity_uses_explicit_tree_and_preserves_staged_index():
    _, candidate_tree = resolve_candidate_tree()
    assert candidate_tree == os.environ["F97_CANDIDATE_TREE"]
    assert _git(["write-tree"]).stdout.strip() == candidate_tree


def _validate_actionlint_contract(source: str) -> None:
    assert f"ACTIONLINT_VERSION: '{ACTIONLINT_VERSION}'" in source
    assert f"ACTIONLINT_ASSET: {ACTIONLINT_ASSET}" in source
    assert "linux_x86_64" not in source
    assert "linux_386" not in source
    assert "linux_arm64" not in source
    assert ACTIONLINT_SHA256 in source
    assert "sha256sum -c -" in source
    assert "test \"$actionlint_version\" = \"$ACTIONLINT_VERSION\"" in source
    assert "find .github/workflows" in source
    assert "-name '*.yml'" in source
    assert "-name '*.yaml'" in source
    assert "-print0" in source
    assert "xargs -0" in source
    assert "test -s \"$workflow_list\"" in source
    assert "RUNNER_TEMP" in source
    assert "$GITHUB_WORKSPACE/actionlint" not in source
    assert "curl -fsSLo actionlint.tar.gz" not in source


@pytest.mark.parametrize(
    "relative",
    [".github/workflows/security-audit.yml", ".github/workflows/f9-7-contract.yml"],
)
def test_actionlint_tuple_is_immutable_and_nul_safe(relative: str):
    _validate_actionlint_contract(_source(relative))


@pytest.mark.parametrize(
    "mutator",
    [
        lambda s: s.replace("linux_amd64", "linux_x86_64"),
        lambda s: s.replace("linux_amd64", "linux_386"),
        lambda s: s.replace("linux_amd64", "linux_arm64"),
        lambda s: s.replace("linux_amd64", "linux_ppc64le"),
        lambda s: s.replace(ACTIONLINT_SHA256, "0" * 64),
        lambda s: s.replace(ACTIONLINT_VERSION, "1.7.8", 1),
        lambda s: s.replace('test "$actionlint_version" = "$ACTIONLINT_VERSION"', "true"),
        lambda s: s.replace("-name '*.yaml'", "-name '*.yml'"),
        lambda s: s.replace("$RUNNER_TEMP/actionlint", "$GITHUB_WORKSPACE/actionlint"),
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


def test_changed_only_eol_fails_for_invalid_git_objects(tmp_path: Path):
    repo = tmp_path / "eol-invalid"
    repo.mkdir()
    _init_repo(repo)
    _write(repo / "tracked.txt", "ok\n")
    baseline = _commit(repo, "baseline")

    with pytest.raises(subprocess.CalledProcessError):
        _changed_eol_findings(repo, baseline, ZERO_SHA)


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
family_state = state.setdefault(family, {"chains": {}, "jumps": {}})
fail = os.environ.get("FAKE_FIREWALL_FAIL", "")

def save_exit(code):
    state_path.write_text(json.dumps(state, sort_keys=True))
    raise SystemExit(code)

def fails(op):
    return fail in {f"{family}:{op}", f"all:{op}"}

def chain_name_after(flag):
    return args[args.index(flag) + 1]

if args[:3] == ["-w", "10", "-L"] and args[3] == "OUTPUT":
    save_exit(1 if fails("available") else 0)
if args[:3] == ["-w", "10", "-nL"]:
    if fails("query"):
        save_exit(2)
    save_exit(0 if args[3] in family_state["chains"] else 1)
if args[:3] == ["-w", "10", "-C"]:
    if fails("query"):
        save_exit(2)
    chain = args[-1]
    save_exit(0 if family_state["jumps"].get(chain, 0) > 0 else 1)
if args[:3] == ["-w", "10", "-N"]:
    if fails("new"):
        save_exit(1)
    chain = args[3]
    if chain in family_state["chains"]:
        save_exit(1)
    family_state["chains"][chain] = True
    save_exit(0)
if args[:3] == ["-w", "10", "-A"]:
    if fails("append"):
        save_exit(1)
    save_exit(0 if args[3] in family_state["chains"] else 1)
if args[:3] == ["-w", "10", "-I"]:
    if fails("insert"):
        save_exit(1)
    chain = args[-1]
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
    save_exit(0 if args[3] in family_state["chains"] else 1)
if args[:3] == ["-w", "10", "-X"]:
    if fails("delete-chain"):
        save_exit(1)
    chain = args[3]
    if chain not in family_state["chains"] or family_state["jumps"].get(chain, 0):
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


def _run_firewall(tmp_path: Path, action: str, chain: str, state_dir: Path, fail: str = ""):
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


def test_firewall_helper_setup_cleanup_and_partial_failures_are_fail_closed(tmp_path: Path):
    state_dir = tmp_path / "state"
    state_dir.mkdir(mode=0o700)
    assert _run_firewall(tmp_path, "setup", "F97_FRONTEND_EGRESS", state_dir).returncode == 0
    assert _run_firewall(tmp_path, "cleanup", "F97_FRONTEND_EGRESS", state_dir).returncode == 0
    assert _firewall_state(tmp_path)["iptables"]["chains"] == {}
    assert _firewall_state(tmp_path)["ip6tables"]["chains"] == {}

    partial = tmp_path / "partial"
    partial.mkdir(mode=0o700)
    assert _run_firewall(tmp_path, "setup", "FASE097_EGRESS", partial, "iptables:insert").returncode != 0
    assert _run_firewall(tmp_path, "cleanup", "FASE097_EGRESS", partial).returncode == 0

    partial6 = tmp_path / "partial6"
    partial6.mkdir(mode=0o700)
    assert _run_firewall(tmp_path, "setup", "FASE097_AUDIT_EGRESS", partial6, "ip6tables:append").returncode != 0
    assert _run_firewall(tmp_path, "cleanup", "FASE097_AUDIT_EGRESS", partial6).returncode == 0


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
        "tests/test_fase09_7_release_gates.py",
        "config/**",
        *PROTECTED_PATHS,
    ):
        assert f"'{required}'" in workflow


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
        assert 'test "$(git write-tree)" = "$F97_CANDIDATE_TREE"' in workflow


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
