# ADR-0007 - Desviacion Fail-Closed Del Canary Certification F9.9

| Campo | Valor |
|---|---|
| ID | `ADR-0007` |
| Estado | `ACCEPTED` |
| Decision humana | `USER_OWNER_APPROVED_IN_CHAT_2026-08-03` |
| Contexto relacionado | `REQ-EST-001`, `HITO-001`, `TASK-H1-001`, `F9.9`, `PLAN-H1-CA1-ONLY-001` |

## Contexto

F9.9 promovio el candidate selectivo CA1-only a `certificacion` mediante PR #277, aprobado y fusionado en el commit `920ac9c7514f2e5f2e0315bf4cccb95940f3de17`. El gate `security-audit`, el boundary selectivo F9.9 y los checks CI requeridos terminaron en PASS.

El canary Certification posterior demostro que la ruta de control falla de forma cerrada ante condiciones externas no autorizadas o no demostrables. Los runs registrados son evidencia sanitizada; no incluyen URLs privadas, UUIDs operativos, project refs, hosts, secrets ni payloads:

| Run | Resultado sanitizado |
|---|---|
| `30777088545` | Cancelado esperando aprobacion de environment; sin ejecucion efectiva ni entrega de secretos. |
| `30781870451` | FAIL por duplicado normalizado en inventario; cleanup e idempotencia exitosos. |
| `30782109395` | FAIL por source slug no configurado; cleanup e idempotencia exitosos. |
| `30782242009` | FG1 PASS; FG2 FAIL por HTTP 403; cleanup e idempotencia exitosos. |
| `30782360475` | FG1 PASS; FG2 FAIL por HTTP 403; cleanup e idempotencia exitosos. |

La ventana `F99_CERTIFICATION_CANARY_MUTABLE_APPROVED` quedo restaurada a `false`. Las cohortes intentadas quedaron sin markers F9.9 residuales y los artifacts disponibles reportaron cero drift no-cohorte. Los stages FG2 downstream y FG3 no tuvieron validacion positiva.

## Decision

Se acepta la desviacion `DEVIATION_ACCEPTED_FAIL_CLOSED` para la evidencia Certification F9.9. Esta decision acepta el comportamiento fail-closed observado ante HTTP 403 desde egress compartido de GitHub-hosted runners, pero no reclasifica el canary de Certification como resultado positivo.

La validacion positiva de success path se desplaza a un canary Production acotado y a observacion programada posterior, ambos sujetos a autorizaciones separadas, controles pre-main y evidencia nueva.

## Alcance

La desviacion cubre solamente la imposibilidad de completar el success path desde egress compartido en Certification.

La desviacion no cubre:

- errores de credenciales, RLS o target Supabase;
- exposure de secretos;
- failure de cleanup o idempotencia;
- CA2, schema, migrations, backfill, leads/email, frontend o Edge;
- mutaciones fuera de cohorte;
- falsos verdes;
- Production, schedules o `main` sin controles adicionales.

## Controles Compensatorios

Antes de cualquier promocion a `main` deben estar documentados y luego implementados en subfase autorizada:

1. `db-sync-to-pro.yml` en push a `main` solo dry-run/report-only; apply solo por `workflow_dispatch`, aprobacion Production, backup/PITR verificado y autorizacion DDL separada.
2. Environments `Production-Scheduled-FG1`, `Production-Scheduled-FG2` y `Production-Scheduled-FG3` con reviewer humano, branch policy `main`, secrets minimos separados y `AUTOMATION_ENABLED=false` inicial.
3. Gate de automatizacion con preflight asociado al environment programado y output explicito por writer.
4. `PRODUCTION_WRITERS_PAUSED` efectivo y fail-closed antes de cada estacion mutante y antes de migraciones.
5. Canary Production manual, acotado, con host Pro allowlisted, snapshot privado, restore exacto, segundo restore NOOP y artifacts sanitizados, antes de habilitar schedules.
6. Gate main/F10 con boundary CA1-only, cero CA2, credential scan, workflows validos, tests obligatorios, commit/tree/digest inmutables y review humano.
7. Rollback con backup/restore ensayados, responsable, RTO/RPO, cancelacion de jobs activos, deshabilitacion de schedules, rollback de datos, migracion compensatoria si existiera DDL y revert de codigo solo mediante PR forward-only.

## Vigencia Y Expiracion

La desviacion expira cuando se complete la observacion Production aprobada o ante el primer fallo que demuestre que el problema no era exclusivo del egress Certification.

Mientras la observacion no exista, F9.9 permanece abierta y Hito 1 no se declara completado.

## Rollback

La decision se revierte manteniendo `EVID-H1-008=PLANNED/BLOCKED` y exigiendo un canary Certification positivo antes de continuar. No requiere rollback de datos porque esta ADR no ejecuta DDL, DML, workflows, schedules ni Production.

## Consecuencias Para F9.10 Y F10

F9.10 debe revisar la desviacion, confirmar QA independiente y preparar readiness sin ejecutar Production. F10 no puede iniciar hasta que existan controles pre-main, canary Production acotado y aprobaciones separadas.

## Alternativas Rechazadas

- Declarar PASS con HTTP 403 o salida parcial verde.
- Relajar la clasificacion 403 o circuit breakers.
- Rotar instituciones indefinidamente desde la misma IP compartida.
- Presentar replay o datos sembrados como harvest real.
- Promover a `main` sin neutralizar `db-sync-to-pro`, sin environments programados y sin canary Production acotado.

## Enlaces

- [Estado del proyecto](../estado_del_proyecto.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- [PLAN-H1-CA1-ONLY-001](../operaciones/plan_cierre_hito1_ca1_only.md)
- [Certificacion Hito 1 F9](../operaciones/certificacion_hito1_f9.md)
- [Paquete de evidencia Hito 1](../evidencias_cliente/sprint_1/paquete_hito_001.md)
