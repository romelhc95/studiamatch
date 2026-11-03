# Borrador técnico: BFF y sesión Admin HttpOnly para H3REQ1

> **DISEÑO HISTÓRICO PROPUESTO 2026-10-01; no inventario del código actual.**
> La implementación candidata posterior vive en middleware/BFF/transporte y usa SSR
> HttpOnly. No crear las rutas propuestas ni rehacer el diseño por leer los supuestos
> siguientes. Contrastar el código con la [ficha vigente de runtime Admin](../componentes/admin_runtime.md)
> y la [arquitectura del sistema](../arquitectura.md),
> [evidencia BFF](../evidencia/h3req1_bff_local_cycle_2026-10-02.md) y
> [estado](../estado_del_proyecto.md); no implica adopción remota ni autorización.

**Fecha:** 2026-10-01  
**Estado:** `SCOPE_ATTESTED_LOCAL_DESIGN_ONLY_TECHNICAL_VALIDATION_PENDING`  
**Autoridad:** el estado vivo permanece en [`estado_del_proyecto.md`](../estado_del_proyecto.md).  
**Importante:** el alcance está atestado en la evidencia sanitizada versionada; este documento sigue siendo una propuesta técnica por validar. No es waiver y no autoriza SQL/DDL remoto, Preview, Auth remoto, deploy, push ni PR.

## 1. Propósito y hallazgo

El candidato actual configura Supabase Auth para persistir la sesión en el
navegador y cambia la migración desde `sessionStorage` hacia `localStorage` para
compartir sesiones entre pestañas. Ambos storages son legibles por JavaScript; el
segundo además amplía persistencia y superficie cross-tab. La revisión de seguridad
read-only clasificó esta exposición como **HIGH**, sin waiver aprobado.

El objetivo de diseño es que el navegador nunca reciba ni persista los access o
refresh tokens de Admin. El frontend conserva el static export actual y envía
operaciones Admin same-origin a un Backend-for-Frontend (BFF) en Cloudflare Pages
Functions. Supabase Auth y PostgREST reciben el JWT de usuario únicamente desde el
runtime servidor. Las lecturas públicas del catálogo no requieren migrar al BFF.

HttpOnly reduce la posibilidad de exfiltrar y reutilizar tokens desde JavaScript,
pero no impide que un XSS activo emita operaciones same-origin mientras la víctima
tiene sesión. CSP, escape/validación de entradas, verificación de autorización en el
servidor y protección de sesión siguen siendo necesarios.

## 2. Hechos del checkout y supuestos por validar

- `web/next.config.js` usa `output: 'export'`; por tanto, no se debe basar el diseño
  en Route Handlers, Server Actions ni SSR de Next sin cambiar y revalidar ese
  contrato.
- Existe `web/functions/_middleware.ts`; actualmente restringe host para rutas
  `/admin*`, no para rutas `/api/admin*`. No hay en el checkout una ruta BFF Admin.
- `web/src/lib/admin-auth.ts` usa el cliente Auth del navegador para login,
  callbacks, sesión, recuperación, cambio de contraseña y MFA. También llama RPCs
  administrativos y `admin-invite` desde el navegador.
- `web/src/lib/supabase.ts` configura `persistSession: true` y almacenamiento
  browser compartido. El catálogo público utiliza además lecturas PostgREST con la
  publishable key.
- No se ha acreditado en este ciclo que la configuración de Cloudflare Pages
  empaquete una carpeta nueva `web/functions/api/admin/` junto con `web/out/`. La
  raíz de Pages, el comando de publicación y sus bindings son un gate de diseño,
  no una suposición.
- La plantilla Auth local actual y el formato real de los enlaces de invitación y
  recovery deben inventariarse sin exponer enlaces, tokens, PII ni contenido
  privado. No se inspeccionó ni modificó la configuración remota.

## 3. Arquitectura objetivo propuesta

### 3.1 Superficies

1. **Static export:** la UI Admin permanece prerenderizada. Sus llamadas de
   autenticación/administración pasan a endpoints same-origin bajo
   `/api/admin/...`; no se crean rutas dinámicas de Next.
2. **Pages Functions BFF:** funciones pequeñas y explícitas para sesión, login,
   callback Auth, MFA, logout, RPCs allowlisted y envío de invitaciones. No crear un
   proxy genérico que acepte paths, funciones RPC, URLs o métodos arbitrarios del
   cliente.
