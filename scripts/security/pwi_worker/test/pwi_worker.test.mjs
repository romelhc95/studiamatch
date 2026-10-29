import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { GitHubApi, createAppJwt } from "../github.mjs";
import { PwiCoordinator, handleRequest } from "../index.mjs";
import {
  REPOSITORY_FULL_NAME,
  REPOSITORY_ID,
  classifyProtectedFiles,
  hasTrustedCurrentApproval,
  pullRequestContext,
} from "../policy.mjs";

const HEAD = "a".repeat(40);
const NEXT_HEAD = "b".repeat(40);
const NOW = Date.parse("2026-10-19T15:00:00Z");
const APP_ID = "12345";
const INSTALLATION_ID = "67890";
const WEBHOOK_SECRET = "synthetic-only-webhook-secret-value-123456";
const encoder = new TextEncoder();

test("Wrangler config binds the tested per-PR coordinator as a new SQLite class", () => {
  const config = JSON.parse(readFileSync(new URL("../wrangler.jsonc", import.meta.url), "utf8"));
  assert.equal(config.name, "studiamatch-pwi-verifier");
  assert.deepEqual(config.durable_objects.bindings, [
    { name: "PWI_COORDINATOR", class_name: "PwiCoordinator" },
  ]);
  assert.deepEqual(config.migrations, [
    { tag: "v1", new_sqlite_classes: ["PwiCoordinator"] },
  ]);
  assert.equal(config.workers_dev, true);
});

function approval({
  login = "approver",
  type = "User",
  association = "COLLABORATOR",
  state = "APPROVED",
  commitId = HEAD,
  submittedAt = "2026-10-19T14:00:00Z",
  id = 1,
} = {}) {
  return {
    id,
    state,
    commit_id: commitId,
    submitted_at: submittedAt,
    author_association: association,
    user: { login, type },
  };
}

function prPayload({ headSha = HEAD, repoId = REPOSITORY_ID, repoName = REPOSITORY_FULL_NAME } = {}) {
  return {
    action: "synchronize",
    installation: { id: Number(INSTALLATION_ID) },
    repository: { id: repoId, full_name: repoName },
    number: 501,
    pull_request: {
      number: 501,
      base: { ref: "desarrollo" },
      head: { sha: headSha },
      user: { login: "romelhc95" },
    },
  };
}

async function generateAppKeyPair() {
  const pair = await crypto.subtle.generateKey(
    { name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: Uint8Array.of(1, 0, 1), hash: "SHA-256" },
    true,
    ["sign", "verify"],
  );
  const bytes = new Uint8Array(await crypto.subtle.exportKey("pkcs8", pair.privateKey));
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  const encoded = btoa(binary).match(/.{1,64}/g).join("\n");
  return {
    privateKeyPem: `-----BEGIN PRIVATE KEY-----\n${encoded}\n-----END PRIVATE KEY-----`,
    publicKey: pair.publicKey,
  };
}

const APP_KEY_PAIR = await generateAppKeyPair();
const PRIVATE_KEY_PEM = APP_KEY_PAIR.privateKeyPem;
const ENV = {
  GITHUB_APP_ID: APP_ID,
  GITHUB_INSTALLATION_ID: INSTALLATION_ID,
  GITHUB_APP_PRIVATE_KEY: PRIVATE_KEY_PEM,
  GITHUB_WEBHOOK_SECRET: WEBHOOK_SECRET,
};

