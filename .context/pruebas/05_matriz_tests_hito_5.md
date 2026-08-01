# Matriz De Tests Hito 5

Plan subordinado a [TASK-H5-001](../backlog_tareas/req_est_001_sprint_1/tarea_005_hito_5.md).
Hito 5 permanece `PENDING`.

| Test ID | CA | Requisito verificable | Clasificacion | Precondicion | Procedimiento | Resultado esperado | Ambiente | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|---|
| `T-H5-CA8-001` | `CA8 / H5-CA8` | Search permanece sticky en Resultados | `CONTRACTUAL_CA` | Dataset paginado | Hacer scroll en desktop/mobile | Busqueda disponible segun referencia | Local / Certification | Vacia hasta candidate | `PLANNED` |
| `T-H5-CA8-002` | `CA8 / H5-CA8` | Chips se remueven y limpiar filtros restablece estado | `CONTRACTUAL_CA` | Multiples filtros activos | Remover uno y luego limpiar todos | Query, resultados y controles quedan consistentes | Local / Certification | Vacia hasta candidate | `PLANNED` |
| `T-H5-CA9-001` | `CA9 / H5-CA9` | Sidebar cubre seis dimensiones aprobadas | `CONTRACTUAL_CA` | Dataset por dimension | Aplicar disponibilidad, area, modalidad, pais, precio y duracion | Cada dimension reduce el conjunto correctamente | Local / Certification | Vacia hasta candidate | `PLANNED` |
| `T-H5-CA9-002` | `CA9 / H5-CA9` | Combinacion, orden y paginacion son deterministas | `REGRESSION_REQUIRED` | Dataset mayor a una pagina | Combinar filtros, navegar y repetir | Mismo orden, conteo y elementos por pagina | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H5-CA9-003` | `CA9 / H5-CA9` | Queries publicas son acotadas | `SECURITY_REQUIRED` | API stub y candidate | Inspeccionar columnas, filtros y limites | Sin ampliar columnas/gates ni respuestas masivas | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H5-CA10-001` | `CA10 / H5-CA10` | Patrocinado y organico se distinguen por flag certificado | `CONTRACTUAL_CA` | Dataset mixto | Renderizar y ordenar cards | Badge/distincion correctos; verificado no equivale a patrocinado | Local / Certification | Vacia hasta candidate | `PLANNED` |
| `T-H5-CA10-002` | `CA10 / H5-CA10` | Card navega; acciones secundarias no navegan | `REGRESSION_REQUIRED` | Card interactiva | Activar detalle, Comparar, Me interesa y Avisarme | Solo card/detalle navega; no aparece texto Contactar | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H5-CA11-001` | `CA11 / H5-CA11` | Contador refleja filtros y paginas | `CONTRACTUAL_CA` | Dataset controlado | Aplicar, remover y combinar filtros | Conteo coincide con conjunto total y estado vacio | Local / Certification | Vacia hasta candidate | `PLANNED` |
| `T-H5-CA12-001` | `CA12 / H5-CA12` | CA12 esta absorbido por CA9 | `OUT_OF_SCOPE` | Matriz final | Revisar entregables y cobertura CA9 | Sin segunda funcionalidad, suite o conteo contractual | Documental | Vacia hasta candidate | `PLANNED` |
| `T-H5-CA13R-001` | `CA13 / H5-CA13R` | Resultados respeta referencia aprobada | `CONTRACTUAL_CA` | Referencia aprobada | Comparar estructura, paleta, jerarquia y CTA por viewport | Diferencias objetivas registradas y aceptadas | Certification | Vacia hasta candidate | `PLANNED` |
| `T-H5-REG-001` | `CA8-CA13R` | Teclado, foco, zoom, reflow y estados degradados funcionan | `REGRESSION_REQUIRED` | Build estatico | Ejecutar matriz accesible y responsive | Sin bloqueo, overflow, hydration o errores de consola | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H5-OOS-001` | `CA10` | Acciones no activan entrega real-time | `OUT_OF_SCOPE` | Candidate Resultados | Bloquear y observar egress | Cero email/webhook real-time | Local / CI | Vacia hasta candidate | `PLANNED` |

## Gate De Salida

CA12 reutiliza la evidencia CA9 y nunca genera doble alcance. CA13R requiere
referencia aprobada y comparacion reproducible; la matriz no decide una nueva
ruta frontend.
