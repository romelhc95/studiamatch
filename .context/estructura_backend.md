# Estructura Backend — Arquitectura de Tres Capas

> **Actualizado**: 2026-07-05 · **Stack**: Python 3.11 + Supabase + Next.js 16

## Diagrama de Capas

```text
┌──────────────────────────────────────────────────────────────────┐
│                    CAPA 1 — Ingesta Python                        │
│                                                                    │
│   ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌───────┐ │
│   │  Harvester   │→│  Cleansing   │→│  Enrichment   │→│ Sync  │ │
│   │  (FG2-1)     │  │  (FG2-1.5)   │  │  (FG2-2)      │  │(FG2-3)│ │
│   └──────┬──────┘  └──────┬──────┘  └──────┬───────┘  └───┬───┘ │
│          │                │                │               │      │
│   staging_raw      cleansed_programs  enriched_programs  courses │
│                                                                    │
│   Orquestador: GitHub Actions (workflow_dispatch + cron 0 5 *)   │
│   Runtime: ubuntu-latest, Python 3.11, Playwright Chromium       │
│   Timeout: 350 min (harvester/enrichment), 60 min (cleansing/sync)│
└──────────────────────────────────────────────────────────────────┘
        │                                                      ▲
        │  Publishable Key (lectura)                           │
        │  Secret Key (escritura + pipeline reads)             │
        ▼                                                      │
┌──────────────────────────────────────────────────────────────────┐
│                    CAPA 2 — Supabase BaaS                         │
│                                                                    │
│   ┌──────────────────────────────────────────────────────┐       │
│   │              PostgreSQL 15 + Extensiones              │       │
│   │  pg_trgm (búsqueda difusa) · vector 0.8.0 · pg_net   │       │
│   │                                                       │       │
│   │  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │       │
│   │  │ Catálogo │  │  Social  │  │  Pipeline ETL     │  │       │
│   │  │          │  │          │  │                   │  │       │
│   │  │ courses  │  │  leads   │  │  staging_raw      │  │       │
│   │  │ instit.. │  │  ratings │  │  cleansed_programs│  │       │
│   │  │ catego.. │  │  reviews │  │  enriched_programs│  │       │
│   │  │ market.. │  │  email.. │  │  institution_     │  │       │
│   │  │ category│  │          │  │  site_profiles    │  │       │
│   │  └──────────┘  └──────────┘  └───────────────────┘  │       │
│   └──────────────────────────────────────────────────────┘       │
│                                                                    │
│   ┌──────────────────────┐  ┌──────────────────────────────┐     │
│   │  PostgREST (API REST)│  │  RPCs (SECURITY DEFINER)     │     │
│   │  auto-generada sobre │  │  atomic_cleansing_promote    │     │
│   │  esquema public      │  │  atomic_enrichment_promote   │     │
│   │  filtros: ?select=   │  │  lock_staging_records        │     │
│   │  &order=&limit=      │  │  exec_sql (migraciones)      │     │
│   └──────────────────────┘  └──────────────────────────────┘     │
│                                                                    │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  RLS (Row Level Security)                                 │   │
│   │  · anon        → SELECT en catálogo público              │   │
│   │  · authenticated → SELECT + INSERT en social             │   │
│   │  · service_role → ALL (pipeline + admin)                 │   │
│   │  · Tablas ETL bloqueadas completamente para anon          │   │
│   └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
        │                                                      ▲
        │  PostgREST REST API                                  │
        │  fetch() directo (sin @supabase/supabase-js)         │
        ▼                                                      │
┌──────────────────────────────────────────────────────────────────┐
│                    CAPA 3 — Next.js BFF                           │
│                                                                    │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  Server Components (BFF — Backend-for-Frontend)           │   │
│   │                                                           │   │
│   │  layout.tsx          → Metadata global, fuentes, shell    │   │
│   │  page.tsx (/)        → fetchCourses() c/ revalidate 1h    │   │
│   │  [institution]/[slug] → generateStaticParams()            │   │
│   │                      → generateMetadata() + JSON-LD       │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                    │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  Client Components (hidratacion en browser)               │   │
│   │                                                           │   │
│   │  HomeContent.tsx               → Catálogo interactivo     │   │
│   │  CourseDetailClient.tsx         → Detalle + leads         │   │
│   │  CompareContent.tsx             → Comparación multi-curso │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                    │
│   Build: output: 'export' (static) → Cloudflare Pages             │
│   Rebuild: trigger via API al completar FG2 pipeline              │
└──────────────────────────────────────────────────────────────────┘
```

## Capa 1 — Ingesta Python (Data Plane)

### Responsabilidad
Extraer, limpiar, enriquecer y publicar datos de programas educativos desde sitios web institucionales hacia la base de datos Supabase.

