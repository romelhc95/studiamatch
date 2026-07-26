\set ON_ERROR_STOP on

-- TEST-ONLY reconstruction of the four policies that survived the v1 overlay.
CREATE ROLE authenticator LOGIN NOINHERIT;
GRANT anon, authenticated, service_role TO authenticator;
CREATE ROLE canary_runner NOLOGIN NOINHERIT NOBYPASSRLS NOSUPERUSER;
GRANT canary_runner TO authenticator;
GRANT USAGE ON SCHEMA public TO canary_runner;
GRANT SELECT ON TABLE
    public.institutions,
    public.institution_site_profiles,
    public.courses
TO canary_runner;

CREATE POLICY institutions_canary_runner_select
ON public.institutions
AS PERMISSIVE
FOR SELECT
TO canary_runner
USING (slug LIKE 'zz-studiamatch-canary-%');

CREATE POLICY profiles_canary_runner_select
ON public.institution_site_profiles
AS PERMISSIVE
FOR SELECT
TO canary_runner
USING (COALESCE(notes, '') = 'DB_AS_CODE_RELEASE_CANARY');

CREATE POLICY courses_canary_runner_select
ON public.courses
AS PERMISSIVE
FOR SELECT
TO canary_runner
USING (url LIKE 'https://canary.invalid/%');

CREATE POLICY profiles_service_role
ON public.institution_site_profiles
AS PERMISSIVE
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- This expected service policy completes the observed pre-overlay inventory.
CREATE POLICY institutions_service_role
ON public.institutions
AS PERMISSIVE
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
