from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.maintenance import db_migrate
from scripts.maintenance.migration_manifest import (
    MIGRATION_FILENAME_RE,
    ManifestError,
    canonical_sql_sha256,
    load_manifest,
    validate_promotable_sql,
)


ROOT = Path(__file__).resolve().parents[1]
F6_MANIFEST = ROOT / "db/manifests/fase06_promotable.json"
F8_MANIFEST = ROOT / "db/manifests/fase08_candidate.json"
F8_MIGRATION = (
    ROOT / "db/migrations/20260725_fase08_hito1_functional_closure.sql"
)


def _marker(path: Path) -> str:
    return f"sha256:{canonical_sql_sha256(path)}"


def test_fase08_candidate_is_blocked_exact_overlay():
    f6 = json.loads(F6_MANIFEST.read_text(encoding="utf-8"))
    f8 = json.loads(F8_MANIFEST.read_text(encoding="utf-8"))

    assert f8["status"] == "reconciled_not_certified"
    assert f8["blocked_targets"] == ["free", "pro"]
    assert f8["entries"][:3] == f6["entries"]
    assert f8["excluded"]["H-00"] == "historical_free_only"
    assert [entry["component"] for entry in f8["entries"]] == [
        "g1b",
        "hito1",
        "g1b_closure",
        "hito1_functional_closure",
    ]
    assert f8["entries"][-1]["path"] == F8_MIGRATION.relative_to(
        ROOT
    ).as_posix()
    assert f8["entries"][-1]["sha256"] == canonical_sql_sha256(F8_MIGRATION)

    free_paths = load_manifest(F8_MANIFEST, "free")
    assert free_paths == load_manifest(F8_MANIFEST, "pro")
    assert free_paths[-1] == F8_MIGRATION
    with pytest.raises(ManifestError, match="required ready_for_free"):
        load_manifest(F8_MANIFEST, "free", required_status="ready_for_free")
    with pytest.raises(ManifestError, match="required free_certified"):
        load_manifest(F8_MANIFEST, "pro", required_status="free_certified")


def test_fase08_manifest_rejects_order_prefix_and_invalid_target_transition(
    tmp_path: Path,
):
    manifest = json.loads(F8_MANIFEST.read_text(encoding="utf-8"))
    manifest["entries"][2], manifest["entries"][3] = (
        manifest["entries"][3],
        manifest["entries"][2],
    )
    reordered = tmp_path / "reordered.json"
    reordered.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ManifestError, match="exactly and in order"):
        load_manifest(reordered, "free")

    manifest = json.loads(F8_MANIFEST.read_text(encoding="utf-8"))
    manifest["blocked_targets"] = ["free"]
    unblocked = tmp_path / "unblocked.json"
    unblocked.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ManifestError, match="target blocks"):
        load_manifest(unblocked, "free")

    manifest = json.loads(F8_MANIFEST.read_text(encoding="utf-8"))
    manifest["entries"][-1]["path"] = (
        "db/migrations/20260725_fase07_g1b_closure.sql"
    )
    wrong_prefix = tmp_path / "wrong-prefix.json"
    wrong_prefix.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ManifestError, match="wrong phase prefix"):
        load_manifest(wrong_prefix, "free")

    manifest = json.loads(F8_MANIFEST.read_text(encoding="utf-8"))
    manifest["status"] = "ready_for_free"
    status_only = tmp_path / "status-only.json"
    status_only.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ManifestError, match="target blocks"):
        load_manifest(
            status_only, "free", required_status="ready_for_free"
        )

    manifest["blocked_targets"] = ["pro"]
    status_only = tmp_path / "ready.json"
    status_only.write_text(json.dumps(manifest), encoding="utf-8")
    assert load_manifest(
        status_only, "free", required_status="ready_for_free"
    )
    with pytest.raises(ManifestError, match="required free_certified"):
        load_manifest(status_only, "pro", required_status="free_certified")


def test_manifest_rejects_unsafe_migration_filename():
    assert MIGRATION_FILENAME_RE.fullmatch(
        "20260725_fase08_hito1_functional_closure.sql"
    )
    assert not MIGRATION_FILENAME_RE.fullmatch(
        "20260725_fase08_comment\nDROP_TABLE.sql"
    )
    assert not MIGRATION_FILENAME_RE.fullmatch(
        "20260725_fase08_bad-name.sql"
    )


def test_fase08_migration_contract_is_forward_only_and_strong():
    sql = F8_MIGRATION.read_text(encoding="utf-8")
    validate_promotable_sql(sql, label=F8_MIGRATION.name)

    assert "SET search_path = '';" in sql
    assert "SECURITY INVOKER" in sql
    assert "SECURITY DEFINER" in sql
    assert "metadata = EXCLUDED.metadata" in sql
    assert "brochure_url = EXCLUDED.brochure_url" in sql
    assert "verify_fase07_g1b_closure" in sql
    assert "relation.relrowsecurity" in sql
    assert "policy.permissive = 'PERMISSIVE'" in sql
    assert "constraint_record.convalidated" in sql
    assert "index_record.indisvalid" in sql
    assert "has_column_privilege" in sql
    assert "verify_fase08_hito1_contract" in sql
    assert "auth.role()" not in sql

    course_grant = sql.split("GRANT SELECT (", 1)[1].split(
        ") ON TABLE public.courses TO anon, authenticated;", 1
    )[0]
    assert "view_count" not in course_grant
    assert "comparison_count" not in course_grant
    assert "publication_status" in course_grant
    assert "brochure_url" in course_grant