3. **Supabase público:** home, catálogo, comparación y detalle pueden conservar
   `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` en `apikey` para lecturas sujetas a RLS.
   El cliente público no persiste una sesión Admin.
4. **Supabase Auth/PostgREST/Edge:** el BFF obtiene la sesión desde la cookie,
   valida la identidad contra Auth y reenvía únicamente operaciones explícitas.
   No se envían API keys como `Authorization: Bearer`, no se coloca una secret key
   en el bundle y no se sustituye la identidad del usuario por `service_role`.
   La excepción humana aprobada permite que el cliente Auth server-side envíe el JWT
   de sesión del usuario como Bearer solo a RPCs allowlisted de `/rest/v1/rpc/*`;
   `apikey` conserva la publishable key. Esta excepción se inventaría y prueba en
   `tests/test_supabase_credentials_contract.py`; no se amplía a rutas arbitrarias.

### 3.2 Cookie y almacenamiento

- Solo el servidor crea, renueva y elimina la cookie; el cliente no usa
  `document.cookie` para representar una sesión autenticada.
- Cookie de host, `HttpOnly`, `Secure`, `Path=/`, sin atributo `Domain` y con
  `SameSite` definido tras probar callbacks top-level. `Lax` es el punto inicial
  de evaluación para callbacks desde correo; `Strict` solo si PKCE/invitación y
  recovery continúan funcionando sin excepción. Mutaciones requieren además
  validación CSRF/Origin explícita.
- Evaluar primero `@supabase/ssr` y su adapter de cookies en el runtime Workers de
  Pages. Validar compatibilidad, refresh, chunking y atributos HttpOnly con el
  lockfile actual antes de decidir dependencia. Si el adapter no cumple, detenerse
  y diseñar la alternativa; no escribir criptografía de sesión ad hoc.
- Comparar dos almacenamientos server-side antes de fijar contrato: (A) sesión
  Supabase en cookies HttpOnly manejadas por SSR; (B) cookie opaca con sesión en
  Durable Object. B reduce datos de sesión en el cliente, pero agrega bindings,
  lifecycle, revocación y coordinación de refresh; no asumir que Durable Objects
  estén configurados.
- Ninguna respuesta JSON, URL, fragmento, log, analítica o error del BFF contiene
  access/refresh tokens. Un endpoint de estado puede devolver solo datos mínimos
  para UI (autenticado, rol autorizado, AAL y expiración aproximada).
- Preservar el timeout Admin de inactividad vigente (30 min) con enforcement en
  servidor además de la UX. BroadcastChannel puede comunicar actividad/logout entre
  pestañas; `localStorage` solo podría guardar una señal no secreta y nunca tokens.

### 3.3 Contrato de endpoints candidato

Los nombres son una propuesta para revisión, no rutas autorizadas ni implementadas.

| Endpoint | Función | Controles mínimos |
|---|---|---|
| `POST /api/admin/auth/login` | Recibir credenciales y autenticar servidor a servidor | Schema/tamaño, TLS, rate limit, Origin, errores sanitizados; no devolver tokens. |
| `GET /api/admin/auth/callback` | Completar invitación/recovery/PKCE y emitir cookie | Aceptar solo formatos aprobados, validar estado/OTP, `no-store`, no loguear query, redirect local allowlisted y limpiar URL con 303. |
| `GET /api/admin/session` | Consultar estado mínimo de sesión | Verificar Auth remoto; no devolver JWT, refresh token ni claims sin validar. |
| `POST /api/admin/auth/mfa/*` | Listar/enrolar/verificar/retirar TOTP y consultar AAL | User activo; AAL requerido para operaciones sensibles; QR/secret TOTP solo durante enrolamiento autorizado. |
| `POST /api/admin/rpc/<allowlisted-name>` | Ejecutar RPC Admin/editorial existente | Allowlist por RPC/método/rol; body Zod-equivalente; verificar usuario, membresía activa y AAL2; pasar JWT del usuario, nunca service role. |
| `POST /api/admin/invitations` | Invocar Edge `admin-invite` desde el BFF | Caller autenticado; Origin/CSRF; sesión AAL2; sin permitir cambiar proyecto/URL/redirect desde el navegador. |
| `POST /api/admin/auth/logout` | Revocar sesión según contrato y limpiar cookie | Respuesta no-cache; revocación confirmada; limpiar expiración/estado idle server-side. |

