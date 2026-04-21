-- ==========================================
-- SCRIPT MAESTRO DE INICIALIZACIÃ“N: PRODUCCIÃ“N
-- Proyecto: StudIAMatch
-- Fecha: 2026-04-16
-- DescripciÃ³n: Esquema saneado (sin columnas redundantes) con RLS y Triggers activos.
-- ==========================================

-- 1. TIPOS PERSONALIZADOS (Enums)
DO $$ BEGIN
    CREATE TYPE lead_type AS ENUM ('info', 'recommendation');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE lead_status AS ENUM ('pending', 'contacted', 'resolved');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. TABLAS BASE
-- Instituciones
CREATE TABLE IF NOT EXISTS public.institutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    slug VARCHAR UNIQUE NOT NULL,
    website_url TEXT,
    location_lat NUMERIC,
    location_long NUMERIC,
    address TEXT,
    last_harvest_at TIMESTAMPTZ,
    last_harvest_duration_sec INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- CategorÃ­as
CREATE TABLE IF NOT EXISTS public.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Reglas de CategorÃ­a
CREATE TABLE IF NOT EXISTS public.category_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    keyword TEXT UNIQUE NOT NULL,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Cursos (ESQUEMA SANEADO - SIN SUB-CATEGORÃAS NI EXCESOS)
CREATE TABLE IF NOT EXISTS public.courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    slug VARCHAR NOT NULL,
    price_pen NUMERIC CHECK (price_pen >= 0),
    price_status TEXT DEFAULT 'publicado',
    mode VARCHAR CHECK (mode IN ('Presencial', 'HÃ­brido', 'Remoto')),
    address TEXT,
    duration VARCHAR,
    category VARCHAR,
    category_id UUID REFERENCES categories(id),
    category_confirmed BOOLEAN DEFAULT false,
    url TEXT UNIQUE,
    description_long TEXT,
    syllabus TEXT,
    target_audience TEXT,
    requirements TEXT,
    certification TEXT,
    benefits TEXT,
    objectives TEXT,
    expected_monthly_salary NUMERIC,
    seniority_level TEXT DEFAULT 'Mid',
    roi_months NUMERIC DEFAULT 0,
    course_type TEXT,
    brochure_url TEXT,
    brochure_text TEXT,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    start_date_text VARCHAR,
    last_scraped_at TIMESTAMPTZ,
    last_404_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Salarios de Mercado (Master Data)
CREATE TABLE IF NOT EXISTS public.market_salaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    category_name TEXT UNIQUE NOT NULL,
    salary_junior NUMERIC NOT NULL,
    salary_average NUMERIC NOT NULL,
    salary_senior NUMERIC NOT NULL,
    last_updated TIMESTAMPTZ DEFAULT now()
);

