# ADR-0015 - G5 Deployment-Ready Disabled

| Campo | Valor |
|---|---|
| Estado | `DEPLOYMENT_READY_DISABLED_NOT_CONFIGURED` |
| Fecha | 2026-08-15 |
| Subfase | `F10.9` |
| Alcance | PR D repository-only |
| Gate real | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Trust operacional | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| Connected mode | `IMPLEMENTED_DISABLED_NOT_CONFIGURED` |
| Workflow ejecutado | `NO` |

## Contexto

PR #386 promovio PR C y dejo en `desarrollo` el workflow manual placeholder y el
connected adapter deshabilitado de ADR-0014. El siguiente incremento debe versionar
la forma deployment-ready del camino G5 sin activar ningun recurso remoto ni cambiar
el estado real del gate.

## Decision

El workflow `g5-manual-trust-gate.yml` conserva `workflow_dispatch`, pero el unico
job real queda apagado por defecto mediante el guard
`vars.G5_TRUST_OPERATIONAL_ENABLED == 'true'`, `refs/heads/main` y
`run_attempt == 1`. La variable `G5_TRUST_OPERATIONAL_ENABLED` permanece ausente;
por tanto queda sin workflow ejecutado, deployment ejecutado ni approval consumida.

El job declara la forma futura minima: `environment: Production`, permisos
`contents: read`, `actions: read`, `deployments: read` e `id-token: write`, checkout
pinneado y llamada local al cliente G5. Esa forma no concede Production operativa,
Cloudflare, GitHub App, JWKS/API live ni Supabase live.

El Worker agrega interfaces inyectables y testeadas offline:

- cliente OIDC GitHub Actions con audience fija;
- cliente HTTP de trust broker configurado solo por `G5_TRUST_BROKER_ENDPOINT`;
- validacion de receipt ligado a repository/run/check/environment/deployment;
- consumo local single-use del receipt;
- collector Supabase GET-only publishable-only con paginacion, timeout, limite de
  bytes, SSRF guards, doble snapshot y probes HEAD/GET inyectables.

La configuracion ausente mantiene el modo conectado en
`IMPLEMENTED_DISABLED_NOT_CONFIGURED`. El collector prohibe secret key, Authorization
Bearer para Supabase, metodos write, SQL, RPC, DDL/DML y cualquier writer.

## Fronteras

- Cero Cloudflare deployment o configuracion remota.
- Cero GitHub App configurada o installation token.
- Cero Supabase live, SQL, DDL, DML, RPC, grants, writers o schedules.
- Cero `workflow_dispatch` ejecutado y cero Production operacional.
- Cero gate creado, aprobado o consumido.
- `G5_TRUST_BROKER_ENDPOINT` es una configuracion futura, no presente ni consumida.
- `NEXT_SUPABASE_PUBLISHABLE_KEY` solo representa un contrato futuro publishable-only.

## Criterio De Salida

- Tests offline Node cubren OIDC client, broker HTTP client, receipt single-use y
  collector GET-only.
- Tests Python congelan `IMPLEMENTED_DISABLED_NOT_CONFIGURED` y la fuente protegida
  de PR C mergeado.
- Boundary F10.9 permite solo paths PR D.
- Security, QA, Data Quality y Release revisan sin blockers.
- Commit unico y PR protegido a `desarrollo`; sin merge automatico.
