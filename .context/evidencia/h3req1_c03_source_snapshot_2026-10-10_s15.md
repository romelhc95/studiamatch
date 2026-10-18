jit=H3-CLOSE-03-SOURCE-SNAPSHOT-S15-2026-10-10
runner-sha256=a77e11e13e825ebf69295aef0a4cfcde08315889575b59163a97fead5e7243e7
sidecar-sha256=9bd4780012c119dd6985c80486caeceaa22a256923d8e0b5a0a9745477ad09e5
source-manifest-sha256=be416dbca1bdd8eb814534ae345a14b3d0bac5a56a06c6df0aaa9e2acdad45a2
# H3REQ1 complete source snapshot S15

scope=14 allowlisted files only (13 source inputs plus v7 source manifest; source set <=8 MiB; tar stream hard-capped at 9437184 bytes); volume driver has no quota; PASS contains only bounded hash-verified snapshot, while NO-GO may preserve partial bytes; no dependency install, egress, DB, Edge, SQL, credentials, or remotes
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844
source-volume=h3req1-c03-startup-source-20261010-s15
snapshot-container=h3req1-c03-startup-snapshot-20261010-s15
source-files=14
source-bytes=558493
source-permission-files=14
source-permission-map-sha256=d56f44c30eace5568bf82d5f4f1a1f6b797e91c67d8bc8375d55c18d86f28b16
network=none
archive-limiter-tests=PASS|exact-limit=accepted|limit-plus-one=rejected|bytes-forwarded-at-limit=5
container-created-id=28942ad3b8bb4370c61d63703b07aeebe306b921165d0d16de2c83a88344337b
container-controls=PASS|state=created|network=none|rootfs=read-only|memory=128m|cpus=0.5|pids=64|mount=source-volume-rw
source-snapshot=PASS|files=14|source-manifest=13/13|permissions=exact|no-same-owner=true
source-tar-producer-status=0|archive-limiter-status=0|snapshot-receiver-status=0|output-filter-status=0|archive-limit-bytes=9437184
snapshot-container=h3req1-c03-startup-snapshot-20261010-s15|exited|0|oom=false|network=none
snapshot-volume=h3req1-c03-startup-source-20261010-s15|local-persistent|owner-verified
snapshot-verifier=exit-0|network=none|mount=readonly
source-snapshot=PASS files=14 symlinks=0 producer=0 receiver=0 verifier=0
Source snapshot S15: PASS; volume and exited container preserved.
source-snapshot-result=PASS
