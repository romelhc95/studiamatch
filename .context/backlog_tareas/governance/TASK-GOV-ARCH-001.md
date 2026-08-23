# TASK-GOV-ARCH-001 - Remediacion Documental Arquitectura

| Campo | Valor |
|---|---|
| Estado | `COMPLETED_EXTERNALLY_BY_PR_425` |
| Work package | `WP-GOV-ARCH-001` |
| Objetivo | Crear fuentes canonicas de arquitectura aplicativa, pipeline, Supabase y adopcion DB. |
| Baseline | `desarrollo@96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9` |
| Alcance | Documentacion local y validadores semanticos; sin cambios funcionales ni remotos. Consumido por PR #425. |

## Resultado

`WP-GOV-ARCH-001` fue aprobado por digest `df48d75129cfe2ba8971f55573a597ca47fb0e3c20e11a3a6a63377349be44e1` y consumido externamente por PR #425, mergeado a `desarrollo@4cce43a743de5860c4da86eecf1782efab91d26b` con tree `ac16b545b74a03b149aac538062def20101187fb`, Governance Preflight PASS, `security-audit` PASS y review humano. El manifest `WP-GOV-ARCH-001.json` se conserva sin mutacion como artifact firmado.

## Alcance

1. Crear `.context/arquitectura_pipeline.md`, `.context/sistema_db_supabase.md` y `.context/operaciones/matriz_adopcion_db.md`.
2. Enlazar las fuentes desde el MOC, README, Context Graph y AGENTS.
3. Marcar como `SUPERSEDED_HISTORY` los documentos legacy que compitan como fuente de verdad.
4. Agregar validaciones para que los tres documentos canonicos no desaparezcan.
5. Mantener H2-CA2/H2-CA3 en `NOT_STARTED` y no iniciar Hito 2 funcional.

## Fuera De Alcance

- Push, PR, merge, Certification, Main, R2/R3 operativo.
- Supabase remoto, DDL/DML, migraciones, backfill, RLS/grants remotos.
- Deploys, writers, schedules o cambios funcionales en `web/`, `scripts/core/` o `scripts/maintenance/`.

## Criterio De Salida Local

- Resultado R2 publicado en `desarrollo` por PR #425.
- Proximo paso: `WP-GOV-HOM-001` para reconciliacion post-merge y homologacion no recursiva.
