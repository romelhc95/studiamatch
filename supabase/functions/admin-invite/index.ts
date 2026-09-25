import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient, type SupabaseClient } from "npm:@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "";
const SERVICE_KEY = Deno.env.get("NEXT_SUPABASE_SECRET_KEY") || "";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const BEARER_PREFIX = "Bear" + "er ";
const DEFAULT_RESEND_COOLDOWN_SECONDS = 60;

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
  const allowedOrigins = (Deno.env.get("ADMIN_INVITE_ALLOWED_ORIGINS") || "")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
  return {
    "Access-Control-Allow-Origin": origin && allowedOrigins.includes(origin) ? origin : "null",
    "Vary": "Origin",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-request-id",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };
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
  const url = Deno.env.get("ADMIN_INVITE_REDIRECT_URL")?.trim() || "";
  const allowed = (Deno.env.get("ADMIN_INVITE_ALLOWED_REDIRECTS") || "")
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
  if (!url || !allowed.includes(url)) return null;

  try {
    const parsed = new URL(url);
    if ((parsed.protocol !== "https:" && parsed.hostname !== "localhost") || parsed.username || parsed.password || parsed.hash) {
      return null;
    }
    return {
      url,
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
  constructor(public readonly code: string, message: string) {
    super(message);
  }
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
): Promise<{ id: string; status: string; userId: string | null; resent: boolean } | null> {
  const { data, error } = await admin
    .from("admin_invitations")
    .select("id,status,admin_member_user_id,resend_of_invitation_id")
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
  };
  return {
    id: row.id,
    status: row.status,
    userId: row.admin_member_user_id || null,
    resent: Boolean(row.resend_of_invitation_id),
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
  const { data, error } = await admin.auth.admin.inviteUserByEmail(email, { redirectTo: redirect.url });
  if (error || !data.user?.id) throw new InviteError("auth_invite_failed", "Auth invitation failed");
  return data.user as AuthUser;
}

async function reserveInvitation(
  admin: SupabaseClient,
  input: {
    email: string;
    role: Role;
    actorId: string;
    authUserId: string | null;
    resend: boolean;
    requestId: string;
    redirect: { environment: string; origin: string };
  },
): Promise<ReserveRow> {
  const cooldown = numberEnv("ADMIN_INVITE_RESEND_COOLDOWN_SECONDS", DEFAULT_RESEND_COOLDOWN_SECONDS, 0, 86400);
  const { data, error } = await admin.rpc("admin_invitation_reserve", {
    p_email: input.email,
    p_role: input.role,
    p_actor_user_id: input.actorId,
    p_auth_user_id: input.authUserId,
    p_resend: input.resend,
    p_request_id: input.requestId,
    p_metadata: sanitizedMetadata(input.redirect, input.requestId),
    p_resend_cooldown_until: new Date(Date.now() - cooldown * 1000).toISOString(),
  });
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

async function handleInvite(req: Request): Promise<Response> {
  const requestId = getRequestId(req);
  if (!SUPABASE_URL || !SERVICE_KEY) return json({ error: "Server configuration incomplete", request_id: requestId }, 500);

  const redirect = configuredRedirect();
  if (!redirect) return json({ error: "Invitation redirect is not configured", request_id: requestId }, 500);

  const accessToken = parseBearerToken(req.headers.get("Authorization") || "");
  if (!accessToken) return json({ error: "Missing access token", request_id: requestId }, 401);

  let payload: InvitePayload;
  try {
    payload = await req.json() as InvitePayload;
  } catch {
    return json({ error: "Invalid JSON body", code: "invalid_json", request_id: requestId }, 400);
  }

  const email = parseEmail(payload.email);
  const role = parseRole(payload.role);
  const resend = parseBoolean(payload.resend);
  if (!EMAIL_RE.test(email)) return json({ error: "Invalid email", code: "invalid_email", request_id: requestId }, 400);
  if (!role) return json({ error: "Invalid role: must be admin or user", code: "invalid_role", request_id: requestId }, 400);

  const admin = createClient(SUPABASE_URL, SERVICE_KEY, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
  let actorId = "";
  let authUserId: string | null = null;
  let invitationId: string | null = null;

  try {
    actorId = await authorize(admin, accessToken);
    const requestInvitation = await findRequestInvitation(admin, actorId, requestId, email, role);
    if (requestInvitation) {
      if (requestInvitation.status === "send_failed") {
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
      }, 200, req);
    }

    const existingAuthUser = await findAuthUser(admin, email);
    const existingMember = existingAuthUser ? await findMember(admin, existingAuthUser.id) : null;
    const pending = await findPending(admin, email);

    if (pending && new Date(pending.expires_at).getTime() <= Date.now()) {
      await admin.from("admin_invitations").update({ status: "expired" }).eq("id", pending.id).eq("status", "pending");
    }
    const livePending = pending && new Date(pending.expires_at).getTime() > Date.now() ? pending : null;

    if (existingMember?.account_status === "ready") throw new InviteError("duplicate_ready", "User already has a ready membership");
    if (existingMember && ["inactive", "revoked"].includes(existingMember.account_status)) {
      throw new InviteError("membership_blocked", "User membership is inactive or revoked");
    }
    if (existingMember && existingMember.account_status !== "invited") {
      throw new InviteError("onboarding_in_progress", "User onboarding is already in progress");
    }
    if (livePending && !resend) throw new InviteError("duplicate_pending", "Invitation already pending");
    if (livePending && resend) {
      const cooldown = numberEnv("ADMIN_INVITE_RESEND_COOLDOWN_SECONDS", DEFAULT_RESEND_COOLDOWN_SECONDS, 0, 86400);
      if (Date.now() - new Date(livePending.last_sent_at).getTime() < cooldown * 1000) {
        throw new InviteError("resend_cooldown", "Invitation resend is temporarily unavailable");
      }
    }
    if (existingAuthUser?.email_confirmed_at || existingAuthUser?.confirmed_at) {
      throw new InviteError("reconciliation_required", "Confirmed Auth identity requires reconciliation");
    }
    if (existingMember && existingMember.role !== role) {
      throw new InviteError("role_mismatch", "Existing membership role must be managed separately");
    }

    try {
      const authUser = await sendAuthInvitation(admin, email, redirect);
      authUserId = authUser.id;
      if (existingAuthUser && existingAuthUser.id !== authUserId) {
        throw new InviteError("reconciliation_required", "Auth identity changed during invitation");
      }

      const reserved = await reserveInvitation(admin, {
        email,
        role,
        actorId,
        authUserId: existingAuthUser?.id || null,
        resend: Boolean(livePending && resend),
        requestId,
        redirect,
      });
      invitationId = reserved.invitation_id;
      if (!invitationId) throw new InviteError("persistence_failed", "Invitation reservation failed");
      await completeInvitation(admin, invitationId, authUserId);
      return json({
        success: true,
        email,
        user_id: authUserId,
        invitation_id: invitationId,
        status: "pending",
        resent: reserved.resent,
      });
    } catch (error) {
      const failureCode = error instanceof InviteError && error.code !== "persistence_failed"
        ? error.code
        : "persistence_failed";
      const expectedBusinessError = [
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
      throw new InviteError(
        failureCode === "auth_invite_failed" ? "auth_invite_failed" : "reconciliation_required",
        failureCode === "auth_invite_failed" ? "Auth invitation failed" : "Invitation requires reconciliation",
      );
    }
  } catch (error) {
    const failure = error instanceof InviteError ? error : new InviteError("internal_error", "Invitation could not be completed");
    if (actorId && failure.code === "auth_invite_failed") {
      try {
        await failInvitation(admin, null, authUserId, "auth_invite_failed", {
          email,
          role,
          actorId,
          requestId,
          redirect,
        });
      } catch {
        // Preserve a sanitized response; reconciliation remains required if recording fails.
      }
    }
    console.error("admin-invite failed", { code: failure.code, request_id: requestId });
    return json({ error: failure.message, code: failure.code, request_id: requestId }, statusFor(failure.code), req);
  }
}

Deno.serve(async (req: Request): Promise<Response> => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders(req) });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405, req);
  return handleInvite(req);
});
