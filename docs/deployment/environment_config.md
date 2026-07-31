# Configuracion de Ambientes — StudIAMatch

> Estado vigente: referencia historica no operativa. La autoridad actual esta en `.context/estado_del_proyecto.md` y `.context/operaciones/flujo_release_minimo.md`. Free es el ambiente DB de desarrollo/certificacion del contrato; `certificacion` como rama/release, Pro, `main`, Production y Cloudflare manual permanecen bloqueados hasta sus gates.

## Arquitectura de ambientes

| Ambiente | Rama Git | URL | Supabase Proyecto | DB |
|---|---|---|---|---|
| Ambiente | Rama Git | URL | Supabase Proyecto | DB |
|---|---|---|---|---|
| Desarrollo | `desarrollo` | `https://desarrollo.studiamatch.pages.dev` | `YOUR_FREE_PROJECT_REF` | Free |
| Certificacion | `certificacion` | `https://studiamatch.pages.dev` | `YOUR_FREE_PROJECT_REF` | Free |
| Produccion | `main` | `https://www.studiamatch.com` | `[PENDIENTE - CREAR EN R6]` | Pro |
| Local | N/A | `http://localhost:3000` | `YOUR_FREE_PROJECT_REF` | Free |

## Variables de entorno requeridas por ambiente

### Cloudflare Pages (Desarrollo, Certificacion y Produccion)

No configurar en Cloudflare Dashboard desde este documento. Cualquier cambio de Workers & Pages, variables o dominios requiere la autorizacion vigente del flujo release.

| Variable | Desarrollo | Certificacion | Produccion |
|---|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://YOUR_FREE_PROJECT_REF.supabase.co` | `https://YOUR_FREE_PROJECT_REF.supabase.co` | `[URL_PRO_PENDIENTE]` |
| `NEXT_SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_...` de Free | `sb_publishable_...` de Free | `sb_publishable_...` de Pro |
| `NODE_VERSION` | `20` | `20` | `20` |

Las variables se inyectan en build time (`npm run build` → `output: export`).

### GitHub Actions (Pipelines)

No configurar GitHub Environments ni secrets desde este documento; la tabla es historica y no operativa.

| Environment | Secret | Valor |
|---|---|---|
| Development | `SUPABASE_URL` | `https://YOUR_FREE_PROJECT_REF.supabase.co` |
| Development | `NEXT_SUPABASE_SECRET_KEY` | `sb_secret_...` de Free (para escritura pipeline) |
| Development | `NEXT_SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_...` de Free (para lectura frontend) |
| Certification | `SUPABASE_URL` | `https://YOUR_FREE_PROJECT_REF.supabase.co` |
| Certification | `NEXT_SUPABASE_SECRET_KEY` | `sb_secret_...` de Free |
| Certification | `NEXT_SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_...` de Free |
| Production | `SUPABASE_URL` | `[URL_PRO_PENDIENTE]` |
| Production | `NEXT_SUPABASE_SECRET_KEY` | `sb_secret_...` de Pro |
| Production | `NEXT_SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_...` de Pro |

### Local (Docker + Next.js dev)

**Python scripts** (usan `.env.local` en raiz del proyecto):
- `NEXT_PUBLIC_SUPABASE_URL` → Free tier
- `NEXT_SUPABASE_PUBLISHABLE_KEY` → `sb_publishable_...` (lectura)
- `NEXT_SUPABASE_SECRET_KEY` → `sb_secret_...` (escritura pipeline)

**Frontend Next.js** (usa `web/.env.local`):
- `NEXT_PUBLIC_SUPABASE_URL` → Free tier
- `NEXT_SUPABASE_PUBLISHABLE_KEY` → `sb_publishable_...` (lectura)

## Claves Supabase

### Free tier (Desarrollo — `YOUR_FREE_PROJECT_REF`)
| Key | Valor |
|---|---|
| URL | `https://YOUR_FREE_PROJECT_REF.supabase.co` |
| Publishable Key | Ver `.env.local` |
| Secret Key | Ver `.env.local` |

### Pro tier (Produccion — bloqueado)
| Key | Valor |
|---|---|
| URL | Bloqueado; no registrar ni configurar desde este documento |
| Publishable Key | Bloqueado; no registrar ni configurar desde este documento |
| Secret Key | Bloqueado; no registrar ni configurar desde este documento |

## Verificacion

Los diagnosticos remotos desde navegador quedan retirados de este documento. Usar solo gates autorizados, evidencia sanitizada y scripts aprobados por la fase vigente.

## Problemas conocidos

### "0 Programas" en produccion
Si `www.studiamatch.com` muestra 0 resultados, verificar:
1. No diagnosticar Production/Pro desde este documento.
2. Consultar el flujo vigente y solicitar autorizacion F10/F11 si corresponde.

### Discrepancia de cursos (185 vs 600+)
Si local muestra menos cursos que la web:
1. Usar el procedimiento vigente en contenedor y sin exponer URLs, keys ni conteos sensibles.

### Static export y env vars
`NEXT_PUBLIC_*` se incrusta en el JS en build time. Para cambiar la URL de Supabase se requiere un nuevo build.
