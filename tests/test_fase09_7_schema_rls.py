from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.maintenance import db_migrate
from scripts.maintenance import fase09_7_candidate as candidate_module
from scripts.maintenance.fase09_7_candidate import (
    ManifestError,
    ManifestPlan,
    canonical_json_sha256,
    canonical_sql_sha256,
    classify_manifest_ledger,
    load_manifest,
    validate_promotable_sql,
)
from scripts.maintenance.fase09_7_notify_truth import (
    NOTIFY_VARIANTS_BY_NAME,
    PROJECT_REF_GRAMMAR,
    PROJECT_REF_LENGTH,
)


ROOT = Path(__file__).resolve().parents[1]
F8_MANIFEST = ROOT / "db/manifests/fase08_candidate.json"
F9_7_HISTORICAL_MANIFEST = ROOT / "db/manifests/fase09_7_free_schema_rls.json"
F9_7_V2_MANIFEST = ROOT / "db/manifests/fase09_7_free_schema_rls_v2.json"
F9_7_MANIFEST = ROOT / "db/manifests/fase09_7_free_schema_rls_v3.json"
F9_7_MIGRATION = (
    ROOT / "db/migrations/20260727_fase09_7_public_access_closure.sql"
)
F9_7_RETIREMENT_V2 = (
    ROOT / "db/migrations/20260727_fase09_7_notify_new_lead_retirement.sql"
)
F9_7_RETIREMENT = (
    ROOT / "db/migrations/20260728_fase09_7_notify_new_lead_retirement_v3.sql"
)
F9_7_MIGRATION_SHA256 = (
    "040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b"
)
LF_MIGRATION_SHA256 = {
    "20260724_fase06_g1b_reconciliation.sql": "d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df",
    "20260724_fase06_hito1_editorial_contract.sql": "b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a",
    "20260725_fase07_g1b_closure.sql": "9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120",
    "20260725_fase08_hito1_functional_closure.sql": "7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527",
    "20260727_fase09_7_public_access_closure.sql": "040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b",
}
F9_7_DESCRIPTOR_SHA256 = (
    "33c3b262dd1754d2fd8e7c8684e50601043654010c41b2d7b97c7386645a180c"
)
F9_7_RETIREMENT_SHA256 = (
    "f1fd6e618bd16ff4216f46587ce897756e465ada92ee9bc398335cd9239fe188"
)
F9_7_V2_DESCRIPTOR_SHA256 = (
    "e198125dbaa20a7966abcdfb9676e3ab38813d9f5347f57d7b3118d24953190d"
)
F9_7_RETIREMENT_V2_SHA256 = (
    "fd6287795245a131b6b71bc2242ed4c8727091c61af27f4fe5cf9faaecc742fa"
)
F9_7_HISTORICAL_DESCRIPTOR_SHA256 = (
    "5d32ed2c977c59c38d56948e687ba2b05ecd9ad8b2d3f5752cce3a9836889de3"
)
INSERT_ALLOWLIST = {
    "first_name",
    "last_name",
    "email",
    "whatsapp",
    "source_page",
    "type",
    "course_id",
    "area_interest",
    "budget",
    "modality",
    "description",
    "is_late_enrollment_request",
}


