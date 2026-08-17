# ADR-0024 - G5 Link Header Hardening Closure

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED_REPOSITORY_ONLY_PR_N_CANDIDATE` |
| Fecha | `2026-08-17` |
| Subfase | `F10.9` |
| Alcance | Cierre repository-only del hardening de `Link` bajo `F10.9 Trusted Boundary PR N v1` |

## Contexto

PR #397 queda registrado como `MERGED_POST_MERGE_VERIFIED`: candidate `8adede3ed10605f3af36e905d8f11e7489815d8a`, merge `9a5fcf539c69b635a41616e52716c0ee34837df4`, tree `b33228a031312062b165f8f612d27eacee2fea00`, Security `31984379751=PASS`, `security-audit` job `95256753465=PASS`, F9.7 `31984379715=PASS`, F9.7 job `95256780481=PASS`, focused G5 `95256691723=PASS`, M3 `95256691760=PASS` y `run_attempt=1`.

PR M2 dejo fusionado el check versionado `F10.9 Trusted Boundary PR N v1`; PR N no modifica workflows ni `scripts/security/f109_trusted_boundary_bootstrap.py`. La actualizacion remota de branch protection queda preparada, pero no ejecutada.

## Decision

El contrato `Link` del trust broker queda cerrado como `CANONICAL_REL_ONLY_REJECT_NEXT_AND_UNEXPECTED`:

- solo se acepta una entrada GitHub API ligada al mismo endpoint solicitado, con parametro unico `rel="last"` y query canonica;
- `rel="next"` sigue siendo blocker fail-closed;
- cualquier parametro adicional, incluso bien formado, se considera `Link` inesperado y termina `STOP_G5_BINDING_DRIFT`;
- headers malformados, ambiguos, duplicados o con host no GitHub API siguen rechazados.

## Estado Integral Hito 1

CA1 tecnico original permanece `PASS`. El estado integral queda `CA_ORIGINAL_PASS_CORRECTIVE_ACCEPTANCE_PENDING`, con readiness de evidencias `75%` y cierre formal `NOT_READY`.

Hito 1 `60%`, F10.9 `38%` y G5 `50%` se conservan solo como tracking tecnico interno; no son denominadores de aceptacion contractual.

## Desviacion Permitida

La desviacion se reporta exclusivamente contra:

- CA1 tecnico original: `PASS`, sin cierre correctivo integral.
- Trusted boundary obligatorio: check `F10.9 Trusted Boundary PR N v1` requerido como raiz antes de convertirlo en required check.
- E2-E6: `NOT_EXECUTED`.
- Criterios correctivos FG2: pendientes de gates operacionales posteriores.
- Criterios correctivos FG3: pendientes de gates operacionales posteriores.
- `GO_SCHEDULES`: `NOT_REACHED`.
- Tres pares naturales durante al menos 72 horas: `NOT_STARTED`.
- `EVID-H1-011..013`: `PENDING`.
- `EVID-H1-016`: `PENDING_POST_OBSERVATION`.
- Cierre formal binario: `NOT_READY`.

PRs, commits y tareas no se usan como denominadores de aceptacion. Solo sirven como evidencia tecnica trazable.

## Consecuencias

El cierre `Link` pasa a `CLOSED_BY_PR_N_TRUSTED_BOUNDARY` dentro del candidate repository-only. El bloqueo vivo posterior queda `E2_STOP_TRUSTED_BOUNDARY_REQUIRED_CHECK_APPROVAL_PENDING` hasta aprobacion explicita para modificar branch protection.

`BK-F10.9-G5-ATOMIC-AUTHORITY` permanece backlog cotizable no ejecutable.

No se configura GitHub App, Cloudflare, endpoint, OIDC, Production, Supabase, SQL, writers, schedules ni `workflow_dispatch`.
