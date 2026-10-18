jit=H3-CLOSE-03-SOURCE-SNAPSHOT-S10-2026-10-10
runner-sha256=354292c1fa0d022d6f771e98c28017afa32ac1281bc5e14126333907132f9f67
sidecar-sha256=d9b418da57e8fe2b9ba5f8a4cb343bbe21f2c322d1cc4ab1366bfd2e9902cde4
source-manifest-sha256=fdcba48af1ec5ffeba91de0a6fa44022dd3027b85d6b9a5c02afea4c79678233
# H3REQ1 complete source snapshot S10

scope=14 allowlisted files only (13 source inputs plus v4 source manifest); no dependency install, egress, DB, Edge, SQL, credentials, or remotes
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844
source-volume=h3req1-c03-startup-source-20261010-s10
snapshot-container=h3req1-c03-startup-snapshot-20261010-s10
source-files=14
source-bytes=540851
source-permission-files=14
source-permission-map-sha256=e37b30d5483cfe16fbe0fa93f141fced3f86d26ab50f6e8ce7ca4fb9869a9537
network=none
container-created-id=bbe5a8d2594255f0e15584bb0d989d60bceb68575391671b781fc91139aed7af
container-controls=PASS|state=created|network=none|rootfs=read-only|memory=128m|cpus=0.5|pids=64|mount=source-volume-rw
source-snapshot=PASS|files=14|source-manifest=13/13|permissions=exact|no-same-owner=true
source-tar-producer-status=0|snapshot-receiver-status=0|output-filter-status=0
NO-GO: read-only snapshot verifier failed
bounded-stop=completed|container-preserved=true
source-snapshot-result=NO-GO|phase=independent-read-only-volume-verification|exit=1
