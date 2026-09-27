# Plan Maestro Sprint 1 H2-H5

> Esta nota no crea alcance ni autoriza ejecucion. La autoridad viva esta en
> [`estado_del_proyecto.md`](../estado_del_proyecto.md) y el nuevo plan activo
> esta en [Plan Vinculante Nuevo Pedido](plan_vinculante_nuevo_pedido_2026_08_25.md).

## Estado

```text
FASE = F11
ESTADO = NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE
SUBGATE_H3_03B_DB = H3-BUILD-03B-DB_LOCAL_VALIDATED
historical_prestart_gate = H3_READY_FOR_PROMPT_CONTINUA
H2-H5 = REDEFINED_ACTIVE_SEQUENCE
H3 = LOCAL_UAT_GO_REMOTE_CLOSURE_PENDING
active_work_package = NONE_SUPERSEDED
next_gate = UAT Development + JIT 03A/03B remoto; luego Certification
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
H3 local: ciclo de corrección 2026-09-02 y revalidación documental 2026-09-03 completados
(workflow/gates H3, invariantes DB, regresión A6/A13 PG17, MFA local, UAT E2E/artifacts,
auditorías locales) -> PR protegido a desarrollo (mergeado en `e3d21c1`)
-> validación remota Development sobre Free + preview Pages de `desarrollo` (Free/A6-A13 PASS; UAT admin pendiente por despliegue)
-> corrección y validación de separación Pages/Access por ambiente
-> PR protegido desarrollo a certificacion
-> validación remota Certification sobre Free + preview/hostname de `certificacion`
-> PR protegido certificacion a main
-> validación remota Production sobre Pro + `admin.studiamatch.com`
-> contract de legacy y cierre documental
```

Addendum 2026-09-21: el subgate DB de `H3-BUILD-03B` quedó validado localmente
con TTL de 24 horas, RPCs de onboarding, locks, auditoría e idempotencia.
Frontend/Auth local y Mock UAT-02 quedaron validados posteriormente; el siguiente
gate es JIT/UAT remoto por ambiente, no se salta directamente a promoción.

## Reglas

- H2-H5 quedan redefinidos por el nuevo plan vinculante; H2 conserva su historia de promoción. H3 conserva GO técnico local, pero el cierre vigente es `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`; el PR está en `desarrollo` (`e3d21c1`). La validación remota Development debe ejecutarse sobre Free y el deployment/preview real de `desarrollo`, no sobre `admin.studiamatch.com`, que permanece reservado al deployment productivo. JIT-B mantiene E1/E3/E4/E8 PASS y E2/E5/E6/E7 pendientes hasta corregir hostname/build/Access. Build normal/mock PASS; waiver static export superseded.
- Antes de iniciar y al cerrar todo hito/task debe validarse contra la fuente privada cliente usando su atestación sanitizada versionada; si falla, se corrige primero la documentación y no se ejecuta el siguiente hito.
- La ampliación H3 está respaldada por la atestación sanitizada `H3-EXPANDED-PROMPT-2026-08-30`, que autoriza ejecución local Docker hasta GO local; las acciones remotas, promoción y despliegue siguen bloqueadas por aprobaciones separadas.
- Pro es la fuente autoritativa de schema, tipos, constraints, campos y migraciones H2; Free y PostgreSQL 17 local convergen hacia Pro. No se usa Free/local para modificar Pro ni se sincronizan datos operativos como mecanismo normal.
- Las migraciones H3 ya validadas en Docker se conservan y reutilizan como candidato. Se rebasan contra la forma Pro en una base PG17 limpia; solo se crean deltas idempotentes por incompatibilidad demostrada. No se repite ni elimina trabajo H3 local automáticamente y no se promueven datos de prueba.
- Work Packages, grants R3, digests documentales, Context Graph y promotion gates historicos quedan superseded y no autorizan ejecucion.
- Cambios DB, DDL/DML, Supabase, writers, schedules, deploys, produccion, backups y acciones destructivas requieren aprobacion JIT separada.
- `security-audit` permanece como check requerido.
- DB Sync permanece manual-only.
- Todo cambio debe documentar transicion transparente `expand -> compatibilidad -> deploy -> contract`, preservando funcionalidad legacy durante construccion/promocion y retirandola tras estabilizar produccion.
- Addendum de cierre 2026-09-23: MFA/`aal2` fue retirado del gate por decisión de alcance, por complejidad de prueba y porque no bloquea la funcionalidad principal H3REQ1. Se conserva como compatibilidad/mejora evolutiva. El cierre contractual es `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE` hasta completar UAT remota, 03A/03B remoto, Certification y contract/cleanup.

## Bases De Transicion

| Rama | Commit | Estado |
|---|---|---|
| `desarrollo` | `e3d21c1b0de7faa224b0b34f830b3ecbc5d6921d` | PR #495 mergeado; preview Pages `88f02c53.studiamatch-aty.pages.dev` validado como deployment del SHA de desarrollo. |
| `certificacion` | `8b843ac3714866dbce7b44958362fe7243ae06b9` | PR #452 mergeado con reconciliacion; pendiente promoción H3. |
| `main` | `6128e5861ade426840a650335f7f859c803e5431` | Producción Pages; `admin.studiamatch.com` no debe usarse para validar `desarrollo`. |

## Hitos y siguientes gates

| Hito | Estado | Gate futuro |
|---|---|---|
| H2 | `CLOSED_H2_PRO_EXPAND_VERIFIED_MAIN` | Pro `expand + compatibilidad` y DB Sync H2 verificados; promoción protegida a `main` completada. |
| H3 | `H3-BUILD-03B-DB_LOCAL_VALIDATED` como subgate técnico local; cierre `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE` | Edge 03A y DB onboarding 03B validados en Docker PG17; faltan validación remota, UAT por ambiente, Certification y main. |
| H4 | `PLANNED_AFTER_H2_CONTRACT_STABLE` | Contrato H2 estable. |
| H5 | `PLANNED_AFTER_H2_CONTRACT_STABLE` | Contrato H2 estable. |

## Stop Conditions

- Aparece un secreto o valor credential-like.
- Cambia una ruta protegida sin aprobacion separada.
- Se intenta ejecutar DB Sync, DDL/DML o writer productivo.
- Se intenta iniciar H2 con DDL/DML, Supabase o backfill sin aprobacion JIT separada.
- Falta evidencia de compatibilidad, rollback o contraccion legacy para un cambio funcional, DB, UI, pipeline o despliegue.
- Se intenta promover `certificacion -> main` antes de verificar Pro expandido con baseline `224` y vista `courses_public_effective` compatible.
- Se intenta cerrar H3 sin invitación auditada por correo, sin onboarding remoto, sin UAT por ambiente o sin aislamiento `admin.studiamatch.com`/404 público. MFA queda fuera del gate conforme al addendum 2026-09-23.
