jit=H3-CLOSE-03-WORKERD-STARTUP-DIAGNOSTIC-S14-2026-10-10
runner-sha256=fc67fce4b7ba6851c9590bed8d01c17a490b8edc575c40fdc7c71ba332b92ff4
inputs-sha256=e787a7cd371b2f5705646ef6b5322d3562d8bc6c401079bfefc9bef32d3555eb
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
scope=single Pages/workerd diagnostic; reused S16 snapshot and S11 fresh locks; no bootstrap, DB, PostgREST, Edge, SQL, Auth, email, secrets, remotes, or original-checkout writes
prior-runtime=s13|id=fdb48dc98b01d6bc413be83bea30c06a49eebb963cc8da03083f1ce77c2f21e5|exit=1|oom=false|last-stage=runtime-uncaught-error|error=ERR_MODULE_NOT_FOUND|module=unclassified|healthz=NO-GO
runtime-image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|network=h3req1-c03-startup-net-20261010-s11|network-id=9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa|internal=true|resources=2GiB-2CPU|timeout=180s
phase=preflight|error_code=PASS
phase=runtime-diagnostic-synthetic|error_code=PASS
runtime-stage=runtime-uncaught-error
runtime-error-class=ERROR
runtime-error-code=ERR_MODULE_NOT_FOUND
runtime-missing-module=relative-module|from=candidate-tests
runtime-missing-module-shape=module-import
runtime-last-stage=runtime-uncaught-error
healthz=NO-GO reason=runtime-not-ready attempts=2
runtime-exit=code:1 signal:none
runtime-output-sanitization=allowlisted-events-only
runtime-docker-exit=1|filter-exit=0
runtime-container=h3req1-c03-startup-runtime-20261010-s14|id=5243c9e452f397f8194501418c897905ac43fda9c298479eaff6d2756a748f5c|state=exited|exit=1|oom=false|network=9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa|readonly=true|mounts=5-readonly
NO-GO: Pages/workerd healthz was not reached
runtime-stop=not-required|state=exited|container-id=5243c9e452f397f8194501418c897905ac43fda9c298479eaff6d2756a748f5c|resource=preserved
diagnostic-result=NO-GO|phase=one-shot-pages-workerd-runtime-diagnostic|exit=1