def _manifest(path: Path = F9_7_MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _marker(path: Path) -> str:
    return f"sha256:{canonical_sql_sha256(path)}"


class _VerifierDatabase:
    def __init__(self, result: bool = True, catalog_result: bool = True):
        self.result = result
        self.catalog_result = catalog_result
        self.calls: list[str] = []
        self.catalog_calls: list[str] = []

    def rpc_raise(self, name: str, _params: dict) -> bool:
        self.calls.append(name)
        return self.result

    def scalar_bool(self, sql: str) -> bool:
        self.catalog_calls.append(sql)
        return self.catalog_result


def test_manifest_is_exact_schema_v3_six_entry_successor():
    f8 = _manifest(F8_MANIFEST)
    historical = _manifest(F9_7_HISTORICAL_MANIFEST)
    v2 = _manifest(F9_7_V2_MANIFEST)
    candidate = _manifest()

    assert candidate["schema_version"] == 3
    assert candidate["phase"] == "F9.7"
    assert candidate["package_id"] == candidate_module.PACKAGE_ID
    assert candidate["status"] == "reconciled_not_certified"
    assert candidate["blocked_targets"] == ["free", "pro"]
    assert historical["entries"][:4] == f8["entries"]
    assert candidate["entries"][:5] == historical["entries"]
    assert v2["entries"][:5] == candidate["entries"][:5]
    assert len(candidate["entries"]) == 6
    assert candidate["entries"][-1] == {
        "id": "F9.7-NOTIFY-NEW-LEAD-RETIREMENT-V3",
        "component": "notify_new_lead_retirement_v3",
        "path": "db/migrations/20260728_fase09_7_notify_new_lead_retirement_v3.sql",
        "sha256": F9_7_RETIREMENT_SHA256,
        "provenance": "new_forward_only",
        "targets": ["free", "pro"],
    }
    assert candidate["supersedes"] == {
        "manifest": "db/manifests/fase09_7_free_schema_rls_v2.json",
        "status": "superseded_non_promotable",
        "reason": "fresh_free_notify_drift_classified_successor_v3_required",
    }
    assert candidate["prerequisites"] == [
        "backend_service_identity_verified",
        "local_postgresql17_candidate_verified",
        "notify_drift_diagnostic_successor_v3_eligible",
    ]
    assert "free_certified" not in candidate["prerequisites"]
    assert not any("backfill" in item for item in candidate["prerequisites"])


def test_manifest_freezes_closure_and_canonical_descriptor_digests():
    candidate = _manifest()
    historical = _manifest(F9_7_HISTORICAL_MANIFEST)
    v2 = _manifest(F9_7_V2_MANIFEST)
    canonical = json.dumps(
        candidate,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    assert canonical_sql_sha256(F9_7_MIGRATION) == F9_7_MIGRATION_SHA256
    assert canonical_sql_sha256(F9_7_RETIREMENT) == F9_7_RETIREMENT_SHA256
    assert canonical_sql_sha256(F9_7_RETIREMENT_V2) == F9_7_RETIREMENT_V2_SHA256
    assert canonical_json_sha256(historical) == F9_7_HISTORICAL_DESCRIPTOR_SHA256
    assert canonical_json_sha256(v2) == F9_7_V2_DESCRIPTOR_SHA256
    assert hashlib.sha256(canonical).hexdigest() == F9_7_DESCRIPTOR_SHA256
    assert canonical_json_sha256(candidate) == F9_7_DESCRIPTOR_SHA256
    assert candidate_module.MANIFEST_SHA256 == F9_7_DESCRIPTOR_SHA256
    assert load_manifest(F9_7_MANIFEST, "free") == load_manifest(
        F9_7_MANIFEST, "pro"
    )


def test_first_five_migrations_freeze_lf_identity_across_worktree_eol():
    for name, lf_sha256 in LF_MIGRATION_SHA256.items():
        path = ROOT / "db/migrations" / name
        raw_bytes = path.read_bytes()
        assert hashlib.sha256(raw_bytes.replace(b"\r\n", b"\n")).hexdigest() == lf_sha256
        assert canonical_sql_sha256(path) == lf_sha256


@pytest.mark.parametrize(
    ("migration", "expected_sha256"),
    [
        (F9_7_MIGRATION, F9_7_MIGRATION_SHA256),
        (F9_7_RETIREMENT_V2, F9_7_RETIREMENT_V2_SHA256),
        (F9_7_RETIREMENT, F9_7_RETIREMENT_SHA256),
    ],
)
def test_sql_checksum_is_stable_across_lf_and_crlf(
    tmp_path: Path,
    migration: Path,
    expected_sha256: str,
):
    lf = migration.read_bytes().replace(b"\r\n", b"\n")
    crlf_path = tmp_path / migration.name
    crlf_path.write_bytes(lf.replace(b"\n", b"\r\n"))
    assert canonical_sql_sha256(crlf_path) == expected_sha256


def test_manifest_excludes_non_candidate_surfaces_without_historical_entries():
    candidate = _manifest()
    assert candidate["excluded"] == {
        "fase09_5_artifacts": "historical_non_promotable",
        "H-00": "historical_free_only",
        "backfill": "separate_future_gate",
        "pro_execution": "blocked",
        "persistent_canary": "excluded",
        "operational_data": "excluded",
        "historical_snapshots": "superseded",
        "remote_predicate_trigger_attestation": (
            "replaced_by_local_forward_only_retirement"
        ),
        "fase09_7_v2_manifest": "superseded_non_promotable",
    }
    entry_identity = json.dumps(candidate["entries"], sort_keys=True)
    assert "20260726_fase09_5" not in entry_identity
    assert "rls_canary_reconciliation" not in entry_identity
    assert "policy_inventory_reconciliation" not in entry_identity
    assert all(entry["targets"] == ["free", "pro"] for entry in candidate["entries"])


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["entries"].reverse(),
        lambda value: value["entries"][-1].__setitem__("sha256", "0" * 64),
        lambda value: value["entries"].append(dict(value["entries"][-1])),
        lambda value: value.__setitem__("status", "ready_for_free"),
        lambda value: value.__setitem__("blocked_targets", ["pro"]),
        lambda value: value["prerequisites"].append("free_certified"),
        lambda value: value.__setitem__("unexpected", True),
    ],
)
def test_schema_v3_descriptor_rejects_any_digest_or_shape_drift(
    tmp_path: Path,
    mutation,
):
    candidate = _manifest()
    mutation(candidate)
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(candidate), encoding="utf-8")
    with pytest.raises(ManifestError, match="F9.7.*schema-v3 digest"):
        load_manifest(path, "free", root=ROOT)


