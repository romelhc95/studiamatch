jit=H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S4-RESUME-S3
manifest-sha256=1cb90249466e65ccf59fc6ae3d2d7088f8c658917d91ece5f55c66bfd9268f29
runner-sha256=c4659f16889a41987c6512d7167ffe397d6a31edf58b645a77bc888d627eca7c
# H3REQ1 C03 startup smoke S4 — continuation from verified S3 resources

scope=Pages/workerd startup and healthz only; reused S3 snapshot/dependency volumes; no egress, DB, PostgREST, Edge, SQL, Auth, email, or remotes
.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log: OK
.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d1.log: OK
.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d2.log: OK
.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s3.md: OK
.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s3_diagnosis.md: OK
tests/h3req1-c03-integrated-diagnostic-r4-d1.sha256: OK
tests/h3req1-c03-integrated-diagnostic-r4-d2.sha256: OK
tests/h3req1-c03-integrated.sha256: OK
tests/h3req1-c03-startup-smoke-s3.sha256: OK
tests/h3req1-c03-startup-source-s1-v3.sha256: OK
tests/h3req1_c03_bootstrap_output_filter_s1.mjs: OK
tests/h3req1_c03_integrated_runtime.mjs: OK
tests/h3req1_c03_integrated_runtime_diag_d1.sh: OK
tests/h3req1_c03_integrated_runtime_diag_d2.sh: OK
tests/h3req1_c03_startup_smoke_s1.mjs: OK
tests/h3req1_c03_startup_smoke_s3.sh: OK
tests/h3req1_c03_startup_smoke_s3_resume_s4.sh: OK
phase=s3-resources|error_code=OK
phase=s3-network-id-resolution|error_code=OK
dependency-bootstrap=both-locked-npm-ci-containers-exited-zero
healthz=not-ready transport=ECONNREFUSED
runtime-output-class=dependency-roots-present stream=stdout
healthz=not-ready transport=ECONNREFUSED
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
runtime-output-class=unclassified stream=stderr
healthz=NO-GO reason=runtime-exited-before-ready code=1 signal=none
runtime-exit=code:1 signal:none
runtime-output-sanitization=allowlisted-events-only
bounded-stop=completed container=h3req1-c03-startup-runtime-20261010-s4 owner=verified; resource preserved
bounded-stop=completed container=h3req1-c03-startup-runtime-20261010-s4; resource preserved
Startup continuation halted phase=one-shot-pages-workerd-runtime-healthz exit=1; preserve all S3 resources.
NO-GO: S4 runtime did not attach to the exact preflighted internal network ID
Startup continuation halted phase=one-shot-pages-workerd-runtime-healthz exit=1; preserve all S3 resources.
