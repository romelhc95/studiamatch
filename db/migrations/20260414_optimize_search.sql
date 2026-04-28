-- MIGRACIÓN: Optimización de Búsqueda
-- FECHA: 2026-04-14
-- DESCRIPCIÓN: Habilita pg_trgm y crea un índice GIN en courses.name para búsqueda difusa (fuzzy search).

-- 1. Habilitar la extensión pg_trgm en Supabase (si no está ya habilitada)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Crear un índice GIN en la columna 'name' de la tabla 'courses'
-- El uso de 'gin_trgm_ops' es fundamental para que el índice funcione con operadores de similitud (LIKE, ILIKE, %, etc.)
CREATE INDEX IF NOT EXISTS idx_courses_name_trgm ON courses USING gin (name gin_trgm_ops);

-- Nota: Para aprovechar este índice en consultas, se puede usar:
-- SELECT * FROM courses WHERE name % 'término_búsqueda' ORDER BY similarity(name, 'término_búsqueda') DESC;
