from pathlib import Path


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

    assert "Esta nota es la autoridad exclusiva del estado vivo" in state
    assert "H2_DEVELOPMENT_COMPAT_REMOTE_VERIFIED_PENDING_REVIEW" in state
    assert "REMOTE_VERIFIED_PENDING_REVIEW" in state
    assert "REDEFINICION.md` eliminado definitivamente" in state
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


def test_pre_commit_scans_staged_blobs_not_working_tree():
    hook = read(".githooks/pre-commit")
    scanner = read("scripts/security/scan_credentials.sh")

    assert "--staged" in hook
    assert "git show \":$file\"" in scanner
    assert "^\\.env" not in scanner


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
