jit=H3-CLOSE-03-SOURCE-SNAPSHOT-S12-2026-10-10
runner-sha256=e03287ad6d05bbb497f7cfc87aac3ad4fe9ef33a7e059396dd2d9fe0ebd69807
sidecar-sha256=2d89fa0edc87f744a5e602acd5ddf8e9417083c94b1eb4842ef365f2e7028872
source-manifest-sha256=fdcba48af1ec5ffeba91de0a6fa44022dd3027b85d6b9a5c02afea4c79678233
# H3REQ1 complete source snapshot S12

scope=14 allowlisted files only (13 source inputs plus v4 source manifest; source set <=8 MiB; tar stream hard-capped at 9437184 bytes); volume driver has no quota; PASS contains only bounded hash-verified snapshot, while NO-GO may preserve partial bytes; no dependency install, egress, DB, Edge, SQL, credentials, or remotes
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844
source-volume=h3req1-c03-startup-source-20261010-s12
snapshot-container=h3req1-c03-startup-snapshot-20261010-s12
source-files=14
source-bytes=540851
source-permission-files=14
source-permission-map-sha256=e37b30d5483cfe16fbe0fa93f141fced3f86d26ab50f6e8ce7ca4fb9869a9537
network=none
archive-limiter-tests=PASS|exact-limit=accepted|limit-plus-one=rejected|bytes-forwarded-at-limit=5
container-created-id=deed0a611eae8a8052d9fb21907a7ab6bc75c7c099d20532dbd28590045d1401
container-controls=PASS|state=created|network=none|rootfs=read-only|memory=128m|cpus=0.5|pids=64|mount=source-volume-rw
source-snapshot=PASS|files=14|source-manifest=13/13|permissions=exact|no-same-owner=true
source-tar-producer-status=0|archive-limiter-status=0|snapshot-receiver-status=0|output-filter-status=0|archive-limit-bytes=9437184
snapshot-container=h3req1-c03-startup-snapshot-20261010-s12|exited|0|oom=false|network=none
snapshot-volume=h3req1-c03-startup-source-20261010-s12|local-persistent|owner-verified
snapshot-verifier=exit-0|network=none|mount=readonly
source-snapshot=PASS files=14 symlinks=0 producer=0 receiver=0 verifier=0
Source snapshot S12: PASS; volume and exited container preserved.
source-snapshot-result=PASS
