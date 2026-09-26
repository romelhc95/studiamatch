# H3REQ1 Remote Validation â€” Read-only Evidence

**Captured:** 2026-09-24 UTC 04:08â€“04:09
**Mode:** read-only; no SQL writes, migrations, Auth writes, Edge deploys,
Cloudflare actions, push, PR, merge or promotion were executed.
**Projects:** Free `aqrldlmlszjtgpqiegaa`; Pro `xwhtiqmboljkshrtviyw`.

## Reproduction provenance

The snapshot was obtained through the Supabase project read-only operations:

```text
supabase-free.list_migrations()
supabase-pro.list_migrations()
supabase-free.list_edge_functions()
supabase-pro.list_edge_functions()
supabase-free.get_edge_function({ function_slug: "admin-invite" })
supabase-free.execute_sql(read-only metadata query)
supabase-pro.execute_sql(read-only metadata query)
```

The SQL query inspected only `current_setting('server_version')`,
`supabase_migrations.schema_migrations`, `information_schema.tables`,
`information_schema.columns` and public routine metadata. It did not select
operational rows, users, tokens, passwords, credentials or invitation content.

## Remote result

| Check | Free | Pro | Result |
|---|---|---|---|
| PostgreSQL | 17.6 | 17.6 | Informational only |
| H3 migrations recorded | H3 through `20260903` | None returned | Proves environment drift |
| `admin_members` | Present | Absent | H3 RBAC only partially present |
| `admin_membership_audit` | Present | Absent | H3 audit only partially present |
| `admin_invitations` | Absent | Absent | 03A/03B persistence not applied |
| Invitation/onboarding RPCs | Absent | Absent | 03A/03B runtime not applied |
| `admin-invite` Edge Function | ACTIVE, v1, `verify_jwt=true` | Not listed | Free runtime exists without its DB contract; Pro absent |

### Free migration rows

```text
20260902212528  20260828_h3_admin_auth
20260902212535  20260828_h3_admin_course_queue_view
20260902212546  20260828_h3_admin_editorial_reader_rpc
20260902212607  20260828_h3_admin_editorial_rpc
20260902212618  20260828_h3_admin_queue_rpc
20260902212629  20260829_h3_rbac_users
20260902212642  20260830_h3_expanded_contract
20260902212656  20260902_h3_pr_contract
20260903045855  h3_rbac_contract_fix
```

No migration rows matching `20260918`, `20260919`, `20260920` or `20260921`
were returned from Free. Pro returned no rows matching `h3` or `202609`.

### Free Edge Function identity

```text
name: admin-invite
status: ACTIVE
version: 1
verify_jwt: true
ezbr_sha256: 012d9b04f6e1038ab5c66dddf8ec007a4d8112345ff63563b96540ff3043cf35
```

The local source hash at capture time was:

```text
58371eea6945f83db62595afa350fd9218d2a101db41990768dab821d981d759  supabase/functions/admin-invite/index.ts
```

These hashes are evidence identifiers only; they do not authorize deployment.

## Findings mapped to H3REQ1

### H3-001 â€” Complete remote H3 evidence

**Result:** `FAIL` / evidence now complete as a reproducible negative audit, but
the acceptance criterion remains open. The remote snapshot proves that the
required invitation/onboarding contract is not present in either required
environment.

### H3-002 â€” Complete real invitation/onboarding flow

**Result:** `BLOCKED`. A real flow cannot be executed safely because the remote
DB contract required by the Edge Function and onboarding pages is absent. Local
mock evidence remains separate and is not promoted to remote evidence.

### H3-003 â€” Verify H3 migrations in required environments

**Result:** `FAIL`. Free has only the earlier RBAC/editorial H3 migrations;
Pro has no recorded H3 migrations. The four invitation/onboarding migrations
are not present remotely.

### H3-004 â€” Expand â†’ compatibility â†’ deploy â†’ contract, including rollback

**Result:** `BLOCKED`. Local expand/compatibility evidence exists, but remote
deploy, contract/cleanup and rollback execution remain unperformed. No rollback
was attempted because there is no approved remote change to roll back.

## Current decision

`NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`

Next actions require separate human JIT approvals for Free DDL, Pro DDL, Edge
deployment, controlled Auth/invitation test data, and any deployment or
promotion. No GO can be declared from this artifact alone.
