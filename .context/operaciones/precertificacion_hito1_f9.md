# Precertificacion Local Hito 1 F9

> **Identidad historica:** `FASE-09`, `F9`, `fase09-*` y la frase de autorizacion de esta nota identifican exclusivamente el package local implementado/remediado por PR #231/#232 y cerrado por PR #233. [ADR-0003](../decisiones/ADR-0003_taxonomia_macrofases_subfases.md) lo mapea a F9.1. No significa que la macrofase F9 este completa y no autoriza trabajo futuro.

Esta nota define el alcance ejecutable de `FASE-09` bajo `H1-CA2P`. F9 es exclusivamente local y offline respecto de bases, APIs y providers: no autoriza leer o mutar Supabase Free/Pro, cargar credenciales, ejecutar parity remoto, despachar workflows manuales, pausar writers remotos, crear respaldos remotos ni ejecutar backfill.

Registro historico no reutilizable: la ejecucion original requirio la frase `Ejecuta las tareas pendientes de la Fase 09` despues de fusionar su definicion. Esa frase no autoriza ninguna subfase vigente.

## Objetivo

Cerrar los gaps locales indispensables antes de solicitar una fase Free posterior, conservando byte-identico el candidate F8 y su status `reconciled_not_certified` con ambos targets bloqueados.

F9 aporta evidencia directa a `H1-CA2P`; no crea criterios, subtareas, migrations ni manifests nuevos y no cambia el alcance de `HITO-001`.

## Entregables Exactos

1. Ejecutar el payload de las cuatro entradas del manifest F8 mediante un fixture local `public.exec_sql(text)` en PostgreSQL 17 efimero.
2. Probar commit atomico de los marcadores `20260724_fase06_g1b_reconciliation`, `20260724_fase06_hito1_editorial_contract`, `20260725_fase07_g1b_closure` y `20260725_fase08_hito1_functional_closure`.
3. Probar rollback total por fault injection en el verifier final: cero marcadores nuevos y ausencia de los efectos de schema/funciones del package. Una segunda ejecucion del runner debe detectar cero pendientes sin reenviar SQL.
4. Paginar la lectura contractual del ledger usada por parity mediante una funcion pura testeable, sin ejecutar `check_db_parity.py` como CLI ni cargar ambientes. Cubrir 1001 filas, HTTP/error de transporte, JSON invalido, pagina incompleta y nombres duplicados.
5. Retirar la nomenclatura y bookkeeping legacy de tres intentos de enrichment. Conservar exactamente un intento por ID por sesion y aborto fail-fast cuando la persistencia no se demuestra; providers, smart mock, gates y estados ETL no cambian.
6. Precisar en el runbook editorial que plan de backfill, aplicacion de schema Free, ejecucion de backfill y certificacion Free son gates distintos, sin SQL ejecutable ni cohortes reales.
7. Agregar el job bloqueante `fase09-pre-free`, con nombre `FASE-09 Pre-Free Local Contract`, al agregador `security-audit`.
8. Registrar resultados local, CI y post-merge en esta nota.

La dependencia textual de policies queda aceptada fail-closed sobre PostgreSQL 17. Su compatibilidad con la version real de Free se verifica read-only en una fase remota posterior; F9 no altera policies ni verifiers.

## Allowlist F9

- `scripts/maintenance/db_migrate.py` solo para exponer/probar el payload local existente; no se ejecutan modos remotos.
- `scripts/maintenance/check_db_parity.py` solo para extraer paginacion pura; su `main`, carga de environment y requests reales no se ejecutan en F9.
- `scripts/core/enrichment_worker.py` solo para reconciliar nombres/comentarios/bookkeeping con el fail-fast vigente.
- `tests/test_fase09_db.py` y `tests/test_fase09_workers.py`.
- `tests/sql/fase09_exec_sql_fixture.sql`, `fase09_functional_test.sql` y `run_fase09_postgres.sh`; `tests/run_fase09_local.ps1` solo para orquestar Docker con cleanup `finally`.
- Lectura sin modificacion de `tests/sql/fase08_minimal_baseline.sql`, las cuatro migrations F6-F8 y `db/manifests/fase08_candidate.json`.
- `.github/workflows/security-audit.yml` solo para el job F9 automatico, sin environment ni secrets.
- `db/operations/editorial/README.md` solo para separar gates futuros; no puede contener SQL ejecutable ni cohortes reales.
- `.context/00_INDICE.md`, `estado_del_proyecto.md`, `backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md`, `changelog/2026-07-25.md`, `operaciones/flujo_release_minimo.md` y esta nota.

