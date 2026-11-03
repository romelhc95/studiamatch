-- H3REQ1: bind the Admin RPC gateway proof to the exact typed dispatch payload.
-- Additive EXPAND only. Activation, key provisioning, and disposable PG17 execution
-- each require their own JIT approval; this migration performs none of them.
BEGIN;

CREATE OR REPLACE FUNCTION private.h3_admin_rpc_gateway_fail(
  p_code TEXT,
  p_message TEXT,
  p_status INTEGER
)
RETURNS VOID
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  response_headers JSONB := CASE WHEN p_status = 503
    THEN pg_catalog.jsonb_build_object('Retry-After', '30')
    ELSE '{}'::JSONB END;
BEGIN
  RAISE SQLSTATE 'PGRST'
    USING MESSAGE = pg_catalog.jsonb_build_object(
      'code', p_code, 'message', p_message, 'details', NULL, 'hint', NULL
    )::TEXT,
    DETAIL = pg_catalog.jsonb_build_object(
      'status', p_status, 'headers', response_headers
    )::TEXT;
END;
$$;
REVOKE ALL ON FUNCTION private.h3_admin_rpc_gateway_fail(TEXT, TEXT, INTEGER)
  FROM PUBLIC, anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION private.h3_admin_rpc_gateway_signature_matches(
  p_actual TEXT,
  p_expected TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql IMMUTABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  actual_bytes BYTEA;
  expected_bytes BYTEA;
  difference INTEGER := 0;
  byte_index INTEGER;
BEGIN
  IF p_actual IS NULL OR p_actual !~ '^[a-f0-9]{64}$'
     OR p_expected IS NULL OR p_expected !~ '^[a-f0-9]{64}$' THEN
    RETURN FALSE;
  END IF;
  actual_bytes := pg_catalog.decode(p_actual, 'hex');
  expected_bytes := pg_catalog.decode(p_expected, 'hex');
  FOR byte_index IN 0..31 LOOP
    difference := difference | (pg_catalog.get_byte(actual_bytes, byte_index)
                               # pg_catalog.get_byte(expected_bytes, byte_index));
  END LOOP;
  RETURN difference = 0;
EXCEPTION WHEN OTHERS THEN
  RETURN FALSE;
END;
$$;
REVOKE ALL ON FUNCTION private.h3_admin_rpc_gateway_signature_matches(TEXT, TEXT)
  FROM PUBLIC, anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION private.h3_admin_rpc_args_match(
  p_args JSONB,
  p_allowed_keys TEXT[],
  p_required_keys TEXT[]
)
RETURNS BOOLEAN
LANGUAGE SQL IMMUTABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
  SELECT pg_catalog.jsonb_typeof(p_args) = 'object'
     AND p_args - p_allowed_keys = '{}'::JSONB
     AND NOT EXISTS (
       SELECT 1
       FROM pg_catalog.unnest(p_required_keys) AS required_key(key)
       WHERE NOT (p_args ? required_key.key)
     )
$$;
REVOKE ALL ON FUNCTION private.h3_admin_rpc_args_match(JSONB, TEXT[], TEXT[])
  FROM PUBLIC, anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION private.h3_admin_rpc_gateway_verify_payload(
  p_rpc_name TEXT,
  p_args JSONB,
  p_signed_payload TEXT
)
RETURNS VOID
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  request_path TEXT := COALESCE(pg_catalog.current_setting('request.path', true), '');
  request_method TEXT := upper(COALESCE(pg_catalog.current_setting('request.method', true), ''));
  request_role TEXT := COALESCE(
    NULLIF(pg_catalog.current_setting('request.jwt.claim.role', true), ''),
    NULLIF(pg_catalog.current_setting('request.jwt.claims', true), '')::JSONB ->> 'role',
    ''
  );
  request_headers JSONB;
  actor_text TEXT;
  actor_id UUID;
  issued_text TEXT;
  issued_seconds BIGINT;
  nonce_text TEXT;
  nonce_id UUID;
  v_key_id TEXT;
  metadata_signature TEXT;
  payload_signature TEXT;
  project_ref TEXT;
  signing_secret TEXT;
  expected_signature TEXT;
  expected_payload_signature TEXT;
  metadata_canonical TEXT;
  payload_canonical TEXT;
  payload_args JSONB;
  now_at TIMESTAMPTZ := clock_timestamp();
  inserted_rows INTEGER;
  target_names CONSTANT TEXT[] := ARRAY[
    'admin_current_user_role', 'admin_accept_current_invitation',
    'admin_get_onboarding_status', 'admin_complete_password_setup',
    'admin_get_course_audit', 'admin_get_course_editorial', 'admin_update_course',
    'admin_set_course_availability', 'admin_publish_course', 'admin_unpublish_course',
    'admin_archive_course', 'admin_update_quality_status', 'admin_get_course_queue_facets',
    'admin_get_course_queue_filtered', 'admin_count_course_queue_filtered',
    'admin_list_members_onboarding', 'admin_update_member'
  ];
BEGIN
  IF p_rpc_name IS NULL OR NOT (p_rpc_name = ANY(target_names)) THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_not_allowlisted', 'Administrative RPC is not allowlisted', 403
    );
  END IF;
  IF pg_catalog.regexp_match(request_path, '^/?(?:rest/v1/)?rpc/admin_signed_rpc$') IS NULL
     OR request_method <> 'POST' THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_invalid', 'Administrative RPC signature is invalid', 403
    );
  END IF;
  IF request_role <> 'authenticated' OR auth.uid() IS NULL THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_required', 'Administrative RPC signature is required', 403
    );
  END IF;
  IF p_signed_payload IS NULL OR pg_catalog.octet_length(p_signed_payload) > 65536
     OR pg_catalog.jsonb_typeof(p_args) <> 'object' THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_invalid', 'Administrative RPC signature is invalid', 403
    );
  END IF;
  BEGIN
    payload_args := p_signed_payload::JSONB;
  EXCEPTION WHEN OTHERS THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_invalid', 'Administrative RPC signature is invalid', 403
    );
  END;
  IF payload_args IS DISTINCT FROM p_args THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_invalid', 'Administrative RPC signature is invalid', 403
    );
  END IF;

  BEGIN
    request_headers := COALESCE(
      NULLIF(pg_catalog.current_setting('request.headers', true), '')::JSONB,
      '{}'::JSONB
    );
  EXCEPTION WHEN OTHERS THEN
    request_headers := '{}'::JSONB;
  END;
  v_key_id := request_headers ->> 'x-studiamatch-admin-rpc-key-id';
  actor_text := request_headers ->> 'x-studiamatch-admin-rpc-actor';
  issued_text := request_headers ->> 'x-studiamatch-admin-rpc-issued-at';
  nonce_text := request_headers ->> 'x-studiamatch-admin-rpc-nonce';
  metadata_signature := request_headers ->> 'x-studiamatch-admin-rpc-signature';
  payload_signature := request_headers ->> 'x-studiamatch-admin-rpc-payload-signature';

  IF v_key_id IS NULL AND actor_text IS NULL AND issued_text IS NULL
     AND nonce_text IS NULL AND metadata_signature IS NULL AND payload_signature IS NULL THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_required', 'Administrative RPC signature is required', 403
    );
  END IF;
  IF v_key_id IS NULL OR v_key_id !~ '^[A-Za-z0-9._-]{1,32}$'
     OR actor_text IS NULL OR actor_text !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
     OR issued_text IS NULL OR issued_text !~ '^[0-9]{10}$'
     OR nonce_text IS NULL OR nonce_text !~* '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
     OR metadata_signature IS NULL OR metadata_signature !~ '^[a-f0-9]{64}$'
     OR payload_signature IS NULL OR payload_signature !~ '^[a-f0-9]{64}$' THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_invalid', 'Administrative RPC signature is invalid', 403
    );
  END IF;

  actor_id := actor_text::UUID;
  nonce_id := nonce_text::UUID;
  issued_seconds := issued_text::BIGINT;
  IF actor_id IS DISTINCT FROM auth.uid()
     OR issued_seconds > floor(extract(epoch FROM now_at))::BIGINT
     OR floor(extract(epoch FROM now_at))::BIGINT - issued_seconds > 60 THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_invalid', 'Administrative RPC signature is invalid', 403
    );
  END IF;

  SELECT gateway_key.project_ref, gateway_key.secret
    INTO project_ref, signing_secret
  FROM private.h3_admin_rpc_gateway_keys AS gateway_key
  WHERE gateway_key.key_id = v_key_id AND gateway_key.valid_until > now_at;
  IF NOT FOUND THEN
    IF NOT EXISTS (
      SELECT 1 FROM private.h3_admin_rpc_gateway_keys AS gateway_key
      WHERE gateway_key.valid_until > now_at
    ) THEN
      PERFORM private.h3_admin_rpc_gateway_fail(
        'rpc_gateway_unavailable', 'Administrative RPC gateway is unavailable', 503
      );
    END IF;
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_invalid', 'Administrative RPC signature is invalid', 403
    );
  END IF;

  metadata_canonical := pg_catalog.concat_ws(E'\n',
    'studiamatch-admin-rpc-v1', project_ref, 'POST', 'admin_signed_rpc',
    actor_id::TEXT, issued_text, nonce_id::TEXT, v_key_id
  );
  payload_canonical := pg_catalog.concat_ws(E'\n',
    'studiamatch-admin-rpc-payload-v1', project_ref, 'POST', 'admin_signed_rpc',
    p_rpc_name, actor_id::TEXT, issued_text, nonce_id::TEXT, v_key_id, p_signed_payload
  );
  expected_signature := private.h3_admin_rpc_gateway_hmac(metadata_canonical, signing_secret);
  expected_payload_signature := private.h3_admin_rpc_gateway_hmac(payload_canonical, signing_secret);
  IF expected_signature IS NULL OR expected_payload_signature IS NULL THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_gateway_unavailable', 'Administrative RPC gateway is unavailable', 503
    );
  END IF;
  IF NOT private.h3_admin_rpc_gateway_signature_matches(metadata_signature, expected_signature)
     OR NOT private.h3_admin_rpc_gateway_signature_matches(payload_signature, expected_payload_signature) THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_invalid', 'Administrative RPC signature is invalid', 403
    );
  END IF;

  DELETE FROM private.h3_admin_rpc_gateway_nonces AS old_nonce
  WHERE old_nonce.expires_at <= now_at;
  INSERT INTO private.h3_admin_rpc_gateway_nonces(nonce, actor, rpc_name, issued_at, expires_at)
  VALUES (nonce_id, actor_id, p_rpc_name, pg_catalog.to_timestamp(issued_seconds),
          pg_catalog.to_timestamp(issued_seconds + 60))
  ON CONFLICT (nonce) DO NOTHING;
  GET DIAGNOSTICS inserted_rows = ROW_COUNT;
  IF inserted_rows <> 1 THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_replay_rejected', 'Administrative RPC replay is not allowed', 409
    );
  END IF;
