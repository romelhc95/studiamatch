jit=H3-CLOSE-03-SOURCE-SNAPSHOT-S13-2026-10-10
runner-sha256=42bf972fb638becf30308258cea4b7c8e3e19606a605984ad8506cbaf49a6dfa
sidecar-sha256=ae7f89139fd28ec948b137f3eb4012ae168389f5a759088cd33548dbeab76d51
source-manifest-sha256=9a6530849379cb398d553cf5931a115652a4feea61b37f7dafcd418bf37df086
# H3REQ1 complete source snapshot S13

scope=14 allowlisted files only (13 source inputs plus v5 source manifest; source set <=8 MiB; tar stream hard-capped at 9437184 bytes); volume driver has no quota; PASS contains only bounded hash-verified snapshot, while NO-GO may preserve partial bytes; no dependency install, egress, DB, Edge, SQL, credentials, or remotes
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844
source-volume=h3req1-c03-startup-source-20261010-s13
snapshot-container=h3req1-c03-startup-snapshot-20261010-s13
source-files=14
source-bytes=552843
source-permission-files=14
source-permission-map-sha256=1265e51daba6ec2648f7dfa322eb596ca391dfef8105733d371638b54ca10c04
network=none
archive-limiter-tests=PASS|exact-limit=accepted|limit-plus-one=rejected|bytes-forwarded-at-limit=5
container-created-id=35b4f7f60524d71fcb9c27b1373a2630c04dd4a9c8d3dd2b3478b1fa19c3ac55
container-controls=PASS|state=created|network=none|rootfs=read-only|memory=128m|cpus=0.5|pids=64|mount=source-volume-rw
source-snapshot=PASS|files=14|source-manifest=13/13|permissions=exact|no-same-owner=true
source-tar-producer-status=0|archive-limiter-status=0|snapshot-receiver-status=0|output-filter-status=0|archive-limit-bytes=9437184
snapshot-container=h3req1-c03-startup-snapshot-20261010-s13|exited|0|oom=false|network=none
snapshot-volume=h3req1-c03-startup-source-20261010-s13|local-persistent|owner-verified
snapshot-verifier=exit-0|network=none|mount=readonly
source-snapshot=PASS files=14 symlinks=0 producer=0 receiver=0 verifier=0
Source snapshot S13: PASS; volume and exited container preserved.
source-snapshot-result=PASS