async function signedWebhook(payload, { event = "pull_request", secret = WEBHOOK_SECRET, delivery = crypto.randomUUID() } = {}) {
  const raw = encoder.encode(JSON.stringify(payload));
  const key = await crypto.subtle.importKey("raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const digest = new Uint8Array(await crypto.subtle.sign("HMAC", key, raw));
  const signature = [...digest].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  return new Request("https://pwi.example.workers.dev/webhooks/github", {
    method: "POST",
    headers: {
      "x-github-event": event,
      "x-github-delivery": delivery,
      "x-hub-signature-256": `sha256=${signature}`,
      "content-type": "application/json",
    },
    body: raw,
  });
}

function jsonResponse(value, status = 200) {
  return new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json" } });
}

function derValue(bytes, offset, expectedTag) {
  assert.equal(bytes[offset], expectedTag);
  let length = bytes[offset + 1];
  let headerLength = 2;
  if ((length & 0x80) !== 0) {
    const octets = length & 0x7f;
    length = 0;
    for (let index = 0; index < octets; index += 1) length = length * 256 + bytes[offset + 2 + index];
    headerLength += octets;
  }
  const start = offset + headerLength;
  return { start, end: start + length, bytes: bytes.slice(start, start + length) };
}

function githubMock({
  files = [{ filename: "scripts/security/policy.mjs", status: "added" }],
  reviews = [approval()],
  headSha = HEAD,
  apiFailure = null,
  precheckPatchFailures = 0,
} = {}) {
  const requests = [];
  const checkPosts = [];
  let failedFileCalls = 0;
  let failedPrecheckPatchCalls = 0;
  const fetchImpl = async (input, init = {}) => {
    const url = new URL(input);
    requests.push({ url, init });
    if (url.origin !== "https://api.github.com") throw new Error("unexpected destination");
    if (url.pathname === `/app/installations/${INSTALLATION_ID}/access_tokens`) {
      return jsonResponse({ token: "synthetic-installation-token", expires_at: "2026-10-19T16:00:00Z" });
    }
    if (url.pathname === "/repos/romelhc95/studiamatch/pulls/501" && init.method === "GET") {
      return jsonResponse({
        number: 501,
        base: { ref: "desarrollo" },
        head: { sha: headSha },
        user: { login: "romelhc95" },
      });
    }
    if (url.pathname === "/repos/romelhc95/studiamatch/pulls/501/files" && init.method === "GET") {
      if (apiFailure === "files_500_until_exhausted") {
        failedFileCalls += 1;
        if (failedFileCalls <= 4) return jsonResponse({ message: "synthetic" }, 500);
      }
      return jsonResponse(files);
    }
    if (url.pathname === "/repos/romelhc95/studiamatch/pulls/501/reviews" && init.method === "GET") {
      return jsonResponse(reviews);
    }
    if (/^\/repos\/romelhc95\/studiamatch\/commits\/[0-9a-f]{40}\/check-runs$/.test(url.pathname) && init.method === "GET") {
      const requestedSha = url.pathname.split("/").at(-2);
      return jsonResponse({ check_runs: checkPosts.flatMap((check, index) => check.head_sha === requestedSha ? [{
        id: index + 111,
        name: check.name,
        head_sha: check.head_sha,
        external_id: check.external_id,
        app: { id: Number(APP_ID) },
      }] : []) });
    }
    if (url.pathname === "/repos/romelhc95/studiamatch/check-runs" && init.method === "POST") {
      checkPosts.push(JSON.parse(init.body));
      return jsonResponse({ id: 111, head_sha: checkPosts.at(-1).head_sha, status: "in_progress" });
    }
    if (url.pathname.startsWith("/repos/romelhc95/studiamatch/check-runs/") && init.method === "PATCH") {
      const index = Number(url.pathname.split("/").at(-1)) - 111;
      const patch = JSON.parse(init.body);
      if (patch.status === "in_progress" && failedPrecheckPatchCalls < precheckPatchFailures) {
        failedPrecheckPatchCalls += 1;
        return jsonResponse({ message: "synthetic" }, 500);
      }
      Object.assign(checkPosts[index], patch);
      if (patch.status === "in_progress") {
        delete checkPosts[index].conclusion;
        delete checkPosts[index].completed_at;
      }
      return jsonResponse({ id: index + 111, head_sha: checkPosts[index].head_sha, status: patch.status, conclusion: patch.conclusion });
    }
    throw new Error(`unexpected GitHub API request ${init.method} ${url.pathname}`);
  };
  return {
    fetchImpl,
    requests,
    checkPosts,
    get failedFileCalls() { return failedFileCalls; },
    get failedPrecheckPatchCalls() { return failedPrecheckPatchCalls; },
  };
}

function workerEnv(mock) {
  const env = { ...ENV };
  const clock = { now: NOW };
  const coordinator = new PwiCoordinator({}, env, {
    fetchImpl: mock.fetchImpl,
    now: () => clock.now,
    sleep: async () => {},
  });
  env.PWI_COORDINATOR = {
    getByName(name) {
      assert.equal(name, `${REPOSITORY_ID}:pull:501`);
      return { fetch: (request) => coordinator.fetch(request) };
    },
  };
  return { env, coordinator, advance(ms) { clock.now += ms; } };
}

test("classifies protected destinations and rename sources only", () => {
  assert.deepEqual(classifyProtectedFiles([
    { filename: ".github/workflows/new.yml", status: "added" },
    { filename: "web/src/page.tsx", previous_filename: "scripts/security/old.mjs", status: "renamed" },
    { filename: "README.md", status: "modified" },
  ]), [".github/workflows/new.yml", "scripts/security/old.mjs"]);
});

test("fails closed for malformed paths and incomplete renames", () => {
  assert.throws(() => classifyProtectedFiles([{ filename: "safe.txt", status: "renamed" }]), /rename_source_missing/);
  assert.throws(() => classifyProtectedFiles([{ filename: "../.github/workflows/x.yml" }]), /invalid_changed_path/);
  assert.throws(() => classifyProtectedFiles([{ filename: ".github\\workflows\\x.yml" }]), /invalid_changed_path/);
});

test("accepts only a trusted non-author approval on the current head", () => {
  assert.equal(hasTrustedCurrentApproval([approval()], { headSha: HEAD, prAuthor: "romelhc95" }), true);
  assert.equal(hasTrustedCurrentApproval([approval({ commitId: "b".repeat(40) })], { headSha: HEAD, prAuthor: "romelhc95" }), false);
  assert.equal(hasTrustedCurrentApproval([approval({ login: "romelhc95" })], { headSha: HEAD, prAuthor: "romelhc95" }), false);
  assert.equal(hasTrustedCurrentApproval([approval({ association: "NONE" })], { headSha: HEAD, prAuthor: "romelhc95" }), false);
  assert.equal(hasTrustedCurrentApproval([approval({ type: "Bot" })], { headSha: HEAD, prAuthor: "romelhc95" }), false);
});

test("a later non-approval supersedes the same reviewer's approval", () => {
  assert.equal(hasTrustedCurrentApproval([
    approval({ id: 1, state: "APPROVED", submittedAt: "2026-10-19T14:00:00Z" }),
    approval({ id: 2, state: "CHANGES_REQUESTED", submittedAt: "2026-10-19T14:01:00Z" }),
  ], { headSha: HEAD, prAuthor: "romelhc95" }), false);
});

test("rejects webhook with invalid signature before contacting GitHub", async () => {
  const request = await signedWebhook(prPayload(), { secret: "different-synthetic-secret-value-123456" });
  const mock = githubMock();
  const result = await handleRequest(request, workerEnv(mock).env);
  assert.equal(result.status, 401);
  assert.equal(mock.requests.length, 0);
});

test("publishes trusted PWI success from the App for the exact current SHA", async () => {
  const request = await signedWebhook(prPayload());
  const mock = githubMock();
  const { env, coordinator } = workerEnv(mock);
  const result = await handleRequest(request, env);
  const data = await result.json();
  assert.equal(result.status, 202);
  assert.equal(data.status, "queued");
  await coordinator.alarm();
  assert.equal(mock.checkPosts.length, 1);
  assert.equal(mock.checkPosts[0].head_sha, HEAD);
  assert.equal(mock.checkPosts[0].name, "Protected Workflow Integrity");
  assert.equal(mock.checkPosts[0].conclusion, "success");
  assert.equal(mock.checkPosts[0].external_id, `pwi-v1-${REPOSITORY_ID}-501`);
  assert.ok(mock.requests.every(({ url }) => url.origin === "https://api.github.com"));
  assert.equal(mock.requests[0].url.pathname, `/app/installations/${INSTALLATION_ID}/access_tokens`);
});

test("returns 503 when durable alarm scheduling fails and accepts the same delivery after retry", async () => {
  const mock = githubMock();
  const { env, coordinator } = workerEnv(mock);
  let failScheduling = true;
  coordinator.ctx = {
    storage: {
      async setAlarm() {
        if (failScheduling) throw new Error("synthetic alarm storage failure");
      },
      async deleteAlarm() {},
    },
  };
  const delivery = crypto.randomUUID();
  const request = await signedWebhook(prPayload(), { delivery });

  const rejected = await handleRequest(request, env);
  assert.equal(rejected.status, 503);
  assert.equal(coordinator.getEventByDelivery(delivery).status, "pending");
  assert.equal(coordinator.pendingEvents, 1);

  failScheduling = false;
  const retried = await handleRequest(await signedWebhook(prPayload(), { delivery }), env);
  assert.equal(retried.status, 202);
  assert.deepEqual(await retried.json(), { status: "already_queued" });
  assert.equal(coordinator.pendingEvents, 1);
});

test("schedules a durable retry when pre-ack check invalidation fails", async () => {
  const mock = githubMock({ precheckPatchFailures: 4 });
  mock.checkPosts.push({
    name: "Protected Workflow Integrity",
    external_id: `pwi-v1-${REPOSITORY_ID}-501`,
    head_sha: HEAD,
    status: "completed",
    conclusion: "success",
  });
  const { env, coordinator } = workerEnv(mock);
  let scheduledAlarm = null;
  coordinator.ctx = {
    storage: {
      async setAlarm(timestamp) { scheduledAlarm = timestamp; },
      async deleteAlarm() { scheduledAlarm = null; },
    },
  };

  const result = await handleRequest(await signedWebhook(prPayload()), env);
  assert.equal(result.status, 503, "a failed precheck must not acknowledge the webhook");
  assert.equal(mock.failedPrecheckPatchCalls, 4, "the GitHub API client keeps its bounded retry limit");
  assert.equal(mock.checkPosts[0].status, "completed", "the test preserves the prior check until the retry runs");
  assert.equal(mock.checkPosts[0].conclusion, "success");
  assert.equal(coordinator.pendingEvents, 1, "the normalized event remains queued");
  assert.equal(scheduledAlarm, NOW + 50, "the persisted event must have a durable retry scheduled");

  await coordinator.alarm();
  assert.equal(mock.checkPosts[0].status, "completed");
  assert.equal(mock.checkPosts[0].conclusion, "success");
  const reopenIndex = mock.requests.findIndex(({ init }) =>
    init.method === "PATCH" && JSON.parse(init.body).status === "in_progress",
  );
  const pullReadIndex = mock.requests.findIndex(({ url }) =>
    url.pathname === "/repos/romelhc95/studiamatch/pulls/501",
  );
  assert.ok(reopenIndex >= 0 && reopenIndex < pullReadIndex, "the retry invalidates the old check before evaluation");
});

test("publishes failure when protected paths lack a trusted current approval", async () => {
  const request = await signedWebhook(prPayload());
  const mock = githubMock({ reviews: [approval({ commitId: "b".repeat(40) })] });
  const { env, coordinator } = workerEnv(mock);
  const result = await handleRequest(request, env);
  assert.equal(result.status, 202);
  await coordinator.alarm();
  assert.equal(mock.checkPosts[0].conclusion, "failure");
  assert.match(mock.checkPosts[0].output.summary, /current head SHA/);
});

test("serializes approval and revocation events for one PR so stale success cannot win", async () => {
  const mock = githubMock();
  let releaseFirstReview;
  let announceFirstReview;
  const firstReviewStarted = new Promise((resolve) => { announceFirstReview = resolve; });
  const releaseGate = new Promise((resolve) => { releaseFirstReview = resolve; });
  let reviewCalls = 0;
  const concurrentFetch = async (input, init) => {
    const url = new URL(input);
    if (url.pathname === "/repos/romelhc95/studiamatch/pulls/501/reviews" && init.method === "GET") {
      reviewCalls += 1;
      if (reviewCalls === 1) {
        announceFirstReview();
        await releaseGate;
        return jsonResponse([approval()]);
      }
      return jsonResponse([]);
    }
    return mock.fetchImpl(input, init);
  };
  const serialMock = { ...mock, fetchImpl: concurrentFetch };
  const { env, coordinator } = workerEnv(serialMock);
  const firstRequest = await signedWebhook(prPayload());
  const revocation = prPayload();
  revocation.action = "submitted";
  revocation.review = approval({ state: "CHANGES_REQUESTED", id: 2 });
  const secondRequest = await signedWebhook(revocation, { event: "pull_request_review" });

  const firstResponse = await handleRequest(firstRequest, env);
  assert.equal(firstResponse.status, 202);
  const firstAlarm = coordinator.alarm();
  await firstReviewStarted;
  const secondResponse = await handleRequest(secondRequest, env);
  assert.equal(secondResponse.status, 202);
  assert.equal(reviewCalls, 1, "second event must wait while the first event is inside the PR coordinator");
  releaseFirstReview();
  await firstAlarm;
  assert.equal(mock.checkPosts.length, 0, "an earlier review must not publish a stale success while a newer event is queued");
  await coordinator.alarm();

  assert.equal(reviewCalls, 2);
  assert.equal(mock.checkPosts.length, 1);
  assert.equal(mock.checkPosts[0].conclusion, "failure");
});

test("does not publish a stale success when revocation arrives during check lookup", async () => {
  const currentReviews = [approval()];
  const mock = githubMock({ reviews: currentReviews });
  let delayCheckLookup = false;
  let releaseCheckLookup;
  let announceCheckLookup;
  const checkLookupStarted = new Promise((resolve) => { announceCheckLookup = resolve; });
  const releaseGate = new Promise((resolve) => { releaseCheckLookup = resolve; });
  const delayedFetch = async (input, init) => {
    const url = new URL(input);
    if (delayCheckLookup && url.pathname === `/repos/romelhc95/studiamatch/commits/${HEAD}/check-runs` && init.method === "GET") {
      delayCheckLookup = false;
      announceCheckLookup();
      await releaseGate;
    }
    return mock.fetchImpl(input, init);
  };
  const delayedMock = { ...mock, fetchImpl: delayedFetch };
  const { env, coordinator } = workerEnv(delayedMock);
  const firstResponse = await handleRequest(await signedWebhook(prPayload()), env);
  assert.equal(firstResponse.status, 202);
  delayCheckLookup = true;
  const firstAlarm = coordinator.alarm();
  await checkLookupStarted;

  const revocation = prPayload();
  revocation.action = "submitted";
  revocation.review = approval({ state: "CHANGES_REQUESTED", id: 2 });
  currentReviews.splice(0, currentReviews.length, revocation.review);
  const revocationDelivery = crypto.randomUUID();
  const secondResponse = await handleRequest(
    await signedWebhook(revocation, { event: "pull_request_review", delivery: revocationDelivery }),
    env,
  );
  assert.equal(secondResponse.status, 503, "the pre-ACK lock times out closed while an older check lookup is unresolved");
  releaseCheckLookup();
  await firstAlarm;

  assert.equal(mock.checkPosts.length, 0, "a queued revocation must be checked again after the check lookup completes");
  const redelivery = await handleRequest(
    await signedWebhook(revocation, { event: "pull_request_review", delivery: revocationDelivery }),
    env,
  );
  assert.equal(redelivery.status, 202, "redelivery invalidates the check before acknowledging the webhook");
  assert.equal(mock.checkPosts.length, 0, "a missing prior check needs no mutation before ACK");
  await coordinator.alarm();
  assert.equal(mock.checkPosts.length, 1);
  assert.equal(mock.checkPosts[0].conclusion, "failure");
});

test("reopens an earlier success before PR reads and leaves it pending when superseded", async () => {
  const currentReviews = [approval()];
  const mock = githubMock({ reviews: currentReviews });
  let delayPullLookup = false;
  let releasePullLookup;
  let announcePullLookup;
  const pullLookupStarted = new Promise((resolve) => { announcePullLookup = resolve; });
  const pullLookupGate = new Promise((resolve) => { releasePullLookup = resolve; });
  const delayedFetch = async (input, init) => {
    const url = new URL(input);
    if (delayPullLookup && url.pathname === "/repos/romelhc95/studiamatch/pulls/501" && init.method === "GET") {
      delayPullLookup = false;
      announcePullLookup();
      await pullLookupGate;
    }
    return mock.fetchImpl(input, init);
  };
  const delayedMock = { ...mock, fetchImpl: delayedFetch };
  const { env, coordinator } = workerEnv(delayedMock);
  const firstResponse = await handleRequest(await signedWebhook(prPayload()), env);
  assert.equal(firstResponse.status, 202);
  await coordinator.alarm();
  assert.equal(mock.checkPosts[0].conclusion, "success");

  const renewedApproval = prPayload();
  renewedApproval.action = "submitted";
  renewedApproval.review = approval({ id: 2, submittedAt: "2026-10-19T14:30:00Z" });
  currentReviews.splice(0, currentReviews.length, renewedApproval.review);
  const secondResponse = await handleRequest(
    await signedWebhook(renewedApproval, { event: "pull_request_review" }),
    env,
  );
  assert.equal(secondResponse.status, 202);
  assert.equal(mock.checkPosts[0].status, "in_progress", "webhook acknowledgement must invalidate the prior success before the alarm starts");
  delayPullLookup = true;
  const secondAlarm = coordinator.alarm();
  await pullLookupStarted;
  assert.equal(mock.checkPosts[0].status, "in_progress", "a previous success must be reopened before waiting on PR reads");

  const revocation = prPayload();
  revocation.action = "submitted";
  revocation.review = approval({ state: "CHANGES_REQUESTED", id: 3, submittedAt: "2026-10-19T14:45:00Z" });
  currentReviews.splice(0, currentReviews.length, revocation.review);
  const thirdResponse = await handleRequest(
    await signedWebhook(revocation, { event: "pull_request_review" }),
    env,
  );
  assert.equal(thirdResponse.status, 202);
  releasePullLookup();
  await secondAlarm;

  assert.equal(mock.checkPosts[0].status, "in_progress", "a superseded event must not restore the earlier success");
  assert.equal(mock.checkPosts[0].conclusion, undefined);
  await coordinator.alarm();
  assert.equal(mock.checkPosts[0].status, "completed");
  assert.equal(mock.checkPosts[0].conclusion, "failure");
});

test("reopens an earlier success when a newer event is already queued", async () => {
  const currentReviews = [approval()];
  const mock = githubMock({ reviews: currentReviews });
  const { env, coordinator } = workerEnv(mock);
  const firstResponse = await handleRequest(await signedWebhook(prPayload()), env);
  assert.equal(firstResponse.status, 202);
  await coordinator.alarm();
  assert.equal(mock.checkPosts[0].conclusion, "success");

  const renewedApproval = prPayload();
  renewedApproval.action = "submitted";
  renewedApproval.review = approval({ id: 2, submittedAt: "2026-10-19T14:30:00Z" });
  const queuedApproval = await handleRequest(
    await signedWebhook(renewedApproval, { event: "pull_request_review" }),
    env,
  );
  assert.equal(queuedApproval.status, 202);

  const revocation = prPayload();
  revocation.action = "submitted";
  revocation.review = approval({ state: "CHANGES_REQUESTED", id: 3, submittedAt: "2026-10-19T14:45:00Z" });
  currentReviews.splice(0, currentReviews.length, revocation.review);
  const queuedRevocation = await handleRequest(
    await signedWebhook(revocation, { event: "pull_request_review" }),
    env,
  );
  assert.equal(queuedRevocation.status, 202);

  const pullReadsBefore = mock.requests.filter(({ url }) => url.pathname === "/repos/romelhc95/studiamatch/pulls/501").length;
  await coordinator.alarm();
  assert.equal(mock.checkPosts[0].status, "in_progress", "a superseded event must reopen the previous success");
  assert.equal(mock.checkPosts[0].conclusion, undefined);
  assert.equal(
    mock.requests.filter(({ url }) => url.pathname === "/repos/romelhc95/studiamatch/pulls/501").length,
    pullReadsBefore,
    "a queued successor must be detected before reading the PR",
  );

  await coordinator.alarm();
  assert.equal(mock.checkPosts[0].status, "completed");
  assert.equal(mock.checkPosts[0].conclusion, "failure");
});

test("persists a current event and invalidates an earlier success when the queue is full", async () => {
  const mock = githubMock();
  mock.checkPosts.push({
    name: "Protected Workflow Integrity",
    external_id: `pwi-v1-${REPOSITORY_ID}-501`,
    head_sha: HEAD,
    status: "completed",
    conclusion: "success",
  });
  const { env, coordinator } = workerEnv(mock);
  const queuedDeliveries = [];
  for (let index = 0; index < 8; index += 1) {
    const delivery = crypto.randomUUID();
    queuedDeliveries.push(delivery);
    coordinator.insertEvent({ delivery, prNumber: 501, headSha: HEAD }, NOW + index);
  }

  const incomingDelivery = crypto.randomUUID();
  const result = await handleRequest(
    await signedWebhook(prPayload(), { delivery: incomingDelivery }),
    env,
  );
  assert.equal(result.status, 202);
  assert.equal(mock.checkPosts[0].status, "in_progress", "a full queue must not leave an earlier success current");
  assert.equal(coordinator.pendingEvents, 8);
  assert.equal(coordinator.getEventByDelivery(queuedDeliveries[0]).status, "failed");
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).headSha, HEAD);
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).status, "pending");
});

