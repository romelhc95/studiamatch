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
- Activar o cambiar schedules/workflows, retirar proteccion de Environments, abrir writers, dispatches y retries sin sus gates especificos. Para E10 se conserva una aprobacion humana inicial de activacion; los runs programados posteriores no requieren aprobacion por corrida. El workflow_dispatch manual sigue protegido por Production y su reviewer humano por run.
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
| Aprobacion inicial de activacion E10 | Aprobacion humana unica, posterior a E9 funcional y previa a la activacion gradual; no se repite por run schedule. |
| Configurar Required reviewers | Autorizacion de configuracion GitHub por Environment; retirar solo de los tres Production-Scheduled-*, uno a uno. Manual Production queda intacto. |
| Run programado despues de E10 | Sin aprobacion humana por corrida; main-only, flags, preflight, limites, pausa y controles del workflow siguen aplicando. |
| workflow_dispatch manual | Autorizacion JIT del dispatch y aprobacion humana requerida por corrida en Production. |
| Habilitar workflow/schedule | Autorizacion separada para la habilitacion exacta; cron y alcance vigentes se preservan. |
| Abrir o pausar writers/flags | Autorizacion separada para el recurso y valores exactos; el kill switch se conserva. |
| Retries | Autorizacion especifica del run/alcance; no hay reintento automatico fuera del plan. |
| DDL/DML Free | Aprobacion explicita Free. |
| Backup/restore Pro | Aprobacion operacional. |
| DDL/DML Pro | Aprobacion con cantidades/digest. |
| Re-enrichment/backfill | Aprobacion de writer/backfill. |
| Codigo/tests/docs y promocion | F10.9, validacion local, revision de seguridad y flujo PR protegido; promocion mantiene sus gates. |
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

#### Reanudación local desde el clon íntegro validado por TL — 2026-11-09

La rama `codex/h1req1-fg2-bounded-first-run-20261109` se retomó desde
`/tmp/h1-tl-fg2-historial-20261109.IpjVdE/repo`, con `HEAD`
`c0f19bcec33ec84a82dfc06581311ec37452fc23` y base `desarrollo`
`c736336819bc0a927cc7224a053429e27433a748`. Se añade una barrera explícita para
el posible bypass de presupuesto: antes de lanzar Playwright, el runner rechaza
cualquier ruta de browser; el wrapper común de navegación también detiene
`page.goto` antes de emitir una solicitud en modo controlado. La primera FG2
controlada queda restringida a perfiles `traditional_ssr` y discovery HTTP
soportado; SPA/ecommerce, extracción por scroll, stealth y anti-bot quedan
deferidos sin contacto a la fuente. El camino de schedule no cambia.

Revalidación final local en la imagen Docker fijada
`sha256:bb30d6237846f120d39b7c9794f8eb0c938c69e8cc15e0e93d2ca03641a7ade1`,
`--network none`, sobre copia sanitaria read-only: FG2 focal **68 passed**.
La regresión (cuatro módulos bounded, pipeline walk, contrato de credenciales y
fase 09/10) dio **148 passed, 1 deselected**. Sin filtro: **148 passed, 1
failed** en la aserción H2 ajena
`test_db_sync_main_push_is_report_only_and_manual_apply_is_guarded`; el test y
`.github/workflows/db-sync-to-pro.yml` siguen idénticos a HEAD c0f19b. La
advertencia es deprecación PyPDF2. No hubo red productiva, fuentes, Pro ni
escrituras. El resultado previo 67/154 se conserva en el changelog como
checkpoint anterior a la revalidación del primer write.

El self-test candidate-aware con manifest pasó con 769/769 fuentes asignadas,
122/122 documentos activos alcanzables y 433/433 históricos enlazados. La
comparación integral reproducible de git-archive c0 con este candidato queda
FAIL **349→349**, listas idénticas, SHA-256 ordenado
`7775152137258a7709396217c4e521d64a9f185f4dfc7ebfc513f8564ab64434`. Esto
corrige el conteo 201→201 consignado antes, que no coincide con la salida íntegra
del checker en este corte. El FAIL histórico de FG3 **348→348** permanece aparte.

El lote y el refresh de este ciclo son sintéticos. No existe en este paquete un
snapshot read-only de Pro, URLs/IDs reales, hashes o evidencia de las colas
operativas; por ello no se presenta como dry-run productivo ni se prepara un
dispatch ejecutable. Antes de writer/dispatch, el owner debe autorizar por
separado la lectura mínima de Pro que permita formar el lote exacto, medir las
filas que consumiría cada etapa, cuantificar alcance/coste y producir su efecto
y recuperación. No resetear `processing`, reabrir `processed` ni ejecutar DML.

#### Revalidación de identidad de URL — 2026-11-09

La revisión detectó que el filtro exacto `url=in.(...)` del snapshot podía
omitir filas con slash final o segmento `/en/`, aunque `normalize_url` del
harvester las considera la misma identidad. Además, el sync no propagaba el
`course_id` del manifest y buscaba `courses` por la URL entrante; un alias podía
crear otra fila o perder el override editorial de la existente.

El candidato local revalida con la misma normalización compartida, conserva en
el digest las URLs crudas exactas del snapshot, consulta metadatos paginados de
courses/staging para no ocultar aliases, rechaza duplicados y owners cruzados
antes del harvester, vuelve a leer las filas aprobadas por ID y conserva el URL
almacenado al promover staging/upsert courses. El sync transporta el `course_id`
aprobado a través de las referencias staging→cleansed→enriched. `new_discovery`
se detiene si ya aparece un curso con esa identidad; `refresh_existing` exige
exactamente el ID aprobado y una única coincidencia canónica. Esto no deduplica,
reabre ni repara filas históricas, y no agrega una restricción DB o atomicidad:
la lectura y el write siguen separados, por lo que un conflicto al instante del
upsert conserva STOP y requiere observación, sin retry alterno.

Validación final local, 2026-11-09 17:16 Lima, en la imagen Docker fijada
`sha256:bb30d6237846f120d39b7c9794f8eb0c938c69e8cc15e0e93d2ca03641a7ade1`,
`--network none`, árbol montado read-only: **106 passed** en FG2 acotado,
pipeline walk y contrato H2; **169 passed, 1 deselected, 1 warning** en la
regresión ampliada con contrato de credenciales y controles fase 09/10. El único
deselected es `test_db_sync_main_push_is_report_only_and_manual_apply_is_guarded`,
cuya expectativa H2 ya fallaba contra los archivos idénticos de HEAD c0; no se
cuenta como PASS. La advertencia es la deprecación upstream de PyPDF2. Los casos
de identidad verifican aliases slash y `/en/`, rechazo de ambigüedad antes del
contacto/write, `course_id` propagado y preservación de URL/override. El
credential scan Docker `--tree` y `git diff --check` pasaron. El checker
candidate-aware pasa con el manifest versionado; el diagnóstico integral sigue
FAIL 349→349, listas idénticas, SHA-256 ordenado
`7775152137258a7709396217c4e521d64a9f185f4dfc7ebfc513f8564ab64434`. No es
lote real ni autoriza fuente, Pro, dispatch, writer, push, PR, merge, schedule o
promoción.

La revisión Codex Security del mismo paquete local terminó el 2026-11-09
17:38 Lima: scan `faa63933-92e9-495a-89e2-acc089e60bf7`, diff snapshot
`codex-security-snapshot/v1:sha256:1e7f6642443ed74216c03dff0899fa64327f6fcd608a3a63b775a8c00c1781b9`, cobertura completa, cero findings. El inventario automatizado priorizó
seis archivos runtime; la revisión manual del parent cubrió además las otras
doce rutas cambiadas. No hubo tráfico productivo ni cambios en GitHub. El
hallazgo operativo a considerar al armar el lote es que el control de aliases
repite inventarios completos paginados; el costo real depende del tamaño de las
tablas y del lote y no se midió en este ciclo. El resultado aplica al snapshot
escaneado, no a producción ni a autorización de publicación/ejecución.

#### Guard de ejecución productiva solo en `main` — candidato local 2026-11-09

La brecha del dispatch no-main queda cerrada en el candidato local: FG1, cada
estación FG2 y FG3 requieren el ref completo `refs/heads/main`. Cada workflow
usa primero un job de guard sin Environment, secrets, vars ni checkout, con
`contents: none`; preflight y etapas funcionales dependen de su éxito. Además,
`.github/scripts/production_control_preflight.sh` rechaza refs no-main aunque
los flags permitan writer. Production Canary mantiene su job manual, limitado
al ref exacto de main antes del Environment, y sus preflights revalidan la ref.
Se preservan DB Sync, el canary aceptado, CI y la promoción protegida.

