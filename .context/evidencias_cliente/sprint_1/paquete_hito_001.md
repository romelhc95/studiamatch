# Paquete De Evidencia Hito 1

| Campo | Valor |
|---|---|
| ID | `EVID-PACK-H1-001` |
| Estado | `DRAFT_WITH_F9_10_TARGET_AWARE_CONTROLS` |
| Hito | `HITO-001` |
| Criterio | `H1-CA1` vigente por adenda |
| Candidate | `desarrollo@5b282461149b7319685cf090534e28051e5eb32c` (PR #270/#271), replay post-merge PASS |

Este documento define la evidencia que se entregara al cliente. No afirma que
Hito 1 este completado.

## Aprobacion Contractual Sanitizada

| Evidencia | Estado | Fecha | Rol aprobador | ID opaco | Digest |
|---|---|---|---|---|---|
| `EVID-H1-001` | `VERIFIED` | `2026-08-01` | `CLIENT_AUTHORIZED_APPROVER` | `RECORDED_PRIVATELY` | `RECORDED_OUT_OF_GIT` |

La evidencia privada permanece fuera de Git. Esta atestacion no copia contenido
comercial, firmas, datos personales, rutas privadas, hashes completos ni
credenciales.

## Resultado Ejecutivo

Candidate local F9.8 CA1-only implementado y replay-validado post-merge en
Docker/Linux (PR #270/#271, `desarrollo@5b282461149b7319685cf090534e28051e5eb32c`).
PR #277 promovio el candidate selectivo a Certification y quedo
aprobado/fusionado; los canaries Certification posteriores se aceptan solo como
`DEVIATION_ACCEPTED_FAIL_CLOSED`, no como PASS. PR #280 agrego controles
pre-main en `desarrollo`, PR #282 los reconstruyo sobre Certification y QA
independiente verifico la desviacion como `PASS`. F9.10 reconstruye ahora los
deltas F10 posteriores de forma target-aware sobre `certificacion@bc227629`,
sin copiar blobs completos de workers. Produccion observada, conformidad
cliente y PR a `main` siguen pendientes en F10/F11.

## Alcance Entregado

| Elemento | Resultado | Evidencia |
|---|---|---|
| Schedules FG2/FG3 | `LOCAL_CANDIDATE` | Workflows con kill switch y environments dedicados; runs pendientes |
| Gates/circuit breaker | `LOCAL_REPLAY_PASS` | Tests focused locales y replay post-merge PASS; ejecucion remota pendiente |
| Secrets solo CI | `CI_SECURITY_PASS` | PR #277/#280/#282 CI y credential scans PASS; F9.10 revalida controles pre-main y canary Production manual |
| Development/Certification/Production | `CERTIFICATION_DEVIATION_DOCUMENTED` | PR #277 Approved/Merged; Production y main pendientes |
| Cero cambios CA2 | `LOCAL_REPLAY_PASS` | Diff `638c51c..M` = 2 paths CI, cero CA2 |

FG1 se valida en un anexo tecnico interno como soporte de inventario. No forma
parte del alcance entregado ni de la conformidad contractual CA1.

## Matriz CA1

| Cambio | Prueba | Ambiente | Umbral | Resultado |
|---|---|---|---|---|
| Cadencia y refs | Workflow contract | Local/CI | PASS | `LOCAL_PASS_CI_PENDING` |
| Gates antes de limites | Tests de orquestacion | Local/Development | PASS | `LOCAL_REPLAY_PASS_REMOTE_PENDING` |
| Circuit breaker | Error/recuperacion | Local/Certification | PASS | `LOCAL_REPLAY_PASS_REMOTE_PENDING` |
| FG2 | Canary y schedule | Certification/Production | Completo, sin mock | `CERTIFICATION_FAIL_CLOSED_PRODUCTION_PENDING` |
| FG3 | HTTP/SSRF/mutacion | Certification/Production | Sin falsos verdes | `PRODUCTION_PENDING` |
| Secrets | Credential scan | CI/Production | Cero exposicion | `CI_PASS_PRODUCTION_PENDING` |
| Frontera CA2 | Object/digest diff | Todos | Cero cambios | `PENDING_REVERIFY_MAIN_CANDIDATE` |

## Identidad Inmutable

- Base commit/tree: `d9c7f180495c985a1e9a0ada4a42525fda60a870` / `7c510dfdbf90a97b97d2358596cab12a8cc4c2a3`.
- Candidate commit/tree: `5b282461149b7319685cf090534e28051e5eb32c` / `d1fe60a403aa213e8a1beb51d49af12aba727cfd`.
- Patch-id y hashes: patch-id estable `ba0f680c09d1d91684f772e326d077676a05370e`; candidate F9.7 congelado `258ef3a98c7c1010efe58522bb1eca892e26390e` / tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de`.
- Merge desarrollo/certificacion/main: `desarrollo` en candidate M; PR #277 fusionado en `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17`; `main` pendiente (F10).

## Validaciones

- Local/container: `PASS` para py_compile CA1, assertions focused F9.8 CA1 y replay post-merge Docker/Linux (53 focused + focused jobs CI + F9.7 congelado 226+7 + runners PG17).
- CI: PR #277/#280/#282 PASS; F9.10 target-aware pendiente de PR/checks sobre `certificacion`.
- Security: `LOCAL_PASS` sin blockers; residual SSRF DNS TOCTOU documentado como riesgo no bloqueante.
- QA independiente: `PASS` para la desviacion F9.9.
- Canary Certification: `DEVIATION_ACCEPTED_FAIL_CLOSED`, no PASS.
- Canary Production: workflow manual `main`-only preparado para F10; ejecucion pendiente y no autorizada en F9.10.
- Schedule observado: pendiente.

## Exclusiones Confirmadas

El paquete final debera confirmar que no se promovieron schema, RLS/RPC,
frontend, leads/email, Edge, backfill, admin, Home o Resultados CA2+.

## Riesgos Residuales

Se enlaza el [anexo CA2/RLS](./anexo_h1_ca2_seguridad_rls.md). Ningun riesgo
puede presentarse como mitigado sin evidencia.

## Aprobaciones

- Aprobacion contractual de adenda: `EVID-H1-001=VERIFIED`.
- Revision tecnica: pendiente para el PR F9.10 target-aware.
- QA: `EVID-H1-015=VERIFIED` para la desviacion F9.9; confirmacion final F9.10 pendiente.
- Aprobacion de release: pendiente.
- Conformidad cliente: pendiente.

## Ledger De Evidencias H1

| ID | Estado |
|---|---|
| `EVID-H1-001` | `VERIFIED` |
| `EVID-H1-002` | `VERIFIED` |
| `EVID-H1-003` | `VERIFIED` |
| `EVID-H1-004` | `VERIFIED` |
| `EVID-H1-005` | `VERIFIED` |
| `EVID-H1-006` | `VERIFIED` |
| `EVID-H1-007` | `VERIFIED` |
| `EVID-H1-008` | `DEVIATION_ACCEPTED_FAIL_CLOSED` |
| `EVID-H1-009` | `PLANNED` |
| `EVID-H1-010` | `PLANNED` |
| `EVID-H1-011` | `PLANNED` |
| `EVID-H1-012` | `PLANNED` |
| `EVID-H1-013` | `PLANNED` |
| `EVID-H1-014` | `PENDING_REVERIFY_MAIN_CANDIDATE` |
| `EVID-H1-015` | `VERIFIED` |
| `EVID-H1-016` | `PLANNED` |
