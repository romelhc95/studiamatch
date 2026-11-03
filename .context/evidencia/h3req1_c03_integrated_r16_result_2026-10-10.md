# G07 R16 — preflight PASS; address pool exhausted before services

## Resultado

- Candidato: `feat/h3req1-sync-20261002` @ `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Manifiesto: 65/65, SHA-256 `186862f80907e1e668b258d9c3ab7058d0360476be8b58f491288e501a324dfc`.
- R16 full drill: exit 1; log [R16](h3req1_c03_integrated_run_2026-10-10_r16.log), SHA-256 `c7b9e83ad2fd7d19e951b97681ba5593a59f4fa40b910877563643db2eee842e`.
- Docker endpoint/identity, manifest, PG17.11, source snapshot, runner contracts and dependency-cache digests passed.
- Phase `create-internal-data-network`: Docker returned `all predefined address pools have been fully subnetted`; edge network was created, the data network was not. No PG17, PostgREST, Pages/workerd or Edge service started. Failure-stop found no run-owned running containers.

## Inventory before targeted network cleanup

The exact structured inventory is preserved in [network inventory](h3req1_c03_integrated_network_inventory_precleanup_2026-10-10.txt), SHA-256 `f24a56db5351911a8bfe971bc72e29a6e091c01849cfee2acf9072ac0f1b2ac3`. Nineteen prior H3 integrated networks were found (R5, R6, R8–R11, R13–R16, data/edge where present). Every listed network had `Internal=true`, `attached=0`, exact `H3-CLOSE-03-INTEGRATED-2026-10-10-Rn` ownership labels, and no file/volume mount capability. The R16 data network was absent. After preserving evidence, the exact 19 empty networks were removed; all containers, 27 H3 volumes, images, logs and snapshots were preserved. `studiamatch-dev` remains healthy. Details and the first cleanup wrapper correction are in [selective network cleanup](h3req1_c03_integrated_network_cleanup_2026-10-10.md). No global prune or engine configuration change.

## Gate status

R16 did not reach the newly added early-response classifier; that diagnosis remains pending. G07 stays partial; no downstream C03 assertions ran and the percentage does not change. After preserving inventory, remove only the listed network IDs after revalidating ID, labels, `Internal=true`, and zero attachments; then proceed with a fresh R17 runtime because R16 is consumed.