Todo path no enumerado queda fuera de F9. En particular, `.github/workflows/db-sync-to-pro.yml`, migrations y manifests quedan excluidos.

## Fixture Exec SQL

- Existe solo en `tests/sql/fase09_exec_sql_fixture.sql` y solo dentro de la DB efimera `studiamatch_f9`.
- Firma: `public.exec_sql(sql_text text) RETURNS jsonb`, `SECURITY DEFINER`, owner `postgres`, `search_path=''`.
- Revoca `PUBLIC`, `anon` y `authenticated`; concede execute solo al `service_role` sintetico.
- F9 no agrega ni modifica una definicion productiva. La migration legacy `20260510_pro_schema_sync.sql`, fuera del package F8, permanece inventariada e inmutable; el test distingue esa definicion conocida del fixture.
- `run_fase09_postgres.sh` registra un trap que elimina el fixture aun ante fallo; `run_fase09_local.ps1` destruye contenedor/red en `finally`. Se verifica que el diff no agregue otra definicion `exec_sql`.

## Aislamiento Mecanico

- Los comandos F9 se ejecutan con `env -i`, PATH/PYTHONPATH explicitos y sin variables `SUPABASE`, `CF_*`, `OPENCODE_*` o `RESEND_*`; `NEXT_*` solo admite los dos placeholders publicos exactos del build frontend. El runner aborta ante cualquier otro valor.
- No se leen `.env*`, gestores de secretos, GitHub environments ni Supabase MCP. Los tests interceptan `dotenv.load_dotenv`, `dotenv_values`, `open` y `Path.open/read_text` para fallar si un path `.env*` es consultado.
- `db_migrate.py` solo puede ejecutarse con `--validate-only`; `--dry-run` y modos normales quedan prohibidos fuera del RPC sintetico.
- `check_db_parity.py` no se ejecuta como CLI. Sus pruebas reemplazan transporte y socket para fallar ante cualquier egress DB/API/provider inesperado.
- `TEST_DATABASE_URL` acepta solo esquema `postgresql`, usuario `postgres`, puerto `5432`, DB `studiamatch_f9` y host `127.0.0.1`, `localhost` o `studiamatch-f9-postgres`; rechaza query params, dominios Supabase y cualquier otro host.
- Fixtures usan UUID deterministas, dominios reservados y provenance sintetica; nunca Free, Pro, backups, exports o artifacts ignorados.
- GitHub Actions automatico de PR/push esta permitido solo como gate de codigo: el job F9 no declara `environment`, no consume secrets, bloquea conexiones externas nuevas con `iptables`/`ip6tables` y usa PostgreSQL 17 en loopback. `workflow_dispatch` y workflows de aplicacion permanecen prohibidos.
- El bootstrap puede consultar registries de paquetes e imagenes sin credenciales del proyecto. La evidencia comienza despues; usa dependencias instaladas y `docker run --pull=never`, y prohibe egress DB/API/provider mediante los guards anteriores.
- Evidencia solo pass/fail, checksums y conteos agregados; sin filas, URLs reales, project refs, payloads ni identificadores operativos.

## Exclusiones

- Cualquier acceso remoto, incluso read-only, a Free o Pro.
- DDL/DML/RPC remoto, parity remoto, workflow dispatch o GitHub environment.
- Cambiar status a `ready_for_free` o `free_certified`, retirar targets bloqueados o crear candidate F9.
- Editar migrations o manifests F6/F7/F8 existentes.
- Crear, alterar, conceder o manifestar `exec_sql` fuera del fixture efimero.
- Cambiar policies, verifiers, grants, roles, columnas expuestas o privilegios RPC de negocio.
- SQL ejecutable de backfill, H-00, cohortes operativas, counts reales o copia de datos entre ambientes.
- Pausa/reanudacion real de writers, backups reales o maintenance windows.
- Cambios de providers, reintentos de provider, smart mock, orquestacion o estados ETL.
- Hitos 2 a 5, Pro, certificacion/main y funcionalidad ajena a `H1-CA2P`.

## Gates De Entrada

1. El PR de definicion F9 fue aprobado y fusionado con CI verde.
2. Se emitio una nueva autorizacion humana exacta despues de ese merge.
3. La rama de implementacion nace limpia desde `desarrollo` verificado despues del cierre F8.
4. Las cuatro migrations, manifest F8 y checksums son byte-identicos.
5. `TASK-H1-001` y `H1-CA2P` permanecen `IN_PROGRESS`.
6. El comando de evidencia usa el entorno sanitizado y PostgreSQL 17 efimero definidos arriba.

