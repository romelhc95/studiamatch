# ADR-0025 - G5 Default Branch Trusted Workflow Registration

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED_REPOSITORY_ONLY_PR_O_CANDIDATE` |
| Fecha | `2026-08-17` |
| Subfase | `F10.9` |
| Alcance | Bootstrap humano no autoatestiguado para registrar el trusted workflow en default branch |

## Contexto

PR #398 queda `MERGED_POST_MERGE_VERIFIED_TRUSTED_ATTESTATION_MISSING_DEFAULT_BRANCH_REGISTRATION_REQUIRED`: candidate `d03ee28ce90abcbf8efd7c4b37de99b72717207e`, base `9a5fcf539c69b635a41616e52716c0ee34837df4`, merge `85d7f647a37dc784fe16c11da0318956e255b698`, tree `91706dfcc3766fbf69b4fb8c893318786445a2a9`, Security `31992887172=PASS`, `security-audit` job `95279485661=PASS`, F9.7 `31992887025=PASS`, F9.7 job `95279525942=PASS`, focused G5 `95279414529=PASS`, M3 `95279414473=PASS` y trusted check=`NOT_EXECUTED`.

La causa raiz es exacta: default_branch=main; el workflow existe en desarrollo; workflow_exists_in_main=false; `pull_request_target` requires the workflow file on default branch; `edited`/retry/API enable no pueden corregir la ausencia; PR #398 no puede acreditarse retroactivamente como merge-gated.

## Decision

PR O prepara un bootstrap humano no autoatestiguado. El workflow protegido pasa a check futuro `F10.9 Trusted Boundary PR P v1`, con perfil exacto `PR_P_DEFAULT_BRANCH_REGISTRATION_PROBE` para una rama futura `feat/f10-9-pr-p-trusted-boundary-registration-probe`.

El perfil PR P exige un unico commit directo, delta exacto sobre `.context/operaciones/g5_trusted_boundary_pr_p_probe_2026_08_17.md`, rechaza forks, prohibe candidate workflows, prohibe trusted-validator candidate code y conserva inspeccion del candidate solo como Git objects no confiables.

El workflow conserva `contents:read`, `persist-credentials=false`, `submodules=false`, Git aislado, hooks deshabilitados, fetch sin submodules y cero secrets. No ejecuta codigo, scripts, actions ni tests del candidate.

## Promocion Selectiva

Se prepara `g5_trusted_workflow_default_branch_promotion_sanitized_2026_08_17.json` con estado `PREPARED_NOT_EXECUTED` para promocion selectiva `desarrollo -> certificacion -> main`. No se ejecuta en PR O.

## Consecuencias

El STOP vigente queda `E2_STOP_DEFAULT_BRANCH_TRUSTED_WORKFLOW_REGISTRATION_REQUIRED`. CA1 tecnico original permanece `PASS`; Hito 1 queda `CA_ORIGINAL_PASS_CORRECTIVE_ACCEPTANCE_PENDING`; Hito 1 `60%`, F10.9 `38%`, G5 `50%`, readiness `75%` y cierre formal `NOT_READY` no cambian.

No se cambia default_branch, branch protection, Actions por API, GitHub App, Cloudflare, endpoint, OIDC, Production, Supabase, SQL, writers, schedules ni `workflow_dispatch`.

`BK-F10.9-G5-ATOMIC-AUTHORITY` permanece backlog cotizable no ejecutable.
