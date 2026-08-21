import json
from pathlib import Path

import hashlib


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / ".context" / "work_packages"


def independent_digest(data):
    excluded = {"candidate_digest", "status", "approval_digest", "approved_by", "approved_at", "activated_at"}
    payload = {key: value for key, value in data.items() if key not in excluded}
    canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_sprint1_work_packages_are_proposed():
    manifests = sorted(MANIFEST_DIR.glob("WP-H*-001.json"))
    assert [path.stem for path in manifests] == ["WP-H2-001", "WP-H3-001", "WP-H4-001", "WP-H5-001"]
    for path in manifests:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "PROPOSED"
        assert data["id"] == path.stem
        assert data["allowed_paths"]
        assert data["denied_without_jit"]
        assert data["dependencies"]
        assert data["r3_operations"]
        assert data["exit_criteria"]
        assert data["candidate_digest"] == independent_digest(data)
        assert data["approval_digest_source"]
        assert "approval_digest" not in data
        assert "production" in data["denied_without_jit"]
        assert "writers" in data["denied_without_jit"]
        assert "schedules" in data["denied_without_jit"]
        assert "lead_capture" in data["denied_without_jit"]
        assert "egress" in data["denied_without_jit"]
        assert "**" not in data["allowed_paths"]
        assert "*" not in data["allowed_paths"]


def test_h2_requires_r3_for_database_changes():
    data = json.loads((MANIFEST_DIR / "WP-H2-001.json").read_text(encoding="utf-8"))
    assert data["risk_level"] == "R3_REQUIRED_FOR_DDL_DML"
    assert "production" in data["denied_without_jit"]
    assert "supabase-pro" in data["denied_without_jit"]
    assert "ddl" in data["r3_operations"]
    assert "dml" in data["r3_operations"]


def test_context_graph_has_reusable_governance_nodes():
    context = ROOT / ".context"
    assert (context / "operaciones" / "context_graph_semantico.md").exists()
    assert (context / "seguimiento" / "plantilla_tracker_reutilizable.md").exists()
    assert (context / "seguimiento" / "retrospectiva_hito_001.md").exists()
    adr = (context / "decisiones" / "ADR-0028_context_graph_semantico_y_autorizacion_r0_r3.md").read_text(encoding="utf-8")
    for level in ("`R0`", "`R1`", "`R2`", "`R3`", "`R3+`"):
        assert level in adr
