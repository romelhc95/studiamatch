# ADR-0023 - G5 Trusted Boundary Bootstrap Repository-Only

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED_REPOSITORY_ONLY_BOOTSTRAP_NOT_SELF_ATTESTED` |
| Fecha | `2026-08-16` |
| Subfase | `F10.9` |
| Alcance | PR M bootstrap de raiz de confianza independiente para boundaries G5 |

## Contexto

PR #395 quedo fusionado como `MERGED_POST_MERGE_VERIFIED_TRUSTED_BOUNDARY_BOOTSTRAP_REQUIRED` en `desarrollo@d04a174915910f50b8adf3d4d4b1216ffbc90b75` / tree `b30329f66ad8b8ba36e6cbd51303bd8e729036a0`, con Security `31974315708=PASS`, F9.7 `31974315810=PASS`, focused G5 `95231385472=PASS`, F9.7 job `95231489296=PASS` y `run_attempt=1`.

El siguiente control requerido no es otro cambio runtime, sino una raiz independiente para validar futuros PRs G5 desde codigo de la rama protegida. PR M no puede autoatestiguarse porque el workflow `pull_request_target` nuevo no existe en la base protegida hasta despues del merge humano de PR M.

## Decision

Se agrega `.github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml` como workflow `pull_request_target` read-only con check exclusivo `F10.9 Trusted Boundary Bootstrap`.

El workflow:

- corre con `permissions: contents: read`;
- no referencia `secrets.*`, environments, Cloudflare, Supabase, Production, SQL, writers ni schedules;
- usa solo workflow y codigo de la rama protegida mediante checkout del `base.sha`;
- usa acciones pinneadas por SHA;
- nunca hace checkout ni ejecuta codigo, tests, scripts o acciones del candidate;
- inspecciona commits, parents, ancestry, modes y diff del candidate como Git objects no confiables;
- rechaza forks, repositorios cruzados, branch shapes inesperados, multi-commit candidates, renames, modes inesperados y path/status delta no exacto;
- no sustituye los tests funcionales `pull_request` existentes ni el check `security-audit`.

## Consecuencias

PR M es un bootstrap humano no autoatestiguado: requiere revision humana y los checks `pull_request` existentes para entrar a `desarrollo`. Solo despues del merge de PR M, el check `F10.9 Trusted Boundary Bootstrap` existe como raiz protegida para validar PR N.

El hardening de `Link` no queda cerrado en PR M. PR L conserva sus cambios repository-only como antecedente, pero el cierre protegido queda diferido a PR N despues del merge de PR M.

E2-E6 siguen `NOT_EXECUTED`, con `E2_STOP_TRUSTED_BOUNDARY_BOOTSTRAP_REQUIRED`. El backlog `BK-F10.9-G5-ATOMIC-AUTHORITY` permanece no ejecutable, cotizable y fuera del avance.
