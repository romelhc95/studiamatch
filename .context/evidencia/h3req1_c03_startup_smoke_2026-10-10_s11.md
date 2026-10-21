jit=H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S11-CURRENT-LOCKS
manifest-sha256=de1fbbb302ad10ba5bca51d0ce08c4c30d3f17615e10056f886f23c0605df6de
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
# H3REQ1 C03 startup smoke S11 — current source and fresh locked dependencies

scope=Pages/workerd healthz only; source snapshot S16; fresh npm dependencies from pinned package locks; npm registry bootstrap over Docker bridge with lifecycle scripts disabled; runtime on verified internal network; no DB, PostgREST, Edge, SQL, Auth, email, secrets, or remotes
source-manifest-sha256=5312e12762db37a8a2eac28658bd609d966c74dd0d210d38363cb3ebb62e209e
source-files=13
source-bytes=558493
source-mode-map-sha256=220afb6ba654952b8dd4c1e3916defe6ea416d74554a49462e32286c753a7b7e
dependency-lock-resolutions=registry-npmjs-777|local-vendor-1|other-0
node-image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844
npm-lifecycle-scripts=disabled
resource-limits=bootstrap-2GiB-2CPU-600s|runtime-2GiB-2CPU-180s|automatic-fetch-retries=0
tests/h3req1_c03_startup_smoke_s11.sh: OK
tests/h3req1-c03-startup-source-s1-v8.sha256: OK
tests/h3req1_c03_source_snapshot_s16.sh: OK
tests/h3req1-c03-source-snapshot-s16.sha256: OK
.context/evidencia/h3req1_c03_source_snapshot_2026-10-10_s16.md: OK
tests/h3req1_c03_bootstrap_output_filter_s1.mjs: OK
tests/h3req1_c03_startup_output_filter_s8.sh: OK
tests/h3req1_c03_startup_runtime_probe_s8.mjs: OK
tests/h3req1_c03_startup_validation_preload_s8.cjs: OK
phase=s16-snapshot-readonly-verifier|error_code=PASS
NO-GO: bootstrap output-filter synthetic marker mismatch
startup-result=NO-GO|phase=bootstrap-synthetics|exit=1
