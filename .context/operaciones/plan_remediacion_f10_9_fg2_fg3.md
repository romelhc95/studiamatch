# PLAN-REM-F10.9-001 - Remediacion FG2/FG3 Post-Activacion Programada

| Campo | Valor |
|---|---|
| ID | `PLAN-REM-F10.9-001` |
| Estado | `DOCUMENTED_EXECUTION_PENDING_SEPARATE_APPROVAL` |
| Incidente | [INC-F10.9-001](./incidente_f10_9_fg2_fg3_2026-08-09.md) |
| Subfase | `F10.9` |
| Hito | `HITO-001` |
| Criterio | `H1-CA1` |
| Autoriza ejecucion | `NO` |

## Objetivo

Restaurar la operacion global segura de FG2 y FG3 sin ocultar parciales, sin
inventar datos, sin debilitar controles SSRF y sin aplicar reparaciones remotas
antes de backup, dry-run, validacion Free y aprobaciones DDL/DML separadas.

Este plan es subordinado a
[PLAN-H1-CA1-ONLY-001](./plan_cierre_hito1_ca1_only.md). No crea tarea,
criterio, subfase ni autorizacion paralela.

## Linea Base Read-Only

| Hallazgo | Valor observado |
|---|---:|
| Grupos URL normalizados duplicados | `38` |
| Filas staging excedentes | `281` |
| Filas globales stale en `processing` | `798` |
| Resultados FG3 inconclusos | `24` |
| Cursos activos incompletos post-run | `104` |
| Cursos activos totales post-run | `224` |

Las cantidades son un snapshot diagnostico y deben recalcularse con fingerprint
antes de cualquier apply. El drift produce STOP.

## Frontera De Este Plan

Permitido tras autorizacion especifica:

- Contencion mediante kill switches.
- Codigo y tests CA1 para preflight, clasificacion y observabilidad.
- Planners read-only y dry-run por ambiente.
- Correcciones de perfil DB-as-Code verificadas primero en Free.
- Remediacion DDL/DML/backfill solo mediante gates separados y cantidades
  congeladas.

Prohibido sin aprobacion adicional:

- DDL/DML Free o Pro.
- Deletes o repointing masivos.
- Re-enrichment/backfill.
- Schedules, retries y dispatches.
- Bypass de WAF/CAPTCHA o terminos de fuentes externas.
- Debilitar SSRF, exact-one, kill switch o salida no cero.
- Cualquier alcance CA2.

## WP-REM-01 - Contencion

1. Aplicar `AUTOMATION_ENABLED=false` y `PRODUCTION_WRITERS_PAUSED=true` a
   `Production-Scheduled-FG2` y `Production-Scheduled-FG3`.
2. Confirmar cero runs queued, waiting o in-progress.
3. Congelar SHA/tree y metadata de environments sin leer secret values.
4. Preservar logs sanitizados y conteos de mutaciones parciales.
5. No reintentar automaticamente.

La contencion requiere atestacion operacional separada; este documento no afirma
que ya fue ejecutada.

## WP-REM-02 - Preflight Read-Only FG2

Implementar un preflight anterior a cualquier writer que detecte:

- identidad URL normalizada duplicada;
- estados desconocidos o stale `processing`;
- payload/hash conflictivo;
- referencias downstream;
- perfil `hardcoded_urls` sin seeds;
- perfil habilitado sin discovery valido;
- fuente inaccesible bajo transportes autorizados.

El preflight debe emitir solo reason codes y conteos sanitizados. Cualquier
hallazgo bloqueante impide harvesting completo y garantiza cero mutaciones.

Reason codes minimos:

```text
DUPLICATE_NORMALIZED_URL
STALE_PROCESSING
CONFLICTING_CONTENT_HASH
DOWNSTREAM_REFERENCE_CONFLICT
INVALID_EMPTY_HARDCODED_PROFILE
SOURCE_ACCESS_403
SOURCE_TIMEOUT
```

## WP-REM-03 - Recuperacion De Lifecycle

Antes de deduplicar, un planner debe clasificar las `798` filas stale:

| Evidencia | Estado candidato |
|---|---|
| Downstream limpio valido | `processed` |
| Payload valido sin downstream | `pending` |
| Sin payload valido | `discovered` |
| Evidencia contradictoria | `HOLD_MANUAL` |
| Dependencias incompatibles | `HOLD_DEPENDENCY_CONFLICT` |

La antiguedad por si sola nunca autoriza transicion. El apply requiere snapshot,
backup restaurable, writer pause, dry-run estable y DML separada.

## WP-REM-04 - Deduplicacion Determinista

La unidad de reparacion es `normalization_version + normalized_url`. La
seleccion de survivor prioriza:

1. referencia downstream unica;
2. payload y content hash validos;
3. `processed` demostrado;
4. `pending` valido;
5. `discovered`;
6. timestamp atribuible;
7. UUID como desempate final.

Grupos con hashes distintos, multiples linajes o contradicciones quedan HOLD.
Para cada grupo aprobado, una transaccion debe bloquear miembros, revalidar el
fingerprint, reapuntar referencias, preservar mapping privado, retirar solo
losers aprobados y probar exactamente una identidad viva.

Postcondiciones:

```text
pre_rows - retired_rows = post_rows
retired_rows = archived_rows
orphan_references = 0
normalized_duplicate_groups = 0
second_apply = NOOP
```

## WP-REM-05 - Prevencion De Duplicados

Propuesta sujeta a ADR y DDL separada:

- funcion SQL immutable de normalizacion versionada;
- columna generada `normalized_url`;
- indice diagnostico antes del repair;
- unicidad global despues de cero colisiones;
- FK fisica `cleansed_programs.staging_id -> staging_raw.id` con delete
  restrictivo, despues de resolver orphans;
