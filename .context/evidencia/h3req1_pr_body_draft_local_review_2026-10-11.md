# Borrador del cuerpo PR H3REQ1 — solo revisión local — 2026-10-11

Este texto sigue la plantilla versionada `.github/pull_request_template.md`.
Es un borrador con resultados reales, no una solicitud para abrir PR. G09 sigue
parcial y el inventario de staging no está cerrado; por eso no está listo para
publicación. No se creó commit/PR ni se ejecutó ninguna operación remota.

## Resumen

Implementación local H3REQ1 para edición editorial/Admin, auditoría y
disponibilidad, membresías/invitaciones, BFF con cookies HttpOnly, gateway RPC
firmado, cuotas y controles locales. El trabajo corresponde a los criterios de
aceptación sanitizados de Sprint 1. El comportamiento se probó solo contra
fixtures locales sintéticos.

- Rama candidata: `feat/h3req1-sync-20261002`.
- HEAD baseline: `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- HEAD no identifica el WIP: al preparar este corte hay 60 rutas tracked
  modificadas, 795 entradas untracked visibles en `git status` y cero staged.
  `git ls-files --others --exclude-standard` enumera 14.272 archivos, muchos
  anidados bajo evidencia/build. El PR no debe usar automáticamente ese
  conjunto completo. Fingerprint de `git status --porcelain=v1 --untracked-files=all`:
  `bf1fde7a760cb3ebdc080a7ea50429022e38f32cc66a957cbf53514a0ff21999`;
  fingerprint de `git diff --binary` tracked al corte:
  `d0d82af573c37810082f47e8ed9660c76446a7fe49ca406ffa43cd87eec6e459`.
  El manifiesto de contenido de las 84 rutas propuestas para el alcance PR
  (`60` tracked modificadas + `24` untracked seleccionadas) es
  `.context/evidencia/h3req1_pr_scope_manifest_2026-10-11.json`, SHA-256
  `0e220208a2de2f02e082422fa02dd80964692366d15a08680f83bb5a597e6a0d`.
  No incluye este borrador, el propio manifiesto, secretos operativos ni los
  demás artefactos WIP.
- Inputs del build normal/mock R9/R10: 57 archivos allowlisted, SHA-256
  `3894b6c5807677736c0c963b6ff8caed24dbda701489e5960dd2f9fc007293ab`.
- Identidad del delta Admin R41: `web/src/app/admin/users/page.tsx` SHA-256
  `befd0c9bee0ee762ceb22723e092dbf544d99172ef05f487e67d6c9230208a35`;
  `tests/h3_local_uat.mjs` SHA-256
  `60e617325cc5ff8633c6ad5741e553af617207aff829b30eed1efe3db4ed594d`.
- Veredicto: G08 completo para checks locales aplicables; G09 parcial; G10
  remoto pendiente. No se declara GO local, `GO_LOCAL_PR` ni
  `GO_DEVELOPMENT_REAL`.

## Evidencia De Este PR

| Resultado | Comando/caso e inputs | Ambiente y grado | Evidencia y límites |
|---|---|---|---|
| G08 checks | Pytest 331 passed/4 skipped; contrato de credenciales 43/43; credential scanner y H2 writer scan PASS; ESLint exit 0 (9 warnings conocidos); Next typegen/TypeScript PASS; Python AST 176; npm audit full/prod con 0 vulnerabilidades; actionlint, ShellCheck, workflow guard y scope guard reutilizados con hashes coincidentes. | Docker local, imagen fijada `studiamatch-h3req1:20261009-v3`; pruebas sintéticas. Los 4 skips y checks live no se cuentan PASS. | `.context/evidencia/h3req1_g08_final_checks_reconciliation_2026-10-11.md`. |
| Build normal/mock | R9 normal y R10 mock: cada uno exit 0, 17/17 páginas, 126 artefactos; la verificación de hashes pasó. R9 preserva el fallo de dispatcher mock exit 254 por cwd incorrecto; R10 lo corrigió en el runner sin cambiar producto. | Build Docker local; manifest de 57 inputs; proxy de egress limitado para fuentes sintéticas/locales. | `.context/evidencia/h3req1_g08_candidate_final_2026-10-11_r2/normal-mock-builds-r9-r10-reconciliation.log`. |
| Integración C03 | R51: PASS, 128/128 inputs coinciden, Pages/workerd + Edge + PG17 + PostgREST locales. | Runtime/DB sintéticos; no equivale a servicios remotos. | `.context/evidencia/h3req1_c03_integrated_run_2026-10-10_r51.txt` y manifiesto R51. |
| UAT catálogo | R28/R29/R30 concilian 63 casos × 3 viewports = 189 ejecuciones. Un PASS vigente por ejecución tras reemplazos focales; los fallos iniciales permanecen preservados. | Chromium 1228 headless; runtimes locales y datos sintéticos. | `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/r28_r29_catalog_reconciliation_2026-10-11.md`. |
| Pipeline | R18: 24/24 PASS, 1 warning PyPDF2; recuperación/idempotencia y discovery con transports sintéticos. | `studiamatch-dev`/PG17 local según handoff; sin writers cloud. | `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/local-pipeline-walk-r2-handoff-2026-10-11.md`. |
| Onboarding | R8: 10/10 PASS, 0 retries, 10 capturas con hashes y un vídeo. INV-008 corrigió un ciclo real de rutas para `password_pending`. | Chromium 1228 headless, Pages/workerd, Auth/BFF mock y PG17 sintético. | `.context/evidencia/h3req1_g09_onboarding_r8_inv008_topology_2026-10-11.md`; no se usó cuenta real ni correo real. |
| Delta de teclado/membresías | R41 H3-UAT-040: 3/3 viewports, 51 assertions PASS, 0 retries; role/state persistidos, bloqueo del último admin y restauración del miembro sintético. | Playwright Chromium 1228 headless; runtime Pages/workerd en el contenedor UAT y PG17 R12 sintético. | `.context/evidencia/h3req1_g09_uat_2026-10-11_r41_membership_keyboard.md`; capturas por viewport abajo. No se capturó vídeo R41. |
| Windows/local preview | `http://localhost:3335/admin/login/` y `/admin/users/` sirven el runtime R41 sobre PG17 sintético R12. | Sidecar Docker publicado solo en `127.0.0.1:3335`; postflight WSL: login/Admin 200, Host `127.0.0.1` rechazado 421 y curso pipeline 404 en el bundle R41. El runtime R12 distinto de `:3333` sirve ese curso 200 sobre la misma base sintética. | `.context/evidencia/h3req1_g09_uat_2026-10-11_r41_membership_keyboard.md` y `.context/evidencia/h3req1_g09_windows_loopback_r41_postflight_2026-10-11.md`. Identidad sintética; no se imprimió password. Windows GUI no se usó. No es Cloudflare preview ni deploy. LOCAL-03/16 siguen parciales. |

