-- Migration: Fase 74 — Create + Seed institution_site_profiles in Pro
-- PREREQUISITE: Run this in Supabase Dashboard > SQL Editor for the PRODUCTION project
-- Includes: CREATE TABLE (if not exists) + RLS + indexes + 10 profile INSERTs
BEGIN;

-- ============================================================
-- STEP 1: Create table (if not exists)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.institution_site_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    institution_id UUID NOT NULL REFERENCES public.institutions(id) ON DELETE CASCADE UNIQUE,
    site_type TEXT NOT NULL DEFAULT 'traditional_ssr'
        CHECK (site_type IN ('traditional_ssr', 'ecommerce', 'spa_js_heavy', 'paginated_catalog', 'catalog_link_extraction', 'cloudflare_protected')),
    discovery_mode TEXT NOT NULL DEFAULT 'sitemap_bfs'
        CHECK (discovery_mode IN ('sitemap_bfs', 'hardcoded_urls', 'paginated_catalog', 'catalog_link_extraction')),
    seed_urls JSONB DEFAULT '[]'::JSONB,
    exclusion_patterns JSONB DEFAULT '[]'::JSONB,
    catalog_url_patterns JSONB DEFAULT '[]'::JSONB,
    catalog_link_selector TEXT,
    catalog_max_pages INT DEFAULT 5,
    catalog_scroll_iterations INT DEFAULT 0,
    requires_stealth BOOLEAN DEFAULT false,
    requires_cloudflare_bypass BOOLEAN DEFAULT false,
    warmup_url TEXT,
    popup_close_selectors JSONB DEFAULT '[]'::JSONB,
    detail_wait_ms INT DEFAULT 2000,
    section_keywords JSONB DEFAULT '{}'::JSONB,
    field_defaults JSONB DEFAULT '{}'::JSONB,
    section_mode_map JSONB DEFAULT '{}'::JSONB,
    section_course_type_map JSONB DEFAULT '{}'::JSONB,
    title_prefix_removals JSONB DEFAULT '[]'::JSONB,
    title_split_separators JSONB DEFAULT '[]'::JSONB,
    price_regex TEXT,
    duration_regex TEXT,
    max_courses_per_run INT DEFAULT 500,
    soft_delete_before_scrape BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- STEP 2: RLS + Index (idempotent — use IF NOT EXISTS where possible)
-- ============================================================
ALTER TABLE public.institution_site_profiles ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    -- Drop anon SELECT policy (security: profiles contain scraping strategy)
    IF EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'profiles_select_public' AND tablename = 'institution_site_profiles') THEN
        EXECUTE 'DROP POLICY IF EXISTS profiles_select_public ON public.institution_site_profiles';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'profiles_select_authenticated' AND tablename = 'institution_site_profiles') THEN
        EXECUTE 'CREATE POLICY profiles_select_authenticated ON public.institution_site_profiles FOR SELECT TO authenticated USING (true)';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'profiles_service_role' AND tablename = 'institution_site_profiles') THEN
        EXECUTE 'CREATE POLICY profiles_service_role ON public.institution_site_profiles FOR ALL TO service_role USING (true) WITH CHECK (true)';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_profiles_institution ON public.institution_site_profiles(institution_id);

-- ============================================================
-- STEP 3: Seed 10 institution profiles
-- ============================================================

-- Institution: universidad-de-lima (Universidad de Lima)
-- Exclusions: 146 (global + institutional)

