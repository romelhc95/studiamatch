-- H2 Pro backfill: create non-published editorial states for existing courses.
-- Scope: Production DML only after explicit JIT and h2-expand-compat manifest approval.

INSERT INTO public.course_editorial_state (
    course_id,
    editorial_status,
    quality_status,
    missing_fields,
    field_sources,
    field_timestamps,
    availability_status,
    created_at,
    updated_at
)
SELECT
    c.id,
    'pending_review',
    CASE WHEN cardinality(private.h2_required_missing_fields(c, '{}'::jsonb)) = 0 THEN 'complete' ELSE 'pending' END,
    private.h2_required_missing_fields(c, '{}'::jsonb),
    '{}'::jsonb,
    '{}'::jsonb,
    CASE WHEN c.is_active IS TRUE AND c.is_verified IS TRUE THEN 'available' ELSE 'unknown' END,
    now(),
    now()
FROM public.courses c
ON CONFLICT (course_id) DO NOTHING;

DO $$
DECLARE
    course_count INTEGER;
    state_count INTEGER;
BEGIN
    SELECT count(*) INTO course_count FROM public.courses;
    SELECT count(*) INTO state_count FROM public.course_editorial_state;
    IF state_count < course_count THEN
        RAISE EXCEPTION 'H2 Pro backfill incomplete: states %, courses %', state_count, course_count;
    END IF;
END;
$$;
