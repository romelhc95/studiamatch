# ADR-0034 - Boundary post-merge para pushes de promocion

## Estado

`ACCEPTED_CANDIDATE`

## Contexto

PR #433 valido O2 `desarrollo -> certificacion` antes del merge. Tras el merge, el push a `certificacion` fallo `Canonical Path Boundary` porque el delta `event.before..event.after` incluyo todos los cambios acumulados de la promocion.

## Decision

Los pushes posteriores a merges de promociones O2-O5 se validan con un modo estructural especifico. El modo solo aprueba si confirma por evidencia read-only de GitHub que el `after` es el merge commit de un PR protegido, same-repo, con par O2-O5 exacto, attestation valida, tree del merge igual al tree del head promovido, checks pre-merge verdes, merger `romelhc95` y review `APPROVED` de `romelhc95-approver`.

Si cualquier evidencia falta, el workflow vuelve al boundary incremental existente. No hay skip permisivo.

## Consecuencias

- El push directo sigue gobernado por `validate_work_package.py --changed-from`.
- No se consume de nuevo el grant R3 en el evento push.
- O3 queda bloqueado hasta publicar CI5 en `desarrollo` y re-promoverlo a `certificacion` con un nuevo O2.
- La regla operativa de dos colaboradores queda: `romelhc95` mergea; `romelhc95-approver` aprueba PRs y deployments.
