# Gobierno De Hallazgos

Un hallazgo no modifica por si mismo alcance, CA, TASK, Hito o fase. Toda
ampliacion sigue [Flujo de requerimientos](../operaciones/flujo_requerimientos.md):
`INTAKE -> EST -> REQ -> TASK`.

## Clasificaciones Autorizadas

| Clasificacion | Condicion | Efecto |
|---|---|---|
| `BLOCKING_IN_SCOPE` | Incumple de forma reproducible un CA vigente, un invariante obligatorio de seguridad o rompe una superficie modificada | Bloquea GO del candidate |
| `RESIDUAL_ACCEPTED` | Riesgo en alcance contenido y aceptado expresamente por autoridad humana | Se documenta; no implica remediacion automatica |
| `BACKLOG_OUT_OF_SCOPE` | Mejora valida sin incumplimiento del alcance vigente | Se deriva por intake; no bloquea el Hito actual |
| `DUPLICATE` | Ya existe un hallazgo equivalente con autoridad | Se enlaza al original |
| `FALSE_POSITIVE` | No existe ruta, impacto o reproduccion demostrable | Se cierra con evidencia |

## Registro Minimo

```text
Finding ID | Run ID o Test ID | CA | Clasificacion |
Requisito o invariante afectado | Superficie | Reproduccion |
Esperado | Observado | Impacto | Disposicion y owner | Evidencia | Estado
```

## Reglas De Decision

1. `BLOCKING_IN_SCOPE` exige reproduccion determinista y mapeo explicito a CA,
   seguridad obligatoria o regresion de la superficie modificada.
2. `RESIDUAL_ACCEPTED` requiere aceptacion humana identificable; QA no puede
   asignarla unilateralmente.
3. `BACKLOG_OUT_OF_SCOPE` no se remedia dentro del candidate actual y no crea
   una subtarea implicita.
4. Un hallazgo arquitectonico, de performance o calidad sin umbral aprobado es
   `BACKLOG_OUT_OF_SCOPE`, no criterio contractual. `QUALITY_ADVISORY` se usa
   solo para clasificar tests, nunca hallazgos.
5. Un nuevo test puede ampliar cobertura de un CA, pero no cambiar su resultado
   esperado sin actualizar REQ/TASK por el flujo formal.
6. Secrets, PII o detalle explotable se redactan y activan stop condition.

## Casos Que No Amplian Alcance

- Gates de seguridad, secretos, RLS y egress protegen el CA relacionado.
- Lint, typecheck, build, rollback, canary y smoke son gates tecnicos.
- Accesibilidad y responsive se vinculan solo donde la TASK ya los exige.
- Paginacion e idempotencia protegen correccion; no prometen carga masiva.
- Ausencia de funcionalidades excluidas se registra como `OUT_OF_SCOPE` o
  guard de regresion, no como entregable nuevo.

## Evidencia Cliente

La matriz tecnica puede contener `FAIL` verificado. La evidencia cliente solo
pasa a `APPROVED_FOR_CLIENT` tras sanitizacion y revision humana conforme al
[indice de evidencia](../evidencias_cliente/sprint_1/_index.md).
