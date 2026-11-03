-- StudIAMatch-Docs: .context/componentes/database_migrations.md#migration-20261102-h3-legacy-public-withdrawal
CREATE OR REPLACE VIEW public.courses_public_effective
WITH (security_invoker = true)
AS SELECT * FROM private.h2_public_courses_effective();
REVOKE ALL ON FUNCTION private.h2_public_courses_effective() FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.h2_public_courses_effective() TO anon, authenticated, service_role;
REVOKE ALL ON TABLE public.courses_public_effective FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT ON TABLE public.courses_public_effective TO anon, authenticated, service_role;
