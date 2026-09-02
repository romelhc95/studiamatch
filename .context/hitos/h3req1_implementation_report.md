# H3REQ1 — Panel Administrativo Editorial

## Estado

- **Hito**: HITO-003 / H3REQ1
- **Criterio**: H3-CA4
- **Estado**: `H3_PR_DEVELOPMENT_READY_LOCAL`
- **Fecha**: 2026-09-02
- **Ciclo**: auditoría de readiness para PR (`H3_PR_DEVELOPMENT_NO_GO`, histórica)
  seguida del ciclo de corrección local que resolvió los bloqueadores
  HIGH/CRITICAL y dejó el candidato en GO para PR (`READY_LOCAL`)

La atestación sanitizada `H3-EXPANDED-PROMPT-2026-08-30` existe y autoriza
únicamente ejecución local Docker hasta GO local. No autoriza Supabase writes,
Auth remoto, Cloudflare, DNS, push, PR, merge, deploy, schedules ni
`workflow_dispatch`.

## Resumen Para Continuar Sin Conocimiento Previo

H3 es una oficina privada del sitio. Un `user` completa información que falta y un
`admin` puede además aprobar cambios y administrar personas. La auditoría de
readiness determinó que dos corridas UAT (47/47 y 141/141) solo verificaban
presencia de código o controles en parte de la matriz y dejó el estado en
`H3_PR_DEVELOPMENT_NO_GO` (histórico). El ciclo de corrección local del 2026-09-02
resolvió los bloqueadores HIGH/CRITICAL de CI, DB, MFA real, UAT/evidencia y
rollback, regeneró la UAT canónica (47/47 casos y 141/141 ejecuciones PASS con 0
retries) y dejó el candidato en `H3_PR_DEVELOPMENT_READY_LOCAL` (GO para PR).
Commit + push + PR a `desarrollo` quedaron autorizados por instrucción humana
separada.

El static export ya no es bloqueante: `npm run build` y `npm run build:mock` fueron
re-ejecutados en Docker el 2026-09-02, compilaron correctamente y produjeron las
cuatro rutas admin esperadas. El waiver
[waiver_h3_static_export.md](../waivers/waiver_h3_static_export.md) queda
superseded para este candidato; no debe usarse para omitir el required check de CI.

Orden cumplido para el cierre:

1. Separación de código de construcción y navegador terminada (`'use client'`
   retirado de `web/src/lib/supabase.ts`; módulo server-safe removido al quedar sin
   usos tras la restauración de imports).
2. PostgreSQL local preparado y servidor mock de autenticación operativo.
3. Build normal y mock re-ejecutados en Docker: PASS; `web/out/admin/`,
   `admin/login/`, `admin/edit/` y `admin/users/` existen.
4. Dev server + mock Auth + perímetro `static-server.js` sirviendo rutas públicas y
   administrativas.
5. UAT canónica regenerada el 2026-09-02: 47/47 y 141/141 PASS, 141 screenshots, 0
   retries, evidencia en `.context/evidencia/h3-expanded/`.
6. Corrección del ciclo: workflow/allowlist/db-gate H3 (`GATE_OK`), contrato
   `20260902_h3_pr_contract.sql` (lector efectivo + gate de publicabilidad), seed
   idempotente con categorías, harnesses `h3_pg17_harness_ok` y
   `h3_pg17_harness_local_ok`, MFA con secreto/QR y `aal` real; auditorías
   especializadas del ciclo previo resueltas sin HIGH/CRITICAL pendientes.
7. Documentación reconciliada a `H3_PR_DEVELOPMENT_READY_LOCAL` (GO para PR).

## Contrato de roles

- `admin`: acceso completo a la superficie editorial, edición allowlisted, publicar, despublicar, archivar, actualizar `quality_status` y gestionar usuarios/membresías.
- `user`: acceso administrativo editorial operativo y edición únicamente de campos presentes en `missing_fields`; sin publicar, despublicar, archivar, actualizar `quality_status` ni gestionar usuarios/membresías.
- `admin` puede invitar por correo, cambiar el rol y activar/desactivar cualquier membresía `admin` o `user` desde el panel mediante botón o checkbox.
- La gestión no puede dejar el sistema sin un `admin` activo ni permitir el auto-bloqueo accidental del último admin.
- No existe tercer rol válido.
- La autorización depende de `auth.uid()` y `public.admin_members`; no usa `user_metadata` ni datos de identidad enviados por navegador.
- La decisión de alcance confirmada conserva `admin` y `user` como roles vigentes dentro de `/admin/`: `user` completa faltantes y `admin` hereda esas capacidades y agrega las administrativas. La superficie de membresías queda reservada a `admin`. Los documentos canónicos fueron reconciliados con este contrato.

