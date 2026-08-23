# TASK-GOV-CI-004 - Environment dedicado para Promotion Boundary

## Estado

`CANDIDATE_R1_LOCAL`

## Contexto

PR #430 publico `WP-GOV-CI-003` a `desarrollo@235c2329eb5fd8903c31785640a63466b23f0dd8`, tree `cc774746d21cb6649f7018da3049fc811a3f294b`.

El nuevo intento O2 en PR #431 fallo antes de ejecutar el validator de attestation. GitHub rechazo el job `Promotion Boundary` porque el Environment `Certification` solo permite la rama `certificacion`, mientras los eventos `pull_request` usan el ref sintetico `refs/pull/<n>/merge`.

## Problema

La seleccion del Environment por rama destino (`Certification`, `Production` o `Development`) mezcla dos contratos: proteccion de ambientes de despliegue y validacion CI de promociones. Esa mezcla impide ejecutar el gate en PRs de promocion antes de cualquier paso Python.

## Alcance R1

- Cambiar `Promotion Boundary` para usar exclusivamente el Environment `Promotion`.
- Documentar que `Promotion` debe tener reviewer requerido `romelhc95-approver`, `prevent_self_review=true` y ninguna deployment branch policy.
- Mantener condiciones same-repo y pares exactos O2-O5 en workflow y validator.
- Bloquear `PR #431` y `R3-GOV-HOM-003-O2-REQ1` como consumidos por fallo.
- Crear nuevas solicitudes estaticas `R3-GOV-HOM-004-O2/O3/O4/O5-REQ1`.

## Fuera De Alcance

- Crear/configurar remotamente el Environment `Promotion` durante R1.
- Cerrar, editar, reabrir, reintentar o mergear PR #431.
- Abrir un nuevo O2/O3/O4/O5.
- Certification, Main, Supabase, DB, DDL/DML, migraciones, backfill, RLS/grants, writers, schedules, deploys, workflow_dispatch, secretos o cualquier R3.

## Criterios De Salida

- `WP-GOV-CI-004` valida por digest.
- `Promotion Boundary` usa `environment.name: Promotion` y no usa `Certification`, `Production` ni `Development` como environment del gate.
- PR #431 y `R3-GOV-HOM-003-O2-REQ1` quedan bloqueados por validator.
- Nuevas solicitudes HOM-004 existen sin SHA/tree/digest/approval/expiry/consumed.
- Tests de gobierno pasan en Docker.
- `security-auditor` no reporta hallazgos bloqueantes.
