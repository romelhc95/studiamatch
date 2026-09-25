# H3REQ1 Remediation Plan — 2026-09-24

Estado vivo: `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`

Revisión documental: 2026-09-24, ciclo 3. Esta revisión solo afina el plan;
no modifica código, SQL, Edge, frontend ni pruebas, y no ejecuta DDL, writes,
Auth, correo, deploy, push, PR, merge, cleanup, rollback o promoción.

Este plan continúa la auditoría del 2026-09-23. No amplía el alcance H3REQ1 y no
autoriza DDL, writes Supabase, Auth real, despliegues, push, PR, merge ni
promoción.

## Tareas y gates

| ID | Tarea | Gate de validación | Estado | Bloqueador |
|---|---|---|---|---|
| R1 | Capturar baseline remoto Free/Pro en modo lectura | Snapshot sanitizado de migrations, tablas, RPCs y Edge Functions | `PASS` | El snapshot existe; el drift contractual se evalúa en H3-001/R3 |
| R2 | Validar Free y aplicar solo deltas aprobados | Migraciones `20260918`–`20260921` y hardening `20260924`, smoke Auth/DB y auditoría | `BLOCKED` | No repetir migraciones Free ya registradas; JIT DDL si aparece delta |
| R3 | Alinear Pro con baseline H3REQ1 aprobado | Migrations aplicadas, metadata y RPCs verificadas | `BLOCKED` | JIT DDL Pro separado |
| R4 | Alinear/deployar `admin-invite` por ambiente | Hash/version/`verify_jwt=true`, logs sin secretos y smoke controlado | `BLOCKED` | JIT Edge deploy separado |
| R5 | Ejecutar flujo real admin → invitación → aceptación → password → onboarding → privado | UAT remota por ambiente, correo/Auth real y reconciliación Auth/DB | `BLOCKED` | R2/R3/R4 y datos de prueba autorizados |
| R6 | Completar `expand → compatibilidad → deploy → contract` | Evidencia por ambiente, contract/cleanup y rollback reproducible | `BLOCKED` | Deploy/promotion y autorización humana |

`PASS` en R1 solo acredita que el inventario read-only fue capturado. No acredita
convergencia, runtime ni autorización de cambios. El resultado contractual vigente
de H3-001 es `FAIL` por drift Pro. Todo resultado operativo de este plan usa
exclusivamente `PASS`, `FAIL` o `BLOCKED`; no se usa `PASS_WITH_DRIFT`.

## Criterio de parada

No se continúa con R2–R6 sin aprobación humana JIT explícita para cada clase de
acción. Una aprobación para Free no autoriza Pro, Edge deploy, Auth real,
Cloudflare, promoción ni cleanup.

## Ciclo operativo requerido para alcanzar GO

Este documento no declara GO ni autoriza cambios. Define el ciclo que se
ejecutará cuando exista la autorización humana correspondiente:

```text
baseline local
  -> validación Docker
  -> snapshot remoto
  -> promoción autorizada del componente
  -> prueba remota del gate
  -> análisis del resultado
  -> corrección local si falla
  -> validación Docker de la corrección
  -> nueva promoción autorizada
  -> revalidación remota
```

La unidad de promoción será el componente mínimo que corrige el fallo. No se
subirá un nuevo conjunto completo si el hallazgo está limitado a DB, Edge o
frontend. Cada iteración tendrá un identificador, commit/artefacto, ambiente,
timestamp y evidencia before/after.

### Fase A — baseline local congelado

1. Identificar commit, migraciones, Edge Function, frontend y pruebas exactas.
2. Ejecutar Docker/PG17 limpio y validar H3-001, H3-002, H3-003 y H3-004 local.
3. Validar TypeScript, lint, build, tests focalizados, credential scan y
   compatibilidad legacy.
4. Registrar hashes de SQL y artefactos.

Salida: `LOCAL_BASELINE_PASS` o retorno a corrección local. No se promueve un
baseline con errores ni con paths de prueba no reproducibles.

### Fase B — preflight remoto read-only

Para cada ambiente se captura antes de cualquier write:

- migraciones registradas;
- tablas, columnas, tipos, constraints e índices;
- RLS, policies y grants;
- firmas de RPC y funciones `SECURITY DEFINER`;
- Edge version, hash y `verify_jwt`;
- hostname, SHA y artefacto Pages;
- advisories y estado de datos de prueba.

