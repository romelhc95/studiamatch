import json
from pathlib import Path

import pytest

from scripts.maintenance.f10_10_m3_public_db_acl_diagnostic import (
    DIAGNOSTIC_SQL,
    FIELDS,
    GATE,
    run,
    validate_row,
)


def valid_row() -> dict[str, int | bool]:
    return {
        "transaction_read_only": True,
        "transaction_repeatable_read": True,
        "postgres_major_17": True,
        "target_count": 1,
        "target_connectable": True,
        "target_public_connect_count": 1,
        "target_violation_count": 0,
        "other_connectable_count": 0,
        "other_connectable_violation_count": 0,
        "non_connectable_count": 2,
        "non_connectable_public_connect_acl_count": 2,
        "non_connectable_public_temporary_acl_count": 0,
        "non_connectable_public_create_acl_count": 0,
    }


def test_sql_is_single_counts_only_pg_catalog_query() -> None:
    assert DIAGNOSTIC_SQL.startswith("BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;")
    assert DIAGNOSTIC_SQL.endswith("COMMIT;")
    assert DIAGNOSTIC_SQL.count("BEGIN TRANSACTION") == 1
    assert DIAGNOSTIC_SQL.count("COMMIT;") == 1
    assert "current_setting('transaction_read_only') = 'on'" in DIAGNOSTIC_SQL
    assert "current_setting('transaction_isolation') = 'repeatable read'" in DIAGNOSTIC_SQL
    assert "current_setting('server_version_num')::integer BETWEEN 170000 AND 179999" in DIAGNOSTIC_SQL
    assert "pg_catalog.pg_database" in DIAGNOSTIC_SQL
    assert "TARGET" in DIAGNOSTIC_SQL
    assert "OTHER_CONNECTABLE" in DIAGNOSTIC_SQL
    assert "NON_CONNECTABLE" in DIAGNOSTIC_SQL
    assert "public.courses" not in DIAGNOSTIC_SQL
    assert not any(word in DIAGNOSTIC_SQL.upper() for word in ("INSERT ", "UPDATE ", "DELETE ", "GRANT ", "REVOKE "))


@pytest.mark.parametrize("field", ["transaction_read_only", "transaction_repeatable_read", "postgres_major_17"])
def test_transaction_attestation_is_fail_closed(field: str) -> None:
    row = valid_row()
    row[field] = False
    assert validate_row(row)["policy_conformant"] is False


def test_non_connectable_acl_is_informational() -> None:
    manifest = validate_row(valid_row())
    assert manifest["decision"] == "OFFLINE_ROW_VALIDATED_NOT_REMOTE_EVIDENCE"
    assert manifest["policy_conformant"] is True
    assert manifest["gate"] == GATE
    assert manifest["application_rows_read"] == 0
    assert manifest["ddl"] == manifest["dml"] == 0
    assert set(manifest["summary"]) == set(FIELDS)
    assert "datname" not in json.dumps(manifest)


@pytest.mark.parametrize("field", ["target_violation_count", "other_connectable_violation_count"])
def test_connectable_violation_stops(field: str) -> None:
    row = valid_row()
    row[field] = 1
    assert validate_row(row)["policy_conformant"] is False


def test_validate_mode_never_signals_remote_success_for_policy_violation(tmp_path: Path) -> None:
    row = valid_row()
    row["target_violation_count"] = 1
    source = tmp_path / "row.json"
    source.write_text(json.dumps(row), encoding="utf-8")
    code, manifest = run(["--mode", "validate", "--input", str(source)])
    assert code == 3
    assert manifest["policy_conformant"] is False


def test_missing_or_malformed_field_stops() -> None:
    row = valid_row()
    del row["target_count"]
    with pytest.raises(ValueError, match="STOP_DIAGNOSTIC_SCHEMA"):
        validate_row(row)
    row = valid_row()
    row["target_count"] = True
    with pytest.raises(ValueError, match="STOP_DIAGNOSTIC_SCHEMA"):
        validate_row(row)


def test_validate_mode_never_signals_remote_success_for_conformant_json(tmp_path: Path) -> None:
    source = tmp_path / "row.json"
    source.write_text(json.dumps(valid_row()), encoding="utf-8")
    code, manifest = run([
        "--mode", "validate",
        "--input", str(source),
    ])
    assert code == 3
    assert manifest["decision"] == "OFFLINE_ROW_VALIDATED_NOT_REMOTE_EVIDENCE"


def test_consumed_v1_payload_preserves_historical_digest() -> None:
    payload = json.loads((Path(__file__).resolve().parents[1] / ".context/operaciones/m3_public_db_acl_diagnostic_free_payload_2026_08_12.json").read_text())
    assert payload["diagnostic_query_digest"] == "sha256:c0abd18bc1da371fba3bf28f2bd15f3952856fc20ebdc45eb3ff58572cccfa40"
    assert payload["status"] == "CONSUMED_ONCE_STOP_CANDIDATE_BINDING_PENDING"
    assert payload["diagnostic_query_digest"] != manifest_digest()


def test_v2_envelope_is_superseded_by_v3() -> None:
    assert manifest_digest() == "sha256:82a5848a8ac5958aa781424a436687117f1c39b7dc07f686993b0765bf110a6d"


def manifest_digest() -> str:
    from scripts.maintenance.f10_10_m3_public_db_acl_diagnostic import sql_digest

    return sql_digest()
