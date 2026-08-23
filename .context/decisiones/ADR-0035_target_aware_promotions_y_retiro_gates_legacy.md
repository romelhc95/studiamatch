# ADR-0035 - Promociones target-aware y retiro de gates legacy

## Estado

`ACCEPTED_CANDIDATE`

## Contexto

PR #435 intento O2 despues de CI5 y fallo antes de mergear por ejecucion del workflow legacy F9.7. El fallo consumio el grant HOM-005 O2 y mostro dos problemas: gates congelados siguen activos en contextos modernos, y las promociones directas entre ramas protegidas no resuelven la divergencia historica con `strict=true`.

## Decision

Las promociones O2-O5 posteriores a CI6 usaran ramas sinteticas target-aware `promote/gov-hom-006-oN`. Cada candidate commit tendra como primer padre el SHA exacto del target y como segundo padre el SHA exacto del source; su tree sera igual al tree del source y a `T_FINAL`.

El contrato F9.7 queda en modo `MANUAL_FROZEN_ONLY`: conserva evidencia historica congelada, pero elimina triggers automaticos `pull_request` y `push`. Solo puede ejecutarse manualmente con autorizacion R3 separada si se necesita auditar el frozen commit `258ef3a98c7c1010efe58522bb1eca892e26390e`.

## Consecuencias

- Branch protection `strict=true` permanece activa; no hay bypass.
- PR #435 no se edita ni reintenta; su grant queda consumido.
- Las nuevas solicitudes HOM-006 no contienen SHAs, digests, aprobaciones ni expiries concretos.
- O3 hacia `main` reconoce efectos automaticos de Production: Cloudflare Pages rebuild y DB Sync detect-only. El unico resultado aceptable de DB Sync es `NO_DB_CHANGES`; apply, DDL/DML y writers siguen prohibidos sin R3 adicional.
- El cierre pre H2-H5 deja de ser recursivo: una vez CI6 se publique y homologue, el siguiente trabajo funcional debe iniciar con `WP-H2-002` nuevo.
