# TASK-H1-001 - HITO-001

| Campo | Valor |
|---|---|
| ID | `TASK-H1-001` |
| Estado | `IN_PROGRESS` |
| Requerimiento | `REQ-EST-001` |
| Hito | [HITO-001](../../hitos/hito_001.md) |
| Fase vigente | Macrofase `F9` completada y `F10` en rebaseline metadata. F10.9 conserva `G4=STOP_REQUIRES_REBASELINE`. [M0 F10.10 post-merge](../../operaciones/m0_f10_10_post_merge_evidence_2026_08_10.md) registra PR #343 fusionado en `desarrollo@f59c35272ccec930434b3ceeb1aee8eac732d4b9`, con Security Audit `31419218575=PASS` y F9.7 `31419218779=PASS`. M0 queda PASS; M1 esta autorizado solo para tooling, fixtures y pruebas offline. M2-M10 no estan autorizados. Hito 1 permanece `TECHNICALLY_DELIVERED_FORMAL_CLOSURE_PENDING`. |
| Criterios activos | `H1-CA1` |
| Criterios historicos | `H1-CA2P` y `H1-CA7P` preservados como antecedentes; alcance pendiente trasladado a `H2-CA2` y `H4-CA7` |
| Adenda vigente | [ADENDA-REQ-EST-001-001](./adenda_cliente_001_sanitizada.md), `APPROVED_EFFECTIVE` |

Esta nota es la autoridad exclusiva del estado vivo de `TASK-H1-001` y de sus criterios. La tarea no tiene subtareas. Los IDs `WP-F9.7-*` son unidades operativas internas de F9.7 y no agregan criterios, subfases ni autorizaciones.

Base tecnica post-cierre documental F10.8: `main@38314170197a907ac5c4c815a9bb18b3d5f29b06` / tree `741627eda4b4fbcf76503b8e353abb08ac0eb1c4`.

El [seguimiento detallado de Hito 1](./seguimiento_detallado_hito_1.md) es una vista `TRACKING_ONLY`: organiza work items y evidencia sin crear subtareas, criterios, alcance ni autoridad de estado paralela.

## Objetivo Contractual

Cerrar Hito 1 con `H1-CA1` exclusivamente: schedules y operacion segura de FG2/FG3, con FG1 como soporte operativo, sin saltar gates, circuit breakers ni controles de credenciales.

## Rebaseline Vigente CA1-Only

La decision humana de F9.7 adopta la adenda aprobada para cerrar Hito 1 con
`H1-CA1` en produccion y trasladar CA2 completo a Hito 2. Desde esta rebaseline:

- `H1-CA1` es el unico criterio activo de esta TASK hasta
  `COMPLETED_PRODUCTION_CA1_ONLY`.
- `H1-CA2P` se preserva como antecedente y su alcance pendiente pasa a
  TASK-H2-001 como `H2-CA2`.
- `H1-CA7P` se preserva como antecedente y su alcance pendiente pasa a
  TASK-H4-001 como `H4-CA7`.
- Los avances CA2 locales no se promueven con el candidate CA1-only.
- Produccion conserva su comportamiento actual para leads/email.

El plan ejecutable futuro es
[PLAN-H1-CA1-ONLY-001](../../operaciones/plan_cierre_hito1_ca1_only.md). F9.8
quedo cerrada por replay post-merge del candidate CA1-only (PR #270/#271,
`desarrollo@5b282461149b7319685cf090534e28051e5eb32c`). F9.9 promovio el
candidate selectivo a `certificacion` mediante PR #277, registra una desviacion
fail-closed aceptada, fusiono controles pre-main en PR #280 y obtuvo QA
independiente `PASS`. F9.10 quedo cerrada despues de PR #285, CI post-merge,
boundary final, run F9.9 cancelado sin pasos y `USER_PERSONAL_UAT=PASS`.
F10.6 quedo completada para control-plane: environments programados fail-closed,
variables verificadas, runs antiguos cancelados con cero pasos y sin aprobacion de
deployments. F10.7 quedo registrada como entrega tecnica post-main por PR #291.
F10.8 promovio la remediacion de Production Canary por PR #297 a
`main@260900a268ab8eb194140ea7311aec2a170b6e17`; `security-audit`, `F10 Main
Boundary`, Cloudflare Pages y Certification Canary `31140933096=PASS` sobre
`certificacion@94026de77fe9c1a01c66eae78bea8b09858daf96` quedaron verificados.
El artifact del canary quedo sanitizado: tres JSON, cohortes `redacted`, sin
`institution_id`, hosts Supabase ni UUIDs operativos en artifacts; conteos y gates
`pre == post == after_cleanup`. DB Sync `31142826000` fallo fail-closed antes de
Supabase porque un push CA1-only sin cambios `db/**` ejecuto un report de
migraciones incompatible con la version de `main`; apply/schema/FG2 quedaron
skipped. La remediacion DB Sync fue promovida por PR #304/#305/#306/#307 hasta
`main@529ca111f1fef40efb15676ad6f07d002a54ae92`; el run post-merge
`31151066062=SUCCESS_NO_DB_CHANGES_SKIPPED` ejecuto solo `Detect DB changes` y
omitio preflight/report/apply/schema/FG2 por ausencia de cambios `db/**`.
`Security Audit Gate` post-main `31151066061=PASS`. La remediacion cleansing
provenance fue promovida por PR #319 a `certificacion` y por PR #320 a
`main@1885806f0d9f189600d410d353fcf13fb8dd4676`. DB Sync to Production
`31243797695=SUCCESS_REPORT_ONLY` detecto exactamente una migracion Pro pendiente
y no aplico DDL. En ese corte no hubo Production Canary acreditable, snapshot
Production, writer ni mutacion DB; la DDL Pro seguia pendiente. El hito queda
`TECHNICALLY_DELIVERED_FORMAL_CLOSURE_PENDING` hasta completar
`EVID-H1-011..013` y `EVID-H1-016`; `EVID-H1-010=VERIFIED` queda registrado
por Production Canary `31272290614`.

