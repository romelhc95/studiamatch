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

## Checkpoint de preparación local H1REQ1 — 2026-11-09

La decisión humana vigente autoriza preparar y, al superar los gates, ejecutar
una primera FG2 controlada antes de cero cursos activos incompletos. Cero sigue
siendo condición de cierre; se preservan los demás umbrales y los tres pares
naturales consecutivos FG2→FG3 durante al menos 72 horas. Esta decisión modifica
el orden de la primera corrida, no el criterio de salida de F10.9 ni CA1.

### Candidato local FG2

El cambio local está en el worktree FG2 aislado
`/home/romel/.codex/worktrees/h1req1-fg2-bounded-harvest-20261109/studiamatch-h1req1-20261108-source`,
con `HEAD=646f14afa845ea3200f40ce919e273f090059c63`, y se validó en Docker sin
red con fixtures sintéticos. Conserva rotación institucional; antes del contacto
valida elegibilidad y seeds. El modo manual opt-in aplica 1 solicitud simultánea
por origen, 5 s mínimos entre inicios, 10 URLs únicas (incluido sitemap) y 20
inicios HTTP por institución (redirects/reintentos incluidos); respeta `Retry-After` hasta 30 s,
difiere si excede el máximo y detiene el origen sin reintento ante 403/429.
Estos límites son propios del candidato controlado; no modifican el camino ni
los límites de la programación ordinaria.

El manifest vincula run, intento, SHA, instituciones, IDs y hashes. Cleansing,
enrichment y sync verifican el digest y no consumen colas globales en esa
primera ejecución. El fixture diferencia `new_discovery` de
`refresh_existing`, preserva el `course_id` y el override editorial. Una fila
`staging_raw` con estado histórico protegido se reporta como blocker; no se
resetea `processing`, no se reabre `processed` y no se reintenta por otro camino.

#### Dry-run sintético final — 2026-11-09

Se amplió el fixture para modelar una URL conocida con una fila histórica
`staging_raw=discovered`, equivalente al estado refreshable observado. Los
identificadores y hashes son exclusivamente sintéticos: institución
`00000000-0000-0000-0000-000000000001`; staging
`40000000-0000-0000-0000-000000000095`; curso
`70000000-0000-0000-0000-000000000091`; cleansed
`50000000-0000-0000-0000-000000000091`; enriched
`60000000-0000-0000-0000-000000000091`. `profile_sha256`=
`6a0421ebd95debed506de02de8da759530b15e3fd10d32eaffb01eb02dcb629b` y
`seed_sha256`=`2c3223dee90ed909a7eaf4d8d1d503a31ade44b463fa1f870dd7051150478222`.
El digest de la URL sintética es
`cc741735bd878822d09ac0756132ae2e4da1a50ef7b7b503467f2c5a3e26672d`; el hash
de contenido anterior es
`83866a516ad68d926ef19a8fb42dac8d41ba1d5114879c663f3a992363a67cd0` y el
nuevo es `82d0ed446d6756f761c437105a1767338c45d35f793dba201221fb519f9d98c2`.

El dry-run reutiliza el mismo `staging_id`, pasa de `discovered` a `pending` por
la promoción normal y luego a `processed` por cleansing; produce un registro
cleansed y uno enriched, y sincroniza sobre el mismo `course_id`. La fuente
editorial conserva `manual_override` y el texto vigente. El `FG2RequestBudget`
real del candidato registra 1 URL única y 1 inicio HTTP; la respuesta y los
datos son fixtures locales, el enrichment usa un resultado sintético y el
adapter no toca Supabase. La aserción anterior detectó que una sustitución de
`_safe_request` daba conteos 0/0; el test corregido usa el transporte sintético
del candidato y toma los valores del snapshot real del presupuesto.

La suite Docker final con red deshabilitada fue `84 passed, 1 deselected, 1`
advertencia PyPDF2. El test excluido es un control H2 ajeno al diff. El test
focal de refresh pasó también de forma aislada. Se conserva el FAIL integral
documental FG3 `348→348`, listas idénticas; la suite candidate-aware y este
dry-run local no cambian ese resultado ni prueban una corrida de Pro.

### Gates de la corrida productiva

Antes de escribir debe estar en main el candidato exacto por promoción
protegida; luego se revalidan SHA, Environments, flags efectivos, ejecuciones y
colas, concurrencia, elegibilidad/perfil/seeds, URLs reales, IDs/estados/hashes,
consumo de cada worker, costo/alcance y recuperación. La lectura de Pro
informada por el TL (224 cursos activos con `last_scraped_at` >30 días,
máximo `2026-07-18`; 798 filas `processing`) es diagnóstico, no manifiesto de
corrida ni autorización. El corte productivo debe congelar los IDs y el dry-run
antes del JIT exacto de writer y dispatch. Configurar Environment, cambiar flags,
habilitar un workflow y despachar son acciones separadas.

