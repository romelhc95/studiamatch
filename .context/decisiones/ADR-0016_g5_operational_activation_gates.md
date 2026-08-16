# ADR-0016 - Activacion Operacional G5 Por Gates Separados

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED_REPOSITORY_ONLY` |
| Fecha | 2026-08-15 |
| Subfase | `F10.9` |
| Alcance | PR E repository-only |
| PR reconciliado | `#387` |
| Resultado PR #387 | `MERGED_POST_MERGE_VERIFIED_WITH_INFRA_RETRY` |
| Gate real | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Trust operacional | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| Connected mode | `IMPLEMENTED_DISABLED_NOT_CONFIGURED` |
| Operacion remota | `NO` |

## Contexto

PR #387 integro PR D en `desarrollo` con workflow G5 deployment-ready disabled,
broker/ledger endurecido y collector GET-only. La evidencia post-merge conserva
ambos attempts del run F9.7:

```text
candidate = d62c8969e7d229bb8d2a9e1f8c6db6a1c4ef4d1d
merge = bd0d82864c26755435e551b835d145b864383810
tree = 135af5a95237a1d4d6e1b977e8bb9ab82ac95e16
security = 31912540519=PASS
focused_pr_d = 95079685172=PASS
m3 = 95079685191=PASS
f9_7_run = 31912540528
attempt_1_job = 95079764790=CANCELLED
attempt_1_classification = CI_INFRA_TIMEOUT_PLAYWRIGHT_APT
attempt_2_job = 95084155346=PASS
attempt_2_classification = CI_RETRY_PASS
attempt_2_run_attempt = 2
```

El retry fue un retry CI de failed jobs por timeout APT en Playwright `--with-deps`.
No reemplaza ni oculta el attempt 1. Tampoco autoriza un rerun operacional G5:
`run_attempt=1` sigue siendo obligatorio para el futuro gate G5 real.

## Decision

G5 avanza a 50% tracking-only porque PR #387 agrega el quinto dominio
repository-only: connected collector deployment-ready disabled. El denominador G5
queda `5/10`:

1. estructura GET-only;
2. routing real;
3. trust-plane;
4. ledger/broker;
5. connected collector deployment-ready.

Permanecen pendientes:

1. workflow real ejecutado;
2. OIDC live;
3. approval real;
4. Production;
5. observacion.

La activacion operacional futura se divide en seis gates separados definidos en
el [runbook G5](../operaciones/g5_operational_activation_runbook_2026_08_15.md):

| Gate | Alcance unico | Estado PR E |
|---|---|---|
| `E1` | Cloudflare Worker/Durable Object trust plane | `DEFINED_NOT_EXECUTED` |
| `E2` | GitHub App read-only | `DEFINED_NOT_EXECUTED` |
| `E3` | Environment `Production` | `DEFINED_NOT_EXECUTED` |
| `E4` | Smoke trust-only sin Production | `DEFINED_NOT_EXECUTED` |
| `E5` | Promocion diagnostica Certification/Main | `DEFINED_NOT_EXECUTED` |
| `E6` | Creacion, aprobacion y consumo G5 | `DEFINED_NOT_EXECUTED` |

Ningun gate concede el siguiente. No se permite combinar deployment, GitHub App,
environment y Production en una sola autorizacion.

## Manifest Y Preflight

El [manifest repository-only](../operaciones/g5_operational_activation_manifest_2026_08_15.json)
contiene solo nombres futuros y estados name-only, sin valores sensibles. Los nombres
son:

- `G5_GITHUB_APP_PRIVATE_KEY`.
- `G5_GITHUB_APP_ID`.
- `G5_OIDC_AUDIENCE`.
- `G5_TRUST_BROKER_ENDPOINT`.
- `G5_TRUST_OPERATIONAL_ENABLED`.

`G5_TRUST_OPERATIONAL_ENABLED` permanece `ABSENT_NOT_CONFIGURED`.

El preflight offline `scripts/shared/f10_9_g5_operational_activation_preflight.py`
valida solo estructura repository-only: nombres, permisos exactos, branch `main`,
environment `Production`, versiones congeladas, gates separados y ausencia de
writes. No lee valores reales, no usa red, no solicita OIDC y no verifica recursos
remotos.

## Permisos Futuros

GitHub App:

- Actions `read`.
- Checks `read`.
- Contents `read`.
- Deployments `read`.
- Metadata `read`.
- Todo `write` prohibido.

Workflow:

- `contents: read`.
- `actions: read`.
- `deployments: read`.
- `id-token: write`.
- Todo otro `write` prohibido.

## Consecuencias

- PR #387 queda transparente como `MERGED_POST_MERGE_VERIFIED_WITH_INFRA_RETRY`.
- Attempt 1 queda preservado como `CI_INFRA_TIMEOUT_PLAYWRIGHT_APT`.
- Attempt 2 queda preservado como `CI_RETRY_PASS`.
- `run_attempt=2` es solo CI; G5 operacional futuro exige `run_attempt=1`.
- Trust real permanece `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED`.
- Connected real permanece `IMPLEMENTED_DISABLED_NOT_CONFIGURED`.
- Gate real permanece `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED`.
- Cloudflare, GitHub App, environments, Production, Supabase, SQL, writers,
  schedules y fuentes permanecen sin ejecutar.

## No Decisiones

- No despliegue Cloudflare.
- No configuracion GitHub App.
- No environment modificado.
- No workflow G5 ejecutado.
- No OIDC live.
- No Production.
- No Supabase, SQL, writers, schedules ni migrations.
- No routes, domains, bindings remotos ni secrets.
