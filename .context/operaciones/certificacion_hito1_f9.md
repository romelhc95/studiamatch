# Certificacion Hito 1 - Macrofase F9

Esta nota es la autoridad operativa de la macrofase F9 del plan `main -> Hito 1`. F9 comienza con preparacion local y termina unicamente en `free_certified`. No incluye Pro, produccion ni cierre final. [ADR-0004](../decisiones/ADR-0004_simplificacion_contractual_hito1.md) y [PLAN-H1-SIMPLIFICADO-001](./plan_simplificado_hito1.md) fijan la secuencia simplificada vigente.

La taxonomia y los alias historicos se fijan en [ADR-0003](../decisiones/ADR-0003_taxonomia_macrofases_subfases.md). La informacion vigente del antecedente temporal se preservo en [Preservacion F9.4](./preservacion_plan_temporal_f9_4.md) antes de retirarlo.

## Estado

- Macrofase F9: `IN_PROGRESS`.
- Base funcional contractual: F6-F8.
- Estado de certificacion: Free sigue sin certificar y Pro permanece bloqueado.
- Subfase activa: F9.7 `ACTIVE_AWAITING_AUTHORIZATION`.
- Subfase autorizada: ninguna. F9.6 esta cerrada sin DML y no habilita automaticamente schema/RLS.
- Ultima subfase cerrada: F9.6 `COMPLETED` como `H00_ALREADY_REMEDIATED_NO_DML`.
- Siguiente accion: F9.7 requiere una autorizacion decimal exacta nueva y sus prerrequisitos propios.

## Subfases

| ID | Alcance | Estado | Evidencia o condicion |
|---|---|---|---|
| `F9.1` | Precertificacion local/offline | `COMPLETED` | Alias historico `FASE-09`; PR #231/#232 y cierre #233 |
| `F9.2` | Reparacion local del contrato de promocion | `COMPLETED` | Alias historico `FASE-10`; PR #235/#236 |
| `F9.3` | Freeze local del contrato de preflight | `COMPLETED` | PR #238/#239; replay post-merge Docker sobre checkout Linux limpio |
| `F9.4` | Reconciliacion contractual local/documental | `COMPLETED` | Plan simplificado adoptado; definicion remota sustituida; antecedente temporal retirado |
| `F9.5` | Cierre contractual/documental | `COMPLETED_WITH_KNOWN_FINDINGS` | PR #245/#247 y sus artifacts son `HISTORICAL_NON_PROMOTABLE`; no queda repeticion Free pendiente |
| `F9.6` | P0 H-00 Free-only | `COMPLETED` | `H00_ALREADY_REMEDIATED_NO_DML`; PII directa remediada en la cohorte pseudonimizada; Gate B DELETE `SUPERSEDED_NON_AUTHORIZABLE`; nunca Pro |
| `F9.7` | Resguardo/restore, pausa, schema/RLS Free y T02 | `ACTIVE_AWAITING_AUTHORIZATION` | Definida, no autorizada; resguardo, migration y writers conservan gates separados |
| `F9.8` | Aprobacion del plan de backfill | `PENDING` | Reservada; sin DML |
| `F9.9` | Ejecucion/certificacion de backfill y T03 | `PENDING` | Reservada; aprobacion de ejecucion separada |
| `F9.10` | Canary, smoke, QA, cleanup y certificacion final T04 | `PENDING` | Termina en `free_certified`/`FREE_CERTIFIED` |

La [definicion remota F9.4 anterior](./preflight_free_f9_4.md) y el [registro F9.5](./preflight_free_f9_5.md) son historia no autorizable. Cada subfase pendiente conserva alcance, stop conditions, PR/review y autorizacion exacta propios.

## Cierre Contractual F9.5

F9.5 concluye sin repetir la lectura Free del overlay v2 y sin declarar `FREE_PREFLIGHT_PASS`. Los findings de los intentos historicos permanecen conocidos; no certifican Free/Pro ni se transforman en un package aplicable.

- Los artifacts de PR #245 y PR #247, incluidos migrations, manifests, reducers, runners, pruebas y cambios CI asociados a F9.5, son `HISTORICAL_NON_PROMOTABLE`.
- Se conservan fisicamente y no se incluyen en la base funcional contractual, en un package de F9.7 ni en un candidate de aplicacion. La base contractual sigue siendo F6-F8.
- `T01_CONDITIONAL_ACCEPTED` se acepto como cierre documental sin crear una attestation ni cambiar la maquina de promocion. Habilito solo la definicion entonces futura de F9.6.
- T01 nunca autorizo schema, migrations, F9.7, writers, backfill, Pro ni produccion. La definicion inicial de F9.6 contemplaba backup previo a DELETE; [el cierre posterior](./cierre_h00_f9_6.md) sustituyo esa rama al verificar la remediacion existente y cerrar sin DML.

