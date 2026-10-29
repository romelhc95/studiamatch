jit=H3-CLOSE-03-WORKERD-STARTUP-DIAGNOSTIC-S15-2026-10-10
runner-sha256=34618ac7d3a14578305de5122acea51fd2fd3470786ac05a1e0924b47eb68294
sidecar-sha256=9bc9f9fd3cfe0ec4df73a1e94145b96795075dac1ee1b95f82698c8517e79568
inputs-sha256=b2a6a47c4407caef78b2c731b223c4fc5c8fd5f7226982c9baa8aae671852484
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
scope=single Pages/workerd diagnostic; reused S18 snapshot and S11 fresh locks; no bootstrap, DB, PostgREST, Edge, SQL, Auth, email, secrets, remotes, or original-checkout writes
phase=runtime-stop-recovery-synthetic|error_code=PASS|cases=9
prior-runtime=s14|id=5243c9e452f397f8194501418c897905ac43fda9c298479eaff6d2756a748f5c|exit=1|oom=false|last-stage=runtime-uncaught-error|error=ERR_MODULE_NOT_FOUND|module=relative-module|healthz=NO-GO
runtime-image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|network=h3req1-c03-startup-net-20261010-s11|network-id=9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa|internal=true|resources=2GiB-2CPU|timeout=180s
phase=preflight|error_code=PASS
phase=s15-runtime-contract|error_code=PASS|cases=7
phase=runtime-diagnostic-synthetic|error_code=PASS
runtime-stage=runtime-ready
healthz=PASS workerd=true pages-worker=root-asset attempts=21
runtime-exit=code:0 signal:none
smoke=PASS workerd-pages-healthz=true pages-worker=root-asset edge-runtime=not-started database=not-started
runtime-output-sanitization=allowlisted-events-only
runtime-docker-exit=0|filter-exit=0
runtime-container=h3req1-c03-startup-runtime-20261010-s15|id=d45b6f4ef1ab80a4b81bccc2900d073f45d17e655acc776e3044757e60343ae1|state=exited|exit=0|oom=false|network=9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa|readonly=true|mounts=5-readonly
NO-GO: startup dependency content digests were not verified
runtime-stop=not-required|state=exited|container-id=d45b6f4ef1ab80a4b81bccc2900d073f45d17e655acc776e3044757e60343ae1|resource=preserved
diagnostic-result=NO-GO|phase=one-shot-pages-workerd-runtime-diagnostic|exit=1
