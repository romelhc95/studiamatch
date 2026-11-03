-- H3REQ1 signed Admin RPC gateway — additive EXPAND only.
-- This file intentionally does NOT configure pgrst.db_pre_request or provision
-- keys. Activate only after signed BFF consumers are deployed and a separate
-- JIT approves the exact PostgREST setting and environment-specific secret.
-- Local execution also requires a separate JIT for a disposable PG17 database.
BEGIN;

CREATE TABLE IF NOT EXISTS private.h3_admin_rpc_gateway_keys (
  key_id TEXT PRIMARY KEY CHECK (key_id ~ '^[A-Za-z0-9._-]{1,32}$'),
  project_ref TEXT NOT NULL CHECK (project_ref ~ '^[a-z0-9-]{1,64}$'),
  secret TEXT NOT NULL CHECK (octet_length(secret) >= 32),
  valid_until TIMESTAMPTZ NOT NULL DEFAULT 'infinity'::timestamptz,
  created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
ALTER TABLE private.h3_admin_rpc_gateway_keys ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE private.h3_admin_rpc_gateway_keys FROM PUBLIC, anon, authenticated, service_role;

CREATE TABLE IF NOT EXISTS private.h3_admin_rpc_gateway_nonces (
  nonce UUID PRIMARY KEY,
  actor UUID NOT NULL,
  rpc_name TEXT NOT NULL CHECK (rpc_name ~ '^admin_[a-z0-9_]+$'),
  issued_at TIMESTAMPTZ NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
ALTER TABLE private.h3_admin_rpc_gateway_nonces ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE private.h3_admin_rpc_gateway_nonces FROM PUBLIC, anon, authenticated, service_role;
CREATE INDEX IF NOT EXISTS h3_admin_rpc_gateway_nonce_expiry
  ON private.h3_admin_rpc_gateway_nonces(expires_at);

-- Resolve pgcrypto from its installed extension schema (Supabase commonly uses
-- `extensions`; standalone PG17 fixtures may use `public`). The caller fails
-- closed if pgcrypto is unavailable; no search_path lookup is trusted.
CREATE OR REPLACE FUNCTION private.h3_admin_rpc_gateway_hmac(p_payload TEXT, p_secret TEXT)
RETURNS TEXT
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE extension_schema TEXT; result TEXT;
BEGIN
  SELECT n.nspname INTO extension_schema
  FROM pg_catalog.pg_extension e
  JOIN pg_catalog.pg_namespace n ON n.oid = e.extnamespace
  WHERE e.extname = 'pgcrypto';
  IF extension_schema IS NULL THEN RETURN NULL; END IF;
  EXECUTE pg_catalog.format(
    'SELECT pg_catalog.encode(%I.hmac(pg_catalog.convert_to($1, ''UTF8''), pg_catalog.convert_to($2, ''UTF8''), ''sha256''), ''hex'')',
    extension_schema
  ) INTO result USING p_payload, p_secret;
  RETURN result;
EXCEPTION WHEN OTHERS THEN
  RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION private.h3_admin_rpc_gateway_hmac(TEXT, TEXT) FROM PUBLIC, anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.h3_admin_rpc_signed_gateway_pre_request()
RETURNS VOID
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  request_path TEXT := COALESCE(pg_catalog.current_setting('request.path', true), '');
  request_method TEXT := upper(COALESCE(pg_catalog.current_setting('request.method', true), ''));
  request_role TEXT := COALESCE(
    NULLIF(pg_catalog.current_setting('request.jwt.claim.role', true), ''),
    NULLIF(pg_catalog.current_setting('request.jwt.claims', true), '')::jsonb ->> 'role',
    ''
  );
  request_headers JSONB;
  path_match TEXT[];
  rpc_name TEXT;
  actor_text TEXT;
  actor_id UUID;
  issued_text TEXT;
  issued_seconds BIGINT;
  nonce_text TEXT;
  nonce_id UUID;
  gateway_key_id TEXT;
  signature TEXT;
  project_ref TEXT;
  signing_secret TEXT;
  expected_signature TEXT;
  expected_bytes BYTEA;
  signature_bytes BYTEA;
  canonical TEXT;
  now_at TIMESTAMPTZ := clock_timestamp();
  now_seconds BIGINT;
  difference INTEGER := 0;
  byte_index INTEGER;
  inserted_rows INTEGER;
  admin_rpc_names CONSTANT TEXT[] := ARRAY[
    'admin_has_aal2','admin_require_aal2','admin_is_active_admin','admin_is_active_editor','admin_user_can_edit_field',
    'admin_current_user_role','admin_accept_current_invitation','admin_get_onboarding_status','admin_complete_password_setup',
    'admin_get_course_audit','admin_get_course_editorial','admin_update_course','admin_set_course_availability',
    'admin_publish_course','admin_unpublish_course','admin_archive_course','admin_update_quality_status',
    'admin_get_course_queue_facets','admin_get_course_queue_filtered','admin_count_course_queue_filtered',
    'admin_list_members_onboarding','admin_update_member','admin_invitation_reserve','admin_invitation_record_failure',
    'admin_invitation_complete','admin_invitation_fail','admin_invitation_expire','admin_invitation_mark_delivery_reconciliation',
    'admin_invitation_request_admit','admin_get_course_queue','admin_count_course_queue','admin_list_members','admin_create_member'
  ];
BEGIN
  path_match := pg_catalog.regexp_match(request_path, '^/?rpc/([A-Za-z][A-Za-z0-9_]*)$');
  rpc_name := path_match[1];
  IF rpc_name IS NULL THEN
    path_match := pg_catalog.regexp_match(request_path, '^/?rest/v1/rpc/([A-Za-z][A-Za-z0-9_]*)$');
    rpc_name := path_match[1];
  END IF;
  IF rpc_name IS NULL OR pg_catalog.left(pg_catalog.lower(rpc_name), 6) <> 'admin_' THEN
    RETURN;
  END IF;
  rpc_name := pg_catalog.lower(rpc_name);

  IF NOT (rpc_name = ANY(admin_rpc_names)) THEN
    RAISE SQLSTATE 'PGRST'
      USING MESSAGE = pg_catalog.jsonb_build_object('code','rpc_not_allowlisted','message','Administrative RPC is not allowlisted','details',NULL,'hint',NULL)::TEXT,
            DETAIL = pg_catalog.jsonb_build_object('status',403,'headers','{}'::jsonb)::TEXT;
  END IF;
  IF request_method <> 'POST' THEN
    RAISE SQLSTATE 'PGRST'
      USING MESSAGE = pg_catalog.jsonb_build_object('code','rpc_method_rejected','message','Administrative RPC method is not allowed','details',NULL,'hint',NULL)::TEXT,
            DETAIL = pg_catalog.jsonb_build_object('status',403,'headers','{}'::jsonb)::TEXT;
  END IF;

  -- Edge/service writers keep their existing service-only identity and reserve
  -- path; the gateway never substitutes that identity for a user session.
  IF request_role = 'service_role' THEN RETURN; END IF;
  IF request_role <> 'authenticated' OR auth.uid() IS NULL THEN
    RAISE SQLSTATE 'PGRST'
      USING MESSAGE = pg_catalog.jsonb_build_object('code','rpc_signature_required','message','Administrative RPC signature is required','details',NULL,'hint',NULL)::TEXT,
            DETAIL = pg_catalog.jsonb_build_object('status',403,'headers','{}'::jsonb)::TEXT;
  END IF;

  BEGIN
    request_headers := COALESCE(NULLIF(pg_catalog.current_setting('request.headers', true), '')::jsonb, '{}'::jsonb);
  EXCEPTION WHEN OTHERS THEN
    request_headers := '{}'::jsonb;
  END;
  gateway_key_id := request_headers ->> 'x-studiamatch-admin-rpc-key-id';
  actor_text := request_headers ->> 'x-studiamatch-admin-rpc-actor';
  issued_text := request_headers ->> 'x-studiamatch-admin-rpc-issued-at';
  nonce_text := request_headers ->> 'x-studiamatch-admin-rpc-nonce';
  signature := request_headers ->> 'x-studiamatch-admin-rpc-signature';

  IF gateway_key_id IS NULL AND actor_text IS NULL AND issued_text IS NULL
     AND nonce_text IS NULL AND signature IS NULL THEN
    RAISE SQLSTATE 'PGRST'
      USING MESSAGE = pg_catalog.jsonb_build_object('code','rpc_signature_required','message','Administrative RPC signature is required','details',NULL,'hint',NULL)::TEXT,
            DETAIL = pg_catalog.jsonb_build_object('status',403,'headers','{}'::jsonb)::TEXT;
  END IF;

  IF gateway_key_id IS NULL OR gateway_key_id !~ '^[A-Za-z0-9._-]{1,32}$'
     OR actor_text IS NULL OR actor_text !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
     OR issued_text IS NULL OR issued_text !~ '^[0-9]{10}$'
     OR nonce_text IS NULL OR nonce_text !~* '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
     OR signature IS NULL OR signature !~ '^[a-f0-9]{64}$' THEN
    RAISE SQLSTATE 'PGRST'
      USING MESSAGE = pg_catalog.jsonb_build_object('code','rpc_signature_invalid','message','Administrative RPC signature is invalid','details',NULL,'hint',NULL)::TEXT,
             DETAIL = pg_catalog.jsonb_build_object('status',403,'headers','{}'::jsonb)::TEXT;
  END IF;

  actor_id := actor_text::UUID;
  nonce_id := nonce_text::UUID;
  issued_seconds := issued_text::BIGINT;
  now_seconds := floor(extract(epoch FROM now_at))::BIGINT;
  IF actor_id IS DISTINCT FROM auth.uid() OR issued_seconds > now_seconds OR now_seconds - issued_seconds > 60 THEN
    RAISE SQLSTATE 'PGRST'
      USING MESSAGE = pg_catalog.jsonb_build_object('code','rpc_signature_invalid','message','Administrative RPC signature is invalid','details',NULL,'hint',NULL)::TEXT,
             DETAIL = pg_catalog.jsonb_build_object('status',403,'headers','{}'::jsonb)::TEXT;
  END IF;

  SELECT k.project_ref, k.secret INTO project_ref, signing_secret
  FROM private.h3_admin_rpc_gateway_keys k
  WHERE k.key_id = gateway_key_id AND k.valid_until > now_at;
  IF NOT FOUND THEN
    IF NOT EXISTS (SELECT 1 FROM private.h3_admin_rpc_gateway_keys k WHERE k.valid_until > now_at) THEN
      RAISE SQLSTATE 'PGRST'
        USING MESSAGE = pg_catalog.jsonb_build_object('code','rpc_gateway_unavailable','message','Administrative RPC gateway is unavailable','details',NULL,'hint',NULL)::TEXT,
              DETAIL = pg_catalog.jsonb_build_object('status',503,'headers',pg_catalog.jsonb_build_object('Retry-After','30'))::TEXT;
    END IF;
    RAISE SQLSTATE 'PGRST'
      USING MESSAGE = pg_catalog.jsonb_build_object('code','rpc_signature_invalid','message','Administrative RPC signature is invalid','details',NULL,'hint',NULL)::TEXT,
             DETAIL = pg_catalog.jsonb_build_object('status',403,'headers','{}'::jsonb)::TEXT;
  END IF;

  canonical := pg_catalog.concat_ws(E'\n','studiamatch-admin-rpc-v1',project_ref,'POST',rpc_name,actor_id::TEXT,issued_text,nonce_id::TEXT,gateway_key_id);
  expected_signature := private.h3_admin_rpc_gateway_hmac(canonical, signing_secret);
  IF expected_signature IS NULL THEN
    RAISE SQLSTATE 'PGRST'
      USING MESSAGE = pg_catalog.jsonb_build_object('code','rpc_gateway_unavailable','message','Administrative RPC gateway is unavailable','details',NULL,'hint',NULL)::TEXT,
            DETAIL = pg_catalog.jsonb_build_object('status',503,'headers',pg_catalog.jsonb_build_object('Retry-After','30'))::TEXT;
  END IF;

  -- Constant-work comparison avoids returning early for a matching signature prefix.
  expected_bytes := pg_catalog.decode(expected_signature,'hex');
  signature_bytes := pg_catalog.decode(signature,'hex');
  FOR byte_index IN 0..31 LOOP
    difference := difference | (pg_catalog.get_byte(expected_bytes,byte_index)
                               # pg_catalog.get_byte(signature_bytes,byte_index));
  END LOOP;
  IF difference <> 0 THEN
    RAISE SQLSTATE 'PGRST'
      USING MESSAGE = pg_catalog.jsonb_build_object('code','rpc_signature_invalid','message','Administrative RPC signature is invalid','details',NULL,'hint',NULL)::TEXT,
             DETAIL = pg_catalog.jsonb_build_object('status',403,'headers','{}'::jsonb)::TEXT;
  END IF;

  -- The nonce commits atomically with a successful PostgREST transaction. If a
  -- transaction aborts, the nonce rolls back too; the RPC's DB effects also roll
  -- back and BFF Durable Object admission remains consumed. Strict replay state
  -- across aborted transactions would require an external durable verifier.
  DELETE FROM private.h3_admin_rpc_gateway_nonces n WHERE n.expires_at <= now_at;
  INSERT INTO private.h3_admin_rpc_gateway_nonces(nonce,actor,rpc_name,issued_at,expires_at)
  VALUES(nonce_id,actor_id,rpc_name,pg_catalog.to_timestamp(issued_seconds),pg_catalog.to_timestamp(issued_seconds + 60))
  ON CONFLICT (nonce) DO NOTHING;
  GET DIAGNOSTICS inserted_rows = ROW_COUNT;
  IF inserted_rows <> 1 THEN
    RAISE SQLSTATE 'PGRST'
      USING MESSAGE = pg_catalog.jsonb_build_object('code','rpc_replay_rejected','message','Administrative RPC replay is not allowed','details',NULL,'hint',NULL)::TEXT,
            DETAIL = pg_catalog.jsonb_build_object('status',409,'headers','{}'::jsonb)::TEXT;
  END IF;
END;
$$;

REVOKE ALL ON FUNCTION public.h3_admin_rpc_signed_gateway_pre_request() FROM PUBLIC;
-- PostgREST v13 runs db-pre-request after user impersonation. The hook therefore
-- needs EXECUTE for its API roles; it exposes no key/table access and is a no-op
-- outside the explicit Admin RPC inventory. It must be configured separately.
GRANT EXECUTE ON FUNCTION public.h3_admin_rpc_signed_gateway_pre_request() TO anon, authenticated, service_role;

COMMENT ON FUNCTION public.h3_admin_rpc_signed_gateway_pre_request() IS
  'H3REQ1 pre-request verifier. Configure only after signed BFF deployment and environment key provisioning.';
COMMIT;
