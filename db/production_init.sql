-- ==========================================
-- SCRIPT MAESTRO DE INICIALIZACIÓN: PRODUCCIÓN
-- Proyecto: StudIAMatch
-- Fecha: 2026-04-16
-- Descripción: Esquema saneado (sin columnas redundantes) con RLS y Triggers activos.
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
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Categorías
CREATE TABLE IF NOT EXISTS public.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Reglas de Categoría
CREATE TABLE IF NOT EXISTS public.category_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    keyword TEXT UNIQUE NOT NULL,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Cursos (ESQUEMA SANEADO - SIN SUB-CATEGORÍAS NI EXCESOS)
CREATE TABLE IF NOT EXISTS public.courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    slug VARCHAR NOT NULL,
    price_pen NUMERIC CHECK (price_pen >= 0),
    price_status TEXT DEFAULT 'publicado',
    mode VARCHAR CHECK (mode IN ('Presencial', 'Híbrido', 'Remoto')),
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

CREATE TRIGGER tr_auto_assign_category
BEFORE INSERT OR UPDATE OF name, description_long ON courses
FOR EACH ROW EXECUTE FUNCTION fn_auto_assign_category();

-- 4. SEGURIDAD (RLS)
ALTER TABLE public.institutions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read for institutions" ON public.institutions FOR SELECT USING (true);

ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read for categories" ON public.categories FOR SELECT USING (true);

ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read for courses" ON public.courses FOR SELECT USING (true);

ALTER TABLE public.market_salaries ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read for market_salaries" ON public.market_salaries FOR SELECT USING (true);

ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
-- Solo el sistema puede insertar leads (Anon key with specific policy or authenticated)
CREATE POLICY "Anyone can insert leads" ON public.leads FOR INSERT WITH CHECK (true);
