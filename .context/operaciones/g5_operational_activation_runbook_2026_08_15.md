# F10.9 G5 - Runbook De Activacion Operacional Por Gates Separados

| Campo | Valor |
|---|---|
| Estado | `PREPARED_NOT_CONFIGURED_TRUSTED_BOUNDARY_BOOTSTRAP_REQUIRED` |
| Subfase | `F10.9` |
| Alcance | PR M repository-only posterior a PR #395 |
| Manifest | [`g5_operational_activation_manifest_2026_08_15.json`](./g5_operational_activation_manifest_2026_08_15.json) |
| Preflight offline | `scripts/shared/f10_9_g5_operational_activation_preflight.py` |
| Gate actual | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Trust actual | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| Connected actual | `IMPLEMENTED_DISABLED_NOT_CONFIGURED` |
| Operacion remota en PR M | `NO` |

## Proposito

Este runbook registra E1 ya ejecutado como bootstrap aislado valido y corrige la
secuencia operacional futura sin desplegar Cloudflare, configurar GitHub App,
habilitar endpoint, ejecutar OIDC live, acceder a Production, Supabase o fuentes,
aplicar SQL, crear writers o schedules, ni ejecutar `workflow_dispatch`.

E1 desplego un Worker/Durable Object bootstrap aislado. E1 no acredita trust
operacional porque no existen bindings runtime de policy exacta, GitHub App live,
endpoint aprobado ni smoke trust-only. El trust permanece
`STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` y el gate permanece
`NOT_CREATED_NOT_APPROVED_NOT_CONSUMED`.

## Reconciliacion PR #387

