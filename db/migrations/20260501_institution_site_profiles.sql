-- Migration: 20260501_institution_site_profiles.sql
-- Fase 61: Site Profiles — consolidate exclusion + discovery + extraction config per institution
-- Replaces crawler_exclusions with institution_site_profiles.exclusion_patterns (JSONB)

BEGIN;

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

ALTER TABLE public.institution_site_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY profiles_select_authenticated ON public.institution_site_profiles
    FOR SELECT TO authenticated USING (true);
CREATE POLICY profiles_service_role ON public.institution_site_profiles
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE INDEX idx_profiles_institution ON public.institution_site_profiles(institution_id);

COMMENT ON TABLE public.institution_site_profiles IS 'Per-institution scraping profiles: site type, discovery config, exclusion patterns, LLM hints';
COMMENT ON COLUMN public.institution_site_profiles.site_type IS 'Site classification: traditional_ssr, ecommerce, spa_js_heavy, paginated_catalog, catalog_link_extraction, cloudflare_protected';
COMMENT ON COLUMN public.institution_site_profiles.discovery_mode IS 'How to discover URLs: sitemap_bfs, hardcoded_urls, paginated_catalog, catalog_link_extraction';
COMMENT ON COLUMN public.institution_site_profiles.seed_urls IS 'JSONB array of hardcoded seed URLs for discovery_mode=hardcoded_urls. e.g. ["https://ulima.edu.pe/pregrado/"]';
COMMENT ON COLUMN public.institution_site_profiles.exclusion_patterns IS 'JSONB array of patterns to exclude. Migrated from crawler_exclusions. e.g. ["/noticias/", "/blog/", ".pdf"]';
COMMENT ON COLUMN public.institution_site_profiles.section_keywords IS 'JSONB map of section heading → LLM extraction target. e.g. {"Dirigido a": "target_audience", "Malla Curricular": "curriculum_summary"}';
COMMENT ON COLUMN public.institution_site_profiles.field_defaults IS 'JSONB map of field → default value when LLM cannot infer. e.g. {"mode": "Presencial", "course_type": "Programa"}';
COMMENT ON COLUMN public.institution_site_profiles.section_mode_map IS 'JSONB map of URL path segment → default modality. e.g. {"/cursos-talleres/": "Remoto"}';

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
