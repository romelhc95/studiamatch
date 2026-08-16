# ADR-0019 - Schema Y Lifecycle Real De GitHub Runtime Para G5

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED_REPOSITORY_ONLY` |
| Fecha | 2026-08-16 |
| Subfase | `F10.9` |
| Alcance | PR I repository-only |
| Operacion remota | `NO` |

## Contexto

PR #391 queda `MERGED_POST_MERGE_VERIFIED`: candidate
`77f475af2e5900bc1338967676ebded71b672642`, merge protegido
`5a76abaae8760a9ce6a418511264e6742fa5c74c`, tree
`9bd83392ade9e245f3fc4ab85bb85eb4f9031040`, Security
`31951803908=PASS`, F9.7 `31951803820=PASS`, focused G5
`95176303149=PASS`, F9.7 job `95176398983=PASS` y `run_attempt=1`.

E1 permanece `COMPLETED`; E2 permanece `NOT_EXECUTED` y queda detenido como
`E2_STOP_GITHUB_RUNTIME_SCHEMA_INCOMPATIBLE` hasta que el adapter use solo campos
reales del runtime GitHub Actions. E2 no configura GitHub App, private key,
installation, secrets, variables ni endpoint.

## Decision

El trust broker no puede depender de campos no garantizados por los endpoints REST
de GitHub Actions. `run.ref_protected` deja de ser autoridad. La proteccion de rama
se valida con `GET /repos/{owner}/{repo}/branches/main`, exigiendo
`branch.name=main` y `branch.protected=true`.

Durante la autorizacion, el workflow y el job autorizados se modelan en curso:
`status=in_progress`, `conclusion=null`, `event=workflow_dispatch` y
`run_attempt=1`. No se exige `success` antes de emitir receipt. Se rechazan runs o
jobs `queued`, `waiting`, `completed`, `cancelled`, `failure`, `skipped`, reruns o
jobs distintos.

`deployment.environment_id` deja de ser autoridad. Los deployments se consultan por
SHA y environment `Production`; luego cada candidate deployment consulta sus
deployment statuses. El deployment seleccionado debe ser exactamente uno y debe
quedar ligado al run/job por `log_url` y `target_url` HTTPS de GitHub con path
`/{owner}/{repo}/actions/runs/{run_id}/job/{job_id}`. Se consulta
`statuses?per_page=100`; 100 resultados o un primer status actual distinto de
`in_progress` detienen por ambiguedad. Se rechazan cero, multiples, redirects,
hostnames alternos, repositorios alternos, run/job distintos y cualquier deployment
aportado por caller.

Las approvals se parsean solo desde `state`, `user.id` y `environments[].id/name`
del endpoint run-scoped `GET /repos/{owner}/{repo}/actions/runs/{run_id}/approvals`.
No se espera `check_run_id`, `deployment_id`, `sha` ni `workflow_sha` en approvals.
Debe existir exactamente una approval `state=approved` para `Production`; el
`environmentId` se deriva desde `approvals.environments` y se comprueba contra
`GET /repos/{owner}/{repo}/environments/Production`.

## Shapes Reales Documentados

| Shape | Endpoint | Campos consumidos | Campos no autoritativos |
|---|---|---|---|
| workflow run | `GET /repos/{owner}/{repo}/actions/runs/{run_id}` | `id`, `repository.id`, `repository.full_name`, `repository.owner.id`, `head_branch`, `run_attempt`, `event`, `status`, `conclusion`, `head_sha`, `actor.id`, `triggering_actor.id` | `ref_protected` |
| workflow jobs | `GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs` | `jobs[].id`, `jobs[].name`, `jobs[].status`, `jobs[].conclusion` | caller job id |
| check runs | `GET /repos/{owner}/{repo}/commits/{sha}/check-runs` | `check_runs[].id`, `check_runs[].name`, `check_runs[].status`, `check_runs[].conclusion` | caller check id |
| branch | `GET /repos/{owner}/{repo}/branches/main` | `name`, `protected` | `run.ref_protected` |
| environment | `GET /repos/{owner}/{repo}/environments/Production` | `id`, `name`, `protection_rules` | caller environment id |
| approvals | `GET /repos/{owner}/{repo}/actions/runs/{run_id}/approvals` | `state`, `user.id`, `environments[].id`, `environments[].name` | `check_run_id`, `deployment_id`, `sha`, `workflow_sha` |
| deployments | `GET /repos/{owner}/{repo}/deployments` | `id`, `sha`, `environment`, `statuses_url`, `repository_url` | `environment_id`, caller deployment id |
| deployment statuses | `GET /repos/{owner}/{repo}/deployments/{deployment_id}/statuses?per_page=100` | `environment`, `state`, `log_url`, `target_url`, `repository_url` | redirects, alternate hostnames |
| commit | `GET /repos/{owner}/{repo}/commits/{sha}` | `sha`, `commit.tree.sha` | caller tree |
| workflow content/blob | `GET /repos/{owner}/{repo}/contents/.github/workflows/g5-manual-trust-gate.yml?ref={candidate_sha}` | `sha` | caller workflow blob |

## Permisos Y Writes

La GitHub App futura conserva permisos read-only: Actions read, Checks read,
Contents read, Deployments read y Metadata read. El unico POST permitido sigue
siendo el exchange del installation token. Approval writes, deployment writes,
workflow writes, `workflow_dispatch`, GitHub App config, Cloudflare deploy,
endpoint enablement y OIDC live permanecen prohibidos en PR I.

## Consecuencias

- E2 sigue `NOT_EXECUTED`.
- Trust sigue `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED`.
- Gate G5 sigue `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED`.
- Runtime flag sigue ausente/false.
- Policy bindings siguen ausentes.
- Endpoint sigue inexistente.
- Hito 1 `60%`, F10.9 `38%` y G5 `50%` se mantienen como tracking-only.
