# H3REQ1 Closure Review Final

**Fecha de auditoría:** 2026-09-23
**Hito:** HITO-003 / H3REQ1
**Fuente cliente:** `SRC-REQ-002` / `ADENDA-REQ-EST-001-001`
**Estado final:** `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`

## Alcance De Cierre

Esta revisión aplica el alcance solicitado para el cierre H3REQ1:

- autenticación administrativa existente;
- RBAC;
- invitaciones;
- aceptación de invitación;
- onboarding;
- gestión de usuarios;
- edición de cursos;
- ownership editorial;
- restricción pública;
- perímetro;
- compatibilidad y transición SDLC.

MFA se retira del gate de aceptación H3REQ1. La decisión se registra por la
complejidad de su prueba y porque no bloquea la funcionalidad principal solicitada.
La implementación MFA/`aal2` existente se conserva como compatibilidad y queda
registrada como mejora evolutiva/posterior; no se modifica código ni se elimina su
enforcement en este cierre.

## Acceptance Criteria Matrix

| Requisito | Código | Evidencia | Estado |
|---|---|---|---|
| Login administrativo | `web/src/app/admin/login/page.tsx`; `supabaseAdminLogin()` en `web/src/lib/admin-auth.ts` | Local: UAT canónica H3-UAT-002 y build mock. Remota: preview expone `/admin/login/`, sin sesión funcional reproducible | `PARTIAL`, remoto pendiente |
| RBAC | `requireActiveAdmin()`, `requireAdmin()`, `admin_current_user_role` y RPCs H3 | Local: UAT H3-CA4.1 y PG17. Remota: Free tiene H3 hasta `20260903`, sin UAT web autenticada | `PARTIAL`, remoto pendiente |
| Invitaciones | `supabase/functions/admin-invite/index.ts`; `admin_invitation_reserve/complete/fail` | Local: `evidencia_h3_invitation_flow_local_2026-09-19.md`, harness Edge PASS, `STUDIAMATCH-H3-UAT-MOCK-02-REPORT.md`. Remota: Edge Free ACTIVE `verify_jwt=true`; no hay migraciones remotas 03A/03B ni prueba de correo real | `PARTIAL`, remoto pendiente |
| Aceptación de invitación | `/admin/auth/callback/`, `exchangeCodeForSession()`, `admin_accept_current_invitation` | Local: Mock UAT-02 PASS y contrato callback PASS. Remota: callback PKCE/Auth real no validado | `PARTIAL`, remoto pendiente |
| Onboarding | `/admin/accept-invite/`, `/admin/setup-password/`, `admin_get_onboarding_status`, `admin_complete_password_setup` | Local: harness DB 03B PASS y Mock UAT-02 PASS. Remota: `20260921_h3_invitation_onboarding_rpc.sql` ausente de Free y Pro | `FAIL de evidencia remota` |
| Gestión de usuarios | `web/src/app/admin/users/page.tsx`; `admin_list_members`, `admin_update_member` | Local: UAT RBAC/membresías y PG17. Remota: no existe UAT autenticada sobre deployment correcto; estados de onboarding no están expuestos por la firma legacy remota | `PARTIAL`, remoto pendiente |
| Edición de cursos | `web/src/app/admin/edit/page.tsx`; `admin_update_course` y mutaciones editoriales | Local: UAT H3-CA4.2/H3-CA4.5, build y PG17 PASS. Remota: no validada sobre deployment y datos del ambiente | `PARTIAL`, remoto pendiente |
| Ownership | allowlist de 13 campos, `missing_fields`, RPC reader/editorial | Local: UAT ownership y harness PG17 PASS. Remota: valores efectivos y permisos no probados en UAT web por ambiente | `PARTIAL`, remoto pendiente |
| Restricción pública | `web/functions/_middleware.ts`; `mock-server/static-server.js`; mecanismo 404 | Remota: `https://www.studiamatch.com/admin/` devuelve 404 y `/` devuelve 200. `admin.studiamatch.com` prueba Access 302, no ausencia de contenido post-login. Apex tuvo error de transporte | `PARTIAL` |
| Perímetro | Cloudflare Access para `admin.studiamatch.com`; host de preview `88f02c53.studiamatch-aty.pages.dev` | Remota: E1/E3/E4/E8 PASS documentados. No existe hostname administrativo estable separado para Development y Certification | `PARTIAL`, no certificable |
| Compatibilidad | migraciones expand-only, rutas legacy, rollback y flujo `expand -> compatibilidad -> deploy -> contract` | Local: builds normal/mock, PG17 y rollback documentados. Remota: deploy, Certification, Pro H3 y contract/cleanup no ejecutados | `FAIL de cierre` |