def test_migration_is_forward_only_access_contract_without_operational_data():
    sql = F9_7_MIGRATION.read_text(encoding="utf-8")
    validate_promotable_sql(sql, label=F9_7_MIGRATION.name)

    assert "ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE public.email_log ENABLE ROW LEVEL SECURITY" in sql
    assert "DROP POLICY IF EXISTS email_log_select_authenticated" in sql
    assert sql.count("CREATE POLICY ") == 4
    assert "SECURITY INVOKER" in sql
    assert "SECURITY DEFINER" not in sql
    assert "verify_fase07_g1b_closure" in sql
    assert "verify_fase09_7_public_access_closure" in sql
    assert "SELECT public.verify_fase09_7_public_access_closure();" in sql
    assert "'REFERENCES', 'TRIGGER', 'MAINTAIN'" in sql
    assert "auth.role()" not in sql
    assert "20260726_fase09_5" not in sql
    for forbidden in (
        "historical_free_only",
        "BACKFILL",
        "release_canary",
        "canary.invalid",
        "INSERT INTO public.leads",
        "INSERT INTO public.email_log",
        "UPDATE public.",
        "DELETE FROM public.",
    ):
        assert forbidden not in sql


def test_sixth_migration_fail_closes_and_retires_only_reviewed_objects():
    sql = F9_7_RETIREMENT.read_text(encoding="utf-8")
    validate_promotable_sql(sql, label=F9_7_RETIREMENT.name)
    preamble = sql.split("DO $retirement_guard$", 1)[0]

    assert preamble.index("SET lock_timeout = '5s';") < preamble.index(
        "LOCK TABLE public.leads IN ACCESS EXCLUSIVE MODE;"
    )
    assert "LOCK TABLE public.leads IN ACCESS EXCLUSIVE MODE;" in sql
    assert "pg_catalog.pg_proc" not in preamble
    assert "pg_catalog.pg_trigger" not in preamble
    assert "pg_catalog.pg_depend" not in preamble
    assert "IN SHARE ROW EXCLUSIVE MODE;" not in preamble
    assert "public.verify_fase09_7_public_access_closure()" in sql
    assert candidate_module.PUBLIC_ACCESS_VERIFIER_SOURCE_SHA256 in sql
    assert candidate_module.PUBLIC_ACCESS_VERIFIER_DEFINITION_SHA256 in sql
    assert "DROP TRIGGER trg_notify_new_lead ON public.leads;" in sql
    assert "DROP FUNCTION public.notify_new_lead();" in sql
    assert sql.index("$retirement_guard$;") < sql.index("DROP TRIGGER")
    assert sql.index("DROP TRIGGER") < sql.index("DROP FUNCTION")
    assert "DROP TRIGGER IF EXISTS" not in sql
    assert "DROP FUNCTION IF EXISTS" not in sql
    assert "DROP TRIGGER trg_notify_new_lead ON public.leads CASCADE" not in sql
    assert "DROP FUNCTION public.notify_new_lead() CASCADE" not in sql
    assert "CREATE OR REPLACE FUNCTION" not in sql
    assert "CREATE FUNCTION public.verify_fase09_7_notify_new_lead_retirement" in sql
    assert "E'\\r\\n', E'\\n'" in sql
    assert PROJECT_REF_LENGTH == 20
    assert f"[a-z0-9]{{{PROJECT_REF_LENGTH}}}" in sql
    assert "IS NOT TRUE" in sql
    assert "verify_fase09_7_notify_new_lead_retirement" in sql
    assert "net.http_post" not in sql
    assert "to_jsonb(NEW)" not in sql
    assert "supabase.co" not in sql
    assert "functions/v1" not in sql
    assert "send-lead-emails" not in sql
    assert "absent_clean" in sql
    for variant in NOTIFY_VARIANTS_BY_NAME.values():
        assert str(variant.prosrc_lf_octets) in sql
        for fingerprint in (
            variant.prosrc_lf_sha256,
            variant.prosrc_normalized_sha256,
            variant.definition_lf_sha256,
            variant.definition_normalized_sha256,
            variant.prosrc_redacted_sha256,
            variant.prosrc_normalized_redacted_sha256,
            variant.definition_redacted_sha256,
            variant.definition_normalized_redacted_sha256,
        ):
            if fingerprint:
                assert fingerprint in sql


