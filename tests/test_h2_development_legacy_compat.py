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
COURSE_DETAIL = ROOT / "web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx"
COMPARE_CONTENT = ROOT / "web/src/app/compare/CompareContent.tsx"
REDIRECTS_FILE = ROOT / "web/public/_redirects"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_h2_development_compatibility_closes_hito_acceptance_criteria() -> None:
    text = read(EVIDENCE)

    assert "Estado: `CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED`" in text
    assert "`H2-CA2` Modelo editorial separado | `GO`" in text
    assert "`H2-CA3` Pipeline tolerante a incompletos | `GO`" in text
    assert "Compatibilidad funcional Desarrollo local/mock | `GO`" in text
    assert "Compatibilidad funcional Desarrollo remoto | `GO_AFTER_FREE_MIGRATION`" in text
    assert "Privacidad de datos editoriales | `GO`" in text
    assert "Transparencia para futuro main | `NO_GO_UNTIL_PRO_EXPAND_COMPAT_VERIFIED`" in text


def test_h2_development_compatibility_does_not_overstate_required_pillars() -> None:
    text = read(EVIDENCE)

    for pillar in ["Escalabilidad", "Seguridad", "Mantenimiento", "Rendimiento"]:
        assert f"| {pillar} | `GO` |" in text

    assert "| Funcionalidad | `GO_AFTER_FREE_MIGRATION` |" in text
    assert "| Calidad | `GO` |" in text
    assert "Desarrollo remoto muestra `227` programas" in text
    assert "llamadas legacy `ratings`/`reviews` retiradas" in text
    assert "No hay fallback frontend a `courses`" in text


def test_h2_quality_gate_removes_broken_detail_rewrites() -> None:
    if not REDIRECTS_FILE.exists():
        return

    redirects = read(REDIRECTS_FILE)
    assert "/courses/:institution/:slug/ /courses/ 200" not in redirects
    assert "/courses/:institution/:slug /courses/ 200" not in redirects


def test_h2_quality_gate_allows_redirect_cleanup_in_protected_paths() -> None:
    workflow = read(ROOT / ".github/workflows/security-audit.yml")

    assert "public/_redirects" in workflow
    assert "src/(lib/" in workflow


def test_h2_quality_gate_removes_public_social_proof_calls() -> None:
    for path in FRONTEND_FILES:
        text = read(path)
        assert "/rest/v1/ratings" not in text
        assert "/rest/v1/reviews" not in text

    detail = read(COURSE_DETAIL)
    for removed_ui in ["PUBLICAR RESEÑA", "Reseñas Verificadas", "Aún no hay calificaciones", "Deja tu opinión"]:
        assert removed_ui not in detail


def test_h2_quality_gate_related_courses_stay_on_valid_static_route_shape() -> None:
    detail = read(COURSE_DETAIL)

    assert "institution_id=eq.${safeInstitutionId}" in detail
    assert "category_id=eq.${safeCatId}" in detail
    assert "institution_slug: course.institution_slug" in detail
    assert "fetchRelatedCourses" in detail


def test_h2_quality_gate_compare_does_not_fabricate_unknown_values() -> None:
    compare = read(COMPARE_CONTENT)

    assert "|| 4500" not in compare
    assert '"4,500"' not in compare
    assert '"12.0"' not in compare
    assert '"Gratis"' not in compare
    assert "No disponible" in compare
    assert "investment && salary ? investment / salary : null" in compare


def test_h2_development_readonly_preflight_records_remote_delta() -> None:
    text = read(EVIDENCE)

    assert "## Preflight Read-Only Free 2026-08-26" in text
    assert "Legacy visible elegible | `227` cursos" in text
    assert "H2 estricto visible | `0` cursos" in text
    assert "Vista efectiva actual | `0` cursos" in text
    assert "`227` cursos legacy faltan" in text
    assert "ordered IDs md5 `b2a88ca4af2075f9796365acec1904c8`" in text
    assert "Post-Apply Free 2026-08-26" in text
    assert "Cohorte legacy | `227` cursos" in text
    assert "Vista efectiva actual | `227` cursos" in text
    assert "Missing legacy IDs | `0`" in text
    assert "Unexpected effective IDs | `0`" in text
    assert "PR #466 y PR #467 ya fueron aprobados" in text


def test_h2_quality_gate_records_remote_preview_verification() -> None:
    text = read(EVIDENCE)

    assert "## Validacion Remota Calidad 2026-08-26" in text
    assert "be52f883" in text
    assert "studiamatch-aty.pages.dev" in text
    assert "sin React #418" in text
    assert "Bundle publicado | `PASS`" in text
    assert "Relacionados | `PASS`" in text


def test_h2_development_compatibility_documents_transparent_transition() -> None:
    text = read(EVIDENCE)

    assert "## Transicion Transparente" in text
    for phase in ["`expand`", "`compatibilidad`", "`deploy`", "`contract`", "Rollback", "No degradacion funcional"]:
        assert phase in text
    assert "Retirar la cohorte legacy" in text
    assert "courses_public_effective=0` era `NO-GO`" in text
    assert "post-apply Free queda `227`" in text


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
