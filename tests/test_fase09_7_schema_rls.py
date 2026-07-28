from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.maintenance import db_migrate
from scripts.maintenance import fase09_7_candidate as candidate_module
from scripts.maintenance.fase09_7_candidate import (
    ManifestError,
    canonical_json_sha256,
    canonical_sql_sha256,
    load_manifest,
    validate_promotable_sql,
)


ROOT = Path(__file__).resolve().parents[1]
F8_MANIFEST = ROOT / "db/manifests/fase08_candidate.json"
F9_7_HISTORICAL_MANIFEST = ROOT / "db/manifests/fase09_7_free_schema_rls.json"
F9_7_MANIFEST = ROOT / "db/manifests/fase09_7_free_schema_rls_v2.json"
F9_7_MIGRATION = (
    ROOT / "db/migrations/20260727_fase09_7_public_access_closure.sql"
)
F9_7_RETIREMENT = (
    ROOT / "db/migrations/20260727_fase09_7_notify_new_lead_retirement.sql"
)
F9_7_MIGRATION_SHA256 = (
    "040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b"
)
F9_7_DESCRIPTOR_SHA256 = (
    "e198125dbaa20a7966abcdfb9676e3ab38813d9f5347f57d7b3118d24953190d"
)
F9_7_RETIREMENT_SHA256 = (
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


def test_manifest_is_exact_schema_v2_six_entry_successor():
    f8 = _manifest(F8_MANIFEST)
    historical = _manifest(F9_7_HISTORICAL_MANIFEST)
    candidate = _manifest()

    assert candidate["schema_version"] == 2
    assert candidate["phase"] == "F9.7"
    assert candidate["package_id"] == candidate_module.PACKAGE_ID
    assert candidate["status"] == "reconciled_not_certified"
    assert candidate["blocked_targets"] == ["free", "pro"]
    assert historical["entries"][:4] == f8["entries"]
    assert candidate["entries"][:5] == historical["entries"]
    assert len(candidate["entries"]) == 6
    assert candidate["entries"][-1] == {
        "id": "F9.7-NOTIFY-NEW-LEAD-RETIREMENT",
        "component": "notify_new_lead_retirement",
        "path": "db/migrations/20260727_fase09_7_notify_new_lead_retirement.sql",
        "sha256": F9_7_RETIREMENT_SHA256,
        "provenance": "new_forward_only",
        "targets": ["free", "pro"],
    }
    assert candidate["prerequisites"] == [
        "backend_service_identity_verified",
        "local_postgresql17_candidate_verified",
    ]
    assert "free_certified" not in candidate["prerequisites"]
    assert not any("backfill" in item for item in candidate["prerequisites"])


def test_manifest_freezes_closure_and_canonical_descriptor_digests():
    candidate = _manifest()
    historical = _manifest(F9_7_HISTORICAL_MANIFEST)
    canonical = json.dumps(
        candidate,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    assert canonical_sql_sha256(F9_7_MIGRATION) == F9_7_MIGRATION_SHA256
    assert canonical_sql_sha256(F9_7_RETIREMENT) == F9_7_RETIREMENT_SHA256
    assert canonical_json_sha256(historical) == F9_7_HISTORICAL_DESCRIPTOR_SHA256
    assert hashlib.sha256(canonical).hexdigest() == F9_7_DESCRIPTOR_SHA256
    assert canonical_json_sha256(candidate) == F9_7_DESCRIPTOR_SHA256
    assert candidate_module.MANIFEST_SHA256 == F9_7_DESCRIPTOR_SHA256
    assert load_manifest(F9_7_MANIFEST, "free") == load_manifest(
        F9_7_MANIFEST, "pro"
    )


@pytest.mark.parametrize(
    ("migration", "expected_sha256"),
    [
        (F9_7_MIGRATION, F9_7_MIGRATION_SHA256),
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
def test_schema_v2_descriptor_rejects_any_digest_or_shape_drift(
    tmp_path: Path,
    mutation,
):
    candidate = _manifest()
    mutation(candidate)
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(candidate), encoding="utf-8")
    with pytest.raises(ManifestError, match="F9.7.*schema-v2 digest"):
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
    assert "IS NOT TRUE" in sql
    assert "verify_fase09_7_notify_new_lead_retirement" in sql
    assert "net.http_post" not in sql
    assert "to_jsonb(NEW)" not in sql
    assert "supabase.co" not in sql
    for fingerprint in (
        "5fa712326d4c331c074caabafc8957dc4edd3e85404ad31ad0f5f7304fc6b32e",
        "42dab6c9e511e61ad04f8dbd8bccf070e23b598d6877de1dd27865b4b2734ccc",
        "c05c403dc06c7a03379591de7bc729f6aa15366566aa5dcf6a00de2e7f3e0d12",
        "7844c0c19a151091d05ba33800013edc4709125725221bd313e59363f647d020",
    ):
        assert fingerprint in sql


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
    assert candidate_module.validate_manifest_ledger_state(
        database, paths, applied
    ) == paths[prefix_size:]
    assert len(database.calls) == prefix_size


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
    ) == paths[4:]
    assert applied["20260101_unrelated_history"] == "sha256:" + "a" * 64


def test_atomic_package_has_final_postcondition_before_six_ledger_writes():
    paths = load_manifest(F9_7_MANIFEST, "free")
    package = candidate_module.build_manifest_package_sql(
        paths, version=20260727093000
    )
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
    assert package.count("DO $manifest_external_verify$") == 1
    assert package.count("INSERT INTO public.supabase_migrations") == 6
    assert final_verifier in package
    assert candidate_module.RETIREMENT_VERIFIER_SOURCE_SHA256 in package
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
    package = candidate_module.build_manifest_package_sql(
        paths[5:], expected_prefix=prefix, version=20260727093005
    )

    assert package.count("DO $manifest_prefix$") == 5
    assert package.count("DO $manifest_prefix_verify$") == 5
    assert "Postcondicion de prefijo fallida" in package
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
    assert "NEXT_SUPABASE_SECRET_KEY" not in frontend
    assert "NEXT_SUPABASE_SECRET_KEY" not in web_sources
    assert "sb_secret_" not in web_sources


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
    assert "supabase/functions/send-lead-emails/index.ts" in workflow
    assert ".context/operaciones/pg_net_queue_drain_f9_7.md" in workflow
    assert "--network none" in workflow
    assert "continue-on-error: true" not in workflow
