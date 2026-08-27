-- H2 Pro contract: retire direct public course reads after stable H2 frontend deploy.
-- Scope: Production DDL only after explicit JIT and post-deploy smoke approval.

DO $$
DECLARE
    effective_count INTEGER;
    cohort_count INTEGER;
    missing_count INTEGER;
    expected_digest TEXT;
    actual_digest TEXT;
BEGIN
    IF to_regclass('private.h2_legacy_public_course_cohort') IS NULL THEN
        RAISE EXCEPTION 'Cannot contract direct courses reads before H2 legacy cohort exists';
    END IF;
    IF to_regclass('public.courses_public_effective') IS NULL THEN
        RAISE EXCEPTION 'Cannot contract direct courses reads before courses_public_effective exists';
    END IF;

    SELECT count(*) INTO cohort_count FROM private.h2_legacy_public_course_cohort;
    SELECT count(*) INTO effective_count FROM public.courses_public_effective;
    SELECT count(*) INTO missing_count
      FROM private.h2_legacy_public_course_cohort cohort
     WHERE NOT EXISTS (
         SELECT 1 FROM public.courses_public_effective effective WHERE effective.id = cohort.course_id
     );
    SELECT max(snapshot_ids_sha256) INTO expected_digest
      FROM private.h2_legacy_public_course_cohort;
    SELECT 'sha256:' || encode(sha256(convert_to(string_agg(course_id::TEXT, ',' ORDER BY course_id::TEXT), 'UTF8')), 'hex')
      INTO actual_digest
      FROM private.h2_legacy_public_course_cohort;
    IF cohort_count <= 0 OR effective_count <> cohort_count THEN
        RAISE EXCEPTION 'Cannot contract direct courses reads: cohort %, effective %', cohort_count, effective_count;
    END IF;
    IF missing_count <> 0 OR expected_digest IS NULL OR actual_digest <> expected_digest THEN
        RAISE EXCEPTION 'Cannot contract direct courses reads: missing %, digest expected %, got %', missing_count, expected_digest, actual_digest;
    END IF;
END;
$$;

DROP POLICY IF EXISTS courses_h2_public_effective_select ON public.courses;
DROP POLICY IF EXISTS courses_exclude_release_canary ON public.courses;
DROP POLICY IF EXISTS "Public read for courses" ON public.courses;
DROP POLICY IF EXISTS courses_select_public ON public.courses;
DROP POLICY IF EXISTS courses_select_authenticated ON public.courses;

REVOKE SELECT ON TABLE public.courses FROM PUBLIC, anon, authenticated;

COMMENT ON COLUMN public.courses.is_active IS
    'Deprecated as publication authority in H2. Technical pipeline availability only; public publication is gated by course_editorial_state.';
COMMENT ON COLUMN public.courses.is_verified IS
    'Deprecated as publication authority in H2. Technical verification only; public publication is gated by course_editorial_state.';
COMMENT ON VIEW public.courses_public_effective IS
    'H2 public effective course view. Direct public courses reads have been retired after stable frontend deployment.';
