import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient, type SupabaseClient } from "npm:@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "";
const SERVICE_KEY = Deno.env.get("NEXT_SUPABASE_SECRET_KEY") || "";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const BEARER_PREFIX = "Bear" + "er ";
const DEFAULT_RESEND_COOLDOWN_SECONDS = 60;
const MAX_INVITE_BODY_BYTES = 64 * 1024;

function isValidSupabaseConfiguration(url: string, apiKey: string): boolean {
  if (!/^sb_secret_[A-Za-z0-9_-]+$/.test(apiKey)) return false;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:"
      && /^[a-z0-9-]+\.supabase\.co$/i.test(parsed.hostname)
      && parsed.pathname === "/"
      && !parsed.username
      && !parsed.password
      && !parsed.search
      && !parsed.hash;
  } catch {
    return false;
  }
}

function createApiKeyOnlyFetch(apiKey: string, fetcher?: typeof fetch): typeof fetch {
  const apiKeyBearerPrefix = "Bear" + "er ";
  return async (input, init) => {
    const send = fetcher || fetch;
    const headers = new Headers(input instanceof Request ? input.headers : undefined);
    new Headers(init?.headers).forEach((value, name) => headers.set(name, value));
    const url = new URL(input instanceof Request ? input.url : String(input));
    if (url.origin !== new URL(SUPABASE_URL).origin || url.username || url.password || url.hash) {
      throw new Error("Supabase transport destination is not allowed.");
    }
    const authorization = headers.get("authorization");
    if (authorization === `${apiKeyBearerPrefix}${apiKey}`) {
      headers.delete("authorization");
    } else if (authorization) {
      const method = (init?.method || (input instanceof Request ? input.method : "GET")).toUpperCase();
      const token = authorization.startsWith(apiKeyBearerPrefix) ? authorization.slice(apiKeyBearerPrefix.length) : "";
      // Auth verifies the token. Shape checking alone never authenticates a user.
      if (method !== "GET" || url.pathname !== "/auth/v1/user"
        || !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(token)) {
        throw new Error("Supabase session transport is not allowed.");
      }
    }
    const response = await send(input, { ...init, headers, redirect: "manual" });
    if ((response.status >= 300 && response.status < 400) || response.type === "opaqueredirect") {
      throw new Error("Supabase redirects are not allowed.");
    }
    return response;
  };
}

type Role = "admin" | "user";

interface InvitePayload {
  email?: unknown;
  role?: unknown;
  resend?: unknown;
}

interface AuthUser {
  id: string;
  email?: string | null;
  email_confirmed_at?: string | null;
  confirmed_at?: string | null;
}

interface Member {
  user_id: string;
  role: Role;
  is_active: boolean;
  account_status: string;
}

interface Invitation {
  id: string;
  status: string;
  expires_at: string;
  last_sent_at: string;
}

interface ReserveRow {
  success: boolean;
  invitation_id: string | null;
  member_id: string | null;
  old_status: string | null;
  resent: boolean;
  error_code: string | null;
}

function corsHeaders(req?: Request): Record<string, string> {
  const origin = req?.headers.get("Origin") || "";
  const configuredOrigins = [
    ...(Deno.env.get("ADMIN_INVITE_ALLOWED_ORIGINS") || "").split(","),
    // Derive CORS origins only from the explicit server-owned redirect allowlist
    // when the dedicated CORS variable is not configured.
    ...(Deno.env.get("ADMIN_INVITE_ALLOWED_REDIRECTS") || "").split(","),
  ];
  const allowedOrigins = new Set(
    configuredOrigins
      .map((value) => {
        try {
          return new URL(value.trim()).origin;
        } catch {
          return "";
        }
      })
      .filter((value) => Boolean(value) && value !== "null"),
  );
  let normalizedOrigin = "";
  try {
    normalizedOrigin = new URL(origin).origin;
  } catch {
    normalizedOrigin = "";
  }
  const headers: Record<string, string> = {
    // An unset/malformed allowlist must fail closed; never reflect an arbitrary Origin.
    "Vary": "Origin",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-request-id",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };
  if (normalizedOrigin && normalizedOrigin !== "null" && allowedOrigins.has(normalizedOrigin)) {
    headers["Access-Control-Allow-Origin"] = normalizedOrigin;
  }
  return headers;
}

function json(body: unknown, status = 200, req?: Request): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders(req), "Content-Type": "application/json" },
  });
}

