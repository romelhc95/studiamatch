jit=H3-CLOSE-03-SOURCE-SNAPSHOT-S16-2026-10-10
runner-sha256=16f160c42ff1e89fd1b6daab876e2c2121cfe51e56f15716851a3c181a33a8e6
sidecar-sha256=4b159bae0f92fa16d466d6150a6cba8b672ad2d997b15bf14f4b983d4f9bd242
source-manifest-sha256=5312e12762db37a8a2eac28658bd609d966c74dd0d210d38363cb3ebb62e209e
# H3REQ1 complete source snapshot S16

scope=14 allowlisted files only (13 source inputs plus v8 source manifest; source set <=8 MiB; tar stream hard-capped at 9437184 bytes); volume driver has no quota; PASS contains only bounded hash-verified snapshot, while NO-GO may preserve partial bytes; no dependency install, egress, DB, Edge, SQL, credentials, or remotes
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844
source-volume=h3req1-c03-startup-source-20261010-s16
snapshot-container=h3req1-c03-startup-snapshot-20261010-s16
source-files=14
source-bytes=558493
source-permission-files=14
source-permission-map-sha256=220afb6ba654952b8dd4c1e3916defe6ea416d74554a49462e32286c753a7b7e
network=none
archive-limiter-tests=PASS|exact-limit=accepted|limit-plus-one=rejected|bytes-forwarded-at-limit=5
container-created-id=fd13e700d0853c03020ad9889f1cd6c063a320904fa1d5ecc969a28226e2f4d2
container-controls=PASS|state=created|network=none|rootfs=read-only|memory=128m|cpus=0.5|pids=64|mount=source-volume-rw
source-snapshot=PASS|files=14|source-manifest=13/13|permissions=exact|no-same-owner=true
source-tar-producer-status=0|archive-limiter-status=0|snapshot-receiver-status=0|output-filter-status=0|archive-limit-bytes=9437184
snapshot-container=h3req1-c03-startup-snapshot-20261010-s16|exited|0|oom=false|network=none
snapshot-volume=h3req1-c03-startup-source-20261010-s16|local-persistent|owner-verified
snapshot-verifier=exit-0|network=none|mount=readonly
source-snapshot=PASS files=14 symlinks=0 producer=0 receiver=0 verifier=0
Source snapshot S16: PASS; volume and exited container preserved.
source-snapshot-result=PASS