Docker offline fijado dio **172 passed, 1 warning**. Los casos ejecutan el shell
guard para `desarrollo`/`certificacion` y `main`, rechazan tags y refs
alternativas, simulan `main` con writer allowed/blocked según flags, y comprueban
que no hay Environment/secrets en el job guard y que cada estación funcional
depende de él. Son pruebas de YAML/shell local; no simulan Actions alojado ni
acreditan producción. La primera invocación quedó antes de pytest por el
entrypoint de sincronización de `node_modules`; la invocación directa de la
misma imagen `sha256:bb30d6237846f120d39b7c9794f8eb0c938c69e8cc15e0e93d2ca03641a7ade1`
ejecutó las suites con `--network none` y pasó. El delta está sin publicar y
no hereda la autorización anterior del push de 21 rutas.

Transición: `expand` añade la barrera de ref y refuerza el control de estación;
`compatibilidad` conserva DB Sync, Production Canary, CI y la promoción normal;
`deploy` requiere el flujo protegido y la verificación del SHA adoptado;
`contract` mantiene main-only para writers productivos. Recuperación: detener
dispatches con la autorización correspondiente, confirmar ausencia de runs
activos y revertir por el flujo protegido. No hubo cambios de configuración,
flags, secretos, schedules, writers, Pro ni refs remotas.

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

Los intentos FG2 42477302202 y FG3 42502107547 con writer bloqueado y jobs
funcionales SKIPPED no forman un par. El run FG2 #252 (42823711354) fue
disparado por schedule en main; despues de la aprobacion de
Production-Scheduled-FG2, el preflight termino SUCCESS con Allow writer=false
y Reason=automation_disabled, mientras harvesting, cleansing, enrichment, sync
y auditoria CA1 quedaron SKIPPED. No acredita ejecucion funcional ni E9.
H2/H3 y el canary FG1 31272290614 se reutilizan solo en el alcance ya aceptado.

E9 conserva el orden FG1 → FG2 → FG3: se reutiliza el canary FG1 31272290614
solo dentro del alcance aceptado, luego se acredita la primera FG2 controlada y
despues FG3. Se inspeccionan alcance, ediciones editoriales, resultados
downstream y postflight entre etapas. Un
preflight exitoso, SKIPPED, un bloqueo o un SUCCESS sin trabajo funcional no
cuentan. E10 no empieza antes de acreditar E9. Los tres pares naturales validos
FG2→FG3 y la ventana minima de 72 h permanecen en cero/no iniciada; H4 mantiene
su gate.

#### Cohorte Pro candidata y efectos downstream — lectura 2026-11-10

La relectura SQL Pro fue de solo lectura; no contactó las fuentes ni escribió
filas. El artefacto de lote existente, FG2-PRO-LOT-PREFLIGHT-READONLY-20261109.json,
fija el prefijo de rotación por last_harvest_at ASC NULLS FIRST. Universidad de
Lima (rango 10; diez seeds seleccionadas) y Certus (rango 11; dos seeds) forman
el prefijo exacto de 12 URLs. Ninguna tenía coincidencia actual de staging,
course o downstream: el resultado esperado es descubrimiento, no refresh de
cursos existentes.

Tres seeds de UTEC (rango 17, fuera del prefijo) sí enlazan a cursos existentes
desde filas staging_raw=discovered. La lectura Pro de este ciclo registró:

| Seed | staging_raw (ID / hash actual) | Downstream actual | Course actual |
|---|---|---|---|
| https://posgrado.utec.edu.pe/cursos/data-science-fundamentals | bba1ef8f-c721-4bd6-85ac-b43a6b71b526 / fa3800f5796f5abf18898b498ca543b9a282d670e9b2ae4d5e602da431928ded | cleansed 4ad808f9-16f9-4be2-a8b6-99e9bba7a4eb=enriched; enriched 86cc1214-6966-47e1-8f61-0d9fe0fed588=synced | 1d723bd7-67c3-47d7-82e3-1994b44703b3, active+verified/public |
| https://posgrado.utec.edu.pe/cursos/big-data | 8fc17004-7f0d-4b7b-8e02-72ae364f3898 / 57fb8dd8e5e139311d03501ca060f22836ac235e0e287e15c477b7520f82f084 | cleansed 064cbc02-ef9a-4bf8-8bba-b3646495d7ed=enriched; enriched cd10bfda-eb6e-4bf9-a499-4d269fb5ae8c=synced | 4e3faad9-1d43-4b63-82c5-6e8a6dce6933, active+verified/public |
| https://posgrado.utec.edu.pe/programas/programa-en-arquitectura-de-datos | d31feadd-a478-45c7-aa50-ab808d6c9e9d / 4c5bc1b1ec964863307ec3cf2da5a435c8fb0bc674c6c3cc1d40cb162fb1ad7e | cleansed a0d2727f-7283-4290-9770-48e2699de8c6=enriched; enriched 24cd2d22-89c6-4434-9070-7356f09ebe78=synced | 7d9b3203-4255-434c-8015-33df7ac3d45c, active+verified/public |

Las tres filas de courses eran visibles en courses_public_effective, con
last_scraped_at el 2026-06-27, last_404_at nulo y editorial_status
pending_review. No se hallaron campos de override editorial manual en el
snapshot. Las dos seeds UTEC restantes no tienen course ni downstream; solo
representan descubrimiento. Cibertec está en rango 16, antes de UTEC, y conserva
cinco filas staging processed. NewHorizons conserva cinco filas processing.
Ambos estados históricos quedan intactos.

Si un manifiesto controlado exacto admitiera las tres filas UTEC, el efecto
previsto que requiere aprobación de writer sería:

| Etapa | Efecto exacto esperado para estas tres filas | Límite |
|---|---|---|
| FG2 harvest | Reclasificar cada staging discovered a pending y refrescar contenido/hash al recibir la URL conocida; mantener staging ID, course ID y URL canónica aprobada. | Solo tres URLs/IDs del manifiesto; 10 URLs únicas y 20 solicitudes HTTP por institución, incluyendo redirects y reintentos; pausa de origen tras 403/429 según el contrato. |
| Cleansing | La RPC observada hace upsert del cleansed existente por URL con status pending y mueve staging pending/processing a processed. | Solo staging IDs del manifiesto; la llamada productiva no se ejecutó. |
| Enrichment | La RPC observada hace upsert del enriched existente por cleansed_id con status pending y mueve cleansed pending a enriched. | Solo los cleansed IDs relacionados al manifiesto; costo de proveedor aún no medido. |
| Sync/publicación | Actualizar los tres courses existentes por identidad URL, con nuevo last_scraped_at y datos derivados; preservar manual_overrides y validar IDs, estado editorial y vista pública después. | Solo course IDs encadenados desde el manifiesto; no se presume que el catálogo público crezca. |

Las definiciones vivas de atomic_cleansing_promote y
atomic_enrichment_promote se leyeron en Pro; no se invocaron. Con manifiesto,
los workers FG2 acotados validan el digest y las referencias relacionadas. El
cron de main todavía llama al camino ordinario sin manifiesto y los workers
posteriores pueden seleccionar colas globales; por ello E10 no está listo ni
habilitado por esta evidencia. La lectura de metadata no tuvo un costo monetario
registrado; el costo del harvest/enrichment real no se estimó ni se incurrió.

El gate de ejecución requiere el candidato exacto en main, manifiesto y digest
aprobados, elegibilidad/URLs/IDs/estados/hash revalidados antes del primer
contacto, flags y Environment correctos, writers permitidos por autorización
JIT y ausencia de una corrida concurrente FG2/FG3. No se amplía el límite de
instituciones, URLs o solicitudes para acomodar el lote. La tabla es un dry-run
de metadata; no es una autorización operativa.

Para acreditar resultado, el run debe mostrar trabajo funcional no-SKIPPED y
publicar el manifiesto con digest, IDs, URLs, hash previo/nuevo, conteos y
resultado por etapa. El postflight debe comparar los tres staging IDs, las tres
relaciones cleansed/enriched y los mismos tres course IDs; comprobar los estados
esperados y el last_scraped_at; confirmar que manual_overrides/editorial_status
se preservaron y que la vista courses_public_effective conserva solo la
elegibilidad esperada. Una diferencia en cualquier fila fuera del manifiesto,
un estado inesperado, deriva de elegibilidad o daño editorial detiene el flujo
y pausa el writer según la autoridad vigente. Se conserva el run/manifiesto como
evidencia; no se reintenta automáticamente ni se restaura por DML sin
autorización específica. Si el run no obtiene cambio de contenido, registrar
NO-OP solo con respuesta y hash verificados; no inferir refresh por SUCCESS.

#### Decisión humana necesaria antes de cambiar la rotación

