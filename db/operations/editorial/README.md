# Future editorial backfill

This directory reserves the operational plan for a future editorial backfill. It does not contain executable SQL or operational data.

## Authorization boundary

- The backfill requires separate, explicit human authorization.
- A reviewed backfill plan does not authorize schema application or backfill execution.
- Schema and RLS application in Free requires its own phase and approval.
- Schema and RLS migrations must be certified in Free before backfill execution is considered.
- Backfill execution and final Free certification are separate gates and approvals.
- The operation runs Free-first and remains within the selected environment.
- H-00 is excluded. Production is never mixed with H-00 or with Free operational data.

## Required strategy

1. Pause the applicable writers for the selected environment.
2. Record counts only before execution. Do not export rows, identifiers, or field values.
3. Select a reviewed, bounded cohort with a deterministic upper limit.
4. Use an idempotent predicate so a successful row is not selected again.
5. Change only the editorial fields authorized for that operation.
6. Record counts only after execution and compare them with the bounded cohort.
7. Re-run the count predicate to prove that the operation is idempotent.
8. Resume writers only after independent verification.

## Environment isolation

- Never copy operational rows between Free and Production.
- Never reuse identifiers, fixtures, exports, or snapshots from another environment.
- Production needs its own authorization, backup, immutable candidate, and verification.
- Any mismatch in counts, scope, or environment is a stop condition.

Executable SQL may be introduced only by a later, separately authorized task after the exact predicate, bound, rollback procedure, and counts-only evidence contract are approved.
