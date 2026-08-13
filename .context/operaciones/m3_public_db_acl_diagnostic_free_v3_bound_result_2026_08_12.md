# F10.10 M3 - Resultado Sanitizado Del Diagnostico ACL PUBLIC Bound

| Campo | Valor |
|---|---|
| Gate | `APPROVE_F10_10_M3_PUBLIC_DB_ACL_DIAGNOSTIC_FREE_V3_BOUND` |
| Estado del gate | `CONSUMED_ONCE` |
| Decision | `STOP_PUBLIC_DB_ACL_REMEDIATION_REQUIRED` |
| Estado resultante | `M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_CANDIDATE_PENDING_PROMOTION` |
| Autoridad merge/tree | `7034d93059da92b34fb77b06b870ad254f192623` / `a86b31d562d3ae094afe1b46da297827eee07020` |
| Candidate merge/tree | `daf3e5babb2f6185304973e4f7607d95d85ab130` / `da047276b78cea8c1a2b8bf7048a6f40c0146f2b` |
| Binding blob | `da3ffe218a94a411b67598c1ce1962a3314d67fb` |
| Binding content digest | `sha256:18ceca81c5308de44618c7275cf41fd300041c7ef9a57dd167ff2e87badb4c96` |
| Checks bound | `security-audit 31652117290=PASS`; `PostgreSQL 17 31652117293=PASS` |
| Payload blob | `d76b75a4876e600d1a7203c24456ab34ad49c1af` |
| Payload content digest | `sha256:c3a9279ad789b7809af030f3b68ab8e5491aef4789cb89adcd7e433caf3ece2c` |
| Envelope digest | `sha256:82a5848a8ac5958aa781424a436687117f1c39b7dc07f686993b0765bf110a6d` |
| Ejecucion | Una llamada `execute_sql`; sin retry; PostgreSQL 17 `REPEATABLE READ READ ONLY` |

## Resultado

| Clase | Conteos publicados | Conformidad |
|---|---|---|
| `TARGET` (`postgres`) | total 1; conectable `true`; `PUBLIC CONNECT=1`; violaciones 1 | `NONCONFORMANT` |
| `OTHER_CONNECTABLE` | conectables 1; violaciones 1 | `NONCONFORMANT` |
| `NON_CONNECTABLE` | total 1; `PUBLIC CONNECT=1`; `PUBLIC TEMPORARY=0`; `PUBLIC CREATE=0` | `CONFORMANT_IMMUTABLE` |

La clase `NON_CONNECTABLE` conserva conformidad porque `CONNECT` es solo ACL
formal sin capacidad mientras la base permanezca no conectable. La clasificacion
y este resultado quedan inmutables; cualquier cambio de conectabilidad exige una
nueva autoridad y no reinterpreta esta evidencia.

## Limites Verificados

- Cero filas de aplicacion leidas.
- Cero DDL, DML, RPC, provider, writer o acceso Pro.
- Cero retry y cero continuidad automatica.
- DDL reader v1/v2 permanecen consumidas, revertidas y no reutilizables.
- Q0, lectura funcional y teardown permanecen no consumidos.
- M4-M10, F10.9/G4, Certification, Pro, schedules y F11.1 permanecen bloqueados.

## Continuidad Propuesta

Los unicos gates futuros propuestos son
`APPROVE_F10_10_M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_FREE_V2`,
`APPROVE_F10_10_M3_PUBLIC_DB_ACL_REMEDIATION_FREE_V1`,
`APPROVE_F10_10_M3_PUBLIC_DB_ACL_POSTFLIGHT_FREE_V1` y, despues de un postflight
conforme, reader v3. Esta evidencia no los crea, aprueba ni consume.

La evidencia publica solo bindings, conteos y flags sanitizados. La unica base
nombrada es `postgres`, por ser la politica publica declarada para `TARGET`.
