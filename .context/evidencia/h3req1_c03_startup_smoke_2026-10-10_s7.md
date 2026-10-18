jit=H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S7-PACKAGE-DIAGNOSTIC
manifest-sha256=21a2237d77d2e77e84f4e2341f0ec02cf063b4383f9e49fb11728e6044d54eee
runner-sha256=2770cf0fc5f9b2115aee0ac23502dbdfe921590b082fed699da372b42c176244
# H3REQ1 C03 startup smoke S7 — Miniflare package-frame diagnostic from verified S3 resources

scope=Pages/workerd startup and healthz only; reused S3 snapshot/dependency volumes; no egress, DB, PostgREST, Edge, SQL, Auth, email, or remotes
.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s6.md: OK
tests/h3req1-c03-startup-smoke-s6.sha256: OK
tests/h3req1_c03_startup_output_filter_s7.sh: OK
tests/h3req1_c03_startup_runtime_probe_s7.mjs: OK
tests/h3req1_c03_startup_smoke_s6.sh: OK
tests/h3req1_c03_startup_smoke_s7.sh: OK
phase=s3-resources|error_code=OK
phase=s3-network-id-resolution|error_code=OK
phase=runtime-output-filter-synthetic|error_code=PASS
phase=runtime-diagnostic-synthetic|error_code=PASS
runtime-stage=dependency-roots-present
runtime-error-code=ERR_VALIDATION
runtime-error-class=MINIFLARECOREERROR
runtime-output-class=unclassified-line-suppressed
runtime-output-class=unclassified-line-suppressed
runtime-project-frame=line:800:column:3
runtime-last-stage=dependency-roots-present
healthz=NO-GO reason=runtime-not-ready attempts=3
runtime-exit=code:1 signal:none
runtime-output-sanitization=allowlisted-events-only
bounded-stop=completed container=h3req1-c03-startup-runtime-20261010-s7 owner=verified; resource preserved
bounded-stop=completed container=h3req1-c03-startup-runtime-20261010-s7; resource preserved
Startup continuation halted phase=one-shot-pages-workerd-runtime-healthz exit=1; preserve all S3 resources.
container=h3req1-c03-startup-runtime-20261010-s7 state=exited|1|false network=internal-s3
NO-GO: Pages/workerd startup runtime failed
Startup continuation halted phase=one-shot-pages-workerd-runtime-healthz exit=1; preserve all S3 resources.
