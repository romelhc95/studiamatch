# Contrato De Promocion Hito 1 F10

> **Identidad historica:** `FASE-10`, `F10-HITO1-PROMOTION-CONTRACT-20260725`, `fase10-*` y la frase de autorizacion de esta nota identifican exclusivamente el package local cerrado por PR #235/#236. [ADR-0003](../decisiones/ADR-0003_taxonomia_macrofases_subfases.md) lo mapea a F9.2; no es la macrofase F10 Produccion.

> **Ruta futura sustituida:** las referencias de este artifact historico a F9.4 `REMOTE_READ_FREE` y F9.5 `ACCEPT_FREE_READINESS` fueron sustituidas por [ADR-0004](../decisiones/ADR-0004_simplificacion_contractual_hito1.md). No definen ni autorizan las subfases vigentes.

Esta nota define el alcance ejecutable de `FASE-10` bajo `H1-CA2P`. F10 repara exclusivamente el contrato local de promocion del package F8. No autoriza conexiones a Free/Pro, credenciales, parity remoto, workflows de aplicacion, cambios de status, DDL/DML/RPC, backups, pausa de writers ni backfill.

Registro historico no reutilizable: la ejecucion original requirio la frase `Ejecuta las tareas pendientes de la Fase 10` despues de fusionar su definicion. Esa frase no autoriza la macrofase F10 Produccion ni ninguna subfase vigente.

## Bloqueo Que Resuelve

El manifest F8 conserva prerrequisitos universales `editorial_backfill_certified` y `free_postconditions_certified`, mientras el contrato editorial exige schema/RLS certificado antes del backfill y las postcondiciones Free solo existen despues de aplicar el package. El loader comprueba presencia de nombres, no evidencia de cumplimiento. Ese ciclo impide una promocion Free coherente y permite que una edicion manual de status aparente cumplir gates inexistentes.

F10 elimina el ciclo mediante requisitos por transicion. El manifest F8 original y sus cuatro migrations permanecen byte-identicos como evidencia historica.

## Capability Class

`LOCAL_PROMOTION_CONTRACT` es la unica capacidad autorizable en F10.

- Target remoto: ninguno.
- Ambiente de ejecucion: contenedores locales y CI sin secrets/environments.
- Resultado: descriptor sucesor bloqueado y maquina de estados validada localmente.
- No produce `ready_for_free`, `free_schema_certified`, `free_backfill_certified` ni `free_certified`.

## Entregables Exactos

1. Reproducir por prueba el ciclo del manifest v1 y rechazar su uso como contrato de promocion futura.
2. Crear `db/manifests/fase10_promotion_contract.json`, schema v2, package `F10-HITO1-PROMOTION-CONTRACT-20260725`, que referencia por path y SHA-256 el manifest F8 y conserva exactamente sus cuatro entradas, orden, checksums, provenance, targets y exclusiones.
3. Mantener el descriptor F10 en `reconciled_not_certified` con `schema_apply_blocked_targets: ["free", "pro"]`; no editarlo para simular evidencia remota.
4. Implementar validacion fail-closed de estados, transiciones, evidencia por transicion, payload heredado y target permitido.
5. Separar en helpers puros los modos `local_contract`, `free_readiness`, `free_schema_acceptance`, `free_backfill_acceptance`, `free_final_certification` y `pro_parity`. F10 solo ejecuta `local_contract` con transporte remoto reemplazado por fallo.
6. Rechazar saltos de estado, evidencia futura/ausente, evidencia sin digest, status/targets inconsistentes, payload drift, H-00, identidades target ambiguas y cualquier intento de aplicar en el estado inicial.
7. Agregar pruebas F10 y el job bloqueante `fase10-promotion-contract`, nombre `FASE-10 Local Promotion Contract`, al agregador `security-audit`.
8. Reconciliar documentos que aun colocan backfill antes de schema/RLS.

## Descriptor V2 Exacto

`fase10_promotion_contract.json` es inmutable. No contiene un campo `current_status` editable. El estado efectivo se deriva desde `initial_state` y una cadena externa de attestations futuras. F10 no crea esa cadena.

