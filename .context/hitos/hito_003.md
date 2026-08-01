# HITO-003 - Panel Administrativo Y Curacion Manual

`HITO-003` agrupa CA4 para `REQ-EST-001`. Esta nota documenta alcance y
trazabilidad; no mantiene estado vivo.

## Alcance Propuesto

- `H3-CA4`: ruta `/admin` con cola de pendientes, edicion inline, fuente manual,
  timestamp de actualizacion y publicacion bajo proteccion compatible con
  static export.

## Seguridad

- Identidad administrativa separada de browser publico y pipeline.
- Escrituras privilegiadas solo mediante un mecanismo server-side/RPC aprobado.
- RLS y grants negativos por rol.
- Auditoria de cambios manuales y conflictos.

## Exclusiones

- No redefine CA2 ni el pipeline de Hito 2.
- No implementa Home o Resultados.
- No expone secret keys en browser.

## Dependencias

- Hito 2 desplegado con cola real y estados CA2/CA3 certificados.
- Mecanismo de autenticacion administrativa aprobado.

## Trazabilidad

- [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md)
- [TASK-H3-001](../backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md)
- [Estado del proyecto](../estado_del_proyecto.md)
- [Matriz de pruebas Hito 3](../pruebas/03_matriz_tests_hito_3.md)