INSERT INTO public.institution_site_profiles (
    institution_id, site_type, discovery_mode,
    seed_urls, exclusion_patterns, catalog_url_patterns,
    catalog_link_selector, catalog_max_pages, catalog_scroll_iterations,
    requires_stealth, requires_cloudflare_bypass, popup_close_selectors,
    detail_wait_ms, section_keywords, field_defaults,
    section_mode_map, section_course_type_map,
    title_prefix_removals, title_split_separators,
    max_courses_per_run, soft_delete_before_scrape, notes
) VALUES (
    '9ec85305-64a6-4ea0-9d0a-1828e7b477aa',
    'traditional_ssr',
    'hardcoded_urls',
    '[]'::jsonb,
    '[".7z", ".avi", ".bmp", ".css", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".js", ".json", ".mov", ".mp3", ".mp4", ".pdf", ".png", ".ppt", ".pptx", ".rar", ".svg", ".tar", ".webp", ".wmv", ".xls", ".xlsx", ".xml", ".zip", "/about/", "/admision", "/admision-internacional", "/admision/", "/admitidos-", "/agenda/", "/agradecimiento/", "/alumni", "/archive/", "/arquitectura-escalas-domesticas", "/assets/", "/athina-seminario", "/author/", "/baccaulerat", "/beca-ulima-", "/biblioteca", "/biblioteca/", "/blog-tags/", "/blog/", "/blogs", "/brochure-", "/campus", "/carrito/", "/categoria/", "/category/", "/centros-e-institutos/", "/colegios-seleccionados", "/congreso-mediacion", "/contabilidad-curso-actualizacion", "/contacto/", "/deportista-calificado", "/diomas/portugues", "/diploma-de-bachillerato", "/educacion-ejecutiva/derecho-y-gestion-publica", "/educacion-ejecutiva/executive-summit/", "/educacion-ejecutiva/finanzas-contabilidad-y-economia", "/educacion-ejecutiva/mooc/", "/en/", "/escolares", "/eventos/", "/examen-de-admision", "/faq/", "/feed/", "/fondo-editorial", "/foro-industrial-", "/gracias", "/graduados/torneo-", "/guia-", "/guia-del-postulante", "/guia-postulante-", "/ibo-", "/idiomas/demo-", "/idiomas/emi-skills", "/idiomas/ingles", "/img/", "/informacion-temario-examen", "/inicio", "/internacional", "/internacional/", "/inversion", "/investigacion/", "/la-universidad/", "/laboratorios", "/login", "/malla-", "/media/", "/node/", "/nosotros/", "/noticias", "/noticias/", "/open-registro", "/page/", "/pagina-de-prueba", "/pec-ventas-agradecimiento", "/podcast", "/politica/", "/posgrado/connect-ulima", "/posgrado/epg-agradecimiento", "/posgrado/sustentaciones-de-grado", "/pregrado/", "/prelima", "/primeros-puestos-en-secundaria", "/privacidad-de-datos", "/privacidad/", "/procesos-de-matricula", "/promociones", "/promociones/", "/publicaciones/", "/publico-objetivo/", "/register/", "/registro-completo", "/registro-exitoso", "/rendimiento-academico", "/requisitos-admision-", "/resultados-ec-", "/rss/", "/search/", "/servicios-inhouse", "/sistema-de-correo-electronico", "/solicitud-de-cambio-de-carrera", "/sostenibilidad/", "/static/", "/tag/", "/tags/", "/taxonomy/", "/terminos/", "/test-de-enlaces", "/thank-you-page/", "/transparencia/", "/traslado", "/ventana-indiscreta", "/ventana-indiscreta/", "/vida-ulima", "/vida-ulima/", "/wp-content/", "/wp-json/", "/xxxvi-edicion-de-la-escuela-complutense"]'::jsonb,
    '[]'::jsonb,
    NULL,
    5,
    0,
    FALSE,
    FALSE,
    '[]'::jsonb,
    3000,
    '{"Perfil del egresado": "graduate_profile", "Malla curricular": "curriculum_summary", "Plan de estudios": "curriculum_summary", "Requisitos": "requirements", "Dirigido a": "target_audience", "Inversion": "total_cost_est", "Inicio": "start_date", "Duracion": "duration_text"}'::jsonb,
    '{"mode": "Presencial"}'::jsonb,
    '{"/pregrado/": "Presencial", "/maestria/": "Presencial", "/doctorado/": "Presencial", "/idiomas/": "Presencial", "/cursos-talleres/": "Remoto"}'::jsonb,
    '{"/pregrado/": "Pregrado", "/maestria/": "Maestria", "/doctorado/": "Doctorado", "/idiomas/": "Curso", "/cursos-talleres/": "Curso"}'::jsonb,
    '["U. Lima | ", "Universidad de Lima | ", "ULIMA - "]'::jsonb,
    '[]'::jsonb,
    500,
    FALSE,
    '102 seed URLs curated. /pregrado/ exclusion removed (Fase 72) — 12 carreras enabled.'
)
ON CONFLICT (institution_id) DO UPDATE SET
    site_type = EXCLUDED.site_type,
    discovery_mode = EXCLUDED.discovery_mode,
    exclusion_patterns = EXCLUDED.exclusion_patterns,
    catalog_url_patterns = EXCLUDED.catalog_url_patterns,
    catalog_link_selector = EXCLUDED.catalog_link_selector,
    catalog_max_pages = EXCLUDED.catalog_max_pages,
    detail_wait_ms = EXCLUDED.detail_wait_ms,
    section_keywords = EXCLUDED.section_keywords,
    field_defaults = EXCLUDED.field_defaults,
    section_mode_map = EXCLUDED.section_mode_map,
    section_course_type_map = EXCLUDED.section_course_type_map,
    title_prefix_removals = EXCLUDED.title_prefix_removals,
    title_split_separators = EXCLUDED.title_split_separators,
    notes = EXCLUDED.notes,
    seed_urls = EXCLUDED.seed_urls,
    catalog_scroll_iterations = EXCLUDED.catalog_scroll_iterations,
    requires_stealth = EXCLUDED.requires_stealth,
    requires_cloudflare_bypass = EXCLUDED.requires_cloudflare_bypass,
    warmup_url = EXCLUDED.warmup_url,
    popup_close_selectors = EXCLUDED.popup_close_selectors,
    max_courses_per_run = EXCLUDED.max_courses_per_run,
    soft_delete_before_scrape = EXCLUDED.soft_delete_before_scrape,
    price_regex = EXCLUDED.price_regex,
    duration_regex = EXCLUDED.duration_regex,
    updated_at = now();

-- Institution: universidad-continental (Universidad Continental)
-- Exclusions: 141 (global + institutional)