END;
$$;
REVOKE ALL ON FUNCTION private.h3_admin_rpc_gateway_verify_payload(TEXT, JSONB, TEXT)
  FROM PUBLIC, anon, authenticated, service_role;

-- The dispatcher has no dynamic SQL: every exposed target is parsed into its
-- declared SQL types before the original RPC is invoked. auth.uid(), target RLS,
-- RBAC and each target's MFA check therefore remain the authority for the call.
CREATE OR REPLACE FUNCTION public.admin_signed_rpc(
  p_rpc_name TEXT,
  p_args JSONB,
  p_signed_payload TEXT
)
RETURNS JSONB
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  result JSONB;
BEGIN
  PERFORM private.h3_admin_rpc_gateway_verify_payload(p_rpc_name, p_args, p_signed_payload);

  IF p_rpc_name = 'admin_current_user_role' THEN
    IF NOT private.h3_admin_rpc_args_match(p_args, ARRAY[]::TEXT[], ARRAY[]::TEXT[]) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    RETURN pg_catalog.to_jsonb(public.admin_current_user_role());

  ELSIF p_rpc_name = 'admin_accept_current_invitation' THEN
    IF NOT private.h3_admin_rpc_args_match(p_args, ARRAY['p_invitation_id'], ARRAY[]::TEXT[]) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_accept_current_invitation((p_args ->> 'p_invitation_id')::UUID) AS rpc_row;
    RETURN result;

  ELSIF p_rpc_name = 'admin_get_onboarding_status' THEN
    IF NOT private.h3_admin_rpc_args_match(p_args, ARRAY[]::TEXT[], ARRAY[]::TEXT[]) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_get_onboarding_status() AS rpc_row;
    RETURN result;

  ELSIF p_rpc_name = 'admin_complete_password_setup' THEN
    IF NOT private.h3_admin_rpc_args_match(p_args, ARRAY[]::TEXT[], ARRAY[]::TEXT[]) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_complete_password_setup() AS rpc_row;
    RETURN result;

  ELSIF p_rpc_name = 'admin_get_course_audit' THEN
    IF NOT private.h3_admin_rpc_args_match(
      p_args, ARRAY['p_course_id','p_first','p_after_created_at','p_after_id'], ARRAY['p_course_id']
    ) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_get_course_audit(
      (p_args ->> 'p_course_id')::UUID,
      CASE WHEN p_args ? 'p_first' THEN (p_args ->> 'p_first')::INTEGER ELSE 20 END,
      (p_args ->> 'p_after_created_at')::TIMESTAMPTZ,
      (p_args ->> 'p_after_id')::UUID
    ) AS rpc_row;
    RETURN result;

  ELSIF p_rpc_name = 'admin_get_course_editorial' THEN
    IF NOT private.h3_admin_rpc_args_match(p_args, ARRAY['p_course_id'], ARRAY['p_course_id']) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_get_course_editorial((p_args ->> 'p_course_id')::UUID) AS rpc_row;
    RETURN result;

  ELSIF p_rpc_name = 'admin_update_course' THEN
    IF NOT private.h3_admin_rpc_args_match(
      p_args, ARRAY['p_course_id','p_manual_overrides','p_version','p_reason'],
      ARRAY['p_course_id','p_manual_overrides','p_version']
    ) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_update_course(
      (p_args ->> 'p_course_id')::UUID,
      p_args -> 'p_manual_overrides',
      (p_args ->> 'p_version')::INTEGER,
      p_args ->> 'p_reason'
    ) AS rpc_row;
    RETURN result;

  ELSIF p_rpc_name = 'admin_set_course_availability' THEN
    IF NOT private.h3_admin_rpc_args_match(
      p_args,
      ARRAY['p_course_id','p_availability_status','p_evidence_url','p_observed_at','p_valid_until','p_version','p_reason'],
      ARRAY['p_course_id','p_availability_status','p_evidence_url','p_observed_at','p_valid_until','p_version','p_reason']
    ) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_set_course_availability(
      (p_args ->> 'p_course_id')::UUID,
      p_args ->> 'p_availability_status', p_args ->> 'p_evidence_url',
      (p_args ->> 'p_observed_at')::TIMESTAMPTZ, (p_args ->> 'p_valid_until')::TIMESTAMPTZ,
      (p_args ->> 'p_version')::INTEGER, p_args ->> 'p_reason'
    ) AS rpc_row;
    RETURN result;

  ELSIF p_rpc_name IN ('admin_publish_course','admin_unpublish_course','admin_archive_course') THEN
    IF NOT private.h3_admin_rpc_args_match(
      p_args, ARRAY['p_course_id','p_reason'], ARRAY['p_course_id']
    ) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    IF p_rpc_name = 'admin_publish_course' THEN
      SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
      FROM public.admin_publish_course((p_args ->> 'p_course_id')::UUID, p_args ->> 'p_reason') AS rpc_row;
    ELSIF p_rpc_name = 'admin_unpublish_course' THEN
      SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
      FROM public.admin_unpublish_course((p_args ->> 'p_course_id')::UUID, p_args ->> 'p_reason') AS rpc_row;
    ELSE
      SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
      FROM public.admin_archive_course((p_args ->> 'p_course_id')::UUID, p_args ->> 'p_reason') AS rpc_row;
    END IF;
    RETURN result;

  ELSIF p_rpc_name = 'admin_update_quality_status' THEN
    IF NOT private.h3_admin_rpc_args_match(
      p_args, ARRAY['p_course_id','p_quality_status','p_reason'], ARRAY['p_course_id','p_quality_status']
    ) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_update_quality_status(
      (p_args ->> 'p_course_id')::UUID, p_args ->> 'p_quality_status', p_args ->> 'p_reason'
    ) AS rpc_row;
    RETURN result;

  ELSIF p_rpc_name = 'admin_get_course_queue_facets' THEN
    IF NOT private.h3_admin_rpc_args_match(p_args, ARRAY[]::TEXT[], ARRAY[]::TEXT[]) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_get_course_queue_facets() AS rpc_row;
    RETURN result;

  ELSIF p_rpc_name = 'admin_get_course_queue_filtered' THEN
    IF NOT private.h3_admin_rpc_args_match(
      p_args, ARRAY['p_first','p_after_cursor','p_editorial_status','p_quality_status','p_institution_slug'], ARRAY[]::TEXT[]
    ) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    IF p_args ? 'p_first' AND p_args -> 'p_first' = 'null'::JSONB THEN
      -- Never pass SQL NULL to LIMIT. Use a bounded invalid sentinel through
      -- the public quota/auth wrapper so quota, MFA, RBAC, and its error contract
      -- remain identical to the original RPC.
      SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
      FROM public.admin_get_course_queue_filtered(
        0, p_args ->> 'p_after_cursor', p_args ->> 'p_editorial_status',
        p_args ->> 'p_quality_status', p_args ->> 'p_institution_slug'
      ) AS rpc_row;
      RETURN result;
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_get_course_queue_filtered(
      CASE WHEN p_args ? 'p_first' THEN (p_args ->> 'p_first')::INTEGER ELSE 20 END,
      p_args ->> 'p_after_cursor', p_args ->> 'p_editorial_status',
      p_args ->> 'p_quality_status', p_args ->> 'p_institution_slug'
    ) AS rpc_row;
    RETURN result;

  ELSIF p_rpc_name = 'admin_count_course_queue_filtered' THEN
    IF NOT private.h3_admin_rpc_args_match(
      p_args, ARRAY['p_editorial_status','p_quality_status','p_institution_slug'], ARRAY[]::TEXT[]
    ) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_count_course_queue_filtered(
      p_args ->> 'p_editorial_status', p_args ->> 'p_quality_status', p_args ->> 'p_institution_slug'
    ) AS rpc_row;
    RETURN result;

  ELSIF p_rpc_name = 'admin_list_members_onboarding' THEN
    IF NOT private.h3_admin_rpc_args_match(p_args, ARRAY[]::TEXT[], ARRAY[]::TEXT[]) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_list_members_onboarding() AS rpc_row;
    RETURN result;

  ELSIF p_rpc_name = 'admin_update_member' THEN
    IF NOT private.h3_admin_rpc_args_match(
      p_args, ARRAY['p_user_id','p_role','p_is_active','p_action'], ARRAY['p_user_id']
    ) THEN
      PERFORM private.h3_admin_rpc_gateway_fail('rpc_arguments_invalid', 'Administrative RPC arguments are invalid', 400);
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(rpc_row)), '[]'::JSONB) INTO result
    FROM public.admin_update_member(
      (p_args ->> 'p_user_id')::UUID, p_args ->> 'p_role',
      (p_args ->> 'p_is_active')::BOOLEAN,
      CASE WHEN p_args ? 'p_action' THEN p_args ->> 'p_action' ELSE 'update' END
    ) AS rpc_row;
    RETURN result;
  END IF;

  PERFORM private.h3_admin_rpc_gateway_fail(
    'rpc_not_allowlisted', 'Administrative RPC is not allowlisted', 403
  );
  RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION public.admin_signed_rpc(TEXT, JSONB, TEXT) FROM PUBLIC, anon, service_role;