- claim/upsert atomico por identidad normalizada;
- tests de paridad Python/PostgreSQL y concurrencia.

No se crea ADR ni migracion en el paquete documental inicial.

## WP-REM-06 - Source Access Y Perfiles

Los perfiles live afectados no pueden permanecer como `hardcoded_urls` con seeds
vacios y fallback silencioso. La remediacion debe:

1. fallar configuracion invalida antes de red;
2. diagnosticar sitemap/robots/GET/Playwright desde runner;
3. usar browser/stealth solo cuando el perfil lo autorice;
4. versionar seeds oficiales o flags demostrados;
5. mantener `discovery_enabled=false` si ninguna ruta autorizada funciona;
6. requerir waiver explicito si la fuente no puede operar globalmente.

No se permite proxy, CAPTCHA bypass ni evasion no autorizada.

## WP-REM-07 - Hardening FG3

Separar probe HTTP, clasificacion, decision y persistencia. Contrato:

| HEAD | Accion final |
|---|---|
| `2xx` | Saludable sin GET. |
| `403` | GET acotado; persistente queda inconcluso. |
| `405/501` | GET acotado. |
| `404/410` | GET obligatorio antes de mutar. |
| `408/425/429/5xx` | Retry acotado con backoff. |
| Timeout/DNS/TLS | Retry acotado y taxonomia explicita. |

Maximo tres intentos por URL, presupuesto temporal, `Retry-After` limitado y
validacion SSRF/pinning en cada redirect. Un inconcluso nunca cambia
`last_404_at` ni `is_active` y produce salida no cero.

Las mutaciones deben ser condicionales, exact-one, idempotentes y capaces de
reconciliar `ALREADY_APPLIED` sin aceptar conflicto.

## WP-REM-08 - Gate De Metadata

La decision humana vigente establece gate cero para cursos activos con syllabus
u objectives faltantes. El conteo incluye null, blank y placeholders.

Los `104` registros tienen texto limpio atribuible, pero no campos enriquecidos
utiles para backfill directo. La remediacion requiere cohorte exacta, snapshot,
re-enrichment desde fuente limpia, provider registrado, fill-only de campos
faltantes, cero contenido inventado y segundo run NOOP.

Este work package es backfill/writer y requiere aprobacion separada.

## WP-REM-09 - Verificacion De Mutaciones Previas

Los dos flags y una desactivacion del run FG3 deben revalidarse mediante GET. Si
GET confirma `404/410`, se preserva el estado. Si demuestra `2xx`, cualquier
restauracion exige DML explicita, snapshot y exact-one. No ejecutar limpieza
masiva de `last_404_at`.

## Matriz De Pruebas

FG2 debe cubrir:

- preflight cero mutaciones;
- duplicados, hashes, stale states y referencias;
- perfil hardcoded vacio;
- NOOP valido vs source failure;
- repair dry-run/apply/segundo NOOP;
- paridad URL Python/PostgreSQL;
- dos writers concurrentes;
- source access sintetico.

FG3 debe cubrir:

- HEAD/GET `2xx`, `403`, `405`, `404`, `410`;
- retries `429/5xx/timeout`;
- redirect SSRF y DNS pinning;
- first flag, grace, deactivate y recovery;
- inconcluso cero mutaciones;
- exact-one, idempotencia y conflicto;
- paginacion mayor a 1000 y TimeGuard;
- gate metadata `0`.

## Rollout

1. Contencion atestada.
2. Codigo/tests y planners sin apply.
3. PR protegido Desarrollo y auditoria de seguridad.
4. Certificacion y pruebas PostgreSQL 17.
5. Dry-run Free congelado.
6. DDL/DML Free autorizada y segundo run NOOP.
7. Backup/restore Pro demostrado.
8. Dry-run Pro con cantidades y digest.
9. Aprobacion humana DDL/DML/backfill Pro.
10. Apply Pro transaccional y segundo run NOOP.
11. Diagnosticos FG2/FG3 acotados.
12. Habilitacion gradual nueva.
13. Reinicio de tres pares naturales y al menos 72h.

## Rollback Y Stop

- Drift de cantidades, schema, SHA, profile o dependency produce STOP.
- Fallo de backup/restore, exact-one, segundo NOOP o non-cohort attestation
  produce STOP.
- Despues de commit DML no se improvisa SQL reverso: se conserva writer pause y
  se usa snapshot/mapping bajo autorizacion de incidente.
- Cualquier cambio runtime/config durante observacion reinicia la secuencia.

## Aprobaciones Separadas

| Accion | Gate requerido |
|---|---|
| Kill switch | Operacion F10.9 |
| Codigo/tests/docs | F10.9 y PR protegido |
| DDL/DML Free | Aprobacion explicita Free |
| Backup/restore Pro | Aprobacion operacional |
| DDL/DML Pro | Aprobacion con cantidades/digest |
| Re-enrichment/backfill | Aprobacion de writer/backfill |
| Schedules/retries/dispatches | Aprobacion F10.9 posterior |

## Criterio De Salida

- Cero duplicados normalizados y cero stale `processing`.
- Cero perfiles invalidos habilitados.
- FG2 completo SUCCESS/NOOP en todas sus estaciones.
- Cero cursos activos incompletos.
- FG3 cohorte completa, cero inconclusos y mutaciones confirmadas.
- Tres pares naturales FG2 -> FG3 consecutivos durante al menos 72h.
- `EVID-H1-011..013=VERIFIED` solo despues de cumplir todos los umbrales.

## Evidencia

El ledger append-only es
[EVID-H1-OBS-F10.9-001](../evidencias_cliente/sprint_1/registro_observacion_production_f10_9_2026-08-09.md).

Este plan no autoriza ejecucion, DDL/DML, backfill, schedules ni merge.