La matriz viva de evidencias y umbrales de salida de Hito 1 se mantiene en
[PLAN-H1-CA1-ONLY-001](../../operaciones/plan_cierre_hito1_ca1_only.md#evidencia-de-salida).
No modifica estados, criterios ni autorizaciones.

## Hallazgo Tardio F10.9

La activacion global posterior al canary descubrio fallos fail-closed de FG2 y
FG3 documentados en
[INC-F10.9-001](../../operaciones/incidente_f10_9_fg2_fg3_2026-08-09.md).
Los runs y reruns diagnosticos no acreditan observacion natural; el contador de
pares vuelve a `0` y la ventana de 72h queda `NOT_STARTED` segun
[EVID-H1-OBS-F10.9-001](../../evidencias_cliente/sprint_1/registro_observacion_production_f10_9_2026-08-09.md).

[PLAN-REM-F10.9-001](../../operaciones/plan_remediacion_f10_9_fg2_fg3.md)
registra contencion, hardening, planners y gates separados. El plan no autoriza
kill switch, codigo, DDL/DML, backfill, schedules ni retries por si mismo. La
decision humana vigente exige cero cursos activos sin syllabus/objectives antes
del cierre. `H1-CA1` no cambia y no se crean subtareas ni criterios nuevos.

### Secuencia Paso A Paso F10.9

La secuencia historicamente planificada se documenta en
[PLAN-REM-F10.9-001](../../operaciones/plan_remediacion_f10_9_fg2_fg3.md). G0-G3
fueron consumidos; G4 produjo STOP. Ninguna frase F10.9 habilita ahora G5-G13:
requieren primero una decision de autoridad superior fuera de F10.9.

1. `G0`: cerrar R0 y estabilizar/integrar P1 sobre ancestry protegido conforme a
   [G0-R0-F10.9](../../operaciones/g0_r0_reconciliacion_f10_9.md).
2. `G1`: `PASS`; P2 planners read-only/offline integrados por PR #335.
3. `G2`: `PASS`; P3 preflight FG2 y P4 atomicidad FG3 integrados por PR #338.
4. `G3`: `PASS`; P5 metadata read-only/fail-closed integrado por PR #341.
5. `G4`: `STOP_REQUIRES_REBASELINE`; bloquea P7/G5 y gates posteriores.
6. `G5`: `BLOCKED_NOT_AUTHORIZED` hasta decision de autoridad superior.
7. `G6`: `SUSPENDED_BY_G4_STOP_REQUIRES_REBASELINE`.
8. `G7`: `SUSPENDED_BY_G4_STOP_REQUIRES_REBASELINE`.
9. `G8`: `SUSPENDED_BY_G4_STOP_REQUIRES_REBASELINE`.
10. `G9`: `SUSPENDED_BY_G4_STOP_REQUIRES_REBASELINE`.
11. `G10`: `SUSPENDED_BY_G4_STOP_REQUIRES_REBASELINE`.
12. `G11`: `SUSPENDED_BY_G4_STOP_REQUIRES_REBASELINE`.
13. `G12`: `SUSPENDED_BY_G4_STOP_REQUIRES_REBASELINE`.
14. `G13`: `SUSPENDED_BY_G4_STOP_REQUIRES_REBASELINE`.

Ningun gate concede el siguiente. G0 cerro el
`BLOCKED_INHERITED_CONTEXT_GRAPH` registrado en el plan, sin importar CA2 ni
inventar documentos. Un cambio de SHA/tree, schema, cantidades, profile,
environment, dependencias o normalization version invalida el manifest y produce
`STOP`. F11.1 y `EVID-H1-016` siguen fuera de esta secuencia hasta que
`EVID-H1-011..013` sean verificadas.

### Secuencia F10.10

F10.10 es la subfase activa para registrar el rebaseline mutante separado. M0 es
documental; M1-M10 requieren frase decimal F10.10 y alcance adicional por gate:

1. `M0`: `PASS`; ADR, plan y autoridad integrados por PR #343.
2. `M1`: `AUTHORIZED_LOCAL_ONLY`; tooling y pruebas offline, sin red/DB/provider.
3. `M2`: promocion de codigo sin ejecucion remota.
4. `M3`: contencion y diagnostico read-only por ambiente.
5. `M4`: generacion privada atribuible.
6. `M5`: revision editorial total de outputs provider.
7. `M6`: pilot maximo 5.
8. `M7`: restore y pruebas NOOP.
9. `M8`: lotes maximo 10 con stop-on-drift.
10. `M9`: metadata cero y cero cambios no-cohorte/ETL.
11. `M10`: decision superior de handoff a F10.9/G4.

F10.10 no habilita schedules ni F11.1 y no copia datos entre ambientes.

## Arbol De Criterios

```text
TASK-H1-001
`- H1-CA1
```

`H1-CA2P` y `H1-CA7P` permanecen fuera del arbol activo como aliases historicos.

## Criterios Y Entregables

| Criterio | Estado contractual | Base implementada o aceptada | Pendiente para certificacion |
|---|---|---|---|
| `H1-CA1` | `ACTIVE_CA1_ONLY` | Workflows automaticos, schedules, gates y circuit breakers de F7; candidate local CA1-only F9.8 replay-validado post-merge; candidate selectivo PR #277 aprobado/fusionado en Certification con fail-closed 403 documentado; controles pre-main PR #280/#282/#283/#285; QA independiente `PASS`; F10.6 control-plane completado fail-closed; F10.7 entrega tecnica post-main por PR #291 con boundary 32 objetos y Cloudflare Pages `SUCCESS`; F10.8 remediacion Production Canary promovida por PR #297 a `main`, Certification Canary final PASS y DB Sync fail-closed pre-Supabase sin DDL/DML ni mutaciones; remediacion DB Sync promovida por PR #304/#305/#306/#307 a `main@529ca111f1fef40efb15676ad6f07d002a54ae92`; remediacion cleansing provenance promovida por PR #319/#320 hasta `main@1885806f0d9f189600d410d353fcf13fb8dd4676`, con DB Sync report-only `31243797695=SUCCESS_REPORT_ONLY`; Pro DDL aplicada una sola vez por `31263024890`; DB Sync verify `31268229878=PASS`; Production Canary completo `31272290614=PASS` con artifact sanitizado `9026139906` | F10.10 M0-M10, handoff superior a F10.9/G4, gates F10.9 rebaselinados, observacion de schedules y F11.1 conformidad/cierre |
| `H1-CA2P` | `HISTORICAL_TRANSFERRED_TO_H2_CA2` | Schema local F6-F8, calidad y seguridad base como preparacion historica | No cierra Hito 1; Hito 2 debe producir candidate, adopcion y evidencia nueva |
| `H1-CA7P` | `HISTORICAL_TRANSFERRED_TO_H4_CA7` | Contrato documentado, Context Graph y `SRC-REQ-001` reconciliada | No cierra Hito 1; Hito 4 debe producir documentacion y evidencia nueva |

El alcance contractual vigente permanece en [REQ-EST-001](./_index.md) y [HITO-001](../../hitos/hito_001.md). [EST-001](../../estimaciones/est_001.md) conserva solo complejidad y estimacion tecnica original; esta tabla no agrega criterios.

## Equivalencias Aceptadas De H1-CA2P

Las siguientes equivalencias semanticas quedan preservadas como antecedente de
`H2-CA2`; no acreditan adopcion remota, no sustituyen pruebas por rol y no
autorizan schema, migrations ni backfill en Hito 1:

| Necesidad contractual | Campo local aceptado |
|---|---|
| Faltantes | `missing_fields` JSONB |
| Fuentes de campo | `field_sources` JSONB |
| Actualizacion manual | `manual_updated_at` |
| Inicio | `start_date` |

## Contexto Verificable

El baseline de workflows debe contrastarse con `H1-CA1`; los comentarios no sustituyen la configuracion ejecutable. La modalidad aprobada es cadencia automatica con gates, circuit breakers y controles de ambiente.

El estado DB vigente se obtiene de `estado_del_proyecto.md` y evidencia F10.8.
[Sistema DB](../../sistema_db_supabase.md) y [Matriz DB](../../operaciones/matriz_adopcion_db.md)
se conservan como referencias historicas pre-F10.8; no autorizan adopcion ni se
editan ledgers historicos.

El candidate DB-as-Code vigente se registra en Reconciliacion F6. PR #223 incorporo el package a `desarrollo` y PR #224 cerro su portabilidad LF/CRLF. La existencia del candidate no prueba adopcion remota ni completa `H1-CA2P` antes de certificacion.

F8 agrego una closure forward-only y certificacion local reproducible documentadas en Certificacion local Hito 1 F8. PR #228 fue fusionado y validado post-merge. El resultado local no habilita Free/Pro ni autoriza el backfill editorial.

El package historico `FASE-09`, ahora mapeado a F9.1, se limita a [precertificacion local H1-CA2P](../../operaciones/precertificacion_hito1_f9.md): package real en PostgreSQL efimero, rollback, replay del contrato F8, ledger paginado y reconciliacion de nomenclatura fail-fast. No completa este criterio ni autoriza acceso remoto.

F9.1 conserva byte-identicos el manifest y las migrations F8. PR #231 y la remediacion CRLF #232 fueron fusionados y validados post-merge; status/targets no cambian.

El package historico `FASE-10`, ahora mapeado a F9.2, se limita al [contrato local de promocion](../../operaciones/promocion_hito1_f10.md): reemplaza prerrequisitos universales por evidencia por transicion y crea un descriptor sucesor bloqueado. No modifica el candidate F8, no cambia status y no accede a ambientes remotos.

F9.2 conserva F8 byte-identico y valida neutralmente estructuras de attestations sin conceder estado/capability. PR #235 fue aprobado, fusionado y validado post-merge sobre `desarrollo@d67fa31`; su ruta operacional historica no otorgo attestations ni transiciones de estado. F9.1/F9.2 no completan la macrofase F9 ni `H1-CA2P`; F10 Produccion y F11 Cierre siguen pendientes.

F9.3 fue autorizada mediante la frase decimal exacta y congelo un contrato exclusivamente local: descriptor inmutable, catalogos read-only cerrados, target binding no reversible, schemas neutrales para la F9.4 entonces prevista, runner sin transportes y job CI sin secrets. PR #238 fue aprobado y fusionado; el replay detecto una incompatibilidad del fixture con CRLF del bind mount Windows, remediada y fusionada mediante PR #239. `desarrollo@4e77fe0` repitio desde un checkout Linux limpio dentro de Docker 55 pruebas focused, 253 de regresion, 22 checks sinteticos, Python compile y Context Graph en PASS. No hubo acceso Free/Pro ni cambio de estado. Al cerrar F9.3, F9.4 aun no estaba autorizada; ADR-0004 sustituyo despues esa ruta.

F9.4 adopta [PLAN-H1-SIMPLIFICADO-001](../../operaciones/plan_simplificado_hito1.md) mediante [ADR-0004](../../decisiones/ADR-0004_simplificacion_contractual_hito1.md). Fue exclusivamente local/documental: reconcilio el Context Graph, convirtio la [definicion remota anterior](../../operaciones/preflight_free_f9_4.md) en `SUPERSEDED_NON_AUTHORIZABLE`, preservo el antecedente temporal y lo retiro. No accedio a Free/Pro, no cargo secrets, no creo T01 y no ejecuto DDL, DML, migrations, H-00, backfill, pausa de writers ni workflows remotos. `H1-CA2P` permanece `IN_PROGRESS`.

## Cierre Contractual F9.5

F9.5 termina `COMPLETED_WITH_KNOWN_FINDINGS`. Los intentos y remediaciones locales anteriores se preservan en el [registro historico F9.5](../../operaciones/preflight_free_f9_5.md), pero no justifican una nueva lectura Free ni certifican Free o Pro.

- Todos los artifacts F9.5 introducidos por PR #245 y PR #247 quedan `HISTORICAL_NON_PROMOTABLE`. Se conservan fisicamente para trazabilidad, sin integrarlos al package contractual, a F9.7 ni a una ruta de aplicacion.
- F6-F8 permanecen como la unica base funcional contractual de Hito 1. Los artifacts F9.5 no sustituyen, amplian ni promocionan esa base.
- Al cerrar F9.5, `T01_CONDITIONAL_ACCEPTED` fue una decision documental sin attestation tecnica nueva y habilito solo la definicion entonces futura de F9.6; nunca autorizo schema, migrations, F9.7 ni ramas.
- `H-00` fue un P0 separado de la ruta sustituida; no es prerrequisito del `HITO-001` CA1-only ni de F9.8.
- La definicion inicial F9.6 exigia backup y predicado antes de una posible eliminacion. Esa rama quedo sustituida al cerrar F9.6 sin DML despues de verificar la remediacion historica de PII directa; los intentos de backup no se reclasifican como PASS.

## Cierre F9.6 - H-00 Ya Remediado

F9.6 termina `COMPLETED` con resultado `H00_ALREADY_REMEDIATED_NO_DML`. La verificacion sanitizada EVID-F9.6-H00-001 confirmo la cohorte con remediacion completa de PII directa y sin coincidencias parciales o invalidas. Seguridad y calidad de datos revisaron la cadena de evidencia en GO.

- Gate B DELETE queda `SUPERSEDED_NON_AUTHORIZABLE`; no se elimino ni modifico ninguna fila.
- La cohorte tiene PII directa remediada y se conserva como pseudonimizada. El data owner acepta el riesgo residual de vinculabilidad de UUID y metadatos dentro de Free restringido; no autoriza correlacionarlos con Pro. F9.7 debe verificar ausencia de lectura publica y F11 revaluar su retencion.
- No hubo DELETE, UPDATE, INSERT, backup valido, acceso Pro, schema, migrations, writers ni backfill.
- H-00 sigue fuera del package promocionable y nunca se aplica en Pro.
- Este cierre no certifica Free, no cambia `H1-CA2P` y no autoriza F9.7.

## Candidate Local Contractual F9.7

La autorizacion local F9.7 implementa y valida el candidate sin acceder a Free/Pro:

1. Conserva byte-identicas las cuatro migrations F6-F8 y agrega una unica closure F9.7 forward-only.
2. Versiona `db/manifests/fase09_7_free_schema_rls.json` como descriptor schema v2 de cinco entradas exactas; Free y Pro permanecen bloqueados.
3. Migra exclusivamente lectores backend automaticos FG1/FG2/FG3 a identidad de servicio fail-closed y conserva publishable en frontend/auditorias publicas.
4. Codifica cierre de lectura publica de `leads`/`email_log`, `INSERT leads` por columnas y verificacion RLS/ACL semantica.
5. Valida localmente PostgreSQL 17, rollback, replay, ledger, checksums, credenciales y frontend sin DDL/DML remoto en Free/Pro.
6. Excluye artifacts F9.5, H-00, backfill, Pro, canary persistente y datos operativos.

Gate B verifico Free de forma pre-DDL/read-only y se consumio sin aplicar schema ni pausar writers. Resguardo/restore, pausa de writers, atestacion suplementaria y cualquier aplicacion permanecen sujetos a gates y aprobaciones separadas.

EVID-F9.7-GATE-B-001 ejecuto Gate B con una consulta Free agregada y termino `FREE_GATE_B_FAIL_STOPPED_READ_ONLY`: el boundary candidate vacio fue permitido, pero el acceso de superficies protegidas activo stop conditions. El runner HTTP y las aprobaciones separadas de resguardo/restore y pausa quedaron `NOT_SUBMITTED_BLOCKED_BY_GATE_B_FAIL`; writers, DDL/DML, Pro y backfill permanecieron en cero.

La definicion de remediacion congela el mismo package de cinco entradas, rollback/postcondiciones y runbooks no ejecutables. La atestacion ACL observo cobertura completa del package para fuentes ACL, sin herencia/SET/owner/unknown; el mismatch y el trigger mantuvieron fail-closed y los predicates no atestados bloquearon aplicacion independientemente. No hubo filas de negocio, HTTP, schema, migrations, DML, backup, restore ni control de writers.

La remediacion local del trigger reemplazo el draft suplementario no confirmado por un manifest sucesor v3 de seis entradas. Las cinco migrations historicas quedan byte-identicas; v2 queda como antecedente historico no promocionable; la sexta elimina de forma fail-closed `trg_notify_new_lead` y `public.notify_new_lead()` sin `CASCADE`, el Edge Function historico queda tombstoneado en Git y el drenaje pg_net queda counts-only. [ADR-0005](../../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md) agrega el corte local: la arquitectura leads/email queda `DEFERRED_NO_IMPLEMENTATION`, el frontend soportado no tiene captura publica y el hold actual queda `SUPERSEDED_NON_PROMOTABLE`; la ruta futura exige [PR-O executor privado](../../operaciones/pr_o_f9_7_successor_private_executor.md). No observa ni modifica Free/Pro y no autoriza aplicacion.

El backfill editorial queda trasladado a `H2-CA2`. Para Hito 1 CA1-only queda
prohibido planificarlo, aplicarlo o usarlo como evidencia de cierre.

Estado del corte local: `public_lead_capture=LOCAL_CODE_REMOVED_REMOTE_UNKNOWN`, `email_egress=LOCAL_TOMBSTONE_REMOTE_UNKNOWN`, `security_hold=LOCAL_CANDIDATE_BLOCKED`, `WP-F9.7-02=GO_WP_LOCAL`, `WP-F9.7-03=GO_WP_LOCAL`, `WP-F9.7-04=COMPLETED_LOCAL_MERGED`, `CORR-WP-F9.7-04-01=NO_GO_CI_PARTIAL`, `CORR-WP-F9.7-04-02=COMPLETED_LOCAL_MERGED`, `WP-F9.7-05=COMPLETED_LOCAL_REPLAYED`, `WP-F9.7-06=COMPLETED_LOCAL_MERGED`, `PR-O-F9.7-PRIVATE-EXECUTOR-002=CERTIFIED_LOCAL_PR_O_SUCCESSOR`, candidate final `258ef3a98c7c1010efe58522bb1eca892e26390e` / tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de`, merge `e95eeaccc864477db587bbb13c827d0c17340d8d`, reconciliacion documental fusionada `desarrollo@fdaac633d29476e3323a8f88741a87570ece3b7c` / tree `2fa573d878eb566dd00f6fe21939e5b6420133ed`, PR #263 `778267948fc3461987a41dc9184b151c9ff19243` / tree `4e6609926ea6f4a3342cac43e71307fd5cd24aba`, certificacion local `771b8b1366e302eae52e4263577e0f6967679d7b` / tree `99f315c6820966e94213665df43cd21f9f4ef730`, evidencia final `issuecomment-5133103661`, approval `romelhc95-approver`, replay post-merge Docker/Linux PASS, candidates `b711e0b`/`249295`, `120d234`/`bf68ed` y `d2cb32e`/`16081a60` no promocionables, dos `SC2086` legacy `RESIDUAL_ACCEPTED_PROTECTED_BASELINE`, T02 `NOT_EXECUTED`, backup `PLANNED`, writers `INVENTORIED`, Free/Pro `UNCHANGED_NOT_ATTESTED`, Supabase previews skipped y `AUTOMATIC_PR_PREVIEW_ACCEPTED` sin Cloudflare manual. La captura publica no puede reactivarse por configuracion; cualquier reactivacion vive en [BK-F9.5-05](backlog_seguridad_leads_email.md).

### Work Packages De Cierre F9.7

El contrato PLAN-F9.7-CIERRE-001 queda como antecedente no incluido en el
candidate CA1-only. La siguiente tabla preserva su resultado historico; la
autoridad viva permanece en el encabezado de esta tarea y en
`estado_del_proyecto.md`:

| Work package | Estado | Resultado requerido |
|---|---|---|
| `WP-F9.7-01` | `COMPLETED` | Contrato, inventario y gobierno congelados en checkpoint documental local |
| `WP-F9.7-02` | `COMPLETED` | Security hold DB con acceso cero y matriz PostgreSQL 17 en `GO_WP` local |
| `WP-F9.7-03` | `COMPLETED` | Frontend no-leads, accesibilidad y egress en `GO_WP` |
| `WP-F9.7-04` | `COMPLETED_LOCAL_MERGED` | `CORR-WP-F9.7-04-02` cerro actionlint/ShellCheck parity y commit-mode read-only; CI verde sobre `258ef3a` |
| `WP-F9.7-05` | `COMPLETED_LOCAL_REPLAYED` | Tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de` materializado en Docker/Linux limpio; matriz post-merge canonica PASS sobre merge `e95eeac` |
| `WP-F9.7-06` | `COMPLETED_LOCAL_MERGED` | Seis auditorias finales `GO_FOR_LOCAL_PR`, `BLOCKING_IN_SCOPE=0`, evidencia final `issuecomment-5133103661`, aprobacion humana y merge PR #258 |

Decisiones vinculantes historicas: todos los roles de aplicacion, incluido `service_role`, quedan sin acceso a `leads`/`email_log` en el package local; la publishable key historica retirada tiene estado `ROTATED_HUMAN_ATTESTED`, sin registrar su valor. [PR-O v1](../../operaciones/pr_o_f9_7_v3_hold.md) y el hold actual quedan `SUPERSEDED_NON_PROMOTABLE`; [PR-O executor privado](../../operaciones/pr_o_f9_7_successor_private_executor.md) queda certificado localmente como `CERTIFIED_LOCAL_PR_O_SUCCESSOR` con executor privado no expuesto por Data API, eliminacion de `public.exec_sql(text)` del estado final esperado, digests vinculantes y approvals single-use. Esa ruta queda superseded para Hito 1 por el rebaseline CA1-only y no autoriza Supabase Free/Pro, DDL/DML remoto en Free/Pro, backup, writers, backfill, Edge, deploy ni Cloudflare manual.

Hold operativo posterior: `USER_PERSONAL_UAT` pertenece a F9.10 como hold manual de experiencia personal del usuario, no como criterio contractual, subtarea, subfase ni transicion de la maquina. Debe ejecutarse despues de canary, validaciones tecnicas Certification y QA, y antes de declarar readiness para F10; exige candidate commit/tree inmutable y `PASS` personal explicito del usuario.

El backlog sin implementacion de policies, canary, hardening, inventarios y limpieza F11 se registra en [Backlog F9.5](backlog_f9_5_known_findings.md). El cierre H-00 y la definicion de F9.7 viven en la macrofase F9.

## Frontera F9.8 CA1-Only

### Permitido

- FG1 como soporte operativo.
- FG2 y FG3 como alcance CA1.
- Schedules, gates, circuit breakers, limites, timeouts y seguridad operacional.
- Tests, CI y evidencia necesarios para CA1.
- Documentos canonicos enlazados desde [el indice](../../00_INDICE.md).

### Prohibido

- `db/**`, `supabase/**` y `web/**`.
- Schema, migrations, RLS, RPC, grants y backfill.
- Leads/email, Edge y artifacts terminales F9.7.
- Admin, Home, Resultados, cards, filtros y campos CA2.
- Tooling para aplicar packages DB.

Esta frontera no autoriza redisenos fuera de estas superficies.

La allowlist ejecutada del alias historico `FASE-09` vive exclusivamente en [Precertificacion F9](../../operaciones/precertificacion_hito1_f9.md#allowlist-f9) y corresponde a F9.1.

La allowlist ejecutada del alias historico `FASE-10` vive exclusivamente en [Contrato de promocion F10](../../operaciones/promocion_hito1_f10.md#allowlist-f10) y corresponde a F9.2. Las siguientes subfases usan allowlists propias.

## Cierre F9.8 - Candidate Local CA1-Only

F9.8 termina `COMPLETED_VERIFIED_POST_MERGE`. El candidate CA1-only implementado
por PR #270 y PR #271 quedo fusionado en `desarrollo@5b282461149b7319685cf090534e28051e5eb32c`
y replay-validado en Docker/Linux (contenedor `studiamatch-dev`, checkout limpio).

- Diff `638c51c..M` = 2 paths de CI, cero paths CA2.
- `EVID-H1-002..005` quedan `VERIFIED`; `EVID-H1-006..016` permanecen `PLANNED`.
- 53 pruebas focused F9.8 PASS; focused FG1/FG2/FG3 y jobs CI PASS; F9.7
  congelado 226+7 PASS; runners PostgreSQL 17 PASS; actionlint/ShellCheck
  0 issues; LF y credential scan PASS; Context Graph PASS.
- Cero red remota, DDL/DML, backfill, Certification, canary, schedules ni
  Production. Free/Pro permanecen `UNCHANGED_NOT_ATTESTED`.
- F9.9 queda como subfase activa; su ejecucion requiere la frase exacta
  `Ejecuta las tareas pendientes de la Fase F9.9`.

## Desviacion F9.9 - Certification Fail-Closed

F9.9 documento la promocion selectiva a `certificacion` y la desviacion aceptada
en [ADR-0007](../../decisiones/ADR-0007_desviacion_canary_certification_f9_9.md):

- PR #277 fue aprobado y fusionado en `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17`.
- `EVID-H1-006=VERIFIED` por equivalencia/boundary selectivo y CI `security-audit` PASS.
- `EVID-H1-007=VERIFIED` por PR #277 `APPROVED/MERGED`.
- `EVID-H1-008=DEVIATION_ACCEPTED_FAIL_CLOSED`: los canaries Certification observaron salida no cero ante inventario invalido o HTTP 403 observado desde GitHub-hosted runners; cleanup e idempotencia pasaron cuando hubo snapshot.
- La desviacion no es `PASS` y no valida FG2 downstream, FG3 ni success path.
- `EVID-H1-009=VERIFIED` y `EVID-H1-014=VERIFIED_POST_MERGE_BOUNDARY` quedan registrados posteriormente por F10.7; `EVID-H1-015=VERIFIED`; en ese corte `EVID-H1-010..013/016` permanecian pendientes.
- La definicion QA F9.9 vive en [QA-F9.9-DEVIATION-001](../../operaciones/qa_desviacion_f9_9.md); el resultado sanitizado [QA-F9.9-DEVIATION-001-RESULT](../../operaciones/qa_desviacion_f9_9_resultado.md) verifica fail-closed sin declarar Certification PASS.
- F9.9 queda `COMPLETED_QA_VERIFIED`. F9.10 queda `COMPLETED_READINESS_F10` con boundary real `main -> certificacion`, candidate/readiness y `USER_PERSONAL_UAT=PASS`; F10 conserva el control-plane, entrega tecnica F10.7 a `main`, canary Production y observacion.

## Remediacion CI F10.7 Local Validada

F10.7 conserva `COMPLETED_TECHNICAL_DELIVERY`. La remediacion local corrigio el
contrato de prueba que bloqueaba PR #292 despues de la promocion tecnica de PR
#291. La entrega tecnica, su boundary, Cloudflare Pages `SUCCESS` y DB Sync
`CANCELLED_ZERO_STEPS` permanecen como evidencia registrada; esta remediacion no
los reabrio ni los sustituyo.

`tests/test_fase10_main_boundary.py` acepta ahora la topologia post-main en la
que `main@64e4ed895d43121c5683e26a355993f18e528a5c` tiene como padre a
`certificacion@1edc65aa848d32dabfa62aa60b53f4bff9b5716e` y conserva el tree
`7d43590c19ca15171d468bf8c823a5e93b47d8cc`, manteniendo la validacion del
boundary de 32 objetos y el fallback pre-main cuando aplique. Validacion local
Docker: `python3 -m pytest -q tests/test_fase09_10_pre_main_controls.py tests/test_fase10_main_boundary.py tests/test_fase10_production_canary.py` = 36 PASS.

Quedan expresamente prohibidos en esta remediacion: cambios de producto,
deployments, workflow dispatch, reruns manuales, Supabase Free/Pro, DDL/DML,
writers, schedules, Production canary, sincronizacion o modificacion de ramas
protegidas, y cambios en `.github/workflows/**` salvo que una validacion local
demuestre necesidad estricta y se solicite otra decision.

## F10.8 Reconciliacion Post-Main, DB Sync Y DDL Auth

F10.8 queda completada como `COMPLETED_PRODUCTION_CANARY_VERIFIED`; F10.9 queda
`STOP_REQUIRES_REBASELINE` en G4. G5-G13, habilitacion y observacion estan
suspendidos hasta una decision de autoridad superior fuera de F10.9.
La remediacion de Production Canary fue promovida por PR #297 y fusionada en
`main@260900a268ab8eb194140ea7311aec2a170b6e17`. La validacion previa al cierre
documental reconfirmo:

- PR #297 `MERGED`, merge commit `260900a268ab8eb194140ea7311aec2a170b6e17`.
- Certification Canary `31140933096=PASS` sobre
  `certificacion@94026de77fe9c1a01c66eae78bea8b09858daf96`.
- `security-audit`, `F10 Main Boundary`, Cloudflare Pages, Credential Scan,
  Python, ESLint y TypeScript en PASS para la promocion.
- Artifact `f9-9-certification-canary-manifests-31140933096-1` sanitizado: tres
  JSON, cohortes `redacted`, sin `institution_id`, hosts Supabase ni UUIDs en
  artifacts; conteos y gates `pre == post == after_cleanup`.
- `DB Sync to Production` run `31142826000=FAIL_CLOSED_PRE_SUPABASE`: el step
  report fallo antes de contactar Supabase porque el workflow ejecuto
  `db_migrate.py --manifest` en una version de `main` que no soporta esa opcion.
  `Apply pending migrations`, `Verify target schema` y `FG2 deferred to scheduled
  production window` quedaron skipped. No hubo DDL/DML, migrations, acceso
  Supabase, snapshot Production, writer ni mutacion DB.

La remediacion DB Sync fue ejecutada por la ruta protegida:

- PR #304 a `desarrollo`: `db0b35b804127ce4df2bf1c8a2668f764fe10d58`.
- PR #305 a `certificacion`: DB Sync remediation CI PASS.
- PR #306 a `certificacion`: main-boundary gate CI PASS.
- PR #307 a `main`: `529ca111f1fef40efb15676ad6f07d002a54ae92`.
- DB Sync post-main `31151066062=SUCCESS_NO_DB_CHANGES_SKIPPED`: solo corrio
  `Detect DB changes`; `DB contract preflight`, `Report pending migrations`,
  `Apply pending migrations`, `Verify target schema` y `FG2 deferred to scheduled
  production window` quedaron skipped por ausencia de cambios `db/**`.
- `Security Audit Gate` post-main `31151066061=PASS`.

La remediacion no ejecuto Supabase, DDL/DML, migrations, workflow dispatch
operativo, Production Canary, schedules, writers, backfill ni CA2. El run
historico `31142826000` no se reintento.

La remediacion cleansing provenance posterior siguio la ruta protegida:

- PR #319 a `certificacion`: `2a70dd001d8ded34d5ba67c19221f7f5e291d2c8`.
- PR #320 a `main`: `1885806f0d9f189600d410d353fcf13fb8dd4676`.
- DB Sync to Production `31243797695=SUCCESS_REPORT_ONLY`: report-only observo
  exactamente `20260808_fase10_8_atomic_cleansing_provenance` como migracion Pro
  pendiente; `Apply pending migrations`, `Verify target schema` y FG2 deferred
  quedaron skipped.
- El registro `DDL-F10_8_ATOMIC_CLEANSING_PROVENANCE_PRO` corrige el deadlock de
  SHA atando la autorizacion al base `1885806f0d9f189600d410d353fcf13fb8dd4676`
  y exige diff allowlisted, dispatch manual, approval `Production`, Backup/PITR
  runtime y writers pausados antes de un apply futuro.

Esta remediacion de gobierno no ejecuto Pro DDL, DML, Production Canary,
schedules, writers, backfill, secrets/environments ni CA2.

PR #323 y PR #324 promovieron verify-only hasta
`main@675ade43f41a2f5d04f05a40f9837b514a8705ce` / tree
`90868898778a1039006e45b870fbc03e6e65291b`. DB Sync verify
`31268229878=PASS` confirmo pending `0`, apply skipped, target schema PASS y FG2
deferred PASS. `USER_PERSONAL_UAT=PASS` fue emitido para ese SHA/tree. El
Production Canary `31269277219` completo FG1/FG2/FG3 y primer restore, pero fallo
fail-closed en el segundo restore `--expect-noop` por JSON truncado durante la
atestacion no-cohorte. La remediacion vigente no autoriza DDL/DML, backfill,
schedules, writers, secrets/environments ni CA2.

PR #325 promovio la remediacion de paginacion no-cohorte a
`main@859d2f7d83f83950d10858fe27bd035febba7f68` / tree
`ba7f6e74e88b2153aef1f4582bb3faa999c01a98`. DB Sync post-merge
`31271765282=SUCCESS_NO_DB_CHANGES_SKIPPED` corrio solo `Detect DB changes`;
Security Audit post-merge `31271765308=PASS`. Production Canary
`31272290614=PASS` completo FG1/FG2/FG3, restore exacto, segundo restore NOOP,
after-cleanup y upload de seis manifests sanitizados en artifact `9026139906`.

`EVID-H1-010=VERIFIED`; `EVID-H1-011..013` y `EVID-H1-016` permanecen
pendientes. Hito 1 queda `TECHNICALLY_DELIVERED_FORMAL_CLOSURE_PENDING`, no
`COMPLETED_PRODUCTION`.

La observacion global posterior se conserva como evidencia fail-closed en
[EVID-H1-OBS-F10.9-001](../../evidencias_cliente/sprint_1/registro_observacion_production_f10_9_2026-08-09.md): cero pares aceptados, ventana 72h no iniciada y
remediacion requerida. Este registro no modifica la verificacion F10.8 ni
autoriza operaciones remotas.

## Exclusiones Historicas Preservadas

- Vault historico, revisiones, evidencias y candidates previos.
- Manifest schema v1, dispatcher autonomo y diffs completos de ramas historicas.
- Mutacion de migrations o ledgers existentes.
- Copia de datos operativos Free hacia Pro.
- H-08 y H-09; redisenos definitivos de H-04 y H-07.

## Dependencia G1b Minima Historica

- El paquete minimo conserva los IDs `H-01` a `H-07` y `H-10` sin publicar postcondiciones explotables.
- F7 mapeo postcondiciones a `H1-CA2P` como antecedente historico; Hito 2 debe producir evidencia nueva para `H2-CA2`.
- La adopcion vigente se decide desde `estado_del_proyecto.md` y evidencia nueva;
  la [matriz DB](../../operaciones/matriz_adopcion_db.md) es referencia historica
  pre-F10.8 y no concede adopcion.
- El frontend debe ser compatible con las superficies que el contrato aprobado retire.

H-00 no forma parte del paquete promocionable. F9.6 verifico la remediacion historica de PII directa y la conservacion pseudonimizada, y cerro sin DML como `H00_ALREADY_REMEDIATED_NO_DML`; nunca se aplica en Pro.

## Criterio De Salida

1. `EVID-H1-001..016` completos, con `EVID-H1-001` ya verificado y las demas evidencias generadas por candidate/ambientes/observacion/conformidad.
2. Candidate CA1-only inmutable con cero cambios `db/**`, `supabase/**`, `web/**`, leads/email, Edge, backfill, admin, Home, Resultados, cards, filtros y campos CA2.
3. Tests CA1, CI, seguridad, QA, desviacion Certification aceptada o canary Certification positivo, `USER_PERSONAL_UAT`, readiness F10, canary Production y observacion en estado aprobado segun [PLAN-H1-CA1-ONLY-001](../../operaciones/plan_cierre_hito1_ca1_only.md).
4. Hitos 2 a 5 permanecen `PENDING` hasta activacion individual.

Ver [Arquitectura](../../arquitectura_pipeline.md), [Estimacion](../../estimaciones/est_001.md) y [Release minimo](../../operaciones/flujo_release_minimo.md).
