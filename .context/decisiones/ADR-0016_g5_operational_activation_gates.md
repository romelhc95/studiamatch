# ADR-0016 - Activacion Operacional G5 Por Gates Separados

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED_REPOSITORY_ONLY` |
| Fecha | 2026-08-15 |
| Subfase | `F10.9` |
| Alcance | PR E + PR F + PR G repository-only |
| PR reconciliado | `#387`, `#388`, `#389` |
| Resultado PR #387 | `MERGED_POST_MERGE_VERIFIED_WITH_INFRA_RETRY` |
| Resultado PR #388 | `MERGED_POST_MERGE_VERIFIED` |
| Resultado PR #389 | `MERGED_POST_MERGE_VERIFIED` |
| Resultado PR #390 | `MERGED_POST_MERGE_VERIFIED` |
| E1 | `E1_DEPLOYMENT_PASS` |
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

PR #388 integro PR E en `desarrollo` como paquete repository-only de runbook,
manifest y preflight E1-E6. La evidencia post-merge queda congelada como:

```text
candidate = eb052c2755937a2bf239cd778bc814274fbc846f
merge = 71d6640b990b934fa02401518650ec38dca6cae4
tree = 815a2316c8de67047567d89a9928576869f43c4f
security = 31917838025=PASS
f9_7_run = 31917838011=PASS
focused = 95092629457=PASS
f9_7_job = 95092706912=PASS
run_attempt = 1
```

El preflight operacional read-only de cuenta queda registrado como
`E1_ACCOUNT_READINESS_GO`, con Workers existentes `0` y deployment
`NOT_EXECUTED`. Antes de autorizar deployment, [ADR-0017](ADR-0017_g5_e1_cloudflare_deployment_hardening.md)
mantiene `E1_DEPLOYMENT_STOP_REPOSITORY_HARDENING_REQUIRED` hasta que el paquete
reproducible, aislado y sin endpoints quede promovido por PR protegido.

PR #389 integro PR F y queda congelado como:

```text
candidate = f48d0f25154970531744815e1d3769a20731717a
merge = 4bdc698cd9a8569e4e8290257effa6bc3aa3bb15
tree = 874ccffa3db9871189ca351d88cc84e120251e95
security = 31921056993=PASS
f9_7_run = 31921056963=PASS
focused = 95100885045=PASS
f9_7_job = 95100958336=PASS
run_attempt = 1
```

El hallazgo `E1_DEPLOYMENT_STOP_WRANGLER_FLAG_INCOMPATIBLE` queda registrado por
incompatibilidad de Wrangler `4.30.0` con `deploy --strict`. PR G no ejecuta E1;
solo fija Wrangler exacto `4.44.0`, demuestra `--strict` y valida dry-run offline
sin credenciales Cloudflare.

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

La activacion operacional futura se divide en gates separados definidos en
el [runbook G5](../operaciones/g5_operational_activation_runbook_2026_08_15.md):

| Gate | Alcance unico | Estado repository-only |
|---|---|---|
| `E1` | Cloudflare Worker/Durable Object trust plane | `E1_DEPLOYMENT_PASS` |
| `E2` | GitHub App read-only | `DEFINED_NOT_EXECUTED` |
| `E3` | Environment `Production` | `DEFINED_NOT_EXECUTED` |
| `E4` | Promocion diagnostica Certification/Main | `DEFINED_NOT_EXECUTED` |
| `E4A` | Binding exacto SHA/tree/blob y redeploy aislado | `DEFINED_NOT_EXECUTED` |
| `E4B` | Decision separada de endpoint del trust broker | `DEFINED_NOT_EXECUTED` |
| `E5` | Smoke trust-only sin Production | `DEFINED_NOT_EXECUTED` |
| `E6` | Creacion, aprobacion y consumo G5 | `DEFINED_NOT_EXECUTED` |

Ningun gate concede el siguiente. No se permite combinar deployment, GitHub App,
environment, endpoint y Production en una sola autorizacion. `E5` queda bloqueado
hasta que `E4`, `E4A` y `E4B` tengan aprobacion separada.

No se puede combinar gates operacionales ni reinterpretar un gate completado como
autorizacion implicita del siguiente.

## Manifest Y Preflight