Campos top-level obligatorios y unicos; cualquier campo extra se rechaza:

```json
{
  "schema_version": 2,
  "phase": "FASE-10",
  "package_id": "F10-HITO1-PROMOTION-CONTRACT-20260725",
  "capability_class": "LOCAL_PROMOTION_CONTRACT",
  "approval_policy": {
    "owner": "romelhc95",
    "reviewer": "romelhc95-approver",
    "self_approval": false
  },
  "source_manifest": {
    "path": "db/manifests/fase08_candidate.json",
    "package_id": "F8-HITO1-FUNCTIONAL-20260725",
    "canonical_json_sha256": "<64 lowercase hex>"
  },
  "initial_state": "reconciled_not_certified",
  "state_order": [
    "reconciled_not_certified",
    "ready_for_free",
    "free_schema_certified",
    "free_backfill_certified",
    "free_certified"
  ],
  "states": {
    "reconciled_not_certified": {"schema_apply_blocked_targets": ["free", "pro"], "next_capabilities": ["REMOTE_READ_FREE", "ACCEPT_FREE_READINESS"]},
    "ready_for_free": {"schema_apply_blocked_targets": ["pro"], "next_capabilities": ["APPLY_SCHEMA_FREE"]},
    "free_schema_certified": {"schema_apply_blocked_targets": ["free", "pro"], "next_capabilities": ["BACKFILL_FREE"]},
    "free_backfill_certified": {"schema_apply_blocked_targets": ["free", "pro"], "next_capabilities": ["CERTIFY_FREE_READ_ONLY"]},
    "free_certified": {"schema_apply_blocked_targets": ["free"], "next_capabilities": ["PROMOTE_PRO"]}
  },
  "payload_entries": [
    {
      "id": "F6-G1B-FORWARD",
      "component": "g1b",
      "path": "db/migrations/20260724_fase06_g1b_reconciliation.sql",
      "sha256": "d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df",
      "provenance": "new_forward_only",
      "targets": ["free", "pro"]
    },
    {
      "id": "F6-HITO1-FORWARD",
      "component": "hito1",
      "path": "db/migrations/20260724_fase06_hito1_editorial_contract.sql",
      "sha256": "b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a",
      "provenance": "new_forward_only",
      "targets": ["free", "pro"]
    },
    {
      "id": "F7-G1B-CLOSURE",
      "component": "g1b_closure",
      "path": "db/migrations/20260725_fase07_g1b_closure.sql",
      "sha256": "9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120",
      "provenance": "new_forward_only",
      "targets": ["free", "pro"]
    },
    {
      "id": "F8-HITO1-FUNCTIONAL-CLOSURE",
      "component": "hito1_functional_closure",
      "path": "db/migrations/20260725_fase08_hito1_functional_closure.sql",
      "sha256": "7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527",
      "provenance": "new_forward_only",
      "targets": ["free", "pro"]
    }
  ],
  "transitions": [
    {
      "id": "T01_FREE_READINESS",
      "from": "reconciled_not_certified",
      "to": "ready_for_free",
      "target": "free",
      "acceptance_capability": "ACCEPT_FREE_READINESS",
      "evidence_types": ["f9_completion", "free_preflight", "free_application_plan_approval"]
    },
    {
      "id": "T02_FREE_SCHEMA",
      "from": "ready_for_free",
      "to": "free_schema_certified",
      "target": "free",
      "acceptance_capability": "ACCEPT_FREE_SCHEMA",
      "evidence_types": ["free_schema_application_approval", "free_backup_restore", "free_writers_pause", "free_schema_postconditions", "free_advisors"]
    },
    {
      "id": "T03_FREE_BACKFILL",
      "from": "free_schema_certified",
      "to": "free_backfill_certified",
      "target": "free",
      "acceptance_capability": "ACCEPT_FREE_BACKFILL",
      "evidence_types": ["free_backfill_plan_approval", "free_backfill_execution_approval", "free_backfill_result"]
    },
    {
      "id": "T04_FREE_FINAL",
      "from": "free_backfill_certified",
      "to": "free_certified",
      "target": "free",
      "acceptance_capability": "ACCEPT_FREE_FINAL",
      "evidence_types": ["free_final_certification_approval", "free_final_readonly", "free_advisors", "free_backfill_idempotency"]
    }
  ],
  "excluded": {
    "H-00": "historical_free_only",
    "canary": "observed_effective_unledgered",
    "historical_snapshots": "superseded"
  }
}
```