- **Conservar el orden vigente:** aceptar el prefijo Universidad de Lima +
  Certus como primera corrida controlada. El resultado puede acreditar
  descubrimiento funcional, pero no debe reportarse como refresh de cursos
  existentes ni como recuperación de sus fechas de actualización.
- **Autorizar una excepción FG2 puntual para UTEC:** permitir como conjunto
  cerrado las tres URLs, staging IDs, hashes y course IDs de la tabla anterior,
  sin sustituirlos por otra institución. Esto salta los rangos 12–16 y requiere
  modificar el contrato/verificador del lote, actualizar pruebas y revisar la
  huella final antes de publicar. No reabre las cinco filas processed de
  Cibertec, no reinicia las cinco processing de NewHorizons y no autoriza por sí
  mismo contacto, dispatch ni escrituras Pro.

Hasta que Romel elija explícitamente una opción, no se cambia el prefijo ni se
genera manifiesto UTEC para un run. Para cualquiera de las dos opciones, el
snapshot de IDs, estados, URLs y hashes se debe releer inmediatamente antes de
contactar fuentes; toda deriva cancela el run antes del harvester.

#### Politica E10: activacion inicial y ejecuciones naturales

- Se conserva una aprobacion humana inicial para activar E10, despues de cerrar
  E9 funcional y antes de abrir la programacion.
- La decision aprobada elimina la aprobacion humana por corrida programada: una
  vez activado, el schedule de FG1, FG2 o FG3 en main no debe esperar Approve.
  No se requiere una aprobacion nueva por cada run programado.
- El workflow_dispatch manual de cualquiera de los tres workflows conserva el
  Environment Production y su reviewer humano por corrida. La solicitud de
  dispatch mantiene su autorizacion separada.
- Retirar Required reviewers es un cambio de configuracion independiente,
  limitado a Production-Scheduled-FG1, Production-Scheduled-FG2 y
  Production-Scheduled-FG3, uno por uno. No se modifica el Environment manual
  Production; se mantienen rama main, reglas restantes, secrets, variables,
  cron, limites y kill switch.
- Antes de tocar cada Environment: comprobar SHA vigente de main, flags,
  workflow habilitado, aprobaciones/propiedades actuales y la cola completa.
  No puede quedar ningun run queued, waiting, con deployment pendiente o
  activo. Si existe, detener la configuracion y hacer que el owner resuelva el
  run bajo su gate; no aprobar ni soltar un run anterior como consecuencia de
  retirar la proteccion.
- Despues de cada cambio, releer el Environment y confirmar el delta exacto:
  solo Required reviewers retirado, rama main intacta, secretos/variables
  presentes sin leer valores, flags y pausa sin cambios. Luego, con autorizacion
  distinta, habilitar el workflow/cron si estuviera apagado y cambiar los flags
  efectivos para permitir el writer. Verificar de nuevo antes de pasar al
  siguiente Environment.
- En orden FG1 → FG2 → FG3, registrar cada primer run natural. Debe avanzar sin
  aprobacion humana por corrida y mostrar ejecucion funcional completa; un
  preflight con writer bloqueado o etapas SKIPPED no sirve. Para FG1 se reutiliza
  el canary aceptado solo como soporte; el cron mensual requiere su propia
  observacion natural. No alterar cron para adelantar esa ventana.
- Mantener FG2/FG3 serializados. Acreditar tres pares naturales consecutivos
  FG2→FG3 a lo largo de al menos 72 h. Ante fallo o drift, pausar con
  AUTOMATION_ENABLED=false y PRODUCTION_WRITERS_PAUSED=true, detener/cancelar
  lo activo conforme a su autorizacion, preservar evidencia y reiniciar la
  observacion solo despues de remediar y revalidar.

La apertura de flags/writers, activacion de workflows, cada configuracion
GitHub, dispatch manual, SQL/DML/backfill y promocion mantienen autorizaciones
propias. Este plan no afirma que E9 o E10 esten ejecutados ni autoriza una
operacion remota.

No hubo en este ciclo escritura Pro, DML, backfill, cambio de flags o secrets,
cambio de Environment, enablement, dispatch, push, PR, merge o promoción. La
autorización local cubre solo código, pruebas Docker offline y documentación;
la primera corrida de producción y cada acción remota conservan sus gates
separados.

#### Relectura de rotación Pro y elegibilidad E9 — 2026-11-10

Relectura SELECT-only de Pro, aproximadamente 17:30–17:36 America/Lima:
el prefijo del primer lote sigue siendo Universidad de Lima (rango 10) y
Certus (rango 11). La comparación canónica de sus 10+2 seeds seleccionadas
contra staging_raw, courses y courses_public_effective devolvió cero filas.
Ese lote puede acreditar descubrimiento al ejecutar con autorización, pero no
refresca cursos existentes.

La ruta de rotación después de Certus tiene estos gates actuales:

| Rango | Institución | Elegibilidad del harvester controlado | Coincidencia por seed y efecto |
|---:|---|---|---|
| 12 | Universidad del Pacífico | production_enabled=false | No se selecciona. |
| 13 | USIL | seed_urls vacío | No pasa el preflight de semillas. |
| 14 | PBS | discovery/pipeline/production habilitados; traditional_ssr; cinco seeds | La seed 1, https://pbs.edu.pe/educacion-ejecutiva/programa-ejecutivo-data-science/, tiene staging 146f7ad0-4b10-4989-a018-795032cf54fc, processing, hash 281c1775ec6abda672418e9e7a0e04ddb27ea6f60d709841b9c96799940e2c92 y ningún course. Las otras cuatro no tuvieron coincidencia staging/course en la lectura. No resetear processing. |
| 15 | Smart Data | site_type=spa_js_heavy | El modo controlado difiere este perfil antes del contacto. |
| 16 | Cibertec | discovery/pipeline/production habilitados; traditional_ssr; cinco seeds | Las cinco seeds resuelven a staging processed y courses activos/verificados. No reabrirlas ni seleccionar esas filas para el lote controlado sin una decisión y operación de datos separadas. |
| 17 | UTEC | discovery/pipeline/production habilitados; traditional_ssr; cinco seeds | Las posiciones 1–2 son discovered sin course. Las posiciones 3–5 son las tres filas discovered que coinciden con cursos públicos; IDs, hashes y course IDs son los de la tabla UTEC inmediatamente anterior. |

Por tanto, la opción documentada anteriormente de seleccionar UTEC como excepción
no conserva la rotación: para llegar a rango 17 el manifiesto tendría que pasar
por PBS y Cibertec. Cibertec no puede integrar una cohorte acotada mientras sus
seeds elegidas tengan estado processed, porque el validador cerrado acepta
staging vacío o discovered y rechaza cualquier estado protegido antes del
contacto. No se infiere stale por fecha ni se reabre processing/processed.

Conteos de colas leídos en la misma ventana: staging processing 798, discovered
372, processed 290, skipped 228, discarded 162, pending 14; cleansed 351;
enriched synced 349 y error 2. Son el estado global, no una cohorte y no un
criterio para deduplicar o decidir qué refrescar.

La decisión humana pendiente para E9 es si se mantiene literalmente la
rotación y se acepta que el primer lote Lima+Certus sea solo de descubrimiento,
dejando incumplida la recuperación de fechas/contenido, o si Romel modifica
explícitamente el orden para un lote único de refresh con las tres seeds UTEC
de posiciones 3–5, saltando PBS rango 14 y Cibertec rango 16. La segunda
opción requiere delta del verificador, prueba, huella/seguridad y gates de
publicación; no autoriza contacto, dispatch ni escritura Pro. No se cambia
rotación bajo la instrucción vigente.

#### Control de la ruta programada E10 — lectura local y Actions 2026-11-10

En el YAML candidato, los guards de ref main y el preflight preceden el
trabajo funcional; el schedule FG2 de 05:00 UTC no recibe el manifiesto/lote
aprobado. El booleano FG2_CONTROLLED_FIRST_RUN solo se establece para
workflow_dispatch, así que el cron toma el camino ordinario y los workers de
cleansing, enrichment y sync consultan sus colas globales. El ambiente
Production-Scheduled-FG2 no basta para acotar esas filas. Corregir/promover
ese recorrido es requisito anterior a activar E10. FG1 mensual 00:00 UTC y
FG3 diario 11:00 UTC también conservan guards de main y preflight; FG2 y FG3
comparten grupo de concurrencia, mientras FG1 usa uno separado. Los dispatch
manuales de main conservan Production y reviewer humano.

