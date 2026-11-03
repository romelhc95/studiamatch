# H3REQ1 — avance actual y traspaso ejecutable del próximo ciclo

En el corte histórico de 2026-10-04 la entrada de ingeniería se remitía a la capa de
trazabilidad de entonces. Para continuidad actual, comenzar por el [índice principal](../indice.md),
leer la [autoridad operativa](../estado_del_proyecto.md) y aplicar el
[protocolo del constructor](../trazabilidad/protocolo_constructor.md). La antigua
`00_entrada_tecnica.md` fue consolidada; su backup y destinos están registrados en la
[evidencia de consolidación R11](../evidencia/h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md).
Usar ficha de impacto antes de editar producto/tooling; este traspaso conserva su corte histórico.

Prompt de continuación del corte 2026-10-08 (histórico): [ruta EXEC-01–06 solicitada 2026-10-06](../evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md).
Los prompts/cortes anteriores quedan históricos: ahora hay bootstrap completado,
R4 healthz FAIL, D1 guard FAIL y D2 pendiente. No volver a pedir bootstrap inicial.

Fecha de revisión: 2026-10-05. Estado: **NO-GO_H3REQ1_DEVELOPMENT_FREE**.
Este traspaso registra los fallos históricos v2/v3 y el PASS del runtime PG17/PostgREST
local v4. El resultado global sigue **NO-GO**; no autoriza reintentos v2/v3/v4, gates
posteriores, Git/Auth/deploy ni declara GO.

## Amarre y orden de lectura

Último contraste: [avance PR/remoto y prompt para nueva sesión](h3req1_estado_pr_y_remoto_2026-10-05.md).
Confirma C03 SQL v3 PASS y separa explícitamente el drill integrado pendiente del PR
y D01–D14 remotos. No volver a solicitar el JIT SQL v3 consumido.

[Índice](../indice.md) → [estado vivo](../estado_del_proyecto.md) →
[HITO-003](../hitos/hito_003.md) →
[TASK-H3-001](../backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md) →
[plan único](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md) →
[evidencia del candidato](../evidencia/h3req1_development_candidate_cycle_2026-10-04.md) →
[manifiesto JIT v1 fallido](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05.md) →
[JIT v2 fallido](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v2.md) →
[resultado JIT v3](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v3.md) →
[resultado JIT v4](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v4.md).
Validar aceptación contra la [atestación sanitizada](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md).
El [mapa histórico del vault](mapa_documental_obsidian_2026-10-04.md) conserva las
referencias y conectividad de aquel corte; el índice actual contiene la navegación vigente.
Ningún enlace histórico concede permisos.

## Addendum ejecutado localmente — 2026-10-05

Se cerró localmente el HIGH de cardinalidad DO agrupando el par de cuotas de login por
IP HMAC, con compatibilidad del payload BFF anterior, límite de cardinalidad y cleanup
transaccional; se corrigió el shard del mock de aislamiento. La lectura del código SDK
2.109.0 confirmó `listFactors()` por GET `/auth/v1/user`, por lo que no se añadió GET
`/auth/v1/factors`; la aprobación humana para ese método quedó sin consumir.

Docker: pytest **287 PASS/4 skips**, TypeScript PASS, lint 0 errores/9 warnings,
regresiones de cuotas/Miniflare/SDK/BFF/Auth/Edge/safe-suspend y smoke H2 PASS. El bootstrap
v2 añadió 90 paquetes, auditó 91 y reportó 0 vulnerabilidades; su riesgo MEDIUM expiró al
completarse npm ci. PG17 v3 pasó H2/H3, baseline Pro, cadena H2→H3 y cuotas; el replay
falló por headers non-editor residuales. Se corrigió el harness para repetir el proof exacto
inmediatamente tras la llamada positiva. Bajo JIT v4 pasaron H2/H3, baseline Pro, cadena,
cuotas, replay 409, safe-suspend y baseline futuro contraído; PostgREST HTTP/SDK, assert y
concurrencia también PASS. El manifiesto v4 registra hashes/resultados. Runners/red/PG17
tmpfs se conservan sin cleanup; no hubo servicios remotos.
Certification/Production siguen fuera del alcance.

