-- Fase 117: fix auto category trigger word-boundary regex and UPDATE firing.

CREATE OR REPLACE FUNCTION public.fn_auto_assign_category()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path = public
AS $$
DECLARE
    target_category_id UUID;
    target_category_name TEXT;
BEGIN
    SELECT r.category_id, cat.name
    INTO target_category_id, target_category_name
    FROM public.category_rules r
    JOIN public.categories cat ON cat.id = r.category_id
    WHERE
        COALESCE(NEW.name, '') ~* ('\y' || regexp_replace(r.keyword, '([\\.^$|?*+(){}\[\]])', '\\\1', 'g') || '\y') OR
        COALESCE(NEW.description_long, '') ~* ('\y' || regexp_replace(r.keyword, '([\\.^$|?*+(){}\[\]])', '\\\1', 'g') || '\y') OR
        COALESCE(NEW.syllabus, '') ~* ('\y' || regexp_replace(r.keyword, '([\\.^$|?*+(){}\[\]])', '\\\1', 'g') || '\y')
    ORDER BY r.priority DESC
    LIMIT 1;

    IF target_category_id IS NOT NULL THEN
        NEW.category_id := target_category_id;
        NEW.category := target_category_name;
        NEW.category_confirmed := true;
    ELSE
        SELECT id, name
        INTO target_category_id, target_category_name
        FROM public.categories
        WHERE name = 'General / Por Clasificar'
        LIMIT 1;

        NEW.category_id := target_category_id;
        NEW.category := target_category_name;
        NEW.category_confirmed := false;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS tr_auto_assign_category ON public.courses;
CREATE TRIGGER tr_auto_assign_category
    BEFORE INSERT OR UPDATE OF name, description_long, syllabus ON public.courses
    FOR EACH ROW
    EXECUTE FUNCTION public.fn_auto_assign_category();

UPDATE public.courses
SET name = name
WHERE category_confirmed = false
   OR category_confirmed IS NULL
   OR category_id IS NULL
   OR category = 'General / Por Clasificar';
