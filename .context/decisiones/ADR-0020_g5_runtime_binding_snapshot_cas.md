# ADR-0020 - G5 Runtime Binding, Snapshot Doble Y CAS

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED` |
| Fecha | 2026-08-16 |
| Subfase | `F10.9` |
| Alcance | PR J repository-only post-merge PR #392 |
| Gate actual | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Trust actual | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| STOP E2 | `E2_STOP_SECURITY_REMEDIATION_REQUIRED` |

## Contexto

PR #392 quedo mergeado y verificado por CI, pero la auditoria Security Auditor
post-merge exigio remediacion antes de crear o configurar la GitHub App E2. El
GO anterior no se oculta: queda preservado como evidencia de que el candidate PR
I paso los checks, pero el estado operativo pasa a remediacion requerida.

## Decision

El broker G5 solo puede ligar el check run desde el job run-scoped:

- Se obtiene el job con `GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page=100`.
- `job.check_run_url` debe apuntar a `https://api.github.com/repos/{owner}/{repo}/check-runs/{id}`.
- No se permite busqueda independiente por SHA/nombre en arrays de check-runs.
- El check exacto se consulta desde esa URL y debe pertenecer a GitHub Actions.

El deployment status vigente se selecciona despues de validar todos los statuses:

- `id` positivo, timestamps validos, `deployment_url`, `log_url`, `target_url`, `environment` y `repository_url` exactos.
- Se rechazan `Link rel=next`, 100 resultados, IDs duplicados, timestamps invalidos, empates temporales y regresion temporal.
- Se selecciona un maximo temporal unico; cualquier `in_progress` historico posterior/inferior invalida la evidencia.

El CAS se ejecuta solo despues de doble snapshot:

- Snapshot A obtiene run, job, check, branch, environment, approval, commit, workflow blob, deployment y deployment status.
- Snapshot B reconsulta la misma evidencia inmediatamente antes del CAS.
- La identidad estable debe ser identica; no existe retry interno ante mismatch.
- Cambios de run, job, check, deployment status, branch protection o approval detienen el consumo.

La identidad del gate incluye `jobId`, `deploymentStatusId` y `checkSuiteId`. `checkSuiteId` se incluye porque `check_run.check_suite.id` es expuesto por REST como identificador autoritativo y estable del check exacto consultado.

## Token De Instalacion

El unico POST permitido sigue siendo el exchange de installation token. Debe enviar
`repository_ids` con exactamente el `repository_id` verificado desde OIDC y debe
validar que la respuesta contiene exactamente `romelhc95/studiamatch`.

Permisos exactos:

- `actions: read`.
- `checks: read`.
- `contents: read`.
- `deployments: read`.
- `metadata: read`.

Permisos ausentes, adicionales o `write` quedan prohibidos.

## Consecuencias

- E2 permanece `NOT_EXECUTED`.
- El endpoint sigue inexistente.
- `G5_TRUST_RUNTIME_ENABLED` sigue ausente o false.
- No se configura GitHub App, private key ni installation ID.
- No se despliega Cloudflare ni se modifica Worker remoto.
- No se ejecuta OIDC live, `workflow_dispatch`, Production, Supabase, SQL, writers ni schedules.
- Un preflight E2 read-only futuro debe confirmar si el endpoint de environment requiere permiso adicional; no se agrega ningun permiso sin evidencia.