La comparación se hace contra el baseline Pro y el commit local congelado. Un
drift no explicado detiene la iteración y obliga a volver a análisis local.

Cada ficha de evidencia debe contener, como campos obligatorios, `ambiente`,
`project_ref`, `branch/commit/artefacto`, `timestamp UTC`, `prueba ejecutada`,
`resultado` (`PASS`/`FAIL`/`BLOCKED`) y `evidencia sanitizada`. Si falta uno de
estos campos, el resultado de la ficha es `BLOCKED`, aunque la consulta técnica
haya respondido correctamente.

Antes de cualquier DDL se debe producir una tabla de delta exacto por ambiente:

1. comparar cada archivo de `db/migrations/` candidato con las migraciones
   registradas y su contenido efectivo en Free y Pro;
2. inspeccionar tablas, columnas, tipos, defaults, constraints, índices, RLS,
   policies, RPCs, firmas, `SECURITY DEFINER`, `search_path` y grants;
3. clasificar cada diferencia como `ya existe`, `delta requerido`, `drift no
   explicado` o `fuera de alcance`;
4. excluir todo objeto ya aplicado y todo delta no demostrado;
5. validar el delta exacto en Docker/PG17 limpio y registrar sus hashes.

Un delta no puede inferirse solo por la ausencia de una fila en migrations ni
por la presencia de SQL local. Un `drift no explicado` o un delta fuera de
alcance detiene la promoción y devuelve el ciclo a análisis local.

### Fase C — promoción DB

1. Free: no repetir migraciones registradas; aplicar solo deltas demostrados.
2. Pro: aplicar el conjunto H3 aprobado contra el baseline Pro.
3. Capturar metadata after-apply en el mismo ambiente.
4. Ejecutar smoke read-only y regresión H2/A6/A13.
5. Comparar Free/Pro con el contrato H3.

Fallo de SQL, metadata, grants, RLS o convergencia: `FAIL`; se detiene Edge y
Auth, se corrige localmente, se valida PG17 y se solicita JIT adicional si el
DDL cambia.

La promoción DB requiere dos paquetes de autorización independientes: `Free DDL`
para el project ref `aqrldlmlszjtgpqiegaa` y `Pro DDL` para el project ref
`xwhtiqmboljkshrtviyw`. Ninguno autoriza al otro, ni autoriza Auth, Edge, Pages,
cleanup, rollback o promoción protegida. La autorización debe referenciar el
delta, el hash SQL, el ambiente, la ventana y el rollback previsto. Si el SQL
cambia después de la autorización, la autorización anterior deja de aplicar.

El cierre H3-001 exige metadata after-apply del ambiente modificado, smoke
read-only y comparación Free/Pro contra el baseline aprobado. La mera fila de
migration, un check verde del proveedor o una respuesta HTTP no es suficiente.

### Fase D — promoción Edge

1. Desplegar `admin-invite` solo al ambiente autorizado.
2. Verificar hash remoto y `verify_jwt=true`.
3. Ejecutar smoke sin auth, JWT inválido y sesión válida.
4. Revisar logs sin secretos ni PII.

Fallo: retorno a local, corrección del componente Edge, validación de contrato,
nuevo hash y nueva autorización de deploy. No se ejecuta UAT de onboarding con
Edge no verificado.

El paquete de evidencia Edge debe asociar el hash remoto con el artefacto y
commit evaluados, el project ref, `verify_jwt=true`, el hostname del ambiente,
las respuestas sanitizadas de anónimo/JWT inválido/sesión válida y los logs sin
secretos ni PII. Un `404`, hostname cruzado, hash distinto o `verify_jwt=false`
es `FAIL` y detiene H3-002/H3-003.

### Fase E — H3-002 remoto

Ejecutar por ambiente y con datos de prueba autorizados:

- admin crea invitación;
- entrega de correo;
- callback/PKCE;
- aceptación única;
- password setup;
- reconciliación Auth/DB;
- onboarding y acceso privado;
- expiración, revocación, resend/supersede y replay;
- invitación ajena, usuario existente, sesión inválida e inactiva.

Solo se almacenan resultados sanitizados, request IDs y timestamps. No se
persisten passwords, JWT, refresh tokens ni URLs con tokens.