Secuencia siguiente: H3-CLOSE-03 — diseñar/probar rollback integrado workerd+Edge+PG17 y
recuperación con alcance local; luego H3-CLOSE-04–06. CI protegido, integración/despliegue
y aceptación D01–D14 requieren autorizaciones separadas; no ejecutar cleanup.

**Addendum H3-CLOSE-03 — revisión y validación local 2026-10-05:** safe-suspend SQL no revocaba
`admin_signed_rpc` (`SECURITY DEFINER`), aunque revocaba sus funciones objetivo; el
harness de suspensión no ejercitaba esa ruta firmada. Con autorización local acotada se
actualizaron `db/rollback/h3req1_safe_suspend.sql` y
`tests/sql/h3_safe_suspend_harness.sql` para revocar, probar y snapshot/restaurar la ACL
del dispatcher. El JIT nuevo ejecutó baseline H2→H3, cuotas y gateway firmado en PG17,
todos PASS. La salida del gateway reveló HMACs sintéticos de test, sin claves/JWT reales;
no se copiaron valores a evidencia. Safe-suspend después pasó bajo JIT v2 con
`psql -q -o /dev/null`, exit code 0 y sin output. JIT v4 no cubre estos bytes. H3-CLOSE-03
sigue pendiente del ensayo integrado y recuperación real; el restore del harness es
TEST-only. Consultar el [manifiesto JIT v2](../operaciones/manifiesto_jit_h3_close03_safe_suspend_pg17_2026-10-05_v2.md) y preservar su PG17 sin cleanup.
H3-CLOSE-02 v4 sigue vigente (72/72 inputs intactos); la autoría local cambió dos inputs
C03 y agregó uno. Bajo el JIT safe-resume v3 exacto y `continua`, el nuevo subgate SQL
terminó PASS (4/4 exit 0; los tres roots iniciales fueron solo bootstrap). El PASS v2 queda
histórico. El PG17 nuevo se conserva sin cleanup y el anterior no se tocó. C03 integrado
sigue pendiente de JIT independiente. Ver [preflight](../evidencia/h3req1_h3_close03_integrated_preflight_2026-10-05.md).

## 1. Qué se analizó y qué no

