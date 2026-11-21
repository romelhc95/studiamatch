# Arquitectura del sistema

> Estado: descripción de implementación candidata local, corte 2026-10-12. Los diagramas resumen rutas de código y configuración observadas; no demuestran conectividad o adopción remota.

## Límites y runtimes

StudIAMatch se divide en cinco runtimes. El frontend se exporta como archivos estáticos Next.js; las Pages Functions ejecutan el BFF Admin; el Worker con Durable Object conserva contadores de cuota; Supabase ofrece PostgreSQL, Auth, PostgREST y Edge Functions; el pipeline Python se ejecuta en runners GitHub Actions o en Docker local. No hay base de datos local del producto. PostgreSQL 17 se usa únicamente como fixture de prueba desechable.

```mermaid
flowchart LR
  Browser[Browser]
  Static[Cloudflare Pages static assets]
  Build[Next.js build/export]
  PublicReader[Supabase PostgREST public reader]
  Fn[Pages Functions Admin BFF]
  Quota[Worker Durable Object quota]
  Edge[Supabase Edge admin-invite]
  Auth[Supabase Auth]
  Gateway[PostgREST pre-request signed RPC gateway]
  DB[(Supabase PostgreSQL)]
  Actions[GitHub Actions pipeline runners]
  Python[Python FG1 FG2 FG3]
  Providers[Instituciones y proveedores LLM]

  Browser --> Static
  Browser --> PublicReader
  Build --> PublicReader
  Browser --> Fn
  Fn --> Quota
  Fn --> Auth
  Fn --> Gateway
  Fn --> Edge
  Edge --> Auth
  Edge --> EdgeRPC[Supabase PostgREST invitation RPCs via service_role]
  Gateway --> DB
  EdgeRPC --> DB
  PublicReader --> DB
  Actions --> Python
  Python --> DB
  Python --> Providers
```

La página estática se descarga desde Pages; durante uso público el navegador consulta datos efectivos mediante Supabase JS/Data API con publishable key. Separadamente, `next build` consulta PostgREST en `generateStaticParams` y `fetchCourseMeta` para generar rutas y metadata estática; que el build lea DB no significa que Pages estático sea un servidor conectado a DB en runtime. Admin usa el BFF con cookie de sesión HttpOnly y comprobaciones de origen/cookie; el BFF valida el usuario en el mismo proyecto Supabase y limita las RPC a una allowlist. Las llamadas directas `POST /api/admin/rpc` se remapean a `admin_signed_rpc` y llevan firma HMAC verificada por el pre-request de PostgREST. La invitación sigue otro canal: el BFF pasa el JWT de sesión a `admin-invite`; Edge valida la identidad, AAL2 y membresía activa, y después llama las RPC del ciclo de invitación con una API key server-side `service_role` y el actor explícito. El pre-request SQL local retorna temprano para `service_role`, por lo que ese canal no consume el gateway HMAC. Código/migration son locales; configuración, claves y adopción remotas no se consultaron. El Worker de cuota es un binding de runtime interno, distinto del servicio Supabase.

```mermaid
flowchart TD
  Sources[config/institution_sources.json y perfiles]
  FG1[FG1 discovery_institutions]
  Onboard[FG2 perfilado acotado]
  FG2[FG2 master_orchestrator]
  H[Harvester]
  C[Cleansing]
  E[Enrichment]
  S[Sync y publicación]
  I[FG3 integrity_ping]
  Raw[(staging_raw)]
  Clean[(cleansed_programs)]
  Enriched[(enriched_programs)]
  Courses[(courses)]
  Editorial[(course_editorial_state y audit)]
  Effective[courses_public_effective]
  Public[Frontend público]
  Admin[Admin editorial]

  Sources --> FG1
  Sources --> FG2
  FG1 --> FG2
  Sources --> Onboard
  Onboard --> FG2
  FG2 --> H --> Raw --> C --> Clean --> E --> Enriched --> S --> Courses
  S --> Editorial
  Admin --> Editorial
  Courses --> Effective
  Editorial --> Effective
  Effective --> Public
  I --> Courses
```

### FG2: perfilado, tres modos web y frontera editorial — candidato local 2026-11-20

Antes de seleccionar instituciones para harvest, `master_orchestrator.py` puede
diagnosticar únicamente slugs de instituciones ya registradas y explícitamente
incluidos en `FG2_PROFILE_DIAGNOSTIC_SLUGS`. Ese diagnóstico no depende de que
exista un perfil efectivo: usa `institutions.website_url`, aplica límites de
HTTP, DNS público, pinning, validación de redirects, cuerpos de hasta 2 MiB y
una pausa de cinco segundos por origen. Una persona no aprueba cada corrida;
la selección de slugs, persistencia y autoactivación son controles distintos
por Environment. Sus valores remotos no se comprobaron en este ciclo.

El resultado mantiene separados `diagnostic_observed`,
`diagnostic_suggested` y el perfil efectivo. Una señal ambigua o incompleta
queda `pending_review`; no inventa campos, no elimina exclusiones ni activa
stealth. Un perfil activo validado se conserva íntegro. Autoactivación rutinaria
solo puede ocurrir bajo la política explícita y después de verificar origen,
descubrimiento de un programa nuevo y dos fichas de curso; esto no se aplica a
Pro en este candidato. Los perfiles sugeridos no se copian de Free a Pro.