## Inventario de alcance

| Clasificación | Archivos y directorios |
|---|---|
| A — H3 requerido | `db/migrations/20260828_h3_admin_auth.sql`, `db/migrations/20260828_h3_admin_course_queue_view.sql`, `db/migrations/20260828_h3_admin_editorial_reader_rpc.sql`, `db/migrations/20260828_h3_admin_editorial_rpc.sql`, `db/migrations/20260828_h3_admin_queue_rpc.sql`, `db/migrations/20260829_h3_rbac_users.sql`, `db/migrations/20260830_h3_expanded_contract.sql`, `tests/sql/h3_pg17_harness_local.sql`, `web/src/app/admin/`, `web/src/components/AdminCourseQueue.tsx`, `web/src/lib/admin-auth.ts`, `tests/test_supabase_credentials_contract.py`.
| B — Compatibilidad H3 necesaria | `mock-server/server.js`, `mock-server/static-server.js`, `tests/fixtures/h3/admin_auth_local_mock.sql`, `db/seeds/h3_admin_seed_local.sql`, `web/tsconfig.json`, `web/package.json`, `web/package-lock.json`.
| C — Cambio accidental del ciclo | Ninguno identificado entre los archivos H3 anteriores.
| D — Preexistente de otro hito | `web/src/app/layout.tsx` y `.worktrees/` quedan fuera del entregable H3; no se usaron como sustituto de validación H3.
| Evidencia | Baseline histórico preservado en `.context/evidencia/h3-uat-matrix-final.json`, `.context/evidencia/h3-uat-artifact-hashes-final.json` y `.context/evidencia/h3-build-manifest.json`. Evidencia ampliada actual en `.context/evidencia/h3-expanded/h3-expanded-uat-matrix.json`, `.context/evidencia/h3-expanded/h3-expanded-uat-artifact-hashes.json` y `.context/evidencia/h3-expanded/h3_expanded_uat_status.md`.

## Validaciones ejecutadas

| Control | Resultado | Evidencia/comando |
|---|---|---|
| Containers | `PASS` | `docker ps`: `studiamatch-dev` y `studiamatch-h2-pg-test` encendidos.
| Base local | `PASS` | `studiamatch_h3` existe; PostgreSQL `17.11`; no se creó base nueva.
| Scope whitespace | `PASS` | `git diff --check` sin hallazgos; CRLF de `web/next.config.js` normalizado a LF.
| Harness SQL PG17 | `PASS` | Harness local terminó exactamente en `h3_pg17_harness_local_ok` (re-ejecutado en el ciclo de cierre).
| Credential scanner | `PASS` | Diff y archivos untracked del cierre sin credenciales detectables; único hit es referencia de patrón en `AGENTS.md`.
| Seguridad/contratos Python | `PASS CI-SCOPE` | Suite exacta del job `python-check`: 142 passed. El `pytest -q` global indiscriminado recolecta worktrees históricos/tests de integración fuera del gate y produjo 540 errores de colección; no usarlo como evidencia hasta acotar descubrimiento. |
| TypeScript | `PASS` | `npx tsc --noEmit` sin errores.
| Static build | `PASS` | `npm run build` y `npm run build:mock` compilaron en Docker; cuatro rutas admin exportadas. Waiver static export superseded para el candidato actual. |
| Lint | `PASS WITH WARNINGS` | 0 errores y 9 warnings históricos en `HomeContent.tsx`.
| Rutas físicas/hostname | `PASS` | Dev server sirve `/`, `/courses/`, `/compare/`, `/privacidad/`, `/terminos/`, `/admin/`, `/admin/login/`, `/admin/users/`, `/admin/edit/` (200); perímetro `static-server.js` en 3002 devuelve 404 para `Host: studiamatch.com` sobre `/admin/` y 200 para localhost. |
| Processes/ports | `PASS` | mock Auth en 3001 (`NODE_ENV=test`), dev server en 3000, perímetro en 3002; logs sanitizados.
| Python compile | `PASS` | `enrichment_worker.py`, `sync_vector_worker.py`, `universal_harvester.py`, `cleansing_worker.py` y `db_client.py` compilados en Docker.
| UAT ampliada | `PASS` | UAT canónica regenerada el 2026-09-02: 47/47 casos y 141/141 ejecuciones PASS, 141 screenshots, cero retries (evidencia `.context/evidencia/h3-expanded/`). |
| Security review | `PASS LOCAL (POST-CICLO)` | Resueltos en el ciclo de corrección: workflow `security-audit.yml` válido con allowlist H3 y `db-gate` con harness PG17 (gate emulado `GATE_OK`); MFA enrollment con secreto/QR y `aal` real sin asumir `aal2`; credential scan limpio. `sessionStorage` queda como waiver pendiente pre-Certification. |
| QA review | `PASS LOCAL (POST-CICLO)` | `QA_PR_READY` habilitado con UAT canónica E2E 47/47 y 141/141 PASS, rutas protegidas y hostname 404/200 validados sobre perímetro; spec borrador retirado. |
| DB review | `PASS LOCAL (POST-CICLO)` | `DB_PR_READY` habilitado: publicación condicionada a completitud, 13 `missing_fields`, lector efectivo de overrides, último admin protegido/auditado y rollback por harness en transacción reversible. |
| UAT ampliada 47 criterios | `PASS` | Catálogo 47 x 3 válido; UAT canónica E2E 47/47 y 141/141 PASS con 0 retries sobre dev server + mock Auth + perímetro real. |