test("persists a newer current-SHA event when the full queue has that SHA processing", async () => {
  const currentReviews = [approval()];
  const mock = githubMock({ reviews: currentReviews });
  mock.checkPosts.push({
    name: "Protected Workflow Integrity",
    external_id: `pwi-v1-${REPOSITORY_ID}-501`,
    head_sha: HEAD,
    status: "completed",
    conclusion: "success",
  });
  const baseFetch = mock.fetchImpl;
  let delayCompletedPatch = false;
  let releaseCompletedPatch;
  let announceCompletedPatch;
  const completedPatchStarted = new Promise((resolve) => { announceCompletedPatch = resolve; });
  const completedPatchGate = new Promise((resolve) => { releaseCompletedPatch = resolve; });
  mock.fetchImpl = async (input, init = {}) => {
    const url = new URL(input);
    const body = init.body ? JSON.parse(init.body) : {};
    if (delayCompletedPatch && url.pathname === "/repos/romelhc95/studiamatch/check-runs/111" &&
        init.method === "PATCH" && body.status === "completed") {
      delayCompletedPatch = false;
      announceCompletedPatch();
      await completedPatchGate;
    }
    return baseFetch(input, init);
  };

  const { env, coordinator } = workerEnv(mock);
  const processingDelivery = crypto.randomUUID();
  coordinator.insertEvent({ delivery: processingDelivery, prNumber: 501, headSha: HEAD }, NOW - 10);

  delayCompletedPatch = true;
  const processingAlarm = coordinator.alarm();
  await completedPatchStarted;
  const staleDeliveries = [];
  for (let index = 0; index < 7; index += 1) {
    const delivery = crypto.randomUUID();
    staleDeliveries.push(delivery);
    coordinator.insertEvent({ delivery, prNumber: 501, headSha: NEXT_HEAD }, NOW - index - 9);
  }
  currentReviews.splice(0, currentReviews.length, approval({
    state: "CHANGES_REQUESTED",
    id: 2,
    submittedAt: "2026-10-19T14:30:00Z",
  }));

  const incomingDelivery = crypto.randomUUID();
  const incoming = prPayload();
  incoming.action = "submitted";
  incoming.review = currentReviews[0];
  const result = await handleRequest(
    await signedWebhook(incoming, { event: "pull_request_review", delivery: incomingDelivery }),
    env,
  );
  assert.equal(result.status, 503, "the full-queue precheck times out closed while an older publisher owns the check lock");
  assert.equal(coordinator.pendingEvents, 8, "the queue remains capped after replacing one pending event");
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).headSha, HEAD);
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).status, "pending");
  assert.equal(coordinator.getEventByDelivery(staleDeliveries[0]).status, "failed");

  releaseCompletedPatch();
  await processingAlarm;
  const redelivery = await handleRequest(
    await signedWebhook(incoming, { event: "pull_request_review", delivery: incomingDelivery }),
    env,
  );
  assert.equal(redelivery.status, 202, "the same delivery can invalidate the check and be acknowledged after the old write ends");
  assert.equal(coordinator.getEventByDelivery(processingDelivery).status, "done");
  assert.equal(mock.checkPosts[0].status, "in_progress", "the new webhook must supersede an alarm already publishing success");
  assert.equal(mock.checkPosts[0].conclusion, undefined);

  for (let index = 0; index < staleDeliveries.length; index += 1) await coordinator.alarm();
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).status, "done");
  assert.equal(mock.checkPosts[0].status, "completed");
  assert.equal(mock.checkPosts[0].conclusion, "failure", "the latest review state replaces the stale success");
});