-- Leads (Ventas)
CREATE TABLE IF NOT EXISTS public.leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR NOT NULL,
    last_name VARCHAR,
    email VARCHAR NOT NULL,
    whatsapp VARCHAR NOT NULL,
    type lead_type,
    status lead_status DEFAULT 'pending',
    course_id UUID REFERENCES courses(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. FUNCIONES Y TRIGGERS (INTELIGENCIA DE CARGA)
CREATE OR REPLACE FUNCTION fn_auto_assign_category()
RETURNS TRIGGER AS $$
DECLARE
    found_category_id UUID;
    general_id UUID;
BEGIN
    SELECT category_id INTO found_category_id FROM category_rules
    WHERE LOWER(NEW.name) ~* ('\y' || keyword || '\y') OR LOWER(COALESCE(NEW.description_long, '')) ~* ('\y' || keyword || '\y')
    ORDER BY priority DESC LIMIT 1;

    IF found_category_id IS NOT NULL THEN
        NEW.category_id := found_category_id;
        NEW.category_confirmed := true; 
    ELSE
        SELECT id INTO general_id FROM categories WHERE name = 'General / Por Clasificar' LIMIT 1;
        NEW.category_id := general_id;
        NEW.category_confirmed := false;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- CIURGÍA: Borrar si existe para evitar error 42710
DROP TRIGGER IF EXISTS tr_auto_assign_category ON public.courses;

CREATE TRIGGER tr_auto_assign_category
BEFORE INSERT OR UPDATE OF name, description_long ON courses
FOR EACH ROW EXECUTE FUNCTION fn_auto_assign_category();

-- 4. SEGURIDAD (RLS)
ALTER TABLE public.institutions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public read for institutions" ON public.institutions;
CREATE POLICY "Public read for institutions" ON public.institutions FOR SELECT USING (true);

ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public read for categories" ON public.categories;
CREATE POLICY "Public read for categories" ON public.categories FOR SELECT USING (true);

ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public read for courses" ON public.courses;
CREATE POLICY "Public read for courses" ON public.courses FOR SELECT USING (true);

ALTER TABLE public.market_salaries ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public read for market_salaries" ON public.market_salaries;
CREATE POLICY "Public read for market_salaries" ON public.market_salaries FOR SELECT USING (true);

ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can insert leads" ON public.leads;
-- Solo el sistema puede insertar leads (Anon key with specific policy or authenticated)
CREATE POLICY "Anyone can insert leads" ON public.leads FOR INSERT WITH CHECK (true);
-- DEBUG: Exportando datos...
-- CATEGORIAS
INSERT INTO public.categories (name, description) VALUES ('General / Por Clasificar', ''),
('Ofim├ítica y Productividad', ''),
('Data Analytics', ''),
('Ciberseguridad', ''),
('Cloud Computing', ''),
('Data Science & IA', ''),
('DevOps & Infraestructura', ''),
('Gesti├│n y Agilidad', ''),
('Redes y Conectividad', ''),
('Desarrollo y Web', ''),
('Tecnolog├¡a', ''),
('Log├¡stica y Operaciones', ''),
('Finanzas y Legal', 'Cursos relacionados a finanzas, contabilidad, leyes y normativas
legales.'),
('Ingenier├¡a y Construcci├│n', 'Cursos de ingenier├¡a civil, industrial, minas, construcci├│n y
afines.'),
('Arte y Dise├▒o Digital', 'Cursos de dise├▒o gr├ífico, UI/UX, animaci├│n, arte y medios
digitales.'),
('Derecho y Humanidades', 'Cursos de derecho, filosof├¡a, ciencias sociales y humanidades.'),
('Marketing y Ventas', 'Cursos de marketing digital, publicidad, estrategias de ventas y
relaciones p├║blicas.'),
('Artes y Cultura', 'Cursos de expresi├│n art├¡stica, m├║sica, teatro, danza y
gesti├│n cultural.') ON CONFLICT (name) DO NOTHING;

-- SALARIOS
INSERT INTO public.market_salaries (category_id, category_name, salary_junior, salary_average, salary_senior)
SELECT c.id, s.cat_name, s.sj, s.sa, s.ss FROM ( VALUES 
('Data Science & IA', 5200, 11500, 18000),
('Ciberseguridad', 4800, 9500, 16000),
('Cloud Computing', 4500, 10000, 17000),
('DevOps & Infraestructura', 4500, 9800, 16500),
('Desarrollo y Web', 3500, 7500, 14000),
('Data Analytics', 3800, 8200, 13000),
('Log├¡stica y Operaciones', 2800, 5800, 11000),
('Finanzas y Legal', 3200, 7200, 15000),
('Ingenier├¡a y Construcci├│n', 3000, 6500, 14000),
('Marketing y Ventas', 2500, 5500, 10000),
('Gesti├│n y Agilidad', 3500, 8500, 15000),
('Redes y Conectividad', 2800, 6000, 11000),
('Ofim├ítica y Productividad', 1200, 2800, 4500),
('Arte y Dise├▒o Digital', 2200, 4800, 9000),
('Derecho y Humanidades', 2500, 5500, 12000),
('Tecnolog├¡a', 3000, 7000, 13000),
('General / Por Clasificar', 1025, 2500, 5000)
) as s(cat_name, sj, sa, ss) JOIN public.categories c ON c.name = s.cat_name ON CONFLICT (category_name) DO NOTHING;