El harvester soporta perfiles `traditional_ssr`, `spa_js_heavy` y `ecommerce`.
Sitemap, catálogo paginado y extracción de enlaces son fuentes de discovery;
las páginas de detalle usan filtros de cursos. Tanto el diagnóstico como el
runtime browser de cosecha usan Chromium con sandbox: HTTP de página y
subrecursos cruzan la ruta validada, fijada y contabilizada; WebSocket se cierra
antes de conectar; WebRTC y WebTransport se deshabilitan y verifican antes de
cargar contenido. En el diagnóstico también se apaga QUIC. La cosecha falla
cerrada si no instala o verifica sus guardas; un intento WebSocket detiene la
institución y no se registra el curso parcial. Los orígenes de recursos de
terceros se bloquean salvo allowlist exacta. Los límites por institución cubren
requests, URLs, redirects, retries, concurrencia y ritmo. 403/429 detiene esa
institución y no abre una exclusión permanente.

La ruta de datos continúa por staging, cleansing, enrichment y sync. El curso
nuevo entra a `courses` con su estado editorial `pending_review`; el
ensayo candidato comprobó que queda en la cola leída por las RPC Admin y que
no aparece en `courses_public_effective`. El refresh sintético conservó
`course_id` y el override editorial. HTTP y proveedor fueron fixtures locales;
esto no acredita extracción institucional real, credenciales, permisos,
políticas remotas ni disponibilidad de los proveedores.

La migration `20261120120000_fg2_profile_onboarding_state.sql` es aditiva y
local. Transición: `expand` agrega metadata diagnóstica y estados compatibles;
`compatibilidad` mantiene el perfil efectivo actual y deja los nuevos campos
con defaults; `deploy` requiere promoción protegida, comparación de schema y
autorización DB JIT por ambiente; `contract` solo después de observación
funcional y sin retirar compatibilidad útil. Rollback antes de aplicar es
descartar el diff; tras integración, revertir por PR y conservar datos
diagnósticos antes de cualquier DDL destructivo separado.

## Datos y dependencias

- El catálogo institucional y sus perfiles gobiernan descubrimiento, exclusiones y elegibilidad del pipeline.
- Datos operativos por ambiente pasan por staging, limpieza y enriquecimiento; el writer normal final es sync. La tarea FG3 mantiene/verifica courses.
- La capa editorial separa valores efectivos/editoriales de campos base del pipeline. La vista pública aplica estado publicado y calidad completa junto con condiciones de curso/institución.
- Admin usa Supabase Auth para identidad y admin_members para rol/actividad. MFA AAL2 se exige para las acciones sensibles configuradas.
- Dependencias externas: páginas/sitemaps institucionales, proveedores LLM en orden con fallback, Cloudflare Pages/Workers, Supabase y GitHub Actions. La configuración local no acredita versiones activas remotas ni disponibilidad de proveedores.

## Compatibilidad, recuperación y puntos de fallo

Las promociones con cambio de contrato siguen expand -> compatibilidad -> deploy -> contract: añadir compatibilidad, comprobar coexistencia, desplegar el consumidor y retirar el contrato viejo solo tras verificar estabilización. El plan de rollback debe ser específico por ambiente y por writer; SQL de rollback no es permiso para ejecutarlo.

Los cortes principales son: export estático sin ruta generada hasta un rebuild; lectura de Supabase fallida o datos públicos no publicados; BFF/DO de cuota sin disponibilidad (fail closed); verificación de sesión, MFA o gateway ausente; fallo de proveedor LLM con fallback agotado; y gates/perfiles de institución que saltan estaciones. Se registran errores/estados en tablas del pipeline, responses HTTP y evidencia de workflow. No se documenta una observabilidad remota consultada en este corte.

## Fuentes

| Afirmación | Fuente local |
|---|---|
| Entrega estática, lectura pública y rutas estáticas | web/next.config.js, web/src/lib/supabase.ts, web/src/app/page.tsx, web/src/app/courses/[institution]/[slug]/page.tsx (`generateStaticParams`, `fetchCourseMeta`), web/functions/_middleware.ts. |
| Transporte Admin y sesiones | web/src/lib/admin-auth.ts, web/functions/_lib/admin-bff.ts, migración 20261004_h3_admin_rpc_signed_gateway_expand.sql. |
| Datos efectivos y pipeline | db/restore_full_schema.sql, migraciones H2/H3, scripts/core/{master_orchestrator,universal_harvester,cleansing_worker,enrichment_worker,sync_vector_worker,integrity_ping}.py. |
| Durables y Edge | workers/admin-quota/index.ts, workers/admin-quota/wrangler.jsonc, supabase/functions/admin-invite/index.ts, supabase/config.toml. |
| Restricciones/ambientes | AGENTS.md, [estado operativo](estado_del_proyecto.md). |
| Validación integrada local | [R178](evidencia/h3req1_g09_local_close_r178_2026-10-11.md), sin prueba de despliegue actual. |

## Navegación relacionada

[Índice principal](indice.md) · [Frontend](frontend.md) · [Backend](backend.md) · [Base de datos](database.md) · [Pipeline](componentes/pipeline.md) · [Seguridad](seguridad.md) · [Pruebas](pruebas.md) · [Operación](operacion.md) · [CI/CD](ci_cd.md) · [Requerimientos](requerimientos/README.md) · [Hitos](hitos/README.md) · [Decisiones](decisiones/README.md)
