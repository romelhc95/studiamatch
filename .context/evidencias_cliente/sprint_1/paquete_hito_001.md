# Paquete De Evidencia Hito 1

| Campo | Valor |
|---|---|
| ID | `EVID-PACK-H1-001` |
| Estado | `DRAFT_WITH_F9_9_DEVIATION_DOCUMENTED` |
| Hito | `HITO-001` |
| Criterio | `H1-CA1` vigente por adenda |
| Candidate | `desarrollo@5b282461149b7319685cf090534e28051e5eb32c` (F9.8 local) y `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17` (PR #277) |

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
Docker/Linux. PR #277 promovio el candidate selectivo a Certification y quedo
aprobado/fusionado; los canaries Certification posteriores se aceptan solo como
evidencia fail-closed (`DEVIATION_ACCEPTED_FAIL_CLOSED`), no como PASS. Produccion
observada, conformidad, PR a main, canary Production, schedules y QA siguen
pendientes. El resultado final debera indicar claramente que se entrego CA1 y
que CA2 se traslado a Hito 2.

## Alcance Entregado

| Elemento | Resultado | Evidencia |
|---|---|---|
| Schedules FG2/FG3 | `LOCAL_CANDIDATE` | Workflows con kill switch y environments dedicados; observacion Production pendiente |
| Gates/circuit breaker | `FAIL_CLOSED_CERTIFICATION_OBSERVED_PENDING_QA` | Runs F9.9 fallaron con salida no cero y cleanup/idempotencia cuando hubo snapshot; revision QA independiente pendiente |
| Secrets solo CI | `CI_SECURITY_PASS` | PR #277 `security-audit` y credential scan PASS; no secretos en evidencia F9.9 |
| Development/Certification/Production | `CERTIFICATION_DEVIATION_DOCUMENTED` | PR #277 Approved/Merged; Production y main pendientes |
| Cero cambios CA2 | `CERTIFICATION_BOUNDARY_PASS_MAIN_PENDING` | Gate selectivo F9.9 PASS; reverify requerido contra candidate main |

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
| Secrets | Credential scan | CI/Production | Cero exposicion | `LOCAL_SECURITY_PASS_CI_PENDING` |
| Frontera CA2 | Object/digest diff | Todos | Cero cambios | `LOCAL_TREE_CLOSED_REMOTE_PENDING` |

## Identidad Inmutable

- Base commit/tree: `d9c7f180495c985a1e9a0ada4a42525fda60a870` / `7c510dfdbf90a97b97d2358596cab12a8cc4c2a3`.
- Candidate commit/tree: `5b282461149b7319685cf090534e28051e5eb32c` / `d1fe60a403aa213e8a1beb51d49af12aba727cfd`.
- Patch-id y hashes: patch-id estable `ba0f680c09d1d91684f772e326d077676a05370e`; candidate F9.7 congelado `258ef3a98c7c1010efe58522bb1eca892e26390e` / tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de`.
- Merge desarrollo/certificacion/main: `desarrollo@df18dc0c4c516e998071498d1db8792f7891f766`; `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17`; `main` pendiente.

## Validaciones

- Local/container: `PASS` para py_compile CA1, assertions focused F9.8 CA1 y replay post-merge Docker/Linux (53 focused + focused jobs CI + F9.7 congelado 226+7 + runners PG17).
- CI: PR #277 PASS (`security-audit`, boundary selectivo, credential scan, Python, typecheck, lint); F10/main pendiente.
- Security: `LOCAL_PASS` sin blockers; residual SSRF DNS TOCTOU documentado como riesgo no bloqueante.
- QA independiente: pendiente.
- Canary Certification: `DEVIATION_ACCEPTED_FAIL_CLOSED`, no PASS.
- Definicion QA: [QA-F9.9-DEVIATION-001](../../operaciones/qa_desviacion_f9_9.md) pendiente de ejecucion.
- Canary Production: pendiente.
- Schedule observado: pendiente.

## Desviacion F9.9 Certification

La decision [ADR-0007](../../decisiones/ADR-0007_desviacion_canary_certification_f9_9.md)
acepta evidencia fail-closed sin cerrar el Hito:

| Run | Estado sanitizado |
|---|---|
| `30777088545` | Cancelado esperando aprobacion; sin ejecucion ni secretos. |
| `30781870451` | FAIL por duplicado normalizado en inventario; cleanup e idempotencia exitosos. |
| `30782109395` | FAIL por source slug no configurado; cleanup e idempotencia exitosos. |
| `30782242009` | FG1 PASS; FG2 FAIL por HTTP 403; cleanup e idempotencia exitosos. |
| `30782360475` | FG1 PASS; FG2 FAIL por HTTP 403; cleanup e idempotencia exitosos. |

Condiciones:

- No se declara resultado positivo de Certification.
- `F99_CERTIFICATION_CANARY_MUTABLE_APPROVED` quedo restaurado a `false`.
- Las cohortes intentadas quedaron documentadas como sin markers F9.9 residuales; QA debe verificar el bundle primario.
- Los artifacts disponibles reportaron conteos no-cohorte sin cambio; no se afirma digest de contenido no-cohorte hasta QA.
- FG2 downstream, FG3, QA, canary Production, schedules y conformidad siguen pendientes.
- La desviacion expira con observacion Production completada en F10 o ante un fallo que descarte que el problema fuese el egress observado en Certification.

## Exclusiones Confirmadas

El paquete final debera confirmar que no se promovieron schema, RLS/RPC,
frontend, leads/email, Edge, backfill, admin, Home o Resultados CA2+.

## Riesgos Residuales

Se enlaza el [anexo CA2/RLS](./anexo_h1_ca2_seguridad_rls.md). Ningun riesgo
puede presentarse como mitigado sin evidencia.

## Aprobaciones

- Aprobacion contractual de adenda: `EVID-H1-001=VERIFIED`.
- Revision tecnica: controles pre-main de repositorio implementados como candidate local/CI; pendiente review/merge y QA independiente.
- QA: pendiente.
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
| `EVID-H1-015` | `PENDING` |
| `EVID-H1-016` | `PLANNED` |
