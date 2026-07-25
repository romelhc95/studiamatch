-- FASE-06 G1b forward-only reconciliation.
-- Defines the known ETL and access contract without operational data changes.

SET lock_timeout = '5s';
SET statement_timeout = '60s';
SET search_path = '';

CREATE OR REPLACE FUNCTION public.atomic_cleansing_promote(
    p_staging_ids uuid[],
    p_cleansed_data jsonb
)
RETURNS SETOF public.cleansed_programs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
BEGIN
    INSERT INTO public.cleansed_programs (
        staging_id,
        institution_id,
        url,
        effective_url,
        canonical_url,
        clean_name,
        clean_description,
        modality,
        location,
        base_price,
        currency,
        status,
        metadata
    )
    SELECT
        (item->>'staging_id')::uuid,
        (item->>'institution_id')::uuid,
        item->>'url',
        item->>'effective_url',
        item->>'canonical_url',
        item->>'clean_name',
        item->>'clean_description',
        item->>'modality',
        item->>'location',
        (item->>'base_price')::numeric,
        item->>'currency',
        'pending',
        (item->>'metadata')::jsonb
    FROM pg_catalog.jsonb_array_elements(p_cleansed_data) AS item
    ON CONFLICT (url) DO UPDATE
    SET clean_name = EXCLUDED.clean_name,
        clean_description = EXCLUDED.clean_description,
        status = 'pending';

    UPDATE public.staging_raw
    SET status = 'processed'
    WHERE public.staging_raw.id = ANY(p_staging_ids)
      AND public.staging_raw.status IN ('pending', 'processing');

    RETURN QUERY
    SELECT cleansed.*
    FROM public.cleansed_programs AS cleansed
    WHERE cleansed.url IN (
        SELECT item->>'url'
        FROM pg_catalog.jsonb_array_elements(p_cleansed_data) AS item
    );
END;
$function$;

CREATE OR REPLACE FUNCTION public.atomic_enrichment_promote(
    p_enriched_data jsonb,
    p_cleansed_id uuid
)
RETURNS SETOF public.enriched_programs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
BEGIN
    INSERT INTO public.enriched_programs (
        cleansed_id,
        institution_id,
        url,
        official_name,
        duration_text,
        duration_months,
        total_cost_est,
        requirements,
        graduate_profile,
        curriculum_summary,
        modality,
        primary_campus,
        degree_type,
        start_date,
        partnerships,
        certifications,
        language,
        categories,
        difficulty_level,
        ai_summary,
        status,
        provider_used,
        is_mock_data
    )
    SELECT
        (item->>'cleansed_id')::uuid,
        (item->>'institution_id')::uuid,
        item->>'url',
        item->>'official_name',
        item->>'duration_text',
        COALESCE(NULLIF(item->>'duration_months', '')::numeric, 0)::integer,
        NULLIF(item->>'total_cost_est', '')::numeric,
        item->>'requirements',
        item->>'graduate_profile',
        COALESCE(NULLIF(item->>'curriculum_summary', ''), '{}')::jsonb,
        item->>'modality',
        item->>'primary_campus',
        item->>'degree_type',
        item->>'start_date',
        item->>'partnerships',
        item->>'certifications',
        item->>'language',
        item->>'categories',
        item->>'difficulty_level',
        item->>'ai_summary',
        'pending',
        item->>'provider_used',
        (item->>'is_mock_data')::boolean
    FROM pg_catalog.jsonb_array_elements(p_enriched_data) AS item
    ON CONFLICT (cleansed_id) DO UPDATE
    SET official_name = EXCLUDED.official_name,
        duration_text = EXCLUDED.duration_text,
        duration_months = COALESCE(EXCLUDED.duration_months, 0),
        total_cost_est = EXCLUDED.total_cost_est,
        requirements = EXCLUDED.requirements,
        graduate_profile = EXCLUDED.graduate_profile,
        curriculum_summary = EXCLUDED.curriculum_summary,
        modality = EXCLUDED.modality,
        primary_campus = EXCLUDED.primary_campus,
        degree_type = EXCLUDED.degree_type,
        start_date = EXCLUDED.start_date,
        categories = EXCLUDED.categories,
        difficulty_level = EXCLUDED.difficulty_level,
        ai_summary = EXCLUDED.ai_summary,
        provider_used = EXCLUDED.provider_used,
        is_mock_data = EXCLUDED.is_mock_data,
        status = 'pending';

    UPDATE public.cleansed_programs
    SET status = 'enriched'
    WHERE public.cleansed_programs.id = p_cleansed_id
      AND public.cleansed_programs.status = 'pending';

    RETURN QUERY
    SELECT enriched.*
    FROM public.enriched_programs AS enriched
    WHERE enriched.cleansed_id = p_cleansed_id;
