from pathlib import Path
import os
import re
import subprocess
import shlex
import shutil


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_agents_declares_simple_flow_and_boundaries():
    text = read("AGENTS.md")
    assert "feat/* o docs/* desde desarrollo" in text
    assert "DB Sync" in text
    assert "workflow_dispatch" in read(".github/workflows/db-sync-to-pro.yml").split("permissions:", 1)[0]
    assert "Work Packages" in text
    assert "grants persistentes" in text
    assert "digests documentales" in text
    assert "REDEFINICION.md` fue retirado definitivamente" in text


def test_obsidian_is_living_authority_and_redefinition_is_removed():
    state = read(".context/estado_del_proyecto.md")

    assert "> Autoridad operativa única." in state
    assert "## Corte vigente" in state
    assert "El candidato no se publicó:" in state
    assert "Development sigue NO-GO" in state
    assert "REDEFINICION.md" not in state
    assert not (ROOT / "REDEFINICION.md").exists()


def test_agents_no_longer_uses_wp_digest_as_authority():
    text = read("AGENTS.md")
    sprint_index = read(".context/backlog_tareas/req_est_001_sprint_1/_index.md")

    assert "Los Work Packages, digests documentales, grants persistentes" in text
    assert "Apruebo WP-<ID>" not in text
    assert "grant persistente WP/digest" not in text
    assert "acordada por WP" not in sprint_index
    assert "WP exija" not in sprint_index
    assert "aprobado por digest" not in sprint_index


def test_security_audit_keeps_required_check_name():
    text = read(".github/workflows/security-audit.yml")
    assert "name: security-audit" in text
    assert "scripts/security/scan_credentials.sh --tree" in text
    assert "Protected Path Integrity" in text
    assert "validate_work_package.py" not in text
    assert "validate_context_graph.py" not in text


def test_h2_main_gate_checkout_resolves_verified_ancestor(tmp_path):
    workflow = read(".github/workflows/security-audit.yml")
    gate = workflow.split("  h2-main-production-expand-gate:", 1)[1].split("  security-audit:", 1)[0]
    checkout = gate.split("      - uses: actions/checkout@", 1)[1].split("      - name:", 1)[0]
    configured_depth = re.search(r"^\s+fetch-depth:\s*(\d+)\s*$", checkout, re.MULTILINE)
    depth = int(configured_depth.group(1)) if configured_depth else 1
    fetch = next(line.strip() for line in gate.splitlines() if line.strip().startswith("git fetch --no-tags origin "))

    def git(*args, cwd):
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

    upstream = tmp_path / "upstream"
    upstream.mkdir()
    git("init", "-q", "--initial-branch=certificacion", cwd=upstream)
    revisions = []
    for label in ("main baseline", "verified candidate", "documentation only"):
        (upstream / "evidence.txt").write_text(label, encoding="utf-8")
        git("add", "evidence.txt", cwd=upstream)
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", label, cwd=upstream)
        revisions.append(git("rev-parse", "HEAD", cwd=upstream))
    git("branch", "main", revisions[0], cwd=upstream)
    git("update-ref", "refs/pull/1/head", revisions[2], cwd=upstream)
    clone = tmp_path / "checkout"
    options = ["clone", "-q", "--single-branch", "--branch", "certificacion"]
    if depth:
        options.append(f"--depth={depth}")
    git(*options, upstream.as_uri(), str(clone), cwd=tmp_path)
    env = {**os.environ, "PR_NUMBER": "1", "PR_HEAD_SHA": revisions[2]}
    subprocess.run(["bash", "-eu", "-c", fetch], cwd=clone, env=env, check=True, capture_output=True, text=True)
    git("cat-file", "-e", f"{revisions[1]}^{{commit}}", cwd=clone)
    git("merge-base", "--is-ancestor", revisions[1], "HEAD", cwd=clone)


