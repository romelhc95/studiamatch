# ADR-0040 - Promocion Transaccional Y Cierre O3

## Estado

Aceptada localmente como candidate CI11.

## Contexto

PR #443 fallo sin merge durante HOM-010 O2. Para evitar reutilizacion parcial de aprobaciones y carreras entre eventos, HOM-010 queda cerrado: `R3-GOV-HOM-010-O2-REQ1` consumido y HOM-010 O3-O5 superseded.

## Decision

Las promociones futuras usan HOM-011 y un secreto protegido unico `R3_JIT_APPROVAL_ENVELOPE` con schema `promotion-jit-envelope-v1`. El envelope es JSON estricto, sin campos desconocidos, y queda ligado a PR, run `opened`, `run_attempt=1`, refs, SHAs, tree, WP, digest, identidades, side effects y expiry.

`edited`, `reopened`, `synchronize`, `ready_for_review` y rerun invalidan la transaccion. La concurrency de promociones no cancela el run `opened` valido. `Promotion.can_admins_bypass=false` es desired state obligatorio antes de HOM-011.

O3 se considera cerrado solo si Cloudflare Pages reporta success con app_id `85455` sobre el merge SHA de `main` y `DB Sync Detect Only` reporta `NO_DB_CHANGES`. La ruta no-change no consume credenciales Production ni ejecuta report/apply/verify. O4 queda bloqueado hasta registrar cierre O3.

## Consecuencias

- PR #443 no se edita, cierra, reabre, rerunea ni mergea.
- No se reutiliza HOM-010.
- HOM-011 O2-O5 requieren R3 JIT separados y single-use.
- Readiness preflight puede leer metadata local/remota, pero no muta recursos.
- DB apply, DDL/DML, Supabase, writers, schedules, deploy manual y produccion siguen prohibidos sin R3 separado.
