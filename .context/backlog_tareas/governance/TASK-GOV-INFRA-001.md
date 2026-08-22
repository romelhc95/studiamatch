# TASK-GOV-INFRA-001 - Release Infraestructura De Gobierno

| Campo | Valor |
|---|---|
| Estado | `PROPOSED_R2_PENDING_DIGEST_APPROVAL` |
| Work package | `WP-GOV-INFRA-001` |
| Objetivo | Publicar guardrails de CI, runner Docker y script de pruebas de gobierno requeridos por PR #424. |
| Baseline candidate | `486bf420cb0d8ad250bc7b3cceb21545184b4dd5` |
| Base PR | `desarrollo@974f9d4bde6d79230afde5c5a86ba7a3894233c6` |

## Alcance

1. Cubrir exclusivamente infraestructura de gobierno ya presente en el diff acumulado del PR #424.
2. Mantener separado el alcance documental de `WP-GOV-OBS-001`.
3. No autorizar cambios funcionales, DB, frontend, pipeline, maintenance, Supabase ni despliegues.
4. No autorizar Certification/Main/R3.

## Criterio De Salida R2 Futuro

- `Canonical Path Boundary` del PR #424 pasa contra `desarrollo` usando la union explicita `WP-GOV-OBS-001` + `WP-GOV-INFRA-001`.
- CI `security-audit` pasa.
- Proximo gate posterior sigue siendo R3 JIT separado para `certificacion`.
