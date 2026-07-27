\set ON_ERROR_STOP on

-- TEST-ONLY F9.7 access drift. It contains schema and ACLs, never rows.
CREATE TABLE public.institutions (
    id uuid PRIMARY KEY,
    name text NOT NULL,
    slug text NOT NULL UNIQUE
);

CREATE TABLE public.categories (
    id uuid PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE public.category_rules (
    id uuid PRIMARY KEY,
    category_id uuid,
    keyword text NOT NULL
);

CREATE TABLE public.market_salaries (
    id uuid PRIMARY KEY,
    category_id uuid,
    monthly_salary numeric
);

ALTER TABLE public.leads
    ALTER COLUMN id SET DEFAULT pg_catalog.gen_random_uuid(),
    ADD COLUMN last_name text,
    ADD COLUMN source_page text,
    ADD COLUMN type text,
    ADD COLUMN area_interest text,
    ADD COLUMN budget numeric,
    ADD COLUMN modality text,
    ADD COLUMN description text,
    ADD COLUMN is_late_enrollment_request boolean NOT NULL DEFAULT false,
    ADD COLUMN status text NOT NULL DEFAULT 'pending';

CREATE TABLE public.email_log (
    id uuid PRIMARY KEY DEFAULT pg_catalog.gen_random_uuid(),
    lead_id uuid REFERENCES public.leads(id),
    recipient_type text NOT NULL,
    recipient_email text NOT NULL,
    subject text,
    status text NOT NULL DEFAULT 'pending',
    resend_id text,
    error_message text,
    created_at timestamptz NOT NULL DEFAULT pg_catalog.now()
);

ALTER TABLE public.email_log ENABLE ROW LEVEL SECURITY;
GRANT ALL PRIVILEGES ON TABLE public.email_log TO service_role;
GRANT SELECT ON TABLE public.email_log TO authenticated;
GRANT SELECT (recipient_email) ON TABLE public.email_log TO anon;

CREATE POLICY email_log_service_role
ON public.email_log
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY email_log_select_authenticated
ON public.email_log
FOR SELECT
TO authenticated
USING (true);
