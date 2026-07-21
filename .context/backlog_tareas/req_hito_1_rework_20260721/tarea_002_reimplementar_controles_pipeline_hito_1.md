---
id: TAREA-H1R-002
fase: Hito 1 Rework
estado: pendiente
prioridad: alta
estimacion_ref: est_001
requerimiento: req_hito_1_rework_20260721
hito: Hito 1 Rework
paquete: Pipeline/orquestacion
cas: "CA1, CA2 parcial"
responsable: IA implementadora
revisor: pipeline-engineer, security-auditor
aprobador: Usuario/PM
skill_principal: pipeline-engineer
skills_apoyo: "devops-release-manager, qa-test-engineer"
gate_obligatorio: security-auditor
entregable: "PR limpio a desarrollo con controles pipeline Hito 1"
creado: 2026-07-21
tags: [hito-1, rework, pipeline]
---

# TAREA-H1R-002: Reimplementar Controles Pipeline De Hito 1

## Contexto
- Evaluacion origen: [[../../operaciones/evaluacion_prs_cancelados_hito1_20260721]]
- Referencia historica: PR #203 cerrado.

## Alcance Funcional
- Revalidar y reimplementar FG3 manual-only si no existe en `desarrollo` actual.
- Preservar modo discovery-only sin publicar cursos incompletos.
- Aplicar elegibilidad/circuit breaker antes del limit de procesamiento.
- Mantener cambios minimos en orquestacion, sin arrastrar normalizacion o refactors ajenos.

## Criterios De Aceptacion
- [ ] FG3 no corre automaticamente sin autorizacion explicita.
- [ ] Discovery-only no avanza registros a publicacion final.
- [ ] Elegibilidad/circuit breaker se evalua antes de consumir cupos.
- [ ] Tests o validaciones reproducen el comportamiento esperado.
- [ ] `py_compile` pasa para scripts Python modificados.

## Archivos Candidatos
| Archivo | Tipo de cambio |
|---|---|
| `scripts/core/master_orchestrator.py` | Modificacion si aplica |
| `.github/workflows/fg3_integrity.yml` | Modificacion si aplica |
| `.github/workflows/production_pipeline.yml` | Modificacion si aplica |
| `tests/...` | Tests de contrato |

## Resultado
Pendiente.