Capturas R41:

- [Desktop](.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/H3-UAT-040-desktop.png)
- [Tablet](.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/H3-UAT-040-tablet.png)
- [Móvil](.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/H3-UAT-040-mobile.png)

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Editor Admin y origen/override | Mantiene procedencia pipeline/manual override, control de versión y restauración de estado. | Admin, lectores y publicación. | R30/H3-UAT-049 y pruebas focales; G09 sigue abierto para todos los bordes de LOCAL-13/14/16. |
| Disponibilidad y auditoría | Evidencia HTTPS, actor/razón, rango inclusivo hasta 90 días y fallos cerrados. | RPC Admin, publicación y lectura pública. | R30/H3-UAT-049, G01 PG17 y R51. Faltan validaciones legacy/despublicación y toda la cobertura integrada listada en la matriz. |
| BFF y sesión | Cookies HttpOnly, MFA/RBAC, gateway firmado y cuota conservados. | Admin UI, BFF/Pages Functions y RPC allowlisted. | G03 BFF 90 checks; contrato de credenciales 43/43 y R51. No acredita bindings remotos. |
| Membresías | Región accesible y desplazable por teclado; operaciones de rol/estado y último admin probadas con fixture sintético. | Panel Admin y membresías. | R41 H3-UAT-040; quedan carreras/recovery en LOCAL-10. |
| CI independiente | Workflow local `protected-workflow-integrity.yml` preparado. | Protección propuesta para el candidato. | No se publicó ni se hizo required; G10 sigue pendiente hasta revisión/integración/enforcement reales. |

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | Parcial | G01–G07 PASS; G08 PASS; G09 con LOCAL-01..03, 05..10, 12..20 y 22..23 parciales/faltantes según matriz. |
| Escalabilidad | Parcial | Recursos de runtimes locales acotados; no se ejecutó carga ni se demuestra un SLA/escala de producción. |
| Seguridad | Parcial | Scanner, writer scan, auditorías y controles locales PASS/reusados con inputs coincidentes; no se usaron secretos reales. Negativos restantes de replay/nonce/cuotas y revisión final siguen pendientes. |
| Mantenimiento | Parcial | Lint, typecheck, scripts y builds PASS. Persisten 9 warnings conocidos y evidencia de harnesses fallidos que se conserva. |
| Calidad | Parcial | G08 completo; G09 y revisión independiente final del delta actual incompletos. 4 skips no se cuentan como aprobación. |
| Rendimiento | Parcial | Navegación local y recursos acotados medidos; falta dataset ampliado y medición repetible comparada con baseline. |

