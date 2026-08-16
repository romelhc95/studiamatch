import assert from "node:assert/strict";
import { createHash, generateKeyPairSync, sign } from "node:crypto";
import test from "node:test";

import worker, {
  G5AtomicLedgerDurableObject,
  G5ConnectedGithubAppAdapter,
  G5ConnectedSupabaseCollector,
  G5GithubJwksClient,
  G5GithubActionsOidcClient,
  G5SingleUseReceiptSession,
  G5TrustBroker,
  G5TrustBrokerHttpClient,
  GithubAppReadOnlyAdapter,
  INTERNALS,
  REASONS,
  TrustBrokerError,
  createDisabledConnectedGithubAppAdapter,
  createGithubAppJwt,
  gateIdentity,
  g5WorkflowGuard,
  repositoryPolicyFromRuntimeBindings,
  rejectCallerAuthority,
  runG5ConnectedDiagnosticCli,
  validateTrustBrokerReceipt,
  verifyGithubOidc,
} from "../src/index.mjs";

const NOW = 1_787_000_000;
const SHA = "1".repeat(40);
const TREE = "2".repeat(40);
const WORKFLOW_SHA = SHA;
const WORKFLOW_BLOB = "3".repeat(40);
const WORKFLOW_REF = INTERNALS.WORKFLOW_REF;
const POLICY_ENV = Object.freeze({
  G5_ALLOWED_CANDIDATE_SHA: SHA,
  G5_ALLOWED_CANDIDATE_TREE: TREE,
  G5_ALLOWED_WORKFLOW_BLOB_SHA: WORKFLOW_BLOB,
});
const POLICY = repositoryPolicyFromRuntimeBindings(POLICY_ENV);
const RUNTIME_ENV = Object.freeze({
  ...POLICY_ENV,
  G5_TRUST_RUNTIME_ENABLED: "true",
  G5_GITHUB_APP_ID: "12345",
  G5_GITHUB_APP_INSTALLATION_ID: "67890",
  G5_GITHUB_APP_PRIVATE_KEY: "-----BEGIN PRIVATE KEY-----\nZmFrZQ==\n-----END PRIVATE KEY-----",
});

