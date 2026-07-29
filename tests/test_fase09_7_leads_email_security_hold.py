from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.maintenance import db_migrate
from scripts.maintenance import fase09_7_candidate as v3_candidate
from scripts.maintenance import fase09_7_leads_email_security_hold_candidate as hold


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "db/manifests/fase09_7_leads_email_security_hold.json"
MIGRATION = ROOT / "db/migrations/20260729_fase09_7_leads_email_security_hold.sql"
V3_MANIFEST = ROOT / "db/manifests/fase09_7_free_schema_rls_v3.json"


def _marker(path: Path) -> str:
    return f"sha256:{hold.canonical_sql_sha256(path)}"


def _terminal_function_body(sql: str) -> str:
    return sql.split(
        "CREATE OR REPLACE FUNCTION public.verify_fase09_7_leads_email_security_hold()",
        1,
    )[1].split("$function$;", 1)[0]


def test_manifest_is_terminal_single_entry_dependent_on_v3():
    v3_paths, hold_path = hold.load_security_hold_manifest(MANIFEST, "free")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert hold.load_security_hold_manifest(MANIFEST, "pro") == (v3_paths, hold_path)
    assert hold.canonical_json_sha256(manifest) == hold.MANIFEST_SHA256
    assert manifest["package_id"] == hold.PACKAGE_ID
    assert manifest["application_authorized"] is False
    assert manifest["blocked_targets"] == ["free", "pro"]
    assert manifest["allowed_boundaries"] == [6, 7]
    assert manifest["data_plane_roles"] == [
        "anon",
        "authenticated",
        "authenticator",
        "service_role",
    ]
    assert manifest["control_plane_exception"] == {
        "routine": "public.exec_sql(text)",
        "owner": "postgres",
        "security": "SECURITY DEFINER",
        "search_path": "\"\"",
        "execute_grantees": ["service_role"],
        "purpose": "single privileged manifest package application",
        "residual_backlog": "BK-F9.5-07",
    }
    assert manifest["residuals"] == ["BK-F9.5-07"]
    assert manifest["depends_on"]["package_id"] == v3_candidate.PACKAGE_ID
    assert manifest["depends_on"]["manifest_sha256"] == v3_candidate.MANIFEST_SHA256
    assert len(manifest["depends_on"]["entries"]) == 6
    assert len(manifest["entries"]) == 1
    assert hold_path == MIGRATION
    assert hold.canonical_sql_sha256(hold_path) == hold.HOLD_ENTRY["sha256"]
    assert v3_paths == v3_candidate.load_manifest(V3_MANIFEST, "free")


def test_terminal_migration_is_hold_only_without_cascade_or_legacy_postcondition():
    sql = MIGRATION.read_text(encoding="utf-8")
    body = _terminal_function_body(sql)

    assert "LOCK TABLE public.supabase_migrations" in sql
    assert sql.index("LOCK TABLE public.supabase_migrations") < sql.index(
        "LOCK TABLE public.leads"
    )
    assert sql.index("LOCK TABLE public.leads") < sql.index(
        "LOCK TABLE public.email_log"
    )
    assert "CASCADE" not in sql.upper()
    assert "ON CONFLICT" not in sql.upper()
    assert "INSERT INTO public.supabase_migrations" not in sql
    assert "public.verify_fase09_7_public_access_closure() IS NOT TRUE" in sql
    assert "public.verify_fase09_7_notify_new_lead_retirement() IS NOT TRUE" in sql
    assert "public.verify_fase09_7_public_access_closure() IS NOT TRUE" not in body
    assert "public.verify_fase09_7_notify_new_lead_retirement() IS NOT TRUE" not in body
    assert "GRANT SELECT ON TABLE public.leads TO service_role;" not in sql
    assert "GRANT SELECT ON TABLE public.email_log TO service_role;" not in sql
    assert "GRANT SELECT, DELETE" not in sql
    assert "leads_security_hold_service_delete" not in body
    assert "email_log_security_hold_service_delete" not in body
    assert "CHECK (false) NOT VALID" in sql
    for marker in (
        "-- security-hold-stage-revokes-complete",
        "-- security-hold-stage-policies-complete",
        "-- security-hold-stage-constraints-complete",
        "-- security-hold-stage-verifier-complete",
        "-- security-hold-stage-postcondition-complete",
        "-- security-hold-stage-terminal-verification-complete",
        "-- security-hold-stage-after-ledger",
    ):
        assert (sql + hold.build_security_hold_package_sql(
            hold.classify_security_hold_ledger(
                *hold.load_security_hold_manifest(MANIFEST, "free"),
                {
                    path.stem: _marker(path)
                    for path in hold.load_security_hold_manifest(MANIFEST, "free")[0]
                },
            ),
            version=20260729000100,
        )).count(marker) >= 1
    assert "WITH RECURSIVE reachable_roles" in body
    assert "membership.inherit_option" in body
    assert "membership.set_option" in body
    assert "membership.admin_option" in body
    assert "authenticator_oid" in body
    assert "dependent_views(view_oid, path)" in body
    assert "publication.puballtables" in body
    assert "pg_publication_namespace" in body
    assert "pg_catalog.pg_get_functiondef(procedure_record.oid)" in body
    assert "public.exec_sql(text)" in body
    assert "authenticator" in body
    assert "DROP TABLE" not in sql.upper()
    assert "public.ratings" not in sql
    assert "public.reviews" not in sql
    assert "public.staging_raw" not in sql
    assert "public.cleansed_programs" not in sql
    assert "public.enriched_programs" not in sql
    assert "public.courses" not in sql