## Correcciones realizadas

- Consolidada la raíz Next canónica en `web/src/app`; se retiró la duplicación `web/app` que sombreaba las rutas públicas.
- Incluido `web/app` en `tsconfig` durante la transición y después retirado junto con la raíz duplicada.
- Corregido el tipo `current_value` y la conversión de valores del editor.
- Mock local: `MOCK_DB_PASSWORD` y passwords de identidades son obligatorias por entorno, sin fallback; identidades allowlisted; tokens opacos en memoria; refresh ligado a sesión; SQL parametrizado; `set_config` con scope local; commit/rollback y liberación de conexiones.
- Fixture local actualizado para aceptar exactamente `admin` y `user`.
- Seed local sin password fija en texto; usa setting transaccional de prueba.
- Static server protegido contra path traversal.
- Harness ampliado con rechazo de campo desconocido, despublicación user y gestión de miembros no-admin.
- Contrato de scanner actualizado para el transporte Auth H3 sin exponer valores sensibles.
- Eliminado trailing whitespace de `web/package.json` y `web/package-lock.json`.
- Completada la separación de configuración server/client en el ciclo actual:
  retirado `'use client'` de `web/src/lib/supabase.ts` (módulo compartido sin
  directiva), revertidos los imports de `page.tsx` y `courses/[institution]/[slug]`
  a `@/lib/supabase`, y eliminado `web/src/lib/supabase-server.ts` por quedar sin
  usos. `tsc --noEmit` sin errores tras la separación.
- Runner UAT adaptado al dev server: espera de hidratación React tras la
  navegación a `/admin/login/` y `/admin/users/` (`waitUntil: 'networkidle'` +
  margen) para eliminar el click sobre formulario no hidratado; caso de hostname
  apuntado al perímetro real `static-server.js` (`H3_PERIMETER_URL=3002`); selector
  del caso 035 limitado al Card del formulario (strict-mode del label `Rol`).
- Restaurado `web/.env.local` con valores reales de Free (quedaba pisado por un
  `cp` de `build:mock` cuyo `git checkout` nunca corría al fallar el build) y
  corregido `build:mock` para inyectar las variables mock inline sin mutar el
  archivo de entorno.
- `git diff --check` limpiado (normalización LF de `web/next.config.js`) y
  eliminados helpers temporales del cierre (`tmp_*`).

## Rutas esperadas en el export

- Rutas públicas históricas: `/`, `/courses/`, `/compare/`, `/privacidad/`, `/terminos/`.
- Rutas administrativas requeridas: `/admin/`, `/admin/login/`, `/admin/edit/`, `/admin/users/`.
- Estado vigente: el static export de estas rutas quedó acreditado por `npm run
  build`/`build:mock` PASS en Docker; el dev server sirve las rutas administrativas
  con HTTP 200 y el perímetro `static-server.js` mantiene el bloqueo
  `studiamatch.com/admin/ → 404`.

