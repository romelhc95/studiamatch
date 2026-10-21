jit=H3-CLOSE-03-SOURCE-SNAPSHOT-S17-2026-10-10
runner-sha256=8a4864f94753bad494cafa5a0061825e6256762d75bc1076b98f73d03069646f
sidecar-sha256=a1c5ae0bb76c75b763a15b38eaad9f19c4ca0311aefd323ee73575ddf5bf4450
source-manifest-sha256=b1711c0b253c077fc1ff9493d9c74a11d12fa684acc0a144a97f5889b5d63012
phase=snapshot-stop-recovery-synthetic|error_code=PASS|cases=13
# H3REQ1 complete source snapshot S17

scope=17 allowlisted files only (16 source inputs plus v9 source manifest; source set <=8 MiB; tar stream hard-capped at 9437184 bytes); volume driver has no quota; PASS contains only bounded hash-verified snapshot, while NO-GO may preserve partial bytes; no dependency install, egress, DB, Edge, SQL, credentials, or remotes
branch=feat/h3req1-sync-20261002
head=4eb4d877a50b012bb630a129bd0c74482c33be9c
image=node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844
source-volume=h3req1-c03-startup-source-20261010-s17
snapshot-container=h3req1-c03-startup-snapshot-20261010-s17
source-files=17
source-bytes=565973
source-permission-files=17
source-permission-map-sha256=7987fb503cbdfada28777a9e7d8772736dc2ee3792a86316f607174aaaf57b75
network=none
archive-limiter-tests=PASS|exact-limit=accepted|limit-plus-one=rejected|bytes-forwarded-at-limit=5
container-created-id=31484390dfdbe8912bb9d2e916a221456cbe41c205dda803b8f7b28fce4a1104
container-controls=PASS|state=created|network=none|rootfs=read-only|memory=128m|cpus=0.5|pids=64|mount=source-volume-rw
source-snapshot=PASS|files=17|source-manifest=16/16|permissions=exact|no-same-owner=true
source-tar-producer-status=0|archive-limiter-status=0|snapshot-receiver-status=0|output-filter-status=0|archive-limit-bytes=9437184
snapshot-container=h3req1-c03-startup-snapshot-20261010-s17|exited|0|oom=false|network=none
snapshot-volume=h3req1-c03-startup-source-20261010-s17|local-persistent|owner-verified
snapshot-verifier=exit-0|network=none|mount=readonly
source-snapshot=PASS files=17 symlinks=0 producer=0 receiver=0 verifier=0
Source snapshot S17: PASS; volume and exited container preserved.
source-snapshot-result=PASS
