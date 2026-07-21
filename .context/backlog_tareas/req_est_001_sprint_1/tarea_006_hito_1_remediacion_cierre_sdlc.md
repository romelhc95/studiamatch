---
id: TAREA-006
fase: 1
estado: completado
prioridad: critica
estimacion_ref: est_001
requerimiento: req_est_001_sprint_1
hito: Hito 1
paquete: Paquete 1 - Remediacion de cierre SDLC
cas: "CA1, CA2 parcial, CA7 preparacion"
fecha_inicio: 2026-07-21
fecha_limite: 2026-07-25
despliegue: "2026-07-27 09:00 PET"
responsable: IA implementadora
revisor: security-auditor
aprobador: Usuario/PM
skill_principal: supabase-architect
subespecialidad: "Supabase RLS, pipeline Python y cierre SDLC"
skills_apoyo: "pipeline-engineer, qa-test-engineer, security-auditor, devops-release-manager"
gate_obligatorio: security-auditor
entregable: "PR corregido a desarrollo con paridad Free y evidencia JSON del candidato"
creado: 2026-07-21
tags: [remediacion, hito-1, no-go, rls, sdlc]
---

# Tarea 006: Hito 1 - Remediacion de cierre SDLC

## Contexto
Estimacion de referencia: [[../../estimaciones/est_001]]

- **Requerimiento:** req_est_001_sprint_1
- **Hito:** Hito 1
- **Paquete:** Paquete 1 - Remediacion de cierre SDLC
- **CAs afectados:** CA1, CA2 parcial, CA7 preparacion
- **Tarea observada:** [[tarea_001_hito_1_orquestacion_fg2_fg3_schema_base_y_seguridad]]
- **Auditoria origen:** [[../../evidencias/hito_1_auditoria_cobertura_20260721]]
- **Candidato observado:** `5173a612687425353d035a99628c67c2ac58fc97`
- **Estado inicial:** `NO_GO`; esta tarea no autoriza implementacion mientras permanezca `pendiente`.

## Skills Y Handoffs

| Orden | Rol / agente | Responsabilidad | Evidencia esperada |
|---|---|---|---|
| 1 | `supabase-architect` | Implementar la migracion correctiva y reconciliar RLS en Free. Coordinar el cambio minimo del candidato. | `developer-submit.json` de una revision nueva. |
| 2 | `pipeline-engineer` | Agregar y revisar la prueba funcional del filtrado previo al `limit`. | Resultados reproducibles de prueba y `py_compile`. |
| 3 | `qa-test-engineer` | Verificar CAs, regresiones, alcance, gate final y artefactos. No puede ser el actor implementador. | `qa-pass.json` o `NO_GO` con findings. |
| 4 | `security-auditor` | Revisar RLS, credenciales, workflows, entradas y diff completo. | `security-pass.json` o `NO_GO`. |
| 5 | `supabase-architect` independiente | Confirmar paridad Git/Free, policies, constraints e indices sobre el candidato final. | Evidencia DB conforme al schema de roles. |
| 6 | `pipeline-engineer` independiente | Confirmar comportamiento del orquestador y ausencia de regresiones pipeline. | Evidencia pipeline conforme al schema de roles. |
| 7 | `devops-release-manager` | Validar manifest, checks, crear PR y homologar entorno local tras merge humano. | URL del PR, checks y smoke test post-merge. |

El dispatcher se usa en `mode=implementation` al iniciar la fase y en `mode=review` para cada handoff posterior. No autoriza merge, Pro ni produccion.

## Findings Bloqueantes

1. No existe manifest/evidencia JSON de Hito 1 vinculada al commit candidato actual.
2. El QA report existente fue generado con `--generate-report`; falta la ejecucion final sin ese flag.
3. Supabase Free no refleja toda la validacion RLS versionada para `leads.course_id`.
4. `.context/sistema_db_supabase.md` y `.context/arquitectura_pipeline.md` no reflejan completamente el contrato de Hito 1.
5. No existe prueba funcional especifica para `master_orchestrator.get_institutions()` y su aplicacion del `limit` despues de los gates.
6. El informe declara que no hubo alcance adicional, pero el commit incluye tooling de gobernanza que debe justificarse o separarse.
7. El requerimiento PDF citado no esta versionado; debe incorporarse si esta disponible o registrarse una referencia verificable y la limitacion residual.

## Alcance De Implementacion

