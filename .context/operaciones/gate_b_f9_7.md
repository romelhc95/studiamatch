# Gate B F9.7 - EVID-F9.7-GATE-B-001

## Resultado

`FREE_GATE_B_FAIL_STOPPED_READ_ONLY`.

La autorizacion exacta `Ejecuta las tareas pendientes de la Fase F9.7` se consumio exclusivamente para Gate B pre-DDL/read-only en Free. La consulta agregada activo stop conditions por drift de acceso en superficies protegidas y privilegios publicos distintos del contrato final. No se ejecuto el runner HTTP posterior, no se solicitaron aprobaciones operativas y no se aplico ninguna mutacion.

## Binding Congelado

- Target: conexion project-scoped `supabase-free`; no se consulto ni cargo Pro.
- Candidate package: `F9.7-PUBLIC-ACCESS-CLOSURE-20260727`.
- Candidate revisado: commit `71868c62db3cf6a8303cdc117e834c11db282011`; tree `e08acc3f136ea9fd6a0d3c01def20d2a42542d13`; merge `3e18ec7ad2d2304179a0ce979b854db73e33d883`.
- Manifest candidate canonico: `5d32ed2c977c59c38d56948e687ba2b05ecd9ad8b2d3f5752cce3a9836889de3`.
- Closure: `040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b`.
- Contrato Gate B previo a la lectura: commit `9daf0ddef2955cc00239bba93541e1ac2c72ca0b`; tree `3912661b39a1122fba4a2a379d04dbb281c17822`.
- Query allowlisted: `F9.7-GATE-B-CATALOG-V1`; SHA-256 canonico `b7fc2e6485865ccbf91750a95a186f8e0468d9e8286a9b630af6780e054a8448`.

No se registran URL, project ref, keys, filas, UUID, PII, expresiones de policies ni respuestas raw.

## Allowlist Ejecutada

| Mecanismo | Permitido | Ejecutado | Resultado |
|---|---:|---:|---|
| `supabase-free.execute_sql` con el SQL exacto congelado | 1 | 1 | Una fila agregada; FAIL |
| Runner HTTP GET-only publishable/service | 6 requests maximo | 0 | Omitido por stop condition previa |
| Tools `supabase-pro`, DDL, DML, RPC, logs, advisors, branches o migrations | 0 | 0 | No autorizado |

La primera invocacion delegada se detuvo localmente por no recibir la frase literal y realizo cero llamadas. La misma sesion recibio despues la autorizacion exacta; solo entonces ejecuto la unica llamada remota registrada.

## Evidencia Agregada

| Control reducido | Resultado |
|---|---|
| Boundary y checksums del package candidate | `PASS_EMPTY_ALLOWED_BOUNDARY` |
| Colision con artifacts F9.5 no promocionables | `PASS_ABSENT` |
| Relaciones, columnas, RLS, owners y roles requeridos | `PASS` |
| Postura y acceso catalogado de identidad service | `PASS` |
| Policies no administradas por el candidate | `PASS_ABSENT` |
| Delegacion, grant options, membresias administrativas y accesos indirectos | `PASS_ABSENT` |
| Ausencia de lectura publica en superficies protegidas | `FAIL` |
| Restriccion exacta de columnas para captura publica | `FAIL` |
| Ausencia de capacidades publicas adicionales de tabla | `FAIL` |
| Compatibilidad remota con el estado final candidate | `FAIL` |
| Resultado consolidado Gate B | `FAIL_STOPPED_READ_ONLY` |

La evidencia completa se redujo en memoria desde una unica fila de conteos/booleanos y no se versiona para evitar publicar un mapa operativo. La consulta no leyo datos operativos. El candidate local demuestra convergencia sintetica, pero Gate B no puede usar esa prueba local para convertir el estado remoto observado en PASS ni para autorizar DDL.

## Responsables Y Aprobaciones

| Mecanismo | Operation owner | Reviewer humano | Estado |
|---|---|---|---|
| Resguardo y restore Free | Owner operativo vigente del repositorio | Reviewer humano independiente vigente | `NOT_SUBMITTED_BLOCKED_BY_GATE_B_FAIL` |
| Pausa de writers Free | Owner operativo vigente del repositorio | Reviewer humano independiente vigente | `NOT_SUBMITTED_BLOCKED_BY_GATE_B_FAIL` |

Las identidades concretas fueron resueltas desde la policy de aprobacion existente y no se duplican en esta evidencia. Los mecanismos requieren artifacts y decisiones humanas separadas. Solicitarlos ahora permitiria aprobar una ventana operativa sobre un preflight tecnico fallido, por lo que la stop condition prevalece. Reanudacion de writers sigue fuera de F9.7 y reservada para F9.10.

## Limite De Ejecucion

- Free: una consulta read-only agregada.
- Pro: cero acceso.
- DDL/DML/schema/migrations: cero.
- Pausa o reanudacion de writers: cero.
- Backup/restore ejecutado: cero.
- H-00, backfill, F9.8, certificacion, `main` y produccion: cero.
- Evidencia HTTP/runtime posterior: cero por fail-fast.

F9.7 permanece `IN_PROGRESS` y Free no esta certificada. Cualquier remediacion, nueva lectura, aprobacion operativa o aplicacion de la closure requiere una autorizacion decimal exacta nueva y un alcance definido desde el estado vivo.

## Referencias

- [Estado del proyecto](../estado_del_proyecto.md)
- [Macrofase F9](./certificacion_hito1_f9.md)
- [Plan simplificado](./plan_simplificado_hito1.md)
- [Matriz de adopcion DB](./matriz_adopcion_db.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
