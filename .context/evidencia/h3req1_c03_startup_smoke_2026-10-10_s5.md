jit=H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S5-DIAGNOSTIC
manifest-sha256=08a428daf847d690f4f72fdad03379eab4faeeba64362b78762c28e6f9e4ab03
runner-sha256=6e886754cde2c4a3feb998adaea6d8d5ecde03558eae15841e4cdb2c60347fdf
# H3REQ1 C03 startup smoke S5 — diagnostic continuation from verified S3 resources

scope=Pages/workerd startup and healthz only; reused S3 snapshot/dependency volumes; no egress, DB, PostgREST, Edge, SQL, Auth, email, or remotes
.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log: OK
.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d1.log: OK
.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d2.log: OK
.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s3.md: OK
.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s3_diagnosis.md: OK
.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s4.md: OK
.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s4_diagnosis.md: OK
tests/h3req1-c03-integrated-diagnostic-r4-d1.sha256: OK
tests/h3req1-c03-integrated-diagnostic-r4-d2.sha256: OK
tests/h3req1-c03-integrated.sha256: OK
tests/h3req1-c03-startup-smoke-s3-resume-s4.sha256: OK
tests/h3req1-c03-startup-smoke-s3.sha256: OK
tests/h3req1-c03-startup-source-s1-v3.sha256: OK
tests/h3req1_c03_bootstrap_output_filter_s1.mjs: OK
tests/h3req1_c03_integrated_runtime.mjs: OK
tests/h3req1_c03_integrated_runtime_diag_d1.sh: OK
tests/h3req1_c03_integrated_runtime_diag_d2.sh: OK
tests/h3req1_c03_startup_runtime_probe_s5.mjs: OK
tests/h3req1_c03_startup_smoke_s1.mjs: OK
tests/h3req1_c03_startup_smoke_s3.sh: OK
tests/h3req1_c03_startup_smoke_s3_resume_s4.sh: OK
tests/h3req1_c03_startup_smoke_s5.sh: OK
phase=s3-resources|error_code=OK
phase=s3-network-id-resolution|error_code=OK
phase=runtime-diagnostic-synthetic|error_code=PASS
runtime-stage=dependency-roots-present
runtime-project-frame=line:800:column:3
runtime-last-stage=dependency-roots-present
healthz=NO-GO reason=runtime-not-ready attempts=3
runtime-exit=code:1 signal:none
runtime-output-sanitization=allowlisted-events-only
bounded-stop=completed container=h3req1-c03-startup-runtime-20261010-s5 owner=verified; resource preserved
bounded-stop=completed container=h3req1-c03-startup-runtime-20261010-s5; resource preserved
Startup continuation halted phase=one-shot-pages-workerd-runtime-healthz exit=1; preserve all S3 resources.
container=h3req1-c03-startup-runtime-20261010-s5 state=exited|1|false network=internal-s3
NO-GO: Pages/workerd startup runtime failed
Startup continuation halted phase=one-shot-pages-workerd-runtime-healthz exit=1; preserve all S3 resources.