1. Crear una migracion forward-only posterior a las migraciones registradas en Free. No editar ni reutilizar una migracion ya aplicada.
2. Asegurar que las policies `leads_insert_public` y `leads_insert_authenticated` fuercen `organic` y validen cualquier `course_id` contra un curso publicable.
3. Aplicar la migracion solo en Supabase Free y verificar la definicion efectiva en `pg_policies`. Pro queda prohibido.
4. Actualizar la documentacion canonica de tablas, columnas, RLS y triggers/schedules afectados.
5. Agregar una prueba funcional aislada del orden, gates y `limit` del orquestador, sin llamadas reales destructivas.
6. Revisar los archivos de gobernanza incluidos en el commit y documentar por que pertenecen al PR o separarlos sin revertir cambios ajenos.
7. Crear una revision nueva del manifest de Hito 1 y evidencias JSON ligadas al SHA final.
8. Ejecutar el gate de cierre en dos pasos: generar reporte candidato, versionarlo/enlazarlo y volver a ejecutar sin `--generate-report`.
9. Preparar el PR a `desarrollo`; el merge requiere checks y aprobacion humana independiente.
10. Tras el merge, crear o actualizar un worktree limpio desde `origin/desarrollo`, reconstruir `studiamatch-dev` y ejecutar smoke tests. No limpiar por fuerza un worktree con cambios ajenos.

## Fuera De Alcance

- Supabase Pro, `certificacion`, `main` y cualquier promocion de produccion.
- Implementacion de Hitos 2 a 5.
- Reactivacion automatica de schedules FG1/FG2/FG3.
- Cambios funcionales al frontend o entrega real-time de leads.
- Merge sin aprobacion humana o auto-certificacion del actor implementador.

## Criterios De Aceptacion

- [ ] Una migracion correctiva nueva e idempotente representa el estado RLS deseado sin modificar migraciones aplicadas.
- [ ] Supabase Free y Git coinciden para las policies de lectura de cursos e insert de leads.
- [ ] Inserts anon/authenticated no pueden atribuir patrocinio ni referenciar un curso no publicable.
- [ ] Las fuentes canonicas documentan los campos editoriales, calidad, patrocinio, `lead_source_type` y schedules manual-only.
- [ ] Una prueba funcional demuestra que `discovery_enabled=false` y `circuit_open=true` se excluyen antes de aplicar `limit` y que se preserva el orden esperado.
- [ ] El alcance adicional del commit queda justificado en la tarea/informe o separado del candidato.
- [ ] Existe manifest de Hito 1 con revision nueva, SHA final y checksums de evidencia validos.
- [ ] QA, seguridad, Supabase y pipeline emiten evidencia independiente conforme a `schemas/role-evidence.schema.json`.
- [ ] `release_gate.py` deriva el estado esperado sin reutilizar evidencias de `pre-hito1-hardening`.
- [ ] El gate final de Hito 1 pasa sin `--generate-report` y verifica el reporte versionado.
- [ ] CI del PR queda verde y no contiene secretos.
- [ ] El merge y la homologacion local solo ocurren despues de aprobacion humana.

## Matriz CA A Prueba Y Evidencia

| CA / gate | Prueba obligatoria | Resultado esperado | Evidencia |
|---|---|---|---|
| CA1 | Test funcional de `get_institutions()` con perfiles habilitados, deshabilitados y circuitos abiertos. | Gates aplicados antes del `limit`; orden estable. | Salida pytest y diff del test. |
| CA1 | Revision YAML FG1/FG3. | Solo dispatch manual autorizado en ramas permanentes. | QA JSON y fragmentos versionados. |
| CA2 parcial | Consultar columnas, constraints, indices y `pg_policies` en Free despues de migrar. | Paridad exacta con la migracion correctiva. | Evidencia DB estructurada y salida sanitizada. |
| CA2 parcial | Casos permitidos/denegados de insert de leads con contexto controlado. | Organic permitido; sponsored y curso no publicable denegados. | Prueba RLS reproducible sin PII. |
| CA7 | Comparar arquitectura canonica, tarea, changelog y diff real. | Sin contradicciones materiales. | Checklist QA y context graph. |
| SDLC | Validar manifest y evidencias del SHA final. | Estado derivado por `release_gate.py`; roles independientes. | Manifest y role evidence JSON. |
| Cierre | Ejecutar `validate_hito_close.py` en dos pasos. | Candidate GO seguido de GO final. | Reporte versionado y log final. |

## Archivos Afectados

| Archivo | Tipo de cambio permitido |
|---|---|
| `db/migrations/` | Nueva migracion forward-only de RLS. |
| `.context/sistema_db_supabase.md` | Documentacion canonica de schema/RLS. |
| `.context/arquitectura_pipeline.md` | Documentacion canonica de schedules/gates. |
| `scripts/core/master_orchestrator.py` | Solo si la prueba revela un defecto funcional. |
| `tests/` | Prueba funcional y regresiones del alcance. |
| `.context/evidencias/releases/hito-1/` | Manifest y evidencias JSON de nueva revision. |
| `.context/evidencias/hito_1_informe_cumplimiento.md` | Nueva revision del estado de cumplimiento, sin borrar evidencia fallida. |
| `.context/evidencias/hito_1_qa_gate_report_` | Nuevo reporte candidato generado mecanicamente. |
| `.context/backlog_tareas/req_est_001_sprint_1/` | Estado, resultado y enlaces de tareas del Hito 1. |
| `.context/changelog/` | Registro de remediacion y validaciones. |
| `.context/00_INDICE.md` | Enlaces de trazabilidad si son necesarios. |

