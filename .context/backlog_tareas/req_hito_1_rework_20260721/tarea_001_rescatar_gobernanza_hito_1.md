---
id: TAREA-H1R-001
fase: Hito 1 Rework
estado: pendiente
prioridad: alta
estimacion_ref: est_001
requerimiento: req_hito_1_rework_20260721
hito: Hito 1 Rework
paquete: Gobernanza y alcance
cas: "CA1, CA2 parcial, CA7 preparacion"
responsable: IA implementadora
revisor: qa-test-engineer, security-auditor
aprobador: Usuario/PM
skill_principal: qa-test-engineer
skills_apoyo: "security-auditor, devops-release-manager"
gate_obligatorio: security-auditor
entregable: "PR limpio a desarrollo con gobernanza minima reproducible"
creado: 2026-07-21
tags: [hito-1, rework, gobernanza]
---

# TAREA-H1R-001: Rescatar Gobernanza De Hito 1

## Contexto
- Evaluacion origen: [[../../operaciones/evaluacion_prs_cancelados_hito1_20260721]]
- Backlog: [[backlog_tareas/req_hito_1_rework_20260721/_index]]
- Referencia historica: PR #202 cerrado.

## Alcance Funcional
- Identificar que partes de #202 siguen faltando en `desarrollo` actual.
- Mantener solo controles minimos: matriz CA, validacion de cierre y evidencia reproducible.
- Evitar normalizacion masiva, cambios en agentes y archivos no relacionados.

## Criterios De Aceptacion
- [ ] Existe comparacion documentada entre #202 y `origin/desarrollo` actual.
- [ ] Solo se reimplementan gaps reales no cubiertos por PR #208 a PR #212.
- [ ] La tarea no introduce cambios funcionales de pipeline ni DB.
- [ ] `validate_context_graph.py` pasa si se modifica `.context`.

## Archivos Candidatos
| Archivo | Tipo de cambio |
|---|---|
| `.context/backlog_tareas/req_hito_1_rework_20260721/` | Documentacion |
| `scripts/maintenance/validate_hito_close.py` | Nuevo o ajuste solo si falta en desarrollo |
| `tests/...` | Tests recurrentes del gate |

## Resultado
Pendiente.
