\set ON_ERROR_STOP on

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS extensions;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN BYPASSRLS;
  END IF;
END
$$;
ALTER ROLE service_role BYPASSRLS;
GRANT USAGE ON SCHEMA public, extensions TO anon, authenticated, service_role;

CREATE SCHEMA IF NOT EXISTS auth;
CREATE TABLE auth.users (
  id uuid PRIMARY KEY,
  email text UNIQUE NOT NULL
);
CREATE OR REPLACE FUNCTION auth.uid()
RETURNS uuid LANGUAGE sql STABLE SET search_path = pg_catalog AS $$
  SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;
CREATE OR REPLACE FUNCTION auth.jwt()
RETURNS jsonb LANGUAGE sql STABLE SET search_path = pg_catalog AS $$
  SELECT coalesce(nullif(current_setting('request.jwt.claims', true), '')::jsonb, '{}'::jsonb)
$$;

CREATE TABLE public.institutions (
  id uuid PRIMARY KEY,
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  website_url text
);
CREATE TABLE public.institution_site_profiles (
  institution_id uuid PRIMARY KEY REFERENCES public.institutions(id) ON DELETE CASCADE,
  pipeline_ready boolean NOT NULL DEFAULT false,
  pipeline_enabled boolean NOT NULL DEFAULT false,
  discovery_enabled boolean NOT NULL DEFAULT false,
  production_enabled boolean NOT NULL DEFAULT false,
  notes text,
  website_url text,
  site_type text,
  discovery_mode text,
  seed_urls jsonb NOT NULL DEFAULT '[]'::jsonb,
  sitemap_url text,
  allowed_url_patterns jsonb NOT NULL DEFAULT '[]'::jsonb,
  exclusion_patterns jsonb NOT NULL DEFAULT '[]'::jsonb,
  noise_patterns jsonb NOT NULL DEFAULT '[]'::jsonb,
  noise_name_patterns jsonb NOT NULL DEFAULT '[]'::jsonb,
  field_defaults jsonb NOT NULL DEFAULT '{}'::jsonb,
  section_mode_map jsonb NOT NULL DEFAULT '{}'::jsonb,
  catalog_url_patterns jsonb NOT NULL DEFAULT '[]'::jsonb,
  catalog_max_pages integer NOT NULL DEFAULT 1,
  catalog_scroll_iterations integer NOT NULL DEFAULT 0,
  catalog_link_selector text,
  field_selectors jsonb NOT NULL DEFAULT '{}'::jsonb,
  label_selectors jsonb NOT NULL DEFAULT '{}'::jsonb,
  extraction_confidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  extraction_transforms jsonb NOT NULL DEFAULT '{}'::jsonb,
  price_regex text,
  title_prefix_removals jsonb NOT NULL DEFAULT '[]'::jsonb,
  title_split_separators jsonb NOT NULL DEFAULT '[]'::jsonb,
  url_type_rules jsonb NOT NULL DEFAULT '{}'::jsonb,
  section_keywords jsonb NOT NULL DEFAULT '{}'::jsonb,
  popup_close_selectors jsonb NOT NULL DEFAULT '[]'::jsonb,
  detail_wait_ms integer NOT NULL DEFAULT 0,
  requires_stealth boolean NOT NULL DEFAULT false,
  requires_cloudflare_bypass boolean NOT NULL DEFAULT false,
  warmup_url text,
  max_consecutive_errors integer NOT NULL DEFAULT 5,
  circuit_open boolean NOT NULL DEFAULT false,
  circuit_opened_at timestamptz
);

CREATE TABLE public.categories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text UNIQUE NOT NULL,
  description text,
  created_at timestamptz DEFAULT now()
);
CREATE TABLE public.courses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  institution_id uuid REFERENCES public.institutions(id) ON DELETE CASCADE,
  category_id uuid REFERENCES public.categories(id),
  name text NOT NULL,
  slug text NOT NULL,
  url text UNIQUE,
  price_pen numeric,
  price_status text DEFAULT 'publicado',
  mode text,
  duration text,
  category text,
  description_long text,
  syllabus text,
  target_audience text,
  requirements text,
  certification text,
  benefits text,
  objectives text,
  start_date date,
  start_date_text text,
  course_type text,
  brochure_url text,
  expected_monthly_salary numeric,
  seniority_level text,
  roi_months numeric,
  provider_used text,
  is_mock_data boolean DEFAULT false,
  view_count integer DEFAULT 0,
  comparison_count integer DEFAULT 0,
  is_active boolean DEFAULT true,
  is_verified boolean DEFAULT false,
  last_404_at timestamptz,
  last_scraped_at timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
CREATE TABLE public.leads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text NOT NULL,
  course_id uuid REFERENCES public.courses(id)
);
CREATE TABLE public.market_salaries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  category_id uuid REFERENCES public.categories(id),
  category_name text NOT NULL,
  min_salary_junior numeric NOT NULL,
  avg_salary numeric NOT NULL,
  min_salary_mid numeric,
  min_salary_senior numeric,
  currency text DEFAULT 'PEN',
  last_updated timestamptz DEFAULT now()
);
CREATE OR REPLACE FUNCTION public.increment_view_count(p_course_id uuid)
RETURNS void LANGUAGE plpgsql SET search_path = public AS $$
BEGIN
  UPDATE public.courses SET view_count = view_count + 1 WHERE id = p_course_id;
END
$$;

\i /fixture/20260430_intermediate_tables_ddl.sql
\i /fixture/20260505_add_provider_tracking.sql
\i /fixture/20260808_fase10_8_atomic_cleansing_provenance.sql
\i /fixture/20260525_fase113_pro_rls_and_rpc_sync.sql
\i /fixture/20260825_h2_editorial_layer.sql
\i /fixture/20260825_h2_editorial_layer_grants_fix.sql
\i /fixture/20260825_h2_editorial_layer_start_date_view_fix.sql
\i /fixture/20260825_h2_editorial_layer_allowlist_fix.sql
\i /fixture/20260826_h2_editorial_layer_forward_fix.sql
\i /fixture/20260826_h2_security_advisor_remediation.sql
\i /fixture/20260826_h2_seed_editorial_field_definitions.sql
\i /fixture/20260826_h2_public_effective_view_public_fields_fix.sql
\i /fixture/20260827_h2_pro_expand_schema_compat.sql

GRANT ALL ON TABLE
  public.institutions,
  public.institution_site_profiles,
  public.staging_raw,
  public.cleansed_programs,
  public.enriched_programs,
  public.courses,
  public.categories,
  public.market_salaries
TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

INSERT INTO public.institutions (id, name, slug, website_url)
VALUES (
  '10000000-0000-0000-0000-000000000001',
  'H3 Synthetic Institute',
  'h3-synthetic',
  'https://synthetic.h3.example'
);
INSERT INTO public.institution_site_profiles (
  institution_id, pipeline_ready, pipeline_enabled, discovery_enabled,
  production_enabled, website_url, site_type, discovery_mode, seed_urls,
  field_defaults, field_selectors, label_selectors, section_keywords,
  exclusion_patterns
)
VALUES (
  '10000000-0000-0000-0000-000000000001', true, true, true,
  true, 'https://synthetic.h3.example', 'traditional_ssr', 'hardcoded_urls',
  '["https://synthetic.h3.example/programas/analitica-aplicada"]'::jsonb,
  '{"price_status":"publicado"}'::jsonb, '{}'::jsonb, '{}'::jsonb,
  '{}'::jsonb, '[]'::jsonb
);
