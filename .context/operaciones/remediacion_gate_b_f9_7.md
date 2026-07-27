# Definicion De Remediacion Gate B F9.7

## Resultado

`REMEDIATION_DEFINED_BLOCKED_PENDING_ACL_SOURCE_ATTRIBUTION`.

La autorizacion exacta recibida se consumio solo para definir localmente la remediacion de [EVID-F9.7-GATE-B-001](./gate_b_f9_7.md). No hubo nueva lectura Free, acceso Pro, DDL/DML, schema remoto, migrations remotas, backup/restore, pausa de writers, backfill ni promocion.

## Conclusion De Cobertura

La closure F9.7 cubre localmente y hace converger las tres clases directas reducidas por Gate B:

| Clase reducida | Reparacion congelada | Prueba local |
|---|---|---|
| Lectura publica en superficies protegidas | Elimina policies conocidas, revoca `SELECT` efectivo directo y verifica policies/ACL finales | `LOCAL_PROVEN` |
| Columnas de captura publica no exactas | Revoca `INSERT` de tabla/columnas y concede solo la allowlist de doce columnas | `LOCAL_PROVEN` |
| Capacidades publicas adicionales | Revoca privilegios de tabla/columna y verifica ausencia efectiva final | `LOCAL_PROVEN` |

La prueba PostgreSQL 17 parte del boundary F8, confirma que los controles Gate B estan en FAIL, aplica exclusivamente la quinta entrada y exige que los controles de acceso y el agregado final pasen, con ledger final exacto.

La cobertura remota completa no puede afirmarse todavia. La evidencia sanitizada preserva el resultado efectivo, pero no el rol origen de cada ACL. Un grant heredado desde un rol ordinario no seria revocado por la closure actual: el verifier lo detecta y la transaccion revierte, pero deteccion no equivale a convergencia. La suite demuestra ese rollback y convierte la atribucion de origen en precondicion bloqueante de cualquier ventana futura.

## Package Congelado

- Package: `F9.7-PUBLIC-ACCESS-CLOSURE-20260727`.
- Manifest: `db/manifests/fase09_7_free_schema_rls.json`.
- Manifest canonico: `5d32ed2c977c59c38d56948e687ba2b05ecd9ad8b2d3f5752cce3a9836889de3`.
- Candidate revisado: commit `71868c62db3cf6a8303cdc117e834c11db282011`; tree `e08acc3f136ea9fd6a0d3c01def20d2a42542d13`.
- Closure: `040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b`.
- Orden: las cinco entradas F6-F8 + F9.7 existentes, sin cambios.
- Boundaries aceptados: vacio, F7, F8 y final.
- Ejecucion futura: una sola transaccion; ledger append-only despues de todas las postcondiciones.
- Migrations nuevas o modificadas por esta definicion: cero.
- F9.5, H-00, backfill, datos operativos y Pro: excluidos.

El descriptor no ejecutable es `db/manifests/fase09_7_remediation_definition.json`. Conserva `capabilities=[]`, bloquea Free/Pro y no habilita la generacion ni aplicacion remota del package.

## Allowlist Futura Congelada

Una fase posterior solo podra avanzar, bajo autorizacion nueva, por esta secuencia logica:

1. Ligar Free mediante fingerprint privado no reversible.
2. Verificar commit, tree, package, orden y digests exactos.
3. Atribuir read-only el origen de toda ACL efectiva de roles publicos.
4. Rechazar cualquier origen de ACL que el package congelado no revoque.
5. Rechazar policy no administrada, grant heredado o acceso indirecto.
6. Confirmar boundary de ledger permitido, sin gap, colision ni cambio concurrente.
7. Exigir runbook de resguardo/restore en `RESTORE_PROVEN`.
8. Exigir runbook de writers en `HELD`.
9. Exigir decisiones humanas separadas y vigentes.
10. Aplicar solo el package exacto en una transaccion.
11. Ejecutar postcondiciones dentro de la transaccion antes del ledger.
12. Ejecutar postcondiciones read-only independientes despues del commit.
13. Mantener writers pausados hasta F9.10.

Esta lista no contiene SQL, comandos, transporte, secretos ni capacidad remota. La atribucion read-only futura no esta implementada ni autorizada por esta definicion.

## Rollback Y Recuperacion

### Antes Del Commit