## Evidencia Local

- UAT core: `47/47` casos, `141/141` ejecuciones, tres viewports, 141 screenshots y 0 retries en `.context/evidencia/h3-expanded/`.
- Builds normal y mock PASS; TypeScript PASS; lint PASS con 9 warnings históricos; credential scan PASS; `git diff --check` PASS.
- PG17 H3, Edge 03A y DB onboarding 03B PASS en Docker.
- Mock UAT de invitación actualizado el 2026-09-23: `STUDIAMATCH-H3-UAT-MOCK-02-REPORT.md`, flujo `invite -> inbox -> verify -> callback -> setSession -> accept -> password -> READY` PASS.
- La evidencia local no sustituye Auth, correo, Edge, DB o Pages remotos.

## Evidencia Remota

- Supabase Free mantiene las migraciones H3 base y `20260903_h3_rbac_contract_fix`; la inspección read-only no muestra `20260918`, `20260919`, `20260920` ni `20260921`.
- Supabase Free expone `admin-invite` ACTIVE con `verify_jwt=true`.
- Supabase Pro no muestra migraciones H3 en el inventario remoto revisado.
- `www.studiamatch.com/` respondió 200 y `www.studiamatch.com/admin/` respondió 404.
- `admin.studiamatch.com/admin/` respondió con la pantalla de Cloudflare Access, evidenciando el perímetro, no una UAT del panel.
- `88f02c53.studiamatch-aty.pages.dev` corresponde documentalmente al preview de Development, pero las rutas nuevas `/admin/accept-invite/`, `/admin/setup-password/` y `/admin/auth/callback/` respondieron 404 en la consulta de cierre.

## Checklist De Validación Remota

| Caso | Resultado | Evidencia de cierre |
|---|---|---|
| 1. Usuario admin ingresa | `PENDIENTE` | Falta login interactivo con Auth y membresía del ambiente correcto |
| 2. Usuario recibe invitación | `PENDIENTE` | Falta Edge remoto funcional, correo real y persistencia 03A |
| 3. Usuario acepta invitación | `PENDIENTE` | Falta callback PKCE/Auth real y migración 03B remota |
| 4. Usuario completa onboarding | `PENDIENTE` | Falta `setup-password` remoto y reconciliación Auth/DB |
| 5. Admin administra usuarios | `PENDIENTE` | Falta UAT autenticada sobre deployment correcto |
| 6. Admin edita información | `PENDIENTE` | Falta UAT autenticada sobre datos remotos |
| 7. Usuario sin permisos recibe bloqueo | `PENDIENTE` | El negativo está probado localmente; falta repetición remota |
| 8. `/admin` público no expone contenido privado | `PARCIAL PASS` | `www` `/admin/` 404 PASS; Access 302 PASS; apex, post-login y todos los ambientes no están cerrados |

## Evidencia Faltante

- UAT remota completa de los ocho casos en Development, con SHA/deployment ID y
  Supabase project ref.
- Aplicación y verificación remota de las migraciones 03A/03B en el ambiente
  autorizado, sin asumir que el inventario Free actual las contiene.
- Prueba remota de `verify_jwt=true`, correo real, redirect allowlist, callback PKCE,
  aceptación, password setup, TTL e idempotencia.
- Hostnames administrativos separados y protegidos para Development y Certification.
- UAT H3 completa en Certification y evidencia de Pro antes de la promoción a main.
- Diff de convergencia completo con Pro como baseline, incluyendo funciones, grants,
  RLS, vistas, constraints y migraciones H3.
- Evidencia de `deploy -> contract`, contract/cleanup y retiro controlado de legacy.
- Revalidación funcional remota inequívoca de A6/A13; la presencia de la migración
  `20260903` no sustituye la ejecución de los casos.

## Hallazgos

