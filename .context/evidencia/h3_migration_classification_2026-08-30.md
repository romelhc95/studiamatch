# H3 migration classification

| Migration | Classification | Evidence |
|---|---|---|
| `20260828_h3_admin_auth.sql` | reusable with delta | Applied on isolated PG17; creates H3 membership/RBAC base |
| `20260828_h3_admin_course_queue_view.sql` | reusable | Applied on isolated PG17 |
| `20260828_h3_admin_editorial_reader_rpc.sql` | reusable with delta | Reader currently requires effective-value reconciliation |
| `20260828_h3_admin_queue_rpc.sql` | reusable | Cursor/filter validation covered by local harness |
| `20260828_h3_admin_editorial_rpc.sql` | reusable with delta | Needs server-side missing_fields/quality recomputation on manual update |
| `20260829_h3_rbac_users.sql` | reusable with delta | AAL2, email validation and membership audit added locally |
| `20260830_h3_expanded_contract.sql` | reusable with delta | AAL2 helper, append-only membership audit and serialized admin mutation added |

First application: successful on `studiamatch-h2-pg-test`.
Second application: successful with expected `IF NOT EXISTS`/`DROP ... IF EXISTS` notices; equivalent idempotent operation.
No original migration was rewritten; only forward local changes were made.
