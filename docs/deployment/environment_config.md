# Configuracion de Ambientes — StudIAMatch

## Arquitectura de ambientes

| Ambiente | Rama Git | URL | Supabase Proyecto | DB |
|---|---|---|---|---|
| Desarrollo | `desarrollo` | `https://desarrollo.studiamatch.pages.dev` | `fmcxwoqvxatbrawwtqke` | Free |
| Certificacion | `certificacion` | `https://studiamatch.pages.dev` | `fmcxwoqvxatbrawwtqke` | Free |
| Produccion | `main` | `https://www.studiamatch.com` | `zogdcvlqxanzqbvkkdar` | Pro |
| Local | N/A | `http://localhost:3000` | `fmcxwoqvxatbrawwtqke` | Free |

## Variables de entorno requeridas por ambiente

### Cloudflare Pages (Desarrollo, Certificacion y Produccion)

Configurar en Cloudflare Dashboard > Workers & Pages > studiamatch > Settings > Environment variables:

| Variable | Desarrollo | Certificacion | Produccion |
|---|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://fmcxwoqvxatbrawwtqke.supabase.co` | `https://fmcxwoqvxatbrawwtqke.supabase.co` | `https://zogdcvlqxanzqbvkkdar.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Clave anon de Free | Clave anon de Free | Clave anon de Pro |
| `NODE_VERSION` | `20` | `20` | `20` |

Las variables se inyectan en build time (`npm run build` → `output: export`).

### GitHub Actions (Pipelines)

Configurar en GitHub > Settings > Environments:

| Environment | Secret | Valor |
|---|---|---|
| Development | `SUPABASE_URL` | `https://fmcxwoqvxatbrawwtqke.supabase.co` |
| Development | `SUPABASE_SERVICE_ROLE_KEY` | Clave service_role de Free |
| Certification | `SUPABASE_URL` | `https://fmcxwoqvxatbrawwtqke.supabase.co` |
| Certification | `SUPABASE_SERVICE_ROLE_KEY` | Clave service_role de Free |
| Production | `SUPABASE_URL` | `https://zogdcvlqxanzqbvkkdar.supabase.co` |
| Production | `SUPABASE_SERVICE_ROLE_KEY` | Clave service_role de Pro |

### Local (Docker + Next.js dev)

**Python scripts** (usan `.env` en raiz del proyecto):
- Source: `.env` (prioridad) o `.env.local` (fallback)
- `NEXT_PUBLIC_SUPABASE_URL` → Free tier
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` → Free tier
- `SUPABASE_SERVICE_ROLE_KEY` → Free tier

**Frontend Next.js** (usa `web/.env.local`):
- `NEXT_PUBLIC_SUPABASE_URL` → Free tier
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` → Free tier

## Claves Supabase

### Free tier (Desarrollo — `fmcxwoqvxatbrawwtqke`)
| Key | Valor |
|---|---|
| URL | `https://fmcxwoqvxatbrawwtqke.supabase.co` |
| Anon Key | Ver `.env.local` |
| Service Role | Ver `.env.local` |

### Pro tier (Produccion — `zogdcvlqxanzqbvkkdar`)
| Key | Valor |
|---|---|
| URL | `https://zogdcvlqxanzqbvkkdar.supabase.co` |
| Anon Key | Ver `.env.gitprod` |
| Service Role | Ver `.env.gitprod` |

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
1. `NEXT_PUBLIC_SUPABASE_URL` en Cloudflare Pages apunta a Pro (`zogdcvlqxanzqbvkkdar`)
2. `NEXT_PUBLIC_SUPABASE_ANON_KEY` es la clave anon de Pro (NO la service_role)
3. RLS en Pro permite SELECT anon en la tabla `courses`
4. Re-ejecutar el build (las env vars se incrustan en build time)

### Discrepancia de cursos (185 vs 600+)
Si local muestra menos cursos que la web:
1. Verificar que `web/.env.local` apunta al proyecto correcto
2. Ejecutar `rm -rf .next` y reiniciar `npm run dev`
3. Comparar el content-range del fetch desde el navegador

### Static export y env vars
`NEXT_PUBLIC_*` se incrusta en el JS en build time. Para cambiar la URL de Supabase se requiere un nuevo build.
