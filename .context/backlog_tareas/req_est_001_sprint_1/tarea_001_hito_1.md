# TASK-H1-001 - HITO-001

| Campo | Valor |
|---|---|
| ID | `TASK-H1-001` |
| Estado | `IN_PROGRESS` |
| Requerimiento | `REQ-EST-001` |
| Hito | [HITO-001](../../hitos/hito_001.md) |
| Fase vigente | Macrofase `F9` en progreso; remediacion RLS local validada y repeticion F9.5 read-only pendiente de reautorizacion |
| Criterios | `H1-CA1`, `H1-CA2P`, `H1-CA7P` |

Esta nota es la autoridad exclusiva del estado vivo de `TASK-H1-001` y de sus criterios. La tarea no tiene subtareas.

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

| Criterio | Entregable | Verificacion | Evidencia | Estado |
|---|---|---|---|---|
| `H1-CA1` | Workflows automaticos y gates | Contrato F7 | PR #226, CI y validacion post-merge | Completed |
| `H1-CA2P` | Schema/RLS | Verificadores locales F6-F10 + PostgreSQL 17 | F9.1/F9.2 cerradas; package bloqueado hasta certificacion Free | `IN_PROGRESS` |
| `H1-CA7P` | Contrato documentado | Context Graph + reconciliacion | PR #221, CI y `SRC-REQ-001` reconciliada | Completed |

El alcance contractual de los tres criterios permanece en [REQ-EST-001](./_index.md) y [HITO-001](../../hitos/hito_001.md). [EST-001](../../estimaciones/est_001.md) conserva solo complejidad y estimacion tecnica original; esta tabla no agrega criterios.

## Contexto Verificable

El baseline de workflows debe contrastarse con `H1-CA1`; los comentarios no sustituyen la configuracion ejecutable. La modalidad aprobada es cadencia automatica con gates, circuit breakers y controles de ambiente.

Los nombres, adopcion Free/Pro y postcondiciones exactas se fijan en [Sistema DB](../../sistema_db_supabase.md) y [Matriz DB](../../operaciones/matriz_adopcion_db.md). No se editan ledgers historicos.

El candidate DB-as-Code vigente se registra en [Reconciliacion F6](../../operaciones/reconciliacion_db_as_code_f6.md). PR #223 incorporo el package a `desarrollo` y PR #224 cerro su portabilidad LF/CRLF. La existencia del candidate no prueba adopcion remota ni completa `H1-CA2P` antes de certificacion.

F8 agrego una closure forward-only y certificacion local reproducible documentadas en [Certificacion local Hito 1 F8](../../operaciones/certificacion_hito1_f8.md). PR #228 fue fusionado y validado post-merge. El resultado local no habilita Free/Pro ni autoriza el backfill editorial.

El package historico `FASE-09`, ahora mapeado a F9.1, se limita a [precertificacion local H1-CA2P](../../operaciones/precertificacion_hito1_f9.md): package real en PostgreSQL efimero, rollback, replay del contrato F8, ledger paginado y reconciliacion de nomenclatura fail-fast. No completa este criterio ni autoriza acceso remoto.

F9.1 conserva byte-identicos el manifest y las migrations F8. PR #231 y la remediacion CRLF #232 fueron fusionados y validados post-merge; status/targets no cambian.

El package historico `FASE-10`, ahora mapeado a F9.2, se limita al [contrato local de promocion](../../operaciones/promocion_hito1_f10.md): reemplaza prerrequisitos universales por evidencia por transicion y crea un descriptor sucesor bloqueado. No modifica el candidate F8, no cambia status y no accede a ambientes remotos.

F9.2 conserva F8 byte-identico y valida neutralmente estructuras de attestations sin conceder estado/capability. PR #235 fue aprobado, fusionado y validado post-merge sobre `desarrollo@d67fa31`; la ruta operacional permanece en cero attestations/status transitions hasta F9.5. F9.1/F9.2 no completan la [macrofase F9](../../operaciones/certificacion_hito1_f9.md) ni `H1-CA2P`; F10 Produccion y F11 Cierre siguen pendientes.

F9.3 fue autorizada mediante la frase decimal exacta y congelo un contrato exclusivamente local: descriptor inmutable, catalogos read-only cerrados, target binding no reversible, schemas neutrales para la F9.4 entonces prevista, runner sin transportes y job CI sin secrets. PR #238 fue aprobado y fusionado; el replay detecto una incompatibilidad del fixture con CRLF del bind mount Windows, remediada y fusionada mediante PR #239. `desarrollo@4e77fe0` repitio desde un checkout Linux limpio dentro de Docker 55 pruebas focused, 253 de regresion, 22 checks sinteticos, Python compile y Context Graph en PASS. No hubo acceso Free/Pro ni cambio de estado. Al cerrar F9.3, F9.4 aun no estaba autorizada; ADR-0004 sustituyo despues esa ruta.

F9.4 adopta [PLAN-H1-SIMPLIFICADO-001](../../operaciones/plan_simplificado_hito1.md) mediante [ADR-0004](../../decisiones/ADR-0004_simplificacion_contractual_hito1.md). Fue exclusivamente local/documental: reconcilio el Context Graph, convirtio la [definicion remota anterior](../../operaciones/preflight_free_f9_4.md) en `SUPERSEDED_NON_AUTHORIZABLE`, preservo el antecedente temporal y lo retiro. No accedio a Free/Pro, no cargo secrets, no creo T01 y no ejecuto DDL, DML, migrations, H-00, backfill, pausa de writers ni workflows remotos. `H1-CA2P` permanece `IN_PROGRESS`.

## Definicion Autorizable F9.5

La definicion cerrada de herramientas, candidate, evidencia y stop conditions vive en [Preflight Free F9.5](../../operaciones/preflight_free_f9_5.md).

