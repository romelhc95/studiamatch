# H3REQ1 UAT Matrix - Evidencia Local 2026-09-23

**Ambiente:** Docker local con mock Auth/PostgreSQL 17
**Fecha:** 2026-09-23
**Regla:** cada estado se refiere exclusivamente a la evidencia indicada; no
implica cierre remoto ni promocion.

| Criterio | Estado | Evidencia asociada | Resultado observado |
|---|---|---|---|
| Login admin | PASS | H3-UAT-002 x3 viewports; `h3-expanded-uat-matrix.json` | Admin entra al dashboard y conserva la sesion PKCE/MFA del mock. |
| RBAC | PASS local | H3-UAT-003/004/031/032; PG17 harness | `admin` y `user` llegan a superficies distintas; `user` no accede a usuarios ni mutaciones privilegiadas. |
| Invitacion | PASS local | INV-001/002/003/004/005/009/012; `evidencia_h3_invitation_flow_remediation_local_2026-09-23.md` | Creacion, admin/user, expiracion, revocacion, resend, redirect allowlist y replay cubiertos. |
| Aceptacion | PASS local | INV-001/005/012; callback contract tests | Callback hash/PKCE, aceptacion una vez y rechazo de enlace usado observados. |
| Onboarding | PASS local | INV-001/007; `h3_invitation_onboarding_harness_ok` | `password_pending` requiere password; Auth recibe password y el RPC no recibe password; cuenta llega a `ready`. |
| Usuarios | PASS local | H3-UAT-034/035/036/037/038/039; PG17 harness | Listado, rol, activacion/desactivacion, duplicados, email invalido y rol invalido cubiertos. |
| Ownership | PASS local | H3-UAT-007/008/009/010; PG17 harness | `user` edita solo campos faltantes; campos existentes quedan read-only. |
| Rutas privadas | PASS local | H3-UAT-001/004; `web/functions/_middleware.ts` | Sin sesion se redirige a login; user no expone gestion de membresias. |
| Acceso publico | PASS local | H3-UAT-040/041/042; `mock-server/static-server.js` | Host admin local sirve login, `studiamatch.com/admin/` devuelve 404 en perímetro local y rutas publicas siguen 200. |

## Estado remoto separado

| Criterio | Estado | Falta verificable |
|---|---|---|
| Login admin remoto | PARTIAL | UAT Auth real en Development y Certification. |
| RBAC remoto | PARTIAL | Revalidacion web autenticada sobre ambiente correcto y A6/A13 remotos posteriores al delta. |
| Invitacion remota | PARTIAL | Edge 03A, correo real, persistencia 03B y reconciliacion Auth/DB. |
| Aceptacion/onboarding remoto | FAIL | No se acredita aplicacion remota de `20260921_h3_invitation_onboarding_rpc.sql`. |
| Hostnames/perimetro remoto | PARTIAL | Hostnames separados por ambiente y smoke interactivo Access. |
| Promotion/contract | FAIL | Certification, Pro H3, deploy y contract/cleanup no autorizados ni ejecutados. |

La evidencia local no se presenta como evidencia remota. El criterio de cierre
permanece abierto hasta que un auditor independiente revise y certifique los
gates remotos.
