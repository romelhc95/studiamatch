# TASK-GOV-OBS-001 - Release Documentacion Obsidian

| Campo | Valor |
|---|---|
| Estado | `PROPOSED_R2_PENDING_DIGEST_APPROVAL` |
| Work package | `WP-GOV-OBS-001` |
| Objetivo | Publicar y homologar documentacion Obsidian candidate hasta `desarrollo` mediante R2. |
| Baseline candidate | `486bf420cb0d8ad250bc7b3cceb21545184b4dd5` |
| Tree candidate | `bc521d7b030095fb1ef928923e333cb4721cda94` |
| Cierre Etapa 1 | `LOCAL_CANDIDATE_PENDING_MAIN` |

## Alcance

1. Preparar aprobacion por digest de `WP-GOV-OBS-001` hasta R2, emparejada con `WP-GOV-INFRA-001` para cubrir el diff completo del PR #424.
2. Autorizar posteriormente solo push, PR y merge a `desarrollo` del bundle documental.
3. Mantener Certification/Main, DB, Supabase, deploys, writers, schedules y produccion como R3 JIT separados.
4. Mantener H2-CA2 y H2-CA3 en `NOT_STARTED`.

## Criterio De Salida R2 Futuro

- PR protegido a `desarrollo` con CI y review humano.
- Sin cambios funcionales frente al candidate documental.
- Proximo gate posterior: R3 JIT single-use para `certificacion`.

Esta TASK no autoriza operaciones remotas por si sola. La autorizacion ejecutable debe usar el formato WP/digest R0-R3.
