// StudIAMatch-Docs: .context/componentes/supabase_transport.md#contrato-api-key-y-sesion
/**
 * supabase-js falls back to the supplied API key as an Authorization token
 * when no user session exists. Modern Supabase API keys belong only in
 * `apikey`; preserve real user-session JWTs used by the Admin BFF.
 */
export interface ServerSessionTransportPolicy {
  projectOrigin: string;
  rpcAllowlist: ReadonlySet<string>;
  rpcGateway?: {
    projectRef: string;
    keyId: string;
    hmacKey: string;
  };
}

const RPC_SIGNATURE_HEADERS = {
  keyId: 'x-studiamatch-admin-rpc-key-id',
  actor: 'x-studiamatch-admin-rpc-actor',
  issuedAt: 'x-studiamatch-admin-rpc-issued-at',
  nonce: 'x-studiamatch-admin-rpc-nonce',
  signature: 'x-studiamatch-admin-rpc-signature',
  payloadSignature: 'x-studiamatch-admin-rpc-payload-signature',
} as const;

const SIGNED_ADMIN_RPC = 'admin_signed_rpc';

function subjectFromJwt(token: string): string {
  const payload = token.split('.')[1];
  if (!payload) throw new Error('Supabase session token is invalid.');
  const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
  const binary = atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, '='));
  const bytes = Uint8Array.from(binary, character => character.charCodeAt(0));
  const claims = JSON.parse(new TextDecoder().decode(bytes)) as { sub?: unknown };
  if (typeof claims.sub !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(claims.sub)) {
    throw new Error('Supabase session subject is invalid.');
  }
  return claims.sub.toLowerCase();
}

async function signAdminRpc(
  headers: Headers,
  url: URL,
  method: string,
  targetRpcName: string,
  token: string,
  gateway: NonNullable<ServerSessionTransportPolicy['rpcGateway']> | undefined,
  args: Record<string, unknown>,
): Promise<string> {
  if (!gateway || new TextEncoder().encode(gateway.hmacKey).byteLength < 32
    || !/^[a-z0-9-]{1,64}$/.test(gateway.projectRef)
    || !/^[A-Za-z0-9._-]{1,32}$/.test(gateway.keyId)) {
    throw new Error('Admin RPC gateway is not configured.');
  }
  const projectHostMatches = gateway.projectRef === 'local'
    ? ['localhost', '127.0.0.1'].includes(url.hostname)
    : url.hostname === `${gateway.projectRef}.supabase.co`;
  if (!projectHostMatches) throw new Error('Admin RPC gateway project is invalid.');

  const actor = subjectFromJwt(token);
  const issuedAt = String(Math.floor(Date.now() / 1000));
  const nonce = crypto.randomUUID();
  const signedPayload = JSON.stringify(args);
  if (new TextEncoder().encode(signedPayload).byteLength > 64 * 1024) {
    throw new Error('Admin RPC payload is too large.');
  }
  const canonical = [
    'studiamatch-admin-rpc-v1', gateway.projectRef, method, SIGNED_ADMIN_RPC, actor, issuedAt, nonce, gateway.keyId,
  ].join('\n');
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(gateway.hmacKey), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'],
  );
  const payloadCanonical = [
    'studiamatch-admin-rpc-payload-v1', gateway.projectRef, method, SIGNED_ADMIN_RPC,
    targetRpcName, actor, issuedAt, nonce, gateway.keyId, signedPayload,
  ].join('\n');
  const [signature, payloadSignature] = await Promise.all([
    crypto.subtle.sign('HMAC', key, new TextEncoder().encode(canonical)),
    crypto.subtle.sign('HMAC', key, new TextEncoder().encode(payloadCanonical)),
  ]);
  const toHex = (value: ArrayBuffer) => Array.from(new Uint8Array(value), byte => byte.toString(16).padStart(2, '0')).join('');
  headers.set(RPC_SIGNATURE_HEADERS.keyId, gateway.keyId);
  headers.set(RPC_SIGNATURE_HEADERS.actor, actor);
  headers.set(RPC_SIGNATURE_HEADERS.issuedAt, issuedAt);
  headers.set(RPC_SIGNATURE_HEADERS.nonce, nonce);
  headers.set(RPC_SIGNATURE_HEADERS.signature, toHex(signature));
  headers.set(RPC_SIGNATURE_HEADERS.payloadSignature, toHex(payloadSignature));
  return JSON.stringify({ p_rpc_name: targetRpcName, p_args: args, p_signed_payload: signedPayload });
}