## Campos editoriales y ownership

La visualización pública no implica que un campo sea editable por `user`. H3
separa ownership de presentación: el pipeline conserva los campos de origen,
transformación y cálculo; `admin` puede corregir los 13 campos editoriales
públicos; `user` solo puede completar un campo si aparece en
`course_editorial_state.missing_fields`.

| Campo editorial | Harvester/enrichment/sync | Admin | User | Regla de publicación |
|---|---|---|---|---|
| `name` | Sí | Sí | Si falta | Requerido |
| `price_pen` | Sí | Sí | Si falta | Opcional |
| `price_status` | Sí | Sí | Si falta | Opcional |
| `mode` | Sí | Sí | Si falta | Requerido |
| `duration` | Sí | Sí | Si falta | Requerido |
| `description_long` | Sí | Sí | Si falta | Opcional |
| `syllabus` | Sí | Sí | Si falta | Opcional |
| `target_audience` | Parcial; debe separarse de objetivos | Sí | Si falta | Opcional |
| `requirements` | Sí | Sí | Si falta | Opcional |
| `certification` | Actualmente se pierde en sync | Sí | Si falta | Opcional |
| `benefits` | Actualmente no se transporta en Golden Path | Sí | Si falta | Opcional |
| `objectives` | Actualmente reutiliza `graduate_profile` | Sí | Si falta | Opcional |
| `start_date_text` | Sí | Sí | Si falta | Opcional |

No son editables por `user`: `id`, `institution_id`, nombre/slug de institución,
`url`, `slug`, `category_id`, `category`, `start_date`, `course_type`,
`brochure_url`, `expected_monthly_salary`, `seniority_level`, `roi_months`,
`view_count`, `comparison_count`, timestamps, estados y metadatos técnicos.

El transporte pendiente se ubica en `scripts/core/sync_vector_worker.py:347-366`:
`certification` se fuerza a vacío, `benefits` no se mapea y `objectives` y
`target_audience` reciben el mismo origen. Estos hallazgos deben corregirse y
probarse antes del cierre ampliado.

## Estrategia de reutilización y rebase de BD H3

La implementación H3 existente en PostgreSQL 17 Docker no se desecha ni se
reimplementa manualmente. Sus migraciones, harness y fixtures son el candidato
funcional local ya validado. El cambio de autoridad modifica el orden de validación,
no borra el trabajo: primero se toma Pro como baseline H2 y luego se revalida/rebasa
el candidato H3 sobre una base local con forma Pro.

Pro (`xwhtiqmboljkshrtviyw`) es la fuente autoritativa para schema, tipos,
constraints, campos y últimas migraciones H2. Free (`aqrldlmlszjtgpqiegaa`) y
PostgreSQL 17 local deben converger hacia Pro; nunca se debe usar Free o local para
decidir cambios en Pro ni sincronizar datos operativos como mecanismo normal.

| Componente H3 local existente | Estado de reutilización | Estrategia |
|---|---|---|
| `20260828_h3_admin_auth.sql` | Reutilizable como candidato | Aplicar después del baseline Pro en una validación PG17 limpia; conservar funciones/tabla si las firmas son compatibles y añadir deltas solo si el baseline lo exige. |
| `20260828_h3_admin_course_queue_view.sql` | Reutilizable como candidato | Recompilar/verificar contra `courses` y `course_editorial_state` conformes a Pro; no copiar filas operativas. |
| `20260828_h3_admin_queue_rpc.sql` | Reutilizable con verificación | Mantener cursor, filtros y permisos; comprobar tipos, grants y rol `user/admin` contra Pro. |
| `20260828_h3_admin_editorial_reader_rpc.sql` | Reutilizable con delta | Conservar lector y allowlist; incorporar ownership de los 13 campos y enforcement MFA `aal2` donde corresponda. |
| `20260828_h3_admin_editorial_rpc.sql` | Reutilizable con delta | Conservar allowlist, optimistic locking y auditoría; agregar validación `aal2` y revisar columnas/constraints del baseline Pro. |
| `20260829_h3_rbac_users.sql` | Parcialmente reutilizable | Conservar listado/alta de membresía, pero completar invitación por correo, cambio de rol y activación/desactivación de cualquier `admin/user`, auditoría y protección del último admin. |
| `h3_pg17_harness_local.sql` y fixtures | Reutilizables como pruebas | No promover usuarios, passwords, UUIDs ni datos de prueba; regenerar fixture sobre el schema rebased y ampliar casos de membresía/MFA. |
| Auditoría/filas H3 locales | No migrables | Son evidencia/datos de prueba locales; no se copian a Free ni Pro. En una base limpia se validan estructura, ACL y append-only. |

