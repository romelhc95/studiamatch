# ADR-0030 - Separacion CI Y Review Gate

## Estado

`PROPOSED`

## Contexto

`security-audit` era a la vez un gate tecnico y un proxy de review humana: se disparaba en `pull_request_review`, consultaba la Reviews API y exigia una aprobacion con digest repetido en el texto. Si la review llegaba despues del primer run, el PR hacia `desarrollo` podia necesitar rerun manual para que el status requerido reflejara el estado aprobado.

## Decision

Separar responsabilidades:

- `security-audit` valida solo el contrato tecnico: attestation, manifest, digest, `Base-SHA`, `Candidate-SHA`, head real, ancestry, expiry, target level, branch, paths y co-change.
- GitHub branch protection valida review humana nativa: 1 approval, stale review dismissal, last-push approval y `enforce_admins`.
- La review no dispara CI y el preflight no consulta la Reviews API.
- El digest ya no debe repetirse obligatoriamente en el texto de review; sigue siendo obligatorio en la attestation y en la aprobacion R2 por digest externa.

## Consecuencias

- No se requiere rerun manual por emitir review despues del run inicial.
- `security-audit` conserva un unico required status check.
- Branch protection queda como autoridad mecanica unica de review humana.
- `certificacion`, `main`, DB, Supabase, deploys, writers, schedules y cualquier R3 siguen requiriendo grants JIT single-use separados.