def test_security_audit_allowlists_scanner_worktree_helper_and_pre_push():
    workflow = read(".github/workflows/security-audit.yml")
    guard = read("scripts/security/protected_path_scope_guard.sh")
    extra_line = next(line for line in guard.splitlines() if line.strip().startswith("allowed_h3_extra='"))
    extra_pattern = extra_line.split("allowed_h3_extra='", 1)[1].split("'", 1)[0]
    local_block = guard.split("allowed_h3_local=$(cat <<'H3_LOCAL_PATHS'", 1)[1]
    local_block = local_block.split("\nH3_LOCAL_PATHS", 1)[0]
    local_paths = {line.strip() for line in local_block.splitlines() if line.strip()}

    expected_paths = {
        ".githooks/pre-push",
        "scripts/security/scan_worktree_file.py",
        "tests/h3req1_c03_docker_daemon_identity_f2d.py",
    }
    assert all(re.fullmatch(extra_pattern, path) for path in expected_paths)
    assert expected_paths <= local_paths
    assert "run: bash scripts/security/protected_path_scope_guard.sh --compare-candidate" in workflow


def test_security_audit_installs_python_dependencies_from_hashed_lockfile():
    workflow = read(".github/workflows/security-audit.yml")

    assert "python3 -m pip install --require-hashes -r requirements-pipeline.txt" in workflow
    assert "python3 -m pip install pytest requests python-dotenv PyPDF2 playwright" not in workflow


def test_protected_path_guard_preserves_git_filename_boundaries():
    workflow = read(".github/workflows/security-audit.yml")
    guard = read("scripts/security/protected_path_scope_guard.sh")

    assert "bash scripts/security/protected_path_scope_guard.sh --compare-candidate" in workflow
    assert "git diff --name-only -z" in guard
    assert 'protected_path_scope_capture "$changed_path_file"' in guard
    assert "read -r -d '' candidate" in guard
    assert "unsupported control character" in guard


def test_manual_security_audit_dispatch_fails_closed_without_trusted_diff_base():
    text = read(".github/workflows/security-audit.yml")
    guard = read("scripts/security/protected_path_scope_guard.sh")

    assert "PROTECTED_BASELINE_SHA: ${{ github.event.pull_request.base.sha || github.event.before }}" in text
    assert "PROTECTED_BASELINE_SHA: ${{ github.event.pull_request.base.sha || github.event.before || github.sha }}" not in text
    assert "bash scripts/security/protected_path_scope_guard.sh --compare-candidate" in text
    assert 'if [ -z "$PROTECTED_BASELINE_SHA" ]; then' in guard
    assert "protected-path checks require a trusted pull_request or push baseline" in guard
    assert 'if [ "$base" = "0000000000000000000000000000000000000000" ]; then' in guard
    assert "git hash-object -t tree -w /dev/null" in guard
    assert 'base="$PROTECTED_BASELINE_SHA"' in guard
    assert "database changes require a trusted pull_request or push baseline" in text


def test_postgrest_ci_harness_invokes_binary_with_readable_config():
    workflow = read(".github/workflows/security-audit.yml")

    assert 'chmod 644 "$postgrest_config"' in workflow
    assert "/bin/postgrest /etc/postgrest.conf" in workflow


def test_pwi_is_external_and_candidate_workflow_is_removed():
    audit = read(".github/workflows/security-audit.yml")
    pwi_readme = read("scripts/security/pwi_worker/README.md")
    assert not (ROOT / ".github/workflows/protected-workflow-integrity.yml").exists()
    assert "pwi-worker-contract:" in audit
    assert "name: PWI Worker Contract" in audit
    assert "Protected Workflow Integrity" in pwi_readme
    assert "check from its GitHub App" in pwi_readme
    assert "Pull requests: read" in pwi_readme
    assert "Checks: write" in pwi_readme
    active_triggers = audit.split("permissions:", 1)[0]
    assert "pull_request_review:" not in active_triggers
    assert "trusted-workflow-integrity:" not in audit
    assert "needs: [trusted-workflow-integrity," not in audit
    assert "needs.trusted-workflow-integrity.result" not in audit
    assert "actions/workflows/protected-workflow-integrity.yml/runs" not in audit


