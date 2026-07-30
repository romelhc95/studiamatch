# TASK-H1-001 - HITO-001

| Campo | Valor |
|---|---|
| ID | `TASK-H1-001` |
| Estado | `IN_PROGRESS` |
| Requerimiento | `REQ-EST-001` |
| Hito | [HITO-001](../../hitos/hito_001.md) |
| Fase vigente | Macrofase `F9` en progreso; [PLAN-F9.7-CIERRE-001](../../operaciones/cierre_definitivo_f9_7.md) divide el corte local en seis work packages; PR #258 cerro localmente `CORR-WP-F9.7-04-02` y `WP-F9.7-04..06` con candidate `258ef3a98c7c1010efe58522bb1eca892e26390e`, tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de`, seis auditorias `GO_FOR_LOCAL_PR`, aprobacion humana, merge `e95eeaccc864477db587bbb13c827d0c17340d8d` y replay post-merge PASS; PR #259 reconcilio el replay y fue fusionado en `desarrollo@fdaac633d29476e3323a8f88741a87570ece3b7c` con tree `2fa573d878eb566dd00f6fe21939e5b6420133ed`; candidates `b711e0b`/`249295`, `120d234`/`bf68ed` y `d2cb32e`/`16081a60` quedan no promocionables; frontend sin leads, Edge tombstone Git-only, security hold terminal `LOCAL_CANDIDATE_BLOCKED` y Free/Pro `UNCHANGED_NOT_ATTESTED`; F9.7 permanece `IN_PROGRESS` hasta `GO_F9.7_COMPLETE` en Free |
| Criterios | `H1-CA1`, `H1-CA2P`, `H1-CA7P` |

Esta nota es la autoridad exclusiva del estado vivo de `TASK-H1-001` y de sus criterios. La tarea no tiene subtareas. Los IDs `WP-F9.7-*` son unidades operativas internas de F9.7 y no agregan criterios, subfases ni autorizaciones.

El [seguimiento detallado de Hito 1](./seguimiento_detallado_hito_1.md) es una vista `TRACKING_ONLY`: organiza work items y evidencia sin crear subtareas, criterios, alcance ni autoridad de estado paralela.

## Objetivo Contractual

Preparar la orquestacion FG2/FG3, el schema editorial y de calidad, y la seguridad base sin saltar gates, exponer credenciales ni promover cambios no certificados.

## Arbol De Criterios