function getRequestId(req: Request): string {
  const value = req.headers.get("x-request-id")?.trim() || crypto.randomUUID();
  return /^[A-Za-z0-9._:-]{1,100}$/.test(value) ? value : crypto.randomUUID();
}

function parseBearerToken(header: string): string {
  return header.startsWith(BEARER_PREFIX) ? header.slice(BEARER_PREFIX.length).trim() : "";
}

function parseEmail(value: unknown): string {
  return typeof value === "string" ? value.trim().toLowerCase() : "";
}

function parseRole(value: unknown): Role | "" {
  const role = typeof value === "string" ? value.trim().toLowerCase() : "";
  return role === "admin" || role === "user" ? role : "";
}

function parseBoolean(value: unknown): boolean {
  return value === true || value === "true";
}

async function readInvitePayload(req: Request): Promise<
  | { ok: true; payload: InvitePayload }
  | { ok: false; status: 400 | 413; code: "invalid_json" | "body_too_large" }
> {
  if (!req.headers.get("Content-Type")?.toLowerCase().startsWith("application/json")) {
    return { ok: false, status: 400, code: "invalid_json" };
  }
  const declaredLength = Number(req.headers.get("Content-Length") || 0);
  if (declaredLength > MAX_INVITE_BODY_BYTES) return { ok: false, status: 413, code: "body_too_large" };
  if (!req.body) return { ok: false, status: 400, code: "invalid_json" };

  const reader = req.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > MAX_INVITE_BODY_BYTES) {
      await reader.cancel();
      return { ok: false, status: 413, code: "body_too_large" };
    }
    chunks.push(value);
  }

  try {
    const bytes = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    const parsed: unknown = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return { ok: false, status: 400, code: "invalid_json" };
    }
    return { ok: true, payload: parsed as InvitePayload };
  } catch {
    return { ok: false, status: 400, code: "invalid_json" };
  }
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const segment = token.split(".")[1];
    if (!segment) return null;
    const base64 = segment.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
    return JSON.parse(atob(padded)) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function configuredRedirect(): { url: string; environment: string; origin: string } | null {
  const configuredUrl = Deno.env.get("ADMIN_INVITE_REDIRECT_URL")?.trim() || "";
  const allowed = (Deno.env.get("ADMIN_INVITE_ALLOWED_REDIRECTS") || "")
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
  if (!configuredUrl || !allowed.includes(configuredUrl)) return null;

  try {
    const parsed = new URL(configuredUrl);
    if (
      parsed.pathname !== "/admin/auth/callback/"
      || parsed.search
      || parsed.protocol !== "https:"
      || parsed.username
      || parsed.password
      || parsed.hash
    ) {
      return null;
    }
    return {
      url: configuredUrl,
      origin: parsed.origin,
      environment: (Deno.env.get("APP_ENV") || Deno.env.get("ENVIRONMENT") || "development").toLowerCase(),
    };
  } catch {
    return null;
  }
}

