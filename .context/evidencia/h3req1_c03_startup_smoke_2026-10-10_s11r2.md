jit=H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S11-CURRENT-LOCKS
manifest-sha256=a261d0f3933f5a70180ebc62ba66c54f7a089aeb5bf1c858a3da4c0be8deab82
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
# H3REQ1 C03 startup smoke S11-R2 — current source and fresh locked dependencies

attempt=2; prior-attempt-evidence=.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s11.md
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
phase=bootstrap-output-filter-synthetic|error_code=PASS
phase=runtime-output-filter-synthetic|error_code=PASS
phase=runtime-diagnostic-synthetic|error_code=PASS
volume-holder=h3req1-c03-startup-volume-holder-20261010-s11|state=running|network=none
bootstrap-output=non-diagnostic-lines-suppressed
bootstrap-docker-exit=0|filter-exit=0
container=h3req1-c03-startup-tools-20261010-s11|state=exited|exit=0|oom=false|network=bridge
container-retirement=evidence-written|name=h3req1-c03-startup-tools-20261010-s11|id=39aa759b5c3a4206a4f089810f0563695fbad7b8cbb470c35ffb37f208b16d0d
container-retirement=completed|name=h3req1-c03-startup-tools-20261010-s11|id=39aa759b5c3a4206a4f089810f0563695fbad7b8cbb470c35ffb37f208b16d0d
bootstrap-output=non-diagnostic-lines-suppressed
bootstrap-docker-exit=0|filter-exit=0
container=h3req1-c03-startup-pages-20261010-s11|state=exited|exit=0|oom=false|network=bridge
container-retirement=evidence-written|name=h3req1-c03-startup-pages-20261010-s11|id=cdadd6e1a39231568242e42e79f9a79b0119520aa12881b9a6e57a626db1d8f4
container-retirement=completed|name=h3req1-c03-startup-pages-20261010-s11|id=cdadd6e1a39231568242e42e79f9a79b0119520aa12881b9a6e57a626db1d8f4
runtime-network=h3req1-c03-startup-net-20261010-s11|id=9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa|driver=bridge|internal=true|endpoints=0
phase=runtime-diagnostic-synthetic|error_code=PASS
runtime-stage=runtime-uncaught-error
runtime-last-stage=runtime-uncaught-error
healthz=NO-GO reason=runtime-not-ready attempts=2
runtime-exit=code:1 signal:none
runtime-output-sanitization=allowlisted-events-only
runtime-docker-exit=1|filter-exit=0
container=h3req1-c03-startup-runtime-20261010-s11|state=exited|exit=1|oom=false|network=9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa
NO-GO: Pages/workerd runtime container returned nonzero exit
startup-result=NO-GO|phase=one-shot-pages-workerd-healthz|exit=1
