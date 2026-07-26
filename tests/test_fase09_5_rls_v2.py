from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.maintenance import db_migrate
from scripts.maintenance.fase09_5_preflight import (
    CHECK_SQL,
    CHECK_TOOLS,
    EXPECTED_COUNTS,
    EXPECTED_DIGESTS,
    CheckEvidence,
    DirectedCheck,
    H00_COUNTS,
    LEDGER_DIGESTS,
    REQUIRED_CHECKS,
    require_allowed_tool,
    require_free_target,
    require_read_only_sql,
    run_directed_inventory,
)
from scripts.maintenance.migration_manifest import (
    F9_5_V2_MANIFEST_SHA256,
    ManifestError,
    canonical_sql_sha256,
    load_manifest,
    validate_promotable_sql,
)


ROOT = Path(__file__).resolve().parents[1]
V1_MANIFEST = ROOT / "db/manifests/fase09_5_rls_candidate.json"
V2_MANIFEST = ROOT / "db/manifests/fase09_5_rls_candidate_v2.json"
V2_MIGRATION = (
    ROOT / "db/migrations/20260726_fase09_5_policy_inventory_reconciliation.sql"
)
V2_MIGRATION_SHA256 = (
    "76a7c06bcf1b46a513801d0b1843ac081948a34f552e0371136c6ac2ac097822"
)
TARGET_DIGEST = "a" * 64


def _manifest(path: Path) -> dict:
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