La página Actions se recargó a las 17:35:59 America/Lima; las 30 entradas
recientes visibles no mostraron queued/waiting/pending/requested/in progress.
FG2 #252/42823711354 y FG3 #120/42874819447 fueron terminal success con etapas
funcionales SKIPPED. Este vistazo no es consulta completa de cola ni crédito
E9. No se activó E10 ni se leyeron/escribieron Environments en esta
revalidación. Antes de activar siguen pendientes el control de colas completo,
la demostración del manifiesto acotado por schedule, el SHA de main, flags y
propiedades remotas actuales, además de su autorización específica.

#### Dictamen de revisión y ruta ordinaria FG2 — preparación local 2026-11-11

El dictamen sanitizado del revisor confirmó el baseline
`c736336819bc0a927cc7224a053429e27433a748` y revisó estáticamente las 35 rutas
del diff anterior, SHA-256
`7bb2f49199e1e2d986c079fa342145a1869fd85dd96a611aac7eb51d57a8f0ba`; su
veredicto fue NO-GO para FG2 ordinario y readiness H1. El scan asociado es
`371e1513-379a-4d05-820e-4d97da8ada21`: standard, 1.847 archivos, cobertura
general parcial de 6/9 unidades y cinco registros que se deduplican en tres
familias. Ese scan no acredita cobertura exacta del candidato actual, cuyo
delta local cambió después de la revisión.

La familia SSRF sí afecta la ruta ordinaria FG2: sitemap anidados, enlaces y
redirects pueden originar nuevas solicitudes; `site_diagnostics.py` también
obtiene la URL inicial y sigue redirects. El delta actual valida y fija cada
salto HTTP a DNS público antes de solicitarlo, y las solicitudes de sitemap
anidados reutilizan ese guard. Los destinos públicos de otro host se conservan.
El segundo hallazgo de H1 es el caller controlado que podía entrar a cleansing
sin delegar el manifest; ahora falla antes de seleccionar DB o lanzar workers.
El tercero corresponde al flujo controlado: enrichment y sync comparan la URL
y referencias del manifest antes de proveedor y writer. La sustitución de URL
manteniendo ID/institución falla cerrado en las pruebas.

El schedule sigue separado y no recibe manifest. El YAML ejecuta harvesting
ordinario con límite de diez instituciones, después cleansing global por
`staging_raw.pending` (lock `inst_id=NULL`, batches de 100 y time guard),
enrichment global por `cleansed_programs.pending` de instituciones habilitadas
y sync por `enriched_programs.pending` de instituciones habilitadas. Cleansing
puede marcar `skipped` filas de instituciones sin pipeline habilitado. El
schedule no selecciona automáticamente `discovered`, `processing` o `processed`
y habilitarlo no los reencola. No se infiere qué IDs se consumirían de los
agregados observados. El alcance global de esas etapas mantiene bloqueada la
activación E10 hasta una solución aprobada y un preflight fresco.

Queda además documentado como límite de este delta que el cuerpo del GET
ordinario de `UniversalHarvester` y los cuerpos de Playwright no tienen el tope
de 2 MiB que sí aplica al primer run controlado y a `site_diagnostics.py`;
Playwright valida URL antes de continuar pero Chromium no usa el pin DNS curl.
No se afirma cierre de CWE-400 o DNS-rebinding para schedules browser. Ningún
control de las pruebas locales cambia esa condición ni acredita una corrida.

El dictamen también registró XSS en JSON-LD como riesgo posible de una
publicación H1 posterior y una acción OpenCode activable por comentario como
hallazgo fuera de esta ruta. No se cambian `web/**` ni ese workflow: están fuera
del delta CA1 solicitado. La observación histórica de tres URLs UTEC que podrían
refrescar frente a cinco seeds no es una lectura actual ni autoriza saltar el
prefijo de rotación; si CA1/E9 debe acreditar refresh, el owner debe decidir
explícitamente entre discovery-only bajo la rotación vigente y un delta/revisión
de excepción para las tres URLs. No se reabren estados `processed`.

#### Corrección del Code Reviewer y preparación del schedule FG2 — 2026-11-11

La revisión de `5399fc66…` identificó tres defectos aplicables: P1 DNS rebinding
en el guard de Playwright; P1 comparación de la URL cruda del manifest contra la
URL transformada por cleansing; P2 duplicación de enlaces paginados durante una
misma corrida. El candidato corrige el transporte de navegador cerrando todas
las solicitudes HTTP(S) antes de continuarlas, conserva digests separados para
URL cruda y URL canónica de cleansing a través de enrichment/sync y deduplica
cada enlace antes de encolarlo.

El candidato también prepara un camino de `schedule` en `main` separado del
dispatch manual: el orquestador fija run, intento, SHA y perfil/seeds bounded en
un manifiesto; los jobs downstream reciben y verifican su digest. Cleansing
selecciona `staging_raw` por los IDs del manifest; enrichment solo consume
`cleansed_programs` relacionados por `staging_id`; sync deriva los `cleansed_id`
del mismo conjunto y consume únicamente `enriched_programs.pending` relacionado.
Las pruebas sintéticas comprueban aislamiento de filas fuera de cohorte y que
los tres workers no vuelven a la cola global cuando la cohorte está vacía. No se
resetea `processing` ni se reabre `processed`.

Los límites preparados usan `FG2_LIMITS`: hasta 10 instituciones por corrida,
10 URLs únicas y 20 solicitudes HTTP por institución; una solicitud simultánea
por origen, 5 s entre inicios, `Retry-After` hasta 30 s, cap de cuerpo 2 MiB y
redirects/reintentos dentro del presupuesto. Este cambio es local: no activa
schedule, Environment, flags ni writer. La autorización para E10 permanece
posterior a E9 y requiere revalidar la cola remota, permisos y primera ventana.

El snapshot read-only Pro del 2026-11-11 identificó 11 perfiles productivos,
discovery y pipeline habilitados que necesitan Playwright: coderhouse, datapath,
digitalhouse, dmc, educacionit, idat, lewagon, smartdata, soyhenry, tripleten y
upc. El camino scheduled bounded los omite antes de contactar esos orígenes; no
acredita cobertura para ellos. La decisión de alcance queda pendiente: mantener
la exclusión hasta contar con un transporte de navegador con pin DNS y el mismo
presupuesto, o encargar esa implementación y validarla antes de E10. No se
reemplazan datos ni se infiere elegibilidad adicional.

Docker `--network none`, candidato read-only, suites FG2 bounded/orquestación/
workers/workflow: **96 passed, 1 warning** PyPDF2. Dos fallos anteriores de la
prueba nueva fueron solo fixtures incompletos (telemetría y estado `discovered`);
ambos se corrigieron y la suite final pasó. El dictamen del Code Reviewer para
el diff corregido, checker documental candidate-aware, credential scan y guard
del diff siguen como gates antes de solicitar publicación. E9 no se ejecutó;
E10 sigue apagado, los pares válidos siguen en 0/3 y H4 conserva su gate.

#### Revalidación ampliada posterior — 2026-11-11

La revalidación incluyó siete suites afectadas: bounded FG2, workers,
orquestación, contrato de workflow, controles pre-main, recorrido sintético del
pipeline y credenciales Supabase. Resultado final en Docker sin red:
**199 passed, 1 warning** de deprecación PyPDF2. La ejecución expandida previa
detectó nueve expectativas antiguas: el test de manifest no esperaba el hash
canónico adicional, los stubs HTTP no modelaban la sesión con DNS fijado y los
stubs Playwright asumían navegación permitida. Se actualizaron para comprobar
hash dual, pin DNS y bloqueo HTTP(S) sin solicitudes ni filas nuevas; los nueve
casos focales pasan y el conjunto completo queda verde.

El test integrado del scope guard confirma negativos, vecinos rechazados,
selección H1 para PR a Desarrollo y promoción integral separada. Además, la
comparación protegida del candidato de 35 rutas, materializado en un commit
temporal sobre `c736336819bc0a927cc7224a053429e27433a748`, quedó allowlisted.
Checker documental candidate-aware/self-test, `DOC_GATE_PASS` y credential
scan del diff pasaron. El FAIL documental integral H3 `348→348`, listas
idénticas, se conserva sin promoverlo a PASS.

El bloqueo de Playwright aplica a toda invocación del harvester: los once
perfiles indicados arriba no tienen cobertura programada y el dispatch manual
tampoco puede completar esas rutas hasta implementar un transporte compatible
con el pin DNS y el presupuesto. Las demás corridas manuales siguen esperando
aprobación de `Production`; la programación FG1–FG3 en `main` conserva su
ejecución automática sin reviewer por corrida solo después de activación
autorizada. E9 debe acreditarse antes de E10. No se cambió ningún Environment,
flag, secret, writer, schedule, run, dato Pro ni cohorte operativa.

