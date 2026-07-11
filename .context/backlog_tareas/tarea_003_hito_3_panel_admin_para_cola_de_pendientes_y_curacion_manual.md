---
id: TAREA-003
fase: 3
estado: pendiente
prioridad: critica
estimacion_ref: est_001
hito: Hito 3
paquete: Paquete 3 - Panel /admin para cola de pendientes y curacion manual
cas: "CA4"
fecha_inicio: 2026-08-18
fecha_limite: 2026-09-01
despliegue: "2026-09-07 09:00 PET"
responsable: IA implementadora
revisor: security-auditor
aprobador: Usuario/PM
skill_principal: frontend-architect
subespecialidad: Frontend Next.js 16 admin + Supabase RLS/RPC
skills_apoyo: "supabase-architect, security-auditor, accessibility, qa-test-engineer"
gate_obligatorio: security-auditor
entregable: "PR a desarrollo con /admin seguro para listar, editar y publicar pendientes"
creado: 2026-07-11
tags: []
---

# Tarea 003: Hito 3 - Panel admin para cola de pendientes y curacion manual

## Contexto
Estimacion de referencia: [[../estimaciones/est_001]]

- **Hito:** Hito 3
- **Paquete:** Paquete 3 - Panel /admin para cola de pendientes y curacion manual
- **CAs cubiertos:** CA4
- **Responsable de ejecucion:** IA implementadora
- **Revisor obligatorio:** security-auditor
- **Aprobador:** Usuario/PM
- **Entregable:** PR a desarrollo con /admin seguro para listar, editar y publicar pendientes

## Skills y sub-especialidad
- **Skill principal:** frontend-architect
- **Sub-especialidad tecnica:** Frontend Next.js 16 admin + Supabase RLS/RPC
- **Skills de apoyo:** supabase-architect, security-auditor, accessibility, qa-test-engineer
- **Gate obligatorio:** security-auditor

## Plazos
- **Inicio comprometido:** 2026-08-18
- **Fecha limite de construccion:** 2026-09-01
- **Despliegue objetivo:** 2026-09-07 09:00 PET

## Dependencias
- TAREA-002 desplegada o aprobada internamente

## Criterios de Aceptacion
- [ ] /admin lista programas pendientes
- [ ] Formulario inline permite editar precio, duracion, modalidad, fecha, area y campos faltantes
- [ ] Al guardar se marca fuente manual y timestamp actualizado
- [ ] Publicar solo es posible cuando el registro cumple criterios minimos bajo RLS/RPC segura

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `web/src/app/admin/page.tsx` | Nueva ruta admin compatible con static export |
| `web/src/app/admin/` | Nuevos componentes cliente para cola, edicion y publicacion |
| `db/migrations/` | RPC/RLS/vistas seguras para operaciones admin si aplica |

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
