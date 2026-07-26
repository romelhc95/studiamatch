# Certificacion Hito 1 - Macrofase F9

Esta nota es la autoridad operativa de la macrofase F9 del plan `main -> Hito 1`. F9 comienza con preparacion local y termina unicamente en `free_certified`. No incluye Pro, produccion ni cierre final.

La taxonomia y los alias historicos se fijan en [ADR-0003](../decisiones/ADR-0003_taxonomia_macrofases_subfases.md). `TEMP_PLAN_RECONSTRUCCION_MAIN_HITO1.md` permanece como antecedente congelado y no autoriza ejecucion.

## Estado

- Macrofase F9: `IN_PROGRESS`.
- Estado del package: `reconciled_not_certified`.
- Free y Pro: schema apply bloqueado.
- Attestations: cero.
- Subfase autorizada: ninguna; la autorizacion consumida de F9.3 no incluye F9.4 ni operaciones remotas.
- Ultima subfase cerrada: F9.3 local mediante PR #238, remediacion #239 y replay post-merge Docker.
- Siguiente subfase: F9.4 definida como `DEFINED_BLOCKED`; no autorizable mientras existan blockers.

## Subfases

| ID | Alcance | Estado | Evidencia o condicion |
|---|---|---|---|
| `F9.1` | Precertificacion local/offline | `COMPLETED` | Alias historico `FASE-09`; PR #231/#232 y cierre #233 |
| `F9.2` | Reparacion local del contrato de promocion | `COMPLETED` | Alias historico `FASE-10`; PR #235/#236 |
| `F9.3` | Freeze local del contrato de preflight | `COMPLETED` | PR #238/#239; replay post-merge Docker sobre checkout Linux limpio |
| `F9.4` | Ejecucion remota Free estrictamente read-only | `PENDING` | [Definida y bloqueada](./preflight_free_f9_4.md); usa unicamente F9.3 byte-identical |
| `F9.5` | Aceptacion local de readiness y T01 | `PENDING` | Reservada; no conecta ni aplica schema |
| `F9.6` | Backup aprobado, pausa aprobada, schema/RLS Free y T02 | `PENDING` | Reservada; migration y writers tienen gates separados |
| `F9.7` | H-00 Free-only counts-only | `PENDING` | Reservada; DML y aprobacion separadas |
| `F9.8` | Aprobacion del plan de backfill | `PENDING` | Reservada; sin DML |
| `F9.9` | Ejecucion/certificacion de backfill y T03 | `PENDING` | Reservada; aprobacion de ejecucion separada |
| `F9.10` | Canary, smoke, QA, cleanup y certificacion final T04 | `PENDING` | Termina en `free_certified`/`FREE_CERTIFIED` |

F9.4 tiene definicion documental propia, pero no es ejecutable mientras permanezca `DEFINED_BLOCKED`. Las reservas F9.5-F9.10 no son definiciones ejecutables. Cada subfase requiere alcance, allowlist, stop conditions, PR aprobado y autorizacion exacta propios.

## Identidades Historicas

- [Precertificacion local F9](./precertificacion_hito1_f9.md) conserva la identidad ejecutable cerrada `FASE-09` y se mapea a F9.1.
- [Contrato local F10](./promocion_hito1_f10.md) conserva descriptor, package y jobs `FASE-10` y se mapea a F9.2.
- El evidence type congelado `f9_completion` significa cierre del package historico `FASE-09`/F9.1, no cierre de la macrofase F9.
- Los nombres historicos no autorizan nuevas operaciones y no se renombran en codigo, manifests, tests o CI.

## Definicion De F9.3

F9.3 tiene capability exclusiva `LOCAL_FREE_PREFLIGHT_CONTRACT`. Congela y prueba localmente el unico contrato que una F9.4 posterior podra ejecutar contra Free. F9.3 no carga configuracion de ambiente, no conecta y no produce `FREE_PREFLIGHT_PASS/FAIL`.

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
- Implementar un flag, funcion o primitive que permita transporte antes de F9.4.

### Gates F9.3

1. Esta reconciliacion y definicion deben pasar Context Graph, auditorias, CI, review y merge.
2. Despues del merge se requiere la frase exacta `Ejecuta las tareas pendientes de la Fase F9.3`.
3. La implementacion F9.3 no puede conectar; solo congela consultas, evidencia, target binding y enforcement con pruebas sinteticas.
4. El candidate F9.3 debe recibir auditorias, CI, review, merge, replay post-merge y PR documental de cierre.
5. F9.4 no puede definirse ni autorizarse hasta cerrar F9.3. Debe conservar byte-identicos descriptor, catalogo de consultas, schema de evidencia y validadores; solo puede agregar un adapter de transporte minimo bajo allowlist/review propios.

### Evidencia De Cierre F9.3