La revisión del Code Reviewer sobre el diff final permanece pendiente; el
dictamen de `5399fc66…` y su NO-GO no se reutilizan como aprobación del nuevo
candidato.

#### Remediación de hallazgos del Code Reviewer — 2026-11-11

El Code Reviewer sobre la huella local `62a09c0a…` no reportó de nuevo los dos
P1 ni el P2 originales; señaló dos P2 adicionales: el CLI documentado
`scripts/maintenance/diagnose_institution.py` no encontraba el paquete raíz
`scripts.core`, y el harvester podía agregar bloqueos por cada URL protegida de
un sitemap sin consumir la cota de URLs únicas.

El ajuste mínimo hace que `site_diagnostics.py` y `fg2_bounded_run.py` acepten
sus dos contextos de importación (CLI: `shared`/`core`; workflow: `scripts.shared`/
`scripts.core`) y conserva el helper compatible `detect_noise_patterns()` que
usa el CLI al importar. En rutas controlled, URLs únicas válidas examinadas
—incluidas filas protegidas— consumen el mismo máximo de diez por institución.
Se registran como bloqueos, no como trabajo elegible, y estados históricos
permanecen intactos. La paginación y los seeds usan el mismo conteo.

Las regresiones sintéticas nuevas ejecutan el CLI sin `PYTHONPATH` ni URL
objetivo, y presentan doce URLs protegidas para probar que el manifest conserva
solo diez bloqueos y que las doce filas siguen `processed`. Docker offline
focal pasó `2/2`; la regresión ampliada, checker documental, scope guard,
credential scan y nuevo dictamen de Code Reviewer quedan asociados únicamente
a la huella corregida, nunca a `62a09c0a…`.

#### Seguimiento del Code Reviewer del schedule — 2026-11-11

La revisión del acumulado `8d3af1a9…` contra `c736336…` emitió NO-GO: el child
ordinario schedule estaba entrando por el contrato `--controlled` que exige el
lote manual; el hash de cleansing no seguía la precedencia
`canonical_url → effective_url → url`; y un resultado schedule `no_op` salía
antes de mover `last_harvest_at`, pudiendo repetir los mismos diez slots de la
rotación. El dictamen se conserva en el changelog H1REQ1.

La corrección local separa `--scheduled-cohort` de `--controlled`: el primer
modo valida schedule/main, manifest ligado al run y límites, pero no solicita
un lote humano; el segundo conserva obligatoria la referencia y huella del lote
revisado. La URL hash downstream usa la identidad normalizada que cleansing
selecciona, conservando además el hash de URL solicitada. En un schedule sin
filas modificadas, el manifest sigue marcando `no_op` y se actualiza el
timestamp de intento para permitir la rotación; no se registra como refresh ni
como ejecución funcional.

Las regresiones de modo, precedencia de URL y rotación pasan en Docker
`--network none`; las siete suites focales ampliadas quedaron **207 passed, 1
warning** (deprecación PyPDF2). El dictamen del Code Reviewer sobre la nueva
huella y el checker documental de la documentación corregida aún están
pendientes antes de solicitar publicación.

La consulta actualizada de Pro no se completó: `supabase-pro/get_project_url`
falló en la renovación OAuth antes de una consulta de datos. No se sustituyó el
MCP por otro transporte. La lectura histórica del 2026-11-11 conserva 11
perfiles que requieren Playwright y quedarían sin cobertura de schedule/manual
hasta un transporte de navegador compatible con DNS pinning y presupuesto. La
decisión E10 sigue siendo diferirlos explícitamente o mantener E10 cerrado
mientras se prepara tal transporte. E9 antecede a E10; no hubo cambios remotos,
contacto institucional ni escrituras Pro.

#### Hallazgos de Code Reviewer y corrección focal — 2026-11-11

La revisión de `0309ed4b…` confirmó los tres fixes, pero dejó NO-GO con tres
P2 adicionales: el redirect target no consumía el límite de URLs únicas; sync
repaginaba toda `courses` por cada fila acotada; y un perfil schedule
`sitemap_bfs` podía tratar una página de catálogo seed como XML y registrar un
NO-OP sin usar el sitemap de origen. La corrección local hace reservar cada
redirect antes del siguiente request, mantiene una copia run-scoped del
inventario de cursos para verificaciones de alias (con comprobación exacta por
ID aprobado y actualización de la copia después del upsert), y fija el seed de
schedule `sitemap_bfs` a `{website_url}/sitemap.xml`, igual que la ruta ordinaria
preexistente. La selección se decide en preflight y queda ligada al hash de
seeds del manifest antes de contactar el origen.

Pruebas focales nuevas verifican tope de redirect, seed sitemap de schedule y
una sola lectura de inventario por worker. El candidato requiere volver a pasar
las suites Docker, checker documental y Code Reviewer sobre la nueva huella;
este addendum no declara todavía esos gates ni autoriza publicar el PR.

#### Corrección de hallazgos adicionales Code Reviewer — 2026-11-11

El Code Reviewer de `f7aa2472…` dejó NO-GO con dos P2: el lote manual `sitemap_bfs`
podía enviar seeds de página al parser de sitemap, y el harvester podía marcar
como `new_discovery` una ruta de detalle que cleansing consolida en una URL de
curso existente. La corrección mantiene separados los modos: el schedule usa
el sitemap raíz fijado en preflight; el lote manual procesa sus seeds aprobados
como candidatos exactos, sin expansión fuera de alcance. La clasificación del
camino ordinary usa la misma limpieza de sufijos de URL que cleansing antes de
resolver el curso existente y registrar su ID.

La prueba de página seed y la prueba de alias se ejecutaron primero en estado
RED contra `f7aa2472…` y fallaron como se esperaba. Se preservó además el caso
de un seed XML legítimo dentro del lote manual. Después de implementar el
ajuste, las seis suites focales de FG2, workers/manifiesto, workflow,
controles main/manual y recorrido sintético pasaron **167/167** en Docker
`--network none`, con una advertencia deprecada PyPDF2. El checker
candidate-aware pasó `DOC_SELF_TEST_PASS`/`DOC_GATE_PASS` con 769/769 fuentes,
122/122 documentos activos y 433/433 históricos; el nuevo dictamen de Code
Reviewer sigue pendiente sobre la huella final. El FAIL integral histórico
`348→348`, listas idénticas, se conserva. Este cambio no ejecuta workflows ni
cambia filas, workers, URLs remotas, cron o ambientes.

#### Remediación de findings de Code Reviewer — 2026-11-11

La revisión del candidato `e22455c0…` contra `c736336819bc0a927cc7224a053429e27433a748`
terminó NO-GO con tres defectos: `new_discovery` podía tomar la primera fila no
relacionada de `courses` como destino del upsert; una denegación del guard de DNS
antes del primer HTTP fallaba al persistirse en el manifest; y las suites FG2
bounded declaradas en el scope de CI no estaban en el comando efectivo de
pytest. La corrección mantiene el inventario como comprobación de colisión y
deja `existing` vacío para una fila nueva; admite `deferred` sin hora de inicio
HTTP, mientras que `blocked` continúa exigiendo que haya ocurrido el request;
y suma las cuatro suites FG2 al allowlist `python-check`.

Las tres regresiones focales se ejecutaron primero en Docker sin red y fallaron
por los motivos reportados; después pasaron **3/3**. La regresión completa de
seis suites FG2/orquestación/workers/workflow/main-manual/pipeline pasó
**169/169**, con una advertencia deprecada PyPDF2. No se ejecutó CI remoto y no
se infiere de esta prueba local. Checker candidate-aware: `DOC_SELF_TEST_PASS`,
`DOC_GATE_PASS` (769/769 fuentes asignadas, 122/122 documentos activos,
433/433 históricos); credential scan exacto de las 35 rutas: PASS; `git diff
--check`: PASS. Falta dictamen del Code Reviewer de la nueva huella; no se
declara aún el candidato apto para PR. No hubo tráfico institucional, Pro, DML,
commit, push, PR, cambio de flags ni activación E10.

#### Serialización del worker frente a Production Canary — 2026-11-11

El dictamen sobre `359c32fd…` encontró un P2: el lector cleansing de la cohorte
manifestada dejaba las filas en `pending` mientras procesaba; el `lock_staging_records`
del camino ordinario y la estación cleansing de `production_canary.yml` podían
competir. Una reclamación exacta transaccional exigiría otro contrato DB/RPC y
quedaría fuera de esta reparación local sin aprobación JIT de DB. Para los
callers actuales de Actions, la salvaguarda mínima es compartir en ambos
workflows el grupo root `studiamatch-fg2-${{ github.ref }}` con
`cancel-in-progress: false`. GitHub permite que workflows distintos del mismo
repositorio se excluyan al compartir un grupo; el test local de workflow verifica
igualdad exacta. Esto no cambia la API de worker ni crea un claim por fila; el
guard de main/protecciones siguen aplicando.

