const VERSION = "f10.9-g5-trust-broker.v1";
const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "studiamatch-f10-9-g5-production-trust-plane";
const MAIN_REF = "refs/heads/main";
const ENVIRONMENT = "Production";
const REPOSITORY = "romelhc95/studiamatch";
const WORKFLOW_REF = "romelhc95/studiamatch/.github/workflows/f9-7-contract.yml@refs/heads/main";
const CONNECTED_STOP = "STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED";
const TRUST_STOP = "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED";
const MAX_TOKEN_LIFETIME_SECONDS = 600;
const MAX_LEDGER_RECORDS = 10_000;
const REPOSITORY_POLICY = Object.freeze({
  repository: REPOSITORY,
  workflowRef: WORKFLOW_REF,
  candidateSha: "191539de71cbff95552c476463305e8d6f3e4b73",
  candidateTree: "7fe13bb907053f4dea51ac593b5df0de78cb40d6",
  workflowBlobSha: "4b3dfb155081f9c3c9b638373b6e5aa2a06cca65",
});
const MANUAL_WORKFLOW_POLICY = Object.freeze({
  state: "REPOSITORY_ONLY_DISABLED",
  dispatchAllowed: false,
  idTokenPermission: false,
  productionEnvironment: false,
  connectedTransport: false,
});

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
});
const PUBLIC_REASON_CODES = new Set([...Object.values(REASONS), TRUST_STOP]);

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
    this.state = "REPOSITORY_ONLY_DISABLED";
  }

  async authoritativeEvidence(claims) {
    void claims;
    stop(CONNECTED_STOP);
  }
}

export function createDisabledConnectedGithubAppAdapter(options = Object.freeze({ enabled: false })) {
  return new G5ConnectedGithubAppAdapter(options);
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
    connectedMode: CONNECTED_STOP, operationalTrust: TRUST_STOP,
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

export const INTERNALS = Object.freeze({
  VERSION, ISSUER, AUDIENCE, MAIN_REF, ENVIRONMENT, REPOSITORY, WORKFLOW_REF,
  REPOSITORY_POLICY, MANUAL_WORKFLOW_POLICY, MAX_TOKEN_LIFETIME_SECONDS, MAX_LEDGER_RECORDS,
});