`payload_entries` copia los objetos F8 completos sin el array legacy `prerequisites`; el package historico F10/F9.2 sustituye ese array por requisitos de transicion. `schema_apply_blocked_targets` gobierna exclusivamente aplicacion/replay del payload DDL, no backfill ni inspeccion read-only. `next_capabilities` es una secuencia ordenada; en estado inicial exige primero F9.4 `REMOTE_READ_FREE` y despues F9.5 `ACCEPT_FREE_READINESS`; F9.3 congela previamente el contrato local. El descriptor no autoriza capabilities; solo identifica cuales subfases separadas pueden definirse.

Objetos `transitions` exactos:

| ID | From | To | Target | Acceptance capability | Evidence types exactos, uno de cada uno |
|---|---|---|---|---|---|
| `T01_FREE_READINESS` | `reconciled_not_certified` | `ready_for_free` | `free` | `ACCEPT_FREE_READINESS` | `f9_completion`, `free_preflight`, `free_application_plan_approval` |
| `T02_FREE_SCHEMA` | `ready_for_free` | `free_schema_certified` | `free` | `ACCEPT_FREE_SCHEMA` | `free_schema_application_approval`, `free_backup_restore`, `free_writers_pause`, `free_schema_postconditions`, `free_advisors` |
| `T03_FREE_BACKFILL` | `free_schema_certified` | `free_backfill_certified` | `free` | `ACCEPT_FREE_BACKFILL` | `free_backfill_plan_approval`, `free_backfill_execution_approval`, `free_backfill_result` |
| `T04_FREE_FINAL` | `free_backfill_certified` | `free_certified` | `free` | `ACCEPT_FREE_FINAL` | `free_final_certification_approval`, `free_final_readonly`, `free_advisors`, `free_backfill_idempotency` |

El validator exige igualdad exacta de IDs, orden, from/to/target, acceptance capability y evidence types. El target `pro` no aparece en transitions F10.

## Maquina De Estados

| Estado | Significado | Schema apply Free | Schema apply Pro |
|---|---|---:|---:|
| `reconciled_not_certified` | Payload local reconciliado; sin preflight Free vigente | Bloqueado | Bloqueado |
| `ready_for_free` | Preflight Free read-only y plan operativo aprobados | Aplicacion elegible bajo otro gate | Bloqueado |
| `free_schema_certified` | Schema/RLS aplicado y aceptado en Free | Solo verificacion | Bloqueado |
| `free_backfill_certified` | Backfill separado ejecutado y certificado | Solo verificacion | Bloqueado |
| `free_certified` | Certificacion final Free completada | Certificado | Elegible bajo gate Production independiente |

Unicas transiciones permitidas:

```text
reconciled_not_certified
  -> ready_for_free
  -> free_schema_certified
  -> free_backfill_certified
  -> free_certified
```

No se permiten saltos, transiciones automaticas, rollback de status ni reutilizacion de evidencia entre transiciones.

## Attestation Por Transicion

F10 define el contrato, pero no produce attestations remotas ni ejecuta transiciones. Cada fase futura crea un archivo nuevo bajo `db/attestations/hito1/`; nunca edita descriptor o attestations anteriores.

En el package historico F10/F9.2, `validate_attestation_inventory_structure` verifica sobre repositorios Git/fixtures sinteticos la estructura T01-T04, inventory completo, fingerprint, bytes versionados, commit/tree y ancestry, pero retorna `None`: no concede estado ni capability. Solo los tests calculan el estado esperado desde el descriptor congelado. La API operacional publica acepta cero attestations y falla cerrado ante cualquier inventory no vacio. F9.5 debera verificar autenticidad del review GitHub y habilitar una ruta operacional nueva; campos `approval` auto-declarados nunca bastan para cambiar estado.

