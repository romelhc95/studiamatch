# ADR-0036 - Evidencia post-merge fail-closed

## Estado

`ACCEPTED_CANDIDATE`

## Contexto

ADR-0034 permitia fallback incremental cuando faltaba evidencia post-merge. PR #437 demostro que esa regla es insuficiente: GitHub Actions puede devolver check-runs con `pull_requests: []` para commits sinteticos, y la misma promocion tambien incumplio el contrato de identidad porque fue mergeada por `romelhc95-approver`.

## Decision

Los pushes post-merge se clasifican en tres resultados: `VERIFIED_PROMOTION`, `NOT_APPLICABLE` y `BLOCKED`. Solo `NOT_APPLICABLE`, reservado para pushes inequívocamente ordinarios, puede usar el boundary incremental `--changed-from`. Toda promocion invalida, promotion-shaped, ambigua, incompleta, pendiente o con evidencia no confiable debe terminar `BLOCKED` y no producir ruido secundario de paths.

Esta ADR supersede explicitamente solo la decision permisiva de ADR-0034 que permitia fallback cuando faltaba evidencia. Se conserva el objetivo estructural de validar promociones post-merge con evidencia read-only, pero ahora falta de evidencia es fail-closed.

## Consecuencias

- `pull_requests: []` en check-runs no es falso negativo si la asociacion merge -> PR es unica y valida.
- Check-runs requieren paginacion, retries acotados, `app.id=15368`, SHA exacto, timestamps validos y workflow run `pull_request` comun.
- Reviews usan el ultimo estado efectivo de `romelhc95-approver` y requieren `commit_id` exacto.
- `merged_by` debe ser `romelhc95`; el reviewer requerido es `romelhc95-approver` y ambos deben ser distintos.
- PR #437 y `R3-GOV-HOM-006-O2-REQ1` quedan consumidos por fallo; HOM-006 O3-O5 quedan superseded.
- HOM-007 reemplaza completamente a HOM-006 para solicitudes futuras.
