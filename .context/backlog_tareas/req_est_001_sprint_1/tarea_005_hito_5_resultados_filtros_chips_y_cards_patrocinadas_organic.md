---
id: TAREA-005
fase: 5
estado: pendiente
prioridad: critica
estimacion_ref: est_001
requerimiento: req_est_001_sprint_1
hito: Hito 5
paquete: Paquete 5 - Resultados filtrados, sidebar, chips y cards patrocinadas/organicas
cas: "CA8, CA9, CA10, CA11, CA12, CA13 Resultados"
fecha_inicio: 2026-09-15
fecha_limite: 2026-09-29
despliegue: "2026-10-05 09:00 PET"
responsable: IA implementadora
revisor: security-auditor
aprobador: Usuario/PM
skill_principal: frontend-architect
subespecialidad: Frontend Next.js 16 resultados + filtros + cards
skills_apoyo: "accessibility, seo, security-auditor, data-quality-analyst, qa-test-engineer"
gate_obligatorio: security-auditor
entregable: "PR a desarrollo con resultados filtrados segun mockup aprobado"
creado: 2026-07-11
tags: []
---

# Tarea 005: Hito 5 - Resultados filtros chips y cards patrocinadas organicas

## Contexto
Estimacion de referencia: [[../../estimaciones/est_001]]

- **Requerimiento:** req_est_001_sprint_1
- **Hito:** Hito 5
- **Paquete:** Paquete 5 - Resultados filtrados, sidebar, chips y cards patrocinadas/organicas
- **CAs cubiertos:** CA8, CA9, CA10, CA11, CA12, CA13 Resultados
- **Responsable de ejecucion:** IA implementadora
- **Revisor obligatorio:** security-auditor
- **Aprobador:** Usuario/PM
- **Entregable:** PR a desarrollo con resultados filtrados segun mockup aprobado

## Skills y sub-especialidad
- **Skill principal:** frontend-architect
- **Sub-especialidad tecnica:** Frontend Next.js 16 resultados + filtros + cards
- **Skills de apoyo:** accessibility, seo, security-auditor, data-quality-analyst, qa-test-engineer
- **Gate obligatorio:** security-auditor

## Plazos
- **Inicio comprometido:** 2026-09-15
- **Fecha limite de construccion:** 2026-09-29
- **Despliegue objetivo:** 2026-10-05 09:00 PET

## Dependencias
- TAREA-004 desplegada o aprobada internamente

## Criterios de Aceptacion
- [ ] Resultados incluyen sticky search bajo nav, chips removibles y Limpiar todo
- [ ] Sidebar filtra por disponibilidad, area, modalidad, pais, precio y duracion con pills escalables
- [ ] Cards distinguen patrocinado y organico; card navega a detalle y botones internos no navegan
- [ ] Contador contextual y paginacion reflejan filtros activos
- [ ] No se usa el texto Contactar en CTAs

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `web/src/app/courses/page.tsx` | Ajuste de ruta/resultados si aplica |
| `web/src/app/courses/CoursesFallbackPage.tsx` | Vista funcional de resultados/fallback |
| `web/src/app/HomeContent.tsx` | Integracion de filtros/resultados derivados desde Home si aplica |
| `web/src/components/` | Componentes ResultsSearchStrip, chips, sidebar, cards y paginacion |

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
