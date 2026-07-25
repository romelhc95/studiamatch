-- FASE-06 Hito 1 editorial, quality, sponsorship, and moderation contract.
-- This migration contains schema, RLS, policy, and grant changes only.

SET lock_timeout = '5s';
SET statement_timeout = '60s';
SET search_path = '';

ALTER TABLE public.courses
    ADD COLUMN IF NOT EXISTS publication_status text NOT NULL DEFAULT 'borrador',
    ADD COLUMN IF NOT EXISTS data_quality_status text NOT NULL DEFAULT 'pendiente',
    ADD COLUMN IF NOT EXISTS missing_fields jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS field_sources jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS manual_updated_at timestamptz,
    ADD COLUMN IF NOT EXISTS is_sponsored boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS sponsorship_priority integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS sponsorship_label text;

ALTER TABLE public.leads
    ADD COLUMN IF NOT EXISTS lead_source_type text NOT NULL DEFAULT 'organic';

ALTER TABLE public.ratings
    ADD COLUMN IF NOT EXISTS moderation_status text NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS moderated_at timestamptz;

ALTER TABLE public.reviews
    ADD COLUMN IF NOT EXISTS moderation_status text NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS moderated_at timestamptz;

ALTER TABLE public.courses
    ALTER COLUMN publication_status SET DEFAULT 'borrador',
    ALTER COLUMN publication_status SET NOT NULL,
    ALTER COLUMN data_quality_status SET DEFAULT 'pendiente',
    ALTER COLUMN data_quality_status SET NOT NULL,
    ALTER COLUMN missing_fields SET DEFAULT '[]'::jsonb,
    ALTER COLUMN missing_fields SET NOT NULL,
    ALTER COLUMN field_sources SET DEFAULT '{}'::jsonb,
    ALTER COLUMN field_sources SET NOT NULL,
    ALTER COLUMN is_sponsored SET DEFAULT false,
    ALTER COLUMN is_sponsored SET NOT NULL,
    ALTER COLUMN sponsorship_priority SET DEFAULT 0,
    ALTER COLUMN sponsorship_priority SET NOT NULL;

ALTER TABLE public.leads
    ALTER COLUMN lead_source_type SET DEFAULT 'organic',
    ALTER COLUMN lead_source_type SET NOT NULL;

ALTER TABLE public.ratings
    ALTER COLUMN moderation_status SET DEFAULT 'pending',
    ALTER COLUMN moderation_status SET NOT NULL;

ALTER TABLE public.reviews
    ALTER COLUMN moderation_status SET DEFAULT 'pending',
    ALTER COLUMN moderation_status SET NOT NULL;

ALTER TABLE public.courses
    DROP CONSTRAINT IF EXISTS chk_courses_publication_status,
    DROP CONSTRAINT IF EXISTS chk_courses_data_quality_status,
    DROP CONSTRAINT IF EXISTS chk_courses_missing_fields_array,
    DROP CONSTRAINT IF EXISTS chk_courses_field_sources_object,
    DROP CONSTRAINT IF EXISTS chk_courses_sponsorship_priority_nonnegative,
    DROP CONSTRAINT IF EXISTS chk_courses_sponsorship_label_length;

ALTER TABLE public.courses
    ADD CONSTRAINT chk_courses_publication_status
        CHECK (
            publication_status IN (
                'borrador',
                'pendiente_revision',
                'publicado',
                'despublicado'
            )
        ),
    ADD CONSTRAINT chk_courses_data_quality_status
        CHECK (data_quality_status IN ('pendiente', 'completo')),
    ADD CONSTRAINT chk_courses_missing_fields_array
        CHECK (pg_catalog.jsonb_typeof(missing_fields) = 'array'),
    ADD CONSTRAINT chk_courses_field_sources_object
        CHECK (pg_catalog.jsonb_typeof(field_sources) = 'object'),
    ADD CONSTRAINT chk_courses_sponsorship_priority_nonnegative
        CHECK (sponsorship_priority >= 0),
    ADD CONSTRAINT chk_courses_sponsorship_label_length
        CHECK (
            sponsorship_label IS NULL
            OR pg_catalog.char_length(sponsorship_label) <= 80
        );

