import { runInDurableObject } from "cloudflare:test";
import { env } from "cloudflare:workers";
import { expect, it } from "vitest";

const REPOSITORY_ID = 1211718813;
const REPOSITORY = "romelhc95/studiamatch";
const INSTALLATION_ID = "67890";

function enqueueRequest(delivery, prNumber, headSha) {
  return new Request("https://pwi.internal/enqueue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      delivery,
      repositoryId: REPOSITORY_ID,
      repositoryFullName: REPOSITORY,
      installationId: INSTALLATION_ID,
      prNumber,
      headSha,
    }),
  });
}

it("persists a bounded metadata-only queue and processes one event through the Workers alarm runtime", async () => {
  const stub = env.PWI_COORDINATOR.getByName(`${REPOSITORY_ID}:pull:501`);
  const initialized = await stub.fetch("https://pwi.internal/not-found");
  expect(initialized.status).toBe(404);

  const outcome = await runInDurableObject(stub, async (instance, state) => {
    const processed = [];
    instance.env = {
      GITHUB_APP_ID: "12345",
      GITHUB_INSTALLATION_ID: INSTALLATION_ID,
      GITHUB_WEBHOOK_SECRET: "synthetic-only-webhook-secret-value-123456",
      GITHUB_APP_PRIVATE_KEY: "synthetic-only-key-not-used-by-queue-test",
    };
    instance.dependencies = {
      reopenCheckForWebhook: async () => {},
      reopenCurrentCheckForFullQueue: async (message, _env, _dependencies, onCurrentHead) => ({
        currentHeadSha: message.headSha,
        queueState: onCurrentHead(message.headSha),
      }),
      processQueuedEvent: async (message) => {
        processed.push(message);
        await new Promise((resolve) => setTimeout(resolve, 25));
        return { status: 200 };
      },
    };

    const accepted = [];
    const deliveries = Array.from({ length: 8 }, (_, index) =>
      `00000000-0000-4000-8000-${String(index + 1).padStart(12, "0")}`,
    );
    for (let index = 0; index < deliveries.length; index += 1) {
      const response = await instance.fetch(enqueueRequest(deliveries[index], 501, String(index + 1).repeat(40)));
      accepted.push(response.status);
    }
    const overflow = await instance.fetch(enqueueRequest(
      "00000000-0000-4000-8000-000000000009",
      501,
      "9".repeat(40),
    ));
    const duplicate = await instance.fetch(enqueueRequest(deliveries[1], 501, "2".repeat(40)));
    const before = state.storage.sql.exec(
      "SELECT delivery, pr_number, head_sha, status, attempts FROM pwi_event_queue ORDER BY sequence",
    ).toArray();
    const alarmBefore = await state.storage.getAlarm();

    await instance.alarm();

    const after = state.storage.sql.exec(
      "SELECT delivery, pr_number, head_sha, status, attempts FROM pwi_event_queue ORDER BY sequence",
    ).toArray();
    const columns = state.storage.sql.exec("PRAGMA table_info(pwi_event_queue)").toArray().map((column) => column.name);
    return {
      accepted,
      overflowStatus: overflow.status,
      overflowBody: await overflow.json(),
      duplicateStatus: duplicate.status,
      duplicateBody: await duplicate.json(),
      alarmScheduled: typeof alarmBefore === "number",
      before,
      after,
      columns,
      processed,
    };
  });

  expect(outcome.accepted).toEqual(Array(8).fill(202));
  expect(outcome.overflowStatus).toBe(202);
  expect(outcome.overflowBody).toEqual({ status: "queued" });
  expect(outcome.duplicateStatus).toBe(202);
  expect(outcome.duplicateBody).toEqual({ status: "already_queued" });
  expect(outcome.alarmScheduled).toBe(true);
  expect(outcome.before).toHaveLength(9);
  expect(outcome.before.filter((event) => event.status === "pending")).toHaveLength(8);
  expect(outcome.before.filter((event) => event.status === "failed")).toHaveLength(1);
  expect(outcome.after.filter((event) => event.status === "done")).toHaveLength(1);
  expect(outcome.after.filter((event) => event.status === "pending")).toHaveLength(7);
  expect(outcome.columns).not.toContain("payload");
  expect(outcome.columns).not.toContain("email");
  expect(outcome.processed).toHaveLength(1);
  expect(outcome.processed[0]).toEqual({
    delivery: "00000000-0000-4000-8000-000000000003",
    repositoryId: REPOSITORY_ID,
    repositoryFullName: REPOSITORY,
    installationId: INSTALLATION_ID,
    prNumber: 501,
    headSha: "3".repeat(40),
  });
});