Campos obligatorios y unicos de cada attestation:

```json
{
  "schema_version": 1,
  "attestation_id": "ATT-<transition-id>-<UTC basic timestamp>-<12 lowercase hex>",
  "transition_id": "<enum exacto>",
  "from_state": "<exacto>",
  "to_state": "<exacto>",
  "target_environment": "free",
  "target_fingerprint_sha256": "<64 lowercase hex; no URL/ref>",
  "package_id": "F10-HITO1-PROMOTION-CONTRACT-20260725",
  "descriptor_sha256": "<64 lowercase hex>",
  "source_manifest_sha256": "<64 lowercase hex>",
  "commit_sha": "<40 lowercase hex>",
  "tree_sha": "<40 lowercase hex>",
  "operation_owner": "romelhc95",
  "previous_attestation_sha256": null,
  "created_at": "<UTC RFC3339 seconds, Z>",
  "result": "PASS",
  "approval": {"github_login": "romelhc95-approver", "review_id": "<positive integer>", "reviewed_commit_sha": "<same commit_sha>", "decision": "APPROVED"},
  "evidence": [
    {"type": "<enum exacto>", "sha256": "<64 lowercase hex>", "observed_at": "<UTC RFC3339 seconds, Z>", "expires_at": "<UTC RFC3339 seconds, Z>"}
  ]
}
```

Para `T01`, `previous_attestation_sha256` es `null`; para T02-T04 es el SHA-256 canonico de la attestation previa. `created_at` debe ser posterior a la attestation previa y caer dentro de todos los intervalos `[observed_at, expires_at]`. Cada intervalo es positivo y no excede 24 horas. En replay historico solo se valida que la evidencia estaba vigente en `created_at`; nunca se compara `expires_at` con el clock actual. La fase que crea una attestation rechaza `created_at` futuro usando un clock UTC inyectado/fijado en prueba, pero la cadena historica permanece durable. La attestation no autoriza una operacion futura y cada fase operativa repite su preflight fresco.

`target_fingerprint_sha256`, package ID, descriptor hash y source-manifest hash son identidades estables: deben ser iguales en T01-T04. `attestation_id`, hash de attestation, evidence digests y `review_id` son unicos por transicion. `commit_sha`/`tree_sha` identifican el candidate operacional revisado y ejecutado antes de crear la attestation; ese commit debe ser ancestro del commit documental que agrega la attestation, evitando autoreferencia. `approval.reviewed_commit_sha` coincide exactamente con `commit_sha`, decision `APPROVED`, reviewer/owner coinciden con `approval_policy` y son distintos. Evidence types/cardinalidad coinciden exactamente con la tabla; faltantes, extras o duplicados fallan.

El estado efectivo se obtiene validando desde T01 una cadena consecutiva. Cero attestations equivale a `reconciled_not_certified`. Cualquier gap, fork, replay, attestation duplicada, predecessor incorrecto, resultado distinto de `PASS` o evidencia que no estaba vigente en `created_at` aborta sin estado parcial.

`target_fingerprint_sha256` se deriva sin loggear componentes como SHA-256 de bytes UTF-8: `studiamatch-target-v1\0free\0<canonical-origin-lowercase>\0<sha256-publishable-key-lowercase-hex>`. `canonical-origin` exige `https`, hostname `<project-ref>.supabase.co`, sin userinfo, port, path, query, fragment ni trailing slash. El fingerprint esperado proviene de configuracion privada read-only; el observado se calcula independientemente desde las credenciales Free de la fase remota. Igualdad constant-time es obligatoria y solo PASS/FAIL se registra. Variables genericas o `PRO_*` abortan antes de conectar.

El repositorio solo guarda metadata sanitizada; endpoints, project refs, filas, UUID operativos, payloads y detalles explotables permanecen fuera de Git.

## Canonicalizacion Y Hashes

