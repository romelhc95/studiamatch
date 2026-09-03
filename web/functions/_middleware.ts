interface MiddlewareContext {
  request: Request;
  env: Record<string, string | undefined>;
  next: () => Promise<Response>;
}

const PUBLIC_HOSTS = new Set(["studiamatch.com", "www.studiamatch.com"]);
const SLASH_REDIRECT_PATHS = new Set(["/admin", "/admin/login", "/admin/edit", "/admin/users"]);

function isAdminPath(pathname: string): boolean {
  return pathname === "/admin" || pathname.startsWith("/admin/");
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

  if (!isAdminPath(pathname)) {
    return context.next();
  }

  const isPublicHost = PUBLIC_HOSTS.has(hostname);
  const allowedHosts = parseAllowedHosts(context.env.ADMIN_ALLOWED_HOSTS);
  const isAllowedHost = allowedHosts.size > 0 ? allowedHosts.has(hostname) : !isPublicHost;

  if (isPublicHost || !isAllowedHost) {
    return new Response("Not found", {
      status: 404,
      headers: { "Content-Type": "text/plain" },
    });
  }

  if (SLASH_REDIRECT_PATHS.has(pathname)) {
    return new Response(null, {
      status: 302,
      headers: { Location: `${pathname}/` },
    });
  }

  return context.next();
}