def test_notify_truth_table_is_shared_by_diagnostic_and_migration():
    migration = F9_7_RETIREMENT.read_text(encoding="utf-8")
    diagnostic = (
        ROOT / "scripts/maintenance/fase09_7_notify_drift_diagnostic.sql"
    ).read_text(encoding="utf-8")

    assert PROJECT_REF_GRAMMAR in migration
    assert PROJECT_REF_GRAMMAR in diagnostic
    assert "boundary_class" in diagnostic
    assert "route_class" in diagnostic
    assert "successor_v3_eligible" in diagnostic
    assert "diagnostic_fail_closed" in diagnostic
    assert "SUCCESSOR_V3_ELIGIBLE" in diagnostic
    assert "STOP_ABSENT_CLEAN_BOUNDARY_0" in diagnostic
    assert "STOP_F9_7_V2_STEM" in diagnostic
    assert "STOP_F9_5_HISTORICAL_NON_PROMOTABLE" in diagnostic
    assert candidate_module.PUBLIC_ACCESS_VERIFIER_SOURCE_SHA256 in diagnostic
    assert candidate_module.PUBLIC_ACCESS_VERIFIER_DEFINITION_SHA256 in diagnostic
    for variant in NOTIFY_VARIANTS_BY_NAME.values():
        assert variant.name in diagnostic
        for fingerprint in (
            variant.prosrc_lf_sha256,
            variant.prosrc_normalized_sha256,
            variant.definition_lf_sha256,
            variant.definition_normalized_sha256,
            variant.prosrc_redacted_sha256,
            variant.prosrc_normalized_redacted_sha256,
            variant.definition_redacted_sha256,
            variant.definition_normalized_redacted_sha256,
        ):
            if fingerprint:
                assert fingerprint in migration
                assert fingerprint in diagnostic


