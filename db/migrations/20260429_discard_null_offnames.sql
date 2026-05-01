-- ============================================================
-- FASE 59 P1-5: Descarte de enriched_programs sin official_name
-- 
-- Contexto: 24 registros en enriched_programs tienen official_name=NULL.
-- Sus cleansed_programs correspondientes tampoco tienen clean_name
-- (son ruido: charlas, eventos, agendas de U. Lima).
-- sync_vector_worker.py ya los skippea (validación Fase 57).
-- 
-- Acción: Marcar como 'discarded' para limpiar el pipeline.
-- 
-- ⚠️ EJECUTAR MANUALMENTE en Supabase Dashboard > SQL Editor
-- ============================================================

UPDATE enriched_programs
SET status = 'discarded',
    metadata = jsonb_set(
        COALESCE(metadata, '{}'::jsonb),
        '{discard_reason}',
        '"official_name_null_no_clean_name_fallback"'
    )
WHERE official_name IS NULL
  AND status = 'synced';