it("returns 503 when SQLite alarm scheduling fails, then accepts a same-id redelivery after recovery", async () => {
  const stub = env.PWI_COORDINATOR.getByName(`${REPOSITORY_ID}:alarm-failure`);
  const initialized = await stub.fetch("https://pwi.internal/not-found");
  expect(initialized.status).toBe(404);

  const delivery = "00000000-0000-4000-8000-000000000101";
  const outcome = await runInDurableObject(stub, async (instance, state) => {
    instance.env = {
      GITHUB_APP_ID: "12345",
      GITHUB_INSTALLATION_ID: INSTALLATION_ID,
      GITHUB_WEBHOOK_SECRET: "synthetic-only-webhook-secret-value-123456",
      GITHUB_APP_PRIVATE_KEY: "synthetic-only-key-not-used-by-queue-test",
    };
    instance.dependencies = { reopenCheckForWebhook: async () => {} };
    const storage = state.storage;
    const originalSetAlarm = storage.setAlarm.bind(storage);
    let failScheduling = true;
    storage.setAlarm = async (...args) => {
      if (failScheduling) throw new Error("synthetic alarm persistence failure");
      return originalSetAlarm(...args);
    };

    const rejected = await instance.fetch(enqueueRequest(delivery, 501, "a".repeat(40)));
    const rowAfterFailure = state.storage.sql.exec(
      "SELECT status FROM pwi_event_queue WHERE delivery = ?",
      delivery,
    ).one();
    failScheduling = false;
    const accepted = await instance.fetch(enqueueRequest(delivery, 501, "a".repeat(40)));
    const alarmAfterRecovery = await state.storage.getAlarm();
    storage.setAlarm = originalSetAlarm;
    return { rejected: rejected.status, rowAfterFailure, accepted: accepted.status, alarmAfterRecovery };
  });

  expect(outcome.rejected).toBe(503);
  expect(outcome.rowAfterFailure.status).toBe("pending");
  expect(outcome.accepted).toBe(202);
  expect(typeof outcome.alarmAfterRecovery).toBe("number");
});