def test_lead_insert_grant_is_the_exact_frontend_allowlist():
    sql = F9_7_MIGRATION.read_text(encoding="utf-8")
    grant = sql.split("GRANT INSERT (", 1)[1].split(
        ") ON TABLE public.leads TO anon, authenticated;", 1
    )[0]
    granted = {item.strip() for item in grant.replace("\n", " ").split(",")}
    assert granted == INSERT_ALLOWLIST
    assert {"id", "status", "created_at", "lead_source_type"}.isdisjoint(
        granted
    )
    assert "lead_source_type = 'organic'" in sql
    assert "'''organic''::text" in sql
    assert "course.publication_status = 'publicado'" in sql
    assert "profile.production_enabled = true" in sql


def test_functional_sql_has_complete_direct_public_negatives():
    sql = (ROOT / "tests/sql/fase09_7_functional_test.sql").read_text(
        encoding="utf-8"
    )
    assert "BEGIN;" in sql
    assert sql.rstrip().endswith("ROLLBACK;")
    for marker in (
        "anon lead SELECT denied",
        "authenticated lead SELECT denied",
        "anon email_log SELECT denied",
        "authenticated email_log SELECT denied",
        "managed id denied",
        "managed status denied",
        "managed created_at denied",
        "managed lead_source_type denied even when organic",
        "MAINTAIN grant drift",
        "unrelated private policy is allowed",
        "transitive SELECT policy drift",
        "F8 courses RLS drift",
        "F8 publication default drift",
        "F8 inherited courses SELECT policy drift",
        "F8 representative constraint drift",
        "F8 representative index drift",
        "F8 representative function ACL drift",
        "inherited permissive leads INSERT policy drift",
        "malformed insert is accepted only while verifier is false",
        "service reader ACL drift",
        "notify_new_lead function retired",
        "notify_new_lead trigger retired",
        "trigger retirement verifier is service-only",
    ):
        assert marker in sql


@pytest.mark.parametrize("prefix_size", [0, 3, 4, 5, 6])
def test_planner_accepts_only_reviewed_ledger_boundaries(prefix_size: int):
    paths = load_manifest(F9_7_MANIFEST, "free")
    applied = {path.stem: _marker(path) for path in paths[:prefix_size]}
    database = _VerifierDatabase()
    plan = classify_manifest_ledger(paths, applied)
    assert isinstance(plan, ManifestPlan)
    assert plan.boundary == prefix_size
    assert plan.exact_prefix == tuple(
        (path.stem, _marker(path)) for path in paths[:prefix_size]
    )
    assert list(plan.pending_paths) == paths[prefix_size:]
    validated = candidate_module.validate_manifest_ledger_state(database, paths, applied)
    assert validated == plan
    assert len(database.calls) == prefix_size
    assert len(database.catalog_calls) == int(prefix_size >= 5) + int(prefix_size >= 6)


@pytest.mark.parametrize("prefix_size", [1, 2])
def test_planner_rejects_unsafe_partial_boundaries(prefix_size: int):
    paths = load_manifest(F9_7_MANIFEST, "free")
    applied = {path.stem: _marker(path) for path in paths[:prefix_size]}
    with pytest.raises(RuntimeError, match="F9.7.*boundaries"):
        candidate_module.validate_manifest_ledger_state(
            _VerifierDatabase(), paths, applied
        )


