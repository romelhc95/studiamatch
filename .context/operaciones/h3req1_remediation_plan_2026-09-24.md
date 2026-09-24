# H3REQ1 Remediation Plan — 2026-09-24

Estado vivo: `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`

Este plan continúa la auditoría del 2026-09-23. No amplía el alcance H3REQ1 y no
autoriza DDL, writes Supabase, Auth real, despliegues, push, PR, merge ni
promoción.

## Tareas y gates

| ID | Tarea | Gate de validación | Estado | Bloqueador |
|---|---|---|---|---|
| R1 | Capturar baseline remoto Free/Pro en modo lectura | Snapshot sanitizado de migrations, tablas, RPCs y Edge Functions | `PASS` | Ninguno |
| R2 | Aplicar 03A/03B en Free | Migraciones `20260918`–`20260921`, smoke Auth/DB y auditoría | `PARTIAL/PASS DB` | UAT Auth/correo y smoke funcional pendientes |
| R3 | Alinear Pro con baseline H3REQ1 aprobado | Migrations aplicadas, metadata y RPCs verificadas | `BLOCKED` | JIT DDL Pro separado |
| R4 | Alinear/deployar `admin-invite` por ambiente | Hash/version/`verify_jwt=true`, logs sin secretos y smoke controlado | `PASS DEVELOPMENT EDGE` | UAT funcional y otros ambientes bloqueados |
| R5 | Ejecutar flujo real admin → invitación → aceptación → password → onboarding → privado | UAT remota por ambiente, correo/Auth real y reconciliación Auth/DB | `BLOCKED` | R2/R3/R4 y datos de prueba autorizados |
| R6 | Completar `expand → compatibilidad → deploy → contract` | Evidencia por ambiente, contract/cleanup y rollback reproducible | `BLOCKED` | Deploy/promotion y autorización humana |

## Criterio de parada

No se continúa con R2–R6 sin aprobación humana JIT explícita para cada clase de
acción. Una aprobación para Free no autoriza Pro, Edge deploy, Auth real,
Cloudflare, promoción ni cleanup.

## Evidencia de auditoría

- `.context/evidencia/h3_remote_validation_readonly_2026-09-24.md`
- `.context/evidencia/h3req1_remediation_baseline_2026-09-23.md`
- `.context/evidencia/h3req1_remediation_report_2026-09-23.md`

## Matriz de remediación requerida

La siguiente matriz agrega causa, componentes, validación, riesgo y evidencia
esperada. Todas las acciones remotas permanecen bloqueadas hasta recibir la
aprobación JIT correspondiente.

| Hallazgo | Causa demostrada | Archivo/componente afectado | Acción requerida | Validación necesaria | Riesgo | Evidencia esperada |
|---|---|---|---|---|---|---|
| H3-001 | Free no registra las cuatro migraciones y Pro no registra H3; la evidencia existente solo acredita ausencia | `db/migrations/20260918`–`20260921`; Supabase Free/Pro; `.context/evidencia/` | Preservar SQL local, obtener aprobación JIT por ambiente y aplicar únicamente las migraciones aprobadas, en orden y de forma idempotente | `list_migrations`, metadata de tablas/RPC/constraints/RLS y hashes de migración por ambiente | Drift entre ambientes, fallo parcial de contrato o incompatibilidad con baseline Pro | Snapshot before/after, filas de `schema_migrations`, objetos H3 y resultado de smoke read-only |
| H3-002 | `admin_invitations` y RPCs de invitación/onboarding están ausentes en Free y Pro | `supabase/functions/admin-invite/index.ts`; RPCs `admin_invitation_*`, `admin_accept_current_invitation`, `admin_complete_password_setup`, `admin_get_onboarding_status` | Tras contrato DB validado, ejecutar UAT real controlada admin → invitación → aceptación → password → onboarding; no exponer tokens ni passwords | Auth/PKCE, correo de prueba autorizado, identidad caller, TTL, aceptación, replay, reconciliación Auth/DB y RBAC | Crear datos Auth o invitaciones no reconciliables; envío real accidental | Logs sanitizados, request IDs, resultado Auth/DB reconciliado, evidencia de no exposición de secretos |
| H3-003 | Free solo tiene RBAC/editorial H3 parcial y Pro no tiene baseline H3 verificable | Supabase Free/Pro; baseline Pro de schema; `db/migrations/20260918`–`20260921` | Comparar contra baseline Pro autoritativo; obtener JIT Pro separado; aplicar solo deltas idempotentes aprobados y verificar convergencia | Inventario de migraciones, columnas, constraints, funciones, grants y RLS en ambos ambientes | Alterar producción fuera de baseline o promover SQL incompatible | Matriz Free/Pro antes-después, aprobación JIT referenciada y consulta de contrato por ambiente |
| H3-004 | No existe evidencia de deploy, contract/cleanup ni rollback remoto; local expand/compatibilidad no sustituye deploy | Edge `admin-invite`; frontend admin; Supabase/Auth; Certification/Pro | Documentar y ejecutar por separado `expand → compatibilidad → deploy → contract`; preparar rollback reversible antes de cualquier deploy; cleanup solo con aprobación | Hash/version Edge, `verify_jwt=true`, smoke por ambiente, UAT Certification, contract/cleanup y rollback reproducible | Degradación del login legacy, pérdida de compatibilidad o rollback incompleto | Evidencia de cada fase, manifest/hash, logs sanitizados, decisión contract, rollback drill y estado post-cleanup |

## Orden de ejecución condicionado

1. **R1 — Baseline read-only:** ya completado; conservar el baseline y no
   inferir aplicación desde la presencia de SQL local.
2. **R2 — Free DB:** migraciones aplicadas y metadata validada bajo JIT Free.
   Auth UAT/correo sigue pendiente y no se considera completado por metadata.
3. **R3 — Pro DB:** detenido hasta JIT DDL Pro y revisión contra baseline Pro.
   Una autorización Free no cubre Pro.
4. **R4 — Edge:** Development aplicado bajo JIT Edge deploy; `verify_jwt=true`
   y hash/version quedaron registrados. Certification/Pro siguen bloqueados.
5. **R5 — UAT real:** detenido hasta R2–R4; requiere datos de prueba y correo
   expresamente autorizados, con limpieza y reconciliación documentadas.
6. **R6 — Contract/rollback:** detenido hasta tener evidencia deploy, smoke,
   contract, cleanup autorizado y rollback reproducible sin acciones
   destructivas.

## Gate de continuación

El siguiente ciclo solo puede iniciar implementación local con el prompt humano
`continua`. Las operaciones remotas requieren además aprobaciones JIT concretas:

- Free DDL/migraciones.
- Pro DDL/migraciones.
- Auth writes y datos de invitación/correo de prueba.
- Edge deploy `admin-invite` por ambiente.
- Cleanup, rollback remoto y cualquier promoción protegida.

Hasta entonces el estado es `NO-GO`; no se declara `READY FOR VALIDATION` ni GO.
- `.context/hitos/h3req1_closure_review_final_2026-09-23.md`
