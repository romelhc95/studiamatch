# ADR-0037 - Clasificacion Post-Merge Por Ruta Con Evidencia Positiva

## Estado

Aceptada localmente como candidate CI8.

## Contexto

CI7 introdujo un clasificador tri-state post-merge, pero valido campos de promocion antes de decidir si la ruta era ordinaria. El merge ordinario PR #438 hacia `desarrollo` quedo bloqueado por `POST_MERGE_PAIR_INVALID`.

## Decision

La clasificacion post-merge se decide primero por evidencia GitHub positiva de PR asociado, target branch y head ref confiables. Solo un PR ordinario unico hacia `desarrollo` puede ser `NOT_APPLICABLE`. `certificacion` y `main` requieren promocion exacta. Pushes directos, evidencia ausente, forks de promocion, familias superseded y rutas desconocidas son `BLOCKED`.

## Consecuencias

- `BLOCKED` nunca ejecuta `--changed-from`.
- `VERIFIED_PROMOTION` requiere revalidacion con Environment `Promotion`.
- HOM-008 reemplaza a HOM-007 como familia runtime futura; HOM-006/HOM-007 quedan bloqueadas como historia superseded.