## Transicion Transparente

| Fase | Alcance/resultado real | Evidencia / autorización |
|---|---|---|
| expand | Cambios aditivos ensayados en PG17 desechable; gates y compatibilidad local ejecutados. | G01/G02/G07 local; no se escribió en Supabase remoto. |
| compatibilidad | BFF HttpOnly, roles, MFA, gateway y fallback legacy se conservaron en pruebas locales donde están cubiertos. | G03/R51/UAT. Los límites legacy pendientes están en LOCAL-09/13/15/19. |
| deploy | No ejecutado. | Requiere instrucción humana separada; Production/Certification excluidos. |
| contract | No ejecutado en remoto ni declarado. | Depende de promoción/estabilización y autorización futura. |
| Rollback/recuperación | Recuperación local C03 y scripts de rollback están en el candidato; no hay ejecución de rollback remoto. | R51 y `db/rollback/h3req1_safe_*.sql`; prueba remota pendiente. |
| No degradación funcional | R28/R29/R30 189 ejecuciones conciliadas; R41 renueva la UI de membresías; G09 aún tiene gaps. | Evidencia local sintética; no es aceptación remota. |

## Evidencia Para Cliente

Se usa únicamente la atestación sanitizada versionada de Sprint 1; el documento
privado no se incorpora. Resultados locales sobre fixtures:

| Criterio | Resultado local | Pendiente/límite |
|---|---|---|
| Admin completa/corrige cursos y conserva origen | PASS en el recorrido R30 para el curso sintético. | Campo por campo, cancelación y conflicto/concurrencia siguen pendientes según LOCAL-13/14. |
| Auditoría actor/fecha/antes/después | PASS en el recorrido integrado sintético y contratos PG17/R51. | Atomicidad y protección de edición por user requieren renovar LOCAL-13 contra inputs finales. |
| Disponibilidad válida, máximo 90 días y compatibilidad legacy | Evidencia válida y frontera inclusiva pasan; pruebas negativas se ejercitan en harness/editor. | Rechazos legacy, exceso, vencimiento y despublicación integrados deben quedar reconciliados por LOCAL-15. |
| Encabezado muestra correo y conserva roles | PASS para admin/user en catálogo local; R41 protege acciones de membresía/último admin. | MFA/sesión y flujos remotos no se infieren; LOCAL-09/10 mantiene pendientes. |

No se afirma aceptación contractual remota. No hay waivers nuevos.

## Validaciones

