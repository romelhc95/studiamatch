from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.maintenance import db_migrate
from scripts.maintenance.migration_manifest import (
    F9_5_MANIFEST_SHA256,
    ManifestError,
    canonical_sql_sha256,
    load_manifest,
    validate_promotable_sql,
)


ROOT = Path(__file__).resolve().parents[1]
F8_MANIFEST = ROOT / "db/manifests/fase08_candidate.json"
F9_5_MANIFEST = ROOT / "db/manifests/fase09_5_rls_candidate.json"
F9_5_MIGRATION = (
    ROOT / "db/migrations/20260726_fase09_5_rls_canary_reconciliation.sql"
)
F8_RAW_LF_SHA256 = (
    "6946570738aba234bb41273fc0839a50ece0617d464906a84736d1b2aafd4fee"
)
F8_MIGRATION_SHA256 = {
    "db/migrations/20260724_fase06_g1b_reconciliation.sql": (
        "d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df"
    ),
    "db/migrations/20260724_fase06_hito1_editorial_contract.sql": (
        "b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a"
    ),
    "db/migrations/20260725_fase07_g1b_closure.sql": (
        "9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120"
    ),
    "db/migrations/20260725_fase08_hito1_functional_closure.sql": (
        "7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527"
    ),
}
F9_5_ENTRY = {
    "id": "F9.5-RLS-CANARY-RECONCILIATION",
    "component": "rls_canary_reconciliation",
    "path": "db/migrations/20260726_fase09_5_rls_canary_reconciliation.sql",
    "sha256": "4959b3f1ad60e2fe3a6e9a23161dd0467cfc549e10c1262ba8a0bb2aaf4c9a01",
    "provenance": "new_forward_only",
    "targets": ["free", "pro"],
}


def _read_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest(tmp_path: Path, manifest: dict, name: str) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _marker(path: Path) -> str:
    return f"sha256:{canonical_sql_sha256(path)}"


class _VerifierDatabase:
    def __init__(self, result: bool = True):
        self.result = result
        self.calls: list[str] = []

    def rpc_raise(self, name: str, _params: dict) -> bool:
        self.calls.append(name)
        return self.result


