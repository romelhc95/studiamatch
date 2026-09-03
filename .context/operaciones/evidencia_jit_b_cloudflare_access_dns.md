# Evidencia JIT-B — Cloudflare Access/DNS por ambiente

- **Fecha**: 2026-09-03 (UTC; corridas sobre zona activa)
- **Autorización**: humana — `Aprobar JIT-B y ejecutar ahora` (respuesta a opciones) + aprobación expresa vía pregunta.
- **Cuenta/IDs**: zone `studiamatch.com` = `a257c08d403e2402cdc27a73c8ddd969` (active, full); Pages project `studiamatch` (subdomain `studiamatch-aty.pages.dev`, `production_branch=main`, dominios `admin.studiamatch.com`, `www.studiamatch.com` y pages.dev); Zero Trust IdP built-in type `cloudflare` = `c7d805a1-092a-4f25-843b-bebc031f0b00`.
- **Contrato de ambientes corregido**: `studiamatch.com`/`www.studiamatch.com` = público de producción (`main`); URL de commit `88f02c53.studiamatch-aty.pages.dev` = preview reproducible del commit `e3d21c1` de `desarrollo`; `admin.studiamatch.com` no representa el preview de `desarrollo` y debe reservarse para el panel de producción una vez separado el proyecto/artefacto administrativo.
- **Entorno**: token nuevo `CF_JIT_TOKEN` inyectado en `.env.local` del contenedor por el humano. El `CF_API_TOKEN` legacy (Workers AI) no alcanza: `403 9109 Invalid access token` en `/zones` (hallazgo de credenciales).

## Preflight 6.1 (read-only)
- Zona activa; Pages `studiamatch` confirmado; **no existía** hostname/app `admin.studiamatch.com`.
- Apps Access existentes (intocadas): App Launcher `05c81876-…`, `omni` self-hosted `ce7bea5f-…` (omni.studiamatch.com).
- IdPs: solo built-in `cloudflare` (login OTP por email). Sin permiso `Identity Providers: Write` en el token → no se creó IdP `onetimepin` formal; la allowlist se hizo por selector `email` sobre el built-in OTP.

## 6.2 DNS + custom domain
- Custom domain Pages: **`admin.studiamatch.com`** id `f78c1ba5-96aa-4894-8000-c6c63b03a3a2` → estado **active** (verification active; cert Google CA active; `created_on 2026-09-03T00:05:48Z`).
- DNS: CNAME `admin.studiamatch.com` → `studiamatch-aty.pages.dev`, proxied, id `d5ee0c4c1623182f2ce6ef251f8cb03c` (creado manualmente; Pages pidió "CNAME record not set").
- **Interpretación corregida**: este custom domain pertenece al proyecto Pages único cuya rama de producción es `main`; no es un alias de la preview `desarrollo`. No debe usarse para certificar `desarrollo`.
- Smoke sin sesión: `https://admin.studiamatch.com/` fue interceptado por Access; esto prueba el perímetro, no que el artefacto servido pertenezca a la rama bajo prueba.

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
2. **E3 404 es coyuntural**: la URL `88f02c53.studiamatch-aty.pages.dev` se usa únicamente como preview reproducible de `desarrollo`; no se mezcla con `admin.studiamatch.com`. Al promover H3 (panel `/admin`) a `main`, al promover H3 (panel `/admin`) a `main`, el export estático volvería a servir `/admin` públicamente. Requiere el **build 404** (Pages Function/Worker) autorizado por la frase de build pendiente antes de esa promoción.
3. **E2/E5/E6/E7 pendientes**: requieren (a) sesión Access interactiva; (b) build de la Edge Function de invitación (H3-CA4.8) + 404; (c) config Auth Supabase por ambiente; (d) una URL administrativa que apunte al deployment de la rama bajo prueba. La prueba Google con `romelhc95@gmail.com` ya superó `membership_restricted`, pero no certificó el artefacto correcto de `desarrollo`. JIT-B queda **parcial** vs E2/E5; el perímetro E1/E3/E4/E8 queda validado en el alcance indicado.
4. Entorno Pages/GitHub `Development`/`Certification`: variables apuntando a `admin.studiamatch.com` son writes de entorno → requieren aprobación aparte.