| Validación | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS: candidato y delta R41; pruebas sintéticas PASS. | Docker local, sin mostrar valores de secretos. | `.context/evidencia/h3req1_g08_final_checks_reconciliation_2026-10-11.md`; owner: responsable H3. |
| Python tests | 331 passed, 4 skipped, 1 warning. | Docker; suite de proyecto. | Los skips no son PASS; warning PyPDF2 conservado. |
| Python compile | AST de 176 archivos `.py` PASS; no equivale a ejecutar esos módulos. | Docker local. | Log Python AST de G08. |
| PostgreSQL DB Change Gate | PASS para harnesses G01/G02 y C03 integrado local R51. | PG17.11 desechable/sintético. | No es una escritura remota ni reemplaza aceptación final de G09. |
| ESLint | PASS, exit 0, 9 warnings conocidos; delta R41 revalidado. | Docker local. | Sin errores. |
| TypeScript | typegen y `tsc --noEmit` PASS con memoria acotada; delta R41 revalidado. | Docker local. | Log G08 y delta R41. |
| Static build | Normal R9 y mock R10 PASS, 17/17 páginas y 126 artefactos cada uno. | Docker local. | R9 dispatcher mock falló por cwd (exit 254); R10 corrigió harness y pasó. |
| actionlint / ShellCheck | PASS/reusado con hashes coincidentes; delta R41 no altera workflows ni scripts. | Docker local. | Logs G03/G08. |
| UAT/runtime/integración | R28/R29/R30: 189/189 seleccionadas PASS; R41: 3/3 viewports PASS; R51: 128/128 inputs PASS. | Browser/runtime/DB sintéticos en Docker; Chromium headless. | G09 continúa parcial y hay fallos históricos preservados; no se reclaman retries. |
| `security-audit` / CI independiente efectivo | Workflow local preparado; enforcement NO-EJECUTADO. | No se usó GitHub remoto. | G10 pendiente de revisión, integración y required-check efectivo. |
| CodeQL si aplica | NO-EJECUTADO en este ciclo. | No se ejecutó CI/remoto. | El responsable debe determinar su aplicabilidad al PR. |
| Cloudflare Pages / smoke preview | NO-EJECUTADO. | No hubo deploy ni preview remoto. | No se cambió Production/Certification. |
| Browser snapshot si aplica | R41 screenshots 3/3 verificadas; catálogo 189 con capturas históricas conciliadas. | Chromium 1228 headless. | R41 no produjo vídeo. |
| security-auditor | Revisión local del delta R41 sin findings; revisión final independiente del candidato completo pendiente. | Revisión estática local, no un control remoto. | Este borrador no reclama aprobación final. |
| Documentación / trazabilidad / fuente cliente | Estado, matriz y evidencia R41 actualizados; atestación sanitizada enlazada en la trazabilidad. | Local. | Pendiente reconciliación final LOCAL-01..23 y scope guard del conjunto de paths. |

## Seguridad Y Datos

- [x] Scanner y revisión del delta R41 no encontraron secretos/PII añadidos; no
  se imprimieron valores operativos.
- [x] API keys/identidad/RLS/roles/MFA/último admin se probaron localmente en los
  alcances declarados; el último admin se preservó.
- [ ] HIGH/CRITICAL ausentes en revisión final independiente del candidato
  completo: pendiente, no inferido de la revisión focal R41.
- [x] No hubo DB/secretos/Production/restore/schedules/writers remotos.

## Alcance Y Limites

**Inventario propuesto para una futura selección de PR, no staging:**

- Incluir como candidatos de código los cambios tracked H3 en `.context/`
  (estado/trazabilidad/tarea/atestación), `.env.example`, `.github/`,
  `AGENTS.md`, `Dockerfile`, `README.md`, `db/migrations/`, `db/rollback/`,
  `db/seeds/`, `mock-server/`, `scripts/`, `supabase/`, `tests/`, `workers/`
  y `web/`, sujetos a scope guard y review de cada archivo.
- Incluir los artefactos de build que son dependencias reales, en particular
  `web/vendor/braces-3.0.4-h3.1.tgz`, porque `package.json` y lockfile apuntan a
  ese tarball local.