El [manifest repository-only](../operaciones/g5_operational_activation_manifest_2026_08_15.json)
contiene solo nombres futuros y estados name-only, sin valores sensibles. Los nombres
son:

- `G5_GITHUB_APP_PRIVATE_KEY`.
- `G5_GITHUB_APP_ID`.
- `G5_GITHUB_APP_INSTALLATION_ID`.
- `G5_OIDC_AUDIENCE`.
- `G5_TRUST_BROKER_ENDPOINT`.
- `G5_ALLOWED_CANDIDATE_SHA`.
- `G5_ALLOWED_CANDIDATE_TREE`.
- `G5_ALLOWED_WORKFLOW_BLOB_SHA`.
- `G5_TRUST_RUNTIME_ENABLED`.

`G5_TRUST_RUNTIME_ENABLED` permanece `ABSENT_NOT_CONFIGURED`.

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
- PR #388 queda transparente como `MERGED_POST_MERGE_VERIFIED`.
- PR #389 queda transparente como `MERGED_POST_MERGE_VERIFIED`.
- `E1_ACCOUNT_READINESS_GO` no autorizo deployment por si solo.
- `E1_DEPLOYMENT_STOP_REPOSITORY_HARDENING_REQUIRED` queda como blocker historico resuelto por PR F.
- `E1_DEPLOYMENT_STOP_WRANGLER_FLAG_INCOMPATIBLE` queda como blocker historico resuelto por PR G.
- `E1_DEPLOYMENT_PASS` no acredita trust operacional ni habilita E2-E6.
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

## Enmienda PR H - Reconciliacion E1 Y Orden Operacional

PR #390 queda `MERGED_POST_MERGE_VERIFIED` con candidate
`c36cc9b6efb166f2f840615759793b7917142f38`, merge protegido
`9811b19e1527b39366e43907990c4b77d1394f75` y tree
`edb7c827621fce1089d636b50494405115d348a6`. Security `31926378062=PASS`,
F9.7 run `31926378069=PASS`, focused G5 job `95114516929=PASS`, F9.7 job
`95114603279=PASS` y `run_attempt=1` quedan reconciliados.

E1 queda `E1_DEPLOYMENT_PASS` y la credencial queda atestada como
`E1_CREDENTIAL_REVOKED_AND_LOCAL_REMOVED`. La evidencia conservada es solo
sanitizada: version `f10.9-g5-trust-broker.v2`, binding `G5_ATOMIC_LEDGER`, clase
`G5AtomicLedgerDurableObject`, migration tag `repository-only-v1`, digests
sanitizados, `workers.dev=false`, preview URLs disabled, routes/domains/schedules
/vars/secrets `0` y endpoint publico inexistente. No se registra account ID, token,
Worker ID, deployment ID, URL ni subdomain.

E1 desplego un bootstrap aislado valido, pero no acredita trust operacional. El
trust sigue `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED`, el gate sigue
`NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` y E2-E6 siguen `NOT_EXECUTED`.

La secuencia previa E4-before-E5 queda
`E4_BEFORE_E5_SUPERSEDED_NOT_EXECUTABLE`. El orden vigente pasa a: E1 bootstrap
aislado `COMPLETED`; E2 GitHub App read-only; E3 Environment Production disabled;
E4 promocion diagnostica Certification/Main; E4A binding exacto SHA/tree/blob y
redeploy aislado; E4B exposicion endpoint; E5 smoke trust-only sin data plane; E6
creacion, aprobacion y consumo G5.

La policy runtime futura usa solo nombres ausentes: `G5_ALLOWED_CANDIDATE_SHA`,
`G5_ALLOWED_CANDIDATE_TREE`, `G5_ALLOWED_WORKFLOW_BLOB_SHA`,
`G5_GITHUB_APP_INSTALLATION_ID` y `G5_TRUST_RUNTIME_ENABLED`, ademas de los nombres
GitHub App/OIDC ya definidos. El commit de `main` se promociona primero; luego se
configuran SHA/tree/blob exactos; el broker los consume como policy inmutable; ningun
caller puede aportarlos; cualquier fallback a SHA/tree/blob legacy queda prohibido.

Ver [ADR-0018](ADR-0018_g5_trust_live_remediation_repository_only.md).