La prueba de concurrencia fue RED antes del ajuste y GREEN después. Las seis
suites FG2 bounded/orquestación/workers/workflow/main-manual/pipeline pasan
**170/170**, 1 warning de deprecación PyPDF2. Es evidencia de YAML/contrato
local; no simula la cola remota ni acredita settings GitHub. Tras actualizar las
notas: checker documental candidate-aware `DOC_SELF_TEST_PASS` y `DOC_GATE_PASS`
(769/769 fuentes, 122/122 activos, 433/433 históricos), credential scan en las
35 rutas PASS y `git diff --check` PASS. Un Code Reviewer debe cerrar la nueva
huella antes de pedir PR. E9 sigue antes de cualquier activación E10 y no se
ejecutó ningún writer.

#### Seguimiento Code Reviewer: pin DNS y lecturas del lote — 2026-11-11

El Code Reviewer de la huella `6d487f0a…` contra Desarrollo
`c736336819bc0a927cc7224a053429e27433a748` emitió NO-GO con dos hallazgos:
P1, el pin `CurlOpt.RESOLVE` se entregaba como string aunque `curl_cffi` requiere
una lista de entradas; P2, la revalidación del lote llamaba `select_all` sin
filtro sobre `staging_raw` y `courses`, paginando tablas completas repetidamente.
No se trasladó ese dictamen a un SHA nuevo ni se hicieron operaciones remotas.

La remediación local preserva la resolución y validación por salto, pero pasa el
pin como `[resolve_entry]` en `UniversalHarvester` y `site_diagnostics.py`; los
redirects públicos reciben una sesión nueva con su propio pin. La regresión usa
el binding `Curl.setopt()` de Docker sin request, y fixtures comprueban la
primera solicitud y cada redirect para ambas rutas curl. No cubre Playwright.

El lookup aprobado ahora agrupa exclusivamente las URLs del lote por
institución, usa patrones anclados que cubren las formas equivalentes de
`normalize_url` y consulta únicamente esos aliases; staging y cursos conservan
owner, ID, estados y hashes, y cleansing/enrichment revisan también los IDs
downstream aprobados. Cada lectura se limita a `cantidad de URLs/IDs + 1` para
detenerse ante una fila ambigua sin paginar. El máximo es seis lecturas por
institución, hasta 60 en un lote de 10 instituciones, con hasta 11 filas por
respuesta; no es un snapshot productivo ni un claim transaccional.

Las siete suites afectadas de lote, orquestación, workers, workflow,
main/manual, recorrido sintético y seguridad del diagnóstico dieron **180
passed, 10 subtests passed y 1 warning** (deprecación PyPDF2) en Docker
`--network none`, filesystem read-only. Las regresiones reprodujeron primero el
pin escalar, el scan completo y el alias query tardío, y quedaron en verde tras
los cambios. El Code Reviewer debe dictaminar el diff corregido completo después
de consolidar las notas. El FAIL integral de documentación `348→348` conserva
su estado separado.

E10 sigue preparado pero inactivo; la prueba/local YAML muestra que el
manifestado limita cleansing a staging IDs de la cohorte en `pending`,
enrichment a cleansed rows relacionadas y sync a enriched rows `pending`
relacionadas. Esto no identifica IDs actuales de Pro. Los once perfiles que
requieren Playwright (`coderhouse`, `datapath`, `digitalhouse`, `dmc`,
`educacionit`, `idat`, `lewagon`, `smartdata`, `soyhenry`, `tripleten`, `upc`)
siguen sin cobertura/refresh en este camino. Antes de E10 Romel debe elegir:
mantenerlo cerrado hasta validar un transporte browser acotado, o aceptar
explícitamente su omisión temporal y el riesgo de que F10.9 siga incompleto.
E9 funcional antecede a esa activación. Schedule automático en main y revisión
Production en ejecuciones manuales siguen siendo la política; no se cambió
ningún Environment, flag, workflow, run ni dato Pro.

#### Guard del lote manual frente a schedule — 2026-11-11

El Code Reviewer del acumulado de 35 rutas 3d66cb01…, contra Desarrollo
c736336819bc0a927cc7224a053429e27433a748, confirmó los tres fixes asociados
a 5399fc66… y encontró un P2 adicional: el validador del modo
controlled_first_run exigía el binding del lote, pero no el evento manual.
Por tanto un schedule en main con esos parámetros podía intentar el lote
humano aprobado dentro de la ruta automática.

La corrección local hace que validate_harvester_run_mode exija a ese modo
GITHUB_EVENT_NAME=workflow_dispatch y GITHUB_REF=refs/heads/main antes de
aceptar el lote. scheduled_cohort conserva su contrato independiente de
schedule + main y rechaza cualquier binding del lote manual. La nueva
prueba fue RED ante schedule, y GREEN tras la guarda; confirma también que el
modo manual válido sigue pasando y que desarrollo se rechaza.

Sobre el diff corregido, las siete suites focales corrieron en Docker
--network none, checkout read-only: 181 passed, 10 subtests passed, 1
warning de deprecación PyPDF2. Revisión documental candidate-aware y nuevo
dictamen del Code Reviewer están pendientes sobre la huella consolidada; no se
traslada el NO-GO del candidato anterior ni se afirma aptitud para PR.
No hubo contacto institucional, Pro, DML, ejecución workflow, push o PR.
E9 sigue pendiente, E10 permanece inactivo y H4 conserva su gate.

#### Resultado Code Reviewer: sitemap deferred y alias de curso — 2026-11-11

Sobre el acumulado de 35 rutas c603b3fd… el Code Reviewer emitió NO-GO con
tres P2: agotar el presupuesto durante el sitemap podía dejar filas discovered
fuera del manifest; el lookup schedule por URL exacta podía omitir un curso con
la variante /en/; y un seed manual /presentacion no heredaba el course_id de
la URL padre que cleansing agrupa con ese detalle.

La remediación local deja en memoria los enlaces parciales cuando el crawler
termina deferred/blocked por presupuesto, sin crear staging rows para candidatos
que no podrán procesarse en ese run. La identidad de curso se deriva con la
misma normalización y cleanse_course_url que usan cleansing/sync. Schedule y
lote revisado consultan aliases acotados; un snapshot de lote puede vincular la
URL de detalle con el row courses padre y valida ID, owner, estados y last_404_at.
Un lote que contenga dos URLs que colapsan al mismo curso se rechaza antes del
contacto. No se reabren ni alteran estados históricos.

Tres regresiones fixture-first fallaron antes y pasan después en Docker
--network none. Las siete suites FG2/pre-main/pipeline: 185 passed,
10 subtests passed y una advertencia PyPDF2. El alcance sigue siendo local;
sin snapshot Pro, el número de rows hijas queda determinado por el manifest y
las relaciones reales de cada run, no por un supuesto máximo de 100 filas.
El candidato debe pasar checker documental, scan de credenciales, guard de
rutas y Code Reviewer sobre su nueva huella antes de solicitar publicación.

#### Curso guardado como detalle y ejecución parcial — 2026-11-11

La revisión siguiente, sobre el mismo acumulado de 35 rutas `03d52e43…`, dio
NO-GO con dos P2. El filtro de alias podía omitir una fila `courses.url` que ya
almacenaba `/presentacion`, creando clasificación de descubrimiento o duplicado.
Además, si una página cosechada correctamente precedía a un error HTTP no
bloqueante, el job del harvester fallaba y GitHub Actions no lanzaba cleansing;
el registro exitoso quedaba `pending` fuera de downstream.

La corrección extiende el filtro acotado con identidad normalizada, URL pedida y
sufijos detail conocidos, con rechazo ante ambigüedad. El resultado de corrida
`partial` permite downstream solo cuando existe al menos una entrada exitosa
del manifest; cleansing/enrichment/sync siguen limitados a sus IDs y relaciones
exactas. El schedule registra el intento para mantener la rotación. Un run sin
éxitos conserva fallo. No cambia estados históricos ni el límite de cohort.

Docker `--network none`: los seis suites afectados reportaron **187 passed, una
advertencia PyPDF2** y las diez regresiones focales resultaron GREEN; se mantiene
pendiente repetir checker candidate-aware y credential scan tras la
documentación consolidada, fijar la nueva huella y obtener Code Reviewer. Esto
solo prueba fixtures/contratos, no lectura Pro, E9, contacto institucional o
habilitación E10.

#### P2 de identidad URL al escribir sync — 2026-11-11