def test_admin_invitation_bff_sanitizes_internal_edge_business_codes():
    bff = read("web/functions/_lib/admin-bff.ts")

    assert "const SAFE_INVITE_ERROR_CODES = new Set([" in bff
    assert "SAFE_INVITE_ERROR_CODES.has(requestedEdgeCode)" in bff
    assert "? requestedEdgeCode" in bff
    assert ": 'invitation_failed'" in bff
    assert "edgeResponse.status" not in bff
    assert "const forbidden = rpcStatus === 403;" in bff
    assert "code: mfaRequired ? 'mfa_required' : forbidden ? 'forbidden' : 'rpc_failed'" in bff
    assert "mfaRequired ? 403 : rpcStatus === 403 ? 403 : rpcStatus === 400 ? 400 : rpcStatus === 503 ? 503 : 502" in bff
    assert "error.code || 'rpc_failed'" not in bff


def test_pre_commit_scans_staged_blobs_not_working_tree():
    hook = read(".githooks/pre-commit")
    scanner = read("scripts/security/scan_credentials.sh")

    assert "--staged" in hook
    assert "git show \":$file\"" in scanner
    assert 'grep -aE "$PATTERNS"' in scanner
    assert 'git show "$commit:$file"' in scanner
    assert 'git rev-list --reverse "$base..$head"' in scanner
    assert 'git diff-tree --root -m --no-commit-id' in scanner
    assert "CF_API_TOKEN|SUPABASE_ACCESS_TOKEN|RESEND_API_KEY" in scanner
    assert "grep -nIE" not in scanner
    assert "^\\.env" not in scanner


def test_pre_push_scans_each_commit_and_materializes_empty_tree_base():
    hook = read(".githooks/pre-push")

    assert 'git hash-object -t tree -w /dev/null' in hook
    assert 'scan_credentials.sh --diff "$remote_sha" "$local_sha"' in hook


def test_db_sync_is_manual_only():
    text = read(".github/workflows/db-sync-to-pro.yml")
    agents = read("AGENTS.md")

    header = text.split("permissions:", 1)[0]
    assert "workflow_dispatch:" in header
    assert "push:" not in header
    assert "PGRST202" in agents
    assert "aprobación JIT DDL separada" in agents


def test_h2_jit_approval_is_scoped_to_free_ddl():
    request = read(".context/operaciones/ddl_authorizations/DDL-H2-EDITORIAL-LAYER-FREE.md")
    inventory = read(".context/operaciones/h2_editorial_layer_inventory.md")

    assert "Status: CONSUMED_BY_FREE_DDL" in request
    assert "Authorized migrations: `20260825_h2_editorial_layer.sql`, `20260825_h2_editorial_layer_grants_fix.sql`, `20260825_h2_editorial_layer_start_date_view_fix.sql`, `20260825_h2_editorial_layer_allowlist_fix.sql`" in request
    normalized_request = " ".join(request.split())
    assert "No autoriza Pro, backfill, writers, schedules, canaries ni deploys" in normalized_request
    assert "No autoriza DDL, DML, Supabase MCP" in inventory
    assert "Cualquier accion adicional requiere nueva JIT" in normalized_request
    status_line = next(line for line in request.splitlines() if line.startswith("Status:"))
    assert status_line == "Status: CONSUMED_BY_FREE_DDL"


DDL_AUTH_PATH = ".context/operaciones/ddl_authorizations/DDL-H3-EDITORIAL-EXPAND-PRO-20261101.md"

