-- Canary-only atomic promotions with institution scope enforced in PostgreSQL.

DROP FUNCTION IF EXISTS public.lock_staging_records_scoped(uuid, integer);
DROP FUNCTION IF EXISTS public.atomic_cleansing_promote_scoped(uuid, uuid[], jsonb);
DROP FUNCTION IF EXISTS public.atomic_enrichment_promote_scoped(uuid, jsonb, uuid);
DROP FUNCTION IF EXISTS public.atomic_canary_sync(uuid, uuid, jsonb);

CREATE FUNCTION public.lock_staging_records_scoped(
    inst_id uuid,
    batch_size integer DEFAULT 1
)
RETURNS SETOF public.staging_raw
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO ''
AS $$
BEGIN
    IF batch_size <> 1 OR NOT EXISTS (
        SELECT 1
        FROM public.institutions i
        JOIN public.institution_site_profiles p ON p.institution_id = i.id
        WHERE i.id = inst_id
          AND i.slug LIKE 'zz-studiamatch-canary-%'
          AND i.status = 'Inactiva'
          AND p.notes = 'DB_AS_CODE_RELEASE_CANARY'
          AND p.production_enabled = false
    ) THEN
        RAISE EXCEPTION 'invalid canary lock scope';
    END IF;
    RETURN QUERY
    UPDATE public.staging_raw sr
    SET status = 'processing'
    WHERE sr.id IN (
        SELECT candidate.id
        FROM public.staging_raw candidate
        WHERE candidate.institution_id = inst_id
          AND candidate.status = 'pending'
          AND candidate.url LIKE 'https://canary.invalid/%'
        ORDER BY candidate.created_at
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    )
    RETURNING sr.*;
END;
$$;

ALTER FUNCTION public.lock_staging_records_scoped(uuid, integer) OWNER TO postgres;
REVOKE ALL ON FUNCTION public.lock_staging_records_scoped(uuid, integer)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.lock_staging_records_scoped(uuid, integer)
TO service_role, canary_runner;

CREATE FUNCTION public.atomic_cleansing_promote_scoped(
    p_institution_id uuid,
    p_staging_ids uuid[],
    p_cleansed_data jsonb
)
RETURNS SETOF public.cleansed_programs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO ''
AS $$
DECLARE
    written_count integer;
    updated_count integer;
