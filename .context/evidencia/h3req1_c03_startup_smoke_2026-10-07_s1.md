jit=H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-06-S1
manifest-sha256=67fdea215c289cec028dae46172ba431814c598211561c17e6846d24e1c9ca7f
runner-sha256=c5fd272fdd18ef5a84d19bd1de229c421eb7dcccef7c2f1817460bcd9cc1a0d0
# H3REQ1 C03 startup smoke S1

scope=one fresh Pages/workerd startup smoke; no DB/PostgREST/Edge/SQL/Auth/email/remotes
.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log: OK
.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d1.log: OK
.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d2.log: OK
tests/h3req1-c03-integrated.sha256: OK
tests/h3req1-c03-integrated-diagnostic-r4-d1.sha256: OK
tests/h3req1-c03-integrated-diagnostic-r4-d2.sha256: OK
tests/h3req1_c03_integrated_runtime_diag_d1.sh: OK
tests/h3req1_c03_integrated_runtime_diag_d2.sh: OK
tests/h3req1_c03_startup_smoke_s1.sh: OK
tests/h3req1_c03_startup_smoke_s1.mjs: OK
tests/h3req1_c03_integrated_runtime.mjs: OK
tests/h3req1-c03-startup-source-s1.sha256: OK
tests/h3req1_c03_bootstrap_output_filter_s1.mjs: OK
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
docker-context=local-unix-socket-verified
volume-holder=h3req1-c03-startup-volume-holder-20261006-s1 state=running network=none
bounded-stop=completed container=h3req1-c03-startup-snapshot-20261006-s1 owner=verified; resource preserved
bounded-stop=completed container=h3req1-c03-startup-snapshot-20261006-s1; resource preserved
Startup smoke halted phase=create-new-source-snapshot exit=2; preserve all resources; no cleanup/resume.
NO-GO: new source snapshot failed; safe output suppressed (exit=2)
Startup smoke halted phase=create-new-source-snapshot exit=1; preserve all resources; no cleanup/resume.
