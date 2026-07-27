from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

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
F9_7_MANIFEST = ROOT / "db/manifests/fase09_7_free_schema_rls.json"
F9_7_MIGRATION = (
    ROOT / "db/migrations/20260727_fase09_7_public_access_closure.sql"
)
F9_7_MIGRATION_SHA256 = (
    "040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b"
)
F9_7_DESCRIPTOR_SHA256 = (
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
    def __init__(self, result: bool = True):
        self.result = result
        self.calls: list[str] = []

    def rpc_raise(self, name: str, _params: dict) -> bool:
        self.calls.append(name)
        return self.result


def test_manifest_is_exact_schema_v2_five_entry_successor():
    f8 = _manifest(F8_MANIFEST)
    candidate = _manifest()

    assert candidate["schema_version"] == 2
    assert candidate["phase"] == "F9.7"
    assert candidate["package_id"] == candidate_module.PACKAGE_ID
    assert candidate["status"] == "reconciled_not_certified"
    assert candidate["blocked_targets"] == ["free", "pro"]
    assert candidate["entries"][:4] == f8["entries"]
    assert len(candidate["entries"]) == 5
    assert candidate["entries"][-1] == {
        "id": "F9.7-PUBLIC-ACCESS-CLOSURE",
        "component": "public_access_closure",
        "path": "db/migrations/20260727_fase09_7_public_access_closure.sql",
        "sha256": F9_7_MIGRATION_SHA256,
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
    canonical = json.dumps(
        candidate,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    assert canonical_sql_sha256(F9_7_MIGRATION) == F9_7_MIGRATION_SHA256
    assert hashlib.sha256(canonical).hexdigest() == F9_7_DESCRIPTOR_SHA256
    assert canonical_json_sha256(candidate) == F9_7_DESCRIPTOR_SHA256
    assert candidate_module.MANIFEST_SHA256 == F9_7_DESCRIPTOR_SHA256
    assert load_manifest(F9_7_MANIFEST, "free") == load_manifest(
        F9_7_MANIFEST, "pro"
    )


def test_sql_checksum_is_stable_across_lf_and_crlf(tmp_path: Path):
    lf = F9_7_MIGRATION.read_bytes().replace(b"\r\n", b"\n")
    crlf_path = tmp_path / F9_7_MIGRATION.name
    crlf_path.write_bytes(lf.replace(b"\n", b"\r\n"))
    assert canonical_sql_sha256(crlf_path) == F9_7_MIGRATION_SHA256


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
    ):
        assert marker in sql


@pytest.mark.parametrize("prefix_size", [0, 3, 4, 5])
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


def test_atomic_package_has_final_postcondition_before_five_ledger_writes():
    paths = load_manifest(F9_7_MANIFEST, "free")
    package = candidate_module.build_manifest_package_sql(
        paths, version=20260727093000
    )
    final_verifier = "public.verify_fase09_7_public_access_closure()"

    assert package.count("-- manifest-entry") == 5
    assert package.startswith(
        "LOCK TABLE public.supabase_migrations IN SHARE ROW EXCLUSIVE MODE;"
    )
    assert package.count("DO $manifest_pending$") == 5
    assert package.count("DO $manifest_verify$") == 5
    assert package.count("INSERT INTO public.supabase_migrations") == 5
    assert final_verifier in package
    assert package.index(final_verifier) < package.index(
        "-- manifest-ledger-registration"
    )
    assert "ON CONFLICT (name) DO NOTHING" not in package


def test_candidate_module_is_local_only_and_historical_modules_are_isolated():
    source = (
        ROOT / "scripts/maintenance/fase09_7_candidate.py"
    ).read_text(encoding="utf-8")
    assert "requests" not in source
    assert "http://" not in source
    assert "https://" not in source
    assert "migration_manifest" not in source
    assert "db_migrate" not in source
    assert len(load_manifest(F9_7_MANIFEST, "free")) == 5


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
    assert "name: F9.7 Public Access Closure PostgreSQL 17 Contract" in workflow
    assert "bash tests/sql/run_fase09_7_postgres.sh" in workflow
    assert "studiamatch-f97-postgres" in workflow
    assert "--network none" in workflow
    assert "continue-on-error: true" not in workflow