INSERT INTO public.institution_site_profiles (
    institution_id, site_type, discovery_mode,
    seed_urls, exclusion_patterns, catalog_url_patterns,
    catalog_link_selector, catalog_max_pages, catalog_scroll_iterations,
    requires_stealth, requires_cloudflare_bypass, popup_close_selectors,
    detail_wait_ms, section_keywords, field_defaults,
    section_mode_map, section_course_type_map,
    title_prefix_removals, title_split_separators,
    max_courses_per_run, soft_delete_before_scrape, notes
) VALUES (
    '7dc17e61-b06f-4383-b076-6669be2f483c',
    'traditional_ssr',
    'sitemap_bfs',
    '[]'::jsonb,
    '[".7z", ".avi", ".bmp", ".css", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".js", ".json", ".mov", ".mp3", ".mp4", ".pdf", ".png", ".ppt", ".pptx", ".rar", ".svg", ".tar", ".webp", ".wmv", ".xls", ".xlsx", ".xml", ".zip", "/#new_tab", "/2014/", "/about/", "/accion-pastoral", "/admision/", "/agradecimiento/", "/archive/", "/assets/", "/author/", "/beca-18", "/beneficios-y-servicios", "/biblioteca/", "/bienestar-universitario", "/blog/", "/blogs", "/calidad-educativa", "/campus-", "/campus/", "/carrito/", "/categoria/", "/category/", "/centro-cultural", "/centro-de-investigacion-de-servicios-psicologicos", "/centro-psicologico", "/change", "/ciclo-verano-", "/colocacion-laboral", "/comunicados", "/conferencia-", "/conferencias/", "/contacto/", "/conti-tv", "/convocatorias-investigacion", "/dt_gallery_category", "/duplicado-home", "/entrevistas", "/especiales", "/estudios/", "/eventos/", "/faq/", "/feed/", "/galeria-de-eventos", "/grados-y-titulos", "/huancayo-examenes-parciales", "/i-congreso-civil", "/ii-evento-headhunters", "/img/", "/impactopositivo", "/informacion-institucional", "/inventado-peru-emprendimientos", "/investiga/", "/investigacion/", "/iv-seminario-de-psicologia", "/ixecc", "/la-formalizacion-empresarial", "/labbco", "/login", "/logros-uc", "/logros/", "/matricula", "/media/", "/medicina-genomica", "/medios", "/mkt", "/nosotros/", "/noticias/", "/nuestra-historia", "/nuestros-campus", "/nuevo-reglamento", "/nuevo/", "/oficina-de-consejeria-academica", "/oola-promperu", "/oportunidades-laborales", "/page/", "/plan-de-estudios", "/planeamiento-tributario", "/politica/", "/por-que-continental", "/portal-de-padres", "/portal-familia", "/privacidad/", "/programa-training", "/proyeccion-social", "/publicaciones/", "/razones", "/register/", "/revista-experiencias-magistrales", "/revistas-informativas-prosuc", "/revistas-prosuc-", "/rss/", "/search/", "/servicios/", "/sin-categoria", "/sostenibilidad/", "/static/", "/tag/", "/tags/", "/terminos-condiciones-", "/terminos/", "/testimonio-colegios", "/testimonios", "/thank-you-page/", "/transparencia/", "/uc-global/", "/vida-universitaria/", "/videos-conferencias-magistrales", "/videos/", "/viiecc", "/viiiecc", "/wp-content/", "/wp-json/", "/xecc"]'::jsonb,
    '[]'::jsonb,
    NULL,
    5,
    0,
    FALSE,
    FALSE,
    '[]'::jsonb,
    2000,
    '{}'::jsonb,
    '{"mode": "Presencial"}'::jsonb,
    '{}'::jsonb,
    '{}'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb,
    500,
    FALSE,
    'SPA-like pages but SSR accessible.'
)
ON CONFLICT (institution_id) DO UPDATE SET
    site_type = EXCLUDED.site_type,
    discovery_mode = EXCLUDED.discovery_mode,
    exclusion_patterns = EXCLUDED.exclusion_patterns,
    catalog_url_patterns = EXCLUDED.catalog_url_patterns,
    catalog_link_selector = EXCLUDED.catalog_link_selector,
    catalog_max_pages = EXCLUDED.catalog_max_pages,
    detail_wait_ms = EXCLUDED.detail_wait_ms,
    section_keywords = EXCLUDED.section_keywords,
    field_defaults = EXCLUDED.field_defaults,
    section_mode_map = EXCLUDED.section_mode_map,
    section_course_type_map = EXCLUDED.section_course_type_map,
    title_prefix_removals = EXCLUDED.title_prefix_removals,
    title_split_separators = EXCLUDED.title_split_separators,
    notes = EXCLUDED.notes,
    seed_urls = EXCLUDED.seed_urls,
    catalog_scroll_iterations = EXCLUDED.catalog_scroll_iterations,
    requires_stealth = EXCLUDED.requires_stealth,
    requires_cloudflare_bypass = EXCLUDED.requires_cloudflare_bypass,
    warmup_url = EXCLUDED.warmup_url,
    popup_close_selectors = EXCLUDED.popup_close_selectors,
    max_courses_per_run = EXCLUDED.max_courses_per_run,
    soft_delete_before_scrape = EXCLUDED.soft_delete_before_scrape,
    price_regex = EXCLUDED.price_regex,
    duration_regex = EXCLUDED.duration_regex,
    updated_at = now();

-- Institution: utp (UTP)
-- Exclusions: 66 (global + institutional)

