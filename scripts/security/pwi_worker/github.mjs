import { checkRunExternalId } from "./policy.mjs";

const API_ORIGIN = "https://api.github.com";
const API_VERSION = "2026-03-10";
const MAX_API_BODY_BYTES = 1_000_000;
const MAX_PAGE_SIZE = 100;
const MAX_FILE_PAGES = 30;
const MAX_REVIEW_PAGES = 10;
const MAX_MATCHING_CHECK_RUNS = 20;

function pwiError(code) {
  const error = new Error(code);
  error.code = code;
  return error;
}

function b64url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function decodePem(pem) {
  if (typeof pem !== "string") throw pwiError("private_key_invalid");
  const match = pem.trim().match(/^-----BEGIN (PRIVATE KEY|RSA PRIVATE KEY)-----([\s\S]+)-----END \1-----$/);
  if (!match) throw pwiError("private_key_format_unsupported");
  const encoded = match[2].replace(/\s/g, "");
  if (!/^[A-Za-z0-9+/]+={0,2}$/.test(encoded)) throw pwiError("private_key_invalid");
  let binary;
  try {
    binary = atob(encoded);
  } catch {
    throw pwiError("private_key_invalid");
  }
  const der = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  if (match[1] === "PRIVATE KEY") return der;
  return wrapPkcs1AsPkcs8(der);
}

function encodeDerLength(length) {
  if (length < 0x80) return Uint8Array.of(length);
  const octets = [];
  let remaining = length;
  while (remaining > 0) {
    octets.unshift(remaining & 0xff);
    remaining >>>= 8;
  }
  return Uint8Array.of(0x80 | octets.length, ...octets);
}

function derSequence(content) {
  return new Uint8Array([0x30, ...encodeDerLength(content.length), ...content]);
}

function wrapPkcs1AsPkcs8(pkcs1) {
  const algorithm = Uint8Array.of(
    0x30, 0x0d, 0x06, 0x09, 0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01, 0x05, 0x00,
  );
  const privateKeyOctet = new Uint8Array([0x04, ...encodeDerLength(pkcs1.length), ...pkcs1]);
  const version = Uint8Array.of(0x02, 0x01, 0x00);
  return derSequence(new Uint8Array([...version, ...algorithm, ...privateKeyOctet]));
}

export async function createAppJwt({ appId, privateKeyPem, now = Date.now() }) {
  if (!/^\d{1,20}$/.test(String(appId ?? ""))) throw pwiError("app_id_invalid");
  const key = await crypto.subtle.importKey(
    "pkcs8",
    decodePem(privateKeyPem),
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const issuedAt = Math.floor(now / 1000) - 60;
  const header = b64url(new TextEncoder().encode(JSON.stringify({ alg: "RS256", typ: "JWT" })));
  const claims = b64url(new TextEncoder().encode(JSON.stringify({
    iss: String(appId),
    iat: issuedAt,
    exp: issuedAt + 540,
  })));
  const message = `${header}.${claims}`;
  const signature = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(message));
  return `${message}.${b64url(new Uint8Array(signature))}`;
}

async function readBodyLimited(response, limit = MAX_API_BODY_BYTES) {
  if (!response.body) return new Uint8Array();
  const reader = response.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > limit) {
        await reader.cancel();
        throw pwiError("github_response_too_large");
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const result = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return result;
}

async function parseJsonResponse(response) {
  const bytes = await readBodyLimited(response);
  if (bytes.length === 0) return null;
  try {
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  } catch {
    throw pwiError("github_response_invalid_json");
  }
}

function safeRetryDelay(response, attempt) {
  const retryAfter = response.headers.get("retry-after");
  const value = retryAfter === null ? Number.NaN : Number(retryAfter);
  if (Number.isFinite(value) && value >= 0 && value <= 1) return Math.ceil(value * 1000);
  return [250, 500, 1000][attempt] ?? 1000;
}