ALTER TABLE public.leads
    DROP CONSTRAINT IF EXISTS chk_leads_source_type;
ALTER TABLE public.leads
    ADD CONSTRAINT chk_leads_source_type
        CHECK (lead_source_type IN ('organic', 'sponsored'));

ALTER TABLE public.ratings
    DROP CONSTRAINT IF EXISTS ratings_moderation_status_check,
    DROP CONSTRAINT IF EXISTS ratings_course_id_fkey;
ALTER TABLE public.ratings
    ADD CONSTRAINT ratings_moderation_status_check
        CHECK (moderation_status IN ('pending', 'approved', 'rejected')),
    ADD CONSTRAINT ratings_course_id_fkey
        FOREIGN KEY (course_id) REFERENCES public.courses(id);

ALTER TABLE public.reviews
    DROP CONSTRAINT IF EXISTS reviews_moderation_status_check,
    DROP CONSTRAINT IF EXISTS reviews_course_id_fkey;
ALTER TABLE public.reviews
    ADD CONSTRAINT reviews_moderation_status_check
        CHECK (moderation_status IN ('pending', 'approved', 'rejected')),
    ADD CONSTRAINT reviews_course_id_fkey
        FOREIGN KEY (course_id) REFERENCES public.courses(id);

CREATE INDEX IF NOT EXISTS idx_courses_publication_quality
    ON public.courses (publication_status, data_quality_status)
    WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_courses_missing_fields_gin
    ON public.courses USING gin (missing_fields);
