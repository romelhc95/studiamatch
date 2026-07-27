import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

from scripts.maintenance import fase09_7_gate_b_http as gate_b_http


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "db/manifests/fase09_7_gate_b_readonly.json"
QUERY = ROOT / "scripts/maintenance/fase09_7_gate_b_catalog_v1.sql"
HTTP_RUNNER = ROOT / "scripts/maintenance/fase09_7_gate_b_http.py"
QUERY_SHA256 = "b7fc2e6485865ccbf91750a95a186f8e0468d9e8286a9b630af6780e054a8448"
HTTP_SHA256 = "eea58a8ee28de70bba330fe125416060624b564ede1281a7bc08899d18b0fc41"
MANIFEST_SHA256 = "67b055217958d93bdeb69047412b376929f3b5e211e7f159fa610489011b2c3d"
EXPECTED_PATHS = (
    "/rest/v1/courses?select=id&limit=0",
    "/rest/v1/leads?select=id&limit=0",
    "/rest/v1/email_log?select=id&limit=0",
)


def _load_manifest() -> dict:
    def reject_duplicates(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate manifest key: {key}")
            value[key] = item
        return value

    return json.loads(MANIFEST.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)


def test_catalog_query_is_exact_single_read_only_statement():
    raw = QUERY.read_bytes()
    canonical = raw.replace(b"\r\n", b"\n")
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
    assert not re.search(r"(?i)\b(?:dblink|lo_import|lo_export|pg_read_file)\b", sql)
    function_calls = set(re.findall(r"pg_catalog\.([a-z_]+)\s*\(", sql))
    assert function_calls <= {
        "acldefault",
        "aclexplode",
        "coalesce",
        "count",
        "has_column_privilege",
        "has_function_privilege",
        "has_schema_privilege",
        "has_table_privilege",
        "max",
        "pg_has_role",
        "to_regclass",
        "unnest",
    }


def test_manifest_freezes_candidate_tools_http_and_evidence_shape():
    manifest = _load_manifest()
    canonical = json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == MANIFEST_SHA256
    assert manifest["schema_version"] == 1
    assert manifest["phase"] == "F9.7"
    assert manifest["gate"] == "GATE_B_PRE_DDL_READ_ONLY"
    assert manifest["target"] == "free"
    assert manifest["status"] == "frozen_for_read_only_execution"

    candidate = manifest["candidate"]
    assert candidate == {
        "package_id": "F9.7-PUBLIC-ACCESS-CLOSURE-20260727",
        "base_commit": "f7b808f38d9a554932a8ae3547891a1a052d26e1",
        "reviewed_head_commit": "71868c62db3cf6a8303cdc117e834c11db282011",
        "reviewed_tree": "e08acc3f136ea9fd6a0d3c01def20d2a42542d13",
        "merge_commit": "3e18ec7ad2d2304179a0ce979b854db73e33d883",
        "manifest_canonical_sha256": "5d32ed2c977c59c38d56948e687ba2b05ecd9ad8b2d3f5752cce3a9836889de3",
        "closure_sha256": "040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b",
    }

    tools = manifest["positive_tool_allowlist"]
    assert [item["tool"] for item in tools] == ["supabase-free.execute_sql"]
    assert tools[0]["max_calls"] == 1
    assert tools[0]["canonical_sha256"] == QUERY_SHA256
    assert tools[0]["cardinality"] == 1

    http = manifest["positive_http_allowlist"]
    assert http["runner_canonical_sha256"] == HTTP_SHA256
    assert http["method"] == "GET"
    assert tuple(http["paths"]) == EXPECTED_PATHS
    assert http["identities"] == ["publishable", "service"]
    assert http["max_calls_per_identity_and_path"] == 1
    assert http["forbid_response_body"] is True
    assert http["expected_results"] == {
        "publishable": {
            "courses": ["success", True],
            "leads": ["denied", False],
            "email_log": ["denied", False],
        },
        "service": {
            "courses": ["success", True],
            "leads": ["success", True],
            "email_log": ["success", True],
        },
    }
    assert manifest["separate_human_approvals"]["separate_artifacts_required"] is True


def test_manifest_closes_scope_and_stops_before_mutation():
    manifest = _load_manifest()
    assert set(manifest["explicitly_forbidden"]) == {
        "supabase-pro",
        "apply_migration",
        "database_mutation",
        "schema_change",
        "writer_pause_or_resume",
        "h00",
        "backfill",
        "f9_8",
        "certificacion",
        "main",
        "production",
    }
    assert "any_ddl_dml_rpc_lock_copy_call_set_or_writer_control" in manifest["stop_conditions"]
    assert "raw_row_pii_uuid_url_key_policy_expression_or_query_text_in_evidence" in manifest["stop_conditions"]
    assert "approval_request_ids" in manifest["allowed_evidence"]


def test_gate_b_contract_is_enforced_by_independent_ci():
    workflow = (ROOT / ".github/workflows/f9-7-contract.yml").read_text(
        encoding="utf-8"
    )
    postgres_runner = (ROOT / "tests/sql/run_fase09_7_postgres.sh").read_text(
        encoding="utf-8"
    )
    for path in (
        "db/manifests/fase09_7_gate_b_readonly.json",
        "scripts/maintenance/fase09_7_gate_b_catalog_v1.sql",
        "scripts/maintenance/fase09_7_gate_b_http.py",
        "tests/test_fase09_7_gate_b_readonly.py",
        "tests/test_supabase_credentials_contract.py",
    ):
        assert path in workflow
    assert "tests/test_fase09_7_gate_b_readonly.py" in workflow
    assert "tests/test_supabase_credentials_contract.py" in workflow
    assert 'GATE_B_QUERY="$ROOT/scripts/maintenance/fase09_7_gate_b_catalog_v1.sql"' in postgres_runner
    assert 'gate_b_output="$(' in postgres_runner
    assert 'mapfile -t gate_b_rows <<< "$gate_b_output"' in postgres_runner
    assert "[[ ${#gate_b_rows[@]} -eq 1 ]]" in postgres_runner
    assert '[[ "${gate_b_rows[0]##*|}" == "t" ]]' in postgres_runner

    producer_failure = subprocess.run(
        [
            "bash",
            "-c",
            'set -e; output="$(printf partial; exit 42)"; printf "%s" "$output"',
        ],
        capture_output=True,
        check=False,
    )
    assert producer_failure.returncode == 42
    assert producer_failure.stdout == b""


class FakeResponse:
    def __init__(self, status_code, headers=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.closed = False

    def close(self):
        self.closed = True


def _bind_free_env(monkeypatch):
    monkeypatch.setenv(
        gate_b_http.ORIGIN_ENV,
        "https://abcdefghijklmnopqrst.supabase.co",
    )
    monkeypatch.setenv(gate_b_http.PUBLISHABLE_ENV, "sb_publishable_example")
    monkeypatch.setenv(gate_b_http.SERVICE_ENV, "sb_secret_example")
    origin, publishable, _service = gate_b_http._load_private_binding()
    fingerprint = gate_b_http.derive_target_fingerprint(origin, publishable, _service)
    monkeypatch.setenv(gate_b_http.EXPECTED_FINGERPRINT_ENV, fingerprint)
    for name in gate_b_http.FORBIDDEN_ENV:
        monkeypatch.delenv(name, raising=False)
    for name in gate_b_http.AMBIGUOUS_ENV:
        monkeypatch.delenv(name, raising=False)


def test_http_runner_is_exact_get_only_and_discards_bodies(monkeypatch):
    _bind_free_env(monkeypatch)
    responses = [
        FakeResponse(206, {"Content-Range": "*/0"}),
        FakeResponse(403),
        FakeResponse(401),
        FakeResponse(206, {"Content-Range": "*/0"}),
        FakeResponse(206, {"Content-Range": "*/0"}),
        FakeResponse(200, {"Content-Range": "*/0"}),
    ]
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return responses[len(calls) - 1]

    result = gate_b_http.execute_attestation(fake_get)
    assert result["gate_b_http_pass"] is True
    assert len(result["checks"]) == 6
    assert all(response.closed for response in responses)
    assert [url.split(".co", 1)[1] for url, _kwargs in calls] == [
        *EXPECTED_PATHS, *EXPECTED_PATHS
    ]
    assert all("Authorization" not in kwargs["headers"] for _url, kwargs in calls)
    assert all(kwargs["allow_redirects"] is False for _url, kwargs in calls)
    assert all(kwargs["stream"] is True for _url, kwargs in calls)
    runner_source = HTTP_RUNNER.read_text(encoding="utf-8")
    assert "session.trust_env = False" in runner_source
    assert '"Authorization"' not in runner_source


def test_http_runner_fails_closed_on_identity_target_or_status_drift(monkeypatch):
    _bind_free_env(monkeypatch)
    monkeypatch.setenv(gate_b_http.EXPECTED_FINGERPRINT_ENV, "0" * 64)
    with pytest.raises(gate_b_http.GateBError, match="fingerprint mismatch"):
        gate_b_http.execute_attestation(lambda *_args, **_kwargs: None)

    _bind_free_env(monkeypatch)
    monkeypatch.setenv(gate_b_http.SERVICE_ENV, "sb_secret_different")
    with pytest.raises(gate_b_http.GateBError, match="fingerprint mismatch"):
        gate_b_http.execute_attestation(lambda *_args, **_kwargs: None)

    _bind_free_env(monkeypatch)
    monkeypatch.setenv("PRO_SUPABASE_URL", "https://pro.example")
    with pytest.raises(gate_b_http.GateBError, match="Pro binding"):
        gate_b_http.execute_attestation(lambda *_args, **_kwargs: None)

    monkeypatch.delenv("PRO_SUPABASE_URL")
    _bind_free_env(monkeypatch)
    responses = [
        FakeResponse(200), FakeResponse(403), FakeResponse(403),
        FakeResponse(206), FakeResponse(206), FakeResponse(206),
    ]
    result = gate_b_http.execute_attestation(
        lambda *_args, **_kwargs: responses.pop(0)
    )
    assert result["gate_b_http_pass"] is False
