-- =============================================================================
-- RESTORE FULL SCHEMA — StudIAMatch
-- Proyecto: StudIAMatch (Free: YOUR_FREE_PROJECT_REF)
-- Descripcion: Schema completo desde cero (PRODUCTION_MASTER + migraciones)
-- Ejecutar en: Supabase Dashboard > SQL Editor (Ctrl+Enter todo)
-- =============================================================================

-- =============================================================================
-- 1. EXTENSIONES
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- 2. TIPOS PERSONALIZADOS (Enums)
-- =============================================================================
DO $$ BEGIN
    CREATE TYPE lead_type AS ENUM ('info', 'recommendation');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE lead_status AS ENUM ('pending', 'contacted', 'resolved');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- 3. TABLAS — PUBLICAS (contenido)
-- =============================================================================

-- 3a. Instituciones
CREATE TABLE IF NOT EXISTS public.institutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    slug VARCHAR UNIQUE NOT NULL,
    website_url TEXT,
    official_website TEXT,
    type VARCHAR(50) CHECK (type IN ('Univ', 'Inst')),
    status VARCHAR(50) CHECK (status IN ('Activa', 'Inactiva')) DEFAULT 'Activa',
    region VARCHAR(100),
    location_lat NUMERIC,
    location_long NUMERIC,
    address TEXT,
    last_harvest_at TIMESTAMPTZ,
    last_harvest_duration_sec INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 3b. Categorias
CREATE TABLE IF NOT EXISTS public.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3c. Reglas de Categoria
CREATE TABLE IF NOT EXISTS public.category_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    keyword TEXT UNIQUE NOT NULL,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3d. Cursos
CREATE TABLE IF NOT EXISTS public.courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    slug VARCHAR NOT NULL,
    price_pen NUMERIC CHECK (price_pen >= 0),
    price_status TEXT DEFAULT 'publicado',
    mode VARCHAR CHECK (mode IN ('Presencial', 'Hibrido', 'Remoto')),
    address TEXT,
    region VARCHAR(100),
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
    seniority_level VARCHAR(20) DEFAULT 'Mid',
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

-- 3e. Salarios de Mercado
CREATE TABLE IF NOT EXISTS public.market_salaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    category_name TEXT UNIQUE NOT NULL,
    salary_junior NUMERIC NOT NULL,
    salary_average NUMERIC NOT NULL,
    salary_senior NUMERIC NOT NULL,
    last_updated TIMESTAMPTZ DEFAULT now()
);

-- 3f. Leads
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

