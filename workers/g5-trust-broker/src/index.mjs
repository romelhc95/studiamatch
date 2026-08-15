const VERSION = "f10.9-g5-trust-broker.v2";
const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "studiamatch-f10-9-g5-production-trust-plane";
const MAIN_REF = "refs/heads/main";
const ENVIRONMENT = "Production";
const REPOSITORY = "romelhc95/studiamatch";
const WORKFLOW_PATH = ".github/workflows/g5-manual-trust-gate.yml";
const WORKFLOW_NAME = "F10.9 G5 Production Read-Only Diagnostic";
const WORKFLOW_REF = `${REPOSITORY}/${WORKFLOW_PATH}@${MAIN_REF}`;
const CONNECTED_DISABLED = "IMPLEMENTED_DISABLED_NOT_CONFIGURED";
const CONNECTED_STOP = CONNECTED_DISABLED;
const TRUST_STOP = "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED";
const CONFIG_STOP = "STOP_G5_CONNECTED_MODE_DISABLED_NOT_CONFIGURED";
const MAX_TOKEN_LIFETIME_SECONDS = 600;
const MAX_LEDGER_RECORDS = 10_000;
const STRICT_TIMEOUT_MS = 15_000;
const MAX_RESPONSE_BYTES = 32_000_000;
const PAGE_SIZE = 1_000;
const MAX_PAGES = 50;
const MAX_ROWS = 50_000;
const MAX_SOURCE_TARGETS = 64;
const MAX_PROFILE_SOURCE_PAIRS = 50_000;
const TRUST_BROKER_ENDPOINT_CONFIG_NAME = "G5_TRUST_BROKER_ENDPOINT";
const SUPABASE_SECRET_KEY_PREFIX = ["sb", "secret", ""].join("_");
const GITHUB_ACTIONS_OIDC_HOST = "token.actions.githubusercontent.com";
const VALIDATED_RECEIPT = Symbol("g5.validatedReceipt");
const REPOSITORY_POLICY = Object.freeze({
  repository: REPOSITORY,
  workflowRef: WORKFLOW_REF,
  candidateSha: "74defb6326d8432bf790cb84b4aa549fefc425be",
  candidateTree: "b9b4cc8a6f8279f898b2b8bf2a900c56a741b528",
  workflowBlobSha: "992308681c31dd5b2be3ab9c3fb1d20369120d92",
});
const MANUAL_WORKFLOW_POLICY = Object.freeze({
  state: "DEPLOYMENT_READY_DISABLED_NOT_CONFIGURED",
  dispatchDefined: true,
  operationalGuard: "vars.G5_TRUST_OPERATIONAL_ENABLED == 'true'",
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
  "deployment_id", "approver_id", "workflow_sha", "workflow_blob_sha",
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

export class GithubAppReadOnlyAdapter {
  constructor(transport) {
    const methods = [
      "getWorkflowRun", "listWorkflowJobs", "listDeployments", "getEnvironment",
      "listApprovals", "getCommit", "getWorkflowBlob",
    ];
    if (!transport || methods.some((method) => typeof transport[method] !== "function")) {
      stop(REASONS.AUTHORITY);
    }
    this.transport = transport;
  }

  async authoritativeEvidence(claims) {
    const reference = Object.freeze({
      repository: claims.repository, runId: claims.runId, runAttempt: claims.runAttempt,
      candidateSha: claims.candidateSha, workflowRef: claims.workflowRef,
      environment: claims.environment,
    });
    const [run, check, deployment, environment, approval, commit, workflowBlob] = await Promise.all([
      this.transport.getWorkflowRun(reference),
      this.transport.listWorkflowJobs(reference),
      this.transport.listDeployments(reference),
      this.transport.getEnvironment(reference),
      this.transport.listApprovals(reference),
      this.transport.getCommit(reference),
      this.transport.getWorkflowBlob(reference),
    ]).then((groups) => groups.map((group, index) => exactOneComplete(
      group,
      index === 4 ? REASONS.APPROVAL : REASONS.BINDING,
    )));
    return Object.freeze({ run, check, deployment, environment, approval, commit, workflowBlob });
  }
}

export class G5ConnectedGithubAppAdapter {
  constructor(options = {}) {
    if (!exactObject(options) || options.enabled !== false) stop(CONNECTED_STOP);
    this.state = CONNECTED_DISABLED;
  }

  async authoritativeEvidence(claims) {
    void claims;
    stop(CONNECTED_STOP);
  }
}

export function createDisabledConnectedGithubAppAdapter(options = Object.freeze({ enabled: false })) {
  return new G5ConnectedGithubAppAdapter(options);
}

export function g5WorkflowGuard({ vars = {}, ref, runAttempt } = {}) {
  const enabled = vars.G5_TRUST_OPERATIONAL_ENABLED === "true";
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
  constructor({ endpoint, transport, dnsResolve, proofVerifier, timeoutMs = 5_000, maxBytes = 16_384 } = {}) {
    if (typeof endpoint !== "string" || typeof transport?.fetch !== "function") stop(REASONS.CONFIG);
    if (!proofVerifier || typeof proofVerifier.verify !== "function") stop(REASONS.CONFIG);
    if (!positiveInteger(timeoutMs) || !positiveInteger(maxBytes)) stop(REASONS.CONFIG);
    this.endpoint = requireSafeHttpsUrl(endpoint);
    this.transport = transport;
    this.dnsResolve = dnsResolve;
    this.proofVerifier = proofVerifier;
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
    return validateTrustBrokerReceipt(body, context, REPOSITORY_POLICY, this.proofVerifier);
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

export async function validateTrustBrokerReceipt(body, context, policy = REPOSITORY_POLICY, proofVerifier) {
  if (!proofVerifier || typeof proofVerifier.verify !== "function") stop(REASONS.RECEIPT);
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
    "repositoryId", "runId", "runAttempt", "checkRunId", "jobName", "environmentId",
    "deploymentId", "candidateSha", "candidateTree", "workflowSha", "workflowBlobSha",
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
    binding.jobName !== WORKFLOW_NAME || !positiveInteger(binding.environmentId) ||
    !positiveInteger(binding.deploymentId) || binding.candidateSha !== policy.candidateSha ||
    binding.candidateTree !== policy.candidateTree || binding.workflowSha !== policy.candidateSha ||
    binding.workflowBlobSha !== policy.workflowBlobSha || !digestText(binding.contractDigest) ||
    !digestText(binding.schemaDigest) || !digestText(binding.algorithmDigest) ||
    !digestText(binding.capabilityDigest)
  ) stop(REASONS.RECEIPT);
  if (context.checkRunId !== undefined && binding.checkRunId !== decimalId(context.checkRunId)) stop(REASONS.RECEIPT);
  if (context.environmentId !== undefined && binding.environmentId !== decimalId(context.environmentId)) stop(REASONS.RECEIPT);
  if (context.deploymentId !== undefined && binding.deploymentId !== decimalId(context.deploymentId)) stop(REASONS.RECEIPT);
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
  const { run, check, deployment, environment, approval, commit, workflowBlob } = evidence;
  if (
    !exactObject(policy) || policy.repository !== REPOSITORY ||
    policy.workflowRef !== WORKFLOW_REF || policy.candidateSha !== claims.candidateSha ||
    policy.candidateTree !== commit.tree || policy.workflowBlobSha !== workflowBlob.blobSha ||
    run.id !== claims.runId || run.repositoryId !== claims.repositoryId ||
    run.ownerId !== claims.ownerId || run.repository !== claims.repository ||
    run.ref !== claims.ref || run.refProtected !== true ||
    run.attempt !== 1 || run.event !== "workflow_dispatch" ||
    run.headSha !== claims.candidateSha || run.actorId !== claims.actorId ||
    !positiveInteger(run.triggeringActorId) || run.conclusion !== "success" ||
    check.runId !== run.id || !positiveInteger(check.id) || check.name !== "F10.9 G5 Production Read-Only Diagnostic" ||
    check.conclusion !== "success" || deployment.runId !== run.id ||
    deployment.sha !== claims.candidateSha || deployment.environmentId !== environment.id ||
    deployment.environment !== ENVIRONMENT || !positiveInteger(deployment.id) ||
    environment.name !== ENVIRONMENT || !positiveInteger(environment.id) || environment.protected !== true ||
    commit.sha !== claims.candidateSha ||
    !/^[0-9a-f]{40}$/.test(commit.tree) || workflowBlob.ref !== claims.workflowRef ||
    workflowBlob.workflowSha !== claims.workflowSha || !/^[0-9a-f]{40}$/.test(workflowBlob.blobSha)
  ) stop(REASONS.BINDING);
  if (
    approval.runId !== run.id || approval.checkRunId !== check.id ||
    approval.deploymentId !== deployment.id || approval.environmentId !== environment.id ||
    approval.sha !== claims.candidateSha || approval.workflowSha !== claims.workflowSha ||
    approval.state !== "approved" || !positiveInteger(approval.reviewerId) ||
    approval.reviewerId === claims.actorId || approval.reviewerId === run.triggeringActorId
  ) stop(REASONS.APPROVAL);
  return Object.freeze({
    repositoryId: claims.repositoryId, runId: run.id, runAttempt: run.attempt,
    checkRunId: check.id, environmentId: environment.id, deploymentId: deployment.id,
    candidateSha: claims.candidateSha, candidateTree: commit.tree,
    workflowRef: claims.workflowRef, workflowSha: claims.workflowSha,
    workflowBlobSha: workflowBlob.blobSha, actorId: claims.actorId,
    triggeringActorId: run.triggeringActorId, reviewerId: approval.reviewerId,
    nonce: claims.nonce, jti: claims.jti, expiresAt: claims.expiresAt,
  });
}

export async function gateIdentity(binding) {
  return digest([
    binding.repositoryId, binding.runId, binding.runAttempt, binding.checkRunId,
    binding.environmentId, binding.deploymentId,
  ]);
}

function validateLedgerBinding(binding) {
  if (!exactObject(binding)) stop(REASONS.LEDGER);
  const expectedKeys = [
    "actorId", "candidateSha", "candidateTree", "checkRunId", "deploymentId",
    "environmentId", "expiresAt", "jti", "nonce", "repositoryId", "reviewerId",
    "runAttempt", "runId", "triggeringActorId", "workflowBlobSha", "workflowRef",
    "workflowSha",
  ];
  if (stable(Object.keys(binding).sort()) !== stable(expectedKeys)) stop(REASONS.LEDGER);
  for (const field of [
    "actorId", "checkRunId", "deploymentId", "environmentId", "expiresAt",
    "repositoryId", "reviewerId", "runAttempt", "runId", "triggeringActorId",
  ]) {
    if (!positiveInteger(binding[field])) stop(REASONS.LEDGER);
  }
  if (
    binding.runAttempt !== 1 ||
    typeof binding.nonce !== "string" || !/^sha256:[0-9a-f]{64}$/.test(binding.nonce) ||
    typeof binding.jti !== "string" || binding.jti.length < 16 || binding.jti.length > 256 ||
    binding.workflowRef !== WORKFLOW_REF || binding.workflowSha !== REPOSITORY_POLICY.candidateSha ||
    binding.candidateSha !== REPOSITORY_POLICY.candidateSha ||
    binding.candidateTree !== REPOSITORY_POLICY.candidateTree ||
    binding.workflowBlobSha !== REPOSITORY_POLICY.workflowBlobSha
  ) stop(REASONS.LEDGER);
}

function publicResult(decision, reasonCode, receiptDigest = null) {
  return Object.freeze({
    version: VERSION, decision, reasonCode, receiptDigest,
    authorizationComplete: false, transportCreated: false,
    connectedMode: CONNECTED_DISABLED, operationalTrust: TRUST_STOP,
  });
}

export class G5AtomicLedgerDurableObject extends DurableObjectBase {
  constructor(state, env = {}) {
    super(state, env);
    if (!state?.storage || typeof state.storage.transaction !== "function") stop(REASONS.AUTHORITY);
    this.storage = state.storage;
    this.clock = typeof env.clock === "function" ? env.clock : () => Math.floor(Date.now() / 1000);
  }

  async consume(binding) {
    validateLedgerBinding(binding);
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
        nonceDigest: await digest(binding.nonce), jtiDigest: await digest(binding.jti),
        consumedAt: nowEpochSeconds, expiresAt: binding.expiresAt, policyVersion: VERSION,
      });
      const receiptDigest = await digest(receiptMaterial);
      await transaction.put(gateKey, Object.freeze({
        state: "CONSUMED", identity, expiresAt: binding.expiresAt,
        receiptDigest, receipt: receiptMaterial,
      }));
      return Object.freeze({ result: publicResult("STOP", TRUST_STOP, receiptDigest) });
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
  constructor({ jwks, githubApp, ledger, clock }) {
    this.jwks = jwks;
    this.githubApp = githubApp;
    this.ledger = ledger;
    this.policy = REPOSITORY_POLICY;
    this.clock = clock;
  }

  async authorize(request, hooks = {}) {
    rejectCallerAuthority(request);
    if (typeof this.clock !== "function") stop(REASONS.AUTHORITY);
    const claims = await verifyGithubOidc(request.bearerOidc, this.jwks, this.clock());
    if (claims.runId !== request.gateReference.runId || claims.runAttempt !== 1) stop(REASONS.BINDING);
    const evidence = await this.githubApp.authoritativeEvidence(claims);
    const binding = validateAuthority(claims, evidence, this.policy);
    if (!this.ledger || typeof this.ledger.consume !== "function") stop(REASONS.AUTHORITY);
    if (hooks.beforeCas) await hooks.beforeCas();
    let result;
    try {
      result = await this.ledger.consume(binding);
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
      const githubApp = new GithubAppReadOnlyAdapter(env.G5_GITHUB_APP_READ_ONLY);
      const broker = new G5TrustBroker({
        jwks: env.G5_OFFLINE_JWKS,
        githubApp,
        ledger: env.G5_ATOMIC_LEDGER.getByName("g5-atomic-ledger-v1"),
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
  VERSION, ISSUER, AUDIENCE, MAIN_REF, ENVIRONMENT, REPOSITORY, WORKFLOW_REF,
  WORKFLOW_NAME, CONNECTED_DISABLED, TRUST_BROKER_ENDPOINT_CONFIG_NAME,
  REPOSITORY_POLICY, MANUAL_WORKFLOW_POLICY, SUPABASE_TABLES,
  MAX_TOKEN_LIFETIME_SECONDS, MAX_LEDGER_RECORDS, STRICT_TIMEOUT_MS, MAX_RESPONSE_BYTES,
  PAGE_SIZE, MAX_PAGES, MAX_ROWS,
});