| ID | Descripción | Impacto | Evidencia faltante | Responsable | Siguiente acción |
|---|---|---|---|---|---|
| H3-CR-001 | El alcance MFA ya fue retirado por decisión humana, pero documentos históricos todavía lo describen como criterio obligatorio | Medio, trazabilidad | Decisión canónica y referencias actualizadas | Release Manager | Mantener este documento como autoridad de cierre y marcar referencias antiguas como históricas |
| H3-CR-002 | El flujo 03A/03B no está instalado en los ambientes remotos revisados | Alto, invitación y onboarding no operables remotamente | Migraciones `20260918`-`20260921` y verificación de funciones/RPC | Supabase/Platform | Solicitar JIT DDL y validar Free; no tocar Pro sin aprobación separada |
| H3-CR-003 | El preview actual devuelve 404 para las tres rutas nuevas de onboarding | Alto, impide UAT del flujo | Deployment correcto con rutas y SHA verificables | Frontend/DevOps | Reconciliar artefacto Pages y repetir smoke; no declarar PASS por el preview actual |
| H3-CR-004 | Los casos remotos 1-7 no tienen ejecución autenticada reproducible | Alto, aceptación contractual incompleta | Artifacts de UAT por ambiente | QA/Release Manager | Ejecutar UAT remota cuando exista hostname y autorización JIT |
| H3-CR-005 | `admin.studiamatch.com` pertenece al Pages de producción y no representa Development | Alto, perímetro/ambiente ambiguo | Hostnames, deployment IDs y policies por ambiente | DevOps/Cloudflare | Separar targets administrativos y documentar SHA/ref |
| H3-CR-006 | Certification no tiene evidencia H3 y Pro no tiene migraciones H3 verificadas | Alto, promoción no autorizable | UAT Certification y preflight Pro | Release Manager/Supabase | Completar Development, luego PR protegido a Certification y finalmente Pro con JIT |
| H3-CR-007 | La transición `expand -> compatibilidad -> deploy -> contract` permanece abierta | Alto, no hay cierre ni rollback remoto probado | Evidencia de deploy, contract/cleanup y rollback por ambiente | Release Manager | Cerrar cada fase con evidencia antes de promover |
| H3-CR-008 | La matriz Pro/Free/local no demuestra convergencia completa del delta H3 | Alto, riesgo de drift | Comparación reproducible de schema, RPC, grants, RLS y vistas | Supabase/DBA | Ejecutar diff read-only autorizado y corregir solo en la dirección Pro -> Free/local |

## Riesgos Abiertos

- `sessionStorage` permanece como riesgo documentado pre-Certification.
- `npm audit` reporta dependencias transitorias HIGH/CRITICAL; no se modifica el
  baseline en este cierre.
- El endpoint público apex `studiamatch.com` no tuvo una respuesta HTTP reproducible
  en esta auditoría; `www` sí tiene evidencia 200/404.
- El listado de usuarios conserva una firma legacy que puede mostrar estados de
  invitación como `No expuesta` hasta que el contrato remoto exponga esos campos.
- MFA/`aal2` continúa presente en el código y en las RPC sensibles como compatibilidad;
  queda fuera del gate H3, no eliminado.

## Cambios Documentales Realizados

- Se registra MFA como criterio retirado del gate, con motivo y estado evolutivo.
- Se incorpora esta matriz final requisito-código-evidencia-estado.
- Se separan evidencia local, evidencia remota y evidencia pendiente.
- Se reconcilia la evidencia Mock UAT-01 histórica con el reporte Mock UAT-02 PASS
  del 2026-09-23.
- Se registra el inventario remoto observado sin afirmar aplicación de migraciones
  03A/03B ni UAT funcional remota.
- Se conserva la transición `expand -> compatibilidad -> deploy -> contract` y el
  rollback como requisito abierto.
- Durante la revalidación local apareció un error TypeScript en dos llamadas a
  `supabase.auth.setSession()` porque la versión SDK instalada no acepta campos de
  expiración en ese objeto. Se retiraron únicamente esos campos redundantes de
  `web/src/lib/admin-auth.ts`; no cambió el flujo funcional ni se tocaron DB,
  migraciones o ambientes remotos. `tsc`, build mock, contratos H3 y credential
  scan volvieron a pasar.

## Transición Y Rollback

- `expand`: implementado y validado localmente; no se agregan cambios funcionales en
  esta auditoría.
- `compatibilidad`: rutas legacy, Auth existente y MFA legacy se conservan.
- `deploy`: no ejecutado por restricción explícita.
- `contract`: bloqueado hasta completar evidencia remota por ambiente.
- `rollback`: debe ser una operación aprobada y reproducible por ambiente; no hubo
  writes remotos en este ciclo.

## Decisión Final

**NO-GO cierre H3REQ1.**

El GO técnico local permanece válido para el alcance local, pero no se cumplen los
criterios de cierre solicitados porque la evidencia remota es incompleta y contiene
un deployment que no sirve las rutas actuales de onboarding. No se autoriza declarar
cierre ni avanzar promoción `desarrollo -> certificación -> main` con la evidencia
actual. No se ejecutaron migraciones, deploy, merge, push ni writes/cambios remotos
en esta auditoría. La corrección TypeScript local fue la única modificación de
código, necesaria para cerrar la validación reproducible del candidato.
