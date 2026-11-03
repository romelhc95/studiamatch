# Protected Workflow Integrity verifier

This Worker evaluates pull requests targeting `desarrollo` in `romelhc95/studiamatch` and publishes a `Protected Workflow Integrity` check from its GitHub App. Whether branch protection requires this App's check is a separate setting and must be verified after configuration. A SQLite-backed Durable Object keyed by repository and PR serializes review events for that PR. It persists only a normalized delivery UUID, PR number, head SHA, state, attempt count and timestamps; it does not persist webhook payloads, file lists, reviews, user details, tokens or secrets. The queue is capped at eight outstanding events. At capacity, the Worker reads the API-confirmed current head and deterministically displaces one row: a different SHA first, then `pending` before `processing`, then the oldest sequence. The displaced row becomes terminal `failed` and remains available for bounded manual redelivery if it later remains relevant. Network I/O does not run inside `blockConcurrencyWhile`.

The coordinator also serializes Check Run lookup, pre-ack invalidation, publication and compensation writes. A webhook waits at most 7.5 seconds for the matching operation; if the prior write does not finish in time, the event stays queued and the Worker responds `503` so GitHub can redeliver it. Only one matching App Check Run may be mutated for a PR/SHA; if GitHub reports duplicates, PWI fails closed without modifying them.

It reads only pull request metadata, changed filenames, and review submissions. It never fetches file contents, runs pull request code, or accepts API destinations from a webhook. The webhook must have a valid HMAC signature. Verification failures never publish a new successful check. If the immediate check-invalidation request cannot be confirmed, the endpoint schedules the persisted event for the existing bounded Durable Object alarm retries and returns `503`; the delivery remains unacknowledged and must be redelivered after recovery. If alarm scheduling also fails, the endpoint still returns `503`. The old check may remain visible until an API retry succeeds, so a failed precheck remains an operational NO-GO and must never be overridden manually. The branch still requires its independent native human-review rule and the App check.

## Local checks

The Worker runtime has no external dependencies. Its Node unit tests use the built-in test runner, and a second suite runs inside Cloudflare's local Workers runtime to exercise the real Durable Object SQLite queue, alarm scheduling and slow event processing:

```sh
npm run check
npm test
npm run test:runtime
```

Run all checks inside the approved Docker environment. Install the pinned test tools with `npm ci --legacy-peer-deps`, then run `npm run check`, `npm test`, and `npm run test:runtime`. The runtime suite uses Cloudflare's Workers Vitest plugin and runs the queue in the actual local Workers runtime with a synthetic delayed verification task. The Node suite covers the GitHub API request and failure behavior with synthetic PRs, reviews, keys, and responses; no Cloudflare or GitHub account is contacted.

## Runtime configuration

Non-secret Worker variables:

- `GITHUB_APP_ID`: numeric ID shown in the GitHub App settings.
- `GITHUB_INSTALLATION_ID`: numeric installation ID for this repository only.

Encrypted Worker secrets, entered through the Cloudflare secret manager:

- `GITHUB_APP_PRIVATE_KEY`: the App's PEM private key.
- `GITHUB_WEBHOOK_SECRET`: the webhook secret configured for the App.

Never put either value in this repository, a GitHub Actions secret, a command line, or a chat message. Use the same generated webhook secret in the GitHub App and Worker secret manager.

The App should be installed only on `romelhc95/studiamatch`, with `Pull requests: read` and `Checks: write`; repository metadata read is automatic. Subscribe only to `pull_request`, `pull_request_review`, and `check_run` so the Worker can re-evaluate a check when GitHub requests a rerun. Do not grant Contents, Actions, branch-protection, bypass, or administration permissions.

Webhook URL path: `/webhooks/github`. Health check path: `/healthz`.

## Operational limits