it("reorders a full-queue redelivery and guards terminal transitions in Durable Object SQLite", async () => {
  const stub = env.PWI_COORDINATOR.getByName(`${REPOSITORY_ID}:full-queue-redelivery`);
  const initialized = await stub.fetch("https://pwi.internal/not-found");
  expect(initialized.status).toBe(404);

  const failedDelivery = "00000000-0000-4000-8000-000000000301";
  const currentSha = "a".repeat(40);
  const staleSha = "b".repeat(40);
  const outcome = await runInDurableObject(stub, async (instance, state) => {
    instance.env = {
      GITHUB_APP_ID: "12345",
      GITHUB_INSTALLATION_ID: INSTALLATION_ID,
      GITHUB_WEBHOOK_SECRET: "synthetic-only-webhook-secret-value-123456",
      GITHUB_APP_PRIVATE_KEY: "synthetic-only-key-not-used-by-queue-test",
    };
    instance.dependencies = {
      reopenCurrentCheckForFullQueue: async (message, _env, _dependencies, onCurrentHead) => ({
        currentHeadSha: currentSha,
        queueState: onCurrentHead(currentSha),
      }),
    };

    instance.insertEvent({ delivery: failedDelivery, prNumber: 501, headSha: currentSha }, Date.now());
    instance.updateEvent(failedDelivery, {
      status: "failed",
      attempts: 3,
      nextAttemptAt: Date.now(),
      updatedAt: Date.now(),
    });
    const staleDeliveries = [];
    for (let index = 0; index < 8; index += 1) {
      const delivery = `00000000-0000-4000-8000-${String(index + 401).padStart(12, "0")}`;
      staleDeliveries.push(delivery);
      instance.insertEvent({ delivery, prNumber: 501, headSha: staleSha }, Date.now());
      instance.updateEvent(delivery, {
        status: "processing",
        attempts: 1,
        nextAttemptAt: Date.now() + 600_000,
        updatedAt: Date.now(),
      });
    }
    const previousMaximum = state.storage.sql.exec(
      "SELECT MAX(sequence) AS maximum FROM pwi_event_queue",
    ).one().maximum;

    const redelivery = await instance.fetch(enqueueRequest(failedDelivery, 501, currentSha));
    const requeued = state.storage.sql.exec(
      "SELECT sequence, status, attempts FROM pwi_event_queue WHERE delivery = ?",
      failedDelivery,
    ).one();
    const displaced = state.storage.sql.exec(
      "SELECT sequence, status FROM pwi_event_queue WHERE delivery = ?",
      staleDeliveries[0],
    ).one();
    const pendingBeforeGuard = state.storage.sql.exec(
      "SELECT COUNT(*) AS count FROM pwi_event_queue WHERE status IN ('pending', 'processing')",
    ).one().count;
    instance.updateEvent(staleDeliveries[1], {
      status: "failed",
      attempts: 1,
      nextAttemptAt: Date.now(),
      updatedAt: Date.now(),
    });
    const followingDelivery = "00000000-0000-4000-8000-000000000499";
    instance.insertEvent({ delivery: followingDelivery, prNumber: 501, headSha: currentSha }, Date.now());
    const followingSequence = state.storage.sql.exec(
      "SELECT sequence FROM pwi_event_queue WHERE delivery = ?",
      followingDelivery,
    ).one().sequence;

    const selected = { sequence: requeued.sequence, delivery: failedDelivery, attempts: 0 };
    instance.updateEvent(failedDelivery, {
      status: "processing",
      attempts: 1,
      nextAttemptAt: Date.now() + 600_000,
      updatedAt: Date.now(),
    });
    instance.updateEvent(failedDelivery, {
      status: "failed",
      attempts: 1,
      nextAttemptAt: Date.now(),
      updatedAt: Date.now(),
    });
    instance.completeProcessingEvent(selected, {
      status: "done",
      attempts: 1,
      nextAttemptAt: Date.now(),
      updatedAt: Date.now(),
    });
    const afterGuard = state.storage.sql.exec(
      "SELECT status FROM pwi_event_queue WHERE delivery = ?",
      failedDelivery,
    ).one().status;

    return {
      status: redelivery.status,
      body: await redelivery.json(),
      previousMaximum,
      requeued,
      displaced,
      pendingBeforeGuard,
      followingSequence,
      afterGuard,
    };
  });

  expect(outcome.status).toBe(202);
  expect(outcome.body).toEqual({ status: "queued" });
  expect(outcome.requeued.sequence).toBeGreaterThan(outcome.previousMaximum);
  expect(outcome.requeued.status).toBe("pending");
  expect(outcome.requeued.attempts).toBe(0);
  expect(outcome.followingSequence).toBeGreaterThan(outcome.requeued.sequence);
  expect(outcome.displaced.status).toBe("failed");
  expect(outcome.pendingBeforeGuard).toBe(8);
  expect(outcome.afterGuard).toBe("failed");
});

it("refreshes a failed same-delivery row to the current SHA below queue capacity in SQLite", async () => {
  const stub = env.PWI_COORDINATOR.getByName(`${REPOSITORY_ID}:failed-row-redelivery-low-capacity`);
  const initialized = await stub.fetch("https://pwi.internal/not-found");
  expect(initialized.status).toBe(404);

  const delivery = "00000000-0000-4000-8000-000000000501";
  const webhookSha = "a".repeat(40);
  const currentSha = "b".repeat(40);
  const outcome = await runInDurableObject(stub, async (instance, state) => {
    instance.env = {
      GITHUB_APP_ID: "12345",
      GITHUB_INSTALLATION_ID: INSTALLATION_ID,
      GITHUB_WEBHOOK_SECRET: "synthetic-only-webhook-secret-value-123456",
      GITHUB_APP_PRIVATE_KEY: "synthetic-only-key-not-used-by-queue-test",
    };
    let currentHeadReads = 0;
    instance.dependencies = {
      reopenCurrentCheckForFullQueue: async (message, _env, _dependencies, onCurrentHead) => {
        currentHeadReads += 1;
        const queueState = onCurrentHead(currentSha);
        return { currentHeadSha: currentSha, queueState };
      },
    };

    instance.insertEvent({ delivery, prNumber: 501, headSha: webhookSha }, Date.now());
    instance.updateEvent(delivery, {
      headSha: currentSha,
      status: "failed",
      attempts: 3,
      nextAttemptAt: Date.now(),
      updatedAt: Date.now(),
    });
    const redelivery = await instance.fetch(enqueueRequest(delivery, 501, webhookSha));
    const row = state.storage.sql.exec(
      "SELECT head_sha, status, attempts FROM pwi_event_queue WHERE delivery = ?",
      delivery,
    ).one();
    return {
      status: redelivery.status,
      body: await redelivery.json(),
      currentHeadReads,
      row,
      activeCount: state.storage.sql.exec(
        "SELECT COUNT(*) AS count FROM pwi_event_queue WHERE status IN ('pending', 'processing')",
      ).one().count,
      alarm: await state.storage.getAlarm(),
    };
  });

  expect(outcome.status).toBe(202);
  expect(outcome.body).toEqual({ status: "queued" });
  expect(outcome.currentHeadReads).toBe(1);
  expect(outcome.row.head_sha).toBe(currentSha);
  expect(outcome.row.status).toBe("pending");
  expect(outcome.row.attempts).toBe(0);
  expect(outcome.activeCount).toBe(1);
  expect(typeof outcome.alarm).toBe("number");
});

