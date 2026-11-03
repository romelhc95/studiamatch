jit=H3-CLOSE-03-WORKERD-STARTUP-DIAGNOSTIC-S13-2026-10-10
runner-sha256=6b9527169e1c4c9abbefe37a10175e87dcfc61d99fa68df399d7baddc2b33dff
inputs-sha256=0591fc3e7e98aecc5b69534286b97f56d9548bfa9b8d3d081990d8ad84278611
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
scope=single Pages/workerd diagnostic; reused S16 snapshot and S11 fresh locks; no bootstrap, DB, PostgREST, Edge, SQL, Auth, email, secrets, remotes, or original-checkout writes
prior-runtime=s12|id=09de091c56585687a0dd3166742f37cb80c6a45b116e6a817547a227ccbd5810|exit=1|oom=false|last-stage=runtime-uncaught-error|error=ERR_MODULE_NOT_FOUND|healthz=NO-GO
runtime-image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|network=h3req1-c03-startup-net-20261010-s11|network-id=9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa|internal=true|resources=2GiB-2CPU|timeout=180s
phase=preflight|error_code=PASS
phase=runtime-diagnostic-synthetic|error_code=PASS
runtime-stage=runtime-uncaught-error
runtime-error-class=ERROR
runtime-error-code=ERR_MODULE_NOT_FOUND
runtime-missing-module=unclassified|from=other
runtime-last-stage=runtime-uncaught-error
healthz=NO-GO reason=runtime-not-ready attempts=2
runtime-exit=code:1 signal:none
runtime-output-sanitization=allowlisted-events-only
runtime-docker-exit=1|filter-exit=0
runtime-container=h3req1-c03-startup-runtime-20261010-s13|id=fdb48dc98b01d6bc413be83bea30c06a49eebb963cc8da03083f1ce77c2f21e5|state=exited|exit=1|oom=false|network=9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa|readonly=true|mounts=5-readonly
NO-GO: Pages/workerd healthz was not reached
runtime-stop=not-required|state=exited|container-id=fdb48dc98b01d6bc413be83bea30c06a49eebb963cc8da03083f1ce77c2f21e5|resource=preserved
diagnostic-result=NO-GO|phase=one-shot-pages-workerd-runtime-diagnostic|exit=1