export class GitHubApi {
  constructor({ fetchImpl = fetch, token, deadline = Date.now() + 50_000, now = Date.now, sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms)) }) {
    this.fetchImpl = fetchImpl;
    this.token = token;
    this.deadline = deadline;
    this.now = now;
    this.sleep = sleep;
  }

  async request(method, path, body = undefined) {
    if (typeof path !== "string" ||
        (!path.startsWith("/repos/romelhc95/studiamatch/") && !path.startsWith("/app/installations/")) ||
        path.includes("\\") || path.includes("\0") || path.includes("#") || path.includes("\n")) {
      throw pwiError("github_path_out_of_scope");
    }
    const url = `${API_ORIGIN}${path}`;

    for (let attempt = 0; attempt <= 3; attempt += 1) {
      const remaining = this.deadline - this.now();
      if (remaining <= 0) throw pwiError("worker_deadline_exceeded");
      let response;
      try {
        response = await this.fetchImpl(url, {
          method,
          headers: {
            Accept: "application/vnd.github+json",
            Authorization: `Bearer ${this.token}`,
            "X-GitHub-Api-Version": API_VERSION,
            ...(body === undefined ? {} : { "Content-Type": "application/json" }),
          },
          ...(body === undefined ? {} : { body: JSON.stringify(body) }),
          signal: AbortSignal.timeout(Math.min(10_000, remaining)),
        });
      } catch {
        throw pwiError("github_transport_failed");
      }
      if (response.ok) return parseJsonResponse(response);
      if ((response.status === 429 || response.status >= 500) && attempt < 3 && method !== "POST") {
        await this.sleep(Math.min(safeRetryDelay(response, attempt), Math.max(0, this.deadline - this.now())));
        continue;
      }
      throw pwiError(`github_http_${response.status}`);
    }
    throw pwiError("github_retry_limit_reached");
  }

  async createInstallationToken({ appId, privateKeyPem, installationId, now = this.now() }) {
    if (!/^\d{1,20}$/.test(String(installationId ?? ""))) throw pwiError("installation_id_invalid");
    const jwt = await createAppJwt({ appId, privateKeyPem, now });
    let response;
    for (let attempt = 0; attempt <= 3; attempt += 1) {
      const remaining = this.deadline - this.now();
      if (remaining <= 0) throw pwiError("worker_deadline_exceeded");
      try {
        response = await this.fetchImpl(`${API_ORIGIN}/app/installations/${installationId}/access_tokens`, {
          method: "POST",
          headers: {
            Accept: "application/vnd.github+json",
            Authorization: `Bearer ${jwt}`,
            "X-GitHub-Api-Version": API_VERSION,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            repositories: ["studiamatch"],
            permissions: { pull_requests: "read", checks: "write" },
          }),
          signal: AbortSignal.timeout(Math.min(10_000, remaining)),
        });
      } catch {
        throw pwiError("github_installation_token_transport_failed");
      }
      if (response.ok) break;
      if ((response.status === 429 || response.status >= 500) && attempt < 3) {
        await this.sleep(Math.min(safeRetryDelay(response, attempt), Math.max(0, this.deadline - this.now())));
        continue;
      }
      throw pwiError(`github_installation_token_http_${response.status}`);
    }
    if (!response?.ok) throw pwiError("github_installation_token_retry_limit_reached");
    const data = await parseJsonResponse(response);
    if (!data || typeof data.token !== "string" || !data.token || typeof data.expires_at !== "string") {
      throw pwiError("github_installation_token_invalid");
    }
    return data.token;
  }

  async listAll(path, maxPages, maxRecords, label) {
    const records = [];
    for (let page = 1; page <= maxPages; page += 1) {
      const separator = path.includes("?") ? "&" : "?";
      const response = await this.request("GET", `${path}${separator}per_page=${MAX_PAGE_SIZE}&page=${page}`);
      if (!Array.isArray(response) || response.some((item) => item === null || typeof item !== "object" || Array.isArray(item))) {
        throw pwiError(`${label}_response_invalid`);
      }
      records.push(...response);
      if (records.length > maxRecords) throw pwiError(`${label}_limit_reached`);
      if (response.length < MAX_PAGE_SIZE) return records;
    }
    throw pwiError(`${label}_pagination_truncated`);
  }

  listPullRequestFiles(number) {
    return this.listAll(`/repos/romelhc95/studiamatch/pulls/${number}/files`, MAX_FILE_PAGES, 2999, "files");
  }

  listPullRequestReviews(number) {
    return this.listAll(`/repos/romelhc95/studiamatch/pulls/${number}/reviews`, MAX_REVIEW_PAGES, 999, "reviews");
  }

  getPullRequest(number) {
    return this.request("GET", `/repos/romelhc95/studiamatch/pulls/${number}`);
  }

  async findMatchingCheckRuns(headSha, appId, externalId) {
    const found = [];
    for (let page = 1; page <= 5; page += 1) {
      const result = await this.request(
        "GET",
        `/repos/romelhc95/studiamatch/commits/${headSha}/check-runs?filter=all&check_name=${encodeURIComponent("Protected Workflow Integrity")}&per_page=${MAX_PAGE_SIZE}&page=${page}`,
      );
      if (!result || !Array.isArray(result.check_runs)) throw pwiError("check_runs_response_invalid");
      for (const run of result.check_runs) {
        if (run?.app?.id === Number(appId) && run.external_id === externalId) found.push(run);
      }
      if (result.check_runs.length < MAX_PAGE_SIZE) return found;
      if (found.length > MAX_MATCHING_CHECK_RUNS) throw pwiError("duplicate_check_limit_reached");
    }
    throw pwiError("check_runs_pagination_truncated");
  }

  async patchCheckRun(runId, headSha, body) {
    const updated = await this.request("PATCH", `/repos/romelhc95/studiamatch/check-runs/${runId}`, body);
    if (updated?.id !== runId || updated.head_sha !== headSha || updated.status !== body.status ||
        (body.status === "completed" && updated.conclusion !== body.conclusion)) {
      throw pwiError("updated_check_run_invalid");
    }
    return updated;
  }

  async beginCheckVerification({ headSha, appId, prNumber, hasSupersedingEvent }) {
    const externalId = checkRunExternalId(prNumber);
    const existing = await this.findMatchingCheckRuns(headSha, appId, externalId);
    if (existing.length > 1) throw pwiError("duplicate_check_runs");
    if (existing.some((run) => !Number.isSafeInteger(run.id) || run.head_sha !== headSha)) {
      throw pwiError("existing_check_run_invalid");
    }

    const pendingBody = {
      name: "Protected Workflow Integrity",
      external_id: externalId,
      status: "in_progress",
      started_at: new Date(this.now()).toISOString(),
      output: {
        title: "Protected Workflow Integrity",
        summary: "PWI is processing the current event queue; the result is pending.",
      },
    };
    for (const run of existing) {
      await this.patchCheckRun(run.id, headSha, pendingBody);
    }
    return !hasSupersedingEvent?.();
  }

  async publishCheck({ headSha, appId, prNumber, conclusion, summary, hasSupersedingEvent }) {
    const externalId = checkRunExternalId(prNumber);
    const timestamp = new Date(this.now()).toISOString();
    const pendingBody = {
      name: "Protected Workflow Integrity",
      external_id: externalId,
      status: "in_progress",
      started_at: timestamp,
      output: {
        title: "Protected Workflow Integrity",
        summary: "PWI is processing the current event queue; the result is pending.",
      },
    };
    const completedBody = {
      ...pendingBody,
      status: "completed",
      conclusion,
      completed_at: timestamp,
      output: { title: "Protected Workflow Integrity", summary },
    };
    const existing = await this.findMatchingCheckRuns(headSha, appId, externalId);
    if (hasSupersedingEvent?.()) return false;
    if (existing.length > 1) throw pwiError("duplicate_check_runs");
    let runIds;
    if (existing.length === 0) {
      const created = await this.request("POST", "/repos/romelhc95/studiamatch/check-runs", {
        ...pendingBody,
        head_sha: headSha,
      });
      if (!Number.isSafeInteger(created?.id) || created.head_sha !== headSha || created.status !== "in_progress") {
        throw pwiError("created_check_run_invalid");
      }
      runIds = [created.id];
    } else if (existing.some((run) => !Number.isSafeInteger(run.id) || run.head_sha !== headSha)) {
      throw pwiError("existing_check_run_invalid");
    } else {
      runIds = existing.map((run) => run.id);
    }

    const patchRun = (runId, body) => this.patchCheckRun(runId, headSha, body);
    const reopenAll = async () => {
      for (const runId of runIds) await patchRun(runId, pendingBody);
    };

    if (existing.length > 0) await reopenAll();
    if (hasSupersedingEvent?.()) return false;

    for (const runId of runIds) {
      if (hasSupersedingEvent?.()) return false;
      await patchRun(runId, completedBody);
      if (hasSupersedingEvent?.()) {
        await reopenAll();
        return false;
      }
    }
    return true;
  }
}