INSERT INTO public.institution_site_profiles (
    institution_id, site_type, discovery_mode,
    seed_urls, exclusion_patterns, catalog_url_patterns,
    catalog_link_selector, catalog_max_pages, catalog_scroll_iterations,
    requires_stealth, requires_cloudflare_bypass, popup_close_selectors,
    detail_wait_ms, section_keywords, field_defaults,
    section_mode_map, section_course_type_map,
    title_prefix_removals, title_split_separators,
    max_courses_per_run, soft_delete_before_scrape, notes
) VALUES (
    '6c86caf1-e62f-4c9a-bdb7-e8811c352a6e',
    'traditional_ssr',
    'sitemap_bfs',
    '[]'::jsonb,
    '[".7z", ".avi", ".bmp", ".css", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".js", ".json", ".mov", ".mp3", ".mp4", ".pdf", ".png", ".ppt", ".pptx", ".rar", ".svg", ".tar", ".webp", ".wmv", ".xls", ".xlsx", ".xml", ".zip", "/about/", "/admision/", "/agradecimiento/", "/archive/", "/assets/", "/author/", "/biblioteca/", "/blog/", "/carrito/", "/categoria/", "/category/", "/contacto/", "/eventos/", "/faq/", "/feed/", "/img/", "/login", "/media/", "/nosotros/", "/noticias/", "/page/", "/politica/", "/pregrado/", "/privacidad/", "/publicaciones/", "/register/", "/rss/", "/search/", "/static/", "/tag/", "/tags/", "/terminos/", "/thank-you-page/", "/transparencia/", "/vida-universitaria/", "/wp-content/", "/wp-json/"]'::jsonb,
    '[]'::jsonb,
    NULL,
    5,
    0,
    FALSE,
    FALSE,
    '[]'::jsonb,
    2000,
    '{}'::jsonb,
    '{"mode": "Presencial"}'::jsonb,
    '{}'::jsonb,
    '{}'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb,
    500,
    FALSE,
    'UTP website.'
)
ON CONFLICT (institution_id) DO UPDATE SET
    site_type = EXCLUDED.site_type,
    discovery_mode = EXCLUDED.discovery_mode,
    exclusion_patterns = EXCLUDED.exclusion_patterns,
    catalog_url_patterns = EXCLUDED.catalog_url_patterns,
    catalog_link_selector = EXCLUDED.catalog_link_selector,
    catalog_max_pages = EXCLUDED.catalog_max_pages,
    detail_wait_ms = EXCLUDED.detail_wait_ms,
    section_keywords = EXCLUDED.section_keywords,
    field_defaults = EXCLUDED.field_defaults,
    section_mode_map = EXCLUDED.section_mode_map,
    section_course_type_map = EXCLUDED.section_course_type_map,
    title_prefix_removals = EXCLUDED.title_prefix_removals,
    title_split_separators = EXCLUDED.title_split_separators,
    notes = EXCLUDED.notes,
    seed_urls = EXCLUDED.seed_urls,
    catalog_scroll_iterations = EXCLUDED.catalog_scroll_iterations,
    requires_stealth = EXCLUDED.requires_stealth,
    requires_cloudflare_bypass = EXCLUDED.requires_cloudflare_bypass,
    warmup_url = EXCLUDED.warmup_url,
    popup_close_selectors = EXCLUDED.popup_close_selectors,
    max_courses_per_run = EXCLUDED.max_courses_per_run,
    soft_delete_before_scrape = EXCLUDED.soft_delete_before_scrape,
    price_regex = EXCLUDED.price_regex,
    duration_regex = EXCLUDED.duration_regex,
    updated_at = now();

-- Institution: unmsm (UNMSM)
-- Exclusions: 67 (global + institutional)

INSERT INTO public.institution_site_profiles (
    institution_id, site_type, discovery_mode,
    seed_urls, exclusion_patterns, catalog_url_patterns,
    catalog_link_selector, catalog_max_pages, catalog_scroll_iterations,
    requires_stealth, requires_cloudflare_bypass, popup_close_selectors,
    detail_wait_ms, section_keywords, field_defaults,
    section_mode_map, section_course_type_map,
    title_prefix_removals, title_split_separators,
    max_courses_per_run, soft_delete_before_scrape, notes
) VALUES (
    '312d1aa3-69f2-4a46-87de-3f4f8f2d1352',
    'traditional_ssr',
    'sitemap_bfs',
    '[]'::jsonb,
    '[".7z", ".avi", ".bmp", ".css", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".js", ".json", ".mov", ".mp3", ".mp4", ".pdf", ".png", ".ppt", ".pptx", ".rar", ".svg", ".tar", ".webp", ".wmv", ".xls", ".xlsx", ".xml", ".zip", "/about/", "/admision/", "/agradecimiento/", "/archive/", "/assets/", "/author/", "/biblioteca/", "/blog/", "/carrito/", "/categoria/", "/category/", "/contacto/", "/eventos/", "/facultad/", "/faq/", "/feed/", "/img/", "/laboratorio/", "/login", "/media/", "/nosotros/", "/noticias/", "/page/", "/politica/", "/pregrado/", "/privacidad/", "/publicaciones/", "/register/", "/rss/", "/search/", "/static/", "/tag/", "/tags/", "/terminos/", "/thank-you-page/", "/transparencia/", "/wp-content/", "/wp-json/"]'::jsonb,
    '[]'::jsonb,
    NULL,
    5,
    0,
    FALSE,
    FALSE,
    '[]'::jsonb,
    2000,
    '{}'::jsonb,
    '{"mode": "Presencial"}'::jsonb,
    '{}'::jsonb,
    '{}'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb,
    500,
    FALSE,
    'UNMSM.'
)
ON CONFLICT (institution_id) DO UPDATE SET
    site_type = EXCLUDED.site_type,
    discovery_mode = EXCLUDED.discovery_mode,
    exclusion_patterns = EXCLUDED.exclusion_patterns,
    catalog_url_patterns = EXCLUDED.catalog_url_patterns,
    catalog_link_selector = EXCLUDED.catalog_link_selector,
    catalog_max_pages = EXCLUDED.catalog_max_pages,
    detail_wait_ms = EXCLUDED.detail_wait_ms,
    section_keywords = EXCLUDED.section_keywords,
    field_defaults = EXCLUDED.field_defaults,
    section_mode_map = EXCLUDED.section_mode_map,
    section_course_type_map = EXCLUDED.section_course_type_map,
    title_prefix_removals = EXCLUDED.title_prefix_removals,
    title_split_separators = EXCLUDED.title_split_separators,
    notes = EXCLUDED.notes,
    seed_urls = EXCLUDED.seed_urls,
    catalog_scroll_iterations = EXCLUDED.catalog_scroll_iterations,
    requires_stealth = EXCLUDED.requires_stealth,
    requires_cloudflare_bypass = EXCLUDED.requires_cloudflare_bypass,
    warmup_url = EXCLUDED.warmup_url,
    popup_close_selectors = EXCLUDED.popup_close_selectors,
    max_courses_per_run = EXCLUDED.max_courses_per_run,
    soft_delete_before_scrape = EXCLUDED.soft_delete_before_scrape,
    price_regex = EXCLUDED.price_regex,
    duration_regex = EXCLUDED.duration_regex,
    updated_at = now();