- JSON se parsea rechazando claves duplicadas, floats, NaN/Infinity, strings no NFC y tipos fuera de object/array/string/integer/boolean/null.
- Representacion canonica project-JCS-v1: UTF-8, Unicode NFC, keys ordenadas lexicograficamente, separators `,` y `:`, sin whitespace ni ASCII escaping innecesario.
- SHA-256 es lowercase hex sobre esos bytes canonicos. CRLF/LF y formato visual del JSON no cambian identidad.
- SQL conserva el hash LF canonico ya definido por F6-F9.
- El descriptor hash excluye nada: cubre el objeto completo. Cada attestation hash cubre el objeto completo; no contiene su propio hash.

## Allowlist F10

- `db/manifests/fase10_promotion_contract.json` como descriptor nuevo y bloqueado.
- `scripts/maintenance/migration_manifest.py` solo para schema v2 y transiciones puras.
- `scripts/maintenance/db_migrate.py` solo para rechazar estados/targets no aplicables y consumir el descriptor sin transporte remoto.
- `scripts/maintenance/check_db_parity.py` solo para separar modos puros; su CLI y requests reales no se ejecutan.
- `tests/test_fase10_promotion_contract.py`.
- `tests/run_fase10_local.ps1` como wrapper Docker-only con aislamiento/restauracion `finally`.
- Tests F8/F9 son solo lectura/ejecucion; F10 no puede editar, borrar, saltar, `xfail` ni debilitar su cobertura historica.
- `.github/workflows/security-audit.yml` solo para el job F10 local, sin service DB, environment ni secrets.
- `.context/00_INDICE.md`, `estado_del_proyecto.md`, `backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md`, `changelog/2026-07-25.md`, `operaciones/flujo_release_minimo.md`, `operaciones/reconciliacion_db_as_code_f6.md` y esta nota.

Lectura sin modificacion:

- `db/manifests/fase08_candidate.json`.
- Las cuatro migrations F6/F7/F8 y sus pruebas SQL F8/F9.
- `db/operations/editorial/README.md`.

Todo path no enumerado queda fuera. En particular se excluyen migrations nuevas, `db-sync-to-pro.yml`, workflows FG1/FG2/FG3, `web/`, scripts de backfill y cualquier `.env*`.

## Aislamiento Mecanico

- Comandos con `env -i`, PATH/PYTHONPATH explicitos y sin variables Supabase/provider.
- Tests reemplazan requests, sockets, dotenv y lectura `.env*` por fallos deterministas.
- `tests/run_fase10_local.ps1` desconecta todas las redes originales de `studiamatch-dev`, conecta una red Docker interna sin peers remotos, ejecuta F10, y restaura topology en `finally`; no ejecuta Python/npm en host.
- CI instala dependencias antes de evidencia y luego bloquea conexiones externas nuevas IPv4/IPv6; el job F10 no declara service DB, environment ni secrets y restaura reglas en `always()`.
- `db_migrate.py` solo usa `--validate-only`; `--dry-run` y modos normales estan prohibidos.
- `check_db_parity.py` no se ejecuta como CLI.
- Evidencia permitida: PASS/FAIL, conteos, estados, commit/tree y checksums no reversibles.

## Exclusiones

- Acceso Free/Pro, incluso read-only, Supabase MCP o advisors remotos.
- Crear/cargar credenciales, `.env*` o GitHub environments.
- Cambiar status/blocked targets del manifest F8 o `schema_apply_blocked_targets` del descriptor F10.
- Editar las cuatro migrations, crear migrations o aplicar schema/RLS.
- Invocar `exec_sql`, RPCs de negocio, parity remoto o workflow dispatch.
- SQL/ejecucion de backfill, cohortes reales, H-00 o datos operativos.
- Backup real, pausa/reanudacion de writers o maintenance window.
- Policies, grants, roles, frontend, providers, pipeline o Pro.
- Completar `H1-CA2P` o `TASK-H1-001`.

## Gates De Entrada

1. El PR de definicion F10 fue aprobado y fusionado con CI verde.
2. Nueva autorizacion humana exacta para F10 despues de ese merge.
3. Rama limpia desde `desarrollo@b9053ab` o descendiente canonico verificado.
4. El package historico `FASE-09`/F9.1 esta `COMPLETED`; `TASK-H1-001` y `H1-CA2P` siguen `IN_PROGRESS`.
5. Manifest F8 y cuatro migrations byte-identicos; status `reconciled_not_certified`; Free/Pro bloqueados.
6. Entorno sanitizado y transporte remoto mecanicamente prohibido.