test("same-delivery redelivery waits for an active publisher and leaves work queued", async () => {
  const mock = githubMock();
  mock.checkPosts.push({
    name: "Protected Workflow Integrity",
    external_id: `pwi-v1-${REPOSITORY_ID}-501`,
    head_sha: HEAD,
    status: "completed",
    conclusion: "success",
  });
  const baseFetch = mock.fetchImpl;
  let delayCompletedPatch = true;
  let releaseCompletedPatch;
  let announceCompletedPatch;
  const completedPatchStarted = new Promise((resolve) => { announceCompletedPatch = resolve; });
  const completedPatchGate = new Promise((resolve) => { releaseCompletedPatch = resolve; });
  const delayedMock = {
    ...mock,
    fetchImpl: async (input, init = {}) => {
      const url = new URL(input);
      const body = init.body ? JSON.parse(init.body) : {};
      if (delayCompletedPatch && url.pathname === "/repos/romelhc95/studiamatch/check-runs/111" &&
          init.method === "PATCH" && body.status === "completed") {
        delayCompletedPatch = false;
        announceCompletedPatch();
        await completedPatchGate;
      }
      return baseFetch(input, init);
    },
  };
  const { env, coordinator } = workerEnv(delayedMock);
  const delivery = crypto.randomUUID();
  coordinator.insertEvent({ delivery, prNumber: 501, headSha: HEAD }, NOW);

  const processingAlarm = coordinator.alarm();
  await completedPatchStarted;
  let redeliveryResolved = false;
  const redelivery = handleRequest(
    await signedWebhook(prPayload(), { delivery }),
    env,
  ).then((result) => {
    redeliveryResolved = true;
    return result;
  });
  for (let attempt = 0; attempt < 50 && coordinator.getEventByDelivery(delivery).status !== "pending"; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  assert.equal(coordinator.getEventByDelivery(delivery).status, "pending", "the active row is resequenced for redelivery");
  assert.equal(redeliveryResolved, false, "pre-ACK invalidation waits for the active check writer");

  releaseCompletedPatch();
  await processingAlarm;
  const result = await redelivery;
  assert.equal(result.status, 202);
  assert.equal(coordinator.pendingEvents, 1, "the redelivered event remains available to finish verification");
  assert.equal(coordinator.getEventByDelivery(delivery).status, "pending");
  assert.equal(mock.checkPosts[0].status, "in_progress", "the old completion cannot become the last write before ACK");

  await coordinator.alarm();
  assert.equal(coordinator.getEventByDelivery(delivery).status, "done");
  assert.equal(mock.checkPosts[0].status, "completed");
  assert.equal(mock.checkPosts[0].conclusion, "success");
});

test("fails closed without mutating duplicate matching Check Runs", async () => {
  const duplicateCheck = {
    name: "Protected Workflow Integrity",
    external_id: `pwi-v1-${REPOSITORY_ID}-501`,
    head_sha: HEAD,
    status: "completed",
    conclusion: "success",
  };
  const mock = githubMock();
  mock.checkPosts.push({ ...duplicateCheck }, { ...duplicateCheck });
  const result = await handleRequest(await signedWebhook(prPayload()), workerEnv(mock).env);

  assert.equal(result.status, 503);
  assert.deepEqual(mock.checkPosts, [duplicateCheck, duplicateCheck]);
});

test("does not run a queued check write after its deadline expires", async () => {
  const { coordinator } = workerEnv(githubMock());
  let releaseFirst;
  let announceFirst;
  const firstStarted = new Promise((resolve) => { announceFirst = resolve; });
  const firstGate = new Promise((resolve) => { releaseFirst = resolve; });
  const first = coordinator.withCheckWriteLock(async () => {
    announceFirst();
    await firstGate;
  });
  await firstStarted;

  let expiredOperationRan = false;
  await assert.rejects(
    coordinator.withCheckWriteLock(() => { expiredOperationRan = true; }, NOW + 5),
    /check_write_deadline_exceeded/,
  );
  releaseFirst();
  await first;
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(expiredOperationRan, false);
});

test("pre-ACK invalidation is the final check write when post-publication recovery fails", async () => {
  const currentReviews = [approval()];
  const mock = githubMock({ reviews: currentReviews });
  mock.checkPosts.push({
    name: "Protected Workflow Integrity",
    external_id: `pwi-v1-${REPOSITORY_ID}-501`,
    head_sha: HEAD,
    status: "completed",
    conclusion: "success",
  });
  const baseFetch = mock.fetchImpl;
  let delayCompletedPatch = true;
  let completedApplied = false;
  let compensationFailures = 4;
  let releaseCompletedPatch;
  let announceCompletedPatch;
  const completedPatchStarted = new Promise((resolve) => { announceCompletedPatch = resolve; });
  const completedPatchGate = new Promise((resolve) => { releaseCompletedPatch = resolve; });
  const delayedMock = {
    ...mock,
    fetchImpl: async (input, init = {}) => {
      const url = new URL(input);
      const body = init.body ? JSON.parse(init.body) : {};
      if (delayCompletedPatch && url.pathname === "/repos/romelhc95/studiamatch/check-runs/111" &&
          init.method === "PATCH" && body.status === "completed") {
        delayCompletedPatch = false;
        announceCompletedPatch();
        await completedPatchGate;
        const result = await baseFetch(input, init);
        completedApplied = true;
        return result;
      }
      if (completedApplied && compensationFailures > 0 &&
          url.pathname === "/repos/romelhc95/studiamatch/check-runs/111" &&
          init.method === "PATCH" && body.status === "in_progress") {
        compensationFailures -= 1;
        return jsonResponse({ message: "synthetic recovery failure" }, 500);
      }
      return baseFetch(input, init);
    },
  };
  const { env, coordinator } = workerEnv(delayedMock);
  const processingDelivery = crypto.randomUUID();
  coordinator.insertEvent({ delivery: processingDelivery, prNumber: 501, headSha: HEAD }, NOW);

  const processingAlarm = coordinator.alarm();
  await completedPatchStarted;
  const revocation = prPayload();
  revocation.action = "submitted";
  revocation.review = approval({ state: "CHANGES_REQUESTED", id: 2, submittedAt: "2026-10-19T14:30:00Z" });
  currentReviews.splice(0, currentReviews.length, revocation.review);
  const incomingDelivery = crypto.randomUUID();
  let webhookResolved = false;
  const webhook = handleRequest(
    await signedWebhook(revocation, { event: "pull_request_review", delivery: incomingDelivery }),
    env,
  ).then((result) => {
    webhookResolved = true;
    return result;
  });
  for (let attempt = 0; attempt < 50 && !coordinator.getEventByDelivery(incomingDelivery); attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).status, "pending");
  assert.equal(webhookResolved, false, "the webhook must wait for the older check writer before ACK");

  releaseCompletedPatch();
  await processingAlarm;
  const result = await webhook;
  assert.equal(result.status, 202);
  assert.equal(compensationFailures, 0, "the older publisher's bounded recovery failed before the precheck write");
  assert.equal(mock.checkPosts[0].status, "in_progress", "no stale success remains after the webhook receives 202");
  assert.equal(mock.checkPosts[0].conclusion, undefined);
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).status, "pending");
});