def test_planner_accepts_only_boundaries_6_and_7():
    v3_paths, hold_path = hold.load_security_hold_manifest(MANIFEST, "free")
    v3_applied = {path.stem: _marker(path) for path in v3_paths}

    boundary6 = hold.classify_security_hold_ledger(v3_paths, hold_path, v3_applied)
    assert boundary6.boundary == 6
    assert boundary6.pending_path == hold_path
    assert not boundary6.replay_only

    boundary7 = hold.classify_security_hold_ledger(
        v3_paths,
        hold_path,
        {**v3_applied, hold_path.stem: _marker(hold_path)},
    )
    assert boundary7.boundary == 7
    assert boundary7.pending_path is None
    assert boundary7.replay_only

    with pytest.raises(RuntimeError, match="boundary 6"):
        hold.classify_security_hold_ledger(v3_paths, hold_path, dict(list(v3_applied.items())[:5]))
    with pytest.raises(RuntimeError, match="checksum"):
        hold.classify_security_hold_ledger(
            v3_paths, hold_path, {**v3_applied, hold_path.stem: "sha256:" + "0" * 64}
        )
    with pytest.raises(RuntimeError, match="non-promotable"):
        hold.classify_security_hold_ledger(
            v3_paths,
            hold_path,
            {**v3_applied, v3_candidate.F9_7_V2_RETIREMENT_STEM: "sha256:" + "a" * 64},
        )
    with pytest.raises(RuntimeError, match="unknown F9.7"):
        hold.classify_security_hold_ledger(
            v3_paths,
            hold_path,
            {**v3_applied, "20260728_fase09_7_unreviewed_terminal": "sha256:" + "b" * 64},
        )


def test_package_generation_separates_apply_from_replay():
    v3_paths, hold_path = hold.load_security_hold_manifest(MANIFEST, "free")
    v3_applied = {path.stem: _marker(path) for path in v3_paths}

    boundary6 = hold.classify_security_hold_ledger(v3_paths, hold_path, v3_applied)
    package = hold.build_security_hold_package_sql(boundary6, version=20260729000100)
    assert package.count("-- manifest-entry 20260729_fase09_7_leads_email_security_hold") == 1
    assert package.count("INSERT INTO public.supabase_migrations") == 1
    assert package.count("-- security-hold-stage-before-ledger") == 1
    assert "SELECT public.exec_sql" not in package
    assert not package.lstrip().startswith("BEGIN;")
    assert "COMMIT;" not in package
    assert "ON CONFLICT" not in package.upper()
    assert "security hold ledger contamination" in package
    assert "20260727_fase09_7_notify_new_lead_retirement" in package
    assert package.index("public.verify_fase09_7_leads_email_security_hold()") < package.index(
        "-- manifest-ledger-registration"
    )

    boundary7 = hold.classify_security_hold_ledger(
        v3_paths,
        hold_path,
        {**v3_applied, hold_path.stem: _marker(hold_path)},
    )
    replay = hold.build_security_hold_package_sql(boundary7, version=20260729000100)
    assert "SET TRANSACTION READ ONLY;" not in replay
    assert "LOCK TABLE public.supabase_migrations IN SHARE ROW EXCLUSIVE MODE;" in replay
    assert "LOCK TABLE public.leads IN ACCESS EXCLUSIVE MODE;" in replay
    assert "LOCK TABLE public.email_log IN ACCESS EXCLUSIVE MODE;" in replay
    assert "-- manifest-entry" not in replay
    assert "INSERT INTO public.supabase_migrations" not in replay
    assert "security hold ledger contamination" in replay
    for forbidden in ("ALTER TABLE", "CREATE OR REPLACE FUNCTION", "DROP POLICY", "GRANT ", "REVOKE "):
        assert forbidden not in replay


def test_terminal_stem_is_blocked_outside_manifest_only_runner():
    assert "20260729_fase09_7_" in db_migrate.MANIFEST_ONLY_PREFIXES
    with pytest.raises(db_migrate.ManifestError, match="only --validate-only"):
        db_migrate._load_manifest_paths(MANIFEST, "free", offline_only=False)
    with pytest.raises(db_migrate.ManifestError, match="09.7"):
        db_migrate.select_legacy_migrations([hold.HOLD_STEM])
    with pytest.raises(db_migrate.ManifestError, match="manifest-only"):
        db_migrate.apply_migration(object(), str(MIGRATION), dry_run=True)