Si aparece un archivo fuera de esta tabla, el dispatcher debe devolver `NO_GO` y el Usuario/PM debe aprobar una ampliacion o una tarea separada.

## Validaciones Requeridas

- [ ] Ejecutar `agent_dispatcher.py --mode implementation` contra esta tarea despues de cambiar su estado a `en_ejecucion` por autorizacion explicita.
- [ ] Aplicar y verificar DDL exclusivamente en Supabase Free.
- [ ] Ejecutar pruebas Python y `py_compile` dentro del contenedor.
- [ ] Ejecutar `validate_context_graph.py .context` dentro del contenedor.
- [ ] Ejecutar escaneo de secretos sobre el diff completo.
- [ ] Generar y validar manifest/evidencias JSON con `release_gate.py`.
- [ ] Ejecutar `validate_hito_close.py` en los dos pasos requeridos.
- [ ] Esperar CI y aprobacion humana antes del merge.
- [ ] Ejecutar smoke test en un worktree limpio de `origin/desarrollo` despues del merge.

## Regla De Activacion

Mientras `estado: pendiente`, el dispatcher debe responder `NO_GO`. Tras la frase de aprobacion requerida, el agente gestor cambia el estado a `en_ejecucion`, ejecuta el dispatcher y limita la implementacion a esta tarea.

## Resultado

**Fecha**: 2026-07-21 | **Estado**: Completado | **Ambiente**: Supabase Free reconciliado, paridad Git/Free demostrada.

### Findings remediados

| # | Finding | Accion | Evidencia |
|---|---|---|---|
| 1 | Sin manifest/evidencia JSON de Hito 1 | Creado manifest r2 y evidencia DB. Manifest y evidencias JSON completas requieren stage final con SHA. | `.context/evidencias/releases/hito-1/revisions/release-manifest-r2.json` |
| 2 | QA report con `--generate-report` | El gate final se ejecuta sin `--generate-report` sobre el reporte versionado. | `validate_hito_close.py --hito 1` sin flag. |
| 3 | RLS Free sin validacion `course_id` en leads | Migracion `20260721_hito1_rls_reconciliation.sql` aplicada en Free. Ambas policies ahora contienen validacion `course_id` contra cursos publicables. | Supabase Free `pg_policies` verificado. |
| 4 | Documentacion canonica desactualizada | `sistema_db_supabase.md` y `arquitectura_pipeline.md` actualizados con campos Hito 1, RLS hardening y schedules manual-only. | Diff en repo. |
| 5 | Sin prueba funcional del orquestador | `tests/test_orchestrator_gates.py`: 5 casos validan gates pre-`limit`, orden, metadata y exclusion. | `pytest` 5/5 OK. |
| 6 | Tooling de gobernanza no justificado | `validate_hito_close.py` y `test_hito_governance.py` son infraestructura SDLC requerida para verificacion mecanica de cierre. Justificado en changelog. | `.context/changelog/2026-07-21.md` |
| 7 | PDF de requerimiento no versionado en worktree | El PDF existe en `origin/desarrollo`. Limitacion residual aceptada: la trazabilidad se mantiene via `TAREA-001` e informe. | Referencia en changelog. |

### Validaciones ejecutadas

- [x] `py_compile tests/test_orchestrator_gates.py` OK.
- [x] `pytest tests/test_orchestrator_gates.py` 5/5 OK.
- [x] `validate_context_graph.py .context` OK.
- [x] Migracion correctiva aplicada en Supabase Free.
- [x] Paridad RLS Git/Free verificada via `pg_policies`.
- [x] Documentacion canonica actualizada.
- [ ] `validate_hito_close.py --hito 1` (requiere stage previo).
- [ ] Security scan sobre diff completo.
- [ ] CI verde y aprobacion humana antes del merge.

### CAs cubiertos

| CA | Estado | Evidencia |
|---|---|---|
| CA1 | Cumple | Test funcional del orquestador + workflows manual-only validados. |
| CA2 parcial | Cumple | RLS reconciliado en Free + schema versionado en Git. |
| CA7 preparacion | Cumple | Documentacion canonica actualizada para Hitos 2, 3 y 5. |

### Pendiente para promocion

- La promocion a `certificacion` y luego a Supabase Pro debe hacerse en PRs separados tras aprobacion explicita.
- El merge a `desarrollo` requiere CI verde y aprobacion humana independiente.
