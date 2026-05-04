-- Fase 75: Re-queue records skipped by pipeline_ready gate
-- Permite resetear registros marcados como 'skipped' cuando una institucion
-- se habilita con pipeline_ready=true
--
-- USO:
--   1. Setear pipeline_ready=true para la institucion
--   2. Ejecutar: SELECT requeue_pipeline_records('institution-uuid-here');
--   3. Los registros volveran a estado 'pending' para ser procesados

CREATE OR REPLACE FUNCTION requeue_pipeline_records(p_inst_id uuid)
RETURNS TABLE(tbl text, count int) AS $$
BEGIN
    -- staging_raw: skipped → pending
    UPDATE staging_raw SET status = 'pending', error_message = NULL
    WHERE institution_id = p_inst_id AND status = 'skipped'
      AND error_message = 'pipeline_ready=false';
    GET DIAGNOSTICS count = ROW_COUNT;
    tbl := 'staging_raw'; RETURN NEXT; count := 0;

    -- cleansed_programs: skipped → pending
    UPDATE cleansed_programs SET status = 'pending', error_message = NULL
    WHERE institution_id = p_inst_id AND status = 'skipped'
      AND error_message = 'pipeline_ready=false';
    GET DIAGNOSTICS count = ROW_COUNT;
    tbl := 'cleansed_programs'; RETURN NEXT; count := 0;

    -- enriched_programs: skipped → pending
    UPDATE enriched_programs SET status = 'pending', error_message = NULL
    WHERE institution_id = p_inst_id AND status = 'skipped'
      AND error_message = 'pipeline_ready=false';
    GET DIAGNOSTICS count = ROW_COUNT;
    tbl := 'enriched_programs'; RETURN NEXT;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION requeue_pipeline_records IS 'Fase 75: Re-queue registros skipped por pipeline_ready=false cuando se habilita una institucion.';
