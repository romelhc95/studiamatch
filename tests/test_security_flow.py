from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_redefinition_declares_simple_flow_and_boundaries():
    text = read("REDEFINICION.md")
    assert "origin/main@9b486146962bd2a092acfd649fdcf716e922de89" in text
    assert "feat/* o docs/* desde desarrollo" in text
    assert "DB Sync to Production` queda manual-only" in text
    assert "Work Packages, grants persistentes, digests documentales" in text


def test_agents_no_longer_uses_wp_digest_as_authority():
    text = read("AGENTS.md")
    assert "Los Work Packages, digests documentales, grants persistentes" in text
    assert "Apruebo WP-<ID>" not in text
    assert "grant persistente WP/digest" not in text


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
    header = text.split("permissions:", 1)[0]
    assert "workflow_dispatch:" in header
    assert "push:" not in header
