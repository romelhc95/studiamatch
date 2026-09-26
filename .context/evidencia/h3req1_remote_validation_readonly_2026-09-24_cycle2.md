# H3REQ1 — validación remota read-only, ciclo 2 — 2026-09-24

Estado del ciclo: `NO-GO_H3REQ1_REMOTE_DRIFT_PRO_AND_RUNTIME_UNVALIDATED`

Clasificación de esta evidencia: `PASS` únicamente para la captura read-only
documentada; no implica PASS contractual H3REQ1. La convergencia H3-001 queda
`FAIL` por drift Pro y H3-002/H3-003/H3-004 quedan `BLOCKED`. Esta precisión
evita interpretar `PASS_WITH_DRIFT` como resultado operativo.

## Alcance y autorización

- Modo: read-only.
- No se ejecutaron DDL, migraciones, writes Auth/DB, Edge deploy, cleanup,
  rollback, Cloudflare, push, PR, merge ni promoción.
- Ambientes inspeccionados: Free `aqrldlmlszjtgpqiegaa` y Pro
  `xwhtiqmboljkshrtviyw`.
- La evidencia se obtuvo directamente de los ambientes evaluados y no reutiliza
  pruebas locales como evidencia remota.

## Identificación obligatoria de la captura

| Campo | Valor |
|---|---|
| Ambiente | Supabase Free/Development y Supabase Pro/Production, separados en cada consulta |
| Project ref | `aqrldlmlszjtgpqiegaa` / `xwhtiqmboljkshrtviyw` |
| Branch/commit/artefacto | Candidato H3REQ1 documentado en el estado vivo; no hubo deploy ni artefacto remoto modificado |
| Timestamp | 2026-09-24; conservar timestamp UTC exacto del registro de herramienta al regenerar |
| Prueba ejecutada | Inventario read-only de migrations, schema, RLS/policies/grants, RPCs, Edge y advisories |
| Resultado | `PASS` para captura read-only; `FAIL` H3-001 contractual; `BLOCKED` H3-002/H3-003/H3-004 |
| Evidencia | Esta nota y sus tablas sanitizadas, sin secretos, JWT, passwords, PII ni URLs con tokens |

La fila de branch/commit/artefacto no sustituye la identificación exacta del
candidato. Antes de cualquier nueva promoción debe completarse con el commit o
artefacto exacto evaluado; si falta, la nueva evidencia será `BLOCKED`.

## Revalidación read-only — ciclo 3, 2026-09-24

Timestamp UTC exacto de captura ciclo 3: `2026-09-24T20:09:11.140Z`–
`2026-09-24T20:09:13.053Z`.

| Campo | Free / Development | Pro / Production |
|---|---|---|
| Project ref | `aqrldlmlszjtgpqiegaa` | `xwhtiqmboljkshrtviyw` |
| Prueba | `list_migrations`, `list_tables` verbose, `list_edge_functions`, advisors security/performance | Mismas pruebas |
| Resultado H3-001 | `PASS` para inventario: 15 migraciones H3 relacionadas; tablas `admin_members`, `admin_membership_audit`, `admin_invitations` presentes | `FAIL`: 0 migraciones H3 relacionadas; no existen tablas H3 de membresías/invitaciones/auditoría |
| Edge `admin-invite` | `PASS` informativo: `ACTIVE`, v3, `verify_jwt=true` | `BLOCKED`: no existe `admin-invite` |
| Advisories | `FAIL` de cierre de hardening: WARN `authenticated_security_definer_function_executable` (20), WARN leaked-password protection (1), INFO RLS/policies (5) | `FAIL`/drift baseline: WARN search_path mutable (7), WARN SECURITY DEFINER ejecutable, duplicado de índice |
| Timestamp | Captura directa del ciclo 3; regenerar con timestamp UTC exacto antes de promoción | Captura directa del ciclo 3; regenerar con timestamp UTC exacto antes de promoción |

La revalidación confirma que el drift Pro no se cerró. No se ejecutaron DDL,
writes, Auth, Edge deploy, Pages, cleanup, rollback ni promoción.

La reconciliación local del ciclo 4 recuperó los dos archivos de hardening
registrados en Free y validó sus hashes en PG17. Esto cambia el estado del
hallazgo `LOCAL-VAL-005` a `PASS` local, pero no cambia el resultado remoto:
Pro continúa sin esas migraciones y no existe autorización JIT para aplicar el
delta en ningún ambiente.

## Pruebas ejecutadas

- `list_migrations()` en Free y Pro.
- Consulta SQL read-only de versión PostgreSQL, migraciones H3, tablas H3 y RPCs
  de invitación/onboarding.
- Consulta SQL read-only de RLS, cantidad de policies y grants de RPCs H3.
- `list_edge_functions()` y advisories de seguridad por ambiente.

## Resultado baseline y migraciones