### Componentes

| Worker | Script | Entrada | Salida | Orquestacion |
|---|---|---|---|---|
| FG2-1 Harvester | `scripts/core/universal_harvester.py` | `institutions` + `institution_site_profiles` | `staging_raw` | `master_orchestrator.py` |
| FG2-1.5 Cleansing | `scripts/core/cleansing_worker.py` | `staging_raw.status=pending` | `cleansed_programs` | GitHub Actions job |
| FG2-2 Enrichment | `scripts/core/enrichment_worker.py` | `cleansed_programs.status=pending` | `enriched_programs` | GitHub Actions job |
| FG2-3 Sync | `scripts/core/sync_vector_worker.py` | `enriched_programs.status=pending` | `courses` (insert/update protegido por `is_active`) | GitHub Actions job |
| FG3 Integrity | `scripts/core/integrity_ping.py` | `courses.is_active=true` | `courses` (PATCH) | GitHub Actions job |

### Modos de Discovery por Institucion
Definidos en `institution_site_profiles.discovery_mode`:
- `sitemap_bfs` — BFS desde sitemaps XML (default)
- `hardcoded_urls` — URLs semilla del profile
- `paginated_catalog` — Paginacion de catalogo
- `catalog_link_extraction` — Extraccion de links desde indice

### Tipos de Sitio Soportados
Definidos en `institution_site_profiles.site_type`:
- `traditional_ssr` — HTTP GET + BeautifulSoup
- `spa_js_heavy` — Playwright con Chromium headless
- `ecommerce` — Playwright con soporte WooCommerce

### Mecanismos de Control
- **Content Hashing**: SHA256 del HTML limpio para evitar re-procesamiento
- **Circuit Breaker**: Se abre tras `max_consecutive_errors` (default 5) de 403/429
- **Time Guard**: 20,400s (5h40m) — 20 min antes del timeout de GitHub Actions (6h)
- **Freshness Guard**: Skip de catalogos densos cosechados hace <3 dias

### Sistema de Gating (3 niveles)
| Gate | Controla | Default |
|---|---|---|
| `discovery_enabled` | Harvester descubre URLs | `false` |
| `pipeline_enabled` | Cleansing + Enrichment + Sync procesan | `false` → requiere `discovery_enabled` |
| `production_enabled` | Cursos son publicos en frontend | `false` → requiere `pipeline_enabled` |

> Documentacion completa en [[arquitectura_pipeline]]

## Capa 2 — Supabase BaaS (Data Layer)

### Responsabilidad
Almacenar, validar, proteger y exponer datos via API REST autogenerada con Row Level Security.

### Extensiones Activas
| Extension | Version | Proposito |
|---|---|---|
| `pg_trgm` | 1.6 | Indice GIN para busqueda difusa en `courses.name` |
| `vector` | 0.8.0 | Instalada; embeddings en `TEXT` (sin indice vectorial operativo) |
| `pg_net` | 0.20.0 | `net.http_post` para webhooks de leads |
| `pg_stat_statements` | 1.11 | Monitoreo de queries (interno Supabase) |
| `pgcrypto` | 1.3 | `gen_random_uuid()` |
| `uuid-ossp` | 1.1 | Funciones auxiliares UUID |

### Tablas por Dominio (14 tablas activas)

| Dominio | Tablas | Visibilidad |
|---|---|---|
| Catalogo | `courses`, `institutions`, `categories`, `category_rules`, `market_salaries` | Publica (anon SELECT) |
| Social/Leads | `leads`, `ratings`, `reviews`, `email_log` | Mixta (INSERT publico, SELECT varia) |
| Pipeline ETL | `staging_raw`, `cleansed_programs`, `enriched_programs`, `institution_site_profiles` | Privada (solo service_role) |
| Legado | `crawler_exclusions` (0 filas, no usada) | Publica SELECT |

### RLS — Modelo de Seguridad

```
anon
 ├── SELECT → courses (is_active + is_verified + production_enabled)
 ├── SELECT → institutions, categories, category_rules, market_salaries
 ├── INSERT → leads, ratings, reviews
 └── BLOQUEADO → staging_raw, cleansed_programs, enriched_programs

authenticated
 ├── SELECT → mismo que anon + email_log
 └── INSERT → leads, ratings, reviews

service_role
 └── ALL → todas las tablas + todas las RPCs
```

### RPCs Criticas para el Pipeline

| RPC | Capa consumidora | Funcion |
|---|---|---|
| `lock_staging_records` | Capa 1 (Harvester) | Reserva lotes con `FOR UPDATE SKIP LOCKED` |
| `atomic_cleansing_promote` | Capa 1 (Cleansing) | Insercion atomica staging→cleansed |
| `atomic_enrichment_promote` | Capa 1 (Enrichment) | Insercion atomica cleansed→enriched |
| `increment_view_count` | Capa 3 (Frontend) | Contador de visitas |
| `exec_sql` | CI/CD (db_migrate.py) | Aplica migraciones DDL |

