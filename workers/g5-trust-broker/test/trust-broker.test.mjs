import assert from "node:assert/strict";
import { generateKeyPairSync, sign } from "node:crypto";
import test from "node:test";

import worker, {
  G5AtomicLedgerDurableObject,
  G5ConnectedGithubAppAdapter,
  G5TrustBroker,
  GithubAppReadOnlyAdapter,
  INTERNALS,
  REASONS,
  TrustBrokerError,
  createDisabledConnectedGithubAppAdapter,
  gateIdentity,
  rejectCallerAuthority,
  verifyGithubOidc,
} from "../src/index.mjs";

const NOW = 1_787_000_000;
const SHA = INTERNALS.REPOSITORY_POLICY.candidateSha;
const TREE = INTERNALS.REPOSITORY_POLICY.candidateTree;
const WORKFLOW_SHA = SHA;
const WORKFLOW_BLOB = INTERNALS.REPOSITORY_POLICY.workflowBlobSha;
const WORKFLOW_REF = INTERNALS.WORKFLOW_REF;

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

function fixture(overrides = {}) {
  const base = {
    workflow_run: [{
      id: 303, repositoryId: 101, ownerId: 202, repository: "romelhc95/studiamatch",
      ref: "refs/heads/main", refProtected: true, attempt: 1,
      event: "workflow_dispatch", headSha: SHA,
      actorId: 404, triggeringActorId: 405, conclusion: "success",
    }],
    check_run_job: [{ id: 505, runId: 303, name: "F10.9 G5 Production Read-Only Diagnostic", conclusion: "success" }],
    deployment: [{ id: 606, runId: 303, sha: SHA, environmentId: 707, environment: "Production" }],
    environment: [{ id: 707, name: "Production", protected: true }],
    approval: [{
      runId: 303, checkRunId: 505, deploymentId: 606, environmentId: 707,
      sha: SHA, workflowSha: WORKFLOW_SHA, state: "approved", reviewerId: 808,
    }],
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
  const ledger = new G5AtomicLedgerDurableObject({ storage }, { clock: () => clock.now });
  const transport = new FakeGithubTransport(data, transportOptions);
  const githubApp = new GithubAppReadOnlyAdapter(transport);
  const broker = new G5TrustBroker({
    jwks: JWKS, githubApp, ledger, policy,
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
  await assert.rejects(call, (error) => error instanceof TrustBrokerError && error.reason === expected);
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
    "approval", "check_run_job", "commit_tree", "deployment", "environment",
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
    [{ ...fixture().approval[0], deploymentId: 999 }],
    [{ ...fixture().approval[0], workflowSha: "9".repeat(40) }],
  ]) {
    const { broker, request } = setup({ data: fixture({ approval }) });
    await reason(() => broker.authorize(request), REASONS.APPROVAL);
  }
});

test("authoritative evidence must declare a complete result set", async () => {
  const { broker, request } = setup({ transportOptions: { incompleteResource: "check_run_job" } });
  await reason(() => broker.authorize(request), REASONS.BINDING);
});

test("deployment must be exact-one and bound to candidate SHA", async () => {
  for (const deployment of [[], [fixture().deployment[0], fixture().deployment[0]], [{ ...fixture().deployment[0], sha: "9".repeat(40) }]]) {
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

test("matching alternate evidence and injected policy cannot replace frozen policy", async () => {
  const alternateTree = "8".repeat(40);
  const alternateBlob = "7".repeat(40);
  const data = fixture({
    commit_tree: [{ sha: SHA, tree: alternateTree }],
    workflow_blob: [{ ...fixture().workflow_blob[0], blobSha: alternateBlob }],
  });
  const policy = {
    ...INTERNALS.REPOSITORY_POLICY,
    candidateTree: alternateTree,
    workflowBlobSha: alternateBlob,
  };
  const { broker, request } = setup({ data, policy });
  await reason(() => broker.authorize(request), REASONS.BINDING);
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

test("connected GitHub App adapter remains disabled before transport", async () => {
  const adapter = createDisabledConnectedGithubAppAdapter();
  assert.equal(adapter.state, "REPOSITORY_ONLY_DISABLED");
  await reason(() => adapter.authoritativeEvidence(claims()), "STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED");
  await reason(async () => {
    new G5ConnectedGithubAppAdapter({ enabled: true });
  }, "STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED");
});

test("manual workflow policy is repository-only disabled", () => {
  assert.deepEqual(INTERNALS.MANUAL_WORKFLOW_POLICY, {
    state: "REPOSITORY_ONLY_DISABLED",
    dispatchAllowed: false,
    idTokenPermission: false,
    productionEnvironment: false,
    connectedTransport: false,
  });
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

test("Worker handler closes arbitrary dependency errors to sanitized reason", async () => {
  const setupValues = setup();
  setupValues.transport.getWorkflowRun = async () => {
    throw new TrustBrokerError("private dependency detail");
  };
  const env = {
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
