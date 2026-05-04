-- Fase 73: Filtrado por Fecha Expirada
-- Agrega columna start_date DATE a courses para filtrado de programas expirados (>90d).
-- También agrega start_date a enriched_programs como columna estructurada.

-- 1. Agregar start_date DATE a courses (paralelo a start_date_text TEXT)
ALTER TABLE courses
ADD COLUMN IF NOT EXISTS start_date DATE;

COMMENT ON COLUMN courses.start_date IS 'Fecha de inicio parseada (DATE). Usado para filtrado de expiración con 90d de gracia.';

-- 2. Agregar start_date DATE a enriched_programs (columna estructurada junto a start_date TEXT)
ALTER TABLE enriched_programs
ADD COLUMN IF NOT EXISTS start_date DATE;

COMMENT ON COLUMN enriched_programs.start_date IS 'Fecha de inicio parseada desde start_date TEXT. Poblado por enrichment_worker.';

-- 3. Índice para búsquedas por fecha de inicio
CREATE INDEX IF NOT EXISTS idx_courses_start_date ON courses(start_date) WHERE start_date IS NOT NULL;

-- 4. Marcar cursos activos con fecha expirada (>90d) como inactivos
-- NOTA: Ejecutar solo después de que sync_vector_worker haya poblado start_date.
-- UPDATE courses SET is_active = false
-- WHERE start_date IS NOT NULL AND start_date < CURRENT_DATE - INTERVAL '90 days' AND is_active = true;
