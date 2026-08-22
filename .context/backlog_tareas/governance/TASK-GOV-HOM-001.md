# TASK-GOV-HOM-001 - Reconciliacion Post-PR425 Y Homologacion No Recursiva

| Campo | Valor |
|---|---|
| Estado | `PROPOSED_R2_PENDING_DIGEST_APPROVAL` |
| Work package | `WP-GOV-HOM-001` |
| Objetivo | Registrar PR #425, congelar la ruta de homologacion no recursiva F10.11 y producir `T_HOM` para convergencia posterior. |
| Baseline | `desarrollo@4cce43a743de5860c4da86eecf1782efab91d26b` |
| Tree baseline | `ac16b545b74a03b149aac538062def20101187fb` |
| Alcance | Documentacion de gobierno, manifest, validadores y regresiones; sin promocion remota. |

## Antecedente Consumido

`WP-GOV-ARCH-001` fue aprobado externamente por digest `df48d75129cfe2ba8971f55573a597ca47fb0e3c20e11a3a6a63377349be44e1` y consumido por PR #425, mergeado a `desarrollo@4cce43a743de5860c4da86eecf1782efab91d26b` con tree `ac16b545b74a03b149aac538062def20101187fb`, Governance Preflight PASS, `security-audit` PASS y review humano. El manifest `WP-GOV-ARCH-001` se preserva como artifact firmado y no se modifica.

## Alcance

1. Crear `WP-GOV-HOM-001` como candidate `R2` local.
2. Actualizar Estado, Plan Maestro, Tracker, Context Graph, evidencia H2, flujo release e indice para reemplazar el gate consumido por `PREPARE_WP_GOV_HOM_R2_APPROVAL`.
3. Definir predicado externo de cierre F10.11 antes de cualquier R3.
4. Definir templates separados para `O2`, `O3`, `O4` y `O5` sin concederlos ni ejecutarlos.
5. Clasificar Cloudflare Pages de `desarrollo` como `AUTOMATIC_NON_PRODUCTION_PREVIEW_SIDE_EFFECT`.
6. Mantener `WP-H2-001=ACTIVE_R1`, `H2-CA2=NOT_STARTED`, `H2-CA3=NOT_STARTED` y progreso contractual `0`.

## Fuera De Alcance

- Push, PR, merge, Certification, Main o cualquier R3.
- Supabase Free/Pro, DDL/DML, migraciones, backfill, RLS/grants remotos.
- Workflow dispatch, writers, schedules, deploy manual, secretos, PII o fuentes privadas.
- Cambios en `web/**`, `db/**`, `supabase/**`, `scripts/core/**`, `scripts/maintenance/**` o `workers/**`.
- Mutar `WP-GOV-ARCH-001.json`.
- Iniciar H2.

## Criterio De Salida Local

- Candidate commit local con `WP-GOV-HOM-001` en `PROPOSED` y digest calculado.
- Validadores, tests, scans y boundary pasan contra `4cce43a743de5860c4da86eecf1782efab91d26b`.
- Siguiente gate unico: aprobacion humana por digest para `WP-GOV-HOM-001` hasta R2.
