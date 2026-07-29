import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const expected = process.argv[2];
assert.ok(
  expected === "enabled" || expected === "disabled" || expected === "unset",
  "expected enabled|disabled|unset",
);

const outDir = new URL("../out", import.meta.url).pathname;
assert.ok(existsSync(outDir), "static export out/ must exist");

function* filesByExtension(dir, extensions) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* filesByExtension(fullPath, extensions);
    } else if (extensions.some((extension) => entry.name.endsWith(extension))) {
      yield fullPath;
    }
  }
}

const html = Array.from(filesByExtension(outDir, [".html"]), (file) =>
  readFileSync(file, "utf8")
).join("\n");
const coursesFallbackHtml = readFileSync(join(outDir, "courses", "index.html"), "utf8");
const assets = Array.from(filesByExtension(outDir, [".html", ".js", ".txt"]), (file) =>
  readFileSync(file, "utf8")
).join("\n");

for (const surface of ["home", "course-detail"]) {
  assert.match(
    html,
    new RegExp(`data-lead-capture-server-marker="${surface}"[^>]*data-lead-capture-state="${expected}"`),
  );
}

assert.match(
  coursesFallbackHtml,
  new RegExp(`data-lead-capture-server-marker="course-detail"[^>]*data-lead-capture-state="${expected}"`),
);

if (expected !== "enabled") {
  // Next can CSR-bail out client components, so static HTML must fail closed.
  assert.doesNotMatch(html, /data-lead-capture-form=/);
  assert.doesNotMatch(html, /data-pii-control=/);
} else {
  assert.match(assets, /data-lead-capture-state/);
  assert.match(assets, /data-lead-capture-form/);
  assert.match(assets, /data-pii-control/);
}
