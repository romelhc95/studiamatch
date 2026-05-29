-- Fase 121: normalize category catalog names and restore missing base categories.

DO $$
DECLARE
    pair RECORD;
    old_id UUID;
    new_id UUID;
    old_salary_id UUID;
    new_salary_id UUID;
BEGIN
    FOR pair IN
        SELECT * FROM (VALUES
            ('Gestión y Agilidad', 'Gestion y Agilidad'),
            ('Ofimática y Productividad', 'Ofimatica y Productividad'),
            ('Tecnología', 'Tecnologia'),
            ('Logística y Operaciones', 'Logistica y Operaciones'),
            ('Ingeniería y Construcción', 'Ingenieria y Construccion'),
            ('Arte y Diseño Digital', 'Arte y Diseno Digital'),
            ('Diseño CAD y Manufactura', 'Diseno CAD y Manufactura'),
            ('Psicología y Salud Mental', 'Psicologia y Salud Mental'),
            ('Salud y Ciencias Médicas', 'Salud y Ciencias Medicas')
        ) AS mappings(old_name, new_name)
    LOOP
        SELECT id INTO old_id FROM public.categories WHERE name = pair.old_name LIMIT 1;
        SELECT id INTO new_id FROM public.categories WHERE name = pair.new_name LIMIT 1;
        SELECT id INTO old_salary_id
        FROM public.market_salaries
        WHERE category_name = pair.old_name OR (old_id IS NOT NULL AND category_id = old_id)
        LIMIT 1;
        SELECT id INTO new_salary_id
        FROM public.market_salaries
        WHERE category_name = pair.new_name OR (new_id IS NOT NULL AND category_id = new_id)
        LIMIT 1;

        IF old_id IS NOT NULL AND new_id IS NULL THEN
            UPDATE public.categories SET name = pair.new_name WHERE id = old_id;
            new_id := old_id;
            old_id := NULL;
        END IF;

        IF old_id IS NOT NULL AND new_id IS NOT NULL AND old_id <> new_id THEN
            UPDATE public.courses
            SET category_id = new_id,
                category = pair.new_name
            WHERE category_id = old_id OR category = pair.old_name;

            UPDATE public.category_rules
            SET category_id = new_id
            WHERE category_id = old_id;

            IF old_salary_id IS NOT NULL AND new_salary_id IS NOT NULL AND old_salary_id <> new_salary_id THEN
                DELETE FROM public.market_salaries
                WHERE id = old_salary_id;
            ELSE
                UPDATE public.market_salaries
                SET category_id = new_id,
                    category_name = pair.new_name
                WHERE id = old_salary_id;
            END IF;

            DELETE FROM public.categories WHERE id = old_id;
        END IF;

        SELECT id INTO new_id FROM public.categories WHERE name = pair.new_name LIMIT 1;
        IF new_id IS NOT NULL THEN
            UPDATE public.courses
            SET category = pair.new_name
            WHERE category_id = new_id OR category IN (pair.old_name, pair.new_name);

            SELECT id INTO old_salary_id
            FROM public.market_salaries
            WHERE category_name = pair.old_name OR (old_id IS NOT NULL AND category_id = old_id)
            LIMIT 1;
            SELECT id INTO new_salary_id
            FROM public.market_salaries
            WHERE category_name = pair.new_name OR category_id = new_id
            LIMIT 1;

            IF old_salary_id IS NOT NULL AND new_salary_id IS NOT NULL AND old_salary_id <> new_salary_id THEN
                DELETE FROM public.market_salaries
                WHERE id = old_salary_id;
            ELSIF old_salary_id IS NOT NULL THEN
                UPDATE public.market_salaries
                SET category_id = new_id,
                    category_name = pair.new_name
                WHERE id = old_salary_id;
            ELSIF new_salary_id IS NOT NULL THEN
                UPDATE public.market_salaries
                SET category_id = new_id,
                    category_name = pair.new_name
                WHERE id = new_salary_id;
            END IF;
        END IF;
    END LOOP;
END $$;

