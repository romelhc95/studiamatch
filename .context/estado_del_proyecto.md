# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-07-26`.

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases. El estado vivo de la tarea activa pertenece a la propia tarea.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `F0` | Preservacion | `COMPLETED` | Preservacion verificada. |
| `F1` | Main a certificacion | `COMPLETED` | Convergencia verificada. |
| `F2` | Certificacion a desarrollo | `COMPLETED` | Convergencia verificada. |
| `F3` | Higiene remota | `COMPLETED` | Higiene terminada. |
| `F4` | Bootstrap local | `COMPLETED` | Entorno local verificado. |
| `F5` | Obsidian minimo | `COMPLETED` | Gobierno documental, PR #221 y `SRC-REQ-001` reconciliada. |
| `F6` | Reconciliacion DB-as-Code | `COMPLETED` | PR #223 y #224 fusionados; package forward-only y checksum LF/CRLF validados post-merge. Ningun cambio remoto aplicado. |
| `F7` | G1b minimo | `COMPLETED` | PR #226 fusionado; G1b y postcondiciones F7 validadas post-merge. Package bloqueado. |
| `F8` | Hito 1 funcional | `COMPLETED` | PR #228 fusionado; contrato funcional local y PostgreSQL 17 validados post-merge. Sin aplicacion DB remota. |
| `F9` | Certificacion Hito 1 en Free | `IN_PROGRESS` | F9.1-F9.4 completadas; F9.5 es el siguiente preflight dirigido. Free sigue `reconciled_not_certified`. |
| `F10` | Pro y produccion | `PENDING` | Bloqueada hasta que F9 termine en `free_certified`; incluye canary, `main`, smoke y observacion. |
| `F11` | Cierre final | `PENDING` | Bloqueada hasta completar produccion observada; consolida evidencia final y limpieza autorizada. |

## Subfases F9

| ID | Estado | Identidad vigente |
|---|---|---|
| `F9.1` | `COMPLETED` | Precertificacion local; alias historico `FASE-09`, PR #231/#232 y cierre #233 |
| `F9.2` | `COMPLETED` | Contrato local de promocion; alias historico `FASE-10`, PR #235/#236 |
| `F9.3` | `COMPLETED` | Freeze local; PR #238, remediacion CRLF #239 y replay post-merge Docker sobre checkout Linux limpio |
| `F9.4` | `COMPLETED` | Reconciliacion contractual local; plan simplificado adoptado, definicion remota sustituida y antecedente temporal retirado |
| `F9.5` | `PENDING` | [Preflight Free dirigido](operaciones/preflight_free_f9_5.md); T01 solo tras PASS/aceptacion; no autorizado |
| `F9.6` a `F9.10` | `PENDING` | H-00, schema/T02, plan/ejecucion backfill/T03 y certificacion/T04; gates separados |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase autorizada: ninguna. La autorizacion F9.4 se consume con el merge de su reconciliacion documental y no autoriza F9.5 ni operaciones remotas.
- Siguiente subfase: F9.5 preflight Free read-only dirigido, definida y `PENDING`. Requiere la frase decimal exacta propia antes de cualquier acceso Free o carga de configuracion autorizada.

## Alcance Inmediato

La [macrofase F9](operaciones/certificacion_hito1_f9.md) sigue el [plan simplificado](operaciones/plan_simplificado_hito1.md). Los packages historicos `FASE-09` y `FASE-10` se preservan como F9.1/F9.2 sin renombrar artifacts. F8 permanece byte-identico, `reconciled_not_certified`, con Free/Pro bloqueados. `H1-CA2P` y `TASK-H1-001` siguen en progreso. F9.4 reconcilio el contrato, marco la [definicion remota anterior](operaciones/preflight_free_f9_4.md) como no autorizable y preservo la informacion vigente del antecedente antes de retirarlo. F9.5 no esta autorizada; F10 Produccion y F11 Cierre permanecen pendientes.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
