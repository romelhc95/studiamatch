# TASK-GOV-ARCH-001 - Remediacion Documental Arquitectura

| Campo | Valor |
|---|---|
| Estado | `PROPOSED_R2_PENDING_DIGEST_APPROVAL` |
| Work package | `WP-GOV-ARCH-001` |
| Objetivo | Crear fuentes canonicas de arquitectura aplicativa, pipeline, Supabase y adopcion DB. |
| Baseline | `desarrollo@96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9` |
| Alcance | Documentacion local y validadores semanticos; sin cambios funcionales ni remotos. |

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

- Candidate commit local con digest calculado de `WP-GOV-ARCH-001`.
- Markdown links, Context Graph, manifest validation, tests y credential scan pasan.
- Proximo paso: aprobacion humana por digest para R2 separado.