La allowlist de RPC debe derivarse de llamadas reales en `admin-auth.ts`, cola,
editor y usuarios; incluir `admin_current_user_role`, onboarding, queue facets,
editor/audit/availability, actualización de miembros y acciones de publicación
que correspondan. No aceptar un `functionName` libre del cliente.

### 3.4 Identidad, MFA y autorización

- No confiar en `getSession()` local, rol enviado por UI, `aal` decodificado desde
  un token no verificado ni en la cookie indicadora legible actual.
- Para operaciones, validar el usuario con Supabase Auth desde el BFF; obtener
  membresía/rol mediante el contrato RPC vigente y comprobar `active/ready`.
- Mantener `aal2` para operaciones que hoy lo exigen. Login AAL1 puede crear un
  estado restringido para terminar challenge, pero no acceder a RPC/editor/invite
  protegidos hasta verificar AAL2 en servidor.
- El BFF debe conservar `admin_require_aal2`, RBAC y checks de membresía en SQL;
  el proxy no reemplaza los controles de base de datos.
- El secreto de servicio no debe usarse para hacer RPCs que requieren identidad de
  usuario. `admin-invite` conserva su responsabilidad server-side actual; si el
  BFF lo llama, transmite el contexto autenticado mediante el contrato HTTP
  permitido e inventariado.

### 3.5 CSRF, host y hardening

- Same-origin sin CORS abierto. Rechazar `Origin` distinto al host Development
  aprobado y validar `Sec-Fetch-Site` como señal adicional; no como único control.
- Cookie `SameSite` no sustituye CSRF para mutaciones. Usar token CSRF ligado a la
  sesión o mecanismo equivalente, validar Origin en cada POST/PUT/PATCH/DELETE,
  permitir `Content-Type: application/json` únicamente y limitar tamaño del body.
- Aplicar rate limit a login, callbacks/OTP, recovery, invitaciones y MFA; no
  exponer si una cuenta existe. Evitar redirects configurables por payload.
- Extender el perímetro de `web/functions/_middleware.ts` para proteger `/api/admin`
  con el mismo host allowlist que `/admin`; separar host de producción y Preview.
  La validación de host es perímetro, no autorización de usuario.
- Revisar CSP y dependencias cargadas por el panel. BFF/HttpOnly reduce robo
  persistente de tokens, pero XSS todavía puede operar same-origin mientras una
  víctima tenga sesión.

## 4. Transición transparente

| Fase | Propuesta y gate |
|---|---|
| **Expand** | Añadir funciones BFF y contratos mock sin retirar RPC/Auth legacy. Confirmar empaquetado local de Pages Functions junto a static export. Ninguna llamada usa secretos del browser. |
| **Compatibilidad** | Habilitar BFF solo en Development/Preview aprobado; preservar pantallas, roles, MFA y legacy necesario. No copiar tokens de `sessionStorage` a `localStorage`. Expirar/limpiar el token legacy del navegador y pedir login/MFA con la cuenta existente; no canjear tokens legacy, crear otra cuenta, reinvitar ni repetir onboarding. |
| **Deploy** | Solo SHA exacto y hostname aprobado, con JIT de Preview independiente. Verificar cookie, login existente, MFA AAL1/AAL2, RBAC, callbacks, RPCs, expiry/logout, URLs y perímetro. No probar correo ni Auth writes sin JIT específico. |
| **Contract** | Tras estabilidad acreditada, eliminar Auth browser-side, migración de tokens a storage JS y endpoints legacy. Mantener una ruta de rollback segura; no fallback silencioso a `localStorage`. |
| **Rollback** | Deshabilitar el BFF candidato o volver a una versión compatible preservando el perímetro; decidir cómo se invalidan/limpian cookies. No volver a publicar tokens en storage JS sin waiver temporal específico y aprobación humana. |

## 5. Matriz de pruebas requerida

### Locales, sin credenciales reales

1. Unit/contract de cookie: HttpOnly/Secure/Path/SameSite/host-only, expiración,
   rotación, revocación y ausencia de tokens en JSON, logs, URL y Web Storage.
