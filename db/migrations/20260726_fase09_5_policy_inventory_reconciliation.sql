-- FASE-09.5 forward-only reconciliation of the historical policy inventory.

SET lock_timeout = '5s';
SET statement_timeout = '60s';
SET search_path = '';

ALTER TABLE public.institutions OWNER TO postgres;
ALTER TABLE public.institution_site_profiles OWNER TO postgres;
ALTER TABLE public.courses OWNER TO postgres;
ALTER SCHEMA public OWNER TO pg_database_owner;

REVOKE ALL PRIVILEGES ON SCHEMA public
FROM PUBLIC, anon, authenticated, service_role, canary_runner CASCADE;
GRANT USAGE ON SCHEMA public TO PUBLIC;

REVOKE ALL PRIVILEGES ON TABLE
    public.institutions,
    public.institution_site_profiles,
    public.courses,
    public.leads,
    public.ratings,
    public.reviews
FROM canary_runner CASCADE;
GRANT SELECT ON TABLE
    public.institutions,
    public.institution_site_profiles,
    public.courses
TO canary_runner;

DROP POLICY IF EXISTS institutions_canary_runner_select
ON public.institutions;
CREATE POLICY institutions_canary_runner_select
ON public.institutions
AS PERMISSIVE
FOR SELECT
TO canary_runner
USING (slug LIKE 'zz-studiamatch-canary-%');

DROP POLICY IF EXISTS profiles_canary_runner_select
ON public.institution_site_profiles;
CREATE POLICY profiles_canary_runner_select
ON public.institution_site_profiles
AS PERMISSIVE
FOR SELECT
TO canary_runner
USING (COALESCE(notes, '') = 'DB_AS_CODE_RELEASE_CANARY');

DROP POLICY IF EXISTS courses_canary_runner_select
ON public.courses;
CREATE POLICY courses_canary_runner_select
ON public.courses
AS PERMISSIVE
FOR SELECT
TO canary_runner
USING (url LIKE 'https://canary.invalid/%');

