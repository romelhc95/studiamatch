# HITO-003 - Admin Editorial

`PRESTART_CLIENT_SOURCE_ATTESTED_AFTER_H2_CERTIFICATION`
`SRC-REQ-002`
`ADENDA-REQ-EST-001-001`

| Campo | Valor |
|---|---|
| Estado | `H3_PR_DEVELOPMENT_READY_LOCAL` |
| Work package | `NONE_SUPERSEDED` |
| Criterio | `H3-CA4` |
| Gate | READY_LOCAL: GO para PR. Los bloqueadores HIGH/CRITICAL que la auditoría de readiness detectó (CI H3, invariantes DB, MFA real, cobertura E2E, rollback y trazabilidad) fueron resueltos en el ciclo de corrección local del 2026-09-02; UAT canónica 47/47 y 141/141 PASS con 0 retries. Commit + push + PR autorizados por instrucción humana separada. |

## Lectura Rápida Para Una Persona No Técnica

- **Objetivo:** crear una oficina privada dentro del sitio para corregir cursos y
  administrar quién puede entrar.
- **Estado:** lista localmente. Se aprobó el programa de pruebas completo dos veces
  seguidas: las 47 situaciones y las 141 comprobaciones (tres tamaños de pantalla)
  pasaron, con capturas de pantalla y sin reintentos.
- **Qué ocurrió antes:** el programa de pruebas anterior falló porque la oficina
  privada no aparecía en la copia construida que estaba siendo servida.
- **Qué se corrigió:** se ajustó el programa de pruebas para esperar a que la
  página terminara de cargar antes de tocarla, se validó el bloqueo público
  (`studiamatch.com/admin/` responde 404) sobre un servidor de perímetro y se
  corrigió un selector de prueba. Con eso, dos corridas consecutivas pasaron 47/47
  y 141/141.
- **Cómo se demuestra el cierre:** dos corridas consecutivas 141/141 aprobadas,
  con 141 capturas cada una, guardadas en la carpeta de evidencia, y evidencia
  canónica regenerada el 2026-09-02 tras el ciclo de corrección local.
- **Qué está autorizado ahora:** commit + push + PR protegido a `desarrollo` por
  instrucción humana separada. Publicar, tocar Supabase real, configurar accesos
  reales o desplegar siguen bloqueados hasta sus aprobaciones separadas.

## Alcance

`admin.studiamatch.com` como hostname canónico exclusivo del panel, Cloudflare Access
como perímetro, Supabase Auth con MFA TOTP obligatorio para `admin` y `user`,
membresía `admin_members`, invitación por correo mediante backend privilegiado,
gestión de roles y activación, cola paginada, filtros, edición editorial completa
para `admin`, edición de `missing_fields` para `user`, optimistic locking,
publicar/despublicar/archivar, calidad, auditoría y compatibilidad con static export.

`studiamatch.com/admin/` debe responder `404` y no servir el panel.

### Contrato de campos

Los campos editoriales públicos de curso son: `name`, `price_pen`, `price_status`,
`mode`, `duration`, `description_long`, `syllabus`, `target_audience`,
`requirements`, `certification`, `benefits`, `objectives` y `start_date_text`.

`admin` puede corregirlos todos. `user` puede corregir únicamente los que aparezcan
en `course_editorial_state.missing_fields`. Identidad, institución, URL, slug,
categoría, fecha estructurada, tipo de curso, brochure, cálculos ROI, métricas,
metadata y estados editoriales no son editables por `user`.

El pipeline debe transportar `benefits`, `certification`, `objectives` y
`target_audience` con semántica independiente; no se acepta sustituirlos
silenciosamente por el mismo origen ni marcar `missing_fields` únicamente por
`duration` sin validar el diccionario de publicación.

## Validacion Contra Fuente Cliente

El alcance base de H3 (`/admin`, cola, edición manual y publicación) se valida contra la fuente privada cliente `SRC-REQ-002` mediante la atestación sanitizada versionada [ADENDA-REQ-EST-001-001](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md). La ampliación está respaldada por la atestación sanitizada [H3-EXPANDED-PROMPT-2026-08-30](../evidencias_cliente/sprint_1/atestado_h3_ampliacion_prompt_humano_sanitizado.md), que autoriza únicamente ejecución local Docker hasta GO local. La fuente privada no se versiona ni se expone en PRs.

## Contrato De Acceso

- Usuario anonimo no accede.
- Usuario autenticado sin membresia activa no accede.
- Usuario con membresia activa `user` accede a `/admin/`, consulta la cola y completa unicamente campos incluidos en `missing_fields`.
- Usuario con membresia activa `admin` hereda las capacidades de `user` y ademas publica, despublica, archiva, actualiza `quality_status` y gestiona membresias.
- Toda mutación exige identidad y rol válidos dentro de la RPC; las acciones administrativas exigen rol `admin` y dejan auditoría.
- `admin` puede invitar por correo, cambiar el rol y activar/desactivar cualquier membresía `admin` o `user` desde el panel mediante botón o checkbox, sujeto únicamente a la invariante de conservar al menos un `admin` activo y evitar el auto-bloqueo accidental del último admin.

## Contrato Funcional

