-- ==============================================================================
-- FASE 18: Saneamiento de Huérfanos y Actualizaciones de Arquitectura
-- ==============================================================================

-- ==========================================
-- PARTE 1: RESPONSABILIDADES DE ARQUITECTURA
-- ==========================================

-- 1. Catálogo Maestro: Crear tabla de instituciones
CREATE TABLE IF NOT EXISTS public.institutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    official_website TEXT,
    type VARCHAR(50) CHECK (type IN ('Univ', 'Inst')),
    status VARCHAR(50) CHECK (status IN ('Activa', 'Inactiva')) DEFAULT 'Activa',
    region VARCHAR(100), -- Preparado para filtrado por regiones del Perú
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Integridad y Escalabilidad: Vincular cursos a la institución
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='courses' AND column_name='institution_id') THEN
        ALTER TABLE public.courses ADD COLUMN institution_id UUID REFERENCES public.institutions(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='courses' AND column_name='region') THEN
        ALTER TABLE public.courses ADD COLUMN region VARCHAR(100);
    END IF;
END $$;


-- ==========================================
-- PARTE 2: FASE 18 - SANEAMIENTO DE HUÉRFANOS
-- ==========================================

-- 1. Crear las 5 nuevas categorías
INSERT INTO public.categories (name, description) VALUES 
('Finanzas y Legal', 'Cursos relacionados a finanzas, contabilidad, leyes y normativas legales.'),
('Ingeniería y Construcción', 'Cursos de ingeniería civil, industrial, minas, construcción y afines.'),
('Arte y Diseño Digital', 'Cursos de diseño gráfico, UI/UX, animación, arte y medios digitales.'),
('Derecho y Humanidades', 'Cursos de derecho, filosofía, ciencias sociales y humanidades.'),
('Marketing y Ventas', 'Cursos de marketing digital, publicidad, estrategias de ventas y relaciones públicas.')
ON CONFLICT (name) DO NOTHING;

-- 2. Generar reglas de mapeo para las nuevas categorías y reforzar las existentes
WITH cat AS (SELECT id, name FROM public.categories)
INSERT INTO public.category_rules (category_id, keyword, priority)
SELECT c.id, k.keyword, k.priority
FROM (VALUES 
    -- Reglas: Finanzas y Legal
    ('Finanzas y Legal', 'finanzas', 20),
    ('Finanzas y Legal', 'contabilidad', 20),
    ('Finanzas y Legal', 'tributario', 25),
    ('Finanzas y Legal', 'auditoría', 20),
    ('Finanzas y Legal', 'laboral', 15),
    ('Finanzas y Legal', 'niif', 30),
    
    -- Reglas: Ingeniería y Construcción
    ('Ingeniería y Construcción', 'ingeniería', 15),
    ('Ingeniería y Construcción', 'construcción', 20),
    ('Ingeniería y Construcción', 'civil', 20),
    ('Ingeniería y Construcción', 'minas', 25),
    ('Ingeniería y Construcción', 'soma', 30),
    ('Ingeniería y Construcción', 'lean construction', 30),
    
    -- Reglas: Arte y Diseño Digital
    ('Arte y Diseño Digital', 'diseño gráfico', 25),
    ('Arte y Diseño Digital', 'ui/ux', 30),
    ('Arte y Diseño Digital', 'animación', 20),
    ('Arte y Diseño Digital', 'illustrator', 30),
    ('Arte y Diseño Digital', 'photoshop', 30),
    ('Arte y Diseño Digital', 'arte digital', 25),
    
    -- Reglas: Derecho y Humanidades
    ('Derecho y Humanidades', 'derecho', 20),
    ('Derecho y Humanidades', 'penal', 25),
    ('Derecho y Humanidades', 'humanidades', 15),
    ('Derecho y Humanidades', 'psicología', 20),
    ('Derecho y Humanidades', 'sociología', 20),
    ('Derecho y Humanidades', 'filosofía', 20),
    
    -- Reglas: Marketing y Ventas
    ('Marketing y Ventas', 'marketing', 20),
    ('Marketing y Ventas', 'ventas', 20),
    ('Marketing y Ventas', 'seo', 30),
    ('Marketing y Ventas', 'sem', 30),
    ('Marketing y Ventas', 'redes sociales', 25),
    ('Marketing y Ventas', 'comercio electrónico', 25),
    ('Marketing y Ventas', 'e-commerce', 25),

    -- Reforzar reglas existentes (Agilidad, SQL Server, RPA)
    ('Gestión y Agilidad', 'agilidad', 25),
    ('Gestión y Agilidad', 'agile', 25),
    ('Gestión y Agilidad', 'kanban', 30),
    
    ('Data Analytics', 'sql server', 30),
    ('Data Analytics', 'big data', 25),
    
    ('Desarrollo y Web', 'rpa', 30),
    ('Desarrollo y Web', 'uipath', 35),
    ('Desarrollo y Web', 'automatización', 20)

) AS k(cat_name, keyword, priority)
JOIN cat c ON c.name = k.cat_name
ON CONFLICT (keyword) DO NOTHING;

-- 3. Disparar re-categorización
-- (Se incluye name = name en caso de que el trigger tr_auto_assign_category restrinja la ejecución
-- a la actualización de columnas específicas, sin embargo, se respeta la solicitud del comando exacto)
UPDATE public.courses SET category_confirmed = false, name = name;
