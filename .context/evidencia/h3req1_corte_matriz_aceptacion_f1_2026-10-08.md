# H3REQ1 — matriz de aceptación y bloqueo F1

Fecha: 2026-10-08. Sesión: `01a11de1-1403-7133-b10e-6fd9f8543905`.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`,
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Ficha de impacto

- **Objetivo/criterio cliente:** cerrar la validación local de cuatro ajustes ya implementados
  y remover el bloqueo de Docker sin diagnosticar a ciegas; conservar BFF/HttpOnly, roles,
  MFA, gateway, cuotas y compatibilidad legacy.
- **Rutas/dominios:** Admin editor y encabezado (`web/src/app/admin/`); RPC, disponibilidad,
  auditoría y publicación (`db/migrations/20261001_h3_course_editorial_audit_availability.sql`);
  runners existentes `tests/sql/h3_pg17_harness.sql` y `tests/h3_local_uat.mjs`; lectura
  Docker Desktop WSL fijada a un ID de contenedor y campos F1; patch independiente de CI V3.
- **Contrato K / tipo de cambio:** no se modificó lógica funcional, SQL de producto, BFF,
  gateway, cuota ni workflow remoto. Se fortaleció cobertura en runners existentes y se
  preparó un helper diagnóstico acotado para el error observado. Patch CI V3 permanece
  separado y sin aplicar.
- **Consumidores:** edición y recuperación tras conflicto → BFF firmado → PostgREST/RPC y
  estado editorial; auditoría → RPC Admin/MFA con actor/fecha/antes/después; evidencia de
  disponibilidad → gate de publicación y proyección pública legacy; email → sesión Auth por
  BFF y encabezado con role gate previo. Los checks CI protegen workflows/scripts y no deben
  publicar producto por Pages.
- **Preservación:** los checkouts, WIP, imágenes/containers, secretos, migraciones y evidencia
  histórica se conservan. El checkout original `/home/romel/src/studiamatch` no se editó.
  La cuenta Auth existente no se reinvita ni se resetea. No se altera BFF/HttpOnly ni se
  vuelve a guardar token Auth en storage accesible desde JavaScript.
- **Pruebas concretas:** se amplían dos runners ya existentes. `tests/sql/h3_pg17_harness.sql`
  añade aserciones sobre procedencia, audit actor/fecha/diff, falta de evidencia y rechazo de
  publicación sin disponibilidad. `tests/h3_local_uat.mjs` conserva 48 casos/144 ejecuciones
  y 0 retries; amplía el header Admin/User y complementa la comprobación del conflicto con dos
  saves RPC simultáneos con la misma versión, verificación de ganador/conflicto y restauración
  del valor de pipeline. Conserva la aserción estática del contrato visual de recuperación.
  No se ejecutaron todavía.
- **Evidencia preservable/renovable:** se conservan como históricos los 122 tests Python,
  TypeScript/lint/static smoke y PG17 del ciclo editorial 2026-10-01; los 11 tests de
  encabezado; UAT BFF r2 (60 checks/10 casos de cuota); 144/144 capturas y onboarding 10/10
  del candidato anterior; y C03 SQL v3 41/41. La modificación del harness obliga a ejecutar
  el candidato actual para los casos nuevos. Los cambios BFF/workflow explican C02 70/72;
  validar esos deltas en r9, no repetir SQL/wire cuyos inputs sigan idénticos.
- **Transición/rollback:** expand/compatibilidad/deploy/contract no aplica a estas aserciones
  de test ni al lector diagnóstico; no hay despliegue. Rollback local limitado a los cambios
  de los runners/helper nuevo y esta evidencia. Los deltas funcionales siguen la estrategia
  ya atestada; este corte no contrae compatibilidad ni migra datos.
- **Permisos/gates:** pruebas y comandos de desarrollo pendientes de ejecución en Docker.
  La ejecución de F1 requiere el JIT separado vinculado abajo. El bootstrap CI requiere
  autorización humana separada para publicación/revisión/settings. Ningún archivo/hash pide
  permiso separado dentro de una invocación aprobada.
- **Pilares/desconocidos:** no se afirma PASS de runtime, seguridad global, escalabilidad ni
  rendimiento. Se reconoció un marcador de error de template, pero no se conoce si ocurrió en
  parseo o evaluación ni qué campo falló. No se presume que F1 falte o que el Engine esté mal.
  Preview branch control y merge queue por rama continúan pendientes para un rollout seguro de CI.
- **Gate y stop:** el JIT F1 fue aprobado y consumido; sus tres líneas no fueron `OK`, así que
  G03/G04 siguen abiertos y r9 no inicia. Una invocación futura requiere corrección y prueba
  mínima demostrables, seguida de un JIT separado.

## Docker: intento histórico y resultado del JIT consumido

El intento anterior usó el archivo
[output-capture JIT](../operaciones/jit_h3req1_docker_desktop_wsl_output_capture_once_2026-10-08.md)
con SHA-256 `bbaa2242bf026f252864b4e476a60e9de2a8e327c0456d2b343b612402c61c92`.
La salida `DOCKER_READ_FAILED` se reportó antes de la aprobación del JIT. Se conserva como
**evento histórico no autorizado**, no como resultado actual ni cierre de gate. Ese JIT no se
repite.

Predicado que falló: `docker inspect --type container --format <F1 allowlist> <ID F1>`
terminó en código no cero bajo el helper. La salida histórica del runner era
`phase=f1-container-read|error_code=DOCKER_READ_FAILED`, y su exit era 1; no expuso el exit
numérico del CLI. El resultado actual, de la invocación aprobada posterior, se detalla abajo.

La corrección diagnóstica preparada captura stderr solo en memoria y limita su tamaño a 4096
bytes; clasifica en códigos cerrados (`CONTAINER_NOT_FOUND`, `DOCKER_ACCESS_DENIED`,
`DOCKER_ENGINE_UNAVAILABLE`, `INSPECT_TEMPLATE_ERROR` o `DOCKER_READ_FAILED`) y no imprime,
persiste ni incorpora texto crudo. Sintéticos preparados cubren esas categorías, fallback y
salida sanitizada. El runner vuelve a fijar endpoint/Engine Linux, lee imagen F1 y realiza un
solo inspect del mismo ID. No consulta `/proc`, no necesita root y no cambia ni instala Docker.

El JIT de clasificación para esta fase fue
[JIT de clasificación F1](../operaciones/jit_h3req1_docker_desktop_wsl_f1_error_classification_once_2026-10-08.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-READ-ERROR-CLASSIFICATION-ONCE-20261008-V1`, SHA-256
`ce424f43901752cab76d9bcad88ceca05eb94a65790e4750a3b5f71f4b417395`. Estado: aprobado para
una invocación y ejecutado una vez por `romel` en terminal interactiva Ubuntu WSL, sin `sudo`.
Resultado sanitizado:

