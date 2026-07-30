# Atestacion De Origen ACL F9.7

## Resultado

`FREE_ACL_SOURCE_ATTESTED_PACKAGE_COVERAGE_COMPLETE_STOPPED_READ_ONLY`.

`EVID-F9.7-ACL-SOURCE-001` consumio una autorizacion de alcance decimal exacto mediante una sola llamada `supabase-free.execute_sql`, sin retry ni HTTP. La sentencia congelada fue un unico `WITH RECURSIVE ... SELECT`, leyo exclusivamente `pg_catalog`, devolvio una fila de escalares sanitizados y no consulto filas de negocio.

## Binding

- Contrato: commit `64939f389d14fa9f878f925812ca9abea2de9bc8`; tree `0fbdd52f4eebfff63b4d3760f076511e9caff306`.
- Query: `F9.7-ACL-SOURCE-CATALOG-PG17-V1`.
- SHA-256 canonico: `71ff247d9608257ea99777d8f72f7d7db7f8f688601c4d8311c6bc6ee5bd8889`.
- Package comparado: `F9.7-PUBLIC-ACCESS-CLOSURE-20260727`.
- Manifest canonico: `5d32ed2c977c59c38d56948e687ba2b05ecd9ad8b2d3f5752cce3a9836889de3`.
- Closure: `040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b`.

## Atribucion Sanitizada

Los conteos siguientes son incidencias agregadas de fuente efectiva por principal/capacidad, no filas de negocio ni una lista de objetos o identidades:

| Clase | Resultado |
|---|---|
| Targets/roles requeridos | `2/3`, completos; PostgreSQL 17 soportado |
| RLS/owner/postura de roles | `2` targets con RLS; `0` mismatches o violaciones |
| Rutas de membresia | `3` directas; `0` inherited, SET, SET-then-INHERIT o truncadas |
| Delegacion/elevacion | `0` admin options, rutas elevadas o grant options |
| Fuentes ACL | `48` tabla directas, `0` columna, `7` schema; `0` heredadas, SET o desconocidas |
| Acceso por owner publico | `0` |
| Policies | `5` administradas por la closure; `0` no administradas |
| Views/rules/definers desconocidos | `0/0/0`; rules target `0` |
| Trigger indirecto | `4` incidencias del trigger conocido; `0` triggers inesperados |
| Dynamic/publication/partition | `0/0/0` |

La atribucion concluye `package_source_coverage=complete`: no se observo una fuente heredada, asumible, de owner, elevada, desconocida o indirecta no reparada por el package congelado. Esta conclusion vale solo para el snapshot catalog-only observado y no prueba convergencia ni ausencia de drift posterior.

## Comparacion Con La Closure

El estado actual permanece `closure_coverage=incomplete` y `catalog_comparison_pass=false`. El snapshot observo drift directo reparable: capacidades publicas de tabla, lectura publica, columnas `INSERT leads` faltantes respecto de la allowlist final y una policy de lectura administrada por la closure.

`fail_closed=true` porque `catalog_comparison_pass=false` y el trigger conocido activa `requires_supplemental_attestation=true`. Ademas, un limite deliberado bloquea independientemente cualquier aplicacion:

1. Los predicados de policy no fueron leidos ni atestados.
2. El trigger conocido de captura permanece alcanzable y requiere una atestacion separada de cuerpo, destino y efecto externo.

La atestacion ACL no autoriza aplicar el package. Los runbooks siguen `PLANNED`/`INVENTORIED`, las aprobaciones siguen sin concederse y la ventana operativa no existe.

[ADR-0005](../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md) conserva esta atestacion como historia read-only consumida. No atesta el security hold terminal, no prueba Free/Pro contenidos y no habilita una nueva lectura; PR-O posterior debera obtener evidencia propia para v3 + hold.

## Operaciones Excluidas

- DDL/DML, schema y migrations: cero.
- Backup/restore y pausa/reanudacion de writers: cero.
- Lecturas de filas de negocio y HTTP/PostgREST: cero.
- Pro, backfill, F9.8, certificacion y produccion: cero.
- Llamadas Free adicionales o retries: cero.

## Siguiente Gate

La autorizacion queda consumida y no es reutilizable. F9.7 permanece `IN_PROGRESS`; antes de cualquier aplicacion se requiere definir, autorizar y ejecutar separadamente evidencia para v3 + security hold, ademas de satisfacer restore `RESTORE_PROVEN`, writers `HELD` y decisiones humanas independientes.

## Referencias

- [Estado del proyecto](../estado_del_proyecto.md)
- [Definicion de remediacion](./remediacion_gate_b_f9_7.md)
- [Gate B](./gate_b_f9_7.md)
- [Macrofase F9](./certificacion_hito1_f9.md)
- [Matriz DB](./matriz_adopcion_db.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
