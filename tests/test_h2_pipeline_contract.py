from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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


def test_sync_vector_never_publishes_with_legacy_course_flags() -> None:
    text = read("scripts/core/sync_vector_worker.py")

    assert '"is_active": False' in text
    assert '"is_verified": False' in text
    assert '"is_active": course_is_active' not in text
    assert "h2_update_course_quality" in text
    assert "compute_editorial_state" in text
    assert "editorial_status" not in text.split("h2_update_course_quality", 1)[1].split("})", 1)[0]
