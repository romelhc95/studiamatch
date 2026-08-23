# TASK-GOV-CI-002 - Boundary estructural de homologacion O2-O5

## Estado

`PROPOSED_R2_PENDING_DIGEST_APPROVAL`

## Objetivo

Separar el `Canonical Path Boundary` incremental por WP del boundary estructural requerido para promociones protegidas O2-O5 entre `desarrollo`, `certificacion` y `main`.

## Contexto

PR #428 intento ejecutar O2 (`desarrollo -> certificacion`) pero fallo el job `Canonical Path Boundary` porque el diff acumulado entre ramas protegidas fue evaluado como si fuera un cambio incremental del WP activo. El grant JIT O2 quedo consumido por fallo y no autoriza retry.

## Alcance R2

- Agregar validacion estructural de eventos de promocion O2-O5 en `scripts/security/validate_work_package.py`.
- Enrutar O2-O5 desde `.github/workflows/security-audit.yml` al modo estructural.
- Mantener el boundary incremental para PR normales a `desarrollo`.
- Documentar la atestacion requerida de promociones.
- Registrar ADR-0031 y actualizar Context Graph.
- Bloquear PR #428 y el grant consumido `R3-GOV-HOM-001-O2` como rutas de retry.
- Requerir `opened` y `GITHUB_RUN_ATTEMPT=1` para promociones estructurales; cambios posteriores del PR fallan cerrados.

## Fuera De Alcance

- No ejecutar O2, O3, O4 ni O5.
- No cerrar, editar, reintentar ni mergear PR #428.
- No modificar manifests consumidos `WP-GOV-ARCH-001`, `WP-GOV-HOM-001` ni `WP-GOV-CI-001`.
- No ejecutar DB, Supabase, DDL/DML, backfills, writers, schedules, deploys ni secrets.

## Criterios De Salida

- `security-audit` identifica promociones O2-O5 por par base/head y exige `Promotion Attestation`.
- PR normales siguen evaluados con `--changed-from` y allowlist incremental.
- Las promociones validan repositorio origen, operacion, `Grant-ID` nuevo y unico, par, Base-SHA, Candidate-SHA, ancestry, tree sintetico, `Final-WP`, `D_FINAL`, `T_FINAL`, nivel R3 JIT, referencia de aprobacion, expiry, accion `opened` y run attempt `1`.
- La validacion local no crea ni consume grants R3; el consumo por exito, fallo, timeout o cancelacion se registra externamente en el gate posterior porque CI no tiene ledger persistente en este alcance.
- GOV-CI-002 queda como candidate local R2, pendiente de aprobacion humana por digest antes de push/PR.