-- Institution: universidad-del-pacifico (Universidad del Pacifico)
-- Exclusions: 67 (global + institutional)

INSERT INTO public.institution_site_profiles (
    institution_id, site_type, discovery_mode,
    seed_urls, exclusion_patterns, catalog_url_patterns,
    catalog_link_selector, catalog_max_pages, catalog_scroll_iterations,
    requires_stealth, requires_cloudflare_bypass, popup_close_selectors,
    detail_wait_ms, section_keywords, field_defaults,
    section_mode_map, section_course_type_map,
    title_prefix_removals, title_split_separators,
    max_courses_per_run, soft_delete_before_scrape, notes
) VALUES (
    'a4fd99a6-d161-4854-bdc8-6b5f1bd8163e',
    'traditional_ssr',
    'sitemap_bfs',
    '[]'::jsonb,
    '[".7z", ".avi", ".bmp", ".css", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".js", ".json", ".mov", ".mp3", ".mp4", ".pdf", ".png", ".ppt", ".pptx", ".rar", ".svg", ".tar", ".webp", ".wmv", ".xls", ".xlsx", ".xml", ".zip", "/about/", "/admision/", "/agradecimiento/", "/archive/", "/assets/", "/author/", "/biblioteca/", "/blog/", "/carrito/", "/categoria/", "/category/", "/contacto/", "/egp/", "/eventos/", "/faq/", "/feed/", "/idiomas/", "/img/", "/login", "/maestrias/", "/media/", "/nosotros/", "/noticias/", "/page/", "/politica/", "/privacidad/", "/publicaciones/", "/register/", "/rss/", "/search/", "/static/", "/tag/", "/tags/", "/terminos/", "/thank-you-page/", "/transparencia/", "/wp-content/", "/wp-json/"]'::jsonb,
    '[]'::jsonb,
    NULL,
    5,
    0,
    FALSE,
    FALSE,
    '[]'::jsonb,
    2000,
    '{"Plan de estudios": "curriculum_summary", "Perfil del egresado": "graduate_profile"}'::jsonb,
    '{"mode": "Presencial"}'::jsonb,
    '{}'::jsonb,
    '{}'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb,
    500,
    FALSE,
    'U. del Pacifico.'
)
ON CONFLICT (institution_id) DO UPDATE SET
    site_type = EXCLUDED.site_type,
    discovery_mode = EXCLUDED.discovery_mode,
    exclusion_patterns = EXCLUDED.exclusion_patterns,
    catalog_url_patterns = EXCLUDED.catalog_url_patterns,
    catalog_link_selector = EXCLUDED.catalog_link_selector,
    catalog_max_pages = EXCLUDED.catalog_max_pages,
    detail_wait_ms = EXCLUDED.detail_wait_ms,
    section_keywords = EXCLUDED.section_keywords,
    field_defaults = EXCLUDED.field_defaults,
    section_mode_map = EXCLUDED.section_mode_map,
    section_course_type_map = EXCLUDED.section_course_type_map,
    title_prefix_removals = EXCLUDED.title_prefix_removals,
    title_split_separators = EXCLUDED.title_split_separators,
    notes = EXCLUDED.notes,
    seed_urls = EXCLUDED.seed_urls,
    catalog_scroll_iterations = EXCLUDED.catalog_scroll_iterations,
    requires_stealth = EXCLUDED.requires_stealth,
    requires_cloudflare_bypass = EXCLUDED.requires_cloudflare_bypass,
    warmup_url = EXCLUDED.warmup_url,
    popup_close_selectors = EXCLUDED.popup_close_selectors,
    max_courses_per_run = EXCLUDED.max_courses_per_run,
    soft_delete_before_scrape = EXCLUDED.soft_delete_before_scrape,
    price_regex = EXCLUDED.price_regex,
    duration_regex = EXCLUDED.duration_regex,
    updated_at = now();

-- Institution: idat (IDAT)
-- Exclusions: 65 (global + institutional)

