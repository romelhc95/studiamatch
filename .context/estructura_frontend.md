# Estructura Frontend

> **Actualizado**: 2026-07-05 · **Framework**: Next.js 16 + React 19 · **Build**: Static Export (`output: 'export'`) · **Styling**: Tailwind CSS v4 + shadcn `base-nova`

## Stack

| Capa | Tecnologia | Version |
|---|---|---|
| Framework | Next.js (App Router) | ^16.2.3 |
| UI | React | ^19.2.4 |
| Estilos | Tailwind CSS + shadcn/ui | ^4 / ^4.1.1 |
| Iconos | Lucide React | ^1.7.0 |
| Componentes base | @base-ui/react | ^1.3.0 |
| Utilidades | clsx, tailwind-merge, class-variance-authority | |
| Tipado | TypeScript | ^5 |
| Linting | ESLint + `eslint-config-next` | ^9 / ^16.2.1 |
| Hosting | Cloudflare Pages (static export) | |

## Mapa de Rutas (App Router)

```
web/src/app/
├── layout.tsx                          # Root Layout (Server)
├── page.tsx                            # / — Home (Server shell)
│   └── HomeContent.tsx                 #   └─ Client UI (catalogo, busqueda, filtros)
├── globals.css                         # Estilos globales
├── courses/
│   ├── page.tsx                        # /courses — Fallback (Server)
│   │   └── CoursesFallbackPage.tsx     #   └─ Client redirect wrapper
│   └── [institution]/
│       └── [slug]/
│           ├── page.tsx                # /courses/:inst/:slug — Detalle (Server)
│           ├── CourseDetailClientWrapper.tsx  # Client shell (dynamic import, ssr:false)
│           └── CourseDetailClient.tsx   #   └─ Client UI (fetch, tabs, lead form)
├── compare/
│   ├── page.tsx                        # /compare — Server Suspense shell
│   └── CompareContent.tsx              #   └─ Client UI (fetch, comparacion)
├── privacidad/
│   └── page.tsx                        # /privacidad — Server static
└── terminos/
    └── page.tsx                        # /terminos — Server static
```

### Resumen de rutas

| Ruta | Server/Client | `generateStaticParams` | `generateMetadata` | JSON-LD |
|---|---|---|---|---|
| `/` | Server shell + Client UI | — | Si (layout) | No |
| `/courses` | Server → delega a client | — | — | — |
| `/courses/[institution]/[slug]` | Server (metadata + LdJson) + Client | Si (todos los cursos activos) | Si (fetch por slug) | Si (`Course`) |
| `/compare` | Server Suspense + Client | — | — | — |
| `/privacidad` | Server static | — | Si | — |
| `/terminos` | Server static | — | Si | — |

## Componentes Clave

### Server Components
- **`layout.tsx`**: Root HTML/body, fuentes Geist, metadata global, `Header` + `Footer`
- **`page.tsx` (Home)**: `fetchCourses()` con `next: { revalidate: 3600 }`, pasa datos a `HomeContent`
- **`courses/[institution]/[slug]/page.tsx`**: `generateStaticParams()`, `generateMetadata()`, `CourseJsonLd`
- **`compare/page.tsx`**: Solo Suspense wrapper que delega a `CompareContent`
- **`privacidad/page.tsx`**, **`terminos/page.tsx`**: Contenido estatico legal

### Client Components
- **`HomeContent.tsx`**: Catalogo principal — busqueda, filtros, sort, paginacion, cache local (5min TTL + polling), lista de comparacion en localStorage, lead modal
- **`CourseDetailClient.tsx`**: Detalle de curso — fetch, tabs (ROI, pilares, requisitos, reviews), lead form, ratings, cursos relacionados
- **`CourseDetailClientWrapper.tsx`**: Dynamic import con `ssr: false` para evitar errores de hidratacion
- **`CompareContent.tsx`**: Comparacion via query params `?ids=...`, fetch multiple, calculo de mejor ROI y mas economico
- **`Header.tsx`**: Navegacion con active route y menu mobile
- **`AnimatedCounter.tsx`**: Contador animado con IntersectionObserver + RAF

### UI Primitives (`components/ui/`)
- **`button.tsx`**: `"use client"` — Base UI + CVA variants
- **`card.tsx`**: Server-compatible
- **`input.tsx`**: Server-compatible
- **`badge.tsx`**: Server-compatible

## Patron de Acceso a Datos

El frontend **NO usa `@supabase/supabase-js`**. Todas las llamadas son `fetch()` directo a PostgREST:

