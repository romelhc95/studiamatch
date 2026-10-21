export const REPOSITORY_ID = 1211718813;
export const REPOSITORY_FULL_NAME = "romelhc95/studiamatch";
export const TARGET_BRANCH = "desarrollo";
export const CHECK_NAME = "Protected Workflow Integrity";
export const MAX_PULL_REQUEST_FILES = 3000;
export const MAX_REVIEW_RECORDS = 1000;

export const PROTECTED_PREFIXES = Object.freeze([
  ".github/workflows/",
  ".github/actions/",
  ".github/scripts/",
  ".githooks/",
  "scripts/security/",
]);

const TRUSTED_ASSOCIATIONS = new Set(["OWNER", "MEMBER", "COLLABORATOR"]);
const REVIEW_STATES = new Set([
  "APPROVED",
  "CHANGES_REQUESTED",
  "COMMENTED",
  "DISMISSED",
  "PENDING",
]);

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function validatePath(path) {
  if (
    typeof path !== "string" ||
    path.length === 0 ||
    path.startsWith("/") ||
    path.includes("\\") ||
    path.includes("\0") ||
    path.split("/").some((part) => part === ".." || part === ".")
  ) {
    throw new Error("invalid_changed_path");
  }
  return path;
}

export function pullRequestContext(payload, expectedHeadSha = null) {
  if (!isRecord(payload) || !isRecord(payload.repository) || !isRecord(payload.pull_request)) {
    throw new Error("invalid_pull_request_event");
  }
  const pr = payload.pull_request;
  if (
    payload.repository.id !== REPOSITORY_ID ||
    payload.repository.full_name !== REPOSITORY_FULL_NAME ||
    !Number.isSafeInteger(pr.number) ||
    pr.number < 1 ||
    !isRecord(pr.base) ||
    pr.base.ref !== TARGET_BRANCH ||
    !isRecord(pr.head) ||
    typeof pr.head.sha !== "string" ||
    !/^[0-9a-f]{40}$/i.test(pr.head.sha) ||
    !isRecord(pr.user) ||
    typeof pr.user.login !== "string" ||
    pr.user.login.length === 0
  ) {
    throw new Error("pull_request_out_of_scope_or_malformed");
  }
  if (expectedHeadSha !== null && pr.head.sha.toLowerCase() !== expectedHeadSha.toLowerCase()) {
    throw new Error("pull_request_head_mismatch");
  }
  return {
    number: pr.number,
    headSha: pr.head.sha.toLowerCase(),
    author: pr.user.login,
    baseRef: pr.base.ref,
  };
}

export function classifyProtectedFiles(fileRecords) {
  if (!Array.isArray(fileRecords)) throw new Error("invalid_changed_file_list");
  if (fileRecords.length >= MAX_PULL_REQUEST_FILES) {
    throw new Error("changed_file_limit_reached");
  }

  const protectedPaths = new Set();
  for (const file of fileRecords) {
    if (!isRecord(file)) throw new Error("invalid_changed_file_record");
    const currentPath = validatePath(file.filename);
    if (PROTECTED_PREFIXES.some((prefix) => currentPath.startsWith(prefix))) {
      protectedPaths.add(currentPath);
    }
    if (file.previous_filename !== undefined && file.previous_filename !== null) {
      const previousPath = validatePath(file.previous_filename);
      if (PROTECTED_PREFIXES.some((prefix) => previousPath.startsWith(prefix))) {
        protectedPaths.add(previousPath);
      }
    } else if (file.status === "renamed") {
      throw new Error("rename_source_missing");
    }
  }
  return [...protectedPaths].sort();
}

function parseTimestamp(value) {
  if (value === null || value === "") return null;
  if (typeof value !== "string") throw new Error("invalid_review_timestamp");
  const time = Date.parse(value);
  if (!Number.isFinite(time) || !/(Z|[+-]\d{2}:?\d{2})$/i.test(value)) {
    throw new Error("invalid_review_timestamp");
  }
  return time;
}

export function hasTrustedCurrentApproval(reviewRecords, { headSha, prAuthor }) {
  if (!Array.isArray(reviewRecords) || !/^[0-9a-f]{40}$/i.test(headSha ?? "") || !prAuthor) {
    throw new Error("invalid_approval_context");
  }
  if (reviewRecords.length >= MAX_REVIEW_RECORDS) throw new Error("review_limit_reached");

  const latestByReviewer = new Map();
  for (const review of reviewRecords) {
    if (
      !isRecord(review) ||
      !isRecord(review.user) ||
      typeof review.user.login !== "string" ||
      review.user.login.length === 0 ||
      typeof review.user.type !== "string" ||
      review.user.type.length === 0 ||
      typeof review.state !== "string" ||
      !REVIEW_STATES.has(review.state) ||
      !Number.isSafeInteger(review.id) ||
      review.id < 0
    ) {
      throw new Error("invalid_review_record");
    }
    const submittedAt = parseTimestamp(review.submitted_at);
    if (submittedAt === null || review.user.type !== "User") continue;
    if (review.user.login.toLowerCase() === prAuthor.toLowerCase()) continue;
    if (review.commit_id !== null && review.commit_id !== undefined &&
        (typeof review.commit_id !== "string" || !/^[0-9a-f]{40}$/i.test(review.commit_id))) {
      throw new Error("invalid_review_commit");
    }

    const key = review.user.login.toLowerCase();
    const previous = latestByReviewer.get(key);
    if (!previous || submittedAt > previous.submittedAt ||
        (submittedAt === previous.submittedAt && review.id >= previous.id)) {
      latestByReviewer.set(key, { submittedAt, id: review.id, review });
    }
  }

  return [...latestByReviewer.values()].some(({ review }) =>
    review.state === "APPROVED" &&
    review.commit_id?.toLowerCase() === headSha.toLowerCase() &&
    typeof review.author_association === "string" &&
    TRUSTED_ASSOCIATIONS.has(review.author_association),
  );
}

export function checkRunExternalId(prNumber) {
  if (!Number.isSafeInteger(prNumber) || prNumber < 1) throw new Error("invalid_pr_number");
  return `pwi-v1-${REPOSITORY_ID}-${prNumber}`;
}
