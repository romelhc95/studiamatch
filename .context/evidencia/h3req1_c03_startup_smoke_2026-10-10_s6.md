jit=H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S6-DIAGNOSTIC
manifest-sha256=6590fee0612153c22e902b00c378c48803424b56277a1fd1db841e20f10be8ad
runner-sha256=74d7ae4285a27741cc698caa55ff47363e8fd26efbed4c577ca6464bcd40e354
# H3REQ1 C03 startup smoke S6 — diagnostic continuation from verified S3 resources

scope=Pages/workerd startup and healthz only; reused S3 snapshot/dependency volumes; no egress, DB, PostgREST, Edge, SQL, Auth, email, or remotes
.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s5.md: OK
tests/h3req1-c03-startup-smoke-s5.sha256: OK
tests/h3req1_c03_startup_output_filter_s6.sh: OK
tests/h3req1_c03_startup_runtime_probe_s6.mjs: OK
tests/h3req1_c03_startup_smoke_s6.sh: OK
phase=s3-resources|error_code=OK
phase=s3-network-id-resolution|error_code=OK
phase=runtime-output-filter-synthetic|error_code=PASS
phase=runtime-diagnostic-synthetic|error_code=PASS
runtime-stage=dependency-roots-present
runtime-error-class=MINIFLARECOREERROR
runtime-project-frame=line:800:column:3
runtime-last-stage=dependency-roots-present
healthz=NO-GO reason=runtime-not-ready attempts=4
runtime-exit=code:1 signal:none
runtime-output-sanitization=allowlisted-events-only
bounded-stop=completed container=h3req1-c03-startup-runtime-20261010-s6 owner=verified; resource preserved
bounded-stop=completed container=h3req1-c03-startup-runtime-20261010-s6; resource preserved
Startup continuation halted phase=one-shot-pages-workerd-runtime-healthz exit=1; preserve all S3 resources.
container=h3req1-c03-startup-runtime-20261010-s6 state=exited|1|false network=internal-s3
NO-GO: Pages/workerd startup runtime failed
Startup continuation halted phase=one-shot-pages-workerd-runtime-healthz exit=1; preserve all S3 resources.
