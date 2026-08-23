# ADR-0038 - Owner-Only Updates Para Ramas Protegidas

## Estado

Aceptada localmente como candidate CI9.

## Contexto

PR #440 completo correctamente el contenido de O2 hacia `certificacion`, pero el push post-merge fallo con `POST_MERGE_MERGER_INVALID` porque `romelhc95-approver` aprobo y tambien mergeo el PR. Las branch protections actuales exigen review y CI, pero no impiden que un colaborador con `write` actualice `desarrollo`, `certificacion` o `main` despues de aprobar.

## Decision

Se define un desired state permanente owner-only para updates de ramas protegidas. `romelhc95-approver` conserva su rol real de reviewer/aprobador, incluyendo aprobacion del Environment `Promotion`, pero no debe actualizar ni mergear `desarrollo`, `certificacion` o `main`. `romelhc95` conserva el rol de desarrollador y merger una vez que CI y review esten verdes.

El mecanismo objetivo es un ruleset de branch con `Restrict updates` aplicado a `refs/heads/desarrollo`, `refs/heads/certificacion` y `refs/heads/main`, con bypass exclusivo para el usuario `romelhc95` (`actor_id=18040405`). El usuario `romelhc95-approver` (`actor_id=306979205`) queda excluido del bypass.

## Consecuencias

- La separacion reviewer/merger deja de depender de recordar cambiar de cuenta.
- Branch protection, `security-audit`, reviews y `enforce_admins` se mantienen como capas existentes.
- El validador post-merge conserva la comprobacion de identidad como defensa secundaria.
- HOM-009 reemplaza a HOM-008 como familia runtime futura; HOM-006/HOM-007/HOM-008 quedan bloqueadas como historia superseded.
- Crear o modificar el ruleset remoto requiere R3 JIT separado y no queda autorizado por este candidate local.