BEGIN
    IF p_institution_id IS NULL OR pg_catalog.jsonb_typeof(p_cleansed_data) IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION 'institution and cleansed JSON array are required';
    END IF;
    IF COALESCE(pg_catalog.array_length(p_staging_ids, 1), 0) <> 1
       OR pg_catalog.jsonb_array_length(p_cleansed_data) <> 1 THEN
        RAISE EXCEPTION 'canary cleansing requires exactly one source and destination';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM public.institutions i
        JOIN public.institution_site_profiles p ON p.institution_id = i.id
        WHERE i.id = p_institution_id
          AND i.slug LIKE 'zz-studiamatch-canary-%'
          AND i.status = 'Inactiva'
          AND p.notes = 'DB_AS_CODE_RELEASE_CANARY'
          AND p.production_enabled = false
    ) THEN
        RAISE EXCEPTION 'institution is not a reserved canary fixture';
    END IF;
    PERFORM 1
    FROM public.staging_raw sr
    WHERE sr.id = p_staging_ids[1]
      AND sr.institution_id = p_institution_id
      AND sr.status IN ('pending', 'processing')
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'staging scope mismatch';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_catalog.unnest(p_staging_ids) AS requested(id)
        LEFT JOIN public.staging_raw sr ON sr.id = requested.id
        WHERE sr.id IS NULL
           OR sr.institution_id IS DISTINCT FROM p_institution_id
           OR sr.status NOT IN ('pending', 'processing')
    ) THEN
        RAISE EXCEPTION 'staging scope mismatch';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_catalog.jsonb_array_elements(p_cleansed_data) AS item
        WHERE (item->>'institution_id')::uuid IS DISTINCT FROM p_institution_id
           OR NOT ((item->>'staging_id')::uuid = ANY(p_staging_ids))
           OR NOT EXISTS (
               SELECT 1 FROM public.staging_raw sr
               WHERE sr.id = (item->>'staging_id')::uuid
                 AND sr.url = item->>'url'
           )
    ) THEN
        RAISE EXCEPTION 'cleansed payload scope mismatch';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM pg_catalog.jsonb_array_elements(p_cleansed_data) AS item
        JOIN public.cleansed_programs cp ON cp.url = item->>'url'
        WHERE cp.institution_id IS DISTINCT FROM p_institution_id
    ) THEN
        RAISE EXCEPTION 'cleansed URL belongs to another institution';
    END IF;

    INSERT INTO public.cleansed_programs (
        staging_id, institution_id, url, effective_url, canonical_url,
        clean_name, clean_description, modality, location, base_price,
        currency, status, metadata
    )
    SELECT
        (item->>'staging_id')::uuid, p_institution_id, item->>'url',
        item->>'effective_url', item->>'canonical_url', item->>'clean_name',
        item->>'clean_description', item->>'modality', item->>'location',
        (item->>'base_price')::numeric, item->>'currency', 'pending',
        (item->>'metadata')::jsonb
    FROM pg_catalog.jsonb_array_elements(p_cleansed_data) AS item
    ON CONFLICT (url) DO UPDATE
    SET staging_id = EXCLUDED.staging_id,
        effective_url = EXCLUDED.effective_url,
        canonical_url = EXCLUDED.canonical_url,
        clean_name = EXCLUDED.clean_name,
        clean_description = EXCLUDED.clean_description,
        modality = EXCLUDED.modality,
        location = EXCLUDED.location,
        base_price = EXCLUDED.base_price,
        currency = EXCLUDED.currency,
        metadata = EXCLUDED.metadata,
        status = 'pending'
    WHERE public.cleansed_programs.institution_id = p_institution_id;
    GET DIAGNOSTICS written_count = ROW_COUNT;
    IF written_count <> 1 THEN
        RAISE EXCEPTION 'canary cleansing destination cardinality mismatch';
    END IF;

    UPDATE public.staging_raw
    SET status = 'processed'
    WHERE id = ANY(p_staging_ids)
      AND institution_id = p_institution_id
      AND status IN ('pending', 'processing');
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    IF updated_count <> 1 THEN
        RAISE EXCEPTION 'canary cleansing source cardinality mismatch';
    END IF;

    RETURN QUERY
    SELECT cp.*
    FROM public.cleansed_programs cp
    WHERE cp.institution_id = p_institution_id
      AND cp.url IN (
          SELECT item->>'url'
          FROM pg_catalog.jsonb_array_elements(p_cleansed_data) AS item
      );
END;
$$;

CREATE FUNCTION public.atomic_enrichment_promote_scoped(
    p_institution_id uuid,
    p_enriched_data jsonb,
    p_cleansed_id uuid
)
RETURNS SETOF public.enriched_programs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO ''
AS $$
DECLARE
    written_count integer;
    updated_count integer;
