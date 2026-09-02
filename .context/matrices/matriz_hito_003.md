# Matriz Hito 003

`PRESTART_CLIENT_SOURCE_ATTESTED_AFTER_H2_CERTIFICATION`
`SRC-REQ-002`
`ADENDA-REQ-EST-001-001`

| Unidad | Estado | Evidencia requerida |
|---|---|---|
| `H3-CA4` | `H3_PR_DEVELOPMENT_READY_LOCAL` | Bloqueadores HIGH/CRITICAL de CI, DB, MFA real, cobertura E2E y artifacts resueltos en el ciclo de corrección local del 2026-09-02; UAT canónica 47/47 y 141/141 PASS con 0 retries y evidencia regenerada. Commit + push + PR protegido a `desarrollo` autorizados por instrucción humana separada; acciones remotas posteriores siguen como gates separados. |

Estado histórico preservado: `READY_FOR_PROMPT_CONTINUA` fue el gate de pre-arranque documental anterior.

## Criterios de cierre ampliados

| ID | Criterio | Evidencia GO requerida |
|---|---|---|
| H3-CA4.1 | Auth y RBAC | anon/auth sin membresía/inactivo bloqueados; user y admin autorizados según rol |
| H3-CA4.2 | Ownership editorial | 13 campos clasificados; `admin` edita todos; `user` solo `missing_fields` |
| H3-CA4.3 | Transporte de datos | enrichment/sync preservan `benefits`, `certification`, `objectives` y `target_audience` con semántica independiente |
| H3-CA4.4 | Cola editorial | filtros, contador, cursor, archivados excluidos y más de una página |
| H3-CA4.5 | Mutaciones | allowlist, optimistic locking, publicar/despublicar/archivar/calidad según rol |
| H3-CA4.6 | Auditoría | cada mutación editorial/membresía auditada y append-only |
| H3-CA4.7 | MFA | TOTP obligatorio en admin/user; `aal1` bloqueado para sensibles; `aal2` permitido |
| H3-CA4.8 | Membresías e invitaciones | admin invita por correo, cambia rol y activa/desactiva cualquier membresía `admin`/`user` mediante botón o checkbox, sin exponer `service_role`; conserva al menos un admin activo y evita auto-bloqueo accidental |
| H3-CA4.9 | Hostname | panel solo en `admin.studiamatch.com`; `studiamatch.com/admin/` devuelve 404 |
| H3-CA4.10 | Baseline Pro y convergencia | Pro (`xwhtiqmboljkshrtviyw`) es autoritativo; Free (`aqrldlmlszjtgpqiegaa`) y PostgreSQL 17 local convergen hacia Pro en schema, tipos, constraints, campos, migraciones, grants, RLS, vistas y RPCs. Las migraciones H3 Docker se reutilizan y rebaten sobre la forma Pro; no se modifica Pro por drift inferior ni se sincronizan datos operativos como mecanismo normal |
| H3-CA4.11 | UAT | UAT local ampliada, Free y Certification con artifacts completos |

## Estado de validación

### Estado de cierre local

`H3_PR_DEVELOPMENT_READY_LOCAL`: los bloqueadores HIGH/CRITICAL que QA, seguridad y
DB detectaron fueron resueltos en el ciclo de corrección local del 2026-09-02:
workflow/allowlist/db-gate H3 corregidos (gate `GATE_OK`), contrato
`20260902_h3_pr_contract.sql` con lector efectivo y gate de publicabilidad, seed
idempotente con categorías, harnesses `h3_pg17_harness_ok` y
`h3_pg17_harness_local_ok`, MFA con secreto/QR y `aal` real, y UAT canónica
47/47 y 141/141 PASS con 0 retries y evidencia regenerada en
`.context/evidencia/h3-expanded/`. Commit + push + PR a `desarrollo` quedaron
autorizados por instrucción humana separada.

### Porcentaje de avance histórico

| Criterio | Implementación | Validación | Estado resumido |
|---|---:|---:|---|
| H3-CA4 global | 78.7% provisional | 57.7% provisional | `H3_PR_DEVELOPMENT_READY_LOCAL`; GO local para PR; validación remota pendiente de JIT. |
| H3-CA4.1 Auth/RBAC | 90% | 85% | RBAC y negativos locales cubiertos por UAT; Auth real pendiente. |
| H3-CA4.2 Ownership | 85% | 75% | Allowlist y `missing_fields` cubiertos por UAT; falta entorno real. |
| H3-CA4.3 Transporte | 60% | 40% | Mapeos y fixture E2E diferenciado; falta entorno real. |
| H3-CA4.4 Cola | 85% | 70% | RPC/UI y paginación cubiertos por UAT; falta entorno real. |
| H3-CA4.5 Mutaciones | 90% | 75% | RPCs y locking cubiertos por UAT; falta entorno real. |
| H3-CA4.6 Auditoría | 85% | 60% | Append-only y eventos cubiertos por UAT; falta entorno real. |
| H3-CA4.7 MFA | 80% | 55% | Mock `aal2` positivo y negativos `aal1` cubiertos por UAT; falta Auth real. |
| H3-CA4.8 Membresías | 75% | 45% | Gestión, último admin e invitación mock cubiertos por UAT; falta Edge Function real. |
| H3-CA4.9 Hostname | 60% | 40% | 404 público validado sobre perímetro real; falta allowlist de despliegue y Access. |
| H3-CA4.10 Convergencia | 55% | 35% | PG17 y snapshot Pro; falta diff completo/remoto con JIT. |
| H3-CA4.11 UAT | 100% estructural | 55% contractual | Dos corridas reportadas; faltan E2E real, artifacts autocontenidos y vínculo al candidato. |
| **Promedio** | **78.7% provisional** | **57.7% provisional** | **READY_LOCAL para PR; corrección local completada, JIT remoto posterior.** |

Los porcentajes distinguen presencia de implementación de evidencia ejecutada y no
sustituyen los gates obligatorios de cierre.

### Validado localmente (ciclo de corrección 2026-09-02)

- UAT canónica 47/47 y 141/141 PASS con 0 retries y evidencia regenerada en
  `.context/evidencia/h3-expanded/`.
- Build normal/mock PASS en Docker; rutas admin exportadas.
- Suite CI-local 142 PASS, TypeScript PASS, lint 0 errores/9 warnings históricos,
  pycompile, credential scan y `git diff --check` PASS.
- Harnesses H3 PG17: `h3_pg17_harness_ok` y `h3_pg17_harness_local_ok`.
- Hostname público `studiamatch.com/admin/ → 404` validado sobre perímetro local;
  `/admin/login/` 200 en el admin origin del perímetro.

### Pendiente (gates posteriores y separados)

- Commit + push + PR protegido a `desarrollo`: autorizados por instrucción humana
  separada y en ejecución con la plantilla de PR.
- Free/Auth, Cloudflare, DNS, merge y deploy permanecen bajo JIT/promoción
  posterior separada.