function sessionDestinationAllowed(url: URL, method: string, policy: ServerSessionTransportPolicy): boolean {
  if (url.origin !== policy.projectOrigin || url.username || url.password || url.hash) return false;
  const path = url.pathname;
  const rpc = /^\/rest\/v1\/rpc\/([a-z][a-z0-9_]*)$/.exec(path);
  if (rpc) return method === 'POST' && policy.rpcAllowlist.has(rpc[1]);
  if (path === '/auth/v1/user') return method === 'GET' || method === 'PUT';
  if (path === '/auth/v1/factors') return method === 'POST';
  if (path === '/functions/v1/admin-invite') return method === 'POST';
  const factor = /^\/auth\/v1\/factors\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?:\/(challenge|verify))?$/.exec(path);
  return Boolean(factor && (factor[1] ? method === 'POST' : method === 'DELETE'));
}

export function createApiKeyOnlyFetch(
  apiKey: string,
  fetcher: typeof fetch,
  policy?: ServerSessionTransportPolicy,
): typeof fetch {
  const apiKeyBearerPrefix = 'Bear' + 'er ';

  return async (input, init) => {
    const headers = new Headers(input instanceof Request ? input.headers : undefined);
    new Headers(init?.headers).forEach((value, name) => headers.set(name, value));
    for (const name of Object.values(RPC_SIGNATURE_HEADERS)) headers.delete(name);

    const url = new URL(input instanceof Request ? input.url : String(input));
    if (policy && (url.origin !== policy.projectOrigin || url.username || url.password || url.hash)) {
      throw new Error('Supabase transport destination is not allowed.');
    }
    const authorization = headers.get('authorization');
    const method = (init?.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
    let fetchInput: RequestInfo | URL = input;
    let fetchInit: RequestInit = { ...init, headers, redirect: 'manual' };
    if (authorization === `${apiKeyBearerPrefix}${apiKey}`) {
      headers.delete('authorization');
    } else if (authorization) {
      // Shape is a transport guard, NOT signature/identity verification. Auth/RLS
      // remain responsible for verifying the JWT and authorizing the operation.
      const token = authorization.startsWith(apiKeyBearerPrefix) ? authorization.slice(apiKeyBearerPrefix.length) : '';
      if (!policy || !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(token)
        || !sessionDestinationAllowed(url, method, policy)) {
        throw new Error('Supabase session transport is not allowed.');
      }
      const rpc = /^\/rest\/v1\/rpc\/([a-z][a-z0-9_]*)$/.exec(url.pathname);
      if (rpc) {
        let rawBody: string;
        if (typeof init?.body === 'string') {
          rawBody = init.body;
        } else if (input instanceof Request) {
          rawBody = await input.clone().text();
        } else {
          throw new Error('Admin RPC payload is missing.');
        }
        let args: unknown;
        try {
          args = JSON.parse(rawBody);
        } catch {
          throw new Error('Admin RPC payload is invalid.');
        }
        if (!args || typeof args !== 'object' || Array.isArray(args)) {
          throw new Error('Admin RPC payload is invalid.');
        }
        const signedBody = await signAdminRpc(
          headers, url, method, rpc[1], token, policy.rpcGateway, args as Record<string, unknown>,
        );
        url.pathname = url.pathname.replace(/\/rpc\/[a-z][a-z0-9_]*$/, `/rpc/${SIGNED_ADMIN_RPC}`);
        fetchInput = url.toString();
        fetchInit = { ...fetchInit, method, body: signedBody };
      }
    }
    // workerd does not support redirect:error. Manual + explicit rejection keeps
    // the same no-follow security contract on browsers, Deno and Cloudflare.
    const response = await fetcher(fetchInput, fetchInit);
    if ((response.status >= 300 && response.status < 400) || response.type === 'opaqueredirect') {
      throw new Error('Supabase redirects are not allowed.');
    }
    return response;
  };
}
