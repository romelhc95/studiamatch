# F10.9 G5 - Runbook De Activacion Operacional Por Gates Separados

| Campo | Valor |
|---|---|
| Estado | `PREPARED_NOT_CONFIGURED_DEFAULT_BRANCH_TRUSTED_WORKFLOW_REGISTRATION_REQUIRED` |
| Subfase | `F10.9` |
| Alcance | PR Q repository-only posterior a PR #399 |
| Manifest | [`g5_operational_activation_manifest_2026_08_15.json`](./g5_operational_activation_manifest_2026_08_15.json) |
| Preflight offline | `scripts/shared/f10_9_g5_operational_activation_preflight.py` |
| Gate actual | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Trust actual | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| Connected actual | `IMPLEMENTED_DISABLED_NOT_CONFIGURED` |
| Operacion remota en PR M2 | `NO` |

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

CA1 tecnico original permanece `PASS`; el estado integral del Hito 1 queda
`CA_ORIGINAL_PASS_CORRECTIVE_ACCEPTANCE_PENDING`, readiness de evidencias `75%` y
cierre formal `NOT_READY`. Hito 1 `60%`, F10.9 `38%` y G5 `50%` son tracking
tecnico interno, no denominadores de aceptacion.

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

## Reconciliacion PR #396 Y Hardening PR M2

PR #396 queda `MERGED_POST_MERGE_VERIFIED_TRUSTED_BOUNDARY_HARDENING_REQUIRED`:

```text
candidate = 063fb88b3b3dabda78ea641f46da69af09058ab7
merge = 0ec3da6c77b7819a38adcd2f38cd81699adc9283
tree = ecbe760d50f06d0edce0f36ef84fabacb0a4037c
security = 31979524771=PASS
f9_7_run = 31979524732=PASS
focused_g5_job = 95243979388=PASS
f9_7_job = 95244079936=PASS
run_attempt=1
```

PR M2 endurece solo la raiz trusted-boundary ya fusionada:

- check versionado y exclusivo para PR N: `F10.9 Trusted Boundary PR N v1`;
- `pull_request_target` incluye `edited` para cubrir retargets o cambios de metadata;
- PR N no puede modificar `.github/workflows/**` ni el trusted validator
  `scripts/security/f109_trusted_boundary_bootstrap.py`;
- los OIDs se validan como SHA hex exactos antes de cualquier comando Git;
- Git usa config aislada, hooks deshabilitados y fetch `--no-recurse-submodules`;
- `persist-credentials=false` permanece obligatorio;
- el workflow ejecuta codigo del base protegido solamente y no ejecuta codigo,
  scripts, actions ni tests del candidate.

El check `F10.9 Trusted Boundary PR N v1` queda
`NOT_REQUIRED_PENDING_SEPARATE_REMOTE_APPROVAL`. Convertirlo en required check
necesita una aprobacion remota separada posterior a PR M2. El payload sanitizado
preparado para esa accion es
`g5_trusted_required_check_payload_sanitized_2026_08_16.json`; no se ejecuto y debe
detenerse ante drift de branch protection.

El STOP vigente pasa a `E2_STOP_TRUSTED_BOUNDARY_HARDENING_REQUIRED`. E2-E6 siguen
`NOT_EXECUTED`; no se configura GitHub App, Cloudflare, endpoint, OIDC live,
Production, Supabase, SQL, writers, schedules ni branch protection remota.

## Reconciliacion PR #397 Y Cierre PR N

PR #397 queda `MERGED_POST_MERGE_VERIFIED`:

```text
candidate = 8adede3ed10605f3af36e905d8f11e7489815d8a
merge = 9a5fcf539c69b635a41616e52716c0ee34837df4
tree = b33228a031312062b165f8f612d27eacee2fea00
security = 31984379751=PASS
security_audit_job = 95256753465=PASS
f9_7_run = 31984379715=PASS
f9_7_job = 95256780481=PASS
focused_g5_job = 95256691723=PASS
m3_job = 95256691760=PASS
run_attempt=1
```