it("serializes a review event enqueued during a slow alarm verification", async () => {
  const stub = env.PWI_COORDINATOR.getByName(`${REPOSITORY_ID}:slow-verification`);
  const initialized = await stub.fetch("https://pwi.internal/not-found");
  expect(initialized.status).toBe(404);

  const firstDelivery = "00000000-0000-4000-8000-000000000201";
  const secondDelivery = "00000000-0000-4000-8000-000000000202";
  const outcome = await runInDurableObject(stub, async (instance, state) => {
    instance.env = {
      GITHUB_APP_ID: "12345",
      GITHUB_INSTALLATION_ID: INSTALLATION_ID,
      GITHUB_WEBHOOK_SECRET: "synthetic-only-webhook-secret-value-123456",
      GITHUB_APP_PRIVATE_KEY: "synthetic-only-key-not-used-by-queue-test",
    };
    let announceStarted;
    let releaseFirst;
    const firstStarted = new Promise((resolve) => { announceStarted = resolve; });
    const releaseGate = new Promise((resolve) => { releaseFirst = resolve; });
    const processed = [];
    instance.dependencies = {
      reopenCheckForWebhook: async () => {},
      async processQueuedEvent(message) {
        processed.push(message.delivery);
        if (message.delivery === firstDelivery) {
          announceStarted();
          await releaseGate;
        }
        return { status: 200 };
      },
    };

    const firstAccepted = await instance.fetch(enqueueRequest(firstDelivery, 501, "1".repeat(40)));
    const firstAlarm = instance.alarm();
    await firstStarted;
    const secondAccepted = await instance.fetch(enqueueRequest(secondDelivery, 501, "2".repeat(40)));
    const overlappingAlarm = await instance.alarm();
    const processedDuringFirst = [...processed];
    releaseFirst();
    await firstAlarm;
    const afterFirst = state.storage.sql.exec(
      "SELECT delivery, status FROM pwi_event_queue ORDER BY sequence",
    ).toArray();
    await instance.alarm();
    const afterSecond = state.storage.sql.exec(
      "SELECT delivery, status FROM pwi_event_queue ORDER BY sequence",
    ).toArray();
    return { firstAccepted: firstAccepted.status, secondAccepted: secondAccepted.status,
      processedDuringFirst, processed, afterFirst, afterSecond, overlappingAlarm };
  });

  expect(outcome.firstAccepted).toBe(202);
  expect(outcome.secondAccepted).toBe(202);
  expect(outcome.processedDuringFirst).toEqual([firstDelivery]);
  expect(outcome.afterFirst).toEqual([
    { delivery: firstDelivery, status: "done" },
    { delivery: secondDelivery, status: "pending" },
  ]);
  expect(outcome.processed).toEqual([firstDelivery, secondDelivery]);
  expect(outcome.afterSecond).toEqual([
    { delivery: firstDelivery, status: "done" },
    { delivery: secondDelivery, status: "done" },
  ]);
});