def _run_scope_candidate(tmp_path: Path, candidate_path: str) -> subprocess.CompletedProcess[str]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    repo = tmp_path / "scope-fixture"
    repo.mkdir()

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.stdout.strip()

    git("init", "-q")
    git("config", "user.name", "H3 scope synthetic fixture")
    git("config", "user.email", "h3-scope-fixture@example.invalid")
    guard_path = repo / "scripts/security/protected_path_scope_guard.sh"
    guard_path.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "scripts/security/protected_path_scope_guard.sh", guard_path)
    guard_path.chmod(0o755)
    git("add", "scripts/security/protected_path_scope_guard.sh")
    git("commit", "-qm", "synthetic guard baseline")
    baseline = git("rev-parse", "HEAD")

    changed = repo / candidate_path
    changed.parent.mkdir(parents=True, exist_ok=True)
    changed.write_text("Status: DRAFT_NOT_AUTHORIZED\n", encoding="utf-8")
    git("add", candidate_path)
    git("commit", "-qm", "synthetic scope candidate")

    runner_temp = tmp_path / "runner-temp"
    runner_temp.mkdir()
    env = {
        **os.environ,
        "PROTECTED_BASELINE_SHA": baseline,
        "RUNNER_TEMP": str(runner_temp),
        "GITHUB_BASE_REF": "desarrollo",
        "GITHUB_HEAD_REF": "feature/h3-auth-fixture",
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_REF": "refs/pull/fixture/merge",
    }
    return subprocess.run(
        ["bash", str(guard_path), "--compare-candidate"],
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_h3_ddl_draft_fails_the_actual_workflow_status_check(tmp_path: Path) -> None:
    workflow = read(".github/workflows/db-sync-to-pro.yml")
    apply_section = workflow.split("  apply:", 1)[1].split("  verify:", 1)[0]
    status_check = next(
        line.strip()
        for line in apply_section.splitlines()
        if line.strip() == 'grep -Fx "Status: APPROVED_FOR_PRODUCTION_DDL" "$auth_file"'
    )

    # Exercise both states as fixtures; a later approved real document is legitimate.
    draft_file = tmp_path / "synthetic-draft-fixture.md"
    draft_file.write_text("Status: DRAFT_NOT_AUTHORIZED\n", encoding="utf-8")
    draft_result = subprocess.run(
        [
            "bash",
            "-e",
            "-u",
            "-o",
            "pipefail",
            "-c",
            f"auth_file={shlex.quote(str(draft_file))}\n{status_check}\n",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert draft_result.returncode == 1

    # Disposable synthetic positive fixture only; it has no production authority.
    synthetic_auth_file = tmp_path / "synthetic-approved-fixture.md"
    synthetic_auth_file.write_text(
        "Status: APPROVED_FOR_PRODUCTION_DDL\n", encoding="utf-8"
    )
    synthetic_approved = subprocess.run(
        [
            "bash",
            "-e",
            "-u",
            "-o",
            "pipefail",
            "-c",
            f"auth_file={shlex.quote(str(synthetic_auth_file))}\n{status_check}\n",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert synthetic_approved.returncode == 0


def test_h3_ddl_scope_guard_admits_only_the_exact_route(tmp_path: Path) -> None:
    guard = read("scripts/security/protected_path_scope_guard.sh")
    local_allowlist = guard.split("allowed_h3_local=$(cat <<'H3_LOCAL_PATHS'", 1)[1].split(
        "H3_LOCAL_PATHS", 1
    )[0]
    assert DDL_AUTH_PATH in local_allowlist
    for rejected in (
        ".context/operaciones/ddl_authorizations/DDL-H3-EDITORIAL-EXPAND-PRO-20261101-copy.md",
        ".context/operaciones/ddl_authorizations/DDL-H3-EDITORIAL-EXPAND-PRO-20261102.md",
        ".context/operaciones/ddl_authorizations/../ddl_authorizations/DDL-H3-EDITORIAL-EXPAND-PRO-20261101.md",
    ):
        assert rejected not in local_allowlist
    broad_matchers = re.findall(
        r"(?m)^\s*allowed_h3(?:_extra|_migration_manifest)?='([^']*)'", guard
    )
    assert all(re.search(pattern, DDL_AUTH_PATH) is None for pattern in broad_matchers)

    exact = _run_scope_candidate(tmp_path / "exact", DDL_AUTH_PATH)
    assert exact.returncode == 0
    assert "protected H3 candidate paths are allowlisted" in exact.stdout

    for index, rejected in enumerate(
        (
            ".context/operaciones/ddl_authorizations/DDL-H3-EDITORIAL-EXPAND-PRO-20261101-copy.md",
            ".context/operaciones/ddl_authorizations/DDL-H3-EDITORIAL-EXPAND-PRO-20261102.md",
        )
    ):
        result = _run_scope_candidate(tmp_path / f"rejected-{index}", rejected)
        assert result.returncode == 1
        assert "candidate path omitted" in result.stdout + result.stderr


def test_actual_apply_gate_rejects_authorization_id_traversal() -> None:
    workflow = read(".github/workflows/db-sync-to-pro.yml")
    apply_section = workflow.split("  apply:", 1)[1].split("  verify:", 1)[0]
    id_check = next(
        line.strip()
        for line in apply_section.splitlines()
        if line.strip().startswith("printf '%s' \"$DDL_AUTHORIZATION_ID\"")
    )
    result = subprocess.run(
        ["bash", "-e", "-u", "-o", "pipefail", "-c", id_check],
        env={**os.environ, "DDL_AUTHORIZATION_ID": "DDL-H3-EDITORIAL-EXPAND-PRO-20261101/../../outside"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 1


def test_actual_apply_gate_allows_only_the_auth_file_after_payload(tmp_path: Path) -> None:
    workflow = read(".github/workflows/db-sync-to-pro.yml")
    apply_section = workflow.split("  apply:", 1)[1].split("  verify:", 1)[0]
    changed_line = next(
        line.strip()
        for line in apply_section.splitlines()
        if line.strip().startswith('changed_after_payload="$(git diff --name-only')
    )
    exact_file_check = next(
        line.strip()
        for line in apply_section.splitlines()
        if line.strip() == 'test "$changed_after_payload" = "$auth_file"'
    )

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.stdout.strip()

    git("init", "-q")
    git("config", "user.name", "H3 auth contract fixture")
    git("config", "user.email", "h3-auth-fixture@example.invalid")
    auth_file = tmp_path / DDL_AUTH_PATH
    auth_file.parent.mkdir(parents=True)
    auth_file.write_text("Status: DRAFT_NOT_AUTHORIZED\n", encoding="utf-8")
    context_file = tmp_path / ".context" / "future-doc.md"
    context_file.write_text("payload baseline\n", encoding="utf-8")
    git("add", DDL_AUTH_PATH, ".context/future-doc.md")
    git("commit", "-qm", "synthetic payload")
    payload_sha = git("rev-parse", "HEAD")

    auth_file.write_text("synthetic approved fixture only\n", encoding="utf-8")
    git("add", DDL_AUTH_PATH)
    git("commit", "-qm", "synthetic authorization fixture")
    auth_only_sha = git("rev-parse", "HEAD")

    shell = f"auth_file={shlex.quote(DDL_AUTH_PATH)}\n{changed_line}\n{exact_file_check}\n"
    env = {**os.environ, "PAYLOAD_SHA": payload_sha, "CANDIDATE_SHA": auth_only_sha}
    auth_only = subprocess.run(
        ["bash", "-e", "-u", "-o", "pipefail", "-c", shell],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert auth_only.returncode == 0

    post_payload_extra = tmp_path / ".context" / "post-payload-extra.md"
    post_payload_extra.write_text("extra after payload\n", encoding="utf-8")
    git("add", ".context/post-payload-extra.md")
    git("commit", "-qm", "synthetic additional post-payload file")
    candidate_with_extra_sha = git("rev-parse", "HEAD")
    env["CANDIDATE_SHA"] = candidate_with_extra_sha
    with_extra = subprocess.run(
        ["bash", "-e", "-u", "-o", "pipefail", "-c", shell],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert with_extra.returncode == 1