const { privateKey, publicKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
const publicJwk = publicKey.export({ format: "jwk" });
const JWKS = { keys: [{ ...publicJwk, kid: "offline-key-1", alg: "RS256", use: "sig" }] };

function b64url(value) {
  return Buffer.from(typeof value === "string" ? value : JSON.stringify(value)).toString("base64url");
}

function claims(overrides = {}) {
  return {
    iss: INTERNALS.ISSUER,
    aud: INTERNALS.AUDIENCE,
    iat: NOW - 10,
    nbf: NOW - 15,
    exp: NOW + 300,
    jti: "offline-jti-00000001",
    repository: "romelhc95/studiamatch",
    repository_id: "101",
    repository_owner_id: "202",
    ref: INTERNALS.MAIN_REF,
    sha: SHA,
    workflow_ref: WORKFLOW_REF,
    workflow_sha: WORKFLOW_SHA,
    run_id: "303",
    run_attempt: "1",
    environment: INTERNALS.ENVIRONMENT,
    actor_id: "404",
    ...overrides,
  };
}

function token(payload = claims(), key = privateKey, header = {}) {
  const encodedHeader = b64url({ alg: "RS256", typ: "JWT", kid: "offline-key-1", ...header });
  const encodedPayload = b64url(payload);
  const material = `${encodedHeader}.${encodedPayload}`;
  return `${material}.${sign("RSA-SHA256", Buffer.from(material), key).toString("base64url")}`;
}

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value !== null && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stable(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function digest(value) {
  return `sha256:${createHash("sha256").update(stable(value)).digest("hex")}`;
}

function validBrokerReceipt(context = {}) {
  const binding = {
    repositoryId: context.repositoryId ?? 101,
    runId: context.runId ?? 303,
    runAttempt: 1,
    checkRunId: context.checkRunId ?? 505,
    jobName: INTERNALS.WORKFLOW_NAME,
    environmentId: context.environmentId ?? 707,
    deploymentId: context.deploymentId ?? 606,
    candidateSha: SHA,
    candidateTree: TREE,
    workflowSha: SHA,
    workflowBlobSha: WORKFLOW_BLOB,
    contractDigest: digest("contract"),
    schemaDigest: digest("schema"),
    algorithmDigest: digest("algorithm"),
    capabilityDigest: digest("capability"),
  };
  const receipt = {
    identity: "g5-trust-broker-offline",
    expiresAt: context.expiresAt ?? Math.floor(Date.now() / 1000) + 300,
    binding,
  };
  const receiptDigest = digest(receipt);
  return {
    version: INTERNALS.VERSION,
    decision: "AUTHORIZED",
    receiptDigest,
    receipt,
    proof: {
      type: "G5_TRUST_BROKER_RECEIPT_PROOF",
      keyId: "offline-proof-key",
      value: digest(["proof", receiptDigest]),
    },
  };
}

const proofVerifier = Object.freeze({
  verify: async ({ proof, receiptDigest }) => proof.value === digest(["proof", receiptDigest]),
});

class FakeFetchTransport {
  constructor(handler) {
    this.handler = handler;
    this.calls = [];
  }

  async fetch(request, init) {
    const text = await request.clone().text().catch(() => "");
    const call = {
      method: request.method,
      url: String(request.url),
      headers: Object.fromEntries(request.headers),
      body: text,
      init,
    };
    this.calls.push(call);
    return this.handler(request, call);
  }

  async fetchPinned(request, init) {
    if (!Array.isArray(init.resolvedAddresses) || init.resolvedAddresses.length === 0) {
      throw new Error("missing pinned addresses");
    }
    return this.fetch(request, init);
  }
}

function oneRowTables() {
  const tables = Object.fromEntries(Object.entries(INTERNALS.SUPABASE_TABLES).map(([table, columns]) => [
    table,
    [Object.fromEntries(columns.split(",").map((column) => [column, column === "id" ? `${table}-1` : null]))],
  ]));
  tables.institutions[0] = {
    ...tables.institutions[0],
    name: "Institution",
    slug: "institution",
    website_url: "https://catalog.example/",
  };
  tables.institution_site_profiles[0] = {
    ...tables.institution_site_profiles[0],
    institution_id: tables.institutions[0].id,
    discovery_enabled: false,
    pipeline_enabled: false,
    pipeline_ready: true,
    site_type: "traditional_ssr",
    discovery_mode: "hardcoded_urls",
    seed_urls: [],
    catalog_url_patterns: [],
    catalog_max_pages: 1,
    allowed_url_patterns: [],
    exclusion_patterns: [],
    requires_cloudflare_bypass: false,
    warmup_url: null,
    circuit_open: false,
    circuit_opened_at: null,
  };
  return tables;
}

function receiptStore() {
  const consumed = new Set();
  return {
    capability: "DURABLE_SINGLE_USE_RECEIPT_LEDGER",
    consumeOnce: async (receiptDigest, expiresAt) => {
      assert.ok(/^sha256:[0-9a-f]{64}$/.test(receiptDigest));
      assert.equal(Number.isSafeInteger(expiresAt), true);
      if (consumed.has(receiptDigest)) return false;
      consumed.add(receiptDigest);
      return true;
    },
  };
}

function fixture(overrides = {}) {
  const base = {
    workflow_run: [{
      id: 303, repositoryId: 101, ownerId: 202, repository: "romelhc95/studiamatch",
      ref: "refs/heads/main", attempt: 1, status: "in_progress",
      event: "workflow_dispatch", headSha: SHA,
      actorId: 404, triggeringActorId: 405, conclusion: null,
    }],
    branch: [{ name: "main", protected: true }],
    check_run_job: [{
      id: 505, jobId: 909, runId: 303, name: "F10.9 G5 Production Read-Only Diagnostic",
      jobStatus: "in_progress", jobConclusion: null, checkStatus: "in_progress", checkConclusion: null,
    }],
    deployment: [{ id: 606, runId: 303, jobId: 909, sha: SHA, environment: "Production", statusState: "in_progress" }],
    environment: [{ id: 707, name: "Production", protected: true }],
    approval: [{ runId: 303, environmentId: 707, environment: "Production", state: "approved", reviewerId: 808 }],
    commit_tree: [{ sha: SHA, tree: TREE }],
    workflow_blob: [{ ref: WORKFLOW_REF, workflowSha: WORKFLOW_SHA, blobSha: WORKFLOW_BLOB }],
  };
  return { ...base, ...overrides };
}

class FakeGithubTransport {
  constructor(data = fixture(), options = {}) {
    this.data = data;
    this.options = options;
    this.calls = [];
  }

  async query(resource, reference) {
    this.calls.push({ resource, reference });
    if (this.options.timeoutResource === resource) throw new Error("fixture timeout");
    return {
      complete: this.options.incompleteResource !== resource,
      items: structuredClone(this.data[resource] ?? []),
    };
  }

  getWorkflowRun(reference) { return this.query("workflow_run", reference); }
  listWorkflowJobs(reference) { return this.query("check_run_job", reference); }
  listDeployments(reference) { return this.query("deployment", reference); }
  getEnvironment(reference) { return this.query("environment", reference); }
  listApprovals(reference) { return this.query("approval", reference); }
  getCommit(reference) { return this.query("commit_tree", reference); }
  getWorkflowBlob(reference) { return this.query("workflow_blob", reference); }
  getBranch(reference) { return this.query("branch", reference); }
}

class FakeDurableStorage {
  constructor() {
    this.values = new Map();
    this.tail = Promise.resolve();
  }

  async get(key) {
    return structuredClone(this.values.get(key));
  }

  async transaction(callback) {
    const run = this.tail.then(async () => {
      const snapshot = new Map(structuredClone([...this.values]));
      const transaction = {
        get: async (key) => structuredClone(snapshot.get(key)),
        put: async (key, value) => snapshot.set(key, structuredClone(value)),
      };
      try {
        const result = await callback(transaction);
        this.values = snapshot;
        return result;
      } catch (error) {
        throw error;
      }
    });
    this.tail = run.catch(() => undefined);
    return run;
  }
}

function setup({ payload = claims(), data = fixture(), transportOptions = {}, policy } = {}) {
  const storage = new FakeDurableStorage();
  const clock = { now: NOW };
  const runtimePolicy = policy ?? POLICY;
  const ledger = new G5AtomicLedgerDurableObject({ storage }, { policy: runtimePolicy, clock: () => clock.now });
  const transport = new FakeGithubTransport(data, transportOptions);
  const githubApp = new GithubAppReadOnlyAdapter(transport);
  const broker = new G5TrustBroker({
    jwks: JWKS, githubApp, ledger, policy: runtimePolicy,
    clock: () => clock.now,
  });
  const request = { bearerOidc: token(payload), gateReference: { runId: 303, expectedRunAttempt: 1 } };
  return { broker, githubApp, ledger, storage, clock, transport, request };
}

function ledgerBinding(overrides = {}) {
  return {
    repositoryId: 101, runId: 303, runAttempt: 1, checkRunId: 505,
    environmentId: 707, deploymentId: 606, candidateSha: SHA, candidateTree: TREE,
    workflowRef: WORKFLOW_REF, workflowSha: WORKFLOW_SHA, workflowBlobSha: WORKFLOW_BLOB,
    actorId: 404, triggeringActorId: 405, reviewerId: 808,
    nonce: `sha256:${"a".repeat(64)}`, jti: "offline-jti-00000001", expiresAt: NOW + 300,
    ...overrides,
  };
}

async function onlyGate(storage) {
  const gates = [...storage.values.entries()].filter(([key]) => key.startsWith("gate:"));
  assert.equal(gates.length, 1);
  return structuredClone(gates[0][1]);
}

async function reason(call, expected) {
  let thrown;
  try {
    await call();
  } catch (error) {
    thrown = error;
  }
  assert.equal(thrown instanceof TrustBrokerError && thrown.reason === expected, true);
}

test("valid JWT and authoritative exact-one evidence consume once with sanitized receipt", async () => {
  const setupValues = setup();
  const { broker, ledger, storage, request, transport } = setupValues;
  const result = await broker.authorize(request);
  assert.deepEqual(Object.keys(result).sort(), [
    "authorizationComplete", "connectedMode", "decision", "operationalTrust",
    "reasonCode", "receiptDigest", "transportCreated", "version",
  ]);
  assert.match(result.receiptDigest, /^sha256:[0-9a-f]{64}$/);
  assert.equal(result.authorizationComplete, false);
  assert.equal(result.transportCreated, false);
  const gate = await onlyGate(storage);
  assert.equal(await ledger.receipt(gate.identity), result.receiptDigest);
  assert.deepEqual(transport.calls.map((call) => call.resource).sort(), [
    "approval", "branch", "check_run_job", "commit_tree", "deployment", "environment",
    "workflow_blob", "workflow_run",
  ]);
});

test("invalid signature and closed algorithm are rejected", async () => {
  const other = generateKeyPairSync("rsa", { modulusLength: 2048 }).privateKey;
  await reason(() => verifyGithubOidc(token(claims(), other), JWKS, NOW), REASONS.PROOF);
  await reason(() => verifyGithubOidc(token(claims(), privateKey, { alg: "PS256" }), JWKS, NOW), REASONS.PROOF);
});

test("issuer and audience drift are rejected", async () => {
  await reason(() => verifyGithubOidc(token(claims({ iss: "https://issuer.invalid" })), JWKS, NOW), REASONS.PROOF);
  await reason(() => verifyGithubOidc(token(claims({ aud: "generic" })), JWKS, NOW), REASONS.PROOF);
});

test("expired, not-before, and future-issued tokens are rejected", async () => {
  await reason(() => verifyGithubOidc(token(claims({ exp: NOW })), JWKS, NOW), REASONS.PROOF);
  await reason(() => verifyGithubOidc(token(claims({ nbf: NOW + 1 })), JWKS, NOW), REASONS.PROOF);
  await reason(() => verifyGithubOidc(token(claims({ iat: NOW + 1, nbf: NOW + 1 })), JWKS, NOW), REASONS.PROOF);
  await reason(() => verifyGithubOidc(token(claims({ iat: NOW - 700 })), JWKS, NOW), REASONS.PROOF);
});

test("GitHub-like not-before before issued-at is accepted", async () => {
  const verified = await verifyGithubOidc(token(claims({ nbf: NOW - 15, iat: NOW - 10 })), JWKS, NOW);
  assert.equal(verified.runId, 303);
});

test("OIDC numeric identity claims require canonical decimal strings", async () => {
  for (const override of [
    { repository_id: "1e2" }, { repository_owner_id: 202 },
    { run_id: "303.0" }, { run_attempt: 1 }, { actor_id: true },
  ]) {
    await reason(() => verifyGithubOidc(token(claims(override)), JWKS, NOW), REASONS.PROOF);
  }
});

for (const [name, override] of [
  ["repository", { repository_id: "999" }],
  ["ref", { ref: "refs/heads/desarrollo" }],
  ["workflow", { workflow_ref: "romelhc95/studiamatch/.github/workflows/other.yml@refs/heads/main" }],
  ["sha", { sha: "9".repeat(40) }],
  ["attempt", { run_attempt: "2" }],
  ["environment", { environment: "Certification" }],
]) {
  test(`OIDC ${name} drift is rejected`, async () => {
    const { broker, request } = setup({ payload: claims(override) });
    await reason(
      () => broker.authorize(request),
      name === "repository" ? REASONS.BINDING : REASONS.PROOF,
    );
  });
}

test("self-review is rejected", async () => {
  for (const reviewerId of [404, 405]) {
    const data = fixture({ approval: [{ ...fixture().approval[0], reviewerId }] });
    const { broker, request } = setup({ data });
    await reason(() => broker.authorize(request), REASONS.APPROVAL);
  }
});

test("approval must be exact-one and bound to run/deployment/workflow", async () => {
  for (const approval of [
    [],
    [fixture().approval[0], fixture().approval[0]],
    [{ ...fixture().approval[0], environmentId: 999 }],
    [{ ...fixture().approval[0], environment: "Certification" }],
    [{ ...fixture().approval[0], state: "rejected" }],
    [{ ...fixture().approval[0], reviewerId: 0 }],
  ]) {
    const { broker, request } = setup({ data: fixture({ approval }) });
    await reason(() => broker.authorize(request), REASONS.APPROVAL);
  }
});

test("authoritative evidence must declare a complete result set", async () => {
  const { broker, request } = setup({ transportOptions: { incompleteResource: "check_run_job" } });
  await reason(() => broker.authorize(request), REASONS.BINDING);
});

test("workflow run does not require ref_protected and must be in progress", async () => {
  const valid = setup();
  assert.equal((await valid.broker.authorize(valid.request)).decision, "STOP");
  for (const workflow_run of [
    [{ ...fixture().workflow_run[0], status: "queued" }],
    [{ ...fixture().workflow_run[0], status: "waiting" }],
    [{ ...fixture().workflow_run[0], status: "completed", conclusion: "success" }],
    [{ ...fixture().workflow_run[0], status: "in_progress", conclusion: "failure" }],
    [{ ...fixture().workflow_run[0], status: "in_progress", conclusion: "cancelled" }],
    [{ ...fixture().workflow_run[0], status: "in_progress", conclusion: "skipped" }],
    [{ ...fixture().workflow_run[0], attempt: 2 }],
  ]) {
    const { broker, request } = setup({ data: fixture({ workflow_run }) });
    await reason(() => broker.authorize(request), REASONS.BINDING);
  }
});

test("branch protection is verified through the branch endpoint", async () => {
  for (const branch of [[], [{ name: "main", protected: false }], [{ name: "desarrollo", protected: true }]]) {
    const { broker, request } = setup({ data: fixture({ branch }) });
    await reason(() => broker.authorize(request), REASONS.BINDING);
  }
});

test("job and check run must be the exact in-progress workflow job", async () => {
  for (const check_run_job of [
    [{ ...fixture().check_run_job[0], name: "Other job" }],
    [{ ...fixture().check_run_job[0], jobStatus: "completed", jobConclusion: "success" }],
    [{ ...fixture().check_run_job[0], checkStatus: "completed", checkConclusion: "success" }],
    [{ ...fixture().check_run_job[0], jobConclusion: "failure" }],
    [{ ...fixture().check_run_job[0], id: 0 }],
    [{ ...fixture().check_run_job[0], jobId: 0 }],
  ]) {
    const { broker, request } = setup({ data: fixture({ check_run_job }) });
    await reason(() => broker.authorize(request), REASONS.BINDING);
  }
});

test("environment must be exact-one and match approval-derived Production id", async () => {
  for (const data of [
    fixture({ environment: [] }),
    fixture({ environment: [fixture().environment[0], fixture().environment[0]] }),
    fixture({ approval: [{ ...fixture().approval[0], environmentId: 708 }] }),
  ]) {
    const { broker, request } = setup({ data });
    await reason(() => broker.authorize(request), data.approval[0]?.environmentId === 708 ? REASONS.APPROVAL : REASONS.BINDING);
  }
});

test("deployment must be exact-one and bound to candidate SHA", async () => {
  for (const deployment of [
    [],
    [fixture().deployment[0], fixture().deployment[0]],
    [{ ...fixture().deployment[0], sha: "9".repeat(40) }],
    [{ ...fixture().deployment[0], jobId: 910 }],
    [{ ...fixture().deployment[0], statusState: "failure" }],
  ]) {
    const { broker, request } = setup({ data: fixture({ deployment }) });
    await reason(() => broker.authorize(request), REASONS.BINDING);
  }
});

test("commit tree and workflow blob drift are rejected", async () => {
  for (const data of [
    fixture({ commit_tree: [{ sha: SHA, tree: "8".repeat(40) }] }),
    fixture({ workflow_blob: [{ ...fixture().workflow_blob[0], blobSha: "7".repeat(40) }] }),
  ]) {
    const { broker, request } = setup({ data });
    await reason(() => broker.authorize(request), REASONS.BINDING);
  }
});

test("runtime policy comes from bindings and legacy protected source is rejected", async () => {
  await reason(() => repositoryPolicyFromRuntimeBindings({}), REASONS.CONFIG);
  await reason(
    () => repositoryPolicyFromRuntimeBindings({
      G5_ALLOWED_CANDIDATE_SHA: INTERNALS.LEGACY_POLICY_DENYLIST[0].candidateSha,
      G5_ALLOWED_CANDIDATE_TREE: TREE,
      G5_ALLOWED_WORKFLOW_BLOB_SHA: WORKFLOW_BLOB,
    }),
    REASONS.BINDING,
  );
  await reason(
    () => repositoryPolicyFromRuntimeBindings({
      G5_ALLOWED_CANDIDATE_SHA: SHA,
      G5_ALLOWED_CANDIDATE_TREE: INTERNALS.LEGACY_POLICY_DENYLIST[0].candidateTree,
      G5_ALLOWED_WORKFLOW_BLOB_SHA: WORKFLOW_BLOB,
    }),
    REASONS.BINDING,
  );
  await reason(
    () => repositoryPolicyFromRuntimeBindings({
      G5_ALLOWED_CANDIDATE_SHA: SHA,
      G5_ALLOWED_CANDIDATE_TREE: TREE,
      G5_ALLOWED_WORKFLOW_BLOB_SHA: INTERNALS.LEGACY_POLICY_DENYLIST[0].workflowBlobSha,
    }),
    REASONS.BINDING,
  );
  assert.deepEqual(repositoryPolicyFromRuntimeBindings(POLICY_ENV), POLICY);
});

test("caller-supplied authority is rejected before JWT verification", async () => {
  const { broker, request, transport } = setup();
  for (const field of ["claims", "approval", "deployment", "receipt", "repository_id", "jti"]) {
    await reason(() => broker.authorize({ ...request, [field]: "caller" }), REASONS.AUTHORITY);
  }
  assert.equal(transport.calls.length, 0);
  assert.throws(() => rejectCallerAuthority({ bearerOidc: "x", gateReference: { runId: 303, expectedRunAttempt: 2 } }), TrustBrokerError);
});

test("nonce and jti replay are rejected even with a different signed JWT", async () => {
  const { broker, request } = setup();
  await broker.authorize(request);
  const different = { ...request, bearerOidc: token(claims({ iat: NOW - 9 })) };
  await reason(() => broker.authorize(different), REASONS.REPLAY);
});

test("nonce and jti indexes reject replay independently across gate identities", async () => {
  const first = setup();
  const binding = ledgerBinding();
  await first.ledger.consume(binding);
  await reason(
    () => first.ledger.consume({ ...binding, deploymentId: 607, jti: "offline-jti-00000002" }),
    REASONS.REPLAY,
  );
  await reason(
    () => first.ledger.consume({ ...binding, deploymentId: 608, nonce: `sha256:${"b".repeat(64)}` }),
    REASONS.REPLAY,
  );
});

test("concurrent cross-identity nonce replay permits only one consume", async () => {
  const { ledger } = setup();
  const binding = ledgerBinding();
  const results = await Promise.allSettled([
    ledger.consume(binding),
    ledger.consume({ ...binding, deploymentId: 607, jti: "offline-jti-00000002" }),
  ]);
  assert.equal(results.filter((result) => result.status === "fulfilled").length, 1);
  assert.equal(results.find((result) => result.status === "rejected").reason.reason, REASONS.REPLAY);
});

test("two concurrent consumes serialize and only one succeeds", async () => {
  const { broker, request } = setup();
  const results = await Promise.allSettled([broker.authorize(request), broker.authorize(request)]);
  assert.equal(results.filter((result) => result.status === "fulfilled").length, 1);
  const failure = results.find((result) => result.status === "rejected");
  assert.equal(failure.reason.reason, REASONS.REPLAY);
});

test("timeout before CAS leaves ABSENT", async () => {
  const { broker, storage, request } = setup();
  await assert.rejects(() => broker.authorize(request, { beforeCas: async () => { throw new Error("timeout"); } }));
  assert.equal([...storage.values.keys()].some((key) => key.startsWith("gate:")), false);
});

test("timeout or diagnostic failure after CAS preserves CONSUMED and receipt", async () => {
  const { broker, ledger, storage, request } = setup();
  await assert.rejects(() => broker.authorize(request, { afterCas: async () => { throw new Error("diagnostic failed"); } }));
  const gate = await onlyGate(storage);
  assert.equal(gate.state, "CONSUMED");
  const receipt = await ledger.receipt(gate.identity);
  assert.match(receipt, /^sha256:/);
  await reason(() => broker.authorize(request), REASONS.REPLAY);
  assert.equal(await ledger.receipt(gate.identity), receipt);
});

test("expiry is re-evaluated after authoritative queries and before CAS", async () => {
  const { broker, clock, storage, request } = setup();
  await reason(
    () => broker.authorize(request, { beforeCas: async () => { clock.now = NOW + 301; } }),
    REASONS.EXPIRED,
  );
  assert.equal((await onlyGate(storage)).state, "EXPIRED");
});

test("expired gate cleanup creates a non-resurrectable tombstone", async () => {
  const { ledger, storage } = setup();
  const binding = ledgerBinding({ expiresAt: NOW - 1 });
  await reason(() => ledger.consume(binding), REASONS.EXPIRED);
  const gate = await onlyGate(storage);
  assert.equal(gate.state, "EXPIRED");
  assert.equal(await ledger.cleanup(gate.identity), "EXPIRED");
  await reason(() => ledger.consume({ ...binding, expiresAt: NOW + 300 }), REASONS.EXPIRED);
});

test("cleanup transitions persisted READY to EXPIRED without resurrection", async () => {
  const { ledger, storage } = setup();
  const identity = await gateIdentity(ledgerBinding());
  storage.values.set(`gate:${identity}`, { state: "READY", identity, expiresAt: NOW - 1 });
  assert.equal(await ledger.cleanup(identity), "EXPIRED");
  assert.equal((await onlyGate(storage)).state, "EXPIRED");
  assert.equal(await ledger.cleanup(identity), "EXPIRED");
});

test("ledger rejects malformed RPC bindings and non-ABSENT persisted states", async () => {
  const { ledger, storage } = setup();
  await reason(() => ledger.consume({ repositoryId: 101 }), REASONS.LEDGER);
  const binding = ledgerBinding();
  const identity = await gateIdentity(binding);
  storage.values.set(`gate:${identity}`, { state: "READY", identity, expiresAt: NOW + 10 });
  await reason(() => ledger.consume(binding), REASONS.LEDGER);
  storage.values.set(`gate:${identity}`, { state: "CORRUPT", identity });
  await reason(() => ledger.consume(binding), REASONS.LEDGER);
  await reason(() => ledger.cleanup(identity), REASONS.LEDGER);
});

test("ledger capacity is exact, atomic, and rejects malformed counters", async () => {
  const exact = setup();
  exact.storage.values.set("record_count", INTERNALS.MAX_LEDGER_RECORDS - 3);
  await exact.ledger.consume(ledgerBinding());
  assert.equal(await exact.storage.get("record_count"), INTERNALS.MAX_LEDGER_RECORDS);

  const insufficient = setup();
  insufficient.storage.values.set("record_count", INTERNALS.MAX_LEDGER_RECORDS - 2);
  const before = structuredClone([...insufficient.storage.values]);
  await reason(() => insufficient.ledger.consume(ledgerBinding()), REASONS.LEDGER);
  assert.deepEqual([...insufficient.storage.values], before);

  const tombstone = setup();
  tombstone.storage.values.set("record_count", INTERNALS.MAX_LEDGER_RECORDS - 1);
  await reason(
    () => tombstone.ledger.consume(ledgerBinding({ expiresAt: NOW - 1 })),
    REASONS.EXPIRED,
  );
  assert.equal(await tombstone.storage.get("record_count"), INTERNALS.MAX_LEDGER_RECORDS);
  await reason(
    () => tombstone.ledger.consume(ledgerBinding({
      deploymentId: 607, nonce: `sha256:${"b".repeat(64)}`,
      jti: "offline-jti-00000002", expiresAt: NOW - 1,
    })),
    REASONS.LEDGER,
  );

  for (const corrupt of [null, -1, 1.5, INTERNALS.MAX_LEDGER_RECORDS + 1]) {
    const invalid = setup();
    invalid.storage.values.set("record_count", corrupt);
    await reason(() => invalid.ledger.consume(ledgerBinding()), REASONS.LEDGER);
  }
});

test("falsy persisted replay markers still reject consumption", async () => {
  const { ledger, storage } = setup();
  const binding = ledgerBinding();
  await ledger.consume(binding);
  const nonceKey = [...storage.values.keys()].find((key) => key.startsWith("nonce:"));
  storage.values.set(nonceKey, false);
  await reason(
    () => ledger.consume({ ...binding, deploymentId: 607, jti: "offline-jti-00000002" }),
    REASONS.REPLAY,
  );
});

test("broker preserves allowlisted reasons reconstructed across Durable Object RPC", async () => {
  const { broker, request } = setup();
  broker.ledger = {
    consume: async () => {
      throw new Error(REASONS.REPLAY);
    },
  };
  await reason(() => broker.authorize(request), REASONS.REPLAY);
});

test("cleanup and receipt reject falsy corrupted gate records", async () => {
  const { ledger, storage } = setup();
  const identity = await gateIdentity(ledgerBinding());
  for (const corrupt of [null, false, 0, ""]) {
    storage.values.set(`gate:${identity}`, corrupt);
    await reason(() => ledger.cleanup(identity), REASONS.LEDGER);
    await reason(() => ledger.receipt(identity), REASONS.LEDGER);
  }
});

test("receipt retrieval verifies persisted receipt integrity", async () => {
  const { ledger, storage } = setup();
  await ledger.consume(ledgerBinding());
  const gate = await onlyGate(storage);
  storage.values.set(`gate:${gate.identity}`, { ...gate, receiptDigest: `sha256:${"0".repeat(64)}` });
  await reason(() => ledger.receipt(gate.identity), REASONS.LEDGER);
});

test("GitHub App transport timeout before CAS leaves no gate", async () => {
  const { broker, storage, request } = setup({ transportOptions: { timeoutResource: "deployment" } });
  await assert.rejects(() => broker.authorize(request));
  assert.equal([...storage.values.keys()].some((key) => key.startsWith("gate:")), false);
});

test("connected GitHub App adapter remains implemented but disabled by default", async () => {
  const adapter = createDisabledConnectedGithubAppAdapter();
  assert.equal(adapter.state, INTERNALS.CONNECTED_DISABLED);
  await reason(() => adapter.authoritativeEvidence(claims()), INTERNALS.CONNECTED_DISABLED);
  await reason(async () => {
    new G5ConnectedGithubAppAdapter({ enabled: true });
  }, INTERNALS.CONNECTED_DISABLED);
  await reason(async () => {
    new G5ConnectedGithubAppAdapter({
      env: { ...RUNTIME_ENV, G5_TRUST_RUNTIME_ENABLED: "false" },
      transport: new FakeFetchTransport(() => Response.json({})),
      policy: POLICY,
      endpointApproved: true,
      signer: async () => "signature",
    });
  }, INTERNALS.CONNECTED_DISABLED);
});

test("connected GitHub App adapter uses only read permissions and fake transport", async () => {
  const messages = [];
  const originalLog = console.log;
  console.log = (...values) => messages.push(values.join(" "));
  const transport = new FakeFetchTransport((request, call) => {
    const url = new URL(request.url);
    if (request.method === "POST") {
      assert.equal(url.pathname, "/app/installations/67890/access_tokens");
      const body = JSON.parse(call.body);
      assert.deepEqual(body.permissions, {
        actions: "read",
        checks: "read",
        contents: "read",
        deployments: "read",
        metadata: "read",
      });
      return Response.json({
        token: "installation-token-redacted",
        expires_at: new Date((NOW + 300) * 1000).toISOString(),
        permissions: body.permissions,
      });
    }
    assert.equal(request.method, "GET");
    assert.equal(request.headers.get("authorization"), "Bearer installation-token-redacted");
    if (url.pathname.endsWith("/actions/runs/303")) {
      return Response.json({
        id: 303,
        repository: { id: 101, full_name: "romelhc95/studiamatch", owner: { id: 202 } },
        head_branch: "main",
        run_attempt: 1,
        event: "workflow_dispatch",
        status: "in_progress",
        head_sha: SHA,
        actor: { id: 404 },
        triggering_actor: { id: 405 },
        conclusion: null,
      });
    }
    if (url.pathname.endsWith("/branches/main")) {
      return Response.json({ name: "main", protected: true });
    }
    if (url.pathname.endsWith("/actions/runs/303/jobs")) {
      return Response.json({ jobs: [{ id: 909, name: INTERNALS.WORKFLOW_NAME, status: "in_progress", conclusion: null }] });
    }
    if (url.pathname.endsWith(`/commits/${SHA}/check-runs`)) {
      return Response.json({
        check_runs: [{ id: 505, name: INTERNALS.WORKFLOW_NAME, status: "in_progress", conclusion: null }],
      });
    }
    if (url.pathname.endsWith("/deployments")) {
      return Response.json([{
        id: 606,
        sha: SHA,
        environment: "Production",
        repository_url: "https://api.github.com/repos/romelhc95/studiamatch",
        statuses_url: "https://api.github.com/repos/romelhc95/studiamatch/deployments/606/statuses",
      }]);
    }
    if (url.pathname.endsWith("/deployments/606/statuses")) {
      const jobUrl = "https://github.com/romelhc95/studiamatch/actions/runs/303/job/909";
      return Response.json([{
        state: "in_progress",
        environment: "Production",
        log_url: jobUrl,
        target_url: jobUrl,
        repository_url: "https://api.github.com/repos/romelhc95/studiamatch",
      }]);
    }
    if (url.pathname.endsWith("/environments/Production")) {
      return Response.json({ id: 707, name: "Production", protection_rules: [{ type: "required_reviewers" }] });
    }
    if (url.pathname.endsWith("/actions/runs/303/approvals")) {
      return Response.json([{
        state: "approved",
        user: { id: 808 },
        environments: [{ id: 707, name: "Production" }],
      }]);
    }
    if (url.pathname.endsWith(`/commits/${SHA}`)) {
      return Response.json({ sha: SHA, commit: { tree: { sha: TREE } } });
    }
    if (url.pathname.endsWith("/contents/.github/workflows/g5-manual-trust-gate.yml")) {
      return Response.json({ sha: WORKFLOW_BLOB });
    }
    throw new Error(`unexpected fake GitHub path ${url.pathname}`);
  });
  try {
    const adapter = new G5ConnectedGithubAppAdapter({
      env: RUNTIME_ENV,
      transport,
      policy: POLICY,
      endpointApproved: true,
      now: () => NOW,
      signer: async () => "signature",
    });
    const callsBeforeUnsafePath = transport.calls.length;
    await reason(() => adapter.githubFetch("GET", "//evil.invalid/repos/romelhc95/studiamatch"), REASONS.TRANSPORT);
    assert.equal(transport.calls.length, callsBeforeUnsafePath);
    const { broker, request, ledger } = setup();
    broker.githubApp = adapter;
    broker.ledger = ledger;
    const result = await broker.authorize(request);
    assert.equal(result.decision, "STOP");
    assert.match(result.receiptDigest, /^sha256:/);
    assert.equal(transport.calls.filter((call) => call.method === "POST").length, 1);
    assert.equal(transport.calls.every((call) => call.method === "GET" || call.url.endsWith("/access_tokens")), true);
    assert.equal(messages.join("\n").includes("installation-token-redacted"), false);
  } finally {
    console.log = originalLog;
  }
});

test("connected adapter derives deployment from GitHub deployment statuses", async () => {
  const jobUrl = "https://github.com/romelhc95/studiamatch/actions/runs/303/job/909";
  function transportFor({ deployments, statusesByDeployment }) {
    return new FakeFetchTransport((request, call) => {
      const url = new URL(request.url);
      if (request.method === "POST") {
        return Response.json({
          token: "installation-token-redacted",
          expires_at: new Date((NOW + 300) * 1000).toISOString(),
          permissions: JSON.parse(call.body).permissions,
        });
      }
      if (url.pathname.endsWith("/deployments")) return Response.json(deployments);
      const match = url.pathname.match(/\/deployments\/(\d+)\/statuses$/);
      if (match) {
        assert.equal(url.search, "?per_page=100");
        return Response.json(statusesByDeployment[match[1]] ?? []);
      }
      throw new Error(`unexpected fake GitHub path ${url.pathname}`);
    });
  }
  const deployment = {
    id: 606,
    sha: SHA,
    environment: "Production",
    repository_url: "https://api.github.com/repos/romelhc95/studiamatch",
    statuses_url: "https://api.github.com/repos/romelhc95/studiamatch/deployments/606/statuses",
  };
  const validStatus = {
    state: "in_progress",
    environment: "Production",
    log_url: jobUrl,
    target_url: jobUrl,
    repository_url: "https://api.github.com/repos/romelhc95/studiamatch",
  };
  const reference = Object.freeze({
    repository: "romelhc95/studiamatch",
    runId: 303,
    runAttempt: 1,
    candidateSha: SHA,
    workflowRef: WORKFLOW_REF,
    environment: "Production",
    jobId: 909,
  });
  const adapter = new G5ConnectedGithubAppAdapter({
    env: RUNTIME_ENV,
    transport: transportFor({ deployments: [deployment], statusesByDeployment: { 606: [validStatus] } }),
    policy: POLICY,
    endpointApproved: true,
    now: () => NOW,
    signer: async () => "signature",
  });
  assert.deepEqual(await adapter.listDeployments(reference), {
    complete: true,
    items: [{ id: 606, runId: 303, jobId: 909, sha: SHA, environment: "Production", statusState: "in_progress" }],
  });

  for (const status of [
    { ...validStatus, target_url: "https://github.com/romelhc95/studiamatch/actions/runs/304/job/909" },
    { ...validStatus, log_url: "https://github.com/romelhc95/studiamatch/actions/runs/303/job/910" },
    { ...validStatus, target_url: "https://evil.example/romelhc95/studiamatch/actions/runs/303/job/909" },
    { ...validStatus, state: "failure" },
    { ...validStatus, repository_url: "https://api.github.com/repos/other/repo" },
    { ...validStatus, repository_url: undefined },
  ]) {
    const drift = new G5ConnectedGithubAppAdapter({
      env: RUNTIME_ENV,
      transport: transportFor({ deployments: [deployment], statusesByDeployment: { 606: [status] } }),
      policy: POLICY,
      endpointApproved: true,
      now: () => NOW,
      signer: async () => "signature",
    });
    assert.deepEqual(await drift.listDeployments(reference), { complete: true, items: [] });
  }

  const staleHistoricalInProgress = new G5ConnectedGithubAppAdapter({
    env: RUNTIME_ENV,
    transport: transportFor({
      deployments: [deployment],
      statusesByDeployment: { 606: [{ ...validStatus, state: "failure" }, validStatus] },
    }),
    policy: POLICY,
    endpointApproved: true,
    now: () => NOW,
    signer: async () => "signature",
  });
  assert.deepEqual(await staleHistoricalInProgress.listDeployments(reference), { complete: true, items: [] });

  const multi = new G5ConnectedGithubAppAdapter({
    env: RUNTIME_ENV,
    transport: transportFor({
      deployments: [
        deployment,
        { ...deployment, id: 607, statuses_url: "https://api.github.com/repos/romelhc95/studiamatch/deployments/607/statuses" },
      ],
      statusesByDeployment: { 606: [validStatus], 607: [validStatus] },
    }),
    policy: POLICY,
    endpointApproved: true,
    now: () => NOW,
    signer: async () => "signature",
  });
  assert.equal((await multi.listDeployments(reference)).items.length, 2);

  const saturatedDeployments = new G5ConnectedGithubAppAdapter({
    env: RUNTIME_ENV,
    transport: transportFor({
      deployments: Array.from({ length: 100 }, (_, index) => ({
        ...deployment,
        id: index + 1,
        statuses_url: `https://api.github.com/repos/romelhc95/studiamatch/deployments/${index + 1}/statuses`,
      })),
      statusesByDeployment: {},
    }),
    policy: POLICY,
    endpointApproved: true,
    now: () => NOW,
    signer: async () => "signature",
  });
  await reason(() => saturatedDeployments.listDeployments(reference), REASONS.BINDING);

  const saturatedStatuses = new G5ConnectedGithubAppAdapter({
    env: RUNTIME_ENV,
    transport: transportFor({
      deployments: [deployment],
      statusesByDeployment: { 606: Array.from({ length: 100 }, () => validStatus) },
    }),
    policy: POLICY,
    endpointApproved: true,
    now: () => NOW,
    signer: async () => "signature",
  });
  await reason(() => saturatedStatuses.listDeployments(reference), REASONS.BINDING);
});

test("GitHub App JWT and JWKS client fail closed without logging secrets", async () => {
  const jwt = await createGithubAppJwt({
    appId: "12345",
    privateKey: "not-logged-private-key",
    nowEpochSeconds: NOW,
    signer: async (material, privateKey) => {
      assert.equal(privateKey, "not-logged-private-key");
      assert.equal(material.split(".").length, 2);
      return "signature";
    },
  });
  assert.equal(jwt.split(".").length, 3);
  assert.equal(jwt.includes("not-logged-private-key"), false);

  const timeoutClient = new G5GithubJwksClient({
    timeoutMs: 1,
    transport: {
      fetch: async (_request, init) => new Promise((_, reject) => {
        init.signal.addEventListener("abort", () => reject(new Error("aborted")));
      }),
    },
  });
  await reason(() => timeoutClient.jwks(NOW), REASONS.TRANSPORT);

  const failingClient = new G5GithubJwksClient({
    transport: new FakeFetchTransport(() => Response.json({ keys: [] })),
  });
  await reason(() => failingClient.jwks(NOW), REASONS.PROOF);

  const okClient = new G5GithubJwksClient({
    transport: new FakeFetchTransport(() => Response.json(JWKS)),
  });
  assert.equal((await okClient.jwks(NOW)).keys[0].kid, "offline-key-1");
  assert.equal((await okClient.jwks(NOW + 1)).keys[0].kid, "offline-key-1");
});

test("manual workflow policy is deployment-ready but disabled without operational var", () => {
  assert.deepEqual(INTERNALS.MANUAL_WORKFLOW_POLICY, {
    state: "DEPLOYMENT_READY_DISABLED_NOT_CONFIGURED",
    dispatchDefined: true,
    operationalGuard: "vars.G5_TRUST_RUNTIME_ENABLED == 'true'",
    defaultEnabled: false,
    mainRef: "refs/heads/main",
    runAttempt: 1,
    idTokenPermission: true,
    productionEnvironment: "Production",
    connectedMode: INTERNALS.CONNECTED_DISABLED,
    concurrencyIsLedger: false,
  });
  assert.equal(g5WorkflowGuard({ vars: {}, ref: INTERNALS.MAIN_REF, runAttempt: 1 }).enabled, false);
  assert.equal(g5WorkflowGuard({ vars: { G5_TRUST_RUNTIME_ENABLED: "true" }, ref: "refs/heads/desarrollo", runAttempt: 1 }).enabled, false);
  assert.equal(g5WorkflowGuard({ vars: { G5_TRUST_RUNTIME_ENABLED: "true" }, ref: INTERNALS.MAIN_REF, runAttempt: 2 }).enabled, false);
  assert.equal(g5WorkflowGuard({ vars: { G5_TRUST_RUNTIME_ENABLED: "true" }, ref: INTERNALS.MAIN_REF, runAttempt: 1 }).enabled, true);
});

test("OIDC client fetches a sanitized token with fixed audience", async () => {
  const transport = new FakeFetchTransport((request) => {
    const url = new URL(request.url);
    assert.equal(request.method, "GET");
    assert.equal(url.searchParams.get("audience"), INTERNALS.AUDIENCE);
    assert.equal(request.headers.get("authorization"), "Bearer request-token-0001");
    return Response.json({ value: "a.b.c" });
  });
  const client = new G5GithubActionsOidcClient({
    env: {
      ACTIONS_ID_TOKEN_REQUEST_TOKEN: "request-token-0001",
      ACTIONS_ID_TOKEN_REQUEST_URL: "https://token.actions.githubusercontent.com/id-token",
    },
    transport,
  });
  assert.equal(await client.fetchToken(), "a.b.c");
  assert.equal(transport.calls.length, 1);
  await reason(async () => {
    const drift = new G5GithubActionsOidcClient({
      env: {
        ACTIONS_ID_TOKEN_REQUEST_TOKEN: "request-token-0001",
        ACTIONS_ID_TOKEN_REQUEST_URL: "https://oidc.example/id-token",
      },
      transport,
    });
    await drift.fetchToken();
  }, REASONS.PROOF);
});

test("trust broker HTTP client requires future config and validates one receipt", async () => {
  const context = { repositoryId: 101, runId: 303, runAttempt: 1, checkRunId: 505, environmentId: 707, deploymentId: 606 };
  const body = validBrokerReceipt(context);
  const transport = new FakeFetchTransport(async (request, call) => {
    assert.equal(request.method, "POST");
    assert.equal(new URL(request.url).protocol, "https:");
    assert.deepEqual(JSON.parse(call.body), {
      bearerOidc: "header.payload.signature",
      gateReference: { runId: 303, expectedRunAttempt: 1 },
    });
    return Response.json(body);
  });
  const endpoint = G5TrustBrokerHttpClient.endpointFromConfig({
    [INTERNALS.TRUST_BROKER_ENDPOINT_CONFIG_NAME]: "https://broker.example/authorize",
  });
  const client = new G5TrustBrokerHttpClient({
    endpoint,
    transport,
    dnsResolve: async () => ["93.184.216.34"],
    proofVerifier,
    policy: POLICY,
  });
  const receipt = await client.authorize({ oidcToken: "header.payload.signature", context });
  assert.equal(receipt.digest, body.receiptDigest);
  const session = new G5SingleUseReceiptSession();
  assert.equal(session.consume(receipt).receiptDigest, body.receiptDigest);
  assert.throws(() => session.consume(receipt), TrustBrokerError);
  await reason(
    () => validateTrustBrokerReceipt({ ...body, receiptDigest: digest({ drift: true }) }, context, POLICY, proofVerifier),
    REASONS.RECEIPT,
  );
  await reason(
    () => validateTrustBrokerReceipt(validBrokerReceipt({ ...context, expiresAt: NOW - 1 }), { ...context, nowEpochSeconds: NOW }, POLICY, proofVerifier),
    REASONS.EXPIRED,
  );
});

test("trust broker HTTP client rejects unsafe endpoints before transport", async () => {
  await reason(async () => {
    new G5TrustBrokerHttpClient({
      endpoint: "http://127.0.0.1/authorize",
      transport: new FakeFetchTransport(() => Response.json({})),
      dnsResolve: async () => ["127.0.0.1"],
      proofVerifier,
      policy: POLICY,
    });
  }, REASONS.TRANSPORT);
  await reason(async () => {
    new G5TrustBrokerHttpClient({
      endpoint: "https://[::ffff:127.0.0.1]/authorize",
      transport: new FakeFetchTransport(() => Response.json({})),
      dnsResolve: async () => ["93.184.216.34"],
      proofVerifier,
      policy: POLICY,
    });
  }, REASONS.TRANSPORT);
  await reason(async () => {
    G5TrustBrokerHttpClient.endpointFromConfig({});
  }, REASONS.CONFIG);
});

test("connected Supabase collector is GET-only, publishable-only, paginated, and stable", async () => {
  const tables = oneRowTables();
  const transport = new FakeFetchTransport((request) => {
    const url = new URL(request.url);
    assert.equal(request.method, "GET");
    assert.equal(request.headers.has("authorization"), false);
    assert.equal(request.headers.get("apikey"), "sb_publishable_offline");
    const table = url.pathname.split("/").at(-1);
    assert.ok(Object.hasOwn(INTERNALS.SUPABASE_TABLES, table));
    if (url.searchParams.get("select") === "id" && url.searchParams.get("limit") === "1") {
      return Response.json([{ id: `${table}-1` }], { headers: { "content-range": "0-0/1" } });
    }
    assert.equal(url.searchParams.get("select"), INTERNALS.SUPABASE_TABLES[table]);
    return Response.json(tables[table]);
  });
  const sourceCalls = [];
  const collector = new G5ConnectedSupabaseCollector({
    env: {
      NEXT_PUBLIC_SUPABASE_URL: "https://supabase.example",
      NEXT_SUPABASE_PUBLISHABLE_KEY: "sb_publishable_offline",
    },
    transport,
    dnsResolve: async () => ["93.184.216.34"],
    receiptStore: receiptStore(),
    sourceTransport: {
      requestPinned: async (call) => {
        sourceCalls.push({ method: call.method, url: call.url });
        assert.deepEqual(call.resolvedAddresses, ["93.184.216.34"]);
        return { status: call.method === "HEAD" ? 405 : 200, redirected: false };
      },
    },
  });
  const receipt = await validateTrustBrokerReceipt(validBrokerReceipt(), {
    repositoryId: 101, runId: 303, runAttempt: 1,
  }, POLICY, proofVerifier);
  tables.institution_site_profiles[0] = {
    ...tables.institution_site_profiles[0],
    discovery_enabled: true,
    pipeline_enabled: true,
    pipeline_ready: true,
    seed_urls: ["https://catalog.example:443/programs?utm_source=x&fbclid=1", "https://catalog.example/programs"],
    circuit_open: false,
  };
  const result = await collector.collect({ receipt });
  assert.equal(result.decision, "PASS");
  assert.equal(result.connectedMode, INTERNALS.CONNECTED_DISABLED);
  assert.equal(Object.hasOwn(result, "counts"), false);
  assert.deepEqual(sourceCalls, [
    { method: "HEAD", url: "https://catalog.example/programs" },
    { method: "GET", url: "https://catalog.example/programs" },
  ]);
  assert.equal(transport.calls.every((call) => call.method === "GET"), true);
  await reason(() => collector.collect({ receipt }), REASONS.REPLAY);
});

test("connected Supabase collector rejects forged receipts and incomplete counts", async () => {
  const tables = oneRowTables();
  const withoutContentRange = new FakeFetchTransport((request) => {
    const table = new URL(request.url).pathname.split("/").at(-1);
    return Response.json(tables[table]);
  });
  const collector = new G5ConnectedSupabaseCollector({
    env: {
      NEXT_PUBLIC_SUPABASE_URL: "https://supabase.example",
      NEXT_SUPABASE_PUBLISHABLE_KEY: "sb_publishable_offline",
    },
    transport: withoutContentRange,
    dnsResolve: async () => ["93.184.216.34"],
    receiptStore: receiptStore(),
  });
  await reason(() => collector.collect({
    receipt: { digest: digest({ forged: true }), receipt: { forged: true } },
    sourceTargets: ["https://catalog.example/programs"],
  }), REASONS.SOURCE);
  await reason(() => collector.collect({
    receipt: { digest: digest({ forged: true }), receipt: { forged: true } },
  }), REASONS.RECEIPT);
  const receipt = await validateTrustBrokerReceipt(validBrokerReceipt(), {
    repositoryId: 101, runId: 303, runAttempt: 1,
  }, POLICY, proofVerifier);
  await reason(() => collector.collect({ receipt }), REASONS.PAGINATION);

  const countDriftTables = oneRowTables();
  let countCalls = 0;
  const countDrift = new FakeFetchTransport((request) => {
    const url = new URL(request.url);
    const table = url.pathname.split("/").at(-1);
    if (url.searchParams.get("select") === "id") {
      countCalls += 1;
      const count = countCalls === 1 ? 1 : 2;
      return Response.json([{ id: `${table}-1` }], { headers: { "content-range": `0-0/${count}` } });
    }
    return Response.json(countDriftTables[table]);
  });
  const countDriftCollector = new G5ConnectedSupabaseCollector({
    env: {
      NEXT_PUBLIC_SUPABASE_URL: "https://supabase.example",
      NEXT_SUPABASE_PUBLISHABLE_KEY: "sb_publishable_offline",
    },
    transport: countDrift,
    dnsResolve: async () => ["93.184.216.34"],
    receiptStore: receiptStore(),
  });
  await reason(() => countDriftCollector.collect({ receipt }), REASONS.COUNT);

  const malformedTables = oneRowTables();
  malformedTables.institution_site_profiles[0].seed_urls = null;
  const malformedTransport = new FakeFetchTransport((request) => {
    const url = new URL(request.url);
    const table = url.pathname.split("/").at(-1);
    if (url.searchParams.get("select") === "id") {
      return Response.json([{ id: `${table}-1` }], { headers: { "content-range": "0-0/1" } });
    }
    return Response.json(malformedTables[table]);
  });
  const malformedCollector = new G5ConnectedSupabaseCollector({
    env: {
      NEXT_PUBLIC_SUPABASE_URL: "https://supabase.example",
      NEXT_SUPABASE_PUBLISHABLE_KEY: "sb_publishable_offline",
    },
    transport: malformedTransport,
    dnsResolve: async () => ["93.184.216.34"],
    receiptStore: receiptStore(),
  });
  await reason(() => malformedCollector.collect({ receipt }), REASONS.PROFILE);

  const duplicateTables = oneRowTables();
  duplicateTables.institution_site_profiles.push({
    ...duplicateTables.institution_site_profiles[0],
    id: "institution_site_profiles-2",
  });
  const duplicateTransport = new FakeFetchTransport((request) => {
    const url = new URL(request.url);
    const table = url.pathname.split("/").at(-1);
    const rows = duplicateTables[table];
    if (url.searchParams.get("select") === "id") {
      return Response.json([{ id: rows[0].id }], { headers: { "content-range": `0-0/${rows.length}` } });
    }
    return Response.json(rows);
  });
  const duplicateCollector = new G5ConnectedSupabaseCollector({
    env: {
      NEXT_PUBLIC_SUPABASE_URL: "https://supabase.example",
      NEXT_SUPABASE_PUBLISHABLE_KEY: "sb_publishable_offline",
    },
    transport: duplicateTransport,
    dnsResolve: async () => ["93.184.216.34"],
    receiptStore: receiptStore(),
  });
  await reason(() => duplicateCollector.collect({ receipt }), REASONS.PROFILE);
});

test("connected Supabase collector derives required source targets from enabled profiles", async () => {
  const tables = oneRowTables();
  tables.institution_site_profiles[0] = {
    ...tables.institution_site_profiles[0],
    discovery_enabled: true,
    pipeline_enabled: true,
    pipeline_ready: true,
    seed_urls: ["https://catalog.example/programs"],
    circuit_open: false,
  };
  const transport = new FakeFetchTransport((request) => {
    const url = new URL(request.url);
    const table = url.pathname.split("/").at(-1);
    if (url.searchParams.get("select") === "id") {
      return Response.json([{ id: `${table}-1` }], { headers: { "content-range": "0-0/1" } });
    }
    return Response.json(tables[table]);
  });
  const collector = new G5ConnectedSupabaseCollector({
    env: {
      NEXT_PUBLIC_SUPABASE_URL: "https://supabase.example",
      NEXT_SUPABASE_PUBLISHABLE_KEY: "sb_publishable_offline",
    },
    transport,
    dnsResolve: async () => ["93.184.216.34"],
    receiptStore: receiptStore(),
    sourceTransport: { requestPinned: async () => ({ status: 503, redirected: false }) },
  });
  const receipt = await validateTrustBrokerReceipt(validBrokerReceipt(), {
    repositoryId: 101, runId: 303, runAttempt: 1,
  }, POLICY, proofVerifier);
  const result = await collector.collect({ receipt });
  assert.equal(result.decision, "STOP");
  assert.equal(result.reasonCode, REASONS.SOURCE);
});

test("connected Supabase collector remains disabled when config is absent or secret", async () => {
  await reason(async () => {
    new G5ConnectedSupabaseCollector({
      env: {},
      transport: new FakeFetchTransport(() => Response.json([])),
      dnsResolve: async () => ["93.184.216.34"],
    });
  }, REASONS.CONFIG);
  await reason(async () => {
    new G5ConnectedSupabaseCollector({
      env: {
        NEXT_PUBLIC_SUPABASE_URL: "https://supabase.example",
        NEXT_SUPABASE_PUBLISHABLE_KEY: "sb_publishable_offline",
        NEXT_SUPABASE_SECRET_KEY: ["sb", "secret", "forbidden"].join("_"),
      },
      transport: new FakeFetchTransport(() => Response.json([])),
      dnsResolve: async () => ["93.184.216.34"],
    });
  }, REASONS.SUPABASE);
  await reason(async () => {
    new G5ConnectedSupabaseCollector({
      env: {
        NEXT_PUBLIC_SUPABASE_URL: "https://supabase.example",
        NEXT_SUPABASE_PUBLISHABLE_KEY: "sb_publishable_offline",
      },
      transport: new FakeFetchTransport(() => Response.json([])),
      dnsResolve: async () => ["93.184.216.34"],
    });
  }, REASONS.CONFIG);
});

test("connected diagnostic CLI reports disabled instead of silently no-op", async () => {
  const result = await runG5ConnectedDiagnosticCli({
    argv: ["node", "index.mjs", "--g5-connected-diagnostic"],
    env: {},
  });
  assert.equal(result.decision, "STOP");
  assert.equal(result.reasonCode, REASONS.CONFIG);
});

test("identity includes all six authoritative numeric bindings", async () => {
  const base = { repositoryId: 1, runId: 2, runAttempt: 1, checkRunId: 3, environmentId: 4, deploymentId: 5 };
  const original = await gateIdentity(base);
  for (const field of Object.keys(base)) {
    assert.notEqual(await gateIdentity({ ...base, [field]: base[field] + 1 }), original);
  }
});

test("broker emits no logs or sensitive token material", async () => {
  const messages = [];
  const methods = Object.getOwnPropertyNames(console).filter(
    (method) => typeof console[method] === "function",
  );
  const originals = Object.fromEntries(methods.map((method) => [method, console[method]]));
  for (const method of methods) console[method] = (...values) => messages.push(values.join(" "));
  try {
    const { broker, request } = setup();
    await broker.authorize(request);
    assert.deepEqual(messages, []);
  } finally {
    for (const method of methods) console[method] = originals[method];
  }
});

test("Worker handler constructs broker from repository-only bindings", async () => {
  const setupValues = setup();
  const env = {
    ...RUNTIME_ENV,
    G5_TRUST_BROKER_ENDPOINT: "https://g5-trust-broker.example.invalid/authorize",
    G5_OFFLINE_JWKS: JWKS,
    G5_GITHUB_APP_READ_ONLY: setupValues.transport,
    G5_ATOMIC_LEDGER: { getByName: () => setupValues.ledger },
  };
  const request = new Request("https://repository-only.invalid/authorize", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(setupValues.request),
  });
  const originalNow = Date.now;
  Date.now = () => NOW * 1000;
  try {
    const response = await worker.fetch(request, env);
    const result = await response.json();
    assert.equal(response.status, 200);
    assert.match(result.receiptDigest, /^sha256:/);
  } finally {
    Date.now = originalNow;
  }
});

test("Worker handler stops when runtime bindings are absent", async () => {
  const setupValues = setup();
  const request = new Request("https://repository-only.invalid/authorize", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(setupValues.request),
  });
  const response = await worker.fetch(request, {
    G5_OFFLINE_JWKS: JWKS,
    G5_GITHUB_APP_READ_ONLY: setupValues.transport,
    G5_ATOMIC_LEDGER: { getByName: () => setupValues.ledger },
  });
  const body = await response.json();
  assert.equal(response.status, 400);
  assert.equal(body.decision, "STOP");
  assert.equal(body.reasonCode, INTERNALS.CONNECTED_DISABLED);
});

test("Worker handler closes arbitrary dependency errors to sanitized reason", async () => {
  const setupValues = setup();
  setupValues.transport.getWorkflowRun = async () => {
    throw new TrustBrokerError("private dependency detail");
  };
  const env = {
    ...RUNTIME_ENV,
    G5_TRUST_BROKER_ENDPOINT: "https://g5-trust-broker.example.invalid/authorize",
    G5_OFFLINE_JWKS: JWKS,
    G5_GITHUB_APP_READ_ONLY: setupValues.transport,
    G5_ATOMIC_LEDGER: { getByName: () => setupValues.ledger },
  };
  const request = new Request("https://repository-only.invalid/authorize", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(setupValues.request),
  });
  const originalNow = Date.now;
  Date.now = () => NOW * 1000;
  try {
    const response = await worker.fetch(request, env);
    assert.equal((await response.json()).reasonCode, REASONS.AMBIGUOUS);
  } finally {
    Date.now = originalNow;
  }
});