PR N cierra exclusivamente el hardening `Link` bajo el perfil protegido
`F10.9 Trusted Boundary PR N v1`. El contrato queda
`CANONICAL_REL_ONLY_REJECT_NEXT_AND_UNEXPECTED`: solo se acepta `rel="last"`
canonico, del mismo endpoint solicitado y sin parametros extra; `rel="first"`,
`rel="prev"`, `rel="next"`, parametros adicionales y headers malformados,
ambiguos, duplicados o inesperados fallan cerrado con `STOP_G5_BINDING_DRIFT`.

El payload remoto para convertir `F10.9 Trusted Boundary PR N v1` en required check
queda preparado desde branch protection vivo, preservando `security-audit`,
`strict=true`, `require_last_push_approval=true`, una aprobacion requerida,
`dismiss_stale_reviews=true`, admin enforcement y restricciones nulas observadas.
No se ejecuta sin aprobacion explicita adicional.

El STOP vigente pasa a `E2_STOP_TRUSTED_BOUNDARY_REQUIRED_CHECK_APPROVAL_PENDING`.
E2-E6 siguen `NOT_EXECUTED`; no se configura GitHub App, Cloudflare, endpoint,
OIDC live, Production, Supabase, SQL, writers, schedules, branch protection remota
ni `workflow_dispatch`.

## Reconciliacion PR #398 Y Bootstrap PR O

PR #398 queda `MERGED_POST_MERGE_VERIFIED_TRUSTED_ATTESTATION_MISSING_DEFAULT_BRANCH_REGISTRATION_REQUIRED`:

```text
candidate = d03ee28ce90abcbf8efd7c4b37de99b72717207e
base = 9a5fcf539c69b635a41616e52716c0ee34837df4
merge = 85d7f647a37dc784fe16c11da0318956e255b698
tree = 91706dfcc3766fbf69b4fb8c893318786445a2a9
security = 31992887172=PASS
security_attempt = 1
security_audit_job = 95279485661=PASS
f9_7_run = 31992887025=PASS
f9_7_attempt = 1
f9_7_job = 95279525942=PASS
focused_g5_job = 95279414529=PASS
m3_job = 95279414473=PASS
trusted check=NOT_EXECUTED
```

Causa raiz exacta:

```text
default_branch=main
workflow_exists_in_desarrollo=true
workflow_exists_in_main=false
pull_request_target requires the workflow file on default branch
edited/retry/API enable cannot correct the missing default-branch file
PR #398 no puede acreditarse retroactivamente como merge-gated
```

PR O es `BOOTSTRAP_HUMAN_NOT_SELF_ATTESTED`: prepara el registro repository-only
del workflow trusted en la rama por defecto, pero no puede autoatestiguar su propio
merge. El check futuro cambia a `F10.9 Trusted Boundary PR P v1` y queda asociado
al perfil `PR_P_DEFAULT_BRANCH_REGISTRATION_PROBE`, que exige un unico commit
directo, rechaza forks, prohibe candidate workflows y prohibe modificar
`scripts/security/f109_trusted_boundary_bootstrap.py` desde el candidate.

El workflow conserva `permissions: contents: read`, checkout de base protegida,
`persist-credentials=false`, `submodules=false`, Git con config aislada,
hooks deshabilitados, fetch sin submodules y cero `secrets.*`. No ejecuta codigo,
scripts, actions ni tests del candidate.

La promocion selectiva queda preparada y no ejecutada en
`g5_trusted_workflow_default_branch_promotion_sanitized_2026_08_17.json` con ruta
`desarrollo -> certificacion -> main`. No cambia `default_branch`, no modifica
branch protection, no usa API enable de Actions ni `workflow_dispatch` y preserva
required checks existentes sin mutacion remota.

## Reconciliacion PR #399 Y Hardening PR Q

PR #399 queda `MERGED_POST_MERGE_VERIFIED`:

```text
candidate = 2e7422e9f67e91ee6b02b4b44fccc060248c13a3
base = 85d7f647a37dc784fe16c11da0318956e255b698
merge = ab5b0dffe8fe7d677c083e258e86f590d393b731
tree = fb0b0166b67a58cab14dd0c20e89f034a8adab6e
security = 31998458176=PASS
security_attempt = 1
security_audit_job = 95294350579=PASS
f9_7_run = 31998458172=PASS
f9_7_attempt = 1
f9_7_job = 95294383627=PASS
focused_g5_job = 95294259790=PASS
m3_job = 95294259769=PASS
```