- Fixed GitHub API origin and repository allowlist.
- Only base branch `desarrollo` is evaluated.
- Maximum 2,999 changed-file records and 999 review records; pagination truncation fails closed.
- Webhook body limited to 128 KiB; the internal queue message is limited to 4 KiB; GitHub API response bodies limited to 1 MB. On a new event below capacity, the coordinator first persists the normalized row, then attempts to reopen any matching App check as `in_progress` within a 7.5-second deadline, then schedules the alarm. It returns `202` only after those steps succeed. If the API precheck fails, the existing persisted event is scheduled before returning `503` and receives the same maximum three alarm attempts as other events; if alarm scheduling also fails, the event is not acknowledged and GitHub must redeliver it.
- When the queue is full, the Worker first reads only the PR number, base branch and current head SHA from GitHub, then invalidates the existing PWI check for that API-confirmed SHA. It replaces at most one eligible active row with the newest delivery for that SHA, keeping the pending/processing count at eight. Victim selection prefers a different SHA, then a matching SHA; within each group it prefers `pending` over recovered `processing`, then the oldest sequence. The displaced row becomes terminal `failed` with its delivery, SHA, attempts and received time preserved. A redelivery of an existing terminal `failed` row also reads and validates current PR metadata when it arrives below capacity; it reuses that row at a fresh monotonic sequence with the API-confirmed SHA before pre-ACK invalidation. If a same-delivery row was active when the current-head read began but its alarm completes it as `done` while GitHub is responding, the coordinator reuses that same row, assigns a fresh sequence and requeues it for the API-confirmed SHA; it never inserts a duplicate delivery. Processing completion is conditional on the same sequence, status and attempt so a displaced row cannot overwrite its successor. The event is scheduled and returns `202` only if precheck succeeds. If precheck or scheduling fails, the response is `503`; a persisted current-SHA event still gets the bounded alarm retries. Terminal rows are retained within the 100-row limit.
- If the API cannot be reached, it cannot invalidate GitHub's prior check state; an old success may remain visible until a later retry succeeds. That state is operational NO-GO and must never be overridden manually. GitHub recommends a 2xx response within ten seconds.
- Pre-acknowledgement invalidation, R3/R3-DO and the exact R5 queue/Check Run package `/tmp/h3req1_pwi_r3_queue_serialization_jit_delta_20261019_r5.md` are approved but unconsumed. The added below-capacity metadata read and reactivation of a terminal failed row are described only by `/tmp/h3req1_pwi_r3_failed_row_redelivery_jit_delta_20261020_r6.md`, which is approved for the exact below-capacity failed-row redelivery delta and remains unconsumed. The App check must be required only for `desarrollo` as separately authorized; preserve all existing checks and review rules. Do not deploy until z24 passes its local gates and the exact final Worker code receives independent review.
- Each PR Durable Object stores only a delivery UUID, PR number, head SHA, state, attempt count and timestamps in SQLite. It never persists webhook payloads, reviews, user details, diffs, tokens or secrets.
- The per-PR queue admits at most eight pending/processing events. A new event for the API-confirmed current SHA takes an active slot according to the documented victim order, including same-SHA rows when required. An alarm processes one event at a time; processing is limited to three attempts total with 1-second and 4-second delays. At most 100 completed/failed rows are retained for deduplication and diagnosis.
- Before acknowledging a webhook, and again at the start of processing each event, the Worker reopens any existing check from this App for the same PR and SHA as `in_progress`, before reading the pull request, files or reviews. An active same-delivery redelivery uses the SHA stored in its row; a terminal `failed` redelivery first confirms the current PR head and persists that SHA in the same row. This prevents an older payload SHA from leaving a current successful check visible. The Worker then rechecks the queue immediately before publishing a conclusion. If another event has arrived, the old event leaves the check pending for the next event to re-read current state; it cannot restore an earlier success. A row already `done` before delivery remains idempotent; only a row that transitions from active to `done` during the awaited full-queue head lookup is requeued by that request.
- `blockConcurrencyWhile()` is used only to create the SQLite table during initialization. It is never held across external network I/O. Alarm execution is guarded per Durable Object instance; a processing lease prevents a recovered row from being selected before its bounded expiry. A terminal failed delivery requires bounded manual redelivery; no application retries continue beyond the declared limit.
- Each GitHub API invocation is bounded at 25 seconds; a delivery that cannot be processed remains failed/pending and does not produce a successful PWI check.
- One initial API attempt plus at most three retries, and only for HTTP 429 or 5xx.
- No secrets or raw webhook/API response bodies are logged.
