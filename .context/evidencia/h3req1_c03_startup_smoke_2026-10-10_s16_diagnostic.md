jit=H3-CLOSE-03-WORKERD-STARTUP-DIAGNOSTIC-S16-2026-10-10
runner-sha256=2e658f6d2e0dc9e75296080c2c4ca9dd0cee6684edb001208ce2521e3685669e
sidecar-sha256=c8c6358427b0948ce5754de5fd2fc0107912fe21b914e1e2a22ba2c303c9ccc0
inputs-sha256=fefd46a83f50fe73fcb717a51c100208e0ec62942b6dfe79414ce94a18c9241e
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
scope=single Pages/workerd diagnostic; reused S18 snapshot and S11 fresh locks; no bootstrap, DB, PostgREST, Edge, SQL, Auth, email, secrets, remotes, or original-checkout writes
phase=runtime-stop-recovery-synthetic|error_code=PASS|cases=9
prior-runtime=s15|id=d45b6f4ef1ab80a4b81bccc2900d073f45d17e655acc776e3044757e60343ae1|exit=0|oom=false|healthz=PASS|wrapper=NO-GO|reason=dependency-marker-not-forwarded
runtime-image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|network=h3req1-c03-startup-net-20261010-s11|network-id=9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa|internal=true|resources=2GiB-2CPU|timeout=180s
phase=preflight|error_code=PASS
phase=s15-runtime-contract|error_code=PASS|cases=7
phase=runtime-diagnostic-synthetic|error_code=PASS
runtime-dependency-digests=PASS|groups=2
runtime-stage=runtime-ready
healthz=PASS workerd=true pages-worker=root-asset attempts=22
runtime-exit=code:0 signal:none
smoke=PASS workerd-pages-healthz=true pages-worker=root-asset edge-runtime=not-started database=not-started
runtime-output-sanitization=allowlisted-events-only
runtime-docker-exit=0|filter-exit=0
runtime-container=h3req1-c03-startup-runtime-20261010-s16|id=edf21ce7d3256d29bd41cff26c434d1f2d3a4a16ded2adbfcc84ece6a747c852|state=exited|exit=0|oom=false|network=9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa|readonly=true|mounts=5-readonly
phase=pages-workerd-healthz|error_code=PASS
exit=0
phase=internal-network-after-runtime|error_code=PASS
runtime-container-retirement=completed|id=edf21ce7d3256d29bd41cff26c434d1f2d3a4a16ded2adbfcc84ece6a747c852|volumes-preserved=true|network-preserved=true
retained-for-next-local-gates=source-volume-s18,tools-volume-s11,pages-volume-s11,volume-holder-s11,network-s11
diagnostic-result=PASS
