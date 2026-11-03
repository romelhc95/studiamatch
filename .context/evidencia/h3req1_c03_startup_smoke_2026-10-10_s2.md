jit=H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S2
manifest-sha256=18cda74992361c971d355159c6454477111d86216af30e11089e3ced3575dc62
runner-sha256=67f108ee253e8c7540f5f6bd3fc8533576b1ceaf264fe8f5c1a70525b8e3daae
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
tests/h3req1_c03_startup_smoke_s2.sh: OK
tests/h3req1_c03_startup_smoke_s1.mjs: OK
tests/h3req1_c03_integrated_runtime.mjs: OK
tests/h3req1-c03-startup-source-s1-v3.sha256: OK
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
docker-context=docker-desktop-wsl-attested
volume-holder=h3req1-c03-startup-volume-holder-20261010-s2 state=running network=none
bounded-stop=completed container=h3req1-c03-startup-snapshot-20261010-s2 owner=verified; resource preserved
bounded-stop=completed container=h3req1-c03-startup-snapshot-20261010-s2; resource preserved
Startup smoke halted phase=create-new-source-snapshot exit=2; preserve all resources; no cleanup/resume.
NO-GO: new source snapshot failed; safe output suppressed (exit=2)
Startup smoke halted phase=create-new-source-snapshot exit=1; preserve all resources; no cleanup/resume.