test("redelivery invalidates the API-confirmed current SHA after a full-queue precheck failure", async () => {
  const mock = githubMock({ headSha: NEXT_HEAD, precheckPatchFailures: 4 });
  mock.checkPosts.push({
    name: "Protected Workflow Integrity",
    external_id: `pwi-v1-${REPOSITORY_ID}-501`,
    head_sha: NEXT_HEAD,
    status: "completed",
    conclusion: "success",
  });
  const { env, coordinator } = workerEnv(mock);
  let scheduledAlarm = null;
  const oldDeliveries = [];
  coordinator.ctx = {
    storage: {
      async setAlarm(timestamp) { scheduledAlarm = timestamp; },
      async deleteAlarm() { scheduledAlarm = null; },
    },
  };
  for (let index = 0; index < 8; index += 1) {
    const delivery = crypto.randomUUID();
    oldDeliveries.push(delivery);
    coordinator.insertEvent({ delivery, prNumber: 501, headSha: HEAD }, NOW + index);
  }

  const incomingDelivery = crypto.randomUUID();
  const result = await handleRequest(
    await signedWebhook(prPayload(), { delivery: incomingDelivery }),
    env,
  );
  assert.equal(result.status, 503);
  assert.equal(mock.checkPosts[0].status, "completed");
  assert.equal(mock.checkPosts[0].conclusion, "success");
  assert.equal(coordinator.pendingEvents, 8, "capacity remains capped");
  assert.equal(coordinator.getEventByDelivery(oldDeliveries[0]).status, "failed", "one stale pending row is retained as terminal overflow");
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).headSha, NEXT_HEAD, "the current SHA is persisted in the released slot");
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).status, "pending");
  assert.equal(scheduledAlarm, NOW + 50, "the current SHA is scheduled after the precheck failure");

  const redelivered = await handleRequest(
    await signedWebhook(prPayload(), { delivery: incomingDelivery }),
    env,
  );
  assert.equal(redelivered.status, 202);
  assert.deepEqual(await redelivered.json(), { status: "already_queued" });
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).headSha, NEXT_HEAD);
  assert.equal(mock.checkPosts[0].head_sha, NEXT_HEAD);
  assert.equal(mock.checkPosts[0].status, "in_progress", "idempotent redelivery invalidates the stored API-confirmed SHA before ACK");
  assert.equal(mock.checkPosts[0].conclusion, undefined);

  await coordinator.alarm();
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).status, "done");
  assert.equal(mock.checkPosts[0].status, "completed");
  assert.equal(mock.checkPosts[0].conclusion, "failure", "the current SHA receives a fresh evaluated result after the precheck recovers");
});

