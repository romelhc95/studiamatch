# Estado Del Proyecto

Fecha de corte: 2026-07-24.

## Baseline Git

| Referencia | Commit | Tree |
|---|---|---|
| `main` | `d8f1ea0b210f2a1cf95e73751621cf8b4fcf0f93` | `0c7d31a392612001b786e2ef680cc0be3d1b4c18` |
| `certificacion` | `4d0293b0b36e36494256a574ff49edc0b7e3be7d` | `0c7d31a392612001b786e2ef680cc0be3d1b4c18` |
| `desarrollo` | `3e2b67247c4a92890ee074da239b5da2880f78b6` | `0c7d31a392612001b786e2ef680cc0be3d1b4c18` |
| Local `feat/obsidian-minimo` | baseline `desarrollo@3e2b67247c4a92890ee074da239b5da2880f78b6` | Igual a desarrollo al crear la rama |

La ancestry `main -> certificacion -> desarrollo` esta limpia y los trees convergieron. Solo existen tres ramas remotas permanentes: `main`, `certificacion` y `desarrollo`.

## Fases

| Fase | Estado | Resultado vigente |
|---|---|---|
| F0 Preservacion | `COMPLETED` | Resguardos verificados. |
| F1 Main a certificacion | `COMPLETED` | Convergencia y ancestry verificadas. |
| F2 Certificacion a desarrollo | `COMPLETED` | Convergencia y tree comun verificados. |
| F3 Higiene remota | `COMPLETED` | Quedaron tres ramas remotas permanentes. |
| F4 Bootstrap local | `COMPLETED` | Workspace unico, smoke local y remediacion local completos. |
| Rotacion post-F4 | `COMPLETED` por confirmacion humana | Rotaciones y revocaciones confirmadas sin registrar valores. |
| F5 Obsidian minimo | `HUMAN_GATE` | Contexto canonico creado y Context Graph PASS; aprobacion humana pendiente. |
| F6-F11 | `PENDING` | Reconciliacion DB, G1b, Hito 1, certificacion, produccion y cierre. |

## Alcance Inmediato

F5 documenta el estado verificable sin copiar vaults, revisiones o evidencias. Los siguientes cambios funcionales deben seguir [Tarea 001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).

El estado actual de los schedules esta en [Arquitectura del pipeline](arquitectura_pipeline.md). FG1/FG3 manual-only sigue siendo objetivo contractual, no baseline vigente.
