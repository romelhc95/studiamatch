-- The server-side admin-invite function resolves an existing membership with
-- its service_role client. Keep this explicit so the contract does not depend
-- on project-wide default privileges. No client role receives direct access.
GRANT SELECT ON TABLE public.admin_members TO service_role;