def test_validate_only_never_requires_remote_credentials():
    clean_env = {
        key: value
        for key, value in os.environ.items()
        if "SUPABASE" not in key.upper()
    }
    result = subprocess.run(
        [
            sys.executable,
            "scripts/maintenance/db_migrate.py",
            "--env",
            "free",
            "--manifest",
            str(F8_MANIFEST),
            "--validate-only",
        ],
        cwd=ROOT,
        env=clean_env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "sin acceso remoto" in result.stdout
    assert "Faltan credenciales" not in result.stdout + result.stderr


def test_dry_run_keeps_remote_pending_detection_contract():
    source = (ROOT / "scripts/maintenance/db_migrate.py").read_text(
        encoding="utf-8"
    )
    workflow = (ROOT / ".github/workflows/db-sync-to-pro.yml").read_text(
        encoding="utf-8"
    )

    assert "offline_only = args.validate_only" in source
    assert "PENDIENTE (dry-run, no se ejecuta)" in source
    assert 'grep -c "PENDIENTE"' in workflow


def test_manifest_package_is_one_atomic_privileged_payload(monkeypatch):
    paths = load_manifest(F8_MANIFEST, "free")
    captured: list[str] = []

    class Database:
        def rpc(self, *args, **kwargs):
            return {"status": "success"}

    def fake_exec(db, sql, max_retries=2):
        captured.append(sql)
        return {"status": "success"}

    monkeypatch.setattr(db_migrate, "_exec_sql_with_retry", fake_exec)
    monkeypatch.setattr(
        db_migrate,
        "get_applied_migrations",
        lambda db: {path.stem: _marker(path) for path in paths},
    )

    assert db_migrate.apply_manifest_package(Database(), paths)
    assert len(captured) == 1
    package = captured[0]
    assert package.count("LOCK TABLE public.supabase_migrations") == 1
    assert package.count("-- manifest-entry") == 4
    assert package.count("INSERT INTO public.supabase_migrations") == 4
    assert "ON CONFLICT (name) DO NOTHING" not in package
    assert "Manifest entries changed after planning" in package
    for path in paths:
        name = path.stem
        verifier = db_migrate.PACKAGE_POSTCONDITIONS[name]
        registration = f"'{name}', 'sha256:"
        assert verifier in package
        assert registration in package
        assert package.index(verifier) < package.index(registration)


def test_manifest_ledger_state_allows_prefix_and_fails_on_gap():
    paths = load_manifest(F8_MANIFEST, "free")

    class Database:
        def __init__(self):
            self.verifiers: list[str] = []

        def rpc_raise(self, name, params):
            self.verifiers.append(name)
            return True

    database = Database()
    prefix = {path.stem: _marker(path) for path in paths[:3]}
    assert db_migrate.validate_manifest_ledger_state(
        database, paths, prefix
    ) == [paths[3]]
    assert database.verifiers == [
        "verify_fase06_g1b_reconciliation",
        "verify_fase06_hito1_contract",
        "verify_fase07_g1b_closure",
    ]

    gap = {
        paths[0].stem: _marker(paths[0]),
        paths[2].stem: _marker(paths[2]),
    }
    with pytest.raises(RuntimeError, match="Estado parcial inesperado"):
        db_migrate.validate_manifest_ledger_state(Database(), paths, gap)


def test_manifest_runner_is_idempotent_when_package_is_already_applied():
    paths = load_manifest(F8_MANIFEST, "free")
    applied = {path.stem: _marker(path) for path in paths}

    class Database:
        def __init__(self):
            self.verifiers: list[str] = []

        def rpc_raise(self, name, params):
            self.verifiers.append(name)
            return True

    database = Database()
    assert db_migrate.validate_manifest_ledger_state(
        database, paths, applied
    ) == []
    assert len(database.verifiers) == len(paths)


def test_fase08_has_postcondition_and_manifest_only_prefix():
    name = "20260725_fase08_hito1_functional_closure"
    assert db_migrate.PACKAGE_POSTCONDITIONS[name] == (
        "public.verify_fase08_hito1_contract()"
    )
    assert name.startswith(db_migrate.MANIFEST_ONLY_PREFIXES)


def test_target_parity_requires_fase08_checksum_and_verifier():
    parity = (ROOT / "scripts/maintenance/check_db_parity.py").read_text(
        encoding="utf-8"
    )

    assert '"20260725_fase08_hito1_functional_closure"' in parity
    assert '"verify_fase08_hito1_contract"' in parity
    assert '"name,statements"' in parity
    assert "canonical_sql_sha256" in parity
    assert "free_set - target_set" not in parity
    assert 'required_status="free_certified"' in parity


def test_security_audit_blocks_on_fase08_postgres_contract():
    workflow = (ROOT / ".github/workflows/security-audit.yml").read_text(
        encoding="utf-8"
    )

    assert "name: FASE-08 Hito 1 Functional Contract" in workflow
    assert "postgres:17-alpine" in workflow
    assert "bash tests/sql/run_fase08_postgres.sh" in workflow
    assert "F8: ${{ needs.fase08-hito1.result }}" in workflow
    assert "continue-on-error: true" not in workflow


def test_pro_workflow_uses_same_fase08_manifest_for_detect_and_apply():
    workflow = (ROOT / ".github/workflows/db-sync-to-pro.yml").read_text(
        encoding="utf-8"
    )

    assert "MIGRATION_MANIFEST: db/manifests/fase08_candidate.json" in workflow
    assert workflow.count('--manifest "$MIGRATION_MANIFEST"') == 2
    assert "fase06_promotable.json" not in workflow
