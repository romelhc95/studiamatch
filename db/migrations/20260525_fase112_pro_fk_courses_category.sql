-- Fase 112: FK courses_category_id_fkey for PostgREST embedded resources.
-- PostgREST requires a declared FK to resolve categories(name) in course queries.

CREATE TABLE IF NOT EXISTS public.schema_repair_audit (
  id bigserial PRIMARY KEY,
  migration_name text NOT NULL,
  table_name text NOT NULL,
  record_id uuid NOT NULL,
  old_values jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (migration_name, table_name, record_id)
);

REVOKE ALL ON public.schema_repair_audit FROM anon;
REVOKE ALL ON public.schema_repair_audit FROM authenticated;

-- Audit orphan category references before repairing them.
INSERT INTO public.schema_repair_audit (migration_name, table_name, record_id, old_values)
SELECT
  'fase112_pro_fk_courses_category',
  'courses',
  courses.id,
  jsonb_build_object('category_id', courses.category_id, 'name', courses.name, 'url', courses.url)
FROM public.courses
WHERE category_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM public.categories c
    WHERE c.id = courses.category_id
  )
ON CONFLICT (migration_name, table_name, record_id) DO NOTHING;

-- Repair orphan category references before creating the FK.
UPDATE public.courses
SET category_id = NULL
WHERE category_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM public.categories c
    WHERE c.id = courses.category_id
  );

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'courses_category_id_fkey'
      AND conrelid = 'public.courses'::regclass
  ) THEN
    ALTER TABLE public.courses
      ADD CONSTRAINT courses_category_id_fkey
      FOREIGN KEY (category_id) REFERENCES public.categories(id);
  END IF;
END $$;

COMMENT ON CONSTRAINT courses_category_id_fkey ON public.courses IS
'Fase 112: FK required by PostgREST to resolve categories(name) as an embedded resource.';
