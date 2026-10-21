jit=H3-CLOSE-03-SOURCE-SNAPSHOT-S14-2026-10-10
runner-sha256=102057b9261a4886c01175d74b582bc48ee8fe76d37e6c6811545e732e08011e
sidecar-sha256=282aea3e5b0f9d2e2dce605a292ad029ccd36c24355a4708b2ade975861eb2a8
source-manifest-sha256=2f98ca0d448e4789e05836520a8167298283857fffa92bc054119f3dd69ad168
# H3REQ1 complete source snapshot S14

scope=14 allowlisted files only (13 source inputs plus v6 source manifest; source set <=8 MiB; tar stream hard-capped at 9437184 bytes); volume driver has no quota; PASS contains only bounded hash-verified snapshot, while NO-GO may preserve partial bytes; no dependency install, egress, DB, Edge, SQL, credentials, or remotes
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844
source-volume=h3req1-c03-startup-source-20261010-s14
snapshot-container=h3req1-c03-startup-snapshot-20261010-s14
source-files=14
source-bytes=553126
source-permission-files=14
source-permission-map-sha256=ed682cdf7bd2574cd68646b63fcee6a9780ea4e112bb985b9c52976643824228
network=none
archive-limiter-tests=PASS|exact-limit=accepted|limit-plus-one=rejected|bytes-forwarded-at-limit=5
container-created-id=f4351356bfc0f309a179a04343ff70fc62f1d1fd52c8e09c275239eacd1e0f6b
container-controls=PASS|state=created|network=none|rootfs=read-only|memory=128m|cpus=0.5|pids=64|mount=source-volume-rw
source-snapshot=PASS|files=14|source-manifest=13/13|permissions=exact|no-same-owner=true
source-tar-producer-status=0|archive-limiter-status=0|snapshot-receiver-status=0|output-filter-status=0|archive-limit-bytes=9437184
snapshot-container=h3req1-c03-startup-snapshot-20261010-s14|exited|0|oom=false|network=none
snapshot-volume=h3req1-c03-startup-source-20261010-s14|local-persistent|owner-verified
snapshot-verifier=exit-0|network=none|mount=readonly
source-snapshot=PASS files=14 symlinks=0 producer=0 receiver=0 verifier=0
Source snapshot S14: PASS; volume and exited container preserved.
source-snapshot-result=PASS
