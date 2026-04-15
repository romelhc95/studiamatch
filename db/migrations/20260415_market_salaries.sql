-- ==========================================
-- MIGRACIÓN: Market Salaries Baseline
-- Fecha: 2026-04-15
-- Descripción: Creación de la tabla market_salaries para el cálculo dinámico del ROI.
-- Basado en investigación de mercado proyectada para Abril 2026 en Perú.
-- ==========================================

-- 1. CREACIÓN DE TABLA
CREATE TABLE IF NOT EXISTS public.market_salaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES public.categories(id) ON DELETE CASCADE UNIQUE,
    category_name TEXT NOT NULL,
    min_salary_junior NUMERIC(12, 2) NOT NULL, -- Salario base para perfiles Junior
    avg_salary NUMERIC(12, 2) NOT NULL,        -- Salario promedio del mercado
    currency TEXT DEFAULT 'PEN',
    last_updated TIMESTAMPTZ DEFAULT now()
);

-- 2. POBLACIÓN DE DATOS (SEEDING)
-- Usamos un CTE para obtener los IDs correctos de la tabla categories
WITH cat AS (SELECT id, name FROM public.categories)
INSERT INTO public.market_salaries (category_id, category_name, min_salary_junior, avg_salary)
SELECT c.id, k.cat_name, k.jr_sal, k.avg_sal
FROM (VALUES 
    ('General / Por Clasificar', 1200, 2800),
    ('Ofimática y Productividad', 1800, 3200),
    ('Data Analytics', 4200, 8200),
    ('Ciberseguridad', 4800, 10500),
    ('Cloud Computing', 5200, 11500),
    ('Data Science & IA', 6000, 14000),
    ('DevOps & Infraestructura', 5500, 12500),
    ('Gestión y Agilidad', 4000, 8800),
    ('Redes y Conectividad', 3200, 6500),
    ('Desarrollo y Web', 4500, 9800),
    ('Tecnología', 3800, 7500),
    ('Logística y Operaciones', 2800, 5800),
    ('Finanzas y Legal', 3500, 7500),
    ('Ingeniería y Construcción', 4000, 9000),
    ('Arte y Diseño Digital', 3000, 6000),
    ('Derecho y Humanidades', 3000, 6200),
    ('Marketing y Ventas', 3200, 6800)
) AS k(cat_name, jr_sal, avg_sal)
JOIN cat c ON c.name = k.cat_name
ON CONFLICT (category_id) DO UPDATE SET 
    min_salary_junior = EXCLUDED.min_salary_junior,
    avg_salary = EXCLUDED.avg_salary,
    last_updated = now();