## Comandos Y Evidencia

- Venv: `docker exec -w /app studiamatch-dev env -i HOME=/tmp PATH=/usr/local/bin:/usr/bin:/bin python3 -m venv /tmp/f9qa` y luego `docker exec -w /app studiamatch-dev env -i HOME=/tmp PATH=/tmp/f9qa/bin:/usr/local/bin:/usr/bin:/bin /tmp/f9qa/bin/pip install --require-hashes -r requirements-db-migrate.txt -r requirements-test.txt`.
- Manifest offline: `docker exec -w /app studiamatch-dev env -i HOME=/tmp PATH=/tmp/f9qa/bin:/usr/local/bin:/usr/bin:/bin PYTHONPATH=/app /tmp/f9qa/bin/python scripts/maintenance/db_migrate.py --env free --manifest db/manifests/fase08_candidate.json --validate-only`.
- Python: `docker exec -w /app studiamatch-dev env -i HOME=/tmp CI=true PATH=/tmp/f9qa/bin:/usr/local/bin:/usr/bin:/bin PYTHONPATH=/app /tmp/f9qa/bin/python -m pytest -q tests/test_fase06_db_as_code.py tests/test_fase07_g1b.py tests/test_fase08_db.py tests/test_fase08_workers.py tests/test_fase09_db.py tests/test_fase09_workers.py tests/test_supabase_credentials_contract.py`.
- PostgreSQL local: `powershell -NoProfile -ExecutionPolicy Bypass -File tests/run_fase09_local.ps1`. El wrapper ejecuta `docker network create --internal studiamatch-f9-local`, conecta `studiamatch-dev`, inicia la imagen PostgreSQL fijada con `--pull=never`, ejecuta `run_fase09_postgres.sh` con el `TEST_DATABASE_URL` exacto y usa `finally` para stop/disconnect/remove.
- PostgreSQL CI: `env -i HOME=/tmp CI=true PATH=/tmp/f9qa/bin:/usr/local/bin:/usr/bin:/bin PYTHONPATH=/app TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/studiamatch_f9 bash tests/sql/run_fase09_postgres.sh` dentro del job F9 sin secrets.
- Compile: `docker exec -w /app studiamatch-dev env -i HOME=/tmp PATH=/usr/local/bin:/usr/bin:/bin PYTHONPATH=/app bash -c "find scripts/core scripts/maintenance scripts/shared -name '*.py' -print0 | xargs -0 -n1 python3 -m py_compile"`.
- Context Graph: `docker exec -w /app studiamatch-dev env -i HOME=/tmp PATH=/usr/local/bin:/usr/bin:/bin PYTHONPATH=/app python3 scripts/maintenance/validate_context_graph.py`.
- Frontend lint: `docker exec -w /app/web studiamatch-dev env -i HOME=/tmp CI=true PATH=/usr/local/bin:/usr/bin:/bin npm run lint`.
- Frontend typecheck: `docker exec -w /app/web studiamatch-dev env -i HOME=/tmp CI=true PATH=/usr/local/bin:/usr/bin:/bin ./node_modules/.bin/tsc --noEmit --incremental false`.
- Frontend build: `docker exec -w /app/web studiamatch-dev env -i HOME=/tmp CI=true PATH=/usr/local/bin:/usr/bin:/bin NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:9 NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_ci_test npm run build`. Esta compatibilidad frontend no constituye evidencia de aislamiento F9; la evidencia aislada es el wrapper local y el job F9.
- No se permiten diffs en `web/`; lint debe conservar cero errores y no superar los 10 warnings registrados en F8.
- CI: job `fase09-pre-free` y check agregado `security-audit` en PASS, sin environments/secrets.
- Reviews: auditorias `security-auditor` y `qa-test-engineer` en GO; review/aprobacion por `romelhc95-approver`; merge por merge commit y replay post-merge.
- Nota de evidencia: esta misma nota se actualiza con commit/tree, conteos, resultados y acceso remoto `0`.

## Gates De Salida

1. Los comandos y evidencia anteriores pasan sin secretos ni egress DB/API/provider; el bootstrap de registries queda separado de la evidencia.
2. Payload real local demuestra commit atomico, rollback total y segunda planificacion sin pendientes.
3. Ledger paginado supera 1000 filas y falla cerrado en todos los negativos enumerados.
4. Enrichment conserva fail-fast de un intento por ID sin nomenclatura contradictoria.
5. Manifest F8 permanece byte-identico, `reconciled_not_certified`, con `blocked_targets: ["free", "pro"]` y H-00 excluido.
6. Auditorias independientes, CI, review, merge de implementacion y validacion post-merge pasan.
7. Evidencia explicita: acceso remoto `0`, DDL/DML remoto `0`, backfill ejecutado `0`.