- Cualquier guard, timeout, checksum, verifier o postcondicion falsa revierte la transaccion completa.
- No se agrega ninguna entrada de ledger.
- No se permite continuar parcialmente ni improvisar SQL.
- PostgreSQL 17 prueba rollback con una policy desconocida y con un grant heredado no reparable desde boundary F8.

### Despues Del Commit

- No existe down migration automatica.
- Writers permanecen pausados.
- Se abre un incidente con autorizacion humana independiente.
- Las unicas decisiones permitidas son forward-fix o restore.
- Editar ledger, usar snapshot superseded o reanudar writers queda prohibido.

## Postcondiciones

La aplicacion futura debera demostrar, sin registrar datos raw:

1. Package, orden, checksums y boundary exactos.
2. Verificadores de cada prefijo y verifier final F9.7 en PASS.
3. Ledger final append-only de cinco entradas.
4. RLS, owners y postura de roles exactos.
5. Negativos publicos de lectura en superficies protegidas.
6. `INSERT` publico limitado exactamente a doce columnas.
7. Ausencia de capacidades publicas adicionales, grants heredados y accesos indirectos.
8. Acceso positivo de identidad service.
9. Comportamiento PostgREST negativo publico y positivo service sin bodies.
10. Verificacion post-commit independiente.
11. Writers todavia en `HELD`.

## Runbooks No Ejecutables

### Resguardo Y Restore

`db/runbooks/fase09_7_backup_restore.json` congela estados `PLANNED -> APPROVED -> CREATED -> INTEGRITY_ATTESTED -> RESTORE_PROVEN`, custodia cifrada fuera del repositorio, integridad no reversible, restore en destino aislado, RPO/RTO humanos y recuperacion pre/post-commit. Su estado actual es `PLANNED`; sus dos decisiones humanas siguen `required_not_granted`.

### Pausa De Writers

`db/runbooks/fase09_7_writer_pause.json` congela estados `INVENTORIED -> PAUSE_APPROVED -> PAUSE_CONFIRMED -> DRAIN_CONFIRMED -> HELD`. Incluye FG1, las estaciones FG2, FG3, captura publica y writers manuales/externos. Cualquier writer desconocido o job en vuelo detiene la ventana. Su estado actual es `INVENTORIED`; la pausa no esta aprobada y la reanudacion sigue reservada para F9.10.

Los runbooks contienen `capabilities=[]` y `commands=[]`. Definirlos no crea backup, no restaura, no pausa y no reanuda.

## Gate B Consumido

`db/manifests/fase09_7_gate_b_readonly.json` queda `CONSUMED_FAIL_NON_AUTHORIZABLE`, sin allowlist de tools ni HTTP. El runner HTTP historico no forma parte del tree vigente. El contrato ejecutado permanece auditable por commit/digest, pero no puede reutilizar transporte ni autorizacion.

## Stop Conditions

- Falta atribucion completa de origen de ACL o aparece un origen no reparado.
- Package, commit, tree, orden o digest no coincide.
- Boundary no permitido, gap, colision o cambio concurrente.
- Runbook de restore distinto de `RESTORE_PROVEN`.
- Runbook de writers distinto de `HELD`.
- Decisiones humanas faltantes, reutilizadas o no independientes.
- Aparece policy no administrada, grant heredado o acceso indirecto.
- Cualquier test, CI, auditoria, review o Context Graph falla.
- Se intenta registrar ledger antes de postcondiciones.
- Se intenta nueva lectura, transporte, DDL/DML, pausa o aplicacion con esta autorizacion.
- Se intenta reanudar writers antes de F9.10.

## Estado Y Siguiente Accion

F9.7 permanece `IN_PROGRESS`; Free no esta certificada. La definicion queda bloqueada por atribucion de origen ACL y por runbooks/aprobaciones no satisfechos. Despues del merge y replay post-merge de esta definicion, cualquier nueva lectura read-only o accion operativa requerira otra autorizacion decimal exacta y un alcance nuevo. F9.8, Pro, certificacion y produccion siguen bloqueados.

## Referencias

- [Estado del proyecto](../estado_del_proyecto.md)
- [Evidencia Gate B](./gate_b_f9_7.md)
- [Macrofase F9](./certificacion_hito1_f9.md)
- [Flujo de release](./flujo_release_minimo.md)
- [Matriz DB](./matriz_adopcion_db.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