function configuredRecoveryRedirect(): { url: string; environment: string; origin: string } | null {
  const configuredUrl = Deno.env.get("ADMIN_INVITE_RECOVERY_REDIRECT_URL")?.trim() || "";
  const allowed = (Deno.env.get("ADMIN_INVITE_ALLOWED_REDIRECTS") || "")
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
  if (!configuredUrl || !allowed.includes(configuredUrl)) return null;

  try {
    const parsed = new URL(configuredUrl);
    if (
      parsed.pathname !== "/admin/auth/callback/"
      || parsed.search
      || parsed.protocol !== "https:"
      || parsed.username
      || parsed.password
      || parsed.hash
    ) {
      return null;
    }
    return {
      url: configuredUrl,
      origin: parsed.origin,
      environment: (Deno.env.get("APP_ENV") || Deno.env.get("ENVIRONMENT") || "development").toLowerCase(),
    };
  } catch {
    return null;
  }
}

function numberEnv(name: string, fallback: number, min: number, max: number): number {
  const value = Number(Deno.env.get(name));
  return Number.isFinite(value) && value >= min && value <= max ? value : fallback;
}

function sanitizedMetadata(
  redirect: { environment: string; origin: string },
  requestId: string,
): Record<string, string> {
  return {
    source: "admin-invite",
    environment: redirect.environment,
    redirect_origin: redirect.origin,
    request_id: requestId,
  };
}

function statusFor(code: string): number {
  if (code === "unauthorized") return 401;
  if (code === "forbidden" || code === "mfa_required") return 403;
  if (code === "auth_rate_limited" || code === "quota_rate_limited") return 429;
  if (code === "quota_unavailable" || code === "maintenance_mode") return 503;
  if ([
    "duplicate_ready",
    "duplicate_pending",
    "resend_cooldown",
    "membership_blocked",
    "onboarding_in_progress",
    "role_mismatch",
    "reconciliation_required",
  ].includes(code)) return 409;
  if (["invalid_email", "invalid_role", "invalid_json"].includes(code)) return 400;
  return 500;
}

class InviteError extends Error {
  constructor(public readonly code: string, message: string, public readonly retryAfter?: number) {
    super(message);
  }
}

function authEmailError(
  error: { message?: string; status?: number } | null,
  fallback: string,
  failureCode = "auth_invite_failed",
): InviteError {
  const message = error?.message || "";
  if (error?.status === 429) {
    return new InviteError("auth_rate_limited", "Auth email rate limit exceeded; retry later");
  }
  if (error?.status === 408 || error?.status === 425 || (error?.status !== undefined && error.status >= 500)) {
    return new InviteError("auth_delivery_unknown", "Auth delivery outcome requires reconciliation");
  }
  if (error?.status !== undefined && error.status >= 400 && error.status < 500) {
    return new InviteError(failureCode, fallback);
  }
  if (/rate limit|rate_limit|too many requests/i.test(message)) {
    return new InviteError("auth_delivery_unknown", "Auth delivery outcome requires reconciliation");
  }
  return new InviteError("auth_delivery_unknown", "Auth delivery outcome requires reconciliation");
}

async function findAuthUser(admin: SupabaseClient, email: string): Promise<AuthUser | null> {
  for (let page = 1; page <= 100; page += 1) {
    const { data, error } = await admin.auth.admin.listUsers({ page, perPage: 1000 });
    if (error) throw error;
    const users = (data.users || []) as AuthUser[];
    const user = users.find((candidate) => candidate.email?.trim().toLowerCase() === email);
    if (user) return user;
    if (users.length < 1000) return null;
  }
  throw new Error("auth_user_lookup_limit");
}

async function findMember(admin: SupabaseClient, userId: string): Promise<Member | null> {
  const { data, error } = await admin
    .from("admin_members")
    .select("user_id,role,is_active,account_status")
    .eq("user_id", userId)
    .maybeSingle();
  if (error) throw error;
  return (data as Member | null) || null;
}

async function findPending(admin: SupabaseClient, email: string): Promise<Invitation | null> {
  const { data, error } = await admin
    .from("admin_invitations")
    .select("id,status,expires_at,last_sent_at")
    .eq("email", email)
    .eq("status", "pending")
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) throw error;
  return (data as Invitation | null) || null;
}

