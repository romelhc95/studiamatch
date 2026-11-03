jit=H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S9-VALIDATION-DIAGNOSTIC
manifest-sha256=d9e51fd2487edcff096ee630de2ed9d1f30b7de323a79cbfae9d60516c3d3bf4
runner-sha256=9e8019f686b50835cf3c14f6d29cbdf8c45db305eb3c95fe5365103f2da2d19f
# H3REQ1 C03 startup smoke S9 — Pages/workerd healthz from the verified S12 candidate snapshot

scope=Pages/workerd startup and healthz only; candidate source volume S12 plus S3 tools/pages dependency volumes; internal network without egress; no DB, PostgREST, Edge, SQL, Auth, email, credentials, or remotes
dependency-inputs=compatible|package-locks=unchanged|source-delta=integrated-runtime-only
tests/h3req1-c03-startup-source-s1-v3.sha256: OK
tests/h3req1-c03-startup-source-s1-v4.sha256: OK
tests/h3req1_c03_startup_output_filter_s8.sh: OK
tests/h3req1_c03_startup_runtime_probe_s8.mjs: OK
tests/h3req1_c03_startup_smoke_s9.sh: OK
tests/h3req1_c03_startup_validation_preload_s8.cjs: OK
s12-snapshot=PASS|files=14|hashes=13/13|symlinks=0|permissions=exact|network=none|mount=readonly
phase=s12-candidate-snapshot|error_code=OK
phase=s3-resources|error_code=OK
phase=s3-network-id-resolution|error_code=OK
phase=runtime-output-filter-synthetic|error_code=PASS
phase=runtime-diagnostic-synthetic|error_code=PASS
phase=runtime-diagnostic-synthetic|error_code=PASS
runtime-stage=dependency-roots-present
runtime-stage=runtime-ready
healthz=PASS workerd=true attempts=5
runtime-exit=code:0 signal:none
smoke=PASS workerd-pages-healthz=true edge-runtime=not-started database=not-started
runtime-output-sanitization=allowlisted-events-only
container=h3req1-c03-startup-runtime-20261010-s9 state=exited|0|false network=internal-s3
phase=pages-workerd-healthz|error_code=OK
exit=0
Startup continuation: PASS (fresh real Miniflare/workerd Pages workers only).
S3 snapshot/dependency volumes and internal network remain preserved; no cleanup was performed.
Sanitized evidence: .context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s9.md
