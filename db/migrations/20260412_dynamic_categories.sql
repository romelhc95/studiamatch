-- ==========================================
-- MIGRACIÓN: Catálogo Dinámico de Categorías
-- Fecha: 2026-04-12
-- Descripción: Creación de tablas categories, category_rules y trigger de auto-asignación con Diseño Híbrido.
-- Diseño Híbrido: Clasificación automática por reglas + Categoría General (Fallback) + Flag de Confirmación.
-- ==========================================

-- 1. LIMPIEZA PREVIA (Pre-cleanup)
DROP TRIGGER IF EXISTS tr_auto_assign_category ON courses;
DROP FUNCTION IF EXISTS fn_auto_assign_category();

-- Eliminar tablas si existen (Cuidado en producción)
DROP TABLE IF EXISTS category_rules CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

-- 2. CREACIÓN DE TABLAS
-- Tabla de Categorías Principales
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Tabla de Reglas de Asignación Semántica
CREATE TABLE category_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    keyword TEXT UNIQUE NOT NULL,
    priority INTEGER DEFAULT 0, -- Mayor prioridad gana en caso de múltiples coincidencias
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. ACTUALIZACIÓN DE TABLA COURSES
-- Añadir category_id y category_confirmed a la tabla courses
DO $$
BEGIN
    -- Añadir columna de categoría si no existe
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='courses' AND column_name='category_id') THEN
        ALTER TABLE courses ADD COLUMN category_id UUID REFERENCES categories(id);
    END IF;
    
    -- Añadir flag de confirmación (Diseño Híbrido)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='courses' AND column_name='category_confirmed') THEN
        ALTER TABLE courses ADD COLUMN category_confirmed BOOLEAN DEFAULT false;
    END IF;
END $$;

-- 4. POBLACIÓN INICIAL (SEEDING)
-- Insertar Categorías Base (Incluyendo la categoría Default)
INSERT INTO categories (name) VALUES 
('General / Por Clasificar'),
('Ofimática y Productividad'),
('Data Analytics'),
('Ciberseguridad'),
('Cloud Computing'),
('Data Science & IA'),
('DevOps & Infraestructura'),
('Gestión y Agilidad'),
('Redes y Conectividad'),
('Desarrollo y Web'),
('Tecnología')
ON CONFLICT (name) DO NOTHING;

-- Insertar Reglas de Mapeo Semántico
WITH cat AS (SELECT id, name FROM categories)
INSERT INTO category_rules (category_id, keyword, priority)
SELECT c.id, k.keyword, k.priority
FROM (VALUES 
    ('Ofimática y Productividad', 'office', 10),
    ('Ofimática y Productividad', 'excel', 10),
    ('Ofimática y Productividad', 'word', 10),
    ('Ofimática y Productividad', 'powerpoint', 10),
    ('Ofimática y Productividad', 'outlook', 10),
    ('Ofimática y Productividad', 'visio', 10),
    ('Ofimática y Productividad', 'project', 5),
    ('Data Analytics', 'power bi', 20),
    ('Data Analytics', 'tableau', 20),
    ('Data Analytics', 'qlik', 20),
    ('Data Analytics', 'analytics', 10),
    ('Data Analytics', 'analítica', 10),
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
    ('Cloud Computing', 'amazon web services', 20),
    ('Data Science & IA', 'data', 5),
    ('Data Science & IA', 'datos', 5),
    ('Data Science & IA', 'ia', 15),
    ('Data Science & IA', 'artificial', 15),
    ('Data Science & IA', 'machine learning', 30),
    ('Data Science & IA', 'deep learning', 30),
    ('Data Science & IA', 'python for data', 25),
    ('DevOps & Infraestructura', 'devops', 20),
    ('DevOps & Infraestructura', 'docker', 25),
    ('DevOps & Infraestructura', 'kubernetes', 30),
    ('DevOps & Infraestructura', 'jenkins', 20),
    ('DevOps & Infraestructura', 'terraform', 25),
    ('DevOps & Infraestructura', 'ansible', 20),
    ('Gestión y Agilidad', 'agil', 10),
    ('Gestión y Agilidad', 'scrum', 20),
    ('Gestión y Agilidad', 'itil', 20),
    ('Gestión y Agilidad', 'pmp', 20),
    ('Gestión y Agilidad', 'gestión', 5),
    ('Gestión y Agilidad', 'gestion', 5),
    ('Gestión y Agilidad', 'management', 10),
    ('Gestión y Agilidad', 'liderazgo', 10),
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
    ('Desarrollo y Web', 'programación', 5),
    ('Desarrollo y Web', 'web', 5),
    ('Desarrollo y Web', 'frontend', 15),
    ('Desarrollo y Web', 'backend', 15),
    ('Desarrollo y Web', 'fullstack', 20),
    ('Desarrollo y Web', 'angular', 25),
    ('Desarrollo y Web', 'vue', 25),
    ('Desarrollo y Web', 'node', 20)
) as k(cat_name, keyword, priority)
JOIN cat c ON c.name = k.cat_name
ON CONFLICT (keyword) DO NOTHING;