La base Docker actual puede seguir funcionando para desarrollo incremental. Para
probar convergencia no basta con ella: se debe ejecutar además una validación
reproducible sobre un entorno PG17 desechable o una restauración de schema H2
alineada a Pro, aplicar las migraciones H3 existentes en orden y verificar un
segundo run `NOOP`. Si una migración histórica falla por un objeto ya existente o
por una firma incompatible, no se borra ni se reescribe silenciosamente: se crea
una migración delta idempotente y se documenta el motivo.

La convergencia de Free/local hacia Pro es primero aditiva y compatible. Las
columnas legacy de Free no se eliminan durante `expand/compatibilidad` si el
frontend o pipeline aún las necesita; su retiro pertenece a `contract`, requiere
JIT y evidencia de no degradación. Pro no recibe correcciones derivadas de drift
inferior.

## Contraste Supabase Free/Pro/local

| Objeto/medición | Free | Pro autoritativo | Local PG17 | Estado H3 |
|---|---:|---:|---:|---|
| Columnas `courses` | 47 | 39 | Baseline H3 local | Converger Free/local hacia Pro |
| `editorial_field_definitions` | 41 filas | 41 filas | H3 local | Alinear estructura y contenido |
| `course_editorial_state` | 350 filas | 350 filas | H3 local | Alinear migraciones |
| `course_editorial_audit` | 350 filas | 0 filas | H3 local | No copiar datos; validar estructura |
| `admin_members` | Ausente | Ausente | H3 local | Instalar H3 según baseline Pro + contrato |
| `admin_course_queue` | Ausente | Ausente | H3 local | Instalar H3 según baseline Pro + contrato |
| RPCs `admin_*` | Ausentes | Ausentes | H3 local | Instalar H3 según baseline Pro + contrato |
| `admin_members` governance | Pendiente | Pendiente | Parcial | Completar invite, role change, activate/deactivate cualquier `admin/user`, último admin y auditoría |
| `courses_public_effective` | 227 filas | 224 filas | H3 local | Resolver estructura; documentar datos distintos |
| `missing_fields=[]` | 131 | 129 | H3 local | Recalcular según reglas de Pro |
| `missing_fields=[duration]` | 219 | 221 | H3 local | Recalcular según reglas de Pro |

La comparación debe incluir tablas, columnas, tipos, constraints, índices,
funciones, firmas, grants, RLS, vistas, políticas y versiones de migración. Las
acciones correctivas permitidas son aditivas o de convergencia en Free/local;
Pro solo se modifica mediante JIT explícito y únicamente si el baseline autoritativo
lo requiere. La primera corrida posterior a la convergencia H3 debe ser reversible
y la segunda corrida `NOOP`.

## MFA, invitaciones y hostname

MFA TOTP es obligatorio para ambos roles. El mock local implementa enrollment,
challenge, verify, refresh y unenroll con sesión `aal2`, y las RPC H3 cuentan con
helper de enforcement `aal2`. Esto es evidencia local de contrato, no validación
de Supabase Auth remoto; las pruebas reales requieren JIT separado.

La migración local incorpora auditoría append-only de membresías y la RPC de
actualización de miembros con protección del último admin y del auto-bloqueo
accidental. El contrato de invitación por correo mediante Edge Function protegida
con `verify_jwt=true`, cambio de rol, activación/desactivación y revocación sigue
requiriendo cobertura UAT completa y posterior validación remota. El navegador no
debe recibir `service_role`.

`mock-server/static-server.js` contiene el bloqueo para `studiamatch.com/admin/`
y la última prueba observó HTTP 404; falta repetir el smoke test con un único
proceso y un build controlado. Cloudflare Access, DNS, redirect URLs de Auth,
allowed origins y deep-links requieren JIT separado.

## Estado de implementación y pendientes

### Culminado y avanzado localmente

- Atestación sanitizada `H3-EXPANDED-PROMPT-2026-08-30` y autorización local Docker.
- Flujo mock MFA TOTP con `aal2`, refresh y unenroll; negativos `aal1` cubiertos por UAT (H3-UAT-029/030).
- Enforcement `aal2` en el contrato RPC local verificado por UAT.
- Ownership contractual de 13 campos y separación `admin`/`user` en código y
  harness; casos positivos/negativos de ownership y `missing_fields` en UAT.