Lectura de WIP, historial Git, notas, migraciones/harness y hashes de archivos actuales;
se repitió pytest en Docker y `node --check`, credential scan y diff check tras los últimos
cambios. JIT v2/v3/v4 ejecutaron SQL únicamente en PG17 desechable; v4 completó además
PostgREST/wire local y concurrency. No se ejecutaron Auth/correo, grants, Git/CI remoto,
Cloudflare, deploy ni cleanup. La revisión del grafo corresponde al ciclo documental
anterior.

Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`,
`feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`; el WIP sigue sin commit.
No confundir ese SHA con los bytes modificados o con un deployment. Preservar el
checkout `/home/romel/src/studiamatch`, sin copiarlo ni descartarlo automáticamente.
No se refrescaron refs remotos: los SHA remotos del plan son snapshots históricos.

## 2. Avances consolidados, sin reabrir trabajo resuelto

| Avance | Implementación/evidencia registrada | Qué sigue pendiente |
|---|---|---|
| Auth+MFA existente | Login/challenge/verify y RPC AAL2 reales PASS en el ciclo remoto del 2026-09-27 | Transición de esa misma cuenta al nuevo BFF, refresh/logout y aceptación real del candidato |
| Cuotas BFF/DO y Edge | Admisión DO antes de RPC, persistencia/concurrencia y shard acotado; reserva antes de envío Auth; 120/actor/min Edge; wire/assert/concurrencia PASS bajo v4 | Validación integrada/final y aceptación remota; repetir solo gates afectados por nuevos cambios |
| Gateway metadata | EXPAND y payload-bound probados en PG17/PostgREST bajo v4; actor/proyecto/método/destino/tiempo/key-id y replay 409 | Conservar evidencia de hashes v4; no confundir con activación/enforcement remoto |
| Firma payload-bound | Transporte envía `admin_signed_rpc`, segunda HMAC del destino+JSON args; runtime v4 pasó llamadas firmadas y replay 409 con `v_key_id` | Conservar evidencia; el PASS local no demuestra enforcement remoto |
| Guard `p_first: null` | RPC rechaza SQL NULL; delta forward repara fuente o snapshot privado de cuota; dispatcher convierte JSON null a sentinel 0; harnesses de cadena/cuotas/gateway PASS v4 | Preservar resultado y revalidar por impacto si cambian fuentes; no volver a pedir ejecución inicial del guard |
| Revisión de seguridad y JIT | pytest 287 PASS/4 skips, credential/diff PASS; egress MEDIUM limitado a npm ci y expirado; seguridad estática sin hallazgos; runtime v4 SQL/wire local PASS | JIT v4 consumido; no acredita `db_pre_request`, CI ni enforcement remoto |
| Mantenimiento | Romel owner de braces y facetas priceMin con fecha 2026-11-03 | Owner/disposición de dos warnings no usados, PyPDF2 y cuatro skips live |

No queda el defecto de HMAC no ligada al cuerpo: se remediaron payload-bound y NULL, y el
runtime v4 pasó la firma payload-bound y replay 409. El 403 v3 era el fixture non-editor
residual; el replay exacto se reubicó junto a la llamada positiva y pasó en PG17 v4. El gate
local SQL/wire H3-CLOSE-02 queda PASS, sin acreditar enforcement remoto.
Los errores SQL/HTTP de los JIT 1–5 se conservaron; el quinto confirmó HTTP 403 pero
paró por el código required/invalid. Nunca terminó wire/assert. Las correcciones
posteriores cambian inputs: el «sexto JIT» antiguo de 41 inputs ya está obsoleto.

## 3. Estado de las ocho tareas y dependencia de salida

| ID | Estado actual | Próxima acción verificable | Salida requerida |
|---|---|---|---|
| H3-CLOSE-01 | Parcial | Refrescar inventario, dependencias y manifiesto de fuentes; clasificar WIP/evidencia y baseline | Candidato íntegro, scope/cliente trazables, sin drift pendiente |
| H3-CLOSE-02 | PASS local PG17/PostgREST v4, incluido replay y concurrency | Preservar evidencia y no reutilizar JIT | SQL/harness/wire/assert actuales PASS, rechazo y cuotas sin bypass |
| H3-CLOSE-03 | Subgate SQL safe-suspend/resume PASS bajo JIT C03 v3; integrado pendiente | Preparar JIT nuevo exacto y ensayar Pages+Edge+SQL+cookies+bindings e in-flight/recuperación, incluyendo dispatcher firmado | Rollback integrado PASS y procedimiento de recuperación operativa explícito; restore del harness no basta |
| H3-CLOSE-04 | Parcial | Registrar owners/decisiones restantes y tratamiento individual de skips | Mantenimiento/riesgos explícitos; sin aceptación inventada |
| H3-CLOSE-05 | Pendiente local/remoto | actionlint/shellcheck sobre workflow final; lectura autorizada de protecciones y bootstrap | Check independiente instalado/requerido, review actual y enforcement acreditados |
| H3-CLOSE-06 | Parcial | Build/UAT visual/onboarding actuales + reauditoría/pilares/atestación/hashes | Ready exacto, no cifras copiadas de r17/otros bytes |
| H3-CLOSE-07 | No ejecutado | PR/merge/Free/Edge/Worker/Pages y activación compatibles con permisos separados | Deployment real y recursos/SHA/host identificados |
| H3-CLOSE-08 | No ejecutado | D01–D14 del plan, cuentas separadas, correo real, rollback y recuperación autorizados | GO Development real con aceptación completa |

El próximo gate es H3-CLOSE-03, rollback integrado y recuperación segura entre artefacto
workerd, Edge y PG17. El PASS local H3-CLOSE-02 no lo cubre. Antes de cualquier operación
SQL/servicio remota se requiere JIT independiente; no se repetirá el JIT v4 ni se limpiarán
los recursos locales existentes sin permiso específico.

## 4. Manifiesto de referencia histórico — corte 2026-10-04, NO usar para ejecutar

La tabla conserva los bytes leídos el 2026-10-04, anteriores a `v_key_id`, replay
corregido y safe-suspend del dispatcher. NO es el manifiesto vigente ni una lista de
pendientes. El runtime aprobado corresponde al [v4](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v4.md),
y los bytes posteriores de rollback/harness al [safe-suspend v2](../operaciones/manifiesto_jit_h3_close03_safe_suspend_pg17_2026-10-05_v2.md).
Ambos permisos están consumidos. Para otro ensayo, reunir inputs transitivos y hashes
reales nuevos y pedir JIT específico; no heredar autorizaciones ni repetir los gates
de H3-CLOSE-02 por leer esta tabla histórica.

| Archivo | SHA-256 |
|---|---|
| `db/migrations/20260927_h3_admin_queue_facets_filter.sql` | `efabbb35e5fc8b9dc28ce3159ed3ed2328f20c74e4d8e02d2a1a222e8351600b` |
| `db/migrations/20261004_h3_admin_queue_first_null_guard.sql` | `012f994af8b44353e385e68b22dc1b15535e31f47f8f990716cbd726f1908711` |
| `db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql` | `e80e236348c2eefe79035c6f6ea5e22bc5dea194555d07a1f1b5a8b41a02876c` |
| `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql` | `f1b4dce0dc0634585b5448514877b200924448c7e2dcc06441f1c3f66af78d0f` |
| `web/src/lib/supabase-transport.ts` | `0b4043403c294467f370b5adfe186cf97452efe1c1d031ae07e0ea3d10a9652f` |
| `tests/sql/h3_from_h2_pro_pg17_harness.sql` | `c5f45bd65427497050832b9c0f7c517e687ea9e1961fcdc0e8653f2932b8d379` |
| `tests/sql/h3_admin_quota_harness.sql` | `890464e81ae5bbbce9c3440d7318460c32970e8e5b89dc9693ef7aa30af7ca90` |
| `tests/sql/h3_admin_rpc_signed_gateway_harness.sql` | `221e9100e9353db89e3fafd7f16fad4addcd9f958d8738b4d9a262e62819af01` |
| `tests/sql/h3_safe_suspend_harness.sql` | `c1dcfef828b836e6627530127eb66a157db1df1437ad923a06f6c64e2c6782f1` |
| `tests/sql/h3_quota_postgrest_fixture.sql` | `307704d2734506902b8974beb36fb29c5dd35d36f797e70c9bd2f27070b228ed` |
| `tests/sql/h3_quota_postgrest_assert.sql` | `f0f2285b23bb4fddb7e5fdc4aa2ee409d822524fc1ed110abd42e6ff11a6aad9` |
| `tests/h3_admin_quota_postgrest.mjs` | `7b1770a533773ef9ca7be2bfb9ab24994e25895857c37a50b958fcdbd383be3e` |

Se observó modificación de la fuente `20260927_h3_admin_queue_facets_filter.sql`, ya
aplicada en Free históricamente. No usar ese archivo como mecanismo de reparación
remota ni reescribir el ledger; el delta forward `20261004...first_null_guard` es el
candidato de reparación. Clasificar la diferencia fuente/fixture en el manifiesto y
revisar alcance con humano si el gate de migraciones aplicadas exige decisión.

## 5. Próximo ciclo local: procedimiento para otro agente

1. Leer el amarre; listar tareas/gates y recibir `continua`. Confirmar status/HEAD,
    salud/mounts y ausencia de secretos. No asumir que `/app` sirve este worktree.
    El contenedor candidato registrado es `h3req1-candidate-docker-20261004`, copia
    independiente en `/workspace`; validar que sus fuentes coincidan, no reutilizarla a ciegas.
2. Reconocer H3-CLOSE-02 **PASS local v4** y el subgate SQL safe-suspend/resume
   **PASS C03 v3**. Preservar ambas evidencias y comparar hashes antes de continuar; no
   repetir sus harnesses sin impacto demostrado ni reusar sus JIT consumidos.
3. Empezar **H3-CLOSE-03 integrado**: diseñar runner y protocolo coordinado de Pages/workerd,
   Edge y PG17/PostgREST con cookies, bindings, dispatcher firmado, cuotas y reservas
   in-flight. Diferenciar pruebas interceptadas y runtime real local. Definir qué se
   ejecutará en cada servicio, recursos nuevos/existentes, red aislada, inputs/hashes,
   fixtures sintéticos y estado esperado; no conectar servicios reales.
4. Preparar recuperación operativa explícita antes del ensayo: suspensión conservando
   artefacto endurecido/guard NULL, revocación del dispatcher e iniciadores, finalizadores
   disponibles; recuperación sin reabrir bypass o tokens JS. No usar snapshot/restore
   TEST-only como receta de producción. Si requiere decidir cómo reanudar o aceptar
   interrupción, explicar opciones al humano y esperar respuesta.
5. Solicitar JIT específico antes de autoría/ejecución SQL/grants y de cualquier operación
   protegida del drill. El permiso debe identificar DB/recursos, hashes transitivos,
   pasos, efectos y recuperación; no sustituirlo por `continua` ni por v4/v2 consumidos.
   Preservar contenedores/redes/bases existentes. Cleanup tiene autorización independiente.
6. Bajo permisos exactos, probar normal -> suspensión conjunta -> nuevos iniciadores
   rechazados -> cookies limpiadas -> finalizadores previos completan -> datos/auditoría
   y web pública preservados -> recuperación segura verificada. Incluir llamada firmada
   a `admin_signed_rpc`: no basta medir ACL de funciones internas. Evitar mostrar/persistir
   JWT/HMAC/secretos incluso sintéticos. Detener ante FAIL; conservar resultado sanitizado,
   corregir y revalidar. Cambios en inputs protegidos exigen renovar hashes/JIT.
7. Continuar H3-CLOSE-04–06: owners/skips, build y UAT visual/onboarding del último
   artefacto (48/48 y 144/144, 10/10 según runner actual), actionlint/shellcheck y revisión
   final. Si aumenta cobertura, registrar conteos nuevos. Acreditar CI independiente
   con lectura/bootstrap/protecciones autorizados; no por presencia local del YAML.
8. Completar H3-CLOSE-01 pendiente y congelar manifest fuentes/build/resultados separados,
   paquete PR acotado, revisión final sin HIGH/CRITICAL,
   pilares y aceptación sanitizada; actualizar plan/estado/evidencia/tarea/hito. Ready
   no equivale a GO D. Continuar integración/deploy/UAT real del plan cuando cada permiso
   Git/SQL/Auth/secretos/Cloudflare/rollback haya sido otorgado separadamente.

No reabrir revisión general de gobierno ni recuperación de arquitectura histórica:
esas iniciativas quedan para después de cerrar H3REQ1. Sí completar los controles CI
obligatorios del hito, sin reducir protecciones. Una revisión independiente conserva
su alcance: no afirmar seguridad/GO integral por un PASS focalizado.

## 6. Development real y lo posterior

Mantener D01–D14 del [plan único](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md):
cuenta existente distinta del onboarding, sin reinvitar/reenrolar; roles/último admin;
editor/locking/publicación/auditoría/90 días/ruta elegible; sesiones/perímetro/Access;
cuotas y rollback real. SHA integrado, deployment/hostname, schema/Edge/Worker/config
deben coincidir con evidencia. Free `aqrldlmlszjtgpqiegaa`, no hostname Admin productivo.
Reset de cuenta es estrategia previa, NO permiso; comprobar necesidad y preservar historia.

Después de GO D: pedir promoción `desarrollo -> certificacion`; aislar fixtures y
ventanas porque ambos comparten Free; CI/review y matriz sobre host Certification.
Después de GO C: pedir preparación Pro `xwhtiqmboljkshrtviyw` y promoción a main;
expand compatible antes de frontend, Access en `admin.studiamatch.com`, 404 público,
estabilidad acordada, contract aprobado y evidencia cliente/pilares. Ninguna fase posterior
queda autorizada por este traspaso. Pro es baseline; no sincronizar datos operativos Free.

## 7. Consulta humana en lenguaje sencillo y prompt

La próxima pregunta necesaria, una vez preparado el protocolo, es: «La base y el
acceso firmado ya pasaron sus pruebas. Falta comprobar que podemos pausar y recuperar
todo el panel sin perder datos ni dejar una vía de acceso abierta. ¿Autorizás este
ensayo integrado solo local, con estos recursos y archivos exactos, sin tocar tus
cuentas ni producción?» Adjuntar manifiesto exacto, recuperación y límites. No
preguntar vagamente «¿continuamos todo?» ni solicitar repetir la validación inicial.
Si hay opciones, explicar qué cambia para la persona, recomendar una y esperar decisión.

```text
continua con H3REQ1 en /home/romel/src/studiamatch-h3req1-sync-20261002,
rama feat/h3req1-sync-20261002.
Lee AGENTS.md, .context/estado_del_proyecto.md,
.context/operaciones/plan_cierre_integral_h3req1_2026-10-04.md y
.context/seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md,
con sus evidencias y atestaciones. Lista tareas y gates antes de editar.
H3-CLOSE-02 ya pasó PG17/PostgREST/wire/assert/concurrencia bajo JIT v4;
el subgate SQL safe-suspend/resume persistente pasó bajo JIT C03 v3 exacto.
Empieza en H3-CLOSE-03 integrado: rollback coordinado Pages/workerd+Edge+SQL,
cookies/bindings/in-flight y recuperación operativa segura, no restore TEST-only.
Revalida hashes y alcance; conserva los PASS vigentes y no repitas JIT consumidos.
Si nuevos cambios invalidan evidencia, explica impacto y pide JIT nuevo exacto. El subgate
SQL PASS no autoriza reintentos, integración ni cleanup de sus dos PG17.
Después completa H3-CLOSE-01 pendiente y H3-CLOSE-04–08 hasta GO Development real:
candidato exacto, UAT final, CI obligatorio efectivo, PR/integración/despliegue
y D01–D14 remotos con aprobaciones por operación. No termines solo en PR_READY.
Este continua autoriza el ciclo local funcional, NO SQL/grants, operaciones
remotas, secretos, Auth/reset, push/PR/merge, protección, deploy, rollback/resume,
cleanup ni acciones destructivas: solicita permisos separados y espera respuesta.
Trabaja en Docker contra el worktree correcto; preserva original, WIP, recursos
y evidencias. Conserva Auth+MFA real histórico y prueba transición sin reinvitar
ni reenrolar cuentas existentes. Corrige/revalida sin GO parcial ni bloqueos ocultos.
Actualiza Obsidian enlazado con resultados reales. Ante dudas, explica opciones
en lenguaje sencillo. No revises gobierno general ni recuperes arquitectura histórica.
No ejecutes Certification/Production. Detente en GO Development real o bloqueo
concreto de autorización, drift o validación, con evidencia y siguiente decisión.
```