def test_planner_rejects_checksum_gap_and_semantic_drift():
    paths = load_manifest(F9_7_MANIFEST, "free")
    checksum_drift = {paths[0].stem: "sha256:" + "0" * 64}
    with pytest.raises(RuntimeError, match="Ledger/checksum mismatch"):
        candidate_module.validate_manifest_ledger_state(
            _VerifierDatabase(), paths, checksum_drift
        )

    gap = {
        paths[0].stem: _marker(paths[0]),
        paths[2].stem: _marker(paths[2]),
    }
    with pytest.raises(RuntimeError, match="contiguous manifest prefix"):
        candidate_module.validate_manifest_ledger_state(
            _VerifierDatabase(), paths, gap
        )

    for blocked in (
        candidate_module.F9_7_V2_RETIREMENT_STEM,
        *candidate_module.F9_5_HISTORICAL_NON_PROMOTABLE_STEMS,
    ):
        with pytest.raises(RuntimeError, match="non-promotable"):
            candidate_module.validate_manifest_ledger_state(
                _VerifierDatabase(), paths, {blocked: "sha256:" + "a" * 64}
            )

    applied = {path.stem: _marker(path) for path in paths}
    with pytest.raises(RuntimeError, match="Postcondicion fallida"):
        candidate_module.validate_manifest_ledger_state(
            _VerifierDatabase(result=False), paths, applied
        )

    with pytest.raises(RuntimeError, match="Postcondicion externa fallida"):
        candidate_module.validate_manifest_ledger_state(
            _VerifierDatabase(catalog_result=False), paths, applied
        )


def test_planner_projects_candidate_without_rejecting_unrelated_history():
    paths = load_manifest(F9_7_MANIFEST, "free")
    applied = {
        "20260101_unrelated_history": "sha256:" + "a" * 64,
        **{path.stem: _marker(path) for path in paths[:4]},
    }
    assert candidate_module.validate_manifest_ledger_state(
        _VerifierDatabase(), paths, applied
    ).pending_paths == tuple(paths[4:])
    assert applied["20260101_unrelated_history"] == "sha256:" + "a" * 64


def test_atomic_package_has_final_postcondition_before_six_ledger_writes():
    paths = load_manifest(F9_7_MANIFEST, "free")
    plan = classify_manifest_ledger(paths, {})
    package = candidate_module.build_manifest_package_sql(plan, version=20260727093000)
    final_verifier = "public.verify_fase09_7_notify_new_lead_retirement()"

    assert package.count("-- manifest-entry") == 6
    assert package.startswith("SET lock_timeout = '5s';")
    assert package.index("SET statement_timeout = '60s';") < package.index(
        "LOCK TABLE public.supabase_migrations IN SHARE ROW EXCLUSIVE MODE;"
    )
    assert "LOCK TABLE pg_catalog.pg_proc" not in package
    assert "LOCK TABLE pg_catalog.pg_trigger" not in package
    assert "LOCK TABLE pg_catalog.pg_depend" not in package
    assert package.count("DO $manifest_pending$") == 6
    assert package.count("DO $manifest_verify$") == 6
    assert package.count("DO $manifest_external_verify$") == 2
    assert package.count("INSERT INTO public.supabase_migrations") == 6
    assert final_verifier in package
    assert candidate_module.RETIREMENT_VERIFIER_SOURCE_SHA256 in package
    assert candidate_module.PUBLIC_ACCESS_VERIFIER_SOURCE_SHA256 in package
    assert candidate_module.PUBLIC_ACCESS_VERIFIER_DEFINITION_SHA256 in package
    assert "IS NOT TRUE THEN" in package
    assert "net.http_post" not in package
    assert "to_jsonb(NEW)" not in package
    assert "send-lead-emails" not in package
    assert "functions/v1" not in package
    assert package.index(final_verifier) < package.index(
        "-- manifest-ledger-registration"
    )
    assert package.index("DO $manifest_external_verify$") < package.index(
        "-- manifest-ledger-registration"
    )
    assert "ON CONFLICT (name) DO NOTHING" not in package