Fallo: clasificar causa como DB, Edge, Auth, callback o frontend; corregir en
local; repetir Docker; promover el componente mínimo; repetir el caso remoto y
la reconciliación completa.

### Fase F — H3-003 remoto

Validar admin, user, inactivo y anónimo para permisos positivos y negativos:
ownership, locking, edición, aprobación, gestión de miembros, protección del
último admin, membresía inactiva y acceso público. Verificar auditoría
append-only para cada mutación y ausencia de secretos.

Cualquier bypass, mutación sin auditoría o inconsistencia Auth/DB devuelve el
ciclo a local.

### Fase G — H3-004 remoto

Validar en orden:

1. `expand`: objetos nuevos instalados sin retirar legacy.
2. `compatibilidad`: versión anterior y nueva conviven.
3. `deploy`: DB, Edge, Pages, hostname, SHA y Access corresponden al ambiente.
4. `contract`: retirar legacy solo después de estabilidad y aprobación.
5. `rollback`: restaurar artefacto y comportamiento anterior de forma reproducible.
6. `cleanup`: retirar únicamente datos temporales autorizados.

El check verde de Pages/Edge no sustituye el smoke funcional remoto.

Para Pages se debe verificar el hostname esperado del ambiente, commit/SHA,
artefacto servido, rutas admin, callback, restricción pública y Access. El
hostname productivo no sirve como evidencia de Development o Certification.
`deploy` solo pasa cuando DB, Edge, Pages y configuración de acceso pertenecen
al mismo ambiente y al mismo candidato.

`contract` y `cleanup` son pasos posteriores a estabilidad demostrada y requieren
autorizaciones separadas. `rollback` se prueba con un procedimiento reproducible
por ambiente, restaurando el artefacto/configuración anterior y verificando login
legacy, MFA/`aal2` compatible, acceso público y ausencia de pérdida de datos.
Una prueba de rollback no autoriza cleanup ni una nueva promoción.

### Registro obligatorio por iteración

```text
Iteración:
Ambiente:
Project ref:
Componente:
Branch/commit/artefacto/hash:
Timestamp UTC:
Hallazgo:
Causa:
Corrección local:
Validación local:
Promoción autorizada:
Prueba remota:
Resultado: PASS | FAIL | BLOCKED
Evidencia:
Riesgo residual:
Siguiente acción:
```

## Paquetes JIT que deben solicitarse por separado

Ninguno está concedido por este documento. Antes de ejecutar el paso
correspondiente se debe solicitar explícitamente:

| Paquete | Alcance | No autoriza |
|---|---|---|
| Free DDL | Solo delta DB demostrado en `aqrldlmlszjtgpqiegaa` | Pro, Auth, Edge, Pages, cleanup, rollback o promoción |
| Pro DDL | Solo delta DB demostrado en `xwhtiqmboljkshrtviyw` | Free, Auth, Edge, Pages, cleanup, rollback o promoción |
| Auth/test data/correo | Cuentas, invitaciones, correo y cleanup de datos de prueba del ambiente indicado | DDL, Edge, Pages, producción o promoción |
| Edge deploy | `admin-invite` al ambiente y project ref indicados | Pages, Auth, cleanup, rollback o promoción |
| Pages/deploy | Artefacto y hostname del ambiente indicado | DB, Edge, Auth, cleanup, rollback o promoción |
| Cleanup | Solo datos temporales enumerados, con reconciliación previa | DDL, rollback o promoción |
| Rollback | Drill reversible del ambiente y artefacto indicados | Cleanup, nuevo deploy o promoción |
| Promoción protegida | PR/merge/promoción de la rama y destino indicados | Cualquier write operativo no enumerado |

Una autorización ambigua, vencida, sin project ref/artefacto o que mezcle clases
se trata como `BLOCKED` y no se ejecuta.

### Gate final de GO

Se declara `GO_REQUEST_CERTIFICATION` únicamente si Free y Pro convergen con el
baseline aprobado, H3-001/H3-002/H3-003/H3-004 son `PASS` en el ambiente
evaluado, rollback es reproducible, cleanup está controlado, no existe drift ni
hallazgo HIGH/CRITICAL abierto, no queda `BLOCKED` crítico y todas las evidencias
son remotas del ambiente correspondiente. Las pruebas locales sirven como
precondición y regresión, nunca como sustituto de evidencia remota.

