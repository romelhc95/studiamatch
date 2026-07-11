---
id: TAREA-XXX
fase: XX
estado: pendiente
prioridad: alta
estimacion_ref: est_XXX
hito: Hito X
paquete: Paquete X
cas: "CAx, CAy"
fecha_inicio: YYYY-MM-DD
fecha_limite: YYYY-MM-DD
despliegue: "YYYY-MM-DD 09:00 PET"
responsable: IA implementadora
revisor: security-auditor
aprobador: Usuario/PM
skill_principal: general
subespecialidad: "Por definir"
skills_apoyo: "Por definir"
gate_obligatorio: security-auditor
entregable: "PR a desarrollo + evidencia de validacion"
creado: YYYY-MM-DD
tags: []
---

# Tarea XXX: [Titulo descriptivo]

## Contexto
Estimacion de referencia: [[../estimaciones/est_XXX]]

- **Hito:** Hito X
- **Paquete:** Paquete X
- **CAs cubiertos:** CAx, CAy
- **Responsable de ejecucion:** IA implementadora
- **Revisor obligatorio:** security-auditor
- **Aprobador:** Usuario/PM
- **Entrega interna:** PR a `desarrollo` con validaciones
- **Entrega cliente:** hito cerrado aprobado por Usuario/PM

## Skills y sub-especialidad
- **Skill principal:** [tech-estimator/frontend-architect/supabase-architect/pipeline-engineer/devops-release-manager/qa-test-engineer/data-quality-analyst]
- **Sub-especialidad tecnica:** [Frontend Next.js 16, Supabase RLS, Pipeline Python, DevOps GitHub Actions, Data/QA]
- **Skills de apoyo:** [security-auditor, data-analyst, accessibility, seo]
- **Gate obligatorio:** security-auditor antes de commit/PR

## Plazos
- **Inicio comprometido:** YYYY-MM-DD
- **Fecha limite de construccion:** YYYY-MM-DD
- **Despliegue objetivo:** YYYY-MM-DD 09:00 PET
- **Regla:** no mover fechas sin aprobacion explicita del usuario y actualizacion de estimacion/tarea.

## Dependencias
- [Dependencia tecnica o funcional]

## Alcance funcional
- [Entregable funcional 1]
- [Entregable funcional 2]

## Criterios de Aceptacion
- [ ] [CAx] Criterio verificable
- [ ] [CAy] Criterio verificable
- [ ] No se exponen credenciales ni secrets.
- [ ] Se registra changelog al completar.

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `[ruta]` | [Nuevo/Modificacion/Migracion/Documentacion] |

## Plan de ejecucion
1. Confirmar alcance contra la estimacion aprobada.
2. Implementar el cambio minimo correcto.
3. Ejecutar validaciones aplicables dentro del contenedor `studiamatch-dev`.
4. Invocar revision de seguridad antes de commit/PR.
5. Actualizar changelog y resultado de la tarea.

## Validaciones requeridas
- [ ] `docker exec studiamatch-dev ...` para checks aplicables.
- [ ] Lint/typecheck si toca frontend.
- [ ] `py_compile` si toca Python.
- [ ] Revisión RLS/security si toca Supabase o escrituras.

## Notas de implementacion
<!-- Detalles tecnicos, referencias a ADRs, consideraciones de RLS, etc. -->

## Resultado
<!-- Actualizado por la IA al completar: fecha, commits, PR, evidencias, desviaciones -->