INSERT INTO public.institution_site_profiles (
    institution_id, site_type, discovery_mode,
    seed_urls, exclusion_patterns, catalog_url_patterns,
    catalog_link_selector, catalog_max_pages, catalog_scroll_iterations,
    requires_stealth, requires_cloudflare_bypass, popup_close_selectors,
    detail_wait_ms, section_keywords, field_defaults,
    section_mode_map, section_course_type_map,
    title_prefix_removals, title_split_separators,
    max_courses_per_run, soft_delete_before_scrape, notes
) VALUES (
    'a7a77d2a-0b13-4dab-921f-707234cb0344',
    'spa_js_heavy',
    'sitemap_bfs',
    '[]'::jsonb,
    '[".7z", ".avi", ".bmp", ".css", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".js", ".json", ".mov", ".mp3", ".mp4", ".pdf", ".png", ".ppt", ".pptx", ".rar", ".svg", ".tar", ".webp", ".wmv", ".xls", ".xlsx", ".xml", ".zip", "/about/", "/admision/", "/agradecimiento/", "/archive/", "/assets/", "/author/", "/biblioteca/", "/blog/", "/carrito/", "/categoria/", "/category/", "/contacto/", "/eventos/", "/faq/", "/feed/", "/img/", "/login", "/media/", "/nosotros/", "/noticias/", "/page/", "/politica/", "/pregrado/", "/privacidad/", "/publicaciones/", "/register/", "/rss/", "/search/", "/static/", "/tag/", "/tags/", "/terminos/", "/thank-you-page/", "/transparencia/", "/wp-content/", "/wp-json/"]'::jsonb,
    '[]'::jsonb,
    NULL,
    5,
    0,
    FALSE,
    FALSE,
    '[]'::jsonb,
    4000,
    '{}'::jsonb,
    '{"mode": "Presencial"}'::jsonb,
    '{}'::jsonb,
    '{}'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb,
    500,
    FALSE,
    'IDAT uses heavy JS.'
)
ON CONFLICT (institution_id) DO UPDATE SET
    site_type = EXCLUDED.site_type,
    discovery_mode = EXCLUDED.discovery_mode,
    exclusion_patterns = EXCLUDED.exclusion_patterns,
    catalog_url_patterns = EXCLUDED.catalog_url_patterns,
    catalog_link_selector = EXCLUDED.catalog_link_selector,
    catalog_max_pages = EXCLUDED.catalog_max_pages,
    detail_wait_ms = EXCLUDED.detail_wait_ms,
    section_keywords = EXCLUDED.section_keywords,
    field_defaults = EXCLUDED.field_defaults,
    section_mode_map = EXCLUDED.section_mode_map,
    section_course_type_map = EXCLUDED.section_course_type_map,
    title_prefix_removals = EXCLUDED.title_prefix_removals,
    title_split_separators = EXCLUDED.title_split_separators,
    notes = EXCLUDED.notes,
    seed_urls = EXCLUDED.seed_urls,
    catalog_scroll_iterations = EXCLUDED.catalog_scroll_iterations,
    requires_stealth = EXCLUDED.requires_stealth,
    requires_cloudflare_bypass = EXCLUDED.requires_cloudflare_bypass,
    warmup_url = EXCLUDED.warmup_url,
    popup_close_selectors = EXCLUDED.popup_close_selectors,
    max_courses_per_run = EXCLUDED.max_courses_per_run,
    soft_delete_before_scrape = EXCLUDED.soft_delete_before_scrape,
    price_regex = EXCLUDED.price_regex,
    duration_regex = EXCLUDED.duration_regex,
    updated_at = now();

-- Institution: senati (SENATI)
-- Exclusions: 65 (global + institutional)

INSERT INTO public.institution_site_profiles (
    institution_id, site_type, discovery_mode,
    seed_urls, exclusion_patterns, catalog_url_patterns,
    catalog_link_selector, catalog_max_pages, catalog_scroll_iterations,
    requires_stealth, requires_cloudflare_bypass, popup_close_selectors,
    detail_wait_ms, section_keywords, field_defaults,
    section_mode_map, section_course_type_map,
    title_prefix_removals, title_split_separators,
    max_courses_per_run, soft_delete_before_scrape, notes
) VALUES (
    '1adeb662-b861-4e93-8245-335a619d701c',
    'traditional_ssr',
    'sitemap_bfs',
    '[]'::jsonb,
    '[".7z", ".avi", ".bmp", ".css", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".js", ".json", ".mov", ".mp3", ".mp4", ".pdf", ".png", ".ppt", ".pptx", ".rar", ".svg", ".tar", ".webp", ".wmv", ".xls", ".xlsx", ".xml", ".zip", "/about/", "/admision/", "/agradecimiento/", "/archive/", "/assets/", "/author/", "/biblioteca/", "/blog/", "/carrito/", "/categoria/", "/category/", "/contacto/", "/eventos/", "/faq/", "/feed/", "/img/", "/login", "/media/", "/nosotros/", "/noticias/", "/page/", "/politica/", "/pregrado/", "/privacidad/", "/publicaciones/", "/register/", "/rss/", "/search/", "/static/", "/tag/", "/tags/", "/terminos/", "/thank-you-page/", "/transparencia/", "/wp-content/", "/wp-json/"]'::jsonb,
    '[]'::jsonb,
    NULL,
    5,
    0,
    FALSE,
    FALSE,
    '[]'::jsonb,
    2000,
    '{}'::jsonb,
    '{"mode": "Presencial"}'::jsonb,
    '{}'::jsonb,
    '{}'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb,
    500,
    FALSE,
    'SENATI website.'
)
ON CONFLICT (institution_id) DO UPDATE SET
    site_type = EXCLUDED.site_type,
    discovery_mode = EXCLUDED.discovery_mode,
    exclusion_patterns = EXCLUDED.exclusion_patterns,
    catalog_url_patterns = EXCLUDED.catalog_url_patterns,
    catalog_link_selector = EXCLUDED.catalog_link_selector,
    catalog_max_pages = EXCLUDED.catalog_max_pages,
    detail_wait_ms = EXCLUDED.detail_wait_ms,
    section_keywords = EXCLUDED.section_keywords,
    field_defaults = EXCLUDED.field_defaults,
    section_mode_map = EXCLUDED.section_mode_map,
    section_course_type_map = EXCLUDED.section_course_type_map,
    title_prefix_removals = EXCLUDED.title_prefix_removals,
    title_split_separators = EXCLUDED.title_split_separators,
    notes = EXCLUDED.notes,
    seed_urls = EXCLUDED.seed_urls,
    catalog_scroll_iterations = EXCLUDED.catalog_scroll_iterations,
    requires_stealth = EXCLUDED.requires_stealth,
    requires_cloudflare_bypass = EXCLUDED.requires_cloudflare_bypass,
    warmup_url = EXCLUDED.warmup_url,
    popup_close_selectors = EXCLUDED.popup_close_selectors,
    max_courses_per_run = EXCLUDED.max_courses_per_run,
    soft_delete_before_scrape = EXCLUDED.soft_delete_before_scrape,
    price_regex = EXCLUDED.price_regex,
    duration_regex = EXCLUDED.duration_regex,
    updated_at = now();

