# S11 bootstrap synthetic failure and correction — 2026-10-10

Candidate: `feat/h3req1-sync-20261002` at `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
The original checkout remains unchanged.

## First S11 attempt

- Manifest SHA-256: `de1fbbb302ad10ba5bca51d0ce08c4c30d3f17615e10056f886f23c0605df6de`.
- Runner exited `1` at `bootstrap-synthetics`; no package installation or Pages/workerd runtime started.
- Preserved runner output: `.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s11.md`.
- Exact predicate mismatch: for `npm ERR! ERESOLVE synthetic`, the existing output filter emits `module-resolution-failure` because ERESOLVE is matched before the general npm error class. S11 expected `bootstrap-error`.
- Minimal reproduction in Docker `network none`, with only the filter mounted read-only, returned exit `0` and the sanitized markers:
  `module-resolution-failure`, `network-or-registry-failure`, `sensitive-line-redacted`.
- The filter's classification order is correct. The runner expectation was wrong. No product or filter code changed.
- Post-failure inventory found no S11 volumes, containers, or network; the runner stopped before creating resources.

## Review findings and runner corrections

- Independent static review initially found npm lifecycle scripts could run with bridge egress. Both bootstrap installs now use `--ignore-scripts`; the lock has 777 npm registry resolutions, one approved local vendor package, and zero other resolved sources. Runtime remains on an internal network.
- Bootstrap still uses Docker's bridge network and does not enforce a destination firewall. The registry URL and lockfile constrain npm's declared package sources, lifecycle scripts are disabled, and no credentials or `.env` files are mounted. The post-bootstrap runtime has no external egress.
- The previous cleanup check treated every failed `docker inspect` as proof of absence. It now requires a successful exact-ID `docker ps`/`docker network ls` query with an empty result; ambiguity stops the runner. Runtime attachment must match the verified internal network ID.
- ShellCheck found one unused `RUNNER` constant and intentional literal expansion in the container-side and Docker Go-template commands. The unused constant was removed and the literal boundaries documented. Bash syntax, `git diff --check`, and ShellCheck 0.11.0 pass after correction.
- A first ShellCheck container capped at 128 MiB exited `137`; the corrected 1 GiB isolated ShellCheck run passed. An auxiliary temp-directory removal command was rejected by automatic review; it made no changes, and review proceeded by mounting existing tests read-only.

## Next execution

Corrected runner evidence will be written to `h3req1_c03_startup_smoke_2026-10-10_s11r2.md`; the failed S11 evidence remains preserved. The corrected attempt changes the synthetic expectation and evidence path from the prior runner; prior review fixes remain included. It is subject to the fresh manifest and independent static review before execution.
