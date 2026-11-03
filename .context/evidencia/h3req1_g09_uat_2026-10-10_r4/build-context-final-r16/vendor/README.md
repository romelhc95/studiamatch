# Local `braces` security snapshot

`braces-3.0.4-h3.1.tgz` is a locally versioned snapshot of the security fix in
[`micromatch/braces` PR #72](https://github.com/micromatch/braces/pull/72), pinned
to source commit
`28d440b5dd449dbf1fe6f3506cf94ecca4d02660` from `FSDevelop/braces`.

- The upstream PR was still open and had no official release on 2026-10-03.
- `3.0.4-h3.1` is a local package version, **not** an upstream release. Only the
  package version metadata was changed; the implementation is the pinned PR
  snapshot. Do not describe it as an upstream-published fixed version.
- The patch bounds nested-brace/parenthesis recursion in parse, compile, expand,
  and stringify. The PR's upstream test suite passed 904 tests in Docker.
- Package license: MIT, included in the tarball.
- SHA-256:
  `a8c0b0223dc788781252f9b056207b5b053b8dd0896da861c305769b472f0819`.
- `package-lock.json` pins the local tarball and its SRI integrity. Reproduce with
  a clean Docker `npm ci`, then run the full dependency audit and application
  validation gates.

The fixed PR decision authorizes this local snapshot, not a waiver. Its maintainer
follow-up owner and review deadline are still awaiting confirmation; keep that
decision open and do not freeze/promote the candidate until it is recorded. Replace
the snapshot with an official patched release after validating that release.
