import { routeAdminBff, type AdminBffContext } from './_lib/admin-bff';

type MiddlewareContext = AdminBffContext;

const PUBLIC_HOSTS = new Set(["studiamatch.com", "www.studiamatch.com"]);
const SLASH_REDIRECT_PATHS = new Set(["/admin", "/admin/login", "/admin/edit", "/admin/users", "/admin/auth/callback", "/admin/accept-invite", "/admin/setup-password", "/admin/reset-password"]);

function isAdminPath(pathname: string): boolean {
  return pathname === "/admin" || pathname.startsWith("/admin/");
}

function isAdminApiPath(pathname: string): boolean {
  return pathname === "/api/admin" || pathname.startsWith("/api/admin/");
}

function isAdminNamespacePath(pathname: string): boolean {
  const withSeparators = pathname.replace(/\\/g, "/").replace(/\/{2,}/g, "/");
  const trailingSlash = withSeparators.endsWith("/");
  const segments: string[] = [];
  for (const segment of withSeparators.split("/")) {
    if (!segment || segment === ".") continue;
    if (segment === "..") segments.pop();
    else segments.push(segment);
  }
  const normalized = `/${segments.join("/")}${trailingSlash && segments.length ? "/" : ""}`;
  return isAdminPath(normalized) || isAdminApiPath(normalized);
}

function isEncodedAdminPath(pathname: string): boolean {
  const canonical = pathname.replace(/\\/g, "/").replace(/\/{2,}/g, "/");
  if (pathname !== canonical && isAdminNamespacePath(pathname)) return true;
  let candidate = pathname;
  for (let pass = 0; pass < 4; pass += 1) {
    let decoded: string;
    try {
      decoded = decodeURIComponent(candidate);
    } catch {
      return isAdminNamespacePath(candidate) || candidate.includes("%");
    }
    if (decoded === candidate) return false;
    if (isAdminNamespacePath(decoded)) return true;
    candidate = decoded;
  }
  // A still-encoded path may become an Admin alias after another intermediary
  // decode. Reject it instead of handing it to Pages' static asset fallback.
  return candidate.includes("%") || isAdminNamespacePath(candidate);
}

function isLocalhost(hostname: string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1";
}

function parseAllowedHosts(raw: string | undefined): Set<string> {
  return new Set(
    (raw || "")
      .split(",")
      .map((item) => item.trim().toLowerCase())
      .filter(Boolean)
  );
}

export async function onRequest(context: MiddlewareContext): Promise<Response> {
  const url = new URL(context.request.url);
  const hostname = url.hostname.toLowerCase();
  const pathname = url.pathname;

  // Do not let Pages/static asset routing decode an Admin alias after the
  // hostname and safe-suspend checks have already been bypassed.
  if (isEncodedAdminPath(pathname)) {
    return new Response("Not found", {
      status: 404,
      headers: {
        "Content-Type": "text/plain",
        "Cache-Control": "private, no-store, max-age=0",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
      },
    });
  }

  const isAdminApi = isAdminApiPath(pathname);
  const isAdminCallback = pathname === "/admin/auth/callback" || pathname === "/admin/auth/callback/";
  if (!isAdminPath(pathname) && !isAdminApi) {
    return context.next();
  }

  const isPublicHost = PUBLIC_HOSTS.has(hostname);
  const allowedHosts = parseAllowedHosts(context.env.ADMIN_ALLOWED_HOSTS);
  const isExplicitLocalhost = context.env.ADMIN_BFF_ALLOW_LOCALHOST === "true" && isLocalhost(hostname);
  const isAllowedHost = allowedHosts.has(hostname) || isExplicitLocalhost;
  const isAllowedBffHost = isAllowedHost;

  if (isPublicHost || (isAdminApi || isAdminCallback ? !isAllowedBffHost : !isAllowedHost)) {
    return new Response("Not found", {
      status: 404,
      headers: {
        "Content-Type": "text/plain",
        "Cache-Control": "private, no-store, max-age=0",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
      },
    });
  }

  // Compensating rollback target: KEEP this hardened artifact, do not restore a
  // legacy token-in-JS build. Suspend Admin, clear session cookies, keep public
  // static pages available. Remote flag changes retain their own approval gate.
  if (context.env.ADMIN_BFF_SAFE_SUSPEND === 'true') {
    const headers=new Headers({
      'Content-Type':'text/plain; charset=utf-8','Cache-Control':'private, no-store',
      'Referrer-Policy':'no-referrer','Retry-After':'60','X-Content-Type-Options':'nosniff',
    });
    const names=new Set(['__Host-studiamatch-admin-auth','__Host-studiamatch-admin-auth-code-verifier','__Host-studiamatch-admin-activity','__Host-studiamatch-admin-callback-csrf']);
    for(const part of (context.request.headers.get('Cookie') || '').split(';')) {
      const name=part.trim().split('=')[0];
      if(/^__Host-studiamatch-admin-auth(?:-code-verifier)?\.\d{1,3}$/.test(name) && names.size<64) names.add(name);
    }
    for(const name of names) headers.append('Set-Cookie',`${name}=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Lax`);
    return new Response('Administración temporalmente en mantenimiento.',{status:503,headers});
  }

  const bffResponse = await routeAdminBff(context);
  if (bffResponse) return bffResponse;

  if (SLASH_REDIRECT_PATHS.has(pathname)) {
    return new Response(null, {
      status: 302,
      headers: { Location: `${pathname}/${url.search}` },
    });
  }

  return context.next();
}