- Cola paginada con filtros por estado editorial/calidad.
- Edición admin de todos los campos editoriales públicos definidos; edición user solo de `missing_fields`.
- Optimistic locking por `version`.
- Publicar/despublicar/archivar y cambiar `quality_status` solo para admin.
- Publicar/despublicar/archivar sin que pipeline pueda saltar revisión.
- Auditoría append-only por cada mutación editorial y de membresía.
- MFA TOTP obligatorio para ambos roles: login, enrollment, challenge y verify deben producir sesión Supabase `aal2`; las operaciones sensibles rechazan `aal1`.
- Cloudflare Access protege `admin.studiamatch.com`; `studiamatch.com/admin/` responde HTTP 404 y no sirve el panel.
- Invitación de usuarios por correo mediante Edge Function protegida con `verify_jwt=true`; `service_role` nunca llega al navegador.
- El panel admin debe mostrar el estado activo/inactivo y permitir activarlo o desactivarlo en cualquier miembro `admin` o `user` mediante botón o checkbox con confirmación y feedback.
- Pro es la fuente autoritativa del baseline H2: schema, tipos, constraints, campos y últimas migraciones; Free y el PostgreSQL 17 local deben converger hacia ese baseline Pro, nunca al revés.
- La convergencia H2 debe cubrir schema, funciones, grants, RLS, vistas, campos y migraciones; los datos operativos no se sincronizan como mecanismo normal.
- Las migraciones H3 son un delta funcional nuevo: pueden estar ausentes en Pro hasta su promoción protegida, pero deben ser el mismo artefacto versionado que se valida primero en local, luego en Free y finalmente en Pro.
- Las migraciones H3 Docker, harness y fixtures ya validados se reutilizan como candidato; se rebaten contra la forma Pro en una base PG17 limpia; solo se crean deltas idempotentes cuando exista incompatibilidad demostrada.
- No se borran ni se repiten automáticamente cambios H3 locales; los datos de prueba no se promueven.
- Segunda corrida `NOOP` y validación remota antes de Certification; la validación remota permanece bloqueada hasta GO local y JIT.
- UAT local ampliada: dos corridas reportan 47/47 casos y 141/141 ejecuciones PASS con cero retries y 141 screenshots por corrida. Auditoría posterior determinó que parte de la matriz valida presencia de código/controles y no E2E contractual completo.
- Static build: `npm run build` y `npm run build:mock` revalidados PASS en Docker; las cuatro rutas admin están exportadas. Waiver static export superseded.

## Gate

Estado vigente: `H3_PR_DEVELOPMENT_READY_LOCAL` (GO para PR). Los bloqueadores
HIGH/CRITICAL que QA, seguridad y DB detectaron (workflow/gates H3, invariantes
DB, enrollment y confirmación MFA real, pruebas E2E, rollback y evidencia
autocontenida vinculada al candidato) fueron resueltos en el ciclo de corrección
local del 2026-09-02 y revalidados en Docker: `security-audit.yml` corregido con
allowlist H3 y `db-gate` con harness PG17, contrato `20260902_h3_pr_contract.sql`
con lector efectivo y gate de publicabilidad, seed idempotente con categorías,
harnesses `h3_pg17_harness_ok` y `h3_pg17_harness_local_ok`, MFA con secreto/QR y
`aal` real, UAT canónica 47/47 y 141/141 PASS con 0 retries y evidencia
regenerada en `.context/evidencia/h3-expanded/`.

Commit + push + PR protegido a `desarrollo` quedaron autorizados por instrucción
humana separada y se ejecutan con la plantilla
`.github/pull_request_template.md`. Permanece bloqueada toda acción remota
posterior (JIT Supabase Free/Auth, Cloudflare, certificación, merge y deploy)
hasta su aprobación separada.

## Matriz de avance por criterio

| Criterio | Implementación | Validación | Pendiente de cierre |
|---|---|---:|---:|---|
| H3-CA4.1 Auth/RBAC | 90% | 85% | Auth real y negativos remotos. |
| H3-CA4.2 Ownership de 13 campos | 85% | 75% | Cobertura de valores efectivos en entorno real. |
| H3-CA4.3 Transporte independiente | 60% | 40% | Prueba E2E diferenciando cuatro campos en entorno real. |
| H3-CA4.4 Cola | 85% | 70% | Segunda página y cursor en entorno real. |
| H3-CA4.5 Mutaciones | 90% | 75% | Locking de estados en entorno real. |
| H3-CA4.6 Auditoría | 85% | 60% | Auditoría de todas las mutaciones en entorno real. |
| H3-CA4.7 MFA/`aal2` | 80% | 55% | Supabase Auth real y negativos remotos. |
| H3-CA4.8 Membresías | 75% | 45% | Invitación por correo (Edge Function) y Auth real. |
| H3-CA4.9 Hostname | 60% | 40% | Allowlist positiva, smoke en despliegue y Cloudflare Access. |
| H3-CA4.10 Convergencia | 55% | 35% | Diff Pro/Free/local y validación remota JIT. |
| H3-CA4.11 UAT/artifacts | 100% estructural | 55% contractual | UAT local canónica 47/47 y 141/141 PASS; falta UAT real en Free/Certification. |
| **Readiness PR** | **78.7% provisional** | **57.7% provisional** | **`H3_PR_DEVELOPMENT_READY_LOCAL`; GO local para PR; validación remota pendiente de JIT.** |