```typescript
// web/src/lib/supabase.ts — Configuracion centralizada
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
const SUPABASE_PUBLISHABLE_KEY = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY

// Headers estandar
const headers = {
  'apikey': SUPABASE_PUBLISHABLE_KEY
}
```

Las API keys modernas no son JWT. El frontend nunca las envia como
`Authorization: Bearer`; ese header queda reservado para un access token de
usuario separado. El build falla cerrado si falta una variable publica o la
key no usa el prefijo `sb_publishable_`.

**Columnas publicas**: `COURSE_PUBLIC_FIELDS` — lista explicita de columnas de `courses` expuestas al frontend, excluyendo internals (`provider_used`, `is_mock_data`, `last_scraped_at`).

**Lecturas** (publishable key, con RLS):
- Home: `courses?is_active=eq.true&is_verified=eq.true&select=...courses,institutions(name,slug),categories(name)` + `institutions`
- Detalle: `courses?slug=eq.{slug}&select=name,description_long,url,price_pen,mode,course_type,institutions(name)` + `ratings` + `reviews`
- Comparacion: `courses?id=in.(...)&is_active=eq.true&is_verified=eq.true`
- Static params: `courses?select=slug,url,institutions(slug)&is_active=eq.true&is_verified=eq.true`

**Escrituras** (publishable key, permitidas por RLS):
- `POST /rest/v1/leads` — captura de leads desde home y detalle
- `POST /rest/v1/ratings` — calificaciones
- `POST /rest/v1/reviews` — resenas
- `POST /rest/v1/rpc/increment_view_count` — contador de vistas

## Static Export & SEO

### Configuracion (`next.config.js`)
```js
{
  output: 'export',
  trailingSlash: true,
  typescript: { ignoreBuildErrors: true },
  images: { unoptimized: true }
}
```

### `generateStaticParams`
- `dynamicParams = false` — solo rutas retornadas por `generateStaticParams()` se pre-renderizan
- Fetch de todos los cursos activos (`is_active=eq.true&is_verified=eq.true`) con `institutions(slug)`
- Usa `cleanSlug()` para derivar el slug de institution
- Fallback: `[{ institution: 'pucp', slug: 'estudios-generales' }]`

### `generateMetadata`
- Busca curso por `slug` (no institution+slug — posible colision entre instituciones)
- Construye title, description, Open Graph, canonical URL

### JSON-LD
- Schema `Course` con nombre, descripcion, provider (EducationalOrganization), precio (Offer), credential awarded, idioma

## Sistema de Estilos

- **Tailwind CSS v4** via `@import "tailwindcss"` + `@tailwindcss/postcss`
- **shadcn/ui** `base-nova` style con CSS variables
- **Animaciones**: `tw-animate-css` + keyframes custom (`gradient-x`, `float`, `shimmer`)
- **Design tokens** en `globals.css`:
  - Colores: `brand-blue` (#2563EB), `brand-slate` (#0F172A), `brand-mint` (#10B981), `brand-gray` (#F1F5F9)
  - Sombras: `premium`, `card`, `elevated`
  - Dark mode: variables preparadas (`@custom-variant dark`)
- **Utilidades**: `section-spacing`, `text-balance`, scrollbars custom, animaciones

## Riesgos y Limitaciones

1. **Static export + dynamic routes**: Cursos nuevos o modificados requieren rebuild para tener pagina estatica y metadata SEO. `dynamicParams = false` impide renderizado on-demand.
2. **`generateStaticParams` sin paginacion**: Fetch de cursos sin `limit` — PostgREST default es 1000. Catalogos mas grandes pueden truncar rutas estaticas.
3. **`generateMetadata` busca solo por slug**: Duplicados de slug entre instituciones producen metadata incorrecta.
4. **`typescript.ignoreBuildErrors: true`**: Regresiones de tipo pueden desplegarse sin deteccion en build.
5. **Duplicacion de logica de fetch**: Home, detalle, comparacion tienen codigo de fetch embebido sin capa de API tipada compartida.
6. **Client-heavy**: Home y detalle son componentes cliente grandes con localStorage, polling y filtrado client-side.
7. **Escrituras desde browser**: `leads`, `ratings`, `reviews`, `counter` usan publishable key — requieren RLS fuerte para prevenir spam/abuso.
8. **`parseDurationToMonths`**: Chequea `unit.startsWith('mes')` despues de hacer lowercase, pero `"12 meses"` empieza con digito, no con `"mes"`, retornando 0 incorrectamente.
9. **Sin `@supabase/supabase-js`**: Fetch manual con raw HTTP — sin tipado automatico, sin manejo de sesiones, sin realtime.
