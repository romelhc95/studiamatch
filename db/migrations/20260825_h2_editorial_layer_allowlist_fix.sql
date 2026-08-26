-- H2: align manual_overrides allowlist with pipeline-owned start_date.
-- Scope: Free/Development DDL only under DDL-H2-EDITORIAL-LAYER-FREE.
-- This migration performs no DML/backfill.

ALTER TABLE public.course_editorial_state
    DROP CONSTRAINT IF EXISTS course_editorial_state_manual_overrides_public_allowlist;

ALTER TABLE public.course_editorial_state
    ADD CONSTRAINT course_editorial_state_manual_overrides_public_allowlist
    CHECK (
        manual_overrides
        - 'name'
        - 'price_pen'
        - 'price_status'
        - 'mode'
        - 'duration'
        - 'description_long'
        - 'syllabus'
        - 'target_audience'
        - 'requirements'
        - 'certification'
        - 'benefits'
        - 'objectives'
        - 'start_date_text'
        = '{}'::jsonb
    );