- Auditoría append-only editorial/membresías y protección del último admin;
  eventos y append-only cubiertos por UAT (H3-CA4.6).
- Hostname público `/admin/` bloqueado con HTTP 404 en el perímetro
  `static-server.js`; smoke limpio en el ciclo de cierre (H3-UAT-040/041/042).
- Snapshot/clasificación documental Pro/Free/local y harness PG17 local con
  resultado `h3_pg17_harness_local_ok`.
- Separación construcción/navegador terminada; build normal/mock PASS y waiver
  static export superseded.
- UAT canónica regenerada el 2026-09-02: 47/47 casos y 141/141 ejecuciones PASS,
  141 screenshots, 0 retries, evidencia autocontenida y vinculada al candidato en
  `.context/evidencia/h3-expanded/`.
- Suite CI-local: 142 tests PASS, TypeScript OK, lint 0 errores, pycompile OK,
  credential scan sin hallazgos, `git diff --check` limpio y harnesses H3
  `h3_pg17_harness_ok` / `h3_pg17_harness_local_ok`.
- Correcciones del ciclo (resuelven los hallazgos HIGH/CRITICAL de la auditoría):
  workflow/allowlist/db-gate H3 (`GATE_OK`), contrato `20260902_h3_pr_contract.sql`
  (lector efectivo + gate de publicabilidad), seed idempotente con categorías y MFA
  con secreto/QR y `aal` real. Auditorías especializadas del ciclo previo quedan
  resueltas localmente sin HIGH/CRITICAL pendientes.

### Avance estimado por criterio

| Criterio | Implementación | Validación verificable | Pendiente crítico |
|---|---|---:|---:|---|
| H3-CA4.1 Auth/RBAC | 90% | 85% | Auth real y negativos remotos. |
| H3-CA4.2 Ownership | 85% | 75% | Cobertura de valores efectivos en entorno real. |
| H3-CA4.3 Transporte | 60% | 40% | Prueba E2E diferenciando cuatro campos en entorno real. |
| H3-CA4.4 Cola | 85% | 70% | Segunda página y cursor en entorno real. |
| H3-CA4.5 Mutaciones | 90% | 75% | Locking de estados en entorno real. |
| H3-CA4.6 Auditoría | 85% | 60% | Auditoría de todas las mutaciones en entorno real. |
| H3-CA4.7 MFA/aal2 | 80% | 55% | Supabase Auth real y negativos remotos. |
| H3-CA4.8 Membresías | 75% | 45% | Invitación por correo (Edge Function) y Auth real. |
| H3-CA4.9 Hostname | 60% | 40% | Allowlist positiva, smoke en despliegue y Cloudflare Access. |
| H3-CA4.10 Convergencia | 55% | 35% | Diff Pro/Free/local y validación remota JIT. |
| H3-CA4.11 UAT/artifacts | 100% estructural | 55% contractual | UAT local canónica 47/47 y 141/141 PASS; falta UAT real en Free/Certification. |
| **Promedio simple** | **78.7% provisional** | **57.7% provisional** | **`H3_PR_DEVELOPMENT_READY_LOCAL`; GO local para PR; validación remota pendiente de JIT.** |

### Siguiente gate

1. Corregido en el ciclo local: YAML y gates de `security-audit.yml` con allowlist
   H3 y harnesses H3 en PG17 limpio (gate emulado `GATE_OK`).
2. Corregido en el ciclo local: contratos DB con publicación condicionada a
   completitud, 13 `missing_fields`, valores efectivos, último admin/auditoría ante
   escritura directa y rollback en transacción reversible.
3. Corregido en el ciclo local: MFA con enrollment de secreto/QR y `aal` real desde
   JWT/API sin fallback manipulable.
4. UAT canónica E2E regenerada (47/47 y 141/141 PASS, 0 retries) sobre dev server +
   mock Auth + perímetro, cubriendo transporte, paginación, mutaciones, auditoría,
   membresías y NOOP.
5. Artifacts autocontenidos y vinculados al candidato en `.context/evidencia/
   h3-expanded/`; spec borrador retirado; `.worktrees/` y artifacts stale excluidos.