END;
$function$;

CREATE OR REPLACE FUNCTION public.lock_staging_records(
    inst_id uuid,
    batch_size integer DEFAULT 100
)
RETURNS TABLE(
    id uuid,
    url text,
    institution_id uuid,
    raw_html text,
    raw_name text,
    raw_description text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
BEGIN
    RETURN QUERY
    UPDATE public.staging_raw
    SET status = 'processing'
    WHERE public.staging_raw.id IN (
        SELECT candidate.id
        FROM public.staging_raw AS candidate
        WHERE candidate.status = 'pending'
          AND (candidate.institution_id = inst_id OR inst_id IS NULL)
        ORDER BY candidate.last_harvested_at ASC NULLS FIRST
        LIMIT batch_size
        FOR UPDATE SKIP LOCKED
    )
    RETURNING
        public.staging_raw.id,
        public.staging_raw.url,
        public.staging_raw.institution_id,
        public.staging_raw.raw_html,
        public.staging_raw.raw_name,
        public.staging_raw.raw_description;
END;
$function$;

CREATE OR REPLACE FUNCTION public.lock_cleansed_records(
    batch_size integer DEFAULT 10
)
RETURNS TABLE(
    id uuid,
    cleansed_id uuid,
    clean_name text,
    clean_description text,
    institution_id uuid,
    url text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
BEGIN
    RETURN QUERY
    WITH locked AS (
        SELECT candidate.id
        FROM public.cleansed_programs AS candidate
        WHERE candidate.status = 'pending'
        ORDER BY candidate.id ASC
        LIMIT batch_size
        FOR UPDATE SKIP LOCKED
    )
    UPDATE public.cleansed_programs AS target
    SET status = 'processing'
    FROM locked
    WHERE target.id = locked.id
    RETURNING
        target.id,
        target.staging_id,
        target.clean_name,
        target.clean_description,
        target.institution_id,
        target.url;
END;
$function$;

CREATE OR REPLACE FUNCTION public.mark_cleansed_processing(rec_ids uuid[])
RETURNS void
LANGUAGE sql
SECURITY INVOKER
SET search_path = ''
AS $function$
    UPDATE public.cleansed_programs
    SET status = 'processing'
    WHERE public.cleansed_programs.id = ANY(rec_ids)
      AND public.cleansed_programs.status = 'pending';
$function$;

CREATE OR REPLACE FUNCTION public.unlock_staging_record(
    rec_id uuid,
    new_status text,
    reason text DEFAULT NULL
)
RETURNS void
LANGUAGE sql
SECURITY INVOKER
SET search_path = ''
AS $function$
    UPDATE public.staging_raw
    SET status = new_status,
        discard_reason = CASE
            WHEN new_status = 'discarded' THEN reason
            ELSE public.staging_raw.discard_reason
        END,
        processing_error = CASE
            WHEN new_status = 'error' THEN reason
            ELSE public.staging_raw.processing_error
        END
    WHERE public.staging_raw.id = rec_id
      AND public.staging_raw.status = 'processing';
$function$;

CREATE OR REPLACE FUNCTION public.unlock_cleansed_record(
    rec_id uuid,
    new_status text,
    error_msg text DEFAULT NULL
)
RETURNS void
LANGUAGE sql
SECURITY INVOKER
SET search_path = ''
AS $function$
    UPDATE public.cleansed_programs
    SET status = new_status
    WHERE public.cleansed_programs.id = rec_id
      AND public.cleansed_programs.status = 'processing';
$function$;

CREATE OR REPLACE FUNCTION public.requeue_pipeline_records(p_inst_id uuid)
RETURNS TABLE(tbl text, count integer)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
DECLARE
    affected integer;
BEGIN
    WITH updated AS (
        UPDATE public.staging_raw
        SET status = 'pending',
            processing_error = NULL
        WHERE public.staging_raw.institution_id = p_inst_id
          AND public.staging_raw.status = 'skipped'
          AND public.staging_raw.processing_error = 'pipeline_gate=false'
        RETURNING public.staging_raw.id
    )
    SELECT pg_catalog.count(*)::integer
    INTO affected
    FROM updated;

    tbl := 'staging_raw';
    count := affected;
    RETURN NEXT;

    WITH updated AS (
        UPDATE public.cleansed_programs
        SET status = 'pending',
            metadata = COALESCE(public.cleansed_programs.metadata, '{}'::jsonb)
                - 'skip_reason'
        WHERE public.cleansed_programs.institution_id = p_inst_id
          AND public.cleansed_programs.status = 'skipped'
          AND public.cleansed_programs.metadata->>'skip_reason' = 'pipeline_gate=false'
        RETURNING public.cleansed_programs.id
    )
    SELECT pg_catalog.count(*)::integer
    INTO affected
    FROM updated;

    tbl := 'cleansed_programs';
    count := affected;
    RETURN NEXT;

    WITH updated AS (
        UPDATE public.enriched_programs
        SET status = 'pending',
            metadata = COALESCE(public.enriched_programs.metadata, '{}'::jsonb)
                - 'error'
        WHERE public.enriched_programs.institution_id = p_inst_id
          AND public.enriched_programs.status = 'skipped'
          AND public.enriched_programs.metadata->>'error' = 'pipeline_gate=false'
        RETURNING public.enriched_programs.id
    )
    SELECT pg_catalog.count(*)::integer
    INTO affected
    FROM updated;

    tbl := 'enriched_programs';
    count := affected;
    RETURN NEXT;
END;
$function$;

CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $function$
BEGIN
    NEW.updated_at = pg_catalog.now();
    RETURN NEW;
END;
$function$;

ALTER FUNCTION public.atomic_cleansing_promote(uuid[], jsonb) OWNER TO postgres;
ALTER FUNCTION public.atomic_enrichment_promote(jsonb, uuid) OWNER TO postgres;
ALTER FUNCTION public.lock_staging_records(uuid, integer) OWNER TO postgres;
ALTER FUNCTION public.lock_cleansed_records(integer) OWNER TO postgres;
ALTER FUNCTION public.mark_cleansed_processing(uuid[]) OWNER TO postgres;
ALTER FUNCTION public.unlock_staging_record(uuid, text, text) OWNER TO postgres;
ALTER FUNCTION public.unlock_cleansed_record(uuid, text, text) OWNER TO postgres;
ALTER FUNCTION public.requeue_pipeline_records(uuid) OWNER TO postgres;
ALTER FUNCTION public.update_updated_at() OWNER TO postgres;

ALTER TABLE public.cleansed_programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cleansed_programs_no_public_access
ON public.cleansed_programs;
DROP POLICY IF EXISTS cleansed_programs_public_read
ON public.cleansed_programs;
DROP POLICY IF EXISTS cleansed_programs_select_public
ON public.cleansed_programs;
DROP POLICY IF EXISTS "Allow public insert on ratings" ON public.ratings;
DROP POLICY IF EXISTS ratings_insert_public ON public.ratings;
DROP POLICY IF EXISTS "Allow public insert on reviews" ON public.reviews;
DROP POLICY IF EXISTS reviews_insert_public ON public.reviews;

REVOKE ALL PRIVILEGES ON TABLE public.cleansed_programs
FROM PUBLIC, anon, authenticated;
GRANT ALL PRIVILEGES ON TABLE public.cleansed_programs TO service_role;

REVOKE ALL PRIVILEGES ON TABLE public.ratings, public.reviews
FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.ratings, public.reviews TO anon, authenticated;
GRANT ALL PRIVILEGES ON TABLE public.ratings, public.reviews TO service_role;

DROP FUNCTION IF EXISTS public.test_ping();
DROP FUNCTION IF EXISTS public.test_update_single(uuid);
DROP FUNCTION IF EXISTS public.test_update_array(uuid[]);

DROP TRIGGER IF EXISTS set_updated_at ON public.institution_site_profiles;
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON public.institution_site_profiles
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at();

CREATE OR REPLACE FUNCTION public.verify_fase06_g1b_reconciliation()
RETURNS boolean
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $function$
DECLARE
    function_record record;
    function_signature text;
    expected_definer boolean;
    expected_language text;
BEGIN
    IF (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_proc AS procedure
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = procedure.pronamespace
        WHERE namespace.nspname = 'public'
          AND procedure.proname = ANY(ARRAY[
              'atomic_cleansing_promote',
              'atomic_enrichment_promote',
              'lock_staging_records',
              'lock_cleansed_records',
              'mark_cleansed_processing',
              'unlock_staging_record',
              'unlock_cleansed_record',
              'requeue_pipeline_records'
          ])
    ) <> 8 THEN
        RETURN false;
    END IF;

    FOREACH function_signature IN ARRAY ARRAY[
        'public.atomic_cleansing_promote(uuid[],jsonb)',
        'public.atomic_enrichment_promote(jsonb,uuid)',
        'public.lock_staging_records(uuid,integer)',
        'public.lock_cleansed_records(integer)',
        'public.mark_cleansed_processing(uuid[])',
        'public.unlock_staging_record(uuid,text,text)',
        'public.unlock_cleansed_record(uuid,text,text)',
        'public.requeue_pipeline_records(uuid)'
    ]
    LOOP
        SELECT
            procedure.oid,
            procedure.proowner,
            owner.rolname AS owner_name,
            language.lanname AS language_name,
            procedure.prosecdef,
            procedure.proconfig,
            procedure.proacl
        INTO function_record
        FROM pg_catalog.pg_proc AS procedure
        JOIN pg_catalog.pg_roles AS owner ON owner.oid = procedure.proowner
        JOIN pg_catalog.pg_language AS language ON language.oid = procedure.prolang
        WHERE procedure.oid = pg_catalog.to_regprocedure(function_signature);

        IF NOT FOUND THEN
            RETURN false;
        END IF;

        expected_definer := function_signature LIKE 'public.atomic_%'
            OR function_signature LIKE 'public.lock_%'
            OR function_signature = 'public.requeue_pipeline_records(uuid)';
        expected_language := CASE
            WHEN function_signature IN (
                'public.mark_cleansed_processing(uuid[])',
                'public.unlock_staging_record(uuid,text,text)',
                'public.unlock_cleansed_record(uuid,text,text)'
            ) THEN 'sql'
            ELSE 'plpgsql'
        END;

        IF function_record.owner_name <> 'postgres'
           OR function_record.language_name <> expected_language
           OR function_record.prosecdef IS DISTINCT FROM expected_definer
           OR function_record.proconfig IS DISTINCT FROM ARRAY['search_path=""']::text[]
           OR pg_catalog.has_function_privilege('anon', function_record.oid, 'EXECUTE')
           OR pg_catalog.has_function_privilege(
               'authenticated', function_record.oid, 'EXECUTE'
           )
           OR NOT pg_catalog.has_function_privilege(
               'service_role', function_record.oid, 'EXECUTE'
           )
           OR EXISTS (
               SELECT 1
               FROM pg_catalog.aclexplode(
                   COALESCE(
                       function_record.proacl,
                       pg_catalog.acldefault('f', function_record.proowner)
                   )
               ) AS acl
               WHERE acl.privilege_type = 'EXECUTE'
                 AND (
                     acl.grantee NOT IN (
                         function_record.proowner,
                         (
                             SELECT role.oid
                             FROM pg_catalog.pg_roles AS role
                             WHERE role.rolname = 'service_role'
                         )
                     )
                     OR (
                         acl.grantee = (
                             SELECT role.oid
                             FROM pg_catalog.pg_roles AS role
                             WHERE role.rolname = 'service_role'
                         )
                         AND acl.is_grantable
                     )
                 )
           ) THEN
            RETURN false;
        END IF;
    END LOOP;

    IF NOT (
        SELECT relation.relrowsecurity
        FROM pg_catalog.pg_class AS relation
        WHERE relation.oid = 'public.cleansed_programs'::regclass
    )
       OR pg_catalog.has_table_privilege(
           'anon', 'public.cleansed_programs', 'SELECT'
       )
       OR pg_catalog.has_table_privilege(
           'authenticated', 'public.cleansed_programs', 'SELECT'
       )
       OR NOT pg_catalog.has_table_privilege(
           'service_role', 'public.cleansed_programs', 'SELECT'
       )
       OR EXISTS (
           SELECT 1
           FROM pg_catalog.pg_policies AS policy
           WHERE policy.schemaname = 'public'
             AND policy.tablename = 'cleansed_programs'
             AND policy.roles && ARRAY['public', 'anon', 'authenticated']::name[]
       ) THEN
        RETURN false;
    END IF;

    IF NOT (
        SELECT relation.relrowsecurity
        FROM pg_catalog.pg_class AS relation
        WHERE relation.oid = 'public.ratings'::regclass
    ) OR NOT (
        SELECT relation.relrowsecurity
        FROM pg_catalog.pg_class AS relation
        WHERE relation.oid = 'public.reviews'::regclass
    ) OR EXISTS (
        SELECT 1
        FROM pg_catalog.unnest(ARRAY['anon', 'authenticated']::text[])
            AS denied_role(role_name)
        CROSS JOIN pg_catalog.unnest(
            ARRAY['public.ratings', 'public.reviews']::text[]
        ) AS denied_table(table_name)
        CROSS JOIN pg_catalog.unnest(
            ARRAY['INSERT', 'UPDATE', 'DELETE', 'TRUNCATE']::text[]
        ) AS denied_privilege(privilege_name)
        WHERE pg_catalog.has_table_privilege(
            denied_role.role_name,
            denied_table.table_name,
            denied_privilege.privilege_name
        )
    ) OR EXISTS (
        SELECT 1
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename IN ('ratings', 'reviews')
          AND policy.cmd IN ('ALL', 'INSERT', 'UPDATE', 'DELETE')
          AND policy.roles && ARRAY['public', 'anon', 'authenticated']::name[]
    ) THEN
        RETURN false;
    END IF;

    FOREACH function_signature IN ARRAY ARRAY[
        'public.increment_view_count(uuid)',
        'public.increment_view_count_v2(uuid,text)',
        'public.deactivate_courses_when_production_disabled()',
        'public.fn_auto_assign_category()',
        'public.notify_new_lead()',
        'public.update_updated_at_column()',
        'public.update_updated_at()',
        'public.validate_institution_site_profiles_jsonb()',
        'public.repair_jsonb_array(jsonb)',
        'public.repair_jsonb_object(jsonb)',
        'public.rls_auto_enable()'
    ]
    LOOP
        IF pg_catalog.to_regprocedure(function_signature) IS NULL THEN
            CONTINUE;
        END IF;

        SELECT
            procedure.oid,
            procedure.proowner,
            procedure.proacl
        INTO STRICT function_record
        FROM pg_catalog.pg_proc AS procedure
        WHERE procedure.oid = pg_catalog.to_regprocedure(function_signature);

        IF pg_catalog.has_function_privilege('anon', function_record.oid, 'EXECUTE')
           OR pg_catalog.has_function_privilege(
               'authenticated', function_record.oid, 'EXECUTE'
           )
           OR NOT pg_catalog.has_function_privilege(
               'service_role', function_record.oid, 'EXECUTE'
           )
           OR EXISTS (
               SELECT 1
               FROM pg_catalog.aclexplode(
                   COALESCE(
                       function_record.proacl,
                       pg_catalog.acldefault('f', function_record.proowner)
                   )
               ) AS acl
               WHERE acl.privilege_type = 'EXECUTE'
                 AND (
                     acl.grantee NOT IN (
                         function_record.proowner,
                         (
                             SELECT role.oid
                             FROM pg_catalog.pg_roles AS role
                             WHERE role.rolname = 'service_role'
                         )
                     )
                     OR (
                         acl.grantee = (
                             SELECT role.oid
                             FROM pg_catalog.pg_roles AS role
                             WHERE role.rolname = 'service_role'
                         )
                         AND acl.is_grantable
                     )
                 )
           ) THEN
            RETURN false;
        END IF;
    END LOOP;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_proc AS procedure
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = procedure.pronamespace
        WHERE namespace.nspname = 'public'
          AND procedure.proname LIKE 'test\_%' ESCAPE '\'
    ) OR NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger
        WHERE trigger.tgrelid = 'public.institution_site_profiles'::regclass
          AND trigger.tgname = 'set_updated_at'
          AND trigger.tgfoid = 'public.update_updated_at()'::regprocedure
          AND trigger.tgtype = 19
          AND trigger.tgenabled = 'O'
          AND NOT trigger.tgisinternal
    ) THEN
        RETURN false;
    END IF;

    RETURN true;