def test_atomic_package_revalidates_applied_prefix_under_timeout_without_catalog_locks():
    paths = load_manifest(F9_7_MANIFEST, "free")
    prefix = {path.stem: _marker(path) for path in paths[:5]}
    plan = classify_manifest_ledger(paths, prefix)
    package = candidate_module.build_manifest_package_sql(plan, version=20260727093005)

    assert package.count("DO $manifest_prefix$") == 5
    assert package.count("DO $manifest_prefix_verify$") == 5
    assert package.count("DO $manifest_prefix_external_verify$") == 1
    assert "F9.7 ledger contains non-promotable historical stem" in package
    assert "WITH expected_ledger" in package
    assert "suffix_present_count" in package
    assert "Postcondicion de prefijo fallida" in package
    assert "Postcondicion externa de prefijo fallida" in package
    assert "public.verify_fase09_7_public_access_closure() IS NOT TRUE" in package
    assert "pg_catalog.pg_proc, pg_catalog.pg_trigger" not in package
    assert package.index("SET lock_timeout = '5s';") < package.index(
        "LOCK TABLE public.supabase_migrations IN SHARE ROW EXCLUSIVE MODE;"
    )
    assert package.index(
        "LOCK TABLE public.supabase_migrations IN SHARE ROW EXCLUSIVE MODE;"
    ) < (
        package.index("DO $manifest_prefix_verify$")
    )
    assert package.index("DO $manifest_prefix_verify$") < package.index(
        "-- manifest-entry"
    )


def test_package_generation_rejects_unvalidated_inputs():
    paths = load_manifest(F9_7_MANIFEST, "free")
    with pytest.raises(TypeError, match="ManifestPlan"):
        candidate_module.build_manifest_package_sql(paths, version=20260727093000)  # type: ignore[arg-type]


def test_f9_7_v2_is_manifest_only_and_legacy_runner_guarded():
    assert "20260727_fase09_7_" in db_migrate.MANIFEST_ONLY_PREFIXES
    with pytest.raises(db_migrate.ManifestError, match="09.7"):
        db_migrate.select_legacy_migrations([F9_7_RETIREMENT.stem])
    with pytest.raises(db_migrate.ManifestError, match="manifest-only"):
        db_migrate.apply_migration(object(), str(F9_7_RETIREMENT), dry_run=True)


def test_retired_send_lead_emails_edge_function_has_no_pii_egress():
    source = (ROOT / "supabase/functions/send-lead-emails/index.ts").read_text(
        encoding="utf-8"
    )

    assert "status: 410" in source
    assert "retired in F9.7" in source
    for forbidden in (
        "RESEND_API_KEY",
        "api.resend.com",
        "Deno.env",
        "fetch(",
        "req.json",
        "payload",
        "first_name",
        "last_name",
        "whatsapp",
        "lead.email",
        "mailto:",
        "wa.me",
        "Authorization",
        "Bear" + "er",
    ):
        assert forbidden not in source


def test_candidate_module_is_local_only_and_historical_modules_are_isolated():
    source = (
        ROOT / "scripts/maintenance/fase09_7_candidate.py"
    ).read_text(encoding="utf-8")
    assert "requests" not in source
    assert "http://" not in source
    assert "https://" not in source
    assert "migration_manifest" not in source
    assert "db_migrate" not in source
    assert len(load_manifest(F9_7_MANIFEST, "free")) == 6


def test_unconfirmed_remote_attestation_draft_is_absent():
    for relative_path in (
        "db/manifests/fase09_7_predicate_trigger_attestation.json",
        "scripts/maintenance/fase09_7_predicate_trigger_attestation.sql",
        "tests/test_fase09_7_predicate_trigger_attestation.py",
    ):
        assert not (ROOT / relative_path).exists()


def test_offline_notify_fixture_is_ephemeral_pg17_guarded():
    source = (ROOT / "tests/sql/fase09_7_notify_variants_offline.sql").read_text(
        encoding="utf-8"
    )
    assert source.index("current_database() <> 'studiamatch_f97'") < source.index(
        "CREATE TEMP TABLE IF NOT EXISTS notify_variant_summary"
    )
    assert "server_version_num" in source
    assert "session sentinel" in source
    assert "sed -n" not in source
    assert "/tmp/fase09" not in source