BEGIN
    IF p_institution_id IS NULL OR pg_catalog.jsonb_typeof(p_enriched_data) IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION 'institution and enriched JSON array are required';
    END IF;
    IF pg_catalog.jsonb_array_length(p_enriched_data) <> 1 THEN
        RAISE EXCEPTION 'canary enrichment requires exactly one destination';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM public.institutions i
        JOIN public.institution_site_profiles p ON p.institution_id = i.id
        WHERE i.id = p_institution_id
          AND i.slug LIKE 'zz-studiamatch-canary-%'
          AND i.status = 'Inactiva'
          AND p.notes = 'DB_AS_CODE_RELEASE_CANARY'
          AND p.production_enabled = false
    ) THEN
        RAISE EXCEPTION 'institution is not a reserved canary fixture';
    END IF;
    PERFORM 1
    FROM public.cleansed_programs cp
    WHERE cp.id = p_cleansed_id
      AND cp.institution_id = p_institution_id
      AND cp.status = 'pending'
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'cleansed scope mismatch';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_catalog.jsonb_array_elements(p_enriched_data) AS item
        WHERE (item->>'institution_id')::uuid IS DISTINCT FROM p_institution_id
           OR (item->>'cleansed_id')::uuid IS DISTINCT FROM p_cleansed_id
           OR NOT EXISTS (
               SELECT 1 FROM public.cleansed_programs cp
               WHERE cp.id = p_cleansed_id
                 AND cp.url = item->>'url'
           )
    ) THEN
        RAISE EXCEPTION 'enriched payload scope mismatch';
    END IF;

    INSERT INTO public.enriched_programs (
        cleansed_id, institution_id, url, official_name, duration_text,
        duration_months, total_cost_est, requirements, graduate_profile,
        curriculum_summary, modality, primary_campus, degree_type,
        start_date, partnerships, certifications, language, categories,
        difficulty_level, ai_summary, status,
        provider_used, is_mock_data
    )
    SELECT
        p_cleansed_id, p_institution_id, item->>'url', item->>'official_name',
        item->>'duration_text', COALESCE(NULLIF(item->>'duration_months', '')::numeric, 0)::int,
        NULLIF(item->>'total_cost_est', '')::numeric, item->>'requirements',
        item->>'graduate_profile', COALESCE(NULLIF(item->>'curriculum_summary', ''), '{}')::jsonb,
        item->>'modality', item->>'primary_campus', item->>'degree_type',
        item->>'start_date', item->>'partnerships', item->>'certifications',
        item->>'language', item->>'categories', item->>'difficulty_level',
        item->>'ai_summary', 'pending', item->>'provider_used',
        (item->>'is_mock_data')::boolean
    FROM pg_catalog.jsonb_array_elements(p_enriched_data) AS item
    ON CONFLICT (cleansed_id) DO UPDATE
    SET url = EXCLUDED.url,
        official_name = EXCLUDED.official_name,
        duration_text = EXCLUDED.duration_text,
        duration_months = EXCLUDED.duration_months,
        total_cost_est = EXCLUDED.total_cost_est,
        requirements = EXCLUDED.requirements,
        graduate_profile = EXCLUDED.graduate_profile,
        curriculum_summary = EXCLUDED.curriculum_summary,
        modality = EXCLUDED.modality,
        primary_campus = EXCLUDED.primary_campus,
        degree_type = EXCLUDED.degree_type,
        start_date = EXCLUDED.start_date,
        partnerships = EXCLUDED.partnerships,
        certifications = EXCLUDED.certifications,
        language = EXCLUDED.language,
        categories = EXCLUDED.categories,
        difficulty_level = EXCLUDED.difficulty_level,
        ai_summary = EXCLUDED.ai_summary,
        status = 'pending',
        provider_used = EXCLUDED.provider_used,
        is_mock_data = EXCLUDED.is_mock_data
    WHERE public.enriched_programs.institution_id = p_institution_id;
    GET DIAGNOSTICS written_count = ROW_COUNT;
    IF written_count <> 1 THEN
        RAISE EXCEPTION 'canary enrichment destination cardinality mismatch';
    END IF;

    UPDATE public.cleansed_programs
    SET status = 'enriched'
    WHERE id = p_cleansed_id
      AND institution_id = p_institution_id
      AND status = 'pending';
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    IF updated_count <> 1 THEN
        RAISE EXCEPTION 'canary enrichment source cardinality mismatch';
    END IF;

    RETURN QUERY
    SELECT ep.* FROM public.enriched_programs ep
    WHERE ep.cleansed_id = p_cleansed_id
      AND ep.institution_id = p_institution_id;
END;
$$;

REVOKE ALL ON FUNCTION public.atomic_cleansing_promote_scoped(uuid, uuid[], jsonb)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.atomic_cleansing_promote_scoped(uuid, uuid[], jsonb)
TO service_role, canary_runner;
ALTER FUNCTION public.atomic_cleansing_promote_scoped(uuid, uuid[], jsonb) OWNER TO postgres;

REVOKE ALL ON FUNCTION public.atomic_enrichment_promote_scoped(uuid, jsonb, uuid)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.atomic_enrichment_promote_scoped(uuid, jsonb, uuid)
TO service_role, canary_runner;
ALTER FUNCTION public.atomic_enrichment_promote_scoped(uuid, jsonb, uuid) OWNER TO postgres;

CREATE FUNCTION public.atomic_canary_sync(
    p_institution_id uuid,
    p_enriched_id uuid,
    p_course_data jsonb
)
RETURNS SETOF public.courses
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO ''
AS $$
DECLARE
    existing_institution_id uuid;
    written_count integer;
    updated_count integer;
