# Matriz Hito 003

`PRESTART_CLIENT_SOURCE_ATTESTED_AFTER_H2_CERTIFICATION`
`SRC-REQ-002`
`ADENDA-REQ-EST-001-001`

| Unidad | Estado | Evidencia requerida |
|---|---|---|
| `H3-CA4` | `H3_DEVELOPMENT_REMOTE_PARTIAL` | Gates locales revalidados el 2026-09-03, incluyendo delta `20260903_h3_rbac_contract_fix.sql` y regresión PG17 A6/A13; UAT canónica 47/47 y 141/141 PASS con 0 retries y evidencia regenerada. JIT-A Development sobre Free aplicó `20260903` y validó A6/A13; JIT-B valida membresía y perímetro, pero la UAT administrativa debe ejecutarse sobre el deployment correcto de cada ambiente. El PR fue mergeado a `desarrollo` en `e3d21c1`; `admin.studiamatch.com` queda reservado a producción. |

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

### Estado de validación Development remoto

`H3_DEVELOPMENT_REMOTE_PARTIAL`: los bloqueadores locales que QA, seguridad y DB
detectaron fueron resueltos y revalidados en Docker. El delta
`20260903_h3_rbac_contract_fix.sql` fue aplicado en Free y A6/A13 fueron validados
remotamente; los fixtures temporales quedaron eliminados. JIT-B valida membresía
Cloudflare y perímetro E1/E3/E4/E8. La UAT web E2/E5/E6/E7 queda pendiente hasta
usar el deployment correcto de `desarrollo`; `admin.studiamatch.com` queda reservado
a producción. El PR #495 fue mergeado a `desarrollo` en `e3d21c1`.

### Porcentaje de avance histórico

| Criterio | Implementación | Validación | Estado resumido |
|---|---:|---:|---|
| H3-CA4 global | 78.7% provisional | 57.7% provisional | `H3_DEVELOPMENT_REMOTE_PARTIAL`; Free/A6-A13 y parte del perímetro Cloudflare validados; UAT administrativa por ambiente y Certification pendientes. |
| H3-CA4.1 Auth/RBAC | 90% | 85% | RBAC y negativos locales/Free cubiertos parcialmente; UAT web por ambiente pendiente. |
| H3-CA4.2 Ownership | 85% | 75% | Allowlist y `missing_fields` cubiertos por UAT; falta entorno real. |
| H3-CA4.3 Transporte | 60% | 40% | Mapeos y fixture E2E diferenciado; falta entorno real. |
| H3-CA4.4 Cola | 85% | 70% | RPC/UI y paginación cubiertos por UAT; falta entorno real. |
| H3-CA4.5 Mutaciones | 90% | 75% | RPCs y locking cubiertos por UAT; falta entorno real. |
| H3-CA4.6 Auditoría | 85% | 60% | Append-only y eventos cubiertos por UAT; falta entorno real. |
| H3-CA4.7 MFA | 80% | 65% | Supabase Free Auth/MFA temporal validado con `aal2`, negativos y limpieza; UAT web Access por ambiente pendiente. |
| H3-CA4.8 Membresías | 75% | 45% | Gestión, último admin e invitación mock cubiertos; falta Edge Function real y alta desde flujo productivo. |
| H3-CA4.9 Hostname | 60% | 40% | Perímetro Access/membresía y 404 público parcial; falta separar deployment admin por ambiente y validar SHA. |
| H3-CA4.10 Convergencia | 55% | 35% | PG17 y Free validados; falta diff completo/remoto con Pro como baseline y configuración por ambiente. |
| H3-CA4.11 UAT | 100% estructural | 60% contractual | UAT local histórica y Free parcial reportadas; faltan UAT web por ambiente, Certification y cierre contractual remoto. |
| **Promedio** | **78.7% provisional** | **60.2% provisional** | **`H3_DEVELOPMENT_REMOTE_PARTIAL`; Free/A6-A13 y perímetro parcial validados; UAT administrativa por ambiente y Certification pendientes.** |

Los porcentajes distinguen presencia de implementación de evidencia ejecutada y no
sustituyen los gates obligatorios de cierre.

### Validado localmente (revalidación del candidato 2026-09-03)

- UAT canónica 47/47 y 141/141 PASS con 0 retries y evidencia regenerada en
  `.context/evidencia/h3-expanded/`.
- Build normal/mock PASS en Docker; rutas admin exportadas.
- Suite CI-local 142 PASS, TypeScript PASS, lint 0 errores/9 warnings históricos,
  pycompile, credential scan y `git diff --check` PASS.
- Harness H3 PG17 termina en `h3_pg17_harness_ok` e incluye la regresión A6/A13
  del delta `20260903`; el harness local conserva `h3_pg17_harness_local_ok`.
- Hostname público `studiamatch.com/admin/ → 404` validado; `www` público responde 200 en `/` y 404 en `/admin/`.
- Cloudflare confirma `romelhc95@gmail.com` como miembro `accepted`; E1/E3/E4/E8 PASS.
- Preview `88f02c53.studiamatch-aty.pages.dev` corresponde a `desarrollo`/`e3d21c1`; E2/E5/E6/E7 del panel requieren completar UAT sobre ese deployment, no sobre `admin.studiamatch.com`.

### Siguientes correcciones

- Separar Pages/Access por ambiente: producción `main`/`admin.studiamatch.com`, desarrollo preview `88f02c53.studiamatch-aty.pages.dev` o alias real documentado, certificación preview propio.
- Definir hostname administrativo estable para cada ambiente y registrar SHA, deployment ID y Supabase project ref.
- Implementar Edge Function de invitación y mecanismo 404 público estable antes de promover H3 a `main`.
- Repetir UAT E2–E8 por ambiente; no promover a `certificacion` hasta que el deployment de `desarrollo` y el hostname administrativo estén verificados.