PR Q corrige el hallazgo previo a cualquier promocion: el check requerido preparado
pasa a nombre estable `F10.9 Trusted Boundary v1`, se eliminan `paths` y
`paths-ignore` del workflow `pull_request_target`, y se conserva
`branches=[desarrollo]` con eventos `opened`, `synchronize`, `reopened`,
`ready_for_review` y `edited`.

El perfil PR P exacto se conserva para
`feat/f10-9-pr-p-trusted-boundary-registration-probe`, con delta unico sobre
`.context/operaciones/g5_trusted_boundary_pr_p_probe_2026_08_17.md`, pero el check
esperado pasa a `F10.9 Trusted Boundary v1`.

Los PRs normales fuera de alcance pueden concluir `OUT_OF_SCOPE_SAFE` solo si el
delta no toca superficies trust, F10.9, workflows o trusted-validator protegidas.
Cambios candidate a `.github/workflows/**` o a
`scripts/security/f109_trusted_boundary_bootstrap.py` fallan siempre. Superficies
sensibles sin perfil explicito, forks, metadata inconsistente, SHA invalido, stale
base y mode drift fallan cerrado.

El manifiesto anterior
`g5_trusted_workflow_default_branch_promotion_sanitized_2026_08_17.json` queda
`SUPERSEDED_NOT_EXECUTABLE`. La promocion definitiva queda preparada y no ejecutada
ruta `desarrollo -> certificacion -> main`.

El STOP vigente pasa a `E2_STOP_DEFAULT_BRANCH_TRUSTED_WORKFLOW_REGISTRATION_REQUIRED`.
E2-E6 siguen `NOT_EXECUTED`; no se configura GitHub App, Cloudflare, endpoint,
OIDC live, Production, Supabase, SQL, writers, schedules ni branch protection remota.

## Reconciliacion PR #400 Y Retry CI PR R

PR #400 queda `MERGED_POST_MERGE_VERIFIED_WITH_CI_RETRY`:

```text
candidate = 1995120d98562763f3551f13f9af5db15c087c4c
base = ab5b0dffe8fe7d677c083e258e86f590d393b731
merge = 13a44fb7de6e8d754106b744f96e15c959c45685
tree = b126b5119224010372ea704b87459f98afff2c2a
security = 32025689377=PASS
security_audit_job = 95374636974=PASS
focused_g5_job = 95374505684=PASS
m3_job = 95374505556=PASS
f9_7_run = 32025689461
attempt_1_job = 95374786287=CANCELLED
attempt_1_cancelled_step = Run local-only Python and PostgreSQL contracts
attempt_1_classification = CI_CANCELLED_UNCLASSIFIED_REQUIRES_RERUN
attempt_2_job = 95380342703=PASS
attempt_2_classification = CI_RETRY_PASS
```

El retry es exclusivamente CI. Aunque el run use `run_attempt=2`, el futuro gate
operacional G5 conserva `run_attempt=1` obligatorio y no queda ejecutado.

La promocion definitiva preparada y no ejecutada actualiza su fuente exacta a
`source_commit=13a44fb7de6e8d754106b744f96e15c959c45685` y
`source_tree=b126b5119224010372ea704b87459f98afff2c2a`. Tambien fija path,
modo `100644` y blob SHA exacto para los cuatro archivos promovibles:

```text
.github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml 100644 40d979dd0af57f530e0999ac7736d61ec62b986d
scripts/security/f109_trusted_boundary_bootstrap.py 100644 c814f6124e1d10ad85f455118e22caba6a35ea9b
tests/test_f109_trusted_boundary_bootstrap.py 100644 5dd2d7e6b30cd3c86a81cb7df56db13ef0821aa1
.context/operaciones/g5_trusted_boundary_pr_p_probe_2026_08_17.md 100644 a1853df0c0e6187352869b26984e74576c564db3
```

Cualquier source commit, source tree, path, modo o blob distinto debe fallar
cerrado antes de una promocion futura. PR R no modifica esos cuatro archivos y
no ejecuta promocion a `certificacion` ni `main`.

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
- Link hardening `CLOSED_BY_PR_N_TRUSTED_BOUNDARY`.
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
- ausencia de writes, branch protection ejecutada y operaciones remotas.

El preflight no lee valores reales, no consulta variables de entorno, no realiza red
y no prueba disponibilidad operacional.