```text
status = MERGED_POST_MERGE_VERIFIED_WITH_INFRA_RETRY
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

`run_attempt=2` pertenece solo al retry CI de F9.7. El gate G5 operacional futuro
mantiene `run_attempt=1` obligatorio para evitar replay, partial rerun o aprobacion
ambigua. El retry CI no constituye gate G5 operacional.

## Reconciliacion PR #390 Y E1

PR #390 queda `MERGED_POST_MERGE_VERIFIED`:

```text
candidate = c36cc9b6efb166f2f840615759793b7917142f38
merge = 9811b19e1527b39366e43907990c4b77d1394f75
tree = edb7c827621fce1089d636b50494405115d348a6
security = 31926378062=PASS
f9_7_run = 31926378069=PASS
focused_g5_job = 95114516929=PASS
f9_7_job = 95114603279=PASS
run_attempt = 1
```

E1 queda registrado como `E1_DEPLOYMENT_PASS` con evidencia sanitizada:

```text
credential_state = E1_CREDENTIAL_REVOKED_AND_LOCAL_REMOVED
worker_count_expected = 1
version = f10.9-g5-trust-broker.v2
binding = G5_ATOMIC_LEDGER
class = G5AtomicLedgerDurableObject
migration_tag = repository-only-v1
dry_run_bundle_sha256 = 5eeada06370b303bdd205f39d907f4ef8bddd091a8b965b65ff9659207acdfdf
deployed_payload_sha256 = 2a7ec2810a225a682f641925b1fe93aa45fff6b7d6e41712a51fcc25e17e360c
workers_dev = false
preview_urls = false
routes = 0
custom_domains = 0
schedules = 0
vars = 0
secrets = 0
endpoint_public = false
```

No se registra account ID, token, Worker ID, deployment ID, URL ni subdomain.

## Reconciliacion PR #391, PR #392 Y STOP E2

PR #391 queda `MERGED_POST_MERGE_VERIFIED`:

```text
candidate = 77f475af2e5900bc1338967676ebded71b672642
merge = 5a76abaae8760a9ce6a418511264e6742fa5c74c
tree = 9bd83392ade9e245f3fc4ab85bb85eb4f9031040
security = 31951803908=PASS
f9_7_run = 31951803820=PASS
focused_g5_job = 95176303149=PASS
f9_7_job = 95176398983=PASS
run_attempt = 1
```

E2 queda `NOT_EXECUTED`. El STOP
`E2_STOP_GITHUB_RUNTIME_SCHEMA_INCOMPATIBLE` queda como antecedente de PR I y
`E2_STOP_SECURITY_REMEDIATION_REQUIRED` queda como antecedente posterior a PR J/K.
Ningun STOP configura GitHub App, private key, installation, secrets, variables ni
endpoint; solo habilita remediaciones repository-only antes de E2.

PR #392 queda `MERGED_POST_MERGE_VERIFIED_SECURITY_REMEDIATION_REQUIRED`:

```text
candidate = b3f9678e0df76ef8f9dfde8af9147a458a2e033b
merge = 0672156ae5ea13a3ba40ab5f4fd4fd184ec5811e
tree = 7fa8e5c26ddaa67450584b43d5b61c9f7b9edc98
security = 31958015767=PASS
f9_7_run = 31958015698=PASS
focused_g5_job = 95191560687=PASS
f9_7_job = 95191665616=PASS
run_attempt = 1
previous_security_auditor_go = PRESERVED
post_merge_security = REMEDIATION_REQUIRED
```

El STOP posterior a PR #392 fue `E2_STOP_SECURITY_REMEDIATION_REQUIRED`. Los seis
hallazgos post-merge quedan registrados: tres altos remediados por binding exacto
de job/check, status temporal deterministico y snapshot doble antes del CAS; dos
medios remediados por identidad ampliada y token limitado al repositorio; un
medio queda como STOP explicito de preflight E2 read-only futuro para confirmar si
environment requiere permiso adicional. No se agrega ese permiso sin evidencia.

## Reconciliacion PR #393 Y Remediacion Residual PR K

PR #393 queda `MERGED_POST_MERGE_VERIFIED_RESIDUAL_REMEDIATION_REQUIRED`:

```text
candidate = 4d5d97bb37ffcd5126d467bde9152e705a895c85
merge = 51aaac5d289226b1f8f16de1daf69a16a084d585
tree = 7e7be8072cc416d76d2034a126d39393cdbcc968
security = 31962569422=PASS
security_aggregate = 95202769920=PASS
branch_reconciliation = 95202690518=PASS
f9_7_run = 31962569598=PASS
focused_g5_job = 95202690713=PASS
f9_7_job = 95202805508=PASS
run_attempt=1
```

PR K queda limitado a remediacion residual repository-only: `terminal confirmation`
del run/job/check/deployment inmediatamente antes del CAS, parser robusto de
`Link rel=next`, `total_count` canonico en workflow jobs, identidad exacta de
GitHub Actions (`id=15368`, `owner.id=9919`), token response con
`repository_selection=selected`, schema exacto y promises/tokens segmentados por
`repositoryId`. No configura GitHub App ni ejecuta E2.

## Reconciliacion PR #394 Y Remediacion Follow-Up PR L

PR #394 queda `MERGED_POST_MERGE_VERIFIED_FOLLOWUP_SECURITY_REMEDIATION_REQUIRED`:

```text
candidate_commit_1 = 7861af0cf94b726d6ce5fadad9ffb6c2274fdcaa
candidate_commit_2 = 03bab905901f62dba7631a9fe0a87290d70802d9
candidate_commit_3 = 82ef6e92c125040cededb4a648d1eedd6d519ecf
merge = 25be9caffe5674156c7515735a15ad45c5ad22e2
tree = 9f81f71bdabb2012ab593b1999cf4df92fa712eb
security = 31968991218=PASS
f9_7_run = 31968990202=PASS
focused_g5_job = 95218353795=PASS
f9_7_job = 95218447778=PASS
run_attempt=1
```

PR L elimina el soporte generico para cadenas follow-up: PR #394 solo se preserva
por la identidad historica exacta de esos tres commits y las remediaciones futuras
deben ser un unico commit directo desde su base congelada.

El STOP antecedente posterior a PR L fue
`E2_STOP_FOLLOWUP_SECURITY_REMEDIATION_REQUIRED`. E2-E6 siguen `NOT_EXECUTED`; no
se configura GitHub App, Cloudflare, endpoint, OIDC live, Production, Supabase,
SQL, writers ni schedules.

La remediacion PR L tambien endurece el contrato repository-only:

- `Link` headers malformados, ambiguos, duplicados o inesperados producen STOP;
  `rel=next` permanece prohibido.
- Los fixtures de installation token son independientes del request y no espejan
  los permisos solicitados.
- Las pruebas mutan workflow run, job/check y deployment durante cada llamada de
  confirmacion terminal.

La carrera residual multi-endpoint queda documentada como
`DOCUMENTED_NO_FULL_ATOMICITY_CLAIM`: Snapshot B y terminal confirmation reducen
la ventana TOCTOU, pero no declaran atomicidad completa sobre endpoints GitHub
separados.

Backlog no ejecutable y cotizable: `BK-F10.9-G5-ATOMIC-AUTHORITY`. No suma avance
al hito, no se implementa en PR L ni PR M y requiere estimacion y aprobacion del
cliente.

## Reconciliacion PR #395 Y Bootstrap PR M

PR #395 queda `MERGED_POST_MERGE_VERIFIED_TRUSTED_BOUNDARY_BOOTSTRAP_REQUIRED`:

```text
candidate = 444c674cf2ff2143bb4b511e88ff6cd30c1fb589
merge = d04a174915910f50b8adf3d4d4b1216ffbc90b75
tree = b30329f66ad8b8ba36e6cbd51303bd8e729036a0
security = 31974315708=PASS
f9_7_run = 31974315810=PASS
focused_g5_job = 95231385472=PASS
f9_7_job = 95231489296=PASS
run_attempt=1
```

PR M agrega la raiz repository-only independiente para boundaries G5:

- workflow `pull_request_target` `.github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml`;
- check exclusivo `F10.9 Trusted Boundary Bootstrap`;
- `permissions: contents: read` y cero `secrets.*`;
- acciones pinneadas por SHA;
- checkout del `base.sha` protegido, sin checkout del candidate;
- inspeccion de Git objects del candidate como `GIT_OBJECTS_AS_UNTRUSTED_DATA`;
- rechazo fail-closed de forks, repos cruzados, multi-commit, ancestry invalido,
  renames, modes inesperados y delta path/status no exacto;
- no sustituye `security-audit`, F9.7 ni los tests funcionales `pull_request`.

PR M es `BOOTSTRAP_HUMAN_NOT_SELF_ATTESTED`: no puede autoatestiguarse antes de
estar fusionado en `desarrollo`, porque el workflow `pull_request_target` corre
exclusivamente desde la rama protegida. La atestacion de PR M depende de revision
humana y checks `pull_request` existentes.

El cierre del hardening `Link` queda `NOT_CLOSED_DEFERRED_TO_PR_N`. PR L conserva
sus cambios repository-only como antecedente, pero PR N debe revalidar/cerrar bajo
el check protegido posterior al merge de PR M.

El STOP vigente pasa a `E2_STOP_TRUSTED_BOUNDARY_BOOTSTRAP_REQUIRED`. E2-E6 siguen
`NOT_EXECUTED`; no se configura GitHub App, Cloudflare, endpoint, OIDC live,
Production, Supabase, SQL, writers ni schedules.

## Policy Runtime Futura

Los SHA/tree/blob dejan de ser autoridad hardcodeada final. La secuencia futura
queda resuelta asi:

1. Se promociona primero el commit diagnostico a `main`.
2. Luego se configuran `G5_ALLOWED_CANDIDATE_SHA`, `G5_ALLOWED_CANDIDATE_TREE` y `G5_ALLOWED_WORKFLOW_BLOB_SHA` con los valores exactos de `main`.
3. El broker consume esos bindings como policy inmutable.
4. Ningun caller puede aportar SHA/tree/blob, workflow, approval, environment, deployment, OIDC claims o receipt.
5. Cualquier fallback a SHA/tree/blob legacy queda prohibido.

Nombres futuros repository-only, todos `ABSENT_NOT_CONFIGURED`:

- `G5_ALLOWED_CANDIDATE_SHA`.
- `G5_ALLOWED_CANDIDATE_TREE`.
- `G5_ALLOWED_WORKFLOW_BLOB_SHA`.
- `G5_GITHUB_APP_PRIVATE_KEY`.
- `G5_GITHUB_APP_ID`.
- `G5_GITHUB_APP_INSTALLATION_ID`.
- `G5_OIDC_AUDIENCE`.
- `G5_TRUST_BROKER_ENDPOINT`.
- `G5_TRUST_RUNTIME_ENABLED`.

`G5_TRUST_RUNTIME_ENABLED` permanece ausente. Este PR no configura secretos,
variables ni environments.

## Permisos Futuros Minimos

GitHub App read-only:

| Permiso | Acceso |
|---|---|
| Actions | `read` |
| Checks | `read` |
| Contents | `read` |
| Deployments | `read` |
| Metadata | `read` |

Todo permiso GitHub App `write` queda prohibido. El POST para obtener installation
token solo se permite contra el endpoint de token de instalacion y con permisos
read-only; cualquier otra llamada GitHub no-GET queda prohibida.

Workflow:

| Permiso | Acceso |
|---|---|
| `contents` | `read` |
| `actions` | `read` |
| `deployments` | `read` |
| `id-token` | `write` |

Todo otro permiso workflow `write` queda prohibido. La rama futura debe ser
`main`, la ref `refs/heads/main`, `run_attempt=1` y environment `Production`.

## Schema GitHub Runtime Real

El adapter PR K consume solo fields reales y no requiere fields inventados:

| Evidencia | Endpoint | Regla |
|---|---|---|
| workflow run | `GET /repos/{owner}/{repo}/actions/runs/{run_id}` | `status=in_progress`, `conclusion=null`, `event=workflow_dispatch`, `run_attempt=1` |
| workflow jobs | `GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page=100` | `total_count` entero seguro igual a `jobs.length`; exact-one job run-scoped, `run_id`, `run_attempt=1`, `head_sha`, `check_run_url`, nombre exacto, `status=in_progress`, `conclusion=null` |
| check run exacto | `GET /repos/{owner}/{repo}/check-runs/{check_run_id}` derivado de `job.check_run_url` | `id`, `check_suite.id`, `head_sha`, nombre exacto, `status=in_progress`, `conclusion=null`, app `GitHub Actions` con `app.id=15368` y `app.owner.id=9919`; sin busqueda independiente por SHA/nombre |
| branch | `GET /repos/{owner}/{repo}/branches/main` | `name=main` y `protected=true`; no se usa `run.ref_protected` |
| environment | `GET /repos/{owner}/{repo}/environments/Production` | exact-one `Production`, id positivo |
| approvals | `GET /repos/{owner}/{repo}/actions/runs/{run_id}/approvals` | solo `state`, `user.id`, `environments[].id/name`; no `check_run_id`, `deployment_id`, `sha`, `workflow_sha` |
| deployments | `GET /repos/{owner}/{repo}/deployments` | filter por SHA y `Production`; no `deployment.environment_id` |
| deployment statuses | `GET /repos/{owner}/{repo}/deployments/{deployment_id}/statuses?per_page=100` | valida `id`, timestamps, `deployment_url`, `log_url`, `target_url`, `environment`; selecciona maximo temporal unico; rechaza `Link rel=next`, 100 resultados, empates, IDs duplicados e `in_progress` historico; terminal confirmation repite status antes del CAS |
| commit | `GET /repos/{owner}/{repo}/commits/{sha}` | SHA y tree derivan del endpoint |
| workflow content/blob | `GET /repos/{owner}/{repo}/contents/.github/workflows/g5-manual-trust-gate.yml?ref={candidate_sha}` | blob SHA deriva del endpoint en el candidate SHA |

El broker rechaza workflow queued, waiting inesperado, completed, cancelled,
failure, skipped o rerun; rechaza job completed o job distinto; rechaza cero o
multiples deployments ligados; rechaza self-review; y rechaza cualquier authority
caller-supplied. El CAS solo ocurre tras snapshot A y snapshot B identicos, seguido
por terminal confirmation; no hay retry interno ante mismatch.

## Orden Operacional Corregido

La secuencia anterior E4-before-E5 queda
`E4_BEFORE_E5_SUPERSEDED_NOT_EXECUTABLE`. El orden vigente es:

| Gate | Alcance unico | Estado |
|---|---|---|
| `E1` | Bootstrap Cloudflare Worker/Durable Object aislado | `COMPLETED` |
| `E2` | GitHub App read-only | `NOT_EXECUTED` |
| `E3` | Environment Production disabled | `NOT_EXECUTED` |
| `E4` | Promocion diagnostica Certification/Main | `NOT_EXECUTED` |
| `E4A` | Binding exacto SHA/tree/blob y redeploy aislado | `NOT_EXECUTED` |
| `E4B` | Exposicion endpoint | `NOT_EXECUTED` |
| `E5` | Smoke trust-only sin data plane | `NOT_EXECUTED` |
| `E6` | Creacion, aprobacion y consumo G5 | `NOT_EXECUTED` |

E5 queda bloqueado hasta que E4, E4A y E4B esten completos. E2-E6 permanecen
`NOT_EXECUTED`. El endpoint permanece inexistente.

## Separacion Trust Plane / Data Plane

El Worker y Durable Object pertenecen al trust plane G5. El trust plane solo valida
identidad, receipt, nonce, `jti`, gate single-use y reason codes. No lee ni escribe
data plane, no consulta Supabase por si mismo y no reemplaza los guards del
collector GET-only. El data plane queda fuera hasta autorizacion separada.

## Gate E1 - Bootstrap Cloudflare Worker/Durable Object

Estado: `COMPLETED`.

E1 desplego un bootstrap aislado con `workers.dev=false`, preview URLs disabled,
cero routes/domains/schedules/vars/secrets y sin endpoint publico. El Worker remoto
no se modifica en PR K; ese bootstrap proviene de PR H y queda como base #391.

STOP posterior a E1:

- Runtime policy binding ausente.
- GitHub App config ausente.
- Endpoint no aprobado.
- `G5_TRUST_RUNTIME_ENABLED` ausente.
- Cualquier intento de data plane.

## Gates Pendientes

E2 GitHub App read-only requiere autorizacion separada, matriz read-only, private
key no registrada y obtencion de installation token con timeout y limites.

E3 Environment Production disabled requiere autorizacion separada y conserva
`G5_TRUST_RUNTIME_ENABLED` ausente hasta que corresponda.

E4 promociona primero el commit diagnostico a `main` para resolver la
autorreferencia SHA/tree/blob sin que el caller aporte valores.

E4A configura bindings exactos y redeploy aislado. Sin E4A, el broker termina STOP.

E4B decide y aprueba endpoint. Sin E4B, no existe endpoint publico.

E5 ejecuta smoke trust-only sin data plane. E5 se bloquea si falta E4, E4A o E4B.

E6 crea, aprueba y consume G5 con `run_attempt=1`, exact-one repository/ref/workflow,
run/environment/approval y receipt single-use.

## Regla De No Combinacion

E1, E2, E3, E4, E4A, E4B, E5 y E6 requieren autorizaciones separadas. No se puede
combinar deployment, GitHub App, environment, endpoint, runtime bindings, smoke y
Production en una sola autorizacion. Un gate PASS no concede el siguiente.

## Preflight Offline

El preflight offline valida solo:

- PR #390 reconciliado.
- PR #391 reconciliado.
- E1 PASS sanitizado.
- E2 STOP schema/lifecycle registrado.
- PR #392 registrado como security remediation required.
- PR #393 registrado como residual remediation required.
- PR #394 registrado como follow-up security remediation required.
- PR #395 registrado como trusted boundary bootstrap required.
- `E2_STOP_TRUSTED_BOUNDARY_BOOTSTRAP_REQUIRED` vigente.
- `E2_STOP_FOLLOWUP_SECURITY_REMEDIATION_REQUIRED` preservado como antecedente.
- Link hardening `NOT_CLOSED_DEFERRED_TO_PR_N`.
- Bootstrap `BOOTSTRAP_HUMAN_NOT_SELF_ATTESTED`.
- Binding runtime con `jobId`, `deploymentStatusId` y `checkSuiteId`.
- Snapshot doble antes de CAS.
- Terminal confirmation antes de CAS.
- Mutaciones durante cada llamada de confirmacion terminal.
- GitHub Actions App exacta por slug/name/id/owner id.
- Installation token limitado a un solo repository id, `repository_selection=selected`, schema exacto y permisos read exactos.
- Fixtures de installation token independientes del request.
- Link headers malformados, ambiguos, duplicados o inesperados rechazados.
- Carrera residual multi-endpoint documentada sin declarar atomicidad completa.
- Backlog `BK-F10.9-G5-ATOMIC-AUTHORITY` no ejecutable y cotizable.
- credencial E1 revocada y removida localmente.
- shapes GitHub reales documentados con identificadores sinteticos.
- presencia futura por nombre y ausencia de valores.
- permisos exactos.
- branch `main` y environment `Production`.
- versions congeladas.
- gates separados y reordenados.
- ausencia de writes y operaciones remotas.

El preflight no lee valores reales, no consulta variables de entorno, no realiza red
y no prueba disponibilidad operacional.