| Componente | Free | Pro | Resultado |
|---|---|---|---|
| PostgreSQL | 17.6 | 17.6 | `PASS` informativo |
| Migraciones H3 previas | Presentes | Ausentes | `FAIL` de convergencia |
| Migraciones 20260918–20260921 | Presentes | Ausentes | `FAIL` Pro drift |
| Hardening 20260924 | Presentes: `20260924_h3_onboarding_rbac_hardening` y `..._fix` | Ausentes | `FAIL` Pro drift |
| `admin_invitations` | Presente | Ausente | `PASS` Free / `FAIL` Pro |
| `admin_members` | Presente | Ausente | `PASS` Free / `FAIL` Pro |
| `admin_membership_audit` | Presente | Ausente | `PASS` Free / `FAIL` Pro |
| RPCs invitation/onboarding | 6 presentes | Ausentes | `PASS` Free metadata / `FAIL` Pro |

Free registra actualmente las migraciones H3 hasta:

```text
20260918_h3_invitation_flow_persistence
20260919_h3_invitation_auth_token_delta
20260920_h3_invitation_edge_runtime
20260921_h3_invitation_onboarding_rpc
20260924_h3_onboarding_rbac_hardening
20260924_h3_onboarding_rbac_hardening_fix
```

La observación anterior de ausencia Free quedó superseded por esta captura más
reciente. No se considera evidencia de aplicación correcta en Pro ni de UAT.

## H3-001 — DB contract

**Resultado: `FAIL` contractual / `PASS` parcial en Free.**

Hallazgo: Free contiene las tablas H3 de invitaciones, RLS habilitado en las tres
tablas, tres policies y las seis RPCs de invitación/onboarding con grants
observables. Pro no contiene las tablas, policies, RPCs ni migraciones H3.

Causa: las migraciones H3 se aplicaron o registraron en Free después de la
auditoría anterior, pero no existe convergencia contra el baseline Pro
autoritativo.

Corrección requerida: comparar el conjunto completo contra el baseline Pro y
obtener aprobación JIT DDL Pro antes de aplicar cualquier migración. No se
autoriza corregir Pro en este ciclo.

Prueba ejecutada: inventario remoto de migraciones, tablas, RPCs, RLS, policies y
grants en ambos proyectos.

Resultado: `FAIL`; el gate bloquea Certification.

## H3-002 — invitation/onboarding

**Resultado: `BLOCKED`.**

Hallazgo: Free ahora tiene metadata DB suficiente para intentar el flujo; Pro no
la tiene. No se ejecutó Auth real, correo, PKCE, aceptación, password setup,
replay, revocación, resend/supersede ni reconciliación Auth/DB.

Causa: falta convergencia Pro y falta aprobación separada para Auth/test data y
correo controlado.

Corrección requerida: validar primero el contrato Free completo, alinear Pro con
JIT DDL separado, verificar Edge por ambiente y luego ejecutar UAT controlada.

Prueba ejecutada: inspección read-only de tablas, RPCs y grants; no smoke de
mutación.

Resultado: `BLOCKED`.

## H3-003 — RBAC/auditoría

**Resultado: `BLOCKED` contractual.**

Hallazgo: Free expone RLS en las tablas H3 y metadata de RPCs; Pro carece del
contrato. La metadata no prueba permisos efectivos de admin/user/inactivo/anónimo,
último admin, locking, mutaciones ni auditoría append-only en runtime.

Causa: drift de ambientes y ausencia de UAT remota autenticada.

Corrección requerida: converger schema en Pro, ejecutar matriz negativa/positiva
por actor y verificar filas de auditoría en el ambiente evaluado sin exponer PII
ni secretos.

Prueba ejecutada: inventario read-only de RLS, policies y grants.

Resultado: `BLOCKED`.

## H3-004 — expand → compatibilidad → deploy → contract

**Resultado: `BLOCKED`.**

Hallazgo: no existe en esta captura evidencia de deploy funcional Pages/Edge,
contract/cleanup ni rollback remoto. La presencia de migraciones Free no prueba
compatibilidad ni despliegue.

Causa: deploy y rollback requieren autorizaciones JIT separadas y el deployment
remoto anterior no servía las rutas H3 nuevas.

Corrección requerida: validar artefacto y hostname del ambiente, ejecutar smoke
funcional, demostrar compatibilidad legacy, preparar rollback y solo después
cerrar contract/cleanup con aprobación explícita.

Prueba ejecutada: ninguna operación de deploy; solo inspección remota de DB y
Edge disponible.

Resultado: `BLOCKED`.

## Decisión

El ciclo no alcanza GO. El drift Pro es un bloqueador HIGH. Se mantiene
`NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE` y no se solicita Certification.

## Siguiente corrección autorizable

1. Ejecutar validación local Docker de las migraciones/harness actuales y registrar
   cualquier fallo.
2. Solicitar JIT DDL Pro separado para aplicar el conjunto aprobado.
3. Repetir este inventario read-only Free/Pro y cerrar el drift antes de Auth UAT.
4. Solicitar JIT independiente para Auth/test data, Edge deploy, cleanup y rollback.