-- Institution: upc (UPC)
-- Exclusions: 67 (global + institutional)

INSERT INTO public.institution_site_profiles (
    institution_id, site_type, discovery_mode,
    seed_urls, exclusion_patterns, catalog_url_patterns,
    catalog_link_selector, catalog_max_pages, catalog_scroll_iterations,
    requires_stealth, requires_cloudflare_bypass, popup_close_selectors,
    detail_wait_ms, section_keywords, field_defaults,
    section_mode_map, section_course_type_map,
    title_prefix_removals, title_split_separators,
    max_courses_per_run, soft_delete_before_scrape, notes
) VALUES (
    '19c4ec63-aca5-499d-b581-be1672e2fdf8',
    'spa_js_heavy',
    'sitemap_bfs',
    '[]'::jsonb,
    '[".7z", ".avi", ".bmp", ".css", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".js", ".json", ".mov", ".mp3", ".mp4", ".pdf", ".png", ".ppt", ".pptx", ".rar", ".svg", ".tar", ".webp", ".wmv", ".xls", ".xlsx", ".xml", ".zip", "/about/", "/admision/", "/agradecimiento/", "/archive/", "/assets/", "/author/", "/biblioteca/", "/blog/", "/carrito/", "/categoria/", "/category/", "/contacto/", "/eventos/", "/faq/", "/feed/", "/img/", "/info-importante/", "/login", "/media/", "/nosotros/", "/noticias/", "/page/", "/politica/", "/pregrado/", "/privacidad/", "/publicaciones/", "/register/", "/rss/", "/search/", "/static/", "/tag/", "/tags/", "/terminos/", "/thank-you-page/", "/transparencia/", "/vida-universitaria/", "/wp-content/", "/wp-json/"]'::jsonb,
    '[]'::jsonb,
    NULL,
    5,
    0,
    FALSE,
    FALSE,
    '[]'::jsonb,
    4000,
    '{}'::jsonb,
    '{"mode": "Presencial"}'::jsonb,
    '{}'::jsonb,
    '{}'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb,
    500,
    FALSE,
    'UPC uses heavy JS rendering.'
)
ON CONFLICT (institution_id) DO UPDATE SET
    site_type = EXCLUDED.site_type,
    discovery_mode = EXCLUDED.discovery_mode,
    exclusion_patterns = EXCLUDED.exclusion_patterns,
    catalog_url_patterns = EXCLUDED.catalog_url_patterns,
    catalog_link_selector = EXCLUDED.catalog_link_selector,
    catalog_max_pages = EXCLUDED.catalog_max_pages,
    detail_wait_ms = EXCLUDED.detail_wait_ms,
    section_keywords = EXCLUDED.section_keywords,
    field_defaults = EXCLUDED.field_defaults,
    section_mode_map = EXCLUDED.section_mode_map,
    section_course_type_map = EXCLUDED.section_course_type_map,
    title_prefix_removals = EXCLUDED.title_prefix_removals,
    title_split_separators = EXCLUDED.title_split_separators,
    notes = EXCLUDED.notes,
    seed_urls = EXCLUDED.seed_urls,
    catalog_scroll_iterations = EXCLUDED.catalog_scroll_iterations,
    requires_stealth = EXCLUDED.requires_stealth,
    requires_cloudflare_bypass = EXCLUDED.requires_cloudflare_bypass,
    warmup_url = EXCLUDED.warmup_url,
    popup_close_selectors = EXCLUDED.popup_close_selectors,
    max_courses_per_run = EXCLUDED.max_courses_per_run,
    soft_delete_before_scrape = EXCLUDED.soft_delete_before_scrape,
    price_regex = EXCLUDED.price_regex,
    duration_regex = EXCLUDED.duration_regex,
    updated_at = now();

-- Institution: usil (USIL)
-- Exclusions: 66 (global + institutional)

