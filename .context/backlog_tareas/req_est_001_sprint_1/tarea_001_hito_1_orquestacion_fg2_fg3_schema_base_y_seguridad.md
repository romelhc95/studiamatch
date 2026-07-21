---
id: TAREA-001
fase: 1
estado: pendiente
prioridad: critica
estimacion_ref: est_001
requerimiento: req_est_001_sprint_1
hito: Hito 1
paquete: Paquete 1 - Orquestacion FG2/FG3, schema base y seguridad
cas: "CA1, CA2 parcial, CA7 preparacion"
fecha_inicio: 2026-07-11
fecha_limite: 2026-07-25
despliegue: "2026-07-27 09:00 PET"
responsable: IA implementadora
revisor: security-auditor
aprobador: Usuario/PM
skill_principal: devops-release-manager
subespecialidad: DevOps GitHub Actions + Supabase schema/RLS
skills_apoyo: "supabase-architect, security-auditor, pipeline-engineer"
gate_obligatorio: security-auditor
entregable: "PR a desarrollo con schema/workflows seguros y evidencia de validacion"
creado: 2026-07-11
tags: []
---

# Tarea 001: Hito 1 - Orquestacion FG2 FG3 schema base y seguridad

## Contexto
Estimacion de referencia: [[../../estimaciones/est_001]]

- **Requerimiento:** req_est_001_sprint_1
- **Hito:** Hito 1
- **Paquete:** Paquete 1 - Orquestacion FG2/FG3, schema base y seguridad
- **CAs cubiertos:** CA1, CA2 parcial, CA7 preparacion
- **Responsable de ejecucion:** IA implementadora
- **Revisor obligatorio:** security-auditor
- **Aprobador:** Usuario/PM
- **Entregable:** PR a desarrollo con schema/workflows seguros y evidencia de validacion

## Skills y sub-especialidad
- **Skill principal:** devops-release-manager
- **Sub-especialidad tecnica:** DevOps GitHub Actions + Supabase schema/RLS
- **Skills de apoyo:** supabase-architect, security-auditor, pipeline-engineer
- **Gate obligatorio:** security-auditor

## Plazos
- **Inicio comprometido:** 2026-07-11
- **Fecha limite de construccion:** 2026-07-25
- **Despliegue objetivo:** 2026-07-27 09:00 PET

## Dependencias
- Aprobacion de EST-001 y activacion del Sprint 1

## Criterios de Aceptacion
- [ ] Schedules del harvester/pipeline quedan definidos o reactivados sin saltarse gates ni exponer credenciales
- [ ] Schema soporta estado editorial/calidad, campos faltantes, fuentes manual/scraping, timestamps y proxima fecha de inicio
- [ ] Leads/flag de patrocinio quedan preparados sin implementar entrega real-time fuera de alcance

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `.github/workflows/production_pipeline.yml` | Validacion/ajuste de schedules y environment gating |
| `.github/workflows/fg3_integrity.yml` | Formalizacion de estado activo/inactivo segun alcance aprobado |
| `db/migrations/` | Nueva migracion para campos editoriales/calidad/leads si aplica |
| `scripts/core/master_orchestrator.py` | Validacion de gates, limites y circuit breaker |

## Plan de ejecucion
1. Confirmar alcance contra la estimacion aprobada.
2. Implementar el cambio minimo que satisfaga los criterios.
3. Ejecutar validaciones aplicables en el contenedor Docker.
4. Invocar revision de seguridad antes de commit/PR.
5. Registrar resultado en changelog.

## Notas de implementacion
<!-- Detalles tecnicos aqui -->

## Resultado
<!-- Actualizado por la IA al completar: Fecha, commits, PR -->
