import { GitHubApi } from "./github.mjs";
import {
  CHECK_NAME,
  REPOSITORY_ID,
  REPOSITORY_FULL_NAME,
  TARGET_BRANCH,
  checkRunExternalId,
  classifyProtectedFiles,
  hasTrustedCurrentApproval,
  pullRequestContext,
} from "./policy.mjs";

const MAX_WEBHOOK_BYTES = 128 * 1024;
const MAX_INTERNAL_EVENT_BYTES = 4 * 1024;
const MAX_INVOCATION_MS = 25_000;
const MAX_WEBHOOK_PRECHECK_MS = 7_500;
const MAX_PENDING_EVENTS = 8;
const MAX_TERMINAL_EVENTS = 100;
const MAX_EVENT_ATTEMPTS = 3;
const PROCESSING_LEASE_MS = 10 * 60 * 1_000;
const EVENT_RETRY_DELAYS_MS = [1_000, 4_000];
const PR_ACTIONS = new Set(["opened", "edited", "synchronize", "reopened", "ready_for_review"]);
const REVIEW_ACTIONS = new Set(["submitted", "dismissed"]);

function fail(code) {
  const error = new Error(code);
  error.code = code;
  return error;
}

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

async function readBoundedBody(request, limit) {
  if (!request.body) throw fail("empty_webhook_body");
  const reader = request.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > limit) {
        await reader.cancel();
        throw fail("webhook_body_too_large");
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const body = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body;
}

