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

## Fuentes del requerimiento
- Documento fuente: `[ruta del requerimiento aprobado]`
- Secciones fuente: [ej. Seccion 5 Datos criticos visibles, Seccion 6 Logica de cards, CAx]
- Mockups/referencias: [HTML, PDF, imagen o nota aprobada]

## Matriz CA -> detalle implementable
| CA | Detalle exacto del requerimiento | Implicancia tecnica | Fuera de alcance |
|---|---|---|---|
| CAx | [Texto o resumen fiel del requerimiento fuente] | [Cambio tecnico requerido] | [Lo que no se hara] |

## Alcance incluido
- [Entregable funcional 1]
- [Entregable funcional 2]

## Alcance excluido
- [Elemento fuera de alcance para evitar sobre-implementacion]

## Criterios de Aceptacion
- [ ] [CAx] Criterio verificable
- [ ] [CAy] Criterio verificable
- [ ] No se exponen credenciales ni secrets.
- [ ] Se registra changelog al completar.

## Matriz CA -> pruebas/evidencia
| CA | Prueba obligatoria | Tipo | Metodo / comando | Resultado esperado | Evidencia requerida |
|---|---|---|---|---|---|
| CAx | [Que se valida exactamente] | [DB/RLS/frontend/pipeline/workflow/documental] | `[comando/query/revision]` | [Resultado concreto antes de ejecutar] | [Salida/captura/diff/informe] |

## Analisis tecnico previo obligatorio
- [ ] Revisar estimacion aprobada, CAs, arquitectura vigente y codigo/schema actual antes de definir cambios.
- [ ] Revisar el documento fuente del requerimiento y mapear cada CA a sus secciones detalladas; no usar nombres internos legacy si contradicen el documento aprobado.
- [ ] Identificar archivos/tablas/componentes/workflows exactos que se modificaran.
- [ ] Documentar decisiones tecnicas antes de implementar, incluyendo alternativas descartadas si hay mas de una opcion viable.
- [ ] Si toca DB: listar tabla, columna, tipo, nullability, default, checks, indices, RLS/RPC/grants y si requiere backfill.
- [ ] Si toca frontend: listar ruta, componente, estado cliente, props/datos, interacciones, responsive y accesibilidad esperada.
- [ ] Si toca pipeline: listar worker, funcion/bloque, input esperado, output esperado, errores tolerados y efecto en tablas destino.
- [ ] Si toca CI/CD: listar workflow, trigger, environment, secrets esperados, jobs/steps y condiciones de ejecucion.

## Especificacion exacta del cambio
<!-- Completar antes de ejecutar. No debe quedar en generico. -->

| Dominio | Detalle obligatorio |
|---|---|
| DB/Supabase | Tabla, columna, tipo, default, check, indice, policy/RPC/grant y migracion exacta. |
| Frontend | Ruta, componente, estado, evento, query/fetch, copy, responsive y criterio visual. |
| Pipeline Python | Archivo, funcion, validacion de entrada, normalizacion, escritura final y manejo de errores. |
| DevOps/CI | Workflow, trigger, job, secrets, environment, condiciones y rollback. |
| Documentacion | Archivo, seccion y contenido minimo que debe quedar actualizado. |

## Subtareas tecnicas
- [ ] **ST-01 — [Nombre de subtarea]**
  - Analisis previo: [que se revisa antes de implementar]
  - Objetivo: [resultado concreto]
  - Cambio exacto: [detalle implementable, no generico]
  - Archivos esperados: `[ruta]`
  - CAs relacionados: [CAx]
  - Validacion: [comando/evidencia]
- [ ] **ST-02 — [Nombre de subtarea]**
  - Analisis previo: [que se revisa antes de implementar]
  - Objetivo: [resultado concreto]
  - Cambio exacto: [detalle implementable, no generico]
  - Archivos esperados: `[ruta]`
  - CAs relacionados: [CAy]
  - Validacion: [comando/evidencia]

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `[ruta]` | [Nuevo/Modificacion/Migracion/Documentacion] |

## Plan de ejecucion
1. Leer estimacion aprobada, CAs y esta tarea antes de tocar codigo.
2. Ejecutar el analisis tecnico previo y documentar la especificacion exacta del cambio.
3. Resolver bloqueadores o decisiones pendientes antes de implementar.
4. Ejecutar subtareas en orden, manteniendo cambios minimos y trazables.
5. Validar cada subtarea con la evidencia indicada.
6. Ejecutar validaciones finales dentro del contenedor `studiamatch-dev`.
7. Generar reporte candidato con `validate_hito_close.py --hito X --generate-report`, stagearlo/enlazarlo y ejecutar el gate final con `validate_hito_close.py --hito X`.
8. Invocar `security-auditor` antes de commit/PR.
9. Actualizar changelog, checklist y resultado de la tarea.

## Validaciones requeridas
- [ ] `docker exec studiamatch-dev ...` para checks aplicables.
- [ ] Lint/typecheck si toca frontend.
- [ ] `py_compile` si toca Python.
- [ ] Revisión RLS/security si toca Supabase o escrituras.
- [ ] Ejecucion de la matriz `CA -> pruebas/evidencia`.
- [ ] Generacion de reporte: `docker exec studiamatch-dev python3 scripts/maintenance/validate_hito_close.py --hito X --generate-report`.
- [ ] Verificacion final: `docker exec studiamatch-dev python3 scripts/maintenance/validate_hito_close.py --hito X`.

## Evidencia requerida
- [ ] Resumen de archivos modificados y motivo.
- [ ] Salida de validaciones ejecutadas.
- [ ] Riesgos residuales o decisiones pendientes documentadas.
- [ ] PR enlazada o referencia de entrega interna.
- [ ] Informe de cumplimiento del hito en `.context/evidencias/hito_X_informe_cumplimiento.md`.
- [ ] Veredicto del gate de conformidad requerimiento/evidencia.
- [ ] Salida del gate mecanico de cierre (`GO` o `NO-GO` con brechas).
- [ ] Reporte QA del gate en `.context/evidencias/hito_X_qa_gate_report_YYYYMMDD_HHMMSS.md`.
- [ ] Resultado de cada prueba por CA: OK / observado / no aplica justificado.

## Checklist de cierre
- [ ] Todos los CAs del hito quedan cubiertos o se documenta excepcion aprobada.
- [ ] No se agregan alcances excluidos.
- [ ] El analisis previo y la especificacion exacta quedaron documentados.
- [ ] No quedan credenciales ni datos sensibles en codigo/docs.
- [ ] Changelog actualizado.
- [ ] Informe de cumplimiento generado y revisado para lenguaje cliente.
- [ ] Gate mecanico de cierre ejecutado con resultado `GO`.
- [ ] Reporte QA del gate generado y versionado.
- [ ] Tarea, changelog, informe y artefactos versionados no se contradicen.
- [ ] Si algun CA queda parcial/observado, existen subtareas refinadas antes de tocar mas codigo.
- [ ] Ningun CA queda sin prueba y evidencia.
- [ ] Tarea actualizada con resultado, fecha, commits/PR y evidencia.

## Notas de implementacion
<!-- Detalles tecnicos, referencias a ADRs, consideraciones de RLS, etc. -->

## Resultado
<!-- Actualizado por la IA al completar: fecha, commits, PR, evidencias, desviaciones -->
