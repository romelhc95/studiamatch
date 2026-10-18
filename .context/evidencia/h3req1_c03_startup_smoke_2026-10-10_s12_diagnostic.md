jit=H3-CLOSE-03-WORKERD-STARTUP-DIAGNOSTIC-S12-2026-10-10
runner-sha256=34fe573e3d6b2dcc5072317a8f0cdb8ee40a2332d3ee7e44dd30765a633ca8f6
inputs-sha256=fbfbed931f0253a1a7165419bc9ff3de18e0fad79eb942a2a38d5a2592c5dfba
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
scope=single Pages/workerd diagnostic; reused S16 snapshot and S11 fresh locks; no bootstrap, DB, PostgREST, Edge, SQL, Auth, email, secrets, remotes, or original-checkout writes
prior-runtime=s11r2|id=612d8e1a65358344d8e847ef2b87920a7a7df992b165dd41a972ebdd2176f41d|exit=1|oom=false|last-stage=runtime-uncaught-error|healthz=NO-GO
runtime-image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|network=h3req1-c03-startup-net-20261010-s11|network-id=9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa|internal=true|resources=2GiB-2CPU|timeout=180s
phase=preflight|error_code=PASS
phase=runtime-diagnostic-synthetic|error_code=PASS
runtime-stage=runtime-uncaught-error
runtime-error-class=ERROR
runtime-error-code=ERR_MODULE_NOT_FOUND
runtime-last-stage=runtime-uncaught-error
healthz=NO-GO reason=runtime-not-ready attempts=2
runtime-exit=code:1 signal:none
runtime-output-sanitization=allowlisted-events-only
runtime-docker-exit=1|filter-exit=0
runtime-container=h3req1-c03-startup-runtime-20261010-s12|id=09de091c56585687a0dd3166742f37cb80c6a45b116e6a817547a227ccbd5810|state=exited|exit=1|oom=false|network=9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa|readonly=true|mounts=5-readonly
NO-GO: Pages/workerd healthz was not reached
diagnostic-result=NO-GO|phase=one-shot-pages-workerd-runtime-diagnostic|exit=1
