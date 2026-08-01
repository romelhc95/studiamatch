# TASK-H3-001 - HITO-003

| Campo | Valor |
|---|---|
| ID | `TASK-H3-001` |
| Estado | `PENDING` |
| Requerimiento | `REQ-EST-001` |
| Hito | [HITO-003](../../hitos/hito_003.md) |
| Macrofase vigente | Ninguna; no activa |
| Subfase ejecutable | Ninguna |
| Criterios vigentes pendientes | `H3-CA4` |
| Bloqueador | Hito 2 desplegado con cola real de pendientes |

## Objetivo

Implementar `/admin` para listar pendientes, editar campos, registrar fuente
manual/timestamp y publicar bajo proteccion compatible con static export.

## Alcance

- Cola paginada de pendientes.
- Edicion inline de precio, duracion, modalidad, fecha, area y faltantes.
- Guardado con procedencia manual y control de conflictos.
- Publicacion al cumplir minimos.
- Autenticacion y autorizacion administrativa aprobadas.

## Exclusiones

- No redefine CA2/CA3.
- No usa secret keys en browser.
- No implementa Home ni Resultados.

## Dependencias

- Hito 2 completado y desplegado.
- Modelo de identidad admin y escritura server-side/RPC aprobado.

## Entregables

- Ruta y componentes admin.
- Contrato de autenticacion/autorizacion.
- Auditoria de cambios y pruebas negativas por rol.

## Criterios Y Entregables

| Criterio | Entregable | Verificacion | Evidencia | Estado |
|---|---|---|---|---|
| `H3-CA4` | Panel admin seguro | UI, RLS/RPC, auditoria y smoke | Vacio hasta candidate | `PLANNED` |

## Seguridad, Privacidad Y RLS

- Sesiones, ownership y autorizacion negativa.
- Escrituras privilegiadas fuera del browser.
- Auditoria sin PII en logs y prevencion de escalamiento horizontal/vertical.

## Metodo De Verificacion

La [matriz de pruebas Hito 3](../../pruebas/03_matriz_tests_hito_3.md) permanece
`PLANNED` y subordinada a esta TASK.

## Riesgos O Bloqueos

- Static export sin backend seguro.
- Secretos en cliente.
- Conflictos entre edicion manual y pipeline.
- Falta de trazabilidad de cambios.

## Criterio De Salida

Admin funcional, RLS/grants por rol, auditoria, QA y produccion observada.

## Enlaces Canonicos

- [Requerimiento](./_index.md)
- [Hito](../../hitos/hito_003.md)
- [Estado](../../estado_del_proyecto.md)
