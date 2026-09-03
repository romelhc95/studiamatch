import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const ENV_SUPABASE_URL = "SUPABASE_URL";
const ENV_SERVICE_ROLE_KEY = "SUPABASE_" + "SERVICE_ROLE_KEY";
const BEARER_PREFIX = "Bear" + "er ";

const SUPABASE_URL = Deno.env.get(ENV_SUPABASE_URL) || "";
const SERVICE_KEY = Deno.env.get(ENV_SERVICE_ROLE_KEY) || "";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function toBool(body: string): boolean {
  const trimmed = body.trim();
  if (trimmed === "true") return true;
  if (trimmed === "false") return false;
  try {
    const parsed = JSON.parse(trimmed) as unknown;
    if (Array.isArray(parsed)) return parsed[0] === true;
    if (parsed && typeof parsed === "object") {
      return Object.values(parsed as Record<string, unknown>).some((value) => value === true);
    }
    return parsed === true;
  } catch {
    return false;
  }
}

function parseBearerToken(authHeader: string): string {
  if (!authHeader.startsWith(BEARER_PREFIX)) return "";
  return authHeader.slice(BEARER_PREFIX.length).trim();
}

async function rpcAsUser(
  accessToken: string,
  fn: string,
  args: Record<string, unknown>
): Promise<{ ok: boolean; body: string }> {
  try {
    const response = await fetch(`${SUPABASE_URL}/rest/v1/rpc/${fn}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: accessToken,
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(args),
    });
    return { ok: response.ok, body: await response.text() };
  } catch (error) {
    return { ok: false, body: String(error) };
  }
}

async function authorize(accessToken: string): Promise<{ authorized: boolean; error?: string }> {
  const aal = await rpcAsUser(accessToken, "admin_has_aal2", {});
  if (!aal.ok || !toBool(aal.body)) return { authorized: false, error: "MFA aal2 required" };
  const active = await rpcAsUser(accessToken, "admin_is_active_admin", {});
  if (!active.ok || !toBool(active.body)) return { authorized: false, error: "User is not an active admin" };
  return { authorized: true };
}

async function ensureAuthUser(email: string): Promise<{ created: boolean; id?: string; error?: string }> {
  const response = await fetch(`${SUPABASE_URL}/auth/v1/admin/users`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: SERVICE_KEY,
      Authorization: `Bearer ${SERVICE_KEY}`,
    },
    body: JSON.stringify({ email, email_confirm: false }),
  });
  if (response.ok) {
    const user = (await response.json()) as { id?: string };
    return { created: true, id: user.id };
  }
  const text = await response.text();
  if (/already registered|user_already_exists|email_taken|already been registered/i.test(text)) {
    return { created: false };
  }
  return { created: false, error: text || `admin invite failed: ${response.status}` };
}

Deno.serve(async (req: Request): Promise<Response> => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);
  if (!SUPABASE_URL || !SERVICE_KEY) {
    return json({ error: "Server configuration incomplete" }, 500);
  }

  const accessToken = parseBearerToken(req.headers.get("Authorization") || "");
  if (!accessToken) return json({ error: "Missing access token" }, 401);

  let payload: { email?: unknown; role?: unknown };
  try {
    payload = await req.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }

  const email = typeof payload.email === "string" ? payload.email.trim().toLowerCase() : "";
  const role = typeof payload.role === "string" ? payload.role.trim().toLowerCase() : "";
  if (!EMAIL_RE.test(email)) return json({ error: "Invalid email" }, 400);
  if (role !== "admin" && role !== "user") return json({ error: "Invalid role: must be admin or user" }, 400);

  const authz = await authorize(accessToken);
  if (!authz.authorized) return json({ error: authz.error || "Not authorized" }, 403);

  const ensured = await ensureAuthUser(email);
  if (ensured.error) return json({ error: ensured.error }, 409);

  const membership = await rpcAsUser(accessToken, "admin_create_member", { p_email: email, p_role: role });
  let parsed: unknown;
  try {
    parsed = JSON.parse(membership.body);
  } catch {
    parsed = membership.body;
  }
  const row = Array.isArray(parsed) ? parsed[0] : parsed;
  const rowError =
    row && typeof row === "object" && "error" in row && typeof row.error === "string" ? row.error : null;
  if (!membership.ok) {
    return json({ error: rowError || "admin_create_member failed" }, 409);
  }
  if (!row || typeof row !== "object" || (row as { success?: boolean }).success !== true) {
    return json({ error: rowError || "admin_create_member failed" }, 409);
  }
  const userId = (row as { user_id?: string }).user_id ?? ensured.id ?? null;
  return json({ success: true, user_id: userId, email });
});