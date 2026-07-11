---
id: TAREA-002
fase: 2
estado: pendiente
prioridad: critica
estimacion_ref: est_001
hito: Hito 2
paquete: Paquete 2 - Pipeline deteccion de campos vacios y marcado pendiente
cas: "CA3, CA2 parcial"
fecha_inicio: 2026-07-28
fecha_limite: 2026-08-11
despliegue: "2026-08-17 09:00 PET"
responsable: IA implementadora
revisor: security-auditor
aprobador: Usuario/PM
skill_principal: pipeline-engineer
subespecialidad: Pipeline Python ETL + Supabase PostgREST
skills_apoyo: "supabase-architect, security-auditor, data-quality-analyst, qa-test-engineer"
gate_obligatorio: security-auditor
entregable: "PR a desarrollo con pipeline tolerante a campos vacios y estado pendiente/completo"
creado: 2026-07-11
tags: []
---

# Tarea 002: Hito 2 - Pipeline campos vacios y marcado pendiente

## Contexto
Estimacion de referencia: [[../estimaciones/est_001]]

- **Hito:** Hito 2
- **Paquete:** Paquete 2 - Pipeline deteccion de campos vacios y marcado pendiente
- **CAs cubiertos:** CA3, CA2 parcial
- **Responsable de ejecucion:** IA implementadora
- **Revisor obligatorio:** security-auditor
- **Aprobador:** Usuario/PM
- **Entregable:** PR a desarrollo con pipeline tolerante a campos vacios y estado pendiente/completo

## Skills y sub-especialidad
- **Skill principal:** pipeline-engineer
- **Sub-especialidad tecnica:** Pipeline Python ETL + Supabase PostgREST
- **Skills de apoyo:** supabase-architect, security-auditor, data-quality-analyst, qa-test-engineer
- **Gate obligatorio:** security-auditor

## Plazos
- **Inicio comprometido:** 2026-07-28
- **Fecha limite de construccion:** 2026-08-11
- **Despliegue objetivo:** 2026-08-17 09:00 PET

## Dependencias
- TAREA-001 desplegada o aprobada internamente

## Criterios de Aceptacion
- [ ] El scraping/enriquecimiento no falla si faltan precio, duracion, modalidad, fecha o area
- [ ] Los campos encontrados se guardan y los vacios quedan registrados como campos faltantes o equivalente
- [ ] El registro queda pendiente o completo segun calidad minima y queda disponible para curacion admin

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `scripts/core/universal_harvester.py` | Preservar extraccion parcial sin fallar por campos ausentes |
| `scripts/core/cleansing_worker.py` | Registrar faltantes detectables y no descartar registros validos incompletos |
| `scripts/core/enrichment_worker.py` | Normalizar nulos y salida parcial de 14 pilares |
| `scripts/core/sync_vector_worker.py` | Mapear faltantes a estado editorial pendiente/completo |
| `scripts/core/master_orchestrator.py` | Asegurar continuidad de corrida ante parciales |

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
