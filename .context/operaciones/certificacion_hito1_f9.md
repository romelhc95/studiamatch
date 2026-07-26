# Certificacion Hito 1 - Macrofase F9

Esta nota es la autoridad operativa de la macrofase F9 del plan `main -> Hito 1`. F9 comienza con preparacion local y termina unicamente en `free_certified`. No incluye Pro, produccion ni cierre final. [ADR-0004](../decisiones/ADR-0004_simplificacion_contractual_hito1.md) y [PLAN-H1-SIMPLIFICADO-001](./plan_simplificado_hito1.md) fijan la secuencia simplificada vigente.

La taxonomia y los alias historicos se fijan en [ADR-0003](../decisiones/ADR-0003_taxonomia_macrofases_subfases.md). La informacion vigente del antecedente temporal se preservo en [Preservacion F9.4](./preservacion_plan_temporal_f9_4.md) antes de retirarlo.

## Estado

- Macrofase F9: `IN_PROGRESS`.
- Estado del package: `reconciled_not_certified`.
- Free y Pro: schema apply bloqueado.
- Subfase autorizada: ninguna; la autorizacion read-only del tercer intento F9.5 fue consumida.
- Ultima subfase cerrada: F9.4 local/documental mediante el PR que adopta el plan simplificado.
- Siguiente accion: definir y aprobar una remediacion forward-only del drift de policies antes de repetir F9.5; F9.6 permanece bloqueada.

## Subfases

| ID | Alcance | Estado | Evidencia o condicion |
|---|---|---|---|
| `F9.1` | Precertificacion local/offline | `COMPLETED` | Alias historico `FASE-09`; PR #231/#232 y cierre #233 |
| `F9.2` | Reparacion local del contrato de promocion | `COMPLETED` | Alias historico `FASE-10`; PR #235/#236 |
| `F9.3` | Freeze local del contrato de preflight | `COMPLETED` | PR #238/#239; replay post-merge Docker sobre checkout Linux limpio |
| `F9.4` | Reconciliacion contractual local/documental | `COMPLETED` | Plan simplificado adoptado; definicion remota sustituida; antecedente temporal retirado |
| `F9.5` | Preflight Free read-only dirigido y aceptacion T01 | `BLOCKED` | Tercer `FREE_PREFLIGHT_FAIL`: inventario de policies no compatible con el overlay cerrado |
| `F9.6` | Backup H-00 y remediacion Free-only counts-only | `PENDING` | Reservada; backup y DML con aprobacion propia; nunca Pro |
| `F9.7` | Backup/pausa aprobados, schema/RLS Free y T02 | `PENDING` | Reservada; migration y writers tienen gates separados |
| `F9.8` | Aprobacion del plan de backfill | `PENDING` | Reservada; sin DML |
| `F9.9` | Ejecucion/certificacion de backfill y T03 | `PENDING` | Reservada; aprobacion de ejecucion separada |
| `F9.10` | Canary, smoke, QA, cleanup y certificacion final T04 | `PENDING` | Termina en `free_certified`/`FREE_CERTIFIED` |

