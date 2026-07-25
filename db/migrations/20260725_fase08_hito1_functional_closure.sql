-- FASE-08 Hito 1 functional closure.
-- Forward-only RPC persistence, public course ACL closure, and strong contract verification.

SET lock_timeout = '5s';
SET statement_timeout = '60s';
SET search_path = '';

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
    IF pg_catalog.jsonb_typeof(p_enriched_data) <> 'array'
       OR pg_catalog.jsonb_array_length(p_enriched_data) <> 1
       OR (p_enriched_data->0->>'cleansed_id')::uuid IS DISTINCT FROM
          p_cleansed_id
       OR NOT EXISTS (
           SELECT 1
           FROM public.cleansed_programs AS cleansed
           WHERE cleansed.id = p_cleansed_id
             AND cleansed.institution_id =
                 (p_enriched_data->0->>'institution_id')::uuid
             AND cleansed.url = p_enriched_data->0->>'url'
       ) THEN
        RAISE EXCEPTION 'Invalid atomic enrichment payload identity';
    END IF;

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
        is_mock_data,
        metadata,
        brochure_url
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
        (item->>'is_mock_data')::boolean,
        COALESCE(NULLIF(item->'metadata', 'null'::jsonb), '{}'::jsonb),
        item->>'brochure_url'
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
        metadata = EXCLUDED.metadata,
        brochure_url = EXCLUDED.brochure_url,
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

ALTER FUNCTION public.atomic_enrichment_promote(jsonb, uuid) OWNER TO postgres;
REVOKE ALL ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid)
FROM PUBLIC, anon, authenticated, service_role CASCADE;
GRANT EXECUTE ON FUNCTION public.atomic_enrichment_promote(jsonb, uuid)
TO service_role;

REVOKE ALL PRIVILEGES ON TABLE public.courses
FROM PUBLIC, anon, authenticated;
REVOKE SELECT (view_count, comparison_count) ON TABLE public.courses
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
    publication_status
) ON TABLE public.courses TO anon, authenticated;
GRANT ALL PRIVILEGES ON TABLE public.courses TO service_role;

CREATE OR REPLACE FUNCTION public.verify_fase08_hito1_contract()
RETURNS boolean
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path = ''
AS $function$
DECLARE
    actual_record record;
    expected_record record;
    expected_columns text[];
    function_record record;
    role_name text;
