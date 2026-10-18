jit=H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S8-VALIDATION-DIAGNOSTIC
manifest-sha256=d3500ba707ebd666f4bcb61d01e625ad325c3c269eda8078a6cb4f61fa209c3f
runner-sha256=2113a49686494357586c31e4e3031f3209986a64ac78498501274ea1c61a5ff4
# H3REQ1 C03 startup smoke S8 — Miniflare validation-field diagnostic from verified S3 resources

scope=Pages/workerd startup and healthz diagnostic; reused S3 snapshot/dependency volumes; no egress, DB, PostgREST, Edge, SQL, Auth, email, credentials, or remotes
tests/h3req1-c03-startup-source-s1-v3.sha256: OK
tests/h3req1_c03_startup_output_filter_s8.sh: OK
tests/h3req1_c03_startup_runtime_probe_s8.mjs: OK
tests/h3req1_c03_startup_smoke_s8.sh: OK
tests/h3req1_c03_startup_validation_preload_s8.cjs: OK
phase=s3-resources|error_code=OK
phase=s3-network-id-resolution|error_code=OK
phase=runtime-output-filter-synthetic|error_code=PASS
phase=runtime-diagnostic-synthetic|error_code=PASS
phase=runtime-diagnostic-synthetic|error_code=PASS
runtime-stage=dependency-roots-present
runtime-stage=miniflare-constructor-validation
runtime-validation-issue=scope:shared|index:na|path:log|code:custom|keys:none
runtime-last-stage=miniflare-constructor-validation
healthz=NO-GO reason=runtime-not-ready attempts=3
runtime-exit=code:1 signal:none
runtime-output-sanitization=allowlisted-events-only
bounded-stop=completed container=h3req1-c03-startup-runtime-20261010-s8 owner=verified; resource preserved
bounded-stop=completed container=h3req1-c03-startup-runtime-20261010-s8; resource preserved
Startup continuation halted phase=one-shot-pages-workerd-runtime-healthz exit=1; preserve all S3 resources.
container=h3req1-c03-startup-runtime-20261010-s8 state=exited|1|false network=internal-s3
NO-GO: Pages/workerd startup runtime failed
Startup continuation halted phase=one-shot-pages-workerd-runtime-healthz exit=1; preserve all S3 resources.