- Autorizacion exacta recibida: `Ejecuta las tareas pendientes de la Fase F9.3`.
- Descriptor/runner local: `LOCAL_VALID`, con `git_proof=EXTERNAL_REQUIRED`; no afirma readiness ni produce PASS/FAIL remoto.
- Suite focused: 55 pruebas PASS. Regresion F6-F10/credenciales: 253 pruebas PASS y un warning heredado de PyPDF2; total scoped 308.
- Replay sintetico determinista: 22 checks PASS. `py_compile`, `git diff --check` y Context Graph 30 archivos/232 enlaces: PASS.
- SHA-256 fijado del runner: `543cff44e46f84326ae774009a58ccf4fb7d0525ff0797cd5cca561706e45a00`.
- PR #238: CI verde, aprobacion de `romelhc95-approver` y merge humano en `desarrollo@4e712b0`.
- El primer replay post-merge encontro que el fixture temporal construia un blob CRLF desde el bind mount Windows aunque el validador comparaba correctamente identidad LF. PR #239 limito la remediacion al fixture, agrego la regresion CRLF, recibio CI/auditorias/review en GO y fue fusionado.
- Replay definitivo: `desarrollo@4e77fe0`, tree `efdf3f4edb53a384ee5f2a6251131696ccfb1865`, checkout limpio `i/lf w/lf` en el filesystem Linux interno de `studiamatch-dev`, sin ejecutar Python sobre el bind mount Windows. Pasaron 55 pruebas focused, 253 de regresion, 22 checks sinteticos, `py_compile` y Context Graph 30/232.
- Auditorias finales security y QA: GO, cero hallazgos bloqueantes. CI ejecuto el job F9.3 bajo `unshare --net`; el contenedor local carece deliberadamente de `CAP_SYS_ADMIN`, por lo que el replay local mantuvo ambiente vacio, runner sin transporte y bloqueo de sockets en pruebas. Los gaps de adapter, target identity artifact y produccion de traces/evidencia pertenecen a F9.4.
- Acceso Free/Pro, Supabase MCP, secrets, `.env*`, DDL/DML/RPC, attestations y transiciones de estado: cero.
- El PR documental que contiene esta evidencia completa F9.3 al fusionarse. No define, autoriza ni ejecuta F9.4.

## Definicion Vigente De F9.4

La [definicion F9.4](./preflight_free_f9_4.md) congela capability `REMOTE_READ_FREE`, adapter separado, target binding previo a red, lecturas exactas, evidencia y stop conditions. Preserva byte-identicos descriptor, catalogos, traces/evidence schemas y validators F9.3. Registra cinco blockers: PostgREST, identidad SQL, advisor bridge, completitud ACL y binding cross-plane/single-use; no autoriza implementacion ni acceso remoto. F9.4 nunca crea T01, cambia status o desbloquea schema apply.

## Preservacion De La Secuencia Original F9

| Paso original | Asignacion canonica obligatoria |
|---|---|
| Validacion Free del package exacto | F9.4-F9.6 |
| H-00 Free-only counts-only | F9.7 |
| ACL negativas `anon`/`authenticated` | F9.6 y revalidacion F9.10 |
| ACL positiva `service_role` con fixture sintetica | F9.6 y revalidacion F9.10 |
| Smoke FG2 sin fallback de persistencia | F9.10 |
| Cleanup idempotente | F9.10 |
| PR a `desarrollo` si el candidate nace temporal | Cada subfase aplicable; comprobacion final F9.10 |
| Promocion nueva a `certificacion` | F9.10 con review/CI |
| Canary Free desde package exacto | F9.10 |
| QA independiente | F9.10 |
| Estado final `FREE_CERTIFIED` | F9.10; equivale exactamente al estado de maquina `free_certified` |

## Gates Humanos Preservados

- Toda migration Free y el backup/restore previo requieren aprobacion explicita en F9.6.
- Pausar y reanudar writers son dos decisiones humanas separadas; F9.6 pausa y F9.10 solo puede reanudar despues de postcondiciones/QA.
- H-00 requiere aprobacion DML propia en F9.7.
- Plan y ejecucion de backfill requieren aprobaciones separadas en F9.8/F9.9.
- Cada merge a `desarrollo` y el merge a `certificacion` requieren aprobacion humana y CI en la subfase aplicable/F9.10.
- T04 exige `free_final_certification_approval` explicita en F9.10; canary o QA por si solos no cambian estado.
- Promocion Pro, pausa/reanudacion Pro, merge a `main` y release final pertenecen a F10 y conservan aprobaciones separadas.
- Eliminar ramas remotas y retirar el plan temporal pertenecen a F11 y requieren aprobacion propia.

## Criterio De Salida De La Macrofase F9

F9 solo termina cuando T01-T04 son consecutivas y validas, Free alcanza `free_certified`/`FREE_CERTIFIED`, el package/checksums permanecen inmutables, H-00 queda excluido de Pro, ACL por rol, smoke FG2, canary exacto, QA independiente y cleanup idempotente pasan, y la evidencia queda aprobada. Solo entonces puede iniciar la ejecucion de F10 Produccion.

Ver [Estado](../estado_del_proyecto.md), [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Release minimo](./flujo_release_minimo.md) y [Matriz DB](./matriz_adopcion_db.md).
