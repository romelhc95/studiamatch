-- ==========================================
-- MIGRACIÓN: Seniority Level & ROI Update
-- Fecha: 2026-04-16
-- Descripción: Inferencia de Seniority y actualización masiva de expected_monthly_salary.
-- ==========================================

-- 1. EXTENSIÓN DE LA TABLA market_salaries
-- Agregamos la columna salary_senior si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='market_salaries' AND column_name='salary_senior') THEN
        ALTER TABLE public.market_salaries ADD COLUMN salary_senior NUMERIC(12, 2);
    END IF;
END $$;

-- 2. POBLACIÓN DE salary_senior (Basado en factor de mercado 1.5x sobre el promedio)
UPDATE public.market_salaries 
SET salary_senior = avg_salary * 1.5
WHERE salary_senior IS NULL;

-- 3. EXTENSIÓN DE LA TABLA courses
-- Agregamos los campos necesarios para el ROI
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='courses' AND column_name='seniority_level') THEN
        ALTER TABLE public.courses ADD COLUMN seniority_level VARCHAR(20) CHECK (seniority_level IN ('Junior', 'Mid', 'Senior'));
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='courses' AND column_name='expected_monthly_salary') THEN
        ALTER TABLE public.courses ADD COLUMN expected_monthly_salary NUMERIC(12, 2);
    END IF;
END $$;

-- 4. INFERENCIA DE NIVEL DE SENIORITY (Análisis de Name y Description)
-- Usamos CASE con ILIKE para clasificar los 180 cursos
UPDATE public.courses
SET seniority_level = CASE
    -- SENIOR: Maestrías, MBAs, Alta Dirección, Expertos
    WHEN (name ILIKE '%Maestría%' OR name ILIKE '%Maestria%' OR name ILIKE '%Master%' OR name ILIKE '%MBA%' 
          OR name ILIKE '%Doctorado%' OR name ILIKE '%Executive%' OR name ILIKE '%Gerencia%' 
          OR name ILIKE '%Dirección%' OR name ILIKE '%Experto%' OR name ILIKE '%Senior%'
          OR name ILIKE '%Alta Especialización%' OR name ILIKE '%Alta Especializacion%') THEN 'Senior'
    
    -- MID: Diplomados, Especializaciones, Certificaciones Profesionales
    WHEN (name ILIKE '%Diplomado%' OR name ILIKE '%Especialización%' OR name ILIKE '%Especializacion%' 
          OR name ILIKE '%Certificación%' OR name ILIKE '%Certificacion%' OR name ILIKE '%Professional%'
          OR name ILIKE '%Analyst%' OR name ILIKE '%Especialista%' OR name ILIKE '%Intermediate%'
          OR name ILIKE '%Avanzado%' OR name ILIKE '%Advanced%') THEN 'Mid'
    
    -- JUNIOR: Cursos básicos, talleres, fundamentos (Default)
    ELSE 'Junior'
END;

-- 5. REFINAMIENTO DE JUNIOR (Detección de palabras clave de nivel básico)
UPDATE public.courses
SET seniority_level = 'Junior'
WHERE seniority_level <> 'Senior' -- No degradar Seniors
AND (name ILIKE '%Básico%' OR name ILIKE '%Basico%' OR name ILIKE '%Basic%' 
     OR name ILIKE '%Fundamentos%' OR name ILIKE '%Fundamentals%' OR name ILIKE '%Intro%'
     OR name ILIKE '%Iniciación%' OR name ILIKE '%Iniciacion%' OR name ILIKE '%Taller%'
     OR name ILIKE '%Excel%' OR name ILIKE '%Office%' OR name ILIKE '%PowerPoint%' 
     OR name ILIKE '%Word%' OR name ILIKE '%Outlook%');

-- 6. ACTUALIZACIÓN MASIVA DE expected_monthly_salary
-- Cruzamos con la tabla market_salaries según la categoría del curso
UPDATE public.courses c
SET expected_monthly_salary = CASE
    WHEN c.seniority_level = 'Junior' THEN m.min_salary_junior
    WHEN c.seniority_level = 'Mid' THEN m.avg_salary
    WHEN c.seniority_level = 'Senior' THEN m.salary_senior
    ELSE m.avg_salary -- Fallback al promedio si algo falla
END
FROM public.market_salaries m
WHERE c.category_id = m.category_id;

-- 7. MANEJO DE CATEGORÍA "General / Por Clasificar" (Fallback)
-- Si el curso no tiene categoría asignada o m.category_id es nulo, usamos el promedio general
UPDATE public.courses c
SET expected_monthly_salary = (SELECT avg_salary FROM public.market_salaries WHERE category_name = 'General / Por Clasificar')
WHERE expected_monthly_salary IS NULL;

-- 8. VERIFICACIÓN DE RESULTADOS (REPORTING)
-- Se recomienda ejecutar el siguiente SELECT tras la migración:
-- SELECT seniority_level, count(*), avg(expected_monthly_salary) FROM public.courses GROUP BY seniority_level;