DROP POLICY IF EXISTS profiles_service_role
ON public.institution_site_profiles;
CREATE POLICY profiles_service_role
ON public.institution_site_profiles
AS PERMISSIVE
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

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
            'public.institution_site_profiles'::regclass,
            'public.institutions'::regclass
        ])
          AND relation.relkind IN ('r', 'p')
          AND relation.relrowsecurity
    ) <> 6 THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_class AS relation
        JOIN pg_catalog.pg_roles AS owner
          ON owner.oid = relation.relowner
        WHERE relation.oid = ANY(ARRAY[
            'public.courses'::regclass,
            'public.leads'::regclass,
            'public.ratings'::regclass,
            'public.reviews'::regclass,
            'public.institution_site_profiles'::regclass,
            'public.institutions'::regclass
        ])
          AND owner.rolname <> 'postgres'
    ) OR EXISTS (
        SELECT 1
        FROM pg_catalog.pg_roles AS public_role
        WHERE public_role.rolname IN ('anon', 'authenticated')
          AND (
              public_role.rolsuper
              OR public_role.rolbypassrls
              OR public_role.rolcanlogin
              OR NOT public_role.rolinherit
              OR public_role.rolcreaterole
              OR public_role.rolcreatedb
              OR public_role.rolreplication
              OR EXISTS (
                  SELECT 1
                  FROM pg_catalog.pg_auth_members AS membership
                  LEFT JOIN pg_catalog.pg_roles AS member_role
                    ON member_role.oid = membership.member
                  WHERE membership.member = public_role.oid
                     OR (
                         membership.roleid = public_role.oid
                         AND (
                             member_role.rolname IS DISTINCT FROM 'authenticator'
                             OR membership.admin_option
                             OR membership.inherit_option
                             OR NOT membership.set_option
                         )
                     )
              )
              OR (
                  SELECT pg_catalog.count(*)
                  FROM pg_catalog.pg_auth_members AS membership
                  JOIN pg_catalog.pg_roles AS member_role
                    ON member_role.oid = membership.member
                  WHERE membership.roleid = public_role.oid
                    AND member_role.rolname = 'authenticator'
              ) <> 1
              OR EXISTS (
                  SELECT 1
                  FROM pg_catalog.pg_roles AS privileged_role
                  WHERE (
                      privileged_role.rolsuper
                      OR privileged_role.rolbypassrls
                  )
                    AND pg_catalog.pg_has_role(
                        public_role.oid, privileged_role.oid, 'MEMBER'
                    )
              )
          )
    ) THEN
        RETURN false;
    END IF;

    IF NOT COALESCE((
        SELECT authenticator.rolcanlogin
           AND NOT authenticator.rolinherit
           AND NOT authenticator.rolsuper
           AND NOT authenticator.rolbypassrls
           AND NOT authenticator.rolcreaterole
           AND NOT authenticator.rolcreatedb
           AND NOT authenticator.rolreplication
           AND NOT EXISTS (
               SELECT 1
               FROM pg_catalog.pg_auth_members AS membership
               WHERE membership.roleid = authenticator.oid
           )
           AND NOT EXISTS (
               SELECT 1
               FROM pg_catalog.pg_auth_members AS membership
               JOIN pg_catalog.pg_roles AS granted_role
                 ON granted_role.oid = membership.roleid
               WHERE membership.member = authenticator.oid
                 AND (
                     granted_role.rolname NOT IN (
                         'anon', 'authenticated', 'service_role', 'canary_runner'
                     )
                     OR membership.admin_option
                     OR membership.inherit_option
                     OR NOT membership.set_option
                 )
           )
           AND NOT EXISTS (
               SELECT expected.role_name
               FROM pg_catalog.unnest(ARRAY[
                   'anon', 'authenticated', 'service_role', 'canary_runner'
               ]::text[]) AS expected(role_name)
               EXCEPT ALL
               SELECT granted_role.rolname
               FROM pg_catalog.pg_auth_members AS membership
               JOIN pg_catalog.pg_roles AS granted_role
                 ON granted_role.oid = membership.roleid
               WHERE membership.member = authenticator.oid
                 AND NOT membership.admin_option
                 AND NOT membership.inherit_option
                 AND membership.set_option
           )
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_auth_members AS membership
               WHERE membership.member = authenticator.oid
                 AND NOT membership.admin_option
                 AND NOT membership.inherit_option
                 AND membership.set_option
           ) = 4
        FROM pg_catalog.pg_roles AS authenticator
        WHERE authenticator.rolname = 'authenticator'
    ), false) THEN
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
                'courses', 'courses_exclude_release_canary', 'RESTRICTIVE',
                ARRAY['anon', 'authenticated']::name[], 'SELECT',
                $policy$(((url IS NULL) OR (url !~~ 'https://canary.invalid/%'::text)) AND (EXISTS ( SELECT 1 FROM public.institutions institution_record WHERE (institution_record.id = courses.institution_id))))$policy$,
                NULL::text
            ),
            (
                'courses', 'courses_canary_runner_select', 'PERMISSIVE',
                ARRAY['canary_runner']::name[], 'SELECT',
                $policy$(url ~~ 'https://canary.invalid/%'::text)$policy$,
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
            ),
            (
                'institution_site_profiles',
                'profiles_exclude_release_canary', 'RESTRICTIVE',
                ARRAY['anon', 'authenticated']::name[], 'SELECT',
                $policy$((COALESCE(notes, ''::text) <> 'DB_AS_CODE_RELEASE_CANARY'::text) AND (EXISTS ( SELECT 1 FROM public.institutions institution_record WHERE (institution_record.id = institution_site_profiles.institution_id))))$policy$,
                NULL::text
            ),
            (
                'institution_site_profiles',
                'profiles_canary_runner_select', 'PERMISSIVE',
                ARRAY['canary_runner']::name[], 'SELECT',
                $policy$(COALESCE(notes, ''::text) = 'DB_AS_CODE_RELEASE_CANARY'::text)$policy$,
                NULL::text
            ),
            (
                'institutions', 'institutions_select_public', 'PERMISSIVE',
                ARRAY['anon']::name[], 'SELECT', 'true', NULL::text
            ),
            (
                'institutions', 'institutions_select_authenticated',
                'PERMISSIVE', ARRAY['authenticated']::name[], 'SELECT',
                'true', NULL::text
            ),
            (
                'institutions', 'institutions_exclude_release_canary',
                'RESTRICTIVE', ARRAY['anon', 'authenticated']::name[],
                'SELECT',
                $policy$(slug !~~ 'zz-studiamatch-canary-%'::text)$policy$,
                NULL::text
            ),
            (
                'institutions', 'institutions_canary_runner_select',
                'PERMISSIVE', ARRAY['canary_runner']::name[], 'SELECT',
                $policy$(slug ~~ 'zz-studiamatch-canary-%'::text)$policy$,
                NULL::text
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
            ARRAY[
                'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                'REFERENCES', 'TRIGGER', 'MAINTAIN'
            ]::text[]
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
              'institution_site_profiles', 'institutions'
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
              ('courses', 'courses_exclude_release_canary'),
              ('courses', 'courses_canary_runner_select'),
              ('leads', 'leads_insert_public'),
              ('leads', 'leads_insert_authenticated'),
              ('ratings', 'ratings_select_public'),
              ('reviews', 'reviews_select_public'),
              ('institution_site_profiles', 'profiles_select_public'),
              (
                  'institution_site_profiles',
                  'profiles_exclude_release_canary'
              ),
              (
                  'institution_site_profiles',
                  'profiles_canary_runner_select'
              ),
              ('institutions', 'institutions_select_public'),
              ('institutions', 'institutions_select_authenticated'),
              ('institutions', 'institutions_exclude_release_canary'),
              ('institutions', 'institutions_canary_runner_select')
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
              ('reviews', 'reviews_service_role'),
              ('institution_site_profiles', 'profiles_service_role'),
              ('institutions', 'institutions_service_role')
          )
          AND policy.permissive = 'PERMISSIVE'
          AND policy.cmd = 'ALL'
          AND policy.roles = ARRAY['service_role']::name[]
          AND policy.qual = 'true'
          AND policy.with_check = 'true'
    ) <> 6 OR EXISTS (
        SELECT 1
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename IN (
              'courses', 'leads', 'ratings', 'reviews',
              'institution_site_profiles', 'institutions'
          )
          AND (policy.tablename, policy.policyname) NOT IN (
              ('courses', 'courses_select_public'),
              ('courses', 'courses_select_authenticated'),
              ('courses', 'courses_exclude_release_canary'),
              ('courses', 'courses_canary_runner_select'),
              ('courses', 'courses_service_role'),
              ('leads', 'leads_insert_public'),
              ('leads', 'leads_insert_authenticated'),
              ('leads', 'leads_service_role'),
              ('ratings', 'ratings_select_public'),
              ('ratings', 'ratings_service_role'),
              ('reviews', 'reviews_select_public'),
              ('reviews', 'reviews_service_role'),
              ('institution_site_profiles', 'profiles_select_public'),
              (
                  'institution_site_profiles',
                  'profiles_exclude_release_canary'
              ),
              (
                  'institution_site_profiles',
                  'profiles_canary_runner_select'
              ),
              ('institution_site_profiles', 'profiles_service_role'),
              ('institutions', 'institutions_select_public'),
              ('institutions', 'institutions_select_authenticated'),
              ('institutions', 'institutions_exclude_release_canary'),
              ('institutions', 'institutions_canary_runner_select'),
              ('institutions', 'institutions_service_role')
          )
    ) THEN
        RETURN false;
    END IF;

    IF NOT COALESCE((
        SELECT NOT role.rolsuper
           AND NOT role.rolbypassrls
           AND NOT role.rolcanlogin
           AND NOT role.rolinherit
           AND NOT role.rolcreaterole
           AND NOT role.rolcreatedb
           AND NOT role.rolreplication
           AND NOT EXISTS (
               SELECT 1
               FROM pg_catalog.pg_auth_members AS membership
               LEFT JOIN pg_catalog.pg_roles AS member_role
                 ON member_role.oid = membership.member
               WHERE membership.member = role.oid
                  OR (
                      membership.roleid = role.oid
                      AND (
                          member_role.rolname IS DISTINCT FROM 'authenticator'
                          OR membership.admin_option
                          OR membership.inherit_option
                          OR NOT membership.set_option
                      )
                  )
           )
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_auth_members AS membership
               JOIN pg_catalog.pg_roles AS member_role
                 ON member_role.oid = membership.member
               WHERE membership.roleid = role.oid
                 AND member_role.rolname = 'authenticator'
           ) = 1
           AND NOT EXISTS (
               SELECT 1
               FROM pg_catalog.pg_roles AS privileged_role
               WHERE privileged_role.oid <> role.oid
                 AND (privileged_role.rolsuper OR privileged_role.rolbypassrls)
                 AND pg_catalog.pg_has_role(
                     role.oid, privileged_role.oid, 'MEMBER'
                 )
           )
        FROM pg_catalog.pg_roles AS role
        WHERE role.rolname = 'canary_runner'
    ), false) THEN
        RETURN false;
    END IF;

    IF NOT COALESCE((
        SELECT role.rolbypassrls
           AND NOT role.rolsuper
           AND NOT role.rolcanlogin
           AND role.rolinherit
           AND NOT role.rolcreaterole
           AND NOT role.rolcreatedb
           AND NOT role.rolreplication
           AND NOT EXISTS (
               SELECT 1
               FROM pg_catalog.pg_auth_members AS membership
               LEFT JOIN pg_catalog.pg_roles AS member_role
                 ON member_role.oid = membership.member
               WHERE membership.member = role.oid
                  OR (
                      membership.roleid = role.oid
                      AND (
                          member_role.rolname IS DISTINCT FROM 'authenticator'
                          OR membership.admin_option
                          OR membership.inherit_option
                          OR NOT membership.set_option
                      )
                  )
           )
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_auth_members AS membership
               JOIN pg_catalog.pg_roles AS member_role
                 ON member_role.oid = membership.member
               WHERE membership.roleid = role.oid
                 AND member_role.rolname = 'authenticator'
           ) = 1
           AND NOT EXISTS (
               SELECT 1
               FROM pg_catalog.pg_roles AS privileged_role
               WHERE privileged_role.oid <> role.oid
                 AND (privileged_role.rolsuper OR privileged_role.rolbypassrls)
                 AND pg_catalog.pg_has_role(
                     role.oid, privileged_role.oid, 'MEMBER'
                 )
           )
        FROM pg_catalog.pg_roles AS role
        WHERE role.rolname = 'service_role'
    ), false) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_namespace AS namespace_record
        JOIN pg_catalog.pg_roles AS owner
          ON owner.oid = namespace_record.nspowner
        WHERE namespace_record.nspname = 'public'
          AND owner.rolname <> 'pg_database_owner'
    ) OR EXISTS (
        SELECT 1
        FROM pg_catalog.pg_namespace AS namespace_record
        CROSS JOIN LATERAL pg_catalog.aclexplode(
            COALESCE(
                namespace_record.nspacl,
                pg_catalog.acldefault('n', namespace_record.nspowner)
            )
        ) AS acl
        WHERE namespace_record.nspname = 'public'
          AND acl.grantee <> namespace_record.nspowner
          AND (
              acl.grantee <> 0
              OR acl.privilege_type <> 'USAGE'
              OR acl.is_grantable
          )
    ) OR (
        SELECT pg_catalog.count(*)
        FROM pg_catalog.pg_namespace AS namespace_record
        CROSS JOIN LATERAL pg_catalog.aclexplode(
            COALESCE(
                namespace_record.nspacl,
                pg_catalog.acldefault('n', namespace_record.nspowner)
            )
        ) AS acl
        WHERE namespace_record.nspname = 'public'
          AND acl.grantee = 0
          AND acl.privilege_type = 'USAGE'
          AND NOT acl.is_grantable
    ) <> 1 OR EXISTS (
        SELECT 1
        FROM pg_catalog.unnest(ARRAY[
            'anon', 'authenticated', 'service_role', 'canary_runner'
        ]::text[]) AS checked_role(role_name)
        WHERE NOT pg_catalog.has_schema_privilege(
            checked_role.role_name, 'public', 'USAGE'
        ) OR pg_catalog.has_schema_privilege(
            checked_role.role_name, 'public', 'CREATE'
        )
    ) THEN
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
        expected_columns := ARRAY['id', 'name', 'slug'];
        IF EXISTS (
            SELECT 1
            FROM pg_catalog.unnest(
                ARRAY[
                    'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                    'REFERENCES', 'TRIGGER', 'MAINTAIN'
                ]::text[]
            ) AS denied(privilege_name)
            WHERE pg_catalog.has_table_privilege(
                role_name, 'public.institutions', denied.privilege_name
            )
        ) OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_attribute AS attribute
            WHERE attribute.attrelid = 'public.institutions'::regclass
              AND attribute.attnum > 0
              AND NOT attribute.attisdropped
              AND pg_catalog.has_column_privilege(
                  role_name, attribute.attrelid, attribute.attnum, 'SELECT'
              ) IS DISTINCT FROM (attribute.attname = ANY(expected_columns))
        ) THEN
            RETURN false;
        END IF;

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
                ARRAY[
                    'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                    'REFERENCES', 'TRIGGER', 'MAINTAIN'
                ]::text[]
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

        expected_columns := ARRAY[
            'first_name', 'last_name', 'email', 'whatsapp', 'source_page',
            'type', 'course_id', 'area_interest', 'budget', 'modality',
            'description', 'is_late_enrollment_request'
        ];
        IF EXISTS (
            SELECT 1
            FROM pg_catalog.unnest(
                ARRAY[
                    'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                    'REFERENCES', 'TRIGGER', 'MAINTAIN'
                ]::text[]
            ) AS denied(privilege_name)
            WHERE pg_catalog.has_table_privilege(
                role_name, 'public.leads', denied.privilege_name
            )
        ) OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_attribute AS attribute
            WHERE attribute.attrelid = 'public.leads'::regclass
              AND attribute.attnum > 0
              AND NOT attribute.attisdropped
              AND pg_catalog.has_column_privilege(
                  role_name, attribute.attrelid, attribute.attnum, 'INSERT'
              ) IS DISTINCT FROM (attribute.attname = ANY(expected_columns))
        ) THEN
            RETURN false;
        END IF;
    END LOOP;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_class AS relation
        CROSS JOIN LATERAL pg_catalog.aclexplode(
            COALESCE(
                relation.relacl,
                pg_catalog.acldefault('r', relation.relowner)
            )
        ) AS acl
        LEFT JOIN pg_catalog.pg_roles AS grantee
          ON grantee.oid = acl.grantee
        WHERE relation.oid = ANY(ARRAY[
            'public.courses'::regclass,
            'public.leads'::regclass,
            'public.ratings'::regclass,
            'public.reviews'::regclass,
            'public.institution_site_profiles'::regclass,
            'public.institutions'::regclass
        ])
          AND acl.grantee <> relation.relowner
          AND (
              acl.is_grantable
              OR acl.grantee = 0
              OR grantee.rolname IS NULL
              OR grantee.rolname NOT IN (
                  'anon', 'authenticated', 'service_role', 'canary_runner'
              )
              OR grantee.rolname IN ('anon', 'authenticated')
              OR (
                  grantee.rolname = 'service_role'
                  AND acl.privilege_type NOT IN (
                      'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                      'REFERENCES', 'TRIGGER', 'MAINTAIN'
                  )
              )
               OR (
                   grantee.rolname = 'canary_runner'
                   AND (
                       acl.privilege_type <> 'SELECT'
                       OR relation.oid <> ALL(ARRAY[
                           'public.courses'::regclass,
                           'public.institution_site_profiles'::regclass,
                           'public.institutions'::regclass
                       ])
                   )
               )
          )
    ) OR EXISTS (
        SELECT 1
        FROM pg_catalog.unnest(ARRAY[
            'public.courses', 'public.leads', 'public.ratings',
            'public.reviews', 'public.institution_site_profiles',
            'public.institutions'
        ]::text[]) AS required_table(table_name)
        CROSS JOIN pg_catalog.unnest(ARRAY[
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
            'REFERENCES', 'TRIGGER', 'MAINTAIN'
        ]::text[]) AS required_privilege(privilege_name)
        WHERE NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_class AS relation
            CROSS JOIN LATERAL pg_catalog.aclexplode(
                COALESCE(
                    relation.relacl,
                    pg_catalog.acldefault('r', relation.relowner)
                )
            ) AS acl
            JOIN pg_catalog.pg_roles AS grantee
              ON grantee.oid = acl.grantee
            WHERE relation.oid = required_table.table_name::regclass
              AND grantee.rolname = 'service_role'
              AND acl.privilege_type = required_privilege.privilege_name
              AND NOT acl.is_grantable
        )
    ) OR EXISTS (
        SELECT 1
        FROM pg_catalog.unnest(ARRAY[
            'public.courses', 'public.institution_site_profiles',
            'public.institutions'
        ]::text[]) AS required_table(table_name)
        WHERE NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_class AS relation
            CROSS JOIN LATERAL pg_catalog.aclexplode(
                COALESCE(
                    relation.relacl,
                    pg_catalog.acldefault('r', relation.relowner)
                )
            ) AS acl
            JOIN pg_catalog.pg_roles AS grantee
              ON grantee.oid = acl.grantee
            WHERE relation.oid = required_table.table_name::regclass
              AND grantee.rolname = 'canary_runner'
              AND acl.privilege_type = 'SELECT'
              AND NOT acl.is_grantable
        )
    ) OR EXISTS (
        WITH expected_column_grants(
            table_name, column_name, privilege_name
        ) AS (
            SELECT 'public.institutions', column_name, 'SELECT'
            FROM pg_catalog.unnest(ARRAY['id', 'name', 'slug']) AS column_name
            UNION ALL
            SELECT 'public.courses', column_name, 'SELECT'
            FROM pg_catalog.unnest(ARRAY[
                'id', 'name', 'slug', 'url', 'institution_id', 'price_pen',
                'price_status', 'mode', 'course_type', 'category_id',
                'duration', 'start_date_text', 'description_long', 'syllabus',
                'target_audience', 'requirements', 'certification', 'benefits',
                'objectives', 'expected_monthly_salary', 'seniority_level',
                'roi_months', 'address', 'region', 'is_active', 'is_verified',
                'brochure_url', 'start_date', 'created_at', 'updated_at',
                'publication_status'
            ]) AS column_name
            UNION ALL
            SELECT 'public.ratings', column_name, 'SELECT'
            FROM pg_catalog.unnest(ARRAY[
                'id', 'course_id', 'rating_value', 'user_nickname', 'created_at'
            ]) AS column_name
            UNION ALL
            SELECT 'public.reviews', column_name, 'SELECT'
            FROM pg_catalog.unnest(ARRAY[
                'id', 'course_id', 'content', 'user_nickname', 'created_at'
            ]) AS column_name
            UNION ALL
            SELECT 'public.institution_site_profiles', column_name, 'SELECT'
            FROM pg_catalog.unnest(
                ARRAY['institution_id', 'production_enabled']
            ) AS column_name
            UNION ALL
            SELECT 'public.leads', column_name, 'INSERT'
            FROM pg_catalog.unnest(ARRAY[
                'first_name', 'last_name', 'email', 'whatsapp', 'source_page',
                'type', 'course_id', 'area_interest', 'budget', 'modality',
                'description', 'is_late_enrollment_request'
            ]) AS column_name
        )
        SELECT 1
        FROM expected_column_grants AS expected
        CROSS JOIN pg_catalog.unnest(
            ARRAY['anon', 'authenticated']
        ) AS required_role(role_name)
        WHERE NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_attribute AS attribute
            CROSS JOIN LATERAL pg_catalog.aclexplode(attribute.attacl) AS acl
            JOIN pg_catalog.pg_roles AS grantee
              ON grantee.oid = acl.grantee
            WHERE attribute.attrelid = expected.table_name::regclass
              AND attribute.attname = expected.column_name
              AND grantee.rolname = required_role.role_name
              AND acl.privilege_type = expected.privilege_name
              AND NOT acl.is_grantable
        )
    ) OR EXISTS (
        WITH expected_column_grants(
            table_name, column_name, privilege_name
        ) AS (
            SELECT 'public.institutions', column_name, 'SELECT'
            FROM pg_catalog.unnest(ARRAY['id', 'name', 'slug']) AS column_name
            UNION ALL
            SELECT 'public.courses', column_name, 'SELECT'
            FROM pg_catalog.unnest(ARRAY[
                'id', 'name', 'slug', 'url', 'institution_id', 'price_pen',
                'price_status', 'mode', 'course_type', 'category_id',
                'duration', 'start_date_text', 'description_long', 'syllabus',
                'target_audience', 'requirements', 'certification', 'benefits',
                'objectives', 'expected_monthly_salary', 'seniority_level',
                'roi_months', 'address', 'region', 'is_active', 'is_verified',
                'brochure_url', 'start_date', 'created_at', 'updated_at',
                'publication_status'
            ]) AS column_name
            UNION ALL
            SELECT 'public.ratings', column_name, 'SELECT'
            FROM pg_catalog.unnest(ARRAY[
                'id', 'course_id', 'rating_value', 'user_nickname', 'created_at'
            ]) AS column_name
            UNION ALL
            SELECT 'public.reviews', column_name, 'SELECT'
            FROM pg_catalog.unnest(ARRAY[
                'id', 'course_id', 'content', 'user_nickname', 'created_at'
            ]) AS column_name
            UNION ALL
            SELECT 'public.institution_site_profiles', column_name, 'SELECT'
            FROM pg_catalog.unnest(
                ARRAY['institution_id', 'production_enabled']
            ) AS column_name
            UNION ALL
            SELECT 'public.leads', column_name, 'INSERT'
            FROM pg_catalog.unnest(ARRAY[
                'first_name', 'last_name', 'email', 'whatsapp', 'source_page',
                'type', 'course_id', 'area_interest', 'budget', 'modality',
                'description', 'is_late_enrollment_request'
            ]) AS column_name
        )
        SELECT 1
        FROM pg_catalog.pg_attribute AS attribute
        JOIN pg_catalog.pg_class AS relation
          ON relation.oid = attribute.attrelid
        CROSS JOIN LATERAL pg_catalog.aclexplode(attribute.attacl) AS acl
        LEFT JOIN pg_catalog.pg_roles AS grantee
          ON grantee.oid = acl.grantee
        WHERE relation.oid = ANY(ARRAY[
            'public.courses'::regclass,
            'public.leads'::regclass,
            'public.ratings'::regclass,
            'public.reviews'::regclass,
            'public.institution_site_profiles'::regclass,
            'public.institutions'::regclass
        ])
          AND acl.grantee <> relation.relowner
          AND (
              acl.is_grantable
              OR acl.grantee = 0
              OR grantee.rolname IS NULL
              OR grantee.rolname NOT IN ('anon', 'authenticated')
              OR NOT EXISTS (
                  SELECT 1
                  FROM expected_column_grants AS expected
                  WHERE expected.table_name::regclass = relation.oid
                    AND expected.column_name = attribute.attname
                    AND expected.privilege_name = acl.privilege_type
              )
          )
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.unnest(ARRAY[
            'public.courses', 'public.leads', 'public.ratings',
            'public.reviews', 'public.institution_site_profiles',
            'public.institutions'
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
        procedure_record.provolatile,
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
       OR function_record.provolatile <> 'v'
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
        procedure_record.provolatile,
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
       OR function_record.provolatile <> 's'
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

CREATE OR REPLACE FUNCTION public.verify_fase09_5_rls_canary_reconciliation()
RETURNS boolean
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path = ''
AS $function$
DECLARE
    actual_record record;
    expected_record record;
BEGIN
    IF NOT public.verify_fase08_hito1_contract() THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename = 'institution_site_profiles'
          AND policy.policyname = 'profiles_select_authenticated'
    ) THEN
        RETURN false;
    END IF;

    FOR expected_record IN
        SELECT *
        FROM (VALUES
            (
                'institutions', 'institutions_exclude_release_canary',
                $policy$(slug !~~ 'zz-studiamatch-canary-%'::text)$policy$
            ),
            (
                'institution_site_profiles',
                'profiles_exclude_release_canary',
                $policy$((COALESCE(notes, ''::text) <> 'DB_AS_CODE_RELEASE_CANARY'::text) AND (EXISTS ( SELECT 1 FROM public.institutions institution_record WHERE (institution_record.id = institution_site_profiles.institution_id))))$policy$
            ),
            (
                'courses', 'courses_exclude_release_canary',
                $policy$(((url IS NULL) OR (url !~~ 'https://canary.invalid/%'::text)) AND (EXISTS ( SELECT 1 FROM public.institutions institution_record WHERE (institution_record.id = courses.institution_id))))$policy$
            )
        ) AS expected(table_name, policy_name, using_expression)
    LOOP
        SELECT
            policy.permissive,
            policy.roles,
            policy.cmd,
            pg_catalog.regexp_replace(
                policy.qual, E'\\s+', ' ', 'g'
            ) AS using_expression,
            policy.with_check AS check_expression
        INTO actual_record
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename = expected_record.table_name
          AND policy.policyname = expected_record.policy_name;

        IF NOT FOUND
           OR actual_record.permissive <> 'RESTRICTIVE'
           OR actual_record.roles IS DISTINCT FROM
              ARRAY['anon', 'authenticated']::name[]
           OR actual_record.cmd <> 'SELECT'
           OR actual_record.using_expression IS DISTINCT FROM
              expected_record.using_expression
           OR actual_record.check_expression IS NOT NULL THEN
            RETURN false;
        END IF;
    END LOOP;

    SELECT
        owner.rolname AS owner_name,
        language_record.lanname AS language_name,
        procedure_record.prosecdef,
        procedure_record.provolatile,
        procedure_record.proconfig,
        procedure_record.proacl
    INTO actual_record
    FROM pg_catalog.pg_proc AS procedure_record
    JOIN pg_catalog.pg_roles AS owner
      ON owner.oid = procedure_record.proowner
    JOIN pg_catalog.pg_language AS language_record
      ON language_record.oid = procedure_record.prolang
    WHERE procedure_record.oid =
        'public.verify_fase09_5_rls_canary_reconciliation()'::regprocedure;

    IF NOT FOUND
       OR actual_record.owner_name <> 'postgres'
       OR actual_record.language_name <> 'plpgsql'
       OR actual_record.prosecdef
       OR actual_record.provolatile <> 's'
       OR actual_record.proconfig IS DISTINCT FROM ARRAY['search_path=""']::text[]
       OR pg_catalog.has_function_privilege(
           'anon', 'public.verify_fase09_5_rls_canary_reconciliation()', 'EXECUTE'
       )
       OR pg_catalog.has_function_privilege(
           'authenticated',
           'public.verify_fase09_5_rls_canary_reconciliation()', 'EXECUTE'
       )
       OR NOT pg_catalog.has_function_privilege(
           'service_role',
           'public.verify_fase09_5_rls_canary_reconciliation()', 'EXECUTE'
       )
       OR EXISTS (
           SELECT 1
           FROM pg_catalog.aclexplode(
               COALESCE(
                   actual_record.proacl,
                   pg_catalog.acldefault(
                       'f',
                       (
                           SELECT procedure_record.proowner
                           FROM pg_catalog.pg_proc AS procedure_record
                           WHERE procedure_record.oid =
                               'public.verify_fase09_5_rls_canary_reconciliation()'::regprocedure
                       )
                   )
               )
           ) AS acl
           WHERE acl.privilege_type = 'EXECUTE'
              AND (
                  acl.grantee NOT IN (
                      (
                          SELECT procedure_record.proowner
                          FROM pg_catalog.pg_proc AS procedure_record
                          WHERE procedure_record.oid =
                              'public.verify_fase09_5_rls_canary_reconciliation()'::regprocedure
                      ),
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

ALTER FUNCTION public.verify_fase09_5_rls_canary_reconciliation()
OWNER TO postgres;
REVOKE ALL ON FUNCTION public.verify_fase09_5_rls_canary_reconciliation()
FROM PUBLIC, anon, authenticated, service_role CASCADE;
GRANT EXECUTE
ON FUNCTION public.verify_fase09_5_rls_canary_reconciliation()
TO service_role;

CREATE OR REPLACE FUNCTION public.verify_fase09_5_policy_inventory_reconciliation()
RETURNS boolean
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path = ''
AS $function$
DECLARE
    function_record record;
BEGIN
    IF NOT public.verify_fase08_hito1_contract()
       OR NOT public.verify_fase09_5_rls_canary_reconciliation() THEN
        RETURN false;
    END IF;

    SELECT
        owner.rolname AS owner_name,
        language_record.lanname AS language_name,
        procedure_record.prosecdef,
        procedure_record.provolatile,
        procedure_record.proconfig,
        procedure_record.proacl
    INTO function_record
    FROM pg_catalog.pg_proc AS procedure_record
    JOIN pg_catalog.pg_roles AS owner
      ON owner.oid = procedure_record.proowner
    JOIN pg_catalog.pg_language AS language_record
      ON language_record.oid = procedure_record.prolang
    WHERE procedure_record.oid =
        'public.verify_fase09_5_policy_inventory_reconciliation()'::regprocedure;

    RETURN FOUND
       AND function_record.owner_name = 'postgres'
       AND function_record.language_name = 'plpgsql'
       AND NOT function_record.prosecdef
       AND function_record.provolatile = 's'
       AND function_record.proconfig = ARRAY['search_path=""']::text[]
       AND NOT pg_catalog.has_function_privilege(
           'anon',
           'public.verify_fase09_5_policy_inventory_reconciliation()',
           'EXECUTE'
       )
       AND NOT pg_catalog.has_function_privilege(
           'authenticated',
           'public.verify_fase09_5_policy_inventory_reconciliation()',
           'EXECUTE'
       )
       AND NOT pg_catalog.has_function_privilege(
           'canary_runner',
           'public.verify_fase09_5_policy_inventory_reconciliation()',
           'EXECUTE'
       )
       AND pg_catalog.has_function_privilege(
           'service_role',
           'public.verify_fase09_5_policy_inventory_reconciliation()',
           'EXECUTE'
       )
       AND NOT EXISTS (
           SELECT 1
           FROM pg_catalog.aclexplode(
               COALESCE(
                   function_record.proacl,
                    pg_catalog.acldefault(
                        'f',
                        (
                            SELECT procedure_record.proowner
                            FROM pg_catalog.pg_proc AS procedure_record
                            WHERE procedure_record.oid =
                                'public.verify_fase09_5_policy_inventory_reconciliation()'::regprocedure
                        )
                    )
               )
           ) AS acl
           WHERE acl.privilege_type = 'EXECUTE'
             AND (
                 acl.grantee NOT IN (
                     'postgres'::regrole, 'service_role'::regrole
                 )
                 OR (
                     acl.grantee = 'service_role'::regrole
                     AND acl.is_grantable
                 )
             )
       );
END;
$function$;

ALTER FUNCTION public.verify_fase09_5_policy_inventory_reconciliation()
OWNER TO postgres;
REVOKE ALL
ON FUNCTION public.verify_fase09_5_policy_inventory_reconciliation()
FROM PUBLIC, anon, authenticated, canary_runner, service_role CASCADE;
GRANT EXECUTE
ON FUNCTION public.verify_fase09_5_policy_inventory_reconciliation()
TO service_role;
