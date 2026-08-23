# TASK-GOV-CI-009 - Owner-Only Protected Branch Updates

## Estado

`CANDIDATE_R1_LOCAL`

## Objetivo

Remediar el fallo post-merge de PR #440, donde el reviewer `romelhc95-approver` tambien ejecuto el merge de O2 hacia `certificacion`, violando la separacion requerida entre `required_reviewer=romelhc95-approver` y `required_merger=romelhc95`.

## Alcance

- Registrar PR #440 y run `32662084712` como `MERGED_TO_CERTIFICACION_WITH_POST_MERGE_FAILURE`.
- Marcar `R3-GOV-HOM-008-O2-REQ1` como consumido y no reutilizable.
- Superseder HOM-008 O2-O5 y preparar HOM-009 O2-O5.
- Documentar owner-only merge permanente para `desarrollo`, `certificacion` y `main` mediante ruleset de `Restrict updates`.
- Mantener `romelhc95-approver` como reviewer/aprobador y `romelhc95` como desarrollador/merger.
- Mantener R3, branch protection remota, rulesets remotos, DB, Supabase, writers, schedules y deploys fuera del alcance local R1.

## Evidencia De Entrada

- PR #440 mergeado a `certificacion@df2cde3626c75fa4733bf1624fb105d8ee08c076`.
- Tree `7df05c52da47855d62c082f7cfbd12ee1e38b965`.
- Run post-merge `32662084712` fallo con `POST_MERGE_MERGER_INVALID`.
- Reviewer y merger observado: `romelhc95-approver`.
- Merger requerido: `romelhc95`.

## Salida Esperada

- `WP-GOV-CI-009` congelado localmente con digest canonico.
- Tests de HOM-009, superseded HOM-008 y owner-only desired state verdes.
- Siguiente gate unico: `PREPARE_WP_GOV_CI_009_R2_APPROVAL`.
