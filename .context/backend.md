# Backend: BFF, RPC, Edge y servicios auxiliares

## Mapa de endpoints Admin

El middleware de Pages Functions enruta /api/admin/* al BFF y normaliza rutas Admin. Métodos distintos de los indicados responden error de método. Los cuerpos JSON son acotados y validados en cada handler; los detalles de tipos/respuestas están en routeAdminBff, los handlers de routeMutation, adminApi y la función Edge.

| Endpoint | Método | Entrada principal | Respuesta/errores | Autorización |
|---|---|---|---|---|
| /api/admin/session | GET | cookie Admin | authenticated, session summary o sesión vacía; csrf_rejected, server_configuration_error o 503 | cookie same-origin, sesión Auth vigente y cookie de actividad firmada/fresca. Este endpoint no consulta rol ni membresía; RPC/operaciones protegidas validan permiso. |
| /api/admin/activity | POST | objeto JSON vacío | registra actividad/cookie; errores de sesión, origen o cuota | sesión Auth y protección origen/CSRF |
| /api/admin/auth/login | POST | email, password | session; invalid_credentials, auth_rate_limited u otros errores de Auth | intercambio contra Auth; host permitido y cuotas |
| /api/admin/auth/logout | POST | objeto JSON vacío | success; siempre limpia cookie local | origen válido; disponible aunque upstream/cuota no lo esté |
| /api/admin/auth/callback | POST | formulario: type, code o token_hash, callback_csrf | confirmación y redirect; callback inválido vuelve a callback con error | callback CSRF y redirect acotado |
| /admin/auth/callback/ | GET | code o token_hash más type invite/recovery | página/confirmación que envía POST al BFF; query acotada | path canónico, tipo permitido y parámetros de formato |
| /api/admin/auth/password | POST | password | success; invalid_password o password_update_failed | sesión activa, política 12–128 chars/clases y cuota |
| /api/admin/auth/mfa | POST | action list/assurance/enroll/challenge/verify/unenroll; factorId/challengeId/code según acción | factores TOTP acotados, assurance, enroll o success; códigos mfa_* | sesión actual; cuotas en mutaciones; AAL2 para cambios de factor existente |
| /api/admin/rpc | POST | function, params; x-request-id cuando aplica | data con resultado RPC; rpc_not_allowed, gateway/auth/quota errors | sesión/cookie, RPC allowlisted, rol/MFA por función y gateway firmado |
| /api/admin/invitations | POST | email, role, resend; x-request-id | success, user_id, invitation_id/status; invalid input, conflict/reconciliation, 401/403/429/503 | Admin activo, AAL2, origen/host, cuota y Edge con verify_jwt |

La API permite solo GET/POST bajo /api/admin. Los cuerpos se limitan y parsean antes de mutar. La API key Supabase va exclusivamente en `apikey`. `Authorization: Bearer` con JWT de usuario se permite solo en las rutas Auth/RPC/Edge explícitas al mismo proyecto configurado; no llega al navegador, a tablas Data API arbitrarias ni a destinos/redirects elegidos por request. El BFF no tiene secret/service-role key. En el handler Edge de invitación, la key server-side se usa para las RPC después de verificar la sesión del usuario.

## PostgREST: lector público

El cliente público solo hace lecturas `GET` al proyecto configurado y envía la publishable key en `apikey`; no usa JWT de sesión ni ejecuta escrituras. En runtime browser las peticiones van desde `HomeContent`, comparación y detalle a Supabase Data API. Durante `next build`/export, `generateStaticParams` y `fetchCourseMeta` repiten consultas para generar paths y metadata; los archivos estáticos publicados no mantienen una conexión propia con DB. El contrato completo de campos, vista efectiva y grants/RLS locales está en [database.md](database.md); el SQL local no prueba que los grants estén aplicados remotamente.

| Recurso/método | Inputs observados | Output y consumidor | Acceso/errores |
|---|---|---|---|
| `GET /rest/v1/courses_public_effective` | `select=COURSE_PUBLIC_FIELDS`; catálogo ordena `created_at.desc`; detalle filtra `institution_id` + `slug` (`eq`, fallback acotado `url/slug=ilike` + `limit=1`); comparación filtra `id=in.(UUIDs)` ya validados; relacionados filtran `category_id`, `institution_id`, `id=neq` + `limit=3`; build selecciona `id,institution_id,slug,url` para rutas. | Array JSON de filas de la vista efectiva; metadata estática, catálogo, detalle, comparación y hasta 3 cursos relacionados. | Publishable key en `apikey`, grants/RLS de lectura según SQL local y filtros de publicación/calidad de la vista; no exige sesión de usuario. HTTP no-2xx se traduce a error/estado vacío según pantalla; cero filas se muestra como no disponible/vacío. |
| `GET /rest/v1/institutions` | `select=id,name,slug`; filtro de build/detalle `slug=eq.<slug>` y `limit=1` según consumo. | Array JSON usado para enlazar nombre/slug e `institution_id`; build usa `id,slug` para rutas. | Misma publishable key; solo columnas solicitadas. Errores/arrays inválidos producen fallback/vacío en el consumidor. |
| `GET /rest/v1/categories` | `select=id,name`. | Array JSON que enriquece nombres de categoría en catálogo/comparación/detalle. | Misma publishable key; fallos se tratan como arreglo vacío/fallback de etiqueta. |

El cliente solicita `COURSE_PUBLIC_FIELDS` definido en [`web/src/lib/supabase.ts`](../web/src/lib/supabase.ts). Consumidores y flujos: [`web/src/app/page.tsx`](../web/src/app/page.tsx), [`web/src/app/HomeContent.tsx`](../web/src/app/HomeContent.tsx), [`web/src/app/compare/CompareContent.tsx`](../web/src/app/compare/CompareContent.tsx), [`web/src/app/courses/[institution]/[slug]/page.tsx`](../web/src/app/courses/%5Binstitution%5D/%5Bslug%5D/page.tsx) y [`CourseDetailClient.tsx`](../web/src/app/courses/%5Binstitution%5D/%5Bslug%5D/CourseDetailClient.tsx). CORS, roles, grants, vistas y cache remotos no se inspeccionaron en esta sesión.

## Rutas downstream Supabase Auth permitidas

El BFF usa el SDK server-side y limita el transporte con sesión a rutas/métodos del mismo proyecto configurado. La key pública va solo en `apikey`; el JWT del usuario se reenvía como `Authorization: Bearer` solo para las operaciones listadas. `listFactors()` del SDK usa GET `/auth/v1/user`; no se permite GET `/auth/v1/factors`. Respuestas crudas del proveedor no se devuelven como error de aplicación.

| Método/ruta downstream | Datos y resultado observado | Gate/normalización local |
|---|---|---|
| GET `/auth/v1/user` | Sin body; consulta usuario autenticado. SDK MFA `listFactors()` obtiene TOTP desde esta respuesta del endpoint user. | JWT/cookie BFF válido y mismo proyecto; errores de sesión se normalizan como no autenticado o MFA no disponible. Edge invitation también lo usa solo para `getUser(accessToken)`. |
| PUT `/auth/v1/user` | Actualiza el perfil Auth; en este sistema, nueva password validada por BFF. | Sesión; 12–128 caracteres, mayúscula/minúscula/número/símbolo; el BFF responde `success` o `password_update_failed`. |
| POST `/auth/v1/factors` | Enrola factor `totp`; devuelve id y datos de setup QR/URI/secret al usuario Admin autenticado. | Sesión y reglas de factor pendiente/ya verificado; errores se normalizan como `mfa_enrollment_pending`, `mfa_required` o `mfa_enrollment_failed`. |
| POST `/auth/v1/factors/{factorId}/challenge` | Inicia desafío TOTP y devuelve challenge id. | `factorId` UUID; cuota y sesión; error se normaliza `mfa_challenge_failed`. |
| POST `/auth/v1/factors/{factorId}/verify` | Envía challenge id y código TOTP de 6–8 dígitos; el BFF renueva/actualiza sesión al verificar. | UUID, challenge presente, código validado, sesión vigente y cuota; error `invalid_challenge`/MFA o `session_unavailable`. |
| DELETE `/auth/v1/factors/{factorId}` | Elimina factor por UUID. | Sesión; lista/estado de factor; AAL2 antes de retirar factor verificado; errores `invalid_factor`, `mfa_required`, `mfa_unenroll_failed`. |

Estas excepciones de bearer no habilitan destinos arbitrarios, métodos adicionales, browser JWT ni acceso a tablas PostgREST. La allowlist y pruebas de identidad están en `web/src/lib/supabase-transport.ts`, `web/functions/_lib/admin-bff.ts` y `tests/test_supabase_credentials_contract.py`; el contrato sanitizado de `AGENTS.md` aplica al corte local y no acredita configuración Auth remota.

## BFF y contrato de error

web/functions/_middleware.ts bloquea paths Admin codificados no canónicos, rutas deshabilitadas responden 503 y el resto de /admin y /api/admin se resuelve en routeAdminBff. El BFF valida método, host exacto permitido, origen/CSRF y tamaño/JSON; responde con errores estables como unauthenticated, csrf_rejected, server_configuration_error, quota_unavailable, quota_rate_limited, rpc_not_allowed, rpc_gateway_unavailable, rpc_failed, errores de invitación, password/MFA y not_found. No filtrar tokens, secretos ni errores crudos de proveedor en UI/logs.

Las cookies de sesión son Secure en hosts remotos, HttpOnly y SameSite restringido. Excepciones localhost/mock existen únicamente para desarrollo local aislado. No debe provisionarse la secret/service-role key en el BFF. Logout limpia la cookie del browser incluso si Auth/cuota upstream no responden; no promete revocación global de la sesión del proveedor.

La ficha de [transporte Supabase](componentes/supabase_transport.md#contrato-api-key-y-sesion) mantiene las rutas/métodos exactos, políticas por runtime, firma y límites del wrapper. El SDK público y el BFF importan el mismo helper con policies diferentes; un cambio allí exige revisar ambos callers y sus suites.

## RPC y autorización de datos

RPC Admin relevantes: lectores de cola/facetas y miembros; actualización/publicación/despublicación/archivo/calidad/disponibilidad; auditoría; invitación/onboarding; y control de AAL2, roles, miembro activo y último Admin. Solo el canal directo del BFF `POST /api/admin/rpc` se remapea a `public.admin_signed_rpc`: `createApiKeyOnlyFetch` firma HMAC, key ID, proyecto, identidad, RPC y argumentos allowlisted; los nonces impiden replay dentro de su ventana. La migration `20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql`, función `h3_admin_rpc_signed_gateway_pre_request`, retorna temprano para `service_role`; por tanto no aplica esa firma a la ruta Edge.

### Allowlist RPC Admin y firmas

La lista de invocación directa es exactamente el `ADMIN_RPC_ALLOWLIST` de [`admin-bff.ts`](../web/functions/_lib/admin-bff.ts#L61-L81), no todas las rutinas `admin_*` creadas por SQL. El BFF exige una sesión Auth válida, nombre permitido y `params` objeto no-array; la función SQL sigue aplicando su autorización y validación. Los parámetros omitidos conservan los defaults SQL que se muestran. `POST /api/admin/rpc` envuelve el resultado como `{ "data": ... }`; los errores SQL se normalizan a `mfa_required`, `rpc_failed` y status 403/400/503/502 sin reenviar mensajes crudos. El propio RPC puede devolver `success=false` junto con `error`/`error_code`; eso es resultado de aplicación, no un HTTP 2xx sin revisar el payload.

| Clase | RPC y parámetros (nombre: tipo; default cuando aplica) | Resultado SQL local | Consumidor y fuente de definición |
|---|---|---|---|
| Read | `admin_current_user_role()` | `TEXT` (rol de la identidad; sin parámetros) | `web/src/lib/admin-auth.ts`; [`20260924_h3_onboarding_rbac_hardening_fix.sql`](../db/migrations/20260924_h3_onboarding_rbac_hardening_fix.sql#L5-L25). |
| Read | `admin_get_onboarding_status()` | Fila `success, user_id, email, role, account_status, invitation_status, invitation_id, expires_at, error_code` | `web/src/lib/admin-auth.ts`; [`20260921_h3_invitation_onboarding_rpc.sql`](../db/migrations/20260921_h3_invitation_onboarding_rpc.sql#L676-L691). |
| Read | `admin_get_course_audit(p_course_id: UUID, p_first: INTEGER = 20, p_after_created_at: TIMESTAMPTZ = NULL, p_after_id: UUID = NULL)` | Fila `events JSONB, page_info JSONB, error TEXT` | Página de edición/auditoría; [`20261001_h3_course_editorial_audit_availability.sql`](../db/migrations/20261001_h3_course_editorial_audit_availability.sql#L227-L240). |
| Read | `admin_get_course_editorial(p_course_id: UUID)` | Fila `course JSONB, field_definitions JSONB, error TEXT` | Editor Admin; [`20261001_h3_course_editorial_audit_availability.sql`](../db/migrations/20261001_h3_course_editorial_audit_availability.sql#L327-L337). |
| Read | `admin_get_course_queue_facets()` | Fila `editorial_counts JSONB, quality_counts JSONB, institutions JSONB, error TEXT` | [`AdminCourseQueue.tsx`](../web/src/components/AdminCourseQueue.tsx); [`20260927_h3_admin_queue_facets_filter.sql`](../db/migrations/20260927_h3_admin_queue_facets_filter.sql#L149-L158). |
| Read | `admin_get_course_queue_filtered(p_first: INTEGER = 20, p_after_cursor: TEXT = NULL, p_editorial_status: TEXT = NULL, p_quality_status: TEXT = NULL, p_institution_slug: TEXT = NULL)` | Fila `courses JSONB, page_info JSONB, error TEXT` | [`AdminCourseQueue.tsx`](../web/src/components/AdminCourseQueue.tsx); [`20260927_h3_admin_queue_facets_filter.sql`](../db/migrations/20260927_h3_admin_queue_facets_filter.sql#L6-L20). |
| Read | `admin_count_course_queue_filtered(p_editorial_status: TEXT = NULL, p_quality_status: TEXT = NULL, p_institution_slug: TEXT = NULL)` | Fila `total INTEGER, error TEXT` | [`AdminCourseQueue.tsx`](../web/src/components/AdminCourseQueue.tsx); [`20260927_h3_admin_queue_facets_filter.sql`](../db/migrations/20260927_h3_admin_queue_facets_filter.sql#L105-L116). |
| Read | `admin_list_members_onboarding()` | Filas `user_id UUID, email TEXT, role TEXT, is_active BOOLEAN, created_at TIMESTAMPTZ, account_status TEXT, invitation_status TEXT, expires_at TIMESTAMPTZ` | [`web/src/app/admin/users/page.tsx`](../web/src/app/admin/users/page.tsx); [`20260925_h3_admin_members_onboarding_reader.sql`](../db/migrations/20260925_h3_admin_members_onboarding_reader.sql#L6-L19). |
| Write | `admin_accept_current_invitation(p_invitation_id: UUID = NULL)` | Fila `success, invitation_id, member_id, account_status, role, error_code` | `web/src/lib/admin-auth.ts`; última definición local [`20261001_h3_invitation_reservation_compensation.sql`](../db/migrations/20261001_h3_invitation_reservation_compensation.sql#L817-L831). |
| Write | `admin_complete_password_setup()` | Fila `success, member_id, account_status, role, error_code` | `web/src/lib/admin-auth.ts`; [`20260921_h3_invitation_onboarding_rpc.sql`](../db/migrations/20260921_h3_invitation_onboarding_rpc.sql#L574-L585). |
| Write | `admin_update_course(p_course_id: UUID, p_manual_overrides: JSONB, p_version: INTEGER, p_reason: TEXT = NULL)` | Fila `success BOOLEAN, course_id UUID, new_version INTEGER, error TEXT` | Página de edición; última definición local [`20261001_h3_course_editorial_audit_availability.sql`](../db/migrations/20261001_h3_course_editorial_audit_availability.sql#L482-L496). |
| Write | `admin_set_course_availability(p_course_id: UUID, p_availability_status: TEXT, p_evidence_url: TEXT, p_observed_at: TIMESTAMPTZ, p_valid_until: TIMESTAMPTZ, p_version: INTEGER, p_reason: TEXT)` | Fila `success BOOLEAN, course_id UUID, new_version INTEGER, error TEXT` | Página de edición; [`20261001_h3_course_editorial_audit_availability.sql`](../db/migrations/20261001_h3_course_editorial_audit_availability.sql#L68-L85). |
| Write | `admin_publish_course(p_course_id: UUID, p_reason: TEXT = NULL)` | Fila `success BOOLEAN, course_id UUID, new_status TEXT, error TEXT` | Página de edición; última definición local [`20261001_h3_course_editorial_audit_availability.sql`](../db/migrations/20261001_h3_course_editorial_audit_availability.sql#L643-L655). |
| Write | `admin_unpublish_course(p_course_id: UUID, p_reason: TEXT = NULL)` | Fila `success BOOLEAN, course_id UUID, new_status TEXT, error TEXT` | Página de edición; [`20260828_h3_admin_editorial_rpc.sql`](../db/migrations/20260828_h3_admin_editorial_rpc.sql#L243-L255). |
| Write | `admin_archive_course(p_course_id: UUID, p_reason: TEXT = NULL)` | Fila `success BOOLEAN, course_id UUID, new_status TEXT, error TEXT` | Página de edición; [`20260828_h3_admin_editorial_rpc.sql`](../db/migrations/20260828_h3_admin_editorial_rpc.sql#L319-L331). |
| Write | `admin_update_quality_status(p_course_id: UUID, p_quality_status: TEXT, p_reason: TEXT = NULL)` | Fila `success BOOLEAN, course_id UUID, new_status TEXT, error TEXT` | Página de edición; [`20260828_h3_admin_editorial_rpc.sql`](../db/migrations/20260828_h3_admin_editorial_rpc.sql#L396-L409). |
| Write | `admin_update_member(p_user_id: UUID, p_role: TEXT = NULL, p_is_active: BOOLEAN = NULL, p_action: TEXT = 'update')` | Fila `success BOOLEAN, user_id UUID, role TEXT, is_active BOOLEAN, error TEXT` | [`web/src/app/admin/users/page.tsx`](../web/src/app/admin/users/page.tsx); última definición local [`20260924_h3_onboarding_rbac_hardening.sql`](../db/migrations/20260924_h3_onboarding_rbac_hardening.sql#L101-L110). |

`ADMIN_RPC_READS` clasifica cuotas (`rpc-read`/`rpc-write`) en [`admin-bff.ts`](../web/functions/_lib/admin-bff.ts#L83-L95); contiene además `admin_get_course_queue`, `admin_count_course_queue` y `admin_list_members`, que no aparecen en `ADMIN_RPC_ALLOWLIST` y por ello no son invocables a través de este endpoint directo. No confundir la lista de cuota con el contrato de invocación.

La tabla admin_members separa rol (admin/user), actividad y estado de onboarding. RPC de transición impide auto-bloqueo/retirar el último Admin activo y generan ledger de auditoría append-only. El estado visible proviene de funciones SQL autorizadas, no de confiar en claims editables del navegador.

## Edge de invitación y cuota

supabase/functions/admin-invite/index.ts admite OPTIONS de CORS y POST; rechaza otros métodos con 405. El body tiene límite 64 KiB; el handler verifica JWT del usuario con Auth `getUser`, origen/redirect allowlist, assurance AAL2, membresía Admin activa, rol, email, request ID/idempotencia y admisión/cooldown. Tras esas comprobaciones, su cliente Edge usa `NEXT_SUPABASE_SECRET_KEY` solo server-side como API key en `apikey` y llama RPC de invitaciones, incluyendo `admin_invitation_request_admit`, pasando `p_actor_user_id`; reserva en SQL antes de enviar correo, compensa o registra fallos/reconciliación y no devuelve token persistido en claro. Este canal service-role no lleva la firma HMAC del BFF y queda delimitado por las verificaciones de identidad/rol del handler y los argumentos de actor. `supabase/config.toml` configura `verify_jwt` para la función. Todo lo anterior se acredita desde código/migration local; secreto aprovisionado, pre-request y despliegue por ambiente son desconocidos.

supabase/functions/send-lead-emails/index.ts es otra Edge Function heredada. Acepta OPTIONS y, en el código local observado, no muestra una allowlist de métodos antes de leer JSON. Toma datos de lead/curso/institución del body, arma mensajes para lead, administradores y contacto institucional, y llama Resend cuando RESEND_API_KEY existe; sin ella, el código genera respuesta mock. Usa ADMIN_EMAIL como fuente de destinatarios con alias plural ADMIN_EMAILS derivado y contiene un destinatario literal de fallback; el valor se omite. `rg` en web/scripts/supabase/db/.github/tests no encontró un caller directo distinto del inventario de contratos; un trigger externo/remoto podría existir y no se verificó. No es parte del flujo Admin Invite; no reactivar ni exponer hasta retirar/verificar ese fallback y revisar autenticación, métodos, CORS, validación/escape de PII, provider y caller.

Las plantillas locales `supabase/templates/invite.html` y `password-recovery.html` forman parte del correo Auth: usan `{{ .RedirectTo }}` y `{{ .TokenHash }}` con `type=invite` o `type=recovery`, que consume la ruta `/admin/auth/callback/` y envía la confirmación al BFF. Contratos: `web/src/app/admin/auth/callback/page.tsx`, `tests/test_h3_invitation_callback_contract.py` y `tests/test_h3_password_recovery_contract.py`. Estos archivos locales no acreditan qué plantilla está configurada en Auth remoto.

web/functions/_lib/admin-quota.ts utiliza binding ADMIN_QUOTA; el Worker configura ADMIN_QUOTA_COUNTER Durable Object. El contador mantiene ventanas persistentes con serialización transaccional. Una cuota agotada devuelve 429 con retry-after; indisponibilidad o binding ausente falla cerrado (503). La función SQL de admisión y el DO cubren límites distintos.

### Interfaz interna Worker/DO de cuota

Esta es una interfaz interna entre Pages Functions y el Worker de cuota; no es un endpoint público de la aplicación. `checkAdminQuota` calcula HMAC-SHA256 en el BFF usando `ADMIN_QUOTA_HMAC_KEY` (longitud mínima local 32 caracteres) para no enviar identidades crudas. Pages hace `POST https://admin-quota.internal/check` con `{ "counters": [...] }` vía el service binding `ADMIN_QUOTA`. Cada counter incluye `kind` (uno de `entry`, `login-ip`, `login-account-ip`, `callback`, `mfa`, `password`, `rpc-read`, `rpc-write`), `digest` hex lowercase de 64 caracteres y `shard` opcional del mismo formato. La colección tiene 1–6 counters, máximo 4096 caracteres JSON, sin duplicados por `(kind,digest)`; el par login-account-ip/login-ip debe compartir shard y el Worker rechaza pares incompletos/inconsistentes. El Worker agrupa por shard y reenvía por `POST /check` al Durable Object; DO vuelve a validar el formato y atomiza ledger/alarma transaccionalmente. Para compatibilidad, el Worker puede inferir el shard de login-account-ip a partir del único login-ip cuando falta el campo opcional.

| Respuesta interna | Body/headers | Efecto en BFF |
|---|---|---|
| 200 | `{"allowed":true}`, JSON, `Cache-Control: no-store` | El BFF continúa (`null`, sin respuesta de error). |
| 429 | `{"allowed":false}`, `Retry-After` entero en segundos; el Worker combina los DO bloqueados | El BFF responde 429 `rate_limited` y conserva Retry-After si está entre 1 y 86400. |
| 400 | `{"allowed":false}` para JSON/counters inválidos o demasiado largos | BFF trata cualquier upstream no aceptado como cuota no disponible y falla cerrado con 503. |
| 404 | `{"allowed":false}` para método distinto de POST o path distinto de `/check` | BFF falla cerrado con 503. |
| 503 | `{"allowed":false}`, `Retry-After: 30` ante excepción, fallo de storage o estado inesperado del DO | BFF responde 503 `quota_unavailable`, `Retry-After: 30`. |

Los límites del Worker por identidad son `entry` 300/min; `login-ip` 20/10 min; `login-account-ip`, `callback`, `mfa` y `password` 10/10 min; `rpc-read` 120/min y `rpc-write` 30/min. El DO recibe solo hash de HMAC y no el secreto. El config local declara `workers_dev: false`, `preview_urls: false` y binding interno `ADMIN_QUOTA_COUNTER`; no declara una route pública. Fuentes: `web/functions/_lib/admin-quota.ts:13-45`, `workers/admin-quota/index.ts:13-23,25-43,104-144`, `workers/admin-quota/wrangler.jsonc` y `tests/h3_admin_quota_runtime.mjs`.

### Inventario remoto R15 de Admin

Cloudflare Pages enumeró un preview `desarrollo` con Pages Functions sobre SHA `4eb4…`, pero no el WIP R14. El inventario no mostró `ADMIN_QUOTA`, `ADMIN_QUOTA_HMAC_KEY`, `ADMIN_RPC_GATEWAY_HMAC_KEY` ni `ADMIN_RPC_GATEWAY_KEY_ID`; el Worker `studiamatch-admin-quota`, la clase `AdminQuotaCounter` y namespaces DO esperados tampoco aparecen en la cuenta consultada. `NEXT_SUPABASE_SECRET_KEY` está registrada como binding `plain_text` en preview y producción: solo se leyó el tipo, nunca el valor.

Supabase listó `admin-invite` ACTIVE v12 en Free, cuyo proyecto figura INACTIVE, y no la listó en Pro; Pro listó solo `send-lead-emails` ACTIVE v8 y Free listó esta última v21. No se obtuvo config `verify_jwt`, template Auth, redirects, secrets ni resultado de ejecución. Las lecturas Auth no autenticadas fueron 401/timeout. Estos datos son inventario, no prueba de runtime o de envío. La [evidencia R15](evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md#supabase) separa esas observaciones; el [paquete de integración](evidencia/h3req1_development_integration_package_2026-10-13_r15.md) detalla los permisos requeridos para remediar.

## Consumidores, pruebas y límites

Consumidores del BFF: web/src/lib/admin-auth.ts y rutas/componentes Admin. Consumidor del Edge: endpoint de invitaciones BFF. Consumidor del gateway HMAC: únicamente el canal directo Pages Functions BFF→PostgREST `admin_signed_rpc`; Edge usa RPC de invitación con service role y actor verificado, separado del gateway. Tests principales: tests/test_supabase_credentials_contract.py, test_admin_invite_edge_contract.py, tests H3 de BFF/invitación/MFA, h3_admin_bff_mock_uat.mjs, h3_invitation_uat.mjs, cuotas y harnesses PG17/PostgREST. [R178](evidencia/h3req1_g09_local_close_r178_2026-10-11.md) acredita ejecución local aislada, no la provisión remota.

## Fuentes

web/functions/_middleware.ts, web/functions/_lib/admin-bff.ts (`routeAdminBff`, `routeMutation`), web/src/lib/supabase-transport.ts (`createApiKeyOnlyFetch`, `signAdminRpc`), web/functions/_lib/admin-quota.ts, workers/admin-quota/index.ts, supabase/functions/admin-invite/index.ts, supabase/functions/send-lead-emails/index.ts, supabase/config.toml, web/src/lib/admin-auth.ts, migrations 20260828_h3_*, 20260918_h3_*, 20261002_h3_admin_quota_expand.sql, 20261004_h3_admin_rpc_signed_gateway*.sql.

## Navegación relacionada

[Runtime BFF/Edge/gateway/cuota](componentes/admin_runtime.md) · [Portal Admin](componentes/admin_portal.md) · [Transporte Supabase](componentes/supabase_transport.md) · [Database](database.md) · [Seguridad](seguridad.md) · [Pruebas](pruebas.md) · [Operación](operacion.md) · [Hitos](hitos/README.md) · [Decisiones](decisiones/README.md) · [R178](evidencia/h3req1_g09_local_close_r178_2026-10-11.md) · [Índice](indice.md)

Registro por fuente: [runtime Admin y servicios](trazabilidad/registro_fuentes_componentes.md#runtime-admin) · [utilidades compartidas](trazabilidad/registro_fuentes_componentes.md#utilidades-compartidas).