async function findRequestInvitation(
  admin: SupabaseClient,
  actorId: string,
  requestId: string,
  email: string,
  role: Role,
): Promise<{
  id: string;
  status: string;
  userId: string | null;
  resent: boolean;
  reconciliationRequired: boolean;
  deliveryCompleted: boolean;
  recoverySent: boolean;
} | null> {
  const { data, error } = await admin
    .from("admin_invitations")
    .select("id,status,admin_member_user_id,resend_of_invitation_id,metadata")
    .eq("created_by_user_id", actorId)
    .eq("email", email)
    .eq("role", role)
    .filter("metadata->>request_id", "eq", requestId)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) throw error;
  if (!data) return null;
  const row = data as {
    id: string;
    status: string;
    admin_member_user_id?: string | null;
    resend_of_invitation_id?: string | null;
    metadata?: { reconciliation_required?: boolean; delivery_state?: string; delivery_method?: string } | null;
  };
  return {
    id: row.id,
    status: row.status,
    userId: row.admin_member_user_id || null,
    resent: Boolean(row.resend_of_invitation_id),
    reconciliationRequired: row.metadata?.reconciliation_required === true,
    deliveryCompleted: row.metadata?.delivery_state === "completed",
    recoverySent: row.metadata?.delivery_state === "completed" && row.metadata?.delivery_method === "recovery",
  };
}

async function authorize(admin: SupabaseClient, accessToken: string): Promise<string> {
  const { data, error } = await admin.auth.getUser(accessToken);
  if (error || !data.user?.id) throw new InviteError("unauthorized", "Unauthorized");
  const claims = decodeJwtPayload(accessToken);
  if (claims?.aal !== "aal2") throw new InviteError("mfa_required", "MFA aal2 required");

  const member = await findMember(admin, data.user.id);
  if (!member || member.role !== "admin" || !member.is_active || member.account_status !== "ready") {
    throw new InviteError("forbidden", "Not authorized");
  }
  return data.user.id;
}

async function sendAuthInvitation(
  admin: SupabaseClient,
  email: string,
  redirect: { url: string },
): Promise<AuthUser> {
  let result: Awaited<ReturnType<SupabaseClient["auth"]["admin"]["inviteUserByEmail"]>>;
  try {
    result = await admin.auth.admin.inviteUserByEmail(email, { redirectTo: redirect.url });
  } catch {
    throw new InviteError("auth_delivery_unknown", "Auth delivery outcome requires reconciliation");
  }
  const { data, error } = result;
  if (error) throw authEmailError(error, "Auth invitation failed");
  if (!data.user?.id) throw new InviteError("auth_delivery_unknown", "Auth delivery outcome requires reconciliation");
  return data.user as AuthUser;
}

async function sendAuthRecovery(
  admin: SupabaseClient,
  email: string,
  recoveryRedirect: { url: string },
): Promise<void> {
  let result: Awaited<ReturnType<SupabaseClient["auth"]["resetPasswordForEmail"]>>;
  try {
    result = await admin.auth.resetPasswordForEmail(email, { redirectTo: recoveryRedirect.url });
  } catch {
    throw new InviteError("auth_delivery_unknown", "Auth delivery outcome requires reconciliation");
  }
  const { error } = result;
  if (error) throw authEmailError(error, "Auth recovery email failed", "auth_recovery_failed");
}

