\set ON_ERROR_STOP on

-- TEST-ONLY minimal historical Free drift. No production identifiers or rows.
CREATE TABLE public.institutions (
    id uuid PRIMARY KEY,
    name text NOT NULL,
    slug text NOT NULL UNIQUE,
    contact_email text
);

ALTER TABLE public.institution_site_profiles
ADD COLUMN notes text;

ALTER TABLE public.leads
    ALTER COLUMN id SET DEFAULT pg_catalog.gen_random_uuid(),
    ADD COLUMN last_name text,
    ADD COLUMN source_page text,
    ADD COLUMN type text,
    ADD COLUMN area_interest text,
    ADD COLUMN budget numeric,
    ADD COLUMN modality text,
    ADD COLUMN description text,
    ADD COLUMN is_late_enrollment_request boolean NOT NULL DEFAULT false,
    ADD COLUMN status text NOT NULL DEFAULT 'pending';

ALTER TABLE public.institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institution_site_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;

REVOKE ALL PRIVILEGES ON TABLE public.institutions
FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.institutions TO anon, authenticated;
GRANT ALL PRIVILEGES ON TABLE public.institutions TO service_role;
GRANT UPDATE (status) ON TABLE public.leads TO anon;

CREATE POLICY institutions_select_public
ON public.institutions
FOR SELECT TO anon
USING (true);

CREATE POLICY institutions_select_authenticated
ON public.institutions
FOR SELECT TO authenticated
USING (true);

CREATE POLICY profiles_select_public
ON public.institution_site_profiles
FOR SELECT TO anon
USING (production_enabled = true);

CREATE POLICY profiles_select_authenticated
ON public.institution_site_profiles
FOR SELECT TO authenticated
USING (production_enabled = true);

CREATE POLICY institutions_exclude_release_canary
ON public.institutions
AS RESTRICTIVE
FOR SELECT TO anon, authenticated
USING (slug NOT LIKE 'zz-studiamatch-canary-%');

CREATE POLICY profiles_exclude_release_canary
ON public.institution_site_profiles
AS RESTRICTIVE
FOR SELECT TO anon, authenticated
USING (COALESCE(notes, '') <> 'DB_AS_CODE_RELEASE_CANARY');

CREATE POLICY courses_exclude_release_canary
ON public.courses
AS RESTRICTIVE
FOR SELECT TO anon, authenticated
USING (url IS NULL OR url NOT LIKE 'https://canary.invalid/%');
