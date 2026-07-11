---
id: TAREA-004
fase: 4
estado: pendiente
prioridad: alta
estimacion_ref: est_001
hito: Hito 4
paquete: Paquetes 4 y 6 - Home MVP + documentacion tecnica
cas: "CA5, CA6, CA7, CA13 Home"
fecha_inicio: 2026-09-12
fecha_limite: 2026-09-13
despliegue: "2026-09-14 09:00 PET"
responsable: IA implementadora
revisor: security-auditor
aprobador: Usuario/PM
skill_principal: frontend-architect
subespecialidad: Frontend Next.js 16 + UI Home + documentacion tecnica
skills_apoyo: "accessibility, seo, security-auditor, qa-test-engineer"
gate_obligatorio: security-auditor
entregable: "PR a desarrollo con Home segun mockup aprobado y documentacion tecnica Sprint 1"
creado: 2026-07-11
tags: []
---

# Tarea 004: Hito 4 - Home MVP quick wins visuales y documentacion tecnica

## Contexto
Estimacion de referencia: [[../estimaciones/est_001]]

- **Hito:** Hito 4
- **Paquete:** Paquetes 4 y 6 - Home MVP + documentacion tecnica
- **CAs cubiertos:** CA5, CA6, CA7, CA13 Home
- **Responsable de ejecucion:** IA implementadora
- **Revisor obligatorio:** security-auditor
- **Aprobador:** Usuario/PM
- **Entregable:** PR a desarrollo con Home segun mockup aprobado y documentacion tecnica Sprint 1

## Skills y sub-especialidad
- **Skill principal:** frontend-architect
- **Sub-especialidad tecnica:** Frontend Next.js 16 + UI Home + documentacion tecnica
- **Skills de apoyo:** accessibility, seo, security-auditor, qa-test-engineer
- **Gate obligatorio:** security-auditor

## Plazos
- **Inicio comprometido:** 2026-09-12
- **Fecha limite de construccion:** 2026-09-13
- **Despliegue objetivo:** 2026-09-14 09:00 PET

## Dependencias
- TAREA-003 desplegada o aprobada internamente

## Criterios de Aceptacion
- [ ] Home implementa navbar sticky, selector moneda visual, hero, search bar, pills, stats, instituciones, destacados, inscripciones abiertas, paises, banner y footer
- [ ] Se aplica Inter, cards alineadas al mockup, texto instituciones y ROI oculto en vistas publicas
- [ ] Documentacion tecnica describe tablas/campos, pipeline y criterios operativos modificados

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `web/src/app/page.tsx` | Ajuste shell/datos iniciales de Home |
| `web/src/app/HomeContent.tsx` | Rediseño Home segun mockup y quick wins |
| `web/src/app/globals.css` | Tokens/estilos Tailwind v4 necesarios |
| `web/src/components/` | Componentes reutilizables para cards/sections si aplica |
| `.context/changelog/` | Registro de cierre tecnico del hito |

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
