# Matriz De Tests Hito 3

Plan subordinado a [TASK-H3-001](../backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md).
Hito 3 permanece `PENDING`, bloqueado por Hito 2.

| Test ID | CA | Requisito verificable | Clasificacion | Precondicion | Procedimiento | Resultado esperado | Ambiente | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|---|
| `T-H3-CA4-001` | `CA4 / H3-CA4` | `/admin` lista pendientes paginados | `CONTRACTUAL_CA` | Cola CA2/CA3 certificada | Ingresar como admin y recorrer paginas | Solo pendientes autorizados, sin omisiones/duplicados | Local / Certification | Vacia hasta candidate | `PLANNED` |
| `T-H3-CA4-002` | `CA4 / H3-CA4` | Edicion registra fuente y timestamp manual | `CONTRACTUAL_CA` | Registro pendiente | Editar campos permitidos y guardar | Valores y procedencia manual quedan auditables | Local / Certification | Vacia hasta candidate | `PLANNED` |
| `T-H3-CA4-003` | `CA4 / H3-CA4` | Conflicto pipeline/admin no sobrescribe silenciosamente | `REGRESSION_REQUIRED` | Versiones concurrentes | Actualizar por pipeline y luego guardar edicion obsoleta | Conflicto visible y datos protegidos | Local | Vacia hasta candidate | `PLANNED` |
| `T-H3-CA4-004` | `CA4 / H3-CA4` | Publicacion exige minimos CA2/CA3 | `CONTRACTUAL_CA` | Registros suficiente e insuficiente | Intentar publicar ambos | Solo el suficiente cambia a publicado | Local / Certification | Vacia hasta candidate | `PLANNED` |
| `T-H3-CA4-005` | `CA4 / H3-CA4` | Publico y no-admin no pueden leer cola ni escribir | `SECURITY_REQUIRED` | Matriz de identidades | Ejecutar negativos UI, RPC y PostgREST | Acceso denegado sin fuga de datos | Local / Free | Vacia hasta candidate | `PLANNED` |
| `T-H3-CA4-006` | `CA4 / H3-CA4` | Secret key no entra al static export o browser | `SECURITY_REQUIRED` | Build hostil | Escanear bundle y requests | Cero secretos; writer permanece server-side/RPC aprobado | Local / CI | Vacia hasta candidate | `PLANNED` |
| `T-H3-CA4-007` | `CA4 / H3-CA4` | Auditoria registra actor y cambio sin PII en logs | `SECURITY_REQUIRED` | Edicion autorizada | Editar y revisar auditoria/logs sanitizados | Trazabilidad suficiente, cero PII expuesta | Local / Certification | Vacia hasta candidate | `PLANNED` |
| `T-H3-CA4-008` | `CA4 / H3-CA4` | Proteccion funciona con static export | `OPERABILITY_REQUIRED` | Candidate frontend y mecanismo aprobado | Build, login, edicion y smoke | Ruta protegida funcional sin backend inseguro en browser | Certification / Production | Vacia hasta candidate | `PLANNED` |

## Gate De Salida

Se requiere autenticacion/autorizacion aprobada, negativos por rol, auditoria,
QA y produccion observada. Esta matriz no decide el mecanismo de identidad ni
lo implementa antes de Hito 2.
