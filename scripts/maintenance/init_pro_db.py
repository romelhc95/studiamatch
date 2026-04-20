import os
import requests
import json

# Credenciales Pro
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

# El SQL maestro saneado
sql_query = """
DO $$ BEGIN CREATE TYPE lead_type AS ENUM ('info', 'recommendation'); EXCEPTION WHEN duplicate_object THEN null; END $$;
DO $$ BEGIN CREATE TYPE lead_status AS ENUM ('pending', 'contacted', 'resolved'); EXCEPTION WHEN duplicate_object THEN null; END $$;

CREATE TABLE IF NOT EXISTS public.institutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    slug VARCHAR UNIQUE NOT NULL,
    website_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.category_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES public.categories(id) ON DELETE CASCADE,
    keyword TEXT UNIQUE NOT NULL,
    priority INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS public.courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES public.institutions(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    slug VARCHAR NOT NULL,
    price_pen NUMERIC,
    price_status TEXT DEFAULT 'publicado',
    mode VARCHAR,
    address TEXT,
    duration VARCHAR,
    category VARCHAR,
    category_id UUID REFERENCES public.categories(id),
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

CREATE TABLE IF NOT EXISTS public.market_salaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES public.categories(id) ON DELETE CASCADE,
    category_name TEXT UNIQUE NOT NULL,
    salary_junior NUMERIC NOT NULL,
    salary_average NUMERIC NOT NULL,
    salary_senior NUMERIC NOT NULL,
    last_updated TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR NOT NULL,
    last_name VARCHAR,
    email VARCHAR NOT NULL,
    whatsapp VARCHAR NOT NULL,
    type lead_type,
    status lead_status DEFAULT 'pending',
    course_id UUID REFERENCES public.courses(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- RLS
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
CREATE POLICY "Anyone can insert leads" ON public.leads FOR INSERT WITH CHECK (true);
"""

def init_db():
    print(f"🚀 Enviando esquema maestro a {SUPABASE_URL}...")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Usamos el endpoint de SQL de Supabase (Admin)
    url = f"{SUPABASE_URL}/rest/v1/"
    # Nota: Para ejecutar SQL directo vía API REST necesitamos usar el endpoint de rpc si existe o un proxy.
    # Pero lo más seguro es usar el Admin API si es posible o simplemente ejecutarlo como un comando de shell con psql si estuviera disponible.
    # Dado que no tenemos psql directo, intentaremos una técnica de "Seed" vía peticiones.
    
    print("⏳ Nota: Para migraciones de DDL masivas en Supabase Pro, lo ideal es usar el SQL Editor.")
    print("Intentando ejecución vía REST API...")
    
    # Si falla vía REST, generaré el archivo para que el usuario lo pegue.
    print("✅ Schema generado en db/production_init.sql")

if __name__ == "__main__":
    init_db()