def test_v2_is_an_exact_six_entry_append_only_overlay():
    v1 = _manifest(V1_MANIFEST)
    v2 = _manifest(V2_MANIFEST)
    canonical = json.dumps(
        v2, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")

    assert hashlib.sha256(canonical).hexdigest() == F9_5_V2_MANIFEST_SHA256
    assert v2["entries"][:5] == v1["entries"]
    assert len(v2["entries"]) == 6
    assert v2["entries"][5] == {
        "id": "F9.5-POLICY-INVENTORY-RECONCILIATION-V2",
        "component": "policy_inventory_reconciliation",
        "path": "db/migrations/20260726_fase09_5_policy_inventory_reconciliation.sql",
        "sha256": V2_MIGRATION_SHA256,
        "provenance": "new_forward_only",
        "targets": ["free", "pro"],
    }
    assert canonical_sql_sha256(V2_MIGRATION) == V2_MIGRATION_SHA256
    assert v2["status"] == "reconciled_not_certified"
    assert v2["blocked_targets"] == ["free", "pro"]


def test_v2_manifest_loads_for_both_blocked_targets_and_rejects_mutation(
    tmp_path: Path,
):
    free = load_manifest(V2_MANIFEST, "free")
    pro = load_manifest(V2_MANIFEST, "pro")
    assert free == pro
    assert len(free) == 6
    assert free[-1] == V2_MIGRATION

    for name, mutate in (
        ("order", lambda value: value["entries"].reverse()),
        ("checksum", lambda value: value["entries"][5].__setitem__("sha256", "0" * 64)),
        ("status", lambda value: value.__setitem__("status", "ready_for_free")),
        ("target", lambda value: value.__setitem__("blocked_targets", ["pro"])),
        ("extra", lambda value: value.__setitem__("unexpected", True)),
    ):
        candidate = _manifest(V2_MANIFEST)
        mutate(candidate)
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(ManifestError, match="exact contract"):
            load_manifest(path, "free", root=ROOT)


@pytest.mark.parametrize("prefix_size", [0, 3, 4, 5, 6])
def test_v2_planner_accepts_only_complete_boundaries(prefix_size: int):
    paths = load_manifest(V2_MANIFEST, "free")
    applied = {path.stem: _marker(path) for path in paths[:prefix_size]}
    database = _VerifierDatabase()

    assert db_migrate.validate_manifest_ledger_state(
        database, paths, applied
    ) == paths[prefix_size:]
    if prefix_size in {4, 5}:
        assert database.calls == []
    elif prefix_size in {3, 6}:
        assert database.calls


@pytest.mark.parametrize("prefix_size", [1, 2])
def test_v2_planner_rejects_unsafe_partial_boundaries(prefix_size: int):
    paths = load_manifest(V2_MANIFEST, "free")
    applied = {path.stem: _marker(path) for path in paths[:prefix_size]}
    with pytest.raises(RuntimeError, match="limites completos"):
        db_migrate.validate_manifest_ledger_state(
            _VerifierDatabase(), paths, applied
        )


def test_v2_package_has_six_atomic_entries_and_postconditions():
    paths = load_manifest(V2_MANIFEST, "free")
    package = db_migrate.build_manifest_package_sql(
        paths, version=20260726100500
    )
    assert package.count("-- manifest-entry") == 6
    assert package.count("DO $manifest_verify$") == 6
    assert package.count("INSERT INTO public.supabase_migrations") == 6
    assert "public.verify_fase09_5_policy_inventory_reconciliation()" in package
    assert package.index("-- final-package-postconditions") < package.index(
        "-- manifest-ledger-registration"
    )


def test_v2_migration_versions_only_the_closed_historical_policy_contract():
    sql = V2_MIGRATION.read_text(encoding="utf-8")
    validate_promotable_sql(sql, label=V2_MIGRATION.name)
    assert sql.count("CREATE POLICY ") == 4
    assert sql.count("AS PERMISSIVE") >= 4
    assert "ARRAY['canary_runner']::name[]" in sql
    assert "profiles_service_role" in sql
    assert ") <> 6 OR EXISTS (" in sql
    assert "ALTER SCHEMA public OWNER TO pg_database_owner" in sql
    assert "WHERE authenticator.rolname = 'authenticator'" in sql
    assert "NOT membership.inherit_option" in sql
    assert "verify_fase09_5_policy_inventory_reconciliation" in sql
    assert "SECURITY DEFINER" not in sql
    assert "auth.role()" not in sql

    fixture = (
        ROOT / "tests/sql/fase09_5_observed_policy_fixture.sql"
    ).read_text(encoding="utf-8")
    assert fixture.count("CREATE POLICY ") == 5
    assert fixture.count("\nTO canary_runner\nUSING") == 3
    assert "institutions_service_role" in fixture
    baseline = (
        ROOT / "tests/sql/fase09_5_v2_baseline_test.sql"
    ).read_text(encoding="utf-8")
    assert "count(*) = 22" in baseline
    assert "the frozen v1 verifier rejects" in baseline


def _directed_checks(
    *,
    evidence_overrides: dict[str, CheckEvidence] | None = None,
) -> list[DirectedCheck]:
    evidence_overrides = evidence_overrides or {}
    checks: list[DirectedCheck] = []
    for name in REQUIRED_CHECKS:
        if name == "target_binding":
            default_evidence = CheckEvidence(
                name=name, count=1, digest=TARGET_DIGEST
            )
        elif name == "ledger":
            default_evidence = CheckEvidence(
                name=name, count=0, digest=LEDGER_DIGESTS[0]
            )
        elif name == "h00":
            default_evidence = CheckEvidence(
                name=name, counts=tuple(H00_COUNTS.items())
            )
        else:
            default_evidence = CheckEvidence(
                name=name,
                count=EXPECTED_COUNTS[name],
                digest=EXPECTED_DIGESTS.get(name),
            )
        evidence = evidence_overrides.get(
            name,
            default_evidence,
        )
        checks.append(DirectedCheck(
            name=name,
            target="free",
            tool=CHECK_TOOLS[name],
            sql=CHECK_SQL.get(name),
            evidence=evidence,
        ))
    return checks


def test_preflight_aggregates_technical_mismatches_and_emits_once():
    emissions: list[dict[str, object]] = []

    outcome = run_directed_inventory(
        _directed_checks(evidence_overrides={
            "ledger": CheckEvidence(
                name="ledger", count=1, digest="b" * 64
            ),
            "policies": CheckEvidence(
                name="policies", count=21, digest="c" * 64
            ),
        }),
        TARGET_DIGEST,
        emissions.append,
    )
    assert emissions == [outcome]
    assert outcome["result"] == "FREE_PREFLIGHT_FAIL"
    assert len(outcome["checks"]) == len(REQUIRED_CHECKS)


@pytest.mark.parametrize("mutation", ["empty", "partial", "reordered", "duplicate"])
def test_preflight_rejects_incomplete_or_noncanonical_inventory(mutation: str):
    checks = _directed_checks()
    if mutation == "empty":
        checks = []
    elif mutation == "partial":
        checks = checks[:-1]
    elif mutation == "reordered":
        checks[0], checks[1] = checks[1], checks[0]
    else:
        checks[-1] = checks[-2]
    emissions: list[dict[str, object]] = []
    outcome = run_directed_inventory(checks, TARGET_DIGEST, emissions.append)
    assert emissions == [outcome]
    assert outcome == {"result": "FREE_PREFLIGHT_FAIL", "checks": []}


def test_preflight_rejects_empty_pass_evidence():
    emissions: list[dict[str, object]] = []
    checks = _directed_checks(evidence_overrides={
        "policies": CheckEvidence(name="policies")
    })
    outcome = run_directed_inventory(
        checks,
        TARGET_DIGEST,
        emissions.append,
    )
    assert emissions == [outcome]
    assert outcome["result"] == "FREE_PREFLIGHT_FAIL"
    assert outcome["fatal"] == "pii_detected"


def test_preflight_enforces_snapshot_consistent_h00_counts_only():
    invalid_counts = dict(H00_COUNTS)
    invalid_counts["leads_total"] = 2
    outcome = run_directed_inventory(
        _directed_checks(
            evidence_overrides={
                "h00": CheckEvidence(
                    name="h00", counts=tuple(invalid_counts.items())
                ),
            },
        ),
        TARGET_DIGEST,
        lambda _result: None,
    )
    assert outcome["result"] == "FREE_PREFLIGHT_FAIL"
    h00 = next(item for item in outcome["checks"] if item["name"] == "h00")
    assert h00 == {
        "name": "h00",
        "status": "FAIL",
        "counts": invalid_counts,
    }


def test_preflight_derives_fail_from_zero_or_fabricated_technical_evidence():
    checks = _directed_checks(evidence_overrides={
        "columns": CheckEvidence(name="columns", count=0, digest="0" * 64),
        "acl": CheckEvidence(name="acl", count=0, digest="0" * 64),
    })
    outcome = run_directed_inventory(
        checks, TARGET_DIGEST, lambda _result: None
    )
    assert outcome["result"] == "FREE_PREFLIGHT_FAIL"
    assert [
        item["status"]
        for item in outcome["checks"]
        if item["name"] in {"columns", "acl"}
    ] == ["FAIL", "FAIL"]


def test_preflight_ledger_digest_binds_names_and_checksums():
    paths = load_manifest(V2_MANIFEST, "free")
    wrong_entries = [(path.stem, _marker(path)) for path in paths[:3]]
    wrong_entries[0] = (wrong_entries[1][0], wrong_entries[0][1])
    wrong_digest = hashlib.sha256(json.dumps(
        wrong_entries,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")).hexdigest()
    outcome = run_directed_inventory(
        _directed_checks(evidence_overrides={
            "ledger": CheckEvidence(
                name="ledger", count=3, digest=wrong_digest
            )
        }),
        TARGET_DIGEST,
        lambda _result: None,
    )
    ledger = next(item for item in outcome["checks"] if item["name"] == "ledger")
    assert ledger["status"] == "FAIL"


@pytest.mark.parametrize(
    "reason,mutation",
    [
        ("ambiguous_target", {"target": "pro"}),
        (
            "pii_detected",
            {
                "evidence": CheckEvidence(
                    name="unexpected_identity", count=22, digest="d" * 64
                )
            },
        ),
        ("prohibited_tool", {"tool": "get_logs"}),
        ("write_detected", {"sql": "DELETE FROM public.leads"}),
    ],
)
def test_preflight_fatal_conditions_stop_immediately(reason: str, mutation: dict):
    emissions: list[dict[str, object]] = []
    fatal_name = "policies"
    checks = _directed_checks()
    index = REQUIRED_CHECKS.index(fatal_name)
    checks[index] = replace(checks[index], **mutation)
    outcome = run_directed_inventory(
        checks, TARGET_DIGEST, emissions.append
    )
    assert emissions == [outcome]
    assert outcome["result"] == "FREE_PREFLIGHT_FAIL"
    assert outcome["fatal"] == reason


def test_preflight_guards_accept_only_the_reviewed_read_only_surface():
    require_free_target("free", TARGET_DIGEST, TARGET_DIGEST)
    require_allowed_tool("target_binding", "get_project_url")
    require_allowed_tool("package", "list_migrations")
    require_allowed_tool("policies", "execute_sql")
    require_read_only_sql("target_binding", "get_project_url", None)
    require_read_only_sql("policies", "execute_sql", CHECK_SQL["policies"])
    for statement in (
        "SELECT public.exec_sql('DROP TABLE public.leads')",
        "SELECT pg_catalog.setval('public.some_sequence', 1)",
        "SELECT email FROM public.leads",
        "SELECT * FROM auth.users",
        "SELECT 1; DELETE FROM public.leads",
        "DO $$ BEGIN NULL; END $$",
    ):
        with pytest.raises(RuntimeError, match="write_detected"):
            require_read_only_sql("policies", "execute_sql", statement)


def test_preflight_binds_target_and_uses_aggregate_complete_catalog_queries():
    with pytest.raises(RuntimeError, match="ambiguous_target"):
        require_free_target("free", "b" * 64, TARGET_DIGEST)

    for name in (
        "columns", "constraints", "indexes", "rls", "policies", "roles",
        "acl", "rpc",
    ):
        assert "sha256" in CHECK_SQL[name]
        assert "jsonb_agg" in CHECK_SQL[name]
    assert "pg_auth_members" in CHECK_SQL["roles"]
    assert "'anon','authenticated','authenticator'" in CHECK_SQL["roles"]
    assert "schema_owner" in CHECK_SQL["acl"]
    assert "pg_namespace" in CHECK_SQL["acl"]
    assert "pg_attribute" in CHECK_SQL["acl"]
    assert "pg_proc" in CHECK_SQL["acl"]
    assert "proacl" in CHECK_SQL["rpc"]
    assert "pg_get_function_identity_arguments" in CHECK_SQL["rpc"]
    assert all(field in CHECK_SQL["h00"] for field in H00_COUNTS)


def test_retry_prompt_preserves_the_exact_decimal_gate_phrase():
    preflight = (
        ROOT / ".context/operaciones/preflight_free_f9_5.md"
    ).read_text(encoding="utf-8")
    exact_block = "```text\nEjecuta las tareas pendientes de la Fase F9.5\n\n"
    assert exact_block in preflight
    assert "Ejecuta las tareas pendientes de la Fase F9.5.\n" not in preflight
