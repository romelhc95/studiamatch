import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const testsDir = dirname(fileURLToPath(import.meta.url));
const webDir = dirname(testsDir);
const rootDir = dirname(webDir);
const outDir = join(webDir, "out");
const sourceDir = join(webDir, "src");

assert.ok(existsSync(outDir), "static export out/ must exist");

function* filesByExtension(dir, extensions) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!["node_modules", ".next", "out"].includes(entry.name)) {
        yield* filesByExtension(fullPath, extensions);
      }
    } else if (extensions.some((extension) => entry.name.endsWith(extension))) {
      yield fullPath;
    }
  }
}

function readAll(files) {
  return Array.from(files, (file) => readFileSync(file, "utf8")).join("\n");
}

function routeText(...segments) {
  const path = join(outDir, ...segments);
  assert.ok(existsSync(path), `static route must exist: ${segments.join("/")}`);
  return readFileSync(path, "utf8");
}

async function assertEdgeTombstone() {
  const edgePath = join(rootDir, "supabase", "functions", "send-lead-emails", "index.ts");
  const source = readFileSync(edgePath, "utf8").replace(/^import .*?;\s*/s, "");
  let capturedHandler = null;
  let requestAccesses = 0;
  let envAccesses = 0;
  let fetchCalls = 0;
  const context = {
    Response,
    Deno: {
      serve(handler) {
        capturedHandler = handler;
      },
      env: new Proxy({}, {
        get() {
          envAccesses += 1;
          throw new Error("Deno.env must not be read");
        },
      }),
    },
    fetch() {
      fetchCalls += 1;
      throw new Error("fetch must not be called");
    },
  };
  vm.runInNewContext(source, context, { filename: edgePath });
  assert.equal(typeof capturedHandler, "function", "Deno.serve handler must be captured");

  for (const method of ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]) {
    const request = new Proxy({ method }, {
      get(target, property, receiver) {
        requestAccesses += 1;
        return Reflect.get(target, property, receiver);
      },
    });
    const response = await capturedHandler(request);
    assert.equal(response.status, 410, `${method} must return 410`);
    assert.equal(await response.text(), "Gone", `${method} must return Gone`);
    assert.equal(response.headers.get("Content-Type"), "text/plain");
    assert.equal(response.headers.get("Cache-Control"), "no-store");
    assert.equal(response.headers.get("Access-Control-Allow-Origin"), null);
  }

  assert.equal(requestAccesses, 0, "handler must not read request/body");
  assert.equal(envAccesses, 0, "handler must not read Deno.env");
  assert.equal(fetchCalls, 0, "handler must not fetch");
}

const sourceExtensions = [".ts", ".tsx", ".js", ".jsx", ".json", ".css"];
const exportExtensions = [".html", ".js", ".txt", ".json", ".map"];
const frontendSource = readAll(filesByExtension(sourceDir, sourceExtensions));
const exportAssets = readAll(filesByExtension(outDir, exportExtensions));
const sourceAndExport = `${frontendSource}\n${exportAssets}`;

for (const moduleName of [["lead", "Capture.ts"], ["lead", "CaptureCore.ts"]].map((parts) => parts.join(""))) {
  assert.equal(existsSync(join(webDir, "src", "lib", moduleName)), false, `${moduleName} must not exist`);
}

const home = routeText("index.html");
const courses = routeText("courses", "index.html");
const compare = routeText("compare", "index.html");
const privacidad = routeText("privacidad", "index.html");
const terminos = routeText("terminos", "index.html");
const detailRoute = Array.from(filesByExtension(join(outDir, "courses"), [".html"])).find((file) => {
  const parts = relative(outDir, file).split(/[\\/]/);
  return parts.length >= 4 && parts[0] === "courses" && parts.at(-1) === "index.html";
});
assert.ok(detailRoute, "at least one static course detail route must exist");
const detail = readFileSync(detailRoute, "utf8");

const forbiddenFragments = [
  ["NEXT_PUBLIC", "_LEAD_CAPTURE", "_ENABLED"],
  ["/rest/v1", "/leads"],
  ["submit", "Lead"],
  ["data-", "lead-capture"],
  ["data-", "pii-control"],
  ["home-", "lead-"],
  ["detail-", "lead-"],
  ["/functions/v1"],
  ["send-lead-emails"],
  ["email_log"],
  ["/privacy/"],
  ["/terms/"],
];

for (const fragments of forbiddenFragments) {
  const token = fragments.join("");
  assert.equal(sourceAndExport.includes(token), false, `forbidden public token present: ${fragments.join("+")}`);
}

const leadMutationPattern = /fetch\([^)]*\/rest\/v1\/leads[\s\S]{0,300}method\s*:\s*["'`](POST|PUT|PATCH|DELETE)["'`]/;
assert.equal(leadMutationPattern.test(sourceAndExport), false, "lead endpoint must not be mutated");
const piiFieldPattern = /<(input|textarea|select)\b[^>]*(type|name|id|placeholder|aria-label)=["'`][^"'`]*(email|e-mail|phone|tel|whatsapp|nombre|apellido|first_name|last_name)[^"'`]*["'`][^>]*>/i;
assert.doesNotMatch(sourceAndExport, piiFieldPattern);

assert.match(home, /StudIAMatch/);
assert.match(courses, /StudIAMatch|Explorar/);
assert.match(detail, /StudIAMatch|Comparar programa|GENERAL|REQUISITOS/);
assert.match(compare, /StudIAMatch|Comparar/);
assert.match(privacidad, /Pol[ií]tica de Privacidad/);
assert.match(privacidad, /No recopilamos informaci[oó]n personal identificable/);
assert.match(terminos, /T[eé]rminos de Uso/);
assert.match(terminos, /Naturaleza del servicio/);
assert.match(sourceAndExport, /Cat[aá]logo de Programas|Programas que conectan|Explorar Programas/);
assert.match(sourceAndExport, /Comparar programa|GENERAL|REQUISITOS/);
assert.match(sourceAndExport, /Comparativa de Programas/);
assert.match(sourceAndExport, /Ver detalle/);
assert.doesNotMatch(sourceAndExport, /Solicitar Info/);
assert.doesNotMatch(sourceAndExport, /Solicitar Asesor/);

await assertEdgeTombstone();
