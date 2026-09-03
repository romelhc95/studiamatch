# Evidencia JIT-B — Cloudflare Access/DNS `admin.studiamatch.com`

- **Fecha**: 2026-09-03 (UTC; corridas sobre zona activa)
- **Autorización**: humana — `Aprobar JIT-B y ejecutar ahora` (respuesta a opciones) + aprobación expresa vía pregunta.
- **Cuenta/IDs**: zone `studiamatch.com` = `a257c08d403e2402cdc27a73c8ddd969` (active, full); Pages project `studiamatch` (subdomain `studiamatch-aty.pages.dev`, prod branch `main`, dominios previos `www.studiamatch.com` + pages.dev); Zero Trust IdP built-in type `cloudflare` = `c7d805a1-092a-4f25-843b-bebc031f0b00`.
- **Entorno**: token nuevo `CF_JIT_TOKEN` inyectado en `.env.local` del contenedor por el humano. El `CF_API_TOKEN` legacy (Workers AI) no alcanza: `403 9109 Invalid access token` en `/zones` (hallazgo de credenciales).

## Preflight 6.1 (read-only)
- Zona activa; Pages `studiamatch` confirmado; **no existía** hostname/app `admin.studiamatch.com`.
- Apps Access existentes (intocadas): App Launcher `05c81876-…`, `omni` self-hosted `ce7bea5f-…` (omni.studiamatch.com).
- IdPs: solo built-in `cloudflare` (login OTP por email). Sin permiso `Identity Providers: Write` en el token → no se creó IdP `onetimepin` formal; la allowlist se hizo por selector `email` sobre el built-in OTP.

## 6.2 DNS + custom domain
- Custom domain Pages: **`admin.studiamatch.com`** id `f78c1ba5-96aa-4894-8000-c6c63b03a3a2` → estado **active** (verification active; cert Google CA active; `created_on 2026-09-03T00:05:48Z`).
- DNS: CNAME `admin.studiamatch.com` → `studiamatch-aty.pages.dev`, proxied, id `d5ee0c4c1623182f2ce6ef251f8cb03c` (creado manualmente; Pages pidió "CNAME record not set").
- Smoke resuelve: `https://admin.studiamatch.com/` pasó a ser interceptado por Access.

## 6.4 Cloudflare Access (MFA perímetro)
- Access app self-hosted **StudIAMatch Admin (JIT-B)**: id `803f615f-7c2d-4a3d-b99c-b9ab43f543a2`, domain `admin.studiamatch.com`.
- Policy única en la app: id `36eb2dfc-c8ce-4dff-9c27-ce7dfff0e692`, nombre `JIT-B perimeter MFA (OTP 1h)`, decision `allow`, precedence `1`, `session_duration` `1h` (modificable en Zero Trust → Access → Apps → StudIAMatch Admin), include = `email romelhc95@gmail.com` (login One-time PIN del built-in OTP).
- Nota de proceso: tras 2 intentos de creación rechazados por la API (regla `identity_provider` no válida; precedencia duplicada), la policy correcta apareció ya creada en la app (autoría en paralelo Dashboard humano probable); se verificó que es **única** y con la config correcta.

## Smoke perimetral (E-matrix)
| # | Prueba | Resultado |
|---|---|---|
| E1 | `https://admin.studiamatch.com/admin/` sin sesión | **302** → `weathered-firefly-d5f4.cloudflareaccess.com/cdn-cgi/access/login/admin.studiamatch.com?…&redirect_url=/admin/` (PASS) |
| E3 | `https://www.studiamatch.com/admin/` (host público real) | **404** hoy (PASS actual: main no exporta `/admin`; ver riesgo) |
| E4 | `https://www.studiamatch.com/` | **200** (PASS, sin regresión) |
| E8 | Segunda corrida NOOP (E1b/E3b/E4b) | Idéntico: 302/404/200 (sin drift) |

## Hallazgos y pendientes (bloqueos)
1. **Apex `studiamatch.com` sin registros web** (solo MX/TXT): el público servido hoy es `www.studiamatch.com`. Drift vs AGENTS (main → `studiamatch.com`). No modificado (fuera de alcance JIT-B); requiere decisión de despliegue (apex a Pages/redirect).
2. **E3 404 es coyuntural**: al promover H3 (panel `/admin`) a `main`, el export estático volvería a servir `/admin` públicamente. Requiere el **build 404** (Pages Function/Worker) autorizado por la frase de build pendiente antes de esa promoción.
3. **E2/E5/E6/E7 pendientes**: requieren (a) sesión Access interactiva — OTP al correo `romelhc95@gmail.com`; (b) build de la Edge Function de invitación (H3-CA4.8) + 404; (c) config Auth Supabase (Site URL `https://admin.studiamatch.com`, redirects) vía Dashboard/Management API (sin token en entorno). JIT-B queda **parcial** vs E2/E5; el perímetro (E1/E3/E4/E8) queda validado.
4. Entorno Pages/GitHub `Development`/`Certification`: variables apuntando a `admin.studiamatch.com` son writes de entorno → requieren aprobación aparte.

## Alcance respetado
Custom domain + Access app/policy + smoke. **Sin** cambios de código de aplicación, sin push/PR/merge, sin deploy de producción, sin tocar apps existentes (`omni`, App Launcher).
