# H3REQ1 Remediation Report

**Fecha:** 2026-09-23
**Alcance:** correcciones locales necesarias para los hallazgos H3REQ1; sin
Supabase remoto, deploy, push, PR, merge, workflow dispatch ni promoción.

## Revalidación remota read-only — 2026-09-24

Se ejecutó una auditoría remota sin writes sobre Free y Pro. La evidencia
canónica está en
`.context/evidencia/h3_remote_validation_readonly_2026-09-24.md`.

- Free registra H3 solo hasta `h3_rbac_contract_fix` (`20260903`); no registra
  `20260918`–`20260921`.
- Free tiene `admin-invite` ACTIVE v1 con `verify_jwt=true`, pero no tiene
  `admin_invitations` ni las RPCs de invitación/onboarding requeridas.
- Pro no registra migraciones H3 consultables, no tiene las tablas H3 de
  membresía/invitación y no lista `admin-invite`.
- PostgreSQL remoto reportado: 17.6 en ambos ambientes.

Resultado: los hallazgos remotos siguen abiertos; esta auditoría no ejecutó DDL,
Auth writes, deploy, rollback, push, PR, merge ni promoción.

## Hallazgos corregidos

- Se corrigio el runner UAT para leer la sesion persistida por el cliente oficial
  Supabase PKCE (`*-auth-token`, `access_token`, `refresh_token`).
- Se corrigio el reset del mock para reconstituir identidades RBAC estables y sus
  membresias antes de cada corrida.
- Se hizo configurable el ejecutable Chromium del runner y se alineo al binario
  instalado en Docker.
- Se mantuvieron el callback PKCE, las rutas de onboarding, el cliente browser
  oficial, las RPCs de onboarding, el login legacy y MFA como compatibilidad.

## Evidencia generada

- `.context/evidencia/h3-invitation-flow/evidencia_h3_invitation_flow_remediation_local_2026-09-23.md`
- `.context/evidencia/h3req1_uat_matrix_local_2026-09-23.md`
- `.context/evidencia/h3-expanded/h3-expanded-uat-matrix.json`
- `.context/evidencia/h3-expanded/h3-expanded-uat-executions.json`
- `.context/evidencia/h3-expanded/h3-expanded-uat-manifest.json`
- `.context/evidencia/h3-expanded/h3-expanded-uat-artifact-hashes.json`
- 141 screenshots H3-UAT en `.context/evidencia/h3-expanded/`
- `STUDIAMATCH-H3-UAT-MOCK-02-REPORT.md` y contratos focalizados existentes

## Validaciones ejecutadas

| Validacion | Resultado | Evidencia verificable |
|---|---|---|
| UAT canonica H3 | PASS | 47/47 casos, 141/141 ejecuciones, 141 screenshots, 0 retries |
| UAT invitacion | PASS | 9/9 casos INV-001, INV-002, INV-003, INV-004, INV-005, INV-007, INV-008, INV-009, INV-012 |
| PG17 H3 harness limpio | PASS | `h3_invitation_onboarding_harness_ok`; `h3_pg17_harness_ok` |
| TypeScript | PASS | `npx tsc --noEmit` sin salida de error |
| Lint | PASS con 9 warnings historicos | 0 errores; warnings en `HomeContent.tsx` fuera de esta remediacion |
| Build normal | PASS | `npm run build`, compilacion estatica exitosa |
| Build mock | PASS | `npm run build:mock`, compilacion estatica exitosa |
| Contratos H3 focalizados | PASS | 8 tests `unittest` PASS |
| Python compile | PASS | `find scripts -name '*.py' -exec python3 -m py_compile {} +` |
| Node syntax | PASS | mock server y runners H3 sin errores de sintaxis |
| Credential scan | PASS | `credential scan passed` |
| Whitespace | PASS | `git diff --check` sin errores |

## Seguridad

- El frontend usa solo URL y publishable key desde variables de entorno.
- El secret key no llega al navegador; queda restringido a la Edge Function server-side.
- No se añadieron tokens, passwords, cookies, PII ni credenciales a la evidencia.
- El mock exige variables de entorno y solo habilita inbox/test endpoints con
  `NODE_ENV=test` y token de test.
- Supabase Cloud Only se conserva para el producto; PostgreSQL 17 es únicamente
  un harness local de validacion y no una base de producto alternativa.

## Compatibilidad legacy

- **Expand:** correcciones acotadas al mock y al runner; no se alteraron
  migraciones historicas ni el contrato público.
- **Compatibilidad:** login legacy, MFA existente, rutas publicas, callback PKCE,
  RPCs editoriales y cuentas `ready` se preservan.
- **Deploy:** no ejecutado por restriccion del ciclo.
- **Contract:** PASS local para los artefactos y harnesses; remoto pendiente.
- **Rollback:** revertir localmente los cambios de `mock-server/server.js` y
  `tests/h3_local_uat.mjs`; no requiere writes remotos.

## Riesgos pendientes

- Falta UAT Auth/PKCE real, correo real y reconciliacion Auth/DB en Development y
  Certification.
- No se acredita la aplicacion remota de las migraciones 03A/03B ni su rollback.
- Falta hostname administrativo estable por ambiente, Access interactivo,
  Certification, Pro H3 y `contract/cleanup`.
- `npm audit` mantiene vulnerabilidades transitorias ya documentadas y fuera del
  alcance H3REQ1; no se ejecuta `npm audit fix` en este ciclo.
- MFA/`aal2` permanece fuera del gate H3REQ1 y como mejora evolutiva, aunque la
  compatibilidad local existente continua cubierta por UAT.

## Estado recomendado

**NO-GO**

La evidencia local es reproducible y pasa los checks listados, pero no permite
declarar cierre H3REQ1 ni promoción. El estado recomendado sigue siendo
`NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE` hasta que el auditor
independiente certifique la evidencia remota por ambiente y la transición
`desarrollo -> certificacion -> main`.