**Antes de escribir:** si el manifest muestra una URL cuya fila única de
`staging_raw` está en estado protegido, detener esa URL y presentar el ID,
estado actual, contenido/hash y transición mínima exacta para decisión DML. No
reabrir ni borrar registros como parte del run acotado. Si una cola posterior
contiene registros fuera del manifest, el worker controlado debe rechazarlos;
si falla ese aislamiento, STOP antes de habilitar el writer.

**Después del run:** evaluar por IDs y hash del manifest los resultados de
harvest, cleansing, enrichment y sync; revisar estado anterior/posterior,
referencias downstream, mismo `course_id`, ownership editorial, publicaciones
y postflight. `SKIPPED`, `blocked`, un `SUCCESS` vacío o un NO-OP sin explicación
no acreditan refresh. Un bloqueo o deferencia de origen se conserva y no se
reintenta en esa corrida. Un NO-OP solo es aceptable si se demuestra que la
fuente y los hashes justifican que no había cambio.

**Pendiente histórico independiente:** la observación de 798 `processing` no
demuestra stale por `created_at`, ni se deduplica por conteos. No se resetea
backlog, ni se reabre `processed`, ni se ejecuta backfill o DML sin planner con
IDs/efectos exactos y aprobación separada. El resultado de la primera FG2 no
cierra esos hallazgos si no los procesa ni resuelve.

### Preparación FG3 y seguridad del paquete

Se mantiene intacto `/tmp/studiamatch-h1req1-20261108-source`, HEAD
`c736336819bc0a927cc7224a053429e27433a748`, diff SHA-256
`0252e5c96caf72881c8ccac7bcccf8ed2674d6a3c9fee401bb228b37b0aa7c7e`. Mientras
coincida su huella, se reutilizan 36 pruebas focales y 9 subpruebas; el suite
regression reporta 90 passed y 1 deselected, 9 subtests. FG3 selecciona desde
`courses_public_effective`, lee `last_404_at` de `courses` solo para IDs
seleccionados, preserva gracia 404/410 y transitorios, no expira por fecha y
limita sus escrituras a los campos existentes permitidos en `courses`.

La revisión manual encontró y corrigió el caso de redirect privado y exposición
de URL en log; el credential scan local está separado y reporta PASS; el
scanner Codex de diff terminó antes de emitir `scanId`, por lo que no hay scanner
PASS. El branch protection versionado exige PR, una aprobación humana y check CI
`security-audit`; el scanner gestionado sin `scanId` no sustituye esos gates ni
se presenta como aprobado.

Antes de un posible PATCH FG3 se vuelve a comprobar que el ID siga en la vista
pública; el PATCH se limita al ID y al estado `is_active`/`last_404_at`
esperado. Vista y escritura no son atómicas: persiste una ventana de carrera
estrecha y visible. El candidato omite cuando ya no es público y falla cerrado
ante conflicto, pero no reclama garantía transaccional. Una RPC/migración para
cerrar esa ventana sería un cambio aparte con diseño y JIT; no se añade a esta
preparación. La primera corrida funcional FG3 permanece después de FG2 y del
gating que corresponda.

La comparación documental de FG3 se registra correctamente como **FAIL
348→348, listas idénticas**, cero diagnósticos nuevos y cero resueltos, con SHA de
lista `738e442d6b13b3f604376a3f274747b8208f389fa3c2712e535d5fa015527a92`.
Ese FAIL histórico se conserva como FAIL. Es distinto de las comprobaciones
focales del candidato y no se convierte en PASS integral.

### E9, E10 y límites de continuidad

El último tablero H1 observado conserva los intentos FG2 `42477302202` y FG3
`42502107547` como writer-blocked con jobs funcionales `SKIPPED`; no forman un
par. H2/H3 y el canary FG1 `31272290614` se reutilizan solo en su alcance ya
aceptado; el cron FG1 sigue pendiente. E9 necesita la secuencia funcional
FG1→FG2→FG3 con inspección entre etapas. E10 no empieza hasta acreditar E9; los
tres pares válidos y la ventana de 72 horas siguen en cero/no iniciada. Los
schedules permanecen cerrados durante la primera ejecución controlada y H4
conserva su gate.

No hubo en este ciclo escritura Pro, DML, backfill, cambio de flags o secrets,
cambio de Environment, enablement, dispatch, push, PR, merge o promoción. La
autorización local cubre solo código, pruebas Docker offline y documentación;
la primera corrida de producción y cada acción remota conservan sus gates
separados.
