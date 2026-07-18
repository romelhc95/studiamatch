# Informe de Cumplimiento — Hito X

> Documento orientado a cliente. Resume que se entrego, que requerimiento cubre y que evidencia respalda el cumplimiento. La fuente tecnica versionada queda en Git; este contenido puede copiarse o publicarse en Notion como vista compartida para el cliente.

## 1. Resumen Ejecutivo

| Campo | Detalle |
|---|---|
| Sprint | Sprint X |
| Hito | Hito X |
| Paquete aprobado | Paquete X — [nombre] |
| Fecha de entrega interna | YYYY-MM-DD |
| Estado | En revision / Aprobado / Observado |
| PR / rama | [link o referencia] |

### Resultado para el cliente
- [Explicacion en lenguaje no tecnico de lo que ya quedo disponible.]
- [Beneficio directo asociado al requerimiento aprobado.]
- [Limitaciones o decisiones pendientes, si existen.]

## 2. Alcance Aprobado

| Fuente | Referencia |
|---|---|
| Estimacion aprobada | `.context/estimaciones/est_XXX.md` |
| Tarea tecnica | `.context/backlog_tareas/tarea_XXX_*.md` |
| Documento cliente | `requerimientos/YYYYMMDD/[documento]` |
| Mockups/referencias | `requerimientos/YYYYMMDD/[archivo]` |

## 3. Matriz De Cumplimiento Por Criterio De Aceptacion

| CA | Requerimiento aprobado | Cambio entregado | Evidencia verificable | Estado |
|---|---|---|---|---|
| CAx | [Texto fiel o resumen entendible] | [Que se implemento] | [Archivo, commit, captura, validacion o PR] | Cumple / Parcial / No aplica |

## 4. Matriz De Subtareas Tecnicas

| Subtarea | Resultado | Archivos / artefactos | Validacion | Estado |
|---|---|---|---|---|
| ST-01 | [Resultado concreto] | `[ruta]` | `[comando/evidencia]` | Cumple |

## 5. Matriz De Pruebas Por Criterio De Aceptacion

| CA | Prueba ejecutada | Metodo / comando | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|---|
| CAx | [Que se valido] | `[comando/query/revision]` | [Resultado esperado antes de ejecutar] | [Resultado real/evidencia] | OK / Observado / No aplica justificado |

## 6. Cambios Realizados

### Cambios funcionales
- [Cambio visible o funcional explicado para cliente.]

### Cambios tecnicos de soporte
- [Cambio tecnico necesario explicado sin jerga innecesaria.]

### Fuera de alcance no implementado
- [Elemento no incluido segun estimacion/tarea para evitar confusiones.]

## 7. Evidencia De Validacion

| Validacion | Resultado | Evidencia |
|---|---|---|
| Seguridad / credenciales | Pendiente / OK | [hook, security-auditor, revision] |
| Lint/typecheck/frontend | Pendiente / OK / No aplica | [comando] |
| Python syntax check | Pendiente / OK / No aplica | [comando] |
| SQL/RLS | Pendiente / OK / No aplica | [revision/migration] |
| QA visual/manual | Pendiente / OK / No aplica | [captura/checklist] |
| Gate mecanico de cierre | Pendiente / OK / NO-GO | `docker exec studiamatch-dev python3 scripts/maintenance/validate_hito_close.py --hito X` + `.context/evidencias/hito_X_qa_gate_report_YYYYMMDD_HHMMSS.md` |

## 8. Riesgos, Decisiones Y Observaciones

| Tipo | Descripcion | Decision / Mitigacion |
|---|---|---|
| Riesgo residual | [descripcion] | [mitigacion] |
| Decision tomada | [descripcion] | [razon] |
| Pendiente aprobado | [descripcion] | [hito/tarea futura] |

## 9. Estado Para Entrega

- [ ] Todos los CAs del hito tienen evidencia.
- [ ] Todos los CAs del hito tienen prueba ejecutada o no aplicable justificada.
- [ ] Gate mecanico de cierre ejecutado con resultado `GO`.
- [ ] Reporte QA del gate generado y versionado.
- [ ] No se agregaron alcances fuera de lo aprobado.
- [ ] Las validaciones requeridas fueron ejecutadas o justificadas como no aplicables.
- [ ] El informe puede compartirse con cliente/Notion.
- [ ] La tarea tecnica fue actualizada con resultado, commits/PR y evidencia.

## 10. Version Para Notion / Cliente

Resumen breve para copiar a Notion:

```text
Hito X — [nombre]
Estado: [Aprobado / En revision]

Entregado:
- [punto 1]
- [punto 2]

Criterios cubiertos:
- CAx: [cumple]
- CAy: [cumple]

Evidencia:
- PR/commit: [referencia]
- Validaciones: [resumen]

Pendientes o fuera de alcance:
- [si aplica]
```
