# ADR-0014 - G5 Manual Workflow Y Connected Adapter Repository-Only Deshabilitados

| Campo | Valor |
|---|---|
| Estado | `REPOSITORY_ONLY_WORKFLOW_CONNECTED_PR_C_LOCAL_CANDIDATE` |
| Fecha | 2026-08-15 |
| Subfase | `F10.9` |
| Alcance | PR C repository-only |
| Deployment | `NOT_DEPLOYED` |
| Workflow dispatch | `NOT_EXECUTED_DISABLED_PLACEHOLDER` |
| Connected adapter | `STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED` |
| Gate real | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |

## Contexto

PR #385 integro el trust broker repository-only y quedo verificado post-merge en
`desarrollo`. El siguiente incremento de G5 necesita representar en repositorio el
workflow manual futuro y la frontera de adapter conectado sin activar ningun
transporte, environment, OIDC live, GitHub App ni Cloudflare remoto.

## Decision

Se agrega un workflow manual placeholder con `workflow_dispatch`, permisos vacios y
un unico job `if: false`. El workflow existe solo para versionar la forma futura;
no declara `environment`, no solicita `id-token`, no lee secrets, no invoca
Cloudflare, no llama GitHub API y no puede crear gate.

Se agrega `G5ConnectedGithubAppAdapter` como adapter conectado deshabilitado. Su
constructor exige `enabled=false` y `authoritativeEvidence()` termina siempre con
`STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED` antes de cualquier transporte. No contiene
URL remota, token, fetch, endpoint, Bearer, GitHub API live ni JWKS live.

La policy congelada del broker avanza al merge protegido de PR #385:

```text
protected_source = 191539de71cbff95552c476463305e8d6f3e4b73
tree = 7fe13bb907053f4dea51ac593b5df0de78cb40d6
workflow_blob = 4b3dfb155081f9c3c9b638373b6e5aa2a06cca65
```

## Fronteras

- Cero deployment Cloudflare.
- Cero configuracion GitHub App.
- Cero `workflow_dispatch` ejecutado.
- Cero OIDC/GitHub API/JWKS live.
- Cero Production, Supabase, SQL, writers o schedules.
- Trust operacional permanece `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED`.
- Connected mode permanece `STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED`.

## Criterio De Salida

- Tests offline del Worker y adapter conectado deshabilitado pasan.
- Boundary valida base/tree PR #385, allowlist exacta y marcadores disabled.
- Security, QA, Data Quality y Release revisan sin blockers.
- Commit unico y PR protegido a `desarrollo`; sin merge automatico.