INSERT INTO public.institution_site_profiles (
    institution_id, site_type, discovery_mode,
    seed_urls, exclusion_patterns, catalog_url_patterns,
    catalog_link_selector, catalog_max_pages, catalog_scroll_iterations,
    requires_stealth, requires_cloudflare_bypass, popup_close_selectors,
    detail_wait_ms, section_keywords, field_defaults,
    section_mode_map, section_course_type_map,
    title_prefix_removals, title_split_separators,
    max_courses_per_run, soft_delete_before_scrape, notes
) VALUES (
    '1f376ef7-fc40-49e4-b4dd-b0cc89fe7211',
    'traditional_ssr',
    'sitemap_bfs',
    '[]'::jsonb,
    '[".7z", ".avi", ".bmp", ".css", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".js", ".json", ".mov", ".mp3", ".mp4", ".pdf", ".png", ".ppt", ".pptx", ".rar", ".svg", ".tar", ".webp", ".wmv", ".xls", ".xlsx", ".xml", ".zip", "/about/", "/admision/", "/agradecimiento/", "/archive/", "/assets/", "/author/", "/biblioteca/", "/blog/", "/carrito/", "/categoria/", "/category/", "/contacto/", "/eventos/", "/faq/", "/feed/", "/img/", "/login", "/media/", "/nosotros/", "/noticias/", "/page/", "/politica/", "/pregrado/", "/privacidad/", "/publicaciones/", "/register/", "/rss/", "/search/", "/static/", "/tag/", "/tags/", "/terminos/", "/thank-you-page/", "/transparencia/", "/vida-universitaria/", "/wp-content/", "/wp-json/"]'::jsonb,
    '[]'::jsonb,
    NULL,
    5,
    0,
    FALSE,
    FALSE,
    '[]'::jsonb,
    2000,
    '{}'::jsonb,
    '{"mode": "Presencial"}'::jsonb,
    '{}'::jsonb,
    '{}'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb,
    500,
    FALSE,
    'USIL website.'
)
ON CONFLICT (institution_id) DO UPDATE SET
    site_type = EXCLUDED.site_type,
    discovery_mode = EXCLUDED.discovery_mode,
    exclusion_patterns = EXCLUDED.exclusion_patterns,
    catalog_url_patterns = EXCLUDED.catalog_url_patterns,
    catalog_link_selector = EXCLUDED.catalog_link_selector,
    catalog_max_pages = EXCLUDED.catalog_max_pages,
    detail_wait_ms = EXCLUDED.detail_wait_ms,
    section_keywords = EXCLUDED.section_keywords,
    field_defaults = EXCLUDED.field_defaults,
    section_mode_map = EXCLUDED.section_mode_map,
    section_course_type_map = EXCLUDED.section_course_type_map,
    title_prefix_removals = EXCLUDED.title_prefix_removals,
    title_split_separators = EXCLUDED.title_split_separators,
    notes = EXCLUDED.notes,
    seed_urls = EXCLUDED.seed_urls,
    catalog_scroll_iterations = EXCLUDED.catalog_scroll_iterations,
    requires_stealth = EXCLUDED.requires_stealth,
    requires_cloudflare_bypass = EXCLUDED.requires_cloudflare_bypass,
    warmup_url = EXCLUDED.warmup_url,
    popup_close_selectors = EXCLUDED.popup_close_selectors,
    max_courses_per_run = EXCLUDED.max_courses_per_run,
    soft_delete_before_scrape = EXCLUDED.soft_delete_before_scrape,
    price_regex = EXCLUDED.price_regex,
    duration_regex = EXCLUDED.duration_regex,
    updated_at = now();

-- Institution: uni (UNI)
-- Exclusions: 65 (global + institutional)

INSERT INTO public.institution_site_profiles (
    institution_id, site_type, discovery_mode,
    seed_urls, exclusion_patterns, catalog_url_patterns,
    catalog_link_selector, catalog_max_pages, catalog_scroll_iterations,
    requires_stealth, requires_cloudflare_bypass, popup_close_selectors,
    detail_wait_ms, section_keywords, field_defaults,
    section_mode_map, section_course_type_map,
    title_prefix_removals, title_split_separators,
    max_courses_per_run, soft_delete_before_scrape, notes
) VALUES (
    '2647058e-070a-4fa4-a4a0-e2ed69600cb7',
    'traditional_ssr',
    'sitemap_bfs',
    '[]'::jsonb,
    '[".7z", ".avi", ".bmp", ".css", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".js", ".json", ".mov", ".mp3", ".mp4", ".pdf", ".png", ".ppt", ".pptx", ".rar", ".svg", ".tar", ".webp", ".wmv", ".xls", ".xlsx", ".xml", ".zip", "/about/", "/admision/", "/agradecimiento/", "/archive/", "/assets/", "/author/", "/biblioteca/", "/blog/", "/carrito/", "/categoria/", "/category/", "/contacto/", "/eventos/", "/faq/", "/feed/", "/img/", "/index.php/", "/login", "/media/", "/nosotros/", "/noticias/", "/page/", "/politica/", "/privacidad/", "/publicaciones/", "/register/", "/rss/", "/search/", "/static/", "/tag/", "/tags/", "/terminos/", "/thank-you-page/", "/transparencia/", "/wp-content/", "/wp-json/"]'::jsonb,
    '[]'::jsonb,
    NULL,
    5,
    0,
    FALSE,
    FALSE,
    '[]'::jsonb,
    2000,
    '{}'::jsonb,
    '{"mode": "Presencial"}'::jsonb,
    '{}'::jsonb,
    '{}'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb,
    500,
    FALSE,
    'UNI.'
)
ON CONFLICT (institution_id) DO UPDATE SET
    site_type = EXCLUDED.site_type,
    discovery_mode = EXCLUDED.discovery_mode,
    exclusion_patterns = EXCLUDED.exclusion_patterns,
    catalog_url_patterns = EXCLUDED.catalog_url_patterns,
    catalog_link_selector = EXCLUDED.catalog_link_selector,
    catalog_max_pages = EXCLUDED.catalog_max_pages,
    detail_wait_ms = EXCLUDED.detail_wait_ms,
    section_keywords = EXCLUDED.section_keywords,
    field_defaults = EXCLUDED.field_defaults,
    section_mode_map = EXCLUDED.section_mode_map,
    section_course_type_map = EXCLUDED.section_course_type_map,
    title_prefix_removals = EXCLUDED.title_prefix_removals,
    title_split_separators = EXCLUDED.title_split_separators,
    notes = EXCLUDED.notes,
    seed_urls = EXCLUDED.seed_urls,
    catalog_scroll_iterations = EXCLUDED.catalog_scroll_iterations,
    requires_stealth = EXCLUDED.requires_stealth,
    requires_cloudflare_bypass = EXCLUDED.requires_cloudflare_bypass,
    warmup_url = EXCLUDED.warmup_url,
    popup_close_selectors = EXCLUDED.popup_close_selectors,
    max_courses_per_run = EXCLUDED.max_courses_per_run,
    soft_delete_before_scrape = EXCLUDED.soft_delete_before_scrape,
    price_regex = EXCLUDED.price_regex,
    duration_regex = EXCLUDED.duration_regex,
    updated_at = now();


-- Trigger: auto-update updated_at on row modification
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at ON institution_site_profiles;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON institution_site_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

COMMIT;