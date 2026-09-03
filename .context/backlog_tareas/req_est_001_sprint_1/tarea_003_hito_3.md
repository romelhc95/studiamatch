# TASK-H3-001

`PRESTART_CLIENT_SOURCE_ATTESTED_AFTER_H2_CERTIFICATION`
`SRC-REQ-002`
`ADENDA-REQ-EST-001-001` - HITO-003

| Campo | Valor |
|---|---|
| Estado | `H3_PR_DEVELOPMENT_READY_LOCAL` |
| Work package | `SUPERSEDED` |
| Criterio | `H3-CA4` |
| Bloqueo | Resuelto en el ciclo de corrección local del 2026-09-02: CI H3 completo (allowlist + `db-gate` con harness PG17), invariantes DB garantizadas, MFA con secreto/QR y `aal` real, UAT canónica E2E 47/47 y 141/141 PASS, rollback reversible y evidencia vinculada al candidato. Build normal/mock PASS; waiver static export superseded. Commit + push + PR autorizados por instrucción humana separada. |

Estado histórico preservado: `READY_FOR_PROMPT_CONTINUA` correspondió al pre-arranque documental anterior; la tarea vigente está en `H3_PR_DEVELOPMENT_READY_LOCAL`.

## Explicación Simple De La Tarea

Esta tarea construye una oficina privada para revisar cursos y administrar usuarios.
El cierre local está acreditado: dos corridas consecutivas de UAT ampliada
terminaron con 47/47 casos lógicos y 141/141 ejecuciones PASS en desktop, tablet y
mobile, con 141 screenshots y cero retries, contra el dev server Next.js (3000) +
mock Auth (3001) + PostgreSQL 17 local. El perímetro `static-server.js` (3002)
valida que `studiamatch.com/admin/` responde HTTP 404 y que el hostname local sirve
las rutas administrativas.

La tarea local queda completa. La publicación remota y el acceso a servicios
externos requieren autorizaciones humanas separadas (commit + push + PR a
`desarrollo`, después JIT Supabase Free/Auth, Cloudflare/DNS, merge y deploy).

## Estado del alcance ampliado

La atestación sanitizada `H3-EXPANDED-PROMPT-2026-08-30` autorizó el trabajo local
Docker hasta GO local; el GO fue declarado el 2026-09-02 con evidencia canónica de
dos corridas PASS. El baseline local anterior queda preservado como evidencia
histórica.

### Culminado o avanzado localmente

1. Snapshot read-only y clasificación documental Pro/Free/local preservados.
2. Migraciones H3 existentes y delta `20260830_h3_expanded_contract.sql` aplicados
   y validados localmente; el delta correctivo `20260903_h3_rbac_contract_fix.sql`
   corrige los hallazgos remotos A6/A13 y el harness CI PG17 termina en
   `h3_pg17_harness_ok` con regresión de ambos casos; el harness local termina en
   `h3_pg17_harness_local_ok` (re-ejecutado en el ciclo de cierre).
3. Ownership contractual de los 13 campos y permisos diferenciados admin/user
   implementados en el contrato local.
4. MFA TOTP mock con enrollment, challenge, verify, sesión `aal2`, refresh y
   unenroll validado.
5. Enforcement `aal2`, auditoría append-only de membresías, protección del último
   admin y prevención de auto-bloqueo implementados localmente.
6. Bloqueo `studiamatch.com/admin/` → HTTP 404 implementado y validado en el
   perímetro `static-server.js` durante el ciclo de cierre.
7. TypeScript, suite CI-local de pytest (142 passed) y lint (0 errores, 9
   warnings preexistentes) PASS en la revalidación del candidato; `tsc --noEmit`
   sin errores. `pytest -q` global queda excluido porque recoge worktrees históricos
   y pruebas de integración fuera del alcance.
8. Evidencia canónica regenerada en `.context/evidencia/h3-expanded/` (UAT 47/47 y
   141/141 PASS, 141 screenshots, 0 retries); corridas estructurales previas
   (`h3-expanded-run-pass1`, `h3-expanded-run-pass2`) preservadas como evidencia
   histórica fuera del repo.

### Resultado de auditoría de readiness

`H3_PR_DEVELOPMENT_READY_LOCAL` (GO local para PR): el ciclo de corrección local y
la revalidación documental del 2026-09-03 resolvieron los bloqueadores locales que
QA/seguridad/DB habían encontrado (estado previo `H3_PR_DEVELOPMENT_NO_GO`, histórico).
UAT canónica histórica 47/47 y 141/141 PASS con 0 retries; el candidato actual
además valida en PG17 la regresión A6/A13 del delta `20260903`. JIT-A/JIT-B tienen
evidencia remota parcial documentada; sus pendientes no se presentan como PASS.

### Siguiente gate

Resuelto en el ciclo local: workflow/allowlist/db-gate H3 (`GATE_OK`), invariantes
DB, regresión PG17 A6/A13 del delta `20260903`, MFA local, cobertura E2E, rollback
reversible y artifacts vinculados al candidato. Commit + push + PR a `desarrollo`
autorizados por instrucción humana separada; JIT-A/JIT-B remotos permanecen
parciales y documentados con sus gates posteriores.

### Pendiente vigente (gates posteriores y separados)

1. Revalidación remota A6/A13 en Free después de aplicar el delta `20260903` con JIT DDL.
2. Configuración Auth pendiente y UAT real de login/MFA/redirects.
3. Dependencia build: Edge Function de invitación y mecanismo estable de 404 público.
4. Matriz JIT-B restante E2/E5/E6/E7, UAT en Certification, merge y deploy.
5. `security-audit`, CodeQL, Pages preview y revisión humana remotos al abrir el PR.

### Bloqueos y reglas de detención

- UAT local: `PASS`; UAT canónica 47/47 y 141/141 PASS con 0 retries (corrida
  histórica documentada); el candidato actual revalidó el contrato A6/A13 en PG17.
- Waiver static export: superseded por build normal/mock PASS. `sessionStorage`
  conserva riesgo pre-Certification sin waiver formal.
- La evidencia remota JIT-A conserva A6/A13 FAIL sobre el payload hasta `20260902`;
  `20260903` está versionada y probada localmente, pero requiere aplicación remota
  y revalidación antes del merge/promoción.
- JIT-B tiene perímetro E1/E3/E4/E8 validado; E2/E5/E6/E7 siguen pendientes por
  Access interactivo, configuración Auth y dependencia build.
- Detenerse y consultar si aparece drift, secreto, decisión funcional, acción
  destructiva o cualquier necesidad de Supabase write, Auth remoto, Cloudflare,
  DNS, push, PR, merge, deploy, schedule o `workflow_dispatch`.
