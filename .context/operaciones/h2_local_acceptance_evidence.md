# H2 Local Acceptance Evidence

Snapshot: `H2-LOCAL-VALIDATED-2026-08-25`.

## Alcance Validado Localmente

- Capa editorial separada: `course_editorial_state`, `editorial_field_definitions`, `course_editorial_audit` y `courses_public_effective`.
- Forward-fix local: `db/migrations/20260826_h2_editorial_layer_forward_fix.sql`.
- Contrato determinista: valores efectivos, `missing_fields`, `quality_status`, `field_sources` y timestamps por campo.
- Pipeline tolerante: incompletos no se publican por flags legacy y calidad se recomputa por RPC acotada.
- Backfill: `--dry-run` por defecto, `--apply` explicito, keyset por UUID, batches maximos 1000 y segundo run `NOOP` cubierto por tests.
- Leads: frontend sin `POST /leads`; DDL local revoca INSERT y elimina policies legacy conocidas.
- Publicacion publica: frontend usa `courses_public_effective`; SELECT directo a `courses` queda revocado para roles publicos en forward-fix.

## Commits Locales H2

```text
5bfb231 feat(h2): add editorial layer ddl baseline
c31c43e feat(h2): add editorial quality contract
f492638 feat(h2): harden editorial layer contract
9c20a32 test(h2): add postgres 17 editorial harness
a703d4c feat(h2): make pipeline editorial-gated
662f1e0 feat(h2): add editorial state backfill
5710658 feat(h2): close lead capture surfaces
fe07a9d test(h2): register editorial backfill security inventory
19a383b fix(h2): harden editorial publication safeguards
8806456 fix(h2): route public frontend through editorial view
c91160a ci(h2): enforce editorial safeguards
4bd9439 fix(h2): close legacy public course bypass
eb92e1f fix(h2): drop legacy public courses policy
d356fa8 fix(h2): require editorial view for public course reads
```

## Validaciones Locales

```text
docker exec studiamatch-dev pytest tests/test_h2_writer_scan.py tests/test_h2_pipeline_contract.py tests/test_h2_backfill_editorial_state.py tests/test_editorial_contract.py tests/test_h2_editorial_migration.py tests/test_security_flow.py tests/test_supabase_credentials_contract.py
Resultado: 79 passed

docker exec studiamatch-dev python3 -m py_compile scripts/maintenance/h2_scan_unauthorized_writers.py scripts/maintenance/h2_backfill_editorial_state.py scripts/shared/editorial_contract.py scripts/core/cleansing_worker.py scripts/core/enrichment_worker.py scripts/core/sync_vector_worker.py
Resultado: PASS

PostgreSQL 17 efimero con tests/sql/h2_pg17_harness.sql
Resultado: h2_pg17_harness_ok

docker exec studiamatch-dev sh -lc "cd /app/web && npm run lint"
Resultado: PASS con 10 warnings preexistentes

docker exec studiamatch-dev sh -lc "cd /app/web && npx tsc --noEmit"
Resultado: PASS

docker exec -e NEXT_PUBLIC_SUPABASE_URL=https://aqrldlmlszjtgpqiegaa.supabase.co -e NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_build_placeholder studiamatch-dev sh -lc "cd /app/web && npm run build"
Resultado: PASS
```

## Validaciones No Verdes Globales

```text
docker exec studiamatch-dev pytest
Resultado: FAIL por recoleccion de local/worktrees historicos y tests superseded fuera de alcance.

docker exec studiamatch-dev pytest tests
Resultado: 17 failed, 134 passed, 4 skipped por tests F9/F10 historicos superseded y falta de bs4 en el contenedor.
```

## Seguridad

- Hooks locales de commit: `credential scan passed` en todos los commits H2.
- `security-auditor` final sobre `HEAD d356fa8`: 0 criticos, 0 altos.
- GitHub Advanced Security MCP no disponible en este repo; no sustituye hooks/CI.

## Bloqueos Vigentes

- No se aplico el forward-fix `20260826_h2_editorial_layer_forward_fix.sql` en Supabase Free; requiere JIT DDL separada.
- No se ejecuto seed del diccionario ni backfill remoto; requiere JIT DML separada.
- No se ejecuto Pro, certificacion, schedules, writers remotos, canaries, deploys, push ni PR.
- El workspace conserva cambios ajenos CRLF/whitespace en `scripts/**`, `scripts/shared/utils.py` y `tests/test_harvester.py`; no pertenecen al set H2 commiteado.
