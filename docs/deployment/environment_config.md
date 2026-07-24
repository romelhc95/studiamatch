# Configuracion de Ambientes — StudIAMatch

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

Configurar en Cloudflare Dashboard > Workers & Pages > studiamatch > Settings > Environment variables:

| Variable | Desarrollo | Certificacion | Produccion |
|---|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://YOUR_FREE_PROJECT_REF.supabase.co` | `https://YOUR_FREE_PROJECT_REF.supabase.co` | `[URL_PRO_PENDIENTE]` |
| `NEXT_SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_...` de Free | `sb_publishable_...` de Free | `sb_publishable_...` de Pro |
| `NODE_VERSION` | `20` | `20` | `20` |

Las variables se inyectan en build time (`npm run build` → `output: export`).

### GitHub Actions (Pipelines)

Configurar en GitHub > Settings > Environments:

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

### Pro tier (Produccion — `[PENDIENTE R6]`)
| Key | Valor |
|---|---|
| URL | `[URL_PRO_PENDIENTE]` |
| Publishable Key | Ver `.env.gitprod` |
| Secret Key | Ver `.env.gitprod` |

## Verificacion

Para diagnosticar si un ambiente apunta al proyecto correcto:

```bash
# Desde el navegador, abrir DevTools y ejecutar:
fetch('https://URL_SUPABASE/rest/v1/courses?select=count&is_active=eq.true', {
  headers: { 'apikey': 'ANON_KEY', 'Prefer': 'count=exact' }
}).then(r => console.log(r.headers.get('content-range')))

# Debe retornar: 0-647/648  (648 cursos)
```

Si retorna un numero diferente, el ambiente esta apuntando a un proyecto incorrecto.

## Problemas conocidos

### "0 Programas" en produccion
Si `www.studiamatch.com` muestra 0 resultados, verificar:
1. `NEXT_PUBLIC_SUPABASE_URL` en Cloudflare Pages apunta al proyecto Pro correcto
2. `NEXT_SUPABASE_PUBLISHABLE_KEY` es la `sb_publishable_...` de Pro (NO la secret key)
3. RLS en Pro permite SELECT anon en la tabla `courses`
4. Re-ejecutar el build (las env vars se incrustan en build time)

### Discrepancia de cursos (185 vs 600+)
Si local muestra menos cursos que la web:
1. Verificar que `web/.env.local` apunta al proyecto correcto
2. Ejecutar `rm -rf .next` y reiniciar `npm run dev`
3. Comparar el content-range del fetch desde el navegador

### Static export y env vars
`NEXT_PUBLIC_*` se incrusta en el JS en build time. Para cambiar la URL de Supabase se requiere un nuevo build.