async function reserveInvitation(
  admin: SupabaseClient,
  input: {
    email: string;
    role: Role;
    actorId: string;
    authUserId: string | null;
    resend: boolean;
    recovery?: boolean;
    requestId: string;
    redirect: { environment: string; origin: string };
  },
): Promise<ReserveRow> {
  const secret = Deno.env.get("ADMIN_QUOTA_HMAC_KEY") || "";
  if (secret.length < 32) throw new InviteError("quota_unavailable", "Quota unavailable", 30);
  const key = await crypto.subtle.importKey("raw",new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" },false,["sign"]);
  const signature = await crypto.subtle.sign("HMAC",key,new TextEncoder().encode(`invite-recipient:${input.email.trim().toLowerCase()}`));
  const recipient = Array.from(new Uint8Array(signature),byte=>byte.toString(16).padStart(2,"0")).join("");
  const cooldown = numberEnv("ADMIN_INVITE_RESEND_COOLDOWN_SECONDS", DEFAULT_RESEND_COOLDOWN_SECONDS, 0, 86400);
  const { data, error } = await admin.rpc("admin_invitation_reserve", {
    p_email: input.email,
    p_role: input.role,
    p_actor_user_id: input.actorId,
    p_auth_user_id: input.authUserId,
    p_resend: input.resend,
    p_request_id: input.requestId,
    p_metadata: { ...sanitizedMetadata(input.redirect, input.requestId), delivery_method: input.recovery ? "recovery" : "invite", quota_recipient: recipient },
    p_resend_cooldown_until: new Date(Date.now() - cooldown * 1000).toISOString(),
  });
  if (error?.code === "quota_rate_limited" || error?.code === "quota_unavailable") {
    const retry = Number(error.details);
    throw new InviteError(error.code, "Quota unavailable or exceeded", Number.isInteger(retry) && retry>=1 && retry<=86400 ? retry : 30);
  }
  if (error) throw new InviteError("persistence_failed", "Invitation reservation failed");
  const row = Array.isArray(data) ? data[0] : data;
  if (!row || typeof row !== "object") throw new InviteError("persistence_failed", "Invitation reservation failed");
  const result = row as ReserveRow;
  if (!result.success) throw new InviteError(result.error_code || "persistence_failed", "Invitation could not be reserved");
  return result;
}

async function completeInvitation(
  admin: SupabaseClient,
  invitationId: string,
  authUserId: string,
): Promise<void> {
  const { data, error } = await admin.rpc("admin_invitation_complete", {
    p_invitation_id: invitationId,
    p_auth_user_id: authUserId,
  });
  const row = Array.isArray(data) ? data[0] : data;
  if (error || !row || (row as { success?: boolean }).success !== true) {
    throw new InviteError("persistence_failed", "Invitation completion failed");
  }
}

async function failInvitation(
  admin: SupabaseClient,
  invitationId: string | null,
  authUserId: string | null,
  failureCode: string,
  input: { email: string; role: Role; actorId: string; requestId: string; redirect: { environment: string; origin: string } },
): Promise<void> {
  if (invitationId) {
    const { data, error } = await admin.rpc("admin_invitation_fail", {
      p_invitation_id: invitationId,
      p_auth_user_id: authUserId,
      p_failure_code: failureCode,
    });
    const row = Array.isArray(data) ? data[0] : data;
    if (error || !row || (row as { success?: boolean }).success !== true) {
      throw new InviteError("reconciliation_required", "Invitation failure requires reconciliation");
    }
    return;
  }

  const { data, error } = await admin.rpc("admin_invitation_record_failure", {
    p_email: input.email,
    p_role: input.role,
    p_actor_user_id: input.actorId,
    p_auth_user_id: authUserId,
    p_failure_code: failureCode,
    p_request_id: input.requestId,
    p_metadata: sanitizedMetadata(input.redirect, input.requestId),
  });
  const row = Array.isArray(data) ? data[0] : data;
  if (error || !row || (row as { success?: boolean }).success !== true) {
    throw new InviteError("reconciliation_required", "Invitation failure requires reconciliation");
  }
}

async function markInvitationDeliveryUnknown(
  admin: SupabaseClient,
  invitationId: string,
  authUserId: string | null,
  deliveryOutcome: "unknown" | "auth_accepted",
  failureCode: string,
): Promise<void> {
  const { data, error } = await admin.rpc("admin_invitation_mark_delivery_reconciliation", {
    p_invitation_id: invitationId,
    p_auth_user_id: authUserId,
    p_delivery_outcome: deliveryOutcome,
    p_failure_code: failureCode,
  });
  const row = Array.isArray(data) ? data[0] : data;
  if (error || !row || (row as { success?: boolean }).success !== true) {
    throw new InviteError("reconciliation_required", "Invitation delivery requires reconciliation");
  }
}

async function expireInvitation(
  admin: SupabaseClient,
  invitationId: string,
  actorId: string,
): Promise<void> {
  const { data, error } = await admin.rpc("admin_invitation_expire", {
    p_invitation_id: invitationId,
    p_actor_user_id: actorId,
  });
  const row = Array.isArray(data) ? data[0] : data;
  if (error || !row || (row as { success?: boolean }).success !== true) {
    throw new InviteError("reconciliation_required", "Expired invitation requires reconciliation");
  }
}

async function handleInvite(req: Request): Promise<Response> {
  const requestId = getRequestId(req);
  if (!isValidSupabaseConfiguration(SUPABASE_URL, SERVICE_KEY)) {
    return json({ error: "Server configuration incomplete", request_id: requestId }, 500, req);
  }

  const redirect = configuredRedirect();
  if (!redirect) return json({ error: "Invitation redirect is not configured", request_id: requestId }, 500, req);

  const accessToken = parseBearerToken(req.headers.get("Authorization") || "");
  if (!accessToken) return json({ error: "Missing access token", request_id: requestId }, 401, req);

  const admin = createClient(SUPABASE_URL, SERVICE_KEY, {
    global: { fetch: createApiKeyOnlyFetch(SERVICE_KEY) },
    auth: { autoRefreshToken: false, persistSession: false },
  });
  let actorId = "";
  try {
    actorId = await authorize(admin, accessToken);
  } catch (error) {
    const failure = error instanceof InviteError
      ? error
      : new InviteError("unauthorized", "Unauthorized");
    return json({ error: failure.message, code: failure.code, request_id: requestId }, statusFor(failure.code), req);
  }

  // A separate committed admission RPC counts all authenticated Edge attempts,
  // including replay and business rejection, before scans/body processing/writes.
  const { data: admitted, error: admissionError } = await admin.rpc("admin_invitation_request_admit", { p_actor_user_id: actorId });
  if (admissionError || admitted !== true) {
    const limited = admissionError?.code === "quota_rate_limited";
    const response = json({ error: "Quota unavailable or exceeded", code: limited ? "quota_rate_limited" : "quota_unavailable", request_id: requestId },limited ? 429 : 503,req);
    const retry=Number(admissionError?.details);
    response.headers.set("Retry-After",String(Number.isInteger(retry) && retry>=1 && retry<=86400 ? retry : 30));
    return response;
  }

  const parsedBody = await readInvitePayload(req);
  if (!parsedBody.ok) {
    const message = parsedBody.code === "body_too_large" ? "Request body is too large" : "Invalid JSON body";
    return json({ error: message, code: parsedBody.code, request_id: requestId }, parsedBody.status, req);
  }
  const payload = parsedBody.payload;
  const email = parseEmail(payload.email);
  const role = parseRole(payload.role);
  const resend = parseBoolean(payload.resend);
  if (!EMAIL_RE.test(email)) return json({ error: "Invalid email", code: "invalid_email", request_id: requestId }, 400, req);
  if (!role) return json({ error: "Invalid role: must be admin or user", code: "invalid_role", request_id: requestId }, 400, req);
  if (payload.resend !== undefined && typeof payload.resend !== "boolean") {
    return json({ error: "Invalid resend flag", code: "invalid_request", request_id: requestId }, 400, req);
  }

  let authUserId: string | null = null;
  let invitationId: string | null = null;
  let authCallSucceeded = false;

  try {
    const requestInvitation = await findRequestInvitation(admin, actorId, requestId, email, role);
    if (requestInvitation) {
      if (
        requestInvitation.status === "send_failed"
        || requestInvitation.reconciliationRequired
        || !requestInvitation.deliveryCompleted
      ) {
        throw new InviteError("reconciliation_required", "Invitation requires reconciliation");
      }
      if (!requestInvitation.userId) {
        throw new InviteError("reconciliation_required", "Invitation requires reconciliation");
      }
      return json({
        success: true,
        email,
        user_id: requestInvitation.userId,
        invitation_id: requestInvitation.id,
        status: requestInvitation.status,
        resent: requestInvitation.resent,
        recovery_sent: requestInvitation.recoverySent,
      }, 200, req);
    }

    if (Deno.env.get("ADMIN_INVITE_SAFE_SUSPEND") === "true") {
      throw new InviteError("maintenance_mode", "Administration temporarily unavailable", 60);
    }
    if ((Deno.env.get("ADMIN_QUOTA_HMAC_KEY") || "").length < 32) {
      throw new InviteError("quota_unavailable", "Quota unavailable", 30);
    }
    const existingAuthUser = await findAuthUser(admin, email);
    const existingMember = existingAuthUser ? await findMember(admin, existingAuthUser.id) : null;
    const pending = await findPending(admin, email);

    if (pending && new Date(pending.expires_at).getTime() <= Date.now()) {
      await expireInvitation(admin, pending.id, actorId);
    }
    const livePending = pending && new Date(pending.expires_at).getTime() > Date.now() ? pending : null;

    if (existingMember?.account_status === "ready") throw new InviteError("duplicate_ready", "User already has a ready membership");
    if (existingMember && ["inactive", "revoked"].includes(existingMember.account_status)) {
      throw new InviteError("membership_blocked", "User membership is inactive or revoked");
    }
    if (existingMember && existingMember.account_status !== "invited") {
      throw new InviteError("onboarding_in_progress", "User onboarding is already in progress");
    }
    // admin_members.user_id REFERENCES auth.users(id) ON DELETE CASCADE, so a
    // missing Auth identity cannot retain a live membership. Keep the explicit
    // member check as a defense-in-depth invariant for this transition.
    const orphanedPendingReinvite = Boolean(livePending && !existingAuthUser && !existingMember && !resend);
    if (livePending && !resend && !orphanedPendingReinvite) {
      throw new InviteError("duplicate_pending", "Invitation already pending");
    }
    if (livePending && (resend || orphanedPendingReinvite)) {
      const cooldown = numberEnv("ADMIN_INVITE_RESEND_COOLDOWN_SECONDS", DEFAULT_RESEND_COOLDOWN_SECONDS, 0, 86400);
      if (Date.now() - new Date(livePending.last_sent_at).getTime() < cooldown * 1000) {
        throw new InviteError("resend_cooldown", "Invitation resend is temporarily unavailable");
      }
    }
    if (existingMember && existingMember.role !== role) {
      throw new InviteError("role_mismatch", "Existing membership role must be managed separately");
    }

    const confirmedResend = Boolean(
      livePending &&
      resend &&
      (existingAuthUser?.email_confirmed_at || existingAuthUser?.confirmed_at) &&
      existingMember?.account_status === "invited",
    );

    try {
      if (confirmedResend) {
        const recoveryRedirect = configuredRecoveryRedirect();
        if (!recoveryRedirect) throw new InviteError("reconciliation_required", "Invitation recovery redirect is not configured");
        authUserId = existingAuthUser?.id || null;
        if (!authUserId) throw new InviteError("reconciliation_required", "Confirmed Auth identity requires reconciliation");
        const reserved = await reserveInvitation(admin, {
          email,
          role,
          actorId,
          authUserId,
          resend: true,
          recovery: true,
          requestId,
          redirect,
        });
        invitationId = reserved.invitation_id;
        if (!invitationId) throw new InviteError("persistence_failed", "Invitation reservation failed");
        await sendAuthRecovery(admin, email, recoveryRedirect);
        authCallSucceeded = true;
        await completeInvitation(admin, invitationId, authUserId);
        return json({
          success: true,
          email,
          user_id: authUserId,
          invitation_id: invitationId,
          status: "pending",
          resent: reserved.resent,
          recovery_sent: true,
        }, 200, req);
      } else {
        if (existingAuthUser?.email_confirmed_at || existingAuthUser?.confirmed_at) {
          throw new InviteError("reconciliation_required", "Confirmed Auth identity requires reconciliation");
        }
        const reserved = await reserveInvitation(admin, {
          email,
          role,
          actorId,
          authUserId: existingAuthUser?.id || null,
          resend: Boolean(livePending && (resend || orphanedPendingReinvite)),
          requestId,
          redirect,
        });
        invitationId = reserved.invitation_id;
        if (!invitationId) throw new InviteError("persistence_failed", "Invitation reservation failed");
        const authUser = await sendAuthInvitation(admin, email, redirect);
        authCallSucceeded = true;
        authUserId = authUser.id;
        if (existingAuthUser && existingAuthUser.id !== authUserId) {
          throw new InviteError("reconciliation_required", "Auth identity changed during invitation");
        }
        await completeInvitation(admin, invitationId, authUserId);
        return json({
          success: true,
          email,
          user_id: authUserId,
          invitation_id: invitationId,
          status: "pending",
          resent: reserved.resent,
          recovery_sent: false,
        }, 200, req);
      }
    } catch (error) {
      const failureCode = error instanceof InviteError && error.code !== "persistence_failed"
        ? error.code
        : "persistence_failed";
      if (failureCode === "auth_delivery_unknown" || authCallSucceeded) {
        if (!invitationId) {
          throw new InviteError("reconciliation_required", "Invitation delivery requires reconciliation");
        }
        try {
          await markInvitationDeliveryUnknown(
            admin,
            invitationId,
            authUserId,
            authCallSucceeded ? "auth_accepted" : "unknown",
            authCallSucceeded ? "invitation_completion_failed" : "auth_delivery_unknown",
          );
        } catch {
          throw new InviteError("reconciliation_required", "Invitation delivery requires reconciliation");
        }
        throw new InviteError("reconciliation_required", "Auth delivery outcome requires reconciliation");
      }
      const expectedBusinessError = [
        "quota_rate_limited",
        "quota_unavailable",
        "duplicate_pending",
        "resend_cooldown",
        "duplicate_ready",
        "membership_blocked",
        "onboarding_in_progress",
        "role_mismatch",
        "reconciliation_required",
      ].includes(failureCode);
      if (expectedBusinessError) throw error;
      try {
        await failInvitation(admin, invitationId, authUserId, failureCode, {
          email,
          role,
          actorId,
          requestId,
          redirect,
        });
      } catch {
        throw new InviteError("reconciliation_required", "Invitation requires reconciliation");
      }
      const authFailure = failureCode === "auth_invite_failed"
        || failureCode === "auth_recovery_failed"
        || failureCode === "auth_rate_limited";
      throw new InviteError(
        authFailure ? failureCode : "reconciliation_required",
        authFailure
          ? (failureCode === "auth_rate_limited"
            ? "Auth email rate limit exceeded; retry later"
            : failureCode === "auth_recovery_failed" ? "Auth recovery email failed" : "Auth invitation failed")
          : "Invitation requires reconciliation",
      );
    }
  } catch (error) {
    const failure = error instanceof InviteError ? error : new InviteError("internal_error", "Invitation could not be completed");
    console.error("admin-invite failed", { code: failure.code, request_id: requestId });
    const response = json({ error: failure.message, code: failure.code, request_id: requestId }, statusFor(failure.code), req);
    if (failure.retryAfter) response.headers.set("Retry-After",String(failure.retryAfter));
    return response;
  }
}

Deno.serve(async (req: Request): Promise<Response> => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders(req) });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405, req);
  return handleInvite(req);
});
