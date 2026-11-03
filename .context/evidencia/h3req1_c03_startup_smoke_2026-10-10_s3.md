jit=H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S3
manifest-sha256=351c6590c24c466fe8af531f1d9661ef7a6fcc1f7170c617f223fefc70bdc018
runner-sha256=4077a9c6e14a0588fb972f77c4b27385cc223306a63bbaea553b239c87af1689
# H3REQ1 C03 startup smoke S3

scope=one fresh Pages/workerd startup smoke; no DB/PostgREST/Edge/SQL/Auth/email/remotes
.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log: OK
.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d1.log: OK
.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d2.log: OK
tests/h3req1-c03-integrated-diagnostic-r4-d1.sha256: OK
tests/h3req1-c03-integrated-diagnostic-r4-d2.sha256: OK
tests/h3req1-c03-integrated.sha256: OK
tests/h3req1-c03-startup-source-s1-v3.sha256: OK
tests/h3req1_c03_bootstrap_output_filter_s1.mjs: OK
tests/h3req1_c03_integrated_runtime.mjs: OK
tests/h3req1_c03_integrated_runtime_diag_d1.sh: OK
tests/h3req1_c03_integrated_runtime_diag_d2.sh: OK
tests/h3req1_c03_startup_smoke_s1.mjs: OK
tests/h3req1_c03_startup_smoke_s3.sh: OK
tests/h3req1_c03_integrated_runtime.mjs: OK
tests/h3req1_c03_startup_smoke_s1.mjs: OK
tests/h3req1_c03_cache_digest.mjs: OK
tests/h3req1-c03-bootstrap/package.json: OK
tests/h3req1-c03-bootstrap/package-lock.json: OK
web/package.json: OK
web/package-lock.json: OK
web/vendor/braces-3.0.4-h3.1.tgz: OK
web/functions/_middleware.ts: OK
web/functions/_lib/admin-bff.ts: OK
web/functions/_lib/admin-quota.ts: OK
web/src/lib/supabase-transport.ts: OK
workers/admin-quota/index.ts: OK
docker-context=docker-desktop-wsl-attested
volume-holder=h3req1-c03-startup-volume-holder-20261010-s3 state=running network=none
container=h3req1-c03-startup-snapshot-20261010-s3 state=exited|0|false network=none
source-snapshot=PASS files=14 symlinks=0 extraction-owner-restore=disabled
bootstrap-output=non-diagnostic-lines-suppressed
container=h3req1-c03-startup-tools-20261010-s3 state=exited|0|false network=bridge
bootstrap-output=non-diagnostic-lines-suppressed
container=h3req1-c03-startup-pages-20261010-s3 state=exited|0|false network=bridge
NO-GO: unexpected network name returned
Startup smoke halted phase=create-new-egress-blocked-internal-network exit=1; preserve all resources; no cleanup/resume.
