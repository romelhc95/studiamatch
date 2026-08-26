from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / ".context/operaciones/h2_development_legacy_compat_evidence.md"
MIGRATION = ROOT / "db/migrations/20260826_h2_development_legacy_public_compat.sql"
FRONTEND_FILES = [
    ROOT / "web/src/app/page.tsx",
    ROOT / "web/src/app/HomeContent.tsx",
    ROOT / "web/src/app/compare/CompareContent.tsx",
    ROOT / "web/src/app/courses/[institution]/[slug]/page.tsx",
    ROOT / "web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_h2_development_compatibility_closes_hito_acceptance_criteria() -> None:
    text = read(EVIDENCE)

    assert "Estado: `PREPARED_FOR_FREE_DEVELOPMENT_JIT`" in text
    assert "`H2-CA2` Modelo editorial separado | `GO`" in text
    assert "`H2-CA3` Pipeline tolerante a incompletos | `GO`" in text
    assert "Compatibilidad funcional Desarrollo | `GO`" in text
    assert "Privacidad de datos editoriales | `GO`" in text
    assert "Transparencia para futuro main | `GO_CONDICIONADO`" in text


def test_h2_development_compatibility_approves_required_pillars() -> None:
    text = read(EVIDENCE)

    for pillar in ["Funcionalidad", "Escalabilidad", "Seguridad", "Mantenimiento", "Calidad", "Rendimiento"]:
        assert f"| {pillar} | `GO` |" in text

    assert "web no queda vacia" in text
    assert "No hay fallback frontend a `courses`" in text


def test_h2_development_compatibility_documents_transparent_transition() -> None:
    text = read(EVIDENCE)

    assert "## Transicion Transparente" in text
    for phase in ["`expand`", "`compatibilidad`", "`deploy`", "`contract`", "Rollback", "No degradacion funcional"]:
        assert phase in text
    assert "Retirar la cohorte legacy" in text
    assert "courses_public_effective=0` es `NO-GO`" in text


def test_h2_legacy_cohort_is_private_and_conditioned_to_business_visible_courses() -> None:
    text = read(MIGRATION)

    assert "private.h2_legacy_public_course_cohort" in text
    assert "REVOKE ALL ON TABLE private.h2_legacy_public_course_cohort FROM PUBLIC, anon, authenticated, service_role" in text
    assert "c.is_active = true" in text
    assert "c.is_verified = true" in text
    assert "p.production_enabled = true" in text
    assert "ON CONFLICT (course_id) DO NOTHING" in text


def test_h2_frontend_keeps_single_public_read_surface() -> None:
    for path in FRONTEND_FILES:
        text = read(path)
        assert "courses_public_effective" in text, f"{path} must read the H2 public view"
        assert "/rest/v1/courses?" not in text, f"{path} must not fallback to direct courses reads"


def test_h2_compatibility_evidence_does_not_authorize_production_actions() -> None:
    text = read(EVIDENCE)

    assert "No autoriza Supabase Pro" in text
    assert "merge a `main`" in text
    assert "JIT separada" in text
