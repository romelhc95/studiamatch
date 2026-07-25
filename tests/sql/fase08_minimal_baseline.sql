\set ON_ERROR_STOP on

-- Synthetic PostgreSQL 17 fixture for F6/F7/F8 contract tests.
-- It intentionally contains no production rows, snapshots, endpoints, or credentials.

CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE service_role NOLOGIN BYPASSRLS;

GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

CREATE TABLE public.institution_site_profiles (
    institution_id uuid PRIMARY KEY,
    production_enabled boolean NOT NULL DEFAULT false,
    exclusion_patterns jsonb NOT NULL DEFAULT '[]'::jsonb,
    updated_at timestamptz NOT NULL DEFAULT pg_catalog.now()
);

CREATE TABLE public.courses (
    id uuid PRIMARY KEY,
    name text NOT NULL,
    slug text NOT NULL,
    url text NOT NULL UNIQUE,
    institution_id uuid NOT NULL,
    price_pen numeric,
    price_status text,
    mode text,
    course_type text,
    category_id uuid,
    duration integer,
    start_date_text text,
    description_long text,
    syllabus jsonb,
    target_audience text,
    requirements text,
    certification text,
    benefits text,
    objectives text,
    expected_monthly_salary numeric,
    seniority_level text,
    roi_months integer,
    address text,
    region text,
    is_active boolean NOT NULL DEFAULT true,
    is_verified boolean NOT NULL DEFAULT false,
    brochure_url text,
    start_date date,
    created_at timestamptz NOT NULL DEFAULT pg_catalog.now(),
    updated_at timestamptz NOT NULL DEFAULT pg_catalog.now(),
    view_count integer NOT NULL DEFAULT 0,
    comparison_count integer NOT NULL DEFAULT 0
);

CREATE TABLE public.leads (
    id uuid PRIMARY KEY,
    first_name text NOT NULL,
    email text NOT NULL,
    whatsapp text NOT NULL,
    course_id uuid REFERENCES public.courses(id),
    created_at timestamptz NOT NULL DEFAULT pg_catalog.now()
);

CREATE TABLE public.ratings (
    id uuid PRIMARY KEY,
    course_id uuid NOT NULL,
    rating_value integer NOT NULL,
    user_nickname text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT pg_catalog.now()
);

CREATE TABLE public.reviews (
    id uuid PRIMARY KEY,
    course_id uuid NOT NULL,
    content text NOT NULL,
    user_nickname text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT pg_catalog.now()
);

CREATE TABLE public.staging_raw (
    id uuid PRIMARY KEY,
    institution_id uuid NOT NULL,
    url text NOT NULL UNIQUE,
    raw_html text,
    raw_name text,
    raw_description text,
    status text NOT NULL DEFAULT 'pending',
    discard_reason text,
    processing_error text,
    last_harvested_at timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE public.cleansed_programs (
    id uuid PRIMARY KEY,
    staging_id uuid,
    institution_id uuid NOT NULL,
    url text NOT NULL UNIQUE,
    effective_url text,
    canonical_url text,
    clean_name text,
    clean_description text,
    modality text,
    location text,
    base_price numeric,
    currency text,
    status text NOT NULL DEFAULT 'pending',
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE public.enriched_programs (
    id uuid PRIMARY KEY DEFAULT pg_catalog.gen_random_uuid(),
    cleansed_id uuid NOT NULL UNIQUE,
    institution_id uuid NOT NULL,
    url text NOT NULL,
    official_name text,
    duration_text text,
    duration_months integer,
    total_cost_est numeric,
    requirements text,
    graduate_profile text,
    curriculum_summary jsonb,
    modality text,
    primary_campus text,
    degree_type text,
    start_date text,
    partnerships text,
    certifications text,
    language text,
    categories text,
    difficulty_level text,
    ai_summary text,
    status text NOT NULL DEFAULT 'pending',
    provider_used text,
    is_mock_data boolean,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    brochure_url text
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO service_role;

CREATE FUNCTION public.increment_view_count(uuid)
RETURNS void LANGUAGE sql SET search_path = '' AS 'SELECT';
CREATE FUNCTION public.increment_view_count_v2(uuid, text)
RETURNS void LANGUAGE sql SET search_path = '' AS 'SELECT';
CREATE FUNCTION public.deactivate_courses_when_production_disabled()
RETURNS void LANGUAGE sql SET search_path = '' AS 'SELECT';
CREATE FUNCTION public.fn_auto_assign_category()
RETURNS void LANGUAGE sql SET search_path = '' AS 'SELECT';
CREATE FUNCTION public.notify_new_lead()
RETURNS void LANGUAGE sql SET search_path = '' AS 'SELECT';
CREATE FUNCTION public.update_updated_at_column()
RETURNS trigger LANGUAGE plpgsql SET search_path = '' AS $function$
BEGIN
    RETURN NEW;
END;
$function$;
CREATE FUNCTION public.update_updated_at()
RETURNS trigger LANGUAGE plpgsql SET search_path = '' AS $function$
BEGIN
    RETURN NEW;
END;
$function$;
CREATE FUNCTION public.validate_institution_site_profiles_jsonb()
RETURNS trigger LANGUAGE plpgsql SET search_path = '' AS $function$
BEGIN
    RETURN NEW;
END;
$function$;
CREATE FUNCTION public.repair_jsonb_array(jsonb)
RETURNS jsonb LANGUAGE sql IMMUTABLE SET search_path = '' AS 'SELECT $1';
CREATE FUNCTION public.repair_jsonb_object(jsonb)
RETURNS jsonb LANGUAGE sql IMMUTABLE SET search_path = '' AS 'SELECT $1';
CREATE FUNCTION public.rls_auto_enable()
RETURNS void LANGUAGE sql SET search_path = '' AS 'SELECT';