-- 3g. Ratings
CREATE TABLE IF NOT EXISTS public.ratings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    course_id UUID NOT NULL,
    rating_value INTEGER NOT NULL CHECK (rating_value >= 1 AND rating_value <= 5),
    user_nickname VARCHAR(255) NOT NULL CHECK (char_length(TRIM(user_nickname)) > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3h. Reviews
CREATE TABLE IF NOT EXISTS public.reviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    course_id UUID NOT NULL,
    content TEXT NOT NULL CHECK (char_length(TRIM(content)) > 0),
    user_nickname VARCHAR(255) NOT NULL CHECK (char_length(TRIM(user_nickname)) > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- =============================================================================
-- 4. TABLAS — PIPELINE ETL
-- =============================================================================

-- 4a. crawler_exclusions
CREATE TABLE IF NOT EXISTS crawler_exclusions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id  UUID REFERENCES institutions(id) ON DELETE CASCADE,
    pattern         TEXT NOT NULL,
    reason          TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_crawler_exclusions_institution ON crawler_exclusions(institution_id);
CREATE INDEX IF NOT EXISTS idx_crawler_exclusions_active ON crawler_exclusions(is_active) WHERE is_active = TRUE;
ALTER TABLE crawler_exclusions ADD CONSTRAINT IF NOT EXISTS uq_crawler_exclusions_inst_pattern UNIQUE (institution_id, pattern);
COMMENT ON TABLE crawler_exclusions IS 'Patrones de URL a excluir del harvesting';

-- 4b. staging_raw
CREATE TABLE IF NOT EXISTS staging_raw (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id  UUID REFERENCES institutions(id) ON DELETE SET NULL,
    url             TEXT UNIQUE,
    raw_name        TEXT,
    raw_description TEXT,
    raw_html        TEXT,
    html_content    TEXT,
    description_long TEXT,
    raw_json_ld     JSONB,
    raw_og_tags     JSONB,
    status          TEXT DEFAULT 'pending',
    content_hash    TEXT,
    effective_url   TEXT,
    canonical_url   TEXT,
    discard_reason  TEXT,
    processing_error TEXT,
    metadata        JSONB DEFAULT '{}'::jsonb,
    last_harvested_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_staging_raw_status ON staging_raw(status);
CREATE INDEX IF NOT EXISTS idx_staging_raw_institution_status ON staging_raw(institution_id, status);
CREATE INDEX IF NOT EXISTS idx_staging_raw_url ON staging_raw(url);
COMMENT ON TABLE staging_raw IS 'Estacion 1: HTML crudo del harvester';

-- 4c. cleansed_programs
CREATE TABLE IF NOT EXISTS cleansed_programs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staging_id      UUID,
    institution_id  UUID REFERENCES institutions(id) ON DELETE SET NULL,
    url             TEXT UNIQUE,
    effective_url   TEXT,
    canonical_url   TEXT,
    clean_name      TEXT,
    clean_description TEXT,
    modality        TEXT,
    location        TEXT,
    base_price      NUMERIC,
    currency        TEXT DEFAULT 'PEN',
    status          TEXT DEFAULT 'pending',
    metadata        JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cleansed_programs_status ON cleansed_programs(status);
CREATE INDEX IF NOT EXISTS idx_cleansed_programs_staging ON cleansed_programs(staging_id);
CREATE INDEX IF NOT EXISTS idx_cleansed_programs_url ON cleansed_programs(url);
COMMENT ON TABLE cleansed_programs IS 'Estacion 2: HTML limpio y consolidado';

-- 4d. enriched_programs
CREATE TABLE IF NOT EXISTS enriched_programs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cleansed_id     UUID UNIQUE,
    institution_id  UUID REFERENCES institutions(id) ON DELETE SET NULL,
    url             TEXT,
    official_name   TEXT,
    duration_text   TEXT,
    duration_months INTEGER,
    total_cost_est  NUMERIC,
    requirements    TEXT,
    graduate_profile TEXT,
    curriculum_summary JSONB,
    modality        TEXT,
    primary_campus  TEXT,
    degree_type     TEXT,
    start_date      TEXT,
    partnerships    TEXT,
    certifications  TEXT,
    language        TEXT,
    categories      TEXT,
    difficulty_level TEXT,
    ai_summary      TEXT,
    embedding       TEXT,
    status          TEXT DEFAULT 'pending',
    metadata        JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_enriched_programs_status ON enriched_programs(status);
CREATE INDEX IF NOT EXISTS idx_enriched_programs_cleansed ON enriched_programs(cleansed_id);
CREATE INDEX IF NOT EXISTS idx_enriched_programs_url ON enriched_programs(url);
COMMENT ON TABLE enriched_programs IS 'Estacion 3: Datos enriquecidos por LLM';

-- =============================================================================
-- 5. INDICES ADICIONALES
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_courses_name_trgm ON courses USING gin (name gin_trgm_ops);

-- =============================================================================
-- 6. FUNCIONES RPC — Pipeline ETL (final version with SET search_path)
-- =============================================================================

-- NOTE: Supabase PG17 has a known issue with SET search_path + UPDATE RETURNING
-- in SECURITY DEFINER functions ("cannot set path in scalar").
-- The lock functions below use SELECT-only FOR UPDATE SKIP LOCKED.
-- Callers must call mark_records_processing() separately to set status.

-- 6a. lock_staging_records (SELECT only)
CREATE OR REPLACE FUNCTION public.lock_staging_records(inst_id uuid, batch_size integer DEFAULT 100)
 RETURNS TABLE(id uuid, url text, institution_id uuid, raw_html text, raw_name text, raw_description text)
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
BEGIN
    RETURN QUERY
    SELECT sr.id, sr.url, sr.institution_id, sr.raw_html, sr.raw_name, sr.raw_description
    FROM staging_raw sr
    WHERE sr.status = 'pending'
    AND (sr.institution_id = inst_id OR inst_id IS NULL)
    ORDER BY sr.last_harvested_at ASC NULLS FIRST
    LIMIT batch_size
    FOR UPDATE SKIP LOCKED;
END;
$function$;

-- 6b. mark_records_processing (sets locked records to processing)
CREATE OR REPLACE FUNCTION public.mark_records_processing(rec_ids uuid[])
 RETURNS void
 LANGUAGE sql
AS $function$
    UPDATE staging_raw SET status = 'processing' WHERE id = ANY(rec_ids) AND status = 'pending';
$function$;

-- 6c. unlock_staging_record
CREATE OR REPLACE FUNCTION public.unlock_staging_record(rec_id uuid, new_status text, reason text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE sql
AS $function$
    UPDATE staging_raw
    SET status = new_status,
        discard_reason = CASE WHEN new_status = 'discarded' THEN reason ELSE discard_reason END,
        processing_error = CASE WHEN new_status = 'error' THEN reason ELSE processing_error END
    WHERE id = rec_id AND status = 'processing';
$function$;

-- 6d. lock_cleansed_records (SELECT only)
CREATE OR REPLACE FUNCTION public.lock_cleansed_records(batch_size integer DEFAULT 10)
 RETURNS TABLE(id uuid, cleansed_id uuid, clean_name text, clean_description text, institution_id uuid, url text)
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
BEGIN
    RETURN QUERY
    SELECT cp.id, cp.staging_id, cp.clean_name, cp.clean_description, cp.institution_id, cp.url
    FROM cleansed_programs cp
    WHERE cp.status = 'pending'
    ORDER BY cp.id ASC
    LIMIT batch_size
    FOR UPDATE SKIP LOCKED;
END;
$function$;

-- 6e. mark_cleansed_processing
CREATE OR REPLACE FUNCTION public.mark_cleansed_processing(rec_ids uuid[])
 RETURNS void
 LANGUAGE sql
AS $function$
    UPDATE cleansed_programs SET status = 'processing' WHERE id = ANY(rec_ids) AND status = 'pending';
$function$;

-- 6f. unlock_cleansed_record
CREATE OR REPLACE FUNCTION public.unlock_cleansed_record(rec_id uuid, new_status text, error_msg text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE sql
AS $function$
    UPDATE cleansed_programs SET status = new_status WHERE id = rec_id AND status = 'processing';
$function$;

-- 6g. atomic_cleansing_promote
CREATE OR REPLACE FUNCTION public.atomic_cleansing_promote(p_staging_ids uuid[], p_cleansed_data jsonb)
 RETURNS SETOF cleansed_programs
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
BEGIN
    INSERT INTO cleansed_programs (
        staging_id, institution_id, url, effective_url, canonical_url,
        clean_name, clean_description, modality, location, base_price,
        currency, status, metadata
    )
    SELECT
        (item->>'staging_id')::UUID,
        (item->>'institution_id')::UUID,
        item->>'url',
        item->>'effective_url',
        item->>'canonical_url',
        item->>'clean_name',
        item->>'clean_description',
        item->>'modality',
        item->>'location',
        (item->>'base_price')::NUMERIC,
        item->>'currency',
        'pending',
        (item->>'metadata')::JSONB
    FROM jsonb_array_elements(p_cleansed_data) AS item
    ON CONFLICT (url) DO UPDATE SET
        clean_name = EXCLUDED.clean_name,
        clean_description = EXCLUDED.clean_description,
        status = 'pending';

    UPDATE staging_raw
    SET status = 'processed'
    WHERE id = ANY(p_staging_ids) AND status = 'processing';

    RETURN QUERY
    SELECT * FROM cleansed_programs
    WHERE url IN (SELECT item->>'url' FROM jsonb_array_elements(p_cleansed_data) AS item);
END;
$function$;

-- 6h. atomic_enrichment_promote
CREATE OR REPLACE FUNCTION public.atomic_enrichment_promote(p_enriched_data jsonb, p_cleansed_id uuid)
 RETURNS SETOF enriched_programs
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
BEGIN
    INSERT INTO enriched_programs (
        cleansed_id, institution_id, url, official_name, duration_text,
        duration_months, total_cost_est, requirements, graduate_profile,
        curriculum_summary, modality, primary_campus, degree_type,
        start_date, partnerships, certifications, language, categories,
        ai_summary, status
    )
    SELECT
        (item->>'cleansed_id')::UUID,
        (item->>'institution_id')::UUID,
        item->>'url',
        item->>'official_name',
        item->>'duration_text',
        COALESCE(NULLIF(item->>'duration_months', '')::NUMERIC, 0)::INT,
        (item->>'total_cost_est')::NUMERIC,
        item->>'requirements',
        item->>'graduate_profile',
        (item->>'curriculum_summary')::JSONB,
        item->>'modality',
        item->>'primary_campus',
        item->>'degree_type',
        item->>'start_date',
        item->>'partnerships',
        item->>'certifications',
        item->>'language',
        item->>'categories',
        item->>'ai_summary',
        'pending'
    FROM jsonb_array_elements(p_enriched_data) AS item
    ON CONFLICT (cleansed_id) DO UPDATE SET
        official_name = EXCLUDED.official_name,
        duration_text = EXCLUDED.duration_text,
        duration_months = COALESCE(NULLIF(EXCLUDED.duration_months, NULL)::NUMERIC, 0)::INT,
        total_cost_est = EXCLUDED.total_cost_est,
        requirements = EXCLUDED.requirements,
        graduate_profile = EXCLUDED.graduate_profile,
        curriculum_summary = EXCLUDED.curriculum_summary,
        modality = EXCLUDED.modality,
        primary_campus = EXCLUDED.primary_campus,
        degree_type = EXCLUDED.degree_type,
        start_date = EXCLUDED.start_date,
        categories = EXCLUDED.categories,
        difficulty_level = EXCLUDED.difficulty_level,
        ai_summary = EXCLUDED.ai_summary,
        status = 'pending';

    UPDATE cleansed_programs
    SET status = 'synced'
    WHERE id = p_cleansed_id AND status = 'processing';

    RETURN QUERY
    SELECT * FROM enriched_programs WHERE cleansed_id = p_cleansed_id;
END;
$function$;

-- =============================================================================
-- 7. FUNCIONES — Triggers
-- =============================================================================

-- 7a. fn_auto_assign_category (assigns category_id + category text)
DROP TRIGGER IF EXISTS tr_auto_assign_category ON public.courses;
CREATE OR REPLACE FUNCTION public.fn_auto_assign_category()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path = public
AS $function$
DECLARE
    target_category_id UUID;
    target_category_name TEXT;
BEGIN
    SELECT r.category_id, cat.name 
    INTO target_category_id, target_category_name
    FROM public.category_rules r
    JOIN public.categories cat ON cat.id = r.category_id
    WHERE NEW.name ~* ('\\y' || r.keyword || '\\y')
    ORDER BY r.priority DESC
    LIMIT 1;

    IF target_category_id IS NOT NULL THEN
        NEW.category_id := target_category_id;
        NEW.category := target_category_name;
        NEW.category_confirmed := true;
    ELSE
        SELECT id, name INTO target_category_id, target_category_name
        FROM public.categories WHERE name = 'General / Por Clasificar' LIMIT 1;
        NEW.category_id := target_category_id;
        NEW.category := target_category_name;
        NEW.category_confirmed := false;
    END IF;

    RETURN NEW;
END;
$function$;

CREATE TRIGGER tr_auto_assign_category
BEFORE INSERT OR UPDATE OF name, description_long ON courses
FOR EACH ROW EXECUTE FUNCTION fn_auto_assign_category();

-- 7b. update_updated_at_column
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path = public
AS $function$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$function$;

-- =============================================================================
-- 8. TRIGGERS
-- =============================================================================

-- tr_enriched_programs_updated_at (referenced by maintenance scripts)
DROP TRIGGER IF EXISTS tr_enriched_programs_updated_at ON enriched_programs;
CREATE TRIGGER tr_enriched_programs_updated_at
BEFORE UPDATE ON enriched_programs
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 9. SEED DATA — Categorias
-- =============================================================================
INSERT INTO public.categories (name, description) VALUES
('General / Por Clasificar', ''),
('Ofimatica y Productividad', ''),
('Data Analytics', ''),
('Ciberseguridad', ''),
('Cloud Computing', ''),
('Data Science & IA', ''),
('DevOps & Infraestructura', ''),
('Gestion y Agilidad', ''),
('Redes y Conectividad', ''),
('Desarrollo y Web', ''),
('Tecnologia', ''),
('Logistica y Operaciones', ''),
('Finanzas y Legal', 'Cursos relacionados a finanzas, contabilidad, leyes y normativas legales.'),
('Ingenieria y Construccion', 'Cursos de ingenieria civil, industrial, minas, construccion y afines.'),
('Arte y Diseno Digital', 'Cursos de diseno grafico, UI/UX, animacion, arte y medios digitales.'),
('Derecho y Humanidades', 'Cursos de derecho, filosofia, ciencias sociales y humanidades.'),
('Marketing y Ventas', 'Cursos de marketing digital, publicidad, estrategias de ventas y relaciones publicas.')
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- 10. SEED DATA — category_rules (keyword mappings)
-- =============================================================================
WITH cat AS (SELECT id, name FROM categories)
INSERT INTO public.category_rules (category_id, keyword, priority)
SELECT c.id, k.keyword, k.priority
FROM (VALUES 
    ('General / Por Clasificar', 'general', 0),

    ('Ofimatica y Productividad', 'office', 10),
    ('Ofimatica y Productividad', 'excel', 10),
    ('Ofimatica y Productividad', 'word', 10),
    ('Ofimatica y Productividad', 'powerpoint', 10),
    ('Ofimatica y Productividad', 'outlook', 10),
    ('Ofimatica y Productividad', 'visio', 10),
    ('Ofimatica y Productividad', 'project', 5),

    ('Data Analytics', 'power bi', 20),
    ('Data Analytics', 'tableau', 20),
    ('Data Analytics', 'qlik', 20),
    ('Data Analytics', 'analytics', 10),
    ('Data Analytics', 'analitica', 10),
    ('Data Analytics', 'sql server', 30),
    ('Data Analytics', 'big data', 25),

    ('Ciberseguridad', 'seguridad', 10),
    ('Ciberseguridad', 'hacking', 20),
    ('Ciberseguridad', 'cyber', 10),
    ('Ciberseguridad', 'ciber', 10),
    ('Ciberseguridad', 'owasp', 30),
    ('Ciberseguridad', 'fortinet', 20),
    ('Ciberseguridad', 'palo alto', 20),
    ('Ciberseguridad', 'firewall', 15),

    ('Cloud Computing', 'cloud', 10),
    ('Cloud Computing', 'azure', 20),
    ('Cloud Computing', 'aws', 20),
    ('Cloud Computing', 'google cloud', 20),
    ('Cloud Computing', 'gcp', 20),

    ('Data Science & IA', 'data', 5),
    ('Data Science & IA', 'datos', 5),
    ('Data Science & IA', 'ia', 15),
    ('Data Science & IA', 'artificial', 15),
    ('Data Science & IA', 'machine learning', 30),
    ('Data Science & IA', 'deep learning', 30),

    ('DevOps & Infraestructura', 'devops', 20),
    ('DevOps & Infraestructura', 'docker', 25),
    ('DevOps & Infraestructura', 'kubernetes', 30),
    ('DevOps & Infraestructura', 'jenkins', 20),
    ('DevOps & Infraestructura', 'terraform', 25),
    ('DevOps & Infraestructura', 'ansible', 20),

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

    ('Redes y Conectividad', 'cisco', 20),
    ('Redes y Conectividad', 'redes', 10),
    ('Redes y Conectividad', 'network', 10),
    ('Redes y Conectividad', 'ccna', 30),
    ('Redes y Conectividad', 'ccnp', 30),
    ('Redes y Conectividad', 'routing', 20),
    ('Redes y Conectividad', 'switching', 20),

    ('Desarrollo y Web', 'java', 20),
    ('Desarrollo y Web', 'python', 10),
    ('Desarrollo y Web', 'php', 20),
    ('Desarrollo y Web', 'javascript', 20),
    ('Desarrollo y Web', 'react', 25),
    ('Desarrollo y Web', 'desarrollo', 5),
    ('Desarrollo y Web', 'programacion', 5),
    ('Desarrollo y Web', 'web', 5),
    ('Desarrollo y Web', 'frontend', 15),
    ('Desarrollo y Web', 'backend', 15),
    ('Desarrollo y Web', 'fullstack', 20),
    ('Desarrollo y Web', 'angular', 25),
    ('Desarrollo y Web', 'vue', 25),
    ('Desarrollo y Web', 'node', 20),
    ('Desarrollo y Web', 'rpa', 30),
    ('Desarrollo y Web', 'uipath', 35),
    ('Desarrollo y Web', 'automatizacion', 20),

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
    ('Derecho y Humanidades', 'psicologia', 20),
    ('Derecho y Humanidades', 'sociologia', 20),
    ('Derecho y Humanidades', 'filosofia', 20),

    ('Marketing y Ventas', 'marketing', 20),
    ('Marketing y Ventas', 'ventas', 20),
    ('Marketing y Ventas', 'seo', 30),
    ('Marketing y Ventas', 'sem', 30),
    ('Marketing y Ventas', 'redes sociales', 25),
    ('Marketing y Ventas', 'comercio electronico', 25),
    ('Marketing y Ventas', 'e-commerce', 25)
) AS k(cat_name, keyword, priority)
JOIN cat c ON c.name = k.cat_name
ON CONFLICT (keyword) DO NOTHING;

-- =============================================================================
-- 11. SEED DATA — Salarios de Mercado
-- =============================================================================
INSERT INTO public.market_salaries (category_id, category_name, salary_junior, salary_average, salary_senior)
SELECT c.id, s.cat_name, s.sj, s.sa, s.ss FROM (VALUES 
('Data Science & IA', 5200, 11500, 18000),
('Ciberseguridad', 4800, 9500, 16000),
('Cloud Computing', 4500, 10000, 17000),
('DevOps & Infraestructura', 4500, 9800, 16500),
('Desarrollo y Web', 3500, 7500, 14000),
('Data Analytics', 3800, 8200, 13000),
('Logistica y Operaciones', 2800, 5800, 11000),
('Finanzas y Legal', 3200, 7200, 15000),
('Ingenieria y Construccion', 3000, 6500, 14000),
('Marketing y Ventas', 2500, 5500, 10000),
('Gestion y Agilidad', 3500, 8500, 15000),
('Redes y Conectividad', 2800, 6000, 11000),
('Ofimatica y Productividad', 1200, 2800, 4500),
('Arte y Diseno Digital', 2200, 4800, 9000),
('Derecho y Humanidades', 2500, 5500, 12000),
('Tecnologia', 3000, 7000, 13000),
('General / Por Clasificar', 1025, 2500, 5000)
) as s(cat_name, sj, sa, ss) JOIN public.categories c ON c.name = s.cat_name ON CONFLICT (category_name) DO NOTHING;

-- =============================================================================
-- 12. RLS — Tablas publicas (anon = SELECT, service_role = ALL)
-- =============================================================================
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.category_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.market_salaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;

-- courses
DROP POLICY IF EXISTS "courses_select_public" ON public.courses;
CREATE POLICY "courses_select_public" ON public.courses FOR SELECT TO anon USING (true);
DROP POLICY IF EXISTS "courses_select_authenticated" ON public.courses;
CREATE POLICY "courses_select_authenticated" ON public.courses FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "courses_service_role" ON public.courses;
CREATE POLICY "courses_service_role" ON public.courses FOR ALL TO service_role USING (true) WITH CHECK (true);

-- institutions
DROP POLICY IF EXISTS "institutions_select_public" ON public.institutions;
CREATE POLICY "institutions_select_public" ON public.institutions FOR SELECT TO anon USING (true);
DROP POLICY IF EXISTS "institutions_select_authenticated" ON public.institutions;
CREATE POLICY "institutions_select_authenticated" ON public.institutions FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "institutions_service_role" ON public.institutions;
CREATE POLICY "institutions_service_role" ON public.institutions FOR ALL TO service_role USING (true) WITH CHECK (true);

-- categories
DROP POLICY IF EXISTS "categories_select_public" ON public.categories;
CREATE POLICY "categories_select_public" ON public.categories FOR SELECT TO anon USING (true);
DROP POLICY IF EXISTS "categories_select_authenticated" ON public.categories;
CREATE POLICY "categories_select_authenticated" ON public.categories FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "categories_service_role" ON public.categories;
CREATE POLICY "categories_service_role" ON public.categories FOR ALL TO service_role USING (true) WITH CHECK (true);

-- category_rules
DROP POLICY IF EXISTS "category_rules_select_public" ON public.category_rules;
CREATE POLICY "category_rules_select_public" ON public.category_rules FOR SELECT TO anon USING (true);
DROP POLICY IF EXISTS "category_rules_select_authenticated" ON public.category_rules;
CREATE POLICY "category_rules_select_authenticated" ON public.category_rules FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "category_rules_service_role" ON public.category_rules;
CREATE POLICY "category_rules_service_role" ON public.category_rules FOR ALL TO service_role USING (true) WITH CHECK (true);

-- market_salaries
DROP POLICY IF EXISTS "market_salaries_select_public" ON public.market_salaries;
CREATE POLICY "market_salaries_select_public" ON public.market_salaries FOR SELECT TO anon USING (true);
DROP POLICY IF EXISTS "market_salaries_select_authenticated" ON public.market_salaries;
CREATE POLICY "market_salaries_select_authenticated" ON public.market_salaries FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "market_salaries_service_role" ON public.market_salaries;
CREATE POLICY "market_salaries_service_role" ON public.market_salaries FOR ALL TO service_role USING (true) WITH CHECK (true);

-- leads (anon: INSERT only, authenticated: INSERT, service_role: ALL)
DROP POLICY IF EXISTS "leads_insert_public" ON public.leads;
CREATE POLICY "leads_insert_public" ON public.leads FOR INSERT TO anon WITH CHECK (true);
DROP POLICY IF EXISTS "leads_insert_authenticated" ON public.leads;
CREATE POLICY "leads_insert_authenticated" ON public.leads FOR INSERT TO authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "leads_service_role" ON public.leads;
CREATE POLICY "leads_service_role" ON public.leads FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ratings (authenticated: SELECT+INSERT, service_role: ALL, anon blocked by default)
DROP POLICY IF EXISTS "ratings_select_authenticated" ON public.ratings;
CREATE POLICY "ratings_select_authenticated" ON public.ratings FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "ratings_insert_authenticated" ON public.ratings;
CREATE POLICY "ratings_insert_authenticated" ON public.ratings FOR INSERT TO authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "ratings_service_role" ON public.ratings;
CREATE POLICY "ratings_service_role" ON public.ratings FOR ALL TO service_role USING (true) WITH CHECK (true);

-- reviews (authenticated: SELECT+INSERT, service_role: ALL, anon blocked by default)
DROP POLICY IF EXISTS "reviews_select_authenticated" ON public.reviews;
CREATE POLICY "reviews_select_authenticated" ON public.reviews FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "reviews_insert_authenticated" ON public.reviews;
CREATE POLICY "reviews_insert_authenticated" ON public.reviews FOR INSERT TO authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "reviews_service_role" ON public.reviews;
CREATE POLICY "reviews_service_role" ON public.reviews FOR ALL TO service_role USING (true) WITH CHECK (true);

-- =============================================================================
-- 13. RLS — Tablas ETL (anon blocked, service_role ALL)
-- =============================================================================
ALTER TABLE crawler_exclusions ENABLE ROW LEVEL SECURITY;
ALTER TABLE staging_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleansed_programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE enriched_programs ENABLE ROW LEVEL SECURITY;

-- crawler_exclusions (anon can see active entries)
DROP POLICY IF EXISTS "crawler_exclusions_select_public" ON crawler_exclusions;
CREATE POLICY "crawler_exclusions_select_public"
ON crawler_exclusions FOR SELECT TO anon, authenticated
USING (is_active = true);
DROP POLICY IF EXISTS "crawler_exclusions_service_role" ON crawler_exclusions;
CREATE POLICY "crawler_exclusions_service_role"
ON crawler_exclusions FOR ALL TO service_role
USING (true) WITH CHECK (true);

-- staging_raw (anon completely blocked)
DROP POLICY IF EXISTS "staging_raw_no_public_access" ON staging_raw;
CREATE POLICY "staging_raw_no_public_access" ON staging_raw FOR ALL TO anon USING (false);
DROP POLICY IF EXISTS "staging_raw_service_role" ON staging_raw;
CREATE POLICY "staging_raw_service_role" ON staging_raw FOR ALL TO service_role USING (true) WITH CHECK (true);

-- cleansed_programs (anon completely blocked)
DROP POLICY IF EXISTS "cleansed_programs_no_public_access" ON cleansed_programs;
CREATE POLICY "cleansed_programs_no_public_access" ON cleansed_programs FOR ALL TO anon USING (false);
DROP POLICY IF EXISTS "cleansed_programs_service_role" ON cleansed_programs;
CREATE POLICY "cleansed_programs_service_role" ON cleansed_programs FOR ALL TO service_role USING (true) WITH CHECK (true);

-- enriched_programs (anon completely blocked)
DROP POLICY IF EXISTS "enriched_programs_no_public_access" ON enriched_programs;
CREATE POLICY "enriched_programs_no_public_access" ON enriched_programs FOR ALL TO anon USING (false);
DROP POLICY IF EXISTS "enriched_programs_service_role" ON enriched_programs;
CREATE POLICY "enriched_programs_service_role" ON enriched_programs FOR ALL TO service_role USING (true) WITH CHECK (true);

-- =============================================================================
-- 14. REVOKE EXECUTE on RPCs — solo service_role puede ejecutar
-- =============================================================================
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- =============================================================================
-- 15. MOVER EXTENSIONES a schema extensions
-- =============================================================================
ALTER EXTENSION pg_trgm SET SCHEMA extensions;
ALTER EXTENSION vector SET SCHEMA extensions;

-- =============================================================================
-- VERIFICACION (descomentar para debug)
-- =============================================================================
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
-- SELECT COUNT(*) as categories FROM categories;
-- SELECT COUNT(*) as category_rules FROM category_rules;
-- SELECT COUNT(*) as market_salaries FROM market_salaries;