- Identidad: F9.5 `REMOTE_READ_FREE_DIRECTED`.
- Estado: `PENDING_REAUTHORIZATION`; autorizacion vigente: ninguna. La remediacion local forward-only se consume con el merge de esta reconciliacion.
- Resultado remoto: los `FREE_PREFLIGHT_FAIL` previos permanecen historicos; T01 no fue creada ni aceptada.
- Target: Free unicamente. Pro, DDL, DML, migrations, H-00, backfill, pausa/reanudacion de writers, dispatch y produccion quedan prohibidos.

F9.5 inspecciona las cinco migrations exactas del overlay sucesor: el prefijo byte-identico F8 mas la reconciliacion RLS canary. Revisa columnas, constraints e indices afectados; policies y ACL de `institutions`, `courses`, `leads`, `ratings`, `reviews` e `institution_site_profiles`; owner, `search_path`, modo y grants de RPC; conflictos previos; identidad inequivoca de Free; factibilidad de backup/writers sin ejecutarlos; y H-00 counts-only sin mostrar PII.

F9.5 usa exclusivamente la allowlist project-scoped y evidencia sanitizada de su definicion. No implementa adapter, OpenAPI root, advisor bridge, cross-plane binding, nonce one-shot, inventarios globales ni frameworks nuevos de attestations. Cualquier necesidad de escritura, privilegio adicional, dato raw, acceso Pro o cambio de alcance detiene la subfase.

El intento autorizado del `2026-07-26` verifico localmente 4/4 checksums de blobs Git del package F8 y se detuvo bajo el contrato previo porque no existia el predicado H-00 privado aprobado. No abrio sesion Free, no invoco tools Supabase, no emitio SQL y no inspecciono datos o catalogos; esa evidencia permanece intacta.

La remediacion local posterior reconcilia artifacts H-00 recuperados y adopta exclusivamente una cohorte completa derivada en DB con cutoff `2026-07-19T00:00:00Z`, sin UUID ni identidad individual. PASS exige solo cuatro conteos exactos: 3 leads totales, 3 pre-cutoff, 0 post-cutoff y 0 `email_log`. Cualquier otro shape o valor falla cerrado. Esta decision no acredita los conteos actuales de Free; tras el merge documental, repetir F9.5 requiere otra autorizacion exacta. F9.6 permanece bloqueada.

El segundo intento read-only verifico binding Free, 4/4 checksums locales, ausencia de las cuatro entradas exactas sin colision, 13/13 columnas, 11/11 constraints y 9/9 indices compatibles. La inspeccion RLS encontro 5/5 tablas protegidas, 7/7 policies esperadas presentes, 6/7 compatibles, 3 policies publicas adicionales y 4/4 policies `service_role` compatibles. Como el package no elimina las tres adicionales y el verificador F8 las rechaza, la ejecucion termino `FREE_PREFLIGHT_FAIL` antes de ACL, RPC, conflictos de datos, H-00, backup o writers.

La remediacion forward-only crea `20260726_fase09_5_rls_canary_reconciliation.sql` y `fase09_5_rls_candidate.json`. Versiona los tres guards restrictivos canary, unifica profiles, restringe `institutions` a `id/name/slug`, fija owner `postgres`, rechaza bypass publico, exige `service_role BYPASSRLS`, cierra ACL/policies incluido `PUBLIC` y agrega una postcondicion sucesora con metadata cerrada. El manifest completo queda ligado por digest, conserva exactamente las cuatro entradas F8 y permanece bloqueado para ambos targets.

Las pruebas reproducen explicitamente una reconstruccion sintetica del baseline historico Free con efectos F8 presentes, ledger vacio y drift RLS previo. El planner real converge atomically en PostgreSQL 17 desde 0/5, 3/5 y 4/5; valida `INSERT` publico de leads limitado a las columnas de formulario, RLS por rol, membresias privilegiadas negativas, aislamiento canary separado por URL, profile e institucion, ACL y metadata exactas, rechazo de drift desconocido, rollback, replay y ledger de cinco entradas. El job CI exige PostgreSQL sin red y una prueba incremental del rechazo de egress IPv4 del proceso, bajo reglas IPv4/IPv6. El checksum sucesor es `4959b3f1ad60e2fe3a6e9a23161dd0467cfc549e10c1262ba8a0bb2aaf4c9a01` y el digest completo del manifest es `27af06a3411f65786d5dfbda19814c24b187f13a055a0fa4733698843f1d3353`. El descriptor F10/F9.2 permanece historico; F9.7 debera crear otro descriptor schema v2 para este overlay. La remediacion no accede a ambientes remotos, no crea T01 y no autoriza F9.6. Tras su merge, repetir F9.5 requiere otra autorizacion exacta.

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

H-00 no forma parte del paquete promocionable. Es DML Free-only, con autorizacion separada, respaldo remoto previo, counts-only y verificacion independiente antes de `FREE_CERTIFIED`. Nunca se aplica en Pro.

## Criterio De Salida

1. Cambios clasificados y limitados a la allowlist.
2. Migrations nuevas, forward-only e idempotentes.
3. Tests de gates, governance y RLS verdes en el entorno autorizado.
4. FG1/FG3 conservan o ajustan su cadencia automatica sin omitir gates, circuit breakers ni controles de ambiente.
5. FG2 conserva credenciales fuera del repositorio y respeta gates.
6. Frontend pasa lint, typecheck y build estatico segun el gate acordado.
7. Candidate inmutable, Context Graph PASS y aprobacion humana antes de promocion.

Ver [Arquitectura](../../arquitectura_pipeline.md), [Estimacion](../../estimaciones/est_001.md) y [Release minimo](../../operaciones/flujo_release_minimo.md).