it("only treats later events for the same SHA as superseding in Durable Object SQLite", async () => {
  const stub = env.PWI_COORDINATOR.getByName(`${REPOSITORY_ID}:same-sha-supersession`);
  const initialized = await stub.fetch("https://pwi.internal/not-found");
  expect(initialized.status).toBe(404);

  const currentSha = "a".repeat(40);
  const staleSha = "b".repeat(40);
  const outcome = await runInDurableObject(stub, async (instance) => {
    const currentDelivery = "00000000-0000-4000-8000-000000000601";
    const staleDelivery = "00000000-0000-4000-8000-000000000602";
    const laterCurrentDelivery = "00000000-0000-4000-8000-000000000603";
    instance.insertEvent({ delivery: currentDelivery, prNumber: 501, headSha: currentSha }, Date.now());
    instance.insertEvent({ delivery: staleDelivery, prNumber: 501, headSha: staleSha }, Date.now() + 1);
    const current = instance.getEventByDelivery(currentDelivery);
    const stale = instance.getEventByDelivery(staleDelivery);
    const differentShaDoesNotSupersede = instance.hasSupersedingEvent(
      currentDelivery,
      current.sequence,
      currentSha,
    );
    instance.insertEvent({ delivery: laterCurrentDelivery, prNumber: 501, headSha: currentSha }, Date.now() + 2);
    const sameShaDoesSupersede = instance.hasSupersedingEvent(
      currentDelivery,
      current.sequence,
      currentSha,
    );
    const staleShaDoesNotSeeCurrentSuccessor = instance.hasSupersedingEvent(
      staleDelivery,
      stale.sequence,
      staleSha,
    );
    return { differentShaDoesNotSupersede, sameShaDoesSupersede, staleShaDoesNotSeeCurrentSuccessor };
  });

  expect(outcome).toEqual({
    differentShaDoesNotSupersede: false,
    sameShaDoesSupersede: true,
    staleShaDoesNotSeeCurrentSuccessor: false,
  });
});

it("reconciles an active same-delivery redelivery to the current SHA at queue capacity in SQLite", async () => {
  const stub = env.PWI_COORDINATOR.getByName(`${REPOSITORY_ID}:active-redelivery-at-capacity`);
  const initialized = await stub.fetch("https://pwi.internal/not-found");
  expect(initialized.status).toBe(404);

  const delivery = "00000000-0000-4000-8000-000000000701";
  const staleSha = "a".repeat(40);
  const currentSha = "b".repeat(40);
  const outcome = await runInDurableObject(stub, async (instance, state) => {
    instance.env = {
      GITHUB_APP_ID: "12345",
      GITHUB_INSTALLATION_ID: INSTALLATION_ID,
      GITHUB_WEBHOOK_SECRET: "synthetic-only-webhook-secret-value-123456",
      GITHUB_APP_PRIVATE_KEY: "synthetic-only-key-not-used-by-queue-test",
    };
    instance.dependencies = {
      reopenCurrentCheckForFullQueue: async (_message, _env, _dependencies, onCurrentHead) => ({
        currentHeadSha: currentSha,
        queueState: onCurrentHead(currentSha),
      }),
    };

    instance.insertEvent({ delivery, prNumber: 501, headSha: staleSha }, Date.now());
    instance.updateEvent(delivery, {
      status: "processing",
      attempts: 1,
      nextAttemptAt: Date.now() + 600_000,
      updatedAt: Date.now(),
    });
    const otherDeliveries = [];
    for (let index = 0; index < 7; index += 1) {
      const otherDelivery = `00000000-0000-4000-8000-${String(index + 702).padStart(12, "0")}`;
      otherDeliveries.push(otherDelivery);
      instance.insertEvent({ delivery: otherDelivery, prNumber: 501, headSha: staleSha }, Date.now() + index + 1);
    }
    const maximumBefore = state.storage.sql.exec(
      "SELECT MAX(sequence) AS maximum FROM pwi_event_queue",
    ).one().maximum;

    const redelivery = await instance.fetch(enqueueRequest(delivery, 501, staleSha));
    const row = state.storage.sql.exec(
      "SELECT sequence, head_sha, status, attempts FROM pwi_event_queue WHERE delivery = ?",
      delivery,
    ).one();
    const activeCount = state.storage.sql.exec(
      "SELECT COUNT(*) AS count FROM pwi_event_queue WHERE status IN ('pending', 'processing')",
    ).one().count;
    const displacedCount = state.storage.sql.exec(
      "SELECT COUNT(*) AS count FROM pwi_event_queue WHERE status = 'failed'",
    ).one().count;
    const otherActiveCount = state.storage.sql.exec(
      "SELECT COUNT(*) AS count FROM pwi_event_queue WHERE delivery IN (?, ?, ?, ?, ?, ?, ?) " +
        "AND status IN ('pending', 'processing')",
      ...otherDeliveries,
    ).one().count;
    return {
      status: redelivery.status,
      body: await redelivery.json(),
      maximumBefore,
      row,
      activeCount,
      displacedCount,
      otherActiveCount,
      alarm: await state.storage.getAlarm(),
    };
  });

  expect(outcome.status).toBe(202);
  expect(outcome.body).toEqual({ status: "already_queued" });
  expect(outcome.row.sequence).toBeGreaterThan(outcome.maximumBefore);
  expect(outcome.row.head_sha).toBe(currentSha);
  expect(outcome.row.status).toBe("pending");
  expect(outcome.row.attempts).toBe(0);
  expect(outcome.activeCount).toBe(8);
  expect(outcome.displacedCount).toBe(0);
  expect(outcome.otherActiveCount).toBe(7);
  expect(typeof outcome.alarm).toBe("number");
});

