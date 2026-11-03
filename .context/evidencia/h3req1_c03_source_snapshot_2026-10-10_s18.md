jit=H3-CLOSE-03-SOURCE-SNAPSHOT-S18-2026-10-10
runner-sha256=870acaf354481de9b36a493f954355b1dfaf8555a60f7354a6147b3fa20a241e
sidecar-sha256=13a4bea55ed248d1ec0567f21258c5ccbc8dbfc9fb02667016aba0298ab262cf
source-manifest-sha256=29d8459b81656d5947a6e2c771616ff6a59d1719af13b1f686a8d58b7ce5bc6e
phase=snapshot-stop-recovery-synthetic|error_code=PASS|cases=13
# H3REQ1 complete source snapshot S18

scope=18 allowlisted files only (17 source inputs plus v10 source manifest; source set <=8 MiB; tar stream hard-capped at 9437184 bytes); volume driver has no quota; PASS contains only bounded hash-verified snapshot, while NO-GO may preserve partial bytes; no dependency install, egress, DB, Edge, SQL, credentials, or remotes
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844
source-volume=h3req1-c03-startup-source-20261010-s18
snapshot-container=h3req1-c03-startup-snapshot-20261010-s18
source-files=18
source-bytes=567469
source-permission-files=18
source-permission-map-sha256=73a49a5ecad3c5485a8408eb0457f334d5a0ba489fe1c1499d7e3870c6c58e6c
network=none
archive-limiter-tests=PASS|exact-limit=accepted|limit-plus-one=rejected|bytes-forwarded-at-limit=5
container-created-id=48116e932a4756e9180191e69655fc4b7a571c37fc0e4ccfd627e2ad9857f9ea
container-controls=PASS|state=created|network=none|rootfs=read-only|memory=128m|cpus=0.5|pids=64|mount=source-volume-rw
source-snapshot=PASS|files=18|source-manifest=17/17|permissions=exact|no-same-owner=true
source-tar-producer-status=0|archive-limiter-status=0|snapshot-receiver-status=0|output-filter-status=0|archive-limit-bytes=9437184
snapshot-container=h3req1-c03-startup-snapshot-20261010-s18|exited|0|oom=false|network=none
snapshot-volume=h3req1-c03-startup-source-20261010-s18|local-persistent|owner-verified
snapshot-verifier=exit-0|network=none|mount=readonly
source-snapshot=PASS files=18 symlinks=0 producer=0 receiver=0 verifier=0
Source snapshot S18: PASS; volume and exited container preserved.
source-snapshot-result=PASS