2. Auth mock: password correcto/incorrecto, refresh concurrente, sesión expirada,
   logout, OTP de invitación/recovery, enlace inválido/reutilizado y redirect
   externo rechazado.
3. MFA/RBAC: AAL1 rechazado en cada endpoint sensible; AAL2 permitido solo con
   Admin activo/ready; `user`, membresía inactiva, anónimo y sesión revocada
   denegados según el contrato. No confiar en rol/AAL de cliente.
4. CSRF/Origin: origen ajeno, `Origin` ausente cuando aplica, content-type
   incorrecto, body enorme, método/RPC no permitido, rate limit y request repetido.
5. UI/browser: login, invitación, password setup/recovery, MFA, edición y sesión
   cross-tab; Playwright confirma que no aparecen access/refresh tokens en
   `localStorage`, `sessionStorage`, respuestas ni URLs.
6. Worker/runtime: probar `wrangler pages dev` o el mecanismo real del proyecto;
   documentar cómo conviven `functions/` y el static export. Reejecutar H3 PG17,
   TypeScript, lint, build normal/mock, writer scan, credential scan y actionlint/
   shellcheck sobre el candidato exacto.

### Remotos — cada gate requiere JIT propio

- Preflight Free/Development read-only y baseline del SHA candidato.
- Aplicar migraciones/DDL solo con JIT DDL que liste archivos y hashes exactos.
- Preview solo con JIT que identifique SHA, proyecto, hostname y rutas.
- UAT Admin existente, MFA, H3-003 por roles/auditoría y H3-004 de compatibilidad,
  ruta estática elegible, rollback y contract; Auth/correo, cleanup y rollback
  requieren autorizaciones independientes cuando muten.

## 6. Hallazgos relacionados que no resuelve el BFF

1. El integrity gate no puede considerar seguro que un PR modifique su propia
   definición/allowlist de `security-audit.yml`. Diseñar una validación confiable
   desde el baseline protegido y un flujo separado/revisado para cambiar el gate.
2. Revisar la máquina de estados de invitación para reservar/serializar el intento
   antes de llamar Auth, conservar idempotencia y registrar una compensación única
   ante fallo; sumar prueba de concurrencia. No desplegar ni enviar correo durante
   estas pruebas locales.
3. Decisión humana sanitizada: evidencia de disponibilidad con máximo global de 90
   días calendario desde `observed_at`; `valid_until` no puede superar ese límite.
   Ausencia, invalidez o vencimiento conserva `unknown`. El gate local debe probar
   límites inclusivos/exclusivos y UTC antes de cualquier operación remota.
4. Limitar redirect a `http` solo para loopback aprobado y `https` para otros hosts;
   autenticar/validar método y tamaño de entrada antes de parseo costoso.

## 7. Decisiones y gates pendientes

| Decisión/gate | Responsable | Estado |
|---|---|---|
| Atestación sanitizada que incluya BFF/HttpOnly, MFA, callbacks, sesión y transición | Responsable/cliente | **Contenido resuelto localmente**; el archivo aún no está committed/versionado en Git. |
| Migración de sesión existente | Responsable técnico + UX | **RESUELTO:** expirar/limpiar token legacy y reautenticar cuenta/MFA existente; no crear usuario ni repetir onboarding. |
| Cookie adapter y compatibilidad Workers/Pages Functions + static export | Ingeniería | POC local sin secretos; **PENDIENTE**. |
| Vigencia máxima de evidencia editorial | Dueño de producto | **RESUELTO:** global, máximo 90 días calendario desde `observed_at`. |
| Clasificador semántico automático | Responsable/cliente | **NO requerido este ciclo**; revisión Admin de faltantes/diferencias. Requiere atestación nueva si se propone luego. |
| Protección confiable del workflow de seguridad | Maintainer/DevOps | **PENDIENTE; bloquea PR.** |
| JIT para Free/Preview/Auth/deploy/cleanup/rollback | Responsable humano por operación | **PENDIENTES e independientes.** |

**Salida propuesta:** el alcance ya permite continuar con diseño técnico y cambios
locales; antes de PR deben validarse el adapter/runtime, resolver el HIGH, corregir
el workflow y revalidar sobre un diff acotado. Este borrador no cambia el estado
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` ni concede JIT remoto.
