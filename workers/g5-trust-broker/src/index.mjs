const VERSION = "f10.9-g5-trust-broker.v2";
const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "studiamatch-f10-9-g5-production-trust-plane";
const MAIN_REF = "refs/heads/main";
const ENVIRONMENT = "Production";
const REPOSITORY = "romelhc95/studiamatch";
const WORKFLOW_PATH = ".github/workflows/g5-manual-trust-gate.yml";
const WORKFLOW_NAME = "F10.9 G5 Production Read-Only Diagnostic";
const WORKFLOW_REF = `${REPOSITORY}/${WORKFLOW_PATH}@${MAIN_REF}`;
const MAIN_BRANCH = "main";
const CONNECTED_DISABLED = "IMPLEMENTED_DISABLED_NOT_CONFIGURED";
const CONNECTED_STOP = CONNECTED_DISABLED;
const TRUST_STOP = "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED";
const CONFIG_STOP = "STOP_G5_CONNECTED_MODE_DISABLED_NOT_CONFIGURED";
const RUNTIME_ENABLED_CONFIG_NAME = "G5_TRUST_RUNTIME_ENABLED";
const GITHUB_API_BASE = "https://api.github.com";
const GITHUB_WEB_BASE = "https://github.com";
const GITHUB_API_REPOSITORY_URL = `${GITHUB_API_BASE}/repos/${REPOSITORY}`;
const GITHUB_JWKS_URL = `${ISSUER}/.well-known/jwks`;
const GITHUB_ACTIONS_APP_SLUG = "github-actions";
const GITHUB_ACTIONS_APP_NAME = "GitHub Actions";
const GITHUB_ACTIONS_APP_ID = 15368;
const GITHUB_ACTIONS_APP_OWNER_ID = 9919;
const EXPECTED_GITHUB_APP_PERMISSIONS = Object.freeze({
  actions: "read",
  checks: "read",
  contents: "read",
  deployments: "read",
  metadata: "read",
});
const EXPECTED_GITHUB_TOKEN_RESPONSE_KEYS = Object.freeze([
  "expires_at", "permissions", "repositories", "repository_selection", "token",
]);
const MAX_TOKEN_LIFETIME_SECONDS = 600;
const MAX_LEDGER_RECORDS = 10_000;
const STRICT_TIMEOUT_MS = 15_000;
const MAX_RESPONSE_BYTES = 32_000_000;
const MAX_GITHUB_RESPONSE_BYTES = 1_048_576;
const MAX_GITHUB_TOKEN_RESPONSE_BYTES = 16_384;
const GITHUB_APP_JWT_LIFETIME_SECONDS = 540;
const JWKS_CACHE_SECONDS = 300;
const PAGE_SIZE = 1_000;
const MAX_PAGES = 50;
const MAX_ROWS = 50_000;
const MAX_SOURCE_TARGETS = 64;
const MAX_PROFILE_SOURCE_PAIRS = 50_000;
const TRUST_BROKER_ENDPOINT_CONFIG_NAME = "G5_TRUST_BROKER_ENDPOINT";
const RUNTIME_POLICY_BINDING_NAMES = Object.freeze({
  candidateSha: "G5_ALLOWED_CANDIDATE_SHA",
  candidateTree: "G5_ALLOWED_CANDIDATE_TREE",
  workflowBlobSha: "G5_ALLOWED_WORKFLOW_BLOB_SHA",
});
const GITHUB_APP_CONFIG_NAMES = Object.freeze({
  appId: "G5_GITHUB_APP_ID",
  installationId: "G5_GITHUB_APP_INSTALLATION_ID",
  privateKey: "G5_GITHUB_APP_PRIVATE_KEY",
});
const SUPABASE_SECRET_KEY_PREFIX = ["sb", "secret", ""].join("_");
const GITHUB_ACTIONS_OIDC_HOST = "token.actions.githubusercontent.com";
const VALIDATED_RECEIPT = Symbol("g5.validatedReceipt");
const LEGACY_POLICY_DENYLIST = Object.freeze([
  Object.freeze({
    candidateSha: "74defb6326d8432bf790cb84b4aa549fefc425be",
    candidateTree: "b9b4cc8a6f8279f898b2b8bf2a900c56a741b528",
    workflowBlobSha: "992308681c31dd5b2be3ab9c3fb1d20369120d92",
  }),
]);
const MANUAL_WORKFLOW_POLICY = Object.freeze({
  state: "DEPLOYMENT_READY_DISABLED_NOT_CONFIGURED",
  dispatchDefined: true,
  operationalGuard: "vars.G5_TRUST_RUNTIME_ENABLED == 'true'",
  defaultEnabled: false,
  mainRef: MAIN_REF,
  runAttempt: 1,
  idTokenPermission: true,
  productionEnvironment: ENVIRONMENT,
  connectedMode: CONNECTED_DISABLED,
  concurrencyIsLedger: false,
});
const SUPABASE_TABLES = Object.freeze({
  institutions: "id,name,slug,website_url,last_harvest_at",
  institution_site_profiles: "id,institution_id,discovery_enabled,pipeline_enabled,pipeline_ready,site_type,discovery_mode,seed_urls,catalog_url_patterns,catalog_max_pages,allowed_url_patterns,exclusion_patterns,requires_cloudflare_bypass,warmup_url,circuit_open,circuit_opened_at",
  staging_raw: "id,institution_id,url,status,content_hash,last_harvested_at,created_at",
  cleansed_programs: "id,staging_id,institution_id,url",
  enriched_programs: "id,cleansed_id,institution_id,url",
  courses: "id,institution_id,url,is_active,last_404_at,start_date",
});
const DISCOVERY_MODES = new Set(["hardcoded_urls", "paginated_catalog", "catalog_link_extraction", "sitemap_bfs"]);
const SITE_TYPES = new Set(["traditional_ssr", "ecommerce", "spa_js_heavy", "paginated_catalog", "catalog_link_extraction", "cloudflare_protected"]);
const NON_HTML_EXTENSIONS = Object.freeze([
  ".pdf", ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".ppt",
  ".zip", ".rar", ".7z", ".tar", ".gz", ".jpg", ".jpeg", ".png",
  ".gif", ".svg", ".webp", ".bmp", ".ico", ".mp4", ".mp3", ".avi",
  ".mov", ".wmv", ".css", ".js", ".json", ".xml",
]);
const TRACKING_QUERY_KEYS = new Set(["fbclid", "gclid", "gbraid", "wbraid", "mc_cid", "mc_eid", "igshid", "msclkid"]);

let DurableObjectBase = class {
  constructor(ctx, env) {
    this.ctx = ctx;
    this.env = env;
  }
};
try {
  ({ DurableObject: DurableObjectBase } = await import("cloudflare:workers"));
} catch {
  // Repository-only tests use the local base; deployment remains blocked.
}

export const REASONS = Object.freeze({
  AUTHORITY: "STOP_G5_AUTHORITY_INVALID",
  APPROVAL: "STOP_G5_APPROVAL_INVALID",
  BINDING: "STOP_G5_BINDING_DRIFT",
  REPLAY: "STOP_G5_REPLAY_DETECTED",
  EXPIRED: "STOP_G5_GATE_EXPIRED",
  AMBIGUOUS: "STOP_G5_CONSUMPTION_AMBIGUOUS",
  PROOF: "STOP_G5_PROOF_INVALID",
  LEDGER: "STOP_G5_ATOMIC_LEDGER_REQUIRED",
  CONFIG: CONFIG_STOP,
  TRANSPORT: "STOP_G5_TRANSPORT_INVALID",
  RECEIPT: "STOP_G5_RECEIPT_INVALID",
  SUPABASE: "STOP_G5_SUPABASE_READONLY_INVALID",
  PAGINATION: "STOP_G5_PAGINATION_INCOMPLETE",
  COUNT: "STOP_G5_COUNT_DRIFT",
  SNAPSHOT: "STOP_G5_SNAPSHOT_CONTENT_DRIFT",
  PROFILE: "STOP_G5_PROFILE_ROUTING_INVALID",
  TARGET: "STOP_G5_TARGET_BINDING_INVALID",
  SOURCE: "STOP_G5_SOURCE_BLOCKERS_PRESENT",
});
const PUBLIC_REASON_CODES = new Set([...Object.values(REASONS), TRUST_STOP, CONNECTED_STOP]);

const AUTHORITY_FIELDS = new Set([
  "claims", "evidence", "approval", "deployment", "environment", "receipt",
  "repository_id", "owner_id", "check_run_id", "environment_id",
  "deployment_id", "deployment_status_id", "job_id", "check_suite_id",
  "approver_id", "workflow_sha", "workflow_blob_sha", "jobId",
  "deploymentStatusId", "checkSuiteId",
  "nonce", "jti", "proof", "jwks", "installation_token",
]);

export class TrustBrokerError extends Error {
  constructor(reason) {
    super(reason);
    this.name = "TrustBrokerError";
    this.reason = reason;
  }
}

function stop(reason) {
  throw new TrustBrokerError(reason);
}

function publicReasonFromError(error) {
  if (error instanceof TrustBrokerError && PUBLIC_REASON_CODES.has(error.reason)) {
    return error.reason;
  }
  if (error instanceof Error && PUBLIC_REASON_CODES.has(error.message)) {
    return error.message;
  }
  return null;
}

function exactObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function positiveInteger(value) {
  return Number.isSafeInteger(value) && value > 0;
}

function positiveDecimalString(value) {
  return typeof value === "string" && /^[1-9][0-9]*$/.test(value) && positiveInteger(Number(value));
}

function exactOne(values, reason) {
  if (!Array.isArray(values) || values.length !== 1) stop(reason);
  return values[0];
}

function exactOneComplete(result, reason) {
  if (!exactObject(result) || result.complete !== true) stop(reason);
  return exactOne(result.items, reason);
}

function base64urlDecode(value) {
  if (typeof value !== "string" || !/^[A-Za-z0-9_-]+$/.test(value)) {
    stop(REASONS.PROOF);
  }
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padding = "=".repeat((4 - (normalized.length % 4)) % 4);
  return Uint8Array.from(atob(normalized + padding), (character) => character.charCodeAt(0));
}

