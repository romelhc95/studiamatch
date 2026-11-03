#!/usr/bin/env node
"use strict";

const MAX_BYTES = 1024 * 1024;

function normalize(config) {
  if (!config || typeof config !== "object" || !Array.isArray(config.files) ||
      !Array.isArray(config.include) ||
      !config.files.every((value) => typeof value === "string") ||
      !config.include.every((value) => typeof value === "string")) {
    return null;
  }
  const files = config.files.map((value) => value.replaceAll("\\", "/"));
  const unique = new Set(files);
  const groups = {
    web_source: 0,
    next_generated: 0,
    functions: 0,
    app: 0,
    other: 0,
  };
  for (const path of unique) {
    if (path.includes("/src/")) groups.web_source += 1;
    else if (path.includes("/.next/")) groups.next_generated += 1;
    else if (path.includes("/functions/")) groups.functions += 1;
    else if (path.includes("/app/")) groups.app += 1;
    else groups.other += 1;
  }
  const result = [
    "files=" + files.length,
    "unique_files=" + unique.size,
    "duplicate_paths=" + (files.length - unique.size),
    "include_count=" + config.include.length,
    "duplicate_includes=" + (config.include.length - new Set(config.include).size),
  ];
  for (const name of Object.keys(groups)) result.push(name + "=" + groups[name]);
  return ["phase=tsc-config|error_code=OK", "metrics=" + result.join("|")];
}

function selfTest() {
  const sample = {
    files: [
      "/validation/web/src/page.tsx",
      "/validation/web/src/page.tsx",
      "/validation/web/.next/types/app.d.ts",
      "/validation/web/functions/admin.ts",
      "/validation/web/app/route.ts",
      "/validation/workers/task.ts",
    ],
    include: [".next/types/**/*.ts", ".next/types/**/*.ts", "src/**/*.tsx"],
  };
  const result = normalize(sample);
  return result !== null &&
    result[0] === "phase=tsc-config|error_code=OK" &&
    result[1] === "metrics=files=6|unique_files=5|duplicate_paths=1|include_count=3|duplicate_includes=1|web_source=1|next_generated=1|functions=1|app=1|other=1";
}

if (process.argv[2] === "--self-test") {
  if (selfTest()) {
    console.log("phase=tsc-config-synthetics|error_code=OK");
    process.exit(0);
  }
  console.log("phase=tsc-config-synthetics|error_code=SYNTHETIC_TESTS_FAILED");
  process.exit(1);
}

const chunks = [];
let bytes = 0;
let rejected = false;
process.stdin.on("error", () => {});
process.stdin.on("data", (chunk) => {
  bytes += chunk.length;
  if (bytes > MAX_BYTES) {
    rejected = true;
    console.log("phase=tsc-config|error_code=OUTPUT_LIMIT");
    process.exit(1);
  }
  chunks.push(chunk);
});
process.stdin.on("end", () => {
  if (rejected) return;
  let config;
  try {
    config = JSON.parse(Buffer.concat(chunks, bytes).toString("utf8"));
  } catch {
    console.log("phase=tsc-config|error_code=CONFIG_OUTPUT_INVALID");
    process.exit(1);
  }
  const result = normalize(config);
  if (result === null) {
    console.log("phase=tsc-config|error_code=CONFIG_SHAPE_INVALID");
    process.exit(1);
  }
  console.log(result[0]);
  console.log(result[1]);
});