El Code Reviewer sobre `e055a6db…` encontró que `SyncVectorWorker` identificaba
la fila aprobada por `course_id`, pero validaba su URL almacenada con
`normalize_url` frente a la URL base de cleansing. Si `courses.url` conserva
`/presentacion`, `/beneficios` u otro sufijo de detalle reconocido, la
comparación no coincide y detiene el refresh antes del writer.

El delta local usa `course_identity_url` tanto para comparar el inventario como
para volver a validar la fila leída por ID. Mantiene rechazo por duplicidad,
ID, institución o identidad distinta, y conserva el URL exacto de la fila como
destino de upsert. La fixture `/presentacion/` falló antes del ajuste y pasa
después; la prueba existente de alias ambiguo sigue rechazando antes de escribir.
Las siete suites afectadas pasan **233/233** en Docker `--network none`, con una
advertencia PyPDF2. Checker candidate-aware H1, guard de rutas, credential scan
y diff check pasan. El Code Reviewer debe revisar la huella corregida antes de
solicitar una publicación/PR.

Esto no prueba filas ni relaciones actuales de Pro. Los workers programados
siguen restringidos al manifest exacto y a sus relaciones/estados elegibles; un
límite de 100 URLs de manifest no limita las filas hijas que puedan existir por
relación uno-a-varios. E9 continúa pendiente, E10 inactivo y H4 gated.

#### Hallazgos de avance del sitemap y cierre 403/429 — 2026-11-11 15:24 -05

El Code Reviewer del candidato `6b99c9e7…` emitió NO-GO con dos hallazgos
aplicables al schedule FG2: (1) las filas protegidas (`pending`, `processing`,
`processed`, `discarded`, `skipped` o `error`) al inicio del sitemap agotaban
el cap de diez antes de llegar a URLs elegibles; (2) el GET controlado recibía
y acumulaba body de una respuesta 403/429 antes de parar el origen.

La reparación local no amplía la rotación ni reabre estados: las filas
protegidas se registran como blockers, con un máximo de diez diagnósticos por
institución, pero no cuentan contra el cap de URLs cosechables. La búsqueda
continúa hasta diez URLs únicas nuevas o `discovered` elegibles. El transporte
controlado usa stream, revisa 403/429 y detiene el origen antes de iterar el
body; señala el evento de aborto y espera el cierre asíncrono del stream para no
competir con la liberación del handle. Para los demás estados acumula hasta
2 MiB por bytes, no por `Content-Length`; al exceder, cierra y falla antes de
parseo o escritura staging. La implementación instalada puede haber puesto el
primer chunk en la cola del transporte antes de entregar el response; el
harvester lo deja sin consumir al detectar 403/429.

**Prueba de impacto:** Docker `studiamatch-dev:local`, `--network none`,
candidato de solo lectura: diez escenarios focales pasaron, incluidos sitemap
con prefijo protegido de 12 filas, cuerpos chunked sin longitud, corte por
presupuesto, cierre 403/429, ausencia de reintento y manejo de teardown
asíncrono. Siete suites de orquestación/run/workers/workflow/pre-main/pipeline/
credenciales: **235 passed, 1 warning** (PyPDF2). La prueba loopback se limita a
`127.0.0.1` del contenedor aislado; no contacta instituciones ni servicios
externos. El checker candidate-aware/self-test pasó:
`DOC_SELF_TEST_PASS`, `DOC_GATE_PASS` (769/769 fuentes, 122/122 documentos
activos, 433/433 históricos); `scan_credentials.sh --tree` pasó al montar el
gitdir común solo lectura. Se reutiliza el guard previamente aprobado para las
mismas 35 rutas, sin alta ni baja de rutas. `git diff --check` se revalida tras
esta actualización documental y pasó; el Code Reviewer del diff corregido
sigue pendiente antes de pedir publicación.

**E10 y alcance de downstream:** el job schedule liga run/attempt/SHA al
manifiesto; cleansing consume solo `staging_raw` elegible por los IDs del
manifest; enrichment consume `cleansed_programs` elegibles enlazados por esos
`staging_id`; sync consume `enriched_programs` elegibles de los `cleansed_id`
derivados. Un manifiesto vacío no activa una cola global. Las relaciones pueden
ser uno-a-varios, por lo que diez URLs por institución o cien entradas no
constituyen un límite de filas downstream; el efecto concreto se define por IDs,
relaciones y estados elegibles. No hay snapshot Pro actualizado en este ciclo y
no se afirman IDs ni cardinalidades actuales.

Los once perfiles que necesitan Playwright continúan excluidos del transporte
seguro actual y no reciben cobertura por este schedule: `coderhouse`,
`datapath`, `digitalhouse`, `dmc`, `educacionit`, `idat`, `lewagon`,
`smartdata`, `soyhenry`, `tripleten`, `upc`. Eso aplaza su refresh y puede
mantener cursos incompletos; no prueba que hoy tengan filas elegibles ni
autoriza sustituir instituciones. Decisión pendiente para E10: mantener la
programación cerrada hasta validar un transporte browser con pin DNS y límites
equivalentes, o aceptar explícitamente la omisión temporal y su riesgo para
F10.9. En cualquiera de los casos E9 debe acreditarse antes de activar E10;
schedule automático en `main` para FG1–FG3 y aprobación de `Production` para
manuales se conservan como política, sin habilitación en este ciclo.

#### Revisión P2: avanzar rotación tras `blocked`/`deferred` — 2026-11-11

El Code Reviewer del diff de 35 rutas detectó que el schedule escribía el
resultado `blocked`/`deferred` en el manifest, pero no actualizaba
`institutions.last_harvest_at`. Dado el orden `last_harvest_at ASC NULLS FIRST`,
un perfil detenido podía volver a ocupar los mismos slots diarios y demorar la
cohorte siguiente.

El delta local llama `_record_scheduled_attempt` tras guardar el resultado en
cada una de las tres salidas de `universal_harvester.py` que capturan el stop:
tras discovery, durante extracción y en el cierre controlado del error. El
marcador solo se escribe con `--scheduled-cohort`; el estado manifest permanece
`blocked`/`deferred`, sin insertar, reabrir o actualizar filas del catálogo.
El siguiente run puede ordenar por el nuevo timestamp; la marca es un intento,
no prueba funcional ni refresh.

Pruebas Docker `--network none`, candidato de solo lectura: 4 casos focales
passed y las siete suites afectadas **237 passed**. No hay snapshot Pro ni se
realizan llamadas institucionales; las relaciones downstream permanecen
limitadas al manifest y sus estados/IDs. E9 sigue siendo gate previo a E10; la
programación continúa desactivada y H4 conserva su gate. El Code Reviewer debe
dictaminar el diff final antes de preparar publicación.

#### P2: hash de URL persistida y lookup por aliases — 2026-11-11

El Code Reviewer del snapshot `0415a7e…` detectó que una entrada con staging
`discovered` podía preservar en el PATCH una URL exacta del snapshot, por
ejemplo `/en/` o slash final, mientras `entries[].url_sha256` guardaba el hash
de la URL normalizada. Cleansing compara con el URL que realmente leyó de
`staging_raw` y rechazaba ese lote. También detectó que el caso sin staging en
el snapshot recorría toda `staging_raw` por cada URL aprobada para buscar
aliases aparecidos después del preflight.

El cambio local calcula el hash de la entrada sobre el URL exacto que el PATCH
preservará; el hash de scope del lote sigue describiendo la identidad de la URL
normalizada. El lookup post-contacto aplica `institution_id` del scope aprobado
y `approved_url_alias_filter` sobre una sola URL en la misma consulta a
`staging_raw`, con `limit=2`. Detecta deriva/ambigüedad de esa institución antes
del writer, no pagina el backlog ni mezcla instituciones. No se modifica
cleansing, no se reabre estado ni se expande la URL autorizada.

Las regresiones Docker reprodujeron ambos hallazgos antes del arreglo y luego
pasaron; las cuatro pruebas focales pasan y las siete suites afectadas pasan
**239 tests** en `--network none`. El checker candidate-aware/self-test, el
escaneo de credenciales del árbol, el guard de scope de 35 rutas y
`git diff --check` pasan. El Code Reviewer de la nueva huella sigue pendiente.
La publicación sigue separada; E9 antecede a E10, y la cobertura de Playwright
requiere decisión humana antes de programar esos perfiles.

#### NO-GO: avance parcial de sitemap, sitemap comprimido y cola E10 — 2026-11-11

El Code Reviewer de `3eca3d7a…` confirmó el manejo de los hallazgos de
`5399fc66…`, pero encontró tres P2 adicionales: el presupuesto agotado podía
descartar enlaces ya recibidos de un sitemap index; `.xml.gz` se reconocía
como sitemap, pero el parser recibía bytes gzip; y el dispatch de Production
Canary podía reemplazar el único run pendiente del grupo de concurrencia
compartido con el schedule FG2.

