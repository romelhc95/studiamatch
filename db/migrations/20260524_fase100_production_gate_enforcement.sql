-- Fase 100: enforce production_enabled for public course visibility.

UPDATE public.courses c
SET is_active = false
WHERE NOT EXISTS (
    SELECT 1
    FROM public.institution_site_profiles p
    WHERE p.institution_id = c.institution_id
      AND p.production_enabled = true
);

DROP POLICY IF EXISTS courses_select_public ON public.courses;
CREATE POLICY courses_select_public ON public.courses
    FOR SELECT TO anon
    USING (
        is_active = true
        AND is_verified = true
        AND EXISTS (
            SELECT 1
            FROM public.institution_site_profiles p
            WHERE p.institution_id = courses.institution_id
              AND p.production_enabled = true
        )
    );

DROP POLICY IF EXISTS courses_select_authenticated ON public.courses;
CREATE POLICY courses_select_authenticated ON public.courses
    FOR SELECT TO authenticated
    USING (
        is_active = true
        AND is_verified = true
        AND EXISTS (
            SELECT 1
            FROM public.institution_site_profiles p
            WHERE p.institution_id = courses.institution_id
              AND p.production_enabled = true
        )
    );

CREATE OR REPLACE FUNCTION public.deactivate_courses_when_production_disabled()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    IF OLD.production_enabled = true AND NEW.production_enabled = false THEN
        UPDATE public.courses
        SET is_active = false
        WHERE institution_id = NEW.institution_id;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_deactivate_courses_when_production_disabled
ON public.institution_site_profiles;

CREATE TRIGGER trg_deactivate_courses_when_production_disabled
AFTER UPDATE OF production_enabled ON public.institution_site_profiles
FOR EACH ROW
EXECUTE FUNCTION public.deactivate_courses_when_production_disabled();
