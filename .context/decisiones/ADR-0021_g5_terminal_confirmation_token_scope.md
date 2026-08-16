# ADR-0021 - G5 Terminal Confirmation Y Token Scope Residual

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED` |
| Fecha | 2026-08-16 |
| Subfase | `F10.9` |
| Alcance | PR K repository-only post-merge PR #393 |
| Gate actual | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Trust actual | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| Connected actual | `IMPLEMENTED_DISABLED_NOT_CONFIGURED` |

## Contexto

PR #393 queda reconciliado como `MERGED_POST_MERGE_VERIFIED_RESIDUAL_REMEDIATION_REQUIRED`:

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

La remediacion anterior dejo el CAS doble como defensa principal. La revision residual exige cerrar la ventana TOCTOU final entre Snapshot B y el CAS, endurecer parsing de paginacion y fijar mas estrictamente la identidad runtime de GitHub Actions y el token de instalacion.

## Decision

El broker debe ejecutar `terminal confirmation` despues de Snapshot B e inmediatamente antes del CAS:

- Reconsulta workflow run, workflow job, check run y deployment status.
- Compara `repositoryId`, `runId`, `runAttempt`, `checkRunId`, `checkSuiteId`, `jobId`, `deploymentId` y `deploymentStatusId`.
- No se permite ninguna solicitud externa despues de la confirmacion terminal y antes del CAS.
- No hay retry interno del CAS.

El adapter GitHub App queda endurecido asi:

- El check run debe pertenecer a `GitHub Actions` con `app.slug=github-actions`, `app.name=GitHub Actions`, `app.id=15368` y `app.owner.id=9919`.
- `workflow jobs` debe exponer `total_count` entero seguro, igual a `jobs.length`, y sin paginacion pendiente.
- El parser de `Link` rechaza cualquier `rel=next`, aunque el header sea valido pero no canonico.
- El token response acepta solo el schema esperado, requiere `repository_selection=selected` y prohibe permisos adicionales o `write`.
- La cache de promises/tokens de instalacion se segmenta por `repositoryId`.

## Consecuencias

- E2 permanece `NOT_EXECUTED`.
- E3, E4, E4A, E4B, E5 y E6 permanecen `NOT_EXECUTED`.
- El endpoint sigue inexistente y `G5_TRUST_RUNTIME_ENABLED` sigue ausente o false.
- No se configura GitHub App, private key, installation ID, Cloudflare, endpoint, OIDC live, Production, Supabase, SQL, writers ni schedules.
- Hito 1 `60%`, F10.9 `38%` y G5 `50%` permanecen sin cambio.
