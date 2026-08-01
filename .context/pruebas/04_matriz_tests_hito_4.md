# Matriz De Tests Hito 4

Plan subordinado a [TASK-H4-001](../backlog_tareas/req_est_001_sprint_1/tarea_004_hito_4.md).
Hito 4 permanece `PENDING`.

| Test ID | CA | Requisito verificable | Clasificacion | Precondicion | Procedimiento | Resultado esperado | Ambiente | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|---|
| `T-H4-CA5-001` | `CA5 / H4-CA5` | Home presenta las cuatro secciones aprobadas | `CONTRACTUAL_CA` | Dataset controlado | Renderizar Home desktop y mobile | Instituciones, destacados, inscripciones y paises presentes | Local / Certification | Vacia hasta candidate | `PLANNED` |
| `T-H4-CA5-002` | `CA5 / H4-CA5` | Datos publicos y placeholders respetan contrato | `SECURITY_REQUIRED` | API stub permitida | Inspeccionar queries y estados sin dato | Solo campos publicos; placeholders solo donde estan permitidos | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H4-CA6-001` | `CA6 / H4-CA6` | Tipografia, cards y textos coinciden con referencia | `CONTRACTUAL_CA` | Referencia aprobada | Comparacion visual por viewport | Diferencias dentro de tolerancia acordada | Local / Certification | Vacia hasta candidate | `PLANNED` |
| `T-H4-CA6-002` | `CA6 / H4-CA6` | ROI permanece oculto en superficies publicas | `REGRESSION_REQUIRED` | Candidate exportado | Buscar copy, componentes y datos ROI visibles | Cero ROI publico | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H4-CA7-001` | `CA7 / H4-CA7` | Documentacion describe tablas y campos autorizados | `CONTRACTUAL_CA` | Candidate tecnico | Contrastar docs con schema/codigo versionado | Sin campos inventados, sensibles u obsoletos | Documental | Vacia hasta candidate | `PLANNED` |
| `T-H4-CA7-002` | `CA7 / H4-CA7` | Documentacion describe pipeline y operacion vigente | `CONTRACTUAL_CA` | Candidate tecnico | Contrastar diagramas, jobs, gates y runbooks | Arquitectura coincide con codigo y estados canonicos | Documental | Vacia hasta candidate | `PLANNED` |
| `T-H4-CA13H-001` | `CA13 / H4-CA13H` | Home respeta estructura, paleta, jerarquia y CTA | `CONTRACTUAL_CA` | Referencia aprobada | Comparar desktop y mobile con evidencia visual | Diferencias objetivas registradas y aceptadas | Certification | Vacia hasta candidate | `PLANNED` |
| `T-H4-REG-001` | `CA5, CA6, CA13H` | Home es responsive y accesible | `REGRESSION_REQUIRED` | Build estatico | Teclado, foco, zoom 200%, 375x667 y reflow | Sin bloqueo, overflow ni perdida de contenido | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H4-OPS-001` | `CA5, CA6, CA13H` | Export estatico no presenta errores de hydration o egress | `OPERABILITY_REQUIRED` | Build hostil | Lint, typecheck, build y Playwright hermetico | Cero errores y solo egress permitido | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H4-OOS-001` | `CA5` | Selector no usa tipo de cambio real | `OUT_OF_SCOPE` | Candidate Home | Revisar requests y comportamiento | Selector visual/tasa estatica, sin API cambiaria | Local / CI | Vacia hasta candidate | `PLANNED` |

## Gate De Salida

La referencia visual, los viewports y la tolerancia deben quedar fijados antes
de ejecutar CA6/CA13H. Un screenshot aislado no es evidencia suficiente.
