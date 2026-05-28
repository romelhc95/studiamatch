-- Fase 119: extend category, keyword and salary catalogs without code changes.

INSERT INTO public.categories (name, description)
VALUES
    ('Salud y Ciencias Medicas', 'Enfermeria, farmacia, procedimientos medicos y ciencias de la salud'),
    ('Psicologia y Salud Mental', 'Psicologia clinica, terapia, consejeria y salud mental'),
    ('Diseno CAD y Manufactura', 'Diseno asistido por computadora, BIM, manufactura e impresion 3D'),
    ('SAP y ERP Empresarial', 'Sistemas ERP, SAP y planificacion de recursos empresariales')
ON CONFLICT (name) DO UPDATE
SET description = EXCLUDED.description;

WITH cat AS (
    SELECT id, name FROM public.categories
)
INSERT INTO public.category_rules (category_id, keyword, priority)
SELECT cat.id, rules.keyword, rules.priority
FROM (VALUES
    ('Salud y Ciencias Medicas', 'enfermeria', 20),
    ('Salud y Ciencias Medicas', 'enfermería', 20),
    ('Salud y Ciencias Medicas', 'inyectables', 20),
    ('Salud y Ciencias Medicas', 'farmacia', 20),
    ('Salud y Ciencias Medicas', 'primeros auxilios', 20),
    ('Salud y Ciencias Medicas', 'farmacologia', 20),
    ('Psicologia y Salud Mental', 'psicologia', 20),
    ('Psicologia y Salud Mental', 'psicología', 20),
    ('Psicologia y Salud Mental', 'terapia', 20),
    ('Psicologia y Salud Mental', 'salud mental', 20),
    ('Psicologia y Salud Mental', 'clinica', 20),
    ('Psicologia y Salud Mental', 'consejeria', 20),
    ('Psicologia y Salud Mental', 'neurociencia', 20),
    ('Diseno CAD y Manufactura', 'autocad', 25),
    ('Diseno CAD y Manufactura', 'solidworks', 25),
    ('Diseno CAD y Manufactura', 'revit', 25),
    ('Diseno CAD y Manufactura', 'bim', 25),
    ('Diseno CAD y Manufactura', 'diseño 3d', 25),
    ('Diseno CAD y Manufactura', 'diseno 3d', 25),
    ('Diseno CAD y Manufactura', 'manufactura', 25),
    ('Diseno CAD y Manufactura', 'cnc', 25),
    ('Diseno CAD y Manufactura', 'impresion 3d', 25),
    ('SAP y ERP Empresarial', 'sap', 25),
    ('SAP y ERP Empresarial', 'sap fi', 25),
    ('SAP y ERP Empresarial', 'sap mm', 25),
    ('SAP y ERP Empresarial', 'sap hana', 25),
    ('SAP y ERP Empresarial', 'oracle erp', 25),
    ('SAP y ERP Empresarial', 'erp', 25),
    ('SAP y ERP Empresarial', 'sap business one', 25)
) AS rules(category_name, keyword, priority)
JOIN cat ON cat.name = rules.category_name
ON CONFLICT (keyword) DO UPDATE
SET category_id = EXCLUDED.category_id,
    priority = EXCLUDED.priority;

WITH cat AS (
    SELECT id, name FROM public.categories
)
INSERT INTO public.market_salaries (category_id, category_name, salary_junior, salary_average, salary_senior)
SELECT cat.id, salaries.category_name, salaries.salary_junior, salaries.salary_average, salaries.salary_senior
FROM (VALUES
    ('Salud y Ciencias Medicas', 2500, 5500, 12000),
    ('Psicologia y Salud Mental', 2000, 4500, 8000),
    ('Diseno CAD y Manufactura', 2200, 5000, 9000),
    ('SAP y ERP Empresarial', 3500, 8000, 15000)
) AS salaries(category_name, salary_junior, salary_average, salary_senior)
JOIN cat ON cat.name = salaries.category_name
ON CONFLICT (category_name) DO UPDATE
SET category_id = EXCLUDED.category_id,
    salary_junior = EXCLUDED.salary_junior,
    salary_average = EXCLUDED.salary_average,
    salary_senior = EXCLUDED.salary_senior,
    last_updated = now();

UPDATE public.courses
SET name = name
WHERE category_confirmed = false
   OR category_confirmed IS NULL
   OR category = 'General / Por Clasificar';
