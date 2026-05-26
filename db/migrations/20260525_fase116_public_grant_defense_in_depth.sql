-- Fase 116: Defense-in-depth against accidental PUBLIC grants.
-- Keeps future institution profile configuration private by default.

REVOKE ALL ON public.institution_site_profiles FROM PUBLIC;
REVOKE ALL ON public.schema_repair_audit FROM PUBLIC;