test("persists the current SHA when an out-of-order webhook arrives at capacity", async () => {
  const mock = githubMock({ headSha: NEXT_HEAD });
  mock.checkPosts.push({
    name: "Protected Workflow Integrity",
    external_id: `pwi-v1-${REPOSITORY_ID}-501`,
    head_sha: NEXT_HEAD,
    status: "completed",
    conclusion: "success",
  });
  const { env, coordinator } = workerEnv(mock);
  const currentDelivery = crypto.randomUUID();
  coordinator.insertEvent({ delivery: currentDelivery, prNumber: 501, headSha: NEXT_HEAD }, NOW - 1);
  const staleDeliveries = [];
  for (let index = 0; index < 7; index += 1) {
    const delivery = crypto.randomUUID();
    staleDeliveries.push(delivery);
    coordinator.insertEvent({ delivery, prNumber: 501, headSha: HEAD }, NOW - index - 2);
  }

  const incomingDelivery = crypto.randomUUID();
  const result = await handleRequest(
    await signedWebhook(prPayload(), { delivery: incomingDelivery }),
    env,
  );
  assert.equal(result.status, 202);
  assert.equal(mock.checkPosts[0].status, "in_progress", "capacity handling invalidates the API-confirmed current SHA");
  assert.equal(coordinator.pendingEvents, 8);
  assert.equal(coordinator.getEventByDelivery(currentDelivery).status, "pending");
  assert.equal(coordinator.getEventByDelivery(staleDeliveries[0]).status, "failed");
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).headSha, NEXT_HEAD);
  assert.equal(coordinator.getEventByDelivery(incomingDelivery).status, "pending");
});

test("a stale-SHA webhook cannot supersede queued work for the current SHA below capacity", async () => {
  const mock = githubMock({ headSha: NEXT_HEAD, reviews: [approval({ commitId: NEXT_HEAD })] });
  mock.checkPosts.push({
    name: "Protected Workflow Integrity",
    external_id: `pwi-v1-${REPOSITORY_ID}-501`,
    head_sha: NEXT_HEAD,
    status: "completed",
    conclusion: "success",
  });
  const { env, coordinator } = workerEnv(mock);
  const currentDelivery = crypto.randomUUID();
  coordinator.insertEvent({ delivery: currentDelivery, prNumber: 501, headSha: NEXT_HEAD }, NOW - 2);

  const staleDelivery = crypto.randomUUID();
  const staleResponse = await handleRequest(
    await signedWebhook(prPayload({ headSha: HEAD }), { delivery: staleDelivery }),
    env,
  );
  assert.equal(staleResponse.status, 202);

  await coordinator.alarm();
  assert.equal(coordinator.getEventByDelivery(currentDelivery).status, "done");
  assert.equal(mock.checkPosts[0].status, "completed");
  assert.equal(mock.checkPosts[0].conclusion, "success", "an older SHA must not strand the current SHA check");

  await coordinator.alarm();
  assert.equal(coordinator.getEventByDelivery(staleDelivery).status, "done");
  assert.equal(mock.checkPosts[0].head_sha, NEXT_HEAD);
  assert.equal(mock.checkPosts[0].conclusion, "success");
});

test("same-delivery redelivery at capacity confirms and reopens the current SHA", async () => {
  const mock = githubMock({ headSha: NEXT_HEAD, reviews: [approval({ commitId: NEXT_HEAD })] });
  mock.checkPosts.push({
    name: "Protected Workflow Integrity",
    external_id: `pwi-v1-${REPOSITORY_ID}-501`,
    head_sha: NEXT_HEAD,
    status: "completed",
    conclusion: "success",
  });
  const { env, coordinator } = workerEnv(mock);
  let scheduledAlarm = null;
  coordinator.ctx = {
    storage: {
      async setAlarm(timestamp) { scheduledAlarm = timestamp; },
      async deleteAlarm() { scheduledAlarm = null; },
    },
  };
  const activeDelivery = crypto.randomUUID();
  coordinator.insertEvent({ delivery: activeDelivery, prNumber: 501, headSha: HEAD }, NOW - 2);
  coordinator.updateEvent(activeDelivery, {
    status: "processing",
    attempts: 1,
    nextAttemptAt: NOW + 600_000,
    updatedAt: NOW - 1,
  });
  const previousSequence = coordinator.getEventByDelivery(activeDelivery).sequence;
  const otherDeliveries = [];
  for (let index = 0; index < 7; index += 1) {
    const delivery = crypto.randomUUID();
    otherDeliveries.push(delivery);
    coordinator.insertEvent({ delivery, prNumber: 501, headSha: HEAD }, NOW + index);
  }

  const result = await handleRequest(
    await signedWebhook(prPayload({ headSha: HEAD }), { delivery: activeDelivery }),
    env,
  );
  assert.equal(result.status, 202);
  assert.equal(coordinator.pendingEvents, 8);
  assert.equal(coordinator.getEventByDelivery(activeDelivery).sequence > previousSequence, true);
  assert.equal(coordinator.getEventByDelivery(activeDelivery).headSha, NEXT_HEAD);
  assert.equal(coordinator.getEventByDelivery(activeDelivery).status, "pending");
  assert.equal(scheduledAlarm, NOW + 50);
  assert.equal(mock.checkPosts[0].head_sha, NEXT_HEAD);
  assert.equal(mock.checkPosts[0].status, "in_progress", "the current SHA success is invalidated before redelivery ACK");
  assert.equal(mock.checkPosts[0].conclusion, undefined);
  assert.equal(coordinator.getEventByDelivery(otherDeliveries[0]).status, "pending", "reusing an active delivery must not displace another event");
});

test("reuses a same-delivery row that completes while a full-queue redelivery checks the current head", async () => {
  const baseMock = githubMock();
  baseMock.checkPosts.push({
    name: "Protected Workflow Integrity",
    external_id: `pwi-v1-${REPOSITORY_ID}-501`,
    head_sha: HEAD,
    status: "completed",
    conclusion: "success",
  });
  let releaseCurrentHeadRead;
  let announceCurrentHeadRead;
  const currentHeadReadStarted = new Promise((resolve) => { announceCurrentHeadRead = resolve; });
  const currentHeadReadGate = new Promise((resolve) => { releaseCurrentHeadRead = resolve; });
  let pauseFirstPullRead = true;
  const mock = {
    ...baseMock,
    fetchImpl: async (input, init = {}) => {
      const url = new URL(input);
      if (pauseFirstPullRead && url.pathname === "/repos/romelhc95/studiamatch/pulls/501" && init.method === "GET") {
        pauseFirstPullRead = false;
        announceCurrentHeadRead();
        await currentHeadReadGate;
      }
      return baseMock.fetchImpl(input, init);
    },
  };
  const { env, coordinator } = workerEnv(mock);
  const delivery = crypto.randomUUID();
  coordinator.insertEvent({ delivery, prNumber: 501, headSha: HEAD }, NOW - 1);
  const originalSequence = coordinator.getEventByDelivery(delivery).sequence;
  for (let index = 0; index < 7; index += 1) {
    coordinator.insertEvent({ delivery: crypto.randomUUID(), prNumber: 501, headSha: NEXT_HEAD }, NOW + 10_000 + index);
  }

  const redelivery = handleRequest(await signedWebhook(prPayload(), { delivery }), env);
  await currentHeadReadStarted;

  await coordinator.alarm();
  assert.equal(coordinator.getEventByDelivery(delivery).status, "done", "the original event can finish during the GitHub head read");
  assert.equal(baseMock.checkPosts[0].status, "completed");
  assert.equal(baseMock.checkPosts[0].conclusion, "success");

  releaseCurrentHeadRead();
  const result = await redelivery;
  assert.equal(result.status, 202);
  assert.deepEqual(await result.json(), { status: "queued" });
  const requeued = coordinator.getEventByDelivery(delivery);
  assert.equal(requeued.status, "pending");
  assert.equal(requeued.headSha, HEAD);
  assert.ok(requeued.sequence > originalSequence, "the retained row receives a fresh sequence");
  assert.equal(coordinator.pendingEvents, 8);
  assert.equal(baseMock.checkPosts[0].status, "in_progress", "the completed success is invalidated before ACK");
  assert.equal(baseMock.checkPosts[0].conclusion, undefined);

  await coordinator.alarm();
  assert.equal(coordinator.getEventByDelivery(delivery).status, "done");
  assert.equal(baseMock.checkPosts[0].status, "completed");
});

