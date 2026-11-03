from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql"
ORIGINAL = ROOT / "db/migrations/20261028_h3_editorial_publication_snapshot.sql"
HARNESS = ROOT / "tests/h3_public_price_projection_pg17.sh"


def test_public_price_guard_is_forward_only_and_fails_closed_on_drift() -> None:
    migration = MIGRATION.read_text(encoding="utf-8")
    original = ORIGINAL.read_text(encoding="utf-8")

    assert "pg_get_functiondef" in migration
    assert "private.h2_public_courses_effective()" in migration
    assert "expected one known cast" in migration
    assert "IF _occurrences <> 1" in migration
    assert "NULLIF(BTRIM(c.published_editorial_values ->> 'price_pen'), '') ~ '^[0-9]{1,63}(\\.[0-9]{1,63})?$'" in migration
    assert "ELSE NULL" in migration
    assert "REVOKE ALL ON FUNCTION private.h2_public_courses_effective()" in migration
    assert "GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role" in migration
    assert "INSERT INTO public.courses" not in migration
    assert "UPDATE public.courses" not in migration
    assert "DELETE FROM public.courses" not in migration
    assert original.count("(c.published_editorial_values ->> 'price_pen')::NUMERIC") == 1
    assert "IF pg_catalog.strpos(_definition, _safe_cast) > 0 THEN" in migration
    assert HARNESS.is_file()