INSERT INTO public.categories (name, description)
VALUES
    ('Logistica y Operaciones', 'Cadena de suministro, operaciones, logistica y procesos'),
    ('Finanzas y Legal', 'Finanzas, contabilidad, auditoria, tributacion y compliance legal'),
    ('Ingenieria y Construccion', 'Ingenieria civil, construccion, mineria y gestion de obras'),
    ('Marketing y Ventas', 'Marketing digital, ventas, comercio electronico y crecimiento'),
    ('Arte y Diseno Digital', 'Diseno grafico, UX/UI, animacion y herramientas creativas'),
    ('Derecho y Humanidades', 'Derecho, humanidades, sociologia, filosofia y disciplinas afines')
ON CONFLICT (name) DO UPDATE
SET description = EXCLUDED.description;

WITH cat AS (
    SELECT id, name FROM public.categories
)
UPDATE public.market_salaries ms
SET category_id = cat.id
FROM cat
WHERE cat.name = ms.category_name
  AND ms.category_id IS DISTINCT FROM cat.id;

WITH cat AS (
    SELECT id, name FROM public.categories
)
INSERT INTO public.category_rules (category_id, keyword, priority)
SELECT cat.id, rules.keyword, rules.priority
FROM (VALUES
    ('Ofimatica y Productividad', 'office', 10),
    ('Ofimatica y Productividad', 'excel', 10),
    ('Ofimatica y Productividad', 'word', 10),
    ('Ofimatica y Productividad', 'powerpoint', 10),
    ('Ofimatica y Productividad', 'outlook', 10),
    ('Ofimatica y Productividad', 'visio', 10),
    ('Ofimatica y Productividad', 'project', 5),
    ('Gestion y Agilidad', 'agil', 10),
    ('Gestion y Agilidad', 'scrum', 20),
    ('Gestion y Agilidad', 'itil', 20),
    ('Gestion y Agilidad', 'pmp', 20),
    ('Gestion y Agilidad', 'gestion', 5),
    ('Gestion y Agilidad', 'management', 10),
    ('Gestion y Agilidad', 'liderazgo', 10),
    ('Gestion y Agilidad', 'agilidad', 25),
    ('Gestion y Agilidad', 'agile', 25),
    ('Gestion y Agilidad', 'kanban', 30),
    ('Tecnologia', 'tecnologia', 5),
    ('Logistica y Operaciones', 'logistica', 10),
    ('Logistica y Operaciones', 'operaciones', 5),
    ('Finanzas y Legal', 'finanzas', 20),
    ('Finanzas y Legal', 'contabilidad', 20),
    ('Finanzas y Legal', 'tributario', 25),
    ('Finanzas y Legal', 'auditoria', 20),
    ('Finanzas y Legal', 'laboral', 15),
    ('Finanzas y Legal', 'niif', 30),
    ('Ingenieria y Construccion', 'ingenieria', 15),
    ('Ingenieria y Construccion', 'construccion', 20),
    ('Ingenieria y Construccion', 'civil', 20),
    ('Ingenieria y Construccion', 'minas', 25),
    ('Ingenieria y Construccion', 'soma', 30),
    ('Ingenieria y Construccion', 'lean construction', 30),
    ('Arte y Diseno Digital', 'diseno grafico', 25),
    ('Arte y Diseno Digital', 'ui/ux', 30),
    ('Arte y Diseno Digital', 'animacion', 20),
    ('Arte y Diseno Digital', 'illustrator', 30),
    ('Arte y Diseno Digital', 'photoshop', 30),
    ('Arte y Diseno Digital', 'arte digital', 25),
    ('Derecho y Humanidades', 'derecho', 20),
    ('Derecho y Humanidades', 'penal', 25),
    ('Derecho y Humanidades', 'humanidades', 15),
    ('Derecho y Humanidades', 'sociologia', 20),
    ('Derecho y Humanidades', 'filosofia', 20),
    ('Marketing y Ventas', 'marketing', 20),
    ('Marketing y Ventas', 'ventas', 20),
    ('Marketing y Ventas', 'seo', 30),
    ('Marketing y Ventas', 'sem', 30),
    ('Marketing y Ventas', 'redes sociales', 25),
    ('Marketing y Ventas', 'comercio electronico', 25),
    ('Marketing y Ventas', 'e-commerce', 25)
) AS rules(category_name, keyword, priority)
JOIN cat ON cat.name = rules.category_name
ON CONFLICT (keyword) DO UPDATE
SET category_id = EXCLUDED.category_id,
    priority = EXCLUDED.priority;

UPDATE public.courses
SET name = name
WHERE category_confirmed = false
   OR category_confirmed IS NULL
   OR category = 'General / Por Clasificar';