El estado actual permanece `NO-GO`: H3-001 está en `FAIL` por drift Pro;
H3-002, H3-003 y H3-004 están en `BLOCKED`; y las validaciones locales
`LOCAL-VAL-001`/`LOCAL-VAL-002` siguen pendientes de resolver en Docker. El
próximo paso permitido es preparar el paquete de delta y la solicitud JIT; no
es aplicar migraciones ni iniciar UAT.

## Iteración de desarrollo 4 — hardening local cerrado

La corrección local del ciclo 4 añade y valida los dos archivos de hardening que
estaban registrados en Free pero ausentes del checkout principal:

- `db/migrations/20260924_h3_onboarding_rbac_hardening.sql`
  SHA-256 `E466BF1F7968D71CE715724779CC4BD37818F6462021724D01AD48A9BFB1A857`.
- `db/migrations/20260924_h3_onboarding_rbac_hardening_fix.sql`
  SHA-256 `9A5C5D46BCA6B4DEC438BC6AE63036641423FEE95B73E188237EF8BA230B2978`.

El delta queda validado en PG17 limpio con el harness
`tests/sql/h3_onboarding_rbac_hardening_harness.sql`, cuyo resultado fue
`h3_onboarding_rbac_hardening_harness_ok`. También se mantiene
`h3_pg17_harness_ok`. Esto corrige el bloqueador local de hardening no
reproducible; no cierra el drift remoto ni autoriza DDL.

## Evidencia de auditoría

- `.context/evidencia/h3_remote_validation_readonly_2026-09-24.md`
- `.context/evidencia/h3req1_remediation_baseline_2026-09-23.md`
- `.context/evidencia/h3req1_remediation_report_2026-09-23.md`
- `.context/evidencia/h3req1_remote_validation_readonly_2026-09-24_cycle2.md`

## Hallazgos del ciclo read-only 2 y revalidación 3

| ID | Hallazgo | Causa | Corrección planificada | Prueba de cierre | Resultado actual |
|---|---|---|---|---|---|
| DRIFT-H3-001 | Free registra 03A/03B y hardening 20260924; Pro no registra H3 ni tiene tablas/RPCs | Convergencia incompleta | Comparar SQL aprobado contra baseline Pro y solicitar JIT DDL Pro; no repetir migraciones Free | `list_migrations` + metadata SQL antes/después | `FAIL`, bloquea Certification |
| ENV-H3-002 | RPCs Free no acreditan invitation/onboarding runtime | No se ejecutó Auth, correo, PKCE ni reconciliación Auth/DB | UAT remota controlada después de cerrar DB y Edge | flujo positivo/negativo H3-002 | `BLOCKED` |
| ENV-H3-003 | Metadata Free no prueba autorización efectiva ni Pro | No hay UAT autenticada | Matriz admin/user/inactivo/anónimo, último admin, locking y auditoría | requests autenticados y auditoría | `BLOCKED` |
| DEPLOY-H3-004 | No hay evidencia nueva de deploy, contract/cleanup ni rollback | Requieren JIT separado; preview anterior devolvía 404 | Verificar artefacto, SHA, hostname y rollback | smoke por ambiente + rollback | `BLOCKED` |
| LOCAL-VAL-001 | pytest no pudo ejecutarse: dependencia ausente en Docker | Imagen sin pytest | Resolver en ciclo local futuro; sin cambios de código ahora | repetir suite dentro de Docker | `BLOCKED` |
| LOCAL-VAL-002 | Path `h3_pg17_harness_local.sql` no existe en contenedor | Ruta no coincide con montaje | Verificar ruta real en ciclo local futuro | ejecutar harness existente | `BLOCKED` |

### Cierre de hallazgos de validación local en el ciclo 3

