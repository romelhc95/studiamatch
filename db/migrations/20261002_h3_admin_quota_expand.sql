-- LOCAL approved additive EXPAND. Deploy this before the compatible Edge and
-- BEFORE 20261002_h3_admin_quotas.sql wraps legacy RPCs. Remote JIT required.
BEGIN;
CREATE TABLE IF NOT EXISTS private.h3_admin_quota_events (
  scope TEXT PRIMARY KEY,
  events TIMESTAMPTZ[] NOT NULL DEFAULT '{}',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
ALTER TABLE private.h3_admin_quota_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON private.h3_admin_quota_events FROM PUBLIC, anon, authenticated, service_role;
CREATE INDEX IF NOT EXISTS h3_admin_quota_expiry ON private.h3_admin_quota_events(updated_at);
CREATE OR REPLACE FUNCTION private.h3_take_admin_quota(p_scopes TEXT[], p_limits INTEGER[], p_seconds INTEGER[])
RETURNS INTEGER LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE i INTEGER; recent TIMESTAMPTZ[]; snapshot TIMESTAMPTZ := clock_timestamp(); retry INTEGER := 0;
BEGIN
  IF cardinality(p_scopes) IS NULL OR cardinality(p_scopes) < 1 OR cardinality(p_scopes) > 4
     OR cardinality(p_scopes) <> cardinality(p_limits) OR cardinality(p_scopes) <> cardinality(p_seconds) THEN
    RAISE EXCEPTION 'Invalid quota configuration';
  END IF;
  FOR i IN SELECT indexes FROM generate_subscripts(p_scopes,1) indexes ORDER BY p_scopes[indexes] LOOP
    IF p_scopes[i] IS NULL OR length(p_scopes[i]) > 160 OR p_limits[i] NOT BETWEEN 1 AND 300
       OR p_seconds[i] NOT BETWEEN 1 AND 86400 THEN RAISE EXCEPTION 'Invalid quota configuration'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended('h3-quota:' || p_scopes[i],0));
    INSERT INTO private.h3_admin_quota_events(scope) VALUES(p_scopes[i]) ON CONFLICT DO NOTHING;
    SELECT COALESCE(array_agg(event ORDER BY event),'{}'::timestamptz[]) INTO recent
    FROM private.h3_admin_quota_events q, unnest(q.events) event
    WHERE q.scope=p_scopes[i] AND event > snapshot-make_interval(secs=>p_seconds[i]);
    IF cardinality(recent) >= p_limits[i] THEN
      retry := greatest(retry,ceil(extract(epoch FROM recent[1]+make_interval(secs=>p_seconds[i])-snapshot))::integer);
    END IF;
  END LOOP;
  IF retry > 0 THEN RETURN greatest(1,retry); END IF;
  FOR i IN 1..cardinality(p_scopes) LOOP
    UPDATE private.h3_admin_quota_events q
    SET events=ARRAY(SELECT event FROM unnest(q.events) event
                    WHERE event > snapshot-make_interval(secs=>p_seconds[i]) ORDER BY event) || snapshot,
        updated_at=snapshot WHERE q.scope=p_scopes[i];
  END LOOP;
  DELETE FROM private.h3_admin_quota_events WHERE updated_at < snapshot-interval '24 hours';
  RETURN 0;
END;
$$;
REVOKE ALL ON FUNCTION private.h3_take_admin_quota(TEXT[],INTEGER[],INTEGER[]) FROM PUBLIC,anon,authenticated,service_role;
CREATE OR REPLACE FUNCTION private.h3_raise_admin_quota(p_retry INTEGER)
RETURNS VOID LANGUAGE plpgsql SET search_path=pg_catalog,pg_temp AS $$
BEGIN
  RAISE SQLSTATE 'PGRST' USING
    MESSAGE=json_build_object('code','quota_rate_limited','message','Administrative quota exceeded','details',p_retry::text,'hint',NULL)::text,
    DETAIL=json_build_object('status',429,'headers',json_build_object('Retry-After',p_retry::text))::text;
END;
$$;
REVOKE ALL ON FUNCTION private.h3_raise_admin_quota(INTEGER) FROM PUBLIC,anon,authenticated,service_role;
CREATE OR REPLACE FUNCTION public.admin_invitation_request_admit(p_actor_user_id UUID)
RETURNS BOOLEAN LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE retry INTEGER;
BEGIN
  IF NOT EXISTS(SELECT 1 FROM public.admin_members WHERE user_id=p_actor_user_id
                AND role='admin' AND is_active AND account_status='ready') THEN RETURN false; END IF;
  retry := private.h3_take_admin_quota(ARRAY['edge-request:'||p_actor_user_id::text],ARRAY[120],ARRAY[60]);
  IF retry>0 THEN PERFORM private.h3_raise_admin_quota(retry); END IF;
  RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION public.admin_invitation_request_admit(UUID) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.admin_invitation_request_admit(UUID) TO service_role;
COMMIT;
