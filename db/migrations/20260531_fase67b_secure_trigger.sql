-- Fase 67B v2: Secure trigger — zero hardcoded credentials
-- Trigger queries course + institution data via SECURITY DEFINER,
-- passes complete payload to Edge Function. No DB queries inside Edge Function.

CREATE OR REPLACE FUNCTION public.notify_new_lead()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE
    course_data jsonb;
    inst_data jsonb;
BEGIN
    SELECT jsonb_build_object(
        'id', c.id, 'name', c.name, 'slug', c.slug,
        'price_pen', c.price_pen, 'mode', c.mode, 'duration', c.duration
    ) INTO course_data
    FROM public.courses c WHERE c.id = NEW.course_id;

    SELECT jsonb_build_object(
        'name', i.name, 'slug', i.slug, 'contact_email', i.contact_email
    ) INTO inst_data
    FROM public.institutions i
    WHERE i.id = (SELECT institution_id FROM public.courses WHERE id = NEW.course_id);

    BEGIN
        PERFORM net.http_post(
            url := 'https://xwhtiqmboljkshrtviyw.supabase.co/functions/v1/send-lead-emails',
            body := jsonb_build_object(
                'record', to_jsonb(NEW),
                'course', COALESCE(course_data, '{}'::jsonb),
                'institution', COALESCE(inst_data, '{}'::jsonb)
            ),
            headers := jsonb_build_object('Content-Type', 'application/json'),
            timeout_milliseconds := 5000
        );
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO public.email_log (lead_id, recipient_type, recipient_email, status, error_message)
        VALUES (NEW.id, 'admin', 'system', 'failed', SQLERRM);
    END;
    RETURN NEW;
END;
$$;
