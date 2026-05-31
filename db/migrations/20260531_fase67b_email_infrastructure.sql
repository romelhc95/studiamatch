-- Fase 67B: Email infrastructure — email_log, contact_email, trigger, pg_net
-- Enables email notifications when a lead is created.

-- 1. Enable pg_net extension for async HTTP requests
CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;

-- 2. Add contact_email to institutions
ALTER TABLE public.institutions ADD COLUMN IF NOT EXISTS contact_email TEXT;

-- 3. Create email_log table
CREATE TABLE IF NOT EXISTS public.email_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    lead_id UUID REFERENCES public.leads(id),
    recipient_type TEXT NOT NULL CHECK (recipient_type IN ('user', 'admin', 'institution')),
    recipient_email TEXT NOT NULL,
    subject TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
    resend_id TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.email_log ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'email_log_service_role') THEN
        CREATE POLICY email_log_service_role ON public.email_log
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'email_log_select_authenticated') THEN
        CREATE POLICY email_log_select_authenticated ON public.email_log
            FOR SELECT TO authenticated USING (true);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_email_log_lead_id ON public.email_log(lead_id);
CREATE INDEX IF NOT EXISTS idx_email_log_status ON public.email_log(status);

-- 4. Create notify_new_lead() trigger function
CREATE OR REPLACE FUNCTION public.notify_new_lead()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
    edge_function_url TEXT;
    anon_key TEXT;
BEGIN
    SELECT current_setting('app.settings.edge_function_url', true) INTO edge_function_url;
    IF edge_function_url IS NULL THEN
        edge_function_url := current_setting('app.settings.supabase_url', true) || '/functions/v1/send-lead-emails';
    END IF;

    BEGIN
        PERFORM net.http_post(
            url := edge_function_url,
            body := jsonb_build_object('lead_id', NEW.id, 'record', to_jsonb(NEW)),
            headers := jsonb_build_object(
                'Content-Type', 'application/json',
                'Authorization', current_setting('app.settings.anon_key', true)
            ),
            timeout_milliseconds := 5000
        );
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO public.email_log (lead_id, recipient_type, recipient_email, status, error_message)
        VALUES (NEW.id, 'admin', 'system', 'failed', SQLERRM);
    END;

    RETURN NEW;
END;
$$;

-- 5. Create trigger
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_notify_new_lead') THEN
        CREATE TRIGGER trg_notify_new_lead
        AFTER INSERT ON public.leads
        FOR EACH ROW
        EXECUTE FUNCTION public.notify_new_lead();
    END IF;
END $$;