it("reuses a completed same-delivery SQLite row when a full-queue redelivery waits on the current-head read", async () => {
  const stub = env.PWI_COORDINATOR.getByName(`${REPOSITORY_ID}:completed-redelivery-at-capacity`);
  const initialized = await stub.fetch("https://pwi.internal/not-found");
  expect(initialized.status).toBe(404);

  const delivery = "00000000-0000-4000-8000-000000000801";
  const currentSha = "a".repeat(40);
  const differentSha = "b".repeat(40);
  const outcome = await runInDurableObject(stub, async (instance, state) => {
    instance.env = {
      GITHUB_APP_ID: "12345",
      GITHUB_INSTALLATION_ID: INSTALLATION_ID,
      GITHUB_WEBHOOK_SECRET: "synthetic-only-webhook-secret-value-123456",
      GITHUB_APP_PRIVATE_KEY: "synthetic-only-key-not-used-by-queue-test",
    };
    let releaseHeadRead;
    let announceHeadRead;
    const headReadStarted = new Promise((resolve) => { announceHeadRead = resolve; });
    const headReadGate = new Promise((resolve) => { releaseHeadRead = resolve; });
    instance.dependencies = {
      reopenCurrentCheckForFullQueue: async (message, _env, _dependencies, onCurrentHead) => {
        announceHeadRead();
        await headReadGate;
        const queueState = onCurrentHead(currentSha);
        return { currentHeadSha: currentSha, queueState };
      },
      processQueuedEvent: async () => ({ status: 200 }),
    };

    instance.insertEvent({ delivery, prNumber: 501, headSha: currentSha }, Date.now() - 100);
    const original = state.storage.sql.exec(
      "SELECT sequence FROM pwi_event_queue WHERE delivery = ?",
      delivery,
    ).one();
    for (let index = 0; index < 7; index += 1) {
      instance.insertEvent({
        delivery: `00000000-0000-4000-8000-${String(index + 802).padStart(12, "0")}`,
        prNumber: 501,
        headSha: differentSha,
      }, Date.now() + 10_000 + index);
    }

    const redelivery = instance.fetch(enqueueRequest(delivery, 501, currentSha));
    await headReadStarted;
    await instance.alarm();
    const completed = state.storage.sql.exec(
      "SELECT sequence, status FROM pwi_event_queue WHERE delivery = ?",
      delivery,
    ).one();
    releaseHeadRead();
    const response = await redelivery;
    const requeued = state.storage.sql.exec(
      "SELECT sequence, head_sha, status, attempts FROM pwi_event_queue WHERE delivery = ?",
      delivery,
    ).one();
    const activeCount = state.storage.sql.exec(
      "SELECT COUNT(*) AS count FROM pwi_event_queue WHERE status IN ('pending', 'processing')",
    ).one().count;
    return {
      response: response.status,
      body: await response.json(),
      originalSequence: original.sequence,
      completed,
      requeued,
      activeCount,
      alarm: await state.storage.getAlarm(),
    };
  });

  expect(outcome.completed.status).toBe("done");
  expect(outcome.response).toBe(202);
  expect(outcome.body).toEqual({ status: "queued" });
  expect(outcome.requeued.sequence).toBeGreaterThan(outcome.originalSequence);
  expect(outcome.requeued.head_sha).toBe(currentSha);
  expect(outcome.requeued.status).toBe("pending");
  expect(outcome.requeued.attempts).toBe(0);
  expect(outcome.activeCount).toBe(8);
  expect(typeof outcome.alarm).toBe("number");
});
