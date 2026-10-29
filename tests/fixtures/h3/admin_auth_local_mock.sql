CREATE TABLE IF NOT EXISTS public.admin_members (
  admin_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_email TEXT UNIQUE NOT NULL,
  admin_password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_admin_members_role_active ON public.admin_members (role, is_active);
CREATE INDEX IF NOT EXISTS idx_admin_members_email ON public.admin_members (admin_email);

ALTER TABLE public.admin_members ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS admin_members_service_select ON public.admin_members;
CREATE POLICY admin_members_service_select ON public.admin_members FOR SELECT TO service_role USING (true);

DROP POLICY IF EXISTS admin_members_service_insert ON public.admin_members;
CREATE POLICY admin_members_service_insert ON public.admin_members FOR INSERT TO service_role WITH CHECK (true);

DROP POLICY IF EXISTS admin_members_service_update ON public.admin_members;
CREATE POLICY admin_members_service_update ON public.admin_members FOR UPDATE TO service_role USING (true) WITH CHECK (true);

CREATE OR REPLACE FUNCTION public.admin_current_user_role()
RETURNS TEXT LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  _admin_id UUID;
  _role TEXT;
BEGIN
  BEGIN
    _admin_id := NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID;
  EXCEPTION WHEN OTHERS THEN
    RETURN 'anon';
  END;
  IF _admin_id IS NULL THEN RETURN 'anon'; END IF;
  SELECT role INTO _role FROM public.admin_members WHERE admin_id = _admin_id AND is_active = true;
  RETURN COALESCE(_role, 'authenticated');
EXCEPTION WHEN OTHERS THEN RETURN 'error';
END;
$$;

CREATE OR REPLACE FUNCTION public.admin_is_active_admin()
RETURNS BOOLEAN LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE _admin_id UUID;
BEGIN
  BEGIN _admin_id := NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID; EXCEPTION WHEN OTHERS THEN RETURN false; END;
  RETURN EXISTS (SELECT 1 FROM public.admin_members WHERE admin_id = _admin_id AND role = 'admin' AND is_active = true);
END;
$$;

CREATE OR REPLACE FUNCTION public.admin_is_active_editor()
RETURNS BOOLEAN LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE _admin_id UUID;
BEGIN
  BEGIN _admin_id := NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID; EXCEPTION WHEN OTHERS THEN RETURN false; END;
  RETURN EXISTS (SELECT 1 FROM public.admin_members WHERE admin_id = _admin_id AND role IN ('admin', 'user') AND is_active = true);
END;
$$;

GRANT EXECUTE ON FUNCTION public.admin_current_user_role() TO service_role;
GRANT EXECUTE ON FUNCTION public.admin_is_active_admin() TO service_role;
GRANT EXECUTE ON FUNCTION public.admin_is_active_editor() TO service_role;

CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at := now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS admin_members_updated_at ON public.admin_members;
CREATE TRIGGER admin_members_updated_at BEFORE UPDATE ON public.admin_members FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
