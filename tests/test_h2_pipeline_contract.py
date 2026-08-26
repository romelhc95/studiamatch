from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PUBLIC_SURFACE_FIELDS = {
    "editorial_status",
    "quality_status",
    "missing_fields",
    "field_sources",
    "field_timestamps",
    "is_sponsored",
    "lead_cta_enabled",
    "sponsored_priority",
    "sponsorship_label",
    "availability_status",
    "editorial_updated_at",
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cleansing_preserves_short_descriptions_for_editorial_review() -> None:
    text = read("scripts/core/cleansing_worker.py")

    assert 'return "description_too_short"' not in text
    assert 'return "name_too_short"' in text


def test_enrichment_does_not_fabricate_modality_or_duration() -> None:
    text = read("scripts/core/enrichment_worker.py")

    assert 'logger.warning(f"Unknown modality' in text
    assert 'enriched["modality"] = None' in text
    assert 'duration_text = None' in text
    assert 'modality = None' in text
    assert 'duration_text = "Consultar"' not in text
    assert 'modality = "Presencial"' not in text


def test_sync_vector_preserves_technical_visibility_flags_without_editorial_publication() -> None:
    text = read("scripts/core/sync_vector_worker.py")

    assert '"is_active": course_is_active' in text
    assert '"is_verified": is_real_enrichment' in text
    assert '"is_active": False' not in text
    assert '"is_verified": False' not in text
    assert "h2_update_course_quality" in text
    assert "compute_editorial_state" in text
    assert "canonical_quality_hash" in text
    assert "manual_overrides=existing_state.get('manual_overrides') or {}" in text
    assert "existing_course.get('is_active') is False" not in text
    assert "editorial_status" not in text.split("h2_update_course_quality", 1)[1].split("})", 1)[0]
    assert text.index("editorial_status') == 'archived'") < text.index("self.db.upsert('courses'")


def test_frontend_public_fields_do_not_select_private_editorial_state() -> None:
    text = read("web/src/lib/supabase.ts")
    fields = text.split("export const COURSE_PUBLIC_FIELDS = '", 1)[1].split("';", 1)[0].split(",")

    assert not (set(fields) & PRIVATE_PUBLIC_SURFACE_FIELDS)
