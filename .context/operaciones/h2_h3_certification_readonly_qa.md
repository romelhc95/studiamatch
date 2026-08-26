# QA Read-Only Certificacion H2/H3

Estado: `DEFINED_PENDING_EXECUTION`.

Veredicto actual: `NO_GO_MAIN_UNTIL_QA_EXECUTED`.

Ambiente objetivo: `certificacion`.

## Proposito

Validar que H2 ya promovido a `certificacion` conserva la funcionalidad actual de la aplicacion y que H3 permanece solo en prearranque documental antes de cualquier promocion a `main`.

Este QA es read-only: no autoriza Supabase Pro, produccion, DDL/DML, writers, schedules, canaries, deploys manuales, merge a `main` ni ejecucion de H3.

## Resultado Esperado Para El Cliente

La aplicacion debe seguir funcionando igual o mejor despues de H2: Home, resultados, detalle de programa, comparador y paginas legales deben construir y mantenerse navegables. H2 no debe publicar registros incompletos por accidente ni exponer campos internos; H3 no debe activar administracion real hasta que se ejecute su hito.

## Alcance Read-Only

| Area | Validacion | Evidencia requerida |
|---|---|---|
| Funcionalidad publica | Home, listado de cursos, resultados/filtros, detalle, comparador, terminos y privacidad siguen construyendo. | `npm run build`, typecheck y smoke navegacional sin writes. |
| Contrato frontend H2 | Lecturas publicas usan `courses_public_effective` y no `courses` directa para superficie publica. | Tests de contrato y diff de `web/src/lib/supabase.ts`. |
| Privacidad H2 | Vista publica no expone campos privados/editoriales. | `private_column_count=0`, columnas esperadas y tests SQL. |
| Pipeline H2 | Incompletos quedan pendientes y pipeline no publica automaticamente. | Suite H2, backfill idempotente documentado y writer scan. |
| H3 prearranque | H3 esta documentado contra `SRC-REQ-002` pero no ejecutado. | Estado `PRESTART_CLIENT_SOURCE_ATTESTED_AFTER_H2_CERTIFICATION`. |
| Fuente cliente | QA y siguiente hito conservan trazabilidad contra adenda sanitizada. | `tests/test_requirement_client_source_validation.py`. |
| Seguridad | Sin secretos, sin nuevas acciones remotas y `security-audit` verde. | Credential scan y CI. |

## Comandos Permitidos

Solo dentro del contenedor `studiamatch-dev`:

```bash
docker exec studiamatch-dev pytest tests/test_requirement_client_source_validation.py tests/test_obsidian_context_state.py tests/test_h2_client_evidence_docs.py tests/test_h2_pipeline_contract.py tests/test_h2_editorial_migration.py tests/test_editorial_contract.py tests/test_h2_backfill_editorial_state.py tests/test_h2_writer_scan.py tests/test_security_flow.py tests/test_supabase_credentials_contract.py
docker exec studiamatch-dev sh -lc "cd /app/web && npm run lint"
docker exec studiamatch-dev sh -lc "cd /app/web && npx tsc --noEmit"
docker exec -e NEXT_PUBLIC_SUPABASE_URL=<certification_url> -e NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=<certification_publishable_placeholder_or_secret> studiamatch-dev sh -lc "cd /app/web && npm run build"
docker exec studiamatch-dev sh scripts/security/scan_credentials.sh
```

Si se ejecuta validacion con fuentes privadas locales, usar `STUDIAMATCH_PRIVATE_SOURCE_DIR` solo con archivos fuera de Git y limpiar temporales despues.

## Preflight Read-Only Supabase Certification

Requiere aprobacion JIT read-only separada si se consulta Supabase remoto.

| Consulta | Resultado esperado |
|---|---|
| Ledger H2 | Migraciones H2 presentes o documentar drift antes de `main`. |
| Columnas `courses_public_effective` | `28` columnas publicas, `0` privadas. |
| Grants funcion/vista | `PUBLIC` sin execute sobre funcion privada; roles esperados con permisos minimos. |
| Conteo anon vista publica | Consulta SELECT sin error; conteo documentado. |
| Advisors | Sin hallazgos H2 criticos/warn. |

## Criterios GO/NO-GO

| Criterio | GO | NO-GO |
|---|---|---|
| Funcionalidad | Build/typecheck/lint y smoke pasan. | Rutas publicas fallan, curso detalle no build, comparador roto o Home no carga. |
| Datos publicos | Vista H2 no expone privados y no oculta datos por drift no explicado. | Campos privados expuestos o conteo publico cae por incompatibilidad no documentada. |
| H3 | Solo prearranque documentado. | H3 ejecuta UI/admin/DB sin autorizacion. |
| Fuente cliente | Adenda sanitizada y tests pasan. | CA no trazado o fuente privada no contrastada cuando esta disponible. |
| Seguridad | Credential scan y security-audit verdes. | Secretos, grants excesivos o advisors H2 criticos/warn. |

## Veredicto Actual

`NO_GO_MAIN_UNTIL_QA_EXECUTED`.

El gate queda definido. La promocion `certificacion -> main` solo puede prepararse despues de ejecutar este QA, registrar evidencia y obtener aprobacion humana separada.