-- 5. FUNCIÓN DE AUTO-ASIGNACIÓN (Lógica Híbrida)
-- Busca coincidencias y asigna 'General' como fallback obteniendo su ID dinámicamente.
CREATE OR REPLACE FUNCTION fn_auto_assign_category()
RETURNS TRIGGER AS $$
DECLARE
    found_category_id UUID;
    general_id UUID;
BEGIN
    -- 1. Intentar buscar el category_id con la mayor prioridad que coincida con el texto del curso
    SELECT category_id INTO found_category_id
    FROM category_rules
    WHERE 
        LOWER(NEW.name) ~* ('\y' || keyword || '\y') OR
        LOWER(COALESCE(NEW.description_long, '')) ~* ('\y' || keyword || '\y') OR
        LOWER(COALESCE(NEW.syllabus, '')) ~* ('\y' || keyword || '\y')
    ORDER BY priority DESC
    LIMIT 1;

    -- 2. Si se encontró una categoría por reglas, se asigna y se marca como confirmada
    IF found_category_id IS NOT NULL THEN
        NEW.category_id := found_category_id;
        NEW.category_confirmed := true; 
    ELSE
        -- 3. Si no hay coincidencia, obtener el ID de la categoría "General" dinámicamente
        SELECT id INTO general_id FROM categories WHERE name = 'General / Por Clasificar' LIMIT 1;
        NEW.category_id := general_id;
        NEW.category_confirmed := false; -- Requiere revisión manual (Triaje)
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6. CREACIÓN DEL TRIGGER
CREATE TRIGGER tr_auto_assign_category
BEFORE INSERT OR UPDATE OF name, description_long, syllabus ON courses
FOR EACH ROW
EXECUTE FUNCTION fn_auto_assign_category();

-- 7. BACKFILL (Retroalimentación de cursos existentes)
-- Aplicar la nueva lógica híbrida a todos los cursos sin categoría
UPDATE courses
SET 
    category_id = COALESCE(
        (SELECT category_id FROM category_rules 
         WHERE LOWER(courses.name) ~* ('\y' || keyword || '\y') 
         OR LOWER(COALESCE(courses.description_long, '')) ~* ('\y' || keyword || '\y')
         ORDER BY priority DESC LIMIT 1),
        (SELECT id FROM categories WHERE name = 'General / Por Clasificar' LIMIT 1)
    ),
    category_confirmed = (
        SELECT EXISTS (
            SELECT 1 FROM category_rules 
            WHERE LOWER(courses.name) ~* ('\y' || keyword || '\y') 
            OR LOWER(COALESCE(courses.description_long, '')) ~* ('\y' || keyword || '\y')
        )
    )
WHERE category_id IS NULL OR category_id = (SELECT id FROM categories WHERE name = 'General / Por Clasificar' LIMIT 1);

-- 8. POLÍTICAS DE SEGURIDAD (RLS)
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Categories are viewable by everyone" ON categories;
CREATE POLICY "Categories are viewable by everyone" ON categories FOR SELECT USING (true);

ALTER TABLE category_rules ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Category rules are viewable by everyone" ON category_rules;
CREATE POLICY "Category rules are viewable by everyone" ON category_rules FOR SELECT USING (true);
