-- H2: tighten effective grants after editorial layer creation.
-- Scope: Free/Development DDL only under DDL-H2-EDITORIAL-LAYER-FREE.
-- This migration fixes effective service_role grants; it performs no DML/backfill.

REVOKE ALL ON TABLE public.editorial_field_definitions FROM service_role;
REVOKE ALL ON TABLE public.course_editorial_state FROM service_role;
REVOKE ALL ON TABLE public.course_editorial_audit FROM service_role;
REVOKE ALL ON TABLE public.courses_public_effective FROM service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.editorial_field_definitions TO service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE public.course_editorial_state TO service_role;
GRANT SELECT, INSERT ON TABLE public.course_editorial_audit TO service_role;
GRANT SELECT ON TABLE public.courses_public_effective TO service_role;

REVOKE TRUNCATE, REFERENCES, TRIGGER ON TABLE public.editorial_field_definitions FROM service_role;
REVOKE DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLE public.course_editorial_state FROM service_role;
REVOKE UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLE public.course_editorial_audit FROM service_role;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLE public.courses_public_effective FROM service_role;