## Cierre Exclusivo F9.6

F9.6 fue exclusivamente el P0 H-00, Free-only y previo a `FREE_CERTIFIED`; no es criterio contractual de Hito 1. La evidencia sanitizada [EVID-F9.6-H00-001](./cierre_h00_f9_6.md) verifico la cohorte con remediacion completa de PII directa y sin coincidencias parciales o invalidas. Se conserva pseudonimizada por su riesgo residual de vinculabilidad. El resultado es `H00_ALREADY_REMEDIATED_NO_DML`.

- Gate B DELETE queda `SUPERSEDED_NON_AUTHORIZABLE`.
- Los fixtures conservan UUID y metadatos pseudonimizados; el data owner acepta ese riesgo residual en Free restringido y prohibe correlacionarlos o copiarlos a Pro. F9.7 debe verificar ausencia de lectura publica y F11 revaluar retencion.
- DELETE, UPDATE, INSERT, backup valido, acceso Pro, schema, migrations, writers y backfill fueron cero.
- Seguridad y calidad de datos aprobaron la evidencia agregada. Este cierre no certifica Free ni autoriza F9.7.

## Definicion Exclusiva F9.7

F9.7 es la siguiente subfase y queda `ACTIVE_AWAITING_AUTHORIZATION`. Su primer gate futuro es exclusivamente pre-DDL y read-only: congela package, allowlist y stop conditions; liga Free; verifica identidad backend y estado de acceso; identifica responsables; y somete resguardo/restore y pausa de writers a aprobaciones humanas separadas. No pausa writers ni aplica schema/migrations.

Un gate F9.7 posterior, todavia no definido ni autorizado, podra aplicar schema/RLS/T02 solo despues de esas aprobaciones. Debera demostrar semanticamente que `leads` y `email_log` no tienen lectura publica, que `INSERT leads` solo acepta columnas permitidas y que las lecturas backend usan identidad de servicio. F9.7 no incluye H-00, backfill, Pro ni produccion.

## Dependencias Posteriores

Antes de definir una ejecucion F9.7 deben quedar planificadas y aprobadas: migrar lecturas backend desde identidad publica a identidad de servicio; verificar que `leads` y `email_log` no tengan lectura publica; restringir `INSERT` de `leads` por columnas; y aplicar schema/RLS por comportamiento semantico, no por conteo nominal de policies.

El backfill editorial es dependencia de `H1-CA2P` para F9.8/F9.9 y debe evitar que el catalogo quede invisible. Sus planificacion, autorizacion y ejecucion siguen separadas.

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

- F9.6 cerro H-00 con PII directa ya remediada y la cohorte conservada como pseudonimizada, sin DML; Gate B DELETE fue sustituido y no puede reabrirse desde esta macrofase.
- Toda migration Free y el backup/restore previo requieren aprobacion explicita en F9.7.
- Pausar y reanudar writers son dos decisiones humanas separadas; F9.7 pausa y F9.10 solo puede reanudar despues de postcondiciones/QA.
- Plan y ejecucion de backfill requieren aprobaciones separadas en F9.8/F9.9.
- Cada merge a `desarrollo` y el merge a `certificacion` requieren aprobacion humana y CI en la subfase aplicable/F9.10.
- T04 exige `free_final_certification_approval` explicita en F9.10; canary o QA por si solos no cambian estado.
- Promocion Pro, pausa/reanudacion Pro, merge a `main` y release final pertenecen a F10 y conservan aprobaciones separadas.
- Eliminar ramas remotas pertenece a F11 y requiere aprobacion propia; el antecedente temporal ya fue retirado documentalmente en F9.4.

## Criterio De Salida De La Macrofase F9

F9 solo termina cuando T01 condicionado y T02-T04 cumplen sus gates propios, Free alcanza `free_certified`/`FREE_CERTIFIED`, la base F6-F8 y sus checksums permanecen inmutables, H-00 queda excluido de Pro, ACL por rol, smoke FG2, canary exacto, QA independiente y cleanup idempotente pasan, y la evidencia queda aprobada. Solo entonces puede iniciar la ejecucion de F10 Produccion.

Ver [Estado](../estado_del_proyecto.md), [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Release minimo](./flujo_release_minimo.md) y [Matriz DB](./matriz_adopcion_db.md).