La remediación local conserva, solo para `scheduled_cohort`, enlaces extraídos
de respuestas sitemap completas antes de un stop por presupuesto/bloqueo. Los
URLs permitidos se guardan como `staging_raw.discovered` y
`manifest.discovery_rows`; el run queda `deferred`/`blocked`, no añade filas a
`manifest.entries` y no habilita downstream para esos candidatos. Un schedule
posterior los retoma si siguen publicados. El lote manual conserva su frontera
exacta y no guarda candidatos parciales que no pueda procesar.

Seeds controladas `.xml.gz` fallan en preflight antes de contactar el origen.
Si una respuesta sitemap ya leída anuncia `.xml.gz`, se difiere antes de
solicitar ese recurso. No se añade descompresión; el tope del cuerpo se
mantiene.

**Control operativo E10 preparado, no aplicado:** los workflows
`production_pipeline.yml` y `production_canary.yml` conservan su concurrency
compartida para impedir writers simultáneos. Actions admite un único run
pendiente por grupo y un dispatch puede reemplazarlo. Antes de E10 hay que
leer ambos flujos y dejar cero runs queued/waiting/in progress. Durante E10,
no despachar FG2 ni Production Canary mientras cualquiera de los dos flujos
FG2 esté queued, waiting o in progress. Un run manual que aguarda aprobación
Production debe terminar o cancelarse bajo el procedimiento humano antes de
la siguiente ventana diaria 05:00 UTC. Si una corrida natural falta, se
reemplaza o cancela, no acredita el par; aplicar la parada del plan y reiniciar
la observación. El cron diario y timeout de seis horas acotan schedule contra
schedule en operación normal, pero no sustituyen la lectura de cola. Una cola
FIFO estructural exigiría decisión/diseño separado; no se altera YAML ni la
concurrencia aquí.

La recomendación Playwright se mantiene: no activar E10 hasta disponer de un
transporte browser con pin DNS y límites equivalentes. Si el owner quiere
aceptar temporalmente la omisión de los once perfiles, requiere una decisión
explícita y el riesgo de prolongar el incumplimiento de cero incompletos. E9
funcional continúa como gate previo; descubrimiento, manifest sin entries o
SUCCESS con funcionales omitidos no acreditan refresh.

#### Compatibilidad de la ruta Playwright ordinaria — 2026-11-11

El Code Reviewer de `53ecb6d…` detectó que el interceptor de red agregado al
helper común abortaba también toda navegación HTTP(S) de FG2 ordinario. La
corrección elimina ese interceptor: con `self.controlled=true`, el helper
rechaza antes de `page.goto` y el modo acotado no consume fuentes mediante
Playwright; con el modo ordinario, conserva `page.goto` preexistente después de
validar la forma de la URL inicial. Esa ruta ordinaria no usa el pin DNS ni los
presupuestos de `curl_cffi`, por lo que queda bajo la aprobación manual de
`Production` y no acredita E9 acotado ni cobertura E10. Los once perfiles
Playwright continúan fuera del schedule bounded. E10 no se activa hasta validar
transporte browser con pin y límites equivalentes o hasta recibir una decisión
explícita del owner sobre su exclusión temporal y el riesgo de incompletitud.
La regresión se cubre con fixtures sintéticos; no hay tráfico institucional.

#### P2: conservar el modo de cohorte en la instancia — 2026-11-11

Code Reviewer encontró que el CLI principal ya pasaba `scheduled_cohort=True`
al constructor, pero `UniversalHarvester` no conservaba el valor. Tras un
bloqueo o agotamiento del presupuesto del sitemap, el guard podía tratar el
schedule como lote manual y descartar enlaces ya recibidos. El fixture de
sitemap parcial asignaba el atributo a mano, lo que no cubría el caller real.

El constructor fija ahora `self.scheduled_cohort` desde el argumento. El test
pasa el modo mediante el constructor, comprueba el atributo y recorre dos
corridas sintéticas: candidatos parciales quedan `discovered`, no se agregan a
`manifest.entries` del run diferido, y una ventana posterior los puede retomar.
La prueba focal Docker `--network none` pasó 1/1; las siete suites afectadas
pasaron **245 tests** con un warning PyPDF2. No se amplían los límites HTTP ni
el alcance del manifest.

E9 sigue pendiente y E10 no se activa. El cambio no altera la política de
schedule automático en `main` ni la aprobación manual de `Production`; la
primera sigue sujeta al cierre funcional E9, controles de cola y lectura de
Environment antes de activarse. Los once perfiles Playwright sin transporte
bounded conservan su pendiente explícita. Sin tráfico institucional ni writes
Pro.

#### Hallazgos de revisión post-merge de #552 — 2026-11-12

La revisión automatizada de `certificacion@d36fd103…` dejó abiertos un P1 y un
P2, aunque #552 recibió review humana y se integró. El P1 señaló que la
respuesta de `curl_cffi` decodifica `Response.content`; escribir únicamente en
`_content` de estilo requests devolvía diagnóstico HTML vacío. La corrección
asigna los bytes acotados a `Response.content` antes de leer `.text`. La prueba
nueva usa `curl_cffi.requests.Response` real con un iterador de chunks sintético;
los fixtures anteriores también modelan `content`, no `_content`.

El P2 señaló que `manifest.entries` podía incluir una fila `discovered` antes
de confirmar su PATCH a `pending`. El harvester ahora prepara el objeto de
entrada y lo publica en el manifiesto solo después de que
`_promote_discovered_to_pending()` confirma identidad y estado. Si el PATCH
devuelve error, el harvester hace una lectura limitada por el ID exacto y
comprueba ID, `pending`, institución, URL y hash. Solo si los cinco valores
coinciden con el payload aprobado acepta la promoción y agrega la entrada al
manifiesto. Esto cubre la respuesta perdida después de que el servidor aplicó
el PATCH. Si la lectura falla o el registro no coincide, se detiene sin agregar
la entrada y exige reconciliación; no se asume que la fila siga `discovered`.
Los workers no consumen esa URL sin una entrada válida en el manifiesto. No se
reabren filas `processed`, ni se cambia el contrato de hashes, IDs o ediciones
editoriales.

**Fallo posterior al PATCH confirmado:** si falla el append atómico del
manifiesto después de verificar que la fila ya está `pending`, esa URL queda
fuera de las entradas válidas del manifiesto. El harvester puede terminar con
resultado `partial`: si ya confirmó otras entradas, downstream puede procesar
esas entradas válidas; la fila sin entrada queda excluida. Si no confirmó
ninguna, el harvester falla y downstream no continúa. En ambos casos se
conservan run ID/attempt, SHA de origen, manifiesto de lote aprobado, error y
staging ID; E10 permanece cerrado y no hay reintento automático. Antes de otro
dispatch, una persona revisa en solo lectura ese ID exacto y compara
institución, URL, `content_hash`, estado y artefactos del run contra el lote
aprobado. No se consume una cola global `pending`, no se reconstruye una cohorte
desde conteos y no se reabre ni resetea el estado automáticamente. Si la
evidencia completa permite preparar un manifiesto de recuperación del mismo
lote, ese artefacto debe pasar las validaciones locales y recibir
revisión/autoridad específica antes de que cleansing, enrichment o sync lo
consuman. Si no puede reconstruirse cada campo del manifiesto o la fila no
coincide, se detiene el ciclo y se solicita una decisión JIT exacta para
reconciliar el estado; ninguna DML queda autorizada por este procedimiento.

La primera corrida Docker mostró ambos tests de regresión fallando con el
código anterior. La suite completa detectó además dos fixtures sintéticos
antiguos incompatibles con el contrato real de `curl_cffi`; se ajustaron para
modelar `content` y se repitieron las suites. Validación final, Docker
`--network none`, fixtures sintéticos y checkout montado read-only:
`test_h3req1_local_pipeline_walk.py` + `test_fg2_bounded_orchestration.py`,
118 tests PASS; `test_site_diagnostics_security.py` + las suites bounded run,
workers y workflow, 73 tests y 10 subtests PASS. `py_compile` de ambos módulos
PASS. Cada grupo conserva un warning de deprecación PyPDF2. El Code Reviewer
identificó la respuesta perdida como caso adicional; una regresión sintética
que aplica el PATCH y luego lanza error valida ahora la reconciliación exacta.

Este resultado es local y no autoriza publicar, abrir PR, merge, Pro, dispatch,
writers ni schedules. Se requiere dictamen del Code Reviewer sobre el diff
corregido antes de preparar el PR protegido a Desarrollo. E9 sigue precediendo
a E10 y el gate FG3 conserva su decisión owner independiente.
