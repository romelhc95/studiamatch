# TASK-GOV-CI-010 - Attestation Section-Aware Fail-Closed

## Estado

`CANDIDATE_R1_LOCAL`

## Objetivo

Remediar durablemente el fallo post-merge de PR #441, donde el push a `desarrollo` fallo con `POST_MERGE_ATTESTATION_DUPLICATE` porque el validador post-merge leyo campos repetidos entre `Governance Attestation` y `Promotion Attestation` sin respetar secciones.

## Alcance

- Registrar PR #441 como `MERGED_TO_DESARROLLO_WITH_POST_MERGE_CI_FAILURE`.
- Marcar HOM-009 como superseded y no utilizable para O2-O5.
- Crear parser compartido section-aware para `Governance Attestation` y `Promotion Attestation`.
- Exigir encabezados H2 exactos, sin fallback al body completo.
- Detectar duplicados dentro de la seccion aplicable.
- Clasificar primero ruta ordinaria vs promocion antes de validar campos de Promotion.
- Preparar HOM-010 O2-O5 sin consumir R3.
- Mantener R3, branch protection remota, rulesets remotos, DB, Supabase, writers, schedules y deploys fuera del alcance local R1.

## Evidencia De Entrada

- PR #441 mergeado a `desarrollo@17d383291a5f2877074b54b66f2a0ff48a643667`.
- Tree `e0029083e24016b97fc8896be3be2d4285414117`.
- Run post-merge `32666126533` fallo con `POST_MERGE_ATTESTATION_DUPLICATE`.
- Root cause: `validate_work_package.py::parse_attestation_fields` escaneaba el body completo.

## Salida Esperada

- `WP-GOV-CI-010` congelado localmente con digest canonico.
- Tests de parser, body PR #441, ordinary PR, direct push, upper branches y HOM-010 verdes.
- Siguiente gate unico: `PREPARE_WP_GOV_CI_010_R2_APPROVAL`.
