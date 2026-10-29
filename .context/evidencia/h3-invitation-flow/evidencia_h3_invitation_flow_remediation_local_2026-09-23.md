# Evidencia H3 Invitation Flow - Remediacion Local 2026-09-23

**Fecha de ejecucion:** 2026-09-23 (hora local del workspace)
**Hito:** H3 / `HITO-003` / `TASK-H3-001`
**Ambiente:** Docker local, `studiamatch-dev` + PostgreSQL 17 `studiamatch-h3-postgres`
**Estado de esta evidencia:** `PASS_LOCAL_WITH_REMOTE_GATE_OPEN`
**Remote:** no se ejecutaron Auth remoto, writes Supabase, migraciones remotas, deploy, workflow dispatch, commit, push, PR, merge ni promocion protegida.

## Hallazgos remediados

1. El runner `tests/h3_local_uat.mjs` inspeccionaba `studiamatch_admin_session`,
   `accessToken` y `refreshToken`, pero el cliente oficial PKCE persiste la sesion
   en la clave `*-auth-token` con `access_token` y `refresh_token`. Esto producia
   falsos fallos de assurance, refresh y RPC en UAT.
2. El reset del mock limpiaba identidades temporales y sesiones, pero no
   reconstituia las identidades RBAC estables usadas por la UAT. Tras una corrida
   con mutaciones, el usuario fijo podia quedar sin membresia activa.
3. El entorno de Docker tenia Chromium instalado en
   `/ms-playwright/chromium-1228/chrome-linux64/chrome`, mientras Playwright
   intentaba resolver el headless shell de otra revision. El runner ahora acepta
   `H3_CHROMIUM_PATH` y usa el binario instalado por defecto.

## Flujo ejecutado

| Paso | Resultado esperado | Resultado obtenido | Evidencia |
|---|---|---|---|
| Reset de fixture | Estado limpio y RBAC estable | PASS: reset HTTP 204; admin/user activos y reconstruibles | `mock-server/server.js`, runner UAT |
| Login admin | Sesion administrativa y dashboard | PASS en desktop, tablet y mobile | `h3-expanded-uat-matrix.json`, H3-UAT-002 |
| Login user | Dashboard limitado sin gestion de usuarios | PASS en desktop, tablet y mobile | H3-UAT-003/H3-UAT-004 |
| Invitacion user | Respuesta 200 sin token privado | PASS | `STUDIAMATCH-H3-UAT-MOCK-02-REPORT.md`, INV-001/008 |
| Invitacion admin | Rol admin persistido y acceso a usuarios | PASS | INV-002 |
| Redirect | Host externo no aparece en respuesta | PASS | INV-009 |
| Password setup | Password solo a Auth, RPC sin password | PASS | INV-001; evidencia de requests sanitizada en runner |
| Expiracion | Enlace vencido rechazado | PASS | INV-003 |
| Revocacion | Enlace revocado rechazado | PASS | INV-004 |
| Resend/supersede | Enlace anterior rechazado, nuevo enlace aceptable | PASS | INV-005 |
| Replay | Enlace usado no vuelve a aceptarse | PASS | INV-012 |
| Persistencia DB | Estados y auditoria del onboarding | PASS local PG17 | `h3_invitation_onboarding_harness_ok` |

## Resultados reproducibles

### UAT canónica H3

```text
result=PASS
logicalCases=47
logicalCasesPassed=47
viewportExecutions=141
viewportExecutionsPassed=141
screenshots=141
retries=0
```

Artefactos:

- `.context/evidencia/h3-expanded/h3-expanded-uat-matrix.json`
- `.context/evidencia/h3-expanded/h3-expanded-uat-executions.json`
- `.context/evidencia/h3-expanded/h3-expanded-uat-manifest.json`
- `.context/evidencia/h3-expanded/h3-expanded-uat-artifact-hashes.json`
- 141 screenshots por caso y viewport en `.context/evidencia/h3-expanded/`

### UAT de invitacion

```text
result=PASS
INV-008 PASS
INV-001 PASS
INV-002 PASS
INV-009 PASS
INV-007 PASS
INV-003 PASS
INV-004 PASS
INV-005 PASS
INV-012 PASS
```

### Harness PG17

```text
h3_invitation_onboarding_harness_ok
h3_pg17_harness_ok
```

La ejecucion se hizo sobre la base `h3_gate`, creada localmente para el harness,
con `ON_ERROR_STOP=1`. No se copiaron usuarios, passwords, UUIDs de fixture ni
datos operativos hacia Supabase Free o Pro.

## Logs sanitizados necesarios

```text
[local] mock reset: HTTP 204
[local] invitation UAT: result PASS, cases 9/9
[local] canonical H3 UAT: result PASS, cases 47/47, executions 141/141, screenshots 141, retries 0
[local] PG17: h3_invitation_onboarding_harness_ok
[local] PG17: h3_pg17_harness_ok
[local] credential scan: credential scan passed
[local] git diff --check: PASS
```

No se incluyen tokens, passwords, API keys, cookies, Authorization headers ni
PII en esta evidencia.

## Expand -> compatibilidad -> deploy -> contract

- **Expand:** se corrigio solo el soporte del runner para el contrato de sesion
  PKCE y el reset del mock para identidades RBAC estables; no se reescribieron
  migraciones historicas.
- **Compatibilidad:** rutas admin legacy, cliente Auth oficial, callback PKCE,
  RPCs de onboarding, MFA existente y rutas publicas se conservaron.
- **Deploy:** no ejecutado; requiere aprobacion separada.
- **Contract:** PASS local para UAT y harnesses; pendiente de evidencia remota por
  ambiente, Certification, Pro y contract/cleanup.
- **Rollback:** retirar los cambios locales de `mock-server/server.js` y
  `tests/h3_local_uat.mjs`; no hay filas remotas que revertir porque no hubo
  migraciones ni writes remotos.

## Riesgos pendientes

- Auth/PKCE, correo real, reconciliacion Auth/DB y TTL remoto no estan acreditados.
- Las migraciones H3 de invitacion/onboarding no se aplicaron a Free o Pro en este
  ciclo.
- No existe evidencia remota de UAT sobre deployments correctos de Development y
  Certification.
- Hostnames administrativos por ambiente, Cloudflare Access interactivo,
  contract/cleanup y promocion protegida siguen pendientes.
- MFA/`aal2` permanece fuera del gate H3REQ1 y se conserva como mejora evolutiva.
