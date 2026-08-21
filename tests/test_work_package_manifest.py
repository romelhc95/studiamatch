import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / ".context" / "work_packages"


def test_sprint1_work_packages_are_proposed():
    manifests = sorted(MANIFEST_DIR.glob("WP-H*-001.json"))
    assert [path.stem for path in manifests] == ["WP-H2-001", "WP-H3-001", "WP-H4-001", "WP-H5-001"]
    for path in manifests:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "PROPOSED"
        assert data["id"] == path.stem
        assert data["allowed_paths"]
        assert data["denied_without_jit"]
        assert data["exit_criteria"]
        assert "approval_digest" not in data
        assert "production" in data["denied_without_jit"]
        assert "writers" in data["denied_without_jit"]
        assert "**" not in data["allowed_paths"]
        assert "*" not in data["allowed_paths"]


def test_h2_requires_r3_for_database_changes():
    data = json.loads((MANIFEST_DIR / "WP-H2-001.json").read_text(encoding="utf-8"))
    assert data["risk_level"] == "R3_REQUIRED_FOR_DDL_DML"
    assert "production" in data["denied_without_jit"]
