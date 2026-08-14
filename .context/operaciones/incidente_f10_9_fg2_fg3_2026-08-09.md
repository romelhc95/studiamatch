# INC-F10.9-001 - Fallo Fail-Closed De Primera Observacion Programada

| Campo | Valor |
|---|---|
| ID | `INC-F10.9-001` |
| Estado | `FAIL_CLOSED_FG2_FG3_REMEDIATION_REQUIRED` |
| Fecha | `2026-08-09` |
| Subfase | `F10.9` |
| Hito | `HITO-001` |
| Criterio | `H1-CA1` |
| Base observada | `main@38314170197a907ac5c4c815a9bb18b3d5f29b06` / tree `741627eda4b4fbcf76503b8e353abb08ac0eb1c4` |
| Evidencia afectada | `EVID-H1-011`, `EVID-H1-012`, `EVID-H1-013` |
| Contencion | `PENDING_SEPARATE_OPERATIONAL_ATTESTATION` |
| Metadata incompleta | `TRANSFERRED_NON_BLOCKING_H2_CA2` |

## Contexto

La primera activacion global de schedules F10.9 descubrio deuda operativa que el
Production Canary F10.8, por su cohorte y limites acotados, no podia demostrar.
Los controles fail-closed impidieron que ejecuciones parciales se acreditaran
como cierre. Este incidente no reabre F10.8, no invalida
`EVID-H1-010=VERIFIED` y no modifica el alcance CA1-only.

La actualizacion posterior de credentials de los environments programados fue
validada por los intentos 2: FG2 leyo instituciones y escribio staging, mientras
FG3 leyo la cohorte de cursos y aplico PATCH verificados. Los fallos vigentes no
son de autenticacion.

## Cronologia Sanitizada

| Run | Evento | Intento | Resultado | Acredita F10.9 | Motivo |
|---|---|---:|---|---|---|
| `31297402286` | `schedule` | 1 | `FAIL_CLOSED_AUTH_401` | No | Credenciales scheduled aun no reconciliadas. |
| `31311174311` | `schedule` | 1 | `SUCCESS_PREFLIGHT_ONLY` | No | FG3 permanecia fail-closed; integrity quedo skipped. |
| `31318589218` | `workflow_dispatch` | 1 | `FAIL_CLOSED_PRODUCTION_PAUSED` | No | El dispatch manual uso `Production`, no el environment scheduled. |
| `31318468550` | `workflow_dispatch` | 1 | `FAIL_CLOSED_PRODUCTION_PAUSED` | No | El dispatch manual uso `Production`, no el environment scheduled. |
| `31297402286` | `schedule` rerun | 2 | `FAIL_CLOSED_FG2_PARTIAL` | No | Credenciales validas; harvesting global incompleto. |
| `31311174311` | `schedule` rerun | 2 | `FAIL_CLOSED_FG3_INCONCLUSIVE` | No | Credenciales validas; integrity completo con resultados inconclusos. |

## Hallazgos FG2

- `38` grupos de identidad URL normalizada contienen duplicados.
- `281` filas excedentes requieren clasificacion dry-run antes de cualquier DML.
- `798` filas globales permanecen en `processing` desde hace mas de siete dias.
- Existen miembros duplicados con hashes conflictivos y referencias logicas
  downstream; no es seguro ejecutar un DELETE masivo.
- Seis instituciones fallaron al cargar su inventario duplicado.
- Dos fuentes institucionales devolvieron solo `HTTP 403` durante discovery.
- Una institucion persistio `14` filas validas en staging y otra completo un
  NOOP legitimo; esas mutaciones parciales no deben borrarse incidentalmente.
- Cleansing, enrichment, sync y auditoria quedaron skipped por el fallo de
  harvesting global.

## Hallazgos FG3

- La ejecucion evaluo `225` cursos activos y termino con `24` resultados
  inconclusos por `HTTP 403` y errores de red.
- Se marcaron `2` cursos con primera observacion 404 y se desactivo `1` curso
  despues de la gracia vigente; deben revalidarse mediante GET antes de decidir
  cualquier remediacion DML.
- Tras la ejecucion quedan `224` cursos activos y `104` incompletos: `102`
  carecen solo de syllabus y `2` carecen de syllabus y objectives.
- Los `104` tienen texto limpio atribuible para re-enrichment, pero no existe
  contenido enriquecido valido para un backfill directo.
- Los `104/224` se preservan como conteo historico y quedan
  `TRANSFERRED_NON_BLOCKING_H2_CA2`; no son gate de cierre Hito 1.

## Impacto En Evidencias

- `EVID-H1-010=VERIFIED` permanece inmutable.
- `EVID-H1-011=PENDING`.
- `EVID-H1-012=PENDING`.
- `EVID-H1-013=PENDING`.
- `EVID-H1-016=CLIENT_CONFORMITY_PENDING`.
- Pares FG2 -> FG3 aceptados: `0`.
- Inicio de observacion de 72h: `NOT_STARTED`.
- La secuencia consecutiva debe reiniciarse despues de remediacion promovida y
  autorizacion operacional nueva.

La reclasificacion por ADR-0011 no altera ningun conteo, run ni evidencia
historica. Metadata permanece visible como deuda H2 no bloqueante.

## Stop Conditions

- No ejecutar retries, dispatches o schedules mutables mientras la contencion no
  tenga atestacion separada.
- No ejecutar DML/DDL, deduplicacion, backfill o re-enrichment con base en esta
  nota.
- No reclasificar runs skipped, parciales, manuales o reruns como evidencia
  natural scheduled.
- No registrar URLs, dominios, UUID, hosts Supabase, payloads ni credenciales en
  Git o artifacts publicos.

## Remediacion

El plan subordinado es
[PLAN-REM-F10.9-001](./plan_remediacion_f10_9_fg2_fg3.md). La observacion
append-only se conserva en
[EVID-H1-OBS-F10.9-001](../evidencias_cliente/sprint_1/registro_observacion_production_f10_9_2026-08-09.md).

Esta nota registra hechos y blockers. No autoriza ejecucion.
