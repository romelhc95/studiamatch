from pathlib import Path
import re


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


def test_protected_workflow_integrity_is_prepared_but_not_aggregated_in_stage_one():
    integrity = read(".github/workflows/protected-workflow-integrity.yml")
    audit = read(".github/workflows/security-audit.yml")

    assert "pull_request_target:" in integrity
    assert "pull_request_review:" in integrity
    assert "pull-requests: read" in integrity
    assert "gh api --paginate" in integrity
    assert "ref: ${{ github.event.pull_request.base.sha }}" in integrity
    assert "persist-credentials: false" in integrity
    assert "scripts/security/protected_workflow_review.py" in integrity
    assert integrity.count("uses: actions/checkout@") == 1
    helper = read("scripts/security/protected_workflow_review.py")
    assert '".github/workflows/"' in helper
    assert '".github/actions/"' in helper
    assert '".githooks/"' in helper
    assert '"scripts/security/"' in helper
    assert 'review.get("commit_id") == head_sha' in helper
    assert 'review.get("state") == "APPROVED"' in helper
    assert "reviewer_key == author_key" in helper
    assert "Protected Workflow Integrity" in integrity
    assert "protected-workflow-integrity" in audit
    active_triggers = audit.split("permissions:", 1)[0]
    assert "pull_request_review:" not in active_triggers
    assert "trusted-workflow-integrity:" not in audit
    assert "needs: [trusted-workflow-integrity," not in audit
    assert "needs.trusted-workflow-integrity.result" not in audit
    assert "actions/workflows/protected-workflow-integrity.yml/runs" not in audit
    assert "if: github.event_name == 'pull_request' && github.event.pull_request.base.ref == 'main'" in audit
    assert "pull_request_review" not in audit


def test_admin_invitation_bff_sanitizes_internal_edge_business_codes():
    bff = read("web/functions/_lib/admin-bff.ts")

    assert "const SAFE_INVITE_ERROR_CODES = new Set([" in bff
    assert "SAFE_INVITE_ERROR_CODES.has(requestedEdgeCode)" in bff
    assert "? requestedEdgeCode" in bff
    assert ": 'invitation_failed'" in bff
    assert "edgeResponse.status" not in bff
    assert "code: mfaRequired ? 'mfa_required' : 'rpc_failed'" in bff
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
