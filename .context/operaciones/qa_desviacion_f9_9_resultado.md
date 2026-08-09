# QA-F9.9-DEVIATION-001 - Resultado Sanitizado

| Campo | Valor |
|---|---|
| ID | `QA-F9.9-DEVIATION-001-RESULT` |
| Estado | `PASS` |
| Evidencia objetivo | `EVID-H1-015` |
| Subfase | `F9.9` |
| Candidate runtime | `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17` |
| Revisor | `INDEPENDENT_QA_REVIEWER` / `QA-AGENT-F9-9-2026-08-03` |
| Fecha UTC | `2026-08-03` |

La revision fue read-only sobre evidencia existente. No ejecuto workflows, no accedio
a Supabase o Cloudflare, no uso secrets, no aplico DDL/DML, no habilito schedules,
no abrio Production ni cambio `main`.

## Independencia

El revisor declara no haber actuado como implementador, operador de canaries,
aprobador de PR #277, aprobador de ADR-0007 ni redactor del cambio de estado.

## Runs Revisados

| Run | Resultado QA sanitizado |
|---|---|
| `30777088545` | `NOT_EXECUTED`: cancelado esperando aprobacion, sin runner, steps, logs, artifacts ni consumo de secrets. |
| `30781870451` | `FAIL_CLOSED`: guards PASS, FG1 PASS, FG2 sale no-cero por inventario invalido/duplicado; downstream y FG3 skipped; post-manifest, restore, idempotencia y artifact upload PASS. |
| `30782109395` | `FAIL_CLOSED`: guards PASS, FG1 sale no-cero por source no configurado; FG2/FG3 skipped; post-manifest, restore, idempotencia y artifact upload PASS. |
| `30782242009` | `FAIL_CLOSED`: guards PASS, FG1 PASS, FG2 sale no-cero por HTTP 403 observado desde GitHub-hosted runner egress; downstream y FG3 skipped; cleanup/idempotencia PASS. |
| `30782360475` | `FAIL_CLOSED`: misma clase que `30782242009`; FG1 PASS, FG2 HTTP 403 no-cero, downstream y FG3 skipped, cleanup/idempotencia PASS. |

## Artifacts Sanitizados

| Run | Artifact | Digest publico |
|---|---|---|
| `30781870451` | `f9-9-certification-canary-manifests-30781870451-1` | `sha256:1c1966e65b11be43e4109586a3dc296b38dc63df40a0277ab33ffc8384f9a84e` |
| `30782109395` | `f9-9-certification-canary-manifests-30782109395-1` | `sha256:26e4694af6f9ae54c94c30af9b89b042b7925e6745c10786c7afc348978c4202` |
| `30782242009` | `f9-9-certification-canary-manifests-30782242009-1` | `sha256:69220c666671ca94481b55dbbb132dda770b7484badd73dfd358bfc1177efeba` |
| `30782360475` | `f9-9-certification-canary-manifests-30782360475-1` | `sha256:cf853dcd7ea6cb9335d5b581aaa167fcf03b73d232822190cca1ad6d374ba0ca` |

Los artifacts primarios permanecen fuera de Git. Esta nota no copia URLs privadas,
project refs, hosts, UUIDs operativos, payloads, logs completos, rutas locales
privadas, secrets ni datos de filas.

## Checklist

| Asercion | Estado |
|---|---|
| Jobs negativos no concluyen success | `PASS` |
| Guards de target/limites pasan antes de mutacion | `PASS` |
| HTTP 403: FG1 PASS y FG2 no-cero | `PASS` |
| Downstream/FG3 skipped despues de fallo | `PASS` |
| Post-manifest generado tras fallo controlado | `PASS` |
| Restore mutable state e idempotencia PASS | `PASS` |
| Fallo de cleanup/idempotencia habria mantenido outcome FAIL | `PASS` |
| Evidencia sanitizada sin identificadores prohibidos | `PASS` |
| Cohortes sin markers residuales segun evidencia primaria | `PASS` |
| Datos no-cohorte limitados al nivel demostrado | `PASS` |
| No reclasifica desviacion como Certification PASS | `PASS` |

## Limites De Claim

- Este resultado valida comportamiento fail-closed, no success path.
- No valida FG2 downstream, FG3, Production, schedules, F9.10/F10 readiness ni cierre de Hito 1.
- HTTP 403 se declara solo como observado desde egress de GitHub-hosted runners; no se afirma causa raiz exclusiva.
- `EVID-H1-015` puede marcarse `VERIFIED` por este PR documental, sin autorizar Production, schedules, `main`, DDL/DML, backup/restore, writers ni nuevas ejecuciones Certification.