> Documentacion completa en [[sistema_db_supabase]]

## Capa 3 — Next.js BFF (Presentation + API Gateway)

### Responsabilidad
Servir como Backend-for-Frontend: generar paginas estaticas con datos pre-fetcheados desde Supabase, inyectar metadata SEO (Open Graph + JSON-LD), y delegar interactividad a Client Components.

### Modelo de Datos

```text
Server Components (build time / ISR simulada)
  │
  │  fetch() → PostgREST (anon key)
  │  next: { revalidate: 3600 }
  │
  ├── layout.tsx
  │   └── Metadata global + Header + Footer
  │
  ├── page.tsx (/)
  │   └── fetchCourses() → HomeContent (client)
  │       └── courses + institutions + categories
  │
  └── courses/[institution]/[slug]/page.tsx
      ├── generateStaticParams()  → todos los cursos activos
      ├── generateMetadata()      → title + description + OG
      └── CourseJsonLd            → schema.org Course
          └── CourseDetailClient (client)

Client Components (browser)
  │
  │  fetch() → PostgREST (anon key)
  │  localStorage cache (5min TTL) + polling (5min)
  │
  ├── HomeContent         → busqueda, filtros, paginacion, compare list
  ├── CourseDetailClient  → tabs (ROI, pilares, requisitos), lead form, ratings
  └── CompareContent      → multi-curso, mejor ROI, mas economico
```

### Columnas Publicas Expuestas
Definidas en `web/src/lib/supabase.ts` → `COURSE_PUBLIC_FIELDS`. Excluye columnas internas (`provider_used`, `is_mock_data`, `last_scraped_at`).

### Build & Deploy
- **Build**: `next build` con `output: 'export'` → HTML/CSS/JS estatico en `out/`
- **Hosting**: Cloudflare Pages (estatico puro)
- **Rebuild trigger**: API call desde `phase_4_audit` del pipeline al completar en `main`
- **`dynamicParams: false`**: Solo rutas en `generateStaticParams()` se pre-renderizan

> Documentacion completa en [[estructura_frontend]]

## Flujo de Datos End-to-End

```text
1. Sitio web institucional
        │
        ▼
2. Capa 1: universal_harvester.py
   (HTTP GET / Playwright + anti-bot)
        │  raw_html, raw_json_ld, raw_og_tags
        ▼
3. staging_raw (Supabase)
        │  status=pending
        ▼
4. Capa 1: cleansing_worker.py
   (limpieza HTML, consolidacion sub-paginas, filtros ruido)
        │  clean_name, clean_description, base_price
        ▼
5. cleansed_programs (Supabase)
        │  status=pending
        ▼
6. Capa 1: enrichment_worker.py
   (LLM triple-cloud: DeepSeek → Cloudflare → mock fallback)
        │  14 pilares estructurados
        ▼
7. enriched_programs (Supabase)
        │  status=pending
        ▼
8. Capa 1: sync_vector_worker.py
   (validacion final, ROI compute, slug generation, insert/update protegido por `is_active`)
        │  name, slug, price_pen, mode, salary, roi_months, etc.
        ▼
9. courses (Supabase) ← is_active=true, is_verified=true
        │  RLS: production_enabled check
        ▼
10. Capa 3: Next.js BFF
    (generateStaticParams → metadata → JSON-LD)
        │  HTML estatico
        ▼
11. Cloudflare Pages → studiamatch.com
```

## Ambientes

| Ambiente | Rama Git | Supabase | Frontend |
|---|---|---|---|
| Desarrollo | `desarrollo` | Free (`aqrldlmlszjtgpqiegaa`) | `studiamatch.pages.dev` |
| Certificacion | `certificacion` | Free (`aqrldlmlszjtgpqiegaa`) | Preview deploy |
| Produccion | `main` | Pro (`xwhtiqmboljkshrtviyw`) | `studiamatch.com` |

### Variables de Entorno por Componente

| Componente | Variables requeridas |
|---|---|
| Capa 1 (Python) | `SUPABASE_URL`, `NEXT_SUPABASE_SECRET_KEY`, `NEXT_SUPABASE_PUBLISHABLE_KEY`, `CF_API_TOKEN`, `CF_ACCOUNT_ID`, `OPENCODE_API_KEY` |
| Capa 2 (Supabase) | N/A — gestionado via Dashboard |
| Capa 3 (Next.js) | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` |

> Documentacion de estado general y limitaciones en [[estado_del_proyecto]]