## Gates De Salida

1. El ciclo v1 queda reproducido y eliminado en schema v2 con requisitos por transicion.
2. Manifest/migrations F8 permanecen byte-identicos.
3. Descriptor F10 conserva payload exacto, estado inicial y schema apply bloqueado en ambos targets.
4. Matriz completa acepta solo transiciones consecutivas con evidencia exacta y rechaza todos los negativos.
5. Schema apply Free no es elegible en estado inicial y schema apply Pro no es elegible antes de `free_certified`.
6. Helpers de modos no ejecutan transporte remoto en F10.
7. Suites F6-F10, PostgreSQL 17 heredado, Python compile, Context Graph, credential scan y gates frontend aplicables pasan.
8. Auditorias security/QA, CI, review, merge de implementacion, replay y PR documental de cierre pasan.
9. Evidencia explicita: Free/Pro `0`, DDL/DML/RPC/parity remoto `0`, backfill `0`, secrets `0`.

## Matriz De Pruebas Cerrada

Positivos:

- `P01`: descriptor exacto sin attestations deriva `reconciled_not_certified` y bloquea schema apply Free/Pro.
- `P02` a `P05`: cadenas sinteticas T01, T01-T02, T01-T03 y T01-T04 derivan cada estado consecutivo y mapping exacto.
- `P06`: payload, orden y hashes coinciden con F8 en Windows/Linux.

Negativos obligatorios:

- `N01`: campo desconocido/faltante, clave duplicada, float, string no NFC o hash mal formado.
- `N02`: source manifest, payload, orden, migration hash, provenance, target o exclusion con drift.
- `N03`: transition ID/from/to/target/order alterado, salto, reversa, fork o duplicado.
- `N04`: schema-apply blocked targets, next-capability sequence o acceptance capability distintos del mapping exacto.
- `N05`: evidence type faltante/extra/duplicado, digest invalido o resultado no PASS.
- `N06`: identidad estable cambia entre transiciones; package/descriptor/manifest/target fingerprint/commit/tree/owner/approval no ligado a la transicion.
- `N07`: predecessor nulo fuera de T01, ausente, incorrecto o replay de attestation.
- `N08`: timestamp no ordenado, `created_at` fuera del intervalo de evidencia, intervalo negativo/mayor a 24 horas o clock futuro al crear; replay historico no invalida por tiempo actual.
- `N09`: intento de mutar descriptor/attestation existente o derivar estado desde un campo editable.
- `N10`: transition target Pro, schema apply Free elegible en estado inicial o schema apply Pro elegible antes de `free_certified`.
- `N11`: H-00/canary/snapshot no excluido exactamente.
- `N12`: dotenv, secret/env, socket/request/subprocess de red, CLI parity o modo remoto invocado.

## Comandos Exactos