## Estado sincronizado para el PR
El PR incorpora exclusivamente documentación, el delta SQL `20260903` y la regresión PG17. La evidencia de este documento sigue siendo parcial y no se eleva a PASS global: E1/E3/E4/E8 están validados sobre el hostname administrativo existente; E2/E5/E6/E7 deben repetirse sobre el deployment correcto de cada ambiente y requieren pasos remotos o de build independientes. El 404 E3 observado sobre `www.studiamatch.com` es coyuntural hasta instalar el mecanismo estable por hostname.

## Corrección recomendada de ambientes
1. Mantener `studiamatch.com` y `www.studiamatch.com` como público de producción de `main`.
2. Usar la URL de commit de Pages para evidencia inmutable de `desarrollo`; si Pages expone alias estable de rama, documentar el alias real generado, sin inventarlo.
3. Crear un proyecto/artefacto administrativo separado para `admin.studiamatch.com` apuntando a `main`, protegido por Access en todo el hostname.
4. Crear un hostname administrativo/preview separado para `desarrollo` y otro para `certificacion`, cada uno con su propia policy Access, Supabase project ref y evidencia.
5. Antes de cualquier promoción, probar que el público no contiene `/admin` y que los tres ambientes administrativos apuntan al SHA/deployment esperado.

## Hallazgo posterior a la aceptación del miembro Cloudflare
- El miembro `romelhc95@gmail.com` quedó en estado `accepted` con rol `Minimal Account Access`; el error `membership_restricted` dejó de producirse al iniciar el IdP Cloudflare.
- La app se pudo atravesar hasta el origen, pero el hostname administrativo pertenece al proyecto Pages único de producción; el despliegue de `desarrollo` se valida por su URL de preview. El snapshot del Pages project conserva `production_branch=main` y los dominios `admin.studiamatch.com`, `www.studiamatch.com` y `studiamatch-aty.pages.dev` en el proyecto único.
- La URL de commit `88f02c53.studiamatch-aty.pages.dev` corresponde a la preview de `desarrollo` (`e3d21c1`), no a `admin.studiamatch.com`. No debe usarse el dominio custom de producción para validar una rama preview.
- La ruta `admin.studiamatch.com/admin/` y `/admin/login/` fueron observadas posteriormente con el layout público/404, mientras la preview de commit expone el panel. Esto confirma que el custom domain no es la URL de la rama `desarrollo` y que el artefacto/deployment administrativo debe separarse antes de la UAT completa; no es un fallo de membresía Cloudflare.

## Próximos pasos correctivos documentados

- **C1 — Separación Pages**: decidir y ejecutar, con aprobación de infraestructura, proyecto administrativo separado o artefactos public/admin separados. No reutilizar `admin.studiamatch.com` para una preview de rama.
- **C2 — Hostnames**: definir y registrar `production → main`, `development → preview de desarrollo`, `certification → preview de certificación`, incluyendo deployment ID, SHA y Supabase ref.
- **C3 — Access**: mantener `admin.studiamatch.com` para producción; crear policies/app específicas para los hostnames no productivos y proteger también el dominio Pages directo si puede bypassar el custom domain.
- **C4 — 404 público**: implementar y probar el mecanismo estable para apex, `www` y Pages público antes de promover rutas `/admin` a `main`.
- **C5 — UAT**: repetir E1–E8 por ambiente; E2/E5/E6/E7 solo se marcan PASS cuando el login y el panel correspondan al SHA/deployment esperado.
- **C6 — Configuración Auth**: usar Site URL/redirects y keys del proyecto Supabase correspondiente al ambiente; no cruzar Development, Certification y Production.

## Alcance respetado
La ejecución JIT-B ya realizada fue custom domain + Access app/policy + smoke, sin cambios de código de aplicación, sin push/PR/merge, sin deploy de producción y sin tocar apps existentes (`omni`, App Launcher). El PR actual añade únicamente el delta correctivo versionado, los tests del contrato y documentación; no autoriza acciones remotas posteriores.

## Registro de decisión de ambientes
La imagen/observación de Pages confirma el modelo correcto: `main` es Production y `desarrollo` genera una Preview independiente. `88f02c53.studiamatch-aty.pages.dev` es la URL de commit de `desarrollo` y sirve para evidencia reproducible. No se antepone `admin` a `studiamatch.com` para validar desarrollo: `admin.studiamatch.com` debe reservarse para el panel protegido de producción; desarrollo y certificación requieren hostnames/targets administrativos propios o una separación de proyectos/artefactos antes de UAT completa.
