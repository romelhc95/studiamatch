# H3REQ1 G09 mock build R7 provenance — 2026-10-11

- Candidate: `/home/romel/src/studiamatch-h3req1-sync-20261002`
- Branch / HEAD baseline: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`
- Build purpose: verify the INV-008 login route correction in Pages/workerd static output.
- Build command: `NEXT_PUBLIC_H3_MOCK_URL=http://127.0.0.1:3211 npm run build:mock` in an isolated Docker build container.
- Builder runner SHA-256: `fee8e87c53e77027ef43e949cdfb265ea9e17389167547371fc0d472e831b61a`
- Build image ID: `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`
- Build container ID: `a6e127362376024bb1fe3d2f9d8a8a8c94ef06ccfb681136b2636c16e50a1f19` (exit 0, removed by exact ID without volumes).
- Font proxy ID: `a77a9185f5d31504b716022b0574710bb56ea46a3d0fb4175761ef6f4d9c8709` (exit 0, removed by exact ID); allowlisted egress counts: 13 accepted, 2 rejected, 0 upstream failures.
- Build limits: 4 GiB RAM, 2 CPU; Node heap 3 GiB; 600 s timeout; no retries.
- Network: build container internal-only; separate proxy egress network solely to fetch allowlisted font assets. Build completed and both networks/containers were cleaned by exact identities.
- Source manifest: `source-provenance-r7/source-inputs-r7.sha256`, SHA-256 `94b3d55d4d5bb49bd012e228b7d642cf3c81a3c5cbf1bca275ea654094a3f782`, `643` files.
- `web/package.json`: `dfdd9a7ea0ff192c7eda7c33d9a2141b5b761fb0c53c472d8209e4fa2c309ab2`; `web/package-lock.json`: `d526163caba9300baf9329121979b9c9bc1bd24dfc10b1b4159d0ee8a36334db`.
- Relevant changed inputs: login page `8a9203e458f17492e9e98b09e558ea8369e0cf15a4ecc163ebe2ce041bfc0974`; onboarding UAT `da5fc5fbebd46f66daf5a8ee2252d216f8367d48c021891a599b5296d5753d7b`.
- Mock output: `mock-out-r7/`, 126 files; manifest `mock-out-r7.sha256`, SHA-256 `fcf7ee39dff6cf6891a8eb7c6b1b71ff0f1d4de86b2764c08ae4f44ec24dc8f4`; strict output hash verification PASS.
- No `.env*`, operational credentials, remote DB, or external service data were mounted into the build.
- This is build evidence only; it does not establish runtime acceptance or close G08/G09.
