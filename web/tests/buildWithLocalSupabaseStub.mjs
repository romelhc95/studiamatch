import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import http from "node:http";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { stripVTControlCharacters } from "node:util";
import { fileURLToPath } from "node:url";

const webDir = dirname(dirname(fileURLToPath(import.meta.url)));
const expectedApikey = "sb_publishable_ci_test";
const allowedColdCiBuildWarning = "⚠ No build cache found. Please configure build caching for faster rebuilds. Read more: https://nextjs.org/docs/messages/no-cache";
const coursePublicFields = "id,name,slug,url,institution_id,price_pen,price_status,mode,course_type,category_id,duration,start_date_text,description_long,syllabus,target_audience,requirements,certification,benefits,objectives,expected_monthly_salary,seniority_level,roi_months,address,region,is_active,is_verified,brochure_url,start_date,created_at,updated_at";

const institution = {
  id: "10000000-0000-0000-0000-000000000001",
  name: "PUCP",
  slug: "pucp",
};

const course = {
  id: "00000000-0000-0000-0000-000000000001",
  name: "Estudios Generales",
  slug: "estudios-generales",
  url: "https://example.edu/programa/estudios-generales",
  institution_id: institution.id,
  price_pen: 1000,
  price_status: "published",
  mode: "Remoto",
  course_type: "Curso",
  category_id: "20000000-0000-0000-0000-000000000001",
  duration: "3 meses",
  start_date_text: "Consultar",
  category: "Tecnologia",
  description_long: "Programa publico de prueba para build local.",
  syllabus: "Modulo 1\nModulo 2",
  target_audience: "Personas interesadas en tecnologia.",
  requirements: "Conocimientos basicos.",
  is_active: true,
  is_verified: true,
  roi_months: 2.5,
  expected_monthly_salary: 4500,
  institutions: { name: institution.name, slug: institution.slug },
  categories: { name: "Tecnologia" },
};

const allowedResponses = new Map([
  [
    `/rest/v1/courses?is_active=eq.true&is_verified=eq.true&select=${coursePublicFields},categories(name),institutions(name,slug)&order=created_at.desc`,
    [course],
  ],
  ["/rest/v1/institutions?select=id,name,slug", [institution]],
  [
    "/rest/v1/courses?select=slug,url,institutions(slug)&is_active=eq.true&is_verified=eq.true",
    [{ slug: course.slug, url: course.url, institutions: { slug: institution.slug } }],
  ],
  [
    "/rest/v1/courses?select=name,description_long,url,price_pen,mode,course_type,institutions(name)&slug=eq.estudios-generales&is_active=eq.true&is_verified=eq.true&limit=1",
    [{ ...course, institutions: { name: institution.name } }],
  ],
]);
const requiredSignatures = new Set(allowedResponses.keys());
const seenSignatures = new Set();
let failure = null;
let expectedHost = "";

function json(response, status, body) {
  response.writeHead(status, {
    "content-type": "application/json",
    "access-control-allow-origin": "*",
    "access-control-allow-headers": "apikey, content-type, prefer",
    "access-control-allow-methods": "GET",
  });
  response.end(JSON.stringify(body));
}

function reject(response, status, message) {
  failure = failure || message;
  json(response, status, { error: message });
}

const server = http.createServer((request, response) => {
  const url = new URL(request.url || "/", "http://127.0.0.1");
  const signature = `${url.pathname}${url.search}`;

  if (request.headers.host !== expectedHost) {
    reject(response, 400, `unexpected host ${request.headers.host || ""}`);
    return;
  }
  if (request.method !== "GET") {
    reject(response, 405, `unexpected method ${request.method} ${url.pathname}`);
    return;
  }
  if (request.headers.authorization) {
    reject(response, 400, `authorization header is forbidden on ${url.pathname}`);
    return;
  }
  if (request.headers.apikey !== expectedApikey) {
    reject(response, 401, `unexpected apikey on ${url.pathname}`);
    return;
  }
  if (request.headers["content-length"] || request.headers["transfer-encoding"]) {
    reject(response, 400, `request body is forbidden on ${url.pathname}`);
    return;
  }
  if (
    url.pathname.includes("leads") ||
    url.pathname.includes("email_log") ||
    url.pathname.includes("send-lead-emails") ||
    url.pathname.startsWith("/functions/v1")
  ) {
    reject(response, 410, `forbidden lead/email endpoint ${url.pathname}`);
    return;
  }
  if (!allowedResponses.has(signature)) {
    reject(response, 404, `unexpected signature ${signature}`);
    return;
  }

  seenSignatures.add(signature);
  json(response, 200, allowedResponses.get(signature));
});

