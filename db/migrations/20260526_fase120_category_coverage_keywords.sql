-- Fase 120: close coverage gaps found by category_coverage_audit.

WITH cat AS (
    SELECT id, name FROM public.categories
)
INSERT INTO public.category_rules (category_id, keyword, priority)
SELECT cat.id, rules.keyword, rules.priority
FROM (VALUES
    ('Desarrollo y Web', 'power apps', 25),
    ('Desarrollo y Web', 'power automate', 25),
    ('Gestion y Agilidad', 'mba', 25),
    ('Gestion y Agilidad', 'administracion', 20),
    ('Gestion y Agilidad', 'administración', 20),
    ('Gestion y Agilidad', 'gestion estrategica', 20),
    ('Gestion y Agilidad', 'gestión estratégica', 20),
    ('Marketing y Ventas', 'comunicacion', 20),
    ('Marketing y Ventas', 'comunicación', 20),
    ('Marketing y Ventas', 'contenidos', 20),
    ('Finanzas y Legal', 'tributacion', 20),
    ('Finanzas y Legal', 'tributación', 20),
    ('Finanzas y Legal', 'politica fiscal', 20),
    ('Finanzas y Legal', 'política fiscal', 20),
    ('Ingenieria y Construccion', 'arquitectura', 20),
    ('Ingenieria y Construccion', 'ingenieria del diseno', 20),
    ('Ingenieria y Construccion', 'ingeniería del diseño', 20)
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
