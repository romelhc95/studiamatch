\set ON_ERROR_STOP on

ALTER TABLE public.courses
  ADD COLUMN IF NOT EXISTS last_404_at TIMESTAMPTZ;

ALTER TABLE public.course_editorial_state
  ADD CONSTRAINT h1_fg3_atomic_state_course_fk
  FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE RESTRICT;

ALTER TABLE public.course_editorial_audit
  ADD CONSTRAINT h1_fg3_atomic_audit_course_fk
  FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE RESTRICT;

ALTER TABLE private.h2_legacy_public_course_cohort
  ADD CONSTRAINT h1_fg3_atomic_legacy_course_fk
  FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE RESTRICT;

INSERT INTO public.courses (id, institution_id, name, is_active, is_verified)
VALUES
  ('10000000-0000-0000-0000-000000000015', '10000000-0000-0000-0000-000000000001', 'Atomic grace pending', true, true),
  ('10000000-0000-0000-0000-000000000016', '10000000-0000-0000-0000-000000000001', 'Atomic grace elapsed', true, true);

INSERT INTO private.h2_legacy_public_course_cohort (course_id)
VALUES
  ('10000000-0000-0000-0000-000000000015'),
  ('10000000-0000-0000-0000-000000000016');