def test_f8_artifacts_are_fixed_and_f9_5_is_an_exact_overlay():
    raw_f8 = F8_MANIFEST.read_bytes().replace(b"\r\n", b"\n")
    assert b"\r" not in raw_f8
    assert hashlib.sha256(raw_f8).hexdigest() == F8_RAW_LF_SHA256

    f8 = _read_manifest(F8_MANIFEST)
    overlay = _read_manifest(F9_5_MANIFEST)
    canonical_overlay = json.dumps(
        overlay, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    assert hashlib.sha256(canonical_overlay).hexdigest() == F9_5_MANIFEST_SHA256
    assert overlay["entries"][:4] == f8["entries"]
    assert overlay["entries"][4] == F9_5_ENTRY
    assert len(overlay["entries"]) == 5

    assert {entry["path"]: entry["sha256"] for entry in f8["entries"]} == (
        F8_MIGRATION_SHA256
    )
    for relative, expected_hash in F8_MIGRATION_SHA256.items():
        assert canonical_sql_sha256(ROOT / relative) == expected_hash
    assert canonical_sql_sha256(F9_5_MIGRATION) == F9_5_ENTRY["sha256"]


def test_f9_5_manifest_loads_five_paths_for_both_blocked_targets():
    free_paths = load_manifest(F9_5_MANIFEST, "free")
    pro_paths = load_manifest(F9_5_MANIFEST, "pro")

    assert len(free_paths) == 5
    assert free_paths == pro_paths
    assert free_paths[-1] == F9_5_MIGRATION
    manifest = _read_manifest(F9_5_MANIFEST)
    assert manifest["status"] == "reconciled_not_certified"
    assert manifest["blocked_targets"] == ["free", "pro"]
    with pytest.raises(ManifestError, match="required ready_for_free"):
        load_manifest(F9_5_MANIFEST, "free", required_status="ready_for_free")
    with pytest.raises(ManifestError, match="required free_certified"):
        load_manifest(F9_5_MANIFEST, "pro", required_status="free_certified")


def test_f9_5_manifest_rejects_order_component_prefix_checksum_and_exclusions(
    tmp_path: Path,
):
    cases: list[tuple[str, str, object]] = [
        (
            "order",
            "exact contract",
            lambda value: value["entries"].__setitem__(
                slice(3, 5), [value["entries"][4], value["entries"][3]]
            ),
        ),
        (
            "component",
            "exact contract",
            lambda value: value["entries"][4].__setitem__("component", "hito1"),
        ),
        (
            "prefix",
            "exact contract",
            lambda value: value["entries"][4].__setitem__(
                "path",
                "db/migrations/20260725_fase08_hito1_functional_closure.sql",
            ),
        ),
        (
            "checksum",
            "exact contract",
            lambda value: value["entries"][4].__setitem__("sha256", "0" * 64),
        ),
        (
            "exclusions",
            "exact contract",
            lambda value: value["excluded"].__setitem__(
                "canary_operational_data", "promotable"
            ),
        ),
    ]

    for name, message, mutate in cases:
        manifest = _read_manifest(F9_5_MANIFEST)
        mutate(manifest)
        invalid = _write_manifest(tmp_path, manifest, f"{name}.json")
        with pytest.raises(ManifestError, match=message):
            load_manifest(invalid, "free", root=ROOT)

    manifest = _read_manifest(F9_5_MANIFEST)
    manifest["blocked_targets"] = ["pro"]
    invalid = _write_manifest(tmp_path, manifest, "unblocked.json")
    with pytest.raises(ManifestError, match="exact contract"):
        load_manifest(invalid, "free", root=ROOT)

    for status in ("ready_for_free", "free_certified"):
        manifest = _read_manifest(F9_5_MANIFEST)
        manifest["status"] = status
        manifest["blocked_targets"] = ["pro"] if status == "ready_for_free" else []
        invalid = _write_manifest(tmp_path, manifest, f"{status}.json")
        with pytest.raises(ManifestError, match="exact contract"):
            load_manifest(invalid, "free", root=ROOT)

    manifest = _read_manifest(F9_5_MANIFEST)
    manifest["package_id"] = "SUBSTITUTED-PACKAGE"
    invalid = _write_manifest(tmp_path, manifest, "substituted-package.json")
    with pytest.raises(ManifestError, match="exact contract"):
        load_manifest(invalid, "free", root=ROOT)

    manifest = _read_manifest(F9_5_MANIFEST)
    manifest["unexpected"] = "field"
    invalid = _write_manifest(tmp_path, manifest, "unknown-field.json")
    with pytest.raises(ManifestError, match="exact contract"):
        load_manifest(invalid, "free", root=ROOT)


def test_f9_5_manifest_rejects_duplicate_json_keys(tmp_path: Path):
    duplicate = tmp_path / "duplicate.json"
    text = F9_5_MANIFEST.read_text(encoding="utf-8").replace(
        '"schema_version": 1,', '"schema_version": 1, "schema_version": 1,', 1
    )
    duplicate.write_text(text, encoding="utf-8")

    with pytest.raises(ManifestError, match="duplicate migration manifest key"):
        load_manifest(duplicate, "free", root=ROOT)


def test_exact_f8_prefix_defers_stale_postconditions_only_to_successor():
    paths = load_manifest(F9_5_MANIFEST, "free")
    applied = {path.stem: _marker(path) for path in paths[:4]}
    database = _VerifierDatabase(result=False)

    assert db_migrate.validate_manifest_ledger_state(
        database, paths, applied
    ) == [paths[4]]
    assert database.calls == []

    package = db_migrate.build_manifest_package_sql(
        [paths[4]], expected_prefix=applied, version=20260726090500
    )
    assert package.count("-- manifest-entry") == 1
    assert package.count("INSERT INTO public.supabase_migrations") == 1
    assert "public.verify_fase09_5_rls_canary_reconciliation()" in package
    for name, marker in applied.items():
        assert name in package
        assert marker in package


def test_f9_5_ledger_rejects_checksum_gap_and_nonexact_deferred_suffix(
    tmp_path: Path,
):
    paths = load_manifest(F9_5_MANIFEST, "free")

    checksum_drift = {path.stem: _marker(path) for path in paths[:4]}
    checksum_drift[paths[1].stem] = "sha256:" + "0" * 64
    with pytest.raises(RuntimeError, match="Ledger/checksum mismatch"):
        db_migrate.validate_manifest_ledger_state(
            _VerifierDatabase(), paths, checksum_drift
        )

    gap = {
        paths[0].stem: _marker(paths[0]),
        paths[2].stem: _marker(paths[2]),
    }
    with pytest.raises(RuntimeError, match="prefijo continuo"):
        db_migrate.validate_manifest_ledger_state(_VerifierDatabase(), paths, gap)

    projected_prefix = {
        path.stem: _marker(path) for path in paths[:3]
    }
    projected_prefix["20200101_unrelated_history"] = "sha256:" + "1" * 64
    assert db_migrate.validate_manifest_ledger_state(
        _VerifierDatabase(), paths, projected_prefix
    ) == paths[3:]

    for partial_size in (1, 2):
        partial = {
            path.stem: _marker(path) for path in paths[:partial_size]
        }
        with pytest.raises(RuntimeError, match="limites completos"):
            db_migrate.validate_manifest_ledger_state(
                _VerifierDatabase(), paths, partial
            )

    other_suffix = tmp_path / "20260726_fase09_5_other.sql"
    other_suffix.write_text("SET search_path = '';", encoding="utf-8")
    stale_database = _VerifierDatabase(result=False)
    with pytest.raises(RuntimeError, match="Postcondicion fallida"):
        db_migrate.validate_manifest_ledger_state(
            stale_database, paths[:4] + [other_suffix], {
                path.stem: _marker(path) for path in paths[:4]
            }
        )
    assert stale_database.calls == ["verify_fase06_g1b_reconciliation"]


def test_all_five_applied_reverify_every_postcondition_and_plan_zero_pending():
    paths = load_manifest(F9_5_MANIFEST, "free")
    database = _VerifierDatabase()

    assert db_migrate.validate_manifest_ledger_state(
        database, paths, {path.stem: _marker(path) for path in paths}
    ) == []
    assert database.calls == [
        db_migrate.PACKAGE_POSTCONDITIONS[path.stem]
        .removeprefix("public.")
        .removesuffix("()")
        for path in paths
    ]


def test_complete_f9_5_package_has_five_atomic_entries_and_final_checks():
    paths = load_manifest(F9_5_MANIFEST, "free")
    package = db_migrate.build_manifest_package_sql(
        paths, version=20260726090500
    )

    assert package.count("LOCK TABLE public.supabase_migrations") == 1
    assert package.count("-- manifest-entry") == 5
    assert package.count("INSERT INTO public.supabase_migrations") == 5
    assert package.count("DO $manifest_verify$") == 5
    assert "ON CONFLICT (name) DO NOTHING" not in package
    final_checks = package.index("-- final-package-postconditions")
    registrations = package.index("-- manifest-ledger-registration")
    assert final_checks < registrations
    final_section = package[final_checks:registrations]
    for path in paths:
        verifier = db_migrate.PACKAGE_POSTCONDITIONS[path.stem]
        assert verifier in final_section
        assert package.count(f"'{path.stem}', 'sha256:") == 1


def test_successor_and_historical_fixture_are_forward_only_and_synthetic():
    sql = F9_5_MIGRATION.read_text(encoding="utf-8")
    validate_promotable_sql(sql, label=F9_5_MIGRATION.name)
    assert "SET search_path = '';" in sql
    assert "SECURITY INVOKER" in sql
    assert "verify_fase08_hito1_contract" in sql
    assert "verify_fase09_5_rls_canary_reconciliation" in sql
    assert sql.count("AS RESTRICTIVE") == 3
    assert "profiles_select_authenticated" in sql
    assert "auth.role()" not in sql
    assert "GRANT INSERT (\n    first_name, last_name, email, whatsapp" in sql
    assert "GRANT INSERT ON TABLE public.leads" not in sql
    for denied_column in ("id", "status", "created_at", "lead_source_type"):
        assert denied_column not in sql.split("GRANT INSERT (", 1)[1].split(
            ") ON TABLE public.leads", 1
        )[0].split()

    fixture = (
        ROOT / "tests/sql/fase09_5_historical_rls_fixture.sql"
    ).read_text(encoding="utf-8")
    assert "CREATE TABLE public.institutions" in fixture
    assert "ADD COLUMN notes text" in fixture
    assert "TO anon\nUSING (production_enabled = true)" in fixture
    assert "profiles_select_authenticated" in fixture
    assert fixture.count("AS RESTRICTIVE") == 3
    assert "INSERT INTO" not in fixture
    assert "supabase.co" not in fixture
    assert "ADD COLUMN is_late_enrollment_request" in fixture

    baseline_test = (
        ROOT / "tests/sql/fase09_5_historical_baseline_test.sql"
    ).read_text(encoding="utf-8")
    assert "NOT EXISTS (SELECT 1 FROM public.supabase_migrations)" in baseline_test
    assert "representative F8 function, column, constraint and index effects" in baseline_test
    assert "historical unledgered RLS drift" in baseline_test

    runner = (ROOT / "tests/sql/run_fase09_5_postgres.sh").read_text(
        encoding="utf-8"
    )
    assert "validate_manifest_ledger_state(Adapter(), paths, applied)" in runner
    assert 'plan_manifest "$((5 - prefix_size))" "$package_wrapper"' in runner
    assert 'plan_manifest 5 "$package_wrapper"' in runner
    assert runner.count("plan_manifest 0") == 2
    assert "fase09_5_historical_baseline_test.sql" in runner


def test_security_audit_requires_secretless_egress_restricted_f9_5_job():
    workflow = (ROOT / ".github/workflows/security-audit.yml").read_text(
        encoding="utf-8"
    )
    start = workflow.index("  fase09-5-rls:")
    end = workflow.index("\n  fase10-promotion-contract:", start)
    job = workflow[start:end]

    assert "name: F9.5 RLS Forward-only PostgreSQL 17 Contract" in job
    assert "postgres:17-alpine@sha256:" in job
    assert "--network none" in job
    assert "Start networkless F9.5 PostgreSQL 17" in job
    assert 'chmod 711 "$state_dir"' in job
    assert "{{.HostConfig.NetworkMode}}" in job
    assert "postgres-socket" in job
    assert "tests/test_fase09_5_rls.py" in job
    assert "bash tests/sql/run_fase09_5_postgres.sh" in job
    assert "FASE095_EGRESS" in job
    assert "-o lo -j RETURN" in job
    assert "-j REJECT" in job
    assert "Prove F9.5 external egress is blocked" in job
    assert 'socket.create_connection(("1.1.1.1", 443), timeout=2)' in job
    assert 'awk \'$3 == "REJECT" && $9 == "1.1.1.1"' in job
    assert 'test "$reject_after" -gt "$reject_before"' in job
    assert "environment:" not in job
    assert "${{ secrets." not in job
    assert "continue-on-error" not in job
    assert "setpriv --reuid=65534 --regid=65534 --clear-groups" in job.replace(
        "\\\n", ""
    )
    assert "--bounding-set=-all --inh-caps=-all --ambient-caps=-all" in job
    assert "--no-new-privs" in job
    assert "test ! -r /var/run/docker.sock" in job
    assert "test ! -w /var/run/docker.sock" in job
    assert "timeout --signal=TERM --kill-after=10s 300s" in job
    assert "|| true" not in job

    assert "fase09-5-rls" in workflow.split("needs:", 1)[1]
    assert "F95: ${{ needs.fase09-5-rls.result }}" in workflow
    assert "**fase09-5-rls**" in workflow