END;
$function$;

ALTER FUNCTION public.verify_fase06_g1b_reconciliation() OWNER TO postgres;

REVOKE ALL ON FUNCTION
    public.atomic_cleansing_promote(uuid[], jsonb),
    public.atomic_enrichment_promote(jsonb, uuid),
    public.lock_staging_records(uuid, integer),
    public.lock_cleansed_records(integer),
    public.mark_cleansed_processing(uuid[]),
    public.unlock_staging_record(uuid, text, text),
    public.unlock_cleansed_record(uuid, text, text),
    public.requeue_pipeline_records(uuid),
    public.increment_view_count(uuid),
    public.deactivate_courses_when_production_disabled(),
    public.fn_auto_assign_category(),
    public.notify_new_lead(),
    public.update_updated_at_column(),
    public.update_updated_at(),
    public.validate_institution_site_profiles_jsonb(),
    public.repair_jsonb_array(jsonb),
    public.repair_jsonb_object(jsonb),
    public.rls_auto_enable(),
    public.verify_fase06_g1b_reconciliation()
FROM PUBLIC, anon, authenticated, service_role CASCADE;

GRANT EXECUTE ON FUNCTION
    public.atomic_cleansing_promote(uuid[], jsonb),
    public.atomic_enrichment_promote(jsonb, uuid),
    public.lock_staging_records(uuid, integer),
    public.lock_cleansed_records(integer),
    public.mark_cleansed_processing(uuid[]),
    public.unlock_staging_record(uuid, text, text),
    public.unlock_cleansed_record(uuid, text, text),
    public.requeue_pipeline_records(uuid),
    public.increment_view_count(uuid),
    public.deactivate_courses_when_production_disabled(),
    public.fn_auto_assign_category(),
    public.notify_new_lead(),
    public.update_updated_at_column(),
    public.update_updated_at(),
    public.validate_institution_site_profiles_jsonb(),
    public.repair_jsonb_array(jsonb),
    public.repair_jsonb_object(jsonb),
    public.rls_auto_enable(),
    public.verify_fase06_g1b_reconciliation()
TO service_role;
