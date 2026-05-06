-- Fase 82A: Schema Enhancement — View Counter + Comparison Count
-- Apply on Free (desarrollo) → Certificacion → Pro (produccion)

ALTER TABLE courses ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS comparison_count INTEGER DEFAULT 0;

CREATE OR REPLACE FUNCTION increment_view_count(p_course_id UUID)
RETURNS void
LANGUAGE plpgsql
SET search_path = public
SECURITY DEFINER
AS $$
BEGIN
  UPDATE courses SET view_count = view_count + 1 WHERE id = p_course_id;
END;
$$;

-- Frontend necesita anon key para incrementar contador desde el cliente
REVOKE EXECUTE ON FUNCTION increment_view_count(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION increment_view_count(UUID) TO anon, authenticated, service_role;