BEGIN
    IF NOT public.verify_fase07_g1b_closure() THEN
        RETURN false;
    END IF;

    IF (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_class AS relation
        WHERE relation.oid = ANY(ARRAY[
            'public.courses'::regclass,
            'public.leads'::regclass,
            'public.ratings'::regclass,
            'public.reviews'::regclass,
            'public.institution_site_profiles'::regclass
        ])
          AND relation.relkind IN ('r', 'p')
          AND relation.relrowsecurity
    ) <> 5 THEN
        RETURN false;
    END IF;

    FOR expected_record IN
        SELECT *
        FROM (VALUES
            (
                'courses', 'courses_select_public', 'PERMISSIVE',
                ARRAY['anon']::name[], 'SELECT',
                $policy$((is_active = true) AND (is_verified = true) AND (publication_status = 'publicado'::text) AND (EXISTS ( SELECT 1 FROM public.institution_site_profiles profile WHERE ((profile.institution_id = courses.institution_id) AND (profile.production_enabled = true)))))$policy$,
                NULL::text
            ),
            (
                'courses', 'courses_select_authenticated', 'PERMISSIVE',
                ARRAY['authenticated']::name[], 'SELECT',
                $policy$((is_active = true) AND (is_verified = true) AND (publication_status = 'publicado'::text) AND (EXISTS ( SELECT 1 FROM public.institution_site_profiles profile WHERE ((profile.institution_id = courses.institution_id) AND (profile.production_enabled = true)))))$policy$,
                NULL::text
            ),
            (
                'leads', 'leads_insert_public', 'PERMISSIVE',
                ARRAY['anon']::name[], 'INSERT', NULL::text,
                $policy$((length(first_name) > 0) AND (length(first_name) <= 100) AND (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text) AND (length(email) <= 255) AND (length(whatsapp) <= 30) AND ((course_id IS NULL) OR (EXISTS ( SELECT 1 FROM public.courses course WHERE ((course.id = leads.course_id) AND (course.is_active = true) AND (course.is_verified = true) AND (course.publication_status = 'publicado'::text) AND (EXISTS ( SELECT 1 FROM public.institution_site_profiles profile WHERE ((profile.institution_id = course.institution_id) AND (profile.production_enabled = true)))))))) AND (lead_source_type = 'organic'::text))$policy$
            ),
            (
                'leads', 'leads_insert_authenticated', 'PERMISSIVE',
                ARRAY['authenticated']::name[], 'INSERT', NULL::text,
                $policy$((length(first_name) > 0) AND (length(first_name) <= 100) AND (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text) AND (length(email) <= 255) AND (length(whatsapp) <= 30) AND ((course_id IS NULL) OR (EXISTS ( SELECT 1 FROM public.courses course WHERE ((course.id = leads.course_id) AND (course.is_active = true) AND (course.is_verified = true) AND (course.publication_status = 'publicado'::text) AND (EXISTS ( SELECT 1 FROM public.institution_site_profiles profile WHERE ((profile.institution_id = course.institution_id) AND (profile.production_enabled = true)))))))) AND (lead_source_type = 'organic'::text))$policy$
            ),
            (
                'ratings', 'ratings_select_public', 'PERMISSIVE',
                ARRAY['anon', 'authenticated']::name[], 'SELECT',
                $policy$((moderation_status = 'approved'::text) AND (EXISTS ( SELECT 1 FROM (public.courses course JOIN public.institution_site_profiles profile ON ((profile.institution_id = course.institution_id))) WHERE ((course.id = ratings.course_id) AND (course.is_active = true) AND (course.is_verified = true) AND (course.publication_status = 'publicado'::text) AND (profile.production_enabled = true)))))$policy$,
                NULL::text
            ),
            (
                'reviews', 'reviews_select_public', 'PERMISSIVE',
                ARRAY['anon', 'authenticated']::name[], 'SELECT',
                $policy$((moderation_status = 'approved'::text) AND (EXISTS ( SELECT 1 FROM (public.courses course JOIN public.institution_site_profiles profile ON ((profile.institution_id = course.institution_id))) WHERE ((course.id = reviews.course_id) AND (course.is_active = true) AND (course.is_verified = true) AND (course.publication_status = 'publicado'::text) AND (profile.production_enabled = true)))))$policy$,
                NULL::text
            ),
            (
                'institution_site_profiles', 'profiles_select_public',
                'PERMISSIVE', ARRAY['anon', 'authenticated']::name[],
                'SELECT', '(production_enabled = true)', NULL::text
            )
        ) AS expected(
            table_name, policy_name, permissiveness, policy_roles,
            command_name, using_expression, check_expression
        )
    LOOP
        SELECT
            policy.permissive,
            policy.roles,
            policy.cmd,
            pg_catalog.regexp_replace(
                policy.qual, E'\\s+', ' ', 'g'
            ) AS using_expression,
            pg_catalog.regexp_replace(
                policy.with_check, E'\\s+', ' ', 'g'
            ) AS check_expression
        INTO actual_record
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename = expected_record.table_name
          AND policy.policyname = expected_record.policy_name;

        IF NOT FOUND
           OR actual_record.permissive <> expected_record.permissiveness
           OR actual_record.roles IS DISTINCT FROM expected_record.policy_roles
           OR actual_record.cmd <> expected_record.command_name
           OR actual_record.using_expression IS DISTINCT FROM
              expected_record.using_expression
           OR actual_record.check_expression IS DISTINCT FROM
              expected_record.check_expression THEN
            RETURN false;
        END IF;
    END LOOP;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.unnest(ARRAY['anon', 'authenticated']::text[])
            AS denied_role(role_name)
        CROSS JOIN pg_catalog.unnest(ARRAY[
            'public.ratings', 'public.reviews',
            'public.institution_site_profiles'
        ]::text[]) AS denied_table(table_name)
        CROSS JOIN pg_catalog.unnest(
            ARRAY['INSERT', 'UPDATE', 'DELETE', 'TRUNCATE']::text[]
        ) AS denied_privilege(privilege_name)
        WHERE pg_catalog.has_table_privilege(
            denied_role.role_name,
            denied_table.table_name,
            denied_privilege.privilege_name
        )
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_policies AS policy
        CROSS JOIN LATERAL pg_catalog.unnest(policy.roles)
            AS policy_role(role_name)
        WHERE policy.schemaname = 'public'
          AND policy.tablename IN (
              'courses', 'leads', 'ratings', 'reviews',
              'institution_site_profiles'
          )
          AND CASE
              WHEN policy_role.role_name = 'public' THEN true
              ELSE pg_catalog.pg_has_role(
                  'anon', policy_role.role_name, 'MEMBER'
              ) OR pg_catalog.pg_has_role(
                  'authenticated', policy_role.role_name, 'MEMBER'
              )
          END
          AND (policy.tablename, policy.policyname) NOT IN (
              ('courses', 'courses_select_public'),
              ('courses', 'courses_select_authenticated'),
              ('leads', 'leads_insert_public'),
              ('leads', 'leads_insert_authenticated'),
              ('ratings', 'ratings_select_public'),
              ('reviews', 'reviews_select_public'),
              ('institution_site_profiles', 'profiles_select_public')
          )
    ) THEN
        RETURN false;
    END IF;

    IF (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND (policy.tablename, policy.policyname) IN (
              ('courses', 'courses_service_role'),
              ('leads', 'leads_service_role'),
              ('ratings', 'ratings_service_role'),
              ('reviews', 'reviews_service_role')
          )
          AND policy.permissive = 'PERMISSIVE'
          AND policy.cmd = 'ALL'
          AND policy.roles = ARRAY['service_role']::name[]
          AND policy.qual = 'true'
          AND policy.with_check = 'true'
    ) <> 4 THEN
        RETURN false;
    END IF;

    FOR expected_record IN
        SELECT *
        FROM (VALUES
            ('public.courses'::regclass, 'publication_status', 'text'::regtype, true, '''borrador''::text'::text),
            ('public.courses'::regclass, 'data_quality_status', 'text'::regtype, true, '''pendiente''::text'::text),
            ('public.courses'::regclass, 'missing_fields', 'jsonb'::regtype, true, '''[]''::jsonb'::text),
            ('public.courses'::regclass, 'field_sources', 'jsonb'::regtype, true, '''{}''::jsonb'::text),
            ('public.courses'::regclass, 'manual_updated_at', 'timestamptz'::regtype, false, NULL::text),
            ('public.courses'::regclass, 'is_sponsored', 'boolean'::regtype, true, 'false'::text),
            ('public.courses'::regclass, 'sponsorship_priority', 'integer'::regtype, true, '0'::text),
            ('public.courses'::regclass, 'sponsorship_label', 'text'::regtype, false, NULL::text),
            ('public.leads'::regclass, 'lead_source_type', 'text'::regtype, true, '''organic''::text'::text),
            ('public.ratings'::regclass, 'moderation_status', 'text'::regtype, true, '''pending''::text'::text),
            ('public.ratings'::regclass, 'moderated_at', 'timestamptz'::regtype, false, NULL::text),
            ('public.reviews'::regclass, 'moderation_status', 'text'::regtype, true, '''pending''::text'::text),
            ('public.reviews'::regclass, 'moderated_at', 'timestamptz'::regtype, false, NULL::text)
        ) AS expected(
            relation_oid, column_name, type_oid, is_not_null, default_expression
        )
    LOOP
        SELECT
            attribute.atttypid AS type_oid,
            attribute.atttypmod AS type_modifier,
            attribute.attnotnull AS is_not_null,
            attribute.attidentity AS identity_kind,
            attribute.attgenerated AS generated_kind,
            pg_catalog.pg_get_expr(default_record.adbin, default_record.adrelid)
                AS default_expression
        INTO actual_record
        FROM pg_catalog.pg_attribute AS attribute
        LEFT JOIN pg_catalog.pg_attrdef AS default_record
          ON default_record.adrelid = attribute.attrelid
         AND default_record.adnum = attribute.attnum
        WHERE attribute.attrelid = expected_record.relation_oid
          AND attribute.attname = expected_record.column_name
          AND attribute.attnum > 0
          AND NOT attribute.attisdropped;

        IF NOT FOUND
           OR actual_record.type_oid <> expected_record.type_oid
           OR actual_record.type_modifier <> -1
           OR actual_record.is_not_null IS DISTINCT FROM expected_record.is_not_null
           OR actual_record.identity_kind <> ''
           OR actual_record.generated_kind <> ''
           OR actual_record.default_expression IS DISTINCT FROM
              expected_record.default_expression THEN
            RETURN false;
        END IF;
    END LOOP;

    FOR expected_record IN
        SELECT *
        FROM (VALUES
            ('public.courses'::regclass, 'chk_courses_publication_status', 'c'::"char", '%borrador%pendiente_revision%publicado%despublicado%'::text),
            ('public.courses'::regclass, 'chk_courses_data_quality_status', 'c'::"char", '%pendiente%completo%'::text),
            ('public.courses'::regclass, 'chk_courses_missing_fields_array', 'c'::"char", '%jsonb_typeof(missing_fields)%array%'::text),
            ('public.courses'::regclass, 'chk_courses_field_sources_object', 'c'::"char", '%jsonb_typeof(field_sources)%object%'::text),
            ('public.courses'::regclass, 'chk_courses_sponsorship_priority_nonnegative', 'c'::"char", '%sponsorship_priority >= 0%'::text),
            ('public.courses'::regclass, 'chk_courses_sponsorship_label_length', 'c'::"char", '%char_length(sponsorship_label) <= 80%'::text),
            ('public.leads'::regclass, 'chk_leads_source_type', 'c'::"char", '%organic%sponsored%'::text),
            ('public.ratings'::regclass, 'ratings_moderation_status_check', 'c'::"char", '%pending%approved%rejected%'::text),
            ('public.ratings'::regclass, 'ratings_course_id_fkey', 'f'::"char", '%FOREIGN KEY (course_id)%REFERENCES public.courses(id)%'::text),
            ('public.reviews'::regclass, 'reviews_moderation_status_check', 'c'::"char", '%pending%approved%rejected%'::text),
            ('public.reviews'::regclass, 'reviews_course_id_fkey', 'f'::"char", '%FOREIGN KEY (course_id)%REFERENCES public.courses(id)%'::text)
        ) AS expected(relation_oid, constraint_name, constraint_type, definition_pattern)
    LOOP
        SELECT
            constraint_record.contype AS constraint_type,
            constraint_record.convalidated AS is_validated,
            constraint_record.confrelid AS referenced_relation,
            pg_catalog.pg_get_constraintdef(constraint_record.oid, true)
                AS definition
        INTO actual_record
        FROM pg_catalog.pg_constraint AS constraint_record
        WHERE constraint_record.conrelid = expected_record.relation_oid
          AND constraint_record.conname = expected_record.constraint_name;

        IF NOT FOUND
           OR actual_record.constraint_type <> expected_record.constraint_type
           OR NOT actual_record.is_validated
           OR actual_record.definition NOT LIKE expected_record.definition_pattern
           OR (
               expected_record.constraint_type = 'f'
               AND actual_record.referenced_relation <> 'public.courses'::regclass
           )
           OR (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_constraint AS named_constraint
               WHERE named_constraint.connamespace = 'public'::regnamespace
                 AND named_constraint.conname = expected_record.constraint_name
           ) <> 1 THEN
            RETURN false;
        END IF;
    END LOOP;

    FOR expected_record IN
        SELECT *
        FROM (VALUES
            ('idx_courses_publication_quality', 'public.courses'::regclass, 'btree', false, 2, 'publication_status', 'data_quality_status', false, false, '(is_active = true)'::text),
            ('idx_courses_missing_fields_gin', 'public.courses'::regclass, 'gin', false, 1, 'missing_fields', NULL::text, false, false, NULL::text),
            ('idx_courses_sponsored_priority', 'public.courses'::regclass, 'btree', false, 2, 'is_sponsored', 'sponsorship_priority', false, true, '(is_active = true)'::text),
            ('idx_leads_source_type_created_at', 'public.leads'::regclass, 'btree', false, 2, 'lead_source_type', 'created_at', false, true, NULL::text),
            ('ratings_course_nickname_unique', 'public.ratings'::regclass, 'btree', true, 2, 'course_id', 'user_nickname', false, false, NULL::text),
            ('idx_ratings_course_id', 'public.ratings'::regclass, 'btree', false, 1, 'course_id', NULL::text, false, false, NULL::text),
            ('idx_ratings_moderation_status', 'public.ratings'::regclass, 'btree', false, 1, 'moderation_status', NULL::text, false, false, NULL::text),
            ('idx_reviews_course_id', 'public.reviews'::regclass, 'btree', false, 1, 'course_id', NULL::text, false, false, NULL::text),
            ('idx_reviews_moderation_status', 'public.reviews'::regclass, 'btree', false, 1, 'moderation_status', NULL::text, false, false, NULL::text)
        ) AS expected(
            index_name, relation_oid, access_method, is_unique, key_count,
            first_key, second_key, first_descending, second_descending,
            predicate_expression
        )
    LOOP
        SELECT
            access_method.amname AS access_method,
            index_record.indisunique AS is_unique,
            index_record.indisvalid AS is_valid,
            index_record.indisready AS is_ready,
            index_record.indislive AS is_live,
            index_record.indnkeyatts AS key_count,
            pg_catalog.pg_get_indexdef(index_record.indexrelid, 1, true)
                AS first_key,
            CASE
                WHEN index_record.indnkeyatts > 1
                THEN pg_catalog.pg_get_indexdef(index_record.indexrelid, 2, true)
            END AS second_key,
            (index_record.indoption[0] & 1) = 1 AS first_descending,
            CASE
                WHEN index_record.indnkeyatts > 1
                THEN (index_record.indoption[1] & 1) = 1
                ELSE false
            END AS second_descending,
            pg_catalog.pg_get_expr(
                index_record.indpred, index_record.indrelid
            ) AS predicate_expression
        INTO actual_record
        FROM pg_catalog.pg_class AS index_relation
        JOIN pg_catalog.pg_index AS index_record
          ON index_record.indexrelid = index_relation.oid
        JOIN pg_catalog.pg_am AS access_method
          ON access_method.oid = index_relation.relam
        WHERE index_relation.relnamespace = 'public'::regnamespace
          AND index_relation.relname = expected_record.index_name
          AND index_record.indrelid = expected_record.relation_oid;

        IF NOT FOUND
           OR actual_record.access_method <> expected_record.access_method
           OR actual_record.is_unique IS DISTINCT FROM expected_record.is_unique
           OR NOT actual_record.is_valid
           OR NOT actual_record.is_ready
           OR NOT actual_record.is_live
           OR actual_record.key_count <> expected_record.key_count
           OR actual_record.first_key <> expected_record.first_key
           OR actual_record.second_key IS DISTINCT FROM expected_record.second_key
           OR actual_record.first_descending IS DISTINCT FROM
              expected_record.first_descending
           OR actual_record.second_descending IS DISTINCT FROM
              expected_record.second_descending
           OR actual_record.predicate_expression IS DISTINCT FROM
              expected_record.predicate_expression THEN
            RETURN false;
        END IF;
    END LOOP;

    FOREACH role_name IN ARRAY ARRAY['anon', 'authenticated']
    LOOP
        expected_columns := ARRAY[
            'id', 'name', 'slug', 'url', 'institution_id', 'price_pen',
            'price_status', 'mode', 'course_type', 'category_id', 'duration',
            'start_date_text', 'description_long', 'syllabus', 'target_audience',
            'requirements', 'certification', 'benefits', 'objectives',
            'expected_monthly_salary', 'seniority_level', 'roi_months', 'address',
            'region', 'is_active', 'is_verified', 'brochure_url', 'start_date',
            'created_at', 'updated_at', 'publication_status'
        ];
        IF pg_catalog.has_table_privilege(
            role_name, 'public.courses', 'SELECT'
        ) OR EXISTS (
            SELECT 1
            FROM pg_catalog.unnest(
                ARRAY['INSERT', 'UPDATE', 'DELETE', 'TRUNCATE']::text[]
            ) AS denied(privilege_name)
            WHERE pg_catalog.has_table_privilege(
                role_name, 'public.courses', denied.privilege_name
            )
        ) OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_attribute AS attribute
            WHERE attribute.attrelid = 'public.courses'::regclass
              AND attribute.attnum > 0
              AND NOT attribute.attisdropped
              AND pg_catalog.has_column_privilege(
                  role_name, attribute.attrelid, attribute.attnum, 'SELECT'
              ) IS DISTINCT FROM (attribute.attname = ANY(expected_columns))
        ) THEN
            RETURN false;
        END IF;

        expected_columns := ARRAY[
            'id', 'course_id', 'rating_value', 'user_nickname', 'created_at'
        ];
        IF pg_catalog.has_table_privilege(
            role_name, 'public.ratings', 'SELECT'
        ) OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_attribute AS attribute
            WHERE attribute.attrelid = 'public.ratings'::regclass
              AND attribute.attnum > 0
              AND NOT attribute.attisdropped
              AND pg_catalog.has_column_privilege(
                  role_name, attribute.attrelid, attribute.attnum, 'SELECT'
              ) IS DISTINCT FROM (attribute.attname = ANY(expected_columns))
        ) THEN
            RETURN false;
        END IF;

        expected_columns := ARRAY[
            'id', 'course_id', 'content', 'user_nickname', 'created_at'
        ];
        IF pg_catalog.has_table_privilege(
            role_name, 'public.reviews', 'SELECT'
        ) OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_attribute AS attribute
            WHERE attribute.attrelid = 'public.reviews'::regclass
              AND attribute.attnum > 0
              AND NOT attribute.attisdropped
              AND pg_catalog.has_column_privilege(
                  role_name, attribute.attrelid, attribute.attnum, 'SELECT'
              ) IS DISTINCT FROM (attribute.attname = ANY(expected_columns))
        ) THEN
            RETURN false;
        END IF;

        expected_columns := ARRAY['institution_id', 'production_enabled'];
        IF pg_catalog.has_table_privilege(
            role_name, 'public.institution_site_profiles', 'SELECT'
        ) OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_attribute AS attribute
            WHERE attribute.attrelid = 'public.institution_site_profiles'::regclass
              AND attribute.attnum > 0
              AND NOT attribute.attisdropped
              AND pg_catalog.has_column_privilege(
                  role_name, attribute.attrelid, attribute.attnum, 'SELECT'
              ) IS DISTINCT FROM (attribute.attname = ANY(expected_columns))
        ) THEN
            RETURN false;
        END IF;

        IF NOT pg_catalog.has_table_privilege(
            role_name, 'public.leads', 'INSERT'
        ) OR EXISTS (
            SELECT 1
            FROM pg_catalog.unnest(
                ARRAY['SELECT', 'UPDATE', 'DELETE', 'TRUNCATE']::text[]
            ) AS denied(privilege_name)
            WHERE pg_catalog.has_table_privilege(
                role_name, 'public.leads', denied.privilege_name
            )
        ) THEN
            RETURN false;
        END IF;
    END LOOP;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.unnest(ARRAY[
            'public.courses', 'public.leads', 'public.ratings',
            'public.reviews', 'public.institution_site_profiles'
        ]::text[]) AS required_table(table_name)
        CROSS JOIN pg_catalog.unnest(
            ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE']::text[]
        ) AS required_privilege(privilege_name)
        WHERE NOT pg_catalog.has_table_privilege(
            'service_role', required_table.table_name,
            required_privilege.privilege_name
        )
    ) THEN
        RETURN false;
    END IF;

    SELECT
        procedure_record.oid,
        owner.rolname AS owner_name,
        language_record.lanname AS language_name,
        procedure_record.prosecdef,
        procedure_record.proconfig,
        procedure_record.proacl,
        pg_catalog.pg_get_functiondef(procedure_record.oid) AS definition
    INTO function_record
    FROM pg_catalog.pg_proc AS procedure_record
    JOIN pg_catalog.pg_roles AS owner
      ON owner.oid = procedure_record.proowner
    JOIN pg_catalog.pg_language AS language_record
      ON language_record.oid = procedure_record.prolang
    WHERE procedure_record.oid =
        'public.atomic_enrichment_promote(jsonb,uuid)'::regprocedure;

    IF NOT FOUND
       OR function_record.owner_name <> 'postgres'
       OR function_record.language_name <> 'plpgsql'
       OR NOT function_record.prosecdef
       OR function_record.proconfig IS DISTINCT FROM ARRAY['search_path=""']::text[]
       OR function_record.definition NOT LIKE '%metadata = EXCLUDED.metadata%'
       OR function_record.definition NOT LIKE '%brochure_url = EXCLUDED.brochure_url%'
       OR function_record.definition NOT LIKE '%jsonb_array_length(p_enriched_data) <> 1%'
       OR function_record.definition NOT LIKE '%Invalid atomic enrichment payload identity%'
       OR pg_catalog.has_function_privilege(
           'anon', 'public.atomic_enrichment_promote(jsonb,uuid)', 'EXECUTE'
       )
       OR pg_catalog.has_function_privilege(
           'authenticated',
           'public.atomic_enrichment_promote(jsonb,uuid)',
           'EXECUTE'
       )
       OR NOT pg_catalog.has_function_privilege(
           'service_role',
           'public.atomic_enrichment_promote(jsonb,uuid)',
           'EXECUTE'
       ) THEN
        RETURN false;
    END IF;

    SELECT
        procedure_record.oid,
        owner.rolname AS owner_name,
        language_record.lanname AS language_name,
        procedure_record.prosecdef,
        procedure_record.proconfig,
        procedure_record.proacl
    INTO function_record
    FROM pg_catalog.pg_proc AS procedure_record
    JOIN pg_catalog.pg_roles AS owner
      ON owner.oid = procedure_record.proowner
    JOIN pg_catalog.pg_language AS language_record
      ON language_record.oid = procedure_record.prolang
    WHERE procedure_record.oid =
        'public.verify_fase08_hito1_contract()'::regprocedure;

    IF NOT FOUND
       OR function_record.owner_name <> 'postgres'
       OR function_record.language_name <> 'plpgsql'
       OR function_record.prosecdef
       OR function_record.proconfig IS DISTINCT FROM ARRAY['search_path=""']::text[]
       OR pg_catalog.has_function_privilege(
           'anon', 'public.verify_fase08_hito1_contract()', 'EXECUTE'
       )
       OR pg_catalog.has_function_privilege(
           'authenticated', 'public.verify_fase08_hito1_contract()', 'EXECUTE'
       )
       OR NOT pg_catalog.has_function_privilege(
           'service_role', 'public.verify_fase08_hito1_contract()', 'EXECUTE'
       ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.unnest(ARRAY[
            'public.atomic_enrichment_promote(jsonb,uuid)',
            'public.verify_fase08_hito1_contract()'
        ]::text[]) AS protected_function(function_signature)
        JOIN pg_catalog.pg_proc AS procedure_record
          ON procedure_record.oid =
             pg_catalog.to_regprocedure(protected_function.function_signature)
        CROSS JOIN LATERAL pg_catalog.aclexplode(
            COALESCE(
                procedure_record.proacl,
                pg_catalog.acldefault('f', procedure_record.proowner)
            )
        ) AS acl
        WHERE acl.privilege_type = 'EXECUTE'
          AND (
              acl.grantee NOT IN (
                  procedure_record.proowner,
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

    RETURN true;
END;
$function$;

ALTER FUNCTION public.verify_fase08_hito1_contract() OWNER TO postgres;
REVOKE ALL ON FUNCTION public.verify_fase08_hito1_contract()
FROM PUBLIC, anon, authenticated, service_role CASCADE;
GRANT EXECUTE ON FUNCTION public.verify_fase08_hito1_contract()
TO service_role;