function configuredSupabaseTestOrigin() {
  const raw = process.env.SUPABASE_TEST_ORIGIN || "http://127.0.0.1:54321";
  const parsed = new URL(raw);
  assert.equal(parsed.protocol, "http:");
  assert.equal(parsed.hostname, "127.0.0.1");
  assert.ok(parsed.port, "SUPABASE_TEST_ORIGIN must include a port");
  assert.equal(parsed.username, "");
  assert.equal(parsed.password, "");
  assert.ok(parsed.pathname === "" || parsed.pathname === "/");
  assert.equal(parsed.search, "");
  assert.equal(parsed.hash, "");
  const port = Number(parsed.port);
  assert.ok(Number.isInteger(port) && port > 0 && port <= 65535, "SUPABASE_TEST_ORIGIN port must be valid");
  return { origin: `http://127.0.0.1:${port}`, port };
}

function listen(port) {
  return new Promise((resolve) => {
    server.listen(port, "127.0.0.1", () => resolve(server.address()));
  });
}

function close() {
  return new Promise((resolve, rejectClose) => {
    server.close((error) => (error ? rejectClose(error) : resolve()));
  });
}

function writeNetworkGuard() {
  const directory = mkdtempSync(join(tmpdir(), "studiamatch-net-guard-"));
  const guardPath = join(directory, "guard.cjs");
  writeFileSync(
    guardPath,
    String.raw`
const net = require("node:net");
const tls = require("node:tls");
const http = require("node:http");
const https = require("node:https");

function hostFromNetArgs(args) {
  const first = args[0];
  if (typeof first === "object" && first !== null) return first.host || first.hostname || "127.0.0.1";
  if (typeof args[1] === "string") return args[1];
  return "127.0.0.1";
}

function hostFromRequestArgs(args) {
  const first = args[0];
  if (typeof first === "string" || first instanceof URL) return new URL(first).hostname;
  if (typeof first === "object" && first !== null) return first.hostname || first.host || "127.0.0.1";
  return "127.0.0.1";
}

function assertLoopback(host) {
  const normalized = String(host || "").replace(/^\[|\]$/g, "").split(":")[0];
  if (normalized !== "127.0.0.1" && normalized !== "::1") {
    throw new Error("TEST-NET blocked non-loopback destination before DNS/TCP: " + normalized);
  }
}

const originalNetConnect = net.connect;
net.connect = net.createConnection = function guardedNetConnect(...args) {
  assertLoopback(hostFromNetArgs(args));
  return originalNetConnect.apply(this, args);
};

const originalTlsConnect = tls.connect;
tls.connect = function guardedTlsConnect(...args) {
  assertLoopback(hostFromNetArgs(args));
  return originalTlsConnect.apply(this, args);
};

for (const module of [http, https]) {
  const originalRequest = module.request;
  const originalGet = module.get;
  module.request = function guardedRequest(...args) {
    assertLoopback(hostFromRequestArgs(args));
    return originalRequest.apply(this, args);
  };
  module.get = function guardedGet(...args) {
    assertLoopback(hostFromRequestArgs(args));
    return originalGet.apply(this, args);
  };
}

if (typeof globalThis.fetch === "function") {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async function guardedFetch(input, init) {
    const url = input instanceof URL ? input : new URL(typeof input === "string" ? input : input.url);
    assertLoopback(url.hostname);
    return originalFetch(input, init);
  };
}
`,
    "utf8",
  );
  return { directory, guardPath };
}

function buildEnvironment(origin, guardPath) {
  const inheritedKeys = ["CI", "HOME", "PATH", "TERM", "TMPDIR", "USER", "SHELL"];
  const env = Object.fromEntries(
    inheritedKeys
      .filter((key) => process.env[key])
      .map((key) => [key, process.env[key]]),
  );
  const nodeOptions = [process.env.NODE_OPTIONS, `--require=${guardPath}`].filter(Boolean).join(" ");

  return {
    ...env,
    NODE_OPTIONS: nodeOptions,
    NEXT_PUBLIC_SUPABASE_URL: origin,
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: expectedApikey,
    NEXT_PUBLIC_LEAD_CAPTURE_ENABLED: "true",
    NEXT_TELEMETRY_DISABLED: "1",
  };
}