- La evidencia propuesta y seleccionada se enumera después de las rutas de
  cambio. Se excluyen salidas raw/redundantes, excepto las capturas y vídeo
  explícitamente listados; no se agregan todos los untracked.
- Paths tracked modificados observados, 60:

```text
.context/00_INDICE.md
.context/backlog_tareas/req_est_001_sprint_1/_index.md
.context/backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md
.context/backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md
.context/estado_del_proyecto.md
.context/hitos/h3req1_implementation_report.md
.context/hitos/hito_003.md
.context/matrices/matriz_hito_003.md
.context/operaciones/estandar_prompts_retroalimentados.md
.context/operaciones/matriz_adopcion_db.md
.context/seguimiento/seguimiento_sprint_1_h2_h5.md
.context/sistema_db_supabase.md
.env.example
.github/pull_request_template.md
.github/workflows/security-audit.yml
AGENTS.md
Dockerfile
README.md
db/migrations/20260927_h3_admin_queue_facets_filter.sql
db/seeds/h3_admin_seed_local.sql
mock-server/server.js
scripts/core/universal_harvester.py
scripts/security/h2_web_mock_smoke.sh
scripts/security/scan_credentials.sh
supabase/functions/admin-invite/index.ts
supabase/templates/password-recovery.html
tests/h3_invitation_uat.mjs
tests/h3_local_uat.mjs
tests/sql/h2_pro_pg17_harness.sql
tests/sql/h3_invitation_edge_runtime_harness.sql
tests/sql/h3_invitation_onboarding_harness.sql
tests/sql/h3_pg17_harness.sql
tests/test_admin_invite_edge_contract.py
tests/test_fase09_9_certification_canary.py
tests/test_h3_admin_queue_ux_contract.py
tests/test_h3_invitation_callback_contract.py
tests/test_h3_mock_invitation_contract.py
tests/test_h3_password_recovery_contract.py
tests/test_mfa_compatibility_contract.py
tests/test_password_policy_contract.py
tests/test_security_flow.py
tests/test_supabase_credentials_contract.py
web/eslint.config.mjs
web/functions/_middleware.ts
web/next.config.js
web/package-lock.json
web/package.json
web/src/app/HomeContent.tsx
web/src/app/admin/auth/callback/page.tsx
web/src/app/admin/edit/page.tsx
web/src/app/admin/layout.tsx
web/src/app/admin/login/page.tsx
web/src/app/admin/page.tsx
web/src/app/admin/reset-password/page.tsx
web/src/app/admin/users/page.tsx
web/src/app/compare/CompareContent.tsx
web/src/app/page.tsx
web/src/lib/admin-auth.ts
web/src/lib/supabase.ts
web/tsconfig.json
```

- Código nuevo untracked propuesto, 24 paths:

```text
.github/workflows/protected-workflow-integrity.yml
db/migrations/20260927_h3_publication_visibility_contract.sql
db/migrations/20260928_h3_invitation_accept_email_regex_fix.sql
db/migrations/20261001_h3_course_editorial_audit_availability.sql
db/migrations/20261001_h3_invitation_reservation_compensation.sql
db/migrations/20261002_h3_admin_quota_expand.sql
db/migrations/20261002_h3_admin_quotas.sql
db/migrations/20261004_h3_admin_queue_first_null_guard.sql
db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql
db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql
db/migrations/20261010_h3_admin_members_service_select.sql
db/rollback/h3req1_safe_resume.sql
db/rollback/h3req1_safe_suspend.sql
scripts/security/protected_path_scope_guard.sh
scripts/security/protected_workflow_review.py
supabase/templates/invite.html
web/functions/_lib/admin-bff.ts
web/functions/_lib/admin-quota.ts
web/src/components/admin/AdminSessionGuard.tsx
web/src/lib/supabase-transport.ts
web/vendor/README.md
web/vendor/braces-3.0.4-h3.1.tgz
workers/admin-quota/index.ts
workers/admin-quota/wrangler.jsonc
```

- Evidencia canónica propuesta, 32 rutas:

