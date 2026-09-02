# Plan Maestro Sprint 1 H2-H5

> Esta nota no crea alcance ni autoriza ejecucion. La autoridad viva esta en
> [`estado_del_proyecto.md`](../estado_del_proyecto.md) y el nuevo plan activo
> esta en [Plan Vinculante Nuevo Pedido](plan_vinculante_nuevo_pedido_2026_08_25.md).

## Estado

```text
FASE = F11
ESTADO = H3_PR_DEVELOPMENT_READY_LOCAL
historical_prestart_gate = H3_READY_FOR_PROMPT_CONTINUA
H2-H5 = REDEFINED_ACTIVE_SEQUENCE
H3 = LOCAL_UAT_GO_PENDING_REMOTE
active_work_package = NONE_SUPERSEDED
next_gate = PR + JIT FREE/AUTH (autorizacion humana separada)
DB = FREE_H2_VALIDATED_PRO_EXPAND_VERIFIED_H3_FREE_PENDING
PRODUCTION_MUTATIONS = BLOCKED_WITHOUT_JIT
```

## Flujo Vigente

### Versión simple

```text
UAT estructural 47/47 y 141/141 preservada
-> corregir CI, DB, MFA, E2E, rollback y artifacts
-> repetir QA/seguridad/DB hasta cero HIGH/CRITICAL
-> declarar PR_READY
-> aprobación separada commit + push + PR protegido a desarrollo
-> JIT separado Supabase Free/Auth y evidencia remota en el PR abierto
-> security-audit + revisión + aprobación separada de merge a desarrollo
-> PR protegido desarrollo a certificacion
-> PR protegido certificacion a main
```

### Versión técnica

```text
H3 local: ciclo de corrección 2026-09-02 completado (workflow/gates H3, invariantes
DB, MFA real, UAT E2E/artifacts, auditorías sin HIGH/CRITICAL) -> H3_PR_DEVELOPMENT_READY_LOCAL
-> commit + push + PR protegido a desarrollo (autorización humana separada otorgada)
-> security-audit + revisión + aprobación separada de merge a desarrollo
-> JIT separado Supabase Free/Auth y evidencia remota en el PR abierto
-> PR protegido desarrollo a certificacion
-> PR protegido certificacion a main
```

## Reglas

- H2-H5 quedan redefinidos por el nuevo plan vinculante; H2 conserva su historia de promoción. H3 queda `H3_PR_DEVELOPMENT_READY_LOCAL` (GO para PR): el ciclo de corrección local del 2026-09-02 resolvió los bloqueadores HIGH/CRITICAL que QA/seguridad/DB habían detectado (estado previo `H3_PR_DEVELOPMENT_NO_GO`, histórico) en CI, DB, MFA, E2E, rollback y artifacts, y regeneró la UAT canónica 47/47 y 141/141 PASS con 0 retries. Build normal/mock PASS; waiver static export superseded. Commit + push + PR autorizados por instrucción humana separada; acciones remotas posteriores permanecen bloqueadas.
- Antes de iniciar y al cerrar todo hito/task debe validarse contra la fuente privada cliente usando su atestación sanitizada versionada; si falla, se corrige primero la documentación y no se ejecuta el siguiente hito.
- La ampliación H3 está respaldada por la atestación sanitizada `H3-EXPANDED-PROMPT-2026-08-30`, que autoriza ejecución local Docker hasta GO local; las acciones remotas, promoción y despliegue siguen bloqueadas por aprobaciones separadas.
- Pro es la fuente autoritativa de schema, tipos, constraints, campos y migraciones H2; Free y PostgreSQL 17 local convergen hacia Pro. No se usa Free/local para modificar Pro ni se sincronizan datos operativos como mecanismo normal.
- Las migraciones H3 ya validadas en Docker se conservan y reutilizan como candidato. Se rebasan contra la forma Pro en una base PG17 limpia; solo se crean deltas idempotentes por incompatibilidad demostrada. No se repite ni elimina trabajo H3 local automáticamente y no se promueven datos de prueba.
- Work Packages, grants R3, digests documentales, Context Graph y promotion gates historicos quedan superseded y no autorizan ejecucion.
- Cambios DB, DDL/DML, Supabase, writers, schedules, deploys, produccion, backups y acciones destructivas requieren aprobacion JIT separada.
- `security-audit` permanece como check requerido.
- DB Sync permanece manual-only.
- Todo cambio debe documentar transicion transparente `expand -> compatibilidad -> deploy -> contract`, preservando funcionalidad legacy durante construccion/promocion y retirandola tras estabilizar produccion.

## Bases De Transicion

| Rama | Commit | Estado |
|---|---|---|
| `desarrollo` | `8ed8e36259af53a16e1f473ad906b5beadd5b09c` | PR #451 mergeado con flujo simple. |
| `certificacion` | `8b843ac3714866dbce7b44958362fe7243ae06b9` | PR #452 mergeado con reconciliacion. |
| `main` | `6128e5861ade426840a650335f7f859c803e5431` | PR #453 mergeado; Cloudflare Pages automatico exitoso. |

## Hitos y siguientes gates

| Hito | Estado | Gate futuro |
|---|---|---|
| H2 | `CLOSED_H2_PRO_EXPAND_VERIFIED_MAIN` | Pro `expand + compatibilidad` y DB Sync H2 verificados; promoción protegida a `main` completada. |
| H3 | `H3_PR_DEVELOPMENT_READY_LOCAL` | Bloqueadores QA/seguridad/DB resueltos en el ciclo de corrección local: CI H3, invariantes DB, MFA real, E2E, rollback y evidencia vinculada. Audits repetidos sin HIGH/CRITICAL. Commit + push + PR a desarrollo autorizados; luego JIT Free/Auth, certificación y main. |
| H4 | `PLANNED_AFTER_H2_CONTRACT_STABLE` | Contrato H2 estable. |
| H5 | `PLANNED_AFTER_H2_CONTRACT_STABLE` | Contrato H2 estable. |

## Stop Conditions

- Aparece un secreto o valor credential-like.
- Cambia una ruta protegida sin aprobacion separada.
- Se intenta ejecutar DB Sync, DDL/DML o writer productivo.
- Se intenta iniciar H2 con DDL/DML, Supabase o backfill sin aprobacion JIT separada.
- Falta evidencia de compatibilidad, rollback o contraccion legacy para un cambio funcional, DB, UI, pipeline o despliegue.
- Se intenta promover `certificacion -> main` antes de verificar Pro expandido con baseline `224` y vista `courses_public_effective` compatible.
- Se intenta cerrar H3 sin MFA TOTP `aal2` obligatorio para ambos roles, sin invitación auditada por correo o sin aislamiento `admin.studiamatch.com`/404 público.