function runNodeCanary(guardPath) {
  return new Promise((resolve, rejectRun) => {
    const child = spawn(
      process.execPath,
      [
        "-e",
        "fetch('https://example.com').then(() => process.exit(1)).catch((error) => process.exit(String(error).includes('TEST-NET blocked') ? 0 : 2));",
      ],
      {
        cwd: webDir,
        env: { ...process.env, NODE_OPTIONS: `--require=${guardPath}` },
        stdio: "pipe",
      },
    );
    child.on("error", rejectRun);
    child.on("exit", (code) => {
      if (code === 0) resolve();
      else rejectRun(new Error(`TEST-NET canary failed with exit code ${code}`));
    });
  });
}

function diagnosticLines(text) {
  return stripVTControlCharacters(text)
    .split(/\r?\n/)
    .filter((line) => /(^|\s|[>])(?:warning|warn|error|failed|failure|ERR!|⚠)/i.test(line));
}

function classifyBuildOutput(code, stdout, stderr) {
  const output = `${stdout}\n${stderr}`;
  if (code !== 0) {
    return { ok: false, message: `npm run build failed with exit code ${code}\n${output}` };
  }

  const stderrDiagnostics = diagnosticLines(stderr);
  if (stderrDiagnostics.length > 0) {
    return {
      ok: false,
      message: `unexpected build warning/error output:\n${stderrDiagnostics.join("\n")}`,
    };
  }

  let allowedWarnings = 0;
  const unexpected = [];
  for (const line of diagnosticLines(stdout)) {
    if (line === allowedColdCiBuildWarning) {
      allowedWarnings += 1;
    } else {
      unexpected.push(line);
    }
  }
  if (allowedWarnings > 1) {
    unexpected.push(allowedColdCiBuildWarning);
  }
  if (unexpected.length > 0) {
    return {
      ok: false,
      message: `unexpected build warning/error output:\n${unexpected.join("\n")}`,
    };
  }
  return { ok: true, output };
}

function runBuildOutputSelfTests() {
  assert.equal(classifyBuildOutput(0, `${allowedColdCiBuildWarning}\n`, "").ok, true);
  assert.equal(
    classifyBuildOutput(0, `\u001b[33m${allowedColdCiBuildWarning}\u001b[0m\r\n`, "").ok,
    true,
  );
  assert.equal(classifyBuildOutput(0, "", `${allowedColdCiBuildWarning}\n`).ok, false);
  assert.equal(classifyBuildOutput(0, `${allowedColdCiBuildWarning}.\n`, "").ok, false);
  assert.equal(
    classifyBuildOutput(0, `${allowedColdCiBuildWarning}\n${allowedColdCiBuildWarning}\n`, "").ok,
    false,
  );
  assert.equal(classifyBuildOutput(0, `${allowedColdCiBuildWarning}\nError: extra\n`, "").ok, false);
  assert.equal(classifyBuildOutput(0, "compiled cleanly\n", "").ok, true);
  assert.equal(classifyBuildOutput(1, "compiled cleanly\n", "").ok, false);
}

function runBuild(origin, guardPath) {
  return new Promise((resolve, rejectRun) => {
    const child = spawn("npm", ["run", "build"], {
      cwd: webDir,
      stdio: "pipe",
      env: buildEnvironment(origin, guardPath),
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", rejectRun);
    child.on("close", (code) => {
      const result = classifyBuildOutput(code, stdout, stderr);
      if (!result.ok) {
        rejectRun(new Error(result.message));
        return;
      }
      resolve(result.output);
    });
  });
}

runBuildOutputSelfTests();

const { directory: guardDirectory, guardPath } = writeNetworkGuard();
const configuredOrigin = configuredSupabaseTestOrigin();
const address = await listen(configuredOrigin.port);
assert.equal(address.address, "127.0.0.1");
assert.equal(address.port, configuredOrigin.port);
const origin = configuredOrigin.origin;
expectedHost = `127.0.0.1:${configuredOrigin.port}`;

try {
  await runNodeCanary(guardPath);
  await runBuild(origin, guardPath);
  assert.equal(failure, null);
  for (const signature of requiredSignatures) {
    assert.ok(seenSignatures.has(signature), `build did not request allowed signature: ${signature}`);
  }
  assert.ok(existsSync(join(webDir, "out")), "static export out/ must exist");
} finally {
  await close();
  rmSync(guardDirectory, { recursive: true, force: true });
}
