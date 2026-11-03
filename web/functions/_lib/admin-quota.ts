export interface QuotaBinding {
  fetch(input: Request): Promise<Response>;
}
export interface QuotaEnv {
  ADMIN_QUOTA?: QuotaBinding;
  ADMIN_QUOTA_HMAC_KEY?: string;
}
export type QuotaKind = 'entry' | 'login-ip' | 'login-account-ip' | 'callback' | 'mfa' | 'password' | 'rpc-read' | 'rpc-write';
type QuotaKey =
  | { kind: 'login-account-ip'; identity: string; shardIdentity: string }
  | { kind: Exclude<QuotaKind, 'login-account-ip'>; identity: string; shardIdentity?: never };

export async function checkAdminQuota(
  request: Request, env: QuotaEnv, keys: QuotaKey[],
): Promise<Response | null> {
  try {
    if (!env.ADMIN_QUOTA || !env.ADMIN_QUOTA_HMAC_KEY || env.ADMIN_QUOTA_HMAC_KEY.length < 32) throw new Error('quota unavailable');
    const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(env.ADMIN_QUOTA_HMAC_KEY),
      { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
    const counters = await Promise.all(keys.map(async ({ kind, identity, ...options }) => {
      const [signed, signedShard] = await Promise.all([
        crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`${kind}:${identity}`)),
        options.shardIdentity
          ? crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`login-ip:${options.shardIdentity}`))
          : Promise.resolve(null),
      ]);
      const digest = Array.from(new Uint8Array(signed), byte => byte.toString(16).padStart(2, '0')).join('');
      const shard = signedShard
        ? Array.from(new Uint8Array(signedShard), byte => byte.toString(16).padStart(2, '0')).join('')
        : undefined;
      return { kind, digest, ...(shard ? { shard } : {}) };
    }));
    const response = await env.ADMIN_QUOTA.fetch(new Request('https://admin-quota.internal/check', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ counters }),
    }));
    if (response.status === 200) {
      const payload = await response.json() as { allowed?: unknown };
      if (payload.allowed === true) return null;
    }
    if (response.status === 429) {
      const retry = Number(response.headers.get('Retry-After'));
      if (Number.isInteger(retry) && retry >= 1 && retry <= 86400) return failure(429, 'rate_limited', retry);
    }
  } catch { /* Never leak identity, upstream failure or key. */ }
  return failure(503, 'quota_unavailable', 30);
}

export function trustedQuotaIp(request: Request): string | null {
  // Runtime strips/replaces this header at Cloudflare ingress. Do not use XFF.
  const ip = request.headers.get('CF-Connecting-IP')?.trim();
  if (!ip || ip.length > 45) return null;
  if (/^(?:\d{1,3}\.){3}\d{1,3}$/.test(ip) && ip.split('.').every(part => Number(part) <= 255)) return ip;
  if (ip.includes(':') && /^[0-9a-f:]+$/i.test(ip)) return ip.toLowerCase();
  return null;
}

function failure(status: number, code: string, retry: number): Response {
  return new Response(JSON.stringify({ error: { code } }), { status, headers: {
    'Content-Type': 'application/json', 'Cache-Control': 'private, no-store',
    'Referrer-Policy': 'no-referrer', 'Retry-After': String(retry),
  } });
}