```text
TASK-H1-001
|- H1-CA1
|- H1-CA2P
`- H1-CA7P
```

Los tres criterios son hijos directos de la tarea, no subtareas.

## Criterios Y Entregables

| Criterio | Estado contractual | Base implementada o aceptada | Pendiente para certificacion |
|---|---|---|---|
| `H1-CA1` | `IMPLEMENTED` | Workflows automaticos, schedules, gates y circuit breakers de F7 | Compatibilidad backend y ejecucion efectiva por ambiente |
| `H1-CA2P` | `IN_PROGRESS` | Schema local F6-F8, calidad y seguridad base | Aplicacion Free/Pro, identidad backend de servicio, backfill editorial y pruebas por rol |
| `H1-CA7P` | `COMPLETED` | Contrato documentado, Context Graph y `SRC-REQ-001` reconciliada | Anexo final por ambiente para la certificacion; no reabre el criterio |

El alcance contractual de los tres criterios permanece en [REQ-EST-001](./_index.md) y [HITO-001](../../hitos/hito_001.md). [EST-001](../../estimaciones/est_001.md) conserva solo complejidad y estimacion tecnica original; esta tabla no agrega criterios.

## Equivalencias Aceptadas De H1-CA2P

Las siguientes equivalencias semanticas quedan aceptadas para el alcance de `H1-CA2P`; no acreditan adopcion remota, no sustituyen las pruebas por rol y no autorizan schema, migrations ni backfill:

| Necesidad contractual | Campo local aceptado |
|---|---|
| Faltantes | `missing_fields` JSONB |
| Fuentes de campo | `field_sources` JSONB |
| Actualizacion manual | `manual_updated_at` |
| Inicio | `start_date` |

## Contexto Verificable

El baseline de workflows debe contrastarse con `H1-CA1`; los comentarios no sustituyen la configuracion ejecutable. La modalidad aprobada es cadencia automatica con gates, circuit breakers y controles de ambiente.

Los nombres, adopcion Free/Pro y postcondiciones exactas se fijan en [Sistema DB](../../sistema_db_supabase.md) y [Matriz DB](../../operaciones/matriz_adopcion_db.md). No se editan ledgers historicos.

El candidate DB-as-Code vigente se registra en [Reconciliacion F6](../../operaciones/reconciliacion_db_as_code_f6.md). PR #223 incorporo el package a `desarrollo` y PR #224 cerro su portabilidad LF/CRLF. La existencia del candidate no prueba adopcion remota ni completa `H1-CA2P` antes de certificacion.

F8 agrego una closure forward-only y certificacion local reproducible documentadas en [Certificacion local Hito 1 F8](../../operaciones/certificacion_hito1_f8.md). PR #228 fue fusionado y validado post-merge. El resultado local no habilita Free/Pro ni autoriza el backfill editorial.

El package historico `FASE-09`, ahora mapeado a F9.1, se limita a [precertificacion local H1-CA2P](../../operaciones/precertificacion_hito1_f9.md): package real en PostgreSQL efimero, rollback, replay del contrato F8, ledger paginado y reconciliacion de nomenclatura fail-fast. No completa este criterio ni autoriza acceso remoto.

F9.1 conserva byte-identicos el manifest y las migrations F8. PR #231 y la remediacion CRLF #232 fueron fusionados y validados post-merge; status/targets no cambian.

El package historico `FASE-10`, ahora mapeado a F9.2, se limita al [contrato local de promocion](../../operaciones/promocion_hito1_f10.md): reemplaza prerrequisitos universales por evidencia por transicion y crea un descriptor sucesor bloqueado. No modifica el candidate F8, no cambia status y no accede a ambientes remotos.

F9.2 conserva F8 byte-identico y valida neutralmente estructuras de attestations sin conceder estado/capability. PR #235 fue aprobado, fusionado y validado post-merge sobre `desarrollo@d67fa31`; su ruta operacional historica no otorgo attestations ni transiciones de estado. F9.1/F9.2 no completan la [macrofase F9](../../operaciones/certificacion_hito1_f9.md) ni `H1-CA2P`; F10 Produccion y F11 Cierre siguen pendientes.

F9.3 fue autorizada mediante la frase decimal exacta y congelo un contrato exclusivamente local: descriptor inmutable, catalogos read-only cerrados, target binding no reversible, schemas neutrales para la F9.4 entonces prevista, runner sin transportes y job CI sin secrets. PR #238 fue aprobado y fusionado; el replay detecto una incompatibilidad del fixture con CRLF del bind mount Windows, remediada y fusionada mediante PR #239. `desarrollo@4e77fe0` repitio desde un checkout Linux limpio dentro de Docker 55 pruebas focused, 253 de regresion, 22 checks sinteticos, Python compile y Context Graph en PASS. No hubo acceso Free/Pro ni cambio de estado. Al cerrar F9.3, F9.4 aun no estaba autorizada; ADR-0004 sustituyo despues esa ruta.

F9.4 adopta [PLAN-H1-SIMPLIFICADO-001](../../operaciones/plan_simplificado_hito1.md) mediante [ADR-0004](../../decisiones/ADR-0004_simplificacion_contractual_hito1.md). Fue exclusivamente local/documental: reconcilio el Context Graph, convirtio la [definicion remota anterior](../../operaciones/preflight_free_f9_4.md) en `SUPERSEDED_NON_AUTHORIZABLE`, preservo el antecedente temporal y lo retiro. No accedio a Free/Pro, no cargo secrets, no creo T01 y no ejecuto DDL, DML, migrations, H-00, backfill, pausa de writers ni workflows remotos. `H1-CA2P` permanece `IN_PROGRESS`.

## Cierre Contractual F9.5

F9.5 termina `COMPLETED_WITH_KNOWN_FINDINGS`. Los intentos y remediaciones locales anteriores se preservan en el [registro historico F9.5](../../operaciones/preflight_free_f9_5.md), pero no justifican una nueva lectura Free ni certifican Free o Pro.

- Todos los artifacts F9.5 introducidos por PR #245 y PR #247 quedan `HISTORICAL_NON_PROMOTABLE`. Se conservan fisicamente para trazabilidad, sin integrarlos al package contractual, a F9.7 ni a una ruta de aplicacion.
- F6-F8 permanecen como la unica base funcional contractual de Hito 1. Los artifacts F9.5 no sustituyen, amplian ni promocionan esa base.
- Al cerrar F9.5, `T01_CONDITIONAL_ACCEPTED` fue una decision documental sin attestation tecnica nueva y habilito solo la definicion entonces futura de F9.6; nunca autorizo schema, migrations, F9.7 ni ramas.
- `H-00` es un P0 separado y obligatorio antes de `FREE_CERTIFIED`, pero no es un criterio contractual de `HITO-001`.
- La definicion inicial F9.6 exigia backup y predicado antes de una posible eliminacion. Esa rama quedo sustituida al cerrar F9.6 sin DML despues de verificar la remediacion historica de PII directa; los intentos de backup no se reclasifican como PASS.

## Cierre F9.6 - H-00 Ya Remediado

F9.6 termina `COMPLETED` con resultado `H00_ALREADY_REMEDIATED_NO_DML`. La verificacion sanitizada [EVID-F9.6-H00-001](../../operaciones/cierre_h00_f9_6.md) confirmo la cohorte con remediacion completa de PII directa y sin coincidencias parciales o invalidas. Seguridad y calidad de datos revisaron la cadena de evidencia en GO.

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

[EVID-F9.7-GATE-B-001](../../operaciones/gate_b_f9_7.md) ejecuto Gate B con una consulta Free agregada y termino `FREE_GATE_B_FAIL_STOPPED_READ_ONLY`: el boundary candidate vacio fue permitido, pero el acceso de superficies protegidas activo stop conditions. El runner HTTP y las aprobaciones separadas de resguardo/restore y pausa quedaron `NOT_SUBMITTED_BLOCKED_BY_GATE_B_FAIL`; writers, DDL/DML, Pro y backfill permanecieron en cero.

La [definicion de remediacion](../../operaciones/remediacion_gate_b_f9_7.md) congela el mismo package de cinco entradas, rollback/postcondiciones y runbooks no ejecutables. La [atestacion ACL](../../operaciones/atestacion_origen_acl_f9_7.md) observo cobertura completa del package para fuentes ACL, sin herencia/SET/owner/unknown; el mismatch y el trigger mantuvieron fail-closed y los predicates no atestados bloquearon aplicacion independientemente. No hubo filas de negocio, HTTP, schema, migrations, DML, backup, restore ni control de writers.

La [remediacion local del trigger](../../operaciones/remediacion_trigger_f9_7.md) reemplazo el draft suplementario no confirmado por un manifest sucesor v3 de seis entradas. Las cinco migrations historicas quedan byte-identicas; v2 queda como antecedente historico no promocionable; la sexta elimina de forma fail-closed `trg_notify_new_lead` y `public.notify_new_lead()` sin `CASCADE`, el Edge Function historico queda tombstoneado en Git y el drenaje pg_net queda counts-only. [ADR-0005](../../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md) agrega el corte local: la arquitectura leads/email queda `DEFERRED_NO_IMPLEMENTATION`, el frontend soportado no tiene captura publica y el package terminal [security hold](../../operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md#package-terminal-de-security-hold) queda `LOCAL_CANDIDATE_BLOCKED` como successor separado posterior a v3. No observa ni modifica Free/Pro y no autoriza aplicacion.

El backfill editorial es dependencia de `H1-CA2P` para F9.8/F9.9: debe planificarse y ejecutarse separadamente para evitar que el catalogo quede invisible. No esta autorizado por el candidate local ni por Gate B.

Estado del corte local: `public_lead_capture=LOCAL_CODE_REMOVED_REMOTE_UNKNOWN`, `email_egress=LOCAL_TOMBSTONE_REMOTE_UNKNOWN`, `security_hold=LOCAL_CANDIDATE_BLOCKED`, `WP-F9.7-02=GO_WP_LOCAL`, `WP-F9.7-03=GO_WP_LOCAL`, `WP-F9.7-04=COMPLETED_LOCAL_MERGED`, `CORR-WP-F9.7-04-01=NO_GO_CI_PARTIAL`, `CORR-WP-F9.7-04-02=COMPLETED_LOCAL_MERGED`, `WP-F9.7-05=COMPLETED_LOCAL_REPLAYED`, `WP-F9.7-06=COMPLETED_LOCAL_MERGED`, candidate final `258ef3a98c7c1010efe58522bb1eca892e26390e` / tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de`, merge `e95eeaccc864477db587bbb13c827d0c17340d8d`, reconciliacion documental fusionada `desarrollo@fdaac633d29476e3323a8f88741a87570ece3b7c` / tree `2fa573d878eb566dd00f6fe21939e5b6420133ed`, evidencia final [issuecomment-5133103661](https://github.com/romelhc95/studiamatch/pull/258#issuecomment-5133103661), approval `romelhc95-approver`, replay post-merge Docker/Linux PASS, candidates `b711e0b`/`249295`, `120d234`/`bf68ed` y `d2cb32e`/`16081a60` no promocionables, dos `SC2086` legacy `RESIDUAL_ACCEPTED_PROTECTED_BASELINE`, T02 `NOT_EXECUTED`, backup `PLANNED`, writers `INVENTORIED`, Free/Pro `UNCHANGED_NOT_ATTESTED`, Supabase previews skipped y `AUTOMATIC_PR_PREVIEW_ACCEPTED` sin Cloudflare manual. La captura publica no puede reactivarse por configuracion; cualquier reactivacion vive en [BK-F9.5-05](backlog_seguridad_leads_email.md).

### Work Packages De Cierre F9.7

El contrato, dependencias y criterios completos viven en [PLAN-F9.7-CIERRE-001](../../operaciones/cierre_definitivo_f9_7.md). Esta tabla es la autoridad viva de su avance:

| Work package | Estado | Resultado requerido |
|---|---|---|
| `WP-F9.7-01` | `COMPLETED` | Contrato, inventario y gobierno congelados en checkpoint documental local |
| `WP-F9.7-02` | `COMPLETED` | Security hold DB con acceso cero y matriz PostgreSQL 17 en `GO_WP` local |
| `WP-F9.7-03` | `COMPLETED` | Frontend no-leads, accesibilidad y egress en `GO_WP` |
| `WP-F9.7-04` | `COMPLETED_LOCAL_MERGED` | `CORR-WP-F9.7-04-02` cerro actionlint/ShellCheck parity y commit-mode read-only; CI verde sobre `258ef3a` |
| `WP-F9.7-05` | `COMPLETED_LOCAL_REPLAYED` | Tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de` materializado en Docker/Linux limpio; matriz post-merge canonica PASS sobre merge `e95eeac` |
| `WP-F9.7-06` | `COMPLETED_LOCAL_MERGED` | Seis auditorias finales `GO_FOR_LOCAL_PR`, `BLOCKING_IN_SCOPE=0`, evidencia final `issuecomment-5133103661`, aprobacion humana y merge PR #258 |

Decisiones vinculantes: todos los roles de aplicacion, incluido `service_role`, quedan sin acceso a `leads`/`email_log` en el package local; la publishable key historica retirada tiene estado `ROTATED_HUMAN_ATTESTED`, sin registrar su valor. Siguiente accion exacta: `definicion de PR-O combinado v3 + hold`. Esta reconciliacion no implementa ni aplica PR-O y no autoriza Supabase Free/Pro, DDL/DML remoto en Free/Pro, backup, writers, backfill, deploy ni Cloudflare manual.

El backlog sin implementacion de policies, canary, hardening, inventarios y limpieza F11 se registra en [Backlog F9.5](backlog_f9_5_known_findings.md). El cierre H-00 y la definicion de F9.7 viven en la [macrofase F9](../../operaciones/certificacion_hito1_f9.md).

## Allowlist De Implementacion

- `scripts/core/master_orchestrator.py`.
- `scripts/core/cleansing_worker.py`, `enrichment_worker.py` y `sync_vector_worker.py` para compatibilidad G1b minima.
- Frontend de detalle, comparador, catalogo y selector publico para retirar superficies G1b revocadas.
- Workflows FG1 y FG3; FG2 solo para revision contractual y el guard de refs aprobado explicitamente.
- Workflow de seguridad para convertir pruebas y build F7 en gates bloqueantes.
- `scripts/shared/db_client.py` y `check_db_parity.py` solo para lecturas fail-closed y revalidacion F7.
- Migrations forward-only nuevas para el contrato editorial, calidad y RLS.
- Tests de governance, gates del orquestador y RLS.
- Documentos canonicos enlazados desde [el indice](../../00_INDICE.md).

La ampliacion minima de allowlist anterior fue aprobada explicitamente al iniciar F7. El guard FG2 se aprobo despues como remediacion de seguridad acotada. No autoriza redisenos fuera de estas superficies.

La allowlist ejecutada del alias historico `FASE-09` vive exclusivamente en [Precertificacion F9](../../operaciones/precertificacion_hito1_f9.md#allowlist-f9) y corresponde a F9.1.

La allowlist ejecutada del alias historico `FASE-10` vive exclusivamente en [Contrato de promocion F10](../../operaciones/promocion_hito1_f10.md#allowlist-f10) y corresponde a F9.2. Las siguientes subfases usan allowlists propias.

## Exclusiones

- Vault historico, revisiones, evidencias y candidates previos.
- Manifest schema v1, dispatcher autonomo y diffs completos de ramas historicas.
- Mutacion de migrations o ledgers existentes.
- Copia de datos operativos Free hacia Pro.
- H-08 y H-09; redisenos definitivos de H-04 y H-07.

## Dependencia G1b Minima

- El paquete minimo conserva los IDs `H-01` a `H-07` y `H-10` sin publicar postcondiciones explotables.
- F7 debe mapear cada postcondicion a `H1-CA2P`, un metodo de verificacion y evidencia nueva.
- La adopcion se decide desde la [matriz DB](../../operaciones/matriz_adopcion_db.md), no desde evidencia historica.
- El frontend debe ser compatible con las superficies que el contrato aprobado retire.

H-00 no forma parte del paquete promocionable. F9.6 verifico la remediacion historica de PII directa y la conservacion pseudonimizada, y cerro sin DML como `H00_ALREADY_REMEDIATED_NO_DML`; nunca se aplica en Pro.

## Criterio De Salida

1. Cambios clasificados y limitados a la allowlist.
2. Migrations nuevas, forward-only e idempotentes.
3. Tests de gates, governance y RLS verdes en el entorno autorizado.
4. FG1/FG3 conservan o ajustan su cadencia automatica sin omitir gates, circuit breakers ni controles de ambiente.
5. FG2 conserva credenciales fuera del repositorio y respeta gates.
6. Frontend pasa lint, typecheck y build estatico segun el gate acordado.
7. Candidate inmutable, Context Graph PASS y aprobacion humana antes de promocion.

Ver [Arquitectura](../../arquitectura_pipeline.md), [Estimacion](../../estimaciones/est_001.md) y [Release minimo](../../operaciones/flujo_release_minimo.md).
