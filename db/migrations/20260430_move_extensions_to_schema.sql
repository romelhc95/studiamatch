-- Migration: Move pg_trgm and vector to extensions schema
-- Date: 2026-04-30
-- Description: Mueve extensiones pg_trgm y vector de schema public a extensions.
--   El search_path por defecto de Supabase ya incluye extensions, 
--   por lo que no se requiere configuracion adicional.
--   Testeado: busqueda trigram (ilike) y embeddings funcionan correctamente.
ALTER EXTENSION pg_trgm SET SCHEMA extensions;
ALTER EXTENSION vector SET SCHEMA extensions;