| ID | Prueba de revalidación | Resultado | Evidencia / impacto |
|---|---|---|---|
| LOCAL-VAL-001 | Harness PG17 limpio ejecutado desde `/tmp/h3-run` con rutas SQL reproducibles | `PASS` | `h3_pg17_harness_ok` y `h3_invitation_onboarding_harness_ok`; el bloqueo anterior era de dependencia/ejecutor de pytest, no del harness SQL |
| LOCAL-VAL-002 | Verificación y ejecución de `tests/sql/h3_pg17_harness_local.sql`/harness canónico con montaje reproducible | `PASS` | La ruta existe en `/app/tests/sql`; la corrida canónica limpia se ejecutó en DB aislada `h3_cycle3_clean` |
| LOCAL-VAL-003 | `pytest` focalizado | `PASS` | Dependencias pytest reproducibles añadidas a `requirements-pipeline.txt`; 60 tests focalizados PASS en Docker |
| LOCAL-VAL-004 | UAT mock contra dev server `3000` | `FAIL` inicial / no bloquea baseline final | El servidor dev fue descartado para UAT por manifiestos/HMR inestables; la ejecución final contra build estático y perímetro local `3002` fue 9/9 `PASS` |
| LOCAL-VAL-005 | Hardening 20260924 ausente del checkout principal | `PASS` | Se recuperaron ambos SQL desde el worktree de remediación, se verificaron hashes y se ejecutó el harness RBAC/onboarding en PG17 limpio |
| LOCAL-VAL-006 | Bypass legacy `admin_create_member` podía crear ready/active sin onboarding | `PASS` local | Se añadió `20260925_h3_legacy_member_creation_guard.sql`; la ruta legacy queda como shim rechazado y el harness verifica que no muta membresía |
| LOCAL-VAL-007 | Harness ACL/RLS no comprobaba privilegios directos de roles PostgREST | `PASS` local | El harness canónico ahora verifica que `authenticated` no tenga INSERT/UPDATE/DELETE administrativo y `anon` no tenga SELECT administrativo |
| LOCAL-VAL-008 | UI legacy no exponía account/invitation status | `PASS` local | Se añadió el lector aditivo `admin_list_members_onboarding`; la UI conserva el RPC legacy y ahora consume el contrato enriquecido |

### Cierre de reauditoría de seguridad — ciclo 7

| Hallazgo auditoría | Resultado | Corrección / evidencia |
|---|---|---|
| Mock reader leía tablas directamente | `PASS` | `mock-server/server.js` ahora llama `admin_list_members_onboarding()` dentro de `withIdentity()` |
| Harness usaba fixture inconsistente | `PASS` | Usa `30000000-0000-0000-0000-000000000004`, user `ready` real del seed canónico |
| Legacy `admin_create_member` podía bypass onboarding | `PASS` | Guard 20260925 conserva firma, rechaza creación y no muta `admin_members` |
| Lock pytest/pygments | `PASS` | Un único bloque hash de Pygments y dependencias pytest reproducibles |
| Pro sin baseline H3 | `FAIL` remoto | Sin autorización JIT no se toca; continúa bloqueando Certification |

`LOCAL-VAL-001` y `LOCAL-VAL-002` dejan de ser bloqueadores del baseline local.
`LOCAL-VAL-003` queda cerrado como `PASS` local. La evidencia remota continúa
separada y no mejora por estas pruebas.
`LOCAL-VAL-005` queda cerrado como `PASS` local; la promoción remota sigue
detenida hasta autorización JIT y captura after-apply.
`LOCAL-VAL-006` y `LOCAL-VAL-007` quedan cerrados como `PASS` local. El RPC
legacy no se elimina para preservar compatibilidad de ruta, pero no puede
crear membresías; el único flujo de onboarding válido es `admin-invite`.
`LOCAL-VAL-008` y los hallazgos de la reauditoría de seguridad quedan cerrados
como `PASS` local. El resultado contractual remoto no cambia.

La discrepancia sobre 03A/03B queda reconciliada por timestamp: ciclo 1 acreditó
ausencia y ciclo 2 acredita cambio posterior en Free. No es drift cerrado porque
Pro continúa vacío y no hay evidencia runtime.

## Matriz de remediación requerida

La siguiente matriz agrega causa, componentes, validación, riesgo y evidencia
esperada. Todas las acciones remotas permanecen bloqueadas hasta recibir la
aprobación JIT correspondiente.