La [definicion remota F9.4 anterior](./preflight_free_f9_4.md) es historica y no autorizable. F9.5 se limita al [preflight dirigido](./preflight_free_f9_5.md) y a [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md#definicion-autorizable-f95). Las reservas F9.6-F9.10 no son definiciones ejecutables. Cada subfase conserva alcance, stop conditions, PR/review y autorizacion exacta propios.

El intento F9.5 del `2026-07-26` confirmo localmente el package F8 y sus cuatro checksums, pero fallo cerrado antes de abrir Free porque faltaba el predicado H-00 privado exigido entonces. No se invocaron tools Supabase, no hubo SQL ni se inspeccionaron ledger, catalogos, datos, backup o writers; el FAIL permanece como evidencia historica.

La remediacion local autorizada reconcilia la evidencia H-00 recuperada sin copiar codigo ni SQL. Sustituye el requisito de manifest/UUID por la cohorte completa derivada en DB con cutoff `2026-07-19T00:00:00Z`; PASS requiere exactamente 3 leads totales, 3 pre-cutoff, 0 post-cutoff y 0 `email_log`, sin identidad individual. La decision no observa Free ni crea T01. Tras el merge documental se requiere otra autorizacion F9.5 read-only.

El segundo intento F9.5 read-only verifico binding Free, candidate, ledger, columnas, constraints e indices, y encontro drift RLS que el package exacto no elimina: 7/7 policies esperadas presentes, 6/7 compatibles y 3 policies publicas adicionales. El verificador F8 rechaza ese estado. La ejecucion fallo cerrado antes de ACL, RPC, conflictos, H-00, backup o writers; T01 no existe y F9.6 sigue bloqueada.

La remediacion local forward-only mantiene byte-identicos manifest/migrations F8 y agrega una quinta migration bajo un overlay nuevo ligado por digest completo. Versiona guards canary transitivos, restringe `institutions` a `id/name/slug`, limita `INSERT` de leads a las doce columnas enviadas por los formularios y excluye campos administrados, normaliza ACL de tabla y columna, fija owner `postgres`, rechaza superuser/BYPASS/membresias privilegiadas en roles publicos y `service_role`, exige `service_role BYPASSRLS` y cierra totalmente policies/ACL incluido `PUBLIC`.

La postcondicion sucesora cierra owner, lenguaje, volatilidad, modo, `search_path` y ACL propios. PostgreSQL 17 demostro una reconstruccion sintetica del baseline Free observado y convergencia del planner real desde 0/5, 3/5 y 4/5, aislamiento canary separado por URL, profile e institucion, rechazo de drift, rollback atomico y replay. El job CI exige PostgreSQL `--network none` y una prueba incremental del rechazo de egress IPv4 del proceso bajo reglas IPv4/IPv6.

El checksum sucesor es `4959b3f1ad60e2fe3a6e9a23161dd0467cfc549e10c1262ba8a0bb2aaf4c9a01` y el digest del manifest es `27af06a3411f65786d5dfbda19814c24b187f13a055a0fa4733698843f1d3353`. El descriptor F10/F9.2 no promociona este overlay; F9.7 debera versionar otro schema v2. El overlay sigue `reconciled_not_certified`, Free/Pro bloqueados y T01 ausente.

El tercer intento sincronizo `desarrollo@2e5be1719dffc8a867f4c40e4e8081b51ef56fb7`, confirmo binding Free, prefijo ledger `0/5` sin colision, `13/13` columnas, `11/11` constraints, `9/9` indices, RLS `6/6` y seguridad de roles `3/3`. El inventario de policies no puede converger al contrato cerrado con el overlay exacto y su verifier rechaza el drift persistente. El resultado es `FREE_PREFLIGHT_FAIL` y se detuvo antes de ACL, RPC, conflictos, H-00, backup o writers. T01 no fue preparada y F9.6 sigue bloqueada; el detalle permanece solo en evidencia privada ignorada.

## Identidades Historicas

- [Precertificacion local F9](./precertificacion_hito1_f9.md) conserva la identidad ejecutable cerrada `FASE-09` y se mapea a F9.1.
- [Contrato local F10](./promocion_hito1_f10.md) conserva descriptor, package y jobs `FASE-10` y se mapea a F9.2.
- El evidence type congelado `f9_completion` significa cierre del package historico `FASE-09`/F9.1, no cierre de la macrofase F9.
- Los nombres historicos no autorizan nuevas operaciones y no se renombran en codigo, manifests, tests o CI.

## Definicion De F9.3

Esta seccion conserva el contrato historico F9.3. Toda referencia futura a F9.4 registra el diseno vigente al cerrar F9.3 y fue sustituida por ADR-0004; no define ni autoriza capacidades actuales.

F9.3 tuvo capability exclusiva `LOCAL_FREE_PREFLIGHT_CONTRACT`. Congelo y probo localmente el contrato que entonces se preveia ejecutar en una F9.4 remota. F9.3 no cargo configuracion de ambiente, no conecto y no produjo `FREE_PREFLIGHT_PASS/FAIL`.

### Entregables F9.3

1. Descriptor inmutable del preflight con package/manifest/commit/tree, inventory y algoritmo de digest exactos.
2. Catalogo cerrado de consultas read-only, parametros, cardinalidad, paginacion, timeouts y shape esperado; cualquier consulta no enumerada falla antes de transporte.
3. Target binding Free por fingerprint no reversible, comparacion constant-time y rechazo de variables genericas/Pro/reutilizadas, sin loggear componentes.
4. Enforcement mecanico de solo lectura: metodos HTTP permitidos cerrados y consultas catalogo dentro de transaccion `READ ONLY`; no se expone primitive SQL/RPC generica.
5. Schema de evidencia sanitizada limitado a PASS/FAIL, conteos agregados y digests; prohibe URLs, refs, keys, filas, UUIDs y detalles explotables.
6. Runner de replay sintetico sin red que demuestre fail-closed ante escritura, query drift, target ambiguo, ledger incompleto, paginacion defectuosa, timeout o evidencia extra.
7. Job CI sin environment/secrets que ejecute solo el contrato local con egress bloqueado.

### Allowlist F9.3

- Nuevo descriptor `db/manifests/f9_3_free_preflight_contract.json`.
- Nuevo runner `scripts/maintenance/free_preflight.py`, sin modo remoto ejecutable en F9.3.
- Nuevas pruebas `tests/test_fase09_free_preflight.py` y fixtures sinteticos locales estrictamente necesarios.
- `.github/workflows/security-audit.yml` solo para un job local sin environment/secrets.
- Esta nota, `estado_del_proyecto.md`, `TASK-H1-001`, changelog y documentacion de cierre F9.3.

Todo path no enumerado queda excluido. F9.3 no modifica manifests/migrations F6-F10, workers, frontend, workflows de aplicacion ni artifacts historicos.

### Prohibiciones F9.3

- Cualquier red remota, Supabase MCP, advisor remoto, PostgREST real o carga de `.env*`/secrets.
- DDL, DML, RPC, `exec_sql`, backups, writers, H-00, backfill, migrations, workflow dispatch o cambios de status.
- Crear attestations, evidencia Free o presentar tests sinteticos como readiness.
- Implementar un flag, funcion o primitive que permitiera transporte dentro de F9.3.

### Gates F9.3

1. Esta reconciliacion y definicion deben pasar Context Graph, auditorias, CI, review y merge.
2. Despues del merge se requiere la frase exacta `Ejecuta las tareas pendientes de la Fase F9.3`.
3. La implementacion F9.3 no puede conectar; solo congela consultas, evidencia, target binding y enforcement con pruebas sinteticas.
4. El candidate F9.3 debe recibir auditorias, CI, review, merge, replay post-merge y PR documental de cierre.
5. El gate historico exigio cerrar F9.3 antes de la F9.4 remota entonces prevista y conservar sus artifacts; ADR-0004 sustituyo despues esa ruta sin reescribir la evidencia.

### Evidencia De Cierre F9.3

- Autorizacion exacta recibida: `Ejecuta las tareas pendientes de la Fase F9.3`.
- Descriptor/runner local: `LOCAL_VALID`, con `git_proof=EXTERNAL_REQUIRED`; no afirma readiness ni produce PASS/FAIL remoto.
- Suite focused: 55 pruebas PASS. Regresion F6-F10/credenciales: 253 pruebas PASS y un warning heredado de PyPDF2; total scoped 308.
- Replay sintetico determinista: 22 checks PASS. `py_compile`, `git diff --check` y Context Graph 30 archivos/232 enlaces: PASS.
- SHA-256 fijado del runner: `543cff44e46f84326ae774009a58ccf4fb7d0525ff0797cd5cca561706e45a00`.
- PR #238: CI verde, aprobacion de `romelhc95-approver` y merge humano en `desarrollo@4e712b0`.
- El primer replay post-merge encontro que el fixture temporal construia un blob CRLF desde el bind mount Windows aunque el validador comparaba correctamente identidad LF. PR #239 limito la remediacion al fixture, agrego la regresion CRLF, recibio CI/auditorias/review en GO y fue fusionado.
- Replay definitivo: `desarrollo@4e77fe0`, tree `efdf3f4edb53a384ee5f2a6251131696ccfb1865`, checkout limpio `i/lf w/lf` en el filesystem Linux interno de `studiamatch-dev`, sin ejecutar Python sobre el bind mount Windows. Pasaron 55 pruebas focused, 253 de regresion, 22 checks sinteticos, `py_compile` y Context Graph 30/232.
- Auditorias finales security y QA: GO, cero hallazgos bloqueantes. CI ejecuto el job F9.3 bajo `unshare --net`; el contenedor local carece deliberadamente de `CAP_SYS_ADMIN`, por lo que el replay local mantuvo ambiente vacio, runner sin transporte y bloqueo de sockets en pruebas. Los gaps de adapter, target identity artifact y traces fueron asignados entonces a una F9.4 remota, luego sustituida.
- Acceso Free/Pro, Supabase MCP, secrets, `.env*`, DDL/DML/RPC, attestations y transiciones de estado: cero.
- El PR documental que contiene esta evidencia completa F9.3 al fusionarse. No define, autoriza ni ejecuta F9.4.

## Definicion Sustituida De F9.4

La anterior [definicion F9.4](./preflight_free_f9_4.md) queda `SUPERSEDED_NON_AUTHORIZABLE`. F9.4 fue redefinida y completada como reconciliacion contractual local/documental; nunca implemento adapter ni accedio a Free/Pro. Los artifacts F9.3 permanecen historicos y byte-identicos, pero no gobiernan F9.5 ni crean criterios adicionales.

## Preservacion De La Secuencia Original F9

| Paso original | Asignacion canonica obligatoria |
|---|---|
| Validacion Free del package exacto | F9.5 y F9.7 |
| H-00 Free-only counts-only | F9.6 |
| ACL negativas `anon`/`authenticated` | F9.7 y revalidacion F9.10 |
| ACL positiva `service_role` con fixture sintetica | F9.7 y revalidacion F9.10 |
| Smoke FG2 sin fallback de persistencia | F9.10 |
| Cleanup idempotente | F9.10 |
| PR a `desarrollo` si el candidate nace temporal | Cada subfase aplicable; comprobacion final F9.10 |
| Promocion nueva a `certificacion` | F9.10 con review/CI |
| Canary Free desde package exacto | F9.10 |
| QA independiente | F9.10 |
| Estado final `FREE_CERTIFIED` | F9.10; equivale exactamente al estado de maquina `free_certified` |

## Gates Humanos Preservados

- El respaldo H-00 y su DML requieren aprobaciones propias en F9.6; la eliminacion no comienza sin respaldo verificado.
- Toda migration Free y el backup/restore previo requieren aprobacion explicita en F9.7.
- Pausar y reanudar writers son dos decisiones humanas separadas; F9.7 pausa y F9.10 solo puede reanudar despues de postcondiciones/QA.
- Plan y ejecucion de backfill requieren aprobaciones separadas en F9.8/F9.9.
- Cada merge a `desarrollo` y el merge a `certificacion` requieren aprobacion humana y CI en la subfase aplicable/F9.10.
- T04 exige `free_final_certification_approval` explicita en F9.10; canary o QA por si solos no cambian estado.
- Promocion Pro, pausa/reanudacion Pro, merge a `main` y release final pertenecen a F10 y conservan aprobaciones separadas.
- Eliminar ramas remotas pertenece a F11 y requiere aprobacion propia; el antecedente temporal ya fue retirado documentalmente en F9.4.

## Criterio De Salida De La Macrofase F9

F9 solo termina cuando T01-T04 son consecutivas y validas, Free alcanza `free_certified`/`FREE_CERTIFIED`, el package/checksums permanecen inmutables, H-00 queda excluido de Pro, ACL por rol, smoke FG2, canary exacto, QA independiente y cleanup idempotente pasan, y la evidencia queda aprobada. Solo entonces puede iniciar la ejecucion de F10 Produccion.

Ver [Estado](../estado_del_proyecto.md), [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Release minimo](./flujo_release_minimo.md) y [Matriz DB](./matriz_adopcion_db.md).
