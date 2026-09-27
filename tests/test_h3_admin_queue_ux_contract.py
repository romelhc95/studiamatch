from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_queue_ux_migration_preserves_legacy_and_adds_server_side_facets() -> None:
    source = read("db/migrations/20260927_h3_admin_queue_facets_filter.sql")

    assert "admin_get_course_queue_filtered" in source
    assert "admin_count_course_queue_filtered" in source
    assert "admin_get_course_queue_facets" in source
    assert "p_institution_slug" in source
    assert "admin_get_course_queue(" not in source
    assert "DROP FUNCTION" not in source
    assert "GRANT EXECUTE ON FUNCTION public.admin_get_course_queue_facets() TO authenticated, service_role" in source
    assert "REVOKE ALL ON FUNCTION public.admin_get_course_queue_facets() FROM PUBLIC, anon" in source


def test_queue_ux_migration_keeps_auth_and_editor_gates() -> None:
    source = read("db/migrations/20260927_h3_admin_queue_facets_filter.sql")

    assert source.count("PERFORM public.admin_require_aal2();") == 3
    assert source.count("public.admin_is_active_editor()") == 3
    assert "p_first < 1 OR p_first > 100" in source
    assert "Invalid editorial status" in source
    assert "Invalid quality status" in source


def test_queue_ui_explains_statuses_and_uses_catalogued_institution_filter() -> None:
    source = read("web/src/components/AdminCourseQueue.tsx")

    for label in ("Entender estados", "Estado editorial", "Estado de calidad", "Institución", "Buscar curso"):
        assert label in source
    assert "admin_get_course_queue_filtered" in source
    assert "admin_count_course_queue_filtered" in source
    assert "admin_get_course_queue_facets" in source
    assert "p_institution_slug" in source
    assert "institutions.map" in source


def test_editorial_preview_uses_public_renderer_and_live_field_impact() -> None:
    preview = read("web/src/components/admin/CourseLivePreview.tsx")
    renderer = read("web/src/components/courses/CoursePublicRenderer.tsx")
    public_detail = read("web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx")
    editor = read("web/src/app/admin/edit/page.tsx")

    assert "CoursePublicRenderer" in preview
    assert "CoursePublicRenderer" in public_detail
    assert "preview-impact-${activeField}" in renderer
    assert "Actualización en vivo" in preview
    assert "Ver impacto" in editor
    assert "setActivePreviewField(fieldKey)" in editor
    assert "scrollIntoView({ behavior: 'smooth', block: 'center' })" in editor
    assert "Cambios sin guardar" in editor
