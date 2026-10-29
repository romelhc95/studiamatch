# H3 Pro/Free/local metadata matrix

Status: `PARTIAL_NO_GO`; convergence direction is only `Pro -> Free` and `Pro -> local`.

| Object | Pro | Free | Local PG17 | Difference | Correct direction | Action | Classification | Risk | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| courses | Present; metadata snapshot | Present; read-only snapshot | Present | No blocking object difference observed | Pro -> Free/local | Compare columns/types before remote JIT | reusable baseline | Medium | `h3_pro_h2_authoritative_baseline_2026-08-30.json` |
| editorial_field_definitions | Present | Present | Present | Full column/policy comparison unavailable via current read-only output | Pro -> Free/local | Obtain authorized metadata query | reusable baseline | High | Pro read-only query |
| course_editorial_state | Present | Present | Present | H3 fields exist locally; Pro routine inventory returned empty | Pro -> Free/local | Treat H3 as local delta pending Free/Auth validation | reusable with delta | High | Pro/Free snapshots; PG17 introspection |
| course_editorial_audit | Present | Present | Present | Membership audit is local H3 delta | Pro -> Free/local | Validate append-only and grants in Free | reusable with delta | High | migration `20260830_h3_expanded_contract.sql` |
| admin_members | Not present in returned Pro objects | Not present in returned Free objects | Present locally | H3 RBAC delta absent from baseline snapshots | Pro -> Free/local only | Do not infer Pro changes; request JIT later | new H3 delta | Critical | PG17 introspection |
| admin_membership_audit | Not present in returned Pro objects | Not present in returned Free objects | Present locally | H3 membership audit delta | Pro -> Free/local only | Validate Free after approval | new H3 delta | Critical | PG17 introspection |
| admin_* routines | No routines exposed in Pro read-only result | Not captured | Present locally | Remote metadata unavailable | Pro -> Free/local | Document unavailability; no remote writes | pending evidence | High | read-only snapshot omission |

No rows, users, memberships, UUID fixtures, courses, credentials or operational data were copied. Free/local were not used as sources for Pro changes.