BEGIN
    IF p_institution_id IS NULL OR pg_catalog.jsonb_typeof(p_course_data) IS DISTINCT FROM 'object' THEN
        RAISE EXCEPTION 'institution and course object are required';
    END IF;
    IF (p_course_data->>'institution_id')::uuid IS DISTINCT FROM p_institution_id
       OR COALESCE((p_course_data->>'is_active')::boolean, true)
       OR COALESCE(p_course_data->>'url', '') NOT LIKE 'https://canary.invalid/%' THEN
        RAISE EXCEPTION 'course payload is outside the reserved canary scope';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM public.institutions i
        JOIN public.institution_site_profiles p ON p.institution_id = i.id
        WHERE i.id = p_institution_id
          AND i.slug LIKE 'zz-studiamatch-canary-%'
          AND i.status = 'Inactiva'
          AND p.notes = 'DB_AS_CODE_RELEASE_CANARY'
          AND p.production_enabled = false
    ) THEN
        RAISE EXCEPTION 'institution is not a reserved canary fixture';
    END IF;
    PERFORM 1
    FROM public.enriched_programs ep
    WHERE ep.id = p_enriched_id
      AND ep.institution_id = p_institution_id
      AND ep.url = p_course_data->>'url'
      AND ep.status = 'pending'
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'enriched scope mismatch';
    END IF;
    SELECT c.institution_id
    INTO existing_institution_id
    FROM public.courses c
    WHERE c.url = p_course_data->>'url'
    FOR UPDATE;
    IF existing_institution_id IS NOT NULL
       AND existing_institution_id IS DISTINCT FROM p_institution_id THEN
        RAISE EXCEPTION 'course URL belongs to another institution';
    END IF;

    INSERT INTO public.courses (
        institution_id, name, slug, url, price_pen, price_status, mode,
        duration, start_date_text, start_date, description_long, requirements,
        objectives, target_audience, syllabus, certification, seniority_level,
        course_type, category, is_active, is_verified, last_scraped_at,
        provider_used, is_mock_data
    ) VALUES (
        p_institution_id, p_course_data->>'name', p_course_data->>'slug',
        p_course_data->>'url', NULLIF(p_course_data->>'price_pen', '')::numeric,
        p_course_data->>'price_status', p_course_data->>'mode',
        p_course_data->>'duration', p_course_data->>'start_date_text',
        NULLIF(p_course_data->>'start_date', '')::date,
        p_course_data->>'description_long', p_course_data->>'requirements',
        p_course_data->>'objectives', p_course_data->>'target_audience',
        p_course_data->>'syllabus', p_course_data->>'certification',
        p_course_data->>'seniority_level', p_course_data->>'course_type',
        p_course_data->>'category', false,
        COALESCE((p_course_data->>'is_verified')::boolean, false),
        NULLIF(p_course_data->>'last_scraped_at', '')::timestamptz,
        p_course_data->>'provider_used',
        COALESCE((p_course_data->>'is_mock_data')::boolean, true)
    )
    ON CONFLICT (url) DO UPDATE
    SET name = EXCLUDED.name,
        slug = EXCLUDED.slug,
        price_pen = EXCLUDED.price_pen,
        price_status = EXCLUDED.price_status,
        mode = EXCLUDED.mode,
        duration = EXCLUDED.duration,
        start_date_text = EXCLUDED.start_date_text,
        start_date = EXCLUDED.start_date,
        description_long = EXCLUDED.description_long,
        requirements = EXCLUDED.requirements,
        objectives = EXCLUDED.objectives,
        target_audience = EXCLUDED.target_audience,
        syllabus = EXCLUDED.syllabus,
        certification = EXCLUDED.certification,
        seniority_level = EXCLUDED.seniority_level,
        course_type = EXCLUDED.course_type,
        category = EXCLUDED.category,
        is_active = false,
        is_verified = EXCLUDED.is_verified,
        last_scraped_at = EXCLUDED.last_scraped_at,
        provider_used = EXCLUDED.provider_used,
        is_mock_data = EXCLUDED.is_mock_data
    WHERE public.courses.institution_id = p_institution_id;
    GET DIAGNOSTICS written_count = ROW_COUNT;
    IF written_count <> 1 THEN
        RAISE EXCEPTION 'canary course destination cardinality mismatch';
    END IF;

    UPDATE public.enriched_programs
    SET status = 'synced'
    WHERE id = p_enriched_id
      AND institution_id = p_institution_id
      AND status = 'pending';
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    IF updated_count <> 1 THEN
        RAISE EXCEPTION 'canary enriched source cardinality mismatch';
    END IF;

    RETURN QUERY
    SELECT c.*
    FROM public.courses c
    WHERE c.url = p_course_data->>'url'
      AND c.institution_id = p_institution_id;
END;
$$;

REVOKE ALL ON FUNCTION public.atomic_canary_sync(uuid, uuid, jsonb)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.atomic_canary_sync(uuid, uuid, jsonb)
TO service_role, canary_runner;
ALTER FUNCTION public.atomic_canary_sync(uuid, uuid, jsonb) OWNER TO postgres;