GRANT EXECUTE ON FUNCTION public.admin_signed_rpc(TEXT, JSONB, TEXT) TO authenticated;
COMMENT ON FUNCTION public.admin_signed_rpc(TEXT, JSONB, TEXT) IS
  'H3REQ1 static typed dispatcher. Verifies a payload-bound gateway HMAC before invoking one of the Admin RPCs through its typed signature.';

-- PostgREST does not expose RPC bodies to db-pre-request. The hook therefore
-- admits only this signed dispatcher for authenticated users; the dispatcher
-- validates both HMACs against p_args and consumes the nonce in the same DB tx.
CREATE OR REPLACE FUNCTION public.h3_admin_rpc_signed_gateway_pre_request()
RETURNS VOID
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  request_path TEXT := COALESCE(pg_catalog.current_setting('request.path', true), '');
  request_method TEXT := upper(COALESCE(pg_catalog.current_setting('request.method', true), ''));
  request_role TEXT := COALESCE(
    NULLIF(pg_catalog.current_setting('request.jwt.claim.role', true), ''),
    NULLIF(pg_catalog.current_setting('request.jwt.claims', true), '')::JSONB ->> 'role',
    ''
  );
  request_headers JSONB;
  path_match TEXT[];
  rpc_name TEXT;
  gateway_key_id TEXT;
  actor_text TEXT;
  issued_text TEXT;
  nonce_text TEXT;
  metadata_signature TEXT;
  payload_signature TEXT;
  admin_rpc_names CONSTANT TEXT[] := ARRAY[
    'admin_has_aal2','admin_require_aal2','admin_is_active_admin','admin_is_active_editor','admin_user_can_edit_field',
    'admin_current_user_role','admin_accept_current_invitation','admin_get_onboarding_status','admin_complete_password_setup',
    'admin_get_course_audit','admin_get_course_editorial','admin_update_course','admin_set_course_availability',
    'admin_publish_course','admin_unpublish_course','admin_archive_course','admin_update_quality_status',
    'admin_get_course_queue_facets','admin_get_course_queue_filtered','admin_count_course_queue_filtered',
    'admin_list_members_onboarding','admin_update_member','admin_invitation_reserve','admin_invitation_record_failure',
    'admin_invitation_complete','admin_invitation_fail','admin_invitation_expire','admin_invitation_mark_delivery_reconciliation',
    'admin_invitation_request_admit','admin_get_course_queue','admin_count_course_queue','admin_list_members',
    'admin_create_member','admin_signed_rpc'
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
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_not_allowlisted', 'Administrative RPC is not allowlisted', 403
    );
  END IF;
  IF request_method <> 'POST' THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_method_rejected', 'Administrative RPC method is not allowed', 403
    );
  END IF;
  IF request_role = 'service_role' THEN
    RETURN;
  END IF;
  IF request_role <> 'authenticated' OR auth.uid() IS NULL THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_required', 'Administrative RPC signature is required', 403
    );
  END IF;
  IF rpc_name <> 'admin_signed_rpc' THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signed_wrapper_required', 'Administrative RPC must use the payload-bound dispatcher', 403
    );
  END IF;

  BEGIN
    request_headers := COALESCE(
      NULLIF(pg_catalog.current_setting('request.headers', true), '')::JSONB,
      '{}'::JSONB
    );
  EXCEPTION WHEN OTHERS THEN
    request_headers := '{}'::JSONB;
  END;
  gateway_key_id := request_headers ->> 'x-studiamatch-admin-rpc-key-id';
  actor_text := request_headers ->> 'x-studiamatch-admin-rpc-actor';
  issued_text := request_headers ->> 'x-studiamatch-admin-rpc-issued-at';
  nonce_text := request_headers ->> 'x-studiamatch-admin-rpc-nonce';
  metadata_signature := request_headers ->> 'x-studiamatch-admin-rpc-signature';
  payload_signature := request_headers ->> 'x-studiamatch-admin-rpc-payload-signature';
  IF gateway_key_id IS NULL AND actor_text IS NULL AND issued_text IS NULL
     AND nonce_text IS NULL AND metadata_signature IS NULL AND payload_signature IS NULL THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_required', 'Administrative RPC signature is required', 403
    );
  END IF;
  IF gateway_key_id IS NULL OR gateway_key_id !~ '^[A-Za-z0-9._-]{1,32}$'
     OR actor_text IS NULL OR actor_text !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
     OR issued_text IS NULL OR issued_text !~ '^[0-9]{10}$'
     OR nonce_text IS NULL OR nonce_text !~* '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
     OR metadata_signature IS NULL OR metadata_signature !~ '^[a-f0-9]{64}$'
     OR payload_signature IS NULL OR payload_signature !~ '^[a-f0-9]{64}$' THEN
    PERFORM private.h3_admin_rpc_gateway_fail(
      'rpc_signature_invalid', 'Administrative RPC signature is invalid', 403
    );
  END IF;
END;
$$;
REVOKE ALL ON FUNCTION public.h3_admin_rpc_signed_gateway_pre_request() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.h3_admin_rpc_signed_gateway_pre_request() TO anon, authenticated, service_role;
COMMENT ON FUNCTION public.h3_admin_rpc_signed_gateway_pre_request() IS
  'H3REQ1 pre-request gate: authenticated users may reach only the signed payload-bound Admin dispatcher; gateway HMACs and nonce are verified by that dispatcher.';

COMMIT;