## Evidencia Candidate

- Rama: `feat/fase09-pre-free`.
- Package F8: cuatro entradas y checksums byte-identicos; status `reconciled_not_certified`; Free/Pro bloqueados.
- PostgreSQL 17 efimero: commit atomico, cuatro marcadores exactos, segunda planificacion sin SQL y rollback total por fault injection en PASS.
- Ledger: 1001 filas sinteticas y negativos de transporte, representacion, JSON, pagina incompleta y duplicados en PASS.
- Enrichment: un intento por ID, duplicados omitidos, excepcion fail-fast y conteo solo exitoso en PASS.
- Suite contractual F6/F7/F8/F9 y credenciales: 146 pruebas en PASS; un warning de deprecacion preexistente.
- Python compile: PASS. Context Graph: PASS con 27 archivos y 201 enlaces.
- Frontend sin diff: lint con cero errores/10 warnings preexistentes, typecheck y build estatico en PASS.
- Auditorias finales de seguridad y QA: GO, sin bloqueadores.
- Acceso Free/Pro: `0`; DDL/DML remoto: `0`; backfill: `0`; secrets/environments: `0`.
- Resultados completos, commit/tree, auditorias, CI y post-merge se agregan durante los gates restantes.

## Evidencia Post-Merge

- PR #231: CI verde, aprobacion y merge humano mediante merge commit.
- Replay inicial detecto CRLF Windows; PR #232 recibio CI verde, aprobacion y merge humano mediante merge commit.
- `desarrollo@96e78b5` conserva el tree exacto de la remediacion `5140806`.
- Suite contractual post-merge: 146 pruebas PASS; PostgreSQL 17 aislado PASS; Context Graph PASS con 27 archivos/201 enlaces.
- F8 sigue byte-identico, `reconciled_not_certified` y bloqueado para Free/Pro.
- Acceso Free/Pro `0`; DDL/DML/RPC/parity remoto `0`; backfill `0`; secrets/environments `0`.
- Estado del package historico `FASE-09`/F9.1: `COMPLETED` solo tras fusionar el PR documental de cierre #233.

## Cierre Post-Merge

1. El PR de implementacion F9 deja la fase en `HUMAN_GATE`; su merge no marca `COMPLETED`.
2. Tras ese merge se actualiza `desarrollo`, se verifica tree exacto y se repiten los comandos F9 post-merge.
3. Se crea `docs/close-fase09` con cambios unicamente en esta nota, `estado_del_proyecto.md`, `TASK-H1-001` y el changelog. No requiere otra autorizacion de ejecucion porque solo registra el cierre de la fase ya autorizada.
4. El PR de cierre exige Context Graph, `security-audit`, review de `romelhc95-approver` y merge commit.
5. `FASE-09` pasa a `COMPLETED` solo cuando el PR de cierre queda fusionado. Despues se valida el tree y Context Graph del cierre; no se reutiliza ese gate para una fase remota posterior.

## Estados Permitidos

| Objeto | Resultado F9 |
|---|---|
| `FASE-09` | `PENDING` a `HUMAN_GATE`; `COMPLETED` solo tras merge del PR documental `docs/close-fase09` |
| `TASK-H1-001` | Permanece `IN_PROGRESS` |
| `H1-CA2P` | Permanece `IN_PROGRESS` |
| Candidate F8 | Permanece `reconciled_not_certified` y byte-identico |
| Targets | Free y Pro permanecen bloqueados |
| Adopcion remota | Sin cambios |

## Subfase Remota Posterior

La ruta prevista al cerrar F9.1 asignaba a F9.3 un contrato local y a una F9.4 posterior el preflight remoto; ADR-0004 sustituyo despues esa identidad sin reescribir esta evidencia. Backup, pausa de writers, aplicacion de schema, H-00 y backfill conservan gates posteriores separados. Pro permanece prohibido hasta cerrar la macrofase F9 con un candidate `free_certified` y abrir F10 Produccion.

Ver [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Certificacion F8](./certificacion_hito1_f8.md), [Matriz DB](./matriz_adopcion_db.md) y [Release minimo](./flujo_release_minimo.md).
