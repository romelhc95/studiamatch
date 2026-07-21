# Inventario De Limpieza Del Repositorio — 2026-07-20

## Estado
Inventario inicial. No implica eliminacion remota ni movimiento fisico hasta que el PR de higiene sea aprobado.

## Ramas
Ramas permanentes conservadas:

- `desarrollo`.
- `certificacion`.
- `main`.

Ramas temporales detectadas que requieren cierre, merge, reemplazo o eliminacion documentada:

- PR #202: `docs/obsidian-hito-governance` hacia `desarrollo`.
- PR #203: `feat/hito-1-foundation`, excluido de esta remediacion por contener Hito 1 funcional.
- PR #207: `promote/pre-hito1-to-certification` hacia `certificacion`.
- PR #47: `feat/fase92`, antiguo y con base desactualizada.

## Scripts Recurrentes Que Deben Permanecer
- `scripts/maintenance/release_gate.py`.
- `scripts/maintenance/db_migrate.py`.
- `scripts/maintenance/check_db_parity.py`.
- `scripts/maintenance/apply_nontransactional_migration.py`.
- `scripts/maintenance/verify_manifest_postconditions.py`.
- `scripts/maintenance/pipeline_canary.py`.
- `scripts/maintenance/agent_dispatcher.py`.

## Tests
Permanecen en Git solo tests recurrentes de contrato, gates y regresion. Los tests one-shot deben moverse a `desestimado/` o `scripts/local/` si no forman parte de CI ni de un gate recurrente.
