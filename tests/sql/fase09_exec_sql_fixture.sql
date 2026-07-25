\set ON_ERROR_STOP on

-- TEST-ONLY fixture. It exists solely in the ephemeral studiamatch_f9 DB.
CREATE TABLE public.supabase_migrations (
    version bigint NOT NULL,
    name text PRIMARY KEY,
    statements text NOT NULL DEFAULT '',
    applied_at timestamptz NOT NULL DEFAULT pg_catalog.now()
);

REVOKE ALL PRIVILEGES ON TABLE public.supabase_migrations
FROM PUBLIC, anon, authenticated;
GRANT ALL PRIVILEGES ON TABLE public.supabase_migrations TO service_role;

CREATE FUNCTION public.exec_sql(sql_text text)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
BEGIN
    EXECUTE sql_text;
    RETURN pg_catalog.jsonb_build_object('status', 'success');
END;
$function$;

ALTER FUNCTION public.exec_sql(text) OWNER TO postgres;
REVOKE ALL ON FUNCTION public.exec_sql(text)
FROM PUBLIC, anon, authenticated, service_role CASCADE;
GRANT EXECUTE ON FUNCTION public.exec_sql(text) TO service_role;
