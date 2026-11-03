# StudIAMatch-Docs: .context/componentes/database_migrations.md#migration-20261102-h3-legacy-public-withdrawal
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "db/migrations/20261102_h3_legacy_public_withdrawal_guard.sql"
SNAPSHOT = ROOT / "db/migrations/20261028_h3_editorial_publication_snapshot.sql"
PRICE_GUARD = ROOT / "db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql"
HARNESS = ROOT / "tests/h3_legacy_public_withdrawal_pg17.sh"
SETUP = ROOT / "tests/sql/h3_legacy_public_withdrawal_pg17_setup.sql"
ASSERT = ROOT / "tests/sql/h3_legacy_public_withdrawal_pg17_assert.sql"
READER_VIEW = ROOT / "tests/sql/h3_legacy_public_withdrawal_pg17_reader_view.sql"
DOC_POINTER = "-- StudIAMatch-Docs: .context/componentes/database_migrations.md#migration-20261102-h3-legacy-public-withdrawal"


def test_sql_sources_keep_the_exact_registry_pointer() -> None:
    for source in (MIGRATION, SETUP, READER_VIEW, ASSERT):
        lines = source.read_text(encoding="utf-8").splitlines()[:3]
        assert DOC_POINTER in lines, f"{source.relative_to(ROOT)} must keep its registered source pointer"


def test_withdrawal_guard_filters_only_explicit_legacy_withdrawal_events() -> None:
    migration = MIGRATION.read_text(encoding="utf-8")

    assert "CREATE OR REPLACE VIEW private.h3_legacy_public_course_cohort" in migration
    assert "FROM private.h2_legacy_public_course_cohort AS cohort" in migration
    assert "NOT EXISTS" in migration
    assert "FROM public.course_editorial_audit AS editorial_event" in migration
    assert "editorial_event.action IN ('unpublish', 'archive')" in migration
    assert "SELECT NULL::UUID AS course_id WHERE false" in migration
    assert "REVOKE ALL ON TABLE private.h3_legacy_public_course_cohort" in migration
    assert "GRANT " not in migration
    assert not re.search(r"\b(?:INSERT|UPDATE|DELETE|TRUNCATE)\s+(?:INTO\s+|FROM\s+)?(?:public\.)?(?:courses|course_editorial_state|course_editorial_audit|h2_legacy_public_course_cohort)\b", migration, re.IGNORECASE)
    assert "DROP TABLE" not in migration.upper()
    assert "DROP VIEW" not in migration.upper()


def test_pg17_harness_uses_production_reader_and_covers_withdrawal_lifecycle() -> None:
    runner = HARNESS.read_text(encoding="utf-8")
    setup = SETUP.read_text(encoding="utf-8")
    assertions = ASSERT.read_text(encoding="utf-8")
    reader_view = READER_VIEW.read_text(encoding="utf-8")
    snapshot = SNAPSHOT.read_text(encoding="utf-8")
    price_guard = PRICE_GUARD.read_text(encoding="utf-8")

    assert re.search(r"CREATE OR REPLACE FUNCTION private\.h2_public_courses_effective\(\)", snapshot)
    assert "awk" in runner and r"private\.h2_public_courses_effective\(\)" in runner
    assert "readonly PRICE_GUARD=\"$ROOT/db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql\"" in runner
    snapshot_install = runner.index('"$SNAPSHOT" | docker exec')
    price_guard_install = runner.index('< "$PRICE_GUARD"')
    withdrawal_install = runner.index('< "$MIGRATION"')
    assert snapshot_install < price_guard_install < withdrawal_install
    assert "pg_get_functiondef" in price_guard and "EXECUTE pg_catalog.replace(_definition, _unsafe_cast, _safe_cast)" in price_guard
    assert '"price_pen":""' in setup
    assert "CREATE OR REPLACE VIEW public.courses_public_effective" in reader_view
    for case in (
        "untouched legacy course must remain visible",
        "published snapshot must remain visible",
        "explicit unpublish must withdraw a legacy course",
        "explicit archive must withdraw a legacy course",
        "republished course must use its approved snapshot",
        "course rows must be preserved",
    ):
        assert case in assertions
    assert "H2 cohort rows must be preserved" in assertions
    assert "append-only audit rows must be preserved" in assertions
    assert "explicit unpublish must withdraw a legacy course and prevent its legacy value from returning" in assertions
    assert "explicit archive must withdraw a legacy course and prevent its legacy value from returning" in assertions
    assert "republished course must use its approved snapshot" in assertions
    assert "CREATE TABLE public.course_editorial_audit" in setup
    assert "CREATE TABLE private.h2_legacy_public_course_cohort" in setup
    course_insert = re.search(r"INSERT INTO public\.courses \(id, institution_id, name, is_active, is_verified\)\s*VALUES(.*?);", setup, re.DOTALL)
    assert course_insert is not None
    fixture_rows = re.findall(r"\('[^']+',\s*'[^']+',\s*'[^']+',\s*(?:true|false),\s*(?:true|false)\)", course_insert.group(1), re.IGNORECASE)
    assert len(fixture_rows) == 4, "each courses fixture row must match all five inserted columns"
    assert "malformed published price must be projected as null" in assertions
    assert "has_function_privilege('anon', 'private.h2_public_courses_effective()', 'EXECUTE')" in assertions
    assert "has_table_privilege('anon', 'public.courses_public_effective', 'SELECT')" in assertions
