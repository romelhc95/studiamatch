#!/usr/bin/env node
"use strict";

const { TextDecoder } = require("node:util");
const { EventEmitter } = require("node:events");

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
    if (path.startsWith("/validation/web/src/")) groups.web_source += 1;
    else if (path.startsWith("/validation/web/.next/")) groups.next_generated += 1;
    else if (path.startsWith("/validation/web/functions/")) groups.functions += 1;
    else if (path.startsWith("/validation/web/app/")) groups.app += 1;
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

function summarizeBytes(buffer) {
  if (buffer.length > MAX_BYTES) return { error: "OUTPUT_LIMIT" };
  let config;
  try {
    const text = new TextDecoder("utf-8", { fatal: true }).decode(buffer);
    config = JSON.parse(text);
  } catch {
    return { error: "CONFIG_OUTPUT_INVALID" };
  }
  const lines = normalize(config);
  return lines === null ? { error: "CONFIG_SHAPE_INVALID" } : { lines };
}

function selfTest() {
  const sample = {
    files: [
      "/validation/web/src/page.tsx",
      "/validation/web/src/page.tsx",
      "/validation/web/.next/types/app.d.ts",
      "/validation/web/functions/admin.ts",
      "/validation/web/functions/src/edge.ts",
      "/validation/web/app/route.ts",
      "/validation/workers/src/task.ts",
      "/validation/web/node_modules/pkg/src/index.d.ts",
      "/validation/web2/src/not-web.ts",
    ],
    include: [".next/types/**/*.ts", ".next/types/**/*.ts", "src/**/*.tsx"],
  };
  const expected = [
    "phase=tsc-config|error_code=OK",
    "metrics=files=9|unique_files=8|duplicate_paths=1|include_count=3|duplicate_includes=1|web_source=1|next_generated=1|functions=2|app=1|other=3",
  ];
  const validJson = Buffer.from(JSON.stringify(sample), "utf8");
  const valid = summarizeBytes(validJson);
  const invalidUtf8 = summarizeBytes(Buffer.from([0xc3, 0x28]));
  const invalidJson = summarizeBytes(Buffer.from("{", "utf8"));
  const invalidShape = summarizeBytes(Buffer.from('{"files":[],"include":"bad"}', "utf8"));
  const tooLarge = summarizeBytes(Buffer.alloc(MAX_BYTES + 1, 0x20));
  const failingStream = new EventEmitter();
  let streamError;
  consumeInput(failingStream, (result) => { streamError = result.error; });
  failingStream.emit("error", new Error("synthetic input failure"));

  return valid.lines?.join("\n") === expected.join("\n") &&
    invalidUtf8.error === "CONFIG_OUTPUT_INVALID" &&
    invalidJson.error === "CONFIG_OUTPUT_INVALID" &&
    invalidShape.error === "CONFIG_SHAPE_INVALID" &&
    tooLarge.error === "OUTPUT_LIMIT" &&
    streamError === "PROCESS_INPUT_FAILED";
}

function reportError(errorCode) {
  if (process.exitCode !== undefined && process.exitCode !== 0) return;
  process.exitCode = 1;
  console.log("phase=tsc-config|error_code=" + errorCode);
}

function consumeInput(stream, onResult) {
  const chunks = [];
  let bytes = 0;
  let finished = false;
  const finish = (result) => {
    if (finished) return;
    finished = true;
    onResult(result);
  };

  stream.on("error", () => finish({ error: "PROCESS_INPUT_FAILED" }));
  stream.on("data", (chunk) => {
    if (finished) return;
    bytes += chunk.length;
    if (bytes > MAX_BYTES) {
      finish({ error: "OUTPUT_LIMIT" });
      if (typeof stream.destroy === "function") stream.destroy();
      return;
    }
    chunks.push(chunk);
  });
  stream.on("end", () => {
    if (!finished) finish(summarizeBytes(Buffer.concat(chunks, bytes)));
  });
}

if (process.argv[2] === "--self-test") {
  if (selfTest()) {
    console.log("phase=tsc-config-synthetics|error_code=OK");
    process.exitCode = 0;
  } else {
    console.log("phase=tsc-config-synthetics|error_code=SYNTHETIC_TESTS_FAILED");
    process.exitCode = 1;
  }
} else {
  consumeInput(process.stdin, (result) => {
    if (result.error) {
      reportError(result.error);
      return;
    }
    for (const line of result.lines) console.log(line);
  });
}