| Hallazgo | Causa demostrada | Archivo/componente afectado | Acción requerida | Validación necesaria | Riesgo | Evidencia esperada |
|---|---|---|---|---|---|---|
| H3-001 | Free registra 15 migraciones H3 relacionadas; Pro no registra ninguna de H3 y no tiene tablas de membresías/invitaciones/auditoría | `db/migrations/20260828`–`20260925`; hardening y guard legacy ya recuperados localmente; Supabase Free/Pro; `.context/evidencia/` | No repetir Free. Reconciliar hashes contra Free, preservar migraciones locales y solicitar JIT DDL Free solo si aparece delta exacto. Solicitar JIT DDL Pro separado para el baseline H3 aprobado | `list_migrations`, metadata de tablas/RPC/constraints/RLS, grants, firmas, `SECURITY DEFINER/search_path` y hashes por ambiente | Drift entre ambientes, aplicación parcial o incompatibilidad con baseline Pro | Snapshot before/after, contenido/hashes SQL reconciliados, objetos H3 y smoke read-only del ambiente evaluado |
| H3-002 | `admin_invitations` y RPCs de invitación/onboarding están ausentes en Free y Pro | `supabase/functions/admin-invite/index.ts`; RPCs `admin_invitation_*`, `admin_accept_current_invitation`, `admin_complete_password_setup`, `admin_get_onboarding_status` | Tras contrato DB validado, ejecutar UAT real controlada admin → invitación → aceptación → password → onboarding; no exponer tokens ni passwords | Auth/PKCE, correo de prueba autorizado, identidad caller, TTL, aceptación, replay, reconciliación Auth/DB y RBAC | Crear datos Auth o invitaciones no reconciliables; envío real accidental | Logs sanitizados, request IDs, resultado Auth/DB reconciliado, evidencia de no exposición de secretos |
| H3-003 | Free solo tiene RBAC/editorial H3 parcial y Pro no tiene baseline H3 verificable | Supabase Free/Pro; baseline Pro de schema; `db/migrations/20260918`–`20260921` | Comparar contra baseline Pro autoritativo; obtener JIT Pro separado; aplicar solo deltas idempotentes aprobados y verificar convergencia | Inventario de migraciones, columnas, constraints, funciones, grants y RLS en ambos ambientes | Alterar producción fuera de baseline o promover SQL incompatible | Matriz Free/Pro antes-después, aprobación JIT referenciada y consulta de contrato por ambiente |
| H3-004 | No existe evidencia de deploy, contract/cleanup ni rollback remoto; local expand/compatibilidad no sustituye deploy | Edge `admin-invite`; frontend admin; Supabase/Auth; Certification/Pro | Documentar y ejecutar por separado `expand → compatibilidad → deploy → contract`; preparar rollback reversible antes de cualquier deploy; cleanup solo con aprobación | Hash/version Edge, `verify_jwt=true`, smoke por ambiente, UAT Certification, contract/cleanup y rollback reproducible | Degradación del login legacy, pérdida de compatibilidad o rollback incompleto | Evidencia de cada fase, manifest/hash, logs sanitizados, decisión contract, rollback drill y estado post-cleanup |

## Orden de ejecución condicionado

1. **R1 — Baseline read-only:** ya completado; conservar el baseline y no
   inferir aplicación desde la presencia de SQL local.
2. **R2 — Free DB:** detenido hasta JIT DDL Free. No ejecutar Auth UAT ni
   writers antes de validar tablas, RPCs, constraints, grants y RLS.
3. **R3 — Pro DB:** detenido hasta JIT DDL Pro y revisión contra baseline Pro.
   Una autorización Free no cubre Pro.
4. **R4 — Edge:** detenido hasta JIT Edge deploy por ambiente. `verify_jwt`
   debe permanecer habilitado y el hash remoto debe corresponder al artefacto
   aprobado.
5. **R5 — UAT real:** detenido hasta R2–R4; requiere datos de prueba y correo
   expresamente autorizados, con limpieza y reconciliación documentadas.
6. **R6 — Contract/rollback:** detenido hasta tener evidencia deploy, smoke,
   contract, cleanup autorizado y rollback reproducible sin acciones
   destructivas.

## Gate de continuación

El siguiente ciclo solo puede iniciar implementación local con el prompt humano
`continua`. Las operaciones remotas requieren además aprobaciones JIT concretas:

- Free DDL/migraciones.
- Pro DDL/migraciones.
- Auth writes y datos de invitación/correo de prueba.
- Edge deploy `admin-invite` por ambiente.
- Cleanup, rollback remoto y cualquier promoción protegida.

Hasta entonces el estado es `NO-GO`; no se declara `READY FOR VALIDATION` ni GO.
- `.context/hitos/h3req1_closure_review_final_2026-09-23.md`