```text
.context/evidencia/h3req1_g08_final_checks_reconciliation_2026-10-11.md
.context/evidencia/h3req1_g08_candidate_final_2026-10-11_r2/normal-mock-builds-r9-r10-reconciliation.log
.context/evidencia/h3req1_c03_integrated_r51_preparation_2026-10-10.md
.context/evidencia/h3req1_c03_integrated_run_2026-10-10_r51.txt
tests/h3req1-c03-integrated-r51.sha256
.context/evidencia/h3req1_g09_local_acceptance_matrix_reconciliation_2026-10-11.md
.context/evidencia/h3req1_g09_uat_2026-10-10_r4/r28_r29_catalog_reconciliation_2026-10-11.md
.context/evidencia/h3req1_g09_uat_2026-10-10_r4/local-pipeline-walk-r2-handoff-2026-10-11.md
.context/evidencia/h3req1_g09_onboarding_r8_inv008_topology_2026-10-11.md
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/onboarding-summary-r8.json
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/onboarding-screenshots-r8.sha256
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/onboarding-videos-r8.sha256
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-001.png
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-002.png
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-003.png
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-004.png
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-005.png
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-007.png
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-008.png
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-009.png
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-012.png
.context/evidencia/h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r8/screenshots/INV-013.png
[Original local excluido del paquete público; ver el registro R19 de sanitización visual](h3req1_visual_evidence_redaction_2026-10-18_r19.md#inventario-local-de-originales).
.context/evidencia/h3req1_g09_uat_2026-10-11_r41_membership_keyboard.md
.context/evidencia/h3req1_g09_windows_loopback_r41_postflight_2026-10-11.md
.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/h3-expanded-uat-artifact-hashes.json
.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41-command.log
.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41-runner-exit.txt
.context/evidencia/h3req1_g09_uat_2026-10-10_r4/site-out-r41-verify.log
.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/H3-UAT-040-desktop.png
.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/H3-UAT-040-tablet.png
.context/evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/H3-UAT-040-mobile.png
```

El scope manifest que fija el contenido SHA-256 de las 84 rutas de cambio y
estas 32 evidencias es `.context/evidencia/h3req1_pr_scope_manifest_2026-10-11.json`;
el manifiesto es el artefacto 117 y su digest se publica abajo. El borrador PR
no forma parte del conjunto ni de su propio hash.
- Excluir caches/snapshots/builds (`.next`, `out`, `node_modules`), datasets y
  harnesses temporales generados bajo `tests/h3req1-c03-bootstrap/`, paquetes
  JIT consumidos, intentos Rxx redundantes/raw, capturas de administración
  `.openchamber/`, `.context/.obsidian/`, scripts locales
  `r41_windows_loopback_*.mjs`, `.env*` operativo, credenciales,
  todos los recursos Docker locales y datos/servicios ajenos.
- El árbol actual aún tiene 795 entradas untracked de estado y 14.272 archivos
  enumerados con `--untracked-files=all`; el set definitivo de paths no se ha
  aprobado ni staged. Este borrador no convierte esos paths en inclusión.

## Checklist Tecnico

- [x] Checks locales G08 ejecutados en Docker para el candidato/manifiesto
  indicado; resultados y límites están vinculados arriba.
- [x] Ficha de impacto Admin/membresías y matriz LOCAL-01..23 actualizadas.
- [x] Modelo/atestación sanitizada, seis pilares y transición/rollback
  documentados con fases remotas explícitamente pendientes.
- [ ] Review final de las 84 rutas de cambio propuestas (60 tracked y 24
  untracked), scope guard sobre el set de inclusión y aprobación humana del
  cuerpo PR: pendiente.
- [ ] GO local PR y control CI requerido efectivo: pendiente; no se afirma.

**Estado del borrador:** G08 completo; G09 parcial; tablero G01–G10 80% (8/10),
cierre local G01–G09 8/9 = 88,89%. Próximo trabajo: completar LOCAL faltantes,
renovar por impacto sobre el candidato congelado y revisión independiente.
Integración, PR, merge, deploy Development y D01–D14 requieren instrucciones
posteriores separadas. Certification y Production siguen fuera de alcance.
