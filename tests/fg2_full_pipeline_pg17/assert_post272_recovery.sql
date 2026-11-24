\set ON_ERROR_STOP on
DO $$
DECLARE
  _n integer;
  _staging_id uuid;
  _course_id uuid;
  _cleansed_id uuid;
  _enriched_id uuid;
  _editorial_status text;
BEGIN
  FOR _n IN 1..5 LOOP
    _staging_id := ('52000000-0000-0000-0000-' || lpad(_n::text, 12, '0'))::uuid;
    _course_id := ('53000000-0000-0000-0000-' || lpad(_n::text, 12, '0'))::uuid;
    _cleansed_id := ('54000000-0000-0000-0000-' || lpad(_n::text, 12, '0'))::uuid;
    _enriched_id := ('55000000-0000-0000-0000-' || lpad(_n::text, 12, '0'))::uuid;
    IF NOT EXISTS (SELECT 1 FROM public.staging_raw WHERE id=_staging_id AND status='processed') THEN
      RAISE EXCEPTION 'post272_staging_state_mismatch_%', _n;
    ELSIF NOT EXISTS (SELECT 1 FROM public.cleansed_programs WHERE id=_cleansed_id AND staging_id=_staging_id AND status='enriched') THEN
      RAISE EXCEPTION 'post272_cleansed_state_mismatch_%', _n;
    ELSIF NOT EXISTS (SELECT 1 FROM public.enriched_programs WHERE id=_enriched_id AND cleansed_id=_cleansed_id AND status='synced' AND provider_used='OpenAI' AND is_mock_data IS FALSE) THEN
      RAISE EXCEPTION 'post272_enriched_state_mismatch_%', _n;
    ELSIF NOT EXISTS (SELECT 1 FROM public.courses WHERE id=_course_id AND institution_id='20000000-0000-0000-0000-000000000001' AND is_active IS FALSE AND is_verified IS TRUE) THEN
      RAISE EXCEPTION 'post272_course_state_mismatch_%', _n;
    ELSIF NOT EXISTS (SELECT 1 FROM public.course_editorial_state WHERE course_id=_course_id AND editorial_status='pending_review') THEN
      RAISE EXCEPTION 'post272_editorial_state_mismatch_%', _n;
    END IF;
  END LOOP;

  SELECT state.editorial_status
    INTO _editorial_status
  FROM public.course_editorial_state state
  WHERE state.course_id='53000000-0000-0000-0000-000000000001';
  IF _editorial_status <> 'pending_review'
     OR (SELECT manual_overrides->>'name' FROM public.course_editorial_state WHERE course_id='53000000-0000-0000-0000-000000000001') <> 'Manual recovery title preserved' THEN
    RAISE EXCEPTION 'post272_editorial_override_not_preserved';
  END IF;
  IF NOT EXISTS (
    SELECT 1
    FROM public.admin_course_queue q
    WHERE q.course_id='53000000-0000-0000-0000-000000000001'
      AND q.editorial_status='pending_review'
      AND q.manual_overrides->>'name'='Manual recovery title preserved'
  ) THEN
    RAISE EXCEPTION 'post272_course_missing_from_admin_queue';
  END IF;

  -- The sixth proposed identity and its trailing-slash alias remain untouched.
  IF NOT EXISTS (
       SELECT 1 FROM public.staging_raw
       WHERE id='52000000-0000-0000-0000-000000000006'::uuid AND status='processed'
     )
     OR NOT EXISTS (
       SELECT 1 FROM public.staging_raw
       WHERE id='52000000-0000-0000-0000-000000000066'::uuid AND status='processed'
     )
     OR NOT EXISTS (
       SELECT 1 FROM public.cleansed_programs
       WHERE id='54000000-0000-0000-0000-000000000006'::uuid AND status='pending'
     )
     OR NOT EXISTS (
       SELECT 1 FROM public.cleansed_programs
       WHERE id='54000000-0000-0000-0000-000000000066'::uuid AND status='pending'
     )
     OR NOT EXISTS (
       SELECT 1 FROM public.enriched_programs
       WHERE id='55000000-0000-0000-0000-000000000006'::uuid
         AND status='synced' AND provider_used='prior-fixture'
     )
     OR NOT EXISTS (
       SELECT 1 FROM public.enriched_programs
       WHERE id='55000000-0000-0000-0000-000000000066'::uuid
         AND status='synced' AND provider_used='prior-fixture'
     ) THEN
    RAISE EXCEPTION 'post272_ambiguous_identity_was_mutated';
  END IF;

  FOR _n IN 7..8 LOOP
    _staging_id := ('52000000-0000-0000-0000-' || lpad(_n::text, 12, '0'))::uuid;
    _course_id := ('53000000-0000-0000-0000-' || lpad(_n::text, 12, '0'))::uuid;
    _cleansed_id := ('54000000-0000-0000-0000-' || lpad(_n::text, 12, '0'))::uuid;
    _enriched_id := ('55000000-0000-0000-0000-' || lpad(_n::text, 12, '0'))::uuid;
    IF NOT EXISTS (SELECT 1 FROM public.staging_raw WHERE id=_staging_id AND status='processed' AND metadata->>'fixture_case'='post272_recovery')
       OR NOT EXISTS (SELECT 1 FROM public.cleansed_programs WHERE id=_cleansed_id AND status='synced' AND clean_name='Post-272 recovered course ' || lpad(_n::text, 2, '0'))
       OR NOT EXISTS (SELECT 1 FROM public.enriched_programs WHERE id=_enriched_id AND status='synced' AND provider_used='prior-fixture')
       OR NOT EXISTS (SELECT 1 FROM public.courses WHERE id=_course_id AND name='Original recovery title ' || lpad(_n::text, 2, '0') AND provider_used='prior-fixture' AND updated_at='2026-11-22T00:00:00Z'::timestamptz)
       OR NOT EXISTS (SELECT 1 FROM public.course_editorial_state WHERE course_id=_course_id AND editorial_status='pending_review') THEN
      RAISE EXCEPTION 'post272_unchanged_identity_modified_%', _n;
    END IF;
  END LOOP;

  IF (
    SELECT count(DISTINCT slug)
    FROM public.courses
    WHERE split_part(id::text, '-', 1) = '53000000'
      AND split_part(id::text, '-', 5)::bigint BETWEEN 1 AND 5
  ) <> 5 THEN
    RAISE EXCEPTION 'post272_course_slugs_not_unique';
  END IF;

  IF (SELECT count(*) FROM public.courses_public_effective) <> 0 THEN
    RAISE EXCEPTION 'post272_recovery_unintended_publication';
  END IF;
END $$;
SELECT 'phase=post272_recovery_postflight|result=PASS|changed_synced=5|ambiguous_excluded=1|unchanged=2|editorial_preserved=true|public_effective=0|admin_queue=verified';
