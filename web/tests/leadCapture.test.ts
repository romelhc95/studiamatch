import assert from "node:assert/strict";
import { test } from "node:test";

import {
  getLeadCaptureBuildState,
  isLeadCaptureEnabled,
  submitLeadToEndpoint,
} from "../src/lib/leadCaptureCore.ts";

const SUPABASE_URL = "http://127.0.0.1:54321";
const PUBLISHABLE_KEY = "sb_publishable_ci_test";

test("lead capture flag fail-closes for every value except exact true", async () => {
  for (const value of [undefined, "", "false", "1", "TRUE", "True", "yes"]) {
    assert.equal(isLeadCaptureEnabled(value), false);
  }

  assert.equal(isLeadCaptureEnabled("true"), true);
});

test("lead capture build state preserves unset while failing closed", async () => {
  assert.equal(getLeadCaptureBuildState("true"), "enabled");
  assert.equal(getLeadCaptureBuildState("false"), "disabled");
  assert.equal(getLeadCaptureBuildState(undefined), "unset");
  assert.equal(getLeadCaptureBuildState("TRUE"), "unset");
});

test("submitLead returns disabled without calling fetch", async () => {
  let calls = 0;
  const fetchImpl = (async () => {
    calls += 1;
    return new Response(null, { status: 204 });
  }) as typeof fetch;

  assert.deepEqual(
    await submitLeadToEndpoint(
      { email: "person@example.test" },
      {
        enabled: false,
        supabaseUrl: SUPABASE_URL,
        publishableKey: PUBLISHABLE_KEY,
        fetchImpl,
      },
    ),
    { status: "disabled" },
  );
  assert.equal(calls, 0);
});

test("submitLead posts exactly the allowed payload with apikey only", async () => {
  const requests: Array<{ url: string; init: RequestInit }> = [];
  const fetchImpl = (async (url: string | URL | Request, init?: RequestInit) => {
    requests.push({ url: String(url), init: init ?? {} });
    return new Response(null, { status: 201 });
  }) as typeof fetch;

  const unsafePayload = {
    first_name: "Ada",
    email: "ada@example.test",
    whatsapp: "+51999999999",
    source_page: "home",
    type: "info",
    course_id: "00000000-0000-0000-0000-000000000001",
    unexpected_column: "blocked",
  } as Record<string, string>;
  const result = await submitLeadToEndpoint(unsafePayload, {
    enabled: true,
    supabaseUrl: SUPABASE_URL,
    publishableKey: PUBLISHABLE_KEY,
    fetchImpl,
  });

  assert.deepEqual(result, { status: "submitted" });
  assert.equal(requests.length, 1);
  assert.equal(requests[0].url, "http://127.0.0.1:54321/rest/v1/leads");
  const headers = requests[0].init.headers as Record<string, string>;
  assert.equal(headers.apikey, "sb_publishable_ci_test");
  assert.equal(headers.Authorization, undefined);
  assert.equal(headers.authorization, undefined);
  assert.deepEqual(JSON.parse(String(requests[0].init.body)), {
    first_name: "Ada",
    email: "ada@example.test",
    whatsapp: "+51999999999",
    source_page: "home",
    type: "info",
    course_id: "00000000-0000-0000-0000-000000000001",
  });
});
