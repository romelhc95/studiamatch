from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql"
ROLLBACK = ROOT / "db/rollbacks/20260811_fase10_10_m3_free_reader_compensating.sql"
RUNNER = ROOT / "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh"
PROJECTION = ROOT / "scripts/maintenance/f10_10_m3_apply_projection.py"
WORKFLOW = ROOT / ".github/workflows/f9-7-contract.yml"
DB_SYNC_WORKFLOW = ROOT / ".github/workflows/db-sync-to-pro.yml"


def test_free_only_package_is_outside_pro_migration_glob() -> None:
    db_migrate = (ROOT / "scripts/maintenance/db_migrate.py").read_text(encoding="utf-8")
    db_sync = DB_SYNC_WORKFLOW.read_text(encoding="utf-8")

    assert MIGRATION.is_file()
    assert MIGRATION.parent.name == "free_only_migrations"
    assert '"db", "migrations"' in db_migrate
    assert "free_only_migrations" not in db_migrate
    assert not (ROOT / "db/migrations" / MIGRATION.name).exists()
    assert (
        "':(exclude)db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql'"
        in db_sync
    )
    assert (
        "':(exclude)db/rollbacks/20260811_fase10_10_m3_free_reader_compensating.sql'"
        in db_sync
    )


def test_provisioning_package_contains_no_password_or_remote_operation() -> None:
    migration = MIGRATION.read_text(encoding="utf-8")
    rollback = ROLLBACK.read_text(encoding="utf-8")
    combined = migration + rollback

    assert "PASSWORD NULL" in migration
    assert "studiamatch_m3_reader" in combined
    assert "BYPASSRLS" in migration
    assert "SELECT (id, is_active, syllabus, objectives)" in migration
    assert not re.search(r"PASSWORD\s+'[^']+'", combined, re.IGNORECASE)
    assert not re.search(r"\b(?:INSERT|UPDATE|DELETE)\s+(?:INTO|public\.)", combined, re.IGNORECASE)
    assert "http://" not in combined and "https://" not in combined


def test_package_matches_nullable_courses_schema_contract() -> None:
    migration = MIGRATION.read_text(encoding="utf-8")

    assert "('id', 'uuid'::pg_catalog.regtype, true)" in migration
    assert "('is_active', 'boolean'::pg_catalog.regtype, false)" in migration
    assert "('syllabus', 'text'::pg_catalog.regtype, false)" in migration
    assert "('objectives', 'text'::pg_catalog.regtype, false)" in migration


def test_compensation_quarantines_before_revoking_or_dropping() -> None:
    rollback = ROLLBACK.read_text(encoding="utf-8")

    quarantine = rollback.index("NOLOGIN NOBYPASSRLS PASSWORD NULL")
    revoke = rollback.index("REVOKE CONNECT")
    drop = rollback.index("DROP ROLE studiamatch_m3_reader")
    assert quarantine < revoke < drop
    assert "DROP OWNED" not in rollback
    assert "REASSIGN OWNED" not in rollback


def test_ci_runs_package_on_networkless_postgresql_17() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    startup = workflow.split("- name: Start M3 reader networkless PostgreSQL 17", 1)[1].split(
        "- name: Run M3 reader PostgreSQL 17 contract", 1
    )[0]
    cleanup = workflow.split("- name: Remove M3 reader local database", 1)[1].split(
        "- name: Restore M3 external egress", 1
    )[0]

    assert "--network none" in workflow
    assert workflow.index("docker pull") < workflow.index("Block M3 external egress")
    assert "docker run --detach --pull never" in workflow
    assert "PostgreSQL init process complete; ready for start up." in workflow
    assert 'test -S "$F1010_M3_READER_SOCKET/.s.PGSQL.5432"' in workflow
    assert "timeout-minutes: 10" in workflow
    assert "{{.State.Running}}" in workflow
    assert "final_ready=0" in startup
    assert "for _ in $(seq 1 60)" in startup
    assert 'if [ "$final_ready" -ne 1 ]' in startup
    assert "stable_probes=0" in startup
    assert "for _ in $(seq 1 15)" in startup
    assert "stable_probes=$((stable_probes + 1))" in startup
    assert "stable_probes=0" in startup
    assert 'if [ "$stable_probes" -ne 3 ]' in startup
    assert startup.count("docker logs studiamatch-m3-reader-postgres") == 4
    assert "pg_isready" not in startup.split("init_complete=0", 1)[1].split(
        'if [ "$init_complete" -ne 1 ]', 1
    )[0]
    assert 'state_dir="${F1010_M3_READER_STATE:-}"' in cleanup
    assert 'sudo rm -rf -- "$state_dir"' in cleanup
    assert "postgres:17-alpine@sha256:742f40" in workflow
    assert "run_fase10_10_m3_free_reader_postgres17.sh" in workflow
    assert "F10_10_M3_READER_LOCAL_POSTGRES17_ONLY" in workflow
    assert "TEST_DATABASE_URL must exactly equal" in runner
    assert "refusing non-local/non-PostgreSQL-17 target" in runner
    assert PROJECTION.is_file()
    assert "f10_10_m3_apply_projection.py" in workflow