function hex(bytes) {
  return [...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function timingSafeEqual(left, right) {
  if (left.length !== right.length) return false;
  let mismatch = 0;
  for (let index = 0; index < left.length; index += 1) mismatch |= left.charCodeAt(index) ^ right.charCodeAt(index);
  return mismatch === 0;
}

async function verifyWebhookSignature(body, signature, secret) {
  if (typeof secret !== "string" || secret.length < 32 || !/^sha256=[0-9a-f]{64}$/i.test(signature ?? "")) {
    return false;
  }
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const digest = await crypto.subtle.sign("HMAC", key, body);
  return timingSafeEqual(signature.slice(7).toLowerCase(), hex(new Uint8Array(digest)));
}

function parseBody(body) {
  try {
    const value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(body));
    if (!isRecord(value)) throw new Error("not an object");
    return value;
  } catch {
    throw fail("webhook_json_invalid");
  }
}

function requiredConfig(env) {
  if (!env || !/^\d{1,20}$/.test(String(env.GITHUB_APP_ID ?? "")) ||
      !/^\d{1,20}$/.test(String(env.GITHUB_INSTALLATION_ID ?? "")) ||
      typeof env.GITHUB_APP_PRIVATE_KEY !== "string" ||
      typeof env.GITHUB_WEBHOOK_SECRET !== "string") {
    throw fail("worker_configuration_incomplete");
  }
  return {
    appId: String(env.GITHUB_APP_ID),
    installationId: String(env.GITHUB_INSTALLATION_ID),
    privateKeyPem: env.GITHUB_APP_PRIVATE_KEY,
    webhookSecret: env.GITHUB_WEBHOOK_SECRET,
  };
}

function supportedPrEvent(eventName, action, payload, appId) {
  if (eventName === "pull_request" && PR_ACTIONS.has(action)) {
    if (isRecord(payload.pull_request?.base) && payload.pull_request.base.ref !== TARGET_BRANCH) return null;
    const context = pullRequestContext(payload);
    return { context, expectedHeadSha: context.headSha };
  }
  if (eventName === "pull_request_review" && REVIEW_ACTIONS.has(action)) {
    if (isRecord(payload.pull_request?.base) && payload.pull_request.base.ref !== TARGET_BRANCH) return null;
    const context = pullRequestContext(payload);
    return { context, expectedHeadSha: context.headSha };
  }
  if (eventName === "check_run" && action === "rerequested") {
    const checkRun = payload.check_run;
    if (!isRecord(checkRun) || checkRun.name !== CHECK_NAME || checkRun.app?.id !== Number(appId) ||
        typeof checkRun.head_sha !== "string" || !/^[0-9a-f]{40}$/i.test(checkRun.head_sha) ||
        !Array.isArray(checkRun.pull_requests)) {
      throw fail("check_rerequest_malformed");
    }
    const matches = checkRun.pull_requests.filter((pr) =>
      isRecord(pr) && isRecord(pr.base) && pr.base.ref === TARGET_BRANCH &&
      isRecord(pr.head) && pr.head.sha?.toLowerCase() === checkRun.head_sha.toLowerCase() &&
      Number.isSafeInteger(pr.number) && pr.number > 0,
    );
    if (matches.length !== 1) return null;
    if (checkRun.external_id !== checkRunExternalId(matches[0].number)) return null;
    return {
      context: { number: matches[0].number, headSha: checkRun.head_sha.toLowerCase() },
      expectedHeadSha: checkRun.head_sha.toLowerCase(),
    };
  }
  return null;
}

function validateApiPullRequest(pr, number, expectedSha) {
  if (!isRecord(pr) || pr.number !== number || !isRecord(pr.base) || pr.base.ref !== TARGET_BRANCH ||
      !isRecord(pr.head) || typeof pr.head.sha !== "string" ||
      pr.head.sha.toLowerCase() !== expectedSha.toLowerCase() ||
      !isRecord(pr.user) || typeof pr.user.login !== "string" || !pr.user.login) {
    throw fail("current_pr_does_not_match_webhook");
  }
  return { number, headSha: pr.head.sha.toLowerCase(), author: pr.user.login };
}

async function evaluate(api, context, current) {
  const [files, reviews] = await Promise.all([
    api.listPullRequestFiles(context.number),
    api.listPullRequestReviews(context.number),
  ]);
  const protectedPaths = classifyProtectedFiles(files);
  if (protectedPaths.length === 0) {
    return { conclusion: "success", summary: "No protected workflow or security-control paths changed." };
  }
  if (hasTrustedCurrentApproval(reviews, { headSha: current.headSha, prAuthor: current.author })) {
    return { conclusion: "success", summary: "Protected paths changed and a trusted, non-author approval matches the current head SHA." };
  }
  return { conclusion: "failure", summary: "Protected paths changed; a trusted, non-author approval for the current head SHA is required." };
}

function response(status, body) {
  return Response.json(body, {
    status,
    headers: { "Cache-Control": "no-store", "Content-Type": "application/json; charset=utf-8" },
  });
}

function withCheckWriteLock(dependencies, operation, deadline = Number.POSITIVE_INFINITY) {
  const lock = dependencies.withCheckWriteLock;
  return typeof lock === "function" ? lock(operation, deadline) : operation();
}

async function processEventMessage(message, env, dependencies) {
  const now = dependencies.now ?? Date.now;
  const fetchImpl = dependencies.fetchImpl ?? fetch;
  const sleep = dependencies.sleep ?? ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
  const config = requiredConfig(env);
  if (!isRecord(message) || typeof message.delivery !== "string" || !/^[0-9a-f-]{36}$/i.test(message.delivery) ||
      message.repositoryId !== REPOSITORY_ID || message.repositoryFullName !== REPOSITORY_FULL_NAME ||
      Number(message.installationId) !== Number(config.installationId) ||
      !Number.isSafeInteger(message.prNumber) || message.prNumber < 1 ||
      typeof message.headSha !== "string" || !/^[0-9a-f]{40}$/i.test(message.headSha)) {
    return response(400, { error: "invalid_internal_event" });
  }
  const context = { number: message.prNumber, headSha: message.headSha.toLowerCase() };

  const deadline = now() + MAX_INVOCATION_MS;
  const bootstrapApi = new GitHubApi({ fetchImpl, token: "uninitialized", deadline, now, sleep });
  let token;
  try {
    token = await bootstrapApi.createInstallationToken({
      appId: config.appId,
      privateKeyPem: config.privateKeyPem,
      installationId: config.installationId,
      now: now(),
    });
  } catch {
    return response(503, { error: "github_authentication_unavailable" });
  }
  const api = new GitHubApi({ fetchImpl, token, deadline, now, sleep });

  try {
    const current = await withCheckWriteLock(dependencies, () => api.beginCheckVerification({
      headSha: context.headSha,
      appId: config.appId,
      prNumber: context.number,
      hasSupersedingEvent: dependencies.hasSupersedingEvent,
    }), deadline);
    if (!current) return response(202, { status: "superseded" });
  } catch {
    return response(503, { error: "check_publication_unavailable" });
  }

  let prRecord;
  let current;
  try {
    prRecord = await api.getPullRequest(context.number);
    if (isRecord(prRecord) && prRecord.number === context.number &&
        (prRecord.base?.ref !== TARGET_BRANCH || prRecord.head?.sha?.toLowerCase() !== context.headSha)) {
      return response(202, { status: "stale" });
    }
    current = validateApiPullRequest(prRecord, context.number, context.headSha);
  } catch {
    return response(503, { error: "github_state_unavailable" });
  }

  let result;
  try {
    result = await evaluate(api, context, current);
  } catch (error) {
    result = {
      conclusion: "failure",
      summary: "PWI could not verify the current pull request using the GitHub API; the control failed closed.",
      errorCode: /^[a-z0-9_]+$/.test(error?.code ?? "") ? error.code : "verification_failed",
    };
  }

  try {
    const latest = await api.getPullRequest(context.number);
    if (isRecord(latest) && latest.number === context.number &&
        (latest.base?.ref !== TARGET_BRANCH || latest.head?.sha?.toLowerCase() !== context.headSha)) {
      return response(202, { status: "stale" });
    }
    validateApiPullRequest(latest, context.number, context.headSha);
    if (dependencies.hasSupersedingEvent?.()) {
      return response(202, { status: "superseded" });
    }
    const published = await withCheckWriteLock(dependencies, () => api.publishCheck({
      headSha: context.headSha,
      appId: config.appId,
      prNumber: context.number,
      conclusion: result.conclusion,
      summary: result.summary,
      hasSupersedingEvent: dependencies.hasSupersedingEvent,
    }), deadline);
    if (published === false) return response(202, { status: "superseded" });
  } catch {
    return response(503, { error: "check_publication_unavailable" });
  }

  return response(200, {
    status: "recorded",
    check: CHECK_NAME,
    conclusion: result.conclusion,
    ...(result.errorCode ? { errorCode: result.errorCode } : {}),
  });
}

async function reopenCheckForWebhook(message, env, dependencies) {
  const now = dependencies.now ?? Date.now;
  const fetchImpl = dependencies.fetchImpl ?? fetch;
  const sleep = dependencies.sleep ?? ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
  const config = requiredConfig(env);
  const deadline = now() + MAX_WEBHOOK_PRECHECK_MS;
  const bootstrapApi = new GitHubApi({ fetchImpl, token: "uninitialized", deadline, now, sleep });
  const token = await bootstrapApi.createInstallationToken({
    appId: config.appId,
    privateKeyPem: config.privateKeyPem,
    installationId: config.installationId,
    now: now(),
  });
  const api = new GitHubApi({ fetchImpl, token, deadline, now, sleep });
  await withCheckWriteLock(dependencies, () => api.beginCheckVerification({
    headSha: message.headSha,
    appId: config.appId,
    prNumber: message.prNumber,
  }), deadline);
}

async function reopenCurrentCheckForFullQueue(message, env, dependencies, onCurrentHead) {
  const now = dependencies.now ?? Date.now;
  const fetchImpl = dependencies.fetchImpl ?? fetch;
  const sleep = dependencies.sleep ?? ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
  const config = requiredConfig(env);
  const deadline = now() + MAX_WEBHOOK_PRECHECK_MS;
  const bootstrapApi = new GitHubApi({ fetchImpl, token: "uninitialized", deadline, now, sleep });
  const token = await bootstrapApi.createInstallationToken({
    appId: config.appId,
    privateKeyPem: config.privateKeyPem,
    installationId: config.installationId,
    now: now(),
  });
  const api = new GitHubApi({ fetchImpl, token, deadline, now, sleep });
  const prRecord = await api.getPullRequest(message.prNumber);
  if (isRecord(prRecord) && prRecord.number === message.prNumber && isRecord(prRecord.base) &&
      typeof prRecord.base.ref === "string" && prRecord.base.ref !== TARGET_BRANCH) {
    return { outOfScope: true };
  }
  if (!isRecord(prRecord?.head) || typeof prRecord.head.sha !== "string" ||
      !/^[0-9a-f]{40}$/i.test(prRecord.head.sha)) {
    throw fail("current_pr_head_invalid");
  }
  const current = validateApiPullRequest(prRecord, message.prNumber, prRecord.head.sha);
  const queueState = onCurrentHead(current.headSha);
  await withCheckWriteLock(dependencies, () => api.beginCheckVerification({
    headSha: current.headSha,
    appId: config.appId,
    prNumber: current.number,
  }), deadline);
  return { currentHeadSha: current.headSha, queueState };
}

export class PwiCoordinator {
  constructor(ctx, env, dependencies = {}) {
    this.ctx = ctx;
    this.env = env;
    this.dependencies = dependencies;
    this.sql = ctx?.storage?.sql ?? null;
    this.memoryEvents = [];
    this.nextMemorySequence = 1;
    this.alarmInProgress = false;
    this.checkWriteTail = Promise.resolve();
    this.now = dependencies.now ?? Date.now;
    this.ready = this.sql && typeof ctx?.blockConcurrencyWhile === "function"
      ? ctx.blockConcurrencyWhile(() => {
        this.sql.exec(`
          CREATE TABLE IF NOT EXISTS pwi_event_queue (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            delivery TEXT NOT NULL UNIQUE,
            pr_number INTEGER NOT NULL,
            head_sha TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'done', 'failed')),
            attempts INTEGER NOT NULL DEFAULT 0,
            next_attempt_at INTEGER NOT NULL DEFAULT 0,
            received_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
          );
          CREATE INDEX IF NOT EXISTS pwi_event_queue_due
            ON pwi_event_queue(status, next_attempt_at, sequence);
        `);
      })
      : Promise.resolve();
  }

  get pendingEvents() {
    if (this.sql) {
      return this.sql.exec(
        "SELECT COUNT(*) AS count FROM pwi_event_queue WHERE status IN ('pending', 'processing')",
      ).one().count;
    }
    return this.memoryEvents.filter((event) => event.status === "pending" || event.status === "processing").length;
  }

  withCheckWriteLock(operation, deadline = Number.POSITIVE_INFINITY) {
    let expired = false;
    let timeoutId;
    const previous = this.checkWriteTail;
    const queued = previous.then(async () => {
      if (expired || this.now() >= deadline) throw fail("check_write_deadline_exceeded");
      return operation();
    }, async () => {
      if (expired || this.now() >= deadline) throw fail("check_write_deadline_exceeded");
      return operation();
    });
    this.checkWriteTail = queued.then(() => undefined, () => undefined);
    if (!Number.isFinite(deadline)) return queued;

    const remaining = Math.max(0, deadline - this.now());
    const timeout = new Promise((_, reject) => {
      timeoutId = setTimeout(() => {
        expired = true;
        reject(fail("check_write_deadline_exceeded"));
      }, remaining);
    });
    return Promise.race([queued, timeout]).finally(() => clearTimeout(timeoutId));
  }

  hasSupersedingEvent(delivery, sequence = undefined, headSha = undefined) {
    const current = this.memoryEvents.find((event) => event.delivery === delivery);
    const normalizedSha = typeof headSha === "string" ? headSha.toLowerCase() : current?.headSha?.toLowerCase();
    if (typeof normalizedSha !== "string" || !/^[0-9a-f]{40}$/.test(normalizedSha)) return false;
    if (this.sql) {
      const baselineSequence = Number.isSafeInteger(sequence)
        ? sequence
        : this.sql.exec("SELECT sequence FROM pwi_event_queue WHERE delivery = ?", delivery).one()?.sequence;
      if (!Number.isSafeInteger(baselineSequence)) return false;
      return this.sql.exec(
        "SELECT COUNT(*) AS count FROM pwi_event_queue " +
          "WHERE sequence > ? AND lower(head_sha) = ? " +
          "AND status IN ('pending', 'processing')",
        baselineSequence,
        normalizedSha,
      ).one().count > 0;
    }
    if (!current) return false;
    const baselineSequence = Number.isSafeInteger(sequence) ? sequence : current.sequence;
    return this.memoryEvents.some((event) =>
      event.sequence > baselineSequence && event.headSha.toLowerCase() === normalizedSha &&
        (event.status === "pending" || event.status === "processing"),
    );
  }

  oldestActiveEvent(headSha) {
    const normalizedSha = headSha.toLowerCase();
    if (this.sql) {
      const row = this.sql.exec(
        "SELECT sequence, delivery, pr_number, head_sha, status, attempts, next_attempt_at, received_at " +
          "FROM pwi_event_queue WHERE status IN ('pending', 'processing') " +
          "ORDER BY CASE WHEN lower(head_sha) = ? THEN 1 ELSE 0 END, " +
          "CASE WHEN status = 'pending' THEN 0 ELSE 1 END, sequence LIMIT 1",
        normalizedSha,
      ).toArray()[0];
      return row ? {
        sequence: row.sequence,
        delivery: row.delivery,
        prNumber: row.pr_number,
        headSha: row.head_sha,
        status: row.status,
        attempts: row.attempts,
        nextAttemptAt: row.next_attempt_at,
        receivedAt: row.received_at,
      } : null;
    }
    return this.memoryEvents
      .filter((event) => event.status === "pending" || event.status === "processing")
      .sort((left, right) => {
        const leftSameHead = left.headSha.toLowerCase() === normalizedSha;
        const rightSameHead = right.headSha.toLowerCase() === normalizedSha;
        if (leftSameHead !== rightSameHead) return leftSameHead ? 1 : -1;
        const leftProcessing = left.status === "processing";
        const rightProcessing = right.status === "processing";
        if (leftProcessing !== rightProcessing) return leftProcessing ? 1 : -1;
        return left.sequence - right.sequence;
      })[0] ?? null;
  }

  getEventByDelivery(delivery) {
    if (this.sql) {
      const row = this.sql.exec(
        "SELECT sequence, delivery, pr_number, head_sha, status, attempts, next_attempt_at, received_at " +
          "FROM pwi_event_queue WHERE delivery = ?",
        delivery,
      ).toArray()[0];
      return row ? {
        sequence: row.sequence,
        delivery: row.delivery,
        prNumber: row.pr_number,
        headSha: row.head_sha,
        status: row.status,
        attempts: row.attempts,
        nextAttemptAt: row.next_attempt_at,
        receivedAt: row.received_at,
      } : null;
    }
    return this.memoryEvents.find((event) => event.delivery === delivery) ?? null;
  }

  insertEvent(message, timestamp) {
    if (this.sql) {
      this.sql.exec(
        "INSERT INTO pwi_event_queue " +
          "(delivery, pr_number, head_sha, status, attempts, next_attempt_at, received_at, updated_at) " +
          "VALUES (?, ?, ?, 'pending', 0, ?, ?, ?)",
        message.delivery,
        message.prNumber,
        message.headSha,
        timestamp,
        timestamp,
        timestamp,
      );
      return;
    }
    this.memoryEvents.push({
      sequence: this.nextMemorySequence++,
      delivery: message.delivery,
      prNumber: message.prNumber,
      headSha: message.headSha,
      status: "pending",
      attempts: 0,
      nextAttemptAt: timestamp,
      receivedAt: timestamp,
      updatedAt: timestamp,
    });
  }

  updateEvent(delivery, fields) {
    const { resequence = false, ...updates } = fields;
    if (this.sql) {
      if (resequence) {
        const nextSequence = this.sql.exec(
          "SELECT COALESCE(MAX(sequence), 0) + 1 AS sequence FROM pwi_event_queue",
        ).one().sequence;
        this.sql.exec(
          "UPDATE pwi_event_queue SET sequence = ? WHERE delivery = ?",
          nextSequence,
          delivery,
        );
        this.sql.exec(
          "UPDATE sqlite_sequence SET seq = MAX(seq, ?) WHERE name = 'pwi_event_queue'",
          nextSequence,
        );
      }
      this.sql.exec(
        "UPDATE pwi_event_queue SET head_sha = COALESCE(?, head_sha), status = ?, attempts = ?, " +
          "next_attempt_at = ?, updated_at = ? " +
          "WHERE delivery = ?",
        updates.headSha ?? null,
        updates.status,
        updates.attempts,
        updates.nextAttemptAt,
        updates.updatedAt,
        delivery,
      );
      return;
    }
    const event = this.memoryEvents.find((entry) => entry.delivery === delivery);
    if (event) {
      if (resequence) event.sequence = this.nextMemorySequence++;
      Object.assign(event, updates);
    }
  }

  completeProcessingEvent(event, fields) {
    if (this.sql) {
      this.sql.exec(
        "UPDATE pwi_event_queue SET status = ?, attempts = ?, next_attempt_at = ?, updated_at = ? " +
          "WHERE delivery = ? AND sequence = ? AND status = 'processing' AND attempts = ?",
        fields.status,
        fields.attempts,
        fields.nextAttemptAt,
        fields.updatedAt,
        event.delivery,
        event.sequence,
        fields.attempts,
      );
      return;
    }
    const current = this.memoryEvents.find((entry) => entry.delivery === event.delivery);
    if (current && current.sequence === event.sequence && current.status === "processing" &&
        current.attempts === fields.attempts) {
      Object.assign(current, fields);
    }
  }

  nextDueEvent(timestamp) {
    if (this.sql) {
      const row = this.sql.exec(
        "SELECT sequence, delivery, pr_number, head_sha, status, attempts, next_attempt_at, received_at " +
          "FROM pwi_event_queue " +
          "WHERE status IN ('pending', 'processing') AND next_attempt_at <= ? " +
          "ORDER BY sequence LIMIT 1",
        timestamp,
      ).toArray()[0];
      return row ? {
        sequence: row.sequence,
        delivery: row.delivery,
        prNumber: row.pr_number,
        headSha: row.head_sha,
        status: row.status,
        attempts: row.attempts,
        nextAttemptAt: row.next_attempt_at,
        receivedAt: row.received_at,
      } : null;
    }
    return this.memoryEvents
      .filter((event) => (event.status === "pending" || event.status === "processing") && event.nextAttemptAt <= timestamp)
      .sort((left, right) => left.sequence - right.sequence)[0] ?? null;
  }

  nextAlarmAt() {
    if (this.sql) {
      const value = this.sql.exec(
        "SELECT MIN(next_attempt_at) AS next_at " +
          "FROM pwi_event_queue WHERE status IN ('pending', 'processing')",
      ).one().next_at;
      return value === null ? null : value;
    }
    const pending = this.memoryEvents.filter((event) => event.status === "pending" || event.status === "processing");
    if (pending.length === 0) return null;
    return Math.min(...pending.map((event) => event.nextAttemptAt));
  }

  async scheduleNextAlarm() {
    const storage = this.ctx?.storage;
    if (!storage?.setAlarm || !storage?.deleteAlarm) {
      if (this.sql) throw fail("alarm_storage_unavailable");
      return;
    }
    const nextAt = this.nextAlarmAt();
    if (nextAt === null) {
      await storage.deleteAlarm();
      return;
    }
    await storage.setAlarm(Math.max(this.now() + 50, nextAt));
  }

  pruneTerminalEvents() {
    if (this.sql) {
      this.sql.exec(
        "DELETE FROM pwi_event_queue WHERE sequence IN (" +
          "SELECT sequence FROM pwi_event_queue WHERE status IN ('done', 'failed') " +
          "ORDER BY sequence DESC LIMIT -1 OFFSET ?)" ,
        MAX_TERMINAL_EVENTS,
      );
      return;
    }
    const terminal = this.memoryEvents
      .filter((event) => event.status === "done" || event.status === "failed")
      .sort((left, right) => right.sequence - left.sequence);
    const keep = new Set(terminal.slice(0, MAX_TERMINAL_EVENTS).map((event) => event.sequence));
    this.memoryEvents = this.memoryEvents.filter((event) =>
      event.status === "pending" || event.status === "processing" || keep.has(event.sequence),
    );
  }

  async enqueueEvent(message) {
    await this.ready;
    this.pruneTerminalEvents();
    const existing = this.getEventByDelivery(message.delivery);
    if (existing?.status === "done") return response(202, { status: "already_processed" });
    const atCapacity = this.pendingEvents >= MAX_PENDING_EVENTS;
    const reopenPriorCheck = async (queuedEvent = message) => {
      try {
        const reopen = this.dependencies.reopenCheckForWebhook ?? reopenCheckForWebhook;
        await reopen(queuedEvent, this.env, {
          ...this.dependencies,
          withCheckWriteLock: (operation, deadline) => this.withCheckWriteLock(operation, deadline),
        });
        return true;
      } catch {
        return false;
      }
    };
    if ((existing?.status === "pending" || existing?.status === "processing") && !atCapacity) {
      const timestamp = this.now();
      this.updateEvent(existing.delivery, {
        headSha: existing.headSha,
        status: "pending",
        attempts: 0,
        nextAttemptAt: timestamp,
        updatedAt: timestamp,
        resequence: true,
      });
      const redelivery = this.getEventByDelivery(existing.delivery);
      if (!await reopenPriorCheck(redelivery)) {
        try {
          await this.scheduleNextAlarm();
        } catch {
          return response(503, { error: "alarm_unavailable" });
        }
        return response(503, { error: "check_invalidation_unavailable" });
      }
      try {
        await this.scheduleNextAlarm();
      } catch {
        return response(503, { error: "alarm_unavailable" });
      }
      return response(202, { status: "already_queued" });
    }
    if (atCapacity || existing?.status === "failed") {
      let queueState;
      let prepared;
      try {
        const prepareCurrent = this.dependencies.reopenCurrentCheckForFullQueue ?? reopenCurrentCheckForFullQueue;
        prepared = await prepareCurrent(
          message,
          this.env,
          {
            ...this.dependencies,
            withCheckWriteLock: (operation, deadline) => this.withCheckWriteLock(operation, deadline),
          },
          (currentHeadSha) => {
            const currentDelivery = this.getEventByDelivery(message.delivery);
            const activeCount = this.pendingEvents;
            if (activeCount > MAX_PENDING_EVENTS) {
              queueState = { canQueue: false, alreadyQueued: true };
              return queueState;
            }
            const currentAlreadyActive = currentDelivery?.status === "pending" || currentDelivery?.status === "processing";
            if (currentAlreadyActive) {
              const timestamp = this.now();
              this.updateEvent(message.delivery, {
                headSha: currentHeadSha,
                status: "pending",
                attempts: 0,
                nextAttemptAt: timestamp,
                updatedAt: timestamp,
                resequence: true,
              });
              queueState = { canQueue: true, alreadyQueued: true };
              return queueState;
            }
            const displaced = activeCount === MAX_PENDING_EVENTS
              ? this.oldestActiveEvent(currentHeadSha)
              : null;
            const canQueue = activeCount < MAX_PENDING_EVENTS || Boolean(displaced);
            const timestamp = this.now();
            if (canQueue && displaced) {
              this.updateEvent(displaced.delivery, {
                status: "failed",
                attempts: displaced.attempts,
                nextAttemptAt: timestamp,
                updatedAt: timestamp,
              });
            }
            if (canQueue) {
              if (currentDelivery?.status === "failed" || currentDelivery?.status === "done") {
                this.updateEvent(message.delivery, {
                  headSha: currentHeadSha,
                  status: "pending",
                  attempts: 0,
                  nextAttemptAt: timestamp,
                  updatedAt: timestamp,
                  resequence: true,
                });
              } else {
                this.insertEvent({ ...message, headSha: currentHeadSha }, timestamp);
              }
              this.pruneTerminalEvents();
            }
            queueState = { canQueue, replacedActiveEvent: Boolean(displaced) };
            return queueState;
          },
        );
      } catch {
        try {
          await this.scheduleNextAlarm();
        } catch {
          return response(503, { error: "alarm_unavailable" });
        }
        return response(503, { error: "check_invalidation_unavailable" });
      }
      try {
        await this.scheduleNextAlarm();
      } catch {
        return response(503, { error: "alarm_unavailable" });
      }
      if (prepared.outOfScope) return response(202, { status: "ignored" });
      if (!queueState?.canQueue) return response(503, { error: "coordinator_busy" });
      return response(202, { status: queueState.alreadyQueued ? "already_queued" : "queued" });
    }

    const timestamp = this.now();
    if (existing?.status === "failed") {
      this.updateEvent(message.delivery, {
        status: "pending",
        attempts: 0,
        nextAttemptAt: timestamp,
        updatedAt: timestamp,
        resequence: true,
      });
    } else {
      this.insertEvent(message, timestamp);
    }
    this.pruneTerminalEvents();
    if (!await reopenPriorCheck()) {
      try {
        await this.scheduleNextAlarm();
      } catch {
        return response(503, { error: "alarm_unavailable" });
      }
      return response(503, { error: "check_invalidation_unavailable" });
    }
    try {
      await this.scheduleNextAlarm();
    } catch {
      return response(503, { error: "alarm_unavailable" });
    }
    return response(202, { status: "queued" });
  }

  async fetch(request) {
    const url = new URL(request.url);
    if (request.method !== "POST" || url.pathname !== "/enqueue") {
      return response(404, { error: "not_found" });
    }
    let message;
    try {
      message = parseBody(await readBoundedBody(request, MAX_INTERNAL_EVENT_BYTES));
    } catch {
      return response(400, { error: "invalid_internal_event" });
    }
    let config;
    try {
      config = requiredConfig(this.env);
    } catch {
      return response(503, { error: "coordinator_unavailable" });
    }
    if (!isRecord(message) || typeof message.delivery !== "string" || !/^[0-9a-f-]{36}$/i.test(message.delivery) ||
        message.repositoryId !== REPOSITORY_ID || message.repositoryFullName !== REPOSITORY_FULL_NAME ||
        Number(message.installationId) !== Number(config.installationId) ||
        !Number.isSafeInteger(message.prNumber) || message.prNumber < 1 ||
        typeof message.headSha !== "string" || !/^[0-9a-f]{40}$/i.test(message.headSha)) {
      return response(400, { error: "invalid_internal_event" });
    }
    return this.enqueueEvent({ ...message, headSha: message.headSha.toLowerCase() });
  }

  async alarm() {
    await this.ready;
    if (this.alarmInProgress) return;
    this.alarmInProgress = true;
    try {
      const timestamp = this.now();
      const event = this.nextDueEvent(timestamp);
      if (!event) {
        await this.scheduleNextAlarm();
        return;
      }

      const attempts = event.attempts + 1;
      this.updateEvent(event.delivery, {
        status: "processing",
        attempts,
        nextAttemptAt: timestamp + PROCESSING_LEASE_MS,
        updatedAt: timestamp,
      });
      const message = {
        delivery: event.delivery,
        repositoryId: REPOSITORY_ID,
        repositoryFullName: REPOSITORY_FULL_NAME,
        installationId: this.env.GITHUB_INSTALLATION_ID,
        prNumber: event.prNumber,
        headSha: event.headSha,
      };
      let result;
      try {
        const process = this.dependencies.processQueuedEvent ?? processEventMessage;
        const processDependencies = {
          ...this.dependencies,
          hasSupersedingEvent: () => this.hasSupersedingEvent(event.delivery, event.sequence, event.headSha),
          withCheckWriteLock: (operation, deadline) => this.withCheckWriteLock(operation, deadline),
        };
        result = await process(message, this.env, processDependencies);
      } catch {
        result = response(503, { error: "verification_unavailable" });
      }

      const completedAt = this.now();
      if (Number.isInteger(result?.status) && result.status >= 200 && result.status < 300) {
        this.completeProcessingEvent(event, {
          status: "done",
          attempts,
          nextAttemptAt: completedAt,
          updatedAt: completedAt,
        });
      } else if (attempts < MAX_EVENT_ATTEMPTS) {
        this.completeProcessingEvent(event, {
          status: "pending",
          attempts,
          nextAttemptAt: completedAt + EVENT_RETRY_DELAYS_MS[attempts - 1],
          updatedAt: completedAt,
        });
      } else {
        this.completeProcessingEvent(event, {
          status: "failed",
          attempts,
          nextAttemptAt: completedAt,
          updatedAt: completedAt,
        });
      }
      this.pruneTerminalEvents();
      await this.scheduleNextAlarm();
    } finally {
      this.alarmInProgress = false;
    }
  }
}

export async function handleRequest(request, env) {
  const url = new URL(request.url);

  if (request.method === "GET" && url.pathname === "/healthz") {
    return response(200, { status: "ok" });
  }
  if (request.method !== "POST" || url.pathname !== "/webhooks/github") {
    return response(404, { error: "not_found" });
  }

  let config;
  try {
    config = requiredConfig(env);
  } catch {
    return response(503, { error: "worker_unavailable" });
  }

  let body;
  try {
    body = await readBoundedBody(request, MAX_WEBHOOK_BYTES);
  } catch (error) {
    return response(error.code === "webhook_body_too_large" ? 413 : 400, { error: "invalid_webhook" });
  }
  const validSignature = await verifyWebhookSignature(
    body,
    request.headers.get("x-hub-signature-256"),
    config.webhookSecret,
  ).catch(() => false);
  if (!validSignature) return response(401, { error: "invalid_signature" });

  const delivery = request.headers.get("x-github-delivery");
  if (!delivery || !/^[0-9a-f-]{36}$/i.test(delivery)) return response(400, { error: "invalid_delivery" });
  const eventName = request.headers.get("x-github-event");
  if (!eventName || !/^(pull_request|pull_request_review|check_run)$/.test(eventName)) {
    return response(202, { status: "ignored" });
  }

  let payload;
  let selected;
  try {
    payload = parseBody(body);
    const action = payload.action;
    if (typeof action !== "string") throw fail("event_action_missing");
    if (!isRecord(payload.repository)) throw fail("event_repository_missing");
    if (payload.repository.id !== REPOSITORY_ID || payload.repository.full_name !== REPOSITORY_FULL_NAME) {
      return response(202, { status: "ignored" });
    }
    if (!isRecord(payload.installation) || Number(payload.installation.id) !== Number(config.installationId)) {
      return response(202, { status: "ignored" });
    }
    selected = supportedPrEvent(eventName, action, payload, config.appId);
  } catch {
    return response(400, { error: "invalid_event" });
  }
  if (!selected) return response(202, { status: "ignored" });
  if (!env.PWI_COORDINATOR || typeof env.PWI_COORDINATOR.getByName !== "function") {
    return response(503, { error: "coordinator_unavailable" });
  }
  const coordinator = env.PWI_COORDINATOR.getByName(`${REPOSITORY_ID}:pull:${selected.context.number}`);
  const message = {
    delivery,
    repositoryId: payload.repository.id,
    repositoryFullName: payload.repository.full_name,
    installationId: payload.installation.id,
    prNumber: selected.context.number,
    headSha: selected.context.headSha,
  };
  const internalRequest = new Request("https://pwi.internal/enqueue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(message),
  });
  try {
    return await coordinator.fetch(internalRequest);
  } catch {
    return response(503, { error: "coordinator_unavailable" });
  }
}

export default {
  async fetch(request, env) {
    try {
      return await handleRequest(request, env);
    } catch {
      return response(500, { error: "internal_error" });
    }
  },
};