function base64urlEncode(bytes) {
  let text = "";
  for (const byte of bytes) text += String.fromCharCode(byte);
  return btoa(text).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

function encodeBase64urlJson(value) {
  return base64urlEncode(new TextEncoder().encode(JSON.stringify(value)));
}

function pemToPkcs8Bytes(pem) {
  if (typeof pem !== "string" || pem.length > 10_000 || !pem.includes("BEGIN PRIVATE KEY")) stop(REASONS.CONFIG);
  const material = pem.replace(/-----BEGIN PRIVATE KEY-----/g, "")
    .replace(/-----END PRIVATE KEY-----/g, "")
    .replace(/\s+/g, "");
  if (!/^[A-Za-z0-9+/=]+$/.test(material)) stop(REASONS.CONFIG);
  return Uint8Array.from(atob(material), (character) => character.charCodeAt(0));
}

async function signRs256(material, privateKeyPem) {
  let key;
  try {
    key = await crypto.subtle.importKey(
      "pkcs8",
      pemToPkcs8Bytes(privateKeyPem),
      { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
      false,
      ["sign"],
    );
    const signature = await crypto.subtle.sign(
      "RSASSA-PKCS1-v1_5",
      key,
      new TextEncoder().encode(material),
    );
    return base64urlEncode(new Uint8Array(signature));
  } catch (error) {
    if (error instanceof TrustBrokerError) throw error;
    stop(REASONS.CONFIG);
  }
}

export async function createGithubAppJwt({ appId, privateKey, nowEpochSeconds, signer = signRs256 } = {}) {
  if (!positiveDecimalString(appId) || typeof privateKey !== "string" || !Number.isSafeInteger(nowEpochSeconds)) {
    stop(REASONS.CONFIG);
  }
  if (typeof signer !== "function") stop(REASONS.CONFIG);
  const header = encodeBase64urlJson({ alg: "RS256", typ: "JWT" });
  const payload = encodeBase64urlJson({
    iat: nowEpochSeconds - 30,
    exp: nowEpochSeconds + GITHUB_APP_JWT_LIFETIME_SECONDS,
    iss: appId,
  });
  const material = `${header}.${payload}`;
  const signature = await signer(material, privateKey);
  if (typeof signature !== "string" || !/^[A-Za-z0-9_-]+$/.test(signature)) stop(REASONS.CONFIG);
  return `${material}.${signature}`;
}

function decodeJson(value) {
  try {
    return JSON.parse(new TextDecoder().decode(base64urlDecode(value)));
  } catch {
    stop(REASONS.PROOF);
  }
}

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (exactObject(value)) {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stable(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

async function digest(value) {
  const bytes = new TextEncoder().encode(stable(value));
  const result = await crypto.subtle.digest("SHA-256", bytes);
  return `sha256:${Array.from(new Uint8Array(result), (byte) => byte.toString(16).padStart(2, "0")).join("")}`;
}

function sha(value) {
  return typeof value === "string" && /^[0-9a-f]{40}$/.test(value);
}

function runtimeEnabled(env) {
  return exactObject(env) && env[RUNTIME_ENABLED_CONFIG_NAME] === "true";
}

function validateRepositoryPolicy(policy) {
  if (
    !exactObject(policy) || policy.repository !== REPOSITORY ||
    policy.workflowRef !== WORKFLOW_REF || !sha(policy.candidateSha) ||
    !sha(policy.candidateTree) || !sha(policy.workflowBlobSha)
  ) stop(REASONS.CONFIG);
  if (LEGACY_POLICY_DENYLIST.some((legacy) => (
    policy.candidateSha === legacy.candidateSha ||
    policy.candidateTree === legacy.candidateTree ||
    policy.workflowBlobSha === legacy.workflowBlobSha
  ))) stop(REASONS.BINDING);
  return Object.freeze({
    repository: policy.repository,
    workflowRef: policy.workflowRef,
    candidateSha: policy.candidateSha,
    candidateTree: policy.candidateTree,
    workflowBlobSha: policy.workflowBlobSha,
  });
}

export function repositoryPolicyFromRuntimeBindings(env = {}) {
  if (!exactObject(env)) stop(REASONS.CONFIG);
  const policy = {
    repository: REPOSITORY,
    workflowRef: WORKFLOW_REF,
    candidateSha: env[RUNTIME_POLICY_BINDING_NAMES.candidateSha],
    candidateTree: env[RUNTIME_POLICY_BINDING_NAMES.candidateTree],
    workflowBlobSha: env[RUNTIME_POLICY_BINDING_NAMES.workflowBlobSha],
  };
  return validateRepositoryPolicy(policy);
}

function requireRuntimeReady(env, { endpointApproved = false } = {}) {
  if (!runtimeEnabled(env)) stop(CONNECTED_STOP);
  const policy = repositoryPolicyFromRuntimeBindings(env);
  if (endpointApproved !== true) stop(CONNECTED_STOP);
  return policy;
}

function endpointApprovedFromRuntimeBindings(env) {
  return typeof env?.[TRUST_BROKER_ENDPOINT_CONFIG_NAME] === "string" && env[TRUST_BROKER_ENDPOINT_CONFIG_NAME].trim().length > 0;
}

function digestText(value) {
  return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value);
}

function exactKeys(value, keys, reason) {
  if (!exactObject(value) || stable(Object.keys(value).sort()) !== stable([...keys].sort())) stop(reason);
}

function decimalId(value) {
  if (typeof value === "number") return positiveInteger(value) ? value : null;
  if (positiveDecimalString(value)) return Number(value);
  return null;
}

function lowerHeader(headers, name) {
  if (!headers || typeof headers.get !== "function") return null;
  return headers.get(name) ?? headers.get(name.toLowerCase()) ?? headers.get(name.toUpperCase());
}

function splitLinkHeader(value) {
  const parts = [];
  let start = 0;
  let quoted = false;
  let angled = false;
  for (let index = 0; index < value.length; index += 1) {
    const character = value[index];
    if (character === '"' && value[index - 1] !== "\\") quoted = !quoted;
    if (!quoted && character === "<") angled = true;
    if (!quoted && character === ">") angled = false;
    if (!quoted && !angled && character === ",") {
      parts.push(value.slice(start, index));
      start = index + 1;
    }
  }
  parts.push(value.slice(start));
  return parts;
}

const ALLOWED_LINK_RELATIONS = new Set(["last"]);

function canonicalQueryParams(url) {
  const params = new Map();
  for (const [name, paramValue] of url.searchParams) {
    if (!/^[a-z][a-z0-9_]*$/.test(name) || params.has(name) || paramValue.length === 0) {
      stop(REASONS.BINDING);
    }
    params.set(name, paramValue);
  }
  return params;
}

function requireCanonicalLinkUrl(url, requestUrl) {
  if (url.origin !== GITHUB_API_BASE || url.hash !== "" || url.pathname !== requestUrl.pathname) stop(REASONS.BINDING);
  const requestParams = canonicalQueryParams(requestUrl);
  const linkParams = canonicalQueryParams(url);
  for (const [name, paramValue] of requestParams) {
    if (name !== "page" && linkParams.get(name) !== paramValue) stop(REASONS.BINDING);
  }
  for (const [name, paramValue] of linkParams) {
    if (name === "page") {
      if (!positiveDecimalString(paramValue)) stop(REASONS.BINDING);
    } else if (requestParams.get(name) !== paramValue) {
      stop(REASONS.BINDING);
    }
  }
}

function linkHeaderHasRelNext(value, requestUrl) {
  if (typeof value !== "string") return false;
  const entries = splitLinkHeader(value);
  if (entries.length === 0) stop(REASONS.BINDING);
  const seenRelations = new Set();
  let hasNext = false;
  for (const rawEntry of entries) {
    const entry = rawEntry.trim();
    const match = entry.match(/^<([^<>\s]+)>\s*(;.*)$/);
    if (!match) stop(REASONS.BINDING);
    const url = requireSafeHttpsUrl(match[1], REASONS.BINDING);
    requireCanonicalLinkUrl(url, requestUrl);
    const seenParameters = new Set();
    let relation = null;
    for (const rawParameter of match[2].split(";").slice(1)) {
      const parameter = rawParameter.trim();
      const equals = parameter.indexOf("=");
      if (equals <= 0 || equals !== parameter.lastIndexOf("=")) stop(REASONS.BINDING);
      const name = parameter.slice(0, equals).trim().toLowerCase();
      const parameterValue = parameter.slice(equals + 1).trim();
      if (!/^[a-z][a-z0-9_-]*$/.test(name) || seenParameters.has(name) || parameterValue.length === 0) {
        stop(REASONS.BINDING);
      }
      seenParameters.add(name);
      if (name !== "rel") stop(REASONS.BINDING);
      if (!parameterValue.startsWith('"') || !parameterValue.endsWith('"')) stop(REASONS.BINDING);
      const tokens = parameterValue.slice(1, -1).trim().toLowerCase().split(/\s+/).filter(Boolean);
      if (tokens.length !== 1 || relation !== null) stop(REASONS.BINDING);
      relation = tokens[0];
    }
    if (relation === null || !/^[a-z][a-z0-9.-]*$/.test(relation) || seenRelations.has(relation)) {
      stop(REASONS.BINDING);
    }
    seenRelations.add(relation);
    if (relation === "next") hasNext = true;
    else if (!ALLOWED_LINK_RELATIONS.has(relation)) stop(REASONS.BINDING);
  }
  return hasNext;
}

async function responseTextWithLimit(response, maxBytes, timeoutMs = STRICT_TIMEOUT_MS) {
  if (!response?.body || typeof response.body.getReader !== "function") {
    let timeout;
    const text = await Promise.race([
      response.text(),
      new Promise((_, reject) => {
        timeout = setTimeout(() => reject(new TrustBrokerError(REASONS.TRANSPORT)), timeoutMs);
      }),
    ]).finally(() => clearTimeout(timeout));
    if (new TextEncoder().encode(text).byteLength > maxBytes) stop(REASONS.TRANSPORT);
    return text;
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let bytes = 0;
  let timedOut = false;
  const timeout = setTimeout(() => {
    timedOut = true;
    reader.cancel().catch(() => undefined);
  }, timeoutMs);
  try {
    let text = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (timedOut) stop(REASONS.TRANSPORT);
      if (done) return text + decoder.decode();
      bytes += value.byteLength;
      if (bytes > maxBytes) stop(REASONS.TRANSPORT);
      text += decoder.decode(value, { stream: true });
    }
  } catch (error) {
    if (error instanceof TrustBrokerError) throw error;
    stop(REASONS.TRANSPORT);
  } finally {
    clearTimeout(timeout);
  }
}

async function responseJsonWithLimit(response, maxBytes, timeoutMs = STRICT_TIMEOUT_MS) {
  let parsed;
  try {
    parsed = JSON.parse(await responseTextWithLimit(response, maxBytes, timeoutMs));
  } catch {
    stop(REASONS.TRANSPORT);
  }
  return parsed;
}

async function fetchWithTimeout(transport, request, timeoutMs, resolvedAddresses = null) {
  if (!transport || typeof transport.fetch !== "function") stop(REASONS.TRANSPORT);
  if (resolvedAddresses !== null && typeof transport.fetchPinned !== "function") stop(REASONS.TRANSPORT);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    if (resolvedAddresses !== null) {
      return await transport.fetchPinned(request, { signal: controller.signal, resolvedAddresses });
    }
    return await transport.fetch(request, { signal: controller.signal });
  } catch {
    stop(REASONS.TRANSPORT);
  } finally {
    clearTimeout(timeout);
  }
}

function ipv4Parts(value) {
  if (typeof value !== "string" || !/^\d{1,3}(?:\.\d{1,3}){3}$/.test(value)) return null;
  const parts = value.split(".").map((part) => Number(part));
  return parts.every((part) => Number.isInteger(part) && part >= 0 && part <= 255) ? parts : null;
}

function isGlobalIpv4(value) {
  const parts = ipv4Parts(value);
  if (!parts) return null;
  const [a, b] = parts;
  if (
    a === 0 || a === 10 || a === 127 || a >= 224 ||
    (a === 100 && b >= 64 && b <= 127) ||
    (a === 169 && b === 254) ||
    (a === 172 && b >= 16 && b <= 31) ||
    (a === 192 && (b === 0 || b === 168)) ||
    (a === 198 && (b === 18 || b === 19)) ||
    (a === 198 && b === 51) ||
    (a === 203 && b === 0)
  ) return false;
  return true;
}

function normalizedHostname(value) {
  if (typeof value !== "string") return "";
  const lowered = value.toLowerCase().replace(/\.$/, "");
  return lowered.startsWith("[") && lowered.endsWith("]") ? lowered.slice(1, -1) : lowered;
}

function isGlobalIpv6(value) {
  if (typeof value !== "string" || !value.includes(":")) return null;
  const normalized = normalizedHostname(value);
  const first = Number.parseInt(normalized.split(":", 1)[0] || "0", 16);
  const parts = normalized.split(":").filter(Boolean);
  const embeddedIpv4 = normalized.includes(".") ? normalized.split(":").at(-1) : null;
  if (embeddedIpv4 !== null && isGlobalIpv4(embeddedIpv4) !== true) return false;
  if (
    parts.every((part) => /^0+$/.test(part)) ||
    parts.length === 8 && parts.slice(0, 7).every((part) => /^0+$/.test(part)) && parts[7] === "1"
  ) return false;
  if (
    normalized === "::" || normalized === "::1" || normalized.includes("%") ||
    normalized.startsWith("::ffff:") ||
    Number.isNaN(first) || (first & 0xfe00) === 0xfc00 ||
    (first & 0xffc0) === 0xfe80 || (first & 0xff00) === 0xff00 ||
    normalized.startsWith("2001:db8")
  ) return false;
  return true;
}

function isGlobalAddress(value) {
  const v4 = isGlobalIpv4(value);
  if (v4 !== null) return v4;
  const v6 = isGlobalIpv6(value);
  if (v6 !== null) return v6;
  return null;
}

function requireSafeHttpsUrl(raw, reason = REASONS.TRANSPORT) {
  let parsed;
  try {
    parsed = new URL(raw);
  } catch {
    stop(reason);
  }
  const host = normalizedHostname(parsed.hostname);
  const addressGlobal = isGlobalAddress(host);
  if (
    parsed.protocol !== "https:" || parsed.username || parsed.password || !host ||
    host === "localhost" || host.endsWith(".localhost") || addressGlobal === false
  ) stop(reason);
  return parsed;
}

async function requirePublicDns(hostname, resolver) {
  if (isGlobalAddress(hostname) === true) return Object.freeze([hostname]);
  if (isGlobalAddress(hostname) === false) stop(REASONS.TRANSPORT);
  if (typeof resolver !== "function") stop(REASONS.TRANSPORT);
  let addresses;
  try {
    addresses = await resolver(hostname);
  } catch {
    stop(REASONS.TRANSPORT);
  }
  if (!Array.isArray(addresses) || addresses.length === 0) stop(REASONS.TRANSPORT);
  for (const address of addresses) {
    const value = typeof address === "string" ? address : address?.address;
    if (isGlobalAddress(value) !== true) stop(REASONS.TRANSPORT);
  }
  return Object.freeze(addresses.map((address) => typeof address === "string" ? address : address.address));
}

async function stableDigest(value) {
  return digest(value);
}

export function rejectCallerAuthority(request) {
  if (!exactObject(request)) stop(REASONS.AUTHORITY);
  for (const key of Object.keys(request)) {
    if (AUTHORITY_FIELDS.has(key)) stop(REASONS.AUTHORITY);
  }
  const allowed = Object.keys(request).sort();
  if (stable(allowed) !== stable(["bearerOidc", "gateReference"])) stop(REASONS.AUTHORITY);
  if (typeof request.bearerOidc !== "string" || !exactObject(request.gateReference)) {
    stop(REASONS.AUTHORITY);
  }
  if (Object.keys(request.gateReference).sort().join(",") !== "expectedRunAttempt,runId") {
    stop(REASONS.AUTHORITY);
  }
  if (!positiveInteger(request.gateReference.runId) || request.gateReference.expectedRunAttempt !== 1) {
    stop(REASONS.AUTHORITY);
  }
}

export async function verifyGithubOidc(token, jwks, nowEpochSeconds) {
  if (typeof token !== "string" || token.length > 16_384 || !exactObject(jwks)) stop(REASONS.PROOF);
  const parts = token.split(".");
  if (parts.length !== 3) stop(REASONS.PROOF);
  const header = decodeJson(parts[0]);
  const claims = decodeJson(parts[1]);
  if (!exactObject(header) || header.alg !== "RS256" || typeof header.kid !== "string") stop(REASONS.PROOF);
  const key = exactOne((jwks.keys ?? []).filter((item) => item?.kid === header.kid), REASONS.PROOF);
  if (key.kty !== "RSA" || key.alg !== "RS256" || key.use !== "sig") stop(REASONS.PROOF);
  let imported;
  try {
    imported = await crypto.subtle.importKey(
      "jwk", key, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"],
    );
  } catch {
    stop(REASONS.PROOF);
  }
  const valid = await crypto.subtle.verify(
    "RSASSA-PKCS1-v1_5", imported, base64urlDecode(parts[2]),
    new TextEncoder().encode(`${parts[0]}.${parts[1]}`),
  );
  if (!valid) stop(REASONS.PROOF);
  if (
    claims.iss !== ISSUER || claims.aud !== AUDIENCE ||
    !Number.isSafeInteger(nowEpochSeconds) || !Number.isSafeInteger(claims.exp) ||
    !Number.isSafeInteger(claims.nbf) || !Number.isSafeInteger(claims.iat) ||
    !(claims.iat <= nowEpochSeconds && claims.nbf <= nowEpochSeconds && nowEpochSeconds < claims.exp) ||
    claims.exp <= claims.iat || claims.nbf >= claims.exp ||
    claims.exp - claims.iat > MAX_TOKEN_LIFETIME_SECONDS ||
    typeof claims.jti !== "string" || claims.jti.length < 16 || claims.jti.length > 256 ||
    !positiveDecimalString(claims.repository_id) || !positiveDecimalString(claims.repository_owner_id) ||
    claims.ref !== MAIN_REF || claims.repository !== REPOSITORY ||
    typeof claims.sha !== "string" ||
    !/^[0-9a-f]{40}$/.test(claims.sha) || typeof claims.workflow_ref !== "string" ||
    claims.workflow_ref !== WORKFLOW_REF || claims.workflow_sha !== claims.sha ||
    !positiveDecimalString(claims.run_id) || claims.run_attempt !== "1" ||
    claims.environment !== ENVIRONMENT || !positiveDecimalString(claims.actor_id)
  ) stop(REASONS.PROOF);
  const nonce = await digest([
    "github-oidc-nonce", claims.jti, claims.repository_id, claims.run_id,
    claims.run_attempt,
  ]);
  return Object.freeze({
    repository: claims.repository,
    repositoryId: Number(claims.repository_id),
    ownerId: Number(claims.repository_owner_id),
    ref: claims.ref,
    candidateSha: claims.sha,
    workflowRef: claims.workflow_ref,
    workflowSha: claims.workflow_sha,
    runId: Number(claims.run_id),
    runAttempt: Number(claims.run_attempt),
    environment: claims.environment,
    actorId: Number(claims.actor_id),
    nonce,
    jti: claims.jti,
    expiresAt: claims.exp,
  });
}

export class G5GithubJwksClient {
  constructor({ transport, timeoutMs = 5_000, maxBytes = 65_536, cacheSeconds = JWKS_CACHE_SECONDS } = {}) {
    if (typeof transport?.fetch !== "function") stop(REASONS.CONFIG);
    if (!positiveInteger(timeoutMs) || !positiveInteger(maxBytes) || !positiveInteger(cacheSeconds)) stop(REASONS.CONFIG);
    this.transport = transport;
    this.timeoutMs = timeoutMs;
    this.maxBytes = maxBytes;
    this.cacheSeconds = cacheSeconds;
    this.cached = null;
  }

  async jwks(nowEpochSeconds = Math.floor(Date.now() / 1000)) {
    if (!Number.isSafeInteger(nowEpochSeconds)) stop(REASONS.PROOF);
    if (this.cached && this.cached.expiresAt > nowEpochSeconds) return this.cached.jwks;
    const endpoint = requireSafeHttpsUrl(GITHUB_JWKS_URL, REASONS.PROOF);
    if (endpoint.hostname !== GITHUB_ACTIONS_OIDC_HOST) stop(REASONS.PROOF);
    const response = await fetchWithTimeout(
      this.transport,
      new Request(endpoint, { method: "GET", redirect: "manual", headers: { accept: "application/json" } }),
      this.timeoutMs,
    );
    if (!response || response.status < 200 || response.status >= 300) stop(REASONS.PROOF);
    const body = await responseJsonWithLimit(response, this.maxBytes, this.timeoutMs);
    if (!exactObject(body) || !Array.isArray(body.keys) || body.keys.length === 0 || body.keys.length > 16) stop(REASONS.PROOF);
    for (const key of body.keys) {
      if (!exactObject(key) || key.kty !== "RSA" || key.alg !== "RS256" || key.use !== "sig" || typeof key.kid !== "string") {
        stop(REASONS.PROOF);
      }
    }
    const jwks = Object.freeze({ keys: Object.freeze(body.keys.map((key) => Object.freeze({ ...key }))) });
    this.cached = Object.freeze({ jwks, expiresAt: nowEpochSeconds + this.cacheSeconds });
    return jwks;
  }

  async verify(token, nowEpochSeconds = Math.floor(Date.now() / 1000)) {
    return verifyGithubOidc(token, await this.jwks(nowEpochSeconds), nowEpochSeconds);
  }
}

export class GithubAppReadOnlyAdapter {
  constructor(transport) {
    const methods = [
      "getWorkflowRun", "listWorkflowJobs", "listDeployments", "getEnvironment",
      "listApprovals", "getCommit", "getWorkflowBlob", "getBranch",
    ];
    if (!transport || methods.some((method) => typeof transport[method] !== "function")) {
      stop(REASONS.AUTHORITY);
    }
    this.transport = transport;
  }

  async authoritativeEvidence(claims) {
    const reference = Object.freeze({
      repository: claims.repository, runId: claims.runId, runAttempt: claims.runAttempt,
      repositoryId: claims.repositoryId, ownerId: claims.ownerId, candidateSha: claims.candidateSha,
      workflowRef: claims.workflowRef, environment: claims.environment,
    });
    const [run, check, branch, environment, approval, commit, workflowBlob] = await Promise.all([
      this.transport.getWorkflowRun(reference),
      this.transport.listWorkflowJobs(reference),
      this.transport.getBranch(reference),
      this.transport.getEnvironment(reference),
      this.transport.listApprovals(reference),
      this.transport.getCommit(reference),
      this.transport.getWorkflowBlob(reference),
    ]).then((groups) => groups.map((group, index) => exactOneComplete(
      group,
      index === 4 ? REASONS.APPROVAL : REASONS.BINDING,
    )));
    const deployment = exactOneComplete(
      await this.transport.listDeployments(Object.freeze({ ...reference, jobId: check.jobId })),
      REASONS.BINDING,
    );
    return Object.freeze({ run, check, branch, deployment, environment, approval, commit, workflowBlob });
  }

  async terminalEvidence(claims) {
    const reference = Object.freeze({
      repository: claims.repository, runId: claims.runId, runAttempt: claims.runAttempt,
      repositoryId: claims.repositoryId, ownerId: claims.ownerId, candidateSha: claims.candidateSha,
      workflowRef: claims.workflowRef, environment: claims.environment,
    });
    const run = exactOneComplete(await this.transport.getWorkflowRun(reference), REASONS.BINDING);
    const check = exactOneComplete(await this.transport.listWorkflowJobs(reference), REASONS.BINDING);
    const deployment = exactOneComplete(
      await this.transport.listDeployments(Object.freeze({ ...reference, jobId: check.jobId })),
      REASONS.BINDING,
    );
    return Object.freeze({ run, check, deployment });
  }
}

export class G5ConnectedGithubAppAdapter {
  constructor({
    env = {}, transport, policy, endpointApproved = false, timeoutMs = 5_000,
    maxBytes = MAX_GITHUB_RESPONSE_BYTES, now = () => Math.floor(Date.now() / 1000),
    signer = signRs256,
  } = {}) {
    if (!exactObject(env) || typeof transport?.fetch !== "function") stop(CONNECTED_STOP);
    if (typeof now !== "function" || typeof signer !== "function") stop(REASONS.CONFIG);
    this.policy = validateRepositoryPolicy(policy ?? requireRuntimeReady(env, { endpointApproved }));
    if (!runtimeEnabled(env) || endpointApproved !== true) stop(CONNECTED_STOP);
    const appId = env[GITHUB_APP_CONFIG_NAMES.appId];
    const installationId = env[GITHUB_APP_CONFIG_NAMES.installationId];
    const privateKey = env[GITHUB_APP_CONFIG_NAMES.privateKey];
    if (!positiveDecimalString(appId) || !positiveDecimalString(installationId) || typeof privateKey !== "string") {
      stop(REASONS.CONFIG);
    }
    if (!positiveInteger(timeoutMs) || !positiveInteger(maxBytes) || maxBytes > MAX_GITHUB_RESPONSE_BYTES) stop(REASONS.CONFIG);
    this.env = env;
    this.transport = transport;
    this.appId = appId;
    this.installationId = installationId;
    this.privateKey = privateKey;
    this.timeoutMs = timeoutMs;
    this.maxBytes = maxBytes;
    this.now = now;
    this.signer = signer;
    this.tokenPromises = new Map();
    this.tokens = new Map();
    this.state = "LIVE_READY_GUARDED";
  }

  async authoritativeEvidence(claims) {
    const adapter = new GithubAppReadOnlyAdapter(this);
    return adapter.authoritativeEvidence(claims);
  }

  async terminalEvidence(claims) {
    const adapter = new GithubAppReadOnlyAdapter(this);
    return adapter.terminalEvidence(claims);
  }

  ensureReference(reference) {
    if (
      !exactObject(reference) || reference.repository !== REPOSITORY ||
      reference.runAttempt !== 1 || !positiveInteger(reference.repositoryId) ||
      !positiveInteger(reference.ownerId) || reference.candidateSha !== this.policy.candidateSha ||
      reference.workflowRef !== WORKFLOW_REF || reference.environment !== ENVIRONMENT
    ) stop(REASONS.BINDING);
  }

  async createAppJwt() {
    return createGithubAppJwt({
      appId: this.appId,
      privateKey: this.privateKey,
      nowEpochSeconds: this.now(),
      signer: this.signer,
    });
  }

  async installationToken(repositoryId) {
    if (!positiveInteger(repositoryId)) stop(REASONS.TRANSPORT);
    const nowEpochSeconds = this.now();
    const cached = this.tokens.get(repositoryId);
    if (cached && cached.expiresAt - nowEpochSeconds > 60) return cached.value;
    const existing = this.tokenPromises.get(repositoryId);
    if (existing) return existing;
    const tokenPromise = this.createInstallationToken(nowEpochSeconds, repositoryId).finally(() => {
      this.tokenPromises.delete(repositoryId);
    });
    this.tokenPromises.set(repositoryId, tokenPromise);
    return tokenPromise;
  }

  async createInstallationToken(nowEpochSeconds, repositoryId) {
    const jwt = await this.createAppJwt();
    const body = {
      repository_ids: [repositoryId],
      permissions: { ...EXPECTED_GITHUB_APP_PERMISSIONS },
    };
    const response = await this.githubFetch(
      "POST",
      `/app/installations/${this.installationId}/access_tokens`,
      {
        headers: { authorization: `Bearer ${jwt}` },
        body: JSON.stringify(body),
        maxBytes: MAX_GITHUB_TOKEN_RESPONSE_BYTES,
      },
    );
    if (!exactObject(response) || typeof response.token !== "string" || response.token.length < 16 || response.token.length > 512) {
      stop(REASONS.TRANSPORT);
    }
    exactKeys(response, EXPECTED_GITHUB_TOKEN_RESPONSE_KEYS, REASONS.TRANSPORT);
    if (!exactObject(response.permissions)) stop(REASONS.TRANSPORT);
    exactKeys(response.permissions, Object.keys(EXPECTED_GITHUB_APP_PERMISSIONS), REASONS.TRANSPORT);
    for (const [permission, access] of Object.entries(response.permissions)) {
      if (EXPECTED_GITHUB_APP_PERMISSIONS[permission] !== access) stop(REASONS.TRANSPORT);
    }
    if (response.repository_selection !== "selected") stop(REASONS.TRANSPORT);
    if (!Array.isArray(response.repositories) || response.repositories.length !== 1) stop(REASONS.TRANSPORT);
    const repository = response.repositories[0];
    if (!exactObject(repository) || Number(repository.id) !== repositoryId || repository.full_name !== REPOSITORY) {
      stop(REASONS.TRANSPORT);
    }
    const expiresAt = Date.parse(response.expires_at ?? "");
    if (!Number.isFinite(expiresAt)) stop(REASONS.TRANSPORT);
    const token = Object.freeze({ value: response.token, repositoryId, expiresAt: Math.floor(expiresAt / 1000) });
    if (token.expiresAt <= nowEpochSeconds) stop(REASONS.EXPIRED);
    this.tokens.set(repositoryId, token);
    return response.token;
  }

  async githubFetch(method, path, { headers = {}, body, maxBytes = this.maxBytes } = {}) {
    if (method !== "GET" && !(method === "POST" && path === `/app/installations/${this.installationId}/access_tokens`)) {
      stop(REASONS.TRANSPORT);
    }
    if (typeof path !== "string" || !path.startsWith("/") || path.startsWith("//")) stop(REASONS.TRANSPORT);
    const url = new URL(path, GITHUB_API_BASE);
    if (url.origin !== GITHUB_API_BASE) stop(REASONS.TRANSPORT);
    const response = await fetchWithTimeout(
      this.transport,
      new Request(url, {
        method,
        redirect: "manual",
        headers: {
          accept: "application/vnd.github+json",
          "x-github-api-version": "2022-11-28",
          ...headers,
        },
        body,
      }),
      this.timeoutMs,
    );
    if (!response || response.status < 200 || response.status >= 300) stop(REASONS.TRANSPORT);
    const link = lowerHeader(response.headers, "link");
    if (linkHeaderHasRelNext(link, url)) stop(REASONS.BINDING);
    return responseJsonWithLimit(response, maxBytes, this.timeoutMs);
  }

  async githubGet(path, repositoryId) {
    const token = await this.installationToken(repositoryId);
    return this.githubFetch("GET", path, { headers: { authorization: `Bearer ${token}` } });
  }

  complete(items) {
    return Object.freeze({ complete: true, items: Object.freeze(items.map((item) => Object.freeze(item))) });
  }

  githubApiPathFromUrl(raw, expectedPrefix, reason = REASONS.TRANSPORT) {
    if (typeof raw !== "string") stop(reason);
    const url = requireSafeHttpsUrl(raw, reason);
    if (url.origin !== GITHUB_API_BASE || url.pathname.startsWith("//")) stop(reason);
    if (typeof expectedPrefix === "string" && url.pathname !== expectedPrefix) stop(reason);
    if (url.search !== "" || url.hash !== "") stop(reason);
    return `${url.pathname}${url.search}`;
  }

  githubCheckRunPathFromUrl(raw) {
    if (typeof raw !== "string") stop(REASONS.TRANSPORT);
    const url = requireSafeHttpsUrl(raw, REASONS.TRANSPORT);
    const prefix = `/repos/${REPOSITORY}/check-runs/`;
    if (
      url.origin !== GITHUB_API_BASE || !url.pathname.startsWith(prefix) ||
      url.search !== "" || url.hash !== ""
    ) stop(REASONS.TRANSPORT);
    const id = decimalId(url.pathname.slice(prefix.length));
    if (id === null || url.pathname !== `${prefix}${id}`) stop(REASONS.TRANSPORT);
    return Object.freeze({ id, path: url.pathname, url: `${GITHUB_API_BASE}${url.pathname}` });
  }

  githubActionJobUrlBinding(raw, reference, jobId) {
    if (!positiveInteger(jobId) || typeof raw !== "string") return null;
    const url = requireSafeHttpsUrl(raw, REASONS.TRANSPORT);
    const expectedPath = `/${REPOSITORY}/actions/runs/${reference.runId}/job/${jobId}`;
    if (
      url.origin !== GITHUB_WEB_BASE || url.pathname !== expectedPath ||
      url.search !== "" || url.hash !== ""
    ) return null;
    return Object.freeze({ repository: REPOSITORY, runId: reference.runId, jobId });
  }

  async getWorkflowRun(reference) {
    this.ensureReference(reference);
    const run = await this.githubGet(`/repos/${REPOSITORY}/actions/runs/${reference.runId}`, reference.repositoryId);
    const item = exactObject(run) && run.id !== undefined ? {
      id: Number(run.id),
      repositoryId: Number(run.repository?.id),
      ownerId: Number(run.repository?.owner?.id),
      repository: run.repository?.full_name,
      ref: run.head_branch === MAIN_BRANCH || run.head_branch === MAIN_REF ? MAIN_REF : run.head_branch,
      attempt: Number(run.run_attempt),
      event: run.event,
      status: run.status,
      headSha: run.head_sha,
      actorId: Number(run.actor?.id),
      triggeringActorId: Number(run.triggering_actor?.id),
      conclusion: run.conclusion ?? null,
    } : null;
    return this.complete(item ? [item] : []);
  }

  async getBranch(reference) {
    this.ensureReference(reference);
    const branch = await this.githubGet(`/repos/${REPOSITORY}/branches/${MAIN_BRANCH}`, reference.repositoryId);
    return this.complete([{
      name: branch.name,
      protected: branch.protected === true,
    }]);
  }

  async listWorkflowJobs(reference) {
    this.ensureReference(reference);
    const jobs = await this.githubGet(`/repos/${REPOSITORY}/actions/runs/${reference.runId}/jobs?per_page=100`, reference.repositoryId);
    if (!Array.isArray(jobs.jobs)) stop(REASONS.BINDING);
    if (!Number.isSafeInteger(jobs.total_count) || jobs.total_count !== jobs.jobs.length || jobs.jobs.length >= 100) {
      stop(REASONS.BINDING);
    }
    const jobItems = Array.isArray(jobs.jobs) ? jobs.jobs.filter((job) => job.name === WORKFLOW_NAME) : [];
    if (jobItems.length !== 1) stop(REASONS.BINDING);
    const job = jobItems[0];
    if (!exactObject(job)) stop(REASONS.BINDING);
    const checkBinding = this.githubCheckRunPathFromUrl(job.check_run_url);
    const check = await this.githubGet(checkBinding.path, reference.repositoryId);
    const checkSuiteId = decimalId(check?.check_suite?.id);
    const app = check?.app;
    if (
      !exactObject(check) || !exactObject(app) || Number(check.id) !== checkBinding.id ||
      checkSuiteId === null || Number(job.run_id) !== reference.runId || Number(job.run_attempt) !== 1 ||
      job.head_sha !== reference.candidateSha || job.name !== WORKFLOW_NAME ||
      job.status !== "in_progress" || (job.conclusion ?? null) !== null ||
      check.head_sha !== reference.candidateSha || check.name !== WORKFLOW_NAME ||
      check.status !== "in_progress" || (check.conclusion ?? null) !== null ||
      app.slug !== GITHUB_ACTIONS_APP_SLUG || app.name !== GITHUB_ACTIONS_APP_NAME ||
      Number(app.id) !== GITHUB_ACTIONS_APP_ID || Number(app.owner?.id) !== GITHUB_ACTIONS_APP_OWNER_ID
    ) stop(REASONS.BINDING);
    return this.complete([{
      id: checkBinding.id,
      checkSuiteId,
      jobId: Number(job.id),
      runId: Number(job.run_id),
      runAttempt: Number(job.run_attempt),
      headSha: job.head_sha,
      checkRunUrl: checkBinding.url,
      name: job.name,
      jobStatus: job.status,
      jobConclusion: job.conclusion ?? null,
      checkHeadSha: check.head_sha,
      checkName: check.name,
      checkStatus: check.status,
      checkConclusion: check.conclusion ?? null,
      checkAppSlug: app.slug,
      checkAppName: app.name,
      checkAppId: Number(app.id),
      checkAppOwnerId: Number(app.owner?.id),
    }]);
  }

  parseDeploymentStatus(status, deployment, reference) {
    if (!exactObject(status)) stop(REASONS.BINDING);
    const statusId = decimalId(status.id);
    const deploymentId = decimalId(deployment.id);
    if (statusId === null || deploymentId === null) stop(REASONS.BINDING);
    if (typeof status.state !== "string" || typeof status.created_at !== "string" || typeof status.updated_at !== "string") {
      stop(REASONS.BINDING);
    }
    const createdAtMs = Date.parse(status.created_at ?? "");
    const updatedAtMs = Date.parse(status.updated_at ?? "");
    if (
      !Number.isFinite(createdAtMs) || !Number.isFinite(updatedAtMs) || updatedAtMs < createdAtMs ||
      !/(Z|[+-][0-9]{2}:[0-9]{2})$/.test(status.created_at ?? "") ||
      !/(Z|[+-][0-9]{2}:[0-9]{2})$/.test(status.updated_at ?? "")
    ) stop(REASONS.BINDING);
    this.githubApiPathFromUrl(status.deployment_url, `/repos/${REPOSITORY}/deployments/${deploymentId}`, REASONS.BINDING);
    const log = this.githubActionJobUrlBinding(status.log_url, reference, reference.jobId);
    const target = this.githubActionJobUrlBinding(status.target_url, reference, reference.jobId);
    if (
      status.environment !== ENVIRONMENT || status.repository_url !== GITHUB_API_REPOSITORY_URL ||
      log === null || target === null
    ) stop(REASONS.BINDING);
    return Object.freeze({
      id: statusId,
      state: status.state,
      createdAt: status.created_at,
      updatedAt: status.updated_at,
      createdAtMs,
      updatedAtMs,
    });
  }

  currentDeploymentStatus(statuses, deployment, reference) {
    if (!Array.isArray(statuses)) stop(REASONS.BINDING);
    if (statuses.length >= 100) stop(REASONS.BINDING);
    const ids = new Set();
    const parsed = statuses.map((status) => this.parseDeploymentStatus(status, deployment, reference));
    for (const status of parsed) {
      if (ids.has(status.id)) stop(REASONS.BINDING);
      ids.add(status.id);
    }
    if (parsed.length === 0) return null;
    const ordered = [...parsed].sort((left, right) => (
      right.updatedAtMs - left.updatedAtMs || right.createdAtMs - left.createdAtMs
    ));
    if (
      ordered.length > 1 && ordered[0].updatedAtMs === ordered[1].updatedAtMs &&
      ordered[0].createdAtMs === ordered[1].createdAtMs
    ) stop(REASONS.BINDING);
    const current = ordered[0];
    if (parsed.some((status) => status.id !== current.id && status.state === "in_progress")) stop(REASONS.BINDING);
    return current;
  }

  async listDeployments(reference) {
    this.ensureReference(reference);
    if (!positiveInteger(reference.jobId)) stop(REASONS.BINDING);
    const deployments = await this.githubGet(`/repos/${REPOSITORY}/deployments?sha=${reference.candidateSha}&environment=${encodeURIComponent(ENVIRONMENT)}&per_page=100`, reference.repositoryId);
    if (!Array.isArray(deployments) || deployments.length >= 100) stop(REASONS.BINDING);
    const candidates = Array.isArray(deployments) ? deployments.filter((deployment) => (
      exactObject(deployment) && deployment.sha === reference.candidateSha && deployment.environment === ENVIRONMENT &&
      deployment.repository_url === GITHUB_API_REPOSITORY_URL
    )) : [];
    const items = [];
    for (const deployment of candidates) {
      const deploymentId = decimalId(deployment.id);
      if (deploymentId === null) stop(REASONS.BINDING);
      const statusesPath = this.githubApiPathFromUrl(
        deployment.statuses_url,
        `/repos/${REPOSITORY}/deployments/${deploymentId}/statuses`,
        REASONS.BINDING,
      );
      const statuses = await this.githubGet(`${statusesPath}?per_page=100`, reference.repositoryId);
      const current = this.currentDeploymentStatus(statuses, deployment, reference);
      if (current?.state === "in_progress") {
        items.push({
          id: deploymentId,
          deploymentStatusId: current.id,
          runId: Number(reference.runId),
          jobId: Number(reference.jobId),
          sha: deployment.sha,
          environment: deployment.environment,
          statusState: current.state,
          statusCreatedAt: current.createdAt,
          statusUpdatedAt: current.updatedAt,
        });
      }
    }
    return this.complete(items);
  }

  async getEnvironment(reference) {
    this.ensureReference(reference);
    const environment = await this.githubGet(`/repos/${REPOSITORY}/environments/${encodeURIComponent(ENVIRONMENT)}`, reference.repositoryId);
    return this.complete([{
      id: Number(environment.id),
      name: environment.name,
      protected: Array.isArray(environment.protection_rules) && environment.protection_rules.length > 0,
    }]);
  }

  async listApprovals(reference) {
    this.ensureReference(reference);
    const body = await this.githubGet(`/repos/${REPOSITORY}/actions/runs/${reference.runId}/approvals`, reference.repositoryId);
    const approvals = Array.isArray(body) ? body : body.approvals;
    const items = [];
    if (Array.isArray(approvals)) {
      if (approvals.length >= 100) stop(REASONS.APPROVAL);
      for (const approval of approvals) {
        const environments = Array.isArray(approval?.environments) ? approval.environments : [];
        const productionEnvironments = environments.filter((environment) => environment?.name === ENVIRONMENT);
        if (productionEnvironments.length !== 1) continue;
        items.push({
          runId: Number(reference.runId),
          environmentId: Number(productionEnvironments[0].id),
          environment: productionEnvironments[0].name,
          state: approval.state,
          reviewerId: Number(approval.user?.id),
        });
      }
    }
    return this.complete(items);
  }

  async getCommit(reference) {
    this.ensureReference(reference);
    const commit = await this.githubGet(`/repos/${REPOSITORY}/commits/${reference.candidateSha}`, reference.repositoryId);
    return this.complete([{ sha: commit.sha, tree: commit.commit?.tree?.sha }]);
  }

  async getWorkflowBlob(reference) {
    this.ensureReference(reference);
    const blob = await this.githubGet(`/repos/${REPOSITORY}/contents/${WORKFLOW_PATH}?ref=${reference.candidateSha}`, reference.repositoryId);
    return this.complete([{ ref: reference.workflowRef, workflowSha: reference.candidateSha, blobSha: blob.sha }]);
  }
}

export function createDisabledConnectedGithubAppAdapter(options = Object.freeze({ enabled: false })) {
  if (!exactObject(options) || options.enabled !== false) stop(CONNECTED_STOP);
  return Object.freeze({
    state: CONNECTED_DISABLED,
    authoritativeEvidence: async () => stop(CONNECTED_STOP),
  });
}

export function g5WorkflowGuard({ vars = {}, ref, runAttempt } = {}) {
  const enabled = vars[RUNTIME_ENABLED_CONFIG_NAME] === "true";
  return Object.freeze({
    enabled: enabled && ref === MAIN_REF && runAttempt === 1,
    guard: MANUAL_WORKFLOW_POLICY.operationalGuard,
    refOk: ref === MAIN_REF,
    runAttemptOk: runAttempt === 1,
    connectedMode: CONNECTED_DISABLED,
  });
}

export class G5GithubActionsOidcClient {
  constructor({ env = {}, transport, audience = AUDIENCE, timeoutMs = 5_000, maxBytes = 8_192 } = {}) {
    if (!exactObject(env) || typeof transport?.fetch !== "function") stop(REASONS.AUTHORITY);
    if (audience !== AUDIENCE || !positiveInteger(timeoutMs) || !positiveInteger(maxBytes)) stop(REASONS.AUTHORITY);
    this.env = env;
    this.transport = transport;
    this.audience = audience;
    this.timeoutMs = timeoutMs;
    this.maxBytes = maxBytes;
  }

  async fetchToken() {
    const requestToken = this.env.ACTIONS_ID_TOKEN_REQUEST_TOKEN;
    const requestUrl = this.env.ACTIONS_ID_TOKEN_REQUEST_URL;
    if (typeof requestToken !== "string" || requestToken.length < 16 || typeof requestUrl !== "string") {
      stop(REASONS.PROOF);
    }
    const endpoint = requireSafeHttpsUrl(requestUrl, REASONS.PROOF);
    if (endpoint.hostname.toLowerCase() !== GITHUB_ACTIONS_OIDC_HOST) stop(REASONS.PROOF);
    endpoint.searchParams.set("audience", this.audience);
    const response = await fetchWithTimeout(
      this.transport,
      new Request(endpoint, {
        method: "GET",
        redirect: "manual",
        headers: { authorization: `Bearer ${requestToken}`, accept: "application/json" },
      }),
      this.timeoutMs,
    );
    if (!response || response.status < 200 || response.status >= 300) {
      stop(REASONS.PROOF);
    }
    const body = await responseJsonWithLimit(response, this.maxBytes);
    exactKeys(body, ["value"], REASONS.PROOF);
    if (typeof body.value !== "string" || body.value.length > 16_384 || body.value.split(".").length !== 3) {
      stop(REASONS.PROOF);
    }
    return body.value;
  }
}

export class G5TrustBrokerHttpClient {
  constructor({ endpoint, transport, dnsResolve, proofVerifier, policy, timeoutMs = 5_000, maxBytes = 16_384 } = {}) {
    if (typeof endpoint !== "string" || typeof transport?.fetch !== "function") stop(REASONS.CONFIG);
    if (!proofVerifier || typeof proofVerifier.verify !== "function") stop(REASONS.CONFIG);
    if (!positiveInteger(timeoutMs) || !positiveInteger(maxBytes)) stop(REASONS.CONFIG);
    this.endpoint = requireSafeHttpsUrl(endpoint);
    this.transport = transport;
    this.dnsResolve = dnsResolve;
    this.proofVerifier = proofVerifier;
    this.policy = validateRepositoryPolicy(policy);
    this.timeoutMs = timeoutMs;
    this.maxBytes = maxBytes;
  }

  static endpointFromConfig(config = {}) {
    if (!exactObject(config) || typeof config[TRUST_BROKER_ENDPOINT_CONFIG_NAME] !== "string") {
      stop(REASONS.CONFIG);
    }
    return config[TRUST_BROKER_ENDPOINT_CONFIG_NAME];
  }

  async authorize({ oidcToken, context }) {
    if (typeof oidcToken !== "string" || !exactObject(context)) stop(REASONS.AUTHORITY);
    const resolvedAddresses = await requirePublicDns(this.endpoint.hostname, this.dnsResolve);
    const response = await fetchWithTimeout(
      this.transport,
      new Request(this.endpoint, {
        method: "POST",
        redirect: "manual",
        headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify({
          bearerOidc: oidcToken,
          gateReference: { runId: context.runId, expectedRunAttempt: 1 },
        }),
      }),
      this.timeoutMs,
      resolvedAddresses,
    );
    if (!response || response.status < 200 || response.status >= 300) stop(REASONS.TRANSPORT);
    if (response.url && new URL(response.url).hostname.toLowerCase() !== this.endpoint.hostname.toLowerCase()) {
      stop(REASONS.TRANSPORT);
    }
    const body = await responseJsonWithLimit(response, this.maxBytes, this.timeoutMs);
    return validateTrustBrokerReceipt(body, context, this.policy, this.proofVerifier);
  }
}

async function verifyReceiptProof(proofVerifier, proof, receipt, receiptDigest) {
  exactKeys(proof, ["type", "keyId", "value"], REASONS.RECEIPT);
  if (proof.type !== "G5_TRUST_BROKER_RECEIPT_PROOF" || typeof proof.keyId !== "string" || typeof proof.value !== "string") {
    stop(REASONS.RECEIPT);
  }
  let verified;
  try {
    verified = await proofVerifier.verify({ proof, receipt, receiptDigest, version: VERSION });
  } catch {
    stop(REASONS.RECEIPT);
  }
  if (verified !== true) stop(REASONS.RECEIPT);
}

export async function validateTrustBrokerReceipt(body, context, policy, proofVerifier) {
  if (!proofVerifier || typeof proofVerifier.verify !== "function") stop(REASONS.RECEIPT);
  const trustedPolicy = validateRepositoryPolicy(policy);
  const nowEpochSeconds = Number.isSafeInteger(context?.nowEpochSeconds)
    ? context.nowEpochSeconds
    : Math.floor(Date.now() / 1000);
  exactKeys(body, ["version", "decision", "receiptDigest", "receipt", "proof"], REASONS.RECEIPT);
  if (body.version !== VERSION || body.decision !== "AUTHORIZED" || !digestText(body.receiptDigest)) stop(REASONS.RECEIPT);
  exactKeys(body.receipt, ["identity", "expiresAt", "binding"], REASONS.RECEIPT);
  if (typeof body.receipt.identity !== "string" || !positiveInteger(body.receipt.expiresAt)) stop(REASONS.RECEIPT);
  if (body.receipt.expiresAt <= nowEpochSeconds || body.receipt.expiresAt - nowEpochSeconds > MAX_TOKEN_LIFETIME_SECONDS) {
    stop(REASONS.EXPIRED);
  }
  const bindingKeys = [
    "repositoryId", "runId", "runAttempt", "checkRunId", "checkSuiteId", "jobId",
    "jobName", "environmentId", "deploymentId", "deploymentStatusId",
    "candidateSha", "candidateTree", "workflowSha", "workflowBlobSha",
    "contractDigest", "schemaDigest", "algorithmDigest", "capabilityDigest",
  ];
  exactKeys(body.receipt.binding, bindingKeys, REASONS.RECEIPT);
  const binding = body.receipt.binding;
  const expectedIds = {
    repositoryId: decimalId(context.repositoryId),
    runId: decimalId(context.runId),
    runAttempt: decimalId(context.runAttempt),
  };
  if (
    expectedIds.repositoryId === null || expectedIds.runId === null || expectedIds.runAttempt !== 1 ||
    binding.repositoryId !== expectedIds.repositoryId || binding.runId !== expectedIds.runId ||
    binding.runAttempt !== 1 || !positiveInteger(binding.checkRunId) ||
    !positiveInteger(binding.checkSuiteId) || !positiveInteger(binding.jobId) ||
    binding.jobName !== WORKFLOW_NAME || !positiveInteger(binding.environmentId) ||
    !positiveInteger(binding.deploymentId) || !positiveInteger(binding.deploymentStatusId) ||
    binding.candidateSha !== trustedPolicy.candidateSha ||
    binding.candidateTree !== trustedPolicy.candidateTree || binding.workflowSha !== trustedPolicy.candidateSha ||
    binding.workflowBlobSha !== trustedPolicy.workflowBlobSha || !digestText(binding.contractDigest) ||
    !digestText(binding.schemaDigest) || !digestText(binding.algorithmDigest) ||
    !digestText(binding.capabilityDigest)
  ) stop(REASONS.RECEIPT);
  if (context.checkRunId !== undefined && binding.checkRunId !== decimalId(context.checkRunId)) stop(REASONS.RECEIPT);
  if (context.checkSuiteId !== undefined && binding.checkSuiteId !== decimalId(context.checkSuiteId)) stop(REASONS.RECEIPT);
  if (context.jobId !== undefined && binding.jobId !== decimalId(context.jobId)) stop(REASONS.RECEIPT);
  if (context.environmentId !== undefined && binding.environmentId !== decimalId(context.environmentId)) stop(REASONS.RECEIPT);
  if (context.deploymentId !== undefined && binding.deploymentId !== decimalId(context.deploymentId)) stop(REASONS.RECEIPT);
  if (context.deploymentStatusId !== undefined && binding.deploymentStatusId !== decimalId(context.deploymentStatusId)) stop(REASONS.RECEIPT);
  if (await stableDigest(body.receipt) !== body.receiptDigest) stop(REASONS.RECEIPT);
  await verifyReceiptProof(proofVerifier, body.proof, body.receipt, body.receiptDigest);
  return Object.freeze({
    [VALIDATED_RECEIPT]: true,
    digest: body.receiptDigest,
    receipt: Object.freeze(body.receipt),
  });
}

export class G5SingleUseReceiptSession {
  constructor({ clock = () => Math.floor(Date.now() / 1000) } = {}) {
    if (typeof clock !== "function") stop(REASONS.CONFIG);
    this.clock = clock;
    this.used = false;
  }

  consume(receipt) {
    if (
      this.used || !exactObject(receipt) || receipt[VALIDATED_RECEIPT] !== true ||
      !digestText(receipt.digest) || !exactObject(receipt.receipt)
    ) {
      stop(REASONS.RECEIPT);
    }
    if (!positiveInteger(receipt.receipt.expiresAt) || receipt.receipt.expiresAt <= this.clock()) stop(REASONS.EXPIRED);
    this.used = true;
    return Object.freeze({ receiptDigest: receipt.digest });
  }
}

function validateSupabaseConfig(env) {
  if (!exactObject(env)) stop(REASONS.CONFIG);
  if (env.NEXT_SUPABASE_SECRET_KEY !== undefined || env.SUPABASE_SERVICE_ROLE_KEY !== undefined) {
    stop(REASONS.SUPABASE);
  }
  const url = env.NEXT_PUBLIC_SUPABASE_URL;
  const key = env.NEXT_SUPABASE_PUBLISHABLE_KEY;
  if (typeof url !== "string" || typeof key !== "string") stop(REASONS.CONFIG);
  if (!key.startsWith("sb_publishable_") || key.startsWith(SUPABASE_SECRET_KEY_PREFIX)) stop(REASONS.SUPABASE);
  return Object.freeze({ url: requireSafeHttpsUrl(url, REASONS.SUPABASE), key });
}

function supabaseHeaders(key) {
  return Object.freeze({ apikey: key, accept: "application/json" });
}

function tableColumns(table) {
  if (!Object.prototype.hasOwnProperty.call(SUPABASE_TABLES, table)) stop(REASONS.SUPABASE);
  return SUPABASE_TABLES[table];
}

function routingUrl(value) {
  if (typeof value !== "string" || value === "") stop(REASONS.PROFILE);
  const raw = value.includes("://") || value.startsWith("//") ? value : `https://${value}`;
  const parsed = requireSafeHttpsUrl(raw, REASONS.PROFILE);
  parsed.hash = "";
  parsed.hostname = normalizedHostname(parsed.hostname);
  const canonicalSearch = new URLSearchParams();
  for (const [key, item] of parsed.searchParams) {
    const lowered = key.toLowerCase();
    if (lowered.startsWith("utm_") || TRACKING_QUERY_KEYS.has(lowered)) continue;
    canonicalSearch.append(key, item);
  }
  parsed.search = canonicalSearch.toString();
  return parsed.href;
}

function routingList(value) {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string" || item === "")) {
    stop(REASONS.PROFILE);
  }
  return value;
}

function routingOptionalString(value) {
  if (value === null || typeof value === "string") return value;
  stop(REASONS.PROFILE);
}

function safeProfileRegex(pattern) {
  if (typeof pattern !== "string" || pattern.length > 200) return false;
  let escaped = false;
  for (const character of pattern) {
    if (escaped) {
      escaped = false;
      continue;
    }
    if (character === "\\") {
      escaped = true;
      continue;
    }
    if ("()|*+?{}".includes(character)) return false;
  }
  if (escaped) return false;
  try {
    new RegExp(pattern, "i");
  } catch {
    return false;
  }
  return true;
}

function validatedProfilePatterns(value) {
  const patterns = routingList(value);
  for (const pattern of patterns) {
    if (pattern.startsWith("re:") && !safeProfileRegex(pattern.slice(3))) stop(REASONS.PROFILE);
  }
  return patterns;
}

function profilePatternMatches(pattern, text) {
  if (pattern.startsWith("re:")) return new RegExp(pattern.slice(3), "i").test(text.slice(0, 2000));
  return text.toLowerCase().includes(pattern.toLowerCase());
}

function harvesterCandidateAllowed(url, websiteUrl, allowedPatterns, exclusionPatterns) {
  const parsed = new URL(url);
  const website = new URL(websiteUrl);
  if (parsed.host !== website.host || NON_HTML_EXTENSIONS.some((extension) => parsed.pathname.toLowerCase().endsWith(extension))) {
    return false;
  }
  const lowered = url.toLowerCase();
  if (exclusionPatterns.some((pattern) => profilePatternMatches(pattern, lowered))) return false;
  if (allowedPatterns.length === 0) return true;
  return allowedPatterns.some((pattern) => {
    const text = pattern.startsWith("re:") ? parsed.pathname : lowered;
    return profilePatternMatches(pattern, text);
  });
}

function orderedCanonicalUrls(values) {
  const seen = new Set();
  const result = [];
  for (const value of values) {
    const url = routingUrl(value);
    if (!seen.has(url)) {
      seen.add(url);
      result.push(url);
    }
  }
  return result;
}

function circuitEffectivelyOpen(profile, observedAt) {
  const openedAt = routingOptionalString(profile.circuit_opened_at);
  if (profile.circuit_open !== true || openedAt === null) return false;
  const parsed = new Date(openedAt);
  if (!Number.isFinite(parsed.getTime()) || !/(Z|\+00:00)$/.test(openedAt)) stop(REASONS.PROFILE);
  return observedAt.getTime() - parsed.getTime() < 24 * 60 * 60 * 1000;
}

function validateProfile(profile, institution, observedAt) {
  if (
    !exactObject(profile) || !exactObject(institution) ||
    typeof profile.institution_id !== "string" || profile.institution_id !== institution.id ||
    typeof institution.id !== "string" || typeof institution.website_url !== "string" ||
    typeof profile.discovery_enabled !== "boolean" || typeof profile.pipeline_ready !== "boolean" ||
    typeof profile.pipeline_enabled !== "boolean" || typeof profile.circuit_open !== "boolean" ||
    typeof profile.requires_cloudflare_bypass !== "boolean" ||
    typeof profile.site_type !== "string" || !SITE_TYPES.has(profile.site_type) ||
    typeof profile.discovery_mode !== "string" || !DISCOVERY_MODES.has(profile.discovery_mode) ||
    !Number.isSafeInteger(profile.catalog_max_pages)
  ) {
    stop(REASONS.PROFILE);
  }
  const websiteUrl = routingUrl(institution.website_url);
  return Object.freeze({
    websiteUrl,
    seeds: routingList(profile.seed_urls),
    catalogs: routingList(profile.catalog_url_patterns),
    allowed: validatedProfilePatterns(profile.allowed_url_patterns),
    exclusions: validatedProfilePatterns(profile.exclusion_patterns),
    warmupUrl: routingOptionalString(profile.warmup_url),
    eligible: profile.discovery_enabled && profile.pipeline_enabled && !circuitEffectivelyOpen(profile, observedAt),
  });
}

function addTarget(targets, seen, kind, value) {
  const url = routingUrl(value);
  const key = `${kind}\u0000${url}`;
  if (!seen.has(key)) {
    seen.add(key);
    targets.push(Object.freeze({ kind, url }));
  }
}

function deriveProfileTargets(profile, institution, observedAt) {
  const routing = validateProfile(profile, institution, observedAt);
  const targets = [];
  const seen = new Set();
  const browserRequired = profile.site_type === "spa_js_heavy" || profile.site_type === "ecommerce" || profile.discovery_mode === "catalog_link_extraction";
  if (!routing.eligible) return targets;
  if (browserRequired && profile.requires_cloudflare_bypass && routing.warmupUrl) {
    addTarget(targets, seen, "WARMUP", routing.warmupUrl);
  }
  if (profile.discovery_mode === "hardcoded_urls" && routing.seeds.length > 0) {
    if (routing.seeds.length > MAX_SOURCE_TARGETS) stop(REASONS.TARGET);
    for (const seed of orderedCanonicalUrls(routing.seeds)) {
      if (harvesterCandidateAllowed(seed, routing.websiteUrl, routing.allowed, routing.exclusions)) {
        addTarget(targets, seen, "HARDCODED_DETAIL", seed);
      }
    }
  } else if (profile.discovery_mode === "paginated_catalog" && routing.catalogs.length > 0) {
    if (profile.catalog_max_pages < 1 || profile.catalog_max_pages > MAX_SOURCE_TARGETS) stop(REASONS.TARGET);
    for (const template of routing.catalogs) {
      for (let page = 1; page <= profile.catalog_max_pages; page += 1) {
        addTarget(targets, seen, "CATALOG_PAGE", template.replace("{page}", String(page)));
      }
    }
  } else if (profile.discovery_mode === "catalog_link_extraction") {
    if (routing.seeds.length > MAX_SOURCE_TARGETS) stop(REASONS.TARGET);
    const roots = orderedCanonicalUrls(routing.seeds);
    if (!roots.includes(routing.websiteUrl)) roots.push(routing.websiteUrl);
    for (const root of roots) addTarget(targets, seen, "CATALOG_ROOT", root);
  } else {
    addTarget(targets, seen, "SITEMAP_ROOT", new URL("/sitemap.xml", routing.websiteUrl).href);
    addTarget(targets, seen, "BFS_ROOT", routing.websiteUrl);
  }
  if (targets.length > MAX_SOURCE_TARGETS) stop(REASONS.TARGET);
  return targets;
}

function deriveSourceTargets(profiles, institutions, observedAt = new Date()) {
  if (!Array.isArray(profiles) || !Array.isArray(institutions) || !Number.isFinite(observedAt.getTime())) stop(REASONS.PROFILE);
  const targets = [];
  const profileInstitutions = new Set();
  for (const profile of profiles) {
    if (!exactObject(profile) || typeof profile.institution_id !== "string") stop(REASONS.PROFILE);
    if (profileInstitutions.has(profile.institution_id)) stop(REASONS.PROFILE);
    profileInstitutions.add(profile.institution_id);
    const matches = institutions.filter((institution) => institution.id === profile?.institution_id);
    if (matches.length !== 1) stop(REASONS.PROFILE);
    targets.push(...deriveProfileTargets(profile, matches[0], observedAt));
    if (targets.length > MAX_PROFILE_SOURCE_PAIRS) stop(REASONS.TARGET);
  }
  return targets;
}

export class G5ConnectedSupabaseCollector {
  constructor({ env = {}, transport, dnsResolve, sourceTransport, receiptStore, timeoutMs = STRICT_TIMEOUT_MS } = {}) {
    if (typeof transport?.fetch !== "function") stop(REASONS.CONFIG);
    if (!positiveInteger(timeoutMs) || timeoutMs > STRICT_TIMEOUT_MS) stop(REASONS.CONFIG);
    const config = validateSupabaseConfig(env);
    if (
      !receiptStore || receiptStore.capability !== "DURABLE_SINGLE_USE_RECEIPT_LEDGER" ||
      typeof receiptStore.consumeOnce !== "function"
    ) stop(REASONS.CONFIG);
    this.baseUrl = config.url;
    this.key = config.key;
    this.transport = transport;
    this.dnsResolve = dnsResolve;
    this.sourceTransport = sourceTransport;
    this.timeoutMs = timeoutMs;
    this.receiptStore = receiptStore;
  }

  async collect({ receipt, sourceTargets = [] } = {}) {
    if (!Array.isArray(sourceTargets)) stop(REASONS.SOURCE);
    if (sourceTargets.length !== 0) stop(REASONS.SOURCE);
    const session = new G5SingleUseReceiptSession();
    const consumed = session.consume(receipt);
    let stored;
    try {
      stored = await this.receiptStore.consumeOnce(consumed.receiptDigest, receipt.receipt.expiresAt);
    } catch {
      stop(REASONS.REPLAY);
    }
    if (stored !== true) stop(REASONS.REPLAY);
    this.resolvedAddresses = await requirePublicDns(this.baseUrl.hostname, this.dnsResolve);
    const first = await this.snapshot();
    const targets = deriveSourceTargets(first.tables.institution_site_profiles, first.tables.institutions);
    const sourceSummary = await this.observeSources(targets);
    const second = await this.snapshot();
    if (stable(first.counts) !== stable(second.counts)) stop(REASONS.COUNT);
    const firstDigest = await stableDigest(first.tables);
    const secondDigest = await stableDigest(second.tables);
    if (firstDigest !== secondDigest) stop(REASONS.SNAPSHOT);
    return Object.freeze({
      version: VERSION,
      decision: sourceSummary.blocking === 0 ? "PASS" : "STOP",
      reasonCode: sourceSummary.blocking === 0 ? null : REASONS.SOURCE,
      receiptDigest: consumed.receiptDigest,
      authorizationComplete: false,
      transportCreated: false,
      connectedMode: CONNECTED_DISABLED,
      operationalTrust: TRUST_STOP,
    });
  }

  async snapshot() {
    const tables = {};
    const counts = {};
    let totalRows = 0;
    let totalBytes = 0;
    for (const table of Object.keys(SUPABASE_TABLES).sort()) {
      const result = await this.collectTable(table, MAX_ROWS - totalRows, MAX_RESPONSE_BYTES - totalBytes);
      tables[table] = result.rows;
      counts[table] = result.rows.length;
      totalRows += result.rows.length;
      totalBytes += result.bytes;
      if (totalRows > MAX_ROWS || totalBytes > MAX_RESPONSE_BYTES) stop(REASONS.PAGINATION);
    }
    return Object.freeze({ tables: Object.freeze(tables), counts: Object.freeze(counts) });
  }

  async countTable(table) {
    const url = new URL(`/rest/v1/${table}`, this.baseUrl);
    url.searchParams.set("select", "id");
    url.searchParams.set("order", "id.asc");
    url.searchParams.set("limit", "1");
    const response = await this.supabaseGet(url, { prefer: "count=exact" });
    const contentRange = lowerHeader(response.headers, "content-range");
    if (typeof contentRange === "string") {
      const match = contentRange.match(/\/(\d+)$/);
      if (match) return Number(match[1]);
    }
    stop(REASONS.PAGINATION);
  }

  async selectPage(table, afterId, maxBytes) {
    if (!Number.isSafeInteger(maxBytes) || maxBytes <= 0) stop(REASONS.PAGINATION);
    const url = new URL(`/rest/v1/${table}`, this.baseUrl);
    url.searchParams.set("select", tableColumns(table));
    url.searchParams.set("order", "id.asc");
    url.searchParams.set("limit", String(PAGE_SIZE));
    if (afterId !== null) url.searchParams.set("id", `gt.${afterId}`);
    const response = await this.supabaseGet(url);
    const body = await responseJsonWithLimit(response, maxBytes, this.timeoutMs);
    if (!Array.isArray(body)) stop(REASONS.PAGINATION);
    return body;
  }

  async supabaseGet(url, extraHeaders = {}) {
    const headers = { ...supabaseHeaders(this.key), ...extraHeaders };
    if (Object.keys(headers).some((key) => key.toLowerCase() === "authorization")) stop(REASONS.SUPABASE);
    const response = await fetchWithTimeout(
      this.transport,
      new Request(url, { method: "GET", redirect: "manual", headers }),
      this.timeoutMs,
      this.resolvedAddresses,
    );
    if (!response || response.status < 200 || response.status >= 300 || response.url && new URL(response.url).hostname !== this.baseUrl.hostname) {
      stop(REASONS.TRANSPORT);
    }
    return response;
  }

  async collectTable(table, maxRows, maxBytes) {
    if (!Number.isSafeInteger(maxRows) || maxRows < 0 || !Number.isSafeInteger(maxBytes) || maxBytes < 0) {
      stop(REASONS.PAGINATION);
    }
    const initialCount = await this.countTable(table);
    if (!Number.isSafeInteger(initialCount) || initialCount < 0 || initialCount > maxRows) stop(REASONS.PAGINATION);
    const rows = [];
    let bytes = 0;
    let pages = 0;
    let afterId = null;
    while (rows.length < initialCount) {
      if (pages >= MAX_PAGES) stop(REASONS.PAGINATION);
      const page = await this.selectPage(table, afterId, maxBytes - bytes);
      if (page.length === 0 || page.length > PAGE_SIZE) stop(REASONS.PAGINATION);
      for (const row of page) {
        if (!exactObject(row) || typeof row.id !== "string" || row.id === "" || afterId !== null && row.id <= afterId) {
          stop(REASONS.PAGINATION);
        }
        const expected = tableColumns(table).split(",").sort();
        if (stable(Object.keys(row).sort()) !== stable(expected)) stop(REASONS.SUPABASE);
        bytes += new TextEncoder().encode(stable(row)).byteLength;
        if (bytes > maxBytes) stop(REASONS.PAGINATION);
        rows.push(Object.freeze({ ...row }));
        afterId = row.id;
      }
      pages += 1;
    }
    if (await this.countTable(table) !== initialCount) stop(REASONS.COUNT);
    if (rows.length !== initialCount) stop(REASONS.PAGINATION);
    return Object.freeze({ rows: Object.freeze(rows), pages, bytes });
  }

  async observeSources(targets) {
    if (!Array.isArray(targets)) stop(REASONS.SOURCE);
    if (targets.length > MAX_PROFILE_SOURCE_PAIRS) stop(REASONS.TARGET);
    if (targets.length === 0) return Object.freeze({ blocking: 0 });
    if (!this.sourceTransport || typeof this.sourceTransport.requestPinned !== "function") stop(REASONS.SOURCE);
    let blocking = 0;
    for (const target of targets) {
      if (!exactObject(target) || typeof target.url !== "string" || typeof target.kind !== "string") stop(REASONS.TARGET);
      const url = requireSafeHttpsUrl(target.url, REASONS.SOURCE);
      const resolvedAddresses = await requirePublicDns(url.hostname, this.dnsResolve);
      const head = await this.sourceRequest("HEAD", url, resolvedAddresses);
      if (head.status >= 200 && head.status < 300) continue;
      if (![403, 405, 501].includes(head.status)) {
        blocking += 1;
        continue;
      }
      const get = await this.sourceRequest("GET", url, resolvedAddresses);
      if (!(get.status >= 200 && get.status < 300)) blocking += 1;
    }
    return Object.freeze({ blocking });
  }

  async sourceRequest(method, url, resolvedAddresses) {
    let result;
    try {
      if (typeof this.sourceTransport.requestPinned !== "function") stop(REASONS.SOURCE);
      result = await this.sourceTransport.requestPinned({ method, url: String(url), timeoutMs: this.timeoutMs, maxBytes: MAX_RESPONSE_BYTES, resolvedAddresses });
    } catch {
      stop(REASONS.SOURCE);
    }
    if (!exactObject(result) || !Number.isSafeInteger(result.status) || result.status < 100 || result.status > 599 || result.redirected !== false) stop(REASONS.SOURCE);
    return result;
  }
}

function validateAuthority(claims, evidence, policy) {
  const { run, check, branch, deployment, environment, approval, commit, workflowBlob } = evidence;
  const expectedCheckRunUrl = `${GITHUB_API_REPOSITORY_URL}/check-runs/${check?.id}`;
  if (
    !exactObject(policy) || policy.repository !== REPOSITORY ||
    policy.workflowRef !== WORKFLOW_REF || policy.candidateSha !== claims.candidateSha ||
    policy.candidateTree !== commit.tree || policy.workflowBlobSha !== workflowBlob.blobSha ||
    run.id !== claims.runId || run.repositoryId !== claims.repositoryId ||
    run.ownerId !== claims.ownerId || run.repository !== claims.repository ||
    run.ref !== claims.ref || branch.name !== MAIN_BRANCH || branch.protected !== true ||
    run.attempt !== 1 || run.event !== "workflow_dispatch" ||
    run.headSha !== claims.candidateSha || run.actorId !== claims.actorId ||
    !positiveInteger(run.triggeringActorId) || run.status !== "in_progress" || run.conclusion !== null ||
    check.runId !== run.id || check.runAttempt !== 1 || !positiveInteger(check.id) ||
    !positiveInteger(check.checkSuiteId) || !positiveInteger(check.jobId) ||
    check.headSha !== claims.candidateSha || check.checkRunUrl !== expectedCheckRunUrl ||
    check.name !== "F10.9 G5 Production Read-Only Diagnostic" ||
    check.jobStatus !== "in_progress" || check.jobConclusion !== null ||
    check.checkName !== check.name || check.checkHeadSha !== claims.candidateSha ||
    check.checkStatus !== "in_progress" || check.checkConclusion !== null ||
    check.checkAppSlug !== GITHUB_ACTIONS_APP_SLUG || check.checkAppName !== GITHUB_ACTIONS_APP_NAME ||
    check.checkAppId !== GITHUB_ACTIONS_APP_ID || check.checkAppOwnerId !== GITHUB_ACTIONS_APP_OWNER_ID ||
    deployment.runId !== run.id || deployment.jobId !== check.jobId || deployment.statusState !== "in_progress" ||
    deployment.sha !== claims.candidateSha || deployment.environment !== ENVIRONMENT || !positiveInteger(deployment.id) ||
    !positiveInteger(deployment.deploymentStatusId) ||
    environment.name !== ENVIRONMENT || !positiveInteger(environment.id) || environment.protected !== true ||
    commit.sha !== claims.candidateSha ||
    !/^[0-9a-f]{40}$/.test(commit.tree) || workflowBlob.ref !== claims.workflowRef ||
    workflowBlob.workflowSha !== claims.workflowSha || !/^[0-9a-f]{40}$/.test(workflowBlob.blobSha)
  ) stop(REASONS.BINDING);
  if (
    approval.runId !== run.id || approval.environmentId !== environment.id ||
    approval.environment !== ENVIRONMENT || approval.state !== "approved" || !positiveInteger(approval.reviewerId) ||
    approval.reviewerId === claims.actorId || approval.reviewerId === run.triggeringActorId
  ) stop(REASONS.APPROVAL);
  return Object.freeze({
    repositoryId: claims.repositoryId, runId: run.id, runAttempt: run.attempt,
    checkRunId: check.id, checkSuiteId: check.checkSuiteId, jobId: check.jobId,
    environmentId: environment.id, deploymentId: deployment.id,
    deploymentStatusId: deployment.deploymentStatusId,
    candidateSha: claims.candidateSha, candidateTree: commit.tree,
    workflowRef: claims.workflowRef, workflowSha: claims.workflowSha,
    workflowBlobSha: workflowBlob.blobSha, actorId: claims.actorId,
    triggeringActorId: run.triggeringActorId, reviewerId: approval.reviewerId,
    nonce: claims.nonce, jti: claims.jti, expiresAt: claims.expiresAt,
  });
}

function terminalBinding(binding) {
  return Object.freeze({
    repositoryId: binding.repositoryId,
    runId: binding.runId,
    runAttempt: binding.runAttempt,
    checkRunId: binding.checkRunId,
    checkSuiteId: binding.checkSuiteId,
    jobId: binding.jobId,
    deploymentId: binding.deploymentId,
    deploymentStatusId: binding.deploymentStatusId,
  });
}

function validateTerminalAuthority(claims, evidence, expectedBinding) {
  const { run, check, deployment } = evidence;
  if (
    !exactObject(expectedBinding) ||
    run.id !== claims.runId || run.repositoryId !== claims.repositoryId ||
    run.ownerId !== claims.ownerId || run.repository !== claims.repository ||
    run.ref !== claims.ref || run.attempt !== 1 || run.event !== "workflow_dispatch" ||
    run.headSha !== claims.candidateSha || run.actorId !== claims.actorId ||
    !positiveInteger(run.triggeringActorId) || run.status !== "in_progress" || run.conclusion !== null ||
    check.runId !== run.id || check.runAttempt !== 1 || check.id !== expectedBinding.checkRunId ||
    check.checkSuiteId !== expectedBinding.checkSuiteId || check.jobId !== expectedBinding.jobId ||
    check.headSha !== claims.candidateSha || check.name !== WORKFLOW_NAME ||
    check.jobStatus !== "in_progress" || check.jobConclusion !== null ||
    check.checkHeadSha !== claims.candidateSha || check.checkName !== WORKFLOW_NAME ||
    check.checkStatus !== "in_progress" || check.checkConclusion !== null ||
    check.checkAppSlug !== GITHUB_ACTIONS_APP_SLUG || check.checkAppName !== GITHUB_ACTIONS_APP_NAME ||
    check.checkAppId !== GITHUB_ACTIONS_APP_ID || check.checkAppOwnerId !== GITHUB_ACTIONS_APP_OWNER_ID ||
    deployment.runId !== run.id || deployment.jobId !== check.jobId || deployment.id !== expectedBinding.deploymentId ||
    deployment.deploymentStatusId !== expectedBinding.deploymentStatusId || deployment.statusState !== "in_progress" ||
    deployment.sha !== claims.candidateSha || deployment.environment !== ENVIRONMENT
  ) stop(REASONS.BINDING);
  return terminalBinding(expectedBinding);
}

export async function gateIdentity(binding) {
  return digest([
    binding.repositoryId, binding.runId, binding.runAttempt, binding.checkRunId,
    binding.checkSuiteId, binding.jobId, binding.environmentId, binding.deploymentId,
    binding.deploymentStatusId,
  ]);
}

function validateLedgerBinding(binding, policy) {
  const trustedPolicy = validateRepositoryPolicy(policy);
  if (!exactObject(binding)) stop(REASONS.LEDGER);
  const expectedKeys = [
    "actorId", "candidateSha", "candidateTree", "checkRunId", "checkSuiteId",
    "deploymentId", "deploymentStatusId", "environmentId", "expiresAt", "jobId",
    "jti", "nonce", "repositoryId", "reviewerId", "runAttempt", "runId",
    "triggeringActorId", "workflowBlobSha", "workflowRef", "workflowSha",
  ];
  if (stable(Object.keys(binding).sort()) !== stable(expectedKeys)) stop(REASONS.LEDGER);
  for (const field of [
    "actorId", "checkRunId", "checkSuiteId", "deploymentId", "deploymentStatusId",
    "environmentId", "expiresAt", "jobId", "repositoryId", "reviewerId", "runAttempt",
    "runId", "triggeringActorId",
  ]) {
    if (!positiveInteger(binding[field])) stop(REASONS.LEDGER);
  }
  if (
    binding.runAttempt !== 1 ||
    typeof binding.nonce !== "string" || !/^sha256:[0-9a-f]{64}$/.test(binding.nonce) ||
    typeof binding.jti !== "string" || binding.jti.length < 16 || binding.jti.length > 256 ||
    binding.workflowRef !== WORKFLOW_REF || binding.workflowSha !== trustedPolicy.candidateSha ||
    binding.candidateSha !== trustedPolicy.candidateSha ||
    binding.candidateTree !== trustedPolicy.candidateTree ||
    binding.workflowBlobSha !== trustedPolicy.workflowBlobSha
  ) stop(REASONS.LEDGER);
}

function sanitizedGateBinding(binding) {
  if (binding === null) return null;
  return Object.freeze({
    repositoryId: binding.repositoryId,
    runId: binding.runId,
    runAttempt: binding.runAttempt,
    checkRunId: binding.checkRunId,
    checkSuiteId: binding.checkSuiteId,
    jobId: binding.jobId,
    environmentId: binding.environmentId,
    deploymentId: binding.deploymentId,
    deploymentStatusId: binding.deploymentStatusId,
  });
}

function publicResult(decision, reasonCode, receiptDigest = null, binding = null) {
  return Object.freeze({
    version: VERSION, decision, reasonCode, receiptDigest,
    gateBinding: sanitizedGateBinding(binding),
    authorizationComplete: false, transportCreated: false,
    connectedMode: CONNECTED_DISABLED, operationalTrust: TRUST_STOP,
  });
}

export class G5AtomicLedgerDurableObject extends DurableObjectBase {
  constructor(state, env = {}) {
    super(state, env);
    if (!state?.storage || typeof state.storage.transaction !== "function") stop(REASONS.AUTHORITY);
    this.storage = state.storage;
    this.policy = validateRepositoryPolicy(env.policy ?? repositoryPolicyFromRuntimeBindings(env));
    this.clock = typeof env.clock === "function" ? env.clock : () => Math.floor(Date.now() / 1000);
  }

  async consume(binding) {
    validateLedgerBinding(binding, this.policy);
    const identity = await gateIdentity(binding);
    const gateKey = `gate:${identity}`;
    const nonceKey = `nonce:${await digest(binding.nonce)}`;
    const jtiKey = `jti:${await digest(binding.jti)}`;
    const outcome = await this.storage.transaction(async (transaction) => {
      const nowEpochSeconds = this.clock();
      if (!Number.isSafeInteger(nowEpochSeconds)) stop(REASONS.LEDGER);
      const current = await transaction.get(gateKey);
      if (current?.state === "CONSUMED") stop(REASONS.REPLAY);
      if (current?.state === "EXPIRED") stop(REASONS.EXPIRED);
      if (current !== undefined) stop(REASONS.LEDGER);
      const storedRecordCount = await transaction.get("record_count");
      const recordCount = storedRecordCount === undefined ? 0 : storedRecordCount;
      if (!Number.isSafeInteger(recordCount) || recordCount < 0 || recordCount > MAX_LEDGER_RECORDS) {
        stop(REASONS.LEDGER);
      }
      if (nowEpochSeconds >= binding.expiresAt) {
        if (recordCount + 1 > MAX_LEDGER_RECORDS) stop(REASONS.LEDGER);
        await transaction.put(
          gateKey,
          Object.freeze({ state: "EXPIRED", identity, expiredAt: nowEpochSeconds }),
        );
        await transaction.put("record_count", recordCount + 1);
        return Object.freeze({ stop: REASONS.EXPIRED });
      }
      const nonceOwner = await transaction.get(nonceKey);
      const jtiOwner = await transaction.get(jtiKey);
      if (nonceOwner !== undefined || jtiOwner !== undefined) stop(REASONS.REPLAY);
      if (recordCount + 3 > MAX_LEDGER_RECORDS) stop(REASONS.LEDGER);
      await transaction.put(
        gateKey,
        Object.freeze({ state: "READY", identity, expiresAt: binding.expiresAt }),
      );
      await transaction.put(nonceKey, identity);
      await transaction.put(jtiKey, identity);
      await transaction.put("record_count", recordCount + 3);
      const receiptMaterial = Object.freeze({
        identity, from: "ABSENT", via: "READY", to: "CONSUMED",
        binding: sanitizedGateBinding(binding), bindingDigest: await digest(binding),
        nonceDigest: await digest(binding.nonce), jtiDigest: await digest(binding.jti),
        consumedAt: nowEpochSeconds, expiresAt: binding.expiresAt, policyVersion: VERSION,
      });
      const receiptDigest = await digest(receiptMaterial);
      await transaction.put(gateKey, Object.freeze({
        state: "CONSUMED", identity, expiresAt: binding.expiresAt,
        binding: sanitizedGateBinding(binding),
        receiptDigest, receipt: receiptMaterial,
      }));
      return Object.freeze({ result: publicResult("STOP", TRUST_STOP, receiptDigest, binding) });
    });
    if (outcome.stop) stop(outcome.stop);
    return outcome.result;
  }

  async cleanup(identity) {
    if (typeof identity !== "string" || !/^sha256:[0-9a-f]{64}$/.test(identity)) {
      stop(REASONS.LEDGER);
    }
    return this.storage.transaction(async (transaction) => {
      const gateKey = `gate:${identity}`;
      const current = await transaction.get(gateKey);
      if (current === undefined) return "ABSENT";
      if (!exactObject(current) || current.identity !== identity) stop(REASONS.LEDGER);
      if (current.state === "CONSUMED" || current.state === "EXPIRED") return current.state;
      if (
        current.state !== "READY" || current.identity !== identity ||
        !positiveInteger(current.expiresAt)
      ) stop(REASONS.LEDGER);
      const nowEpochSeconds = this.clock();
      if (nowEpochSeconds >= current.expiresAt) {
        await transaction.put(
          gateKey,
          Object.freeze({ state: "EXPIRED", identity, expiredAt: nowEpochSeconds }),
        );
        return "EXPIRED";
      }
      return current.state;
    });
  }

  async receipt(identity) {
    if (typeof identity !== "string" || !/^sha256:[0-9a-f]{64}$/.test(identity)) {
      stop(REASONS.LEDGER);
    }
    const current = await this.storage.get(`gate:${identity}`);
    if (current === undefined) return null;
    if (!exactObject(current)) stop(REASONS.LEDGER);
    if (current.state !== "CONSUMED") return null;
    if (
      current.identity !== identity || !exactObject(current.receipt) ||
      current.receipt.identity !== identity || await digest(current.receipt) !== current.receiptDigest
    ) stop(REASONS.LEDGER);
    return current.receiptDigest;
  }
}

export class G5TrustBroker {
  constructor({ jwks, githubApp, ledger, clock, policy }) {
    this.jwks = jwks;
    this.githubApp = githubApp;
    this.ledger = ledger;
    this.policy = validateRepositoryPolicy(policy);
    this.clock = clock;
  }

  async authorize(request, hooks = {}) {
    rejectCallerAuthority(request);
    if (typeof this.clock !== "function") stop(REASONS.AUTHORITY);
    const claims = await verifyGithubOidc(request.bearerOidc, this.jwks, this.clock());
    if (claims.runId !== request.gateReference.runId || claims.runAttempt !== 1) stop(REASONS.BINDING);
    const evidenceA = await this.githubApp.authoritativeEvidence(claims);
    const bindingA = validateAuthority(claims, evidenceA, this.policy);
    if (!this.ledger || typeof this.ledger.consume !== "function") stop(REASONS.AUTHORITY);
    if (hooks.beforeCas) await hooks.beforeCas();
    if (hooks.beforeSnapshotB) await hooks.beforeSnapshotB();
    const evidenceB = await this.githubApp.authoritativeEvidence(claims);
    const bindingB = validateAuthority(claims, evidenceB, this.policy);
    if (stable(bindingA) !== stable(bindingB)) stop(REASONS.BINDING);
    if (hooks.beforeTerminalConfirmation) await hooks.beforeTerminalConfirmation();
    if (typeof this.githubApp.terminalEvidence !== "function") stop(REASONS.AUTHORITY);
    const terminalEvidence = await this.githubApp.terminalEvidence(claims, bindingB);
    if (stable(validateTerminalAuthority(claims, terminalEvidence, bindingB)) !== stable(terminalBinding(bindingB))) {
      stop(REASONS.BINDING);
    }
    let result;
    try {
      result = await this.ledger.consume(bindingB);
    } catch (error) {
      const reason = publicReasonFromError(error);
      if (reason) stop(reason);
      throw error;
    }
    if (hooks.afterCas) await hooks.afterCas();
    return result;
  }
}

export default {
  async fetch(request, env) {
    if (request.method !== "POST" || new URL(request.url).pathname !== "/authorize") {
      return Response.json(publicResult("STOP", REASONS.AUTHORITY), { status: 404 });
    }
    try {
      const body = await request.json();
      const endpointApproved = endpointApprovedFromRuntimeBindings(env);
      const policy = requireRuntimeReady(env, { endpointApproved });
      const githubApp = env.G5_GITHUB_APP_READ_ONLY
        ? new GithubAppReadOnlyAdapter(env.G5_GITHUB_APP_READ_ONLY)
        : new G5ConnectedGithubAppAdapter({
          env,
          transport: env.G5_GITHUB_TRANSPORT ?? { fetch: globalThis.fetch?.bind(globalThis) },
          policy,
          endpointApproved,
        });
      if (!env.G5_ATOMIC_LEDGER || typeof env.G5_ATOMIC_LEDGER.getByName !== "function") stop(REASONS.LEDGER);
      const broker = new G5TrustBroker({
        jwks: env.G5_OFFLINE_JWKS,
        githubApp,
        ledger: env.G5_ATOMIC_LEDGER.getByName("g5-atomic-ledger-v1"),
        policy,
        clock: () => Math.floor(Date.now() / 1000),
      });
      return Response.json(await broker.authorize(body));
    } catch (error) {
      const reason = publicReasonFromError(error) ?? REASONS.AMBIGUOUS;
      return Response.json(publicResult("STOP", reason), { status: 400 });
    }
  },
};

export async function runG5ConnectedDiagnosticCli({ argv, env } = {}) {
  const args = argv ?? globalThis.process?.argv ?? [];
  const variables = env ?? globalThis.process?.env ?? {};
  if (!Array.isArray(args) || !args.includes("--g5-connected-diagnostic")) return null;
  const guard = g5WorkflowGuard({
    vars: variables,
    ref: variables.GITHUB_REF,
    runAttempt: Number(variables.GITHUB_RUN_ATTEMPT ?? 0),
  });
  const reason = guard.enabled ? REASONS.CONFIG : REASONS.CONFIG;
  return publicResult("STOP", reason);
}

if (globalThis.process?.argv?.includes("--g5-connected-diagnostic")) {
  const result = await runG5ConnectedDiagnosticCli();
  globalThis.console?.log(JSON.stringify(result));
  globalThis.process.exitCode = result?.decision === "PASS" ? 0 : 1;
}

export const INTERNALS = Object.freeze({
  VERSION, ISSUER, AUDIENCE, MAIN_REF, MAIN_BRANCH, ENVIRONMENT, REPOSITORY, WORKFLOW_REF,
  WORKFLOW_NAME, CONNECTED_DISABLED, TRUST_BROKER_ENDPOINT_CONFIG_NAME,
  RUNTIME_ENABLED_CONFIG_NAME, RUNTIME_POLICY_BINDING_NAMES, GITHUB_APP_CONFIG_NAMES,
  LEGACY_POLICY_DENYLIST, MANUAL_WORKFLOW_POLICY, SUPABASE_TABLES,
  GITHUB_ACTIONS_APP_ID, GITHUB_ACTIONS_APP_OWNER_ID,
  MAX_TOKEN_LIFETIME_SECONDS, MAX_LEDGER_RECORDS, STRICT_TIMEOUT_MS, MAX_RESPONSE_BYTES,
  MAX_GITHUB_RESPONSE_BYTES, MAX_GITHUB_TOKEN_RESPONSE_BYTES, JWKS_CACHE_SECONDS,
  PAGE_SIZE, MAX_PAGES, MAX_ROWS,
});
