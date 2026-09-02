-- H3: Admin course queue view for cursor pagination
-- Scope: Free/Development DDL only under DDL-H3-ADMIN-QUEUE-FREE
-- No backfill, Pro apply, writers, schedules, canaries, or deploys are authorized here.

-- Vista para la cola administrativa
CREATE OR REPLACE VIEW public.admin_course_queue
WITH (security_invoker = true)
AS
SELECT
  c.id AS course_id,
  c.name AS course_name,
  c.slug AS course_slug,
  i.name AS institution_name,
  i.slug AS institution_slug,
  c.url AS course_url,
  es.editorial_status,
  es.quality_status,
  es.missing_fields,
  es.is_sponsored,
  es.lead_cta_enabled,
  es.manual_overrides,
  es.field_sources,
  es.version,
  es.created_at,
  es.updated_at,
  es.manual_updated_at,
  es.published_at,
  es.archived_at,
  c.is_active,
  c.is_verified,
  c.provider_used
FROM public.courses c
JOIN public.institutions i ON c.institution_id = i.id
JOIN public.course_editorial_state es ON es.course_id = c.id
WHERE es.editorial_status <> 'archived';

COMMENT ON VIEW public.admin_course_queue IS 'H3: Admin course queue for editorial review. Excludes archived courses.';

-- Grants para service_role
REVOKE ALL ON TABLE public.admin_course_queue FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.admin_course_queue TO service_role;

-- Índices recomendados para paginación (ya existen en tablas base)
-- idx_course_editorial_state_status: (editorial_status, quality_status)
-- idx_course_editorial_audit_course_created: (course_id, created_at DESC)
