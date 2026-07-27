import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "db/manifests/fase09_7_gate_b_readonly.json"
QUERY = ROOT / "scripts/maintenance/fase09_7_gate_b_catalog_v1.sql"
HTTP_RUNNER = ROOT / "scripts/maintenance/fase09_7_gate_b_http.py"
QUERY_SHA256 = "b7fc2e6485865ccbf91750a95a186f8e0468d9e8286a9b630af6780e054a8448"
MANIFEST_SHA256 = "97fb3d95cd7e8d0035c1deedacbd02fe5dd264569f3d2b88a5bddde47b29f8a2"


def _load_manifest() -> dict:
    def reject_duplicates(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate manifest key: {key}")
            value[key] = item
        return value

    return json.loads(
        MANIFEST.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
    )


def test_historical_catalog_query_remains_byte_exact_and_read_only():
    canonical = QUERY.read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(canonical).hexdigest() == QUERY_SHA256

    sql = canonical.decode("ascii")
    assert sql.startswith("WITH RECURSIVE\n")
    assert sql.endswith(";\n")
    assert sql.count(";") == 1
    assert "--" not in sql
    assert "/*" not in sql

    without_literals = re.sub(r"'(?:''|[^'])*'", "''", sql)
    assert not re.search(
        r"(?i)\b(?:ALTER|CALL|COPY|CREATE|DELETE|DO|DROP|GRANT|INSERT|LOCK|"
        r"MERGE|REASSIGN|RESET|REVOKE|SET|TRUNCATE|UPDATE|VACUUM)\b",
        without_literals,
    )
    assert not re.search(
        r"(?i)\b(?:dblink|lo_import|lo_export|pg_read_file)\b",
        sql,
    )


def test_consumed_gate_b_is_mechanically_non_authorizable():
    manifest = _load_manifest()
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == MANIFEST_SHA256

    assert manifest["schema_version"] == 2
    assert manifest["status"] == "CONSUMED_FAIL_NON_AUTHORIZABLE"
    assert manifest["capabilities"] == []
    assert manifest["positive_tool_allowlist"] == []
    assert manifest["positive_http_allowlist"] == []
    assert manifest["historical_execution"]["result"] == (
        "FREE_GATE_B_FAIL_STOPPED_READ_ONLY"
    )
    assert manifest["historical_execution"]["http_calls"] == 0
    assert manifest["separate_human_approvals"] == {
        "backup_restore": "required_not_granted",
        "writers_pause": "required_not_granted",
        "separate_artifacts_required": True,
    }
    assert "gate_b_reuse" in manifest["explicitly_forbidden"]
    assert "remote_transport" in manifest["explicitly_forbidden"]


def test_consumed_http_transport_primitive_is_absent():
    assert not HTTP_RUNNER.exists()
    workflow = (ROOT / ".github/workflows/f9-7-contract.yml").read_text(
        encoding="utf-8"
    )
    assert "fase09_7_gate_b_http.py" not in workflow


def test_public_gate_b_manifest_has_no_people_or_request_identifiers():
    serialized = json.dumps(_load_manifest(), sort_keys=True).lower()
    for forbidden in (
        "operation_owner\"",
        "reviewer\"",
        "approval_request_id",
        "project_ref",
        "supabase_url",
        "publishable_key",
        "secret_key",
    ):
        assert forbidden not in serialized