test("requeues a failed delivery with a new sequence so it supersedes older work", async () => {
  const mock = githubMock();
  const { env, coordinator } = workerEnv(mock);
  const failedDelivery = crypto.randomUUID();
  const laterDelivery = crypto.randomUUID();
  coordinator.insertEvent({ delivery: failedDelivery, prNumber: 501, headSha: HEAD }, NOW - 2);
  coordinator.updateEvent(failedDelivery, {
    status: "failed",
    attempts: 3,
    nextAttemptAt: NOW - 1,
    updatedAt: NOW - 1,
  });
  coordinator.insertEvent({ delivery: laterDelivery, prNumber: 501, headSha: HEAD }, NOW - 1);
  const laterSequence = coordinator.getEventByDelivery(laterDelivery).sequence;

  const redelivery = await handleRequest(await signedWebhook(prPayload(), { delivery: failedDelivery }), env);
  assert.equal(redelivery.status, 202);
  assert.ok(coordinator.getEventByDelivery(failedDelivery).sequence > laterSequence);
  assert.equal(coordinator.getEventByDelivery(failedDelivery).status, "pending");
});

test("keeps a displaced processing event terminal when its delayed completion returns", () => {
  const { coordinator } = workerEnv(githubMock());
  const delivery = crypto.randomUUID();
  coordinator.insertEvent({ delivery, prNumber: 501, headSha: HEAD }, NOW - 1);
  const selected = { ...coordinator.getEventByDelivery(delivery) };
  coordinator.updateEvent(delivery, {
    status: "processing",
    attempts: 1,
    nextAttemptAt: NOW + 600_000,
    updatedAt: NOW,
  });
  coordinator.updateEvent(delivery, {
    status: "failed",
    attempts: 1,
    nextAttemptAt: NOW,
    updatedAt: NOW,
  });

  coordinator.completeProcessingEvent(selected, {
    status: "done",
    attempts: 1,
    nextAttemptAt: NOW,
    updatedAt: NOW,
  });
  assert.equal(coordinator.getEventByDelivery(delivery).status, "failed");
});

test("keeps the required check pending when revocation arrives during check creation", async () => {
  const currentReviews = [approval()];
  const mock = githubMock({ reviews: currentReviews });
  let releaseCreate;
  let announceCreate;
  const createStarted = new Promise((resolve) => { announceCreate = resolve; });
  const createGate = new Promise((resolve) => { releaseCreate = resolve; });
  const delayedFetch = async (input, init) => {
    const url = new URL(input);
    if (url.pathname === "/repos/romelhc95/studiamatch/check-runs" && init.method === "POST") {
      announceCreate();
      await createGate;
    }
    return mock.fetchImpl(input, init);
  };
  const delayedMock = { ...mock, fetchImpl: delayedFetch };
  const { env, coordinator } = workerEnv(delayedMock);
  const firstResponse = await handleRequest(await signedWebhook(prPayload()), env);
  assert.equal(firstResponse.status, 202);
  const firstAlarm = coordinator.alarm();
  await createStarted;

  const revocation = prPayload();
  revocation.action = "submitted";
  revocation.review = approval({ state: "CHANGES_REQUESTED", id: 2 });
  currentReviews.splice(0, currentReviews.length, revocation.review);
  const revocationDelivery = crypto.randomUUID();
  const secondResponse = await handleRequest(
    await signedWebhook(revocation, { event: "pull_request_review", delivery: revocationDelivery }),
    env,
  );
  assert.equal(secondResponse.status, 503, "pre-ACK invalidation fails closed while the check is being created");
  releaseCreate();
  await firstAlarm;

  assert.equal(mock.checkPosts[0].status, "in_progress", "a superseded check must not remain successful after creation returns");
  assert.equal(mock.checkPosts[0].conclusion, undefined);
  const redelivery = await handleRequest(
    await signedWebhook(revocation, { event: "pull_request_review", delivery: revocationDelivery }),
    env,
  );
  assert.equal(redelivery.status, 202);
  await coordinator.alarm();
  assert.equal(mock.checkPosts[0].status, "completed");
  assert.equal(mock.checkPosts[0].conclusion, "failure");
});

test("reopens the same check when revocation arrives during final check update", async () => {
  const currentReviews = [approval()];
  const mock = githubMock({ reviews: currentReviews });
  let delayCompletedPatch = false;
  let releaseCompletedPatch;
  let announceCompletedPatch;
  const completedPatchStarted = new Promise((resolve) => { announceCompletedPatch = resolve; });
  const completedPatchGate = new Promise((resolve) => { releaseCompletedPatch = resolve; });
  const delayedFetch = async (input, init) => {
    const url = new URL(input);
    const body = init.body ? JSON.parse(init.body) : {};
    if (delayCompletedPatch && url.pathname === "/repos/romelhc95/studiamatch/check-runs/111" &&
        init.method === "PATCH" && body.status === "completed") {
      delayCompletedPatch = false;
      announceCompletedPatch();
      await completedPatchGate;
    }
    return mock.fetchImpl(input, init);
  };
  const delayedMock = { ...mock, fetchImpl: delayedFetch };
  const { env, coordinator } = workerEnv(delayedMock);
  const firstResponse = await handleRequest(await signedWebhook(prPayload()), env);
  assert.equal(firstResponse.status, 202);
  await coordinator.alarm();
  assert.equal(mock.checkPosts[0].conclusion, "success");

  const renewedApproval = prPayload();
  renewedApproval.action = "submitted";
  renewedApproval.review = approval({ id: 2, submittedAt: "2026-10-19T14:30:00Z" });
  currentReviews.splice(0, currentReviews.length, renewedApproval.review);
  const secondResponse = await handleRequest(
    await signedWebhook(renewedApproval, { event: "pull_request_review" }),
    env,
  );
  assert.equal(secondResponse.status, 202);
  delayCompletedPatch = true;
  const secondAlarm = coordinator.alarm();
  await completedPatchStarted;

  const revocation = prPayload();
  revocation.action = "submitted";
  revocation.review = approval({ state: "CHANGES_REQUESTED", id: 3, submittedAt: "2026-10-19T14:45:00Z" });
  currentReviews.splice(0, currentReviews.length, revocation.review);
  const revocationDelivery = crypto.randomUUID();
  const thirdResponse = await handleRequest(
    await signedWebhook(revocation, { event: "pull_request_review", delivery: revocationDelivery }),
    env,
  );
  assert.equal(thirdResponse.status, 503, "pre-ACK invalidation times out while a prior check update is unresolved");
  releaseCompletedPatch();
  await secondAlarm;

  assert.equal(mock.checkPosts[0].status, "in_progress", "a superseding review must reopen the completed check run");
  assert.equal(mock.checkPosts[0].conclusion, undefined);
  const redelivery = await handleRequest(
    await signedWebhook(revocation, { event: "pull_request_review", delivery: revocationDelivery }),
    env,
  );
  assert.equal(redelivery.status, 202);
  await coordinator.alarm();
  assert.equal(mock.checkPosts[0].status, "completed");
  assert.equal(mock.checkPosts[0].conclusion, "failure");
});

test("fails closed and stops after three retries for GitHub 5xx", async () => {
  const request = await signedWebhook(prPayload());
  const mock = githubMock({ apiFailure: "files_500_until_exhausted" });
  const { env, coordinator } = workerEnv(mock);
  const result = await handleRequest(request, env);
  assert.equal(result.status, 202);
  await coordinator.alarm();
  assert.equal(mock.failedFileCalls, 4);
  assert.equal(mock.checkPosts[0].conclusion, "failure");
});

