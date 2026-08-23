# TASK-GOV-CI-008 - Route Classification Fail-Closed Recovery

## Estado

`CANDIDATE_R1_LOCAL`

## Objetivo

Corregir la regresion post-merge observada despues de PR #438, donde un PR ordinario `governance/gov-ci-007 -> desarrollo` fue clasificado como `BLOCKED / POST_MERGE_PAIR_INVALID` en vez de `NOT_APPLICABLE`.

## Alcance

- Reordenar la clasificacion post-merge para distinguir ruta ordinaria verificada de promocion antes de validar attestation HOM.
- Bloquear pushes directos o sin PR asociado en ramas protegidas.
- Bloquear rutas ordinarias hacia `certificacion` y `main`.
- Sustituir familia runtime HOM-007 por HOM-008, dejando HOM-006/HOM-007 como historia superseded.
- Mantener R3, Promotion environment, DB, Supabase, writers, schedules y deploys fuera del alcance.

## Evidencia De Entrada

- PR #438 mergeado a `desarrollo@16045d45811cbe12299ce2ba66f6afd75a93d1ee`.
- Tree `29f76f029f9c1c664fd8a9fc2ebda30d75a0a4df`.
- Run post-merge `32655520324` fallo `Canonical Path Boundary` con `POST_MERGE_PAIR_INVALID`.

## Salida Esperada

- `WP-GOV-CI-008` congelado localmente con digest canonico.
- Tests de tri-state y matriz protegida verdes.
- Siguiente gate unico: `PREPARE_WP_GOV_CI_008_R2_APPROVAL`.
