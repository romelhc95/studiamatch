# ADR-0012 - Trust-Plane G5 Repository-Only

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED_REPOSITORY_ONLY` |
| Subfase | `F10.9` |
| Gate | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Connected mode | `STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED` |
| Trust operacional | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |

## Contexto

PR #383 fusiono el contrato GET-only v2.3 en `desarrollo@9045c90ac78634f17a66cb3e30e723a2431cb6b4`
/ tree `3d8455a29b63a38906a67343ee4ba6dd15b366d7` con Security, F9.7 y focused
post-merge en PASS. El siguiente corte define el control-plane de confianza sin
ejecutarlo.

## Decision

El trust-plane G5 no acepta autoridad caller-supplied. Un caller no puede aportar
authority, approval, credential, gate status, nonce consumido, proof, `run_id`,
`deployment_id`, SHA o digest aislado como autoridad. Todos esos valores solo tienen
sentido si estan ligados por evidencias inmutables y por una validacion OIDC futura.

El modelo repository-only define `GateIntent`, `GitHubOidcClaims`,
`WorkflowRunEvidence`, `EnvironmentEvidence`, `ApprovalEvidence`,
`DeploymentEvidence` y `GateConsumptionReceipt`. La validacion futura exige issuer
GitHub, audience dedicada, firma/JWKS, claims exactos, `jti` no reutilizado, ref
`refs/heads/main` protegida, `run_attempt=1`, approver numerico distinto del iniciador
y environment `Production` por nombre e ID.

El gate tiene una unica transicion valida: `READY -> CONSUMED`. El consumo requiere
compare-and-set exacto de una sola identidad. Cero, multiples, timeout o resultado
ambiguo terminan STOP. Un gate consumido permanece consumido aunque el diagnostico
falle despues.

El ledger queda como interfaz cerrada sin proveedor remoto en este PR. Si GitHub
deployment/approval no demuestra atomicidad single-use, se requiere
`STOP_G5_ATOMIC_LEDGER_REQUIRED`. `deployment_id` o approval por si solos no son
ledger atomico, y PR A no acepta ningun proof caller-supplied para saltar ese STOP.
El workflow binding futuro usa `romelhc95/studiamatch/.github/workflows/f9-7-contract.yml@refs/heads/main`,
SHA/blob congelados por el repositorio y digests recomputados desde contrato, schema,
algoritmo y capability. Approval se liga a run, check-run, deployment, SHA y workflow
SHA; approvals o receipts futuros respecto de `evaluated_at` son invalidos.

## Consecuencias

- Connected mode sigue bloqueado antes de transporte.
- No se crea workflow Production ni environment remoto.
- No se ejecutan GitHub API live, OIDC live, credentials, SQL, writers ni schedules.
- El futuro workflow autorizado debera ser manual-only, main-only y environment
  `Production` con permisos minimos: `contents:read`, `actions:read`,
  `deployments:read`, `id-token:write`; todo `write` restante queda prohibido.