- Bootstrap no probatorio: `docker exec -w /app studiamatch-dev env -i HOME=/tmp PATH=/usr/local/bin:/usr/bin:/bin python3 -m venv /tmp/f10qa` y `docker exec -w /app studiamatch-dev env -i HOME=/tmp PATH=/tmp/f10qa/bin:/usr/local/bin:/usr/bin:/bin /tmp/f10qa/bin/pip install --require-hashes -r requirements-db-migrate.txt -r requirements-test.txt`.
- Unica entrada de evidencia F10 local: `powershell -NoProfile -ExecutionPolicy Bypass -File tests/run_fase10_local.ps1`.
- El wrapper aislado ejecuta internamente `docker exec -w /app studiamatch-dev env -i HOME=/tmp PATH=/tmp/f10qa/bin:/usr/local/bin:/usr/bin:/bin PYTHONPATH=/app /tmp/f10qa/bin/python scripts/maintenance/db_migrate.py --env free --promotion-contract db/manifests/fase10_promotion_contract.json --validate-only`.
- Despues ejecuta internamente `docker exec -w /app studiamatch-dev env -i HOME=/tmp CI=true PATH=/tmp/f10qa/bin:/usr/local/bin:/usr/bin:/bin PYTHONPATH=/app /tmp/f10qa/bin/python -m pytest -q tests/test_fase06_db_as_code.py tests/test_fase07_g1b.py tests/test_fase08_db.py tests/test_fase08_workers.py tests/test_fase09_db.py tests/test_fase09_workers.py tests/test_fase10_promotion_contract.py tests/test_supabase_credentials_contract.py`. Invocar ambos comandos fuera del wrapper no constituye evidencia F10.
- Replay PostgreSQL heredado: `powershell -NoProfile -ExecutionPolicy Bypass -File tests/run_fase09_local.ps1`.
- Compile: `docker exec -w /app studiamatch-dev env -i HOME=/tmp PATH=/usr/local/bin:/usr/bin:/bin PYTHONPATH=/app bash -c "find scripts/core scripts/maintenance scripts/shared -name '*.py' -print0 | xargs -0 -n1 python3 -m py_compile"`.
- Context Graph: `docker exec -w /app studiamatch-dev env -i HOME=/tmp PATH=/usr/local/bin:/usr/bin:/bin PYTHONPATH=/app python3 scripts/maintenance/validate_context_graph.py`.
- Lint: `docker exec -w /app/web studiamatch-dev env -i HOME=/tmp CI=true PATH=/usr/local/bin:/usr/bin:/bin npm run lint`.
- Typecheck: `docker exec -w /app/web studiamatch-dev env -i HOME=/tmp CI=true PATH=/usr/local/bin:/usr/bin:/bin ./node_modules/.bin/tsc --noEmit --incremental false`.
- Build: `docker exec -w /app/web studiamatch-dev env -i HOME=/tmp CI=true PATH=/usr/local/bin:/usr/bin:/bin NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:9 NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_ci_test npm run build`.
- No se permiten diffs en `web/`, errores lint ni aumento sobre 10 warnings heredados.
- CI: `fase10-promotion-contract` y agregado `security-audit` en PASS.

## Cierre Post-Merge

1. El PR de implementacion deja F10 en `HUMAN_GATE`; su merge no marca `COMPLETED`.
2. Tras merge se actualiza `desarrollo`, se verifica tree exacto y se repiten todos los comandos F10.
3. Se crea `docs/close-fase10`, limitado a esta nota, `estado_del_proyecto.md`, `TASK-H1-001` y changelog.
4. El PR de cierre exige Context Graph, `security-audit`, auditorias GO, review de `romelhc95-approver` y merge commit.
5. El package historico F10/F9.2 pasa a `COMPLETED` solo al fusionar el PR de cierre. F9.3 y cada subfase posterior conservan definicion/autorizacion independientes.

## Estados Permitidos En F10

| Objeto | Resultado F10 |
|---|---|
| `FASE-10` | `PENDING` a `HUMAN_GATE`; `COMPLETED` solo tras PR documental de cierre |
| `TASK-H1-001` | Permanece `IN_PROGRESS` |
| `H1-CA2P` | Permanece `IN_PROGRESS` |
| Manifest F8 | Byte-identico y `reconciled_not_certified` |
| Descriptor F10 | Nuevo, bloqueado y `reconciled_not_certified` |
| Adopcion remota | Sin cambios |

## Reservas Reconciliadas

Esta seccion conserva la decision historica de F9.2. [ADR-0004](../decisiones/ADR-0004_simplificacion_contractual_hito1.md) sustituyo despues la identidad de F9.4/F9.5 y el momento de retiro del plan temporal; las frases siguientes no son autorizables.

La reserva no ejecutada antes denominada F11 se sustituye por F9.4 `REMOTE_READ_FREE`: preflight Free read-only, target univoco, ledger completo, baseline, constraints, RLS/ACL, contrato `exec_sql` sin invocarlo, PostgREST, advisors, factibilidad de backup/writer pause/rollback y evidencia counts-only. F9.3 congela primero el contrato local. F9.4 produce `FREE_PREFLIGHT_PASS/FAIL`, pero no crea T01 ni cambia estado.

