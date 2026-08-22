# TASK-GOV-CI-003 - Bootstrap no autorreferencial de grants de promocion

## Estado

`CANDIDATE_R1_LOCAL`

## Contexto

PR #429 publico `WP-GOV-CI-002` a `desarrollo@1ac74f78fec6290e214444e9d2f18619ae3fd3b6`, tree `8191790192580f2e9fb1ddb48d85ab28714720f9`, y endurecio el boundary estructural para O2-O5.

El intento O2 previo en PR #428 permanece `FAILED_NOT_MERGED`; su grant `R3-GOV-HOM-001-O2` quedo consumido y no puede reutilizarse. PR #428 debe cerrarse administrativamente sin merge en el futuro R2 de este WP, antes de publicar nuevos cambios a `desarrollo`.

## Problema

El validador de `WP-GOV-CI-002` espera un archivo `.context/r3_grants/<Grant-ID>.json` que contiene `candidate_sha` y `t_final` exactos del mismo commit que contiene ese archivo. Esto crea una autorreferencia imposible: modificar el JSON cambia el tree y el commit que el JSON intenta fijar.

## Alcance R1

- Reemplazar grants versionados aprobados por solicitudes estaticas `REQUESTED_JIT_SINGLE_USE`.
- Usar bindings simbolicos para `base_sha`, `candidate_sha` y `t_final`.
- Mantener los valores exactos de SHA/tree/digest en la `Promotion Attestation` y validarlos en runtime.
- Precrear solicitudes separadas O2, O3, O4 y O5 dentro del tree final.
- Documentar que aprobacion y consumo son externos; CI no provee ledger persistente.

## Fuera De Alcance

- Cerrar, editar, reabrir, reintentar o mergear PR #428 durante R1.
- Abrir O2/O3/O4/O5.
- Certification, Main, Supabase, DB, DDL/DML, migraciones, backfill, RLS/grants, writers, schedules, deploys, workflow_dispatch, secretos o cualquier R3.

## Criterios De Salida

- `WP-GOV-CI-003` valida por digest.
- Las cuatro solicitudes estaticas O2-O5 existen y no contienen `candidate_sha`, `t_final`, approvals, expiry ni `consumed=false`.
- `validate_promotion_event` valida los bindings simbolicos contra el evento real.
- Tests de gobierno pasan en Docker.
- `security-auditor` no reporta hallazgos bloqueantes.