def test_frontend_public_client_uses_publishable_key_and_never_secret_key():
    frontend = (ROOT / "web/src/lib/supabase.ts").read_text(encoding="utf-8")
    web_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "web").rglob("*")
        if path.is_file()
        and path.suffix in {".ts", ".tsx", ".js", ".jsx"}
        and "node_modules" not in path.parts
        and ".next" not in path.parts
    )

    assert "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY" in frontend
    assert "normalizeSupabaseUrl" in frontend
    assert "sb_publishable_ci_test" in frontend
    assert "supabase\\.co" in frontend
    assert "parsed.origin" in frontend
    assert "NEXT_SUPABASE_SECRET_KEY" not in frontend
    assert "NEXT_SUPABASE_SECRET_KEY" not in web_sources
    assert "sb_secret_" not in web_sources


def test_frontend_lead_capture_flag_fail_closes_before_public_post():
    wrapper = (ROOT / "web/src/lib/leadCapture.ts").read_text(encoding="utf-8")
    core = (ROOT / "web/src/lib/leadCaptureCore.ts").read_text(encoding="utf-8")
    sources = [
        ROOT / "web/src/app/HomeContent.tsx",
        ROOT / "web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx",
    ]

    assert "isLeadCaptureEnabled(" in wrapper
    assert "process.env.NEXT_PUBLIC_LEAD_CAPTURE_ENABLED" in wrapper
    assert "LEAD_CAPTURE_MAINTENANCE_TITLE" in wrapper
    assert "submitLead" in wrapper
    assert "fetchImpl: (input, init) => fetch(input, init)" in wrapper
    assert 'value === "true"' in core
    assert 'value === "false"' in core
    assert core.count("/rest/v1/leads") == 1
    assert "Authorization" not in wrapper
    assert "Authorization" not in core
    assert '"apikey"' in core
    for path in sources:
        source = path.read_text(encoding="utf-8")
        assert "/rest/v1/leads" not in source
        assert "submitLead" in source
        handler = source.split("const handleSubmitLead", 1)[1].split(
            "const filteredCourses" if path.name == "HomeContent.tsx" else "useEffect",
            1,
        )[0]
        assert handler.index("if (!LEAD_CAPTURE_ENABLED)") < handler.index("submitLead")
        assert "data-lead-capture-state" in source
        assert "LEAD_CAPTURE_MAINTENANCE_COPY" in source
        assert "data-pii-control" in source


def test_course_jsonld_escapes_script_breakout_sequences():
    source = (ROOT / "web/src/app/courses/[institution]/[slug]/page.tsx").read_text(
        encoding="utf-8"
    )

    assert "function serializeJsonLd" in source
    assert '"<": "\\\\u003c"' in source
    assert '">": "\\\\u003e"' in source
    assert '"&": "\\\\u0026"' in source
    assert '"\\u2028": "\\\\u2028"' in source
    assert '"\\u2029": "\\\\u2029"' in source
    assert "dangerouslySetInnerHTML={{ __html: serializeJsonLd(ld) }}" in source
    assert "dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }}" not in source


def test_sibling_workflow_contains_networkless_f9_7_job():
    workflow = (ROOT / ".github/workflows/f9-7-contract.yml").read_text(
        encoding="utf-8"
    )
    assert (
        "name: F9.7 Public Access and Trigger Retirement PostgreSQL 17 Contract"
        in workflow
    )
    assert "bash tests/sql/run_fase09_7_postgres.sh" in workflow
    assert "studiamatch-f97-postgres" in workflow
    assert "scripts/maintenance/db_migrate.py" in workflow
    assert "scripts/maintenance/fase09_7_notify_truth.py" in workflow
    assert "supabase/functions/send-lead-emails/index.ts" in workflow
    assert "web/src/lib/leadCapture.ts" in workflow
    assert "web/src/lib/leadCaptureCore.ts" in workflow
    assert "web/src/app/courses/**/CourseDetailClient.tsx" in workflow
    assert ".context/operaciones/pg_net_queue_drain_f9_7.md" in workflow
    assert "--network none" in workflow
    assert "continue-on-error: true" not in workflow