CREATE INDEX IF NOT EXISTS idx_courses_sponsored_priority
    ON public.courses (is_sponsored, sponsorship_priority DESC)
    WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_leads_source_type_created_at
    ON public.leads (lead_source_type, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS ratings_course_nickname_unique
    ON public.ratings (course_id, user_nickname);
CREATE INDEX IF NOT EXISTS idx_ratings_course_id
    ON public.ratings (course_id);
CREATE INDEX IF NOT EXISTS idx_ratings_moderation_status
    ON public.ratings (moderation_status);
CREATE INDEX IF NOT EXISTS idx_reviews_course_id
    ON public.reviews (course_id);
CREATE INDEX IF NOT EXISTS idx_reviews_moderation_status
    ON public.reviews (moderation_status);

COMMENT ON COLUMN public.courses.publication_status IS
    'Editorial state independent from ETL state.';
COMMENT ON COLUMN public.courses.data_quality_status IS
    'Data quality state for editorial review.';
COMMENT ON COLUMN public.courses.missing_fields IS
    'JSON array of missing editorial fields.';
COMMENT ON COLUMN public.courses.field_sources IS
    'JSON object mapping fields to their source.';
COMMENT ON COLUMN public.courses.manual_updated_at IS
    'Time of the latest manual editorial update.';
COMMENT ON COLUMN public.courses.is_sponsored IS
    'Base sponsorship flag.';
COMMENT ON COLUMN public.courses.sponsorship_priority IS
    'Nonnegative sponsorship display priority.';
COMMENT ON COLUMN public.courses.sponsorship_label IS
    'Optional public sponsorship label.';
COMMENT ON COLUMN public.leads.lead_source_type IS
    'Lead classification: organic or sponsored.';
COMMENT ON COLUMN public.ratings.moderation_status IS
    'Moderation state for a rating.';
COMMENT ON COLUMN public.reviews.moderation_status IS
    'Moderation state for a review.';

ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institution_site_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public read for courses" ON public.courses;
DROP POLICY IF EXISTS "Anyone can insert leads" ON public.leads;
DROP POLICY IF EXISTS "Allow public insert on ratings" ON public.ratings;
DROP POLICY IF EXISTS "Allow public read access on ratings" ON public.ratings;
DROP POLICY IF EXISTS "Allow public insert on reviews" ON public.reviews;
DROP POLICY IF EXISTS "Allow public read access on reviews" ON public.reviews;

DROP POLICY IF EXISTS profiles_select_public
ON public.institution_site_profiles;
CREATE POLICY profiles_select_public
ON public.institution_site_profiles
FOR SELECT
TO anon, authenticated
USING (production_enabled = true);

DROP POLICY IF EXISTS courses_select_public ON public.courses;
CREATE POLICY courses_select_public
ON public.courses
FOR SELECT
TO anon
USING (
    is_active = true
    AND is_verified = true
    AND publication_status = 'publicado'
    AND EXISTS (
        SELECT 1
        FROM public.institution_site_profiles AS profile
        WHERE profile.institution_id = courses.institution_id
          AND profile.production_enabled = true
    )
);

DROP POLICY IF EXISTS courses_select_authenticated ON public.courses;
CREATE POLICY courses_select_authenticated
ON public.courses
FOR SELECT
TO authenticated
USING (
    is_active = true
    AND is_verified = true
    AND publication_status = 'publicado'
    AND EXISTS (
        SELECT 1
        FROM public.institution_site_profiles AS profile
        WHERE profile.institution_id = courses.institution_id
          AND profile.production_enabled = true
    )
);

DROP POLICY IF EXISTS leads_insert_public ON public.leads;
CREATE POLICY leads_insert_public
ON public.leads
FOR INSERT
TO anon
WITH CHECK (
    pg_catalog.length(first_name::text) > 0
    AND pg_catalog.length(first_name::text) <= 100
    AND email::text ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    AND pg_catalog.length(email::text) <= 255
    AND pg_catalog.length(whatsapp::text) <= 30
    AND (
        course_id IS NULL
        OR EXISTS (
            SELECT 1
            FROM public.courses AS course
            WHERE course.id = leads.course_id
              AND course.is_active = true
              AND course.is_verified = true
              AND course.publication_status = 'publicado'
              AND EXISTS (
                  SELECT 1
                  FROM public.institution_site_profiles AS profile
                  WHERE profile.institution_id = course.institution_id
                    AND profile.production_enabled = true
              )
        )
    )
    AND lead_source_type = 'organic'
);

DROP POLICY IF EXISTS leads_insert_authenticated ON public.leads;
CREATE POLICY leads_insert_authenticated
ON public.leads
FOR INSERT
TO authenticated
WITH CHECK (
    pg_catalog.length(first_name::text) > 0
    AND pg_catalog.length(first_name::text) <= 100
    AND email::text ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    AND pg_catalog.length(email::text) <= 255
    AND pg_catalog.length(whatsapp::text) <= 30
    AND (
        course_id IS NULL
        OR EXISTS (
            SELECT 1
            FROM public.courses AS course
            WHERE course.id = leads.course_id
              AND course.is_active = true
              AND course.is_verified = true
              AND course.publication_status = 'publicado'
              AND EXISTS (
                  SELECT 1
                  FROM public.institution_site_profiles AS profile
                  WHERE profile.institution_id = course.institution_id
                    AND profile.production_enabled = true
              )
        )
    )
    AND lead_source_type = 'organic'
);

DROP POLICY IF EXISTS ratings_select_public ON public.ratings;
CREATE POLICY ratings_select_public
ON public.ratings
FOR SELECT
TO anon, authenticated
USING (
    moderation_status = 'approved'
    AND EXISTS (
        SELECT 1
        FROM public.courses AS course
        JOIN public.institution_site_profiles AS profile
          ON profile.institution_id = course.institution_id
        WHERE course.id = ratings.course_id
          AND course.is_active = true
          AND course.is_verified = true
          AND course.publication_status = 'publicado'
          AND profile.production_enabled = true
    )
);

DROP POLICY IF EXISTS reviews_select_public ON public.reviews;
CREATE POLICY reviews_select_public
ON public.reviews
FOR SELECT
TO anon, authenticated
USING (
    moderation_status = 'approved'
    AND EXISTS (
        SELECT 1
        FROM public.courses AS course
        JOIN public.institution_site_profiles AS profile
          ON profile.institution_id = course.institution_id
        WHERE course.id = reviews.course_id
          AND course.is_active = true
          AND course.is_verified = true
          AND course.publication_status = 'publicado'
          AND profile.production_enabled = true
    )
);

DROP POLICY IF EXISTS courses_service_role ON public.courses;
CREATE POLICY courses_service_role
ON public.courses
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS leads_service_role ON public.leads;
CREATE POLICY leads_service_role
ON public.leads
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS ratings_service_role ON public.ratings;
CREATE POLICY ratings_service_role
ON public.ratings
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS reviews_service_role ON public.reviews;
CREATE POLICY reviews_service_role
ON public.reviews
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

REVOKE ALL PRIVILEGES ON TABLE public.courses
FROM PUBLIC, anon, authenticated;
GRANT SELECT (
    id,
    name,
    slug,
    url,
    institution_id,
    price_pen,
    price_status,
    mode,
    course_type,
    category_id,
    duration,
    start_date_text,
    description_long,
    syllabus,
    target_audience,
    requirements,
    certification,
    benefits,
    objectives,
    expected_monthly_salary,
    seniority_level,
    roi_months,
    address,
    region,
    is_active,
    is_verified,
    brochure_url,
    start_date,
    created_at,
    updated_at,
    view_count,
    comparison_count,
    publication_status
) ON TABLE public.courses TO anon, authenticated;
GRANT ALL PRIVILEGES ON TABLE public.courses TO service_role;

REVOKE ALL PRIVILEGES ON TABLE public.leads
FROM PUBLIC, anon, authenticated;
GRANT INSERT ON TABLE public.leads TO anon, authenticated;
GRANT ALL PRIVILEGES ON TABLE public.leads TO service_role;

REVOKE ALL PRIVILEGES ON TABLE public.ratings, public.reviews
FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.ratings, public.reviews TO anon, authenticated;
GRANT ALL PRIVILEGES ON TABLE public.ratings, public.reviews TO service_role;

REVOKE ALL PRIVILEGES ON TABLE public.institution_site_profiles
FROM PUBLIC, anon, authenticated;
GRANT SELECT (institution_id, production_enabled)
ON TABLE public.institution_site_profiles
TO anon, authenticated;
GRANT ALL PRIVILEGES ON TABLE public.institution_site_profiles TO service_role;

CREATE OR REPLACE FUNCTION public.verify_fase06_hito1_contract()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = ''
AS $function$
    SELECT
        (
            SELECT pg_catalog.count(*) = 13
            FROM pg_catalog.pg_attribute AS attribute
            WHERE attribute.attrelid IN (
                'public.courses'::regclass,
                'public.leads'::regclass,
                'public.ratings'::regclass,
                'public.reviews'::regclass
            )
              AND (attribute.attrelid, attribute.attname) IN (
                  ('public.courses'::regclass, 'publication_status'),
                  ('public.courses'::regclass, 'data_quality_status'),
                  ('public.courses'::regclass, 'missing_fields'),
                  ('public.courses'::regclass, 'field_sources'),
                  ('public.courses'::regclass, 'manual_updated_at'),
                  ('public.courses'::regclass, 'is_sponsored'),
                  ('public.courses'::regclass, 'sponsorship_priority'),
                  ('public.courses'::regclass, 'sponsorship_label'),
                  ('public.leads'::regclass, 'lead_source_type'),
                  ('public.ratings'::regclass, 'moderation_status'),
                  ('public.ratings'::regclass, 'moderated_at'),
                  ('public.reviews'::regclass, 'moderation_status'),
                  ('public.reviews'::regclass, 'moderated_at')
              )
              AND attribute.attnum > 0
              AND NOT attribute.attisdropped
        )
        AND (
            SELECT pg_catalog.count(*) = 11
            FROM pg_catalog.pg_constraint AS constraint_record
            WHERE constraint_record.connamespace = 'public'::regnamespace
              AND constraint_record.conname = ANY(ARRAY[
                  'chk_courses_publication_status',
                  'chk_courses_data_quality_status',
                  'chk_courses_missing_fields_array',
                  'chk_courses_field_sources_object',
                  'chk_courses_sponsorship_priority_nonnegative',
                  'chk_courses_sponsorship_label_length',
                  'chk_leads_source_type',
                  'ratings_moderation_status_check',
                  'ratings_course_id_fkey',
                  'reviews_moderation_status_check',
                  'reviews_course_id_fkey'
              ])
              AND constraint_record.convalidated
        )
        AND NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_policies AS policy
            WHERE policy.schemaname = 'public'
              AND policy.tablename = 'courses'
              AND policy.roles && ARRAY['public', 'anon', 'authenticated']::name[]
              AND policy.permissive = 'PERMISSIVE'
              AND policy.policyname NOT IN (
                  'courses_select_public',
                  'courses_select_authenticated'
              )
        )
        AND NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_policies AS policy
            WHERE policy.schemaname = 'public'
              AND policy.tablename IN ('ratings', 'reviews')
              AND policy.roles && ARRAY['public', 'anon', 'authenticated']::name[]
              AND policy.cmd IN ('ALL', 'INSERT', 'UPDATE', 'DELETE')
        )
        AND EXISTS (
            SELECT 1
            FROM pg_catalog.pg_policies AS policy
            WHERE policy.schemaname = 'public'
              AND policy.tablename = 'courses'
              AND policy.policyname = 'courses_select_public'
              AND policy.qual LIKE '%publication_status%publicado%'
              AND policy.qual LIKE '%production_enabled%'
        )
        AND EXISTS (
            SELECT 1
            FROM pg_catalog.pg_policies AS policy
            WHERE policy.schemaname = 'public'
              AND policy.tablename = 'leads'
              AND policy.policyname = 'leads_insert_public'
              AND policy.with_check LIKE '%lead_source_type%organic%'
              AND policy.with_check LIKE '%publication_status%publicado%'
        )
        AND EXISTS (
            SELECT 1
            FROM pg_catalog.pg_policies AS policy
            WHERE policy.schemaname = 'public'
              AND policy.tablename = 'ratings'
              AND policy.policyname = 'ratings_select_public'
              AND policy.qual LIKE '%moderation_status%approved%'
        )
        AND EXISTS (
            SELECT 1
            FROM pg_catalog.pg_policies AS policy
            WHERE policy.schemaname = 'public'
              AND policy.tablename = 'reviews'
              AND policy.policyname = 'reviews_select_public'
              AND policy.qual LIKE '%moderation_status%approved%'
        )
        AND NOT pg_catalog.has_column_privilege(
            'anon', 'public.courses', 'missing_fields', 'SELECT'
        )
        AND NOT pg_catalog.has_column_privilege(
            'authenticated', 'public.courses', 'field_sources', 'SELECT'
        )
        AND pg_catalog.has_column_privilege(
            'anon', 'public.courses', 'name', 'SELECT'
        )
        AND pg_catalog.has_column_privilege(
            'anon', 'public.courses', 'publication_status', 'SELECT'
        )
        AND pg_catalog.has_table_privilege(
            'service_role', 'public.courses', 'UPDATE'
        );
$function$;

ALTER FUNCTION public.verify_fase06_hito1_contract() OWNER TO postgres;
REVOKE ALL ON FUNCTION public.verify_fase06_hito1_contract()
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.verify_fase06_hito1_contract()
TO service_role;