6. Suite CI-local, build, lint, typecheck, pycompile, credential scan, harnesses H3
   y auditorías QA/seguridad/DB repetidos sin HIGH/CRITICAL.
7. Documentación reconciliada a `H3_PR_DEVELOPMENT_READY_LOCAL` y plantilla de PR
   preparada con resultados reales. Commit + push + PR a `desarrollo` autorizados
   por instrucción humana separada.

## Resultado y limitaciones vigentes

1. `H3_PR_DEVELOPMENT_READY_LOCAL` (GO para PR): el ciclo de corrección resolvió los
   hallazgos HIGH/CRITICAL de la auditoría previa (`H3_PR_DEVELOPMENT_NO_GO`,
   histórica) y la UAT canónica quedó en 47/47 y 141/141 PASS con 0 retries.
2. Build normal/mock PASS y rutas admin exportadas; waiver static export superseded.
3. `SECURITY_PR_READY`, `QA_PR_READY` y `DB_PR_READY` quedaron habilitados en el
   ciclo local; pendientes únicamente validaciones remotas (Free/Auth, Cloudflare,
   certificación) con sus aprobaciones separadas.
4. El workflow requerido quedó válido: allowlist H3 y `db-gate` con harnesses H3.
5. DB quedó con publicación condicionada a completitud, cálculo de los 13
   `missing_fields`, lectura efectiva de overrides y protección del último admin con
   rollback reversible reproducible.
6. MFA quedó con secreto/QR y `aal` real; `sessionStorage` conserva un riesgo
   adicional como waiver pendiente pre-Certification.
7. No se ejecutaron acciones remotas. Commit + push + PR a `desarrollo` fueron
   autorizados por instrucción humana separada y quedan en ejecución; Supabase,
   Cloudflare, certificación, merge y deploy permanecen como gates posteriores.

## Transición transparente

- **Expand**: implementación local de RBAC, ownership, transporte contractual,
  MFA mock `aal2`, auditoría de membresías, cola, editor, hostname y servidores
  mock seguros.
- **Compatibilidad**: se preservan las cinco rutas públicas y el comportamiento
  legacy necesario; el build es configurable entre endpoint real y mock local sin
  exponer secretos.
- **Deploy**: pendiente y fuera de autorización; requiere JIT para Supabase/Auth,
  Cloudflare y posteriormente promoción protegida.
- **Contract**: UAT local canónica 47/47 y 141/141 PASS y validaciones completas;
  requiere validación Free/Pro con Pro como baseline, estabilización en
  Certification y resolución de waivers (static export, `sessionStorage`) antes de
  retirar soporte legacy.
- **Rollback**: revertir los archivos A/B del cambio H3 ampliado, retirar
  hostname/Access y conservar datos locales; las pruebas SQL mutantes operan en
  transacción reversible o fixture aislado (harness local `h3_pg17_harness_local_ok`).
- **No degradación pública**: las cinco rutas públicas responden 200, el perímetro
  devuelve HTTP 404 para `/admin/` con el hostname público y el panel solo se
  expone en el hostname administrativo.

## Veredicto

`H3_PR_DEVELOPMENT_READY_LOCAL` — GO local para PR ready-for-review a
`desarrollo`. El ciclo de corrección local del 2026-09-02 resolvió los bloqueadores
HIGH/CRITICAL que QA, seguridad y DB habían identificado (workflow corrupto/
incompleto, harness H3 ausente en CI, enrollment/`aal2` real, publicación sin
completitud, `missing_fields` parcial, lector sin valores efectivos, último admin
evadible y rollback no reproducible): `security-audit.yml` corregido con allowlist
H3 y `db-gate` PG17, contrato `20260902_h3_pr_contract.sql` con lector efectivo y
gate de publicabilidad, seed idempotente con categorías, harnesses
`h3_pg17_harness_ok` / `h3_pg17_harness_local_ok`, MFA con secreto/QR y `aal` real,
y UAT canónica 47/47 y 141/141 PASS con 0 retries y evidencia regenerada en
`.context/evidencia/h3-expanded/`. El build normal/mock fue revalidado PASS en
Docker y el waiver static export queda superseded. No se ejecutaron push, PR,
merge, deploy, Supabase remoto, Cloudflare ni DNS. Commit + push + PR a
`desarrollo` fueron autorizados por instrucción humana separada; los gates remotos
y de promoción posteriores requieren sus aprobaciones separadas.