test("bounds alarm retries and allows a failed delivery to be explicitly redelivered", async () => {
  const mock = githubMock();
  let failTokens = false;
  const failingMock = {
    ...mock,
    fetchImpl: async (input, init) => {
      if (failTokens && new URL(input).pathname === `/app/installations/${INSTALLATION_ID}/access_tokens`) {
        return jsonResponse({ message: "synthetic unavailable" }, 503);
      }
      return mock.fetchImpl(input, init);
    },
  };
  const { env, coordinator, advance } = workerEnv(failingMock);
  const delivery = crypto.randomUUID();
  const request = await signedWebhook(prPayload(), { delivery });
  const queued = await handleRequest(request, env);
  assert.equal(queued.status, 202);

  failTokens = true;
  await coordinator.alarm();
  assert.equal(coordinator.getEventByDelivery(delivery).attempts, 1);
  advance(1_000);
  await coordinator.alarm();
  assert.equal(coordinator.getEventByDelivery(delivery).attempts, 2);
  advance(4_000);
  await coordinator.alarm();
  assert.equal(coordinator.getEventByDelivery(delivery).status, "failed");
  assert.equal(coordinator.getEventByDelivery(delivery).attempts, 3);
  assert.equal(coordinator.pendingEvents, 0);

  failTokens = false;
  const redelivery = await signedWebhook(prPayload(), { delivery });
  const requeued = await handleRequest(redelivery, env);
  assert.equal(requeued.status, 202);
  assert.equal(coordinator.getEventByDelivery(delivery).status, "pending");
  assert.equal(coordinator.getEventByDelivery(delivery).attempts, 0);
});

test("failed-row redelivery below queue capacity refreshes and invalidates the API-confirmed current SHA", async () => {
  const mock = githubMock({ headSha: NEXT_HEAD });
  mock.checkPosts.push({
    name: "Protected Workflow Integrity",
    external_id: `pwi-v1-${REPOSITORY_ID}-501`,
    head_sha: NEXT_HEAD,
    status: "completed",
    conclusion: "success",
  });
  const { env, coordinator } = workerEnv(mock);
  const delivery = crypto.randomUUID();
  coordinator.insertEvent({ delivery, prNumber: 501, headSha: NEXT_HEAD }, NOW);
  coordinator.updateEvent(delivery, {
    status: "failed",
    attempts: 3,
    nextAttemptAt: NOW,
    updatedAt: NOW,
  });

  const redelivered = await handleRequest(
    await signedWebhook(prPayload({ headSha: HEAD }), { delivery }),
    env,
  );

  assert.equal(redelivered.status, 202);
  assert.equal(coordinator.getEventByDelivery(delivery).headSha, NEXT_HEAD);
  assert.equal(coordinator.getEventByDelivery(delivery).status, "pending");
  assert.equal(
    mock.requests.some(({ url, init }) =>
      url.pathname === "/repos/romelhc95/studiamatch/pulls/501" && init.method === "GET"
    ),
    true,
    "failed-row redelivery must read the target PR's current metadata before ACK",
  );
  assert.equal(mock.checkPosts[0].head_sha, NEXT_HEAD);
  assert.equal(mock.checkPosts[0].status, "in_progress");
  assert.equal(mock.checkPosts[0].conclusion, undefined);
});

test("does not publish a check for an event whose SHA is no longer current", async () => {
  const request = await signedWebhook(prPayload());
  const mock = githubMock({ headSha: "b".repeat(40) });
  const { env, coordinator } = workerEnv(mock);
  const result = await handleRequest(request, env);
  assert.equal(result.status, 202);
  await coordinator.alarm();
  assert.equal(mock.checkPosts.length, 0);
});

test("ignores repository events outside the fixed repository allowlist", async () => {
  const request = await signedWebhook(prPayload({ repoId: 101, repoName: "someone/other" }));
  const mock = githubMock();
  const result = await handleRequest(request, workerEnv(mock).env);
  assert.equal(result.status, 202);
  assert.equal(mock.requests.length, 0);
});

test("ignores pull requests targeting a branch outside the approved scope", async () => {
  const payload = prPayload();
  payload.pull_request.base.ref = "certificacion";
  const request = await signedWebhook(payload);
  const mock = githubMock();
  const result = await handleRequest(request, workerEnv(mock).env);
  assert.equal(result.status, 202);
  assert.equal(mock.requests.length, 0);
});

test("requests retry only for 429 and 5xx, never 4xx", async () => {
  const calls = [];
  const api = new GitHubApi({
    token: "synthetic",
    now: () => NOW,
    deadline: NOW + 20_000,
    sleep: async () => {},
    fetchImpl: async (input) => {
      calls.push(new URL(input).pathname);
      return jsonResponse({ message: "synthetic" }, 403);
    },
  });
  await assert.rejects(api.request("GET", "/repos/romelhc95/studiamatch/pulls/501"), /github_http_403/);
  assert.equal(calls.length, 1);
});

test("creates an App JWT with a PKCS8 private key without exposing claims", async () => {
  const jwt = await createAppJwt({ appId: APP_ID, privateKeyPem: PRIVATE_KEY_PEM, now: NOW });
  assert.equal(jwt.split(".").length, 3);
  const claims = JSON.parse(Buffer.from(jwt.split(".")[1], "base64url").toString("utf8"));
  assert.equal(claims.iss, APP_ID);
  assert.equal(claims.exp - claims.iat, 540);
  assert.equal(await verifyJwt(jwt, APP_KEY_PAIR.publicKey), true);
});

test("imports GitHub's traditional RSA private-key PEM format", async () => {
  const pkcs8Text = PRIVATE_KEY_PEM.replace(/-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\s/g, "");
  const pkcs8Binary = atob(pkcs8Text);
  const pkcs8 = Uint8Array.from(pkcs8Binary, (character) => character.charCodeAt(0));
  const outer = derValue(pkcs8, 0, 0x30);
  const version = derValue(pkcs8, outer.start, 0x02);
  const algorithm = derValue(pkcs8, version.end, 0x30);
  const privateKey = derValue(pkcs8, algorithm.end, 0x04).bytes;
  let binary = "";
  for (const byte of privateKey) binary += String.fromCharCode(byte);
  const encoded = btoa(binary).match(/.{1,64}/g).join("\n");
  const pkcs1Pem = `-----BEGIN RSA PRIVATE KEY-----\n${encoded}\n-----END RSA PRIVATE KEY-----`;
  const jwt = await createAppJwt({ appId: APP_ID, privateKeyPem: pkcs1Pem, now: NOW });
  assert.equal(jwt.split(".").length, 3);
  assert.equal(await verifyJwt(jwt, APP_KEY_PAIR.publicKey), true);
});

test("stops at the declared pagination boundary instead of approving a partial list", async () => {
  let calls = 0;
  const api = new GitHubApi({
    token: "synthetic",
    now: () => NOW,
    deadline: NOW + 20_000,
    sleep: async () => {},
    fetchImpl: async () => {
      calls += 1;
      return jsonResponse(Array.from({ length: 100 }, (_, index) => ({ filename: `file-${index}.txt` })));
    },
  });
  await assert.rejects(api.listAll("/repos/romelhc95/studiamatch/pulls", 1, 10_000, "test"), /test_pagination_truncated/);
  assert.equal(calls, 1);
});

test("fails closed when check-run pagination is truncated after a matching App run", async () => {
  let calls = 0;
  const api = new GitHubApi({
    token: "synthetic",
    now: () => NOW,
    deadline: NOW + 20_000,
    sleep: async () => {},
    fetchImpl: async () => {
      calls += 1;
      const checkRuns = Array.from({ length: 100 }, (_, index) => ({
        id: index + 1,
        head_sha: HEAD,
        app: { id: Number(APP_ID) },
        external_id: index === 0 ? `pwi-v1-${REPOSITORY_ID}-501` : `other-${index}`,
      }));
      return jsonResponse({ check_runs: checkRuns });
    },
  });
  await assert.rejects(
    api.findMatchingCheckRuns(HEAD, APP_ID, `pwi-v1-${REPOSITORY_ID}-501`),
    /check_runs_pagination_truncated/,
  );
  assert.equal(calls, 5);
});

async function verifyJwt(jwt, publicKey) {
  const [header, claims, signature] = jwt.split(".");
  const base64 = signature.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64 + "=".repeat((4 - base64.length % 4) % 4);
  const bytes = Uint8Array.from(atob(padded), (character) => character.charCodeAt(0));
  return crypto.subtle.verify("RSASSA-PKCS1-v1_5", publicKey, bytes, encoder.encode(`${header}.${claims}`));
}