```text
phase=desktop-wsl-endpoint-attested|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=INSPECT_TEMPLATE_ERROR
```

El runner de diagnóstico termina en exit 1 por esta rama; el exit numérico del CLI `docker
inspect` no fue emitido. El predicado fallido es la lectura `docker inspect --type container
--format <F1 allowlist> <ID>`: el CLI devolvió non-zero y el clasificador reconoció un marcador
de error de template. El texto crudo fue descartado, así que el código no separa parseo de
evaluación de campo y no identifica el token/atributo concreto. Revisión estática del formato
pinneado no muestra una corrección demostrada; no se modifica el template por conjetura. F1
no queda acreditado y los tres `OK` requeridos no se cumplieron. Esta invocación está consumida:
no repetir ni cambiar Docker; r9 y las etapas dependientes siguen detenidas.

**Corrección diagnóstica preparada:** el clasificador V1 colapsaba parseo y evaluación en
`INSPECT_TEMPLATE_ERROR`, brecha confirmada por la salida actual y el código. Se añadió un
helper V2 que separa `INSPECT_TEMPLATE_PARSE_ERROR`,
`INSPECT_TEMPLATE_EVALUATION_ERROR` y marcador ambiguo `INSPECT_TEMPLATE_ERROR`; prioriza el
marcador `executing` porque Docker CLI puede anteponer “Template parsing error” también a una
fallida de ejecución ([caso en el repositorio oficial docker/cli](https://github.com/docker/cli/issues/3727)).
El helper V2 original (`3b5f7c6dd00ba6b690fcaadbc0c018f7d2e0dc11079ac0991cd0ffd06926f706`),
runner combinado original (`385f94732d8f93420533284cd1f4ceee36d82b742ba7ab519c3af0749c6c88df`)
y pruebas sintéticas originales (`48b6944cb741115597319c7097890270f837eef4e3c9a043bd94f16d30f9bd2e`)
pertenecen al [JIT V2 consumido](../operaciones/jit_h3req1_docker_desktop_wsl_f1_classifier_v2_and_r9_once_2026-10-08.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-AND-R9-ONCE-20261008-V1`, SHA-256
`c2f9414cea67402af76727b3c240982d1c264252569ab94aea9dedc47c687a66`. Su salida endpoint OK /
synthetic-tests FAIL y stop previo a F1/r9 se conserva en el
[resultado del 2026-10-09](h3req1_c03_f1_classifier_v2_synthetic_failure_2026-10-09.md).
Ninguna prueba sintética acredita F1.

### Addendum de corrección del fixture y nueva autorización pendiente — 2026-10-09

La revisión estática localizó que el test de `main()` dejaba activa la orquestación
`run_synthetic_tests()`, intentando lanzar Docker anidado dentro del contenedor pytest sin socket.
El fixture ahora sustituye solo esa llamada por no-op; el runner exterior sigue ejecutando las
pruebas V2 reales en el contenedor efímero fijado. La salida cruda del primer pytest se suprimió,
por lo que la revisión no prueba que este fuera el único test fallido. No se ejecutó la
corrección.

Pins corregidos: helper `018f179ffca763b0c328c6ee973f0cbc6ef3370bb5895860970e416c2a5a6408`,
pruebas `67ac4da3ab79dbce7b6a09d1b34597c2f070ba5abb89c72058b7b74cd8930487`, runner combinado
`3212b44753d26bf5f52da1835adc88d872e7e63fa630549a9bd00683ebd8c362`. El nuevo
[JIT corregido](../operaciones/jit_h3req1_docker_desktop_wsl_f1_classifier_v2_fix_and_r9_once_2026-10-09.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-FIX-AND-R9-ONCE-20261009-V1`, SHA-256
`1cb4ad0dbf3f3928c88a62441c2806c8eff2358ff3970c1f07d5a787d8fd29b5`, espera aprobación. Si
aprueba, agrupa pruebas sintéticas corregidas, una lectura F1 y r9 solo bajo los predicados
exactos; falla sin retry. La primera invocación no se repite y no se cambia formato F1 por
conjetura.

## Matriz de aceptación de los cuatro ajustes

| Ajuste e inputs | Pruebas anteriores preservables | Cobertura afectada o faltante demostrada | Resultado actual | Siguiente acción ejecutable |
|---|---|---|---|---|
| **Edición Admin y procedencia.** `admin_update_course`, versión, allowlist de 13 campos, `manual_overrides`, `pipeline_values`, `current_values`, `field_sources`; rol Admin/User. | PG17 editorial 2026-10-01; contratos editoriales; UAT H3-CA4.2; 122 tests Python y checks TS/lint históricos. | El harness verificaba valor efectivo/reset y conflicto secuencial, pero no comparaba explícitamente `pipeline_values`/`field_sources` antes/después ni lanzaba saves simultáneos. El caso UAT de conflicto solo buscaba strings del componente. | No se halló defecto de implementación. Se añadieron aserciones de origen/pipeline al harness y dos RPC saves con misma versión al caso UAT existente; no ejecutados. | En PG17 comprobar ganador único, conflicto stale, valor manual persistido tras reload, origen/pipeline preservados y reset a valor fuente; UAT en los 3 viewports. |
| **Auditoría actor/fecha/antes/después.** Evento `update` y `availability_override` en `course_editorial_audit`, actor Auth, `created_at`, `old_values`, `new_values`; lectura Admin/MFA y append-only. | PG17 histórico audit paging/append-only; pruebas de permisos directos y lector paginado. | El harness contaba eventos y comprobaba `actor_label`, pero no asertaba por fila `actor_user_id`, timestamp, antes y después en edición/disponibilidad; la rama de limpiar override tampoco tenía aserción propia. | SQL de migración ya escribe esos campos; no se mostró un defecto. Se añadieron aserciones para una edición, limpieza del override y disponibilidad, incluida la transición antes/después de limpiar; sin ejecución. | Ejecutar PG17 y exigir evento exacto para update, limpieza de override y availability; confirmar fallo de escritura sin evento incompleto y preservar prueba de permisos/read-only. |
| **Disponibilidad con evidencia ≤90 días.** HTTPS, host fuente, fecha observada/validez, expiración, estado efectivo, cohort legacy y gate publicar. | PG17 conserva boundary inclusivo 90 días, +1 segundo rechazado, host ajeno, expiración, legacy y canary. Tests estáticos de contrato. | El harness ya probaba los extremos, pero no rechazaba explícitamente evidencia faltante sin mutación ni intentaba publicar un curso completo con disponibilidad `unknown`. | No se encontró defecto en el RPC. Se añadieron esas dos comprobaciones al harness, además de auditoría por evento; no ejecutadas. | Ejecutar PG17 y comprobar rechazo sin incremento de versión/audit, no publicación sin evidencia, y compatibilidad legacy/expiración intactas. |
| **Correo autenticado en encabezado.** Email Auth sintético, fallback, orden de autorización, rol/Admin/User y sesión HttpOnly. | 11 contratos enfocados, TS/lint histórico; UAT anterior cubría login/MFA/roles/logout y no token JS; código ya contiene fallback `Usuario autenticado`. | La UAT previa no afirmaba el email visible bajo sesión Admin/User en los tres tamaños; no se registrará correo real. | Se amplió el caso existente de Admin y User con `admin@local.test`/`user@local.test`, sin agregar casos ni alterar 48×3. No ejecutado. | UAT 144 sin retries; revalidar sesión HttpOnly, MFA, invitación, roles, publicación y fallback estático en inputs del candidato actual. |

Los dos cambios del runner conservan 48 casos × 3 viewports = 144 ejecuciones/capturas y
`retries: 0`. El onboarding 10/10 va en escenario separado de la cuenta existente. La UAT
completa, sus capturas, invitación y regresiones no se sustituyen por la matriz ni por sus
aserciones de preparación.

## CI independiente y no regresión de BFF

El patch V3 de bootstrap conserva cuatro rutas, base `4eb4d877a50b012bb630a129bd0c74482c33be9`
y SHA-256 `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`. Sigue sin
aplicar/publicar. La revisión estática independiente quedó `hold_for_evidence`; pytest,
actionlint, Docker, emisión real del check y asociación al SHA no están acreditados. GitHub
requiere actualmente `security-audit`, no el nuevo workflow. Cloudflare Pages Production está
en `main`, con auto-deploy y watch `*`; no abrir/publicar/mergear el patch ni cambiar rules
sin instrucción separada y protección verificable contra deploy incidental.

La captura acreditada de Branches no se repite. Quedan exactos modo Preview branch control,
merge queue por rama, check real y reevaluación al avanzar la rama base con head estable. No
se solicita otra captura por este corte. Se mantienen las reglas actuales de PR, aprobación,
stale review, up-to-date y `security-audit` como único check requerido.

La documentación de Cloudflare Pages confirma que el prefijo `[CF-Pages-Skip]` en el mensaje
del commit omite el deployment y que los builds omitidos no muestran check run. Es una
mitigación documentada, no probada todavía en este PR/repositorio ni con su squash; la falta de
check Pages no se contará como PASS. La comprobación efectiva debe ocurrir bajo autorización
de publicación antes de integrar el bootstrap. [Cloudflare Pages GitHub integration](https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/).

El paquete r9 fijado no incluye `tests/h3_local_uat.mjs` ni
`tests/sql/h3_pg17_harness.sql`; estas ampliaciones no invalidan sus hashes de entrada. No se
modificó el paquete ni se ejecutó su runner antes de la autorización y salida Docker requeridas.

La evaluación complementaria read-only del patch CI exacto (`4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`)
queda `hold_for_evidence`: los controles de fuente son compatibles con el límite de confianza,
pero no hay pytest/actionlint ni check remoto ejecutados. GitHub exige que el workflow de
`pull_request_target` exista en la rama default para ejecutarse; por ello, la primera promoción
por `desarrollo -> certificacion -> main` queda en las reglas actuales hasta que el bootstrap
llegue a `main`. Esto es una ventana de instalación con PR, aprobación y `security-audit`, no
evidencia de PWI efectivo. Quedan pendientes la política/run real, reevaluación con base estable,
merge queue y evitar un deployment Pages del patch.
[GitHub — `pull_request_target`](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

El BFF/HttpOnly y sus límites son parte del candidato. El informe de sessionStorage es
histórico; este corte no afirma ataque ni HIGH actual y no reintroduce tokens JS. Se renuevan
las regresiones de login, renovación/logout, MFA, roles, invitación y publicación porque el
WIP actual alteró BFF/workflows; las pruebas C02 que no cubren esos deltas se conservan como
parciales, no como 72/72.

## Gates y resultados separados

| Gate | Estado | Evidencia/parciales sin sumar |
|---|---:|---|
| G01 | 10/10 | Cierre previo acreditado. |
| G02 | 10/10 | C03 SQL v3 conserva 41/41 inputs; integración real sigue pendiente. |
| G03 | 0/10 | Pytest focal r4 20/20, scanner r7 PASS y otros parciales previos; sintéticos V2 fallaron y r9 no se ejecutó. |
| G04 | 0/10 | Lectura F1 anterior `INSPECT_TEMPLATE_ERROR`; el JIT V2 se detuvo antes de releer F1, sin cambio de Docker/template. |
| G05–G07 | 0/30 | Copia aislada, Pages/workerd healthz e integración Edge/PG17/PostgREST pendientes. |
| G08 | 0/10 | UAT BFF r2 60 checks/10 cuotas; cambios actuales no revalidados. |
| G09 | 0/10 | 144 ejecuciones actuales, onboarding 10/10 separado y aceptación/revisión pendientes. |
| G10 | 0/10 | Patch CI V3 preparado; emisión/enforcement/settings/review remotos pendientes. |
| **Total** | **20%** | No GO; no puntos por documentación, hash, revisión estática o implementación. |

El candidato no está listo para `GO_LOCAL_PR` ni para `Development`. Tras completar los gates
locales y obtener el permiso separado de promoción, se identifica el artefacto real y se
ejecutan D01–D14. Certification/Production de producto quedan fuera.

## Addendum — preflight detenido por pin del runner — 2026-10-09

Se consumió una vez el JIT aprobado
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-FIX-AND-R9-ONCE-20261009-V1`, SHA-256
`1cb4ad0dbf3f3928c88a62441c2806c8eff2358ff3970c1f07d5a787d8fd29b5`. Salida sanitizada:

```text
phase=classifier-v2-r9-preflight|error_code=DIAGNOSTIC_RUNNER_HASH_MISMATCH
```

Exit 1. El preflight encontró que el pin interno del runner combinado (`1fe0…`) no coincidía
con el runner diagnóstico fijado en el JIT (`97b5…`). Se detuvo antes de endpoint, pruebas,
lectura F1 y r9. No se invocó Docker API. Solo se actualizó ese pin; el cambio local aún no
está validado en runtime.

El usuario informó además que `studiamatch-dev` tiene hashes de manifests fuente distintos de
la imagen staged. No se consultó ni reconstruyó; la discrepancia no se atribuye al error del
pin y la autorización consumida excluía ese contenedor.

La matriz de los cuatro ajustes permanece como estaba: los asertos nuevos de auditoría,
disponibilidad y email aún requieren sus runners; la edición Admin conserva la procedencia en
su código existente, sin defecto demostrado. El JIT F1 anterior sigue siendo
`INSPECT_TEMPLATE_ERROR`; este intento no llegó a F1. Se preparó un permiso agrupado nuevo en
[JIT pin corregido](../operaciones/jit_h3req1_docker_desktop_wsl_f1_classifier_v2_pin_corrected_and_r9_once_2026-10-09.md).

G01=10/10 y G02=10/10; G03–G10=0; total 20%, delta cero. Los parciales de r4, r7, C03 SQL v3,
UAT BFF r2, UAT histórico y onboarding histórico se conservan separados. No hay `GO_LOCAL_PR`,
no se ejecutó r9 y no se habilita Development.

## Addendum — synthetic V2 falló con clasificación insuficiente — 2026-10-09

Se aprobó y consumió una vez el JIT con pin corregido, SHA-256
`dbc58ec3dcc3ce7cacc83d84ec6689a16f1564ae40c0776607fba5e35371e79d`. Salida: endpoint
`OK`, sintéticos `SYNTHETIC_TESTS_FAILED`, exit 1. F1/r9 se detuvieron. La invocación no
conservó pytest raw y el helper mapeó cualquier error del contenedor/pytest/aserción al mismo
código; la causa interior no se conoce. La revisión estática no encontró un caso determinista
roto. No se repitió.

Se preparó un runner nuevo que verifica el digest local sin pull y devuelve códigos cerrados de
colección/framework/casos V2, preservando salida raw solo en memoria. La nueva invocación
agrupa diagnóstico, F1 y r9 condicional y necesita aprobación independiente:
[JIT diagnóstico sintético](../operaciones/jit_h3req1_docker_desktop_wsl_f1_classifier_v2_synthetic_diagnostic_and_r9_once_2026-10-09.md),
SHA-256 `708cb4210fb59df7f85d1f69c83f22007304b99a6414496ea0c9268d8bb32d26`.

Los cuatro ajustes conservan el resultado previo de la matriz: no hay defecto funcional
demostrado y los asertos añadidos siguen sin ejecutarse. El parcial endpoint no cierra G04 ni
G03; F1 mantiene su resultado previo `INSPECT_TEMPLATE_ERROR`. G01/G02=20/20; G03–G10=0/80;
total 20%, delta cero. Sin GO.

## Addendum — `main()` sintético falló; causa puntual aún desconocida — 2026-10-09

Se aprobó y consumió una vez el JIT de diagnóstico sintético V2, SHA-256
`708cb4210fb59df7f85d1f69c83f22007304b99a6414496ea0c9268d8bb32d26`. Salida: endpoint y
digest de imagen sintética `OK`; caso `main()` `V2_MAIN_SANITIZATION_FAILED`; exit 1. No se
alcanzaron F1 ni r9. No hubo pull/rebuild/cambio Docker ni acceso a `studiamatch-dev`.

La cobertura fallida es el caso sintético `test_v2_main_emits_only_sanitized_template_error`.
El código no distingue retorno, secuencia de fases, salida con marcador, excepción o
clasificador. Se instrumentaron tres aserciones con etiquetas constantes y un runner V3 que
emite códigos cerrados. Esa instrumentación no se ejecutó aún. El paquete completo está en
[JIT V3](../operaciones/jit_h3req1_docker_desktop_wsl_f1_classifier_v3_main_assertion_and_r9_once_2026-10-09.md),
SHA-256 `1aa957146fbe98b6bec2e04c9d9cbc67414cbb4a9dbe3af138d53b592f8af178`, pendiente de
aprobación exacta. La solicitud anterior con SHA `a7fe73ac…` quedó obsoleta y no se ejecutó:
la revisión encontró una ruta fija al entrypoint V2, ya corregida en el paquete actual.

| Ajuste | Resultado actual tras este ciclo | Siguiente predicado |
|---|---|---|
| Edición Admin y procedencia | Sin resultado nuevo; implementación no presenta defecto demostrado. Asserts nuevos aún sin ejecución. | PG17 ganador/conflicto, reload y origen preservado; UAT responsive. |
| Auditoría actor/fecha/antes/después | Sin resultado nuevo; aserciones ampliadas no ejecutadas. | Evento exacto por update, limpieza y disponibilidad; permisos y append-only. |
| Evidencia de disponibilidad ≤90 días | Sin resultado nuevo; RPC sin defecto demostrado; nuevas comprobaciones sin ejecutar. | Evidencia faltante no muta versión/audit; publicación rechazada; límites y legacy preservados. |
| Email Auth en encabezado | Sin resultado nuevo; UAT extendida no ejecutada. | Email sintético Admin/User, fallback, MFA, roles, invitación, sesión HttpOnly y publicación. |

Los parciales anteriores permanecen separados. G01/G02=20/20; G03–G10=0/80; total **20%**,
delta cero; D01–D14=0/14. El fallo sintético detiene las etapas locales dependientes; CI V3
permanece aislado y sin validación nueva.