La reserva no ejecutada antes denominada F12 se sustituye por F9.5 `ACCEPT_FREE_READINESS`: subfase local/documental separada que valida la evidencia F9.4, aprobacion del plan y bindings, y solo entonces crea T01. F9.5 no conecta, no aplica schema ni ejecuta backfill. F9.3/F9.4/F9.5 requieren definicion, PR y autorizacion independientes.

Aplicacion schema/RLS, backfill y certificacion final Free quedan en fases posteriores separadas. Pro conserva un gate Production independiente.

## Trazabilidad Con El Plan Temporal

La trazabilidad del antecedente temporal fue preservada y el archivo retirado durante F9.4 conforme a ADR-0004. No autoriza ejecucion.

| Plan temporal | Descomposicion canonica restaurada | Estado tras F9.2 |
|---|---|---|
| F9 Certificacion Hito 1 Free | F9.1-F9.3 historia local; F9.4 reconciliacion; F9.5 preflight/T01; F9.6 H-00; F9.7-F9.10 schema, backfill y certificacion | En progreso |
| F10 Produccion | Pro, canary, `main`, smoke y observacion despues de `free_certified` | Pendiente |
| F11 Cierre | Cierre final tras produccion observada y limpieza autorizada | Pendiente |

El package historico F10/F9.2 solo completa preparacion local dentro de la macrofase F9. No completa certificacion Free, produccion ni cierre temporal.

## Evidencia Candidate F10

- Rama: `feat/fase10-promotion-contract`.
- Descriptor v2: payload F8 exacto, estado inicial `reconciled_not_certified`, schema apply Free/Pro bloqueado y cero attestations.
- Canonicalizacion, maquina de estados, attestations, bindings, fingerprint y modos: pruebas sinteticas PASS.
- Wrapper local con red Docker interna, `env -i` y restauracion `finally`: PASS.
- Suite F6-F10 y credenciales: 253 pruebas PASS; un warning de deprecacion heredado.
- Free/Pro, DDL/DML/RPC/parity remoto, backfill, secrets y status transitions: `0`.
- Context Graph: PASS con 28 archivos/208 enlaces. Wrapper self-test de fallos: PASS.
- Git local prueba commit/tree/ancestry y que el commit documental contiene descriptor e inventory exactos; autenticidad GitHub permanece bloqueada para F9.5.
- CI, auditorias, commit/tree y replay post-merge quedaron registrados en la evidencia de cierre.

## Evidencia Post-Merge

- PR #235: `security-audit` y todos sus jobs bloqueantes en PASS; aprobacion de `romelhc95-approver` y merge humano mediante merge commit.
- `desarrollo@d67fa31` tiene padres `a65f921`/`ffbd272` y tree `861aaa1c`, identico al head aprobado `ffbd272`.
- Replay F10 post-merge: self-test PASS, wrapper aislado PASS y suite contractual de 253 pruebas PASS con un warning heredado.
- Replay F9 PostgreSQL 17 PASS; Python compile PASS; Context Graph PASS con 28 archivos/208 enlaces.
- Frontend: lint con 0 errores/10 warnings heredados, typecheck PASS y build estatico PASS con valores publicos sinteticos.
- La restauracion post-replay no dejo redes F9/F10 ni contenedores PostgreSQL temporales.
- Auditorias del candidate previas a PR #235: security/QA GO sin hallazgos; scans pre-commit y pre-push PASS. Credential Scan y `security-audit` del PR tambien quedaron en PASS.
- F8 permanece byte-identico, `reconciled_not_certified` y bloqueado para Free/Pro; attestations/status transitions `0`.
- Acceso Free/Pro `0`; DDL/DML/RPC/parity remoto `0`; backfill `0`; secrets/environments `0`.
- Estado del package historico F10/F9.2: `COMPLETED`. La macrofase F9 sigue `IN_PROGRESS`; F9.3-F9.5 conservan gates independientes y F10 Produccion permanece pendiente.

Ver [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [F9](./precertificacion_hito1_f9.md), [Release minimo](./flujo_release_minimo.md) y [Matriz DB](./matriz_adopcion_db.md).
