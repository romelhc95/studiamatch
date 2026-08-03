# Paquete De Evidencia Hito 1

| Campo | Valor |
|---|---|
| ID | `EVID-PACK-H1-001` |
| Estado | `DRAFT_WITH_F9_10_READINESS_CONTROLS_IN_PROGRESS` |
| Hito | `HITO-001` |
| Criterio | `H1-CA1` vigente por adenda |
| Candidate | `desarrollo@5b282461149b7319685cf090534e28051e5eb32c` (F9.8 local), `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17` (PR #277) y controles F9.10 en `certificacion@bc227629b8df1fcabca47ea7be3ea1d5b4c7667b` (PR #282) |

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
evidencia fail-closed (`DEVIATION_ACCEPTED_FAIL_CLOSED`), no como PASS. QA
independiente verifico esa desviacion. PR #282 agrego controles pre-main en
Certification y F9.10 define el gate `main`, canary Production y rollback sin
ejecutarlos. Produccion observada, conformidad, PR a main, canary Production y schedules siguen pendientes. El resultado final debera
indicar claramente que se entrego CA1 y que CA2 se traslado a Hito 2.

## Alcance Entregado

| Elemento | Resultado | Evidencia |
|---|---|---|
| Schedules FG2/FG3 | `LOCAL_CANDIDATE_WITH_F10_GATES_DEFINED` | Workflows con kill switch y environments dedicados; gate main/canary Production definidos; observacion Production pendiente |
| Gates/circuit breaker | `FAIL_CLOSED_CERTIFICATION_QA_VERIFIED` | Runs F9.9 fallaron con salida no cero y cleanup/idempotencia cuando hubo snapshot; QA independiente `PASS` |
| Secrets solo CI | `CI_SECURITY_PASS` | PR #277 `security-audit` y credential scan PASS; no secretos en evidencia F9.9 |
| Development/Certification/Production | `CERTIFICATION_DEVIATION_DOCUMENTED_F9_10_CONTROLS_IN_PROGRESS` | PR #277 y PR #282 Approved/Merged; Production y main pendientes |
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
- Merge desarrollo/certificacion/main: controles pre-main PR #280 en `desarrollo@ac7d46e7a09213a10616297323e2d411b8d10954` / tree `695f5a358979a81c380641e8f800ca3ab62c9f6a`; candidate F9.9 `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17`; controles F9.10 PR #282 en `certificacion@bc227629b8df1fcabca47ea7be3ea1d5b4c7667b` / tree `b2edda7c538b7e74abe0bcaf59715e9d3f4b9327`; `main` pendiente.

## Validaciones

- Local/container: `PASS` para py_compile CA1, assertions focused F9.8 CA1 y replay post-merge Docker/Linux (53 focused + focused jobs CI + F9.7 congelado 226+7 + runners PG17).
- CI: PR #277 PASS (`security-audit`, boundary selectivo, credential scan, Python, typecheck, lint); PR #280 y CI post-merge PASS en `desarrollo`; PR #282 y CI post-merge PASS en `certificacion`; F10/main pendiente.
- Security: `LOCAL_PASS` sin blockers; residual SSRF DNS TOCTOU documentado como riesgo no bloqueante.
- QA independiente: `PASS` segun [QA-F9.9-DEVIATION-001-RESULT](../../operaciones/qa_desviacion_f9_9_resultado.md).
- Canary Certification: `DEVIATION_ACCEPTED_FAIL_CLOSED`, no PASS.
- F9.10 readiness: run `30824041542` PASS read-only/sanitizado; no DML y no sustituye `USER_PERSONAL_UAT`. El canary Production futuro queda definido con artifacts sin slug/SHA/run/digest privado.
- Readiness main-boundary: el manifest real `main -> certificacion` conserva cuatro objetos CA1 historicos permitidos por allowlist exacta (`requirements-db-migrate.txt`, `certification_canary_state.py`, `roi_engine.py`, `test_fase09_9_certification_canary.py`) y requiere revalidacion object/digest en F10.7.
- `EVID-H1-010` futuro requiere canary Production completo `run_fg1=true`, `run_fg2=true`, `run_fg3=true`, `mutable_authorized=true`, limites `5/5/3/3/3`, snapshot privado, restore y segundo restore NOOP. Runs parciales FG2-only/FG3-only seran diagnosticos, no evidencia de cierre.
- `USER_PERSONAL_UAT` queda pendiente y debe registrar solo PASS personal explicito del usuario contra SHA/tree final de `certificacion`, sin PII, secretos ni identificadores internos.
- Definicion QA: [QA-F9.9-DEVIATION-001](../../operaciones/qa_desviacion_f9_9.md); resultado `PASS` sanitizado en [QA-F9.9-DEVIATION-001-RESULT](../../operaciones/qa_desviacion_f9_9_resultado.md).
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
- Las cohortes intentadas quedaron documentadas como sin markers F9.9 residuales y QA verifico el bundle primario disponible.
- Los artifacts disponibles reportaron conteos no-cohorte sin cambio; no se afirma digest de contenido no-cohorte fuera del nivel demostrado por QA.
- FG2 downstream, FG3, canary Production, schedules y conformidad siguen pendientes.
- La desviacion expira con observacion Production completada en F10 o ante un fallo que descarte que el problema fuese el egress observado en Certification.

## Exclusiones Confirmadas

El paquete final debera confirmar que no se promovieron schema, RLS/RPC,
frontend, leads/email, Edge, backfill, admin, Home o Resultados CA2+.

## Riesgos Residuales

Se enlaza el [anexo CA2/RLS](./anexo_h1_ca2_seguridad_rls.md). Ningun riesgo
puede presentarse como mitigado sin evidencia.

## Aprobaciones

- Aprobacion contractual de adenda: `EVID-H1-001=VERIFIED`.
- Revision tecnica: controles pre-main de repositorio aprobados/fusionados en PR #280 con CI post-merge PASS.
- QA: `PASS` para la desviacion F9.9; no autoriza Production ni `main`.
- Readiness F9.10: controles de repositorio en ejecucion; requiere validaciones, PRs SDLC y `USER_PERSONAL_UAT` antes de F10.
- UAT personal: pendiente; checklist sanitizado debe confirmar CA1-only, F10/Production bloqueados hasta nueva autorizacion y aceptacion explicita sobre SHA/tree final.
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
